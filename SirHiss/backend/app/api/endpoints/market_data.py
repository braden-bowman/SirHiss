"""
Market data management endpoints
Provides real-time and historical market data access
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import time

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.exchange_api import get_configured_exchange
from app.services.data_monitor import MarketDataManager
from app.services.trading_strategies import TradingSignal, SignalType
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TickerResponse(BaseModel):
    """Ticker response schema"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: float
    price_change_24h: Optional[float] = None
    price_change_percent_24h: Optional[float] = None

class CandleResponse(BaseModel):
    """Candle response schema"""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    datetime: str

class TechnicalIndicatorResponse(BaseModel):
    """Technical indicators response schema"""
    symbol: str
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_20: Optional[float] = None
    atr: Optional[float] = None
    volume_sma: Optional[float] = None
    sentiment_score: Optional[float] = None
    timestamp: float

class MarketAlertResponse(BaseModel):
    """Market alert response schema"""
    type: str
    symbol: str
    message: str
    severity: str
    timestamp: float
    metadata: Dict[str, Any]

class TradingSignalResponse(BaseModel):
    """Trading signal response schema"""
    symbol: str
    strategy_name: str
    signal: str
    strength: float
    price: float
    timestamp: float
    metadata: Dict[str, Any]

# Global market data manager (will be initialized when needed)
market_data_manager: Optional[MarketDataManager] = None

def get_market_data_manager() -> MarketDataManager:
    """Get or create market data manager"""
    global market_data_manager
    if market_data_manager is None:
        exchange = get_configured_exchange()
        market_data_manager = MarketDataManager(exchange)
    return market_data_manager

@router.get("/ticker/{symbol}", response_model=TickerResponse)
async def get_ticker(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get current ticker information for symbol"""
    try:
        exchange = get_configured_exchange()
        ticker = exchange.get_ticker(symbol)
        
        return TickerResponse(
            symbol=ticker.symbol,
            price=ticker.price,
            bid=ticker.bid,
            ask=ticker.ask,
            volume=ticker.volume,
            timestamp=ticker.timestamp
        )
    except Exception as e:
        logger.error(f"Error getting ticker for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ticker data: {str(e)}"
        )

@router.get("/historical/{symbol}", response_model=List[CandleResponse])
async def get_historical_data(
    symbol: str,
    interval: str = "1h",
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get historical OHLCV data for symbol"""
    try:
        if limit > 1000:
            limit = 1000
        
        exchange = get_configured_exchange()
        candles = exchange.get_historical_data(symbol, interval, limit)
        
        return [
            CandleResponse(
                timestamp=candle.timestamp,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=candle.volume,
                datetime=datetime.fromtimestamp(candle.timestamp).isoformat()
            )
            for candle in candles
        ]
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get historical data: {str(e)}"
        )

@router.get("/indicators/{symbol}", response_model=TechnicalIndicatorResponse)
async def get_technical_indicators(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get technical indicators for symbol"""
    try:
        mdm = get_market_data_manager()
        market_data = mdm.get_cached_market_data(symbol)
        
        if not market_data:
            # If not cached, get fresh data
            exchange = get_configured_exchange()
            ticker = exchange.get_ticker(symbol)
            candles = exchange.get_historical_data(symbol, "1h", 200)
            
            # Calculate indicators
            from app.services.data_monitor import TechnicalIndicatorCalculator
            calculator = TechnicalIndicatorCalculator()
            indicators = calculator.calculate_all_indicators(candles)
            
            return TechnicalIndicatorResponse(
                symbol=symbol,
                rsi=indicators.get('rsi'),
                macd=indicators.get('macd'),
                macd_signal=indicators.get('macd_signal'),
                bb_upper=indicators.get('bb_upper'),
                bb_middle=indicators.get('bb_middle'),
                bb_lower=indicators.get('bb_lower'),
                sma_20=indicators.get('sma_20'),
                sma_50=indicators.get('sma_50'),
                ema_20=indicators.get('ema_20'),
                atr=indicators.get('atr'),
                volume_sma=indicators.get('volume_sma'),
                sentiment_score=0.5,  # Default neutral
                timestamp=time.time()
            )
        else:
            return TechnicalIndicatorResponse(
                symbol=symbol,
                rsi=market_data.technical_indicators.get('rsi'),
                macd=market_data.technical_indicators.get('macd'),
                macd_signal=market_data.technical_indicators.get('macd_signal'),
                bb_upper=market_data.technical_indicators.get('bb_upper'),
                bb_middle=market_data.technical_indicators.get('bb_middle'),
                bb_lower=market_data.technical_indicators.get('bb_lower'),
                sma_20=market_data.technical_indicators.get('sma_20'),
                sma_50=market_data.technical_indicators.get('sma_50'),
                ema_20=market_data.technical_indicators.get('ema_20'),
                atr=market_data.technical_indicators.get('atr'),
                volume_sma=market_data.technical_indicators.get('volume_sma'),
                sentiment_score=market_data.sentiment_score,
                timestamp=market_data.timestamp
            )
            
    except Exception as e:
        logger.error(f"Error getting technical indicators for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get technical indicators: {str(e)}"
        )

@router.get("/signals/{symbol}", response_model=List[TradingSignalResponse])
async def get_trading_signals(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Get trading signals for symbol"""
    try:
        exchange = get_configured_exchange()
        ticker = exchange.get_ticker(symbol)
        candles = exchange.get_historical_data(symbol, "1h", 200)
        
        # Generate signals from default strategies
        from app.services.trading_strategies import StrategyManager, get_default_strategies
        strategy_manager = StrategyManager()
        
        # Load default strategies
        for strategy in get_default_strategies():
            strategy_manager.add_strategy(strategy)
        
        signals = await strategy_manager.generate_signals(symbol, candles, ticker)
        
        return [
            TradingSignalResponse(
                symbol=signal.symbol,
                strategy_name=signal.strategy_name,
                signal=signal.signal.value,
                strength=signal.strength,
                price=signal.price,
                timestamp=signal.timestamp,
                metadata=signal.metadata
            )
            for signal in signals
        ]
        
    except Exception as e:
        logger.error(f"Error getting trading signals for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trading signals: {str(e)}"
        )

@router.get("/alerts", response_model=List[MarketAlertResponse])
async def get_market_alerts(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get recent market alerts"""
    try:
        mdm = get_market_data_manager()
        alerts = mdm.alert_system.get_recent_alerts(limit)
        
        return [
            MarketAlertResponse(
                type=alert['type'],
                symbol=alert.get('symbol', ''),
                message=alert['message'],
                severity=alert['severity'],
                timestamp=alert['timestamp'],
                metadata={k: v for k, v in alert.items() if k not in ['type', 'message', 'severity', 'timestamp']}
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(f"Error getting market alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market alerts: {str(e)}"
        )

@router.post("/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Add symbol to monitoring watchlist"""
    try:
        mdm = get_market_data_manager()
        # Start monitoring this symbol
        import asyncio
        asyncio.create_task(mdm.start_monitoring([symbol]))
        
        return {"message": f"Added {symbol} to watchlist", "symbol": symbol}
        
    except Exception as e:
        logger.error(f"Error adding {symbol} to watchlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to watchlist: {str(e)}"
        )

@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Remove symbol from monitoring watchlist"""
    try:
        # This would remove symbol from active monitoring
        # For now, just return success
        return {"message": f"Removed {symbol} from watchlist", "symbol": symbol}
        
    except Exception as e:
        logger.error(f"Error removing {symbol} from watchlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from watchlist: {str(e)}"
        )

@router.get("/search/{query}")
async def search_symbols(
    query: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Search for trading symbols"""
    try:
        # Mock symbol search - in real implementation this would query exchange APIs
        common_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "BTC", "ETH", "ADA", "SOL", "AVAX", "DOT", "LINK", "UNI"
        ]
        
        filtered_symbols = [
            symbol for symbol in common_symbols 
            if query.upper() in symbol.upper()
        ][:limit]
        
        return {"symbols": filtered_symbols, "query": query}
        
    except Exception as e:
        logger.error(f"Error searching symbols for query {query}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search symbols: {str(e)}"
        )