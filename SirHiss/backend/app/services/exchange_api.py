"""
Exchange API Abstraction Layer for SirHiss Trading Platform
Provides unified interface for multiple cryptocurrency exchanges
"""

import asyncio
import time
import logging
import requests
import hmac
import hashlib
import base64
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd

from ..core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    timestamp: Optional[float] = None

@dataclass
class Balance:
    asset: str
    free: float
    locked: float
    total: float

@dataclass
class Ticker:
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: float

@dataclass
class Candle:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float

class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_calls: int, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        now = time.time()
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.calls.append(now)

class BaseExchange(ABC):
    """Abstract base class for exchange implementations"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", sandbox: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)
        self.session = requests.Session()
        
    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker:
        """Get current ticker information"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, interval: str, limit: int = 100) -> List[Candle]:
        """Get historical OHLCV data"""
        pass
    
    @abstractmethod
    def get_balance(self, asset: str = None) -> Dict[str, Balance]:
        """Get account balance"""
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> Order:
        """Place an order"""
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    def get_order_status(self, symbol: str, order_id: str) -> Order:
        """Get order status"""
        pass
    
    def _make_request(self, method: str, url: str, params: dict = None, data: dict = None) -> dict:
        """Make HTTP request with rate limiting and error handling"""
        self.rate_limiter.wait_if_needed()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, params=params, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            raise

class BinanceAPI(BaseExchange):
    """Binance exchange implementation"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", sandbox: bool = True):
        super().__init__(api_key, api_secret, sandbox)
        self.base_url = "https://testnet.binance.vision/api/v3" if sandbox else "https://api.binance.com/api/v3"
        
    def _generate_signature(self, params: dict) -> str:
        """Generate HMAC SHA256 signature for Binance API"""
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _signed_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Make signed request to Binance API"""
        if params is None:
            params = {}
        
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        url = f"{self.base_url}{endpoint}"
        
        response = self.session.request(method, url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker for symbol"""
        try:
            url = f"{self.base_url}/ticker/24hr"
            params = {"symbol": symbol.upper()}
            data = self._make_request("GET", url, params)
            
            return Ticker(
                symbol=symbol,
                price=float(data['lastPrice']),
                bid=float(data['bidPrice']),
                ask=float(data['askPrice']),
                volume=float(data['volume']),
                timestamp=time.time()
            )
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {e}")
            raise
    
    def get_historical_data(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Candle]:
        """Get historical kline data"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": min(limit, 1000)  # Binance limit
            }
            data = self._make_request("GET", url, params)
            
            candles = []
            for kline in data:
                candles.append(Candle(
                    timestamp=kline[0] / 1000,  # Convert to seconds
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5])
                ))
            
            return candles
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            raise
    
    def get_balance(self, asset: str = None) -> Dict[str, Balance]:
        """Get account balance"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials required for balance information")
            
            data = self._signed_request("GET", "/account")
            balances = {}
            
            for balance_data in data['balances']:
                asset_name = balance_data['asset']
                free_amount = float(balance_data['free'])
                locked_amount = float(balance_data['locked'])
                
                if asset is None or asset_name == asset.upper():
                    balances[asset_name] = Balance(
                        asset=asset_name,
                        free=free_amount,
                        locked=locked_amount,
                        total=free_amount + locked_amount
                    )
            
            return balances if asset is None else {asset.upper(): balances.get(asset.upper())}
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise
    
    def place_order(self, order: Order) -> Order:
        """Place order on Binance"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials required for trading")
            
            params = {
                "symbol": order.symbol.upper(),
                "side": order.side.value.upper(),
                "type": order.type.value.upper(),
                "quantity": str(order.quantity)
            }
            
            if order.type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                params["price"] = str(order.price)
                params["timeInForce"] = "GTC"  # Good Till Cancelled
            
            if order.type in [OrderType.STOP, OrderType.STOP_LIMIT]:
                params["stopPrice"] = str(order.stop_price)
            
            data = self._signed_request("POST", "/order", params)
            
            order.order_id = str(data['orderId'])
            order.status = OrderStatus.PENDING
            order.timestamp = data['transactTime'] / 1000
            
            return order
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            order.status = OrderStatus.REJECTED
            raise
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order"""
        try:
            params = {
                "symbol": symbol.upper(),
                "orderId": order_id
            }
            self._signed_request("DELETE", "/order", params)
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Order:
        """Get order status"""
        try:
            params = {
                "symbol": symbol.upper(),
                "orderId": order_id
            }
            data = self._signed_request("GET", "/order", params)
            
            status_map = {
                "NEW": OrderStatus.PENDING,
                "PARTIALLY_FILLED": OrderStatus.PENDING,
                "FILLED": OrderStatus.FILLED,
                "CANCELED": OrderStatus.CANCELLED,
                "REJECTED": OrderStatus.REJECTED
            }
            
            return Order(
                symbol=data['symbol'],
                side=OrderSide(data['side'].lower()),
                type=OrderType(data['type'].lower()),
                quantity=float(data['origQty']),
                price=float(data['price']) if data['price'] != '0.00000000' else None,
                order_id=str(data['orderId']),
                status=status_map.get(data['status'], OrderStatus.PENDING),
                timestamp=data['time'] / 1000
            )
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {e}")
            raise

class RobinhoodAPI(BaseExchange):
    """Robinhood exchange implementation with demo data"""
    
    def __init__(self, username: str = "", password: str = "", sandbox: bool = True):
        super().__init__()
        self.username = username
        self.password = password
        self.sandbox = sandbox
        self.token = None
        self.base_url = "https://api.robinhood.com" if not sandbox else "https://api.robinhood.com"
        
    def _authenticate(self):
        """Authenticate with Robinhood (simplified demo)"""
        if not self.token:
            logger.info("Using Robinhood demo mode with simulated data")
            self.token = "demo_token"
    
    def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker - using demo data for development"""
        self._authenticate()
        
        # For demo purposes, return reasonable mock data
        import random
        base_prices = {
            'AAPL': 185.25,
            'MSFT': 365.80, 
            'GOOGL': 142.35,
            'AMZN': 151.94,
            'TSLA': 248.50,
            'NVDA': 875.30
        }
        
        base_price = base_prices.get(symbol.upper(), 100.0)
        price = base_price + random.uniform(-5, 5)
        
        return Ticker(
            symbol=symbol,
            price=price,
            bid=price - 0.01,
            ask=price + 0.01,
            volume=random.uniform(1000, 10000),
            timestamp=time.time()
        )
    
    def get_historical_data(self, symbol: str, interval: str = "hour", limit: int = 100) -> List[Candle]:
        """Get historical data - demo implementation"""
        self._authenticate()
        
        # Mock historical data with realistic price movements
        candles = []
        base_price = 100.0
        current_time = time.time()
        
        for i in range(limit):
            timestamp = current_time - (i * 3600)  # 1 hour intervals
            price = base_price + (i * 0.1) + random.uniform(-2, 2)
            
            candles.append(Candle(
                timestamp=timestamp,
                open=price + random.uniform(-0.5, 0.5),
                high=price + random.uniform(0, 1),
                low=price - random.uniform(0, 1),
                close=price,
                volume=random.uniform(100, 1000)
            ))
        
        return list(reversed(candles))  # Return chronological order
    
    def get_balance(self, asset: str = None) -> Dict[str, Balance]:
        """Get balance - demo implementation"""
        self._authenticate()
        
        # Mock balance data
        mock_balances = {
            "USD": Balance("USD", 10000.0, 0.0, 10000.0),
            "BTC": Balance("BTC", 0.1, 0.0, 0.1),
            "ETH": Balance("ETH", 1.0, 0.0, 1.0)
        }
        
        if asset:
            return {asset.upper(): mock_balances.get(asset.upper())}
        return mock_balances
    
    def place_order(self, order: Order) -> Order:
        """Place order - demo implementation"""
        self._authenticate()
        
        # Mock order placement
        order.order_id = f"RH_{int(time.time())}"
        order.status = OrderStatus.PENDING
        order.timestamp = time.time()
        
        logger.info(f"Demo order placed: {order}")
        return order
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order - demo implementation"""
        self._authenticate()
        logger.info(f"Demo order cancelled: {order_id}")
        return True
    
    def get_order_status(self, symbol: str, order_id: str) -> Order:
        """Get order status - demo implementation"""
        self._authenticate()
        
        # Return mock filled order
        return Order(
            symbol=symbol,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=1.0,
            order_id=order_id,
            status=OrderStatus.FILLED,
            timestamp=time.time()
        )

class ExchangeFactory:
    """Factory class for creating exchange instances"""
    
    @staticmethod
    def create_exchange(exchange_name: str, **kwargs) -> BaseExchange:
        """Create exchange instance by name"""
        exchange_name = exchange_name.lower()
        
        if exchange_name == "binance":
            return BinanceAPI(**kwargs)
        elif exchange_name == "robinhood":
            return RobinhoodAPI(**kwargs)
        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}")

# Integration with SirHiss settings
def get_configured_exchange() -> BaseExchange:
    """Get exchange instance from application settings"""
    # This would read from the database or config
    # For now, return a demo instance
    return ExchangeFactory.create_exchange("robinhood", sandbox=True)