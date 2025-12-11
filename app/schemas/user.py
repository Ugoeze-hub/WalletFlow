from pydantic import BaseModel
from typing import Optional
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class GoogleAuthURL(BaseModel):
    """Response containing Google OAuth URL for manual testing"""
    authorization_url: str
    instructions: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
                "instructions": "Open this URL in your browser, complete login, then copy the 'code' parameter from the redirect URL"
            }
        }
        
class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    
    class Config:
        from_attributes = True