from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, UploadFile, File, Query, Response, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from bson import ObjectId
import io
import os
import secrets
import subprocess
import logging
import uuid
import asyncio
import json
import time
from html import escape
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlparse

try:
    from PIL import Image, ImageOps, UnidentifiedImageError, features as pillow_features
except ImportError:  # pragma: no cover - production installs Pillow via requirements
    Image = None
    ImageOps = None
    UnidentifiedImageError = Exception
    pillow_features = None

# Shared dependencies — DB, auth, models, utilities
from deps import (
    db, client, logger,
    hash_password, verify_password, create_access_token, create_refresh_token,
    get_jwt_secret, JWT_ALGORITHM,
    init_storage_async, put_object_async, get_object_async, APP_NAME,
    reverse_geocode_async, close_http_client, get_mongo_runtime_config,
    get_current_user, require_auth, require_subscriber, require_municipality, require_registered, get_anonymous_id,
    UserRegister, UserLogin, ReportCreate, VoteCreate, ReportVote, ValidationCreate, FlagCreate,
    UsernameUpdate, AdminUserAccountTypeUpdate, MunicipalityLogin, MunicipalityRegister, AppleReceiptVerify, GoogleReceiptVerify,
    REPORT_CATEGORIES, FLAG_REASONS,
    is_valid_municipality_email, generate_verification_code, generate_password_reset_token, hash_password_reset_token,
    APP_STORE_URL, PLAY_STORE_URL,
    is_vip_email,
    GOOGLE_WEB_CLIENT_ID, GOOGLE_ALLOWED_CLIENT_IDS,
    APP_ENV, db_name, is_mongo_local, mongo_url, redacted_mongo_url, is_production_env,
)
import jwt
import re

# Import gamification services
from scoring_service import (
    calc_report_points, calc_vote_points, update_streak, reset_daily_counts,
    HOT_ZONE_BONUS
)
from antispam_service import (
    check_cooldown, check_proximity_duplicate, check_gps_plausible,
    detect_spam_patterns, update_trust_score, is_hot_zone,
    get_trust_tier, TRUST_SPAM_BEHAVIOR, TRUST_DOWNVOTED_REPORT, TRUST_UPVOTED_REPORT_MIN,
    haversine_meters,
)
from validation_service import process_validation
from ranking_service import recalculate_all_ranks, get_user_rank_info
from rank_metadata import DEFAULT_RANK_NAME, get_rank_key
from email_service import send_verification_code as send_verification_email, is_configured as email_configured, send_admin_verification_code
from webhook_handlers import process_apple_notification, process_google_notification
from push_service import notify_nearby_users, VAPID_PUBLIC_KEY, SAVED_LOCATION_ALERT_RADIUS_METERS
from badges_service import check_and_award_badges, get_user_badges, calc_confidence_score, get_freshness_label, calc_neighborhood_cleanliness
from clean_route_service import analyze_clean_route
from digest_service import send_weekly_digests, generate_municipality_digest
from city_rankings_service import get_city_rankings, get_barrio_rankings, get_active_report_cities, get_active_report_barrios, get_city_report_summary
from share_image_service import build_rankings_share_png, build_barrio_snapshot_png, get_share_image_media_type
from location_share_service import (
    ACTIVE_REPORT_MAX_AGE_DAYS,
    LOCATION_SHARE_COPY,
    append_query_params,
    build_active_report_filter,
    build_cache_headers,
    build_download_path,
    build_location_share_metadata,
    build_share_image_path,
    build_share_path,
    get_location_share_summary,
    slugify_location_segment,
)
from account_linking import normalize_auth_methods, build_provider_link_updates, build_password_link_updates
from google_identity import GoogleIdentityError, get_allowed_client_ids, verify_google_credential
from apple_identity import AppleIdentityError, get_allowed_client_ids as get_allowed_apple_client_ids, verify_apple_identity_token
from play_integrity_service import decode_integrity_token, play_integrity_is_configured, summarize_integrity_payload

# ==================== RECEIPT VERIFICATION ====================

# Apple App Store verification
APPLE_KEY_ID = os.environ.get("APPLE_KEY_ID")
APPLE_ISSUER_ID = os.environ.get("APPLE_ISSUER_ID")
APPLE_BUNDLE_ID = os.environ.get("APPLE_BUNDLE_ID")
APPLE_WEB_CLIENT_ID = os.environ.get("APPLE_WEB_CLIENT_ID", "").strip()
APPLE_WEB_REDIRECT_URI = os.environ.get("APPLE_WEB_REDIRECT_URI", "").strip()
APPLE_KEY_PATH = os.environ.get("APPLE_KEY_PATH")  # Path to .p8 key file
APPLE_ENVIRONMENT = os.environ.get("APPLE_ENVIRONMENT", "Sandbox")  # "Production" or "Sandbox"

# Google Play verification
GOOGLE_SERVICE_ACCOUNT_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH")
GOOGLE_PACKAGE_NAME = os.environ.get("GOOGLE_PACKAGE_NAME")

async def verify_apple_receipt(receipt_data: str, transaction_id: str = None) -> dict:
    """Verify Apple App Store receipt using App Store Server API v2.
    Falls back to mock if credentials not configured."""
    if not all([APPLE_KEY_ID, APPLE_ISSUER_ID, APPLE_BUNDLE_ID, APPLE_KEY_PATH]):
        if is_production_env():
            logger.error("Apple credentials not configured in production")
            return {"valid": False, "error": "Apple subscription verification is not configured"}
        logger.warning("Apple credentials not configured — using mock verification")
        return {"valid": True, "mock": True, "product_id": "premium_monthly", "expires": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}

    try:
        from appstoreserverlibrary.api_client import AppStoreServerAPIClient, GetTransactionHistoryVersion
        from appstoreserverlibrary.models.Environment import Environment
        from appstoreserverlibrary.models.TransactionHistoryRequest import TransactionHistoryRequest
        from appstoreserverlibrary.models.ProductType import ProductType
        from appstoreserverlibrary.receipt_utility import ReceiptUtility
        import json as _json, base64 as _b64

        env = Environment.PRODUCTION if APPLE_ENVIRONMENT == "Production" else Environment.SANDBOX

        with open(APPLE_KEY_PATH, 'r') as f:
            signing_key = f.read()

        client = AppStoreServerAPIClient(signing_key, APPLE_KEY_ID, APPLE_ISSUER_ID, APPLE_BUNDLE_ID, env)

        # Extract transaction ID from receipt if not provided
        if not transaction_id and receipt_data:
            receipt_util = ReceiptUtility()
            transaction_id = receipt_util.extract_transaction_id_from_app_receipt(receipt_data)

        if not transaction_id:
            return {"valid": False, "error": "No transaction ID found in receipt"}

        # Get subscription status via transaction history
        request = TransactionHistoryRequest(productTypes=[ProductType.AUTO_RENEWABLE])
        response = client.get_transaction_history(transaction_id, None, request, GetTransactionHistoryVersion.V2)

        if not response.signedTransactions:
            return {"valid": False, "error": "No transactions found"}

        # Decode the latest signed transaction (JWS)
        latest_jws = response.signedTransactions[-1]
        parts = latest_jws.split(".")
        if len(parts) == 3:
            padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
            tx_info = _json.loads(_b64.urlsafe_b64decode(padded))
        else:
            return {"valid": False, "error": "Invalid JWS transaction format"}

        product_id = tx_info.get("productId", "unknown")
        expires_ms = tx_info.get("expiresDate")
        expires_iso = datetime.fromtimestamp(expires_ms / 1000, tz=timezone.utc).isoformat() if expires_ms else None
        original_tx_id = tx_info.get("originalTransactionId", transaction_id)

        # Check if expired
        is_active = True
        if expires_ms:
            is_active = datetime.fromtimestamp(expires_ms / 1000, tz=timezone.utc) > datetime.now(timezone.utc)

        return {
            "valid": is_active,
            "mock": False,
            "product_id": product_id,
            "transaction_id": original_tx_id,
            "expires": expires_iso,
            "environment": str(env),
        }
    except Exception as e:
        logger.error(f"Apple receipt verification failed: {e}")
        return {"valid": False, "error": str(e)}

async def verify_google_receipt(purchase_token: str, subscription_id: str) -> dict:
    """Verify Google Play subscription using Google Play Developer API v3/v2.
    Falls back to mock if credentials not configured."""
    if not all([GOOGLE_SERVICE_ACCOUNT_PATH, GOOGLE_PACKAGE_NAME]):
        if is_production_env():
            logger.error("Google credentials not configured in production")
            return {"valid": False, "error": "Google subscription verification is not configured"}
        logger.warning("Google credentials not configured — using mock verification")
        return {"valid": True, "mock": True, "product_id": subscription_id, "expires": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}

    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_PATH,
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )
        service = build('androidpublisher', 'v3', credentials=credentials)

        # Try subscriptionsv2 first (newer, supports add-ons)
        try:
            result = service.purchases().subscriptionsv2().get(
                packageName=GOOGLE_PACKAGE_NAME,
                token=purchase_token
            ).execute()

            line_items = result.get("lineItems", [])
            if line_items:
                item = line_items[0]
                expiry_str = item.get("expiryTime")  # RFC3339 string
                auto_renew = item.get("autoRenewingPlan", {}).get("autoRenewing", False)
                product_id = item.get("productId", subscription_id)

                is_active = True
                if expiry_str:
                    expiry_dt = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                    is_active = expiry_dt > datetime.now(timezone.utc)

                return {
                    "valid": is_active,
                    "mock": False,
                    "product_id": product_id,
                    "expires": expiry_str,
                    "auto_renewing": auto_renew,
                    "acknowledgement_state": result.get("acknowledgementState"),
                }
        except Exception:
            pass  # Fall back to v3 subscriptions.get

        # Fallback: v3 subscriptions.get (needs subscription_id)
        result = service.purchases().subscriptions().get(
            packageName=GOOGLE_PACKAGE_NAME,
            subscriptionId=subscription_id,
            token=purchase_token
        ).execute()

        expiry_millis = int(result.get('expiryTimeMillis', 0))
        expiry = datetime.fromtimestamp(expiry_millis / 1000, tz=timezone.utc) if expiry_millis else None
        is_active = expiry > datetime.now(timezone.utc) if expiry else False

        return {
            "valid": is_active,
            "mock": False,
            "product_id": subscription_id,
            "expires": expiry.isoformat() if expiry else None,
            "payment_state": result.get('paymentState'),
            "auto_renewing": result.get('autoRenewing', False)
        }
    except Exception as e:
        logger.error(f"Google receipt verification failed: {e}")
        return {"valid": False, "error": str(e)}

from typing import Optional, Literal
from pydantic import BaseModel

# Additional models not in deps
class ModerationAction(BaseModel):
    action: Literal["hide", "restore", "dismiss"]

class MunicipalityVerify(BaseModel):
    email: str
    code: str

class MunicipalityResendVerification(BaseModel):
    email: str

class PushSubscriptionCreate(BaseModel):
    subscription: dict
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None

class SavedLocationCreate(BaseModel):
    name: str
    label: Optional[str] = None
    latitude: float
    longitude: float

class PushPreferencesUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[int] = None

class QuickReportCreate(BaseModel):
    latitude: float
    longitude: float
    description: Optional[str] = None
    source: Optional[str] = "watch_companion"

class UserPreferencesUpdate(BaseModel):
    preferred_language: Optional[str] = None

class PlayIntegrityVerifyRequest(BaseModel):
    integrity_token: str
    request_hash: str | None = None
    action: str | None = None
    label: Optional[str] = None

# Create the main app
app = FastAPI()
app.state.started_at = datetime.now(timezone.utc).isoformat()
api_router = APIRouter(prefix="/api")

ACTION_PROXIMITY_METERS = 5
REPORT_CLEARED_VOTES_NEEDED = 1
REPORT_PHOTO_STORAGE_MAX_SIDE = 1200
APP_VERSIONS_PATH = Path(__file__).resolve().parent.parent / "frontend" / "src" / "appVersions.json"
SUPPORTED_LANGUAGE_CODES = {"es", "en", "eu", "val", "ca", "de", "nl", "pl", "uk", "ru"}


def get_frontend_url() -> str:
    return os.environ.get("FRONTEND_URL", "https://cacaradar.es").rstrip("/")


def get_share_image_version() -> str:
    git_sha = os.environ.get("GIT_SHA", "").strip()
    if git_sha:
        return git_sha[:12]
    versions = load_app_versions()
    return str(versions.get("web") or "share-v1")


def build_download_url(kind: str, **params) -> str:
    frontend_url = get_frontend_url()
    query_parts = [f"kind={quote(kind)}"]
    for key, value in params.items():
        if value is None or value == "":
            continue
        query_parts.append(f"{quote(str(key))}={quote(str(value))}")
    return f"{frontend_url}/download?{'&'.join(query_parts)}"


def build_share_page_url(kind: str, **params) -> str:
    frontend_url = get_frontend_url()
    query_parts = [f"kind={quote(kind)}"]
    for key, value in params.items():
        if value is None or value == "":
            continue
        query_parts.append(f"{quote(str(key))}={quote(str(value))}")
    return f"{frontend_url}/api/share?{'&'.join(query_parts)}"


def build_expired_report_query(max_age_days: int = ACTIVE_REPORT_MAX_AGE_DAYS) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
    return {
        "archived": {"$ne": True},
        "$or": [
            {"refreshed_at": {"$lt": cutoff}},
            {
                "$and": [
                    {"$or": [{"refreshed_at": {"$exists": False}}, {"refreshed_at": None}]},
                    {"created_at": {"$lt": cutoff}},
                ]
            },
        ],
    }


async def archive_expired_reports(max_age_days: int = ACTIVE_REPORT_MAX_AGE_DAYS) -> int:
    now_iso = datetime.now(timezone.utc).isoformat()
    result = await db.reports.update_many(
        build_expired_report_query(max_age_days),
        {
            "$set": {
                "archived": True,
                "status": "archived",
                "archived_reason": "expired",
                "moderated_at": now_iso,
            }
        },
    )
    return result.modified_count


def build_location_download_url(city_slug: str, barrio_slug: str | None = None) -> str:
    return f"{get_frontend_url()}{build_download_path(city_slug, barrio_slug)}"


def build_location_share_url(city_slug: str, barrio_slug: str | None = None) -> str:
    return f"{get_frontend_url()}{build_share_path(city_slug, barrio_slug)}"


def build_location_share_image_url(city_slug: str, barrio_slug: str | None = None) -> str:
    return append_query_params(
        f"{get_frontend_url()}{build_share_image_path(city_slug, barrio_slug)}.png",
        v=get_share_image_version(),
    )


def build_share_image_response(content: bytes, cache_payload: dict | None = None) -> Response:
    headers = {
        "Content-Type": "image/png",
        "Content-Disposition": "inline; filename=share-card.png",
        "Cache-Control": "public, max-age=900, stale-while-revalidate=3600, no-transform",
        "X-Content-Type-Options": "nosniff",
    }
    if cache_payload is not None:
        headers.update(build_cache_headers(cache_payload))
        headers["Cache-Control"] = "public, max-age=900, stale-while-revalidate=3600, no-transform"
    return Response(content=content, media_type="image/png", headers=headers)


def render_share_page(*, title: str, description: str, image_url: str, share_url: str, redirect_url: str) -> str:
    safe_title = escape(title)
    safe_description = escape(description)
    safe_image = escape(image_url)
    safe_share = escape(share_url)
    safe_redirect = escape(redirect_url)
    safe_app_store = escape(APP_STORE_URL)
    safe_play_store = escape(PLAY_STORE_URL)
    return f"""<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{safe_title}</title>
    <meta name="description" content="{safe_description}" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{safe_title}" />
    <meta property="og:description" content="{safe_description}" />
    <meta property="og:image" content="{safe_image}" />
    <meta property="og:image:secure_url" content="{safe_image}" />
    <meta property="og:image:type" content="image/png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:url" content="{safe_share}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{safe_title}" />
    <meta name="twitter:description" content="{safe_description}" />
    <meta name="twitter:image" content="{safe_image}" />
    <link rel="canonical" href="{safe_share}" />
    <style>
      body {{
        margin: 0;
        font-family: Arial, Helvetica, sans-serif;
        background: #f8f9fa;
        color: #2b2d42;
      }}
      main {{
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 24px;
      }}
      .card {{
        width: min(100%, 640px);
        background: white;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(43,45,66,0.08);
        overflow: hidden;
      }}
      .preview {{
        width: 100%;
        display: block;
        background: #f8f9fa;
      }}
      .body {{
        padding: 24px;
      }}
      h1 {{
        margin: 0 0 12px 0;
        font-size: 28px;
        line-height: 1.15;
      }}
      p {{
        margin: 0 0 18px 0;
        color: #5c677d;
        line-height: 1.5;
      }}
      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
      }}
      .button {{
        display: inline-block;
        padding: 12px 16px;
        border-radius: 14px;
        text-decoration: none;
        font-weight: 700;
      }}
      .primary {{ background: #ff6b6b; color: white; }}
      .secondary {{ background: #f8f9fa; color: #2b2d42; }}
    </style>
  </head>
  <body>
    <main>
      <section class="card">
        <img class="preview" src="{safe_image}" alt="{safe_title}" />
        <div class="body">
          <h1>{safe_title}</h1>
          <p>{safe_description}</p>
          <div class="actions">
            <a class="button primary" href="{safe_redirect}">Abrir Caca Radar</a>
            <a class="button secondary" href="{safe_app_store}">App Store</a>
            <a class="button secondary" href="{safe_play_store}">Google Play</a>
          </div>
        </div>
      </section>
    </main>
  </body>
</html>"""


def load_app_versions() -> dict:
    try:
        with APP_VERSIONS_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {
            "web": "unknown",
            "ios": {"version": "unknown", "build": "unknown"},
            "android": {"version": "unknown", "build": "unknown"},
            "backend": "unknown",
        }


def require_report_proximity(report: dict, latitude: float, longitude: float) -> float:
    report_lat = report.get("latitude")
    report_lon = report.get("longitude")
    if report_lat is None or report_lon is None:
        raise HTTPException(status_code=400, detail="El reporte no tiene coordenadas válidas")

    distance_meters = haversine_meters(latitude, longitude, report_lat, report_lon)
    if distance_meters > ACTION_PROXIMITY_METERS:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "outside_proximity",
                "max_meters": ACTION_PROXIMITY_METERS,
                "distance_meters": round(distance_meters, 1),
            },
        )
    return distance_meters

# ==================== GOOGLE / APPLE AUTH ====================

class GoogleTokenLogin(BaseModel):
    credential: str


class AppleTokenLogin(BaseModel):
    identity_token: str
    authorization_code: str = ""
    email: str = ""
    full_name: str = ""
    given_name: str = ""
    family_name: str = ""
    user: str = ""


def build_google_provider_profile(google_claims: dict) -> dict:
    return {
        "email": google_claims["email"],
        "name": google_claims.get("name", ""),
        "picture": google_claims.get("picture", ""),
        "subject": google_claims["sub"],
    }


def build_apple_provider_profile(apple_claims: dict) -> dict:
    return {
        "email": apple_claims.get("email", ""),
        "name": apple_claims.get("name", ""),
        "picture": "",
        "subject": apple_claims["sub"],
    }


async def generate_unique_username(base_email: str) -> str:
    base_username = base_email.split("@")[0].lower().replace(".", "_").replace("-", "_")
    base_username = "".join(c for c in base_username if c.isalnum() or c == "_")[:15] or "cacaradar"
    username = base_username
    attempt = 0
    while await db.users.find_one({"username": username}):
        attempt += 1
        suffix = str(attempt)
        username = f"{base_username[: max(1, 15 - len(suffix))]}{suffix}"
    return username


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")


def is_explicit_native_app_request(request: Request) -> bool:
    context = get_request_context(request)
    platform = normalize_login_platform(request)
    origin = (context.get("origin") or "").strip().lower()
    referer = (context.get("referer") or "").strip().lower()
    native_app = (context.get("native_app") or "").strip().lower()
    native_origin = origin.startswith("capacitor://") or origin.startswith("ionic://") or not origin
    native_referer = (
        referer.startswith("capacitor://")
        or referer.startswith("ionic://")
        or referer.startswith("http://localhost")
        or referer.startswith("https://localhost")
    )
    web_referer = (
        referer.startswith("http://") or referer.startswith("https://")
    ) and ("cacaradar.es" in referer or "emergent.host" in referer) and not native_referer
    return platform in {"ios", "android", "native"} and (native_origin or native_referer) and not web_referer and native_app == "1"


def should_return_body_tokens(request: Request) -> bool:
    return is_explicit_native_app_request(request)


def get_account_type(user: Optional[dict]) -> str:
    if not user:
        return "standard"
    account_type = (user.get("account_type") or "standard").strip().lower()
    return account_type if account_type in {"standard", "municipal_worker"} else "standard"


def is_municipal_worker_account(user: Optional[dict]) -> bool:
    return get_account_type(user) == "municipal_worker"


def report_within_municipal_scope(user: Optional[dict], report: Optional[dict]) -> bool:
    if not user or not report:
        return False
    user_municipality = slugify_location_segment(user.get("municipality_name", "") or "")
    report_municipality = slugify_location_segment(report.get("municipality", "") or "")
    if not user_municipality or not report_municipality or user_municipality != report_municipality:
        return False
    user_province = (user.get("municipality_province") or "").strip().lower()
    report_province = (report.get("province") or "").strip().lower()
    return not user_province or not report_province or user_province == report_province


def can_clear_report_without_proximity(user: Optional[dict], report: Optional[dict]) -> bool:
    if not user:
        return False
    if user.get("role") == "admin":
        return True
    if user.get("role") == "municipality":
        return report_within_municipal_scope(user, report)
    return is_municipal_worker_account(user) and report_within_municipal_scope(user, report)


def issue_auth_session(user: dict, request: Request, response: Response) -> tuple[str, str]:
    user_id = str(user["_id"])
    role = user.get("role", "user")
    access_token = create_access_token(user_id, user.get("email", ""), role)
    refresh_token = create_refresh_token(user_id)
    set_auth_cookies(response, access_token, refresh_token)
    return access_token, refresh_token


def build_auth_payload(user: dict, access_token: str, refresh_token: str, request: Request) -> dict:
    user_id = str(user["_id"])
    role = user.get("role", "user")
    payload = {
        "id": user_id,
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "username": user.get("username"),
        "role": role,
        "account_type": get_account_type(user),
        "subscription_active": user.get("subscription_active", False),
        "subscription_type": user.get("subscription_type"),
        "report_count": user.get("report_count", 0),
        "vote_count": user.get("vote_count", 0),
        "municipality_name": user.get("municipality_name"),
        "municipality_province": user.get("municipality_province"),
        "total_score": user.get("total_score", 0),
        "trust_score": user.get("trust_score", 50),
        "rank": user.get("rank", DEFAULT_RANK_NAME),
        "rank_key": user.get("rank_key", get_rank_key(user.get("rank", DEFAULT_RANK_NAME))),
        "level": user.get("level", 1),
        "streak_days": user.get("streak_days", 0),
        "preferred_language": user.get("preferred_language"),
        "geo_review_exempt": user.get("geo_review_exempt", False),
        "needs_username": not bool(user.get("username")),
        "auth_provider": user.get("auth_provider"),
        "auth_methods": normalize_auth_methods(user),
    }
    if should_return_body_tokens(request):
        payload["access_token"] = access_token
    return payload


def normalize_login_platform(request: Request) -> str:
    context = get_request_context(request)
    platform = (context.get("platform") or "").strip().strip('"').lower()
    if platform in {"ios", "android", "web"}:
        return platform
    if platform == "capacitor":
        user_agent = (context.get("user_agent") or "").lower()
        if "iphone" in user_agent or "ios" in user_agent:
            return "ios"
        if "android" in user_agent:
            return "android"
        return "native"
    if platform:
        return platform
    user_agent = (context.get("user_agent") or "").lower()
    if "iphone" in user_agent or "ipad" in user_agent:
        return "ios"
    if "android" in user_agent:
        return "android"
    return "web"


async def update_login_metadata(user_id: ObjectId, request: Request, existing_user: Optional[dict] = None) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    updates = {
        "last_login_at": now_iso,
        "last_login_platform": normalize_login_platform(request),
    }
    context = get_request_context(request)
    if context.get("app_version"):
        updates["last_login_app_version"] = context["app_version"]
    if context.get("app_environment"):
        updates["last_login_app_environment"] = context["app_environment"]
    if context.get("user_agent"):
        updates["last_login_user_agent"] = context["user_agent"]
    await db.users.update_one({"_id": user_id}, {"$set": updates})
    if existing_user is not None:
        existing_user.update(updates)
        return existing_user
    user = await db.users.find_one({"_id": user_id})
    return user


async def complete_google_login_for_user(user: dict, request: Request, response: Response) -> dict:
    user = await update_login_metadata(user["_id"], request, user)
    access_token, refresh_token = issue_auth_session(user, request, response)
    return build_auth_payload(user, access_token, refresh_token, request)


async def complete_social_login_for_user(user: dict, request: Request, response: Response) -> dict:
    user = await update_login_metadata(user["_id"], request, user)
    access_token, refresh_token = issue_auth_session(user, request, response)
    return build_auth_payload(user, access_token, refresh_token, request)


def get_google_client_ids() -> list[str]:
    return get_allowed_client_ids(GOOGLE_WEB_CLIENT_ID, GOOGLE_ALLOWED_CLIENT_IDS)


def get_apple_client_ids() -> list[str]:
    primary_clients = [APPLE_BUNDLE_ID or "", APPLE_WEB_CLIENT_ID]
    allowed: list[str] = []
    for client_id in primary_clients:
        for normalized in get_allowed_apple_client_ids(client_id, os.environ.get("APPLE_ALLOWED_CLIENT_IDS", "")):
            if normalized not in allowed:
                allowed.append(normalized)
    return allowed


def normalize_post_auth_path(next_path: str | None, default: str = "/") -> str:
    normalized = (next_path or "").strip()
    if normalized.startswith("/") and not normalized.startswith("//"):
        return normalized
    return default


def build_apple_web_redirect_uri(request: Request) -> str:
    if APPLE_WEB_REDIRECT_URI:
        return APPLE_WEB_REDIRECT_URI
    host = (request.url.hostname or "").strip().lower()
    if host in {"", "localhost", "127.0.0.1"}:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "apple_web_not_configured",
                "message": "Apple web sign-in needs APPLE_WEB_REDIRECT_URI on this deployment.",
            },
        )
    return str(request.base_url).rstrip("/") + "/api/auth/apple/callback"


def create_apple_web_state(flow: str, next_path: str, link_user_id: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    nonce = uuid.uuid4().hex
    payload = {
        "flow": flow,
        "next": normalize_post_auth_path(next_path, "/profile" if flow == "link" else "/"),
        "nonce": nonce,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
    }
    if link_user_id:
        payload["link_user_id"] = link_user_id
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_apple_web_state(state_token: str) -> dict:
    try:
        payload = jwt.decode(state_token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "apple_state_invalid",
                "message": "Apple sign-in session expired. Please try again.",
            },
        ) from exc
    flow = payload.get("flow")
    if flow not in {"login", "link"}:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "apple_state_invalid",
                "message": "Apple sign-in session is invalid. Please try again.",
            },
        )
    payload["next"] = normalize_post_auth_path(payload.get("next"), "/profile" if flow == "link" else "/")
    return payload


def build_frontend_redirect_url(path: str, error: str = "", success_query: dict | None = None) -> str:
    base = normalize_post_auth_path(path)
    query_parts = []
    if error:
        query_parts.append(f"apple_error={quote(error)}")
    if success_query:
        for key, value in success_query.items():
            query_parts.append(f"{quote(str(key))}={quote(str(value))}")
    if not query_parts:
        return base
    separator = "&" if "?" in base else "?"
    return base + separator + "&".join(query_parts)


async def verify_google_login_credential(credential: str) -> dict:
    try:
        google_claims = verify_google_credential(credential, get_google_client_ids())
        logger.info(
            "Verified Google ID token for sub=%s aud=%s email=%s",
            google_claims["sub"],
            google_claims["raw"].get("aud"),
            google_claims["email"],
        )
        return google_claims
    except GoogleIdentityError as exc:
        if exc.log_message:
            logger.warning("Google credential verification failed [%s]: %s", exc.code, exc.log_message)
        else:
            logger.warning("Google credential verification failed [%s]", exc.code)
        status_code = 503 if exc.code == "google_not_configured" else 401
        raise HTTPException(status_code=status_code, detail={"code": exc.code, "message": exc.message}) from exc


async def verify_apple_login_credential(data: AppleTokenLogin) -> dict:
    fallback_name = data.full_name.strip() or " ".join(part for part in [data.given_name.strip(), data.family_name.strip()] if part)
    try:
        apple_claims = verify_apple_identity_token(
            data.identity_token,
            get_apple_client_ids(),
            fallback_email=data.email,
            fallback_name=fallback_name,
        )
        logger.info(
            "Verified Apple ID token for sub=%s aud=%s email=%s",
            apple_claims["sub"],
            apple_claims["raw"].get("aud"),
            apple_claims.get("email", ""),
        )
        return apple_claims
    except AppleIdentityError as exc:
        if exc.log_message:
            logger.warning("Apple credential verification failed [%s]: %s", exc.code, exc.log_message)
        else:
            logger.warning("Apple credential verification failed [%s]", exc.code)
        status_code = 503 if exc.code == "apple_not_configured" else 401
        raise HTTPException(status_code=status_code, detail={"code": exc.code, "message": exc.message}) from exc


async def find_or_create_google_user(google_claims: dict) -> tuple[dict, bool]:
    provider_profile = build_google_provider_profile(google_claims)
    email = google_claims["email"]
    is_vip = is_vip_email(email)

    user = await db.users.find_one({"linked_providers.google.subject": google_claims["sub"]})
    if user:
        updates = build_provider_link_updates(user, "google", provider_profile)
        if is_vip and not user.get("subscription_active"):
            updates["subscription_active"] = True
            updates["subscription_type"] = "lifetime"
        if user.get("trust_score", 50) < 50 and is_vip:
            updates["trust_score"] = 50
        if updates:
            await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
            user.update(updates)
        return user, False

    email_user = await db.users.find_one({"email": email})
    if email_user:
        existing_methods = normalize_auth_methods(email_user)
        if "google" in existing_methods:
            updates = build_provider_link_updates(email_user, "google", provider_profile)
            if is_vip and not email_user.get("subscription_active"):
                updates["subscription_active"] = True
                updates["subscription_type"] = "lifetime"
            if email_user.get("trust_score", 50) < 50 and is_vip:
                updates["trust_score"] = 50
            if updates:
                await db.users.update_one({"_id": email_user["_id"]}, {"$set": updates})
                email_user.update(updates)
            return email_user, False

        logger.info("Google login requires linking for existing non-Google account email=%s", email)
        raise HTTPException(
            status_code=409,
            detail={
                "code": "google_link_required",
                "message": "This email already belongs to an existing account. Sign in with your current method and link Google from settings.",
            },
        )

    username = await generate_unique_username(email)
    now = datetime.now(timezone.utc)
    user_doc = {
        "email": email,
        "password_hash": "",
        "name": provider_profile["name"] or username,
        "username": username,
        "picture": provider_profile["picture"],
        "role": "user",
        "auth_provider": "google",
        "auth_methods": ["google"],
        "linked_providers": {
            "google": {
                "email": email,
                "name": provider_profile["name"],
                "picture": provider_profile["picture"],
                "subject": provider_profile["subject"],
                "linked_at": now.isoformat(),
                "last_login_at": now.isoformat(),
            }
        },
        "subscription_active": is_vip,
        "subscription_type": "lifetime" if is_vip else None,
        "total_score": 0,
        "trust_score": 50,
        "rank": DEFAULT_RANK_NAME,
        "rank_key": get_rank_key(DEFAULT_RANK_NAME),
        "level": 1,
        "report_count": 0,
        "vote_count": 0,
        "streak_days": 0,
        "created_at": now,
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc, True


async def find_or_create_apple_user(apple_claims: dict) -> tuple[dict, bool]:
    provider_profile = build_apple_provider_profile(apple_claims)
    email = (apple_claims.get("email") or "").strip().lower()
    is_vip = is_vip_email(email)

    user = await db.users.find_one({"linked_providers.apple.subject": apple_claims["sub"]})
    if user:
        updates = build_provider_link_updates(user, "apple", provider_profile)
        if is_vip and not user.get("subscription_active"):
            updates["subscription_active"] = True
            updates["subscription_type"] = "lifetime"
        if user.get("trust_score", 50) < 50 and is_vip:
            updates["trust_score"] = 50
        if updates:
            await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
            user.update(updates)
        return user, False

    if email:
        email_user = await db.users.find_one({"email": email})
        if email_user:
            existing_methods = normalize_auth_methods(email_user)
            if "apple" in existing_methods:
                updates = build_provider_link_updates(email_user, "apple", provider_profile)
                if is_vip and not email_user.get("subscription_active"):
                    updates["subscription_active"] = True
                    updates["subscription_type"] = "lifetime"
                if email_user.get("trust_score", 50) < 50 and is_vip:
                    updates["trust_score"] = 50
                if updates:
                    await db.users.update_one({"_id": email_user["_id"]}, {"$set": updates})
                    email_user.update(updates)
                return email_user, False

            logger.info("Apple login requires linking for existing non-Apple account email=%s", email)
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "apple_link_required",
                    "message": "This email already belongs to an existing account. Sign in with your current method and link Apple from settings.",
                },
            )

    if not email:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "apple_email_missing",
                "message": "Apple sign-in did not provide an email for this new account. Sign in again and choose to share your email, or link Apple from an existing account.",
            },
        )

    username = await generate_unique_username(email)
    now = datetime.now(timezone.utc)
    user_doc = {
        "email": email,
        "password_hash": "",
        "name": provider_profile["name"] or username,
        "username": username,
        "picture": "",
        "role": "user",
        "auth_provider": "apple",
        "auth_methods": ["apple"],
        "linked_providers": {
            "apple": {
                "email": email,
                "name": provider_profile["name"],
                "picture": "",
                "subject": provider_profile["subject"],
                "linked_at": now.isoformat(),
                "last_login_at": now.isoformat(),
            }
        },
        "subscription_active": is_vip,
        "subscription_type": "lifetime" if is_vip else None,
        "total_score": 0,
        "trust_score": 50,
        "rank": DEFAULT_RANK_NAME,
        "rank_key": get_rank_key(DEFAULT_RANK_NAME),
        "level": 1,
        "report_count": 0,
        "vote_count": 0,
        "streak_days": 0,
        "created_at": now,
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return user_doc, True


def parse_apple_user_payload(raw_user: str) -> tuple[str, str, str, str]:
    if not raw_user:
        return "", "", "", ""
    try:
        user_payload = json.loads(raw_user)
    except Exception:
        return "", "", "", ""
    name = user_payload.get("name") or {}
    given_name = (name.get("firstName") or "").strip()
    family_name = (name.get("lastName") or "").strip()
    full_name = " ".join(part for part in [given_name, family_name] if part)
    email = (user_payload.get("email") or "").strip().lower()
    return email, given_name, family_name, full_name


@api_router.post("/auth/google/login")
async def google_auth_login(data: GoogleTokenLogin, request: Request, response: Response):
    google_claims = await verify_google_login_credential(data.credential)
    user, created = await find_or_create_google_user(google_claims)
    logger.info(
        "Google sign-in %s for user=%s sub=%s",
        "created" if created else "completed",
        user.get("email"),
        google_claims["sub"],
    )
    return await complete_social_login_for_user(user, request, response)


@api_router.get("/auth/apple/start")
async def start_apple_web_auth(request: Request, flow: str = Query("login"), next: str = Query("/")):
    if not APPLE_WEB_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "apple_web_not_configured",
                "message": "Apple sign-in is not configured for the web.",
            },
        )
    normalized_flow = "link" if flow == "link" else "login"
    current_user_id = None
    if normalized_flow == "link":
        current_user = await require_auth(request)
        current_user_id = current_user["_id"]
    redirect_uri = build_apple_web_redirect_uri(request)
    state_token = create_apple_web_state(normalized_flow, next, current_user_id)
    state_payload = decode_apple_web_state(state_token)
    auth_url = (
        "https://appleid.apple.com/auth/authorize"
        f"?response_type={quote('code id_token')}"
        "&response_mode=form_post"
        f"&client_id={quote(APPLE_WEB_CLIENT_ID)}"
        f"&redirect_uri={quote(redirect_uri, safe=':/')}"
        f"&scope={quote('name email')}"
        f"&state={quote(state_token)}"
        f"&nonce={quote(state_payload['nonce'])}"
    )
    return RedirectResponse(url=auth_url, status_code=302)


@api_router.post("/auth/apple/callback")
async def apple_web_auth_callback(
    request: Request,
    state: str = Form(""),
    id_token: str = Form(""),
    code: str = Form(""),
    user: str = Form(""),
    error: str = Form(""),
    error_description: str = Form(""),
):
    try:
        state_payload = decode_apple_web_state(state)
    except HTTPException as exc:
        return RedirectResponse(
            url=build_frontend_redirect_url("/login", exc.detail.get("message", "Apple sign-in failed.")),
            status_code=303,
        )

    destination = state_payload["next"]
    if error:
        return RedirectResponse(
            url=build_frontend_redirect_url(destination, error_description or error),
            status_code=303,
        )

    email, given_name, family_name, full_name = parse_apple_user_payload(user)
    apple_data = AppleTokenLogin(
        identity_token=id_token,
        authorization_code=code,
        email=email,
        full_name=full_name,
        given_name=given_name,
        family_name=family_name,
        user="",
    )

    try:
        apple_claims = verify_apple_identity_token(
            apple_data.identity_token,
            get_apple_client_ids(),
            fallback_email=apple_data.email,
            fallback_name=apple_data.full_name,
            expected_nonce=state_payload["nonce"],
        )
        if state_payload["flow"] == "link":
            current_user = await require_auth(request)
            if current_user["_id"] != state_payload.get("link_user_id"):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "apple_link_session_mismatch",
                        "message": "Please sign in again before linking Apple.",
                    },
                )
            provider_profile = build_apple_provider_profile(apple_claims)
            existing_apple_user = await db.users.find_one({"linked_providers.apple.subject": apple_claims["sub"]})
            if existing_apple_user and str(existing_apple_user["_id"]) != current_user["_id"]:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "apple_already_linked",
                        "message": "This Apple account is already linked to another Caca Radar user.",
                    },
                )
            current_user_doc = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
            updates = build_provider_link_updates(current_user_doc, "apple", provider_profile)
            if updates:
                await db.users.update_one({"_id": current_user_doc["_id"]}, {"$set": updates})
            return RedirectResponse(
                url=build_frontend_redirect_url(destination, success_query={"apple_linked": 1}),
                status_code=303,
            )

        auth_response = Response()
        user_doc, _created = await find_or_create_apple_user(apple_claims)
        await complete_social_login_for_user(user_doc, request, auth_response)
        redirect = RedirectResponse(url=destination, status_code=303)
        for header_name, header_value in auth_response.raw_headers:
            if header_name.lower() == b"set-cookie":
                redirect.headers.append("set-cookie", header_value.decode("utf-8"))
        return redirect
    except HTTPException as exc:
        message = exc.detail.get("message", "Apple sign-in failed.") if isinstance(exc.detail, dict) else str(exc.detail)
        return RedirectResponse(
            url=build_frontend_redirect_url(destination, message),
            status_code=303,
        )
    except AppleIdentityError as exc:
        return RedirectResponse(
            url=build_frontend_redirect_url(destination, exc.message),
            status_code=303,
        )


@api_router.post("/auth/apple/login")
async def apple_auth_login(data: AppleTokenLogin, request: Request, response: Response):
    apple_claims = await verify_apple_login_credential(data)
    user, created = await find_or_create_apple_user(apple_claims)
    logger.info(
        "Apple sign-in %s for user=%s sub=%s",
        "created" if created else "completed",
        user.get("email"),
        apple_claims["sub"],
    )
    return await complete_social_login_for_user(user, request, response)


@api_router.post("/auth/google/link")
async def link_google_account(data: GoogleTokenLogin, request: Request):
    current_user = await require_auth(request)
    google_claims = await verify_google_login_credential(data.credential)
    provider_profile = build_google_provider_profile(google_claims)

    existing_google_user = await db.users.find_one({"linked_providers.google.subject": google_claims["sub"]})
    if existing_google_user and str(existing_google_user["_id"]) != current_user["_id"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "google_already_linked",
                "message": "This Google account is already linked to another Caca Radar user.",
            },
        )

    current_user_doc = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
    updates = build_provider_link_updates(current_user_doc, "google", provider_profile)
    await db.users.update_one({"_id": current_user_doc["_id"]}, {"$set": updates})
    logger.info("Linked Google account sub=%s to user=%s", google_claims["sub"], current_user_doc.get("email"))
    return {"message": "Google account linked", "auth_methods": normalize_auth_methods({**current_user_doc, **updates})}


@api_router.post("/auth/apple/link")
async def link_apple_account(data: AppleTokenLogin, request: Request):
    current_user = await require_auth(request)
    apple_claims = await verify_apple_login_credential(data)
    provider_profile = build_apple_provider_profile(apple_claims)

    existing_apple_user = await db.users.find_one({"linked_providers.apple.subject": apple_claims["sub"]})
    if existing_apple_user and str(existing_apple_user["_id"]) != current_user["_id"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "apple_already_linked",
                "message": "This Apple account is already linked to another Caca Radar user.",
            },
        )

    current_user_doc = await db.users.find_one({"_id": ObjectId(current_user["_id"])})
    updates = build_provider_link_updates(current_user_doc, "apple", provider_profile)
    await db.users.update_one({"_id": current_user_doc["_id"]}, {"$set": updates})
    logger.info("Linked Apple account sub=%s to user=%s", apple_claims["sub"], current_user_doc.get("email"))
    return {"message": "Apple account linked", "auth_methods": normalize_auth_methods({**current_user_doc, **updates})}

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(data: UserRegister, request: Request, response: Response):
    import re
    email = data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    if not data.terms_accepted or not data.privacy_accepted or not data.age_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Debes aceptar la Política de Privacidad, los Términos y confirmar que cumples los requisitos de edad o autorización.",
        )
    
    username = data.username.lower().strip()
    if len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="El nombre de usuario debe tener entre 3 y 20 caracteres")
    if not re.match(r'^[a-z0-9_]+$', username):
        raise HTTPException(status_code=400, detail="Solo letras, números y guiones bajos permitidos")
    existing_username = await db.users.find_one({"username": username})
    if existing_username:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    hashed = hash_password(data.password)
    is_vip = is_vip_email(email)
    registration_timestamp = datetime.now(timezone.utc)
    user_doc = {
        "email": email,
        "password_hash": hashed,
        "name": data.name or username,
        "username": username,
        "auth_provider": "password",
        "auth_methods": ["password"],
        "linked_providers": {},
        "role": "user",
        "subscription_active": is_vip,
        "subscription_type": "lifetime" if is_vip else None,
        "subscription_expires": None,
        "total_score": 0,
        "trust_score": 50,
        "rank": DEFAULT_RANK_NAME,
        "rank_key": get_rank_key(DEFAULT_RANK_NAME),
        "level": 1,
        "report_count": 0,
        "vote_count": 0,
        "daily_report_count": 0,
        "streak_days": 0,
        "last_active_date": None,
        "created_at": registration_timestamp,
        "terms_accepted_at": registration_timestamp,
        "privacy_accepted_at": registration_timestamp,
        "age_confirmation_at": registration_timestamp,
        "legal_notice_version": "2026-05-04",
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    user_doc["_id"] = result.inserted_id
    user_doc = await update_login_metadata(result.inserted_id, request, user_doc)
    
    access_token, refresh_token = issue_auth_session(user_doc, request, response)
    return build_auth_payload(user_doc, access_token, refresh_token, request)

@api_router.post("/auth/login")
async def login(data: UserLogin, request: Request, response: Response):
    email = data.email.lower()
    ip = request.client.host
    identifier = f"{ip}:{email}"
    
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    if attempts and attempts.get("count", 0) >= 5:
        lockout_time = attempts.get("last_attempt", datetime.now(timezone.utc))
        if datetime.now(timezone.utc) - lockout_time < timedelta(minutes=15):
            raise HTTPException(status_code=429, detail="Demasiados intentos. Espera 15 minutos.")
        else:
            await db.login_attempts.delete_one({"identifier": identifier})
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user.get("password_hash", "")):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc)}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if user.get("role") == "municipality" and not user.get("email_verified"):
        raise HTTPException(status_code=403, detail="Debes verificar el email oficial antes de iniciar sesión en el panel municipal")
    
    await db.login_attempts.delete_one({"identifier": identifier})
    
    # Ensure VIP users always have premium and healthy trust
    if is_vip_email(email):
        updates = {}
        if not user.get("subscription_active"):
            updates["subscription_active"] = True
            updates["subscription_type"] = "lifetime"
        if user.get("trust_score", 50) < 50:
            updates["trust_score"] = 50
        if updates:
            await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
            user.update(updates)
    user = await update_login_metadata(user["_id"], request, user)
    
    access_token, refresh_token = issue_auth_session(user, request, response)
    return build_auth_payload(user, access_token, refresh_token, request)

@api_router.post("/auth/forgot-password")
async def forgot_password(request: Request):
    """Send a password reset link to the user's email."""
    body = await request.json()
    email = body.get("email", "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")

    context = get_request_context(request)
    client_ip = context.get("client_ip") or "unknown"
    await enforce_rate_limit(
        key=f"forgot_password:ip:{client_ip}",
        max_attempts=10,
        window_seconds=3600,
        detail="Demasiadas solicitudes. Inténtalo más tarde.",
    )
    await enforce_rate_limit(
        key=f"forgot_password:email:{email}",
        max_attempts=3,
        window_seconds=3600,
        detail="Demasiadas solicitudes. Inténtalo más tarde.",
    )

    user = await db.users.find_one({"email": email})
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}

    # Generate a time-limited reset token (1 hour)
    reset_token = generate_password_reset_token()
    token_hash = hash_password_reset_token(reset_token)
    await db.password_resets.update_one(
        {"email": email},
        {"$set": {
            "email": email,
            "token_hash": token_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "used": False,
        }},
        upsert=True,
    )

    frontend_url = os.environ.get("FRONTEND_URL", "https://caca-radar.emergent.host")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px;">
      <h2 style="color:#2B2D42;">Restablecer contraseña</h2>
      <p>Hemos recibido una solicitud para restablecer tu contraseña en <strong>Caca Radar</strong>.</p>
      <p>Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
      <a href="{reset_link}" style="display:inline-block;background:#FF6B6B;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin:16px 0;">Restablecer contraseña</a>
      <p style="color:#8D99AE;font-size:13px;">Este enlace expira en 1 hora. Si no solicitaste este cambio, ignora este email.</p>
    </div>
    """

    from email_service import send_email
    result = await send_email(email, "Caca Radar — Restablecer contraseña", html)
    logger.info("Password reset requested for %s: email_result=%s", email, result.get("status"))

    return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}


@api_router.post("/auth/reset-password")
async def reset_password(request: Request):
    """Reset password using a valid reset token."""
    body = await request.json()
    token = body.get("token", "").strip()
    new_password = body.get("password", "")

    if not token:
        raise HTTPException(status_code=400, detail="Token requerido")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    token_hash = hash_password_reset_token(token)
    reset_doc = await db.password_resets.find_one({"token_hash": token_hash, "used": False})
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Enlace inválido o ya utilizado")

    # Check expiry
    expires = reset_doc.get("expires_at", "")
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="El enlace ha expirado. Solicita uno nuevo.")

    email = reset_doc["email"]
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    # Update password and link password auth to this account.
    hashed = hash_password(new_password)
    password_updates = build_password_link_updates(user, hashed)
    await db.users.update_one({"email": email}, {"$set": password_updates})

    # Mark token as used
    await db.password_resets.update_one({"token_hash": token_hash}, {"$set": {"used": True}})

    logger.info(f"Password reset completed for {email}")
    return {"message": "Contraseña actualizada correctamente. Ya puedes iniciar sesión."}


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Sesión cerrada"}

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    user["auth_methods"] = normalize_auth_methods(user)
    user["needs_username"] = not bool(user.get("username"))
    user["geo_review_exempt"] = user.get("geo_review_exempt", False)
    user["account_type"] = get_account_type(user)
    return user

@api_router.post("/auth/native/session-tokens")
async def issue_native_session_tokens(request: Request):
    if not is_explicit_native_app_request(request):
        raise HTTPException(status_code=403, detail="Native app request required")
    user = await get_current_user(request)
    if not user:
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            try:
                payload = jwt.decode(refresh_token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
                if payload.get("type") == "refresh":
                    fallback_user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
                    if fallback_user:
                        fallback_user["_id"] = str(fallback_user["_id"])
                        fallback_user.pop("password_hash", None)
                        user = fallback_user
            except Exception:
                user = None
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    access_token = create_access_token(str(user["_id"]), user["email"], user.get("role", "user"))
    return {
        "access_token": access_token,
    }

@api_router.post("/auth/refresh")
async def refresh_token_endpoint(request: Request, response: Response):
    # Accept refresh token from cookie for web, or request body for native.
    token = request.cookies.get("refresh_token")
    if not token and should_return_body_tokens(request):
        try:
            body = await request.json()
            token = body.get("refresh_token")
        except Exception:
            pass
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        new_access = create_access_token(str(user["_id"]), user["email"], user.get("role", "user"))
        if not should_return_body_tokens(request):
            response.set_cookie(key="access_token", value=new_access, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
        return {"message": "Token refreshed", "access_token": new_access}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== USER PROFILE ====================

@api_router.put("/users/username")
async def update_username(data: UsernameUpdate, request: Request):
    import re
    user = await require_auth(request)
    
    username = data.username.lower().strip()
    if len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="El nombre de usuario debe tener entre 3 y 20 caracteres")
    if not re.match(r'^[a-z0-9_]+$', username):
        raise HTTPException(status_code=400, detail="Solo letras, números y guiones bajos permitidos")
    
    existing = await db.users.find_one({"username": username, "_id": {"$ne": ObjectId(user["_id"])}})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"username": username}})
    return {"username": username}

@api_router.put("/users/preferences")
async def update_user_preferences(data: UserPreferencesUpdate, request: Request):
    user = await require_auth(request)
    updates = {}

    if data.preferred_language is not None:
        preferred_language = (data.preferred_language or "").strip().lower()
        if preferred_language and preferred_language not in SUPPORTED_LANGUAGE_CODES:
            raise HTTPException(status_code=400, detail="Idioma no soportado")
        updates["preferred_language"] = preferred_language or None

    if not updates:
        return {
            "preferred_language": user.get("preferred_language"),
        }

    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": updates})
    return {
        "preferred_language": updates.get("preferred_language"),
    }

@api_router.delete("/users/me")
async def delete_current_user_account(request: Request, response: Response):
    user = await require_auth(request)
    user_object_id = user["_id"] if isinstance(user["_id"], ObjectId) else ObjectId(user["_id"])
    user_id = str(user_object_id)
    deleted_at = datetime.now(timezone.utc).isoformat()

    await db.reports.update_many(
        {"user_id": user_id},
        {"$set": {
            "user_id": None,
            "contributor_name": "Anónimo",
            "contributor_rank": None,
            "contributor_rank_key": None,
            "account_deleted_at": deleted_at,
        }}
    )
    await db.report_audit_log.update_many(
        {"user_id": user_id},
        {"$set": {
            "user_id": None,
            "user_email": None,
            "username": "deleted_user",
            "account_deleted_at": deleted_at,
        }}
    )
    await db.votes.delete_many({"user_id": user_id})
    await db.validations.delete_many({"user_id": user_id})
    await db.report_votes.delete_many({"user_id": user_id})
    await db.flags.delete_many({"user_id": user_id})
    await db.notifications.delete_many({"user_id": user_id})
    await db.push_subscriptions.delete_many({"user_id": user_id})
    await db.saved_locations.delete_many({"user_id": user_object_id})
    await db.feedback.delete_many({"user_id": user_id})
    await db.subscription_receipts.delete_many({"user_id": user_object_id})
    await db.users.delete_one({"_id": user_object_id})

    response.delete_cookie(key="access_token", path="/", secure=True, samesite="none")
    response.delete_cookie(key="refresh_token", path="/", secure=True, samesite="none")
    logger.info("Deleted account for user_id=%s email=%s", user_id, user.get("email"))
    return {"message": "Cuenta eliminada correctamente", "deleted": True}

@api_router.post("/users/subscribe")
async def subscribe_user(request: Request):
    """Subscription: €3.99/month or €29.99/year with 7-day free trial."""
    if is_production_env():
        raise HTTPException(status_code=403, detail="Las suscripciones directas de prueba no están disponibles en producción")
    user = await require_auth(request)
    body = await request.json()
    plan = body.get("plan", "monthly")

    # Check if eligible for free trial
    has_used_trial = user.get("trial_used", False)
    trial_active = False

    if not has_used_trial and not user.get("subscription_active"):
        trial_end = datetime.now(timezone.utc) + timedelta(days=7)
        await db.users.update_one(
            {"_id": ObjectId(user["_id"])},
            {"$set": {
                "subscription_active": True,
                "subscription_type": plan,
                "subscription_expires": trial_end.isoformat(),
                "subscription_store": "trial",
                "trial_used": True,
                "trial_end": trial_end.isoformat()
            }}
        )
        return {"message": "Prueba gratuita de 7 días activada", "plan": plan, "trial": True, "expires": trial_end.isoformat()}

    expires = datetime.now(timezone.utc) + (timedelta(days=30) if plan == "monthly" else timedelta(days=365))

    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "subscription_active": True,
            "subscription_type": plan,
            "subscription_expires": expires.isoformat(),
            "subscription_store": "mock"
        }}
    )
    return {"message": "Suscripción activada", "plan": plan, "expires": expires.isoformat(), "mock": True}

@api_router.post("/users/subscribe/apple")
async def subscribe_via_apple(data: AppleReceiptVerify, request: Request):
    """Verify Apple App Store receipt and activate subscription."""
    user = await require_auth(request)
    
    result = await verify_apple_receipt(data.receipt_data, data.transaction_id)
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=f"Verificación de recibo Apple fallida: {result.get('error', 'Unknown')}")
    
    expires = result.get("expires") or (datetime.now(timezone.utc) + (timedelta(days=30) if data.plan == "monthly" else timedelta(days=365))).isoformat()
    
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "subscription_active": True,
            "subscription_type": data.plan,
            "subscription_expires": expires,
            "subscription_store": "apple",
            "subscription_transaction_id": data.transaction_id,
            "subscription_mock": result.get("mock", False)
        }}
    )
    
    # Store receipt for audit
    await db.subscription_receipts.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["_id"],
        "store": "apple",
        "plan": data.plan,
        "transaction_id": data.transaction_id,
        "verification_result": {k: v for k, v in result.items() if k != "error"},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Suscripción Apple activada", "plan": data.plan, "expires": expires, "mock": result.get("mock", False)}

@api_router.post("/users/subscribe/google")
async def subscribe_via_google(data: GoogleReceiptVerify, request: Request):
    """Verify Google Play receipt and activate subscription."""
    user = await require_auth(request)
    
    result = await verify_google_receipt(data.purchase_token, data.subscription_id)
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=f"Verificación de recibo Google fallida: {result.get('error', 'Unknown')}")
    
    expires = result.get("expires") or (datetime.now(timezone.utc) + (timedelta(days=30) if data.plan == "monthly" else timedelta(days=365))).isoformat()
    
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "subscription_active": True,
            "subscription_type": data.plan,
            "subscription_expires": expires,
            "subscription_store": "google",
            "subscription_purchase_token": data.purchase_token,
            "subscription_mock": result.get("mock", False)
        }}
    )
    
    await db.subscription_receipts.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["_id"],
        "store": "google",
        "plan": data.plan,
        "purchase_token": data.purchase_token,
        "subscription_id": data.subscription_id,
        "verification_result": {k: v for k, v in result.items() if k != "error"},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Suscripción Google activada", "plan": data.plan, "expires": expires, "mock": result.get("mock", False)}

@api_router.get("/users/subscription-status")
async def get_subscription_status(request: Request):
    """Check current subscription status."""
    user = await require_auth(request)
    
    return {
        "active": user.get("subscription_active", False),
        "type": user.get("subscription_type"),
        "expires": user.get("subscription_expires"),
        "store": user.get("subscription_store"),
        "mock": user.get("subscription_mock", False)
    }

# ==================== REPORTS ====================

PUBLIC_REGISTERED_USER_LABEL = "registered_user"
PUBLIC_UNRANKED_LABEL = "unranked"
PUBLIC_REPORT_COORDINATE_PRECISION = 4
PUBLIC_ANONYMOUS_REPORTER_NAMES = {"", "Anónimo", "Anonymous", "Anonym", "Anoniem", "Anonim"}


def sanitize_public_report_identity(report: dict) -> dict:
    sanitized = dict(report)
    contributor_name = str(sanitized.get("contributor_name") or "").strip()
    has_registered_identity = bool(
        sanitized.get("user_id")
        or sanitized.get("contributor_rank")
        or contributor_name not in PUBLIC_ANONYMOUS_REPORTER_NAMES
    )
    if has_registered_identity:
        sanitized["contributor_name"] = PUBLIC_REGISTERED_USER_LABEL
    elif not sanitized.get("contributor_name"):
        sanitized["contributor_name"] = "Anónimo"
        sanitized["contributor_rank"] = None
        sanitized["contributor_rank_key"] = None
    return sanitized


def can_view_exact_report_coordinates(user: Optional[dict]) -> bool:
    if not user:
        return False
    if user.get("role") in {"admin", "municipality"}:
        return True
    return get_account_type(user) == "municipal_worker"


def is_report_photo_approved(report: dict) -> bool:
    if not report.get("photo_url"):
        return False
    return report.get("photo_status") in {None, "approved"}


def can_view_report_photo(user: Optional[dict], report: dict) -> bool:
    if not report.get("photo_url"):
        return False
    if user and user.get("role") == "admin":
        return True
    return is_report_photo_approved(report)


def strip_unapproved_report_photo(report: dict) -> dict:
    sanitized = dict(report)
    if sanitized.get("photo_url") and not is_report_photo_approved(sanitized):
        sanitized["photo_url"] = None
    return sanitized


def apply_public_report_privacy(report: dict, viewer: Optional[dict]) -> dict:
    sanitized = sanitize_public_report_identity(report)
    viewer_is_authenticated = bool(viewer)
    if not can_view_exact_report_coordinates(viewer):
        if sanitized.get("latitude") is not None:
            sanitized["latitude"] = round(float(sanitized["latitude"]), PUBLIC_REPORT_COORDINATE_PRECISION)
        if sanitized.get("longitude") is not None:
            sanitized["longitude"] = round(float(sanitized["longitude"]), PUBLIC_REPORT_COORDINATE_PRECISION)
        sanitized["coordinates_hidden"] = True
    else:
        sanitized["coordinates_hidden"] = False

    if not can_view_report_photo(viewer, report):
        sanitized["photo_url"] = None

    if not viewer_is_authenticated:
        sanitized.pop("user_id", None)
    return sanitized


async def apply_current_public_report_ranks(reports: list[dict]) -> list[dict]:
    user_ids = list({report.get("user_id") for report in reports if report.get("user_id")})
    if not user_ids:
        return reports

    users = await db.users.find(
        {"_id": {"$in": user_ids}},
        {"_id": 1, "subscription_active": 1, "rank": 1, "rank_key": 1},
    ).to_list(len(user_ids))
    user_map = {user["_id"]: user for user in users}

    for report in reports:
        user = user_map.get(report.get("user_id"))
        if not user:
            report["contributor_rank"] = PUBLIC_UNRANKED_LABEL
            report["contributor_rank_key"] = PUBLIC_UNRANKED_LABEL
            continue
        if user.get("subscription_active"):
            report["contributor_rank"] = user.get("rank", DEFAULT_RANK_NAME)
            report["contributor_rank_key"] = user.get("rank_key", get_rank_key(report["contributor_rank"]))
        else:
            report["contributor_rank"] = PUBLIC_UNRANKED_LABEL
            report["contributor_rank_key"] = PUBLIC_UNRANKED_LABEL
    return reports

@api_router.get("/reports")
async def get_reports(
    request: Request,
    municipality: Optional[str] = None,
    category: Optional[str] = None,
    freshness: Optional[str] = None,
    status: Optional[str] = None,
    confirmed_only: Optional[bool] = None
):
    await archive_expired_reports()
    viewer = await get_current_user(request)
    query = build_active_report_filter()
    if municipality:
        query["municipality"] = municipality
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    if confirmed_only:
        query["status"] = "verified"

    reports = await db.reports.find(query, {
        "_id": 0, "id": 1, "latitude": 1, "longitude": 1, "category": 1,
        "status": 1, "created_at": 1, "refreshed_at": 1, "upvotes": 1, "downvotes": 1,
        "contributor_name": 1, "contributor_rank": 1, "contributor_rank_key": 1, "municipality": 1,
        "province": 1, "description": 1, "photo_url": 1, "barrio": 1,
        "photo_status": 1,
        "validation_count": 1, "confidence_score": 1, "flagged": 1, "archived": 1, "user_id": 1,
    }).to_list(2000)
    reports = await apply_current_public_report_ranks(reports)

    # Add freshness labels and confidence scores
    for index, report in enumerate(reports):
        r = apply_public_report_privacy(report, viewer)
        r["freshness"] = get_freshness_label(r.get("created_at", ""), r.get("refreshed_at"))
        r["confidence"] = calc_confidence_score(r)
        r["is_premium_report"] = r.get("contributor_rank") is not None
        reports[index] = r

    # Filter by freshness if requested
    if freshness:
        reports = [r for r in reports if r["freshness"] == freshness]

    return reports

@api_router.get("/reports/{report_id}")
async def get_report(report_id: str, request: Request):
    await archive_expired_reports()
    viewer = await get_current_user(request)
    report = await db.reports.find_one({"id": report_id, **build_active_report_filter()}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    [report] = await apply_current_public_report_ranks([report])
    report = apply_public_report_privacy(report, viewer)
    report["freshness"] = get_freshness_label(report.get("created_at", ""), report.get("refreshed_at"))
    report["confidence"] = calc_confidence_score(report)
    report["is_premium_report"] = report.get("contributor_rank") is not None
    return report

async def _create_report_impl(
    request: Request,
    user: dict,
    user_id: str,
    data: ReportCreate,
    *,
    source: str = "mobile_app",
):
    await validate_report_input(db, data, user, user_id)

    nearby_report = await check_proximity_duplicate(db, data.latitude, data.longitude)
    
    # If within 1 meter of an existing report, convert to a "still there" confirmation
    if nearby_report:
        existing_id = nearby_report["id"]
        # Check if user already confirmed this report
        existing_vote = await db.votes.find_one({"report_id": existing_id, "user_id": user_id})
        if not existing_vote:
            await db.votes.insert_one({
                "report_id": existing_id, "user_id": user_id,
                "vote_type": "still_there",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            await db.reports.update_one(
                {"id": existing_id},
                {
                    "$inc": {"still_there_count": 1, "validation_count": 1, "status_score": 1},
                    "$set": {"refreshed_at": datetime.now(timezone.utc).isoformat()},
                }
            )
        # Award reduced points for confirmation
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"vote_count": 1, "total_score": 5}}
        )
        # Return the confirmed report
        confirmed = await db.reports.find_one({"id": existing_id}, {"_id": 0})
        if confirmed:
            confirmed["freshness"] = get_freshness_label(confirmed.get("created_at", ""), confirmed.get("refreshed_at"))
            confirmed["converted_to_confirmation"] = True
            confirmed["points_earned"] = 5
            confirmed["points_breakdown"] = {"confirmation": 5}
            await audit_report_event(
                request,
                "report_converted_to_confirmation",
                user,
                report_id=existing_id,
                latitude=data.latitude,
                longitude=data.longitude,
                municipality=confirmed.get("municipality"),
                province=confirmed.get("province"),
                metadata={"points_earned": 5, "source": source},
            )
            return confirmed
        # Fallback — shouldn't happen but create normally if report vanished
    
    geo = await reverse_geocode_async(data.latitude, data.longitude)
    report_id = str(uuid.uuid4())

    report_doc = build_report_doc(report_id, data, user_id, user, geo, False)
    report_doc["submission_source"] = source
    await db.reports.insert_one(report_doc)

    await audit_report_event(
        request,
        "report_created",
        user,
        report_id=report_id,
        latitude=data.latitude,
        longitude=data.longitude,
        municipality=geo.get("municipality"),
        province=geo.get("province"),
        metadata={"category": report_doc.get("category"), "source": source},
    )

    points_result = await process_report_scoring(db, user, user_id, data, False)
    await upsert_municipality(db, geo)

    report_doc.pop("_id", None)
    report_doc["points_earned"] = points_result["points"]
    report_doc["points_breakdown"] = points_result["breakdown"]

    asyncio.create_task(notify_nearby_users(db, data.latitude, data.longitude, report_id, geo["municipality"]))
    return report_doc

@api_router.post("/reports")
async def create_report(request: Request, data: ReportCreate, response: Response):
    user = await require_registered(request)
    user_id = user["_id"]
    return await _create_report_impl(request, user, user_id, data, source="mobile_app")

@api_router.post("/reports/quick")
async def create_quick_report(request: Request, data: QuickReportCreate):
    user = await require_registered(request)
    user_id = user["_id"]
    report_data = ReportCreate(
        latitude=data.latitude,
        longitude=data.longitude,
        description=data.description,
        category="dog_feces",
    )
    return await _create_report_impl(
        request,
        user,
        user_id,
        report_data,
        source=(data.source or "watch_companion"),
    )

# ==================== REPORT HELPERS ====================

def resolve_runtime_commit() -> str:
    env_commit = (
        os.environ.get("GIT_SHA")
        or os.environ.get("RENDER_GIT_COMMIT")
        or os.environ.get("RAILWAY_GIT_COMMIT_SHA")
    )
    if env_commit:
        return env_commit

    repo_root = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
        commit = result.stdout.strip()
        if commit:
            return commit
    except Exception:
        pass

    return "unknown"

def get_runtime_metadata() -> dict:
    app_versions = load_app_versions()
    return {
        "environment": APP_ENV,
        "mongo_is_local": is_mongo_local(),
        "commit": resolve_runtime_commit(),
        "started_at": app.state.started_at,
        "backend_version": os.environ.get("BACKEND_VERSION") or app_versions.get("backend", "unknown"),
        "app_versions": app_versions,
    }


def get_request_context(request: Request) -> dict:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else None)
    return {
        "client_ip": client_ip,
        "user_agent": request.headers.get("user-agent"),
        "origin": request.headers.get("origin"),
        "referer": request.headers.get("referer"),
        "app_version": request.headers.get("x-app-version") or request.headers.get("x-caca-radar-version"),
        "app_environment": request.headers.get("x-app-environment"),
        "platform": request.headers.get("x-platform") or request.headers.get("sec-ch-ua-platform"),
        "native_app": request.headers.get("x-native-app"),
        "api_base_url": str(request.base_url).rstrip("/"),
    }


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


async def enforce_rate_limit(
    *,
    key: str,
    max_attempts: int,
    window_seconds: int,
    detail: str,
    status_code: int = 429,
) -> None:
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(seconds=window_seconds)).isoformat()
    record = await db.security_rate_limits.find_one({"key": key})

    if record:
        started_at = _parse_iso_datetime(record.get("window_started_at"))
        count = int(record.get("count", 0))
        if started_at and (now - started_at) < timedelta(seconds=window_seconds):
            if count >= max_attempts:
                raise HTTPException(status_code=status_code, detail=detail)
            await db.security_rate_limits.update_one(
                {"key": key},
                {"$set": {"last_attempt_at": now.isoformat(), "expires_at": expires_at}, "$inc": {"count": 1}},
            )
            return

    await db.security_rate_limits.update_one(
        {"key": key},
        {
            "$set": {
                "window_started_at": now.isoformat(),
                "last_attempt_at": now.isoformat(),
                "expires_at": expires_at,
                "count": 1,
            }
        },
        upsert=True,
    )


async def clear_rate_limits(keys: list[str]) -> None:
    if not keys:
        return
    await db.security_rate_limits.delete_many({"key": {"$in": keys}})


async def audit_report_event(
    request: Request,
    event: str,
    user: dict,
    report_id: str,
    latitude: float,
    longitude: float,
    municipality: Optional[str] = None,
    province: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """Write a second, append-only trace for report creation events."""
    try:
        await db.report_audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "event": event,
            "report_id": report_id,
            "user_id": user.get("_id") if user else None,
            "user_email": user.get("email") if user else None,
            "username": user.get("username") if user else None,
            "latitude": latitude,
            "longitude": longitude,
            "municipality": municipality,
            "province": province,
            "metadata": metadata or {},
            "request": get_request_context(request),
            "runtime": get_runtime_metadata(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Failed to write report audit log for {report_id}: {e}")

async def validate_report_input(db, data: ReportCreate, user: dict, user_id: str) -> None:
    """Validate anti-spam rules before creating a report."""
    if not await check_gps_plausible(data.latitude, data.longitude):
        raise HTTPException(status_code=400, detail="Ubicación fuera de España")
    if user is not None and await check_cooldown(db, user_id):
        raise HTTPException(status_code=429, detail="Espera al menos 15 segundos entre reportes")
    # VIP users bypass trust restrictions
    if user is not None and not is_vip_email(user.get("email", "")):
        tier = get_trust_tier(user.get("trust_score", 50))
        if tier == "restricted":
            raise HTTPException(status_code=403, detail="Tu cuenta está restringida por comportamiento sospechoso")

def build_report_doc(report_id: str, data: ReportCreate, user_id: str, user: dict, geo: dict, is_duplicate: bool) -> dict:
    """Build the report document for insertion."""
    now = datetime.now(timezone.utc).isoformat()
    category = data.category if data.category in REPORT_CATEGORIES else "dog_feces"
    doc = {
        "id": report_id, "latitude": data.latitude, "longitude": data.longitude,
        "photo_url": None, "description": data.description, "category": category,
        "photo_status": "none", "photo_bonus_awarded": False,
        "created_at": now, "refreshed_at": now, "status": "verified",
        "status_score": 1, "still_there_count": 1, "cleaned_count": 0,
        "upvotes": 0, "downvotes": 0, "validation_count": 1,
        "user_id": user_id, "contributor_name": "Anónimo", "contributor_rank": None,
        "municipality": geo["municipality"], "province": geo["province"], "country": geo["country"],
        "barrio": geo.get("barrio", ""),
        "archived": False, "flagged": False, "flag_count": 0, "is_duplicate_proximity": is_duplicate
    }
    doc["contributor_name"] = user.get("username") or user.get("name", "Anónimo")
    if user and user.get("subscription_active"):
        doc["contributor_rank"] = user.get("rank", DEFAULT_RANK_NAME)
        doc["contributor_rank_key"] = user.get("rank_key", get_rank_key(doc["contributor_rank"]))
    return doc

async def process_report_scoring(db, user: dict, user_id: str, data: ReportCreate, is_duplicate: bool) -> dict:
    """Calculate and apply points for a report submission."""
    if user is None or is_duplicate:
        return {"points": 0, "breakdown": {}}
    daily_count = user.get("daily_report_count", 0)
    is_sub = user.get("subscription_active", False)
    result = calc_report_points(has_photo=False, has_description=bool(data.description), daily_count=daily_count, is_subscriber=is_sub)
    hot = await is_hot_zone(db, data.latitude, data.longitude)
    if hot and result["points"] > 0:
        result["points"] += HOT_ZONE_BONUS
        result["breakdown"]["hot_zone"] = HOT_ZONE_BONUS
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"report_count": 1, "total_score": result["points"], "daily_report_count": 1}}
    )
    await update_streak(db, user_id)
    violations = await detect_spam_patterns(db, user_id)
    if violations:
        await update_trust_score(db, user_id, TRUST_SPAM_BEHAVIOR, f"spam_detected:{','.join(violations)}")
    # Check badges
    await check_and_award_badges(db, user_id)
    return result

async def upsert_municipality(db, geo: dict) -> None:
    """Ensure municipality exists and increment report count."""
    existing = await db.municipalities.find_one({"name": geo["municipality"], "province": geo["province"]})
    if not existing:
        await db.municipalities.insert_one({
            "id": str(uuid.uuid4()), "name": geo["municipality"],
            "province": geo["province"], "country": geo["country"],
            "report_count": 1, "created_at": datetime.now(timezone.utc).isoformat()
        })
    else:
        await db.municipalities.update_one(
            {"name": geo["municipality"], "province": geo["province"]}, {"$inc": {"report_count": 1}}
        )

# ==================== ANALYTICS HELPERS ====================

async def calc_analytics_summary(db, muni_name: str, now, thirty_days_ago: str, sixty_days_ago: str) -> dict:
    reports_30d = await db.reports.count_documents({"municipality": muni_name, "created_at": {"$gte": thirty_days_ago}})
    reports_prev = await db.reports.count_documents({"municipality": muni_name, "created_at": {"$gte": sixty_days_ago, "$lt": thirty_days_ago}})
    trend = round(((reports_30d - reports_prev) / max(reports_prev, 1)) * 100) if reports_prev > 0 else 0
    active = await db.reports.count_documents({"municipality": muni_name, "archived": {"$ne": True}, "flagged": {"$ne": True}})
    total = await db.reports.count_documents({"municipality": muni_name})
    flagged = await db.reports.count_documents({"municipality": muni_name, "flagged": True})
    flag_rate = round((flagged / max(total, 1)) * 100, 1)
    archived = await db.reports.find(
        {"municipality": muni_name, "archived": True, "created_at": {"$gte": thirty_days_ago}},
        {"_id": 0, "created_at": 1, "moderated_at": 1}
    ).to_list(100)
    hours = []
    for r in archived:
        if r.get("moderated_at"):
            try:
                h = (datetime.fromisoformat(r["moderated_at"]) - datetime.fromisoformat(r["created_at"])).total_seconds() / 3600
                if h > 0:
                    hours.append(h)
            except Exception:
                pass
    avg_res = round(sum(hours) / len(hours), 1) if hours else None
    return {"reports_30d": reports_30d, "reports_trend": trend, "active": active, "avg_resolution_hours": avg_res, "flag_rate": flag_rate}

async def calc_daily_reports(db, muni_name: str, now) -> list:
    result = []
    for i in range(30):
        day = (now - timedelta(days=29 - i)).date()
        count = await db.reports.count_documents({
            "municipality": muni_name, "created_at": {"$gte": day.isoformat(), "$lt": (day + timedelta(days=1)).isoformat()}
        })
        result.append({"date": day.strftime("%d/%m"), "count": count})
    return result

async def calc_hourly_distribution(db, muni_name: str, thirty_days_ago: str) -> list:
    all_reports = await db.reports.find(
        {"municipality": muni_name, "created_at": {"$gte": thirty_days_ago}}, {"_id": 0, "created_at": 1}
    ).to_list(2000)
    hourly = [0] * 24
    for r in all_reports:
        try:
            hourly[datetime.fromisoformat(r["created_at"]).hour] += 1
        except Exception:
            pass
    return [{"hour": f"{h:02d}:00", "count": hourly[h]} for h in range(24)]

async def calc_status_distribution(db, muni_name: str) -> list:
    labels = {"active": "Activo", "flagged": "Marcado", "archived": "Archivado"}
    result = []
    active = await db.reports.count_documents({"municipality": muni_name, "archived": {"$ne": True}, "flagged": {"$ne": True}})
    if active > 0:
        result.append({"status": labels["active"], "count": active})
    flagged = await db.reports.count_documents({"municipality": muni_name, "flagged": True})
    if flagged > 0:
        result.append({"status": labels["flagged"], "count": flagged})
    archived = await db.reports.count_documents({"municipality": muni_name, "archived": True})
    if archived > 0:
        result.append({"status": labels["archived"], "count": archived})
    return result

async def calc_top_zones(db, muni_name: str, thirty_days_ago: str) -> list:
    reports = await db.reports.find(
        {"municipality": muni_name, "created_at": {"$gte": thirty_days_ago}}, {"_id": 0, "latitude": 1, "longitude": 1}
    ).to_list(2000)
    zone_map = {}
    for r in reports:
        key = f"{round(r['latitude'], 3)},{round(r['longitude'], 3)}"
        zone_map[key] = zone_map.get(key, 0) + 1
    top = sorted(zone_map.items(), key=lambda x: -x[1])[:10]
    return [{"area": f"Zona {k}", "count": v} for k, v in top]


def _report_photo_format_candidates() -> list[tuple[str, str, str, dict]]:
    candidates: list[tuple[str, str, str, dict]] = []
    if Image is not None:
        try:
            Image.init()
        except Exception:
            pass

    avif_supported = False
    webp_supported = False
    try:
        avif_supported = bool(pillow_features and pillow_features.check("avif"))
    except Exception:
        avif_supported = False
    try:
        webp_supported = bool(pillow_features and pillow_features.check("webp"))
    except Exception:
        webp_supported = False

    if avif_supported:
        candidates.append(("AVIF", "image/avif", "avif", {"quality": 52, "speed": 6}))
    if webp_supported:
        candidates.append(("WEBP", "image/webp", "webp", {"quality": 78, "method": 6}))
    candidates.append(("JPEG", "image/jpeg", "jpg", {"quality": 82, "optimize": True}))
    return candidates


def normalize_report_photo_for_storage(
    data: bytes,
    original_filename: str | None = None,
    original_content_type: str | None = None,
) -> tuple[bytes, str, str]:
    if Image is None or ImageOps is None:
        ext = (original_filename or "report-photo.jpg").rsplit(".", 1)[-1].lower() if original_filename else "jpg"
        return data, (original_content_type or "image/jpeg"), ext

    try:
        with Image.open(io.BytesIO(data)) as opened:
            try:
                opened.seek(0)
            except Exception:
                pass

            image = ImageOps.exif_transpose(opened)

            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                rgba_image = image.convert("RGBA")
                flattened = Image.new("RGB", image.size, (255, 255, 255))
                flattened.paste(rgba_image, mask=rgba_image.getchannel("A"))
                normalized = flattened
            elif image.mode != "RGB":
                normalized = image.convert("RGB")
            else:
                normalized = image.copy()
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Archivo de imagen no válido") from exc
    except Exception as exc:
        logger.exception("Failed to parse uploaded report photo")
        raise HTTPException(status_code=400, detail="No hemos podido procesar la imagen") from exc

    try:
        longest_side = max(normalized.size)
        if longest_side > REPORT_PHOTO_STORAGE_MAX_SIDE:
            normalized.thumbnail((REPORT_PHOTO_STORAGE_MAX_SIDE, REPORT_PHOTO_STORAGE_MAX_SIDE), Image.Resampling.LANCZOS)

        for fmt, content_type, ext, save_kwargs in _report_photo_format_candidates():
            buffer = io.BytesIO()
            try:
                normalized.save(buffer, format=fmt, **save_kwargs)
                return buffer.getvalue(), content_type, ext
            except OSError:
                continue
    finally:
        normalized.close()

    raise HTTPException(status_code=500, detail="No hemos podido convertir la imagen")

@api_router.post("/reports/{report_id}/photo")
async def upload_photo(report_id: str, request: Request, file: UploadFile = File(...)):
    user = await require_registered(request)

    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (max 5MB)")

    normalized_data, normalized_content_type, ext = normalize_report_photo_for_storage(
        data,
        original_filename=file.filename,
        original_content_type=file.content_type,
    )
    path = f"{APP_NAME}/reports/{report_id}/{uuid.uuid4()}.{ext}"

    result = await put_object_async(path, normalized_data, normalized_content_type)
    
    await db.reports.update_one(
        {"id": report_id},
        {"$set": {
            "photo_url": result["path"],
            "photo_status": "pending",
            "photo_submitted_at": datetime.now(timezone.utc).isoformat(),
            "photo_reviewed_at": None,
            "photo_reviewed_by": None,
            "photo_bonus_awarded": False,
        }},
    )

    return {"photo_url": result["path"], "photo_status": "pending"}

@api_router.get("/files/{path:path}")
async def get_file(path: str, request: Request):
    if path.startswith(f"{APP_NAME}/reports/"):
        report = await db.reports.find_one({"photo_url": path}, {"_id": 0, "id": 1, "photo_status": 1})
        if not report:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")

        viewer = await get_current_user(request)
        if report.get("photo_status") == "pending":
            if not viewer or viewer.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Foto pendiente de revisión")
    try:
        data, content_type = await get_object_async(path)
        return Response(content=data, media_type=content_type)
    except Exception as e:
        logger.error(f"Error getting file: {e}")
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

# ==================== VOTES ====================

@api_router.post("/reports/{report_id}/vote")
async def vote_report(report_id: str, data: VoteCreate, request: Request, response: Response):
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id

    if data.vote_type != "cleaned":
        raise HTTPException(status_code=400, detail={"code": "still_there_removed"})

    distance_meters = None
    if not can_clear_report_without_proximity(user, report):
        distance_meters = require_report_proximity(report, data.latitude, data.longitude)

    existing_vote = await db.votes.find_one({"report_id": report_id, "user_id": user_id})
    if existing_vote:
        raise HTTPException(status_code=400, detail="Ya has votado en este reporte")
    
    vote_doc = {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "user_id": user_id,
        "vote_type": data.vote_type,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "distance_meters": distance_meters,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.votes.insert_one(vote_doc)

    await db.reports.update_one({"id": report_id}, {"$inc": {"cleaned_count": 1, "status_score": -1}})
    
    # Increment user vote count
    if user:
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"vote_count": 1}})
    
    # Auto-archive once the report is treated as cleared/cleaned up
    updated_report = await db.reports.find_one({"id": report_id})
    if updated_report.get("cleaned_count", 0) >= REPORT_CLEARED_VOTES_NEEDED:
        await db.reports.update_one({"id": report_id}, {"$set": {"archived": True, "status": "archived"}})
    
    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=True, samesite="none", max_age=86400*365, path="/")
    
    response_payload = {"message": "Voto registrado", "vote_type": data.vote_type}
    if distance_meters is not None:
        response_payload["distance_meters"] = round(distance_meters, 1)
    if user and can_clear_report_without_proximity(user, report):
        response_payload["municipal_override"] = True
    return response_payload

@api_router.get("/reports/{report_id}/my-vote")
async def get_my_vote(report_id: str, request: Request):
    user = await get_current_user(request)
    anon_id = request.cookies.get("anon_id")
    user_id = user["_id"] if user else anon_id
    if not user_id:
        return {"vote": None}
    vote = await db.votes.find_one({"report_id": report_id, "user_id": user_id}, {"_id": 0})
    return {"vote": vote}


# ==================== VALIDATION ====================

@api_router.post("/reports/{report_id}/validate")
async def validate_report(report_id: str, data: ValidationCreate, request: Request, response: Response):
    """Validate a report (confirm/reject). Triggers consensus check."""
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    distance_meters = require_report_proximity(report, data.latitude, data.longitude)

    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id

    # Can't validate own report
    if report.get("user_id") == user_id:
        raise HTTPException(status_code=400, detail="No puedes validar tu propio reporte")

    # Check if already validated
    existing = await db.validations.find_one({"report_id": report_id, "user_id": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Ya has validado este reporte")

    is_sub = user.get("subscription_active", False) if user else False
    result = await process_validation(
        db,
        report_id,
        user_id,
        data.vote,
        is_sub,
        latitude=data.latitude,
        longitude=data.longitude,
        distance_meters=distance_meters,
    )

    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=True, samesite="none", max_age=86400*365, path="/")

    return result

@api_router.get("/reports/{report_id}/my-validation")
async def get_my_validation(report_id: str, request: Request):
    user = await get_current_user(request)
    anon_id = request.cookies.get("anon_id")
    user_id = user["_id"] if user else anon_id
    if not user_id:
        return {"validation": None}
    val = await db.validations.find_one({"report_id": report_id, "user_id": user_id}, {"_id": 0})
    return {"validation": val}

@api_router.get("/reports/{report_id}/my-report-vote")
async def get_my_report_vote(report_id: str, request: Request):
    user = await get_current_user(request)
    anon_id = request.cookies.get("anon_id")
    user_id = user["_id"] if user else anon_id
    if not user_id:
        return {"vote": None}
    vote = await db.report_votes.find_one({"report_id": report_id, "user_id": user_id}, {"_id": 0})
    return {"vote": vote}

# ==================== UPVOTE / DOWNVOTE ====================

@api_router.post("/reports/{report_id}/upvote")
async def upvote_report(report_id: str, request: Request, response: Response):
    return await _handle_report_vote(report_id, "upvote", request, response)

@api_router.post("/reports/{report_id}/downvote")
async def downvote_report(report_id: str, request: Request, response: Response):
    return await _handle_report_vote(report_id, "downvote", request, response)

async def _handle_report_vote(report_id: str, vote_type: str, request: Request, response: Response):
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    try:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
    except Exception:
        body = {}

    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id

    if vote_type == "upvote" and report.get("user_id") == user_id:
        raise HTTPException(status_code=400, detail="No puedes votar tu propio reporte")

    # Check existing vote
    existing = await db.report_votes.find_one({"report_id": report_id, "user_id": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Ya has votado en este reporte")

    latitude = body.get("latitude")
    longitude = body.get("longitude")
    distance_meters = None
    bypass_proximity = can_clear_report_without_proximity(user, report)

    if vote_type == "downvote":
        if not bypass_proximity:
            if latitude is None or longitude is None:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "location_required",
                        "max_meters": ACTION_PROXIMITY_METERS,
                    },
                )
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Coordenadas inválidas")
            distance_meters = require_report_proximity(report, latitude, longitude)
        else:
            if latitude is not None and longitude is not None:
                try:
                    latitude = float(latitude)
                    longitude = float(longitude)
                except (TypeError, ValueError):
                    latitude = None
                    longitude = None

    report_vote_doc = {
        "id": str(uuid.uuid4()), "report_id": report_id, "user_id": user_id,
        "vote_type": vote_type, "created_at": datetime.now(timezone.utc).isoformat()
    }
    if latitude is not None and longitude is not None:
        report_vote_doc["latitude"] = latitude
        report_vote_doc["longitude"] = longitude
    if distance_meters is not None:
        report_vote_doc["distance_meters"] = distance_meters
    await db.report_votes.insert_one(report_vote_doc)

    # Update report vote counts and treat downvotes as "no longer there" signals.
    report_updates = {"upvotes": 1} if vote_type == "upvote" else {"downvotes": 1, "cleaned_count": 1, "status_score": -1}
    update_doc = {"$inc": report_updates}
    if vote_type == "upvote":
        update_doc["$set"] = {"refreshed_at": datetime.now(timezone.utc).isoformat()}
    await db.reports.update_one({"id": report_id}, update_doc)

    # Award points to the reporter when the report receives an upvote.
    reporter_id = report.get("user_id", "")
    points = calc_vote_points(vote_type)
    updated_report = await db.reports.find_one({"id": report_id})
    try:
        reporter = await db.users.find_one({"_id": ObjectId(reporter_id)})
        if reporter:
            if points:
                await db.users.update_one({"_id": ObjectId(reporter_id)}, {"$inc": {"total_score": points}})
            # Trust score adjustments for heavy voting
            if updated_report:
                net = (updated_report.get("upvotes", 0) - updated_report.get("downvotes", 0))
                if net <= -5:
                    await update_trust_score(db, reporter_id, TRUST_DOWNVOTED_REPORT, "heavily_downvoted")
                elif net >= 10:
                    await update_trust_score(db, reporter_id, TRUST_UPVOTED_REPORT_MIN, "highly_upvoted")
    except Exception:
        pass

    cleared = False
    if vote_type == "downvote" and updated_report and updated_report.get("cleaned_count", 0) >= REPORT_CLEARED_VOTES_NEEDED:
        await db.reports.update_one({"id": report_id}, {"$set": {"archived": True, "status": "archived"}})
        updated_report = await db.reports.find_one({"id": report_id})
        cleared = True

    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=True, samesite="none", max_age=86400*365, path="/")

    return {
        "message": "Voto registrado",
        "vote_type": vote_type,
        "validation_synced": False,
        "consensus": None,
        "cleared": cleared,
        "cleaned_count": updated_report.get("cleaned_count", 0) if updated_report else report.get("cleaned_count", 0),
        **({"distance_meters": round(distance_meters, 1)} if distance_meters is not None else {}),
        **({"municipal_override": True} if bypass_proximity and vote_type == "downvote" else {}),
    }

# ==================== USER GAMIFICATION ====================

@api_router.get("/users/profile")
async def get_user_profile(request: Request):
    """Get full gamification profile for current user."""
    user = await require_auth(request)
    rank_info = await get_user_rank_info(db, user["_id"])
    tier = get_trust_tier(user.get("trust_score", 50))
    badges = get_user_badges(user)
    earned_badges = [b for b in badges if b["earned"]]

    # Accuracy rate
    user_reports = await db.reports.count_documents({"user_id": user["_id"]})
    verified_reports = await db.reports.count_documents({"user_id": user["_id"], "status": "verified"})
    accuracy = round((verified_reports / max(user_reports, 1)) * 100, 1)

    return {
        **rank_info, "trust_tier": tier,
        "username": user.get("username"), "name": user.get("name"),
        "auth_methods": normalize_auth_methods(user),
        "linked_accounts": {
            "password": bool(user.get("password_hash")),
            "google": bool((user.get("linked_providers") or {}).get("google")),
            "apple": bool((user.get("linked_providers") or {}).get("apple")),
        },
        "preferred_language": user.get("preferred_language"),
        "subscription_active": user.get("subscription_active", False),
        "badges": earned_badges,
        "badges_count": len(earned_badges),
        "accuracy_rate": accuracy,
        "impact_score": rank_info.get("total_score", 0) + (verified_reports * 5),
        "trial_used": user.get("trial_used", False)
    }

@api_router.get("/users/impact")
async def get_user_impact(request: Request):
    """Get Community Impact data — user's contribution map + stats."""
    user = await require_auth(request)
    user_id = user["_id"]

    # User's reports (all, including archived/cleaned)
    user_reports = await db.reports.find(
        {"user_id": user_id},
        {"_id": 0, "id": 1, "latitude": 1, "longitude": 1, "status": 1,
         "created_at": 1, "archived": 1, "cleaned_count": 1,
         "still_there_count": 1, "upvotes": 1, "downvotes": 1,
         "municipality": 1, "barrio": 1, "validation_count": 1}
    ).to_list(500)

    # User's votes/validations on OTHER people's reports
    user_votes = await db.votes.find({"user_id": user_id}, {"_id": 0, "report_id": 1}).to_list(500)
    user_validations = await db.validations.find({"user_id": user_id}, {"_id": 0, "report_id": 1}).to_list(500)
    voted_ids = {v["report_id"] for v in user_votes} | {v["report_id"] for v in user_validations}

    # Fetch those reports to show on map
    confirmed_reports = []
    if voted_ids:
        confirmed_reports = await db.reports.find(
            {"id": {"$in": list(voted_ids)}},
            {"_id": 0, "id": 1, "latitude": 1, "longitude": 1, "status": 1,
             "created_at": 1, "archived": 1, "municipality": 1}
        ).to_list(500)

    # Compute stats
    total_reports = len(user_reports)
    cleaned_reports = sum(1 for r in user_reports if r.get("archived") or r.get("cleaned_count", 0) >= REPORT_CLEARED_VOTES_NEEDED)
    active_reports = sum(1 for r in user_reports if not r.get("archived"))
    total_confirmations = len(voted_ids)
    total_upvotes_received = sum(r.get("upvotes", 0) for r in user_reports)

    # Unique municipalities and barrios helped
    municipalities = list({r.get("municipality", "") for r in user_reports if r.get("municipality")})
    barrios = list({r.get("barrio", "") for r in user_reports if r.get("barrio")})

    # Timeline: reports per month
    from collections import defaultdict
    monthly = defaultdict(int)
    for r in user_reports:
        try:
            month = r["created_at"][:7]  # "2026-04"
            monthly[month] += 1
        except Exception:
            pass
    timeline = [{"month": k, "count": v} for k, v in sorted(monthly.items())]

    # Impact score calculation
    impact_score = (total_reports * 10) + (cleaned_reports * 20) + (total_confirmations * 5) + (total_upvotes_received * 2)

    # Mark each report with its type for the map
    map_points = []
    for r in user_reports:
        is_cleaned = r.get("archived") or r.get("cleaned_count", 0) >= REPORT_CLEARED_VOTES_NEEDED
        map_points.append({
            "id": r["id"], "lat": r["latitude"], "lng": r["longitude"],
            "type": "cleaned" if is_cleaned else "active",
            "created_at": r.get("created_at", ""),
            "municipality": r.get("municipality", ""),
        })
    for r in confirmed_reports:
        map_points.append({
            "id": r["id"], "lat": r["latitude"], "lng": r["longitude"],
            "type": "confirmed",
            "created_at": r.get("created_at", ""),
            "municipality": r.get("municipality", ""),
        })

    return {
        "username": user.get("username") or user.get("name", "Usuario"),
        "rank": user.get("rank", DEFAULT_RANK_NAME),
        "rank_key": user.get("rank_key", get_rank_key(user.get("rank", DEFAULT_RANK_NAME))),
        "total_score": user.get("total_score", 0),
        "streak_days": user.get("streak_days", 0),
        "stats": {
            "total_reports": total_reports,
            "cleaned_reports": cleaned_reports,
            "active_reports": active_reports,
            "total_confirmations": total_confirmations,
            "upvotes_received": total_upvotes_received,
            "impact_score": impact_score,
            "municipalities_helped": len(municipalities),
            "barrios_helped": len(barrios),
        },
        "municipalities": municipalities[:10],
        "barrios": barrios[:20],
        "timeline": timeline,
        "map_points": map_points,
    }

@api_router.post("/admin/recalculate-ranks")
async def admin_recalculate_ranks(request: Request):
    """Admin endpoint to trigger rank recalculation."""
    user = await require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    count, rank_changes = await recalculate_all_ranks(db)
    # Store rank change notifications
    for rc in rank_changes:
        await db.notifications.insert_one({
            "user_id": rc["user_id"],
            "type": "rank_change",
            "old_rank": rc["old_rank"],
            "new_rank": rc["new_rank"],
            "old_rank_key": rc.get("old_rank_key"),
            "new_rank_key": rc.get("new_rank_key"),
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    return {"message": f"Ranks recalculated for {count} users, {len(rank_changes)} rank changes"}


# ==================== FLAGS ====================

@api_router.post("/reports/{report_id}/flag")
async def flag_report(report_id: str, data: FlagCreate, request: Request, response: Response):
    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    if data.reason not in FLAG_REASONS:
        raise HTTPException(status_code=400, detail="Motivo de reporte inválido")
    
    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id
    
    existing_flag = await db.flags.find_one({"report_id": report_id, "user_id": user_id})
    if existing_flag:
        raise HTTPException(status_code=400, detail="Ya has reportado esta publicación")
    
    flag_doc = {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "user_id": user_id,
        "reason": data.reason,
        "municipality": report.get("municipality", ""),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.flags.insert_one(flag_doc)
    
    flag_count = await db.flags.count_documents({"report_id": report_id})
    if flag_count >= 2:
        await db.reports.update_one({"id": report_id}, {"$set": {"flagged": True, "flag_count": flag_count}})
    else:
        await db.reports.update_one({"id": report_id}, {"$set": {"flag_count": flag_count}})
    
    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=True, samesite="none", max_age=86400*365, path="/")
    
    return {"message": "Reporte marcado"}

# ==================== CITY & BARRIO RANKINGS ====================

@api_router.get("/rankings/cities")
async def api_city_rankings(request: Request):
    """Get cleanest/dirtiest cities ranked by reports per 10k residents."""
    await archive_expired_reports()
    return await get_city_rankings(db)

@api_router.get("/rankings/cities/share")
async def api_city_rankings_share(list_type: str = "dirtiest"):
    """Public shareable city ranking data (top 10 only)."""
    await archive_expired_reports()
    data = await get_city_rankings(db, limit=10)
    cities = data.get(list_type, data["dirtiest"])[:10]
    title = "Las ciudades más sucias de España" if list_type == "dirtiest" else "Las ciudades más limpias de España"
    app_url = build_download_url("city-rankings", list_type=list_type)
    share_url = build_share_page_url("city-rankings", list_type=list_type)
    image_url = append_query_params(
        f"{get_frontend_url()}/api/rankings/cities/share-image.png?list_type={quote(list_type)}",
        v=get_share_image_version(),
    )
    return {
        "title": title,
        "cities": cities,
        "total_cities": data["total_cities"],
        "generated_at": data["generated_at"],
        "app_url": app_url,
        "share_url": share_url,
        "image_url": image_url,
        "download_links": {
            "ios": APP_STORE_URL,
            "android": PLAY_STORE_URL,
        },
        "share_text": f"{title} según Caca Radar. ¡Descarga la app y ayuda a mantener tu ciudad limpia! {APP_STORE_URL}",
    }


@api_router.get("/rankings/cities/share-image")
@api_router.get("/rankings/cities/share-image.png")
async def api_city_rankings_share_image(list_type: str = "dirtiest"):
    await archive_expired_reports()
    data = await get_city_rankings(db, limit=10)
    cities = data.get(list_type, data["dirtiest"])[:5]
    title = "Ciudades más sucias de España" if list_type == "dirtiest" else "Ciudades más limpias de España"
    subtitle = "¿Cuánta caca de perro hay en nuestras aceras?"
    rows = [
        {
            "rank": city.get("rank", index + 1),
            "label": city.get("city", ""),
            "meta": city.get("province", ""),
            "value": f'{city.get("reports_per_10k", 0)} / 10k',
        }
        for index, city in enumerate(cities)
    ]
    png = build_rankings_share_png(title, subtitle, rows, footer="Comparte y descarga Caca Radar")
    return build_share_image_response(png, {"kind": "city-rankings", "list_type": list_type})

@api_router.get("/rankings/barrios")
async def api_barrio_rankings(request: Request, city: str = "Madrid"):
    """Get barrio rankings within a city."""
    await archive_expired_reports()
    return await get_barrio_rankings(db, city)

@api_router.get("/rankings/barrios/share")
async def api_barrio_rankings_share(city: str = "Madrid"):
    """Public shareable barrio ranking data (top 10 only) for a city."""
    await archive_expired_reports()
    data = await get_barrio_rankings(db, city, limit=10)
    title = f"Los barrios con más avisos en {city}"
    app_url = build_download_url("barrio-rankings", city=city)
    share_url = build_share_page_url("barrio-rankings", city=city)
    image_url = append_query_params(
        f"{get_frontend_url()}/api/rankings/barrios/share-image.png?city={quote(city)}",
        v=get_share_image_version(),
    )
    return {
        "title": title,
        "city": city,
        "barrios": data.get("barrios", [])[:10],
        "total_reports": data.get("total_reports", 0),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "app_url": app_url,
        "share_url": share_url,
        "image_url": image_url,
        "download_links": {
            "ios": APP_STORE_URL,
            "android": PLAY_STORE_URL,
        },
        "share_text": (
            f"{title} según Caca Radar. "
            f"Consulta el ranking y ayuda a mantener tu barrio limpio. {APP_STORE_URL}"
        ),
    }


@api_router.get("/rankings/barrios/share-image")
@api_router.get("/rankings/barrios/share-image.png")
async def api_barrio_rankings_share_image(city: str = "Madrid"):
    await archive_expired_reports()
    data = await get_barrio_rankings(db, city, limit=10)
    barrios = data.get("barrios") or []
    if not barrios:
        png = build_rankings_share_png(
            f"Barrios con más avisos en {city}",
            "¿Cuánta caca de perro hay en nuestras aceras?",
            [],
            footer="Comparte y descarga Caca Radar",
        )
        return build_share_image_response(png, {"kind": "barrio-rankings", "city": city, "empty": True})

    rows = [
        {
            "rank": barrio_data.get("rank", index + 1),
            "label": barrio_data.get("barrio", ""),
            "meta": city,
            "value": f'{barrio_data.get("active_reports", 0)} avisos',
        }
        for index, barrio_data in enumerate(barrios[:4])
    ]
    png = build_rankings_share_png(
        f"Los barrios con más avisos en {city}",
        "¿Cuánta caca de perro hay en nuestras aceras?",
        rows,
        footer="Comparte y descarga Caca Radar",
    )
    return build_share_image_response(png, {"kind": "barrio-rankings", "city": city})


@api_router.get("/city-reports/cities")
async def api_city_report_cities(request: Request):
    """Premium: list cities with active reports for the city report feature."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")
    await archive_expired_reports()
    return await get_active_report_cities(db)


@api_router.get("/city-reports/barrios")
async def api_city_report_barrios(request: Request, city: str):
    """Premium: list barrios with active reports for a selected city."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")
    await archive_expired_reports()
    return await get_active_report_barrios(db, city)


@api_router.get("/city-reports")
async def api_city_report(request: Request, city: str, barrio: str | None = None):
    """Premium: city or barrio report summary with freshness buckets and preview points."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")
    await archive_expired_reports()
    summary = await get_city_report_summary(db, city, barrio=barrio)
    return {
        **summary,
        "display_label": f"{summary['city']} — {summary['barrio']}" if summary.get("barrio") else summary.get("city", city),
        "active_report_count": summary.get("total_active_reports", 0),
        "recent_report_count": summary.get("fresh_reports", 0),
        "fresh_count": summary.get("fresh_reports", 0),
        "old_count": summary.get("older_reports", 0),
        "fossil_count": summary.get("fossil_reports", 0),
        "time_window_label": "últimas 24 h",
        "has_data": summary.get("total_active_reports", 0) > 0,
    }


@api_router.get("/city-reports/share")
async def api_city_report_share(request: Request, city: str, barrio: str | None = None):
    """Authenticated city or barrio report summary."""
    await require_auth(request)
    await archive_expired_reports()
    data = await get_location_share_summary(db, city, barrio)
    if not data.get("has_data"):
        raise HTTPException(status_code=404, detail="Ciudad o barrio sin reportes activos")
    frontend_url = get_frontend_url()
    city_value = data["city"]
    barrio_value = data["barrio"] or None
    metadata = build_location_share_metadata(frontend_url, data, image_version=get_share_image_version())
    image_url = append_query_params(
        f"{frontend_url}/api/city-reports/share-image.png?city={quote(city_value)}" + (f"&barrio={quote(barrio_value)}" if barrio_value else ""),
        v=get_share_image_version(),
    )
    app_url = build_download_url("city-report", city=city_value, barrio=barrio_value)
    share_url = build_share_page_url("city-report", city=city_value, barrio=barrio_value)
    return {
        "city": data["city"],
        "barrio": data["barrio"],
        "city_slug": data["city_slug"],
        "barrio_slug": data["barrio_slug"],
        "display_label": data["display_label"],
        "active_report_count": data["active_report_count"],
        "total_active_reports": data["active_report_count"],
        "recent_report_count": data["recent_report_count"],
        "fresh_count": data["fresh_count"],
        "fresh_reports": data["fresh_count"],
        "old_count": data["old_count"],
        "older_reports": data["old_count"],
        "fossil_count": data["fossil_count"],
        "fossil_reports": data["fossil_count"],
        "preview_points": data["preview_points"],
        "map_bounds": data["map_bounds"],
        "time_window_label": data["time_window_label"],
        "title": metadata["title"],
        "description": metadata["description"],
        "app_url": app_url,
        "share_url": share_url,
        "image_url": image_url,
        "download_links": {
            "ios": APP_STORE_URL,
            "android": PLAY_STORE_URL,
        },
        "share_text": f"{data['display_label']}: {data['fresh_count']} frescos · {data['old_count']} antiguos · {data['fossil_count']} fósiles. {APP_STORE_URL}",
    }


@api_router.get("/city-reports/share-image")
@api_router.get("/city-reports/share-image.png")
async def api_city_report_share_image(request: Request, city: str, barrio: str | None = None):
    await archive_expired_reports()
    summary = await get_location_share_summary(db, city, barrio)
    if not summary.get("has_data"):
        png = build_rankings_share_png(
            f"Avisos activos en {city}",
            LOCATION_SHARE_COPY["headline"],
            [],
            footer="Comparte y descarga Caca Radar",
        )
        return build_share_image_response(png, {"kind": "city-report", "city": city, "barrio": barrio, "empty": True})

    png = build_barrio_snapshot_png(summary)
    return build_share_image_response(png, {"kind": "city-report", "city": city, "barrio": barrio, "generated_at": summary.get("generated_at")})


@api_router.get("/share-image/location")
@api_router.get("/share-image/location.png")
async def api_location_share_image(city: str, barrio: str | None = None):
    png = build_rankings_share_png(
        "Caca Radar",
        "Inicia sesión para ver reportes y paneles privados.",
        [],
        footer="Descarga Caca Radar",
    )
    return build_share_image_response(png, {"kind": "location-share-private", "city": city, "barrio": barrio})


@api_router.get("/share-image/location/{city_slug}")
@api_router.get("/share-image/location/{city_slug}.png")
async def api_location_share_image_city_slug(city_slug: str):
    return await api_location_share_image(city_slug, None)


@api_router.get("/share-image/location/{city_slug}/{barrio_slug}")
@api_router.get("/share-image/location/{city_slug}/{barrio_slug}.png")
async def api_location_share_image_barrio_slug(city_slug: str, barrio_slug: str):
    return await api_location_share_image(city_slug, barrio_slug)


@api_router.get("/share/location", response_class=HTMLResponse)
async def api_location_share_page(city: str, barrio: str | None = None):
    city_slug = slugify_location_segment(city)
    barrio_slug = slugify_location_segment(barrio or "") if barrio else None
    title = "Caca Radar"
    description = "Inicia sesión para ver reportes y paneles privados de Caca Radar."
    image_url = f"{get_frontend_url()}/share-example-es.png"
    share_url = build_location_share_url(city_slug, barrio_slug)
    redirect_url = build_location_download_url(city_slug, barrio_slug)
    headers = build_cache_headers({"city": city, "barrio": barrio, "private_reports": True})
    return HTMLResponse(
        render_share_page(
            title=title,
            description=description,
            image_url=image_url,
            share_url=share_url,
            redirect_url=redirect_url,
        ),
        headers=headers,
    )


@api_router.get("/share/location/{city_slug}", response_class=HTMLResponse)
async def api_location_share_page_city_slug(city_slug: str):
    return await api_location_share_page(city_slug, None)


@api_router.get("/share/location/{city_slug}/{barrio_slug}", response_class=HTMLResponse)
async def api_location_share_page_barrio_slug(city_slug: str, barrio_slug: str):
    return await api_location_share_page(city_slug, barrio_slug)


@api_router.get("/share", response_class=HTMLResponse)
async def api_public_share_page(
    kind: str,
    city: str | None = None,
    barrio: str | None = None,
    list_type: str | None = None,
    name: str | None = None,
    report_id: str | None = None,
):
    frontend_url = get_frontend_url()
    fallback_image = f"{frontend_url}/share-example-es.png"

    if kind == "city-rankings":
        data = await get_city_rankings(db, limit=10)
        selected = list_type or "dirtiest"
        title = "Las ciudades más sucias de España" if selected == "dirtiest" else "Las ciudades más limpias de España"
        description = f"{title} según Caca Radar. Descarga la app y ayuda a mantener tu ciudad limpia."
        image_url = append_query_params(
            f"{frontend_url}/api/rankings/cities/share-image.png?list_type={quote(selected)}",
            v=get_share_image_version(),
        )
        redirect_url = build_download_url("city-rankings", list_type=selected)
        share_url = build_share_page_url("city-rankings", list_type=selected)
        return HTMLResponse(render_share_page(title=title, description=description, image_url=image_url, share_url=share_url, redirect_url=redirect_url))

    if kind == "barrio-rankings":
        selected_city = city or "Madrid"
        title = f"Los barrios con más avisos en {selected_city}"
        description = f"{title} según Caca Radar. Consulta el ranking y ayuda a mantener tu barrio limpio."
        image_url = append_query_params(
            f"{frontend_url}/api/rankings/barrios/share-image.png?city={quote(selected_city)}",
            v=get_share_image_version(),
        )
        redirect_url = build_download_url("barrio-rankings", city=selected_city)
        share_url = build_share_page_url("barrio-rankings", city=selected_city)
        return HTMLResponse(render_share_page(title=title, description=description, image_url=image_url, share_url=share_url, redirect_url=redirect_url))

    if kind == "city-report":
        selected_city = city or "Madrid"
        title = "Caca Radar"
        description = "Inicia sesión para ver informes privados por ciudad o barrio."
        image_url = fallback_image
        redirect_url = build_download_url("city-report", city=selected_city, barrio=barrio)
        share_url = build_share_page_url("city-report", city=selected_city, barrio=barrio)
        return HTMLResponse(render_share_page(title=title, description=description, image_url=image_url, share_url=share_url, redirect_url=redirect_url))

    if kind == "profile":
        display_name = name or "Usuario"
        title = f"{display_name} en Caca Radar"
        description = f"Consulta el perfil compartido de {display_name} en Caca Radar."
        redirect_url = build_download_url("profile", name=display_name)
        share_url = build_share_page_url("profile", name=display_name)
        return HTMLResponse(render_share_page(title=title, description=description, image_url=fallback_image, share_url=share_url, redirect_url=redirect_url))

    if kind == "report" and report_id:
        municipality = city or "España"
        title = "Caca Radar"
        description = "Inicia sesión para ver reportes privados y colaborar con tu municipio."
        image_url = fallback_image
        redirect_url = build_download_url("report", report_id=report_id, city=municipality)
        share_url = build_share_page_url("report", report_id=report_id, city=municipality)
        return HTMLResponse(render_share_page(title=title, description=description, image_url=image_url, share_url=share_url, redirect_url=redirect_url))

    redirect_url = build_download_url("city-rankings", list_type="dirtiest")
    share_url = build_share_page_url("city-rankings", list_type="dirtiest")
    return HTMLResponse(
        render_share_page(
            title="Caca Radar",
            description="Descarga Caca Radar y ayuda a mantener las calles limpias.",
            image_url=fallback_image,
            share_url=share_url,
            redirect_url=redirect_url,
        )
    )

# ==================== NOTIFICATIONS ====================

@api_router.get("/notifications")
async def get_notifications(request: Request):
    """Get unread notifications for the current user."""
    user = await require_auth(request)
    user_id = user["_id"]
    notifications = await db.notifications.find(
        {"user_id": user_id, "read": False},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    return notifications

@api_router.post("/notifications/read")
async def mark_notifications_read(request: Request):
    """Mark all notifications as read."""
    user = await require_auth(request)
    await db.notifications.update_many(
        {"user_id": user["_id"], "read": False},
        {"$set": {"read": True}}
    )
    return {"message": "ok"}

# ==================== LEADERBOARDS ====================

@api_router.get("/leaderboard/national")
async def get_national_leaderboard(request: Request):
    """National leaderboard - subscriber only. Sorted by total_score."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")
    
    top_users = await db.users.find(
        {"role": "user", "total_score": {"$gt": 0}},
        {"_id": 0, "username": 1, "name": 1, "total_score": 1, "report_count": 1, "vote_count": 1,
         "rank": 1, "rank_key": 1, "level": 1, "trust_score": 1, "streak_days": 1, "subscription_active": 1}
    ).sort("total_score", -1).to_list(50)
    
    for i, u in enumerate(top_users):
        u["position"] = i + 1
        u["display_name"] = u.get("username") or u.get("name", "Anónimo")
        u["is_subscriber"] = u.get("subscription_active", False)
    
    return top_users

@api_router.get("/leaderboard/city/{municipality}")
async def get_city_leaderboard(municipality: str, request: Request):
    """Per-city leaderboard - subscriber only."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")
    
    # Get user IDs who have reports in this municipality
    pipeline = [
        {"$match": {"municipality": municipality}},
        {"$group": {"_id": "$user_id", "report_count": {"$sum": 1}}},
        {"$sort": {"report_count": -1}},
        {"$limit": 50}
    ]
    report_agg = await db.reports.aggregate(pipeline).to_list(50)
    
    # Get vote counts per user for this municipality
    vote_pipeline = [
        {"$lookup": {"from": "reports", "localField": "report_id", "foreignField": "id", "as": "report"}},
        {"$unwind": "$report"},
        {"$match": {"report.municipality": municipality}},
        {"$group": {"_id": "$user_id", "vote_count": {"$sum": 1}}}
    ]
    vote_agg = await db.votes.aggregate(vote_pipeline).to_list(100)
    vote_map = {v["_id"]: v["vote_count"] for v in vote_agg}
    
    results = []
    for i, entry in enumerate(report_agg):
        uid = entry["_id"]
        # Try to find user
        try:
            u = await db.users.find_one({"_id": ObjectId(uid)}, {"_id": 0, "username": 1, "name": 1})
        except Exception:
            u = None
        
        display_name = "Anónimo"
        if u:
            display_name = u.get("username") or u.get("name", "Anónimo")
        
        results.append({
            "rank": i + 1,
            "display_name": display_name,
            "report_count": entry["report_count"],
            "vote_count": vote_map.get(uid, 0),
            "total_score": entry["report_count"] + vote_map.get(uid, 0)
        })
    
    return results

@api_router.get("/leaderboard/cities")
async def get_city_list():
    """Get list of municipalities with reports for leaderboard navigation."""
    cities = await db.municipalities.find(
        {"report_count": {"$gt": 0}},
        {"_id": 0, "name": 1, "province": 1, "report_count": 1}
    ).sort("report_count", -1).to_list(100)
    return cities

# ==================== MUNICIPALITY DASHBOARD ====================

@api_router.post("/municipality/register")
async def register_municipality(data: MunicipalityRegister, response: Response):
    email = data.email.lower()
    
    # Validate email domain
    if not is_valid_municipality_email(email):
        raise HTTPException(status_code=400, detail="Debes usar un email oficial del ayuntamiento (no se permiten emails personales como Gmail, Hotmail, etc.)")
    
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Generate verification code
    verification_code = generate_verification_code()
    
    hashed = hash_password(data.password)
    user_doc = {
        "email": email,
        "password_hash": hashed,
        "name": data.name,
        "role": "municipality",
        "municipality_name": data.municipality_name,
        "municipality_province": data.province or "",
        "municipality_subscription_active": False,
        "municipality_subscription_type": None,
        "municipality_subscription_expires": None,
        "email_verified": False,
        "verification_code": verification_code,
        "verification_code_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Send verification email
    email_result = await send_verification_email(email, verification_code, data.municipality_name)
    logger.info("Municipality verification email dispatched for %s with status=%s", email, email_result.get("status"))
    
    return {
        "id": user_id, "email": email, "name": data.name,
        "role": "municipality", "municipality_name": data.municipality_name,
        "municipality_subscription_active": False,
        "verification_required": True,
    }

@api_router.post("/municipality/verify")
async def verify_municipality_email(data: MunicipalityVerify, request: Request):
    email = data.email.lower()
    context = get_request_context(request)
    client_ip = context.get("client_ip") or "unknown"
    generic_response = {"message": "Si los datos son correctos, el email quedará verificado.", "verified": False}

    await enforce_rate_limit(
        key=f"municipality_verify:ip:{client_ip}",
        max_attempts=15,
        window_seconds=3600,
        detail="Demasiados intentos. Inténtalo más tarde.",
    )
    await enforce_rate_limit(
        key=f"municipality_verify:email:{email}",
        max_attempts=8,
        window_seconds=3600,
        detail="Demasiados intentos. Inténtalo más tarde.",
    )

    user = await db.users.find_one({"email": email, "role": "municipality"})
    if not user:
        return generic_response

    if user.get("email_verified"):
        return generic_response

    # Check code
    if user.get("verification_code") != data.code:
        return generic_response

    # Check expiry
    expires = user.get("verification_code_expires", "")
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        return generic_response

    await db.users.update_one(
        {"email": email},
        {"$set": {"email_verified": True}, "$unset": {"verification_code": "", "verification_code_expires": ""}}
    )
    await clear_rate_limits([
        f"municipality_verify:ip:{client_ip}",
        f"municipality_verify:email:{email}",
        f"municipality_resend:email:{email}",
    ])
    return {"message": "Email verificado correctamente", "verified": True}

@api_router.post("/municipality/resend-verification")
async def resend_municipality_verification(data: MunicipalityResendVerification, request: Request):
    email = data.email.lower()
    context = get_request_context(request)
    client_ip = context.get("client_ip") or "unknown"
    generic_response = {"message": "Si el email puede recibir verificación, enviaremos un nuevo código."}

    await enforce_rate_limit(
        key=f"municipality_resend:ip:{client_ip}",
        max_attempts=10,
        window_seconds=3600,
        detail="Demasiadas solicitudes. Inténtalo más tarde.",
    )
    await enforce_rate_limit(
        key=f"municipality_resend:email:{email}",
        max_attempts=3,
        window_seconds=3600,
        detail="Demasiadas solicitudes. Inténtalo más tarde.",
    )

    user = await db.users.find_one({"email": email, "role": "municipality"})
    if not user:
        return generic_response

    if user.get("email_verified"):
        return generic_response

    # Generate new code
    new_code = generate_verification_code()
    await db.users.update_one(
        {"email": email},
        {"$set": {
            "verification_code": new_code,
            "verification_code_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }}
    )
    
    # Send verification email
    user_doc = await db.users.find_one({"email": email})
    muni_name = user_doc.get("municipality_name", "Municipio") if user_doc else "Municipio"
    result = await send_verification_email(email, new_code, muni_name)
    logger.info("Municipality verification email re-sent for %s with status=%s", email, result.get("status"))

    return generic_response

@api_router.post("/municipality/subscribe")
async def subscribe_municipality(request: Request):
    """Municipality subscription at €50/month."""
    if is_production_env():
        raise HTTPException(status_code=403, detail="La activación municipal manual no está disponible en producción sin validación interna")
    user = await require_municipality(request)
    await request.json()  # Accept body for future plan options
    
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "municipality_subscription_active": True,
            "municipality_subscription_type": "monthly",
            "municipality_subscription_price": 50.00,
            "municipality_subscription_expires": expires.isoformat()
        }}
    )
    return {"message": "Suscripción de municipio activada (€50/mes)", "plan": "monthly", "price": "€50/mes", "expires": expires.isoformat()}

def _build_municipality_report_query(muni_name: str, status: Optional[str] = None) -> dict:
    query = {"municipality": muni_name}
    if status == "active":
        query.update(build_active_report_filter())
    elif status == "flagged":
        query["flagged"] = True
    elif status == "archived":
        query["archived"] = True
    return query


async def _get_municipality_stats_data(muni_name: str) -> dict:
    total = await db.reports.count_documents({"municipality": muni_name})
    active = await db.reports.count_documents({"municipality": muni_name, **build_active_report_filter()})
    flagged = await db.reports.count_documents({"municipality": muni_name, "flagged": True})
    archived = await db.reports.count_documents({"municipality": muni_name, "archived": True})
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent = await db.reports.count_documents({"municipality": muni_name, "created_at": {"$gte": week_ago}})
    pending_flags = await db.flags.count_documents({"municipality": muni_name, "status": "pending"})
    return {
        "municipality": muni_name,
        "total_reports": total,
        "active_reports": active,
        "flagged_reports": flagged,
        "archived_reports": archived,
        "recent_reports_7d": recent,
        "pending_flags": pending_flags,
    }


async def _get_municipality_map_data(muni_name: str) -> dict:
    reports = await db.reports.find(
        {"municipality": muni_name},
        {"_id": 0, "id": 1, "latitude": 1, "longitude": 1, "archived": 1, "flagged": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(1000)

    points = []
    lats = []
    lngs = []
    for report in reports:
        lat = report.get("latitude")
        lng = report.get("longitude")
        if lat is None or lng is None:
            continue
        lats.append(lat)
        lngs.append(lng)
        if report.get("archived"):
            marker_type = "archived"
        elif report.get("flagged"):
            marker_type = "flagged"
        else:
            marker_type = "active"
        points.append({
            "id": report.get("id"),
            "lat": lat,
            "lng": lng,
            "type": marker_type,
            "created_at": report.get("created_at"),
        })

    bounds = None
    if lats and lngs:
        bounds = {
            "south": min(lats),
            "north": max(lats),
            "west": min(lngs),
            "east": max(lngs),
            "center_lat": sum(lats) / len(lats),
            "center_lng": sum(lngs) / len(lngs),
        }

    return {
        "municipality": muni_name,
        "points": points,
        "bounds": bounds,
        "total_reports": len(points),
        "active_reports": sum(1 for point in points if point["type"] == "active"),
        "flagged_reports": sum(1 for point in points if point["type"] == "flagged"),
        "archived_reports": sum(1 for point in points if point["type"] == "archived"),
    }


async def _get_municipality_reports_data(
    muni_name: str,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    safe_page = max(page, 1)
    safe_limit = max(1, min(limit, 100))
    query = _build_municipality_report_query(muni_name, status)
    skip = (safe_page - 1) * safe_limit
    total = await db.reports.count_documents(query)
    reports = await db.reports.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(safe_limit).to_list(safe_limit)
    reports = [strip_unapproved_report_photo(report) for report in reports]
    return {
        "reports": reports,
        "total": total,
        "page": safe_page,
        "pages": (total + safe_limit - 1) // safe_limit,
        "limit": safe_limit,
        "status": status or "all",
    }


async def _get_municipality_flags_data(muni_name: str, status: str = "pending") -> list[dict]:
    flags = await db.flags.find(
        {"municipality": muni_name, "status": status},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    for flag in flags:
        report = await db.reports.find_one(
            {"id": flag["report_id"]},
            {"_id": 0, "id": 1, "photo_url": 1, "latitude": 1, "longitude": 1, "created_at": 1}
        )
        flag["report"] = strip_unapproved_report_photo(report) if report else report

    return flags


async def _get_municipality_photo_reviews_data(muni_name: str) -> list[dict]:
    photo_violation_reasons = ["license_plate", "face", "name", "personal_info"]
    flags = await db.flags.find(
        {"municipality": muni_name, "reason": {"$in": photo_violation_reasons}, "status": "pending"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    seen_reports = set()
    reviews = []
    for flag in flags:
        rid = flag["report_id"]
        if rid in seen_reports:
            continue
        seen_reports.add(rid)

        report = await db.reports.find_one({"id": rid}, {"_id": 0})
        if not report:
            continue
        report = strip_unapproved_report_photo(report)

        all_flags = await db.flags.find({"report_id": rid}, {"_id": 0, "reason": 1, "created_at": 1}).to_list(20)

        reviews.append({
            "report": report,
            "flags": all_flags,
            "flag_count": len(all_flags),
            "photo_violation_count": sum(1 for item in all_flags if item["reason"] in photo_violation_reasons),
        })

    return reviews


async def _get_municipality_analytics_data(muni_name: str) -> dict:
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    sixty_days_ago = (now - timedelta(days=60)).isoformat()

    summary = await calc_analytics_summary(db, muni_name, now, thirty_days_ago, sixty_days_ago)
    daily_reports = await calc_daily_reports(db, muni_name, now)
    hourly_distribution = await calc_hourly_distribution(db, muni_name, thirty_days_ago)
    status_distribution = await calc_status_distribution(db, muni_name)
    top_zones = await calc_top_zones(db, muni_name, thirty_days_ago)

    return {
        "municipality": muni_name,
        "summary": summary,
        "daily_reports": daily_reports,
        "hourly_distribution": hourly_distribution,
        "status_distribution": status_distribution,
        "top_zones": top_zones,
    }


async def _build_municipality_dashboard_payload(
    muni_name: str,
    report_status: Optional[str] = "active",
    report_page: int = 1,
    report_limit: int = 20,
    flag_status: str = "pending",
) -> dict:
    await archive_expired_reports()
    stats, map_data, reports, flags, photo_reviews, analytics = await asyncio.gather(
        _get_municipality_stats_data(muni_name),
        _get_municipality_map_data(muni_name),
        _get_municipality_reports_data(muni_name, report_status, report_page, report_limit),
        _get_municipality_flags_data(muni_name, flag_status),
        _get_municipality_photo_reviews_data(muni_name),
        _get_municipality_analytics_data(muni_name),
    )

    return {
        "municipality": muni_name,
        "stats": stats,
        "map": map_data,
        "reports": reports,
        "flags": flags,
        "photo_reviews": photo_reviews,
        "analytics": analytics,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def _get_active_admin_municipality_dashboards() -> list[dict]:
    municipality_users = await db.users.find(
        {
            "role": "municipality",
            "municipality_subscription_active": True,
            "municipality_name": {"$exists": True, "$ne": ""},
        },
        {
            "_id": 0,
            "municipality_name": 1,
            "province": 1,
            "email_verified": 1,
            "created_at": 1,
            "last_login_at": 1,
        },
    ).to_list(500)

    municipalities = {}
    for user in municipality_users:
        name = (user.get("municipality_name") or "").strip()
        if not name:
            continue
        province = (user.get("province") or "").strip()
        entry = municipalities.setdefault(name, {
            "municipality_name": name,
            "province": province,
            "dashboard_count": 0,
            "verified_accounts": 0,
            "latest_login_at": None,
        })
        entry["dashboard_count"] += 1
        if user.get("email_verified"):
            entry["verified_accounts"] += 1
        last_login = user.get("last_login_at")
        if last_login and (not entry["latest_login_at"] or last_login > entry["latest_login_at"]):
            entry["latest_login_at"] = last_login

    return sorted(municipalities.values(), key=lambda item: (item["municipality_name"].lower(), item["province"].lower()))


@api_router.get("/municipality/stats")
async def get_municipality_stats(request: Request):
    user = await require_municipality(request)
    await archive_expired_reports()
    return await _get_municipality_stats_data(user.get("municipality_name", ""))

@api_router.get("/municipality/map")
async def get_municipality_map(request: Request):
    user = await require_municipality(request)
    await archive_expired_reports()
    return await _get_municipality_map_data(user.get("municipality_name", ""))

@api_router.get("/municipality/reports")
async def get_municipality_reports(request: Request, status: Optional[str] = None, page: int = 1, limit: int = 20):
    user = await require_municipality(request)
    await archive_expired_reports()
    return await _get_municipality_reports_data(user.get("municipality_name", ""), status, page, limit)

@api_router.get("/municipality/flags")
async def get_municipality_flags(request: Request, status: str = "pending"):
    user = await require_municipality(request)
    await archive_expired_reports()
    return await _get_municipality_flags_data(user.get("municipality_name", ""), status)

@api_router.post("/municipality/moderate/{report_id}")
async def moderate_report(report_id: str, data: ModerationAction, request: Request):
    user = await require_municipality(request)
    muni_name = user.get("municipality_name", "")
    
    report = await db.reports.find_one({"id": report_id, "municipality": muni_name})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado en tu municipio")
    
    if data.action == "hide":
        await db.reports.update_one({"id": report_id}, {"$set": {"flagged": True, "moderated_by": user["_id"], "moderated_at": datetime.now(timezone.utc).isoformat()}})
        await db.flags.update_many({"report_id": report_id}, {"$set": {"status": "resolved"}})
    elif data.action == "restore":
        await db.reports.update_one({"id": report_id}, {"$set": {"flagged": False, "moderated_by": user["_id"], "moderated_at": datetime.now(timezone.utc).isoformat()}})
        await db.flags.update_many({"report_id": report_id}, {"$set": {"status": "dismissed"}})
    elif data.action == "dismiss":
        await db.flags.update_many({"report_id": report_id, "municipality": muni_name}, {"$set": {"status": "dismissed"}})
    
    return {"message": f"Acción '{data.action}' aplicada"}

@api_router.get("/municipality/photo-reviews")
async def get_photo_reviews(request: Request):
    """Get reports with photos that have been flagged for photo violations (license_plate, face, name, personal_info)."""
    user = await require_municipality(request)
    await archive_expired_reports()
    return await _get_municipality_photo_reviews_data(user.get("municipality_name", ""))






# ==================== CLEAN ROUTE ====================

@api_router.get("/route/clean")
async def get_clean_route(
    start_lat: float, start_lon: float, end_lat: float, end_lon: float,
    request: Request
):
    """Analyze a route and identify danger zones to avoid. Premium only."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Ruta limpia es una función Premium")
    result = await analyze_clean_route(db, start_lat, start_lon, end_lat, end_lon)
    return result

# ==================== WEEKLY DIGEST ====================

@api_router.post("/admin/send-digests")
async def trigger_weekly_digests(request: Request):
    """Manually trigger weekly digest emails. Admin only."""
    user = await require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    result = await send_weekly_digests(db)
    return result

@api_router.get("/municipality/digest-preview")
async def preview_digest(request: Request):
    """Preview the weekly digest for current municipality."""
    user = await require_municipality(request)
    await archive_expired_reports()
    digest = await generate_municipality_digest(db, user.get("municipality_name", ""))
    return digest

# ==================== FEEDBACK ====================

@api_router.post("/feedback")
async def submit_feedback(request: Request):
    """Submit user feedback, bug reports, or suggestions."""
    body = await request.json()
    user = await get_current_user(request)
    await db.feedback.insert_one({
        "category": body.get("category", "other"),
        "message": body.get("message", ""),
        "user_id": user["_id"] if user else None,
        "user_email": body.get("user_email") or (user.get("email") if user else None),
        "username": body.get("username") or (user.get("username") if user else None),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "new",
    })
    return {"message": "Feedback recibido"}

# ==================== ACTIVITY STATS ====================

@api_router.get("/stats/activity")
async def get_activity_stats(request: Request, lat: float = None, lng: float = None, radius: float = 5000):
    """Get activity stats for the homepage banner."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    total_today = await db.reports.count_documents({"created_at": {"$gte": today_start}})
    nearby_today = 0
    active_zones = 0
    if lat and lng:
        all_today = await db.reports.find(
            {"created_at": {"$gte": today_start}, "archived": {"$ne": True}},
            {"_id": 0, "latitude": 1, "longitude": 1}
        ).to_list(1000)
        from antispam_service import haversine_meters
        for r in all_today:
            if haversine_meters(lat, lng, r["latitude"], r["longitude"]) < radius:
                nearby_today += 1
        recent = await db.reports.find(
            {"archived": {"$ne": True}, "flagged": {"$ne": True}},
            {"_id": 0, "latitude": 1, "longitude": 1}
        ).to_list(2000)
        from collections import defaultdict
        grid = defaultdict(int)
        for r in recent:
            cell = (round(r["latitude"] * 200) / 200, round(r["longitude"] * 200) / 200)
            if haversine_meters(lat, lng, r["latitude"], r["longitude"]) < radius:
                grid[cell] += 1
        active_zones = sum(1 for c in grid.values() if c >= 2)
    user_rank = None
    user = await get_current_user(request)
    if user:
        higher = await db.users.count_documents({"role": "user", "total_score": {"$gt": user.get("total_score", 0)}})
        user_rank = higher + 1
    return {"total_today": total_today, "nearby_today": nearby_today, "active_zones": active_zones, "user_rank": user_rank}

# ==================== SOCIAL SHARING ====================

@api_router.get("/users/{user_id_param}/share")
async def get_user_share_data(user_id_param: str):
    """Get shareable profile data for social media."""
    try:
        u = await db.users.find_one({"_id": ObjectId(user_id_param)}, {"_id": 0, "username": 1, "name": 1, "rank": 1, "rank_key": 1, "total_score": 1, "report_count": 1, "badges": 1})
    except Exception:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    display_name = u.get("username") or u.get("name", "Usuario")
    badge_count = len(u.get("badges", []))
    app_url = build_download_url("profile", name=display_name)
    share_url = build_share_page_url("profile", name=display_name)

    return {
        "title": f"{display_name} en Caca Radar",
        "text": f"{display_name} es {u.get('rank', DEFAULT_RANK_NAME)} con {u.get('total_score', 0)} puntos y {u.get('report_count', 0)} reportes. {badge_count} insignias. ¡Únete a mantener tu ciudad limpia!",
        "rank": u.get("rank", DEFAULT_RANK_NAME),
        "rank_key": u.get("rank_key", get_rank_key(u.get("rank", DEFAULT_RANK_NAME))),
        "total_score": u.get("total_score", 0),
        "report_count": u.get("report_count", 0),
        "badge_count": badge_count,
        "url": share_url,
        "app_url": app_url,
        "app_store_url": APP_STORE_URL,
        "play_store_url": PLAY_STORE_URL,
        "download_text": f"Descarga Caca Radar:\niOS: {APP_STORE_URL}\nAndroid: {PLAY_STORE_URL}"
    }

@api_router.get("/store-links")
async def get_store_links():
    """Get app store download links."""
    return {"app_store_url": APP_STORE_URL, "play_store_url": PLAY_STORE_URL}


# ==================== BADGES ====================

@api_router.get("/users/badges")
async def get_my_badges(request: Request):
    user = await require_auth(request)
    badges = get_user_badges(user)
    return badges

# ==================== WEEKLY LEADERBOARD ====================

@api_router.get("/leaderboard/weekly")
async def get_weekly_leaderboard(request: Request):
    """Weekly leaderboard based on reports created this week."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")

    # Get start of current week (Monday)
    now = datetime.now(timezone.utc)
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    pipeline = [
        {"$match": {"created_at": {"$gte": start_of_week.isoformat()}}},
        {"$group": {"_id": "$user_id", "weekly_reports": {"$sum": 1}, "weekly_votes": {"$sum": "$upvotes"}}},
        {"$sort": {"weekly_reports": -1}},
        {"$limit": 50}
    ]
    weekly_agg = await db.reports.aggregate(pipeline).to_list(50)

    results = []
    for i, entry in enumerate(weekly_agg):
        uid = entry["_id"]
        try:
            u = await db.users.find_one({"_id": ObjectId(uid)}, {"_id": 0, "username": 1, "name": 1, "rank": 1, "rank_key": 1, "subscription_active": 1})
        except Exception:
            u = None
        display_name = (u.get("username") or u.get("name", "Anónimo")) if u else "Anónimo"
        results.append({
            "position": i + 1,
            "display_name": display_name,
            "rank": u.get("rank") if u else None,
            "rank_key": u.get("rank_key") if u else None,
            "weekly_reports": entry["weekly_reports"],
            "is_subscriber": u.get("subscription_active", False) if u else False
        })

    return results

# ==================== SAVED LOCATIONS ====================

async def _save_location_impl(data: SavedLocationCreate, request: Request):
    user = await require_subscriber(request)
    loc = {
        "id": str(uuid.uuid4()),
        "user_id": user["_id"],
        "name": data.name,
        "label": data.label or data.name,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.saved_locations.update_one(
        {"user_id": user["_id"], "name": data.name},
        {"$set": loc},
        upsert=True
    )
    return {
        "id": loc["id"],
        "name": loc["name"],
        "label": loc["label"],
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "created_at": loc["created_at"],
    }

@api_router.post("/users/saved-locations")
@api_router.post("/push/saved-locations")
async def save_location(data: SavedLocationCreate, request: Request):
    return await _save_location_impl(data, request)

async def _get_saved_locations_impl(request: Request):
    user = await require_subscriber(request)
    locs = await db.saved_locations.find({"user_id": user["_id"]}, {"_id": 0}).to_list(10)
    return [
        {
            "id": loc.get("id"),
            "name": loc.get("name"),
            "label": loc.get("label") or loc.get("name"),
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "created_at": loc.get("created_at"),
        }
        for loc in locs
    ]

@api_router.get("/users/saved-locations")
@api_router.get("/push/saved-locations")
async def get_saved_locations(request: Request):
    return await _get_saved_locations_impl(request)

async def _delete_saved_location_impl(name: str, request: Request):
    user = await require_subscriber(request)
    await db.saved_locations.delete_one({"user_id": user["_id"], "name": name})
    return {"message": "Ubicación eliminada"}

@api_router.delete("/users/saved-locations/{name}")
@api_router.delete("/push/saved-locations/{name}")
async def delete_saved_location(name: str, request: Request):
    return await _delete_saved_location_impl(name, request)

# ==================== NEIGHBORHOOD CLEANLINESS ====================

@api_router.get("/neighborhood/score")
async def get_neighborhood_score(lat: float, lon: float, radius: float = 0.01):
    """Get cleanliness score for a neighborhood area."""
    reports = await db.reports.find({
        "latitude": {"$gte": lat - radius, "$lte": lat + radius},
        "longitude": {"$gte": lon - radius, "$lte": lon + radius}
    }, {"_id": 0, "archived": 1, "flagged": 1, "created_at": 1, "status": 1}).to_list(500)
    score = calc_neighborhood_cleanliness(reports)
    return {"latitude": lat, "longitude": lon, "cleanliness_score": score, "score": score, "total_reports": len(reports)}

# ==================== ADMIN 2FA LOGIN ====================

@api_router.post("/admin/login")
async def admin_login_step1(request: Request):
    """Step 1: Validate admin credentials, send verification code to email."""
    body = await request.json()
    email = body.get("email", "").lower()
    password = body.get("password", "")
    context = get_request_context(request)
    client_ip = context.get("client_ip") or "unknown"

    await enforce_rate_limit(
        key=f"admin_login_send:ip:{client_ip}",
        max_attempts=10,
        window_seconds=900,
        detail="Demasiados intentos. Espera unos minutos antes de solicitar otro código.",
    )
    await enforce_rate_limit(
        key=f"admin_login_send:email:{email}",
        max_attempts=5,
        window_seconds=900,
        detail="Demasiados intentos. Espera unos minutos antes de solicitar otro código.",
    )

    user = await db.users.find_one({"email": email, "role": "admin"})
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not email_configured():
        logger.error("Admin 2FA email requested for %s but email delivery is not configured", email)
        raise HTTPException(
            status_code=503,
            detail="El envío de códigos por email no está configurado ahora mismo. Contacta con soporte."
        )

    # Generate 6-digit code
    code = generate_verification_code()
    expires = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    await db.admin_codes.update_one(
        {"email": email},
        {"$set": {"code": code, "expires": expires, "attempt_count": 0}},
        upsert=True
    )

    # Send code via email
    email_result = await send_admin_verification_code(email, code)
    if email_result.get("status") != "sent":
        await db.admin_codes.delete_one({"email": email})
        logger.error("Admin 2FA email failed for %s: %s", email, email_result)
        raise HTTPException(
            status_code=502,
            detail="No hemos podido enviar el código de verificación. Inténtalo de nuevo en unos minutos."
        )

    logger.info("Admin 2FA code sent to %s", email)

    return {"message": "Código de verificación enviado a tu email", "email_sent": True}

@api_router.post("/admin/verify")
async def admin_login_step2(request: Request, response: Response):
    """Step 2: Verify the email code and issue session cookies."""
    body = await request.json()
    email = body.get("email", "").lower()
    code = body.get("code", "")
    context = get_request_context(request)
    client_ip = context.get("client_ip") or "unknown"

    await enforce_rate_limit(
        key=f"admin_verify:ip:{client_ip}",
        max_attempts=10,
        window_seconds=900,
        detail="Demasiados intentos. Inicia sesión de nuevo en unos minutos.",
    )
    await enforce_rate_limit(
        key=f"admin_verify:email:{email}",
        max_attempts=5,
        window_seconds=900,
        detail="Demasiados intentos. Inicia sesión de nuevo en unos minutos.",
    )

    record = await db.admin_codes.find_one({"email": email})
    if not record:
        raise HTTPException(status_code=400, detail="No hay código pendiente. Inicia sesión de nuevo.")

    if int(record.get("attempt_count", 0)) >= 5:
        await db.admin_codes.delete_one({"email": email})
        raise HTTPException(status_code=400, detail="Demasiados intentos. Inicia sesión de nuevo.")

    if record["code"] != code:
        next_attempt_count = int(record.get("attempt_count", 0)) + 1
        if next_attempt_count >= 5:
            await db.admin_codes.delete_one({"email": email})
        else:
            await db.admin_codes.update_one({"email": email}, {"$set": {"attempt_count": next_attempt_count}})
        raise HTTPException(status_code=400, detail="Código incorrecto")

    if datetime.fromisoformat(record["expires"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="El código ha expirado. Inicia sesión de nuevo.")

    # Code valid — clean up and issue session
    await db.admin_codes.delete_one({"email": email})
    await clear_rate_limits([
        f"admin_login_send:ip:{client_ip}",
        f"admin_login_send:email:{email}",
        f"admin_verify:ip:{client_ip}",
        f"admin_verify:email:{email}",
    ])
    user = await db.users.find_one({"email": email, "role": "admin"})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    user = await update_login_metadata(user["_id"], request, user)

    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email, "admin")
    refresh_token = create_refresh_token(user_id)
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=3600, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")

    return {"message": "Acceso admin verificado", "role": "admin"}

# ==================== ADMIN DASHBOARD DATA ====================

async def _require_admin(request: Request) -> dict:
    user = await require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return user

@api_router.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    """Full admin dashboard data — platform overview."""
    await _require_admin(request)
    await archive_expired_reports()
    now = datetime.now(timezone.utc)
    seven_days = (now - timedelta(days=7)).isoformat()
    thirty_days = (now - timedelta(days=30)).isoformat()
    fresh_cutoff = (now - timedelta(hours=24)).isoformat()

    total_users = await db.users.count_documents({"role": "user"})
    premium_users = await db.users.count_documents({"role": "user", "subscription_active": True})
    total_municipalities = await db.users.count_documents({"role": "municipality"})
    active_muni_subs = await db.users.count_documents({"role": "municipality", "municipality_subscription_active": True})
    total_reports = await db.reports.count_documents({})
    active_reports = await db.reports.count_documents(build_active_report_filter())
    reports_7d = await db.reports.count_documents({"created_at": {"$gte": seven_days}})
    reports_30d = await db.reports.count_documents({"created_at": {"$gte": thirty_days}})
    flagged_reports = await db.reports.count_documents({"flagged": True})
    fresh_reports = await db.reports.count_documents({"created_at": {"$gte": fresh_cutoff}})
    old_reports = await db.reports.count_documents({"created_at": {"$gte": seven_days, "$lt": fresh_cutoff}})
    fossil_reports = await db.reports.count_documents({"created_at": {"$lt": seven_days}})
    new_users_7d = await db.users.count_documents({"role": "user", "created_at": {"$gte": seven_days}})
    new_users_30d = await db.users.count_documents({"role": "user", "created_at": {"$gte": thirty_days}})

    # Subscription revenue estimate
    monthly_subs = await db.users.count_documents({"role": "user", "subscription_active": True, "subscription_type": "monthly"})
    annual_subs = await db.users.count_documents({"role": "user", "subscription_active": True, "subscription_type": "annual"})
    est_monthly_revenue = (monthly_subs * 3.99) + (annual_subs * 29.99 / 12) + (active_muni_subs * 50)

    return {
        "users": {
            "total": total_users,
            "premium": premium_users,
            "free": total_users - premium_users,
            "conversion_rate": round((premium_users / max(total_users, 1)) * 100, 1),
            "new_7d": new_users_7d,
            "new_30d": new_users_30d,
        },
        "subscriptions": {
            "monthly": monthly_subs,
            "annual": annual_subs,
            "municipality_active": active_muni_subs,
            "municipality_total": total_municipalities,
            "est_monthly_revenue": round(est_monthly_revenue, 2),
        },
        "reports": {
            "total": total_reports,
            "active": active_reports,
            "flagged": flagged_reports,
            "last_7d": reports_7d,
            "last_30d": reports_30d,
            "fresh": fresh_reports,
            "old": old_reports,
            "fossil": fossil_reports,
        },
        "generated_at": now.isoformat(),
    }


@api_router.get("/admin/municipalities")
async def admin_municipality_dashboards(request: Request):
    """List active municipality dashboards available for admin inspection."""
    await _require_admin(request)
    municipalities = await _get_active_admin_municipality_dashboards()
    return {
        "municipalities": municipalities,
        "total": len(municipalities),
    }


@api_router.get("/admin/municipality-dashboard")
async def admin_municipality_dashboard(
    request: Request,
    municipality: str = Query(..., min_length=1),
    status: Optional[str] = Query("active"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Mirror a municipality dashboard for admins, scoped to one selected city."""
    await _require_admin(request)
    target_name = municipality.strip()
    municipalities = await _get_active_admin_municipality_dashboards()
    available_names = {item["municipality_name"] for item in municipalities}
    if target_name not in available_names:
        raise HTTPException(status_code=404, detail="Municipio no disponible en dashboards activos")

    payload = await _build_municipality_dashboard_payload(
        target_name,
        report_status=status,
        report_page=page,
        report_limit=limit,
    )
    selected = next((item for item in municipalities if item["municipality_name"] == target_name), None)
    payload["selection"] = {
        "municipality_name": target_name,
        "available_dashboards": len(municipalities),
        "province": selected.get("province", "") if selected else "",
    }
    return payload


@api_router.get("/admin/recent-reports")
async def admin_recent_reports(request: Request, skip: int = 0, limit: int = 100):
    """Recent reports with reporter identity for admin review."""
    await _require_admin(request)
    await archive_expired_reports()
    safe_limit = max(1, min(limit, 100))
    safe_skip = max(0, skip)

    reports = await db.reports.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "user_id": 1,
            "contributor_name": 1,
            "contributor_rank": 1,
            "contributor_rank_key": 1,
            "municipality": 1,
            "province": 1,
            "barrio": 1,
            "category": 1,
            "description": 1,
            "created_at": 1,
            "archived": 1,
            "flagged": 1,
            "photo_url": 1,
            "latitude": 1,
            "longitude": 1,
        },
    ).sort("created_at", -1).skip(safe_skip).limit(safe_limit).to_list(safe_limit)

    user_ids = []
    for report in reports:
        user_id = report.get("user_id")
        if user_id and ObjectId.is_valid(str(user_id)):
            normalized = str(user_id)
            if normalized not in user_ids:
                user_ids.append(normalized)

    reporter_map = {}
    if user_ids:
        users = await db.users.find(
            {"_id": {"$in": [ObjectId(uid) for uid in user_ids]}},
            {"email": 1, "username": 1, "name": 1, "role": 1},
        ).to_list(len(user_ids))
        reporter_map = {
            str(user["_id"]): {
                "email": user.get("email", ""),
                "username": user.get("username", ""),
                "name": user.get("name", ""),
                "role": user.get("role", "user"),
            }
            for user in users
        }

    serialized = []
    for report in reports:
        reporter = reporter_map.get(str(report.get("user_id")), {})
        display_name = (
            reporter.get("username")
            or reporter.get("name")
            or report.get("contributor_name")
            or "Anónimo"
        )
        serialized.append({
            **report,
            "reporter": {
                "display_name": display_name,
                "email": reporter.get("email", ""),
                "username": reporter.get("username", ""),
                "name": reporter.get("name", ""),
                "role": reporter.get("role", "user"),
            },
        })

    total = await db.reports.count_documents({})
    return {"reports": serialized, "total": total, "skip": safe_skip, "limit": safe_limit}

@api_router.get("/admin/users")
async def admin_users(request: Request, skip: int = 0, limit: int = 50, search: str = ""):
    """List all users with stats."""
    await _require_admin(request)
    user_scope_query = {"$or": [{"role": "user"}, {"role": None}]}
    query = user_scope_query
    if search:
        query = {
            "$and": [
                user_scope_query,
                {
                    "$or": [
                        {"email": {"$regex": search, "$options": "i"}},
                        {"username": {"$regex": search, "$options": "i"}},
                        {"name": {"$regex": search, "$options": "i"}},
                    ]
                },
            ]
        }
    users = await db.users.find(
        query,
        {
            "password_hash": 0,
            "linked_providers": 0,
        }
    ).sort("last_login_at", -1).skip(skip).limit(limit).to_list(limit)

    total = await db.users.count_documents(query)
    serialized = []
    for user in users:
        user_doc = {**user}
        user_doc.pop("_id", None)
        auth_methods = normalize_auth_methods(user)
        serialized.append({
            **user_doc,
            "id": str(user.get("_id")) if user.get("_id") is not None else None,
            "account_type": get_account_type(user),
            "auth_methods": auth_methods,
            "display_name": user.get("username") or user.get("name") or user.get("email"),
            "reports_count": user.get("report_count", 0),
            "votes_count": user.get("vote_count", 0),
            "subscription_label": "PRO" if user.get("subscription_active") else "FREE",
            "last_seen_at": user.get("last_login_at") or user.get("last_active_date"),
            "last_platform": user.get("last_login_platform") or "unknown",
        })
    return {"users": serialized, "total": total, "skip": skip, "limit": limit}


@api_router.put("/admin/users/{user_id}/account-type")
async def admin_update_user_account_type(user_id: str, data: AdminUserAccountTypeUpdate, request: Request):
    await _require_admin(request)
    try:
        target_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Usuario inválido")

    user = await db.users.find_one({"_id": target_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.get("role") not in ("user", None):
        raise HTTPException(status_code=400, detail="Solo se puede actualizar el tipo de cuentas de usuario estándar")

    account_type = get_account_type({"account_type": data.account_type})
    update_fields = {"account_type": account_type}

    if account_type == "municipal_worker":
        municipality_name = (data.municipality_name or "").strip()
        municipality_province = (data.municipality_province or "").strip()
        if not municipality_name:
            raise HTTPException(status_code=400, detail="Debes asignar un municipio para habilitar el operario municipal")
        update_fields["municipality_name"] = municipality_name
        update_fields["municipality_province"] = municipality_province
        update_fields["municipal_worker_enabled_at"] = datetime.now(timezone.utc).isoformat()
    else:
        update_fields["municipality_name"] = None
        update_fields["municipality_province"] = None

    await db.users.update_one({"_id": target_id}, {"$set": update_fields})
    updated_user = await db.users.find_one({"_id": target_id}, {"password_hash": 0, "linked_providers": 0})
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "message": "Tipo de cuenta actualizado",
        "user": {
            "id": str(updated_user["_id"]),
            "email": updated_user.get("email"),
            "account_type": get_account_type(updated_user),
            "municipality_name": updated_user.get("municipality_name"),
            "municipality_province": updated_user.get("municipality_province"),
        },
    }

@api_router.get("/admin/photo-violations")
async def admin_photo_violations(request: Request, skip: int = 0, limit: int = 50):
    """All pending content/report flags across all municipalities."""
    await _require_admin(request)
    await archive_expired_reports()
    flags = await db.flags.find(
        {"status": {"$in": ["pending", None]}},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    # Enrich with report data
    enriched = []
    for flag in flags:
        report = await db.reports.find_one(
            {"id": flag.get("report_id")},
            {"_id": 0, "id": 1, "photo_url": 1, "latitude": 1, "longitude": 1, "municipality": 1, "created_at": 1, "contributor_name": 1, "flag_count": 1}
        )
        enriched.append({**flag, "report": report})

    total = await db.flags.count_documents({"status": {"$in": ["pending", None]}})
    return {"violations": enriched, "total": total}


async def _remove_report_after_photo_rejection(report: dict, admin_user: dict) -> None:
    report_id = report.get("id")
    if not report_id:
        return

    await db.reports.delete_one({"id": report_id})
    await db.votes.delete_many({"report_id": report_id})
    await db.validations.delete_many({"report_id": report_id})
    await db.report_votes.delete_many({"report_id": report_id})
    await db.flags.delete_many({"report_id": report_id})

    municipality_name = report.get("municipality")
    if municipality_name:
        await db.municipalities.update_one(
            {"name": municipality_name, "province": report.get("province", "")},
            {"$inc": {"report_count": -1}},
        )

    await db.report_audit_log.insert_one({
        "id": str(uuid.uuid4()),
        "event": "report_removed_photo_rejected",
        "report_id": report_id,
        "user_id": report.get("user_id"),
        "municipality": municipality_name,
        "province": report.get("province"),
        "metadata": {
            "photo_url": report.get("photo_url"),
            "moderated_by": str(admin_user.get("_id")),
            "moderated_by_email": admin_user.get("email"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


@api_router.get("/admin/photo-approvals")
async def admin_photo_approvals(request: Request, skip: int = 0, limit: int = 100):
    """Admin queue of reports whose photos are pending approval."""
    await _require_admin(request)
    await archive_expired_reports()
    safe_skip = max(skip, 0)
    safe_limit = max(1, min(limit, 100))
    query = {
        "photo_url": {"$ne": None},
        "photo_status": "pending",
        "archived": {"$ne": True},
        "flagged": {"$ne": True},
    }
    approvals = await db.reports.find(
        query,
        {
            "_id": 0,
            "id": 1,
            "photo_url": 1,
            "photo_status": 1,
            "photo_submitted_at": 1,
            "created_at": 1,
            "description": 1,
            "municipality": 1,
            "province": 1,
            "barrio": 1,
            "latitude": 1,
            "longitude": 1,
            "contributor_name": 1,
            "contributor_rank": 1,
            "contributor_rank_key": 1,
            "user_id": 1,
        },
    ).sort("photo_submitted_at", -1).skip(safe_skip).limit(safe_limit).to_list(safe_limit)
    approvals = await apply_current_public_report_ranks(approvals)
    total = await db.reports.count_documents(query)
    return {"approvals": approvals, "total": total, "skip": safe_skip, "limit": safe_limit}


@api_router.post("/admin/photo-approvals/moderate")
async def admin_photo_approvals_moderate(request: Request):
    """Approve or reject pending report photos in batch."""
    admin_user = await _require_admin(request)
    body = await request.json()
    action = body.get("action")
    report_ids = body.get("report_ids") or []

    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Acción inválida")
    if not isinstance(report_ids, list) or not report_ids:
        raise HTTPException(status_code=400, detail="Selecciona al menos un reporte")

    normalized_ids = [str(report_id).strip() for report_id in report_ids if str(report_id).strip()]
    normalized_ids = list(dict.fromkeys(normalized_ids))[:100]
    if not normalized_ids:
        raise HTTPException(status_code=400, detail="Selecciona al menos un reporte")

    pending_reports = await db.reports.find(
        {"id": {"$in": normalized_ids}, "photo_status": "pending"},
        {"_id": 0},
    ).to_list(len(normalized_ids))
    if not pending_reports:
        raise HTTPException(status_code=404, detail="No se encontraron fotos pendientes para revisar")

    moderated_at = datetime.now(timezone.utc).isoformat()

    if action == "approve":
        approved_count = 0
        from scoring_service import REPORT_PHOTO_BONUS

        for report in pending_reports:
            updates = {
                "photo_status": "approved",
                "photo_reviewed_at": moderated_at,
                "photo_reviewed_by": str(admin_user.get("_id")),
            }
            reporter_id = report.get("user_id")
            if reporter_id and not report.get("photo_bonus_awarded"):
                try:
                    await db.users.update_one({"_id": ObjectId(reporter_id)}, {"$inc": {"total_score": REPORT_PHOTO_BONUS}})
                    updates["photo_bonus_awarded"] = True
                except Exception:
                    updates["photo_bonus_awarded"] = False

            await db.reports.update_one({"id": report["id"]}, {"$set": updates})
            approved_count += 1

        return {"message": f"{approved_count} fotos aprobadas", "approved": approved_count}

    rejected_count = 0
    for report in pending_reports:
        await _remove_report_after_photo_rejection(report, admin_user)
        rejected_count += 1

    return {"message": f"{rejected_count} reportes eliminados por rechazo de foto", "rejected": rejected_count}

@api_router.post("/admin/moderate/{report_id}")
async def admin_moderate_report(report_id: str, request: Request):
    """Admin: moderate any report (hide, restore, dismiss flags)."""
    await _require_admin(request)
    body = await request.json()
    action = body.get("action", "hide")

    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    if action == "hide":
        await db.reports.update_one({"id": report_id}, {"$set": {"flagged": True}})
        await db.flags.update_many({"report_id": report_id}, {"$set": {"status": "resolved"}})
    elif action == "restore":
        await db.reports.update_one({"id": report_id}, {"$set": {"flagged": False, "flag_count": 0}})
        await db.flags.update_many({"report_id": report_id}, {"$set": {"status": "dismissed"}})
    elif action == "dismiss":
        await db.flags.update_many({"report_id": report_id}, {"$set": {"status": "dismissed"}})

    return {"message": f"Reporte {action}: {report_id}"}

@api_router.get("/admin/integration-status")
async def admin_integration_status(request: Request):
    """Admin: Check which integrations are configured for production."""
    await _require_admin(request)
    return {
        "apple": {
            "configured": bool(APPLE_KEY_ID and APPLE_ISSUER_ID and APPLE_BUNDLE_ID and APPLE_KEY_PATH),
            "environment": APPLE_ENVIRONMENT,
            "bundle_id": APPLE_BUNDLE_ID or "Not set",
            "key_id": APPLE_KEY_ID[:4] + "..." if APPLE_KEY_ID else "Not set",
        },
        "google": {
            "configured": bool(GOOGLE_SERVICE_ACCOUNT_PATH and GOOGLE_PACKAGE_NAME),
            "package_name": GOOGLE_PACKAGE_NAME or "Not set",
            "service_account": "Configured" if GOOGLE_SERVICE_ACCOUNT_PATH else "Not set",
        },
        "resend": {
            "configured": email_configured(),
            "sender": os.environ.get("SENDER_EMAIL", "Not set"),
        },
        "setup_instructions": {
            "apple": "Set APPLE_KEY_ID, APPLE_ISSUER_ID, APPLE_BUNDLE_ID, APPLE_KEY_PATH in .env. Download .p8 key from App Store Connect > Keys.",
            "google": "Set GOOGLE_SERVICE_ACCOUNT_PATH (JSON key file), GOOGLE_PACKAGE_NAME in .env. Create service account in Google Cloud Console.",
        }
    }

@api_router.get("/play-integrity/status")
async def get_play_integrity_status():
    configured = play_integrity_is_configured()
    return {
        "configured": configured,
        "package_name": GOOGLE_PACKAGE_NAME or "",
        "service_account_configured": bool(GOOGLE_SERVICE_ACCOUNT_PATH),
        "mode": "log_only",
        "message": (
            "Android-only verification scaffold is ready."
            if configured
            else "Set GOOGLE_SERVICE_ACCOUNT_PATH and GOOGLE_PACKAGE_NAME to enable server verification."
        ),
    }

@api_router.post("/play-integrity/verify")
async def verify_play_integrity(data: PlayIntegrityVerifyRequest, request: Request):
    user = await get_current_user(request)

    if not play_integrity_is_configured():
        return {
            "enabled": False,
            "configured": False,
            "mode": "log_only",
            "message": "Play Integrity server verification is not configured yet.",
        }

    try:
        decoded = await asyncio.to_thread(
            decode_integrity_token,
            data.integrity_token,
            GOOGLE_PACKAGE_NAME,
            GOOGLE_SERVICE_ACCOUNT_PATH,
        )
        summary = summarize_integrity_payload(decoded, data.request_hash)
        logger.info(
            "Play Integrity verdict",
            extra={
                "play_integrity_action": data.action or "unspecified",
                "play_integrity_user": user.get("_id") if user else "anonymous",
                "play_integrity_app_verdict": summary.get("app_recognition_verdict"),
                "play_integrity_device_verdict": summary.get("device_recognition_verdict"),
                "play_integrity_license_verdict": summary.get("app_licensing_verdict"),
            },
        )
        return {
            "enabled": True,
            "configured": True,
            "mode": "log_only",
            "action": data.action,
            "summary": summary,
        }
    except Exception as exc:
        logger.error(f"Play Integrity verification failed: {exc}")
        raise HTTPException(status_code=502, detail="Play Integrity verification failed")

# ==================== SUCCESS METRICS (Admin) ====================

@api_router.get("/admin/metrics")
async def get_success_metrics(request: Request):
    user = await require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    seven_days = (now - timedelta(days=7)).isoformat()
    thirty_days = (now - timedelta(days=30)).isoformat()

    total_users = await db.users.count_documents({"role": "user"})
    premium_users = await db.users.count_documents({"role": "user", "subscription_active": True})
    daily_active = await db.reports.aggregate([
        {"$match": {"created_at": {"$gte": today}}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "count"}
    ]).to_list(1)
    dau = daily_active[0]["count"] if daily_active else 0

    total_reports = await db.reports.count_documents({})
    reports_7d = await db.reports.count_documents({"created_at": {"$gte": seven_days}})
    reports_30d = await db.reports.count_documents({"created_at": {"$gte": thirty_days}})
    verified = await db.reports.count_documents({"status": "verified"})
    confirmation_rate = round((verified / max(total_reports, 1)) * 100, 1)
    conversion_rate = round((premium_users / max(total_users, 1)) * 100, 1)

    # 7-day retention
    week_old_users = await db.users.count_documents({"created_at": {"$lte": seven_days}, "role": "user"})
    retained_7d = await db.users.count_documents({"created_at": {"$lte": seven_days}, "role": "user", "last_active_date": {"$gte": seven_days}})
    retention_7d = round((retained_7d / max(week_old_users, 1)) * 100, 1)

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "active_subscriptions": premium_users,
        "conversion_rate": conversion_rate,
        "dau": dau,
        "total_reports": total_reports,
        "reports_7d": reports_7d,
        "reports_30d": reports_30d,
        "confirmation_rate": confirmation_rate,
        "retention_7d": retention_7d,
        "reports_per_user": round(total_reports / max(total_users, 1), 1)
    }


# ==================== PUSH NOTIFICATIONS ====================

@api_router.get("/push/vapid-key")
async def get_vapid_key():
    """Return VAPID public key for client push subscription."""
    return {"vapid_public_key": VAPID_PUBLIC_KEY}

@api_router.post("/push/subscribe")
async def subscribe_push(data: PushSubscriptionCreate, request: Request, response: Response):
    """Subscribe to push notifications for nearby reports."""
    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id
    platform_header = (request.headers.get("X-Platform") or "").strip().lower()
    subscription = dict(data.subscription or {})
    if subscription.get("token") and platform_header in {"ios", "android"}:
        subscription["platform"] = platform_header

    existing = await db.push_subscriptions.find_one({"user_id": user_id}, {"radius_meters": 1})
    radius_meters = data.radius_meters or (existing or {}).get("radius_meters") or 500

    # Upsert subscription
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "subscription": subscription,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "radius_meters": radius_meters,
            "active": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=True, samesite="none", max_age=86400*365, path="/")

    return {"message": "Suscripción push activada"}

@api_router.post("/push/unsubscribe")
async def unsubscribe_push(request: Request):
    user = await get_current_user(request)
    anon_id = request.cookies.get("anon_id")
    user_id = user["_id"] if user else anon_id
    if user_id:
        await db.push_subscriptions.update_one({"user_id": user_id}, {"$set": {"active": False}})
    return {"message": "Suscripción push desactivada"}

@api_router.get("/push/status")
async def get_push_status(request: Request):
    """Check if current user has an active push subscription."""
    user = await get_current_user(request)
    if not user:
        return {"subscribed": False}
    sub = await db.push_subscriptions.find_one(
        {"user_id": user["_id"], "active": True}, {"_id": 0}
    )
    if not sub:
        return {"subscribed": False}
    saved_location_count = await db.saved_locations.count_documents({"user_id": user["_id"]})
    return {
        "subscribed": True,
        "latitude": sub.get("latitude"),
        "longitude": sub.get("longitude"),
        "radius_meters": sub.get("radius_meters", 500),
        "saved_location_alert_radius_meters": SAVED_LOCATION_ALERT_RADIUS_METERS,
        "saved_location_count": saved_location_count,
        "updated_at": sub.get("updated_at"),
        "platform": (sub.get("subscription") or {}).get("platform"),
    }

@api_router.put("/push/preferences")
async def update_push_preferences(data: PushPreferencesUpdate, request: Request):
    """Update radius and target location for an existing push subscription."""
    user = await require_auth(request)
    existing = await db.push_subscriptions.find_one({"user_id": user["_id"], "active": True}, {"_id": 1})
    if not existing:
        raise HTTPException(status_code=404, detail="No active push subscription")

    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.latitude is not None:
        updates["latitude"] = data.latitude
    if data.longitude is not None:
        updates["longitude"] = data.longitude
    if data.radius_meters is not None:
        updates["radius_meters"] = max(100, min(int(data.radius_meters), 5000))

    await db.push_subscriptions.update_one({"_id": existing["_id"]}, {"$set": updates})
    sub = await db.push_subscriptions.find_one({"_id": existing["_id"]}, {"_id": 0})
    saved_location_count = await db.saved_locations.count_documents({"user_id": user["_id"]})
    return {
        "subscribed": True,
        "latitude": sub.get("latitude"),
        "longitude": sub.get("longitude"),
        "radius_meters": sub.get("radius_meters", 500),
        "saved_location_alert_radius_meters": SAVED_LOCATION_ALERT_RADIUS_METERS,
        "saved_location_count": saved_location_count,
        "updated_at": sub.get("updated_at"),
        "platform": (sub.get("subscription") or {}).get("platform"),
    }

# ==================== SOCIAL SHARING ====================

@api_router.get("/reports/{report_id}/share")
async def get_share_data(report_id: str, request: Request):
    """Get shareable data for a report."""
    viewer = await get_current_user(request)
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    report = apply_public_report_privacy(report, viewer)

    municipality = report.get("municipality", "España")
    share_url = build_share_page_url("report", report_id=report_id, city=municipality)
    app_url = build_download_url("report", report_id=report_id, city=municipality)
    created = report.get("created_at", "")

    return {
        "url": share_url,
        "app_url": app_url,
        "title": f"Reporte de caca en {municipality} — Caca Radar",
        "text": f"Nuevo reporte en {municipality}. ¡Ayuda a mantener las calles limpias!",
        "report_id": report_id,
        "municipality": municipality,
        "contributor": sanitize_public_report_identity(report).get("contributor_name", "Anónimo"),
        "created_at": created,
        "photo_url": f"{os.environ.get('FRONTEND_URL', '')}/api/files/{report['photo_url']}" if report.get("photo_url") else None
    }

# ==================== MUNICIPALITY ANALYTICS ====================

@api_router.get("/municipality/analytics")
async def get_municipality_analytics(request: Request):
    """Advanced analytics for municipality dashboard."""
    user = await require_municipality(request)
    return await _get_municipality_analytics_data(user.get("municipality_name", ""))


# ==================== WEBHOOKS ====================

@api_router.post("/webhooks/apple")
async def apple_webhook(request: Request):
    """Apple App Store Server Notifications V2 webhook.
    Apple sends {"signedPayload": "eyJhbGciOiJFUzI1Ni..."} as POST.
    Configure in App Store Connect → App → App Store Server Notifications.
    """
    try:
        body = await request.json()
        signed_payload = body.get("signedPayload")
        if not signed_payload:
            raise HTTPException(status_code=400, detail="Missing signedPayload")

        result = await process_apple_notification(db, signed_payload)

        if result.get("error"):
            logger.error(f"Apple webhook error: {result['error']}")
            # Still return 200 so Apple doesn't retry
            return {"status": "error", "detail": result["error"]}

        logger.info(f"Apple webhook processed: {result.get('event')} for txn {result.get('transaction_id')}")
        return {"status": "received", "event": result.get("event")}

    except Exception as e:
        logger.error(f"Apple webhook exception: {e}")
        return {"status": "error"}

@api_router.post("/webhooks/google")
async def google_webhook(request: Request):
    """Google Play RTDN webhook via Cloud Pub/Sub.
    Pub/Sub sends {"message": {"data": "base64..."}, "subscription": "..."}.
    Configure in Google Play Console → Monetization → Real-time notifications.
    """
    try:
        body = await request.json()
        message = body.get("message", {})
        message_data = message.get("data", "")

        if not message_data:
            raise HTTPException(status_code=400, detail="Missing message data")

        result = await process_google_notification(db, message_data)

        if result.get("error"):
            logger.error(f"Google webhook error: {result['error']}")
            return {"status": "error", "detail": result["error"]}

        logger.info(f"Google webhook processed: {result.get('event')} for token {result.get('purchase_token', '')[:20]}...")
        return {"status": "received", "event": result.get("event")}

    except Exception as e:
        logger.error(f"Google webhook exception: {e}")
        return {"status": "error"}

@api_router.get("/webhooks/status")
async def webhook_status(request: Request):
    """Check webhook configuration status."""
    await _require_admin(request)
    apple_count = await db.webhook_notifications.count_documents({"store": "apple"})
    google_count = await db.webhook_notifications.count_documents({"store": "google"})

    return {
        "apple": {
            "bundle_id_configured": bool(os.environ.get("APPLE_BUNDLE_ID")),
            "notifications_received": apple_count,
            "webhook_url": "/api/webhooks/apple"
        },
        "google": {
            "package_name_configured": bool(os.environ.get("GOOGLE_PACKAGE_NAME")),
            "notifications_received": google_count,
            "webhook_url": "/api/webhooks/google"
        },
        "email": {
            "configured": email_configured(),
            "sender": os.environ.get("SENDER_EMAIL", "no-reply@cacaradar.es")
        }
    }

# ==================== MISC ====================

@api_router.get("/")
async def root():
    return {"message": "Caca Radar API"}

@api_router.get("/health")
async def health():
    return {
        "status": "ok",
        "checks": {
            "process": "ok",
            "readiness_endpoint": "/api/ready",
            "deep_health_endpoint": "/api/health/deep",
        },
    }


READINESS_TIMEOUT_MS = int(os.environ.get("READINESS_TIMEOUT_MS", "5000"))
READINESS_WARN_MS = int(os.environ.get("READINESS_WARN_MS", "1500"))


async def build_readiness_payload(include_runtime: bool = False) -> tuple[dict, int]:
    checks = {
        "status": "ok",
        "database": False,
        "reports_readable": False,
        "users_readable": False,
        "production_db_safe": not is_mongo_local() and db_name != "test_database",
        "timeouts": {
            "readiness_timeout_ms": READINESS_TIMEOUT_MS,
            "warn_threshold_ms": READINESS_WARN_MS,
        },
        "mongo_client": get_mongo_runtime_config(),
    }
    started = time.perf_counter()

    async def run_probe(name: str, operation):
        probe_started = time.perf_counter()
        try:
            result = await asyncio.wait_for(operation, timeout=READINESS_TIMEOUT_MS / 1000)
            checks[f"{name}_latency_ms"] = round((time.perf_counter() - probe_started) * 1000, 1)
            return result
        except Exception as e:
            checks[f"{name}_latency_ms"] = round((time.perf_counter() - probe_started) * 1000, 1)
            checks[f"{name}_error"] = str(e)
            raise

    try:
        result = await run_probe("database", db.command("ping"))
        checks["database"] = result.get("ok") == 1.0
    except Exception:
        checks["status"] = "error"
        checks["total_duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
        if include_runtime:
            checks["runtime"] = get_runtime_metadata()
        return checks, 503

    try:
        await run_probe("reports_read", db.reports.find_one({}, {"_id": 1}))
        checks["reports_readable"] = True
    except Exception:
        checks["status"] = "degraded"

    try:
        await run_probe("users_read", db.users.find_one({}, {"_id": 1}))
        checks["users_readable"] = True
    except Exception:
        checks["status"] = "degraded"

    checks["total_duration_ms"] = round((time.perf_counter() - started) * 1000, 1)
    if checks["total_duration_ms"] > READINESS_WARN_MS and checks["status"] == "ok":
        checks["warning"] = "Readiness checks exceeded the warning threshold."

    if not checks["production_db_safe"]:
        checks["status"] = "error"

    status_code = 200 if checks["status"] == "ok" else 503
    if include_runtime:
        checks["runtime"] = get_runtime_metadata()
    return checks, status_code


@api_router.get("/ready")
async def ready():
    payload, status_code = await build_readiness_payload(include_runtime=False)
    return JSONResponse(content=payload, status_code=status_code)


@api_router.get("/version")
async def version():
    """Return release/runtime metadata without infrastructure internals."""
    metadata = get_runtime_metadata()
    return {
        "environment": metadata["environment"],
        "commit": metadata["commit"],
        "started_at": metadata["started_at"],
        "backend_version": metadata["backend_version"],
        "app_versions": metadata["app_versions"],
    }


@api_router.get("/health/deep")
async def health_deep():
    """Deep health check — verifies database connectivity and read access."""
    payload, status_code = await build_readiness_payload(include_runtime=True)
    return JSONResponse(content=payload, status_code=status_code)


@api_router.get("/health/auth")
async def health_auth(request: Request):
    """Diagnose GIS-based Google sign-in configuration."""
    await _require_admin(request)
    client_ids = get_google_client_ids()
    checks = {
        "google_client_id_configured": bool(GOOGLE_WEB_CLIENT_ID),
        "allowed_client_ids_count": len(client_ids),
        "status": "ok" if client_ids else "degraded",
    }
    if not client_ids:
        checks["message"] = "Set GOOGLE_WEB_CLIENT_ID and optionally GOOGLE_ALLOWED_CLIENT_IDS"
    return checks


@api_router.get("/admin/report-diagnostics")
async def report_diagnostics(
    request: Request,
    municipality: Optional[str] = None,
    province: Optional[str] = None,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lng_min: Optional[float] = None,
    lng_max: Optional[float] = None,
):
    """Report diagnostics for admins — counts by city, timestamps, runtime info."""
    user = await require_auth(request)
    if user.get("role") not in ("admin", "municipality"):
        raise HTTPException(status_code=403, detail="Admin access required")

    query = {}
    if municipality:
        query["municipality"] = {"$regex": municipality, "$options": "i"}
    if province:
        query["province"] = {"$regex": province, "$options": "i"}
    if lat_min is not None or lat_max is not None:
        query["latitude"] = {}
        if lat_min is not None:
            query["latitude"]["$gte"] = lat_min
        if lat_max is not None:
            query["latitude"]["$lte"] = lat_max
    if lng_min is not None or lng_max is not None:
        query["longitude"] = {}
        if lng_min is not None:
            query["longitude"]["$gte"] = lng_min
        if lng_max is not None:
            query["longitude"]["$lte"] = lng_max

    pipeline = [
        {"$group": {"_id": {"municipality": "$municipality", "province": "$province"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    city_counts = await db.reports.aggregate(pipeline).to_list(100)

    earliest = await db.reports.find_one({}, {"_id": 0, "created_at": 1}, sort=[("created_at", 1)])
    latest = await db.reports.find_one({}, {"_id": 0, "created_at": 1}, sort=[("created_at", -1)])

    total_reports = await db.reports.count_documents({})
    total_users = await db.users.count_documents({})
    total_audit = await db.report_audit_log.count_documents({})
    matching_reports = await db.reports.find(
        query,
        {"_id": 0, "id": 1, "user_id": 1, "latitude": 1, "longitude": 1, "municipality": 1, "province": 1, "created_at": 1, "category": 1, "archived": 1, "flagged": 1}
    ).sort("created_at", -1).limit(100).to_list(100)

    runtime = get_runtime_metadata()

    return {
        "runtime": {
            "db_name": db_name,
            "mongo_is_local": is_mongo_local(),
            "mongo_url": redacted_mongo_url(),
            "environment": APP_ENV,
            "commit": runtime["commit"],
            "started_at": runtime["started_at"],
        },
        "counts": {
            "total_reports": total_reports,
            "total_users": total_users,
            "total_audit_entries": total_audit,
            "matching_reports": await db.reports.count_documents(query),
        },
        "reports_by_city": [
            {
                "city": (r["_id"] or {}).get("municipality") or "Unknown",
                "province": (r["_id"] or {}).get("province") or "",
                "count": r["count"],
            }
            for r in city_counts
        ],
        "earliest_report": earliest.get("created_at") if earliest else None,
        "latest_report": latest.get("created_at") if latest else None,
        "query": query,
        "matching_reports": matching_reports,
    }


@api_router.get("/admin/report-audit")
async def admin_report_audit(
    request: Request,
    email: Optional[str] = None,
    report_id: Optional[str] = None,
    municipality: Optional[str] = None,
    limit: int = 100,
):
    user = await require_auth(request)
    if user.get("role") not in ("admin", "municipality"):
        raise HTTPException(status_code=403, detail="Admin access required")

    query = {}
    if email:
        query["user_email"] = email.lower()
    if report_id:
        query["report_id"] = report_id
    if municipality:
        query["municipality"] = {"$regex": municipality, "$options": "i"}

    safe_limit = max(1, min(limit, 500))
    events = await db.report_audit_log.find(query, {"_id": 0}).sort("created_at", -1).limit(safe_limit).to_list(safe_limit)
    return {"runtime": get_runtime_metadata(), "total": await db.report_audit_log.count_documents(query), "events": events}

# Include router
app.include_router(api_router)

# CORS — custom middleware to handle Capacitor + web origins.
# The Kubernetes ingress proxy overwrites CORS headers with wildcard.
# We set Vary: Origin to signal the proxy not to cache/override,
# and include our headers so they take precedence where possible.

def _parse_additional_allowed_origins() -> set[str]:
    raw = os.environ.get("ADDITIONAL_ALLOWED_ORIGINS", "")
    return {
        origin.strip().rstrip("/")
        for origin in raw.split(",")
        if origin.strip()
    }


def _normalize_origin_value(value: str) -> str:
    parsed = urlparse((value or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}".rstrip("/")


ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://localhost",
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
    "https://caca-radar.emergent.host",
    "https://cacaradar.es",
    "https://www.cacaradar.es",
    "capacitor://localhost",
    "ionic://localhost",
} | _parse_additional_allowed_origins()
ALLOWED_BROWSER_ORIGINS = {origin for origin in ALLOWED_ORIGINS if origin.startswith("http://") or origin.startswith("https://")}
ALLOWED_CORS_HEADERS = "Authorization, Content-Type, X-App-Version, X-App-Environment, X-Platform, X-Native-App"
CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def is_allowed_origin(origin: str) -> bool:
    return origin in ALLOWED_ORIGINS


def resolve_browser_origin(request: Request) -> str:
    origin = _normalize_origin_value(request.headers.get("origin", ""))
    if origin:
        return origin
    return _normalize_origin_value(request.headers.get("referer", ""))


def requires_browser_origin_check(request: Request) -> bool:
    if request.method.upper() not in CSRF_PROTECTED_METHODS:
        return False
    if is_explicit_native_app_request(request):
        return False
    return bool(request.cookies.get("access_token") or request.cookies.get("refresh_token"))

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "").rstrip("/")
    is_allowed = is_allowed_origin(origin)

    if requires_browser_origin_check(request):
        browser_origin = resolve_browser_origin(request)
        if not browser_origin or browser_origin not in ALLOWED_BROWSER_ORIGINS:
            return JSONResponse(status_code=403, content={"detail": "Origen no permitido"})

    # Handle preflight OPTIONS
    if request.method == "OPTIONS":
        if origin and not is_allowed:
            return Response(status_code=403, headers={"Vary": "Origin"})
        headers = {
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": request.headers.get("access-control-request-headers", ALLOWED_CORS_HEADERS),
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }
        if is_allowed and origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        return Response(status_code=200, headers=headers)

    response = await call_next(request)

    # Set CORS on all responses
    if is_allowed and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
    response.headers["Access-Control-Allow-Headers"] = ALLOWED_CORS_HEADERS

    return response

# Startup helpers

async def init_database():
    """Create MongoDB indexes."""
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", sparse=True)
    await db.reports.create_index("id", unique=True)
    await db.reports.create_index([("latitude", 1), ("longitude", 1)])
    await db.reports.create_index("municipality")
    await db.reports.create_index("user_id")
    await db.reports.create_index("photo_status")
    await db.votes.create_index([("report_id", 1), ("user_id", 1)], unique=True)
    await db.flags.create_index([("report_id", 1), ("user_id", 1)], unique=True)
    await db.flags.create_index("municipality")
    await db.login_attempts.create_index("identifier")
    await db.municipalities.create_index([("name", 1), ("province", 1)], unique=True)
    await db.validations.create_index([("report_id", 1), ("user_id", 1)], unique=True)
    await db.report_votes.create_index([("report_id", 1), ("user_id", 1)], unique=True)
    await db.trust_log.create_index("user_id")
    await db.webhook_notifications.create_index("store")
    await db.webhook_notifications.create_index("received_at")
    await db.webhook_processing_log.create_index("user_id")
    await db.push_subscriptions.create_index("user_id", unique=True)
    await db.push_subscriptions.create_index([("latitude", 1), ("longitude", 1)])
    await db.barrio_cache.create_index([("lat", 1), ("lng", 1)], unique=True)
    await db.notifications.create_index([("user_id", 1), ("read", 1)])
    await db.admin_codes.create_index("email", unique=True)
    await db.password_resets.create_index("token_hash", unique=True, sparse=True)
    await db.password_resets.create_index("email")
    await db.security_rate_limits.create_index("key", unique=True)
    await db.security_rate_limits.create_index("expires_at", expireAfterSeconds=0)
    await db.report_audit_log.create_index("event")
    await db.report_audit_log.create_index("report_id")
    await db.report_audit_log.create_index("user_id")
    await db.report_audit_log.create_index("user_email")
    await db.report_audit_log.create_index("created_at")
    await db.report_audit_log.create_index([("latitude", 1), ("longitude", 1)])

def env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def startup_seeding_enabled() -> bool:
    return not is_production_env()


def credentials_report_enabled() -> bool:
    return not is_production_env() and env_flag("WRITE_STARTUP_CREDENTIAL_REPORT")


def generated_seed_password(label: str) -> str:
    return f"{label}-{secrets.token_urlsafe(18)}"


async def provision_privileged_accounts(selected_accounts: set[str] | None = None) -> dict | None:
    accounts = selected_accounts or {"admin", "demo_muni", "review"}

    admin_email = os.environ.get("ADMIN_EMAIL", "jefe@cacaradar.es")
    admin_password = os.environ.get("ADMIN_PASSWORD") or (
        generated_seed_password("admin") if not is_production_env() else None
    )
    demo_muni_email = os.environ.get("DEMO_MUNI_EMAIL", "madrid@cacaradar.es")
    demo_muni_password = os.environ.get("DEMO_MUNI_PASSWORD") or (
        generated_seed_password("municipality") if not is_production_env() else None
    )
    review_email = os.environ.get("APP_REVIEW_EMAIL", "appletest@cacaradar.es").lower()
    review_password = os.environ.get("APP_REVIEW_PASSWORD") or (
        generated_seed_password("app-review") if not is_production_env() else None
    )

    if is_production_env():
        missing_credentials = []
        if "admin" in accounts and not admin_password:
            missing_credentials.append("ADMIN_PASSWORD")
        if "demo_muni" in accounts and not demo_muni_password:
            missing_credentials.append("DEMO_MUNI_PASSWORD")
        if "review" in accounts and not review_password:
            missing_credentials.append("APP_REVIEW_PASSWORD")
        if missing_credentials:
            raise RuntimeError(
                "FATAL: secure credentials were not provided for: "
                + ", ".join(missing_credentials)
            )

    seeded: dict[str, str] = {}

    if "admin" in accounts:
        existing = await db.users.find_one({"email": admin_email})
        if existing is None:
            await db.users.insert_one({
                "email": admin_email, "password_hash": hash_password(admin_password),
                "name": "El Jefe", "username": "el_jefe", "role": "admin",
                "subscription_active": True, "subscription_type": "annual",
                "total_score": 0, "trust_score": 100, "rank": "Admin", "level": 10,
                "report_count": 0, "vote_count": 0, "streak_days": 0,
                "created_at": datetime.now(timezone.utc)
            })
            logger.info("Admin user created")
        elif not verify_password(admin_password, existing["password_hash"]):
            await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        seeded["admin_email"] = admin_email
        seeded["admin_password"] = admin_password

    if "demo_muni" in accounts:
        if not await db.users.find_one({"email": demo_muni_email}):
            await db.users.insert_one({
                "email": demo_muni_email, "password_hash": hash_password(demo_muni_password),
                "name": "Ayuntamiento de Madrid", "role": "municipality",
                "municipality_name": "Madrid", "municipality_province": "Madrid",
                "municipality_subscription_active": True, "municipality_subscription_type": "annual",
                "email_verified": True,
                "created_at": datetime.now(timezone.utc)
            })
            logger.info("Demo municipality user created")
        seeded["demo_muni_email"] = demo_muni_email
        seeded["demo_muni_password"] = demo_muni_password

    if "review" in accounts:
        review_username = os.environ.get("APP_REVIEW_USERNAME", "appletest").lower()
        review_user = await db.users.find_one({"email": review_email})
        review_updates = {
            "email": review_email,
            "name": "Apple Review",
            "username": review_username,
            "role": "user",
            "auth_provider": "password",
            "auth_methods": ["password"],
            "linked_providers": {},
            "subscription_active": True,
            "subscription_type": "lifetime",
            "subscription_expires": None,
            "geo_review_exempt": True,
            "trust_score": 50,
            "rank": DEFAULT_RANK_NAME,
            "rank_key": get_rank_key(DEFAULT_RANK_NAME),
            "level": 1,
            "report_count": 0,
            "vote_count": 0,
            "daily_report_count": 0,
            "streak_days": 0,
            "last_active_date": None,
        }
        if review_user is None:
            await db.users.insert_one({
                **review_updates,
                "password_hash": hash_password(review_password),
                "total_score": 0,
                "created_at": datetime.now(timezone.utc),
            })
            logger.info("App review user created")
        else:
            review_mutations = dict(review_updates)
            if not verify_password(review_password, review_user.get("password_hash", "")):
                review_mutations["password_hash"] = hash_password(review_password)
            await db.users.update_one({"_id": review_user["_id"]}, {"$set": review_mutations})
        seeded["review_email"] = review_email
        seeded["review_password"] = review_password
        seeded["review_username"] = review_username

    return seeded or None


async def seed_users():
    """Create admin, review, and demo municipality accounts in non-production environments."""
    if not startup_seeding_enabled():
        logger.info("Startup user seeding skipped for this environment")
        return None
    return await provision_privileged_accounts()

async def run_maintenance():
    """Archive expired reports, deactivate expired subscriptions, recalculate ranks."""
    await archive_expired_reports()
    await reset_daily_counts(db)

    # Deactivate expired subscriptions (skip VIP/lifetime)
    now_iso = datetime.now(timezone.utc).isoformat()
    expired = await db.users.update_many(
        {"subscription_active": True, "subscription_expires": {"$lt": now_iso, "$ne": None}, "subscription_type": {"$ne": "lifetime"}},
        {"$set": {"subscription_active": False}}
    )
    if expired.modified_count > 0:
        logger.info(f"Deactivated {expired.modified_count} expired subscriptions")

    # Recalculate ranks and store notifications
    rank_count, rank_changes = await recalculate_all_ranks(db)
    for rc in rank_changes:
        await db.notifications.insert_one({
            "user_id": rc["user_id"], "type": "rank_change",
            "old_rank": rc["old_rank"], "new_rank": rc["new_rank"],
            "old_rank_key": rc.get("old_rank_key"), "new_rank_key": rc.get("new_rank_key"),
            "read": False, "created_at": datetime.now(timezone.utc).isoformat()
        })
    logger.info(f"Ranks recalculated for {rank_count} users, {len(rank_changes)} changes")

# Startup
@app.on_event("startup")
async def startup():
    await init_storage_async()
    await init_database()
    seeded_credentials = await seed_users()
    await run_maintenance()

    if seeded_credentials and credentials_report_enabled():
        try:
            os.makedirs("/app/memory", exist_ok=True)
            with open("/app/memory/test_credentials.md", "w") as f:
                f.write("# Test Credentials\n\n")
                f.write(f"## Admin\n- Email: {seeded_credentials['admin_email']}\n- Password: {seeded_credentials['admin_password']}\n- Role: admin\n\n")
                f.write(f"## Demo Municipality\n- Email: {seeded_credentials['demo_muni_email']}\n- Password: {seeded_credentials['demo_muni_password']}\n- Role: municipality\n- Municipality: Madrid\n\n")
                f.write(f"## App Review\n- Email: {seeded_credentials['review_email']}\n- Username: {seeded_credentials['review_username']}\n- Password: {seeded_credentials['review_password']}\n- Role: user\n- VIP Access: true\n- Geo Review Exempt: true\n\n")
                f.write("## Auth Endpoints\n- POST /api/auth/register\n- POST /api/auth/login\n- POST /api/auth/google/login\n- POST /api/auth/google/link\n- POST /api/auth/logout\n- GET /api/auth/me\n")
                f.write("## Municipality Endpoints\n- POST /api/municipality/register (with domain verification)\n- POST /api/municipality/verify\n- POST /api/municipality/resend-verification\n- GET /api/municipality/stats\n- GET /api/municipality/reports\n- GET /api/municipality/flags\n- POST /api/municipality/moderate/{report_id}\n")
                f.write("## Subscription Endpoints\n- POST /api/users/subscribe (mock)\n- POST /api/users/subscribe/apple (receipt verification)\n- POST /api/users/subscribe/google (receipt verification)\n- GET /api/users/subscription-status\n")
                f.write("\n## Webhook Endpoints\n")
                f.write("- POST /api/webhooks/apple (App Store Server Notifications V2)\n")
                f.write("- POST /api/webhooks/google (Google Play RTDN via Pub/Sub)\n")
                f.write("- GET /api/webhooks/status (check configuration)\n")
                f.write("\n## Email Service\n")
                f.write(f"- Configured: {email_configured()}\n")
                f.write(f"- Sender: {os.environ.get('SENDER_EMAIL', 'no-reply@cacaradar.es')}\n")
                f.write("- Set RESEND_API_KEY in .env for real emails (get key from resend.com)\n")
        except Exception:
            logger.warning("Could not write test_credentials.md (non-critical)")

    logger.info("Startup complete")

@app.on_event("shutdown")
async def shutdown():
    await close_http_client()
    client.close()
