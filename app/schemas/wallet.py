from pydantic import BaseModel, field_validator
from decimal import Decimal
from datetime import datetime
from app.models.transactions import TransactionType, TransactionStatus

class WalletResponse(BaseModel):
    wallet_number: str
    balance: Decimal
    
    class Config:
        from_attributes = True

class DepositRequest(BaseModel):
    amount: Decimal
    
    @field_validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class DepositResponse(BaseModel):
    reference: str
    authorization_url: str
    message: str

class TransferRequest(BaseModel):
    wallet_number: str
    amount: Decimal
    
    @field_validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class TransferResponse(BaseModel):
    status: str
    message: str
    
class PaystackResponse(BaseModel):
    status: str
    message: str

class DepositStatusResponse(BaseModel):
    reference: str
    status: str
    amount: Decimal
    
class BalanceResponse(BaseModel):
    balance: Decimal
    
class TransactionResponse(BaseModel):
    type: TransactionType
    amount: Decimal
    status: TransactionStatus
    reference: str
    created_at: datetime
    
    class Config:
        from_attributes = True