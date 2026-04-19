import os
from functools import lru_cache

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/playintegrity"]


def play_integrity_is_configured() -> bool:
    service_account_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH", "").strip()
    package_name = os.environ.get("GOOGLE_PACKAGE_NAME", "").strip()
    return bool(service_account_path and package_name)


@lru_cache(maxsize=1)
def _get_authorized_session(service_account_path: str) -> AuthorizedSession:
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=SCOPES,
    )
    return AuthorizedSession(credentials)


def decode_integrity_token(integrity_token: str, package_name: str, service_account_path: str) -> dict:
    session = _get_authorized_session(service_account_path)
    response = session.post(
        f"https://playintegrity.googleapis.com/v1/{package_name}:decodeIntegrityToken",
        json={"integrity_token": integrity_token},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def summarize_integrity_payload(decoded: dict, expected_request_hash: str | None = None) -> dict:
    payload = decoded.get("tokenPayloadExternal", {})
    request_details = payload.get("requestDetails", {})
    app_integrity = payload.get("appIntegrity", {})
    device_integrity = payload.get("deviceIntegrity", {})
    account_details = payload.get("accountDetails", {})

    request_hash = request_details.get("requestHash")
    return {
        "request_package_name": request_details.get("requestPackageName"),
        "request_hash": request_hash,
        "request_hash_matches": None if not expected_request_hash else request_hash == expected_request_hash,
        "app_recognition_verdict": app_integrity.get("appRecognitionVerdict"),
        "package_name": app_integrity.get("packageName"),
        "certificate_digests": app_integrity.get("certificateSha256Digest", []),
        "version_code": app_integrity.get("versionCode"),
        "device_recognition_verdict": device_integrity.get("deviceRecognitionVerdict", []),
        "app_licensing_verdict": account_details.get("appLicensingVerdict"),
        "raw": payload,
    }
