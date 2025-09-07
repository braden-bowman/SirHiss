"""
API Credential model for managing external service credentials
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ApiCredential(Base):
    """API Credential model for external service authentication"""
    
    __tablename__ = "api_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # 'robinhood', 'yahoo_finance', etc.
    name = Column(String(100), nullable=False)  # Display name
    encrypted_credentials = Column(Text, nullable=False)  # JSON string of encrypted credentials
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    status = Column(String(20), default='untested')  # 'connected', 'error', 'untested'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="api_credentials")