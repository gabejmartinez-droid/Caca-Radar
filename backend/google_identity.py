from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


logger = logging.getLogger("server.google_identity")

GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


@dataclass
class GoogleIdentityError(Exception):
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


def verify_google_credential(credential: str, allowed_client_ids: Iterable[str]) -> dict:
    allowed_client_ids = [client_id for client_id in allowed_client_ids if client_id]
    if not allowed_client_ids:
        raise GoogleIdentityError(
            code="google_not_configured",
            message="Google login is not configured on this deployment",
            log_message="No allowed Google client IDs configured",
        )

    if not credential:
        raise GoogleIdentityError(
            code="missing_google_credential",
            message="Google credential is required",
        )

    try:
        token_data = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            audience=None,
        )
    except ValueError as exc:
        detail = str(exc)
        lowered = detail.lower()
        if "expired" in lowered:
            raise GoogleIdentityError(
                code="google_token_expired",
                message="Google token has expired",
                log_message=detail,
            ) from exc
        raise GoogleIdentityError(
            code="invalid_google_token",
            message="Google token verification failed",
            log_message=detail,
        ) from exc

    issuer = token_data.get("iss")
    if issuer not in GOOGLE_ISSUERS:
        raise GoogleIdentityError(
            code="google_issuer_mismatch",
            message="Google token issuer is invalid",
            log_message=f"Unexpected issuer: {issuer}",
        )

    audience = token_data.get("aud")
    if audience not in allowed_client_ids:
        raise GoogleIdentityError(
            code="google_audience_mismatch",
            message="Google token audience does not match this app",
            log_message=f"Audience {audience!r} not in allowed IDs",
        )

    expiration = token_data.get("exp")
    if expiration:
        now_ts = datetime.now(timezone.utc).timestamp()
        if float(expiration) <= now_ts:
            raise GoogleIdentityError(
                code="google_token_expired",
                message="Google token has expired",
            )

    subject = token_data.get("sub")
    if not subject:
        raise GoogleIdentityError(
            code="google_subject_missing",
            message="Google token is missing a stable subject identifier",
        )

    email = (token_data.get("email") or "").strip().lower()
    if not email:
        raise GoogleIdentityError(
            code="google_email_missing",
            message="Google account did not provide an email address",
        )

    if token_data.get("email_verified") is False:
        raise GoogleIdentityError(
            code="google_email_unverified",
            message="Google account email is not verified",
        )

    return {
        "sub": subject,
        "email": email,
        "name": token_data.get("name") or "",
        "picture": token_data.get("picture") or "",
        "given_name": token_data.get("given_name") or "",
        "family_name": token_data.get("family_name") or "",
        "locale": token_data.get("locale") or "",
        "raw": token_data,
    }
