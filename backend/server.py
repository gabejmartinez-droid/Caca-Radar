from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, UploadFile, File, Query, Response, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import uuid
import bcrypt
import jwt
import requests
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal
import random
import string
import asyncio

# Import gamification services
from scoring_service import (
    calc_report_points, calc_vote_points, update_streak, reset_daily_counts,
    HOT_ZONE_BONUS
)
from antispam_service import (
    check_cooldown, check_proximity_duplicate, check_gps_plausible,
    detect_spam_patterns, update_trust_score, is_hot_zone,
    get_trust_tier, TRUST_SPAM_BEHAVIOR, TRUST_DOWNVOTED_REPORT, TRUST_UPVOTED_REPORT_MIN
)
from validation_service import process_validation
from ranking_service import recalculate_all_ranks, get_user_rank_info
from email_service import send_verification_code as send_verification_email, is_configured as email_configured
from webhook_handlers import process_apple_notification, process_google_notification
from push_service import notify_nearby_users, VAPID_PUBLIC_KEY
from badges_service import check_and_award_badges, get_user_badges, calc_confidence_score, get_freshness_label, calc_neighborhood_cleanliness
from clean_route_service import analyze_clean_route
from digest_service import send_weekly_digests, generate_municipality_digest

# App Store placeholder URLs
APP_STORE_URL = "https://apps.apple.com/app/caca-radar/id000000000"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.cacaradar.app"

# ==================== RECEIPT VERIFICATION ====================

# Apple App Store verification
APPLE_KEY_ID = os.environ.get("APPLE_KEY_ID")
APPLE_ISSUER_ID = os.environ.get("APPLE_ISSUER_ID")
APPLE_BUNDLE_ID = os.environ.get("APPLE_BUNDLE_ID")
APPLE_KEY_PATH = os.environ.get("APPLE_KEY_PATH")  # Path to .p8 key file
APPLE_ENVIRONMENT = os.environ.get("APPLE_ENVIRONMENT", "Sandbox")  # "Production" or "Sandbox"

# Google Play verification
GOOGLE_SERVICE_ACCOUNT_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH")
GOOGLE_PACKAGE_NAME = os.environ.get("GOOGLE_PACKAGE_NAME")

async def verify_apple_receipt(receipt_data: str, transaction_id: str = None) -> dict:
    """Verify Apple App Store receipt using App Store Server API v2."""
    if not all([APPLE_KEY_ID, APPLE_ISSUER_ID, APPLE_BUNDLE_ID, APPLE_KEY_PATH]):
        logger.warning("Apple credentials not configured — using mock verification")
        return {"valid": True, "mock": True, "product_id": "premium_monthly", "expires": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()}

    try:
        from appstoreserverlibrary.api_client import AppStoreServerAPIClient, APIException
        from appstoreserverlibrary.models.Environment import Environment
        from appstoreserverlibrary.receipt_utility import ReceiptUtility
        from appstoreserverlibrary.signed_data_verifier import SignedDataVerifier, VerificationException

        env = Environment.PRODUCTION if APPLE_ENVIRONMENT == "Production" else Environment.SANDBOX

        # Read private key
        with open(APPLE_KEY_PATH, 'r') as f:
            signing_key = f.read()

        client = AppStoreServerAPIClient(signing_key, APPLE_KEY_ID, APPLE_ISSUER_ID, APPLE_BUNDLE_ID, env)

        # Extract transaction ID from receipt if not provided
        if not transaction_id and receipt_data:
            receipt_util = ReceiptUtility()
            transaction_id = receipt_util.extract_transaction_id_from_app_receipt(receipt_data)

        if not transaction_id:
            return {"valid": False, "error": "No transaction ID found"}

        # Get transaction info
        response = client.get_transaction_info(transaction_id)
        return {
            "valid": True,
            "mock": False,
            "transaction_id": transaction_id,
            "product_id": getattr(response, 'product_id', 'unknown'),
            "expires": getattr(response, 'expires_date', None)
        }
    except Exception as e:
        logger.error(f"Apple receipt verification failed: {e}")
        return {"valid": False, "error": str(e)}

async def verify_google_receipt(purchase_token: str, subscription_id: str) -> dict:
    """Verify Google Play subscription using Google Play Developer API."""
    if not all([GOOGLE_SERVICE_ACCOUNT_PATH, GOOGLE_PACKAGE_NAME]):
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

        result = service.purchases().subscriptions().get(
            packageName=GOOGLE_PACKAGE_NAME,
            subscriptionId=subscription_id,
            token=purchase_token
        ).execute()

        expiry_millis = int(result.get('expiryTimeMillis', 0))
        expiry = datetime.fromtimestamp(expiry_millis / 1000, tz=timezone.utc) if expiry_millis else None

        return {
            "valid": True,
            "mock": False,
            "product_id": subscription_id,
            "expires": expiry.isoformat() if expiry else None,
            "payment_state": result.get('paymentState'),
            "auto_renewing": result.get('autoRenewing', False)
        }
    except Exception as e:
        logger.error(f"Google receipt verification failed: {e}")
        return {"valid": False, "error": str(e)}

# ==================== DOMAIN VERIFICATION ====================

# Allowed municipality email domains
ALLOWED_MUNICIPALITY_DOMAINS = [
    ".es", ".gob.es", ".org", ".cat", ".eus", ".gal",
    "ayuntamiento", "ajuntament", "concello", "udala",
    "diputacion", "gobierno", "junta"
]

def is_valid_municipality_email(email: str) -> bool:
    """Check if email domain looks like an official municipality domain."""
    domain = email.split("@")[1].lower() if "@" in email else ""
    # Block common free email providers
    blocked = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com", "icloud.com", "protonmail.com", "mail.com"]
    if domain in blocked:
        return False
    # Check if domain matches allowed patterns
    for pattern in ALLOWED_MUNICIPALITY_DOMAINS:
        if pattern in domain:
            return True
    # Allow any non-blocked domain (some small municipalities use local ISPs)
    return True

def generate_verification_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

# Password hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# JWT Token Management
def create_access_token(user_id: str, email: str, role: str = "user") -> str:
    payload = {"sub": user_id, "email": email, "role": role, "exp": datetime.now(timezone.utc) + timedelta(minutes=15), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

# Object Storage
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "caca-radar"
storage_key = None

def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        logger.info("Storage initialized successfully")
        return storage_key
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Reverse Geocoding via Nominatim
def reverse_geocode(lat: float, lon: float) -> dict:
    """Get municipality info from coordinates using Nominatim."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "addressdetails": 1, "zoom": 14},
            headers={"User-Agent": "CacaRadar/1.0"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        address = data.get("address", {})
        
        # Try to get municipality name from various fields
        municipality = (
            address.get("city") or
            address.get("town") or
            address.get("village") or
            address.get("municipality") or
            address.get("county") or
            "Desconocido"
        )
        
        province = address.get("state") or address.get("province") or ""
        country = address.get("country") or "España"
        
        return {
            "municipality": municipality,
            "province": province,
            "country": country,
            "display_name": data.get("display_name", "")
        }
    except Exception as e:
        logger.error(f"Reverse geocode failed: {e}")
        return {"municipality": "Desconocido", "province": "", "country": "España", "display_name": ""}

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    username: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

REPORT_CATEGORIES = ["dog_feces", "trash", "noise", "graffiti", "broken_infrastructure", "other"]

class ReportCreate(BaseModel):
    latitude: float
    longitude: float
    description: Optional[str] = None
    category: Optional[str] = "dog_feces"

class VoteCreate(BaseModel):
    vote_type: Literal["still_there", "cleaned"]

class ReportVote(BaseModel):
    vote_type: Literal["upvote", "downvote"]

class ValidationCreate(BaseModel):
    vote: Literal["confirm", "reject"]

FLAG_REASONS = ["license_plate", "face", "name", "personal_info", "inappropriate", "spam", "other"]

class FlagCreate(BaseModel):
    reason: str

class UsernameUpdate(BaseModel):
    username: str

class MunicipalityLogin(BaseModel):
    email: EmailStr
    password: str

class MunicipalityRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    municipality_name: str
    province: Optional[str] = None

class ModerationAction(BaseModel):
    action: Literal["hide", "restore", "dismiss"]

class AppleReceiptVerify(BaseModel):
    receipt_data: Optional[str] = None
    transaction_id: Optional[str] = None
    plan: Literal["monthly", "annual"]

class GoogleReceiptVerify(BaseModel):
    purchase_token: str
    subscription_id: str
    plan: Literal["monthly", "annual"]

class MunicipalityVerify(BaseModel):
    email: EmailStr
    code: str

class MunicipalityResendVerification(BaseModel):
    email: EmailStr

class PushSubscriptionCreate(BaseModel):
    subscription: dict
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SavedLocationCreate(BaseModel):
    name: str  # "home", "work", "custom"
    latitude: float
    longitude: float
    label: Optional[str] = None

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Auth helper
async def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        return None
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            return None
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except Exception:
        return None

async def require_auth(request: Request) -> dict:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user

async def require_subscriber(request: Request) -> dict:
    user = await require_auth(request)
    if not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")
    return user

async def require_municipality(request: Request) -> dict:
    user = await get_current_user(request)
    if not user or user.get("role") not in ["municipality", "admin"]:
        raise HTTPException(status_code=403, detail="Acceso de municipio requerido")
    return user

async def require_registered(request: Request) -> dict:
    """Require a registered user for reports and votes."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Debes registrarte para realizar esta acción. ¡Es gratis!")
    return user

def get_anonymous_id(request: Request) -> str:
    """Legacy anonymous ID for backward compatibility with existing data."""
    anon_id = request.cookies.get("anon_id")
    if not anon_id:
        anon_id = str(uuid.uuid4())
    return anon_id

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(data: UserRegister, response: Response):
    email = data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    if data.username:
        existing_username = await db.users.find_one({"username": data.username.lower()})
        if existing_username:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    hashed = hash_password(data.password)
    user_doc = {
        "email": email,
        "password_hash": hashed,
        "name": data.name or email.split("@")[0],
        "username": data.username.lower() if data.username else None,
        "role": "user",
        "subscription_active": False,
        "subscription_type": None,
        "subscription_expires": None,
        "total_score": 0,
        "trust_score": 50,
        "rank": "Aspirante Cagón",
        "level": 1,
        "report_count": 0,
        "vote_count": 0,
        "daily_report_count": 0,
        "streak_days": 0,
        "last_active_date": None,
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id, "email": email, "name": user_doc["name"],
        "username": user_doc["username"], "role": "user",
        "subscription_active": False, "report_count": 0, "vote_count": 0,
        "total_score": 0, "trust_score": 50, "rank": "Aspirante Cagón", "level": 1,
        "streak_days": 0
    }

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
    if not user or not verify_password(data.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc)}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    await db.login_attempts.delete_one({"identifier": identifier})
    
    user_id = str(user["_id"])
    role = user.get("role", "user")
    access_token = create_access_token(user_id, email, role)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id, "email": email, "name": user.get("name", ""),
        "username": user.get("username"), "role": role,
        "subscription_active": user.get("subscription_active", False),
        "subscription_type": user.get("subscription_type"),
        "report_count": user.get("report_count", 0),
        "vote_count": user.get("vote_count", 0),
        "municipality_name": user.get("municipality_name"),
        "total_score": user.get("total_score", 0),
        "trust_score": user.get("trust_score", 50),
        "rank": user.get("rank", "Aspirante Cagón"),
        "level": user.get("level", 1),
        "streak_days": user.get("streak_days", 0)
    }

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
    return user

@api_router.post("/auth/refresh")
async def refresh_token_endpoint(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        access_token = create_access_token(str(user["_id"]), user["email"], user.get("role", "user"))
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== USER PROFILE ====================

@api_router.put("/users/username")
async def update_username(data: UsernameUpdate, request: Request):
    user = await require_auth(request)
    if not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium para elegir nombre de usuario")
    
    username = data.username.lower().strip()
    if len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="El nombre de usuario debe tener entre 3 y 20 caracteres")
    
    existing = await db.users.find_one({"username": username, "_id": {"$ne": ObjectId(user["_id"])}})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    
    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"username": username}})
    return {"username": username}

@api_router.post("/users/subscribe")
async def subscribe_user(request: Request):
    """Subscription: €3.99/month or €29.99/year with 7-day free trial."""
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

@api_router.get("/reports")
async def get_reports(
    municipality: Optional[str] = None,
    category: Optional[str] = None,
    freshness: Optional[str] = None,
    status: Optional[str] = None,
    confirmed_only: Optional[bool] = None
):
    query = {"archived": {"$ne": True}, "flagged": {"$ne": True}}
    if municipality:
        query["municipality"] = municipality
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    if confirmed_only:
        query["status"] = "verified"

    reports = await db.reports.find(query, {"_id": 0}).to_list(2000)

    # Add freshness labels and confidence scores
    for r in reports:
        r["freshness"] = get_freshness_label(r.get("created_at", ""))
        r["confidence"] = calc_confidence_score(r)
        r["is_premium_report"] = r.get("contributor_rank") is not None
        if "contributor_name" not in r:
            r["contributor_name"] = "Anónimo"
            r["contributor_rank"] = None

    # Filter by freshness if requested
    if freshness:
        reports = [r for r in reports if r["freshness"] == freshness]

    return reports

@api_router.get("/reports/{report_id}")
async def get_report(report_id: str):
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    report["freshness"] = get_freshness_label(report.get("created_at", ""))
    report["confidence"] = calc_confidence_score(report)
    report["is_premium_report"] = report.get("contributor_rank") is not None
    return report

@api_router.post("/reports")
async def create_report(request: Request, data: ReportCreate, response: Response):
    user = await require_registered(request)
    user_id = user["_id"]

    await validate_report_input(db, data, user, user_id)

    is_duplicate = await check_proximity_duplicate(db, data.latitude, data.longitude)
    geo = reverse_geocode(data.latitude, data.longitude)
    report_id = str(uuid.uuid4())

    report_doc = build_report_doc(report_id, data, user_id, user, geo, is_duplicate)
    await db.reports.insert_one(report_doc)

    points_result = await process_report_scoring(db, user, user_id, data, is_duplicate)
    await upsert_municipality(db, geo)

    report_doc.pop("_id", None)
    report_doc["points_earned"] = points_result["points"]
    report_doc["points_breakdown"] = points_result["breakdown"]

    asyncio.create_task(notify_nearby_users(db, data.latitude, data.longitude, report_id, geo["municipality"]))
    return report_doc

# ==================== REPORT HELPERS ====================

async def validate_report_input(db, data: ReportCreate, user: dict, user_id: str) -> None:
    """Validate anti-spam rules before creating a report."""
    if not await check_gps_plausible(data.latitude, data.longitude):
        raise HTTPException(status_code=400, detail="Ubicación fuera de España")
    if user is not None and await check_cooldown(db, user_id):
        raise HTTPException(status_code=429, detail="Espera al menos 60 segundos entre reportes")
    if user is not None:
        tier = get_trust_tier(user.get("trust_score", 50))
        if tier == "restricted":
            raise HTTPException(status_code=403, detail="Tu cuenta está restringida por comportamiento sospechoso")

def build_report_doc(report_id: str, data: ReportCreate, user_id: str, user: dict, geo: dict, is_duplicate: bool) -> dict:
    """Build the report document for insertion."""
    category = data.category if data.category in REPORT_CATEGORIES else "dog_feces"
    doc = {
        "id": report_id, "latitude": data.latitude, "longitude": data.longitude,
        "photo_url": None, "description": data.description, "category": category,
        "created_at": datetime.now(timezone.utc).isoformat(), "status": "pending",
        "status_score": 0, "still_there_count": 0, "cleaned_count": 0,
        "upvotes": 0, "downvotes": 0, "validation_count": 0,
        "user_id": user_id, "contributor_name": "Anónimo", "contributor_rank": None,
        "municipality": geo["municipality"], "province": geo["province"], "country": geo["country"],
        "archived": False, "flagged": False, "flag_count": 0, "is_duplicate_proximity": is_duplicate
    }
    if user and user.get("subscription_active"):
        doc["contributor_name"] = user.get("username") or user.get("name", "Anónimo")
        doc["contributor_rank"] = user.get("rank", "Aspirante Cagón")
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
    verified = await db.reports.count_documents({"municipality": muni_name, "status": "verified"})
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
    return {"reports_30d": reports_30d, "reports_trend": trend, "verified": verified, "avg_resolution_hours": avg_res, "flag_rate": flag_rate}

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
    labels = {"pending": "Pendiente", "verified": "Verificado", "rejected": "Rechazado", "archived": "Archivado"}
    result = []
    for status in ["pending", "verified", "rejected"]:
        c = await db.reports.count_documents({"municipality": muni_name, "status": status})
        if c > 0:
            result.append({"status": labels[status], "count": c})
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

@api_router.post("/reports/{report_id}/photo")
async def upload_photo(report_id: str, request: Request, file: UploadFile = File(...)):
    # Premium-only photo uploads
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="La subida de fotos es una función Premium")

    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (max 5MB)")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    path = f"{APP_NAME}/reports/{report_id}/{uuid.uuid4()}.{ext}"
    
    result = put_object(path, data, file.content_type or "image/jpeg")
    
    await db.reports.update_one({"id": report_id}, {"$set": {"photo_url": result["path"]}})
    
    # Award photo bonus points to report creator
    report = await db.reports.find_one({"id": report_id})
    if report:
        reporter_id = report.get("user_id", "")
        try:
            reporter = await db.users.find_one({"_id": ObjectId(reporter_id)})
            if reporter:
                from scoring_service import REPORT_PHOTO_BONUS
                await db.users.update_one({"_id": ObjectId(reporter_id)}, {"$inc": {"total_score": REPORT_PHOTO_BONUS}})
        except Exception:
            pass
    
    return {"photo_url": result["path"]}

@api_router.get("/files/{path:path}")
async def get_file(path: str):
    try:
        data, content_type = get_object(path)
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
    
    existing_vote = await db.votes.find_one({"report_id": report_id, "user_id": user_id})
    if existing_vote:
        raise HTTPException(status_code=400, detail="Ya has votado en este reporte")
    
    vote_doc = {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "user_id": user_id,
        "vote_type": data.vote_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.votes.insert_one(vote_doc)
    
    if data.vote_type == "still_there":
        await db.reports.update_one({"id": report_id}, {"$inc": {"still_there_count": 1, "status_score": 1}})
    else:
        await db.reports.update_one({"id": report_id}, {"$inc": {"cleaned_count": 1, "status_score": -1}})
    
    # Increment user vote count
    if user:
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"vote_count": 1}})
    
    # Auto-archive if cleaned votes >= 3
    updated_report = await db.reports.find_one({"id": report_id})
    if updated_report.get("cleaned_count", 0) >= 3:
        await db.reports.update_one({"id": report_id}, {"$set": {"archived": True}})
    
    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")
    
    return {"message": "Voto registrado", "vote_type": data.vote_type}

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
    result = await process_validation(db, report_id, user_id, data.vote, is_sub)

    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")

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

    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id

    # Check existing vote
    existing = await db.report_votes.find_one({"report_id": report_id, "user_id": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="Ya has votado en este reporte")

    await db.report_votes.insert_one({
        "id": str(uuid.uuid4()), "report_id": report_id, "user_id": user_id,
        "vote_type": vote_type, "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Update report vote counts
    inc_field = "upvotes" if vote_type == "upvote" else "downvotes"
    await db.reports.update_one({"id": report_id}, {"$inc": {inc_field: 1}})

    # Award/deduct points to reporter
    reporter_id = report.get("user_id", "")
    points = calc_vote_points(vote_type)
    try:
        reporter = await db.users.find_one({"_id": ObjectId(reporter_id)})
        if reporter:
            await db.users.update_one({"_id": ObjectId(reporter_id)}, {"$inc": {"total_score": points}})
            # Trust score adjustments for heavy voting
            updated_report = await db.reports.find_one({"id": report_id})
            if updated_report:
                net = (updated_report.get("upvotes", 0) - updated_report.get("downvotes", 0))
                if net <= -5:
                    await update_trust_score(db, reporter_id, TRUST_DOWNVOTED_REPORT, "heavily_downvoted")
                elif net >= 10:
                    await update_trust_score(db, reporter_id, TRUST_UPVOTED_REPORT_MIN, "highly_upvoted")
    except Exception:
        pass

    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")

    return {"message": "Voto registrado", "vote_type": vote_type}

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
        "subscription_active": user.get("subscription_active", False),
        "badges": earned_badges,
        "badges_count": len(earned_badges),
        "accuracy_rate": accuracy,
        "impact_score": rank_info.get("total_score", 0) + (verified_reports * 5),
        "trial_used": user.get("trial_used", False)
    }

@api_router.post("/admin/recalculate-ranks")
async def admin_recalculate_ranks(request: Request):
    """Admin endpoint to trigger rank recalculation."""
    user = await require_auth(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    count = await recalculate_all_ranks(db)
    return {"message": f"Ranks recalculated for {count} users"}


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
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")
    
    return {"message": "Reporte marcado"}

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
         "rank": 1, "level": 1, "trust_score": 1, "streak_days": 1, "subscription_active": 1}
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
    
    # Log the verification code (in production, send via email)
    logger.info(f"Municipality verification code for {email}: {verification_code}")
    
    # Send verification email
    email_result = await send_verification_email(email, verification_code, data.municipality_name)
    logger.info(f"Verification email result: {email_result}")
    
    access_token = create_access_token(user_id, email, "municipality")
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id, "email": email, "name": data.name,
        "role": "municipality", "municipality_name": data.municipality_name,
        "municipality_subscription_active": False,
        "verification_required": True,
        "verification_code_hint": verification_code  # Only in dev — remove in production
    }

@api_router.post("/municipality/verify")
async def verify_municipality_email(data: MunicipalityVerify):
    email = data.email.lower()
    user = await db.users.find_one({"email": email, "role": "municipality"})
    
    if not user:
        raise HTTPException(status_code=404, detail="Municipio no encontrado")
    
    if user.get("email_verified"):
        return {"message": "Email ya verificado"}
    
    # Check code
    if user.get("verification_code") != data.code:
        raise HTTPException(status_code=400, detail="Código de verificación incorrecto")
    
    # Check expiry
    expires = user.get("verification_code_expires", "")
    if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="El código ha expirado. Solicita uno nuevo.")
    
    await db.users.update_one(
        {"email": email},
        {"$set": {"email_verified": True}, "$unset": {"verification_code": "", "verification_code_expires": ""}}
    )
    
    return {"message": "Email verificado correctamente", "verified": True}

@api_router.post("/municipality/resend-verification")
async def resend_municipality_verification(data: MunicipalityResendVerification):
    email = data.email.lower()
    user = await db.users.find_one({"email": email, "role": "municipality"})
    
    if not user:
        raise HTTPException(status_code=404, detail="Municipio no encontrado")
    
    if user.get("email_verified"):
        return {"message": "Email ya verificado"}
    
    # Generate new code
    new_code = generate_verification_code()
    await db.users.update_one(
        {"email": email},
        {"$set": {
            "verification_code": new_code,
            "verification_code_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }}
    )
    
    logger.info(f"New municipality verification code for {email}: {new_code}")
    
    # Send verification email
    user_doc = await db.users.find_one({"email": email})
    muni_name = user_doc.get("municipality_name", "Municipio") if user_doc else "Municipio"
    await send_verification_email(email, new_code, muni_name)
    
    return {"message": "Código de verificación reenviado"}

@api_router.post("/municipality/subscribe")
async def subscribe_municipality(request: Request):
    """Municipality subscription at €49/month."""
    user = await require_municipality(request)
    await request.json()  # Accept body for future plan options
    
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "municipality_subscription_active": True,
            "municipality_subscription_type": "monthly",
            "municipality_subscription_price": 49.00,
            "municipality_subscription_expires": expires.isoformat()
        }}
    )
    return {"message": "Suscripción de municipio activada (€49/mes)", "plan": "monthly", "price": "€49/mes", "expires": expires.isoformat()}

@api_router.get("/municipality/stats")
async def get_municipality_stats(request: Request):
    user = await require_municipality(request)
    muni_name = user.get("municipality_name", "")
    
    total = await db.reports.count_documents({"municipality": muni_name})
    active = await db.reports.count_documents({"municipality": muni_name, "archived": False, "flagged": False})
    flagged = await db.reports.count_documents({"municipality": muni_name, "flagged": True})
    archived = await db.reports.count_documents({"municipality": muni_name, "archived": True})
    
    # Reports in last 7 days
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent = await db.reports.count_documents({"municipality": muni_name, "created_at": {"$gte": week_ago}})
    
    # Pending flags
    pending_flags = await db.flags.count_documents({"municipality": muni_name, "status": "pending"})
    
    return {
        "municipality": muni_name,
        "total_reports": total,
        "active_reports": active,
        "flagged_reports": flagged,
        "archived_reports": archived,
        "recent_reports_7d": recent,
        "pending_flags": pending_flags
    }

@api_router.get("/municipality/reports")
async def get_municipality_reports(request: Request, status: Optional[str] = None, page: int = 1, limit: int = 20):
    user = await require_municipality(request)
    muni_name = user.get("municipality_name", "")
    
    query = {"municipality": muni_name}
    if status == "active":
        query["archived"] = False
        query["flagged"] = False
    elif status == "flagged":
        query["flagged"] = True
    elif status == "archived":
        query["archived"] = True
    
    skip = (page - 1) * limit
    total = await db.reports.count_documents(query)
    reports = await db.reports.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {"reports": reports, "total": total, "page": page, "pages": (total + limit - 1) // limit}

@api_router.get("/municipality/flags")
async def get_municipality_flags(request: Request, status: str = "pending"):
    user = await require_municipality(request)
    muni_name = user.get("municipality_name", "")
    
    flags = await db.flags.find(
        {"municipality": muni_name, "status": status},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Attach report data
    for flag in flags:
        report = await db.reports.find_one({"id": flag["report_id"]}, {"_id": 0, "id": 1, "photo_url": 1, "latitude": 1, "longitude": 1, "created_at": 1})
        flag["report"] = report
    
    return flags

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
    muni_name = user.get("municipality_name", "")
    
    photo_violation_reasons = ["license_plate", "face", "name", "personal_info"]
    
    # Get flags with photo-related violations
    flags = await db.flags.find(
        {"municipality": muni_name, "reason": {"$in": photo_violation_reasons}, "status": "pending"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Group by report and attach report data
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
        
        # Get all flags for this report
        all_flags = await db.flags.find({"report_id": rid}, {"_id": 0, "reason": 1, "created_at": 1}).to_list(20)
        
        reviews.append({
            "report": report,
            "flags": all_flags,
            "flag_count": len(all_flags),
            "photo_violation_count": sum(1 for f in all_flags if f["reason"] in photo_violation_reasons)
        })
    
    return reviews






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
    digest = await generate_municipality_digest(db, user.get("municipality_name", ""))
    return digest

# ==================== SOCIAL SHARING ====================

@api_router.get("/users/{user_id_param}/share")
async def get_user_share_data(user_id_param: str):
    """Get shareable profile data for social media."""
    try:
        u = await db.users.find_one({"_id": ObjectId(user_id_param)}, {"_id": 0, "username": 1, "name": 1, "rank": 1, "total_score": 1, "report_count": 1, "badges": 1})
    except Exception:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    display_name = u.get("username") or u.get("name", "Usuario")
    badge_count = len(u.get("badges", []))
    frontend_url = os.environ.get("FRONTEND_URL", "https://caca-radar.preview.emergentagent.com")

    return {
        "title": f"{display_name} en Caca Radar",
        "text": f"{display_name} es {u.get('rank', 'Aspirante Cagón')} con {u.get('total_score', 0)} puntos y {u.get('report_count', 0)} reportes. {badge_count} insignias. ¡Únete a mantener tu ciudad limpia!",
        "url": f"{frontend_url}/profile",
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
            u = await db.users.find_one({"_id": ObjectId(uid)}, {"_id": 0, "username": 1, "name": 1, "rank": 1, "subscription_active": 1})
        except Exception:
            u = None
        display_name = (u.get("username") or u.get("name", "Anónimo")) if u else "Anónimo"
        results.append({
            "position": i + 1,
            "display_name": display_name,
            "rank": u.get("rank") if u else None,
            "weekly_reports": entry["weekly_reports"],
            "is_subscriber": u.get("subscription_active", False) if u else False
        })

    return results

# ==================== SAVED LOCATIONS ====================

@api_router.post("/users/saved-locations")
async def save_location(data: SavedLocationCreate, request: Request):
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
    return loc

@api_router.get("/users/saved-locations")
async def get_saved_locations(request: Request):
    user = await require_subscriber(request)
    locs = await db.saved_locations.find({"user_id": user["_id"]}, {"_id": 0}).to_list(10)
    return locs

@api_router.delete("/users/saved-locations/{name}")
async def delete_saved_location(name: str, request: Request):
    user = await require_subscriber(request)
    await db.saved_locations.delete_one({"user_id": user["_id"], "name": name})
    return {"message": "Ubicación eliminada"}

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

    # Upsert subscription
    await db.push_subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "subscription": data.subscription,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "active": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")

    return {"message": "Suscripción push activada"}

@api_router.post("/push/unsubscribe")
async def unsubscribe_push(request: Request):
    user = await get_current_user(request)
    anon_id = request.cookies.get("anon_id")
    user_id = user["_id"] if user else anon_id
    if user_id:
        await db.push_subscriptions.update_one({"user_id": user_id}, {"$set": {"active": False}})
    return {"message": "Suscripción push desactivada"}

# ==================== SOCIAL SHARING ====================

@api_router.get("/reports/{report_id}/share")
async def get_share_data(report_id: str, request: Request):
    """Get shareable data for a report."""
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    frontend_url = os.environ.get("FRONTEND_URL", "https://caca-radar.preview.emergentagent.com")
    share_url = f"{frontend_url}/?report={report_id}"
    municipality = report.get("municipality", "España")
    created = report.get("created_at", "")
    contributor = report.get("contributor_name", "Anónimo")

    return {
        "url": share_url,
        "title": f"Reporte de caca en {municipality} — Caca Radar",
        "text": f"Nuevo reporte en {municipality} por {contributor}. ¡Ayuda a mantener las calles limpias!",
        "report_id": report_id,
        "municipality": municipality,
        "contributor": contributor,
        "created_at": created,
        "photo_url": f"{os.environ.get('FRONTEND_URL', '')}/api/files/{report['photo_url']}" if report.get("photo_url") else None
    }

# ==================== MUNICIPALITY ANALYTICS ====================

@api_router.get("/municipality/analytics")
async def get_municipality_analytics(request: Request):
    """Advanced analytics for municipality dashboard."""
    user = await require_municipality(request)
    muni_name = user.get("municipality_name", "")

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
        "top_zones": top_zones
    }


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
async def webhook_status():
    """Check webhook configuration status."""
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
    return {"status": "ok"}

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup
@app.on_event("startup")
async def startup():
    init_storage()
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", sparse=True)
    await db.reports.create_index("id", unique=True)
    await db.reports.create_index([("latitude", 1), ("longitude", 1)])
    await db.reports.create_index("municipality")
    await db.reports.create_index("user_id")
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
    
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@cacaradar.es")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email, "password_hash": hashed,
            "name": "Admin", "role": "admin",
            "subscription_active": True, "subscription_type": "annual",
            "total_score": 0, "trust_score": 100, "rank": "Admin", "level": 10,
            "report_count": 0, "vote_count": 0, "streak_days": 0,
            "created_at": datetime.now(timezone.utc)
        })
        logger.info("Admin user created")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
    
    # Seed demo municipality
    demo_muni_email = os.environ.get("DEMO_MUNI_EMAIL", "madrid@cacaradar.es")
    demo_muni_password = os.environ.get("DEMO_MUNI_PASSWORD", "madrid123")
    existing_muni = await db.users.find_one({"email": demo_muni_email})
    if not existing_muni:
        hashed = hash_password(demo_muni_password)
        await db.users.insert_one({
            "email": demo_muni_email, "password_hash": hashed,
            "name": "Ayuntamiento de Madrid", "role": "municipality",
            "municipality_name": "Madrid", "municipality_province": "Madrid",
            "municipality_subscription_active": True,
            "municipality_subscription_type": "annual",
            "created_at": datetime.now(timezone.utc)
        })
        logger.info("Demo municipality user created")
    
    # Archive old reports (7 days)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    await db.reports.update_many(
        {"created_at": {"$lt": cutoff}, "archived": {"$ne": True}},
        {"$set": {"archived": True}}
    )
    
    # Reset daily report counts
    await reset_daily_counts(db)
    
    # Recalculate ranks
    rank_count = await recalculate_all_ranks(db)
    logger.info(f"Ranks recalculated for {rank_count} users")
    
    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write(f"## Admin\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: admin\n\n")
        f.write(f"## Demo Municipality\n- Email: {demo_muni_email}\n- Password: {demo_muni_password}\n- Role: municipality\n- Municipality: Madrid\n\n")
        f.write("## Auth Endpoints\n- POST /api/auth/register\n- POST /api/auth/login\n- POST /api/auth/logout\n- GET /api/auth/me\n")
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
    
    logger.info("Startup complete")

@app.on_event("shutdown")
async def shutdown():
    client.close()
