"""
Auth endpoints: register, login, token refresh, logout
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    RegisterRequest, LoginResponse, TokenRefreshRequest,
    TokenRefreshResponse, UserResponse,
)
from app.core.jwt import create_access_token, create_refresh_token, verify_token
from app.core.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new customer account."""
    # Check duplicate
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_phone = await db.execute(select(User).where(User.phone == request.phone))
    if existing_phone.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    hashed_pw = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()

    user = User(
        name=request.name,
        email=request.email,
        phone=request.phone,
        password_hash=hashed_pw,
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login with email/phone + password. Returns JWT access + refresh tokens."""
    # Support login by email or phone
    result = await db.execute(
        select(User).where(
            (User.email == form_data.username) | (User.phone == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not bcrypt.checkpw(form_data.password.encode(), user.password_hash.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    user.last_login = datetime.utcnow()
    await db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "user_id": str(user.id), "role": user.role, "email": user.email}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using a valid refresh token."""
    payload = verify_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(
        data={"sub": str(user.id), "user_id": str(user.id), "role": user.role, "email": user.email}
    )
    return TokenRefreshResponse(access_token=access_token, token_type="bearer")


@router.post("/verify-token")
async def verify_token_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Internal endpoint for other microservices to validate tokens.
    Called by API Gateway / other services.
    """
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "valid": True,
        "user_id": payload.get("user_id"),
        "role": payload.get("role"),
        "email": payload.get("email"),
    }
