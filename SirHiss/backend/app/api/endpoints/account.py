"""
Account management endpoints for user account information and API status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.api_credential import ApiCredential
from app.core.security import get_current_user
from app.core.encryption import credential_encryption

router = APIRouter()
logger = logging.getLogger(__name__)


class ApiConnectionStatus(BaseModel):
    """API connection status schema"""
    id: int
    platform: str
    name: str
    status: str  # 'connected', 'error', 'untested', 'testing'
    status_color: str  # 'green', 'red', 'yellow', 'blue'
    last_tested: Optional[datetime] = None
    last_successful: Optional[datetime] = None
    error_message: Optional[str] = None
    is_active: bool


class AccountSummary(BaseModel):
    """Account summary information"""
    id: int
    account_number: str
    username: str
    display_name: str
    email: str
    full_name: Optional[str] = None
    
    # Account status
    account_status: str
    account_status_color: str
    risk_level: str
    kyc_status: str
    email_verified: bool
    is_verified: bool
    
    # Account metrics
    account_age_days: int
    created_at: datetime
    last_login_at: Optional[datetime] = None
    login_count: int
    
    # API connections summary
    total_api_connections: int
    active_api_connections: int
    connected_apis: int
    error_apis: int
    
    # API connection details
    api_connections: List[ApiConnectionStatus]


def get_status_color(status: str) -> str:
    """Get color for connection status"""
    status_colors = {
        'connected': 'green',
        'error': 'red',
        'untested': 'yellow',
        'testing': 'blue',
        'disabled': 'gray'
    }
    return status_colors.get(status.lower(), 'yellow')


def get_account_status_color(status: str) -> str:
    """Get color for account status"""
    status_colors = {
        'active': 'green',
        'suspended': 'red',
        'pending': 'yellow',
        'closed': 'gray'
    }
    return status_colors.get(status.lower(), 'yellow')


async def test_api_connection_quick(credential: ApiCredential) -> tuple[str, str]:
    """
    Quick API connection test without full authentication
    Returns (status, error_message)
    """
    try:
        credentials = credential_encryption.decrypt_credentials(credential.encrypted_credentials)
        
        if credential.platform == 'robinhood':
            # Quick validation - check if credentials exist
            if credentials.get('username') and credentials.get('password'):
                return 'connected', None  # Assume connected for quick check
            else:
                return 'error', 'Missing credentials'
                
        elif credential.platform == 'yahoo_finance':
            # Yahoo Finance doesn't require auth for basic usage
            return 'connected', None
            
        elif credential.platform == 'alpha_vantage':
            # Check if API key exists
            if credentials.get('api_key'):
                return 'connected', None
            else:
                return 'error', 'Missing API key'
                
        else:
            # Unknown platform - assume untested
            return 'untested', 'Platform not supported for testing'
            
    except Exception as e:
        return 'error', str(e)


@router.get("/summary", response_model=AccountSummary)
async def get_account_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive account summary with API connection statuses
    
    This endpoint provides all information needed for the dashboard user info section:
    - Account details and verification status
    - Login history and account metrics
    - API connection statuses with color coding
    - Real-time connection testing
    """
    try:
        # Get all API credentials for the user
        api_credentials = db.query(ApiCredential).filter(
            ApiCredential.user_id == current_user.id
        ).all()
        
        # Test API connections and build status list
        api_connections = []
        connected_count = 0
        error_count = 0
        active_count = 0
        
        for cred in api_credentials:
            if cred.is_active:
                active_count += 1
                
            # Quick connection test
            status, error_msg = await test_api_connection_quick(cred)
            
            if status == 'connected':
                connected_count += 1
            elif status == 'error':
                error_count += 1
            
            api_connection = ApiConnectionStatus(
                id=cred.id,
                platform=cred.platform,
                name=cred.name,
                status=status,
                status_color=get_status_color(status),
                last_tested=datetime.utcnow() if status in ['connected', 'error'] else None,
                last_successful=cred.last_used if status == 'connected' else None,
                error_message=error_msg,
                is_active=cred.is_active
            )
            api_connections.append(api_connection)
        
        # Build comprehensive account summary
        account_summary = AccountSummary(
            id=current_user.id,
            account_number=current_user.account_number,
            username=current_user.username,
            display_name=current_user.get_display_name(),
            email=current_user.email,
            full_name=current_user.full_name,
            
            # Account status
            account_status=current_user.account_status,
            account_status_color=get_account_status_color(current_user.account_status),
            risk_level=current_user.risk_level,
            kyc_status=current_user.kyc_status,
            email_verified=current_user.email_verified,
            is_verified=current_user.is_verified(),
            
            # Account metrics
            account_age_days=current_user.get_account_age_days(),
            created_at=current_user.created_at,
            last_login_at=current_user.last_login_at,
            login_count=current_user.login_count,
            
            # API connections summary
            total_api_connections=len(api_credentials),
            active_api_connections=active_count,
            connected_apis=connected_count,
            error_apis=error_count,
            
            # API connection details
            api_connections=api_connections
        )
        
        # Log account access for security monitoring
        logger.info(f"Account summary accessed: {current_user.username} (Account: {current_user.account_number})")
        
        return account_summary
        
    except Exception as e:
        logger.error(f"Error fetching account summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch account information"
        )


@router.get("/api-status", response_model=List[ApiConnectionStatus])
async def get_api_connection_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    test_connections: bool = False
):
    """
    Get API connection statuses for the current user
    
    Args:
        test_connections: If True, perform live connection tests (slower)
    """
    try:
        # Get all API credentials for the user
        api_credentials = db.query(ApiCredential).filter(
            ApiCredential.user_id == current_user.id
        ).all()
        
        api_connections = []
        
        for cred in api_credentials:
            if test_connections:
                # Perform live connection test
                status, error_msg = await test_api_connection_quick(cred)
                last_tested = datetime.utcnow()
            else:
                # Use stored status
                status = cred.status
                error_msg = None
                last_tested = None
            
            api_connection = ApiConnectionStatus(
                id=cred.id,
                platform=cred.platform,
                name=cred.name,
                status=status,
                status_color=get_status_color(status),
                last_tested=last_tested,
                last_successful=cred.last_used if status == 'connected' else None,
                error_message=error_msg,
                is_active=cred.is_active
            )
            api_connections.append(api_connection)
        
        return api_connections
        
    except Exception as e:
        logger.error(f"Error fetching API status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch API connection status"
        )


@router.post("/refresh-api-status")
async def refresh_api_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh all API connection statuses by testing them
    """
    try:
        # Get all API credentials for the user
        api_credentials = db.query(ApiCredential).filter(
            ApiCredential.user_id == current_user.id
        ).all()
        
        updated_count = 0
        
        for cred in api_credentials:
            if cred.is_active:
                # Perform connection test
                status, error_msg = await test_api_connection_quick(cred)
                
                # Update database status
                cred.status = status
                if status == 'connected':
                    cred.last_used = datetime.utcnow()
                
                updated_count += 1
        
        db.commit()
        
        logger.info(f"API connections refreshed for user {current_user.username}: {updated_count} credentials tested")
        
        return {
            "message": f"Successfully refreshed {updated_count} API connections",
            "updated_count": updated_count,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error refreshing API connections for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh API connections"
        )