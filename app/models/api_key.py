from sqlalchemy import Column, String, ForeignKey, Boolean, func, JSON
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
import uuid
from app.database import Base
from sqlalchemy.orm import relationship


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(JSON, nullable=False)  
    is_active = Column(Boolean, default=True)
    expires_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="api_keys")
    