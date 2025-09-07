"""
Portfolio Analytics and Optimization Service
Advanced analytics and optimization tools for the SirHiss trading platform
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from dataclasses import dataclass
import logging

from ..models.trading import TradingBot, BotExecution, Holdings, StrategyPerformance, RiskMetrics
from ..models.portfolio import Portfolio
from ..models.user import User
from ..core.database import get_db

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """Result of portfolio optimization"""
    strategy_allocation: Dict[str, float]
    risk_parameters: Dict[str, float]
    expected_return: float
    expected_risk: float
    confidence_score: float
    recommendations: List[str]

class PerformanceCalculator:
    """Calculate comprehensive performance metrics"""
    
    @staticmethod
    def calculate_returns(prices: List[float]) -> np.ndarray:
        """Calculate returns from price series"""
        if len(prices) < 2:
            return np.array([])
        return np.diff(prices) / prices[:-1]
    
    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return 0.0
        
        downside_deviation = np.std(downside_returns)
        if downside_deviation == 0:
            return 0.0
        
        return np.mean(excess_returns) / downside_deviation * np.sqrt(252)
    
    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> Tuple[float, datetime, datetime]:
        """Calculate maximum drawdown and its duration"""
        if len(prices) < 2:
            return 0.0, None, None
        
        prices_array = np.array(prices)
        peak = np.maximum.accumulate(prices_array)
        drawdown = (prices_array - peak) / peak
        
        max_drawdown_value = np.min(drawdown)
        max_dd_end_idx = np.argmin(drawdown)
        
        # Find start of drawdown period
        max_dd_start_idx = 0
        for i in range(max_dd_end_idx, -1, -1):
            if drawdown[i] == 0:
                max_dd_start_idx = i
                break
        
        return abs(max_drawdown_value), max_dd_start_idx, max_dd_end_idx
    
    @staticmethod
    def calculate_calmar_ratio(returns: np.ndarray, max_drawdown: float) -> float:
        """Calculate Calmar ratio"""
        if max_drawdown == 0 or len(returns) == 0:
            return 0.0
        annual_return = np.mean(returns) * 252
        return annual_return / abs(max_drawdown)
    
    @staticmethod
    def calculate_var(returns: np.ndarray, confidence_level: float = 0.05) -> float:
        """Calculate Value at Risk"""
        if len(returns) == 0:
            return 0.0
        return np.percentile(returns, confidence_level * 100)

class PortfolioAnalyzer:
    """Comprehensive portfolio analysis"""
    
    def __init__(self, db: Session):
        self.db = db
        self.calculator = PerformanceCalculator()
    
    def get_portfolio_data(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Get comprehensive portfolio data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user's bots and executions
        bots = self.db.query(TradingBot).filter(TradingBot.user_id == user_id).all()
        bot_ids = [bot.id for bot in bots]
        
        # Get executions in date range
        executions = self.db.query(BotExecution).filter(
            BotExecution.bot_id.in_(bot_ids),
            BotExecution.timestamp >= cutoff_date
        ).order_by(BotExecution.timestamp).all()
        
        # Get current holdings
        holdings = self.db.query(Holdings).filter(
            Holdings.bot_id.in_(bot_ids)
        ).all()
        
        return {
            'bots': bots,
            'executions': executions,
            'holdings': holdings,
            'analysis_period_days': days
        }
    
    def calculate_portfolio_metrics(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Calculate comprehensive portfolio metrics"""
        data = self.get_portfolio_data(user_id, days)
        executions = data['executions']
        
        if not executions:
            return {}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([{
            'timestamp': exec.timestamp,
            'symbol': exec.symbol,
            'side': exec.side.value,
            'quantity': exec.quantity,
            'price': exec.price,
            'total_value': exec.total_value,
            'strategy_name': exec.strategy_name,
            'bot_id': exec.bot_id,
            'pnl': (exec.price - exec.execution_price) * exec.quantity if exec.execution_price else 0
        } for exec in executions])
        
        # Calculate basic metrics
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        
        # P&L analysis
        total_pnl = df['pnl'].sum()
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # Risk metrics
        returns = df['pnl'].values
        sharpe_ratio = self.calculator.calculate_sharpe_ratio(returns)
        sortino_ratio = self.calculator.calculate_sortino_ratio(returns)
        
        # Portfolio value series (simplified)
        portfolio_values = np.cumsum(returns) + 10000  # Assume $10k starting value
        max_drawdown, dd_start, dd_end = self.calculator.calculate_max_drawdown(portfolio_values.tolist())
        
        var_95 = self.calculator.calculate_var(returns, 0.05)
        var_99 = self.calculator.calculate_var(returns, 0.01)
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'var_99': var_99,
            'calmar_ratio': self.calculator.calculate_calmar_ratio(returns, max_drawdown),
            'portfolio_values': portfolio_values.tolist(),
            'analysis_period': days
        }
    
    def analyze_by_strategy(self, user_id: int, days: int = 90) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by strategy"""
        data = self.get_portfolio_data(user_id, days)
        executions = data['executions']
        
        if not executions:
            return {}
        
        # Group by strategy
        strategy_analysis = {}
        executions_by_strategy = {}
        
        for exec in executions:
            strategy = exec.strategy_name
            if strategy not in executions_by_strategy:
                executions_by_strategy[strategy] = []
            executions_by_strategy[strategy].append(exec)
        
        # Analyze each strategy
        for strategy, strategy_executions in executions_by_strategy.items():
            df = pd.DataFrame([{
                'timestamp': exec.timestamp,
                'pnl': (exec.price - exec.execution_price) * exec.quantity if exec.execution_price else 0,
                'total_value': exec.total_value
            } for exec in strategy_executions])
            
            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            returns = df['pnl'].values
            
            strategy_analysis[strategy] = {
                'total_trades': total_trades,
                'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
                'total_pnl': df['pnl'].sum(),
                'sharpe_ratio': self.calculator.calculate_sharpe_ratio(returns),
                'avg_trade_return': df['pnl'].mean(),
                'volatility': df['pnl'].std(),
                'best_trade': df['pnl'].max(),
                'worst_trade': df['pnl'].min()
            }
        
        return strategy_analysis
    
    def analyze_by_symbol(self, user_id: int, days: int = 90) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by trading symbol"""
        data = self.get_portfolio_data(user_id, days)
        executions = data['executions']
        
        if not executions:
            return {}
        
        symbol_analysis = {}
        executions_by_symbol = {}
        
        for exec in executions:
            symbol = exec.symbol
            if symbol not in executions_by_symbol:
                executions_by_symbol[symbol] = []
            executions_by_symbol[symbol].append(exec)
        
        for symbol, symbol_executions in executions_by_symbol.items():
            df = pd.DataFrame([{
                'pnl': (exec.price - exec.execution_price) * exec.quantity if exec.execution_price else 0,
                'side': exec.side.value
            } for exec in symbol_executions])
            
            total_trades = len(df)
            buy_trades = len(df[df['side'] == 'buy'])
            sell_trades = len(df[df['side'] == 'sell'])
            
            symbol_analysis[symbol] = {
                'total_trades': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades,
                'total_pnl': df['pnl'].sum(),
                'avg_trade_pnl': df['pnl'].mean(),
                'win_rate': len(df[df['pnl'] > 0]) / total_trades if total_trades > 0 else 0
            }
        
        return symbol_analysis

class PortfolioOptimizer:
    """Advanced portfolio optimization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analyzer = PortfolioAnalyzer(db)
    
    def optimize_strategy_allocation(self, user_id: int, days: int = 90) -> Dict[str, float]:
        """Optimize strategy allocation using risk-adjusted returns"""
        strategy_analysis = self.analyzer.analyze_by_strategy(user_id, days)
        
        if not strategy_analysis:
            return {}
        
        # Calculate scores for each strategy
        strategy_scores = {}
        
        for strategy, metrics in strategy_analysis.items():
            # Risk-adjusted score combining multiple factors
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            win_rate = metrics.get('win_rate', 0)
            total_trades = metrics.get('total_trades', 0)
            
            # Penalize strategies with too few trades
            trade_confidence = min(total_trades / 10, 1.0)
            
            # Combined score
            score = (
                sharpe_ratio * 0.4 +
                win_rate * 0.3 +
                trade_confidence * 0.3
            )
            
            strategy_scores[strategy] = max(score, 0.05)  # Minimum allocation
        
        # Normalize to sum to 1.0
        total_score = sum(strategy_scores.values())
        if total_score > 0:
            return {strategy: score / total_score for strategy, score in strategy_scores.items()}
        
        return {}
    
    def calculate_optimal_risk_parameters(self, user_id: int, days: int = 90) -> Dict[str, float]:
        """Calculate optimal risk parameters using Kelly Criterion and volatility analysis"""
        portfolio_metrics = self.analyzer.calculate_portfolio_metrics(user_id, days)
        
        if not portfolio_metrics:
            return {}
        
        suggestions = {}
        
        # Kelly Criterion for position sizing
        win_rate = portfolio_metrics.get('win_rate', 0.5)
        avg_win = abs(portfolio_metrics.get('avg_win', 0.02))
        avg_loss = abs(portfolio_metrics.get('avg_loss', 0.015))
        
        if avg_loss > 0:
            # Kelly fraction
            kelly_f = (win_rate * avg_win / avg_loss - (1 - win_rate)) / avg_win
            # Use fractional Kelly (25% of full Kelly for safety)
            optimal_position_size = max(0.05, min(kelly_f * 0.25, 0.20))
            suggestions['max_position_size'] = round(optimal_position_size, 3)
        
        # Portfolio risk based on volatility targeting
        returns = portfolio_metrics.get('portfolio_values', [])
        if len(returns) > 1:
            price_returns = self.analyzer.calculator.calculate_returns(returns)
            volatility = np.std(price_returns) if len(price_returns) > 0 else 0.02
            
            # Target 15% annual volatility
            target_vol = 0.15 / np.sqrt(252)
            vol_scaling = target_vol / max(volatility, 0.001)
            
            optimal_portfolio_risk = max(0.1, min(vol_scaling * 0.2, 0.4))
            suggestions['max_portfolio_risk'] = round(optimal_portfolio_risk, 3)
        
        # Stop loss based on VaR
        var_95 = abs(portfolio_metrics.get('var_95', 0.02))
        optimal_stop_loss = max(0.03, min(var_95 * 2, 0.15))
        suggestions['stop_loss_percent'] = round(optimal_stop_loss, 3)
        
        # Take profit based on average win
        if avg_win > 0:
            optimal_take_profit = max(0.05, min(avg_win * 1.5, 0.25))
            suggestions['take_profit_percent'] = round(optimal_take_profit, 3)
        
        return suggestions
    
    def generate_rebalancing_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Generate portfolio rebalancing recommendations"""
        # Get current allocation
        bots = self.db.query(TradingBot).filter(TradingBot.user_id == user_id).all()
        
        current_allocation = {}
        total_allocated = 0
        
        for bot in bots:
            allocation = float(bot.allocated_percentage)
            current_allocation[bot.name] = allocation
            total_allocated += allocation
        
        # Get optimal allocation
        optimal_allocation = self.optimize_strategy_allocation(user_id)
        
        recommendations = {
            'current_allocation': current_allocation,
            'optimal_allocation': optimal_allocation,
            'rebalancing_needed': False,
            'changes': {},
            'total_allocated': total_allocated,
            'unallocated': 100.0 - total_allocated
        }
        
        # Compare current vs optimal
        if optimal_allocation:
            for strategy, optimal_weight in optimal_allocation.items():
                current_weight = current_allocation.get(strategy, 0)
                difference = optimal_weight * 100 - current_weight
                
                if abs(difference) > 5:  # 5% threshold
                    recommendations['rebalancing_needed'] = True
                    recommendations['changes'][strategy] = {
                        'current': current_weight,
                        'recommended': optimal_weight * 100,
                        'change': difference
                    }
        
        return recommendations
    
    def optimize_portfolio(self, user_id: int, days: int = 90) -> OptimizationResult:
        """Comprehensive portfolio optimization"""
        try:
            # Get optimized allocations and parameters
            strategy_allocation = self.optimize_strategy_allocation(user_id, days)
            risk_parameters = self.calculate_optimal_risk_parameters(user_id, days)
            
            # Calculate expected metrics
            portfolio_metrics = self.analyzer.calculate_portfolio_metrics(user_id, days)
            
            expected_return = 0.0
            expected_risk = 0.0
            confidence_score = 0.0
            recommendations = []
            
            if portfolio_metrics:
                # Estimate expected return based on historical performance
                total_pnl = portfolio_metrics.get('total_pnl', 0)
                total_trades = portfolio_metrics.get('total_trades', 1)
                avg_return_per_trade = total_pnl / total_trades if total_trades > 0 else 0
                
                expected_return = avg_return_per_trade * 252  # Annualized
                expected_risk = portfolio_metrics.get('max_drawdown', 0.1)
                
                # Confidence based on data quality
                confidence_score = min(total_trades / 100, 1.0) * 0.7 + \
                                 min(days / 90, 1.0) * 0.3
                
                # Generate recommendations
                sharpe = portfolio_metrics.get('sharpe_ratio', 0)
                win_rate = portfolio_metrics.get('win_rate', 0)
                
                if sharpe < 1.0:
                    recommendations.append("Consider improving strategy selection or risk management")
                if win_rate < 0.5:
                    recommendations.append("Focus on strategies with higher win rates")
                if expected_risk > 0.2:
                    recommendations.append("Reduce position sizes to lower portfolio risk")
                
                if len(strategy_allocation) < 2:
                    recommendations.append("Diversify across multiple trading strategies")
            
            return OptimizationResult(
                strategy_allocation=strategy_allocation,
                risk_parameters=risk_parameters,
                expected_return=expected_return,
                expected_risk=expected_risk,
                confidence_score=confidence_score,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            return OptimizationResult(
                strategy_allocation={},
                risk_parameters={},
                expected_return=0.0,
                expected_risk=0.0,
                confidence_score=0.0,
                recommendations=["Insufficient data for optimization"]
            )

class RiskMonitor:
    """Real-time risk monitoring and alerting"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_current_risk_metrics(self, user_id: int) -> Dict[str, Any]:
        """Calculate current risk metrics for user's portfolio"""
        # Get current holdings and portfolio value
        bots = self.db.query(TradingBot).filter(TradingBot.user_id == user_id).all()
        bot_ids = [bot.id for bot in bots]
        
        holdings = self.db.query(Holdings).filter(Holdings.bot_id.in_(bot_ids)).all()
        
        total_exposure = sum(holding.market_value for holding in holdings)
        portfolio_value = sum(bot.current_value or 0 for bot in bots)
        
        # Calculate concentration risk
        position_concentrations = {}
        sector_concentrations = {}
        
        for holding in holdings:
            symbol = holding.symbol
            position_size = holding.market_value / portfolio_value if portfolio_value > 0 else 0
            position_concentrations[symbol] = position_size
            
            # Mock sector classification (would use real data in production)
            if symbol in ['AAPL', 'MSFT', 'GOOGL']:
                sector = 'Technology'
            elif symbol in ['JPM', 'BAC', 'WFC']:
                sector = 'Financial'
            else:
                sector = 'Other'
            
            sector_concentrations[sector] = sector_concentrations.get(sector, 0) + position_size
        
        # Risk alerts
        alerts = []
        
        # Position concentration alerts
        for symbol, concentration in position_concentrations.items():
            if concentration > 0.15:  # 15% concentration limit
                alerts.append(f"High concentration in {symbol}: {concentration:.1%}")
        
        # Sector concentration alerts
        for sector, concentration in sector_concentrations.items():
            if concentration > 0.4:  # 40% sector limit
                alerts.append(f"High sector concentration in {sector}: {concentration:.1%}")
        
        return {
            'total_exposure': total_exposure,
            'portfolio_value': portfolio_value,
            'exposure_ratio': total_exposure / portfolio_value if portfolio_value > 0 else 0,
            'position_concentrations': position_concentrations,
            'sector_concentrations': sector_concentrations,
            'alerts': alerts,
            'risk_score': self._calculate_risk_score(position_concentrations, sector_concentrations)
        }
    
    def _calculate_risk_score(self, position_concentrations: Dict[str, float], 
                            sector_concentrations: Dict[str, float]) -> str:
        """Calculate overall risk score"""
        max_position_concentration = max(position_concentrations.values()) if position_concentrations else 0
        max_sector_concentration = max(sector_concentrations.values()) if sector_concentrations else 0
        
        if max_position_concentration > 0.25 or max_sector_concentration > 0.6:
            return "HIGH"
        elif max_position_concentration > 0.15 or max_sector_concentration > 0.4:
            return "MEDIUM"
        else:
            return "LOW"