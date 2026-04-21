"""
User Auth Service — SwiftShip
Handles: registration, login, JWT tokens, RBAC, OAuth2
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users, tokens
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="SwiftShip — User Auth Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router,   prefix="/api/v1/auth",  tags=["Authentication"])
app.include_router(users.router,  prefix="/api/v1/users", tags=["Users"])
app.include_router(tokens.router, prefix="/api/v1/tokens",tags=["Tokens"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "user-auth-service"}
