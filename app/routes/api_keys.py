from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyRollover
from app.auth.jwt_auth import get_current_user_or_api_key
from app.auth.api_key_auth import create_api_key, revoke_api_key, rollover_api_key, list_user_api_keys
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

@router.post("/revoke/{key_id}")
async def api_key_revoke(
    key_id: str,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Revoke (deactivate) an API key"""
    user_id, _ = auth
     
    success = revoke_api_key(db=db, user_id=user_id, api_key_string=key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found or already revoked")
    
    return {"message": "API key revoked successfully"}


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
    
@router.get("/all")
async def list_api_keys(
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user"""
    user_id, _ = auth
    
    keys = list_user_api_keys(db=db, user_id=user_id)
    
    return {
        "user_id": user_id,
        "total_keys": len(keys),
        "keys": keys
    }