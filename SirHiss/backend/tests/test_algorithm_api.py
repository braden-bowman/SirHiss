"""
Integration tests for algorithm management API endpoints
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.trading_bot import TradingBot
from app.models.algorithm_config import AlgorithmConfig, AlgorithmTemplate
from app.core.security import create_access_token


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_algorithms.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_user():
    """Create test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="fake_hashed_password"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="module")
def test_bot(test_user):
    """Create test trading bot"""
    db = TestingSessionLocal()
    bot = TradingBot(
        user_id=test_user.id,
        portfolio_id=1,  # Assuming portfolio exists
        name="Test Bot",
        description="Test bot for algorithm testing",
        allocated_percentage=25.0,
        status="stopped"
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    db.close()
    return bot


@pytest.fixture(scope="module")
def auth_headers(test_user):
    """Create authentication headers"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_algorithm_templates():
    """Create sample algorithm templates"""
    db = TestingSessionLocal()
    
    templates = [
        AlgorithmTemplate(
            name="Conservative Technical Analysis",
            algorithm_type="AdvancedTechnicalIndicator",
            description="RSI, MACD, and Bollinger Bands with conservative settings",
            category="Technical Analysis",
            default_position_size=0.15,
            default_parameters={
                "rsi_period": 14,
                "rsi_oversold": 25,
                "rsi_overbought": 75,
                "macd_fast": 8,
                "macd_slow": 21
            },
            difficulty_level="beginner",
            min_capital=500.0,
            recommended_timeframe="1 hour to daily"
        ),
        AlgorithmTemplate(
            name="Aggressive Scalping",
            algorithm_type="Scalping",
            description="High-frequency trading for quick profits",
            category="High Frequency",
            default_position_size=0.05,
            default_parameters={
                "min_interval": 5,
                "spread_threshold": 0.001,
                "volume_threshold": 1500
            },
            difficulty_level="advanced",
            min_capital=5000.0,
            recommended_timeframe="1 second to 5 minutes"
        )
    ]
    
    for template in templates:
        db.add(template)
    
    db.commit()
    
    for template in templates:
        db.refresh(template)
    
    db.close()
    return templates


class TestAlgorithmTemplates:
    """Test algorithm template endpoints"""
    
    def test_get_algorithm_templates(self, client, sample_algorithm_templates, auth_headers):
        """Test getting algorithm templates"""
        response = client.get("/api/v1/algorithms/templates", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        
        # Check template structure
        template = data[0]
        assert "id" in template
        assert "name" in template
        assert "algorithm_type" in template
        assert "description" in template
        assert "category" in template
        assert "default_parameters" in template
        assert "difficulty_level" in template
    
    def test_filter_templates_by_category(self, client, sample_algorithm_templates, auth_headers):
        """Test filtering templates by category"""
        response = client.get(
            "/api/v1/algorithms/templates?category=Technical Analysis",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(template["category"] == "Technical Analysis" for template in data)
    
    def test_filter_templates_by_difficulty(self, client, sample_algorithm_templates, auth_headers):
        """Test filtering templates by difficulty"""
        response = client.get(
            "/api/v1/algorithms/templates?difficulty=beginner",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(template["difficulty_level"] == "beginner" for template in data)
    
    def test_get_algorithm_types(self, client, auth_headers):
        """Test getting algorithm types"""
        response = client.get("/api/v1/algorithms/types", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert isinstance(data, dict)
        assert "Technical Analysis" in data
        assert "High Frequency" in data
        
        # Check that each category has algorithm types
        assert isinstance(data["Technical Analysis"], list)
        assert len(data["Technical Analysis"]) > 0


class TestBotAlgorithms:
    """Test bot algorithm management endpoints"""
    
    def test_get_bot_algorithms_empty(self, client, test_bot, auth_headers):
        """Test getting algorithms for bot with no algorithms"""
        response = client.get(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_create_bot_algorithm(self, client, test_bot, auth_headers):
        """Test creating a new algorithm for a bot"""
        algorithm_data = {
            "algorithm_type": "AdvancedTechnicalIndicator",
            "algorithm_name": "My Technical Analysis",
            "position_size": 0.15,
            "max_position_size": 0.3,
            "stop_loss": 0.1,
            "take_profit": 0.2,
            "parameters": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70
            }
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["algorithm_name"] == "My Technical Analysis"
        assert data["algorithm_type"] == "AdvancedTechnicalIndicator"
        assert data["position_size"] == 0.15
        assert data["enabled"] is True
        assert "id" in data
        
        return data["id"]  # Return for use in other tests
    
    def test_create_algorithm_from_template(self, client, test_bot, sample_algorithm_templates, auth_headers):
        """Test creating algorithm from template"""
        template = sample_algorithm_templates[0]
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms/from-template/{template.id}",
            params={
                "algorithm_name": "Template-based Algorithm",
                "position_size": 0.2
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["algorithm_name"] == "Template-based Algorithm"
        assert data["algorithm_type"] == template.algorithm_type
        assert data["position_size"] == 0.2
        assert data["parameters"] == template.default_parameters
    
    def test_create_duplicate_algorithm_name(self, client, test_bot, auth_headers):
        """Test creating algorithm with duplicate name fails"""
        algorithm_data = {
            "algorithm_type": "DynamicDCA",
            "algorithm_name": "My Technical Analysis",  # Same name as previous test
            "position_size": 0.1
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_get_bot_algorithms_with_data(self, client, test_bot, auth_headers):
        """Test getting algorithms after creating some"""
        response = client.get(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        # Check algorithm structure
        algorithm = data[0]
        assert "id" in algorithm
        assert "algorithm_type" in algorithm
        assert "algorithm_name" in algorithm
        assert "parameters" in algorithm
        assert "total_trades" in algorithm
        assert "win_rate" in algorithm
    
    def test_unauthorized_access(self, client, test_bot):
        """Test accessing bot algorithms without authentication"""
        response = client.get(f"/api/v1/algorithms/bots/{test_bot.id}/algorithms")
        assert response.status_code == 401
    
    def test_access_other_user_bot(self, client, auth_headers):
        """Test accessing another user's bot fails"""
        # Try to access a non-existent bot or bot belonging to another user
        response = client.get(
            "/api/v1/algorithms/bots/999/algorithms",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestAlgorithmConfiguration:
    """Test algorithm configuration management"""
    
    @pytest.fixture
    def created_algorithm(self, client, test_bot, auth_headers):
        """Create an algorithm for testing configuration"""
        algorithm_data = {
            "algorithm_type": "AdvancedTechnicalIndicator",
            "algorithm_name": "Config Test Algorithm",
            "position_size": 0.1,
            "parameters": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "macd_fast": 12,
                "macd_slow": 26
            }
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        return response.json()
    
    def test_update_algorithm(self, client, created_algorithm, auth_headers):
        """Test updating algorithm configuration"""
        algorithm_id = created_algorithm["id"]
        
        update_data = {
            "algorithm_name": "Updated Algorithm Name",
            "position_size": 0.2,
            "enabled": False,
            "parameters": {
                "rsi_period": 21,
                "rsi_oversold": 25
            }
        }
        
        response = client.put(
            f"/api/v1/algorithms/algorithms/{algorithm_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["algorithm_name"] == "Updated Algorithm Name"
        assert data["position_size"] == 0.2
        assert data["enabled"] is False
        
        # Parameters should be merged
        assert data["parameters"]["rsi_period"] == 21
        assert data["parameters"]["rsi_oversold"] == 25
        # Original parameters should be preserved if not updated
        assert data["parameters"]["rsi_overbought"] == 70
    
    def test_toggle_algorithm(self, client, created_algorithm, auth_headers):
        """Test toggling algorithm enabled state"""
        algorithm_id = created_algorithm["id"]
        original_state = created_algorithm["enabled"]
        
        response = client.post(
            f"/api/v1/algorithms/algorithms/{algorithm_id}/toggle",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] != original_state
    
    def test_get_algorithm_parameters(self, client, created_algorithm, auth_headers):
        """Test getting algorithm parameters with descriptions"""
        algorithm_id = created_algorithm["id"]
        
        response = client.get(
            f"/api/v1/algorithms/algorithms/{algorithm_id}/parameters",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have parameter descriptions
        assert "rsi_period" in data
        param_info = data["rsi_period"]
        assert "value" in param_info
        assert "description" in param_info
        assert "type" in param_info
        assert "min" in param_info
        assert "max" in param_info
    
    def test_update_algorithm_parameters(self, client, created_algorithm, auth_headers):
        """Test updating algorithm parameters in real-time"""
        algorithm_id = created_algorithm["id"]
        
        new_parameters = {
            "rsi_period": 21,
            "rsi_oversold": 25,
            "rsi_overbought": 75
        }
        
        response = client.put(
            f"/api/v1/algorithms/algorithms/{algorithm_id}/parameters",
            json=new_parameters,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["rsi_period"] == 21
        assert data["rsi_oversold"] == 25
        assert data["rsi_overbought"] == 75
    
    def test_delete_algorithm(self, client, created_algorithm, auth_headers):
        """Test deleting algorithm"""
        algorithm_id = created_algorithm["id"]
        
        response = client.delete(
            f"/api/v1/algorithms/algorithms/{algorithm_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify algorithm is deleted
        response = client.get(
            f"/api/v1/algorithms/algorithms/{algorithm_id}/parameters",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestAlgorithmPerformance:
    """Test algorithm performance tracking endpoints"""
    
    @pytest.fixture
    def algorithm_with_performance(self, client, test_bot, auth_headers):
        """Create algorithm and simulate some performance data"""
        algorithm_data = {
            "algorithm_type": "TrendFollowing",
            "algorithm_name": "Performance Test Algorithm",
            "position_size": 0.1
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        algorithm = response.json()
        
        # Simulate some performance by updating the database directly
        db = TestingSessionLocal()
        algo_config = db.query(AlgorithmConfig).filter(
            AlgorithmConfig.id == algorithm["id"]
        ).first()
        
        if algo_config:
            algo_config.total_trades = 10
            algo_config.winning_trades = 7
            algo_config.win_rate = 0.7
            algo_config.total_return = 15.5
            algo_config.sharpe_ratio = 1.2
            algo_config.max_drawdown = -5.0
            db.commit()
        
        db.close()
        return algorithm
    
    def test_get_algorithm_performance(self, client, algorithm_with_performance, auth_headers):
        """Test getting algorithm performance metrics"""
        algorithm_id = algorithm_with_performance["id"]
        
        response = client.get(
            f"/api/v1/algorithms/algorithms/{algorithm_id}/performance",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["algorithm_name"] == "Performance Test Algorithm"
        assert data["total_trades"] == 10
        assert data["winning_trades"] == 7
        assert data["win_rate"] == 0.7
        assert data["total_return"] == 15.5
        assert data["sharpe_ratio"] == 1.2
        assert data["max_drawdown"] == -5.0
        assert "recent_signals" in data
    
    def test_get_performance_with_limit(self, client, algorithm_with_performance, auth_headers):
        """Test getting performance with signal limit"""
        algorithm_id = algorithm_with_performance["id"]
        
        response = client.get(
            f"/api/v1/algorithms/algorithms/{algorithm_id}/performance?limit=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["recent_signals"]) <= 5


class TestErrorHandling:
    """Test error handling in algorithm API"""
    
    def test_invalid_algorithm_type(self, client, test_bot, auth_headers):
        """Test creating algorithm with invalid type"""
        algorithm_data = {
            "algorithm_type": "InvalidAlgorithmType",
            "algorithm_name": "Invalid Algorithm",
            "position_size": 0.1
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        # Should either accept it (if validation is loose) or reject it
        # The exact behavior depends on implementation
        assert response.status_code in [200, 400]
    
    def test_invalid_position_size(self, client, test_bot, auth_headers):
        """Test creating algorithm with invalid position size"""
        algorithm_data = {
            "algorithm_type": "AdvancedTechnicalIndicator",
            "algorithm_name": "Invalid Position Size",
            "position_size": 1.5  # > 100%
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_nonexistent_algorithm(self, client, auth_headers):
        """Test accessing nonexistent algorithm"""
        response = client.get(
            "/api/v1/algorithms/algorithms/999999/parameters",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_nonexistent_template(self, client, test_bot, auth_headers):
        """Test creating algorithm from nonexistent template"""
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms/from-template/999999",
            params={
                "algorithm_name": "From Nonexistent Template"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestParameterValidation:
    """Test parameter validation for different algorithm types"""
    
    def test_technical_indicator_parameters(self, client, test_bot, auth_headers):
        """Test parameter validation for technical indicator strategy"""
        algorithm_data = {
            "algorithm_type": "AdvancedTechnicalIndicator",
            "algorithm_name": "Parameter Validation Test",
            "position_size": 0.1,
            "parameters": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "macd_fast": 12,
                "macd_slow": 26,
                "bb_period": 20,
                "bb_std": 2.0
            }
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["parameters"]["rsi_period"] == 14
        assert data["parameters"]["rsi_oversold"] == 30
    
    def test_scalping_parameters(self, client, test_bot, auth_headers):
        """Test parameter validation for scalping strategy"""
        algorithm_data = {
            "algorithm_type": "Scalping",
            "algorithm_name": "Scalping Parameter Test",
            "position_size": 0.05,
            "parameters": {
                "min_interval": 5,
                "spread_threshold": 0.002,
                "volume_threshold": 1000
            }
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["parameters"]["min_interval"] == 5
        assert data["parameters"]["spread_threshold"] == 0.002


class TestConcurrency:
    """Test concurrent operations on algorithms"""
    
    def test_concurrent_parameter_updates(self, client, test_bot, auth_headers):
        """Test concurrent parameter updates don't cause conflicts"""
        # Create algorithm
        algorithm_data = {
            "algorithm_type": "AdvancedTechnicalIndicator",
            "algorithm_name": "Concurrency Test",
            "position_size": 0.1,
            "parameters": {"rsi_period": 14}
        }
        
        response = client.post(
            f"/api/v1/algorithms/bots/{test_bot.id}/algorithms",
            json=algorithm_data,
            headers=auth_headers
        )
        algorithm_id = response.json()["id"]
        
        # Simulate concurrent updates
        import threading
        
        def update_parameters(param_value):
            client.put(
                f"/api/v1/algorithms/algorithms/{algorithm_id}/parameters",
                json={"rsi_period": param_value},
                headers=auth_headers
            )
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_parameters, args=(14 + i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify final state is consistent
        response = client.get(
            f"/api/v1/algorithms/algorithms/{algorithm_id}/parameters",
            headers=auth_headers
        )
        assert response.status_code == 200
        # Final value should be one of the updated values
        final_value = response.json()["rsi_period"]["value"]
        assert final_value in range(14, 19)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])