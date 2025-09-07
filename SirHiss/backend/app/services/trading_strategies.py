"""
Advanced Trading Strategies for SirHiss Trading Platform
Implements multiple algorithmic trading strategies with technical analysis
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
class TradingSignal:
    symbol: str
    strategy_name: str
    signal: SignalType
    strength: float  # 0.0 to 1.0
    price: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseTradingStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, allocation: float = 0.1):
        self.name = name
        self.allocation = allocation
        self.is_active = True
        self.position_size = 0.0
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.trade_history = []
        
    @abstractmethod
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate trading signal based on market data"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        """Calculate position size for the signal"""
        pass
    
    def update_position(self, order: Order, is_entry: bool = True):
        """Update position tracking"""
        if is_entry:
            self.position_size = order.quantity if order.side == OrderSide.BUY else -order.quantity
            self.entry_price = order.price or 0.0
        else:
            self.position_size = 0.0
            self.entry_price = 0.0
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Calculate strategy performance metrics"""
        if not self.trade_history:
            return {}
        
        returns = [trade.get('pnl', 0) for trade in self.trade_history]
        winning_trades = [r for r in returns if r > 0]
        
        return {
            'total_trades': len(returns),
            'winning_trades': len(winning_trades),
            'win_rate': len(winning_trades) / len(returns) if returns else 0,
            'total_return': sum(returns),
            'avg_return': statistics.mean(returns) if returns else 0,
            'sharpe_ratio': statistics.mean(returns) / statistics.stdev(returns) if len(returns) > 1 and statistics.stdev(returns) > 0 else 0
        }

class TechnicalAnalyzer:
    """Technical analysis helper class"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """Simple Moving Average"""
        if len(prices) < period:
            return 0.0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[float, float, float]:
        """Bollinger Bands (upper, middle, lower)"""
        if len(prices) < period:
            price = prices[-1] if prices else 0.0
            return price, price, price
        
        sma = sum(prices[-period:]) / period
        variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
        std = variance ** 0.5
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """MACD (macd, signal, histogram)"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        ema_fast = TechnicalAnalyzer.calculate_ema(prices, fast)
        ema_slow = TechnicalAnalyzer.calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        
        # For signal line, we'd need historical MACD values
        # Simplified: use EMA of recent prices as proxy
        signal_line = TechnicalAnalyzer.calculate_ema(prices[-signal:], signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram

class TechnicalIndicatorStrategy(BaseTradingStrategy):
    """Strategy based on technical indicators (RSI, MACD, Bollinger Bands)"""
    
    def __init__(self, allocation: float = 0.1, rsi_period: int = 14, rsi_overbought: float = 70, rsi_oversold: float = 30):
        super().__init__("TechnicalIndicatorStrategy", allocation)
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate signal based on technical indicators"""
        if len(candles) < 50:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"}
            )
        
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        
        # Calculate indicators
        rsi = TechnicalAnalyzer.calculate_rsi(closes, self.rsi_period)
        macd, macd_signal, macd_hist = TechnicalAnalyzer.calculate_macd(closes)
        bb_upper, bb_middle, bb_lower = TechnicalAnalyzer.calculate_bollinger_bands(closes)
        
        current_price = ticker.price
        
        # Signal generation logic
        signals = []
        signal_strength = 0.0
        
        # RSI signals
        if rsi < self.rsi_oversold:
            signals.append(("buy", "rsi_oversold", 0.8))
            signal_strength += 0.3
        elif rsi > self.rsi_overbought:
            signals.append(("sell", "rsi_overbought", 0.8))
            signal_strength += 0.3
        
        # MACD signals
        if macd > macd_signal and macd_hist > 0:
            signals.append(("buy", "macd_bullish", 0.6))
            signal_strength += 0.2
        elif macd < macd_signal and macd_hist < 0:
            signals.append(("sell", "macd_bearish", 0.6))
            signal_strength += 0.2
        
        # Bollinger Bands signals
        if current_price < bb_lower:
            signals.append(("buy", "bb_oversold", 0.7))
            signal_strength += 0.25
        elif current_price > bb_upper:
            signals.append(("sell", "bb_overbought", 0.7))
            signal_strength += 0.25
        
        # Determine final signal
        buy_signals = [s for s in signals if s[0] == "buy"]
        sell_signals = [s for s in signals if s[0] == "sell"]
        
        if len(buy_signals) > len(sell_signals) and signal_strength > 0.5:
            signal_type = SignalType.BUY
        elif len(sell_signals) > len(buy_signals) and signal_strength > 0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
            signal_strength = 0.0
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=signal_type,
            strength=min(signal_strength, 1.0),
            price=current_price,
            timestamp=time.time(),
            metadata={
                "rsi": rsi,
                "macd": macd,
                "bb_position": (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper > bb_lower else 0.5,
                "signals": signals
            }
        )
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        """Calculate position size based on signal strength and allocation"""
        base_size = portfolio_value * self.allocation
        adjusted_size = base_size * signal.strength
        return adjusted_size / signal.price

class TrendFollowingStrategy(BaseTradingStrategy):
    """Moving average crossover trend following strategy"""
    
    def __init__(self, allocation: float = 0.1, fast_period: int = 10, slow_period: int = 30):
        super().__init__("TrendFollowingStrategy", allocation)
        self.fast_period = fast_period
        self.slow_period = slow_period
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate trend following signal"""
        if len(candles) < self.slow_period:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"}
            )
        
        closes = [c.close for c in candles]
        
        fast_ma = TechnicalAnalyzer.calculate_sma(closes, self.fast_period)
        slow_ma = TechnicalAnalyzer.calculate_sma(closes, self.slow_period)
        
        # Previous MAs for crossover detection
        if len(closes) > self.slow_period:
            prev_fast_ma = TechnicalAnalyzer.calculate_sma(closes[:-1], self.fast_period)
            prev_slow_ma = TechnicalAnalyzer.calculate_sma(closes[:-1], self.slow_period)
        else:
            prev_fast_ma = fast_ma
            prev_slow_ma = slow_ma
        
        # Detect crossovers
        bullish_cross = fast_ma > slow_ma and prev_fast_ma <= prev_slow_ma
        bearish_cross = fast_ma < slow_ma and prev_fast_ma >= prev_slow_ma
        
        # Signal strength based on MA spread
        ma_spread = abs(fast_ma - slow_ma) / slow_ma if slow_ma > 0 else 0
        strength = min(ma_spread * 10, 1.0)  # Scale to 0-1
        
        if bullish_cross:
            signal_type = SignalType.BUY
        elif bearish_cross:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
            strength = 0.0
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=signal_type,
            strength=strength,
            price=ticker.price,
            timestamp=time.time(),
            metadata={
                "fast_ma": fast_ma,
                "slow_ma": slow_ma,
                "ma_spread": ma_spread,
                "bullish_cross": bullish_cross,
                "bearish_cross": bearish_cross
            }
        )
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        """Calculate position size"""
        base_size = portfolio_value * self.allocation
        adjusted_size = base_size * signal.strength
        return adjusted_size / signal.price

class DCAStrategy(BaseTradingStrategy):
    """Dollar Cost Averaging strategy"""
    
    def __init__(self, allocation: float = 0.1, interval_hours: int = 24, volatility_threshold: float = 0.05):
        super().__init__("DCAStrategy", allocation)
        self.interval_hours = interval_hours
        self.volatility_threshold = volatility_threshold
        self.last_purchase = 0
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate DCA signal based on time and volatility"""
        current_time = time.time()
        
        # Check if enough time has passed since last purchase
        if current_time - self.last_purchase < (self.interval_hours * 3600):
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=current_time,
                metadata={"reason": "interval_not_reached"}
            )
        
        # Calculate recent volatility
        if len(candles) >= 24:
            recent_prices = [c.close for c in candles[-24:]]
            returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                      for i in range(1, len(recent_prices))]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        else:
            volatility = 0
        
        # DCA signal with volatility adjustment
        base_strength = 0.6  # Conservative DCA approach
        
        # Increase strength during high volatility (buy the dip)
        if volatility > self.volatility_threshold:
            strength = min(base_strength + (volatility * 2), 1.0)
        else:
            strength = base_strength
        
        self.last_purchase = current_time
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.BUY,  # DCA always buys
            strength=strength,
            price=ticker.price,
            timestamp=current_time,
            metadata={
                "volatility": volatility,
                "volatility_adjustment": volatility > self.volatility_threshold
            }
        )
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        """Calculate fixed DCA position size"""
        dca_amount = portfolio_value * self.allocation / 30  # Monthly allocation spread over 30 days
        return dca_amount / signal.price

class GridTradingStrategy(BaseTradingStrategy):
    """Grid trading strategy for range-bound markets"""
    
    def __init__(self, allocation: float = 0.1, grid_levels: int = 10, grid_range: float = 0.10):
        super().__init__("GridTradingStrategy", allocation)
        self.grid_levels = grid_levels
        self.grid_range = grid_range
        self.base_price = 0.0
        self.grid_positions = {}
        
    def generate_signal(self, candles: List[Candle], ticker: Ticker) -> TradingSignal:
        """Generate grid trading signals"""
        if len(candles) < 50:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=time.time(),
                metadata={"reason": "insufficient_data"}
            )
        
        # Set base price if not set (using recent average)
        if self.base_price == 0.0:
            recent_prices = [c.close for c in candles[-20:]]
            self.base_price = sum(recent_prices) / len(recent_prices)
        
        current_price = ticker.price
        
        # Calculate grid levels
        grid_step = (self.base_price * self.grid_range) / self.grid_levels
        
        # Determine which grid level we're at
        price_diff = current_price - self.base_price
        grid_level = int(price_diff / grid_step)
        
        # Grid trading logic
        if grid_level < -2:  # Price significantly below base
            signal_type = SignalType.BUY
            strength = min(abs(grid_level) / 5, 1.0)
        elif grid_level > 2:  # Price significantly above base
            signal_type = SignalType.SELL
            strength = min(grid_level / 5, 1.0)
        else:
            signal_type = SignalType.HOLD
            strength = 0.0
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=signal_type,
            strength=strength,
            price=current_price,
            timestamp=time.time(),
            metadata={
                "base_price": self.base_price,
                "grid_level": grid_level,
                "grid_step": grid_step
            }
        )
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float) -> float:
        """Calculate grid position size"""
        grid_allocation = portfolio_value * self.allocation / self.grid_levels
        return grid_allocation / signal.price

class StrategyManager:
    """Manages multiple trading strategies"""
    
    def __init__(self):
        self.strategies: List[BaseTradingStrategy] = []
        self.active_signals: List[TradingSignal] = []
        
    def add_strategy(self, strategy: BaseTradingStrategy):
        """Add strategy to manager"""
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
            if strategy.is_active:
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
            avg_strength = buy_weight / len(buy_signals)
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
                    "sell_weight": sell_weight
                }
            )
        elif sell_weight > buy_weight and sell_weight > 0.5:
            # Create combined sell signal
            avg_strength = sell_weight / len(sell_signals)
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
                    "sell_weight": sell_weight
                }
            )
        
        return None
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all strategies"""
        performance = {}
        for strategy in self.strategies:
            performance[strategy.name] = strategy.get_performance_metrics()
        return performance

# Default strategy configurations
def get_default_strategies() -> List[BaseTradingStrategy]:
    """Get default strategy configuration"""
    return [
        TechnicalIndicatorStrategy(allocation=0.4),
        TrendFollowingStrategy(allocation=0.3),
        DCAStrategy(allocation=0.2),
        GridTradingStrategy(allocation=0.1)
    ]