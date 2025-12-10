from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
import json
import uuid
from app.auth.jwt_auth import get_current_user_or_api_key, check_permissions
from app.auth.api_key_auth import generate_id
from app.models.wallet import Wallet
from app.models.transactions import TransactionType, TransactionStatus, Transaction
from app.models.user import User
from app.schemas.wallet import (
    DepositStatusResponse, 
    DepositResponse, 
    DepositRequest,
    WalletResponse, 
    BalanceResponse, 
    TransferRequest, 
    TransferResponse, 
    TransactionResponse,
    PaystackResponse
)
    
from app.services.paystack import paystack
from app.database import get_db
from app.services.webhooks import verify_paystack_signature
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.post("/deposit", response_model=DepositResponse)
async def deposit(
    deposit_data: DepositRequest,
    request: Request,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Initialize a Paystack deposit"""
    user_id, permissions = auth
    
    check_permissions(["deposit"], permissions)
    
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    reference = f"dep_{generate_id()}"
    
    try:
        result = await paystack.initialize_transaction(
            email=db.query(User).filter(User.id == user_id).first().email,
            amount=deposit_data.amount,
            reference=reference
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    transaction = Transaction(
        user_id=user_id,
        wallet_id=wallet.id,
        amount=deposit_data.amount,
        transaction_type=TransactionType.DEPOSIT,
        status=TransactionStatus.PENDING,
        reference=reference,
        transaction_data=json.dumps({
            "authorization_url": result["authorization_url"],
            "provider": "paystack"
            })
    )
    
    db.add(transaction)
    db.commit()
    
    return DepositResponse(
        reference=reference,
        authorization_url=result["authorization_url"],
        message=f"Deposit of {transaction.amount} successfull"
    )

@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Paystack webhook notifications"""
    body = await request.body()
    signature = request.headers.get("x-paystack-signature")
    logger.info("Received Paystack webhook")
    
    if not verify_paystack_signature(body, signature):
        logger.error("Invalid Paystack webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    event = data.get("event")
    logger.info(f"Processing Paystack event: {event}")
    
    if event == "charge.success":
        reference = data["data"]["reference"]
        amount = data["data"]["amount"] / 100
        
        transaction = db.query(Transaction).filter(
            Transaction.reference == reference
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
                )
        
        if transaction.status == TransactionStatus.SUCCESS:
            return {"status": True}
        
        transaction.status = TransactionStatus.SUCCESS
        transaction.transaction_data = json.dumps(data["data"])
        
        wallet = db.query(Wallet).filter(
            Wallet.user_id == transaction.user_id
        ).first()
        
        if wallet:
            wallet.balance += amount
            logger.info(f"Wallet {wallet.wallet_number} credited with {amount}")
        
        db.commit()
        logger.info(f"Transaction {reference} marked as SUCCESS")
    
    return PaystackResponse(
        status="success",
        message="Webhook processed"
    )

@router.get("/deposit/{reference}/status", response_model=DepositStatusResponse)
async def check_deposit_status(
    reference: str,
    request: Request,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Check deposit status (manual verification)"""
    user_id, permissions = auth
    check_permissions(["read"], permissions)
    
    transaction = db.query(Transaction).filter(
        Transaction.reference == reference,
        Transaction.user_id == user_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return DepositStatusResponse(
        reference=transaction.reference,
        status=transaction.status.value,
        amount=transaction.amount
    )

@router.get("/balance", response_model=WalletResponse)
async def get_balance(
    request: Request,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Get wallet balance"""
    user_id, permissions = auth
    
    check_permissions(["read"], permissions)
    
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return WalletResponse(
        wallet_number=wallet.wallet_number,
        balance=wallet.balance
       )

@router.post("/transfer", response_model=TransferResponse)
async def transfer(
    transfer_data: TransferRequest,
    request: Request,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Transfer funds to another wallet"""
    user_id, permissions = auth
    
    check_permissions(["transfer"], permissions)
    
    sender_wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not sender_wallet:
        raise HTTPException(status_code=404, detail="Sender wallet not found")
    
    if transfer_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    if sender_wallet.balance < transfer_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    recipient_wallet = db.query(Wallet).filter(
        Wallet.wallet_number == transfer_data.wallet_number
    ).first()
    
    if not recipient_wallet:
        raise HTTPException(status_code=404, detail="Recipient wallet not found")
    
    if recipient_wallet.user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")
    
    try:
        sender_wallet.balance -= transfer_data.amount
        
        recipient_wallet.balance += transfer_data.amount
        user = db.query(User).filter(User.id == user_id).first()
        
        sender_transaction = Transaction(
            user_id=user.id,
            wallet_id=sender_wallet.id,
            sender_wallet_id=sender_wallet.id,
            recipient_wallet_id=recipient_wallet.id,
            amount=transfer_data.amount,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.SUCCESS,            
            reference=str(uuid.uuid4()),
            description=f"Transfer to {recipient_wallet.wallet_number}",
            transaction_data=json.dumps({
                "recipient_wallet": transfer_data.wallet_number,
                "type": "outgoing",
                "recipient_user_id": str(recipient_wallet.user_id)
            })
        )
        
        recipient_transaction =Transaction(
            user_id=recipient_wallet.user_id,
            wallet_id=recipient_wallet.id,
            sender_wallet_id=sender_wallet.id,
            recipient_wallet_id=recipient_wallet.id,
            amount=transfer_data.amount,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.SUCCESS,
            reference=generate_id(),
            description=f"Transfer from {sender_wallet.wallet_number}",
            transaction_data=json.dumps({
                "sender_wallet": sender_wallet.wallet_number,
                "type": "incoming",
                "sender_user_id": str(sender_wallet.user_id)
            })
        )
        
        db.add(sender_transaction)
        db.add(recipient_transaction)
        db.commit()
        
        return TransferResponse(
            status="success",
            message="Transfer completed"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")
    

@router.get("/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    request: Request,
    auth: tuple = Depends(get_current_user_or_api_key),
    db: Session = Depends(get_db)
):
    """Get transaction history"""
    user_id, permissions = auth
    
    check_permissions(["read"], permissions)
    user = db.query(User).filter(User.id == user_id).first()
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.created_at.desc()).all()
    
    return [
            TransactionResponse(
            type=transaction.transaction_type.value,
            amount=transaction.amount,
            status=transaction.status.value,
            reference=transaction.reference,
            created_at=transaction.created_at,
            description=transaction.description
            ) for transaction in transactions
            ]