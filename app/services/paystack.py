import httpx
import uuid
from typing import Optional, Any
from app.config import settings

class Paystack:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize_transaction(self, email: str, amount: float, reference: Optional[str] = None, callback_url: str = None) -> dict[str, Any]:
        """Initialize a Paystack transaction"""
        if reference is None:
            reference = str(uuid.uuid4())
        
        payload = {
            "email": email,
            "amount": int(amount * 100), 
            "reference": reference,
            "callback_url": "http://localhost:8000/wallet/deposit/verify"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.PAYSTACK_INITIALIZE_URL,
                json=payload,
                headers=self.headers
            )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "reference": data["data"]["reference"],
                "authorization_url": data["data"]["authorization_url"]
            }
        else:
            raise Exception(f"Paystack error: {response.text}")
    
    async def verify_transaction(self, reference: str):
        """Verify a transaction status"""
        
        url = f"{settings.PAYSTACK_VERIFY_URL}/{reference}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers
            )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": data["data"]["status"],
                "amount": data["data"]["amount"] / 100, 
                "reference": data["data"]["reference"]
            }
        else:
            raise Exception(f"Paystack error: {response.text}")

paystack = Paystack()