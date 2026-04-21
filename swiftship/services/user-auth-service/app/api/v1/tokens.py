from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.jwt import verify_token

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post("/verify")
async def verify(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"valid": True, "user_id": payload.get("user_id"), "role": payload.get("role")}
