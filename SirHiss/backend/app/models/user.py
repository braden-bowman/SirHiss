"""
User model for authentication and authorization with comprehensive account management
"""

import secrets
import string
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """
    User model for application authentication and account management
    
    Includes comprehensive user tracking with account numbers, creation details,
    and relationship management for trading operations.
    """
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(20), unique=True, index=True, nullable=False)  # Format: SH-XXXX-XXXX-XXXX
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Account metadata
    full_name = Column(String(100), nullable=True)  # Optional full name
    phone_number = Column(String(20), nullable=True)  # Optional phone
    registration_ip = Column(String(45), nullable=True)  # IPv4/IPv6 support
    email_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    login_count = Column(Integer, default=0)
    
    # Account status and risk management
    account_status = Column(String(20), default='active')  # active, suspended, closed
    risk_level = Column(String(10), default='medium')  # low, medium, high
    kyc_status = Column(String(20), default='pending')  # pending, verified, rejected
    
    # Timestamps with timezone awareness
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Additional account metadata as JSON-compatible text
    account_metadata = Column(Text, nullable=True)  # JSON string for additional account info

    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    trading_bots = relationship("TradingBot", back_populates="user", cascade="all, delete-orphan")
    api_credentials = relationship("ApiCredential", back_populates="user", cascade="all, delete-orphan")
    
    @classmethod
    def generate_account_number(cls) -> str:
        """
        Generate a unique SirHiss account number
        Format: SH-XXXX-XXXX-XXXX where X is alphanumeric
        """
        # Generate 3 groups of 4 alphanumeric characters
        chars = string.ascii_uppercase + string.digits
        groups = []
        for _ in range(3):
            group = ''.join(secrets.choice(chars) for _ in range(4))
            groups.append(group)
        
        return f"SH-{'-'.join(groups)}"
    
    def update_login_info(self, ip_address: str = None):
        """Update login tracking information"""
        from datetime import datetime
        self.last_login_at = datetime.utcnow()
        self.login_count += 1
        if ip_address:
            self.last_login_ip = ip_address
    
    def get_account_age_days(self) -> int:
        """Get account age in days"""
        from datetime import datetime
        if self.created_at:
            return (datetime.utcnow() - self.created_at.replace(tzinfo=None)).days
        return 0
    
    def is_verified(self) -> bool:
        """Check if account is fully verified"""
        return self.email_verified and self.kyc_status == 'verified'
    
    def get_display_name(self) -> str:
        """Get display name (full name or username)"""
        return self.full_name if self.full_name else self.username.title()