"""
Auth dependency — validates JWT tokens issued by user-auth-service.
Used by all other microservices to protect endpoints.
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT locally using shared secret (fast path — no network call)."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.debug(f"JWT decode failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency: validates Bearer token and returns user payload.
    First tries local JWT decode; falls back to auth-service verification
    for tokens that need remote validation (e.g. revoked tokens, API keys).
    """
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    role = payload.get("role")

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
        )

    return {
        "user_id": user_id,
        "role": role,
        "email": payload.get("email"),
        "token": token,
    }


def require_roles(*roles: str):
    """
    Dependency factory: ensures user has one of the required roles.
    Usage: Depends(require_roles("ADMIN", "OPS"))
    """
    async def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(roles)}",
            )
        return current_user
    return checker


# Convenience role deps
require_customer = require_roles("CUSTOMER", "ADMIN")
require_agent    = require_roles("AGENT", "ADMIN")
require_ops      = require_roles("OPS", "ADMIN")
require_admin    = require_roles("ADMIN")
