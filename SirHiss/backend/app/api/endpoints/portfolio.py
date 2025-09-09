"""
Portfolio management and analytics endpoints
Provides comprehensive portfolio tracking and risk metrics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime, timedelta
import time

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.holding import Holding
from app.models.trading_bot import TradingBot
from app.services.trading_engine import trading_engine_manager
from app.services.data_monitor import RiskMetrics
from app.services.exchange_api import get_configured_exchange
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class PortfolioResponse(BaseModel):
    """Original portfolio response schema"""
    id: int
    total_value: Decimal
    available_cash: Decimal
    robinhood_account_id: str = None

    class Config:
        from_attributes = True

class HoldingResponse(BaseModel):
    """Original holding response schema"""
    id: int
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pl: Decimal
    asset_type: str

    class Config:
        from_attributes = True

class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary response schema"""
    total_value: Decimal
    total_invested: Decimal
    total_pnl: Decimal
    total_pnl_percent: float
    available_cash: Decimal
    allocated_to_bots: Decimal
    number_of_bots: int
    active_bots: int
    last_updated: str

class PositionResponse(BaseModel):
    """Position response schema"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    realized_pnl: float
    bot_id: Optional[int] = None
    bot_name: Optional[str] = None
    strategy: Optional[str] = None

class BotPerformanceResponse(BaseModel):
    """Bot performance response schema"""
    bot_id: int
    name: str
    allocated_percentage: Decimal
    allocated_amount: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    pnl_percent: float
    status: str
    active_positions: int
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    last_active: str

class RiskMetricsResponse(BaseModel):
    """Risk metrics response schema"""
    portfolio_value: float
    total_exposure: float
    exposure_ratio: float
    max_drawdown: float
    var_95: float
    sharpe_ratio: float
    win_rate: float
    avg_trade_return: float
    risk_score: str  # LOW, MEDIUM, HIGH
    recommendations: List[str]

class AllocationResponse(BaseModel):
    """Portfolio allocation response schema"""
    bot_allocations: List[Dict[str, Any]]
    unallocated_percentage: float
    total_allocated: float
    recommendations: List[str]

@router.get("/", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    
    if not portfolio:
        # Create default portfolio
        portfolio = Portfolio(user_id=current_user.id)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    return portfolio

@router.get("/holdings", response_model=List[HoldingResponse])
async def get_holdings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's holdings"""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    
    if not portfolio:
        return []
    
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
    return holdings

@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive portfolio summary"""
    try:
        # Get or create portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
        if not portfolio:
            portfolio = Portfolio(user_id=current_user.id, total_value=Decimal('10000.00'))
            db.add(portfolio)
            db.commit()
            db.refresh(portfolio)
        
        # Get all user bots
        bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
        
        # Calculate metrics
        total_allocated = sum(bot.allocated_amount or Decimal('0') for bot in bots)
        active_bots = sum(1 for bot in bots if bot.status == "running")
        
        # Calculate total P&L from bots (using current_value vs allocated_amount)
        total_pnl = Decimal('0')
        for bot in bots:
            if bot.current_value and bot.allocated_amount:
                bot_pnl = bot.current_value - bot.allocated_amount
                total_pnl += bot_pnl
        
        # Calculate current portfolio value
        current_value = portfolio.total_value + total_pnl
        pnl_percent = float(total_pnl / portfolio.total_value * 100) if portfolio.total_value > 0 else 0.0
        
        return PortfolioSummaryResponse(
            total_value=current_value,
            total_invested=portfolio.total_value,
            total_pnl=total_pnl,
            total_pnl_percent=pnl_percent,
            available_cash=portfolio.total_value - total_allocated,
            allocated_to_bots=total_allocated,
            number_of_bots=len(bots),
            active_bots=active_bots,
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio summary: {str(e)}"
        )

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all portfolio positions across all bots"""
    try:
        positions = []
        bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
        
        for bot in bots:
            if bot.status == "running":
                bot_positions = trading_engine_manager.get_bot_positions(bot.id)
                
                for pos in bot_positions:
                    pnl_percent = 0.0
                    if pos['entry_price'] > 0:
                        pnl_percent = (pos['current_price'] - pos['entry_price']) / pos['entry_price'] * 100
                    
                    positions.append(PositionResponse(
                        symbol=pos['symbol'],
                        quantity=pos['quantity'],
                        entry_price=pos['entry_price'],
                        current_price=pos['current_price'],
                        market_value=pos['current_price'] * abs(pos['quantity']),
                        unrealized_pnl=pos['unrealized_pnl'],
                        unrealized_pnl_percent=pnl_percent,
                        realized_pnl=pos['realized_pnl'],
                        bot_id=bot.id,
                        bot_name=bot.name
                    ))
        
        return positions
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get positions: {str(e)}"
        )

@router.get("/bot-performance", response_model=List[BotPerformanceResponse])
async def get_bot_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for all bots"""
    try:
        bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
        performance_data = []
        
        for bot in bots:
            # Get bot statistics
            total_pnl = Decimal('0')
            if bot.current_value and bot.allocated_amount:
                total_pnl = bot.current_value - bot.allocated_amount
            pnl_percent = float(total_pnl / bot.allocated_amount * 100) if bot.allocated_amount > 0 else 0.0
            
            # Get active positions count
            active_positions = 0
            if bot.status == "running":
                positions = trading_engine_manager.get_bot_positions(bot.id)
                active_positions = len([p for p in positions if abs(p['quantity']) > 0.0001])
            
            # Mock some statistics (in real implementation, query from executions table)
            total_trades = 0  # Would be calculated from bot_executions
            win_rate = 0.0    # Would be calculated from profitable trades
            sharpe_ratio = 0.0 # Would be calculated from trade returns
            max_drawdown = 0.0 # Would be calculated from equity curve
            
            performance_data.append(BotPerformanceResponse(
                bot_id=bot.id,
                name=bot.name,
                allocated_percentage=bot.allocated_percentage,
                allocated_amount=bot.allocated_amount,
                current_value=bot.current_value or bot.allocated_amount,
                unrealized_pnl=total_pnl,
                realized_pnl=Decimal('0'),
                total_pnl=total_pnl,
                pnl_percent=pnl_percent,
                status=bot.status,
                active_positions=active_positions,
                total_trades=total_trades,
                win_rate=win_rate,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                last_active=(bot.last_active or datetime.utcnow()).isoformat()
            ))
        
        return performance_data
        
    except Exception as e:
        logger.error(f"Error getting bot performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get bot performance: {str(e)}"
        )

@router.get("/risk-metrics", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio risk metrics"""
    try:
        # Get portfolio
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        # Get all positions
        all_positions = []
        bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
        
        for bot in bots:
            if bot.status == "running":
                positions = trading_engine_manager.get_bot_positions(bot.id)
                for pos in positions:
                    all_positions.append({
                        'symbol': pos['symbol'],
                        'value': pos['current_price'] * abs(pos['quantity'])
                    })
        
        # Calculate risk metrics
        portfolio_value = float(portfolio.total_value)
        total_exposure = sum(pos['value'] for pos in all_positions)
        exposure_ratio = total_exposure / portfolio_value if portfolio_value > 0 else 0.0
        
        # Mock risk calculations (would use actual trading data)
        max_drawdown = 0.05  # 5%
        var_95 = portfolio_value * 0.02  # 2% VaR
        sharpe_ratio = 1.2
        win_rate = 0.65
        avg_trade_return = 0.015
        
        # Determine risk score
        if exposure_ratio < 0.5:
            risk_score = "LOW"
            recommendations = ["Consider increasing position sizes for better returns"]
        elif exposure_ratio < 0.8:
            risk_score = "MEDIUM"
            recommendations = ["Portfolio exposure is within normal range"]
        else:
            risk_score = "HIGH"
            recommendations = [
                "High portfolio exposure detected",
                "Consider reducing position sizes",
                "Review stop-loss levels"
            ]
        
        return RiskMetricsResponse(
            portfolio_value=portfolio_value,
            total_exposure=total_exposure,
            exposure_ratio=exposure_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_trade_return=avg_trade_return,
            risk_score=risk_score,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get risk metrics: {str(e)}"
        )

@router.get("/allocation", response_model=AllocationResponse)
async def get_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio allocation breakdown"""
    try:
        bots = db.query(TradingBot).filter(TradingBot.user_id == current_user.id).all()
        
        bot_allocations = []
        total_allocated = 0.0
        
        for bot in bots:
            allocation_pct = float(bot.allocated_percentage)
            total_allocated += allocation_pct
            
            bot_allocations.append({
                "bot_id": bot.id,
                "name": bot.name,
                "percentage": allocation_pct,
                "amount": float(bot.allocated_amount or 0),
                "status": bot.status,
                "strategy": "Mixed"  # Would be determined from bot configuration
            })
        
        unallocated = 100.0 - total_allocated
        
        recommendations = []
        if unallocated > 20:
            recommendations.append("Consider allocating more capital to trading bots")
        elif unallocated < 5:
            recommendations.append("Low cash reserve - consider maintaining some unallocated funds")
        
        if len(bots) > 10:
            recommendations.append("Consider consolidating similar trading strategies")
        
        return AllocationResponse(
            bot_allocations=bot_allocations,
            unallocated_percentage=unallocated,
            total_allocated=total_allocated,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error getting allocation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get allocation: {str(e)}"
        )

@router.post("/rebalance")
async def rebalance_portfolio(
    target_allocation: Dict[str, float],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rebalance portfolio to target allocation"""
    try:
        # Validate allocation adds up to 100%
        total_allocation = sum(target_allocation.values())
        if abs(total_allocation - 100.0) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target allocation must sum to 100%"
            )
        
        # Update bot allocations
        for bot_id_str, target_pct in target_allocation.items():
            bot_id = int(bot_id_str)
            bot = db.query(TradingBot).filter(
                TradingBot.id == bot_id,
                TradingBot.user_id == current_user.id
            ).first()
            
            if bot:
                bot.allocated_percentage = Decimal(str(target_pct))
                # Recalculate allocated amount based on current portfolio value
                portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
                if portfolio:
                    bot.allocated_amount = portfolio.total_value * Decimal(str(target_pct)) / 100
        
        db.commit()
        
        return {"message": "Portfolio rebalanced successfully"}
        
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebalance portfolio: {str(e)}"
        )