import os
from dotenv import load_dotenv
load_dotenv()
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from typing import Optional

JWT_SECRET      = os.getenv("JWT_SECRET", "your-super-secret-key-change-in-production")
JWT_ALGORITHM   = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 24))

# In-memory token blacklist (replace with Redis in production)
_blacklisted_tokens: set = set()


def create_jwt(uuid: str, role: str) -> str:
    payload = {
        "uuid": uuid,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    if token in _blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Token has been invalidated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def blacklist_token(token: str) -> None:
    _blacklisted_tokens.add(token)


def extract_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1]
