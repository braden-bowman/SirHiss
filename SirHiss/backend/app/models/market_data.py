"""
Market data model for caching market information
"""

from sqlalchemy import Column, Integer, String, Numeric, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class MarketData(Base):
    """Market data model for caching market information"""
    
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False)
    price = Column(Numeric(15, 2), nullable=False)
    volume = Column(BigInteger, default=0)
    market_cap = Column(Numeric(20, 2))
    pe_ratio = Column(Numeric(10, 2))
    data_source = Column(String(50), default="robinhood")
    extra_data = Column(JSONB, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now())