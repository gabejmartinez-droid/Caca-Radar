from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import jwt
import requests


logger = logging.getLogger("server.apple_identity")

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ALLOWED_CLIENT_IDS = os.environ.get("APPLE_ALLOWED_CLIENT_IDS", "").strip()

_jwks_cache: dict | None = None


@dataclass
class AppleIdentityError(Exception):
    code: str
    message: str
    log_message: str | None = None

    def __str__(self) -> str:
        return self.message


def get_allowed_client_ids(primary_client_id: str, extra_client_ids: str | None = None) -> list[str]:
    client_ids: list[str] = []
    for value in [primary_client_id, *(extra_client_ids or "").split(",")]:
        normalized = (value or "").strip()
        if normalized and normalized not in client_ids:
            client_ids.append(normalized)
    return client_ids


def _load_apple_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    response = requests.get(APPLE_JWKS_URL, timeout=15)
    response.raise_for_status()
    _jwks_cache = response.json()
    return _jwks_cache


def _resolve_signing_key(identity_token: str):
    header = jwt.get_unverified_header(identity_token)
    kid = header.get("kid")
    if not kid:
        raise AppleIdentityError(
            code="apple_kid_missing",
            message="Apple token header is missing a key identifier",
        )

    jwks = _load_apple_jwks()
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(jwk)

    raise AppleIdentityError(
        code="apple_signing_key_missing",
        message="Unable to find Apple signing key for this token",
        log_message=f"No matching Apple JWK for kid={kid}",
    )


def verify_apple_identity_token(
    identity_token: str,
    allowed_client_ids: Iterable[str],
    fallback_email: str = "",
    fallback_name: str = "",
    expected_nonce: str = "",
) -> dict:
    allowed_client_ids = [client_id for client_id in allowed_client_ids if client_id]
    if not allowed_client_ids:
        raise AppleIdentityError(
            code="apple_not_configured",
            message="Apple sign-in is not configured on this deployment",
            log_message="No allowed Apple client IDs configured",
        )

    if not identity_token:
        raise AppleIdentityError(
            code="missing_apple_identity_token",
            message="Apple identity token is required",
        )

    try:
        signing_key = _resolve_signing_key(identity_token)
        token_data = jwt.decode(
            identity_token,
            signing_key,
            algorithms=["RS256"],
            audience=allowed_client_ids,
            issuer=APPLE_ISSUER,
        )
    except AppleIdentityError:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise AppleIdentityError(
            code="apple_token_expired",
            message="Apple token has expired",
            log_message=str(exc),
        ) from exc
    except jwt.InvalidIssuerError as exc:
        raise AppleIdentityError(
            code="apple_issuer_mismatch",
            message="Apple token issuer is invalid",
            log_message=str(exc),
        ) from exc
    except jwt.InvalidAudienceError as exc:
        raise AppleIdentityError(
            code="apple_audience_mismatch",
            message="Apple token audience does not match this app",
            log_message=str(exc),
        ) from exc
    except Exception as exc:
        raise AppleIdentityError(
            code="invalid_apple_token",
            message="Apple token verification failed",
            log_message=str(exc),
        ) from exc

    issuer = token_data.get("iss")
    if issuer != APPLE_ISSUER:
        raise AppleIdentityError(
            code="apple_issuer_mismatch",
            message="Apple token issuer is invalid",
            log_message=f"Unexpected issuer: {issuer}",
        )

    expiration = token_data.get("exp")
    if expiration:
        now_ts = datetime.now(timezone.utc).timestamp()
        if float(expiration) <= now_ts:
            raise AppleIdentityError(
                code="apple_token_expired",
                message="Apple token has expired",
            )

    subject = token_data.get("sub")
    if not subject:
        raise AppleIdentityError(
            code="apple_subject_missing",
            message="Apple token is missing a stable subject identifier",
        )

    email = (token_data.get("email") or fallback_email or "").strip().lower()
    if token_data.get("email_verified") in {"false", False}:
        raise AppleIdentityError(
            code="apple_email_unverified",
            message="Apple account email is not verified",
        )

    if expected_nonce:
        token_nonce = (token_data.get("nonce") or "").strip()
        if token_nonce != expected_nonce:
            raise AppleIdentityError(
                code="apple_nonce_mismatch",
                message="Apple sign-in response could not be verified",
                log_message=f"Expected nonce {expected_nonce} but received {token_nonce}",
            )

    return {
        "sub": subject,
        "email": email,
        "name": (fallback_name or token_data.get("name") or "").strip(),
        "raw": token_data,
    }
