from pydantic import BaseModel
from typing import Optional
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    
class TokenResponse(Token):
    user_id: str
    email: str
    name: Optional[str] = None
    message: str = "Authentication successful"
    