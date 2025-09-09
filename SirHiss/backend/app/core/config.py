"""
Configuration settings for SirHiss application
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://sirhiss:sirhiss_secure_pwd@localhost:5432/sirhiss_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_SALT: str = "sirhiss_credential_salt"
    SIRHISS_API_KEY: str = "sirhiss_api_key_change_in_production"
    
    # Robinhood API
    ROBINHOOD_USERNAME: Optional[str] = None
    ROBINHOOD_PASSWORD: Optional[str] = None
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Bot execution
    MAX_CONCURRENT_BOTS: int = 10
    BOT_EXECUTION_INTERVAL: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()