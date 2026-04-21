"""
Operations Service — SwiftShip
Handles: manifests, route dispatch, hub management, sorting, reports, exceptions
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import manifests, dispatch, hubs, reports, exceptions
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="SwiftShip — Operations Service",
    description="Hub operations, manifests, dispatch, route management",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(manifests.router, prefix="/api/v1/operations/manifests", tags=["Manifests"])
app.include_router(dispatch.router, prefix="/api/v1/operations/dispatch", tags=["Dispatch"])
app.include_router(hubs.router, prefix="/api/v1/operations/hubs", tags=["Hubs"])
app.include_router(reports.router, prefix="/api/v1/operations/reports", tags=["Reports"])
app.include_router(exceptions.router, prefix="/api/v1/operations/exceptions", tags=["Exceptions"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "operations-service"}
