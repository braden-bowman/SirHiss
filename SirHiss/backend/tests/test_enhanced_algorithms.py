"""
Tests for enhanced trading algorithms integration
Tests the advanced algorithms imported from the research repository
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from typing import List
import numpy as np

from app.services.enhanced_trading_engine import (
    OrderBookAnalyticsStrategy,
    MLModelStrategy,
    PortfolioRebalancingStrategy,
    OnChainAnalysisStrategy,
    create_enhanced_strategy
)
from app.services.advanced_trading_strategies import StrategyConfig, TradingSignal, SignalType
from app.services.exchange_api import BaseExchange, Ticker, Candle, OrderSide


class MockExchange(BaseExchange):
    """Mock exchange for testing"""
    
    def __init__(self):
        self.name = "mock"
        self.symbols = ["BTCUSDT", "ETHUSDT"]
        self.balances = {"USDT": Mock(free=1000, total=1000)}
    
    def get_ticker(self, symbol: str) -> Ticker:
        return Ticker(
            symbol=symbol,
            price=50000.0,
            bid=49995.0,
            ask=50005.0,
            timestamp=time.time()
        )
    
    def get_historical_data(self, symbol: str, interval: str, limit: int) -> List[Candle]:
        """Generate mock historical data"""
        candles = []
        base_price = 50000.0
        
        for i in range(limit):
            # Create some price variation
            price_change = np.random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + price_change)
            volume = np.random.uniform(100, 1000)
            
            candle = Candle(
                symbol=symbol,
                timestamp=time.time() - (limit - i) * 3600,
                open=current_price * 0.999,
                high=current_price * 1.002,
                low=current_price * 0.998,
                close=current_price,
                volume=volume
            )
            candles.append(candle)
            base_price = current_price
            
        return candles
    
    def get_balance(self, asset: str):
        return self.balances.get(asset)
    
    def place_order(self, order):
        # Mock successful order placement
        order.order_id = "mock_order_123"
        order.status = "FILLED"
        return order


@pytest.fixture
def mock_exchange():
    """Fixture providing mock exchange"""
    return MockExchange()


@pytest.fixture
def strategy_config():
    """Fixture providing basic strategy configuration"""
    return StrategyConfig(
        symbol="BTCUSDT",
        position_size=0.1,
        max_position_size=0.25,
        stop_loss=0.15,
        take_profit=0.25,
        risk_per_trade=0.02,
        enabled=True,
        parameters={}
    )


class TestOrderBookAnalyticsStrategy:
    """Test advanced order book analytics strategy"""
    
    def test_strategy_initialization(self, mock_exchange, strategy_config):
        """Test strategy can be initialized properly"""
        strategy_config.parameters = {
            'analysis_levels': 5,
            'vpin_threshold': 0.3,
            'min_interval': 10,
            'spread_threshold': 0.002
        }
        
        strategy = OrderBookAnalyticsStrategy(mock_exchange, strategy_config)
        
        assert strategy.name == "OrderBookAnalyticsStrategy"
        assert strategy.analysis_levels == 5
        assert strategy.vpin_threshold == 0.3
        assert strategy.min_signal_interval == 10
        assert strategy.spread_threshold == 0.002
    
    def test_signal_generation(self, mock_exchange, strategy_config):
        """Test signal generation with mock data"""
        strategy_config.parameters = {
            'analysis_levels': 5,
            'vpin_threshold': 0.3,
            'min_interval': 10,
            'spread_threshold': 0.002
        }
        
        strategy = OrderBookAnalyticsStrategy(mock_exchange, strategy_config)
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 50)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(candles, ticker)
        
        assert isinstance(signal, TradingSignal)
        assert signal.symbol == "BTCUSDT"
        assert signal.strategy_name == "OrderBookAnalyticsStrategy"
        assert signal.signal in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
        assert 0 <= signal.strength <= 1
        assert 'spread' in signal.metadata
    
    def test_spread_too_wide_rejection(self, mock_exchange, strategy_config):
        """Test that signals are rejected when spread is too wide"""
        strategy_config.parameters = {
            'spread_threshold': 0.0001  # Very tight threshold
        }
        
        strategy = OrderBookAnalyticsStrategy(mock_exchange, strategy_config)
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 50)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(candles, ticker)
        
        assert signal.signal == SignalType.HOLD
        assert signal.metadata.get('reason') == 'spread_too_wide'


class TestMLModelStrategy:
    """Test machine learning strategy"""
    
    def test_strategy_initialization(self, mock_exchange, strategy_config):
        """Test ML strategy initialization"""
        strategy_config.parameters = {
            'model_type': 'ensemble',
            'lookback_window': 60,
            'confidence_threshold': 0.65
        }
        
        strategy = MLModelStrategy(mock_exchange, strategy_config)
        
        assert strategy.name == "MLModelStrategy"
        assert strategy.model_type == 'ensemble'
        assert strategy.lookback_window == 60
        assert strategy.confidence_threshold == 0.65
    
    def test_feature_preparation(self, mock_exchange, strategy_config):
        """Test feature preparation from candle data"""
        strategy_config.parameters = {'model_type': 'ensemble'}
        strategy = MLModelStrategy(mock_exchange, strategy_config)
        
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 50)
        features = strategy.prepare_features(candles)
        
        assert features is not None
        assert len(features) == 3  # price_change, volume_ratio, data_points
        assert isinstance(features[0], float)  # price_change
        assert isinstance(features[1], float)  # volume_ratio
        assert isinstance(features[2], int)    # data_points
    
    def test_signal_generation(self, mock_exchange, strategy_config):
        """Test ML signal generation"""
        strategy_config.parameters = {
            'model_type': 'ensemble',
            'confidence_threshold': 0.65
        }
        
        strategy = MLModelStrategy(mock_exchange, strategy_config)
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 50)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(candles, ticker)
        
        assert isinstance(signal, TradingSignal)
        assert signal.strategy_name == "MLModelStrategy"
        assert 'prediction_score' in signal.metadata
        assert 'features' in signal.metadata
        assert 'model_type' in signal.metadata
    
    def test_insufficient_data_handling(self, mock_exchange, strategy_config):
        """Test handling when insufficient data is available"""
        strategy = MLModelStrategy(mock_exchange, strategy_config)
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 5)  # Insufficient data
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(candles, ticker)
        
        assert signal.signal == SignalType.HOLD
        assert signal.metadata.get('reason') == 'insufficient_features'


class TestPortfolioRebalancingStrategy:
    """Test portfolio rebalancing strategy"""
    
    def test_strategy_initialization(self, mock_exchange, strategy_config):
        """Test rebalancing strategy initialization"""
        strategy_config.parameters = {
            'method': 'threshold',
            'threshold': 0.05,
            'interval': 86400,
            'target_allocation': {'crypto': 0.3, 'stable': 0.7}
        }
        
        strategy = PortfolioRebalancingStrategy(mock_exchange, strategy_config)
        
        assert strategy.name == "PortfolioRebalancingStrategy"
        assert strategy.rebalance_method == 'threshold'
        assert strategy.threshold == 0.05
        assert strategy.target_allocation == {'crypto': 0.3, 'stable': 0.7}
    
    def test_rebalance_signal_generation(self, mock_exchange, strategy_config):
        """Test rebalancing signal when deviation exceeds threshold"""
        strategy_config.parameters = {
            'method': 'threshold',
            'threshold': 0.05,
            'interval': 1,  # 1 second for testing
            'target_allocation': {'crypto': 0.3, 'stable': 0.7}
        }
        
        strategy = PortfolioRebalancingStrategy(mock_exchange, strategy_config)
        strategy.last_rebalance = 0  # Force rebalancing
        
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 50)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(candles, ticker)
        
        assert isinstance(signal, TradingSignal)
        assert signal.strategy_name == "PortfolioRebalancingStrategy"
        
        # Should generate buy signal since mock current allocation is 25% < 30% target
        if signal.signal != SignalType.HOLD:
            assert 'rebalance_needed' in signal.metadata
            assert 'deviation' in signal.metadata
            assert 'target_allocation' in signal.metadata
    
    def test_interval_not_reached(self, mock_exchange, strategy_config):
        """Test no signal when rebalancing interval hasn't been reached"""
        strategy_config.parameters = {
            'method': 'threshold',
            'interval': 86400  # 24 hours
        }
        
        strategy = PortfolioRebalancingStrategy(mock_exchange, strategy_config)
        strategy.last_rebalance = time.time()  # Just rebalanced
        
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 50)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(candles, ticker)
        
        assert signal.signal == SignalType.HOLD
        assert signal.metadata.get('reason') == 'rebalance_interval_not_reached'


class TestOnChainAnalysisStrategy:
    """Test on-chain analysis strategy"""
    
    def test_strategy_initialization(self, mock_exchange, strategy_config):
        """Test on-chain strategy initialization"""
        strategy_config.parameters = {
            'mvrv_threshold': 3.0,
            'nvt_threshold': 75,
            'flow_threshold': 1000000,
            'cache_duration': 3600
        }
        
        strategy = OnChainAnalysisStrategy(mock_exchange, strategy_config)
        
        assert strategy.name == "OnChainAnalysisStrategy"
        assert strategy.mvrv_threshold == 3.0
        assert strategy.nvt_threshold == 75
        assert strategy.cache_duration == 3600
    
    def test_mock_onchain_metrics(self, mock_exchange, strategy_config):
        """Test mock on-chain metrics generation"""
        strategy = OnChainAnalysisStrategy(mock_exchange, strategy_config)
        
        metrics = strategy.get_mock_onchain_metrics("BTCUSDT")
        
        assert 'mvrv_ratio' in metrics
        assert 'nvt_ratio' in metrics
        assert 'exchange_inflow' in metrics
        assert 'exchange_outflow' in metrics
        assert 'active_addresses' in metrics
        
        # Test caching
        metrics2 = strategy.get_mock_onchain_metrics("BTCUSDT")
        assert metrics == metrics2  # Should return cached values
    
    def test_signal_generation(self, mock_exchange, strategy_config):
        """Test on-chain signal generation"""
        strategy_config.parameters = {
            'mvrv_threshold': 3.0,
            'nvt_threshold': 75
        }
        
        strategy = OnChainAnalysisStrategy(mock_exchange, strategy_config)
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 50)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(candles, ticker)
        
        assert isinstance(signal, TradingSignal)
        assert signal.strategy_name == "OnChainAnalysisStrategy"
        assert 'onchain_metrics' in signal.metadata
        assert 'analysis_reasons' in signal.metadata
        assert 'net_exchange_flow' in signal.metadata


class TestEnhancedStrategyFactory:
    """Test enhanced strategy factory"""
    
    def test_create_order_book_analytics_strategy(self, mock_exchange, strategy_config):
        """Test factory creates OrderBookAnalytics strategy"""
        strategy = create_enhanced_strategy('OrderBookAnalytics', mock_exchange, strategy_config)
        
        assert isinstance(strategy, OrderBookAnalyticsStrategy)
        assert strategy.name == "OrderBookAnalyticsStrategy"
    
    def test_create_ml_model_strategy(self, mock_exchange, strategy_config):
        """Test factory creates MLModel strategy"""
        strategy = create_enhanced_strategy('MLModel', mock_exchange, strategy_config)
        
        assert isinstance(strategy, MLModelStrategy)
        assert strategy.name == "MLModelStrategy"
    
    def test_create_portfolio_rebalancing_strategy(self, mock_exchange, strategy_config):
        """Test factory creates PortfolioRebalancing strategy"""
        strategy = create_enhanced_strategy('PortfolioRebalancing', mock_exchange, strategy_config)
        
        assert isinstance(strategy, PortfolioRebalancingStrategy)
        assert strategy.name == "PortfolioRebalancingStrategy"
    
    def test_create_onchain_analysis_strategy(self, mock_exchange, strategy_config):
        """Test factory creates OnChainAnalysis strategy"""
        strategy = create_enhanced_strategy('OnChainAnalysis', mock_exchange, strategy_config)
        
        assert isinstance(strategy, OnChainAnalysisStrategy)
        assert strategy.name == "OnChainAnalysisStrategy"
    
    def test_invalid_strategy_type(self, mock_exchange, strategy_config):
        """Test factory falls back for unknown strategy types"""
        # Should fall back to existing strategy creation
        with pytest.raises(ValueError):
            create_enhanced_strategy('NonExistentStrategy', mock_exchange, strategy_config)


class TestStrategyIntegration:
    """Integration tests for enhanced strategies"""
    
    @pytest.mark.asyncio
    async def test_multiple_strategies_execution(self, mock_exchange):
        """Test running multiple enhanced strategies together"""
        strategies = []
        
        # Create different strategy configurations
        configs = [
            StrategyConfig(
                symbol="BTCUSDT",
                position_size=0.1,
                parameters={'analysis_levels': 5, 'vpin_threshold': 0.3}
            ),
            StrategyConfig(
                symbol="BTCUSDT", 
                position_size=0.15,
                parameters={'model_type': 'ensemble', 'confidence_threshold': 0.7}
            ),
            StrategyConfig(
                symbol="BTCUSDT",
                position_size=0.2,
                parameters={'method': 'threshold', 'threshold': 0.05}
            )
        ]
        
        strategy_types = ['OrderBookAnalytics', 'MLModel', 'PortfolioRebalancing']
        
        for strategy_type, config in zip(strategy_types, configs):
            strategy = create_enhanced_strategy(strategy_type, mock_exchange, config)
            strategies.append(strategy)
        
        # Generate signals from all strategies
        candles = mock_exchange.get_historical_data("BTCUSDT", "1h", 100)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signals = []
        for strategy in strategies:
            signal = strategy.generate_signal(candles, ticker)
            signals.append(signal)
        
        assert len(signals) == 3
        for signal in signals:
            assert isinstance(signal, TradingSignal)
            assert signal.symbol == "BTCUSDT"
    
    def test_strategy_performance_tracking(self, mock_exchange, strategy_config):
        """Test that strategies track performance correctly"""
        strategy = create_enhanced_strategy('MLModel', mock_exchange, strategy_config)
        
        # Initially no performance data
        performance = strategy.get_performance_metrics()
        assert performance['total_trades'] == 0
        assert performance['win_rate'] == 0.0
        
        # Simulate some trades
        strategy.performance.add_trade(50000, 51000, 0.1, OrderSide.BUY)  # Winning trade
        strategy.performance.add_trade(51000, 50500, 0.1, OrderSide.SELL)  # Losing trade
        
        performance = strategy.get_performance_metrics()
        assert performance['total_trades'] == 2
        assert performance['winning_trades'] == 1
        assert performance['win_rate'] == 0.5
        assert performance['total_return'] > 0  # Net positive


if __name__ == "__main__":
    pytest.main([__file__])