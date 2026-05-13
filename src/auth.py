import os
import jwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET", "please-change-this-secret-in-production")
ALGORITHM = "HS256"
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")

logger.info(f"Loaded credentials - Username: {ADMIN_USERNAME}, Password: {ADMIN_PASSWORD}")

_bearer = HTTPBearer(auto_error=False)


def create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=8)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def _decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        return None


def verify_admin(credentials: HTTPAuthorizationCredentials = Security(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization required")
    payload = _decode_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]
