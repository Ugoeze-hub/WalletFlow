from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from jwt import JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.user import TokenData
from app.auth.api_key_auth import hash_api_key

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(user_id: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
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
        if user_id is None:
            return None
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None
    
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id:
        return (user_id)
    raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_or_api_key(
    request,
    db: Session = Depends(get_db)
):
    api_key = request.headers.get("x-api-key")
    
    if api_key:
        api_key_obj = db.query(APIKey).filter(
            APIKey.key == api_key,
            APIKey.is_active == True,
            APIKey.expires_at > datetime.now(timezone.utc)
        ).first()
        
        if not api_key_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key"
            )
        
        user = db.query(User).filter(User.id == api_key_obj.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user.id, api_key_obj.permissions
    
    else:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise credentials_exception
        
        token = auth_header.split(" ")[1]
        user_id = verify_token(token)
        if user_id:
            return (user_id, ["deposit", "transfer", "read"])
        raise HTTPException(status_code=401, detail="Invalid token")

def check_permissions(required_permissions: list, user_permissions: str):
    import json
    actual_permissions = json.loads(user_permissions) if user_permissions else []
    
    for perm in required_permissions:
        if perm not in actual_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {perm}"
            )