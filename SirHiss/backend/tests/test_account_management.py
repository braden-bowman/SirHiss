"""
Comprehensive test suite for account management features
Tests account information, API status checking, and enhanced user model
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.api_credential import ApiCredential
from app.core.security import get_password_hash, create_access_token
from app.core.encryption import credential_encryption


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testaccountuser",
        "email": "test.account@example.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def test_user_with_account(test_db):
    """Create a test user with full account information"""
    db = TestingSessionLocal()
    
    # Create user with account number
    user = User(
        account_number="SH-TEST-ACCT-001",
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        is_active=True,
        full_name="Test User",
        phone_number="+1234567890",
        registration_ip="127.0.0.1",
        email_verified=True,
        account_status="active",
        risk_level="medium",
        kyc_status="verified",
        login_count=5
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    return user


@pytest.fixture
def auth_token(test_user_with_account):
    """Generate authentication token for test user"""
    return create_access_token(data={"sub": test_user_with_account.username})


class TestUserAccountModel:
    """Test enhanced User model functionality"""
    
    def test_generate_account_number(self):
        """Test account number generation"""
        account_number = User.generate_account_number()
        
        # Check format: SH-XXXX-XXXX-XXXX
        assert account_number.startswith("SH-")
        parts = account_number.split("-")
        assert len(parts) == 4
        assert parts[0] == "SH"
        assert all(len(part) == 4 for part in parts[1:])
        assert all(part.isalnum() for part in parts[1:])
        assert all(part.isupper() for part in parts[1:])
    
    def test_unique_account_numbers(self):
        """Test that generated account numbers are unique"""
        numbers = [User.generate_account_number() for _ in range(100)]
        assert len(set(numbers)) == 100  # All should be unique
    
    def test_update_login_info(self, test_user_with_account):
        """Test login information tracking"""
        initial_count = test_user_with_account.login_count
        test_user_with_account.update_login_info("192.168.1.1")
        
        assert test_user_with_account.login_count == initial_count + 1
        assert test_user_with_account.last_login_ip == "192.168.1.1"
        assert test_user_with_account.last_login_at is not None
        assert isinstance(test_user_with_account.last_login_at, datetime)
    
    def test_get_account_age_days(self, test_user_with_account):
        """Test account age calculation"""
        age_days = test_user_with_account.get_account_age_days()
        assert isinstance(age_days, int)
        assert age_days >= 0
    
    def test_is_verified(self, test_user_with_account):
        """Test account verification status"""
        assert test_user_with_account.is_verified() == True
        
        test_user_with_account.kyc_status = "pending"
        assert test_user_with_account.is_verified() == False
        
        test_user_with_account.email_verified = False
        assert test_user_with_account.is_verified() == False
    
    def test_get_display_name(self, test_user_with_account):
        """Test display name generation"""
        assert test_user_with_account.get_display_name() == "Test User"
        
        test_user_with_account.full_name = None
        assert test_user_with_account.get_display_name() == "Testuser"


class TestAccountRegistration:
    """Test enhanced user registration with account features"""
    
    def test_register_user_with_account_number(self, test_db, test_user_data):
        """Test user registration generates account number"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "account_number" in data
        assert data["account_number"].startswith("SH-")
        assert data["account_status"] == "active"
        assert data["risk_level"] == "medium"
        assert data["kyc_status"] == "pending"
        assert data["email_verified"] == False
        assert data["login_count"] == 0
    
    def test_account_number_uniqueness(self, test_db):
        """Test that each user gets a unique account number"""
        users_data = [
            {
                "username": f"testuser{i}",
                "email": f"test{i}@example.com",
                "password": "SecurePass123!"
            }
            for i in range(5)
        ]
        
        account_numbers = []
        for user_data in users_data:
            response = client.post("/api/v1/auth/register", json=user_data)
            assert response.status_code == 200
            account_numbers.append(response.json()["account_number"])
        
        # All account numbers should be unique
        assert len(set(account_numbers)) == 5
    
    def test_login_updates_tracking_info(self, test_db, test_user_data):
        """Test that login updates tracking information"""
        # Register user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login multiple times
        for i in range(3):
            response = client.post("/api/v1/auth/login/simple", json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            })
            assert response.status_code == 200
            
            user_data = response.json()["user"]
            assert user_data["login_count"] == i + 1
            assert user_data["last_login_at"] is not None


class TestAccountSummaryEndpoint:
    """Test account summary API endpoint"""
    
    def test_account_summary_success(self, test_db, test_user_with_account, auth_token):
        """Test successful account summary retrieval"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/account/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check account information
        assert data["id"] == test_user_with_account.id
        assert data["account_number"] == test_user_with_account.account_number
        assert data["username"] == test_user_with_account.username
        assert data["email"] == test_user_with_account.email
        assert data["display_name"] == "Test User"
        
        # Check status information
        assert data["account_status"] == "active"
        assert data["account_status_color"] == "green"
        assert data["risk_level"] == "medium"
        assert data["kyc_status"] == "verified"
        assert data["email_verified"] == True
        assert data["is_verified"] == True
        
        # Check metrics
        assert data["account_age_days"] >= 0
        assert data["login_count"] == 5
        
        # Check API connections summary
        assert "total_api_connections" in data
        assert "active_api_connections" in data
        assert "connected_apis" in data
        assert "error_apis" in data
        assert "api_connections" in data
        assert isinstance(data["api_connections"], list)
    
    def test_account_summary_unauthorized(self, test_db):
        """Test account summary without authentication"""
        response = client.get("/api/v1/account/summary")
        assert response.status_code == 401
    
    def test_account_summary_invalid_token(self, test_db):
        """Test account summary with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/account/summary", headers=headers)
        assert response.status_code == 401


class TestApiConnectionStatus:
    """Test API connection status functionality"""
    
    def test_empty_api_connections(self, test_db, test_user_with_account, auth_token):
        """Test account summary with no API connections"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/account/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_api_connections"] == 0
        assert data["active_api_connections"] == 0
        assert data["connected_apis"] == 0
        assert data["error_apis"] == 0
        assert data["api_connections"] == []
    
    def test_api_connections_with_credentials(self, test_db, test_user_with_account, auth_token):
        """Test account summary with API credentials"""
        db = TestingSessionLocal()
        
        # Create test API credential
        test_credentials = {"username": "test_user", "password": "test_pass"}
        encrypted_creds = credential_encryption.encrypt_credentials(test_credentials)
        
        api_cred = ApiCredential(
            user_id=test_user_with_account.id,
            platform="robinhood",
            name="Test Robinhood",
            encrypted_credentials=encrypted_creds,
            is_active=True,
            status="connected"
        )
        
        db.add(api_cred)
        db.commit()
        db.close()
        
        # Test account summary
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/account/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_api_connections"] == 1
        assert data["active_api_connections"] == 1
        assert len(data["api_connections"]) == 1
        
        api_conn = data["api_connections"][0]
        assert api_conn["platform"] == "robinhood"
        assert api_conn["name"] == "Test Robinhood"
        assert api_conn["is_active"] == True
        assert "status" in api_conn
        assert "status_color" in api_conn
    
    def test_refresh_api_status(self, test_db, test_user_with_account, auth_token):
        """Test API connection status refresh"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/v1/account/refresh-api-status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "updated_count" in data
        assert "timestamp" in data
        assert data["updated_count"] >= 0
    
    def test_api_status_endpoint(self, test_db, test_user_with_account, auth_token):
        """Test standalone API status endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test without connections
        response = client.get("/api/v1/account/api-status", headers=headers)
        assert response.status_code == 200
        assert response.json() == []
        
        # Test with test_connections parameter
        response = client.get("/api/v1/account/api-status?test_connections=true", headers=headers)
        assert response.status_code == 200
        assert response.json() == []


class TestAccountSecurity:
    """Test security aspects of account management"""
    
    def test_account_summary_user_isolation(self, test_db):
        """Test that users can only access their own account data"""
        # Create two users
        user1_data = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "SecurePass123!"
        }
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "SecurePass123!"
        }
        
        # Register both users
        client.post("/api/v1/auth/register", json=user1_data)
        client.post("/api/v1/auth/register", json=user2_data)
        
        # Login as user1
        login_response = client.post("/api/v1/auth/login/simple", json={
            "username": user1_data["username"],
            "password": user1_data["password"]
        })
        user1_token = login_response.json()["access_token"]
        user1_account_number = login_response.json()["user"]["account_number"]
        
        # Login as user2
        login_response = client.post("/api/v1/auth/login/simple", json={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        user2_token = login_response.json()["access_token"]
        user2_account_number = login_response.json()["user"]["account_number"]
        
        # Verify account numbers are different
        assert user1_account_number != user2_account_number
        
        # Test that each user only sees their own data
        headers1 = {"Authorization": f"Bearer {user1_token}"}
        response1 = client.get("/api/v1/account/summary", headers=headers1)
        assert response1.status_code == 200
        assert response1.json()["account_number"] == user1_account_number
        
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        response2 = client.get("/api/v1/account/summary", headers=headers2)
        assert response2.status_code == 200
        assert response2.json()["account_number"] == user2_account_number
    
    def test_sensitive_data_not_exposed(self, test_db, test_user_with_account, auth_token):
        """Test that sensitive data is not exposed in API responses"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/v1/account/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Ensure sensitive fields are not present
        sensitive_fields = ["hashed_password", "registration_ip", "last_login_ip", "account_metadata"]
        for field in sensitive_fields:
            assert field not in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])