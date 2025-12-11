import httpx
import uuid
import hashlib
import hmac
from typing import Optional, Any
from decimal import Decimal
from app.config import settings
from sqlalchemy.orm import Session
from app.models.transactions import Transaction, TransactionStatus
from app.models.wallet import Wallet
from fastapi import HTTPException
import json
import logging


logger = logging.getLogger(__name__)

class Paystack:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.initialize_url = settings.PAYSTACK_INITIALIZE_URL
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }

    def verify_paystack_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Paystack webhook signature"""
        if not signature:
            return False
        secret_key = self.secret_key.encode()
        
        computed_signature = hmac.new(
            secret_key,
            payload,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)
    
    async def initialize_transaction(
        self,
        email: str,
        amount: Decimal,
        reference: Optional[str] = None,
        callback_url: str = None,
        metadata: Optional[dict] = None
        ) -> dict[str, Any]:
        """Initialize a Paystack transaction"""
        if not self.secret_key:
            raise Exception("Paystack secret key not configured")
        
        payload = {
            "email": email,
            "amount": int(amount * 100), 
            "reference": reference
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
        
        if metadata:
            payload["metadata"] = metadata
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.initialize_url,
                json=payload,
                headers=self.headers,
                timeout=30.0,
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
        
        if not self.secret_key:
            raise Exception("Paystack secret key not configured")
        
        url = f"{settings.PAYSTACK_VERIFY_URL}/{reference}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                timeout=30.0,
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
        
        
    async def handle_charge_success(self, data: dict, db: Session):
        """Handle Successful payment charge"""
        try:
            reference = data["data"]["reference"]
            amount = data["data"]["amount"] / 100
            logger.info(f"Processing successful charge for reference: {reference} - ₦{amount}")
        
            transaction = db.query(Transaction).filter(
                Transaction.reference == reference
            ).first()
            
            if not transaction:
                logger.error(f"Transaction with reference {reference} not found")
                raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )
                
            if transaction.status == TransactionStatus.SUCCESS:
                logger.info(f"Transaction already processed: {reference}")
                return {"status": True}
            
            transaction.status = TransactionStatus.SUCCESS
            transaction.transaction_data = json.dumps(data["data"])
        
            wallet = db.query(Wallet).filter(
                Wallet.user_id == transaction.user_id
            ).first()
        
            if wallet:
                old_balance = wallet.balance
                wallet.balance += amount
                logger.info(f"Wallet {wallet.wallet_number} credited: "
                            f"₦{old_balance} - ₦{wallet.balance}")
            
            else:
                logger.error(f"Wallet not found for user: {transaction.user_id}")
        
            db.commit()
            logger.info(f"Transaction {reference} completed successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error handling charge.success: {str(e)}")
            raise

    
paystack = Paystack()