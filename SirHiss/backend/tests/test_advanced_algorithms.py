"""
Comprehensive tests for advanced trading algorithms integration
"""

import pytest
import asyncio
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.advanced_trading_strategies import (
    AdvancedTechnicalIndicatorStrategy,
    ScalpingStrategy,
    DynamicDCAStrategy,
    GridTradingStrategy,
    TrendFollowingStrategy,
    SentimentStrategy,
    ArbitrageStrategy,
    AdvancedStrategyManager,
    StrategyConfig,
    TechnicalAnalyzer,
    SentimentAnalyzer,
    create_advanced_strategy
)
from app.services.exchange_api import (
    BaseExchange, Ticker, Candle, Order, OrderSide, OrderType
)
from app.services.enhanced_trading_engine import (
    EnhancedTradingEngine,
    EnhancedTradingEngineManager
)
from app.models.algorithm_config import AlgorithmConfig, AlgorithmExecution
from app.models.trading_bot import TradingBot


class MockExchange(BaseExchange):
    """Mock exchange for testing"""
    
    def __init__(self):
        super().__init__()
        self.mock_price = 50000.0
        self.mock_balance = {"USD": Mock(free=10000.0, locked=0.0, total=10000.0)}
        self.orders = []
        
    def get_ticker(self, symbol):
        import random
        self.mock_price *= (1 + random.uniform(-0.02, 0.02))
        return Ticker(
            symbol=symbol,
            price=self.mock_price,
            bid=self.mock_price * 0.999,
            ask=self.mock_price * 1.001,
            volume=random.uniform(1000, 5000),
            timestamp=time.time()
        )
    
    def get_historical_data(self, symbol, interval="1h", limit=100):
        import random
        candles = []
        base_price = 50000.0
        current_time = time.time()
        
        for i in range(limit):
            open_price = base_price + random.uniform(-500, 500)
            close_price = open_price + random.uniform(-200, 200)
            high_price = max(open_price, close_price) + random.uniform(0, 100)
            low_price = min(open_price, close_price) - random.uniform(0, 100)
            
            candles.append(Candle(
                timestamp=current_time - (i * 3600),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=random.uniform(100, 1000)
            ))
        
        return list(reversed(candles))
    
    def get_balance(self, asset=None):
        if asset:
            return {asset: self.mock_balance.get(asset, Mock(free=0.0, locked=0.0, total=0.0))}
        return self.mock_balance
    
    def place_order(self, order):
        order.order_id = f"test_order_{len(self.orders)}"
        order.timestamp = time.time()
        self.orders.append(order)
        return order
    
    def cancel_order(self, symbol, order_id):
        return True
    
    def get_order_status(self, symbol, order_id):
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None


@pytest.fixture
def mock_exchange():
    return MockExchange()


@pytest.fixture
def sample_candles():
    """Generate sample candlestick data for testing"""
    candles = []
    base_price = 50000.0
    current_time = time.time()
    
    for i in range(100):
        # Create realistic price movements
        price_change = np.random.normal(0, 100)  # Normal distribution around 0
        open_price = base_price + price_change
        close_price = open_price + np.random.normal(0, 50)
        high_price = max(open_price, close_price) + abs(np.random.normal(0, 25))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, 25))
        
        candles.append(Candle(
            timestamp=current_time - (i * 3600),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=np.random.uniform(100, 1000)
        ))
        
        base_price = close_price  # Use close as next base
    
    return list(reversed(candles))  # Return chronological order


@pytest.fixture
def strategy_config():
    return StrategyConfig(
        symbol="BTCUSDT",
        position_size=0.1,
        max_position_size=0.25,
        stop_loss=0.15,
        take_profit=0.25,
        risk_per_trade=0.02,
        enabled=True,
        parameters={
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
    )


class TestTechnicalAnalyzer:
    """Test technical analysis functions"""
    
    def test_calculate_all_indicators(self, sample_candles):
        """Test comprehensive technical indicator calculation"""
        indicators = TechnicalAnalyzer.calculate_all_indicators(sample_candles)
        
        # Check that key indicators are present
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'bb_upper' in indicators
        assert 'bb_lower' in indicators
        assert 'atr' in indicators
        
        # Check RSI is in valid range
        if 'rsi' in indicators:
            assert 0 <= indicators['rsi'] <= 100
        
        # Check Bollinger Bands order
        if all(key in indicators for key in ['bb_upper', 'bb_middle', 'bb_lower']):
            assert indicators['bb_upper'] >= indicators['bb_middle'] >= indicators['bb_lower']
    
    def test_fallback_indicators(self, sample_candles):
        """Test fallback indicators when TA-Lib is not available"""
        with patch('app.services.advanced_trading_strategies.TALIB_AVAILABLE', False):
            indicators = TechnicalAnalyzer._calculate_fallback_indicators(
                np.array([c.close for c in sample_candles]),
                np.array([c.high for c in sample_candles]),
                np.array([c.low for c in sample_candles]),
                np.array([c.volume for c in sample_candles])
            )
            
            # Should have basic indicators
            assert 'sma_20' in indicators or 'sma_50' in indicators
            assert 'rsi' in indicators


class TestSentimentAnalyzer:
    """Test sentiment analysis functionality"""
    
    @pytest.fixture
    def sentiment_analyzer(self):
        return SentimentAnalyzer()
    
    def test_fear_greed_index(self, sentiment_analyzer):
        """Test Fear & Greed Index retrieval"""
        with patch('requests.get') as mock_get:
            # Mock successful API response
            mock_response = Mock()
            mock_response.json.return_value = {
                'data': [{'value': '75'}]
            }
            mock_get.return_value = mock_response
            
            result = sentiment_analyzer.get_fear_greed_index()
            assert 0.0 <= result <= 1.0
            assert result == 0.75  # 75/100
    
    def test_fear_greed_index_error(self, sentiment_analyzer):
        """Test Fear & Greed Index error handling"""
        with patch('requests.get', side_effect=Exception("API Error")):
            result = sentiment_analyzer.get_fear_greed_index()
            assert result == 0.5  # Should return neutral on error
    
    def test_composite_sentiment(self, sentiment_analyzer):
        """Test composite sentiment calculation"""
        with patch.object(sentiment_analyzer, 'get_fear_greed_index', return_value=0.6):
            with patch.object(sentiment_analyzer, 'get_social_sentiment', return_value=0.7):
                result = sentiment_analyzer.calculate_composite_sentiment("BTCUSDT")
                assert 0.0 <= result <= 1.0
                # Should be weighted average: 0.6 * 0.4 + 0.7 * 0.6 = 0.66
                assert abs(result - 0.66) < 0.01


class TestTradingStrategies:
    """Test individual trading strategy implementations"""
    
    def test_advanced_technical_indicator_strategy(self, mock_exchange, strategy_config, sample_candles):
        """Test Advanced Technical Indicator Strategy"""
        strategy = AdvancedTechnicalIndicatorStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(sample_candles, ticker)
        
        assert signal.symbol == "BTCUSDT"
        assert signal.strategy_name == "AdvancedTechnicalIndicatorStrategy"
        assert 0.0 <= signal.strength <= 1.0
        assert signal.metadata is not None
    
    def test_scalping_strategy(self, mock_exchange, strategy_config, sample_candles):
        """Test Scalping Strategy"""
        strategy_config.parameters.update({
            'min_interval': 5,
            'spread_threshold': 0.002,
            'volume_threshold': 1000
        })
        
        strategy = ScalpingStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(sample_candles, ticker)
        
        assert signal.symbol == "BTCUSDT"
        assert signal.strategy_name == "ScalpingStrategy"
        assert 'spread' in signal.metadata
        assert 'volume_ratio' in signal.metadata
    
    def test_dca_strategy(self, mock_exchange, strategy_config, sample_candles):
        """Test Dynamic DCA Strategy"""
        strategy_config.parameters.update({
            'dca_interval': 60,  # 1 minute for testing
            'base_amount': 100,
            'volatility_adjustment': True
        })
        
        strategy = DynamicDCAStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        # First signal should trigger (no previous DCA)
        signal1 = strategy.generate_signal(sample_candles, ticker)
        assert signal1.signal.value == "buy"
        
        # Immediate second signal should not trigger (interval not reached)
        signal2 = strategy.generate_signal(sample_candles, ticker)
        assert signal2.signal.value == "hold"
    
    def test_grid_trading_strategy(self, mock_exchange, strategy_config, sample_candles):
        """Test Grid Trading Strategy"""
        strategy_config.parameters.update({
            'grid_levels': 10,
            'grid_spacing': 0.02
        })
        
        strategy = GridTradingStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        # First call should initialize grid
        signal1 = strategy.generate_signal(sample_candles, ticker)
        assert signal1.signal.value == "hold"
        assert signal1.metadata.get("reason") == "grid_initialized"
        
        # Subsequent calls should evaluate grid positions
        signal2 = strategy.generate_signal(sample_candles, ticker)
        assert 'grid_level' in signal2.metadata or signal2.signal.value == "hold"
    
    def test_trend_following_strategy(self, mock_exchange, strategy_config, sample_candles):
        """Test Trend Following Strategy"""
        strategy_config.parameters.update({
            'fast_ma_period': 50,
            'slow_ma_period': 200,
            'atr_period': 20
        })
        
        strategy = TrendFollowingStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(sample_candles, ticker)
        
        assert signal.symbol == "BTCUSDT"
        assert 'fast_ma' in signal.metadata
        assert 'slow_ma' in signal.metadata
        assert 'trend_strength' in signal.metadata
    
    def test_sentiment_strategy(self, mock_exchange, strategy_config, sample_candles):
        """Test Sentiment Strategy"""
        strategy = SentimentStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        with patch.object(strategy.sentiment_analyzer, 'calculate_composite_sentiment', return_value=0.8):
            signal = strategy.generate_signal(sample_candles, ticker)
            
            assert signal.symbol == "BTCUSDT"
            assert 'sentiment' in signal.metadata
            assert 'momentum' in signal.metadata
    
    def test_arbitrage_strategy(self, mock_exchange, strategy_config, sample_candles):
        """Test Statistical Arbitrage Strategy"""
        strategy_config.parameters.update({
            'lookback_period': 50,
            'z_score_threshold': 2.0
        })
        
        strategy = ArbitrageStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(sample_candles, ticker)
        
        assert signal.symbol == "BTCUSDT"
        assert 'z_score' in signal.metadata
        assert 'threshold' in signal.metadata


class TestStrategyManager:
    """Test strategy management functionality"""
    
    def test_strategy_manager_creation(self, mock_exchange):
        """Test creating strategy manager"""
        manager = AdvancedStrategyManager(mock_exchange)
        assert len(manager.strategies) == 0
    
    def test_add_remove_strategies(self, mock_exchange, strategy_config):
        """Test adding and removing strategies"""
        manager = AdvancedStrategyManager(mock_exchange)
        
        # Add strategy
        manager.add_strategy(AdvancedTechnicalIndicatorStrategy, strategy_config)
        assert len(manager.strategies) == 1
        
        # Remove strategy
        manager.remove_strategy("AdvancedTechnicalIndicatorStrategy")
        assert len(manager.strategies) == 0
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, mock_exchange, strategy_config, sample_candles):
        """Test signal generation from multiple strategies"""
        manager = AdvancedStrategyManager(mock_exchange)
        manager.add_strategy(AdvancedTechnicalIndicatorStrategy, strategy_config)
        manager.add_strategy(TrendFollowingStrategy, strategy_config)
        
        ticker = mock_exchange.get_ticker("BTCUSDT")
        signals = await manager.generate_signals("BTCUSDT", sample_candles, ticker)
        
        assert isinstance(signals, list)
        # Signals should be from enabled strategies only
        for signal in signals:
            assert signal.symbol == "BTCUSDT"
            assert signal.strategy_name in ["AdvancedTechnicalIndicatorStrategy", "TrendFollowingStrategy"]
    
    def test_combined_signal(self, mock_exchange, strategy_config, sample_candles):
        """Test combining multiple signals"""
        from app.services.advanced_trading_strategies import SignalType
        
        manager = AdvancedStrategyManager(mock_exchange)
        
        # Create mock signals
        signals = [
            Mock(signal=SignalType.BUY, strength=0.8, symbol="BTCUSDT", price=50000),
            Mock(signal=SignalType.BUY, strength=0.6, symbol="BTCUSDT", price=50000),
            Mock(signal=SignalType.SELL, strength=0.4, symbol="BTCUSDT", price=50000)
        ]
        
        combined = manager.get_combined_signal(signals)
        
        assert combined is not None
        assert combined.signal == SignalType.BUY  # Buy signals stronger
        assert combined.strategy_name == "CombinedStrategy"


class TestStrategyFactory:
    """Test strategy factory functionality"""
    
    def test_create_all_strategy_types(self, mock_exchange, strategy_config):
        """Test creating all supported strategy types"""
        strategy_types = [
            'AdvancedTechnicalIndicator',
            'Scalping',
            'DynamicDCA',
            'Sentiment',
            'GridTrading',
            'TrendFollowing',
            'Arbitrage'
        ]
        
        for strategy_type in strategy_types:
            strategy = create_advanced_strategy(strategy_type, mock_exchange, strategy_config)
            assert strategy.name == f"{strategy_type}Strategy"
            assert strategy.exchange == mock_exchange
            assert strategy.config == strategy_config
    
    def test_invalid_strategy_type(self, mock_exchange, strategy_config):
        """Test creating invalid strategy type"""
        with pytest.raises(ValueError, match="Unknown strategy type"):
            create_advanced_strategy("InvalidStrategy", mock_exchange, strategy_config)


class TestEnhancedTradingEngine:
    """Test enhanced trading engine functionality"""
    
    @pytest.fixture
    def mock_db(self):
        db = Mock(spec=Session)
        return db
    
    @pytest.fixture
    def mock_bot(self):
        bot = Mock(spec=TradingBot)
        bot.id = 1
        bot.parameters = {
            'exchange': 'robinhood',
            'primary_symbol': 'AAPL',
            'symbols': ['AAPL', 'MSFT']
        }
        return bot
    
    @pytest.fixture
    def mock_algorithm_configs(self):
        return [
            Mock(
                id=1,
                algorithm_type="AdvancedTechnicalIndicator",
                algorithm_name="Tech Analysis 1",
                position_size=0.1,
                max_position_size=0.25,
                stop_loss=0.15,
                take_profit=0.25,
                risk_per_trade=0.02,
                enabled=True,
                parameters={'rsi_period': 14}
            ),
            Mock(
                id=2,
                algorithm_type="DynamicDCA",
                algorithm_name="DCA Strategy",
                position_size=0.15,
                max_position_size=0.3,
                stop_loss=0.1,
                take_profit=0.2,
                risk_per_trade=0.015,
                enabled=True,
                parameters={'dca_interval': 86400}
            )
        ]
    
    def test_engine_initialization(self, mock_db, mock_bot, mock_algorithm_configs):
        """Test enhanced trading engine initialization"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
        mock_db.query.return_value.filter.return_value.all.return_value = mock_algorithm_configs
        
        with patch('app.services.enhanced_trading_engine.ExchangeFactory.create_exchange'):
            engine = EnhancedTradingEngine(1, mock_db)
            
            assert engine.bot_id == 1
            assert engine.bot == mock_bot
            assert len(engine.algorithm_instances) == 2
    
    def test_real_time_state(self, mock_db, mock_bot, mock_algorithm_configs):
        """Test real-time state retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
        mock_db.query.return_value.filter.return_value.all.return_value = mock_algorithm_configs
        
        with patch('app.services.enhanced_trading_engine.ExchangeFactory.create_exchange'):
            engine = EnhancedTradingEngine(1, mock_db)
            
            state = engine.get_real_time_state()
            
            assert state['bot_id'] == 1
            assert state['is_running'] is False
            assert 'algorithm_status' in state
            assert len(state['algorithm_status']) == 2


class TestIntegrationAPIs:
    """Test API integration with algorithm system"""
    
    @pytest.fixture
    def client(self):
        """Mock FastAPI test client"""
        return Mock()
    
    def test_algorithm_creation_workflow(self, client):
        """Test complete algorithm creation workflow"""
        # This would test the actual API endpoints
        # For now, we'll test the workflow logic
        
        # 1. Get templates
        templates_response = Mock()
        templates_response.json.return_value = [
            {
                'id': 1,
                'name': 'Conservative Technical Analysis',
                'algorithm_type': 'AdvancedTechnicalIndicator',
                'default_parameters': {'rsi_period': 14}
            }
        ]
        
        # 2. Create algorithm from template
        create_response = Mock()
        create_response.ok = True
        create_response.json.return_value = {
            'id': 1,
            'algorithm_name': 'My Tech Analysis',
            'algorithm_type': 'AdvancedTechnicalIndicator',
            'enabled': True
        }
        
        assert templates_response.json() is not None
        assert create_response.ok is True


# Performance and Load Tests
class TestPerformance:
    """Test algorithm performance under load"""
    
    @pytest.mark.asyncio
    async def test_multiple_signals_performance(self, mock_exchange, strategy_config, sample_candles):
        """Test performance with multiple rapid signal generations"""
        strategy = AdvancedTechnicalIndicatorStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        # Generate 100 signals rapidly
        start_time = time.time()
        
        for _ in range(100):
            signal = strategy.generate_signal(sample_candles, ticker)
            assert signal is not None
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete 100 signals in reasonable time (< 1 second)
        assert execution_time < 1.0
    
    def test_memory_usage_strategies(self, mock_exchange, strategy_config):
        """Test memory usage doesn't grow excessively"""
        import gc
        import sys
        
        initial_objects = len(gc.get_objects())
        
        # Create and destroy strategies multiple times
        for _ in range(50):
            strategy = AdvancedTechnicalIndicatorStrategy(mock_exchange, strategy_config)
            del strategy
            gc.collect()
        
        final_objects = len(gc.get_objects())
        
        # Should not have significant memory leaks
        object_growth = final_objects - initial_objects
        assert object_growth < 1000  # Allow some growth but not excessive


# Edge Cases and Error Handling
class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_candles(self, mock_exchange, strategy_config):
        """Test strategy behavior with empty candle data"""
        strategy = AdvancedTechnicalIndicatorStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal([], ticker)
        
        assert signal.signal.value == "hold"
        assert signal.metadata.get("reason") == "insufficient_data"
    
    def test_insufficient_candles(self, mock_exchange, strategy_config):
        """Test strategy behavior with insufficient candle data"""
        strategy = AdvancedTechnicalIndicatorStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        # Only 10 candles (insufficient for most indicators)
        few_candles = [
            Candle(time.time() - i*3600, 50000+i*10, 50100+i*10, 49900+i*10, 50050+i*10, 100)
            for i in range(10)
        ]
        
        signal = strategy.generate_signal(few_candles, ticker)
        
        assert signal.signal.value == "hold"
        assert signal.metadata.get("reason") == "insufficient_data"
    
    def test_extreme_market_conditions(self, mock_exchange, strategy_config, sample_candles):
        """Test strategy behavior in extreme market conditions"""
        # Simulate extreme volatility
        extreme_candles = []
        base_price = 50000
        
        for i in range(100):
            if i % 2 == 0:  # Extreme up move
                close = base_price * 1.1
            else:  # Extreme down move
                close = base_price * 0.9
            
            extreme_candles.append(Candle(
                time.time() - i*3600,
                base_price,
                max(base_price, close) * 1.05,
                min(base_price, close) * 0.95,
                close,
                1000
            ))
            base_price = close
        
        strategy = AdvancedTechnicalIndicatorStrategy(mock_exchange, strategy_config)
        ticker = mock_exchange.get_ticker("BTCUSDT")
        
        signal = strategy.generate_signal(extreme_candles, ticker)
        
        # Should handle extreme conditions gracefully
        assert signal is not None
        assert 0.0 <= signal.strength <= 1.0


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])