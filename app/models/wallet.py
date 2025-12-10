from sqlalchemy import Column, String, DateTime, Float, ForeignKey, func
from app.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), index=True, unique=True, nullable=False)
    wallet_number = Column(String, unique=True, index=True, nullable=False)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="wallet")
    sent_transactions = relationship("Transaction", back_populates="wallet", foreign_keys="Transaction.wallet_id")
    received_transactions = relationship("Transaction", back_populates="recipient_wallet", foreign_keys="Transaction.recipient_wallet_id"
    )
    