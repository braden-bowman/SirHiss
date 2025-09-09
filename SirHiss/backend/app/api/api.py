"""
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter
from app.api.endpoints import auth, bots, portfolio, market, market_data, settings, algorithms, security, account

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(account.router, prefix="/account", tags=["account"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(security.router, prefix="/security", tags=["security"])
api_router.include_router(bots.router, prefix="/bots", tags=["trading_bots"]) 
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(market.router, prefix="/market", tags=["market_data"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market_analysis"])
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["algorithms"])