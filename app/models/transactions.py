from sqlalchemy import Column, String, Float, Text, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
import uuid
import enum
from app.database import Base
from sqlalchemy.orm import relationship

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey('wallets.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default='NGN', nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    recipient_wallet_id = Column(UUID(as_uuid=True), ForeignKey('wallets.id'), nullable=True)
    sender_wallet_id = Column(UUID(as_uuid=True), ForeignKey('wallets.id'), nullable=True)
    description = Column(Text)
    reference = Column(String, unique=True, index=True, nullable=False)
    transaction_data = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="transactions")
    wallet = relationship("Wallet", back_populates="primary_transactions", foreign_keys=[wallet_id])
    recipient_wallet = relationship("Wallet", back_populates="received_transactions", foreign_keys=[recipient_wallet_id])
    sender_wallet = relationship("Wallet", back_populates="sent_transactions",  foreign_keys=[sender_wallet_id])