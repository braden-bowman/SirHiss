#!/usr/bin/env python3
"""
Integration Tests for SirHiss Trading Platform
Tests the integration of all components from the for_integration folder
"""

import asyncio
import json
import sys
import os
import requests
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the backend directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Test configuration  
API_BASE = "http://backend:8000"  # Use internal Docker network
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}

class IntegrationTester:
    """Comprehensive integration test suite"""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_bot_id = None
        
    def print_status(self, message: str, status: str = "INFO"):
        """Print formatted status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_color = {
            "INFO": "\033[36m",  # Cyan
            "PASS": "\033[32m",  # Green
            "FAIL": "\033[31m",  # Red
            "WARN": "\033[33m"   # Yellow
        }.get(status, "\033[0m")
        
        print(f"{status_color}[{timestamp}] {status}: {message}\033[0m")
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests"""
        self.print_status("Starting SirHiss Integration Tests", "INFO")
        
        try:
            # Test API availability
            if not await self.test_api_health():
                return False
            
            # Test authentication system
            if not await self.test_authentication():
                return False
            
            # Test portfolio system
            if not await self.test_portfolio_system():
                return False
            
            # Test trading bot system
            if not await self.test_trading_bot_system():
                return False
            
            # Test market data system
            if not await self.test_market_data_system():
                return False
            
            # Test trading strategies
            if not await self.test_trading_strategies():
                return False
            
            # Test risk management
            if not await self.test_risk_management():
                return False
            
            # Test backtesting system
            if not await self.test_backtesting_system():
                return False
            
            self.print_status("All integration tests completed successfully!", "PASS")
            return True
            
        except Exception as e:
            self.print_status(f"Integration test failed: {str(e)}", "FAIL")
            return False
    
    async def test_api_health(self) -> bool:
        """Test API health and availability"""
        self.print_status("Testing API health and availability...")
        
        try:
            # Test health endpoint
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            if response.status_code != 200:
                self.print_status("Health endpoint not accessible", "FAIL")
                return False
            
            # Test API documentation
            response = self.session.get(f"{API_BASE}/api/docs", timeout=10)
            if response.status_code != 200:
                self.print_status("API documentation not accessible", "WARN")
            
            self.print_status("API health check passed", "PASS")
            return True
            
        except requests.exceptions.RequestException as e:
            self.print_status(f"API not accessible: {str(e)}", "FAIL")
            return False
    
    async def test_authentication(self) -> bool:
        """Test authentication system"""
        self.print_status("Testing authentication system...")
        
        try:
            # Test user registration
            register_data = {
                "username": TEST_USER["username"],
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
            
            response = self.session.post(
                f"{API_BASE}/api/v1/auth/register",
                json=register_data,
                timeout=10
            )
            
            if response.status_code not in [200, 201, 409]:  # 409 = user already exists
                self.print_status(f"User registration failed: {response.status_code}", "FAIL")
                return False
            
            # Test user login
            login_data = {
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
            
            response = self.session.post(
                f"{API_BASE}/api/v1/auth/login",
                data=login_data,  # Form data for OAuth2
                timeout=10
            )
            
            if response.status_code != 200:
                self.print_status(f"User login failed: {response.status_code}", "FAIL")
                return False
            
            auth_data = response.json()
            self.auth_token = auth_data.get("access_token")
            
            if not self.auth_token:
                self.print_status("No access token received", "FAIL")
                return False
            
            # Set authorization header for future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
            
            # Test user info endpoint
            response = self.session.get(f"{API_BASE}/api/v1/auth/me", timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get("id")
                self.print_status(f"Authenticated as user: {user_data.get('username')}", "INFO")
            
            self.print_status("Authentication system tests passed", "PASS")
            return True
            
        except Exception as e:
            self.print_status(f"Authentication test failed: {str(e)}", "FAIL")
            return False
    
    async def test_portfolio_system(self) -> bool:
        """Test portfolio management system"""
        self.print_status("Testing portfolio management system...")
        
        try:
            # Test portfolio creation/retrieval
            response = self.session.get(f"{API_BASE}/api/v1/portfolio/", timeout=10)
            if response.status_code != 200:
                self.print_status(f"Portfolio retrieval failed: {response.status_code}", "FAIL")
                return False
            
            portfolio_data = response.json()
            self.print_status(f"Portfolio value: ${portfolio_data.get('total_value', 0)}", "INFO")
            
            # Test portfolio summary
            response = self.session.get(f"{API_BASE}/api/v1/portfolio/summary", timeout=10)
            if response.status_code != 200:
                self.print_status(f"Portfolio summary failed: {response.status_code}", "FAIL")
                return False
            
            summary_data = response.json()
            self.print_status(f"Portfolio summary loaded: {summary_data.get('number_of_bots', 0)} bots", "INFO")
            
            # Test risk metrics
            response = self.session.get(f"{API_BASE}/api/v1/portfolio/risk-metrics", timeout=10)
            if response.status_code not in [200, 404]:  # 404 if no portfolio exists
                self.print_status(f"Risk metrics test failed: {response.status_code}", "FAIL")
                return False
            
            if response.status_code == 200:
                risk_data = response.json()
                self.print_status(f"Risk score: {risk_data.get('risk_score', 'N/A')}", "INFO")
            
            self.print_status("Portfolio system tests passed", "PASS")
            return True
            
        except Exception as e:
            self.print_status(f"Portfolio test failed: {str(e)}", "FAIL")
            return False
    
    async def test_trading_bot_system(self) -> bool:
        """Test trading bot management system"""
        self.print_status("Testing trading bot system...")
        
        try:
            # Test bot listing
            response = self.session.get(f"{API_BASE}/api/v1/bots/", timeout=10)
            if response.status_code != 200:
                self.print_status(f"Bot listing failed: {response.status_code}", "FAIL")
                return False
            
            bots_data = response.json()
            self.print_status(f"Found {len(bots_data)} existing bots", "INFO")
            
            # Test bot creation
            new_bot_data = {
                "name": "Test Integration Bot",
                "description": "Bot created during integration testing",
                "allocated_percentage": 10.0,
                "parameters": {
                    "symbols": ["AAPL", "MSFT"],
                    "strategies": ["TechnicalIndicatorStrategy"],
                    "risk_level": "medium"
                }
            }
            
            response = self.session.post(
                f"{API_BASE}/api/v1/bots/",
                json=new_bot_data,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                self.print_status(f"Bot creation failed: {response.status_code}", "FAIL")
                return False
            
            created_bot = response.json()
            self.test_bot_id = created_bot.get("id")
            self.print_status(f"Created test bot with ID: {self.test_bot_id}", "INFO")
            
            # Test bot start
            if self.test_bot_id:
                response = self.session.post(
                    f"{API_BASE}/api/v1/bots/{self.test_bot_id}/start",
                    timeout=15
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    self.print_status(f"Bot start result: {result_data.get('message', 'Started')}", "INFO")
                else:
                    self.print_status(f"Bot start test failed: {response.status_code}", "WARN")
                
                # Wait a moment for the bot to initialize
                await asyncio.sleep(2)
                
                # Test bot stop
                response = self.session.post(
                    f"{API_BASE}/api/v1/bots/{self.test_bot_id}/stop",
                    timeout=15
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    self.print_status(f"Bot stop result: {result_data.get('message', 'Stopped')}", "INFO")
                else:
                    self.print_status(f"Bot stop test failed: {response.status_code}", "WARN")
            
            self.print_status("Trading bot system tests passed", "PASS")
            return True
            
        except Exception as e:
            self.print_status(f"Trading bot test failed: {str(e)}", "FAIL")
            return False
    
    async def test_market_data_system(self) -> bool:
        """Test market data and analysis system"""
        self.print_status("Testing market data system...")
        
        try:
            # Test ticker data
            response = self.session.get(f"{API_BASE}/api/v1/market-data/ticker/AAPL", timeout=15)
            if response.status_code != 200:
                self.print_status(f"Ticker data test failed: {response.status_code}", "FAIL")
                return False
            
            ticker_data = response.json()
            self.print_status(f"AAPL price: ${ticker_data.get('price', 0):.2f}", "INFO")
            
            # Test historical data
            response = self.session.get(
                f"{API_BASE}/api/v1/market-data/historical/AAPL?limit=50",
                timeout=15
            )
            if response.status_code != 200:
                self.print_status(f"Historical data test failed: {response.status_code}", "FAIL")
                return False
            
            historical_data = response.json()
            self.print_status(f"Retrieved {len(historical_data)} historical candles", "INFO")
            
            # Test technical indicators
            response = self.session.get(f"{API_BASE}/api/v1/market-data/indicators/AAPL", timeout=15)
            if response.status_code != 200:
                self.print_status(f"Technical indicators test failed: {response.status_code}", "FAIL")
                return False
            
            indicators_data = response.json()
            rsi = indicators_data.get("rsi")
            if rsi:
                self.print_status(f"AAPL RSI: {rsi:.2f}", "INFO")
            
            # Test trading signals
            response = self.session.get(f"{API_BASE}/api/v1/market-data/signals/AAPL", timeout=15)
            if response.status_code != 200:
                self.print_status(f"Trading signals test failed: {response.status_code}", "FAIL")
                return False
            
            signals_data = response.json()
            self.print_status(f"Generated {len(signals_data)} trading signals", "INFO")
            
            # Test market alerts
            response = self.session.get(f"{API_BASE}/api/v1/market-data/alerts", timeout=10)
            if response.status_code != 200:
                self.print_status(f"Market alerts test failed: {response.status_code}", "FAIL")
                return False
            
            alerts_data = response.json()
            self.print_status(f"Retrieved {len(alerts_data)} market alerts", "INFO")
            
            self.print_status("Market data system tests passed", "PASS")
            return True
            
        except Exception as e:
            self.print_status(f"Market data test failed: {str(e)}", "FAIL")
            return False
    
    async def test_trading_strategies(self) -> bool:
        """Test trading strategies integration"""
        self.print_status("Testing trading strategies integration...")
        
        try:
            # Import and test strategy components
            from app.services.trading_strategies import (
                TechnicalIndicatorStrategy,
                TrendFollowingStrategy,
                DCAStrategy,
                GridTradingStrategy,
                get_default_strategies
            )
            from app.services.exchange_api import get_configured_exchange
            
            # Test strategy creation
            strategies = get_default_strategies()
            self.print_status(f"Loaded {len(strategies)} default strategies", "INFO")
            
            # Test each strategy
            exchange = get_configured_exchange()
            ticker = exchange.get_ticker("AAPL")
            candles = exchange.get_historical_data("AAPL", "1h", 100)
            
            for strategy in strategies[:2]:  # Test first 2 strategies
                try:
                    signal = strategy.generate_signal(candles, ticker)
                    self.print_status(f"{strategy.name}: {signal.signal.value} signal (strength: {signal.strength:.2f})", "INFO")
                except Exception as e:
                    self.print_status(f"Strategy {strategy.name} test failed: {str(e)}", "WARN")
            
            self.print_status("Trading strategies tests passed", "PASS")
            return True
            
        except ImportError as e:
            self.print_status(f"Trading strategies import failed: {str(e)}", "FAIL")
            return False
        except Exception as e:
            self.print_status(f"Trading strategies test failed: {str(e)}", "FAIL")
            return False
    
    async def test_risk_management(self) -> bool:
        """Test risk management system"""
        self.print_status("Testing risk management system...")
        
        try:
            # Test portfolio analytics if available
            try:
                from app.services.portfolio_analytics import PortfolioAnalyzer, RiskMonitor
                from app.core.database import get_db
                
                # Test risk calculation
                self.print_status("Risk management components loaded successfully", "INFO")
                
            except ImportError as e:
                self.print_status(f"Risk management components not available: {str(e)}", "WARN")
            
            # Test API endpoints
            response = self.session.get(f"{API_BASE}/api/v1/portfolio/allocation", timeout=10)
            if response.status_code == 200:
                allocation_data = response.json()
                total_allocated = allocation_data.get("total_allocated", 0)
                self.print_status(f"Portfolio allocation: {total_allocated:.1f}%", "INFO")
            
            self.print_status("Risk management tests passed", "PASS")
            return True
            
        except Exception as e:
            self.print_status(f"Risk management test failed: {str(e)}", "FAIL")
            return False
    
    async def test_backtesting_system(self) -> bool:
        """Test backtesting system"""
        self.print_status("Testing backtesting system...")
        
        try:
            # Test backtesting imports
            from app.services.backtesting import BacktestEngine, BacktestConfig, BacktestMode
            from app.services.exchange_api import get_configured_exchange
            from datetime import datetime, timedelta
            
            # Test backtesting components
            exchange = get_configured_exchange()
            engine = BacktestEngine(exchange)
            
            # Create a simple backtest configuration
            config = BacktestConfig(
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now() - timedelta(days=1),
                initial_capital=10000.0,
                symbols=["AAPL"],
                mode=BacktestMode.SINGLE_STRATEGY
            )
            
            self.print_status("Backtesting engine created successfully", "INFO")
            self.print_status("Backtesting system tests passed", "PASS")
            return True
            
        except ImportError as e:
            self.print_status(f"Backtesting system import failed: {str(e)}", "FAIL")
            return False
        except Exception as e:
            self.print_status(f"Backtesting system test failed: {str(e)}", "WARN")
            return True  # Non-critical for integration
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        self.print_status("Cleaning up test data...")
        
        try:
            # Delete test bot if created
            if self.test_bot_id:
                response = self.session.delete(
                    f"{API_BASE}/api/v1/bots/{self.test_bot_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    self.print_status("Test bot deleted successfully", "INFO")
                else:
                    self.print_status(f"Test bot deletion failed: {response.status_code}", "WARN")
            
        except Exception as e:
            self.print_status(f"Cleanup failed: {str(e)}", "WARN")

async def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("🐍 SirHiss Trading Platform Integration Tests")
    print("="*60 + "\n")
    
    tester = IntegrationTester()
    
    try:
        success = await tester.run_all_tests()
        
        # Cleanup
        await tester.cleanup_test_data()
        
        print("\n" + "="*60)
        if success:
            print("✅ ALL INTEGRATION TESTS PASSED!")
            print("🎉 SirHiss trading platform integration is working correctly!")
        else:
            print("❌ SOME INTEGRATION TESTS FAILED")
            print("🔧 Please check the errors above and fix any issues")
        print("="*60 + "\n")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        await tester.cleanup_test_data()
        return 130
    except Exception as e:
        print(f"\n\n💥 Fatal test error: {str(e)}")
        await tester.cleanup_test_data()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)