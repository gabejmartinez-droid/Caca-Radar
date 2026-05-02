"""Shared dependencies — DB, auth helpers, models, utilities.

All route modules import from here instead of server.py to avoid circular imports.
"""
from dotenv import load_dotenv
load_dotenv()

import os
import logging
import uuid
import secrets
import hashlib
import bcrypt
import jwt
import httpx
import re
import random
import string
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Query, Response
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# ── Logging ──────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("server")

# ── Runtime / MongoDB ────────────────────────────────
APP_ENV = (
    os.environ.get("APP_ENV")
    or os.environ.get("ENVIRONMENT")
    or os.environ.get("ENV")
    or "development"
).lower()
mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]

PRODUCTION_ENV_NAMES = {"production", "prod"}
LOCAL_MONGO_HOSTS = {"localhost", "127.0.0.1", "::1", "mongo", "mongodb"}
UNSAFE_PRODUCTION_DB_NAMES = {"test", "test_database", "local", "dev", "development", "staging"}


def is_production_env() -> bool:
    return APP_ENV in PRODUCTION_ENV_NAMES


def is_mongo_local() -> bool:
    parsed = urlparse(mongo_url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"mongodb", "mongodb+srv"} and host in LOCAL_MONGO_HOSTS


def redacted_mongo_url() -> str:
    parsed = urlparse(mongo_url)
    host = parsed.hostname or "unknown-host"
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{host}{port}"


def validate_database_config() -> None:
    if not db_name:
        raise RuntimeError("DB_NAME is required")
    if is_production_env() and is_mongo_local():
        raise RuntimeError("FATAL: APP_ENV=production but MONGO_URL points to local MongoDB. Refusing to start.")
    if is_production_env() and db_name.lower() in UNSAFE_PRODUCTION_DB_NAMES:
        raise RuntimeError(f"FATAL: APP_ENV=production but DB_NAME={db_name!r} is unsafe. Refusing to start.")
    if is_production_env() and "prod" not in db_name.lower() and "production" not in db_name.lower():
        raise RuntimeError("FATAL: production DB_NAME must clearly identify production.")


validate_database_config()

MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.environ.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000" if is_production_env() else "15000"))
MONGO_CONNECT_TIMEOUT_MS = int(os.environ.get("MONGO_CONNECT_TIMEOUT_MS", "5000" if is_production_env() else "10000"))
MONGO_SOCKET_TIMEOUT_MS = int(os.environ.get("MONGO_SOCKET_TIMEOUT_MS", "15000" if is_production_env() else "30000"))
MONGO_WAIT_QUEUE_TIMEOUT_MS = int(os.environ.get("MONGO_WAIT_QUEUE_TIMEOUT_MS", "5000" if is_production_env() else "15000"))
MONGO_MAX_POOL_SIZE = int(os.environ.get("MONGO_MAX_POOL_SIZE", "100"))
MONGO_MIN_POOL_SIZE = int(os.environ.get("MONGO_MIN_POOL_SIZE", "5" if is_production_env() else "1"))
MONGO_MAX_IDLE_TIME_MS = int(os.environ.get("MONGO_MAX_IDLE_TIME_MS", "60000"))
MONGO_HEARTBEAT_FREQUENCY_MS = int(os.environ.get("MONGO_HEARTBEAT_FREQUENCY_MS", "10000"))

client = AsyncIOMotorClient(
    mongo_url,
    appname="caca-radar-api",
    serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
    connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
    socketTimeoutMS=MONGO_SOCKET_TIMEOUT_MS,
    waitQueueTimeoutMS=MONGO_WAIT_QUEUE_TIMEOUT_MS,
    maxPoolSize=MONGO_MAX_POOL_SIZE,
    minPoolSize=MONGO_MIN_POOL_SIZE,
    maxIdleTimeMS=MONGO_MAX_IDLE_TIME_MS,
    heartbeatFrequencyMS=MONGO_HEARTBEAT_FREQUENCY_MS,
)
db = client[db_name]


def get_mongo_runtime_config() -> dict:
    return {
        "serverSelectionTimeoutMS": MONGO_SERVER_SELECTION_TIMEOUT_MS,
        "connectTimeoutMS": MONGO_CONNECT_TIMEOUT_MS,
        "socketTimeoutMS": MONGO_SOCKET_TIMEOUT_MS,
        "waitQueueTimeoutMS": MONGO_WAIT_QUEUE_TIMEOUT_MS,
        "maxPoolSize": MONGO_MAX_POOL_SIZE,
        "minPoolSize": MONGO_MIN_POOL_SIZE,
        "maxIdleTimeMS": MONGO_MAX_IDLE_TIME_MS,
        "heartbeatFrequencyMS": MONGO_HEARTBEAT_FREQUENCY_MS,
    }

# ── JWT ──────────────────────────────────────────────
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

def create_access_token(user_id: str, email: str, role: str = "user") -> str:
    payload = {"sub": user_id, "email": email, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=1), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

# ── Password ─────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# ── Object Storage ───────────────────────────────────
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "caca-radar"
storage_key = None
storage_lock = asyncio.Lock()
http_client: Optional[httpx.AsyncClient] = None
HTTP_CONNECT_TIMEOUT_SECONDS = float(os.environ.get("HTTP_CONNECT_TIMEOUT_SECONDS", "5"))
HTTP_READ_TIMEOUT_SECONDS = float(os.environ.get("HTTP_READ_TIMEOUT_SECONDS", "15"))
HTTP_WRITE_TIMEOUT_SECONDS = float(os.environ.get("HTTP_WRITE_TIMEOUT_SECONDS", "30"))
HTTP_POOL_TIMEOUT_SECONDS = float(os.environ.get("HTTP_POOL_TIMEOUT_SECONDS", "5"))

async def get_http_client() -> httpx.AsyncClient:
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=HTTP_CONNECT_TIMEOUT_SECONDS,
                read=HTTP_READ_TIMEOUT_SECONDS,
                write=HTTP_WRITE_TIMEOUT_SECONDS,
                pool=HTTP_POOL_TIMEOUT_SECONDS,
            ),
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=40),
            headers={"User-Agent": "CacaRadar/1.0"},
        )
    return http_client


async def close_http_client() -> None:
    global http_client
    if http_client is not None:
        await http_client.aclose()
        http_client = None


async def init_storage_async():
    global storage_key
    if storage_key:
        return storage_key
    async with storage_lock:
        if storage_key:
            return storage_key
        try:
            client = await get_http_client()
            resp = await client.post(
                f"{STORAGE_URL}/init",
                json={"emergent_key": EMERGENT_KEY},
                timeout=30,
            )
            resp.raise_for_status()
            storage_key = resp.json()["storage_key"]
            logger.info("Storage initialized successfully")
            return storage_key
        except Exception as e:
            logger.error(f"Storage init failed: {e}")
            return None


async def put_object_async(path: str, data: bytes, content_type: str) -> dict:
    key = await init_storage_async()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    client = await get_http_client()
    resp = await client.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        content=data,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


async def get_object_async(path: str) -> tuple:
    key = await init_storage_async()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not available")
    client = await get_http_client()
    resp = await client.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("content-type", "application/octet-stream")

# ── Reverse Geocode ──────────────────────────────────
async def reverse_geocode_async(lat: float, lon: float) -> dict:
    try:
        client = await get_http_client()
        resp = await client.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "addressdetails": 1, "zoom": 16},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        address = data.get("address", {})
        municipality = (
            address.get("city") or address.get("town") or address.get("village") or
            address.get("municipality") or address.get("county") or "Desconocido"
        )
        province = address.get("state") or address.get("province") or ""
        country = address.get("country") or "España"
        barrio = (
            address.get("neighbourhood") or address.get("suburb") or
            address.get("quarter") or address.get("city_district") or ""
        )
        return {"municipality": municipality, "province": province, "country": country, "barrio": barrio, "display_name": data.get("display_name", "")}
    except Exception as e:
        logger.error(f"Reverse geocode failed: {e}")
        return {"municipality": "Desconocido", "province": "", "country": "España", "barrio": "", "display_name": ""}

# ── App Store URLs ───────────────────────────────────
APP_STORE_URL = "https://apps.apple.com/app/caca-radar/id000000000"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.cacaradar.app"

# ── Google Sign-In (GIS) ─────────────────────────────
GOOGLE_WEB_CLIENT_ID = os.environ.get("GOOGLE_WEB_CLIENT_ID", "").strip()
GOOGLE_ALLOWED_CLIENT_IDS = os.environ.get("GOOGLE_ALLOWED_CLIENT_IDS", "").strip()

# ── VIP / Owner emails — permanent premium access ────
VIP_EMAILS = {
    "alexhmartinez27@gmail.com",
    "anavlopez888@gmail.com",
    "arcatasio@gmail.com",
    "doughboymarine@gmail.com",
    "gabeandolesia@gmail.com",
    "gabejmartinez@gmail.com",
    "gmartinezffl@gmail.com",
    "girljillo@gmail.com",
    "lmpi2727@gmail.com",
    "m_beauchamp@me.com",
    "martinez.maria.maggie@gmail.com",
    "olesiamartinez@gmail.com",
    "paul@simpsonmail.us",
    "paulshareshisfreedom@gmail.com",
    "pedroege@gmail.com",
    "pem_es@yahoo.es",
    "tgrazini@gmail.com",
}


def is_vip_email(email: Optional[str]) -> bool:
    return (email or "").strip().lower() in VIP_EMAILS

# ── Auth Middleware ───────────────────────────────────
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
        email = (user.get("email") or "").strip().lower()
        if is_vip_email(email):
            updates = {}
            if not user.get("subscription_active"):
                updates["subscription_active"] = True
                updates["subscription_type"] = "lifetime"
                updates["subscription_expires"] = None
            if user.get("trust_score", 50) < 50:
                updates["trust_score"] = 50
            if updates:
                await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
                user.update(updates)
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
    if user.get("role") == "municipality" and not user.get("email_verified"):
        raise HTTPException(status_code=403, detail="Debes verificar el email oficial antes de acceder al panel municipal")
    return user

async def require_registered(request: Request) -> dict:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Debes registrarte para realizar esta acción. ¡Es gratis!")
    return user

def get_anonymous_id(request: Request) -> str:
    anon_id = request.cookies.get("anon_id")
    if not anon_id:
        anon_id = str(uuid.uuid4())
    return anon_id

# ── Pydantic Models ──────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    username: str

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
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class ReportVote(BaseModel):
    vote_type: Literal["upvote", "downvote"]

class ValidationCreate(BaseModel):
    vote: Literal["confirm", "reject"]
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

FLAG_REASONS = ["license_plate", "face", "name", "personal_info", "inappropriate", "spam", "other"]

class FlagCreate(BaseModel):
    reason: str

class UsernameUpdate(BaseModel):
    username: str

class MunicipalityLogin(BaseModel):
    email: EmailStr
    password: str

class MunicipalityRegister(BaseModel):
    name: str
    municipality_name: str
    province: str
    email: EmailStr
    password: str
    contact_name: Optional[str] = None

class AppleReceiptVerify(BaseModel):
    receipt_data: Optional[str] = None
    transaction_id: Optional[str] = None
    plan: Literal["monthly", "annual"] = "monthly"

class GoogleReceiptVerify(BaseModel):
    purchase_token: str
    subscription_id: str
    plan: Literal["monthly", "annual"] = "monthly"

# ── Municipality domain verification ─────────────────
BASE_MUNICIPALITY_DOMAIN_PATTERNS = [
    r"(?:^|\.)gob\.es$",
    r"(?:^|\.)gov\.es$",
    r"(?:^|\.)ayto-[a-z0-9-]+\.[a-z.]+$",
    r"(?:^|\.)ajuntament[a-z0-9-]*\.[a-z.]+$",
    r"(?:^|\.)concello[a-z0-9-]*\.[a-z.]+$",
    r"(?:^|\.)udal[a-z0-9-]*\.[a-z.]+$",
    r"(?:^|\.)diputacion[a-z0-9-]*\.[a-z.]+$",
    r"(?:^|\.)cacaradar\.es$",
]


def _load_municipality_domain_patterns() -> list[str]:
    patterns = list(BASE_MUNICIPALITY_DOMAIN_PATTERNS)
    extra_domains = [
        value.strip().lower()
        for value in os.environ.get("MUNICIPALITY_ALLOWED_EMAIL_DOMAINS", "").split(",")
        if value.strip()
    ]
    for domain in extra_domains:
        patterns.append(rf"(?:^|\.){re.escape(domain)}$")
    extra_regexes = [
        value.strip()
        for value in os.environ.get("MUNICIPALITY_ALLOWED_EMAIL_REGEXES", "").split(",")
        if value.strip()
    ]
    patterns.extend(extra_regexes)
    return patterns


ALLOWED_MUNICIPALITY_DOMAINS = _load_municipality_domain_patterns()

def is_valid_municipality_email(email: str) -> bool:
    domain = email.split("@")[1].strip().lower() if "@" in email else ""
    if not domain:
        return False
    for pattern in ALLOWED_MUNICIPALITY_DOMAINS:
        if re.fullmatch(pattern, domain):
            return True
    return False

def generate_verification_code() -> str:
    return ''.join(random.choices(string.digits, k=6))


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
