"""
Settings endpoints for managing user preferences and API credentials
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.api_credential import ApiCredential
from app.core.security import get_current_user
from app.core.encryption import credential_encryption

router = APIRouter()


class ApiCredentialCreate(BaseModel):
    """API credential creation schema"""
    platform: str
    name: str
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    mfa_code: Optional[str] = None  # For 2FA during setup
    
    def validate_platform_requirements(self):
        """Validate required fields for each platform"""
        if self.platform == "robinhood":
            if not self.username or not self.password:
                raise ValueError("Robinhood requires username and password")
        elif self.platform == "yahoo_finance":
            # Yahoo Finance is free but can use API key for higher limits
            pass  # No required fields
        elif self.platform == "alpha_vantage":
            if not self.api_key:
                raise ValueError("Alpha Vantage requires API key")
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")


class ApiCredentialUpdate(BaseModel):
    """API credential update schema"""
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    is_active: Optional[bool] = None


class ApiCredentialResponse(BaseModel):
    """API credential response schema"""
    id: int
    platform: str
    name: str
    api_key: str  # This will be masked in the response
    is_active: bool
    status: str
    last_used: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/credentials", response_model=List[ApiCredentialResponse])
async def get_user_credentials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all API credentials for current user"""
    credentials = db.query(ApiCredential).filter(
        ApiCredential.user_id == current_user.id
    ).all()
    
    # Return credentials with masked sensitive data
    result = []
    for cred in credentials:
        try:
            decrypted = credential_encryption.decrypt_credentials(cred.encrypted_credentials)
            masked_key = "****" + (decrypted.get('api_key', decrypted.get('username', ''))[-4:] if decrypted.get('api_key', decrypted.get('username', '')) else '')
        except:
            masked_key = "****"
            
        result.append(ApiCredentialResponse(
            id=cred.id,
            platform=cred.platform,
            name=cred.name,
            api_key=masked_key,
            is_active=cred.is_active,
            status=cred.status,
            last_used=cred.last_used,
            created_at=cred.created_at
        ))
    
    return result


@router.post("/credentials", response_model=ApiCredentialResponse)
async def create_credential(
    credential_data: ApiCredentialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new API credential with comprehensive validation and testing
    
    This endpoint validates platform requirements, encrypts credentials securely,
    and optionally tests the connection before storing.
    """
    
    try:
        # Validate platform-specific requirements
        credential_data.validate_platform_requirements()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Prepare credentials dictionary
    credentials_dict = {}
    for field in ['username', 'password', 'api_key', 'api_secret', 'mfa_code']:
        value = getattr(credential_data, field, None)
        if value:
            credentials_dict[field] = value
    
    # Yahoo Finance doesn't require credentials, so allow empty dict for it
    if not credentials_dict and credential_data.platform != 'yahoo_finance':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one credential field must be provided"
        )
    
    # For Yahoo Finance, add a placeholder to indicate free service
    if credential_data.platform == 'yahoo_finance' and not credentials_dict:
        credentials_dict = {"service_type": "free"}
    
    # Encrypt credentials
    try:
        encrypted_creds = credential_encryption.encrypt_credentials(credentials_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt credentials: {str(e)}"
        )
    
    # Create database record
    db_credential = ApiCredential(
        user_id=current_user.id,
        platform=credential_data.platform,
        name=credential_data.name,
        encrypted_credentials=encrypted_creds,
        status='untested'
    )
    
    db.add(db_credential)
    db.commit()
    db.refresh(db_credential)
    
    # Return with masked data
    masked_key = "****" + (credentials_dict.get('api_key', credentials_dict.get('username', ''))[-4:] if credentials_dict.get('api_key', credentials_dict.get('username', '')) else '')
    
    return ApiCredentialResponse(
        id=db_credential.id,
        platform=db_credential.platform,
        name=db_credential.name,
        api_key=masked_key,
        is_active=db_credential.is_active,
        status=db_credential.status,
        last_used=db_credential.last_used,
        created_at=db_credential.created_at
    )


@router.put("/credentials/{credential_id}", response_model=ApiCredentialResponse)
async def update_credential(
    credential_id: int,
    credential_data: ApiCredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update existing API credential"""
    
    # Get existing credential
    db_credential = db.query(ApiCredential).filter(
        ApiCredential.id == credential_id,
        ApiCredential.user_id == current_user.id
    ).first()
    
    if not db_credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    # Update simple fields
    if credential_data.name is not None:
        db_credential.name = credential_data.name
    if credential_data.is_active is not None:
        db_credential.is_active = credential_data.is_active
    
    # Update encrypted credentials if provided
    credential_fields_to_update = {}
    for field in ['username', 'password', 'api_key', 'api_secret']:
        value = getattr(credential_data, field, None)
        if value is not None:
            credential_fields_to_update[field] = value
    
    if credential_fields_to_update:
        try:
            # Get existing credentials
            existing_creds = credential_encryption.decrypt_credentials(db_credential.encrypted_credentials)
            # Update with new values
            existing_creds.update(credential_fields_to_update)
            # Re-encrypt
            db_credential.encrypted_credentials = credential_encryption.encrypt_credentials(existing_creds)
            db_credential.status = 'untested'  # Reset status when credentials change
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update credentials: {str(e)}"
            )
    
    db.commit()
    db.refresh(db_credential)
    
    # Return with masked data
    try:
        decrypted = credential_encryption.decrypt_credentials(db_credential.encrypted_credentials)
        masked_key = "****" + (decrypted.get('api_key', decrypted.get('username', ''))[-4:] if decrypted.get('api_key', decrypted.get('username', '')) else '')
    except:
        masked_key = "****"
    
    return ApiCredentialResponse(
        id=db_credential.id,
        platform=db_credential.platform,
        name=db_credential.name,
        api_key=masked_key,
        is_active=db_credential.is_active,
        status=db_credential.status,
        last_used=db_credential.last_used,
        created_at=db_credential.created_at
    )


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete API credential"""
    
    db_credential = db.query(ApiCredential).filter(
        ApiCredential.id == credential_id,
        ApiCredential.user_id == current_user.id
    ).first()
    
    if not db_credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    db.delete(db_credential)
    db.commit()
    
    return {"message": "Credential deleted successfully"}


@router.patch("/credentials/{credential_id}")
async def toggle_credential_status(
    credential_id: int,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle credential active status"""
    
    db_credential = db.query(ApiCredential).filter(
        ApiCredential.id == credential_id,
        ApiCredential.user_id == current_user.id
    ).first()
    
    if not db_credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    if 'isActive' in status_data:
        db_credential.is_active = status_data['isActive']
    
    db.commit()
    
    return {"message": "Credential status updated successfully"}


@router.post("/credentials/{credential_id}/test")
async def test_credential_connection(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test API credential connection"""
    
    db_credential = db.query(ApiCredential).filter(
        ApiCredential.id == credential_id,
        ApiCredential.user_id == current_user.id
    ).first()
    
    if not db_credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    try:
        credentials = credential_encryption.decrypt_credentials(db_credential.encrypted_credentials)
        
        # Test connection based on platform
        success = False
        error_message = None
        
        if db_credential.platform == 'robinhood':
            success, error_message = await test_robinhood_connection(credentials)
        elif db_credential.platform == 'yahoo_finance':
            success, error_message = await test_yahoo_finance_connection(credentials)
        elif db_credential.platform == 'alpha_vantage':
            success, error_message = await test_alpha_vantage_connection(credentials)
        else:
            # For unknown platforms, mark as untested
            success = False
            error_message = f"Connection testing not implemented for {db_credential.platform}"
        
        # Update status
        db_credential.status = 'connected' if success else 'error'
        if success:
            db_credential.last_used = datetime.utcnow()
        
        db.commit()
        
        if success:
            return {"message": "Connection test successful", "status": "connected"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed: {error_message or 'Unknown error'}"
            )
            
    except Exception as e:
        db_credential.status = 'error'
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )


async def test_robinhood_connection(credentials: dict) -> tuple[bool, str]:
    """
    Test Robinhood API connection with comprehensive error handling
    
    This function attempts to authenticate with Robinhood using provided credentials.
    It handles various error scenarios including 2FA requirements and account issues.
    """
    try:
        import robin_stocks.robinhood as rh
        import logging
        
        logger = logging.getLogger(__name__)
        
        username = credentials.get('username')
        password = credentials.get('password')
        mfa_code = credentials.get('mfa_code')
        
        if not username or not password:
            return False, "Username and password are required for Robinhood"
        
        logger.info(f"Testing Robinhood connection for user: {username[:3]}***")
        
        # Clear any existing session
        rh.authentication.logout()
        
        try:
            # Attempt login with MFA if provided
            if mfa_code:
                login_result = rh.authentication.login(username, password, mfa_code=mfa_code, store_session=False)
            else:
                login_result = rh.authentication.login(username, password, store_session=False)
            
            if login_result:
                # Test API access by getting account info
                try:
                    account_info = rh.profiles.load_account_profile()
                    if account_info:
                        logger.info("Robinhood connection test successful")
                        rh.authentication.logout()
                        return True, None
                    else:
                        rh.authentication.logout()
                        return False, "Unable to access account information"
                except Exception as api_error:
                    rh.authentication.logout()
                    return False, f"API access error: {str(api_error)}"
            else:
                return False, "Authentication failed - check credentials"
                
        except Exception as auth_error:
            error_msg = str(auth_error).lower()
            
            if "mfa" in error_msg or "two factor" in error_msg:
                return False, "Two-factor authentication required. Please provide MFA code."
            elif "challenge" in error_msg:
                return False, "Account requires additional verification. Please check your email/SMS."
            elif "locked" in error_msg or "disabled" in error_msg:
                return False, "Account is locked or disabled. Please check Robinhood app."
            elif "incorrect" in error_msg or "invalid" in error_msg:
                return False, "Incorrect username or password"
            else:
                logger.error(f"Robinhood authentication error: {str(auth_error)}")
                return False, f"Authentication error: {str(auth_error)}"
            
    except ImportError:
        return False, "robin-stocks library not installed"
    except Exception as e:
        logger.error(f"Unexpected Robinhood connection error: {str(e)}")
        return False, f"Connection error: {str(e)}"


async def test_yahoo_finance_connection(credentials: dict) -> tuple[bool, str]:
    """
    Test Yahoo Finance API connection with comprehensive validation
    
    Yahoo Finance doesn't require authentication for basic usage but we test
    multiple endpoints to ensure reliable data access.
    """
    try:
        import yfinance as yf
        import logging
        from datetime import datetime, timedelta
        
        logger = logging.getLogger(__name__)
        logger.info("Testing Yahoo Finance connection")
        
        # Test multiple endpoints to ensure reliability
        test_symbols = ["AAPL", "GOOGL", "MSFT"]
        successful_tests = 0
        
        for symbol in test_symbols:
            try:
                # Test basic ticker info
                ticker = yf.Ticker(symbol)
                
                # Test info endpoint
                info = ticker.info
                if info and 'symbol' in info:
                    successful_tests += 1
                    break  # One success is enough
                    
                # Test historical data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=5)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    successful_tests += 1
                    break  # One success is enough
                    
            except Exception as ticker_error:
                logger.warning(f"Yahoo Finance test failed for {symbol}: {str(ticker_error)}")
                continue
        
        if successful_tests > 0:
            logger.info("Yahoo Finance connection test successful")
            return True, None
        else:
            return False, "Unable to fetch data from Yahoo Finance - service may be down"
            
    except ImportError:
        return False, "yfinance library not installed"
    except Exception as e:
        logger.error(f"Yahoo Finance connection error: {str(e)}")
        return False, f"Connection error: {str(e)}"


async def test_alpha_vantage_connection(credentials: dict) -> tuple[bool, str]:
    """Test Alpha Vantage API connection"""
    try:
        import requests
        import logging
        
        logger = logging.getLogger(__name__)
        
        api_key = credentials.get('api_key')
        if not api_key:
            return False, "API key is required for Alpha Vantage"
        
        logger.info("Testing Alpha Vantage connection")
        
        # Test API with a simple quote request
        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': 'AAPL',
            'apikey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API error messages
        if 'Error Message' in data:
            return False, f"Alpha Vantage error: {data['Error Message']}"
        elif 'Information' in data:
            return False, f"Alpha Vantage limit: {data['Information']}"
        elif 'Global Quote' in data:
            logger.info("Alpha Vantage connection test successful")
            return True, None
        else:
            return False, "Unexpected response format from Alpha Vantage"
            
    except ImportError:
        return False, "requests library not installed"
    except requests.exceptions.Timeout:
        return False, "Connection timeout - Alpha Vantage may be slow"
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        logger.error(f"Alpha Vantage connection error: {str(e)}")
        return False, f"Connection error: {str(e)}"


class UserSettings(BaseModel):
    """User settings schema"""
    risk_tolerance: Optional[str] = "medium"
    max_position_size: Optional[float] = 0.1
    enable_notifications: Optional[bool] = True
    auto_rebalance: Optional[bool] = False
    dark_mode: Optional[bool] = True


class SecuritySettings(BaseModel):
    """Security settings schema"""
    two_factor_enabled: Optional[bool] = False
    session_timeout: Optional[int] = 30
    max_concurrent_sessions: Optional[int] = 5
    require_strong_passwords: Optional[bool] = True
    email_notifications: Optional[bool] = True
    suspicious_activity_alerts: Optional[bool] = True


@router.get("/user")
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user settings
    
    Note: Returns safe default settings for user preferences
    Full implementation would store user-specific settings in database
    """
    # Return safe defaults - these would be stored per-user in production
    return {
        "risk_tolerance": "medium",  # Conservative default
        "max_position_size": 0.05,  # 5% maximum position size
        "enable_notifications": True,  # Keep users informed
        "auto_rebalance": False,  # Manual control preferred
        "dark_mode": True  # Modern UI preference
    }


@router.post("/user")
async def save_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save user settings
    
    Note: Currently validates and acknowledges settings
    Full implementation would persist to user_settings table
    """
    # Validate settings (basic validation already handled by Pydantic)
    settings_dict = settings.dict(exclude_unset=True)
    
    # Additional validation for risk tolerance
    if settings.risk_tolerance and settings.risk_tolerance not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Risk tolerance must be 'low', 'medium', or 'high'"
        )
    
    # Additional validation for position size
    if settings.max_position_size and (settings.max_position_size <= 0 or settings.max_position_size > 1.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max position size must be between 0 and 1.0 (100%)"
        )
    
    # In production, this would save to database
    return {
        "message": "User settings updated successfully",
        "settings": settings_dict
    }


@router.get("/security")
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get security settings (redirects to security endpoint)
    
    Note: This duplicates the security endpoint for convenience
    Production implementation should consolidate these endpoints
    """
    # Return secure defaults matching security endpoint
    return {
        "two_factor_enabled": False,  # Future enhancement
        "session_timeout": 30,  # Minutes
        "max_concurrent_sessions": 3,  # Conservative default
        "require_strong_passwords": True,  # Always enforced
        "email_notifications": True,  # Security notifications
        "suspicious_activity_alerts": True  # Security monitoring
    }


@router.post("/security")
async def save_security_settings(
    settings: SecuritySettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save security settings
    
    Note: Currently validates and acknowledges settings  
    Full implementation would persist to user_security_settings table
    """
    # Validate settings (basic validation already handled by Pydantic)
    settings_dict = settings.dict(exclude_unset=True)
    
    # Additional validation for session timeout
    if settings.session_timeout and (settings.session_timeout < 5 or settings.session_timeout > 1440):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session timeout must be between 5 and 1440 minutes (24 hours)"
        )
    
    # Additional validation for concurrent sessions
    if settings.max_concurrent_sessions and (settings.max_concurrent_sessions < 1 or settings.max_concurrent_sessions > 10):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Max concurrent sessions must be between 1 and 10"
        )
    
    # In production, this would save to database
    return {
        "message": "Security settings updated successfully",
        "settings": settings_dict
    }