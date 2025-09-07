"""
Trading bot model for managing automated trading strategies
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TradingBot(Base):
    """Trading bot model for automated trading strategies"""
    
    __tablename__ = "trading_bots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    allocated_percentage = Column(Numeric(5, 2), nullable=False)
    allocated_amount = Column(Numeric(15, 2), default=0.00)
    current_value = Column(Numeric(15, 2), default=0.00)
    status = Column(String(20), default="stopped")  # running, stopped, paused, error
    strategy_code = Column(Text)
    parameters = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="trading_bots")
    portfolio = relationship("Portfolio", back_populates="trading_bots")
    executions = relationship("BotExecution", back_populates="bot", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="bot", cascade="all, delete-orphan")