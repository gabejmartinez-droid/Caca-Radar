"""Shared dependencies — DB, auth helpers, models, utilities.

All route modules import from here instead of server.py to avoid circular imports.
"""
from dotenv import load_dotenv
load_dotenv()

import os
import logging
import uuid
import bcrypt
import jwt
import requests
import re
import random
import string
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Literal

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Query, Response
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# ── Logging ──────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("server")

# ── MongoDB ──────────────────────────────────────────
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    return resp.content, resp.headers.get("content-type", "application/octet-stream")

# ── Reverse Geocode ──────────────────────────────────
def reverse_geocode(lat: float, lon: float) -> dict:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json", "addressdetails": 1, "zoom": 16},
            headers={"User-Agent": "CacaRadar/1.0"},
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
    name: str
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
ALLOWED_MUNICIPALITY_DOMAINS = [
    r".*\.es$", r".*\.gob\.es$", r".*\.org\.es$", r".*@ayto-.*", r".*@ajuntament.*",
    r".*@concello.*", r".*@udal.*", r".*@diputacion.*", r".*@cacaradar\.es$",
]

def is_valid_municipality_email(email: str) -> bool:
    domain = email.split("@")[1] if "@" in email else ""
    for pattern in ALLOWED_MUNICIPALITY_DOMAINS:
        if re.match(pattern, email) or re.match(pattern, domain):
            return True
    return False

def generate_verification_code() -> str:
    return ''.join(random.choices(string.digits, k=6))
