from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def webhook_health():
    return {"status": "ok"}
