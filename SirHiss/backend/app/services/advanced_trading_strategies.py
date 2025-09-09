"""
Advanced Trading Strategies for SirHiss Trading Platform
Implements sophisticated algorithmic trading strategies with technical analysis
Integrated with advanced algorithms from the research repository
"""

import asyncio
import time
import logging
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import deque
import random
import requests

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logging.warning("TA-Lib not available, using fallback technical indicators")

from .exchange_api import BaseExchange, Ticker, Candle, Order, OrderSide, OrderType

# Configure logging
logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

@dataclass
class StrategyConfig:
    """Configuration for trading strategies"""
    symbol: str
    position_size: float = 0.1
    max_position_size: float = 0.25
    stop_loss: float = 0.15
    take_profit: float = 0.25
    risk_per_trade: float = 0.02
    enabled: bool = True
    # Strategy-specific parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradingSignal:
    symbol: str
    strategy_name: str
    signal: SignalType
    strength: float  # 0.0 to 1.0
    price: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    config: Optional[StrategyConfig] = None

class PerformanceTracker:
    """Track strategy performance metrics"""
    
    def __init__(self):
        self.trades = []
        self.total_return = 0.0
        self.win_rate = 0.0
        self.sharpe_ratio = 0.0
        self.max_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        
    def add_trade(self, entry_price: float, exit_price: float, quantity: float, side: OrderSide):
        """Add completed trade to performance tracking"""
        if side == OrderSide.BUY:
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity
            
        self.trades.append({
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': pnl,
            'timestamp': time.time()
        })
        
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
            
        self._update_metrics()
    
    def _update_metrics(self):
        """Update performance metrics"""
        if not self.trades:
            return
            
        # Calculate total return
        self.total_return = sum(trade['pnl'] for trade in self.trades)
        
        # Calculate win rate
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        returns = [trade['pnl'] for trade in self.trades]
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            self.sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
        
        # Calculate max drawdown
        cumulative_returns = np.cumsum(returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        self.max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

class TechnicalAnalyzer:
    """Advanced technical analysis with TA-Lib integration"""
    
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
            if TALIB_AVAILABLE:
                # Moving Averages
                indicators['sma_20'] = talib.SMA(closes, timeperiod=20)[-1]
                indicators['ema_20'] = talib.EMA(closes, timeperiod=20)[-1]
                indicators['sma_50'] = talib.SMA(closes, timeperiod=50)[-1]
                indicators['sma_200'] = talib.SMA(closes, timeperiod=200)[-1] if len(closes) >= 200 else 0
                
                # RSI
                rsi = talib.RSI(closes, timeperiod=14)
                indicators['rsi'] = rsi[-1]
                indicators['rsi_oversold'] = rsi[-1] < 30
                indicators['rsi_overbought'] = rsi[-1] > 70
                
                # MACD
                macd, macd_signal, macd_hist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
                indicators['macd'] = macd[-1]
                indicators['macd_signal'] = macd_signal[-1]
                indicators['macd_histogram'] = macd_hist[-1]
                indicators['macd_bullish'] = macd[-1] > macd_signal[-1]
                
                # Bollinger Bands
                bb_upper, bb_middle, bb_lower = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2)
                indicators['bb_upper'] = bb_upper[-1]
                indicators['bb_middle'] = bb_middle[-1]
                indicators['bb_lower'] = bb_lower[-1]
                indicators['bb_width'] = (bb_upper[-1] - bb_lower[-1]) / bb_middle[-1]
                indicators['bb_position'] = (closes[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
                
                # Stochastic
                stoch_k, stoch_d = talib.STOCH(highs, lows, closes, fastk_period=14, slowk_period=3, slowd_period=3)
                indicators['stoch_k'] = stoch_k[-1]
                indicators['stoch_d'] = stoch_d[-1]
                indicators['stoch_oversold'] = stoch_k[-1] < 20
                indicators['stoch_overbought'] = stoch_k[-1] > 80
                
                # ATR (Average True Range)
                atr = talib.ATR(highs, lows, closes, timeperiod=14)
                indicators['atr'] = atr[-1]
                indicators['atr_percent'] = atr[-1] / closes[-1]
                
                # Volume indicators
                indicators['volume_sma'] = talib.SMA(volumes, timeperiod=20)[-1]
                indicators['volume_ratio'] = volumes[-1] / indicators['volume_sma']
                
                # OBV (On Balance Volume)
                obv = talib.OBV(closes, volumes)
                indicators['obv'] = obv[-1]
                indicators['obv_trend'] = 1 if obv[-1] > obv[-10] else -1
                
                # ADX (Average Directional Index)
                adx = talib.ADX(highs, lows, closes, timeperiod=14)
                indicators['adx'] = adx[-1]
                indicators['trend_strength'] = 'strong' if adx[-1] > 25 else 'weak'
                
                # CCI (Commodity Channel Index)
                cci = talib.CCI(highs, lows, closes, timeperiod=14)
                indicators['cci'] = cci[-1]
                
                # Williams %R
                willr = talib.WILLR(highs, lows, closes, timeperiod=14)
                indicators['williams_r'] = willr[-1]
            else:
                # Fallback implementations
                indicators = TechnicalAnalyzer._calculate_fallback_indicators(closes, highs, lows, volumes)
            
            # Price action indicators
            indicators['price_change_1h'] = (closes[-1] - closes[-2]) / closes[-2] if len(closes) > 1 else 0
            indicators['price_change_24h'] = (closes[-1] - closes[-24]) / closes[-24] if len(closes) > 24 else 0
            
            # Support and resistance levels
            indicators['resistance'] = np.max(highs[-20:])
            indicators['support'] = np.min(lows[-20:])
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
        
        return indicators
    
    @staticmethod
    def _calculate_fallback_indicators(closes: np.array, highs: np.array, lows: np.array, volumes: np.array) -> Dict[str, float]:
        """Fallback technical indicators when TA-Lib is not available"""
        indicators = {}
        
        # Simple Moving Average
        if len(closes) >= 20:
            indicators['sma_20'] = np.mean(closes[-20:])
        if len(closes) >= 50:
            indicators['sma_50'] = np.mean(closes[-50:])
        
        # RSI (simplified)
        if len(closes) >= 15:
            deltas = np.diff(closes[-15:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                indicators['rsi'] = 100 - (100 / (1 + rs))
            else:
                indicators['rsi'] = 100
        
        return indicators

class SentimentAnalyzer:
    """Analyze market sentiment from various sources"""
    
    def __init__(self):
        self.sentiment_cache = {}
        self.cache_duration = 900  # 15 minutes
        
    def get_fear_greed_index(self) -> float:
        """Get Fear & Greed Index (0-1 scale)"""
        try:
            # Fear & Greed Index API
            response = requests.get("https://api.alternative.me/fng/", timeout=10)
            data = response.json()
            
            if data and 'data' in data and len(data['data']) > 0:
                value = int(data['data'][0]['value'])
                return value / 100.0  # Convert to 0-1 scale
                
        except Exception as e:
            logger.warning(f"Could not fetch Fear & Greed Index: {e}")
        
        return 0.5  # Neutral if unable to fetch
    
    def get_social_sentiment(self, symbol: str) -> float:
        """Get social media sentiment for symbol"""
        try:
            # Mock implementation for demo - in production would integrate with sentiment APIs
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
            composite = (fear_greed * 0.4 + social * 0.6)
            return max(0.0, min(1.0, composite))  # Clamp to 0-1
            
        except Exception as e:
            logger.error(f"Error calculating composite sentiment: {e}")
            return 0.5

class BaseTradingStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, exchange: BaseExchange, config: StrategyConfig):
        self.name = name
        self.exchange = exchange
        self.config = config
        self.allocation = config.position_size
        self.is_active = config.enabled
        self.current_position = 0.0
        self.last_signal_time = 0
        self.historical_data = deque(maxlen=1000)
        self.min_signal_interval = 60  # Minimum seconds between signals
        self.performance = PerformanceTracker()
        
    @abstractmethod
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate trading signal based on market data"""
        pass
    
    def should_trade(self, signal: TradingSignal) -> bool:
        """Determine if we should execute the trade based on risk management"""
        # Check if enough time has passed since last signal
        if time.time() - self.last_signal_time < self.min_signal_interval:
            return False
        
        # Check position limits
        if signal.signal == SignalType.BUY and self.current_position >= self.config.max_position_size:
            return False
        
        if signal.signal == SignalType.SELL and self.current_position <= -self.config.max_position_size:
            return False
        
        # Check signal strength threshold
        if signal.strength < 0.6:  # Require at least 60% confidence
            return False
        
        return True
    
    def update_position(self, order: Order, is_entry: bool = True):
        """Update position tracking"""
        if is_entry:
            self.current_position = order.quantity if order.side == OrderSide.BUY else -order.quantity
        else:
            self.current_position = 0.0
        
        self.last_signal_time = time.time()
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate strategy performance metrics"""
        return {
            'total_trades': self.performance.total_trades,
            'winning_trades': self.performance.winning_trades,
            'win_rate': self.performance.win_rate,
            'total_return': self.performance.total_return,
            'sharpe_ratio': self.performance.sharpe_ratio,
            'max_drawdown': self.performance.max_drawdown
        }

    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        """Calculate position size for the signal"""
        base_size = portfolio_value * self.allocation
        adjusted_size = base_size * signal.strength
        return adjusted_size / signal.price

# Advanced Strategy Implementations

class AdvancedTechnicalIndicatorStrategy(BaseTradingStrategy):
    """Advanced strategy using multiple technical indicators with TA-Lib"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("AdvancedTechnicalIndicatorStrategy", exchange, config)
        self.rsi_period = config.parameters.get('rsi_period', 14)
        self.rsi_oversold = config.parameters.get('rsi_oversold', 25)  # Crypto-specific
        self.rsi_overbought = config.parameters.get('rsi_overbought', 75)
        self.macd_fast = config.parameters.get('macd_fast', 8)
        self.macd_slow = config.parameters.get('macd_slow', 21)
        self.macd_signal = config.parameters.get('macd_signal', 5)
        self.bb_period = config.parameters.get('bb_period', 10)
        self.bb_std = config.parameters.get('bb_std', 2.0)
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate signal based on advanced technical indicators"""
        if len(candles) < 50:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"},
                config=self.config
            )
        
        # Calculate all indicators
        indicators = TechnicalAnalyzer.calculate_all_indicators(candles)
        
        current_price = ticker.price
        
        # Generate signals based on multiple indicators
        signals = []
        
        # RSI signals
        rsi = indicators.get('rsi', 50)
        if rsi < self.rsi_oversold:
            signals.append(('BUY', 0.7))
        elif rsi > self.rsi_overbought:
            signals.append(('SELL', 0.7))
        
        # MACD signals
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        if macd > macd_signal and indicators.get('macd_bullish', False):
            signals.append(('BUY', 0.6))
        elif macd < macd_signal and not indicators.get('macd_bullish', True):
            signals.append(('SELL', 0.6))
        
        # Bollinger Bands signals
        bb_upper = indicators.get('bb_upper', current_price)
        bb_lower = indicators.get('bb_lower', current_price)
        if current_price <= bb_lower:
            signals.append(('BUY', 0.8))
        elif current_price >= bb_upper:
            signals.append(('SELL', 0.8))
        
        # Stochastic signals
        stoch_k = indicators.get('stoch_k', 50)
        if stoch_k < 20:
            signals.append(('BUY', 0.5))
        elif stoch_k > 80:
            signals.append(('SELL', 0.5))
        
        # Combine signals
        buy_strength = sum(strength for signal, strength in signals if signal == 'BUY')
        sell_strength = sum(strength for signal, strength in signals if signal == 'SELL')
        
        if buy_strength > sell_strength and buy_strength >= 1.0:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.BUY,
                strength=min(buy_strength / 2.0, 1.0),
                price=current_price,
                timestamp=time.time(),
                metadata=indicators,
                config=self.config
            )
        elif sell_strength > buy_strength and sell_strength >= 1.0:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.SELL,
                strength=min(sell_strength / 2.0, 1.0),
                price=current_price,
                timestamp=time.time(),
                metadata=indicators,
                config=self.config
            )
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=time.time(),
            metadata=indicators,
            config=self.config
        )

class ScalpingStrategy(BaseTradingStrategy):
    """High-frequency scalping strategy based on order book imbalance and micro-movements"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("ScalpingStrategy", exchange, config)
        self.min_signal_interval = config.parameters.get('min_interval', 5)  # 5 seconds
        self.spread_threshold = config.parameters.get('spread_threshold', 0.002)  # 0.2%
        self.volume_threshold = config.parameters.get('volume_threshold', 1000)
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate scalping signals based on micro-movements"""
        if len(candles) < 10:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"},
                config=self.config
            )
        
        # Calculate order book imbalance (simplified)
        bid_ask_spread = (ticker.ask - ticker.bid) / ticker.price
        
        if bid_ask_spread > self.spread_threshold:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "spread_too_wide", "spread": bid_ask_spread},
                config=self.config
            )
        
        # Calculate short-term momentum
        recent_closes = [c.close for c in candles[-10:]]
        price_change = (recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        
        # Volume analysis
        avg_volume = np.mean([c.volume for c in candles[-20:]])
        current_volume = candles[-1].volume if candles else 0
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Generate signal based on momentum and volume
        signal_strength = 0.0
        signal_type = SignalType.HOLD
        
        if price_change > 0.001 and volume_ratio > 1.5:  # 0.1% move with high volume
            signal_type = SignalType.BUY
            signal_strength = min(abs(price_change) * 100 + volume_ratio * 0.2, 1.0)
        elif price_change < -0.001 and volume_ratio > 1.5:
            signal_type = SignalType.SELL
            signal_strength = min(abs(price_change) * 100 + volume_ratio * 0.2, 1.0)
        
        if signal_type != SignalType.HOLD and signal_strength > 0.7:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=signal_type,
                strength=signal_strength,
                price=ticker.price,
                timestamp=time.time(),
                metadata={
                    'spread': bid_ask_spread, 
                    'volume_ratio': volume_ratio,
                    'price_change': price_change
                },
                config=self.config
            )
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=ticker.price,
            timestamp=time.time(),
            metadata={'spread': bid_ask_spread, 'volume_ratio': volume_ratio},
            config=self.config
        )

class DynamicDCAStrategy(BaseTradingStrategy):
    """Dynamic Dollar Cost Averaging Strategy with volatility adjustments"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("DynamicDCAStrategy", exchange, config)
        self.dca_interval = config.parameters.get('dca_interval', 3600 * 24)  # Daily
        self.last_dca_time = 0
        self.volatility_adjustment = config.parameters.get('volatility_adjustment', True)
        self.base_amount = config.parameters.get('base_amount', 100)
        
    def calculate_volatility_adjustment(self, candles: List[Candle]) -> float:
        """Calculate volatility adjustment factor"""
        if len(candles) < 20:
            return 1.0
        
        # Calculate 20-period volatility
        closes = np.array([c.close for c in candles[-20:]])
        returns = np.diff(np.log(closes))
        volatility = np.std(returns) * np.sqrt(365)  # Annualized volatility
        
        # Increase DCA amount during high volatility
        if volatility > 0.5:  # High volatility
            return 1.5
        elif volatility > 0.3:  # Medium volatility
            return 1.2
        else:
            return 1.0
    
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate DCA signal based on time and volatility"""
        current_time = time.time()
        
        # Check if it's time for DCA
        if current_time - self.last_dca_time < self.dca_interval:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=current_time,
                metadata={"reason": "interval_not_reached"},
                config=self.config
            )
        
        # Calculate adjusted DCA amount
        base_strength = 0.8
        vol_adjustment = 1.0
        
        if self.volatility_adjustment and len(candles) >= 20:
            vol_adjustment = self.calculate_volatility_adjustment(candles)
            strength = min(base_strength * vol_adjustment, 1.0)
        else:
            strength = base_strength
        
        self.last_dca_time = current_time
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.BUY,  # DCA is always buying
            strength=strength,
            price=ticker.price,
            timestamp=current_time,
            metadata={
                'dca_amount': self.base_amount,
                'volatility_adjusted': self.volatility_adjustment,
                'vol_adjustment': vol_adjustment
            },
            config=self.config
        )

class SentimentStrategy(BaseTradingStrategy):
    """Strategy based on sentiment analysis from news and social media"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("SentimentStrategy", exchange, config)
        self.sentiment_threshold = config.parameters.get('sentiment_threshold', 0.6)
        self.sentiment_analyzer = SentimentAnalyzer()
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate signal based on sentiment analysis"""
        if len(candles) < 10:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"},
                config=self.config
            )
        
        # Get sentiment score
        sentiment = self.sentiment_analyzer.calculate_composite_sentiment(ticker.symbol)
        
        # Calculate price momentum for confirmation
        recent_closes = [c.close for c in candles[-5:]]
        price_momentum = (recent_closes[-1] - recent_closes[0]) / recent_closes[0]
        
        # Generate signals based on sentiment and momentum alignment
        if sentiment > 0.7 and price_momentum > 0.01:  # Strong positive sentiment + upward momentum
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.BUY,
                strength=min(sentiment + abs(price_momentum) * 10, 1.0),
                price=ticker.price,
                timestamp=time.time(),
                metadata={'sentiment': sentiment, 'momentum': price_momentum},
                config=self.config
            )
        
        elif sentiment < 0.3 and price_momentum < -0.01:  # Strong negative sentiment + downward momentum
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.SELL,
                strength=min((1 - sentiment) + abs(price_momentum) * 10, 1.0),
                price=ticker.price,
                timestamp=time.time(),
                metadata={'sentiment': sentiment, 'momentum': price_momentum},
                config=self.config
            )
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=ticker.price,
            timestamp=time.time(),
            metadata={'sentiment': sentiment, 'momentum': price_momentum},
            config=self.config
        )

class GridTradingStrategy(BaseTradingStrategy):
    """Grid trading strategy for range-bound markets"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("GridTradingStrategy", exchange, config)
        self.grid_levels = config.parameters.get('grid_levels', 10)
        self.grid_spacing = config.parameters.get('grid_spacing', 0.02)  # 2% spacing
        self.price_range = None
        self.buy_levels = []
        self.sell_levels = []
        
    def setup_grid(self, current_price: float):
        """Setup grid levels around current price"""
        self.price_range = {
            'center': current_price,
            'top': current_price * (1 + self.grid_spacing * self.grid_levels / 2),
            'bottom': current_price * (1 - self.grid_spacing * self.grid_levels / 2)
        }
        
        # Calculate grid levels
        self.buy_levels = []
        self.sell_levels = []
        
        for i in range(self.grid_levels // 2):
            buy_price = current_price * (1 - self.grid_spacing * (i + 1))
            sell_price = current_price * (1 + self.grid_spacing * (i + 1))
            
            self.buy_levels.append(buy_price)
            self.sell_levels.append(sell_price)
    
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate grid trading signals"""
        current_price = ticker.price
        
        # Initialize grid if not set
        if not self.price_range:
            self.setup_grid(current_price)
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=current_price,
                timestamp=time.time(),
                metadata={"reason": "grid_initialized"},
                config=self.config
            )
        
        # Check if price hit any grid levels
        for buy_level in self.buy_levels:
            if abs(current_price - buy_level) / buy_level < 0.001:  # Within 0.1% of level
                return TradingSignal(
                    symbol=ticker.symbol,
                    strategy_name=self.name,
                    signal=SignalType.BUY,
                    strength=0.8,
                    price=current_price,
                    timestamp=time.time(),
                    metadata={'grid_level': buy_level, 'grid_type': 'buy'},
                    config=self.config
                )
        
        for sell_level in self.sell_levels:
            if abs(current_price - sell_level) / sell_level < 0.001:
                return TradingSignal(
                    symbol=ticker.symbol,
                    strategy_name=self.name,
                    signal=SignalType.SELL,
                    strength=0.8,
                    price=current_price,
                    timestamp=time.time(),
                    metadata={'grid_level': sell_level, 'grid_type': 'sell'},
                    config=self.config
                )
        
        # Reset grid if price moves outside range
        if (current_price > self.price_range['top'] or 
            current_price < self.price_range['bottom']):
            self.setup_grid(current_price)
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=time.time(),
            metadata={"reason": "no_grid_trigger"},
            config=self.config
        )

class TrendFollowingStrategy(BaseTradingStrategy):
    """Advanced trend following strategy using dual moving averages and ATR"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("TrendFollowingStrategy", exchange, config)
        self.fast_ma_period = config.parameters.get('fast_ma_period', 50)
        self.slow_ma_period = config.parameters.get('slow_ma_period', 200)
        self.atr_period = config.parameters.get('atr_period', 20)
        self.atr_multiplier = config.parameters.get('atr_multiplier', 2.5)
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate trend following signals"""
        if len(candles) < self.slow_ma_period:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"},
                config=self.config
            )
        
        # Calculate indicators
        indicators = TechnicalAnalyzer.calculate_all_indicators(candles)
        
        current_price = ticker.price
        fast_ma = indicators.get('sma_50', current_price)  # Use SMA 50 as fast
        slow_ma = indicators.get('sma_200', current_price)  # Use SMA 200 as slow
        atr = indicators.get('atr', current_price * 0.02)
        
        # Trend direction and strength
        trend_strength = abs(fast_ma - slow_ma) / slow_ma if slow_ma > 0 else 0
        
        # Generate signals
        if (fast_ma > slow_ma and trend_strength > 0.02):  # Golden cross with trend strength
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.BUY,
                strength=min(trend_strength * 10, 1.0),
                price=current_price,
                timestamp=time.time(),
                metadata={
                    'fast_ma': fast_ma,
                    'slow_ma': slow_ma,
                    'atr': atr,
                    'stop_loss': current_price - (atr * self.atr_multiplier),
                    'trend_strength': trend_strength
                },
                config=self.config
            )
        
        elif (fast_ma < slow_ma and trend_strength > 0.02):  # Death cross
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.SELL,
                strength=min(trend_strength * 10, 1.0),
                price=current_price,
                timestamp=time.time(),
                metadata={
                    'fast_ma': fast_ma,
                    'slow_ma': slow_ma,
                    'atr': atr,
                    'stop_loss': current_price + (atr * self.atr_multiplier),
                    'trend_strength': trend_strength
                },
                config=self.config
            )
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=current_price,
            timestamp=time.time(),
            metadata={
                'fast_ma': fast_ma,
                'slow_ma': slow_ma,
                'trend_strength': trend_strength
            },
            config=self.config
        )

class ArbitrageStrategy(BaseTradingStrategy):
    """Statistical arbitrage strategy for mean reversion"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("ArbitrageStrategy", exchange, config)
        self.lookback_period = config.parameters.get('lookback_period', 50)
        self.z_score_threshold = config.parameters.get('z_score_threshold', 2.0)
        
    def calculate_z_score(self, prices: np.ndarray) -> float:
        """Calculate z-score for mean reversion"""
        if len(prices) < self.lookback_period:
            return 0.0
        
        recent_prices = prices[-self.lookback_period:]
        mean_price = np.mean(recent_prices)
        std_price = np.std(recent_prices)
        
        if std_price == 0:
            return 0.0
        
        current_price = prices[-1]
        return (current_price - mean_price) / std_price
    
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate mean reversion signals"""
        if len(candles) < self.lookback_period:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"},
                config=self.config
            )
        
        closes = np.array([c.close for c in candles])
        z_score = self.calculate_z_score(closes)
        
        # Generate mean reversion signals
        if z_score > self.z_score_threshold:  # Price too high, expect reversion
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.SELL,
                strength=min(abs(z_score) / 3.0, 1.0),
                price=closes[-1],
                timestamp=time.time(),
                metadata={'z_score': z_score, 'threshold': self.z_score_threshold},
                config=self.config
            )
        
        elif z_score < -self.z_score_threshold:  # Price too low, expect reversion
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.BUY,
                strength=min(abs(z_score) / 3.0, 1.0),
                price=closes[-1],
                timestamp=time.time(),
                metadata={'z_score': z_score, 'threshold': self.z_score_threshold},
                config=self.config
            )
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=ticker.price,
            timestamp=time.time(),
            metadata={'z_score': z_score},
            config=self.config
        )

class AdvancedStrategyManager:
    """Manages multiple advanced trading strategies"""
    
    def __init__(self, exchange: BaseExchange):
        self.exchange = exchange
        self.strategies: List[BaseTradingStrategy] = []
        self.active_signals: List[TradingSignal] = []
        
    def add_strategy(self, strategy_class, config: StrategyConfig):
        """Add strategy to manager"""
        strategy = strategy_class(self.exchange, config)
        self.strategies.append(strategy)
        logger.info(f"Added strategy: {strategy.name}")
    
    def remove_strategy(self, strategy_name: str):
        """Remove strategy by name"""
        self.strategies = [s for s in self.strategies if s.name != strategy_name]
        logger.info(f"Removed strategy: {strategy_name}")
    
    async def generate_signals(self, symbol: str, candles: List[Candle], ticker: Ticker) -> List[TradingSignal]:
        """Generate signals from all active strategies"""
        signals = []
        
        for strategy in self.strategies:
            if strategy.is_active and strategy.config.symbol == symbol:
                try:
                    signal = strategy.generate_signal(candles, ticker)
                    if signal.signal != SignalType.HOLD:
                        signals.append(signal)
                except Exception as e:
                    logger.error(f"Error generating signal for {strategy.name}: {e}")
        
        self.active_signals = signals
        return signals
    
    def get_combined_signal(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """Combine multiple signals into one consensus signal"""
        if not signals:
            return None
        
        buy_signals = [s for s in signals if s.signal == SignalType.BUY]
        sell_signals = [s for s in signals if s.signal == SignalType.SELL]
        
        # Weighted voting based on signal strength
        buy_weight = sum(s.strength for s in buy_signals)
        sell_weight = sum(s.strength for s in sell_signals)
        
        if buy_weight > sell_weight and buy_weight > 0.5:
            # Create combined buy signal
            avg_strength = buy_weight / len(buy_signals) if buy_signals else 0
            return TradingSignal(
                symbol=signals[0].symbol,
                strategy_name="CombinedStrategy",
                signal=SignalType.BUY,
                strength=min(avg_strength, 1.0),
                price=signals[0].price,
                timestamp=time.time(),
                metadata={
                    "buy_signals": len(buy_signals),
                    "sell_signals": len(sell_signals),
                    "buy_weight": buy_weight,
                    "sell_weight": sell_weight,
                    "contributing_strategies": [s.strategy_name for s in buy_signals]
                }
            )
        elif sell_weight > buy_weight and sell_weight > 0.5:
            # Create combined sell signal
            avg_strength = sell_weight / len(sell_signals) if sell_signals else 0
            return TradingSignal(
                symbol=signals[0].symbol,
                strategy_name="CombinedStrategy",
                signal=SignalType.SELL,
                strength=min(avg_strength, 1.0),
                price=signals[0].price,
                timestamp=time.time(),
                metadata={
                    "buy_signals": len(buy_signals),
                    "sell_signals": len(sell_signals),
                    "buy_weight": buy_weight,
                    "sell_weight": sell_weight,
                    "contributing_strategies": [s.strategy_name for s in sell_signals]
                }
            )
        
        return None
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all strategies"""
        performance = {}
        for strategy in self.strategies:
            performance[strategy.name] = strategy.get_performance_metrics()
        return performance
    
    def update_strategy_config(self, strategy_name: str, new_params: Dict[str, Any]):
        """Update strategy parameters in real-time"""
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                strategy.config.parameters.update(new_params)
                logger.info(f"Updated parameters for {strategy_name}: {new_params}")
                break

# Strategy factory for easy creation
def create_advanced_strategy(strategy_type: str, exchange: BaseExchange, config: StrategyConfig) -> BaseTradingStrategy:
    """Factory function to create advanced strategies"""
    strategies = {
        'AdvancedTechnicalIndicator': AdvancedTechnicalIndicatorStrategy,
        'Scalping': ScalpingStrategy,
        'DynamicDCA': DynamicDCAStrategy,
        'Sentiment': SentimentStrategy,
        'GridTrading': GridTradingStrategy,
        'TrendFollowing': TrendFollowingStrategy,
        'Arbitrage': ArbitrageStrategy,
    }
    
    if strategy_type not in strategies:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    return strategies[strategy_type](exchange, config)

# Default advanced strategy configurations
def get_advanced_strategies(exchange: BaseExchange, symbol: str) -> List[BaseTradingStrategy]:
    """Get default advanced strategy configuration"""
    strategies = []
    
    # Advanced Technical Indicator Strategy
    tech_config = StrategyConfig(
        symbol=symbol,
        position_size=0.3,
        parameters={
            'rsi_period': 14,
            'rsi_oversold': 25,
            'rsi_overbought': 75,
            'macd_fast': 8,
            'macd_slow': 21,
            'macd_signal': 5
        }
    )
    strategies.append(AdvancedTechnicalIndicatorStrategy(exchange, tech_config))
    
    # Trend Following Strategy
    trend_config = StrategyConfig(
        symbol=symbol,
        position_size=0.25,
        parameters={
            'fast_ma_period': 50,
            'slow_ma_period': 200,
            'atr_period': 20
        }
    )
    strategies.append(TrendFollowingStrategy(exchange, trend_config))
    
    # Dynamic DCA Strategy
    dca_config = StrategyConfig(
        symbol=symbol,
        position_size=0.2,
        parameters={
            'dca_interval': 24 * 3600,  # Daily
            'base_amount': 100
        }
    )
    strategies.append(DynamicDCAStrategy(exchange, dca_config))
    
    # Grid Trading Strategy
    grid_config = StrategyConfig(
        symbol=symbol,
        position_size=0.15,
        parameters={
            'grid_levels': 10,
            'grid_spacing': 0.02
        }
    )
    strategies.append(GridTradingStrategy(exchange, grid_config))
    
    # Sentiment Strategy  
    sentiment_config = StrategyConfig(
        symbol=symbol,
        position_size=0.1,
        parameters={
            'sentiment_threshold': 0.6
        }
    )
    strategies.append(SentimentStrategy(exchange, sentiment_config))
    
    return strategies