"""
Test cases for user registration and API credential management
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.models.api_credential import ApiCredential

# Test database setup - use PostgreSQL test database
SQLALCHEMY_DATABASE_URL = "postgresql://sirhiss:sirhiss_secure_pwd@postgres:5432/sirhiss_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tables already exist in development DB, no need to create


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestUserRegistration:
    """Test user registration functionality"""
    
    def setup_method(self):
        """Clean up database before each test"""
        db = TestingSessionLocal()
        db.query(ApiCredential).delete()
        db.query(User).delete()
        db.commit()
        db.close()
    
    def test_register_user_success(self):
        """Test successful user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] == True
        assert "id" in data
    
    def test_register_user_duplicate_username(self):
        """Test registration with duplicate username"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        # Create first user
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to create second user with same username
        user_data["email"] = "different@example.com"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        # Create first user
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to create second user with same email
        user_data["username"] = "differentuser"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_login_after_registration(self):
        """Test login functionality after registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        # Register user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login with the registered user
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        login_json = login_response.json()
        assert "access_token" in login_json
        assert login_json["token_type"] == "bearer"
        assert login_json["user"]["username"] == "testuser"


class TestApiCredentials:
    """Test API credential management"""
    
    def setup_method(self):
        """Setup test user and clean database"""
        db = TestingSessionLocal()
        db.query(ApiCredential).delete()
        db.query(User).delete()
        db.commit()
        
        # Create test user
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login to get token
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        db.close()
    
    def test_create_robinhood_credential(self):
        """Test creating Robinhood API credential"""
        credential_data = {
            "platform": "robinhood",
            "name": "My Robinhood Account",
            "username": "robinhood_user",
            "password": "robinhood_pass"
        }
        
        response = client.post(
            "/api/v1/settings/credentials",
            json=credential_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "robinhood"
        assert data["name"] == "My Robinhood Account"
        assert data["status"] == "untested"
        assert data["is_active"] == True
        assert "****" in data["api_key"]  # Should be masked
    
    def test_create_yahoo_finance_credential(self):
        """Test creating Yahoo Finance API credential"""
        credential_data = {
            "platform": "yahoo_finance",
            "name": "Yahoo Finance Data",
            "api_key": "yahoo_api_key_123"
        }
        
        response = client.post(
            "/api/v1/settings/credentials",
            json=credential_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "yahoo_finance"
        assert data["name"] == "Yahoo Finance Data"
        assert "****" in data["api_key"]  # Should be masked
    
    def test_list_user_credentials(self):
        """Test listing user's API credentials"""
        # Create a few credentials
        credentials = [
            {
                "platform": "robinhood",
                "name": "RH Account 1",
                "username": "rh_user1",
                "password": "rh_pass1"
            },
            {
                "platform": "yahoo_finance",
                "name": "Yahoo Data",
                "api_key": "yahoo_key_123"
            }
        ]
        
        for cred in credentials:
            response = client.post(
                "/api/v1/settings/credentials",
                json=cred,
                headers=self.headers
            )
            assert response.status_code == 200
        
        # List all credentials
        response = client.get("/api/v1/settings/credentials", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        platforms = [cred["platform"] for cred in data]
        assert "robinhood" in platforms
        assert "yahoo_finance" in platforms
    
    def test_update_credential(self):
        """Test updating an existing credential"""
        # Create credential
        credential_data = {
            "platform": "robinhood",
            "name": "Original Name",
            "username": "original_user",
            "password": "original_pass"
        }
        
        create_response = client.post(
            "/api/v1/settings/credentials",
            json=credential_data,
            headers=self.headers
        )
        assert create_response.status_code == 200
        
        credential_id = create_response.json()["id"]
        
        # Update credential
        update_data = {
            "name": "Updated Name",
            "username": "updated_user"
        }
        
        update_response = client.put(
            f"/api/v1/settings/credentials/{credential_id}",
            json=update_data,
            headers=self.headers
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Name"
        assert data["status"] == "untested"  # Should reset after credential update
    
    def test_delete_credential(self):
        """Test deleting a credential"""
        # Create credential
        credential_data = {
            "platform": "yahoo_finance",
            "name": "To Delete",
            "api_key": "delete_me_key"
        }
        
        create_response = client.post(
            "/api/v1/settings/credentials",
            json=credential_data,
            headers=self.headers
        )
        assert create_response.status_code == 200
        
        credential_id = create_response.json()["id"]
        
        # Delete credential
        delete_response = client.delete(
            f"/api/v1/settings/credentials/{credential_id}",
            headers=self.headers
        )
        
        assert delete_response.status_code == 200
        
        # Verify it's deleted
        list_response = client.get("/api/v1/settings/credentials", headers=self.headers)
        assert list_response.status_code == 200
        
        credentials = list_response.json()
        credential_ids = [cred["id"] for cred in credentials]
        assert credential_id not in credential_ids
    
    def test_toggle_credential_status(self):
        """Test toggling credential active status"""
        # Create credential
        credential_data = {
            "platform": "robinhood",
            "name": "Status Test",
            "username": "status_user",
            "password": "status_pass"
        }
        
        create_response = client.post(
            "/api/v1/settings/credentials",
            json=credential_data,
            headers=self.headers
        )
        assert create_response.status_code == 200
        
        credential_id = create_response.json()["id"]
        
        # Toggle status to inactive
        toggle_response = client.patch(
            f"/api/v1/settings/credentials/{credential_id}",
            json={"isActive": False},
            headers=self.headers
        )
        
        assert toggle_response.status_code == 200
        
        # Verify status changed
        list_response = client.get("/api/v1/settings/credentials", headers=self.headers)
        credentials = list_response.json()
        
        test_credential = next((c for c in credentials if c["id"] == credential_id), None)
        assert test_credential is not None
        assert test_credential["is_active"] == False
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        # Try to access without token
        response = client.get("/api/v1/settings/credentials")
        assert response.status_code == 401
        
        # Try with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/settings/credentials", headers=headers)
        assert response.status_code == 401