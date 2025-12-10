from pydantic import BaseModel, field_validator
from datetime import datetime
from app.models.transactions import TransactionType, TransactionStatus

class WalletResponse(BaseModel):
    wallet_number: str
    balance: float
    
    class Config:
        from_attributes = True

class DepositRequest(BaseModel):
    amount: float
    
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
    amount: float
    
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
    amount: float
    
class BalanceResponse(BaseModel):
    balance: float
    
class TransactionResponse(BaseModel):
    type: TransactionType
    amount: float
    status: TransactionStatus
    reference: str
    created_at: datetime
    
    class Config:
        from_attributes = True