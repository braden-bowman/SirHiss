"""
Algorithm configuration model for storing trading strategy parameters
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AlgorithmConfig(Base):
    """Algorithm configuration model for trading strategies"""
    
    __tablename__ = "algorithm_configs"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("trading_bots.id"), nullable=False)
    algorithm_type = Column(String(100), nullable=False)  # e.g., "AdvancedTechnicalIndicator"
    algorithm_name = Column(String(200), nullable=False)  # User-friendly name
    position_size = Column(Float, default=0.1)  # Fraction of portfolio allocated
    max_position_size = Column(Float, default=0.25)
    stop_loss = Column(Float, default=0.15)
    take_profit = Column(Float, default=0.25)
    risk_per_trade = Column(Float, default=0.02)
    enabled = Column(Boolean, default=True)
    
    # Strategy-specific parameters stored as JSON
    parameters = Column(JSONB, default={})
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    bot = relationship("TradingBot", back_populates="algorithm_configs")
    executions = relationship("AlgorithmExecution", back_populates="algorithm_config", cascade="all, delete-orphan")


class AlgorithmExecution(Base):
    """Track individual algorithm executions and signals"""
    
    __tablename__ = "algorithm_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    algorithm_config_id = Column(Integer, ForeignKey("algorithm_configs.id"), nullable=False)
    bot_id = Column(Integer, ForeignKey("trading_bots.id"), nullable=False)
    
    # Signal information
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    signal_strength = Column(Float, nullable=False)
    symbol = Column(String(20), nullable=False)
    price = Column(Numeric(15, 8), nullable=False)
    
    # Execution details
    quantity = Column(Numeric(15, 8))
    executed = Column(Boolean, default=False)
    execution_price = Column(Numeric(15, 8))
    order_id = Column(String(100))
    
    # Strategy metadata
    signal_metadata = Column(JSONB, default={})
    
    # Performance tracking for this execution
    pnl = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True))

    # Relationships
    algorithm_config = relationship("AlgorithmConfig", back_populates="executions")
    bot = relationship("TradingBot")


class AlgorithmTemplate(Base):
    """Pre-configured algorithm templates for easy setup"""
    
    __tablename__ = "algorithm_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    algorithm_type = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # e.g., "Technical Analysis", "Sentiment", "Grid Trading"
    
    # Default configuration
    default_position_size = Column(Float, default=0.1)
    default_parameters = Column(JSONB, default={})
    
    # Template metadata
    is_active = Column(Boolean, default=True)
    difficulty_level = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    min_capital = Column(Float, default=1000.0)  # Minimum recommended capital
    recommended_timeframe = Column(String(50))  # e.g., "1 minute to 1 hour", "daily"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AlgorithmPerformanceMetric(Base):
    """Historical performance metrics for algorithms"""
    
    __tablename__ = "algorithm_performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    algorithm_config_id = Column(Integer, ForeignKey("algorithm_configs.id"), nullable=False)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly
    
    # Performance metrics
    trades_count = Column(Integer, default=0)
    winning_trades_count = Column(Integer, default=0)
    losing_trades_count = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    sortino_ratio = Column(Float, default=0.0)
    calmar_ratio = Column(Float, default=0.0)
    
    # Volume metrics
    total_volume = Column(Float, default=0.0)
    average_trade_size = Column(Float, default=0.0)
    
    # Additional metadata
    market_conditions = Column(JSONB, default={})  # e.g., volatility, trend direction
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    algorithm_config = relationship("AlgorithmConfig")


# Default algorithm templates
DEFAULT_ALGORITHM_TEMPLATES = [
    {
        "name": "Conservative Technical Analysis",
        "algorithm_type": "AdvancedTechnicalIndicator",
        "description": "Uses RSI, MACD, and Bollinger Bands with conservative thresholds for stable returns",
        "category": "Technical Analysis",
        "default_position_size": 0.15,
        "default_parameters": {
            "rsi_period": 14,
            "rsi_oversold": 25,
            "rsi_overbought": 75,
            "macd_fast": 8,
            "macd_slow": 21,
            "macd_signal": 5,
            "bb_period": 20,
            "bb_std": 2.0
        },
        "difficulty_level": "beginner",
        "min_capital": 500.0,
        "recommended_timeframe": "1 hour to daily"
    },
    {
        "name": "Aggressive Scalping",
        "algorithm_type": "Scalping",
        "description": "High-frequency trading strategy for quick profits on small price movements",
        "category": "High Frequency",
        "default_position_size": 0.05,
        "default_parameters": {
            "min_interval": 5,
            "spread_threshold": 0.001,
            "volume_threshold": 1500
        },
        "difficulty_level": "advanced",
        "min_capital": 5000.0,
        "recommended_timeframe": "1 second to 5 minutes"
    },
    {
        "name": "Dollar Cost Averaging",
        "algorithm_type": "DynamicDCA",
        "description": "Systematic buying strategy that reduces timing risk through regular purchases",
        "category": "Long-term Investment",
        "default_position_size": 0.20,
        "default_parameters": {
            "dca_interval": 86400,  # Daily
            "base_amount": 100,
            "volatility_adjustment": True
        },
        "difficulty_level": "beginner",
        "min_capital": 1000.0,
        "recommended_timeframe": "daily to weekly"
    },
    {
        "name": "Grid Trading Bot",
        "algorithm_type": "GridTrading",
        "description": "Places buy and sell orders at regular intervals around current price",
        "category": "Market Making",
        "default_position_size": 0.25,
        "default_parameters": {
            "grid_levels": 10,
            "grid_spacing": 0.02
        },
        "difficulty_level": "intermediate",
        "min_capital": 2000.0,
        "recommended_timeframe": "15 minutes to 4 hours"
    },
    {
        "name": "Trend Following Strategy",
        "algorithm_type": "TrendFollowing",
        "description": "Follows market trends using moving averages and ATR for position sizing",
        "category": "Trend Following",
        "default_position_size": 0.20,
        "default_parameters": {
            "fast_ma_period": 50,
            "slow_ma_period": 200,
            "atr_period": 20,
            "atr_multiplier": 2.5
        },
        "difficulty_level": "intermediate",
        "min_capital": 1500.0,
        "recommended_timeframe": "1 hour to daily"
    },
    {
        "name": "Sentiment-Based Trading",
        "algorithm_type": "Sentiment",
        "description": "Uses market sentiment analysis from news and social media",
        "category": "Sentiment Analysis",
        "default_position_size": 0.10,
        "default_parameters": {
            "sentiment_threshold": 0.6
        },
        "difficulty_level": "advanced",
        "min_capital": 3000.0,
        "recommended_timeframe": "4 hours to daily"
    },
    {
        "name": "Mean Reversion Arbitrage",
        "algorithm_type": "Arbitrage",
        "description": "Exploits price deviations from historical mean for profit",
        "category": "Statistical Arbitrage",
        "default_position_size": 0.15,
        "default_parameters": {
            "lookback_period": 50,
            "z_score_threshold": 2.0
        },
        "difficulty_level": "advanced",
        "min_capital": 4000.0,
        "recommended_timeframe": "15 minutes to 1 hour"
    }
]

# Enhanced algorithm templates
ENHANCED_ALGORITHM_TEMPLATES = [
    {
        "name": "Advanced Order Book Analytics",
        "algorithm_type": "OrderBookAnalytics",
        "description": "Uses Level 5 order book analysis and VPIN for high-frequency trading signals",
        "category": "Market Microstructure",
        "default_position_size": 0.05,
        "default_parameters": {
            "analysis_levels": 5,
            "vpin_threshold": 0.3,
            "min_interval": 10,
            "spread_threshold": 0.002
        },
        "difficulty_level": "advanced",
        "min_capital": 10000.0,
        "recommended_timeframe": "1 second to 1 minute"
    },
    {
        "name": "Machine Learning Ensemble",
        "algorithm_type": "MLModel",
        "description": "Combines LSTM and Random Forest models for AI-powered trading decisions",
        "category": "Machine Learning",
        "default_position_size": 0.20,
        "default_parameters": {
            "model_type": "ensemble",
            "lookback_window": 60,
            "confidence_threshold": 0.65,
            "retrain_interval": 86400
        },
        "difficulty_level": "advanced",
        "min_capital": 5000.0,
        "recommended_timeframe": "1 hour to daily"
    },
    {
        "name": "Dynamic Portfolio Rebalancing",
        "algorithm_type": "PortfolioRebalancing",
        "description": "CPPI and threshold-based portfolio rebalancing for risk management",
        "category": "Portfolio Management",
        "default_position_size": 0.30,
        "default_parameters": {
            "method": "threshold",
            "threshold": 0.05,
            "interval": 86400,
            "cppi_multiplier": 3,
            "target_allocation": {"crypto": 0.3, "stable": 0.7}
        },
        "difficulty_level": "intermediate",
        "min_capital": 2000.0,
        "recommended_timeframe": "daily to weekly"
    },
    {
        "name": "On-Chain Analysis Pro",
        "algorithm_type": "OnChainAnalysis",
        "description": "Leverages blockchain metrics like MVRV, NVT, and whale movements",
        "category": "Fundamental Analysis",
        "default_position_size": 0.15,
        "default_parameters": {
            "mvrv_threshold": 3.0,
            "nvt_threshold": 75,
            "flow_threshold": 1000000,
            "cache_duration": 3600
        },
        "difficulty_level": "advanced",
        "min_capital": 3000.0,
        "recommended_timeframe": "4 hours to daily"
    }
]

# All algorithm templates combined
ALL_ALGORITHM_TEMPLATES = DEFAULT_ALGORITHM_TEMPLATES + ENHANCED_ALGORITHM_TEMPLATES