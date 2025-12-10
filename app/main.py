from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import Base, engine
from app.routes import auth_router, wallet_router, api_keys_router
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Wallet Service...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise
    yield
    
    logger.warning("Shutting down Wallet Service...")

app = FastAPI(
    title="WalletFlow API",
    description="A wallet service with Paystack integration",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,
    session_cookie="wallet_session",
    max_age=14*24*60*60,
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(api_keys_router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "WalletFlow API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}