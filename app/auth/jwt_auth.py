from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.user import TokenData
from app.auth.api_key_auth import hash_api_key
import json
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

def create_access_token(user_id: str, user_email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_email,
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("user_id")
        return str(user_id) if user_id else None
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None
    

async def get_current_user_or_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Tuple[str, list]:
    
    headers = dict(request.headers) if request else {}
    logger.info(f"Headers: {headers}")
    
    if request:
        api_key = request.headers.get("x-api-key")
    
        if api_key:
            logger.info("API key found in headers, attempting API key authentication")
            return await _authenticate_by_api_key(api_key, db)
        
    if credentials and credentials.credentials:
        logger.info("Bearer token found in headers, attempting JWT authentication")
        return await _authenticate_by_jwt(credentials.credentials, db)
    
    logger.warning("No authentication credentials provided")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
        
       
async def _authenticate_by_api_key(api_key: str, db: Session) -> Tuple[str, list]:
    """Authenticate using API Key"""
    try:
        active_keys = db.query(APIKey).filter(
            APIKey.key == api_key,
            APIKey.is_active == True
        ).all()
        
        logger.info(f"Active API key query result: {len(active_keys) if active_keys else 0}")
            
        for key_obj in active_keys:
            if pwd_context.verify(api_key, key_obj.key):  
                logger.info(f"API key authenticated for user_id: {key_obj.user_id}")
            
            user = db.query(User).filter(User.id == key_obj.user_id).first()
            if user:
                
                permissions = []
                try:
                    if key_obj.permissions:
                        permissions = json.loads(key_obj.permissions)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode permissions for API key {key_obj.id}")
                
            return user.id, permissions
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
            )
        
    except Exception as e:
        logger.error(f"API key authentication error: {str(e)}") 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
        
        
async def _authenticate_by_jwt(token: str, db: Session) -> Tuple[str, list]:
    """Authenticate using JWT token"""
    try:
        user_id = verify_token(token)
        if not user_id:
            logger.error("Token verification failed")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found in DB: {user_id}")
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
        
        logger.info(f"User {user_id} authenticated")
        return str(user_id), ["deposit", "transfer", "read"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JWT authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"JWT authentication failed: {str(e)}"
        )

def check_permissions(required_permissions: list, user_permissions: list):
    for perm in required_permissions:
        if perm not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {perm}"
            )