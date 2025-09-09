"""
Comprehensive test suite for authentication endpoints
Tests user registration, login, password validation, and security measures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token


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
        "username": "testuser123",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def test_user_weak_password():
    """Sample user data with weak password"""
    return {
        "username": "testuser456",
        "email": "test2@example.com", 
        "password": "weak"
    }


class TestUserRegistration:
    """Test user registration functionality"""

    def test_register_user_success(self, test_db, test_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == test_user_data["username"].lower()
        assert data["email"] == test_user_data["email"].lower()
        assert data["is_active"] == True
        assert "id" in data

    def test_register_user_weak_password(self, test_db, test_user_weak_password):
        """Test registration with weak password fails"""
        response = client.post("/api/v1/auth/register", json=test_user_weak_password)
        assert response.status_code == 422
        
        error_detail = response.json()["detail"]
        assert any("password" in str(error).lower() for error in error_detail)

    def test_register_duplicate_username(self, test_db, test_user_data):
        """Test registration with duplicate username fails"""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register with same username
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        
        response = client.post("/api/v1/auth/register", json=duplicate_data)
        assert response.status_code == 400
        assert "username already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, test_db, test_user_data):
        """Test registration with duplicate email fails"""
        # Register first user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register with same email
        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "differentuser"
        
        response = client.post("/api/v1/auth/register", json=duplicate_data)
        assert response.status_code == 400
        assert "email address already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, test_db):
        """Test registration with invalid email fails"""
        invalid_data = {
            "username": "testuser789",
            "email": "invalid-email",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_register_invalid_username(self, test_db):
        """Test registration with invalid username fails"""
        invalid_data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_password_strength_requirements(self, test_db):
        """Test various password strength requirements"""
        base_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        
        # Test cases: password -> should_fail
        password_tests = [
            ("short", True),  # Too short
            ("nouppercase123!", True),  # No uppercase
            ("NOLOWERCASE123!", True),  # No lowercase  
            ("NoNumbers!", True),  # No numbers
            ("NoSpecialChar123", True),  # No special chars
            ("ValidPass123!", False),  # Valid password
        ]
        
        for i, (password, should_fail) in enumerate(password_tests):
            test_data = base_data.copy()
            test_data["username"] = f"testuser{i}"
            test_data["email"] = f"test{i}@example.com"
            test_data["password"] = password
            
            response = client.post("/api/v1/auth/register", json=test_data)
            
            if should_fail:
                assert response.status_code == 422, f"Password '{password}' should have failed"
            else:
                assert response.status_code == 200, f"Password '{password}' should have succeeded"


class TestUserLogin:
    """Test user login functionality"""

    def test_login_success(self, test_db, test_user_data):
        """Test successful user login"""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with form data (OAuth2PasswordRequestForm)
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"].lower()

    def test_login_simple_success(self, test_db, test_user_data):
        """Test successful simple login (JSON)"""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with JSON data
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login/simple", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_login_invalid_username(self, test_db, test_user_data):
        """Test login with invalid username fails"""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "username": "nonexistent",
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect username or password" in response.json()["detail"].lower()

    def test_login_invalid_password(self, test_db, test_user_data):
        """Test login with invalid password fails"""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "incorrect username or password" in response.json()["detail"].lower()

    def test_login_inactive_user(self, test_db, test_user_data):
        """Test login with inactive user fails"""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Manually deactivate user in database
        db = TestingSessionLocal()
        user = db.query(User).filter(User.username == test_user_data["username"].lower()).first()
        user.is_active = False
        db.commit()
        db.close()
        
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert "account is disabled" in response.json()["detail"].lower()


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""

    def test_get_current_user_success(self, test_db, test_user_data):
        """Test getting current user info with valid token"""
        # Register and login user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Get current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"].lower()
        assert data["email"] == test_user_data["email"].lower()

    def test_get_current_user_no_token(self, test_db):
        """Test getting current user info without token fails"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, test_db):
        """Test getting current user info with invalid token fails"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401


class TestSecurityUtils:
    """Test security utility functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        
        # Verification should work
        assert verify_password(password, hashed) == True
        
        # Wrong password should fail
        assert verify_password("wrongpassword", hashed) == False

    def test_jwt_token_creation(self):
        """Test JWT token creation"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Token should be a string
        assert isinstance(token, str)
        
        # Token should have three parts (header.payload.signature)
        assert len(token.split('.')) == 3


class TestInputValidation:
    """Test input validation and sanitization"""

    def test_username_normalization(self, test_db):
        """Test username is normalized to lowercase"""
        user_data = {
            "username": "TestUser123",
            "email": "TEST@EXAMPLE.COM",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "testuser123"
        assert data["email"] == "test@example.com"

    def test_sql_injection_protection(self, test_db):
        """Test that SQL injection attempts are safely handled"""
        malicious_data = {
            "username": "user'; DROP TABLE users; --",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        # Should not cause server error (SQL injection should be prevented)
        response = client.post("/api/v1/auth/register", json=malicious_data)
        # May fail validation but should not cause 500 error
        assert response.status_code in [200, 400, 422]

    def test_xss_protection(self, test_db):
        """Test XSS protection in user inputs"""
        xss_data = {
            "username": "<script>alert('xss')</script>",
            "email": "test@example.com",
            "password": "SecurePass123!"
        }
        
        response = client.post("/api/v1/auth/register", json=xss_data)
        # Should fail validation due to invalid characters
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])