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
import asyncio

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

class ReportCreate(BaseModel):
    latitude: float
    longitude: float

class VoteCreate(BaseModel):
    vote_type: Literal["still_there", "cleaned"]

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

def get_anonymous_id(request: Request) -> str:
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
        "report_count": 0,
        "vote_count": 0,
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
        "subscription_active": False, "report_count": 0, "vote_count": 0
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
        "municipality_name": user.get("municipality_name")
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
    """Mock subscription endpoint - in production, verified via App Store / Google Play receipts."""
    user = await require_auth(request)
    body = await request.json()
    plan = body.get("plan", "monthly")
    
    expires = datetime.now(timezone.utc) + (timedelta(days=30) if plan == "monthly" else timedelta(days=365))
    
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "subscription_active": True,
            "subscription_type": plan,
            "subscription_expires": expires.isoformat()
        }}
    )
    return {"message": "Suscripción activada", "plan": plan, "expires": expires.isoformat()}

# ==================== REPORTS ====================

@api_router.get("/reports")
async def get_reports(municipality: Optional[str] = None):
    query = {"archived": {"$ne": True}, "flagged": {"$ne": True}}
    if municipality:
        query["municipality"] = municipality
    reports = await db.reports.find(query, {"_id": 0}).to_list(2000)
    return reports

@api_router.get("/reports/{report_id}")
async def get_report(report_id: str):
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return report

@api_router.post("/reports")
async def create_report(request: Request, data: ReportCreate, response: Response):
    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id
    
    # Reverse geocode to get municipality
    geo = reverse_geocode(data.latitude, data.longitude)
    
    report_id = str(uuid.uuid4())
    report_doc = {
        "id": report_id,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "photo_url": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status_score": 0,
        "still_there_count": 0,
        "cleaned_count": 0,
        "user_id": user_id,
        "municipality": geo["municipality"],
        "province": geo["province"],
        "country": geo["country"],
        "archived": False,
        "flagged": False,
        "flag_count": 0
    }
    
    await db.reports.insert_one(report_doc)
    
    # Increment user report count
    if user:
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"report_count": 1}})
    
    # Ensure municipality exists in municipalities collection
    existing_muni = await db.municipalities.find_one({"name": geo["municipality"], "province": geo["province"]})
    if not existing_muni:
        await db.municipalities.insert_one({
            "id": str(uuid.uuid4()),
            "name": geo["municipality"],
            "province": geo["province"],
            "country": geo["country"],
            "report_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    else:
        await db.municipalities.update_one(
            {"name": geo["municipality"], "province": geo["province"]},
            {"$inc": {"report_count": 1}}
        )
    
    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")
    
    report_doc.pop("_id", None)
    return report_doc

@api_router.post("/reports/{report_id}/photo")
async def upload_photo(report_id: str, file: UploadFile = File(...)):
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
    if flag_count >= 3:
        await db.reports.update_one({"id": report_id}, {"$set": {"flagged": True, "flag_count": flag_count}})
    else:
        await db.reports.update_one({"id": report_id}, {"$set": {"flag_count": flag_count}})
    
    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")
    
    return {"message": "Reporte marcado"}

# ==================== LEADERBOARDS ====================

@api_router.get("/leaderboard/national")
async def get_national_leaderboard(request: Request):
    """National leaderboard - subscriber only."""
    user = await get_current_user(request)
    if not user or not user.get("subscription_active"):
        raise HTTPException(status_code=403, detail="Se requiere suscripción premium")
    
    top_reporters = await db.users.find(
        {"role": "user", "report_count": {"$gt": 0}},
        {"_id": 0, "username": 1, "name": 1, "report_count": 1, "vote_count": 1, "municipality": 1}
    ).sort("report_count", -1).to_list(50)
    
    # Add rank
    for i, u in enumerate(top_reporters):
        u["rank"] = i + 1
        u["total_score"] = u.get("report_count", 0) + u.get("vote_count", 0)
        u["display_name"] = u.get("username") or u.get("name", "Anónimo")
    
    return top_reporters

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
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
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
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email, "municipality")
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id, "email": email, "name": data.name,
        "role": "municipality", "municipality_name": data.municipality_name,
        "municipality_subscription_active": False
    }

@api_router.post("/municipality/subscribe")
async def subscribe_municipality(request: Request):
    """Mock municipality subscription - in production verified via payment provider."""
    user = await require_municipality(request)
    body = await request.json()
    plan = body.get("plan", "monthly")
    
    expires = datetime.now(timezone.utc) + (timedelta(days=30) if plan == "monthly" else timedelta(days=365))
    
    await db.users.update_one(
        {"_id": ObjectId(user["_id"])},
        {"$set": {
            "municipality_subscription_active": True,
            "municipality_subscription_type": plan,
            "municipality_subscription_expires": expires.isoformat()
        }}
    )
    return {"message": "Suscripción de municipio activada", "plan": plan, "expires": expires.isoformat()}

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
            "report_count": 0, "vote_count": 0,
            "created_at": datetime.now(timezone.utc)
        })
        logger.info("Admin user created")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
    
    # Seed demo municipality
    demo_muni_email = "madrid@cacaradar.es"
    demo_muni_password = "madrid123"
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
    
    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write(f"## Admin\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: admin\n\n")
        f.write(f"## Demo Municipality\n- Email: {demo_muni_email}\n- Password: {demo_muni_password}\n- Role: municipality\n- Municipality: Madrid\n\n")
        f.write("## Auth Endpoints\n- POST /api/auth/register\n- POST /api/auth/login\n- POST /api/auth/logout\n- GET /api/auth/me\n")
        f.write("## Municipality Endpoints\n- POST /api/municipality/register\n- GET /api/municipality/stats\n- GET /api/municipality/reports\n- GET /api/municipality/flags\n- POST /api/municipality/moderate/{report_id}\n")
    
    logger.info("Startup complete")

@app.on_event("shutdown")
async def shutdown():
    client.close()
