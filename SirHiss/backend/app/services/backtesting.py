"""
Advanced Backtesting Service for SirHiss Trading Platform
Comprehensive backtesting framework with multiple strategies and risk analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from enum import Enum

from .exchange_api import BaseExchange, Candle, Ticker, Order, OrderSide, OrderType
from .trading_strategies import BaseTradingStrategy, TradingSignal, SignalType, get_default_strategies
from .data_monitor import RiskManager, TechnicalIndicatorCalculator
from ..models.trading import BacktestResult

logger = logging.getLogger(__name__)

class BacktestMode(Enum):
    SINGLE_STRATEGY = "single_strategy"
    MULTI_STRATEGY = "multi_strategy"
    WALK_FORWARD = "walk_forward"
    MONTE_CARLO = "monte_carlo"

@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    symbols: List[str] = field(default_factory=list)
    strategies: List[BaseTradingStrategy] = field(default_factory=list)
    commission: float = 0.001  # 0.1% commission
    slippage: float = 0.0005   # 0.05% slippage
    mode: BacktestMode = BacktestMode.SINGLE_STRATEGY
    risk_free_rate: float = 0.02
    benchmark_symbol: str = "SPY"

@dataclass
class Trade:
    """Individual trade record"""
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    strategy_name: str
    pnl: float = 0.0
    pnl_percent: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    duration_hours: float = 0.0
    signal_strength: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BacktestResults:
    """Comprehensive backtesting results"""
    config: BacktestConfig
    
    # Performance metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    avg_trade_duration: float = 0.0
    
    # Risk metrics
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0
    beta: float = 1.0
    alpha: float = 0.0
    
    # Time series data
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    benchmark_curve: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    
    # Trade log
    trades: List[Trade] = field(default_factory=list)
    
    # Strategy breakdown
    strategy_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Additional analysis
    monthly_returns: Dict[str, float] = field(default_factory=dict)
    yearly_returns: Dict[str, float] = field(default_factory=dict)
    rolling_metrics: Dict[str, List[float]] = field(default_factory=dict)

class BacktestEngine:
    """Advanced backtesting engine"""
    
    def __init__(self, exchange: BaseExchange):
        self.exchange = exchange
        self.risk_manager = RiskManager()
        self.tech_calculator = TechnicalIndicatorCalculator()
        
    def run_backtest(self, config: BacktestConfig) -> BacktestResults:
        """Run comprehensive backtest"""
        logger.info(f"Starting backtest: {config.start_date} to {config.end_date}")
        
        results = BacktestResults(config=config)
        
        try:
            if config.mode == BacktestMode.SINGLE_STRATEGY:
                return self._run_single_strategy_backtest(config, results)
            elif config.mode == BacktestMode.MULTI_STRATEGY:
                return self._run_multi_strategy_backtest(config, results)
            elif config.mode == BacktestMode.WALK_FORWARD:
                return self._run_walk_forward_backtest(config, results)
            elif config.mode == BacktestMode.MONTE_CARLO:
                return self._run_monte_carlo_backtest(config, results)
            else:
                raise ValueError(f"Unsupported backtest mode: {config.mode}")
                
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return results
    
    def _run_single_strategy_backtest(self, config: BacktestConfig, results: BacktestResults) -> BacktestResults:
        """Run backtest with single strategy"""
        if not config.strategies:
            logger.warning("No strategies provided for backtest")
            return results
        
        strategy = config.strategies[0]
        portfolio_value = config.initial_capital
        positions = {}  # symbol -> position info
        
        # Get historical data for all symbols
        historical_data = self._get_historical_data(config.symbols, config.start_date, config.end_date)
        
        if not historical_data:
            logger.error("No historical data available")
            return results
        
        # Create unified timeline
        all_timestamps = set()
        for symbol_data in historical_data.values():
            all_timestamps.update([candle.timestamp for candle in symbol_data])
        
        timestamps = sorted(all_timestamps)
        
        # Simulate trading
        for i, timestamp in enumerate(timestamps):
            current_time = datetime.fromtimestamp(timestamp)
            
            # Update portfolio value
            current_portfolio_value = self._calculate_portfolio_value(positions, historical_data, timestamp)
            results.equity_curve.append(current_portfolio_value)
            results.timestamps.append(current_time)
            
            # Process each symbol
            for symbol in config.symbols:
                symbol_data = historical_data.get(symbol, [])
                
                # Find current candle
                current_candle = None
                for candle in symbol_data:
                    if abs(candle.timestamp - timestamp) < 3600:  # Within 1 hour
                        current_candle = candle
                        break
                
                if not current_candle:
                    continue
                
                # Get enough historical data for analysis
                historical_candles = [c for c in symbol_data if c.timestamp <= timestamp][-200:]
                
                if len(historical_candles) < 50:
                    continue
                
                # Create ticker from current candle
                ticker = Ticker(
                    symbol=symbol,
                    price=current_candle.close,
                    bid=current_candle.close - 0.01,
                    ask=current_candle.close + 0.01,
                    volume=current_candle.volume,
                    timestamp=timestamp
                )
                
                # Generate signal
                try:
                    signal = strategy.generate_signal(historical_candles, ticker)
                    
                    if signal.signal != SignalType.HOLD:
                        trade = self._execute_signal(
                            signal, positions, current_portfolio_value, 
                            config, current_time, strategy
                        )
                        if trade:
                            results.trades.append(trade)
                            
                except Exception as e:
                    logger.error(f"Error processing signal for {symbol}: {e}")
        
        # Close remaining positions
        final_timestamp = timestamps[-1] if timestamps else time.time()
        for symbol, position in positions.items():
            if position['quantity'] != 0:
                symbol_data = historical_data.get(symbol, [])
                if symbol_data:
                    exit_price = symbol_data[-1].close
                    trade = self._close_position(
                        symbol, position, exit_price, 
                        datetime.fromtimestamp(final_timestamp),
                        config, strategy.name
                    )
                    if trade:
                        results.trades.append(trade)
        
        # Calculate final metrics
        return self._calculate_results_metrics(results)
    
    def _run_multi_strategy_backtest(self, config: BacktestConfig, results: BacktestResults) -> BacktestResults:
        """Run backtest with multiple strategies"""
        if not config.strategies:
            logger.warning("No strategies provided for multi-strategy backtest")
            return results
        
        # Allocate capital among strategies
        strategy_allocation = {strategy.name: strategy.allocation for strategy in config.strategies}
        total_allocation = sum(strategy_allocation.values())
        
        if total_allocation == 0:
            # Equal allocation if none specified
            allocation_per_strategy = 1.0 / len(config.strategies)
            strategy_allocation = {strategy.name: allocation_per_strategy for strategy in config.strategies}
        else:
            # Normalize allocations
            strategy_allocation = {name: alloc / total_allocation for name, alloc in strategy_allocation.items()}
        
        # Run separate backtest for each strategy
        strategy_results = {}
        
        for strategy in config.strategies:
            strategy_config = BacktestConfig(
                start_date=config.start_date,
                end_date=config.end_date,
                initial_capital=config.initial_capital * strategy_allocation[strategy.name],
                symbols=config.symbols,
                strategies=[strategy],
                commission=config.commission,
                slippage=config.slippage,
                mode=BacktestMode.SINGLE_STRATEGY
            )
            
            strategy_result = self._run_single_strategy_backtest(strategy_config, BacktestResults(config=strategy_config))
            strategy_results[strategy.name] = strategy_result
        
        # Combine results
        return self._combine_strategy_results(strategy_results, results, strategy_allocation)
    
    def _run_walk_forward_backtest(self, config: BacktestConfig, results: BacktestResults) -> BacktestResults:
        """Run walk-forward analysis"""
        total_days = (config.end_date - config.start_date).days
        window_days = max(90, total_days // 4)  # 90 days or 1/4 of total period
        step_days = max(30, window_days // 3)   # 30 days or 1/3 of window
        
        all_trades = []
        equity_curves = []
        
        current_start = config.start_date
        
        while current_start + timedelta(days=window_days) <= config.end_date:
            current_end = current_start + timedelta(days=window_days)
            
            # Create window config
            window_config = BacktestConfig(
                start_date=current_start,
                end_date=current_end,
                initial_capital=config.initial_capital,
                symbols=config.symbols,
                strategies=config.strategies,
                commission=config.commission,
                slippage=config.slippage,
                mode=BacktestMode.SINGLE_STRATEGY
            )
            
            # Run backtest for this window
            window_result = self._run_single_strategy_backtest(window_config, BacktestResults(config=window_config))
            
            all_trades.extend(window_result.trades)
            if window_result.equity_curve:
                equity_curves.extend(window_result.equity_curve)
            
            current_start += timedelta(days=step_days)
        
        # Combine all results
        results.trades = all_trades
        results.equity_curve = equity_curves
        
        return self._calculate_results_metrics(results)
    
    def _run_monte_carlo_backtest(self, config: BacktestConfig, results: BacktestResults) -> BacktestResults:
        """Run Monte Carlo simulation of trades"""
        if not config.strategies:
            return results
        
        # First run normal backtest to get trade distribution
        base_result = self._run_single_strategy_backtest(config, BacktestResults(config=config))
        
        if not base_result.trades:
            return results
        
        # Extract trade returns
        trade_returns = [trade.pnl_percent for trade in base_result.trades if trade.pnl_percent != 0]
        
        if not trade_returns:
            return base_result
        
        # Run Monte Carlo simulations
        num_simulations = 1000
        simulation_results = []
        
        for _ in range(num_simulations):
            # Random sampling of trade returns
            simulated_returns = np.random.choice(trade_returns, size=len(trade_returns), replace=True)
            
            # Calculate cumulative returns
            portfolio_value = config.initial_capital
            equity_curve = [portfolio_value]
            
            for return_pct in simulated_returns:
                portfolio_value *= (1 + return_pct)
                equity_curve.append(portfolio_value)
            
            final_return = (portfolio_value - config.initial_capital) / config.initial_capital
            max_dd = self._calculate_max_drawdown_from_curve(equity_curve)
            
            simulation_results.append({
                'final_return': final_return,
                'max_drawdown': max_dd,
                'equity_curve': equity_curve
            })
        
        # Calculate Monte Carlo statistics
        final_returns = [sim['final_return'] for sim in simulation_results]
        max_drawdowns = [sim['max_drawdown'] for sim in simulation_results]
        
        # Use base result but add Monte Carlo insights
        results = base_result
        results.rolling_metrics['monte_carlo_returns'] = final_returns
        results.rolling_metrics['monte_carlo_drawdowns'] = max_drawdowns
        
        return results
    
    def _get_historical_data(self, symbols: List[str], start_date: datetime, end_date: datetime) -> Dict[str, List[Candle]]:
        """Get historical data for backtesting"""
        historical_data = {}
        
        for symbol in symbols:
            try:
                # Calculate number of periods needed
                days = (end_date - start_date).days
                periods = max(days * 24, 1000)  # Hourly data
                
                candles = self.exchange.get_historical_data(symbol, "1h", periods)
                
                # Filter to date range
                start_timestamp = start_date.timestamp()
                end_timestamp = end_date.timestamp()
                
                filtered_candles = [
                    candle for candle in candles 
                    if start_timestamp <= candle.timestamp <= end_timestamp
                ]
                
                historical_data[symbol] = filtered_candles
                logger.info(f"Loaded {len(filtered_candles)} candles for {symbol}")
                
            except Exception as e:
                logger.error(f"Error loading data for {symbol}: {e}")
        
        return historical_data
    
    def _execute_signal(self, signal: TradingSignal, positions: Dict, portfolio_value: float,
                       config: BacktestConfig, current_time: datetime, 
                       strategy: BaseTradingStrategy) -> Optional[Trade]:
        """Execute trading signal in backtest"""
        symbol = signal.symbol
        current_position = positions.get(symbol, {'quantity': 0, 'entry_price': 0, 'entry_time': None})
        
        # Position sizing
        position_size = strategy.calculate_position_size(signal, portfolio_value)
        trade_value = position_size * signal.price
        
        # Check if we have enough capital
        if trade_value > portfolio_value * 0.95:  # Keep 5% cash buffer
            return None
        
        # Calculate costs
        commission = trade_value * config.commission
        slippage = trade_value * config.slippage
        
        trade = None
        
        if signal.signal == SignalType.BUY and current_position['quantity'] <= 0:
            # Open long position or close short
            quantity = position_size
            
            # Close existing short position first
            if current_position['quantity'] < 0:
                trade = self._close_position(
                    symbol, current_position, signal.price,
                    current_time, config, strategy.name
                )
            
            # Open new long position
            positions[symbol] = {
                'quantity': quantity,
                'entry_price': signal.price,
                'entry_time': current_time,
                'strategy': strategy.name
            }
            
            if not trade:  # Only create trade if we didn't close a position
                trade = Trade(
                    entry_time=current_time,
                    exit_time=None,
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    entry_price=signal.price,
                    exit_price=None,
                    strategy_name=strategy.name,
                    commission=commission,
                    slippage=slippage,
                    signal_strength=signal.strength,
                    metadata=signal.metadata
                )
        
        elif signal.signal == SignalType.SELL and current_position['quantity'] >= 0:
            # Open short position or close long
            quantity = -position_size
            
            # Close existing long position first
            if current_position['quantity'] > 0:
                trade = self._close_position(
                    symbol, current_position, signal.price,
                    current_time, config, strategy.name
                )
            
            # Open new short position
            positions[symbol] = {
                'quantity': quantity,
                'entry_price': signal.price,
                'entry_time': current_time,
                'strategy': strategy.name
            }
            
            if not trade:  # Only create trade if we didn't close a position
                trade = Trade(
                    entry_time=current_time,
                    exit_time=None,
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=abs(quantity),
                    entry_price=signal.price,
                    exit_price=None,
                    strategy_name=strategy.name,
                    commission=commission,
                    slippage=slippage,
                    signal_strength=signal.strength,
                    metadata=signal.metadata
                )
        
        return trade
    
    def _close_position(self, symbol: str, position: Dict, exit_price: float,
                       exit_time: datetime, config: BacktestConfig, strategy_name: str) -> Trade:
        """Close existing position"""
        entry_price = position['entry_price']
        quantity = position['quantity']
        entry_time = position['entry_time']
        
        # Calculate P&L
        if quantity > 0:  # Long position
            pnl = (exit_price - entry_price) * quantity
            side = OrderSide.BUY
        else:  # Short position
            pnl = (entry_price - exit_price) * abs(quantity)
            side = OrderSide.SELL
        
        pnl_percent = pnl / (entry_price * abs(quantity))
        
        # Calculate costs
        trade_value = abs(quantity) * exit_price
        commission = trade_value * config.commission
        slippage = trade_value * config.slippage
        total_costs = commission + slippage
        
        net_pnl = pnl - total_costs
        
        # Calculate duration
        duration_hours = (exit_time - entry_time).total_seconds() / 3600
        
        # Reset position
        position['quantity'] = 0
        position['entry_price'] = 0
        position['entry_time'] = None
        
        return Trade(
            entry_time=entry_time,
            exit_time=exit_time,
            symbol=symbol,
            side=side,
            quantity=abs(quantity),
            entry_price=entry_price,
            exit_price=exit_price,
            strategy_name=strategy_name,
            pnl=net_pnl,
            pnl_percent=pnl_percent,
            commission=commission,
            slippage=slippage,
            duration_hours=duration_hours
        )
    
    def _calculate_portfolio_value(self, positions: Dict, historical_data: Dict, timestamp: float) -> float:
        """Calculate current portfolio value"""
        total_value = 0
        
        for symbol, position in positions.items():
            if position['quantity'] == 0:
                continue
            
            symbol_data = historical_data.get(symbol, [])
            current_price = None
            
            # Find current price
            for candle in symbol_data:
                if abs(candle.timestamp - timestamp) < 3600:  # Within 1 hour
                    current_price = candle.close
                    break
            
            if current_price:
                position_value = position['quantity'] * current_price
                total_value += position_value
        
        return total_value
    
    def _calculate_results_metrics(self, results: BacktestResults) -> BacktestResults:
        """Calculate comprehensive performance metrics"""
        if not results.trades or not results.equity_curve:
            return results
        
        initial_capital = results.config.initial_capital
        final_value = results.equity_curve[-1] if results.equity_curve else initial_capital
        
        # Basic performance
        results.total_return = (final_value - initial_capital) / initial_capital
        
        # Time-based calculations
        total_days = (results.config.end_date - results.config.start_date).days
        years = max(total_days / 365.0, 1/365.0)  # Minimum 1 day
        results.annualized_return = (1 + results.total_return) ** (1/years) - 1
        
        # Trade statistics
        results.total_trades = len(results.trades)
        winning_trades = [t for t in results.trades if t.pnl > 0]
        losing_trades = [t for t in results.trades if t.pnl < 0]
        
        results.winning_trades = len(winning_trades)
        results.losing_trades = len(losing_trades)
        results.win_rate = results.winning_trades / results.total_trades if results.total_trades > 0 else 0
        
        results.avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        results.avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        results.profit_factor = abs(results.avg_win / results.avg_loss) if results.avg_loss != 0 else 0
        
        results.avg_trade_duration = np.mean([t.duration_hours for t in results.trades]) if results.trades else 0
        
        # Risk metrics
        if len(results.equity_curve) > 1:
            returns = np.diff(results.equity_curve) / results.equity_curve[:-1]
            
            results.volatility = np.std(returns) * np.sqrt(252 * 24) if len(returns) > 1 else 0
            results.sharpe_ratio = (results.annualized_return - results.config.risk_free_rate) / results.volatility if results.volatility > 0 else 0
            
            # Sortino ratio (downside deviation)
            downside_returns = returns[returns < 0]
            downside_deviation = np.std(downside_returns) * np.sqrt(252 * 24) if len(downside_returns) > 0 else 0
            results.sortino_ratio = (results.annualized_return - results.config.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
            
            # Drawdown analysis
            results.max_drawdown = self._calculate_max_drawdown_from_curve(results.equity_curve)
            results.calmar_ratio = results.annualized_return / abs(results.max_drawdown) if results.max_drawdown != 0 else 0
            
            # VaR calculations
            results.var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
            results.var_99 = np.percentile(returns, 1) if len(returns) > 0 else 0
            results.cvar_95 = np.mean(returns[returns <= results.var_95]) if len(returns) > 0 else 0
        
        # Monthly/yearly returns
        results.monthly_returns = self._calculate_period_returns(results, 'monthly')
        results.yearly_returns = self._calculate_period_returns(results, 'yearly')
        
        # Strategy performance breakdown
        results.strategy_performance = self._calculate_strategy_performance(results.trades)
        
        return results
    
    def _calculate_max_drawdown_from_curve(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown from equity curve"""
        if len(equity_curve) < 2:
            return 0.0
        
        equity_array = np.array(equity_curve)
        peak = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - peak) / peak
        return float(np.min(drawdown))
    
    def _calculate_period_returns(self, results: BacktestResults, period: str) -> Dict[str, float]:
        """Calculate returns by period (monthly/yearly)"""
        if not results.timestamps or not results.equity_curve:
            return {}
        
        period_returns = {}
        
        # Group by period
        for i, (timestamp, value) in enumerate(zip(results.timestamps, results.equity_curve)):
            if period == 'monthly':
                key = timestamp.strftime('%Y-%m')
            else:  # yearly
                key = str(timestamp.year)
            
            if key not in period_returns:
                period_returns[key] = {'start': value, 'end': value}
            else:
                period_returns[key]['end'] = value
        
        # Calculate returns
        return {
            period: (data['end'] - data['start']) / data['start']
            for period, data in period_returns.items()
            if data['start'] > 0
        }
    
    def _calculate_strategy_performance(self, trades: List[Trade]) -> Dict[str, Dict[str, float]]:
        """Calculate performance metrics by strategy"""
        if not trades:
            return {}
        
        strategy_trades = {}
        for trade in trades:
            if trade.strategy_name not in strategy_trades:
                strategy_trades[trade.strategy_name] = []
            strategy_trades[trade.strategy_name].append(trade)
        
        strategy_performance = {}
        for strategy_name, strategy_trade_list in strategy_trades.items():
            winning_trades = [t for t in strategy_trade_list if t.pnl > 0]
            losing_trades = [t for t in strategy_trade_list if t.pnl < 0]
            
            total_pnl = sum(t.pnl for t in strategy_trade_list)
            total_trades = len(strategy_trade_list)
            
            strategy_performance[strategy_name] = {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / total_trades if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'avg_win': np.mean([t.pnl for t in winning_trades]) if winning_trades else 0,
                'avg_loss': np.mean([t.pnl for t in losing_trades]) if losing_trades else 0,
                'avg_trade_return': total_pnl / total_trades if total_trades > 0 else 0
            }
        
        return strategy_performance
    
    def _combine_strategy_results(self, strategy_results: Dict[str, BacktestResults], 
                                combined_results: BacktestResults, 
                                allocations: Dict[str, float]) -> BacktestResults:
        """Combine multiple strategy results"""
        
        # Combine trades from all strategies
        all_trades = []
        for strategy_name, result in strategy_results.items():
            for trade in result.trades:
                # Scale trade P&L by allocation
                scaled_trade = Trade(
                    entry_time=trade.entry_time,
                    exit_time=trade.exit_time,
                    symbol=trade.symbol,
                    side=trade.side,
                    quantity=trade.quantity * allocations[strategy_name],
                    entry_price=trade.entry_price,
                    exit_price=trade.exit_price,
                    strategy_name=trade.strategy_name,
                    pnl=trade.pnl * allocations[strategy_name],
                    pnl_percent=trade.pnl_percent,
                    commission=trade.commission * allocations[strategy_name],
                    slippage=trade.slippage * allocations[strategy_name],
                    duration_hours=trade.duration_hours,
                    signal_strength=trade.signal_strength,
                    metadata=trade.metadata
                )
                all_trades.append(scaled_trade)
        
        combined_results.trades = sorted(all_trades, key=lambda t: t.entry_time)
        
        # Combine equity curves (weighted by allocation)
        max_length = max(len(result.equity_curve) for result in strategy_results.values() if result.equity_curve)
        combined_equity_curve = [0] * max_length
        
        for strategy_name, result in strategy_results.items():
            allocation = allocations[strategy_name]
            for i, value in enumerate(result.equity_curve):
                if i < len(combined_equity_curve):
                    combined_equity_curve[i] += value * allocation
        
        combined_results.equity_curve = combined_equity_curve
        
        # Use timestamps from the first strategy
        first_result = next(iter(strategy_results.values()))
        combined_results.timestamps = first_result.timestamps
        
        # Calculate combined metrics
        return self._calculate_results_metrics(combined_results)