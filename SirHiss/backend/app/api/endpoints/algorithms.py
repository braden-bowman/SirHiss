"""
Algorithm configuration endpoints for managing trading strategies
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.trading_bot import TradingBot
from app.models.algorithm_config import AlgorithmConfig, AlgorithmTemplate, AlgorithmExecution, DEFAULT_ALGORITHM_TEMPLATES
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

# Pydantic models for API

class AlgorithmParametersBase(BaseModel):
    """Base parameters for algorithm configuration"""
    rsi_period: Optional[int] = 14
    rsi_oversold: Optional[float] = 25
    rsi_overbought: Optional[float] = 75
    macd_fast: Optional[int] = 8
    macd_slow: Optional[int] = 21
    macd_signal: Optional[int] = 5
    bb_period: Optional[int] = 20
    bb_std: Optional[float] = 2.0
    fast_ma_period: Optional[int] = 50
    slow_ma_period: Optional[int] = 200
    atr_period: Optional[int] = 20
    atr_multiplier: Optional[float] = 2.5
    grid_levels: Optional[int] = 10
    grid_spacing: Optional[float] = 0.02
    dca_interval: Optional[int] = 86400  # Daily in seconds
    base_amount: Optional[float] = 100
    volatility_adjustment: Optional[bool] = True
    sentiment_threshold: Optional[float] = 0.6
    lookback_period: Optional[int] = 50
    z_score_threshold: Optional[float] = 2.0
    min_interval: Optional[int] = 5
    spread_threshold: Optional[float] = 0.002
    volume_threshold: Optional[float] = 1000

class AlgorithmConfigCreate(BaseModel):
    algorithm_type: str = Field(..., description="Type of algorithm (e.g., AdvancedTechnicalIndicator)")
    algorithm_name: str = Field(..., description="User-friendly name for the algorithm")
    position_size: float = Field(default=0.1, ge=0.01, le=1.0, description="Fraction of portfolio to allocate")
    max_position_size: float = Field(default=0.25, ge=0.01, le=1.0)
    stop_loss: float = Field(default=0.15, ge=0.01, le=0.5, description="Stop loss percentage")
    take_profit: float = Field(default=0.25, ge=0.01, le=1.0, description="Take profit percentage")
    risk_per_trade: float = Field(default=0.02, ge=0.001, le=0.1)
    enabled: bool = Field(default=True, description="Whether the algorithm is active")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Algorithm-specific parameters")

class AlgorithmConfigUpdate(BaseModel):
    algorithm_name: Optional[str] = None
    position_size: Optional[float] = Field(None, ge=0.01, le=1.0)
    max_position_size: Optional[float] = Field(None, ge=0.01, le=1.0)
    stop_loss: Optional[float] = Field(None, ge=0.01, le=0.5)
    take_profit: Optional[float] = Field(None, ge=0.01, le=1.0)
    risk_per_trade: Optional[float] = Field(None, ge=0.001, le=0.1)
    enabled: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None

class AlgorithmConfigResponse(BaseModel):
    id: int
    bot_id: int
    algorithm_type: str
    algorithm_name: str
    position_size: float
    max_position_size: float
    stop_loss: float
    take_profit: float
    risk_per_trade: float
    enabled: bool
    parameters: Dict[str, Any]
    
    # Performance metrics
    total_trades: int
    winning_trades: int
    win_rate: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AlgorithmTemplateResponse(BaseModel):
    id: int
    name: str
    algorithm_type: str
    description: Optional[str]
    category: Optional[str]
    default_position_size: float
    default_parameters: Dict[str, Any]
    difficulty_level: str
    min_capital: float
    recommended_timeframe: Optional[str]
    
    class Config:
        from_attributes = True

class AlgorithmExecutionResponse(BaseModel):
    id: int
    algorithm_config_id: int
    signal_type: str
    signal_strength: float
    symbol: str
    price: float
    quantity: Optional[float]
    executed: bool
    execution_price: Optional[float]
    metadata: Dict[str, Any]
    pnl: float
    created_at: str
    
    class Config:
        from_attributes = True

class AlgorithmPerformanceResponse(BaseModel):
    algorithm_name: str
    algorithm_type: str
    total_trades: int
    winning_trades: int
    win_rate: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    recent_signals: List[AlgorithmExecutionResponse]

# API Endpoints

@router.get("/templates", response_model=List[AlgorithmTemplateResponse])
async def get_algorithm_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    db: Session = Depends(get_db)
):
    """Get available algorithm templates"""
    query = db.query(AlgorithmTemplate).filter(AlgorithmTemplate.is_active == True)
    
    if category:
        query = query.filter(AlgorithmTemplate.category == category)
    if difficulty:
        query = query.filter(AlgorithmTemplate.difficulty_level == difficulty)
    
    templates = query.all()
    return templates

@router.get("/types", response_model=Dict[str, List[str]])
async def get_algorithm_types():
    """Get available algorithm types and their categories"""
    return {
        "Technical Analysis": [
            "AdvancedTechnicalIndicator",
            "TrendFollowing",
            "Arbitrage"
        ],
        "High Frequency": [
            "Scalping"
        ],
        "Long-term Investment": [
            "DynamicDCA"
        ],
        "Market Making": [
            "GridTrading"
        ],
        "Sentiment Analysis": [
            "Sentiment"
        ],
        "Machine Learning": [
            "MLModel"
        ],
        "Fundamental Analysis": [
            "OnChainAnalysis"
        ],
        "Portfolio Management": [
            "PortfolioRebalancing"
        ],
        "Market Microstructure": [
            "OrderBookAnalytics"
        ],
        "Combination": [
            "AlgorithmCombination"
        ]
    }

@router.get("/bots/{bot_id}/algorithms", response_model=List[AlgorithmConfigResponse])
async def get_bot_algorithms(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all algorithm configurations for a bot"""
    # Verify bot ownership
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    algorithms = db.query(AlgorithmConfig).filter(
        AlgorithmConfig.bot_id == bot_id
    ).all()
    
    return algorithms

@router.post("/bots/{bot_id}/algorithms", response_model=AlgorithmConfigResponse)
async def create_bot_algorithm(
    bot_id: int,
    algorithm: AlgorithmConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new algorithm configuration for a bot"""
    # Verify bot ownership
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Check if algorithm name is unique for this bot
    existing = db.query(AlgorithmConfig).filter(
        AlgorithmConfig.bot_id == bot_id,
        AlgorithmConfig.algorithm_name == algorithm.algorithm_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Algorithm name already exists for this bot"
        )
    
    # Create algorithm configuration
    db_algorithm = AlgorithmConfig(
        bot_id=bot_id,
        algorithm_type=algorithm.algorithm_type,
        algorithm_name=algorithm.algorithm_name,
        position_size=algorithm.position_size,
        max_position_size=algorithm.max_position_size,
        stop_loss=algorithm.stop_loss,
        take_profit=algorithm.take_profit,
        risk_per_trade=algorithm.risk_per_trade,
        enabled=algorithm.enabled,
        parameters=algorithm.parameters
    )
    
    db.add(db_algorithm)
    db.commit()
    db.refresh(db_algorithm)
    
    return db_algorithm

@router.post("/bots/{bot_id}/algorithms/from-template/{template_id}", response_model=AlgorithmConfigResponse)
async def create_algorithm_from_template(
    bot_id: int,
    template_id: int,
    algorithm_name: str,
    position_size: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an algorithm configuration from a template"""
    # Verify bot ownership
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get template
    template = db.query(AlgorithmTemplate).filter(
        AlgorithmTemplate.id == template_id,
        AlgorithmTemplate.is_active == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check if algorithm name is unique for this bot
    existing = db.query(AlgorithmConfig).filter(
        AlgorithmConfig.bot_id == bot_id,
        AlgorithmConfig.algorithm_name == algorithm_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Algorithm name already exists for this bot"
        )
    
    # Create algorithm from template
    db_algorithm = AlgorithmConfig(
        bot_id=bot_id,
        algorithm_type=template.algorithm_type,
        algorithm_name=algorithm_name,
        position_size=position_size or template.default_position_size,
        parameters=template.default_parameters.copy()
    )
    
    db.add(db_algorithm)
    db.commit()
    db.refresh(db_algorithm)
    
    return db_algorithm

@router.put("/algorithms/{algorithm_id}", response_model=AlgorithmConfigResponse)
async def update_algorithm(
    algorithm_id: int,
    algorithm_update: AlgorithmConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an algorithm configuration"""
    # Get algorithm and verify ownership
    algorithm = db.query(AlgorithmConfig).join(TradingBot).filter(
        AlgorithmConfig.id == algorithm_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Update fields
    update_data = algorithm_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "parameters" and value is not None:
            # Merge parameters instead of replacing
            algorithm.parameters.update(value)
        else:
            setattr(algorithm, field, value)
    
    db.commit()
    db.refresh(algorithm)
    
    return algorithm

@router.delete("/algorithms/{algorithm_id}")
async def delete_algorithm(
    algorithm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an algorithm configuration"""
    # Get algorithm and verify ownership
    algorithm = db.query(AlgorithmConfig).join(TradingBot).filter(
        AlgorithmConfig.id == algorithm_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    db.delete(algorithm)
    db.commit()
    
    return {"message": "Algorithm deleted successfully"}

@router.post("/algorithms/{algorithm_id}/toggle")
async def toggle_algorithm(
    algorithm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enable/disable an algorithm"""
    # Get algorithm and verify ownership
    algorithm = db.query(AlgorithmConfig).join(TradingBot).filter(
        AlgorithmConfig.id == algorithm_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    algorithm.enabled = not algorithm.enabled
    db.commit()
    
    return {"enabled": algorithm.enabled}

@router.get("/algorithms/{algorithm_id}/performance", response_model=AlgorithmPerformanceResponse)
async def get_algorithm_performance(
    algorithm_id: int,
    limit: int = Query(default=50, le=200, description="Number of recent signals to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get algorithm performance metrics"""
    # Get algorithm and verify ownership
    algorithm = db.query(AlgorithmConfig).join(TradingBot).filter(
        AlgorithmConfig.id == algorithm_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Get recent executions
    executions = db.query(AlgorithmExecution).filter(
        AlgorithmExecution.algorithm_config_id == algorithm_id
    ).order_by(AlgorithmExecution.created_at.desc()).limit(limit).all()
    
    return AlgorithmPerformanceResponse(
        algorithm_name=algorithm.algorithm_name,
        algorithm_type=algorithm.algorithm_type,
        total_trades=algorithm.total_trades,
        winning_trades=algorithm.winning_trades,
        win_rate=algorithm.win_rate,
        total_return=algorithm.total_return,
        sharpe_ratio=algorithm.sharpe_ratio,
        max_drawdown=algorithm.max_drawdown,
        recent_signals=executions
    )

@router.get("/algorithms/{algorithm_id}/parameters", response_model=Dict[str, Any])
async def get_algorithm_parameters(
    algorithm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get algorithm parameters with descriptions"""
    # Get algorithm and verify ownership
    algorithm = db.query(AlgorithmConfig).join(TradingBot).filter(
        AlgorithmConfig.id == algorithm_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Parameter descriptions by algorithm type
    param_descriptions = get_parameter_descriptions(algorithm.algorithm_type)
    
    result = {}
    for param_name, current_value in algorithm.parameters.items():
        result[param_name] = {
            "value": current_value,
            "description": param_descriptions.get(param_name, {}).get("description", ""),
            "type": param_descriptions.get(param_name, {}).get("type", "number"),
            "min": param_descriptions.get(param_name, {}).get("min"),
            "max": param_descriptions.get(param_name, {}).get("max"),
            "step": param_descriptions.get(param_name, {}).get("step")
        }
    
    return result

@router.put("/algorithms/{algorithm_id}/parameters", response_model=Dict[str, Any])
async def update_algorithm_parameters(
    algorithm_id: int,
    parameters: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update algorithm parameters in real-time"""
    # Get algorithm and verify ownership
    algorithm = db.query(AlgorithmConfig).join(TradingBot).filter(
        AlgorithmConfig.id == algorithm_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    
    # Validate parameters
    valid_params = get_parameter_descriptions(algorithm.algorithm_type)
    validated_params = {}
    
    for param_name, value in parameters.items():
        if param_name not in valid_params:
            continue  # Skip unknown parameters
        
        param_info = valid_params[param_name]
        
        # Type validation and conversion
        if param_info["type"] == "number":
            try:
                value = float(value)
                if param_info.get("min") is not None and value < param_info["min"]:
                    value = param_info["min"]
                if param_info.get("max") is not None and value > param_info["max"]:
                    value = param_info["max"]
                validated_params[param_name] = value
            except (ValueError, TypeError):
                continue
        elif param_info["type"] == "integer":
            try:
                value = int(value)
                if param_info.get("min") is not None and value < param_info["min"]:
                    value = param_info["min"]
                if param_info.get("max") is not None and value > param_info["max"]:
                    value = param_info["max"]
                validated_params[param_name] = value
            except (ValueError, TypeError):
                continue
        elif param_info["type"] == "boolean":
            validated_params[param_name] = bool(value)
        else:
            validated_params[param_name] = value
    
    # Update parameters
    algorithm.parameters.update(validated_params)
    db.commit()
    
    return algorithm.parameters

def get_parameter_descriptions(algorithm_type: str) -> Dict[str, Dict[str, Any]]:
    """Get parameter descriptions for algorithm types"""
    descriptions = {
        "AdvancedTechnicalIndicator": {
            "rsi_period": {"description": "RSI calculation period", "type": "integer", "min": 2, "max": 50, "step": 1},
            "rsi_oversold": {"description": "RSI oversold threshold", "type": "number", "min": 10, "max": 40, "step": 1},
            "rsi_overbought": {"description": "RSI overbought threshold", "type": "number", "min": 60, "max": 90, "step": 1},
            "macd_fast": {"description": "MACD fast period", "type": "integer", "min": 5, "max": 20, "step": 1},
            "macd_slow": {"description": "MACD slow period", "type": "integer", "min": 15, "max": 50, "step": 1},
            "macd_signal": {"description": "MACD signal period", "type": "integer", "min": 3, "max": 15, "step": 1},
            "bb_period": {"description": "Bollinger Bands period", "type": "integer", "min": 5, "max": 50, "step": 1},
            "bb_std": {"description": "Bollinger Bands standard deviation", "type": "number", "min": 1.0, "max": 3.0, "step": 0.1}
        },
        "Scalping": {
            "min_interval": {"description": "Minimum interval between signals (seconds)", "type": "integer", "min": 1, "max": 60, "step": 1},
            "spread_threshold": {"description": "Maximum spread threshold", "type": "number", "min": 0.0001, "max": 0.01, "step": 0.0001},
            "volume_threshold": {"description": "Minimum volume threshold", "type": "number", "min": 100, "max": 10000, "step": 100}
        },
        "DynamicDCA": {
            "dca_interval": {"description": "DCA interval (seconds)", "type": "integer", "min": 3600, "max": 604800, "step": 3600},
            "base_amount": {"description": "Base DCA amount", "type": "number", "min": 10, "max": 1000, "step": 10},
            "volatility_adjustment": {"description": "Enable volatility adjustment", "type": "boolean"}
        },
        "GridTrading": {
            "grid_levels": {"description": "Number of grid levels", "type": "integer", "min": 3, "max": 50, "step": 1},
            "grid_spacing": {"description": "Grid spacing percentage", "type": "number", "min": 0.005, "max": 0.1, "step": 0.005}
        },
        "TrendFollowing": {
            "fast_ma_period": {"description": "Fast moving average period", "type": "integer", "min": 5, "max": 100, "step": 1},
            "slow_ma_period": {"description": "Slow moving average period", "type": "integer", "min": 20, "max": 500, "step": 1},
            "atr_period": {"description": "ATR calculation period", "type": "integer", "min": 5, "max": 50, "step": 1},
            "atr_multiplier": {"description": "ATR multiplier for stop loss", "type": "number", "min": 1.0, "max": 5.0, "step": 0.1}
        },
        "Sentiment": {
            "sentiment_threshold": {"description": "Sentiment threshold for signals", "type": "number", "min": 0.1, "max": 0.9, "step": 0.1}
        },
        "Arbitrage": {
            "lookback_period": {"description": "Lookback period for mean calculation", "type": "integer", "min": 10, "max": 200, "step": 1},
            "z_score_threshold": {"description": "Z-score threshold for signals", "type": "number", "min": 1.0, "max": 4.0, "step": 0.1}
        }
    }
    
    return descriptions.get(algorithm_type, {})

# Initialize default templates on startup
async def init_algorithm_templates(db: Session):
    """Initialize default algorithm templates"""
    for template_data in DEFAULT_ALGORITHM_TEMPLATES:
        existing = db.query(AlgorithmTemplate).filter(
            AlgorithmTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = AlgorithmTemplate(**template_data)
            db.add(template)
    
    db.commit()