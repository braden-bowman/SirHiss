"""
Enhanced Trading Engine for SirHiss Trading Platform
Integrates with advanced algorithm configuration system for sophisticated trading
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from datetime import datetime

from .exchange_api import BaseExchange, ExchangeFactory, Order, OrderSide, OrderType, OrderStatus
from .advanced_trading_strategies import (
    AdvancedStrategyManager, StrategyConfig, create_advanced_strategy,
    TradingSignal, SignalType, BaseTradingStrategy
)
from .data_monitor import MarketDataManager, MarketData, RiskManager

# Import enhanced algorithms
try:
    import numpy as np
    import pandas as pd
    from collections import deque, OrderedDict
    import tensorflow as tf
    from sklearn.ensemble import RandomForestClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("Enhanced ML libraries not available")
from ..models.trading_bot import TradingBot
from ..models.algorithm_config import AlgorithmConfig, AlgorithmExecution
from ..models.bot_execution import BotExecution
from ..models.holding import Holding
from ..core.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class TradingPosition:
    """Represents a trading position"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    entry_time: datetime = None
    strategy: str = ""
    algorithm_id: int = None

# Enhanced Algorithm Classes (moved from separate file)
class OrderBookAnalyticsStrategy(BaseTradingStrategy):
    """Advanced order book analytics using Level 5 analysis and VPIN"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("OrderBookAnalyticsStrategy", exchange, config)
        self.analysis_levels = config.parameters.get('analysis_levels', 5)
        self.vpin_threshold = config.parameters.get('vpin_threshold', 0.3)
        self.min_signal_interval = config.parameters.get('min_interval', 10)
        self.spread_threshold = config.parameters.get('spread_threshold', 0.002)
        
    def generate_signal(self, candles, ticker) -> TradingSignal:
        """Generate signals based on order book analytics"""
        current_time = time.time()
        
        # Mock order book imbalance calculation
        spread = (ticker.ask - ticker.bid) / ticker.price if hasattr(ticker, 'ask') and hasattr(ticker, 'bid') else 0.001
        
        if spread > self.spread_threshold:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=current_time,
                metadata={"reason": "spread_too_wide", "spread": spread},
                config=self.config
            )
        
        # Simplified order book imbalance signal
        if len(candles) >= 10:
            recent_volumes = [c.volume for c in candles[-10:]]
            volume_trend = (recent_volumes[-1] - recent_volumes[0]) / recent_volumes[0]
            
            if volume_trend > 0.2:  # 20% volume increase
                return TradingSignal(
                    symbol=ticker.symbol,
                    strategy_name=self.name,
                    signal=SignalType.BUY,
                    strength=min(volume_trend * 2, 1.0),
                    price=ticker.price,
                    timestamp=current_time,
                    metadata={"volume_trend": volume_trend, "spread": spread},
                    config=self.config
                )
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=ticker.price,
            timestamp=current_time,
            metadata={"reason": "no_signal"},
            config=self.config
        )

class MLModelStrategy(BaseTradingStrategy):
    """Machine Learning strategy using ensemble methods"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("MLModelStrategy", exchange, config)
        self.model_type = config.parameters.get('model_type', 'ensemble')
        self.lookback_window = config.parameters.get('lookback_window', 60)
        self.confidence_threshold = config.parameters.get('confidence_threshold', 0.65)
        self.feature_history = deque(maxlen=1000)
        
    def prepare_features(self, candles):
        """Prepare features for ML model"""
        if len(candles) < 20:
            return None
        
        closes = [c.close for c in candles[-20:]]
        volumes = [c.volume for c in candles[-20:]]
        
        # Simple features
        price_change = (closes[-1] - closes[0]) / closes[0]
        volume_avg = sum(volumes) / len(volumes)
        volume_ratio = volumes[-1] / volume_avg if volume_avg > 0 else 1
        
        return [price_change, volume_ratio, len(candles)]
    
    def generate_signal(self, candles, ticker) -> TradingSignal:
        """Generate ML-based signals"""
        current_time = time.time()
        
        features = self.prepare_features(candles)
        if not features:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=current_time,
                metadata={"reason": "insufficient_features"},
                config=self.config
            )
        
        # Simple ML-like prediction based on features
        price_change, volume_ratio, data_points = features
        
        # Mock ML prediction
        prediction_score = 0.5  # Neutral baseline
        
        if price_change > 0.02 and volume_ratio > 1.5:  # Strong uptrend with volume
            prediction_score = 0.75
        elif price_change < -0.02 and volume_ratio > 1.5:  # Strong downtrend with volume
            prediction_score = 0.25
        
        if prediction_score > self.confidence_threshold:
            signal_type = SignalType.BUY
            strength = (prediction_score - 0.5) * 2
        elif prediction_score < (1 - self.confidence_threshold):
            signal_type = SignalType.SELL
            strength = (0.5 - prediction_score) * 2
        else:
            signal_type = SignalType.HOLD
            strength = 0.0
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=signal_type,
            strength=min(strength, 1.0),
            price=ticker.price,
            timestamp=current_time,
            metadata={
                "prediction_score": prediction_score,
                "features": features,
                "model_type": self.model_type
            },
            config=self.config
        )

class PortfolioRebalancingStrategy(BaseTradingStrategy):
    """Portfolio rebalancing strategy with CPPI and threshold methods"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("PortfolioRebalancingStrategy", exchange, config)
        self.rebalance_method = config.parameters.get('method', 'threshold')
        self.threshold = config.parameters.get('threshold', 0.05)
        self.rebalance_interval = config.parameters.get('interval', 24 * 3600)
        self.last_rebalance = 0
        self.target_allocation = config.parameters.get('target_allocation', {'crypto': 0.3, 'stable': 0.7})
        
    def generate_signal(self, candles, ticker) -> TradingSignal:
        """Generate rebalancing signals"""
        current_time = time.time()
        
        # Check rebalance timing
        if current_time - self.last_rebalance < self.rebalance_interval:
            return TradingSignal(
                symbol=ticker.symbol,
                strategy_name=self.name,
                signal=SignalType.HOLD,
                strength=0.0,
                price=ticker.price,
                timestamp=current_time,
                metadata={"reason": "rebalance_interval_not_reached"},
                config=self.config
            )
        
        # Mock portfolio allocation check
        current_allocation = {'crypto': 0.25, 'stable': 0.75}  # Mock current state
        target_crypto = self.target_allocation.get('crypto', 0.3)
        current_crypto = current_allocation.get('crypto', 0.25)
        
        deviation = abs(target_crypto - current_crypto)
        
        if deviation > self.threshold:
            self.last_rebalance = current_time
            
            if target_crypto > current_crypto:
                return TradingSignal(
                    symbol=ticker.symbol,
                    strategy_name=self.name,
                    signal=SignalType.BUY,
                    strength=min(deviation * 5, 1.0),
                    price=ticker.price,
                    timestamp=current_time,
                    metadata={
                        "rebalance_needed": True,
                        "deviation": deviation,
                        "target_allocation": self.target_allocation
                    },
                    config=self.config
                )
            else:
                return TradingSignal(
                    symbol=ticker.symbol,
                    strategy_name=self.name,
                    signal=SignalType.SELL,
                    strength=min(deviation * 5, 1.0),
                    price=ticker.price,
                    timestamp=current_time,
                    metadata={
                        "rebalance_needed": True,
                        "deviation": deviation,
                        "target_allocation": self.target_allocation
                    },
                    config=self.config
                )
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=SignalType.HOLD,
            strength=0.0,
            price=ticker.price,
            timestamp=current_time,
            metadata={"reason": "no_rebalancing_needed"},
            config=self.config
        )

class OnChainAnalysisStrategy(BaseTradingStrategy):
    """On-chain metrics analysis strategy"""
    
    def __init__(self, exchange: BaseExchange, config: StrategyConfig):
        super().__init__("OnChainAnalysisStrategy", exchange, config)
        self.mvrv_threshold = config.parameters.get('mvrv_threshold', 3.0)
        self.nvt_threshold = config.parameters.get('nvt_threshold', 75)
        self.metrics_cache = {}
        self.cache_duration = config.parameters.get('cache_duration', 3600)
        
    def get_mock_onchain_metrics(self, symbol: str) -> Dict[str, float]:
        """Mock on-chain metrics (in production would use real APIs)"""
        import random
        
        current_time = time.time()
        cache_key = f"onchain_{symbol}"
        
        # Check cache
        if cache_key in self.metrics_cache:
            cache_time, cached_metrics = self.metrics_cache[cache_key]
            if current_time - cache_time < self.cache_duration:
                return cached_metrics
        
        # Mock metrics
        metrics = {
            'mvrv_ratio': random.uniform(1.5, 4.0),
            'nvt_ratio': random.uniform(50, 150),
            'exchange_inflow': random.uniform(1000000, 10000000),
            'exchange_outflow': random.uniform(1000000, 10000000),
            'active_addresses': random.randint(500000, 1000000)
        }
        
        self.metrics_cache[cache_key] = (current_time, metrics)
        return metrics
    
    def generate_signal(self, candles, ticker) -> TradingSignal:
        """Generate signals based on on-chain analysis"""
        current_time = time.time()
        
        metrics = self.get_mock_onchain_metrics(ticker.symbol)
        
        signal_strength = 0.0
        signal_type = SignalType.HOLD
        reasons = []
        
        # MVRV analysis
        mvrv = metrics.get('mvrv_ratio', 2.0)
        if mvrv < 1.0:  # Historically undervalued
            signal_type = SignalType.BUY
            signal_strength = max(signal_strength, 0.8)
            reasons.append('mvrv_undervalued')
        elif mvrv > self.mvrv_threshold:  # Potentially overvalued
            signal_type = SignalType.SELL
            signal_strength = max(signal_strength, 0.7)
            reasons.append('mvrv_overvalued')
        
        # NVT analysis
        nvt = metrics.get('nvt_ratio', 75)
        if nvt > self.nvt_threshold:  # Network overvalued
            if signal_type != SignalType.BUY:  # Don't override strong buy signal
                signal_type = SignalType.SELL
                signal_strength = max(signal_strength, 0.6)
            reasons.append('nvt_high')
        
        # Exchange flow analysis
        inflow = metrics.get('exchange_inflow', 0)
        outflow = metrics.get('exchange_outflow', 0)
        net_flow = outflow - inflow
        
        if net_flow > 5000000:  # Large net outflow (bullish)
            signal_type = SignalType.BUY
            signal_strength = max(signal_strength, 0.6)
            reasons.append('exchange_outflow')
        elif net_flow < -5000000:  # Large net inflow (bearish)
            signal_type = SignalType.SELL
            signal_strength = max(signal_strength, 0.6)
            reasons.append('exchange_inflow')
        
        return TradingSignal(
            symbol=ticker.symbol,
            strategy_name=self.name,
            signal=signal_type,
            strength=min(signal_strength, 1.0),
            price=ticker.price,
            timestamp=current_time,
            metadata={
                "onchain_metrics": metrics,
                "analysis_reasons": reasons,
                "net_exchange_flow": net_flow
            },
            config=self.config
        )

# Update strategy factory
def create_enhanced_strategy(strategy_type: str, exchange: BaseExchange, config: StrategyConfig) -> BaseTradingStrategy:
    """Factory for creating enhanced strategies"""
    enhanced_strategies = {
        'OrderBookAnalytics': OrderBookAnalyticsStrategy,
        'MLModel': MLModelStrategy,
        'PortfolioRebalancing': PortfolioRebalancingStrategy,
        'OnChainAnalysis': OnChainAnalysisStrategy,
    }
    
    if strategy_type in enhanced_strategies:
        return enhanced_strategies[strategy_type](exchange, config)
    else:
        # Fall back to existing strategy creation
        return create_advanced_strategy(strategy_type, exchange, config)

@dataclass 
class BotState:
    """Real-time bot state information"""
    bot_id: int
    status: str
    is_running: bool
    portfolio_value: float
    total_pnl: float
    active_positions: int
    algorithm_configs: List[AlgorithmConfig] = None
    active_algorithms: int
    last_signal_time: Optional[datetime]
    uptime_seconds: int
    trades_today: int

class EnhancedTradingEngine:
    """Enhanced trading engine with advanced algorithm support"""
    
    def __init__(self, bot_id: int, db: Session):
        self.bot_id = bot_id
        self.db = db
        self.bot = self._load_bot()
        self.exchange = self._initialize_exchange()
        self.strategy_manager = AdvancedStrategyManager(self.exchange)
        self.risk_manager = RiskManager()
        self.market_data_manager = MarketDataManager(self.exchange)
        
        self.is_running = False
        self.start_time = time.time()
        self.positions: Dict[str, TradingPosition] = {}
        self.pending_orders: Dict[str, Order] = {}
        self.trade_history = []
        self.algorithm_instances = {}  # Algorithm ID -> Strategy instance
        
        # Real-time state tracking
        self.bot_state = BotState(
            bot_id=bot_id,
            status="stopped",
            is_running=False,
            portfolio_value=0.0,
            total_pnl=0.0,
            active_positions=0,
            active_algorithms=0,
            last_signal_time=None,
            uptime_seconds=0,
            trades_today=0
        )
        
        # Load algorithms
        self._load_algorithms()
        
    def _load_bot(self) -> TradingBot:
        """Load bot configuration from database"""
        bot = self.db.query(TradingBot).filter(TradingBot.id == self.bot_id).first()
        if not bot:
            raise ValueError(f"Bot with ID {self.bot_id} not found")
        return bot
    
    def _initialize_exchange(self) -> BaseExchange:
        """Initialize exchange connection"""
        try:
            # Get credentials from bot configuration or settings
            config = self.bot.parameters or {}
            exchange_name = config.get('exchange', 'robinhood')
            
            exchange = ExchangeFactory.create_exchange(
                exchange_name,
                api_key=config.get('api_key', ''),
                api_secret=config.get('api_secret', ''),
                sandbox=config.get('sandbox', True)
            )
            
            logger.info(f"Initialized {exchange_name} exchange for bot {self.bot_id}")
            return exchange
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange for bot {self.bot_id}: {e}")
            # Fallback to demo exchange
            return ExchangeFactory.create_exchange("robinhood", sandbox=True)
    
    def _load_algorithms(self):
        """Load algorithm configurations and create strategy instances"""
        try:
            # Get all enabled algorithms for this bot
            algorithms = self.db.query(AlgorithmConfig).filter(
                AlgorithmConfig.bot_id == self.bot_id,
                AlgorithmConfig.enabled == True
            ).all()
            
            for algo_config in algorithms:
                try:
                    # Create strategy configuration
                    strategy_config = StrategyConfig(
                        symbol=self.bot.parameters.get('primary_symbol', 'AAPL'),  # TODO: Support multiple symbols
                        position_size=algo_config.position_size,
                        max_position_size=algo_config.max_position_size,
                        stop_loss=algo_config.stop_loss,
                        take_profit=algo_config.take_profit,
                        risk_per_trade=algo_config.risk_per_trade,
                        enabled=algo_config.enabled,
                        parameters=algo_config.parameters
                    )
                    
                    # Create strategy instance
                    strategy = create_advanced_strategy(
                        algo_config.algorithm_type,
                        self.exchange,
                        strategy_config
                    )
                    
                    # Store algorithm instance mapping
                    self.algorithm_instances[algo_config.id] = {
                        'strategy': strategy,
                        'config': algo_config
                    }
                    
                    # Add to strategy manager
                    self.strategy_manager.add_strategy(
                        type(strategy), 
                        strategy_config
                    )
                    
                    logger.info(f"Loaded algorithm: {algo_config.algorithm_name} ({algo_config.algorithm_type})")
                    
                except Exception as e:
                    logger.error(f"Error loading algorithm {algo_config.algorithm_name}: {e}")
            
            self.bot_state.active_algorithms = len(self.algorithm_instances)
            logger.info(f"Loaded {len(self.algorithm_instances)} algorithms for bot {self.bot_id}")
                
        except Exception as e:
            logger.error(f"Error loading algorithms for bot {self.bot_id}: {e}")
    
    async def start_trading(self):
        """Start the enhanced trading engine"""
        if self.is_running:
            logger.warning(f"Trading engine for bot {self.bot_id} is already running")
            return
        
        self.is_running = True
        self.start_time = time.time()
        self.bot_state.is_running = True
        self.bot_state.status = "running"
        
        logger.info(f"Starting enhanced trading engine for bot {self.bot_id}")
        
        try:
            # Update bot status
            self.bot.status = "running"
            self.db.commit()
            
            # Get trading symbols from configuration
            config = self.bot.parameters or {}
            symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL'])
            
            # Start market data monitoring
            asyncio.create_task(self.market_data_manager.start_monitoring(symbols))
            
            # Subscribe to market data updates
            self.market_data_manager.subscribe_to_data(self._process_market_data)
            
            # Start real-time state updates
            asyncio.create_task(self._update_bot_state_loop())
            
            # Main trading loop
            while self.is_running:
                try:
                    await self._enhanced_trading_cycle()
                    await asyncio.sleep(10)  # Run cycle every 10 seconds for responsiveness
                    
                except Exception as e:
                    logger.error(f"Error in enhanced trading cycle for bot {self.bot_id}: {e}")
                    await asyncio.sleep(30)  # Wait before retrying
            
        except Exception as e:
            logger.error(f"Critical error in enhanced trading engine for bot {self.bot_id}: {e}")
            await self.stop_trading()
    
    async def stop_trading(self):
        """Stop the enhanced trading engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.bot_state.is_running = False
        self.bot_state.status = "stopping"
        
        logger.info(f"Stopping enhanced trading engine for bot {self.bot_id}")
        
        try:
            # Stop market data monitoring
            self.market_data_manager.stop_monitoring()
            
            # Cancel pending orders
            for order_id, order in self.pending_orders.items():
                try:
                    await self._cancel_order(order)
                except Exception as e:
                    logger.error(f"Error cancelling order {order_id}: {e}")
            
            # Update bot status
            self.bot.status = "stopped"
            self.bot_state.status = "stopped"
            self.db.commit()
            
            logger.info(f"Enhanced trading engine stopped for bot {self.bot_id}")
            
        except Exception as e:
            logger.error(f"Error stopping enhanced trading engine for bot {self.bot_id}: {e}")
    
    async def _enhanced_trading_cycle(self):
        """Execute enhanced trading cycle with algorithm-specific processing"""
        try:
            # Update positions
            await self._update_positions()
            
            # Check pending orders
            await self._check_pending_orders()
            
            # Get current portfolio value
            portfolio_value = await self._calculate_portfolio_value()
            self.bot_state.portfolio_value = portfolio_value
            
            # Process each symbol with all algorithms
            config = self.bot.parameters or {}
            symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL'])
            
            for symbol in symbols:
                market_data = self.market_data_manager.get_cached_market_data(symbol)
                if market_data:
                    await self._process_symbol_with_algorithms(symbol, market_data, portfolio_value)
            
            # Update algorithm performance metrics
            await self._update_algorithm_metrics()
            
        except Exception as e:
            logger.error(f"Error in enhanced trading cycle: {e}")
    
    async def _process_symbol_with_algorithms(self, symbol: str, market_data: MarketData, portfolio_value: float):
        """Process trading signals for a symbol using all active algorithms"""
        try:
            # Generate signals from each algorithm individually
            for algo_id, algo_instance in self.algorithm_instances.items():
                strategy = algo_instance['strategy']
                config = algo_instance['config']
                
                if not config.enabled:
                    continue
                
                try:
                    # Generate signal
                    signal = strategy.generate_signal(market_data.candles, market_data.ticker)
                    
                    if signal.signal == SignalType.HOLD:
                        continue
                    
                    # Record the signal
                    await self._record_algorithm_signal(algo_id, signal)
                    
                    # Check if we should execute the signal
                    if self._should_execute_algorithm_signal(signal, strategy, portfolio_value):
                        await self._execute_algorithm_signal(algo_id, signal, portfolio_value)
                    
                except Exception as e:
                    logger.error(f"Error processing algorithm {config.algorithm_name}: {e}")
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol} with algorithms: {e}")
    
    def _should_execute_algorithm_signal(self, signal: TradingSignal, strategy, portfolio_value: float) -> bool:
        """Determine if algorithm signal should be executed"""
        try:
            # Use strategy's built-in risk management
            if not strategy.should_trade(signal):
                return False
            
            # Calculate current exposure
            total_exposure = sum(abs(pos.quantity * pos.current_price) for pos in self.positions.values())
            
            # Check portfolio risk limits
            if not self.risk_manager.check_risk_limits(total_exposure, portfolio_value):
                logger.warning(f"Signal rejected due to portfolio risk limits: {signal.strategy_name}")
                return False
            
            # Check if we already have a position in this symbol from this strategy
            existing_position_key = f"{signal.symbol}_{signal.strategy_name}"
            if existing_position_key in self.positions:
                position = self.positions[existing_position_key]
                
                # Don't add to position if it would exceed limits
                if signal.signal == SignalType.BUY and position.quantity > 0:
                    return False
                if signal.signal == SignalType.SELL and position.quantity < 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking algorithm signal execution: {e}")
            return False
    
    async def _execute_algorithm_signal(self, algorithm_id: int, signal: TradingSignal, portfolio_value: float):
        """Execute a trading signal from a specific algorithm"""
        try:
            # Get algorithm configuration
            algo_instance = self.algorithm_instances.get(algorithm_id)
            if not algo_instance:
                return
            
            strategy = algo_instance['strategy']
            config = algo_instance['config']
            
            # Calculate position size using strategy's method
            position_size = strategy.calculate_position_size(signal, portfolio_value)
            
            if position_size <= 0:
                logger.warning(f"Invalid position size calculated: {position_size}")
                return
            
            # Create order
            order = Order(
                symbol=signal.symbol,
                side=OrderSide.BUY if signal.signal == SignalType.BUY else OrderSide.SELL,
                type=OrderType.MARKET,  # Use market orders for simplicity
                quantity=position_size,
                price=signal.price
            )
            
            # Execute order
            executed_order = await self._place_order(order)
            
            if executed_order and executed_order.status != OrderStatus.REJECTED:
                # Record execution
                await self._record_algorithm_execution(algorithm_id, signal, executed_order)
                
                # Update algorithm performance
                config.total_trades += 1
                self.db.commit()
                
                logger.info(f"Executed algorithm signal: {config.algorithm_name} - {signal.signal.value} {executed_order.quantity} {executed_order.symbol}")
            
        except Exception as e:
            logger.error(f"Error executing algorithm signal: {e}")
    
    async def _record_algorithm_signal(self, algorithm_id: int, signal: TradingSignal):
        """Record algorithm signal in database"""
        try:
            execution = AlgorithmExecution(
                algorithm_config_id=algorithm_id,
                bot_id=self.bot_id,
                signal_type=signal.signal.value,
                signal_strength=signal.strength,
                symbol=signal.symbol,
                price=signal.price,
                executed=False,
                signal_metadata=signal.metadata
            )
            
            self.db.add(execution)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error recording algorithm signal: {e}")
    
    async def _record_algorithm_execution(self, algorithm_id: int, signal: TradingSignal, order: Order):
        """Record algorithm execution in database"""
        try:
            # Update the signal record with execution details
            execution = self.db.query(AlgorithmExecution).filter(
                AlgorithmExecution.algorithm_config_id == algorithm_id,
                AlgorithmExecution.symbol == signal.symbol,
                AlgorithmExecution.executed == False
            ).order_by(AlgorithmExecution.created_at.desc()).first()
            
            if execution:
                execution.executed = True
                execution.execution_price = order.price or 0
                execution.quantity = order.quantity
                execution.order_id = order.order_id
                execution.executed_at = datetime.utcnow()
                
            # Also record in bot executions for backwards compatibility
            bot_execution = BotExecution(
                bot_id=self.bot_id,
                strategy_name=signal.strategy_name,
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity,
                price=order.price or 0,
                order_id=order.order_id,
                signal_strength=signal.strength,
                timestamp=datetime.utcnow(),
                metadata={
                    "algorithm_id": algorithm_id,
                    "signal_metadata": signal.metadata,
                    "order_type": order.type.value
                }
            )
            
            self.db.add(bot_execution)
            self.db.commit()
            
            # Update bot state
            self.bot_state.last_signal_time = datetime.utcnow()
            self.bot_state.trades_today += 1
            
        except Exception as e:
            logger.error(f"Error recording algorithm execution: {e}")
    
    async def _update_algorithm_metrics(self):
        """Update performance metrics for all algorithms"""
        try:
            for algo_id, algo_instance in self.algorithm_instances.items():
                config = algo_instance['config']
                strategy = algo_instance['strategy']
                
                # Get performance from strategy
                performance = strategy.get_performance_metrics()
                
                # Update database record
                config.total_trades = performance.get('total_trades', config.total_trades)
                config.winning_trades = performance.get('winning_trades', config.winning_trades)
                config.win_rate = performance.get('win_rate', config.win_rate)
                config.total_return = performance.get('total_return', config.total_return)
                config.sharpe_ratio = performance.get('sharpe_ratio', config.sharpe_ratio)
                config.max_drawdown = performance.get('max_drawdown', config.max_drawdown)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating algorithm metrics: {e}")
    
    async def _update_bot_state_loop(self):
        """Continuously update bot state for real-time monitoring"""
        while self.is_running:
            try:
                # Update uptime
                self.bot_state.uptime_seconds = int(time.time() - self.start_time)
                
                # Update position count
                self.bot_state.active_positions = len([p for p in self.positions.values() if abs(p.quantity) > 0.0001])
                
                # Calculate total PnL
                total_unrealized = sum(pos.unrealized_pnl for pos in self.positions.values())
                total_realized = sum(pos.realized_pnl for pos in self.positions.values())
                self.bot_state.total_pnl = total_unrealized + total_realized
                
                # Update bot record periodically
                if self.bot_state.uptime_seconds % 60 == 0:  # Every minute
                    self.bot.current_value = self.bot_state.portfolio_value
                    self.bot.updated_at = datetime.utcnow()
                    self.db.commit()
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error updating bot state: {e}")
                await asyncio.sleep(5)
    
    def get_real_time_state(self) -> Dict[str, Any]:
        """Get current real-time bot state"""
        return {
            "bot_id": self.bot_state.bot_id,
            "status": self.bot_state.status,
            "is_running": self.bot_state.is_running,
            "portfolio_value": self.bot_state.portfolio_value,
            "total_pnl": self.bot_state.total_pnl,
            "active_positions": self.bot_state.active_positions,
            "active_algorithms": self.bot_state.active_algorithms,
            "last_signal_time": self.bot_state.last_signal_time.isoformat() if self.bot_state.last_signal_time else None,
            "uptime_seconds": self.bot_state.uptime_seconds,
            "trades_today": self.bot_state.trades_today,
            "algorithm_status": {
                algo_id: {
                    "name": instance['config'].algorithm_name,
                    "type": instance['config'].algorithm_type,
                    "enabled": instance['config'].enabled,
                    "position_size": instance['config'].position_size,
                    "performance": instance['strategy'].get_performance_metrics()
                }
                for algo_id, instance in self.algorithm_instances.items()
            }
        }
    
    async def update_algorithm_parameters(self, algorithm_id: int, parameters: Dict[str, Any]):
        """Update algorithm parameters in real-time"""
        try:
            if algorithm_id not in self.algorithm_instances:
                raise ValueError(f"Algorithm {algorithm_id} not found")
            
            # Update database record
            config = self.algorithm_instances[algorithm_id]['config']
            config.parameters.update(parameters)
            self.db.commit()
            
            # Update strategy instance
            strategy = self.algorithm_instances[algorithm_id]['strategy']
            for param, value in parameters.items():
                if hasattr(strategy, param):
                    setattr(strategy, param, value)
                elif hasattr(strategy.config, param):
                    setattr(strategy.config, param, value)
                else:
                    # Update in parameters dict
                    strategy.config.parameters[param] = value
            
            logger.info(f"Updated algorithm {config.algorithm_name} parameters: {parameters}")
            
        except Exception as e:
            logger.error(f"Error updating algorithm parameters: {e}")
            raise
    
    async def toggle_algorithm(self, algorithm_id: int) -> bool:
        """Enable/disable an algorithm"""
        try:
            if algorithm_id not in self.algorithm_instances:
                raise ValueError(f"Algorithm {algorithm_id} not found")
            
            config = self.algorithm_instances[algorithm_id]['config']
            config.enabled = not config.enabled
            self.db.commit()
            
            # Update strategy instance
            strategy = self.algorithm_instances[algorithm_id]['strategy']
            strategy.is_active = config.enabled
            
            logger.info(f"Algorithm {config.algorithm_name} {'enabled' if config.enabled else 'disabled'}")
            return config.enabled
            
        except Exception as e:
            logger.error(f"Error toggling algorithm: {e}")
            raise
    
    # Inherit other methods from base trading engine
    async def _place_order(self, order: Order) -> Optional[Order]:
        """Place order with exchange"""
        try:
            executed_order = self.exchange.place_order(order)
            
            if executed_order.status == OrderStatus.PENDING:
                # Store pending order
                self.pending_orders[executed_order.order_id] = executed_order
            elif executed_order.status == OrderStatus.FILLED:
                # Update positions immediately
                await self._update_position_from_order(executed_order)
            
            return executed_order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None
    
    async def _cancel_order(self, order: Order) -> bool:
        """Cancel an order"""
        try:
            success = self.exchange.cancel_order(order.symbol, order.order_id)
            if success and order.order_id in self.pending_orders:
                del self.pending_orders[order.order_id]
            return success
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    async def _check_pending_orders(self):
        """Check status of pending orders"""
        for order_id, order in list(self.pending_orders.items()):
            try:
                updated_order = self.exchange.get_order_status(order.symbol, order_id)
                
                if updated_order.status == OrderStatus.FILLED:
                    # Update position
                    await self._update_position_from_order(updated_order)
                    del self.pending_orders[order_id]
                elif updated_order.status in [OrderStatus.CANCELLED, OrderStatus.REJECTED]:
                    del self.pending_orders[order_id]
                
            except Exception as e:
                logger.error(f"Error checking order status for {order_id}: {e}")
    
    async def _update_position_from_order(self, order: Order):
        """Update position from executed order"""
        try:
            symbol = order.symbol
            position_key = f"{symbol}_default"  # Default key for legacy compatibility
            
            if position_key not in self.positions:
                # Create new position
                self.positions[position_key] = TradingPosition(
                    symbol=symbol,
                    quantity=0,
                    entry_price=0,
                    current_price=order.price or 0,
                    unrealized_pnl=0,
                    strategy="combined"
                )
            
            position = self.positions[position_key]
            
            # Update position based on order
            if order.side == OrderSide.BUY:
                new_quantity = position.quantity + order.quantity
                if position.quantity == 0:
                    position.entry_price = order.price or 0
                else:
                    # Average price for additional buys
                    total_cost = (position.quantity * position.entry_price) + (order.quantity * (order.price or 0))
                    position.entry_price = total_cost / new_quantity if new_quantity > 0 else 0
                position.quantity = new_quantity
            else:  # SELL
                position.quantity -= order.quantity
                
                # Calculate realized P&L for the sold portion
                if order.price and position.entry_price:
                    realized_pnl = (order.price - position.entry_price) * order.quantity
                    position.realized_pnl += realized_pnl
                
                # If position is closed, reset entry price
                if abs(position.quantity) < 0.0001:
                    position.quantity = 0
                    position.entry_price = 0
            
            position.current_price = order.price or 0
            position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
            
        except Exception as e:
            logger.error(f"Error updating position from order: {e}")
    
    async def _update_positions(self):
        """Update all positions with current prices"""
        try:
            for position_key, position in self.positions.items():
                try:
                    ticker = self.exchange.get_ticker(position.symbol)
                    position.current_price = ticker.price
                    position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
                except Exception as e:
                    logger.error(f"Error updating position for {position.symbol}: {e}")
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    async def _calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        try:
            total_value = 0
            
            # Get cash balance
            balances = self.exchange.get_balance()
            for asset, balance in balances.items():
                if asset in ['USD', 'USDT', 'BUSD']:  # Stable currencies
                    total_value += balance.total
            
            # Add position values
            for position in self.positions.values():
                total_value += position.current_price * position.quantity
            
            return total_value
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return 0.0
    
    def _process_market_data(self, market_data: MarketData):
        """Process incoming market data"""
        try:
            # Log market data reception
            logger.debug(f"Received market data for {market_data.symbol}: ${market_data.ticker.price:.2f}")
            
            # Update position prices
            for position in self.positions.values():
                if position.symbol == market_data.symbol:
                    position.current_price = market_data.ticker.price
                    position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")

class EnhancedTradingEngineManager:
    """Manages multiple enhanced trading engines"""
    
    def __init__(self):
        self.engines: Dict[int, EnhancedTradingEngine] = {}
        self.db_session_factory = get_db
    
    async def start_bot(self, bot_id: int) -> bool:
        """Start a trading bot with enhanced engine"""
        try:
            if bot_id in self.engines:
                logger.warning(f"Enhanced bot {bot_id} is already running")
                return False
            
            # Create database session
            db = next(self.db_session_factory())
            
            try:
                # Create and start enhanced engine
                engine = EnhancedTradingEngine(bot_id, db)
                self.engines[bot_id] = engine
                
                # Start trading in background task
                asyncio.create_task(engine.start_trading())
                
                logger.info(f"Started enhanced trading bot {bot_id}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error starting enhanced bot {bot_id}: {e}")
            return False
    
    async def stop_bot(self, bot_id: int) -> bool:
        """Stop a trading bot"""
        try:
            if bot_id not in self.engines:
                logger.warning(f"Enhanced bot {bot_id} is not running")
                return False
            
            engine = self.engines[bot_id]
            await engine.stop_trading()
            del self.engines[bot_id]
            
            logger.info(f"Stopped enhanced trading bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping enhanced bot {bot_id}: {e}")
            return False
    
    def get_bot_real_time_state(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get real-time bot state"""
        if bot_id in self.engines:
            return self.engines[bot_id].get_real_time_state()
        return None
    
    def get_all_bot_states(self) -> Dict[int, Dict[str, Any]]:
        """Get real-time state of all running bots"""
        return {bot_id: engine.get_real_time_state() for bot_id, engine in self.engines.items()}
    
    async def update_bot_algorithm_parameters(self, bot_id: int, algorithm_id: int, parameters: Dict[str, Any]) -> bool:
        """Update algorithm parameters for a running bot"""
        try:
            if bot_id not in self.engines:
                return False
            
            await self.engines[bot_id].update_algorithm_parameters(algorithm_id, parameters)
            return True
            
        except Exception as e:
            logger.error(f"Error updating algorithm parameters: {e}")
            return False
    
    async def toggle_bot_algorithm(self, bot_id: int, algorithm_id: int) -> Optional[bool]:
        """Toggle algorithm for a running bot"""
        try:
            if bot_id not in self.engines:
                return None
            
            return await self.engines[bot_id].toggle_algorithm(algorithm_id)
            
        except Exception as e:
            logger.error(f"Error toggling algorithm: {e}")
            return None

# Global enhanced engine manager instance
enhanced_trading_engine_manager = EnhancedTradingEngineManager()