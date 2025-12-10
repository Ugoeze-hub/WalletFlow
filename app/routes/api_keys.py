from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyRollover
import app.schemas.api_key as schemas
from app.auth import get_current_user
from app.auth.api_key_auth import create_api_key, rollover_api_key
from app.database import get_db

router = APIRouter(prefix="/keys", tags=["api-keys"])

@router.post("/create", response_model=APIKeyResponse)
async def create_api_key_endpoint(
    api_key_data: APIKeyCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    try:
        result = create_api_key(
            db=db,
            user_id=current_user.id,
            name=api_key_data.name,
            permissions=api_key_data.permissions,
            expiry_str=api_key_data.expiry
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/rollover", response_model=schemas.APIKeyResponse)
async def rollover_api_key_endpoint(
    rollover_data: schemas.APIKeyRollover,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rollover an expired API key"""
    try:
        result = rollover_api_key(
            db=db,
            user_id=current_user.id,
            expired_key_id=rollover_data.expired_key_id,
            expiry_str=rollover_data.expiry
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))