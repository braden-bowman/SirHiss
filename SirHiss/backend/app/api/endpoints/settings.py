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
from app.api.endpoints.auth import oauth2_scheme
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
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Get all API credentials for current user"""
    current_user = await get_current_user(token, db)
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
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Create new API credential"""
    current_user = await get_current_user(token, db)
    
    # Prepare credentials dictionary
    credentials_dict = {}
    for field in ['username', 'password', 'api_key', 'api_secret']:
        value = getattr(credential_data, field, None)
        if value:
            credentials_dict[field] = value
    
    if not credentials_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one credential field must be provided"
        )
    
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
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Update existing API credential"""
    current_user = await get_current_user(token, db)
    
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
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Delete API credential"""
    current_user = await get_current_user(token, db)
    
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
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Toggle credential active status"""
    current_user = await get_current_user(token, db)
    
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
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """Test API credential connection"""
    current_user = await get_current_user(token, db)
    
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
        else:
            # For other platforms, assume success for now
            success = True
        
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
    """Test Robinhood API connection"""
    try:
        # Import here to avoid circular imports
        import robin_stocks.robinhood as rh
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return False, "Username and password are required"
        
        # Attempt login (this is a basic test)
        login_result = rh.authentication.login(username, password, store_session=False)
        if login_result:
            rh.authentication.logout()
            return True, None
        else:
            return False, "Invalid credentials"
            
    except ImportError:
        return False, "robin-stocks library not installed"
    except Exception as e:
        return False, str(e)


async def test_yahoo_finance_connection(credentials: dict) -> tuple[bool, str]:
    """Test Yahoo Finance API connection"""
    try:
        # Yahoo Finance doesn't require authentication for basic usage
        # Just test that we can make a basic request
        import yfinance as yf
        
        # Test with a simple ticker lookup
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info and 'symbol' in info:
            return True, None
        else:
            return False, "Unable to fetch data from Yahoo Finance"
            
    except ImportError:
        return False, "yfinance library not installed"
    except Exception as e:
        return False, str(e)