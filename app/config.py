from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "WalletFlow API"
    
    PAYSTACK_INITIALIZE_URL: str
    PAYSTACK_VERIFY_URL: str
    
    DATABASE_URL: str
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    PAYSTACK_WEBHOOK_SECRET: str
    
    API_KEY_PREFIX: str
    MAX_API_KEYS_PER_USER: int 
    
    class Config:
        env_file = ".env"

settings = Settings()