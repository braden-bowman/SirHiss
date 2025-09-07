"""
Market data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.market_data import MarketData

router = APIRouter()


class MarketDataResponse(BaseModel):
    """Market data response schema"""
    symbol: str
    price: Decimal
    volume: int
    market_cap: Optional[Decimal]
    pe_ratio: Optional[Decimal]
    data_source: str
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/quote/{symbol}", response_model=MarketDataResponse)
async def get_quote(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get latest quote for a symbol"""
    # Get latest market data from cache
    market_data = db.query(MarketData).filter(
        MarketData.symbol == symbol.upper()
    ).order_by(MarketData.timestamp.desc()).first()
    
    if not market_data:
        # TODO: Fetch from Robinhood API and cache
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for symbol {symbol}"
        )
    
    return market_data


@router.get("/search")
async def search_symbols(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for symbols"""
    # TODO: Implement symbol search via Robinhood API
    return {"symbols": [], "message": "Symbol search not implemented yet"}