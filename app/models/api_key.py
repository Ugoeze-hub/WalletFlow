from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.database import Base
from sqlalchemy.orm import relationship

class PermissionType(str, enum.Enum):
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    READ = "read"


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(Enum(PermissionType), nullable=False)  
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="api_keys")
    