import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Dict
from sqlalchemy.orm import Session
from app.models.api_key import APIKey
from app.config import settings
import hashlib

def hash_api_key(key: str) -> str:
    """Hash the API key using SHA-256"""
    return hashlib.sha256(key.encode()).hexdigest()

def generate_id():
    return secrets.token_urlsafe(16)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return settings.API_KEY_PREFIX + secrets.token_urlsafe(32)

def parse_expiry(expiry_str: str) -> datetime:
    """Convert expiry string to datetime"""
    now = datetime.now(timezone.utc)
    
    if expiry_str == "1H":
        return now + timedelta(hours=1)
    elif expiry_str == "1D":
        return now + timedelta(days=1)
    elif expiry_str == "1M":
        return now + timedelta(days=30) 
    elif expiry_str == "1Y":
        return now + timedelta(days=365)
    else:
        raise ValueError("Invalid expiry string")

def create_api_key(
    db: Session,
    user_id: str,
    name: str,
    permissions: list,
    expiry_str: str
) -> Dict:
    """Create a new API key for user"""
    active_keys = db.query(APIKey).filter(
        APIKey.user_id == user_id,
        APIKey.is_active == True,
        APIKey.expires_at > datetime.now(timezone.utc)
    ).count()
    
    if active_keys >= settings.MAX_API_KEYS_PER_USER:
        raise Exception(f"Maximum {settings.MAX_API_KEYS_PER_USER} active API keys allowed")
    
    key = generate_api_key()
    expires_at = parse_expiry(expiry_str)
    
    api_key = APIKey(
        user_id=user_id,
        name=name,
        key=hash_api_key(key),
        permissions=json.dumps(permissions),
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return {
        "api_key": key,
        "expires_at": expires_at
    }

def rollover_api_key(
    db: Session,
    user_id: int,
    expired_key_id: str,
    expiry_str: str
) -> Dict:
    """Rollover an expired API key"""
    expired_key = db.query(APIKey).filter(
        APIKey.id == expired_key_id,
        APIKey.user_id == user_id,
        APIKey.expires_at <= datetime.now(timezone.utc)
    ).first()
    
    if not expired_key:
        raise Exception("Expired key not found or still active")
    
    permissions = json.loads(expired_key.permissions)
    
    new_key_data = create_api_key(
        db=db,
        user_id=user_id,
        name=expired_key.name,
        permissions=permissions,
        expiry_str=expiry_str
    )
    
    return new_key_data