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
def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=15), "type": "access"}
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

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ReportCreate(BaseModel):
    latitude: float
    longitude: float

class VoteCreate(BaseModel):
    vote_type: Literal["still_there", "cleaned"]

class FlagCreate(BaseModel):
    reason: Optional[str] = None

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
    except:
        return None

async def require_auth(request: Request) -> dict:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return user

# Get or create anonymous user ID
def get_anonymous_id(request: Request) -> str:
    anon_id = request.cookies.get("anon_id")
    if not anon_id:
        anon_id = str(uuid.uuid4())
    return anon_id

# Auth Routes
@api_router.post("/auth/register")
async def register(data: UserRegister, response: Response):
    email = data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    hashed = hash_password(data.password)
    user_doc = {
        "email": email,
        "password_hash": hashed,
        "name": data.name or email.split("@")[0],
        "role": "user",
        "created_at": datetime.now(timezone.utc)
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {"id": user_id, "email": email, "name": user_doc["name"]}

@api_router.post("/auth/login")
async def login(data: UserLogin, request: Request, response: Response):
    email = data.email.lower()
    ip = request.client.host
    identifier = f"{ip}:{email}"
    
    # Check brute force
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
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {"id": user_id, "email": email, "name": user.get("name", "")}

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
async def refresh_token(request: Request, response: Response):
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
        access_token = create_access_token(str(user["_id"]), user["email"])
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Reports Routes
@api_router.get("/reports")
async def get_reports():
    # Get all non-archived, non-flagged reports
    reports = await db.reports.find(
        {"archived": {"$ne": True}, "flagged": {"$ne": True}},
        {"_id": 0}
    ).to_list(1000)
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
        "archived": False,
        "flagged": False
    }
    
    await db.reports.insert_one(report_doc)
    
    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")
    
    report_doc.pop("_id", None)
    return report_doc

@api_router.post("/reports/{report_id}/photo")
async def upload_photo(report_id: str, file: UploadFile = File(...)):
    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    
    # Read and upload
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (max 5MB)")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    path = f"{APP_NAME}/reports/{report_id}/{uuid.uuid4()}.{ext}"
    
    result = put_object(path, data, file.content_type or "image/jpeg")
    
    await db.reports.update_one(
        {"id": report_id},
        {"$set": {"photo_url": result["path"]}}
    )
    
    return {"photo_url": result["path"]}

@api_router.get("/files/{path:path}")
async def get_file(path: str):
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=content_type)
    except Exception as e:
        logger.error(f"Error getting file: {e}")
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

# Votes Routes
@api_router.post("/reports/{report_id}/vote")
async def vote_report(report_id: str, data: VoteCreate, request: Request, response: Response):
    report = await db.reports.find_one({"id": report_id, "archived": {"$ne": True}})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id
    
    # Check if already voted
    existing_vote = await db.votes.find_one({"report_id": report_id, "user_id": user_id})
    if existing_vote:
        raise HTTPException(status_code=400, detail="Ya has votado en este reporte")
    
    # Create vote
    vote_doc = {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "user_id": user_id,
        "vote_type": data.vote_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.votes.insert_one(vote_doc)
    
    # Update report counts
    if data.vote_type == "still_there":
        await db.reports.update_one(
            {"id": report_id},
            {"$inc": {"still_there_count": 1, "status_score": 1}}
        )
    else:  # cleaned
        await db.reports.update_one(
            {"id": report_id},
            {"$inc": {"cleaned_count": 1, "status_score": -1}}
        )
    
    # Check if should be archived (cleaned votes >= 3)
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

# Flag Routes
@api_router.post("/reports/{report_id}/flag")
async def flag_report(report_id: str, data: FlagCreate, request: Request, response: Response):
    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    user = await get_current_user(request)
    anon_id = get_anonymous_id(request)
    user_id = user["_id"] if user else anon_id
    
    # Check if already flagged by this user
    existing_flag = await db.flags.find_one({"report_id": report_id, "user_id": user_id})
    if existing_flag:
        raise HTTPException(status_code=400, detail="Ya has reportado esta publicación")
    
    # Create flag
    flag_doc = {
        "id": str(uuid.uuid4()),
        "report_id": report_id,
        "user_id": user_id,
        "reason": data.reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.flags.insert_one(flag_doc)
    
    # Count flags for this report
    flag_count = await db.flags.count_documents({"report_id": report_id})
    if flag_count >= 3:
        await db.reports.update_one({"id": report_id}, {"$set": {"flagged": True}})
    
    if not user:
        response.set_cookie(key="anon_id", value=anon_id, httponly=True, secure=False, samesite="lax", max_age=86400*365, path="/")
    
    return {"message": "Reporte marcado"}

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Caca Radar API"}

# Health check
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
    # Initialize storage
    init_storage()
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.reports.create_index("id", unique=True)
    await db.reports.create_index([("latitude", 1), ("longitude", 1)])
    await db.votes.create_index([("report_id", 1), ("user_id", 1)], unique=True)
    await db.flags.create_index([("report_id", 1), ("user_id", 1)], unique=True)
    await db.login_attempts.create_index("identifier")
    
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@cacaradar.es")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc)
        })
        logger.info("Admin user created")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")
    
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
        f.write("## Auth Endpoints\n- POST /api/auth/register\n- POST /api/auth/login\n- POST /api/auth/logout\n- GET /api/auth/me\n")
    
    logger.info("Startup complete")

@app.on_event("shutdown")
async def shutdown():
    client.close()
