"""
Bot execution model for tracking trading bot activities
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class BotExecution(Base):
    """Bot execution model for tracking trading activities"""
    
    __tablename__ = "bot_executions"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("trading_bots.id"), nullable=False)
    execution_type = Column(String(20), nullable=False)  # buy, sell, analysis
    symbol = Column(String(10))
    quantity = Column(Numeric(15, 8))
    price = Column(Numeric(15, 2))
    total_value = Column(Numeric(15, 2))
    status = Column(String(20), default="pending")  # pending, completed, failed, cancelled
    error_message = Column(Text)
    execution_data = Column(JSONB, default={})
    executed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bot = relationship("TradingBot", back_populates="executions")