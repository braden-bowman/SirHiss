"""
Advanced Trading Engine for SirHiss Trading Platform
Orchestrates trading strategies, risk management, and execution
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from datetime import datetime

from .exchange_api import BaseExchange, ExchangeFactory, Order, OrderSide, OrderType, OrderStatus
from .trading_strategies import StrategyManager, TradingSignal, SignalType, get_default_strategies
from .data_monitor import MarketDataManager, MarketData, RiskManager
from ..models.trading_bot import TradingBot
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

class TradingEngine:
    """Main trading engine that orchestrates all trading activities"""
    
    def __init__(self, bot_id: int, db: Session):
        self.bot_id = bot_id
        self.db = db
        self.bot = self._load_bot()
        self.exchange = self._initialize_exchange()
        self.strategy_manager = StrategyManager()
        self.risk_manager = RiskManager()
        self.market_data_manager = MarketDataManager(self.exchange)
        
        self.is_running = False
        self.positions: Dict[str, TradingPosition] = {}
        self.pending_orders: Dict[str, Order] = {}
        self.trade_history = []
        
        # Load strategies
        self._load_strategies()
        
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
            config = self.bot.configuration or {}
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
    
    def _load_strategies(self):
        """Load trading strategies from configuration"""
        try:
            config = self.bot.configuration or {}
            strategy_config = config.get('strategies', {})
            
            # Load default strategies if none configured
            if not strategy_config:
                strategies = get_default_strategies()
                for strategy in strategies:
                    self.strategy_manager.add_strategy(strategy)
                logger.info(f"Loaded {len(strategies)} default strategies for bot {self.bot_id}")
            else:
                # Load configured strategies
                # This would parse the strategy configuration and create instances
                # For now, load defaults with configured allocations
                strategies = get_default_strategies()
                for strategy in strategies:
                    if strategy.name in strategy_config:
                        strategy.allocation = strategy_config[strategy.name].get('allocation', 0.1)
                        strategy.is_active = strategy_config[strategy.name].get('active', True)
                    self.strategy_manager.add_strategy(strategy)
                
                logger.info(f"Loaded {len(strategies)} configured strategies for bot {self.bot_id}")
                
        except Exception as e:
            logger.error(f"Error loading strategies for bot {self.bot_id}: {e}")
            # Load defaults as fallback
            strategies = get_default_strategies()
            for strategy in strategies:
                self.strategy_manager.add_strategy(strategy)
    
    async def start_trading(self):
        """Start the trading engine"""
        if self.is_running:
            logger.warning(f"Trading engine for bot {self.bot_id} is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting trading engine for bot {self.bot_id}")
        
        try:
            # Update bot status
            self.bot.status = "running"
            self.bot.last_active = datetime.utcnow()
            self.db.commit()
            
            # Get trading symbols from configuration
            config = self.bot.configuration or {}
            symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL'])
            
            # Start market data monitoring
            asyncio.create_task(self.market_data_manager.start_monitoring(symbols))
            
            # Subscribe to market data updates
            self.market_data_manager.subscribe_to_data(self._process_market_data)
            
            # Main trading loop
            while self.is_running:
                try:
                    await self._trading_cycle()
                    await asyncio.sleep(60)  # Run cycle every minute
                    
                except Exception as e:
                    logger.error(f"Error in trading cycle for bot {self.bot_id}: {e}")
                    await asyncio.sleep(30)  # Wait before retrying
            
        except Exception as e:
            logger.error(f"Critical error in trading engine for bot {self.bot_id}: {e}")
            await self.stop_trading()
    
    async def stop_trading(self):
        """Stop the trading engine"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info(f"Stopping trading engine for bot {self.bot_id}")
        
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
            self.bot.last_active = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Trading engine stopped for bot {self.bot_id}")
            
        except Exception as e:
            logger.error(f"Error stopping trading engine for bot {self.bot_id}: {e}")
    
    async def _trading_cycle(self):
        """Execute one trading cycle"""
        try:
            # Update positions
            await self._update_positions()
            
            # Check pending orders
            await self._check_pending_orders()
            
            # Get current portfolio value
            portfolio_value = await self._calculate_portfolio_value()
            
            # Process each symbol
            config = self.bot.configuration or {}
            symbols = config.get('symbols', ['AAPL', 'MSFT', 'GOOGL'])
            
            for symbol in symbols:
                market_data = self.market_data_manager.get_cached_market_data(symbol)
                if market_data:
                    await self._process_symbol(symbol, market_data, portfolio_value)
            
            # Update bot metrics
            await self._update_bot_metrics()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    def _process_market_data(self, market_data: MarketData):
        """Process incoming market data"""
        try:
            # Log market data reception
            logger.debug(f"Received market data for {market_data.symbol}: ${market_data.ticker.price:.2f}")
            
            # Update position prices
            if market_data.symbol in self.positions:
                position = self.positions[market_data.symbol]
                position.current_price = market_data.ticker.price
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
    
    async def _process_symbol(self, symbol: str, market_data: MarketData, portfolio_value: float):
        """Process trading signals for a symbol"""
        try:
            # Generate signals from all strategies
            signals = await self.strategy_manager.generate_signals(
                symbol, market_data.candles, market_data.ticker
            )
            
            if not signals:
                return
            
            # Get combined signal
            combined_signal = self.strategy_manager.get_combined_signal(signals)
            
            if not combined_signal or combined_signal.signal == SignalType.HOLD:
                return
            
            # Check risk limits
            if not self._check_risk_limits(combined_signal, portfolio_value):
                logger.warning(f"Signal rejected due to risk limits: {combined_signal}")
                return
            
            # Execute signal
            await self._execute_signal(combined_signal, portfolio_value)
            
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
    
    def _check_risk_limits(self, signal: TradingSignal, portfolio_value: float) -> bool:
        """Check if signal meets risk management criteria"""
        try:
            # Calculate current exposure
            total_exposure = sum(abs(pos.quantity * pos.current_price) for pos in self.positions.values())
            
            # Check portfolio risk limits
            if not self.risk_manager.check_risk_limits(total_exposure, portfolio_value):
                return False
            
            # Check if we already have a position in this symbol
            if signal.symbol in self.positions:
                position = self.positions[signal.symbol]
                
                # Don't add to position if it would exceed limits
                if signal.signal == SignalType.BUY and position.quantity > 0:
                    return False
                if signal.signal == SignalType.SELL and position.quantity < 0:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return False
    
    async def _execute_signal(self, signal: TradingSignal, portfolio_value: float):
        """Execute a trading signal"""
        try:
            # Calculate position size
            atr = signal.metadata.get('atr', 0.02 * signal.price)  # Default 2% ATR
            position_size = self.risk_manager.calculate_position_size(
                signal.strength, portfolio_value, signal.price, atr
            )
            
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
                await self._record_execution(signal, executed_order)
                logger.info(f"Executed signal: {signal.signal.value} {executed_order.quantity} {executed_order.symbol}")
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
    
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
            
            if symbol not in self.positions:
                # Create new position
                self.positions[symbol] = TradingPosition(
                    symbol=symbol,
                    quantity=0,
                    entry_price=0,
                    current_price=order.price or 0
                )
            
            position = self.positions[symbol]
            
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
            for symbol, position in self.positions.items():
                try:
                    ticker = self.exchange.get_ticker(symbol)
                    position.current_price = ticker.price
                    position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
                except Exception as e:
                    logger.error(f"Error updating position for {symbol}: {e}")
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
    
    async def _record_execution(self, signal: TradingSignal, order: Order):
        """Record trade execution in database"""
        try:
            execution = BotExecution(
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
                    "signal_metadata": signal.metadata,
                    "order_type": order.type.value
                }
            )
            
            self.db.add(execution)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error recording execution: {e}")
    
    async def _update_bot_metrics(self):
        """Update bot performance metrics"""
        try:
            # Calculate portfolio value
            portfolio_value = await self._calculate_portfolio_value()
            
            # Calculate total P&L
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
            
            # Update bot record
            self.bot.current_value = portfolio_value
            self.bot.unrealized_pnl = total_unrealized_pnl
            self.bot.realized_pnl = total_realized_pnl
            self.bot.last_active = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating bot metrics: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "bot_id": self.bot_id,
            "is_running": self.is_running,
            "positions": len(self.positions),
            "pending_orders": len(self.pending_orders),
            "strategies": len(self.strategy_manager.strategies),
            "last_update": time.time()
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        return [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "entry_price": pos.entry_price,
                "current_price": pos.current_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "realized_pnl": pos.realized_pnl
            }
            for pos in self.positions.values()
            if abs(pos.quantity) > 0.0001
        ]

class TradingEngineManager:
    """Manages multiple trading engines"""
    
    def __init__(self):
        self.engines: Dict[int, TradingEngine] = {}
        self.db_session_factory = get_db
    
    async def start_bot(self, bot_id: int) -> bool:
        """Start a trading bot"""
        try:
            if bot_id in self.engines:
                logger.warning(f"Bot {bot_id} is already running")
                return False
            
            # Create database session
            db = next(self.db_session_factory())
            
            try:
                # Create and start engine
                engine = TradingEngine(bot_id, db)
                self.engines[bot_id] = engine
                
                # Start trading in background task
                asyncio.create_task(engine.start_trading())
                
                logger.info(f"Started trading bot {bot_id}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error starting bot {bot_id}: {e}")
            return False
    
    async def stop_bot(self, bot_id: int) -> bool:
        """Stop a trading bot"""
        try:
            if bot_id not in self.engines:
                logger.warning(f"Bot {bot_id} is not running")
                return False
            
            engine = self.engines[bot_id]
            await engine.stop_trading()
            del self.engines[bot_id]
            
            logger.info(f"Stopped trading bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {e}")
            return False
    
    def get_bot_status(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get bot status"""
        if bot_id in self.engines:
            return self.engines[bot_id].get_status()
        return None
    
    def get_bot_positions(self, bot_id: int) -> List[Dict[str, Any]]:
        """Get bot positions"""
        if bot_id in self.engines:
            return self.engines[bot_id].get_positions()
        return []
    
    def get_all_statuses(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all running bots"""
        return {bot_id: engine.get_status() for bot_id, engine in self.engines.items()}

# Global engine manager instance
trading_engine_manager = TradingEngineManager()