from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str]
    expiry: str  # 1H, 1D, 1M, 1Y
    
    @field_validator('expiry')
    def validate_expiry(cls, v):
        valid_expiries = ['1H', '1D', '1M', '1Y']
        if v not in valid_expiries:
            raise ValueError(f'Expiry must be one of {valid_expiries}')
        return v

class APIKeyResponse(BaseModel):
    api_key: str
    expires_at: datetime
    
    class Config:
        from_attributes = True
    


class APIKeyRollover(BaseModel):
    expired_key_id: str
    expiry: str
    
    @field_validator('expiry')
    def validate_expiry(cls, v):
        valid_expiries = ['1H', '1D', '1M', '1Y']
        if v not in valid_expiries:
            raise ValueError(f'Expiry must be one of {valid_expiries}')
        return v