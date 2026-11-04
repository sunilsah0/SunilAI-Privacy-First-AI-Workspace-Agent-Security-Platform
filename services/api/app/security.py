import os, uuid
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash

APP_ENV = os.getenv("APP_ENV", "development")

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
       if APP_ENV == "production":
           raise RuntimeError("SECRET_KEY must be set in production")
       SECRET_KEY = "dev-only-secret-key-change-me-in-production-0123456789"
elif len(SECRET_KEY) < 32:
       raise RuntimeError("SECRET_KEY must be at least 32 characters")


 # Who may create accounts, and which edition this installation is
REGISTRATION_MODE = os.getenv("REGISTRATION_MODE", "" if APP_ENV == "production" else "open")
INVITE_CODE = os.getenv("INVITE_CODE", "")
EDITION = os.getenv("EDITION", "" if APP_ENV == "production" else "enterprise")
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"

if REGISTRATION_MODE not in ("open", "invite", "first_user", "closed"):
    raise RuntimeError("REGISTRATION_MODE must be open, invite, first_user or closed")
if EDITION not in ("personal", "enterprise"):
    raise RuntimeError("EDITION must be personal or enterprise")
if REGISTRATION_MODE == "invite" and len(INVITE_CODE) < 12:
    raise RuntimeError("INVITE_CODE must be at least 12 characters when REGISTRATION_MODE=invite")

ph = PasswordHash.recommended()  # Argon2, a trusted algorithm. Never invent your own.

def hash_password(p: str) -> str:
    return ph.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return ph.verify(p, hashed)

def create_token(user_id: uuid.UUID) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=30)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm="HS256")

def read_token(token: str) -> uuid.UUID:
    data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return uuid.UUID(data["sub"])