"""
Real-time Data Monitoring System for SirHiss Trading Platform
Handles market data collection, technical analysis, and risk monitoring
"""

import asyncio
import time
import logging
import numpy as np
import pandas as pd
import threading
import queue
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import statistics

from .exchange_api import BaseExchange, Ticker, Candle
from .trading_strategies import TradingSignal, SignalType, TechnicalAnalyzer
from ..models.trading_bot import TradingBot
from ..core.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Container for comprehensive market data"""
    symbol: str
    ticker: Ticker
    candles: List[Candle]
    technical_indicators: Dict[str, float] = field(default_factory=dict)
    sentiment_score: float = 0.5
    volume_profile: Dict[str, float] = field(default_factory=dict)
    order_book_imbalance: float = 0.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class RiskMetrics:
    """Risk management metrics"""
    portfolio_value: float = 0.0
    total_exposure: float = 0.0
    max_drawdown: float = 0.0
    var_95: float = 0.0  # Value at Risk 95%
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    avg_trade_return: float = 0.0

class TechnicalIndicatorCalculator:
    """Calculate technical indicators for market data"""
    
    @staticmethod
    def calculate_all_indicators(candles: List[Candle]) -> Dict[str, float]:
        """Calculate comprehensive technical indicators"""
        if len(candles) < 50:
            return {}
        
        # Convert to numpy arrays
        closes = np.array([c.close for c in candles])
        highs = np.array([c.high for c in candles])
        lows = np.array([c.low for c in candles])
        volumes = np.array([c.volume for c in candles])
        
        indicators = {}
        
        try:
            # Moving Averages
            indicators['sma_20'] = TechnicalAnalyzer.calculate_sma(closes.tolist(), 20)
            indicators['ema_20'] = TechnicalAnalyzer.calculate_ema(closes.tolist(), 20)
            indicators['sma_50'] = TechnicalAnalyzer.calculate_sma(closes.tolist(), 50)
            indicators['sma_200'] = TechnicalAnalyzer.calculate_sma(closes.tolist(), 200) if len(closes) >= 200 else 0
            
            # RSI
            rsi = TechnicalAnalyzer.calculate_rsi(closes.tolist(), 14)
            indicators['rsi'] = rsi
            indicators['rsi_oversold'] = rsi < 30
            indicators['rsi_overbought'] = rsi > 70
            
            # MACD
            macd, macd_signal, macd_hist = TechnicalAnalyzer.calculate_macd(closes.tolist())
            indicators['macd'] = macd
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_hist
            indicators['macd_bullish'] = macd > macd_signal
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = TechnicalAnalyzer.calculate_bollinger_bands(closes.tolist())
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
            indicators['bb_position'] = (closes[-1] - bb_lower) / (bb_upper - bb_lower) if bb_upper > bb_lower else 0.5
            
            # ATR (Average True Range) - simplified calculation
            if len(candles) >= 14:
                true_ranges = []
                for i in range(1, len(candles)):
                    tr1 = candles[i].high - candles[i].low
                    tr2 = abs(candles[i].high - candles[i-1].close)
                    tr3 = abs(candles[i].low - candles[i-1].close)
                    true_ranges.append(max(tr1, tr2, tr3))
                
                atr = sum(true_ranges[-14:]) / 14
                indicators['atr'] = atr
                indicators['atr_percent'] = atr / closes[-1]
            
            # Volume indicators
            indicators['volume_sma'] = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
            indicators['volume_ratio'] = volumes[-1] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1
            
            # Price action indicators
            indicators['price_change_1h'] = (closes[-1] - closes[-2]) / closes[-2] if len(closes) > 1 else 0
            indicators['price_change_24h'] = (closes[-1] - closes[-24]) / closes[-24] if len(closes) > 24 else 0
            
            # Support and resistance levels
            indicators['resistance'] = np.max(highs[-20:]) if len(highs) >= 20 else highs[-1]
            indicators['support'] = np.min(lows[-20:]) if len(lows) >= 20 else lows[-1]
            
            # Volatility
            if len(closes) > 1:
                returns = np.diff(closes) / closes[:-1]
                indicators['volatility'] = np.std(returns) if len(returns) > 1 else 0
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
        
        return indicators

class SentimentAnalyzer:
    """Analyze market sentiment from various sources"""
    
    def __init__(self):
        self.sentiment_cache = {}
        self.cache_duration = 900  # 15 minutes
        
    def get_fear_greed_index(self) -> float:
        """Get Fear & Greed Index (0-1 scale)"""
        try:
            response = requests.get("https://api.alternative.me/fng/", timeout=10)
            data = response.json()
            
            if data and 'data' in data and len(data['data']) > 0:
                value = int(data['data'][0]['value'])
                return value / 100.0  # Convert to 0-1 scale
                
        except Exception as e:
            logger.warning(f"Could not fetch Fear & Greed Index: {e}")
        
        return 0.5  # Neutral if unable to fetch
    
    def get_social_sentiment(self, symbol: str) -> float:
        """Get social media sentiment for symbol (mock implementation)"""
        try:
            # This would integrate with APIs like:
            # - Reddit API for r/cryptocurrency mentions
            # - Twitter API for $BTC mentions
            # - LunarCrush API for social metrics
            
            import random
            cache_key = f"social_{symbol}"
            current_time = time.time()
            
            if cache_key in self.sentiment_cache:
                cache_time, cached_sentiment = self.sentiment_cache[cache_key]
                if current_time - cache_time < self.cache_duration:
                    return cached_sentiment
            
            # Simulate sentiment analysis
            base_sentiment = 0.5 + random.uniform(-0.3, 0.3)
            self.sentiment_cache[cache_key] = (current_time, base_sentiment)
            
            return base_sentiment
            
        except Exception as e:
            logger.error(f"Error getting social sentiment for {symbol}: {e}")
            return 0.5
    
    def calculate_composite_sentiment(self, symbol: str) -> float:
        """Calculate composite sentiment score"""
        try:
            fear_greed = self.get_fear_greed_index()
            social = self.get_social_sentiment(symbol)
            
            # Weighted average
            composite = (fear_greed * 0.6 + social * 0.4)
            return max(0.0, min(1.0, composite))  # Clamp to 0-1
            
        except Exception as e:
            logger.error(f"Error calculating composite sentiment: {e}")
            return 0.5

class RiskManager:
    """Monitor and manage trading risks"""
    
    def __init__(self):
        self.max_portfolio_risk = 0.20  # 20% max portfolio risk
        self.max_position_size = 0.10   # 10% max single position
        self.max_drawdown_limit = 0.15  # 15% max drawdown
        self.var_confidence = 0.95      # 95% VaR confidence
        self.trade_history = deque(maxlen=1000)
        
    def calculate_position_size(self, signal_strength: float, portfolio_value: float, 
                              price: float, atr: float) -> float:
        """Calculate optimal position size using risk management"""
        try:
            # Kelly Criterion (simplified)
            win_rate = self.get_recent_win_rate()
            avg_win = self.get_avg_win()
            avg_loss = self.get_avg_loss()
            
            if avg_loss > 0:
                kelly_f = (win_rate * avg_win / avg_loss - (1 - win_rate)) / avg_win
                kelly_f = max(0, min(kelly_f, 0.25))  # Cap at 25%
            else:
                kelly_f = 0.1
            
            # ATR-based position sizing
            risk_amount = portfolio_value * self.max_position_size
            atr_risk = atr * 2.5  # 2.5x ATR stop loss
            
            # Position size based on ATR risk
            if atr_risk > 0:
                atr_position_size = risk_amount / (atr_risk * price)
            else:
                atr_position_size = 0
            
            # Combine Kelly and ATR sizing, adjusted by signal strength
            base_size = min(kelly_f, atr_position_size / portfolio_value) * portfolio_value
            adjusted_size = base_size * signal_strength
            
            # Final position size in base currency
            position_size = adjusted_size / price
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def get_recent_win_rate(self) -> float:
        """Calculate recent win rate from trade history"""
        if len(self.trade_history) < 10:
            return 0.5  # Default 50%
        
        recent_trades = list(self.trade_history)[-50:]  # Last 50 trades
        wins = sum(1 for trade in recent_trades if trade.get('pnl', 0) > 0)
        return wins / len(recent_trades)
    
    def get_avg_win(self) -> float:
        """Get average winning trade amount"""
        if not self.trade_history:
            return 0.02  # Default 2%
        
        wins = [trade['pnl'] for trade in self.trade_history if trade.get('pnl', 0) > 0]
        return statistics.mean(wins) if wins else 0.02
    
    def get_avg_loss(self) -> float:
        """Get average losing trade amount (positive value)"""
        if not self.trade_history:
            return 0.015  # Default 1.5%
        
        losses = [abs(trade['pnl']) for trade in self.trade_history if trade.get('pnl', 0) < 0]
        return statistics.mean(losses) if losses else 0.015
    
    def check_risk_limits(self, current_exposure: float, portfolio_value: float) -> bool:
        """Check if current exposure is within risk limits"""
        exposure_ratio = current_exposure / portfolio_value if portfolio_value > 0 else 0
        return exposure_ratio <= self.max_portfolio_risk
    
    def should_halt_trading(self, current_drawdown: float) -> bool:
        """Determine if trading should be halted due to excessive drawdown"""
        return current_drawdown >= self.max_drawdown_limit

class DataCollector:
    """Collect and manage real-time market data"""
    
    def __init__(self, exchange: BaseExchange):
        self.exchange = exchange
        self.data_queue = queue.Queue()
        self.subscribers = []
        self.is_running = False
        self.collection_interval = 60  # seconds
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.sentiment_analyzer = SentimentAnalyzer()
        
    def subscribe(self, callback: Callable[[MarketData], None]):
        """Subscribe to data updates"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[MarketData], None]):
        """Unsubscribe from data updates"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def _notify_subscribers(self, market_data: MarketData):
        """Notify all subscribers of new data"""
        for callback in self.subscribers:
            try:
                callback(market_data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def collect_data(self, symbols: List[str]):
        """Continuously collect market data for symbols"""
        self.is_running = True
        logger.info(f"Starting data collection for {symbols}")
        
        while self.is_running:
            try:
                for symbol in symbols:
                    # Get ticker data
                    ticker = self.exchange.get_ticker(symbol)
                    
                    # Get historical candles
                    candles = self.exchange.get_historical_data(symbol, "1h", 200)
                    
                    # Calculate technical indicators
                    indicators = self.technical_calculator.calculate_all_indicators(candles)
                    
                    # Get sentiment score
                    sentiment = self.sentiment_analyzer.calculate_composite_sentiment(symbol)
                    
                    # Create market data object
                    market_data = MarketData(
                        symbol=symbol,
                        ticker=ticker,
                        candles=candles,
                        technical_indicators=indicators,
                        sentiment_score=sentiment,
                        timestamp=time.time()
                    )
                    
                    # Notify subscribers
                    self._notify_subscribers(market_data)
                
                # Wait before next collection
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in data collection: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    def stop(self):
        """Stop data collection"""
        self.is_running = False
        logger.info("Data collection stopped")

class AlertSystem:
    """Handle trading alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            'price_change': 0.05,  # 5% price change
            'volume_spike': 2.0,   # 2x volume spike
            'signal_strength': 0.8  # High confidence signals
        }
        self.recent_alerts = deque(maxlen=100)
    
    def check_alerts(self, market_data: MarketData) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        
        try:
            # Price change alerts
            if len(market_data.candles) >= 2:
                price_change = (market_data.ticker.price - market_data.candles[-2].close) / market_data.candles[-2].close
                if abs(price_change) >= self.alert_thresholds['price_change']:
                    alert = {
                        'type': 'price_change',
                        'symbol': market_data.symbol,
                        'change': price_change,
                        'message': f"{market_data.symbol} price changed {price_change:.2%}",
                        'timestamp': time.time(),
                        'severity': 'high' if abs(price_change) > 0.1 else 'medium'
                    }
                    alerts.append(alert)
            
            # Volume spike alerts
            volume_ratio = market_data.technical_indicators.get('volume_ratio', 0)
            if volume_ratio >= self.alert_thresholds['volume_spike']:
                alert = {
                    'type': 'volume_spike',
                    'symbol': market_data.symbol,
                    'ratio': volume_ratio,
                    'message': f"{market_data.symbol} volume spike: {volume_ratio:.1f}x",
                    'timestamp': time.time(),
                    'severity': 'medium'
                }
                alerts.append(alert)
            
            # Technical indicator alerts
            rsi = market_data.technical_indicators.get('rsi', 50)
            if rsi <= 20 or rsi >= 80:
                alert = {
                    'type': 'rsi_extreme',
                    'symbol': market_data.symbol,
                    'rsi': rsi,
                    'message': f"{market_data.symbol} RSI extreme: {rsi:.1f}",
                    'timestamp': time.time(),
                    'severity': 'medium'
                }
                alerts.append(alert)
            
            # Store alerts
            for alert in alerts:
                self.recent_alerts.append(alert)
                self.send_alert(alert)
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
        
        return alerts
    
    def send_alert(self, alert: Dict[str, Any]):
        """Send alert notification"""
        logger.warning(f"ALERT: {alert['message']}")
        
        # Here you could integrate with:
        # - Email notifications
        # - Slack/Discord webhooks
        # - SMS services
        # - Push notifications
        # - Database storage for web interface
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return list(self.recent_alerts)[-limit:]

class MarketDataManager:
    """Central manager for market data collection and analysis"""
    
    def __init__(self, exchange: BaseExchange):
        self.exchange = exchange
        self.data_collector = DataCollector(exchange)
        self.risk_manager = RiskManager()
        self.alert_system = AlertSystem()
        self.market_data_cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def subscribe_to_data(self, callback: Callable[[MarketData], None]):
        """Subscribe to market data updates"""
        self.data_collector.subscribe(callback)
    
    def get_cached_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get cached market data for symbol"""
        if symbol in self.market_data_cache:
            data, timestamp = self.market_data_cache[symbol]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def cache_market_data(self, market_data: MarketData):
        """Cache market data"""
        self.market_data_cache[market_data.symbol] = (market_data, time.time())
    
    async def start_monitoring(self, symbols: List[str]):
        """Start monitoring specified symbols"""
        
        # Set up data processing callback
        def process_market_data(market_data: MarketData):
            # Cache the data
            self.cache_market_data(market_data)
            
            # Check for alerts
            alerts = self.alert_system.check_alerts(market_data)
            
            # Log data collection
            logger.info(f"Processed market data for {market_data.symbol}: "
                       f"${market_data.ticker.price:.2f} "
                       f"({len(market_data.technical_indicators)} indicators)")
        
        # Subscribe to data updates
        self.data_collector.subscribe(process_market_data)
        
        # Start data collection
        await self.data_collector.collect_data(symbols)
    
    def stop_monitoring(self):
        """Stop market data monitoring"""
        self.data_collector.stop()
    
    def get_risk_metrics(self, portfolio_value: float, positions: List[Dict]) -> RiskMetrics:
        """Calculate current risk metrics"""
        try:
            total_exposure = sum(pos.get('value', 0) for pos in positions)
            
            # Calculate other metrics from trade history
            trade_history = list(self.risk_manager.trade_history)
            
            if trade_history:
                returns = [trade.get('pnl', 0) for trade in trade_history]
                win_rate = len([r for r in returns if r > 0]) / len(returns)
                avg_return = statistics.mean(returns)
                
                # Calculate max drawdown
                if len(returns) > 1:
                    cumulative = np.cumsum(returns)
                    peak = np.maximum.accumulate(cumulative)
                    drawdown = (cumulative - peak) / peak
                    max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
                    
                    # Calculate Sharpe ratio
                    sharpe = avg_return / statistics.stdev(returns) if len(returns) > 1 and statistics.stdev(returns) > 0 else 0
                else:
                    max_drawdown = 0
                    sharpe = 0
            else:
                win_rate = 0
                avg_return = 0
                max_drawdown = 0
                sharpe = 0
            
            return RiskMetrics(
                portfolio_value=portfolio_value,
                total_exposure=total_exposure,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe,
                win_rate=win_rate,
                avg_trade_return=avg_return
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(portfolio_value=portfolio_value)