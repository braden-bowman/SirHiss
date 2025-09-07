"""
Holding model for tracking current positions
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Holding(Base):
    """Holding model for tracking current positions"""
    
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("trading_bots.id"), nullable=False)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Numeric(15, 8), nullable=False, default=0)
    average_cost = Column(Numeric(15, 2), nullable=False, default=0)
    current_price = Column(Numeric(15, 2), default=0)
    market_value = Column(Numeric(15, 2), default=0)
    unrealized_pl = Column(Numeric(15, 2), default=0)
    asset_type = Column(String(20), default="stock")  # stock, crypto, option
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    bot = relationship("TradingBot", back_populates="holdings")