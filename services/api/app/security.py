import os, uuid
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key-change-me-in-production-0123456789")  # real value goes in .env later
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