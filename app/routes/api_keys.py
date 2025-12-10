from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyRollover
from app.auth.jwt_auth import get_current_user_or_api_key
from app.auth.api_key_auth import create_api_key, rollover_api_key
from app.database import get_db

router = APIRouter(prefix="/keys", tags=["api-keys"])

@router.post("/create", response_model=APIKeyResponse)
async def api_key(
    api_key_data: APIKeyCreate,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    user_id, permissions = auth
    
    try:
        result = create_api_key(
            db=db,
            user_id=user_id,
            name=api_key_data.name,
            permissions=api_key_data.permissions,
            expiry_str=api_key_data.expiry
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollover", response_model=APIKeyResponse)
async def api_key_rollover(
    rollover_data: APIKeyRollover,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Rollover an expired API key"""
    user_id, permissions = auth
    
    try:
        result = rollover_api_key(
            db=db,
            user_id=user_id,
            expired_key_id=rollover_data.expired_key_id,
            expiry_str=rollover_data.expiry
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))