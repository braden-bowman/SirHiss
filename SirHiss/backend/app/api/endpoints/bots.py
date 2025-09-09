"""
Trading bot management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.trading_bot import TradingBot
from app.models.portfolio import Portfolio
from app.services.trading_engine import trading_engine_manager
from app.services.exchange_api import get_configured_exchange
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class BotCreate(BaseModel):
    """Bot creation schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    allocated_percentage: Decimal = Field(..., ge=0, le=100)
    strategy_code: Optional[str] = None
    parameters: dict = {}


class BotUpdate(BaseModel):
    """Bot update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    allocated_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    strategy_code: Optional[str] = None
    parameters: Optional[dict] = None


class BotResponse(BaseModel):
    """Bot response schema"""
    id: int
    name: str
    description: Optional[str]
    allocated_percentage: Decimal
    allocated_amount: Decimal
    current_value: Decimal
    status: str
    parameters: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[BotResponse])
async def get_bots(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all trading bots for the current user"""
    bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
    return bots


@router.post("/", response_model=BotResponse)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trading bot"""
    # Get or create user's portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=current_user.id)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    # Check if total allocation doesn't exceed 100%
    total_allocated = db.query(TradingBot).filter(
        TradingBot.user_id == current_user.id
    ).with_entities(TradingBot.allocated_percentage).all()
    
    current_total = sum(float(bot.allocated_percentage) for bot in total_allocated)
    if current_total + float(bot_data.allocated_percentage) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total bot allocation cannot exceed 100%"
        )
    
    # Calculate allocated amount based on portfolio value
    allocated_amount = (portfolio.total_value * bot_data.allocated_percentage) / 100
    
    # Create new bot
    db_bot = TradingBot(
        user_id=current_user.id,
        portfolio_id=portfolio.id,
        name=bot_data.name,
        description=bot_data.description,
        allocated_percentage=bot_data.allocated_percentage,
        allocated_amount=allocated_amount,
        strategy_code=bot_data.strategy_code,
        parameters=bot_data.parameters
    )
    
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    
    return db_bot


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific trading bot"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    return bot


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_data: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a trading bot"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Update fields
    update_data = bot_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)
    
    db.commit()
    db.refresh(bot)
    
    return bot


@router.post("/{bot_id}/start")
async def start_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a trading bot"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    if bot.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot is already running"
        )
    
    try:
        # Start bot execution via trading engine
        success = await trading_engine_manager.start_bot(bot_id)
        
        if success:
            bot.status = "running"
            db.commit()
            logger.info(f"Started bot {bot_id} for user {current_user.id}")
            return {"message": "Bot started successfully", "bot_id": bot_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start bot"
            )
    except Exception as e:
        logger.error(f"Error starting bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}"
        )


@router.post("/{bot_id}/stop")
async def stop_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a trading bot"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    try:
        # Stop bot execution via trading engine
        success = await trading_engine_manager.stop_bot(bot_id)
        
        bot.status = "stopped"
        db.commit()
        
        if success:
            logger.info(f"Stopped bot {bot_id} for user {current_user.id}")
            return {"message": "Bot stopped successfully", "bot_id": bot_id}
        else:
            logger.warning(f"Bot {bot_id} was not running")
            return {"message": "Bot was not running", "bot_id": bot_id}
            
    except Exception as e:
        logger.error(f"Error stopping bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop bot: {str(e)}"
        )


@router.delete("/{bot_id}")
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a trading bot"""
    bot = db.query(TradingBot).filter(
        TradingBot.id == bot_id,
        TradingBot.user_id == current_user.id
    ).first()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # TODO: Stop bot if running and divest positions
    
    db.delete(bot)
    db.commit()
    
    return {"message": "Bot deleted successfully", "bot_id": bot_id}