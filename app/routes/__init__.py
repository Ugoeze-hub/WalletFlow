"""Routes package - imports all routers"""

from app.routes.auth import router as auth_router
from app.routes.api_keys import router as api_keys_router
from app.routes.wallet import router as wallet_router

__all__ = [
    "auth_router",
    "api_keys_router",
    "wallet_router",
    "paystack_router",
]