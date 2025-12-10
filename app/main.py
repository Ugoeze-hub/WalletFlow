from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from app.routes import auth_router, wallet_router, api_keys_router

app = FastAPI(
    title="WalletFlow API",
    description="A wallet service with Paystack integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(wallet_router.router)
app.include_router(api_keys_router.router)

@app.lifespan("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified")

@app.get("/")
async def root():
    return {"status": "ok", "message": "WalletFlow API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}