from pydantic import BaseModel, field_validator, ConfigDict
from typing import List
from datetime import datetime, timezone

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str]
    expiry: str  # 1H, 1D, 1M, 1Y
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "key_name",
                "permissions": [
                    "deposit"
                ],
                "expiry": "1M"
            }
        }
    )

class APIKeyResponse(BaseModel):
    api_key: str
    expires_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.astimezone(timezone.utc).isoformat(),
        }
    )



class APIKeyRollover(BaseModel):
    expired_key_id: str
    expiry: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expired_key_id": "abc123def456",
                "expiry": "1M"
            }
        }
    )