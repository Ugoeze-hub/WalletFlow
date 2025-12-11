from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import datetime, timezone
from app.models.transactions import TransactionType, TransactionStatus

class WalletResponse(BaseModel):
    wallet_number: str
    balance: Decimal
    
    
    model_config = ConfigDict(from_attributes=True)


class DepositRequest(BaseModel):
    amount: Decimal = Field(
        ...,
        gt=0, 
        description="Amount to deposit in Naira (minimum: 100 NGN)"
    )
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v < 100:
            raise ValueError("Amount must be at least 100 NGN")
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 5000.00
            }
        }
    )

class DepositResponse(BaseModel):
    reference: str
    authorization_url: str
    message: str

class TransferRequest(BaseModel):
    wallet_number: str
    amount: Decimal
    
    amount: Decimal = Field(
        ...,
        gt=0,  # Must be greater than 0
        description="Amount to deposit in Naira (minimum: 100 NGN)"
    )
    
    @field_validator('amount')
    def validate_amount(cls, v):
        if v < 100:
            raise ValueError("Amount must be at least 100 NGN")
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 5000.00,
                "wallet_number": "1234567890"
            }
        }
    )

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
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat() if dt.tzinfo else dt.replace(tzinfo=timezone.utc).isoformat(),
            Decimal: lambda d: float(d)
        }
    )
