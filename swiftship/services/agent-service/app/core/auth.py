import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if not payload.get("user_id") or not payload.get("role"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token payload")
    return {"user_id": payload["user_id"], "role": payload["role"], "email": payload.get("email")}


def require_roles(*roles: str):
    async def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Required roles: {list(roles)}")
        return current_user
    return checker


# Singular alias used by deliveries.py
def require_role(*roles: str):
    return require_roles(*roles)


require_agent = require_roles("AGENT", "ADMIN")
require_ops   = require_roles("OPS", "ADMIN")
require_admin = require_roles("ADMIN")
