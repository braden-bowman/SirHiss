"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter()


class UserCreate(BaseModel):
    """User creation schema with comprehensive validation"""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]{3,50}$")
    email: str = Field(..., max_length=100, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """
        Validate password strength requirements:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter  
        - Contains digit
        - Contains special character
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
            
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
            
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
            
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in v):
            raise ValueError('Password must contain at least one special character')
            
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format and restrictions"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()  # Store usernames in lowercase for consistency


class UserResponse(BaseModel):
    """User response schema with comprehensive account information"""
    id: int
    account_number: str
    username: str
    email: str
    is_active: bool
    full_name: Optional[str] = None
    account_status: str
    risk_level: str
    kyc_status: str
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    login_count: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with comprehensive validation and security measures
    
    This endpoint:
    - Validates password strength requirements
    - Checks for existing username/email conflicts
    - Securely hashes passwords using bcrypt
    - Creates user account with proper database constraints
    - Logs security events for audit trails
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Normalize email to lowercase for consistency
        email_normalized = user_data.email.lower().strip()
        username_normalized = user_data.username.lower().strip()
        
        # Check if user already exists (case-insensitive)
        existing_user = db.query(User).filter(
            (User.username == username_normalized) | (User.email == email_normalized)
        ).first()
        
        if existing_user:
            # Log the registration attempt for security monitoring
            logger.warning(f"Registration attempt with existing credentials - Username: {username_normalized}, Email: {email_normalized}")
            
            if existing_user.username == username_normalized:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address already registered"
                )
        
        # Hash password securely using bcrypt
        hashed_password = get_password_hash(user_data.password)
        
        # Generate unique account number
        account_number = User.generate_account_number()
        
        # Ensure account number is unique (extremely unlikely collision, but safety first)
        while db.query(User).filter(User.account_number == account_number).first():
            account_number = User.generate_account_number()
        
        # Get client IP for registration tracking
        # Note: In production, this would come from request headers
        registration_ip = None  # TODO: Extract from FastAPI request
        
        # Create new user with comprehensive account data
        db_user = User(
            account_number=account_number,
            username=username_normalized,
            email=email_normalized,
            hashed_password=hashed_password,
            is_active=True,  # New users are active by default
            registration_ip=registration_ip,
            email_verified=False,  # Email verification required
            account_status='active',
            risk_level='medium',  # Default risk level
            kyc_status='pending',  # KYC verification pending
            login_count=0
        )
        
        # Save to database with error handling
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Log successful registration
            logger.info(f"New user registered successfully - ID: {db_user.id}, Username: {db_user.username}")
            
            return db_user
            
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error during user registration: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during user registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token
    
    This endpoint:
    - Validates credentials against database
    - Implements rate limiting protection (future enhancement)
    - Generates secure JWT tokens
    - Logs authentication attempts for security monitoring
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Normalize username for consistent lookup
        username_normalized = form_data.username.lower().strip()
        
        # Lookup user by username
        user = db.query(User).filter(User.username == username_normalized).first()
        
        if not user:
            # Log failed login attempt - user not found
            logger.warning(f"Login attempt with non-existent username: {username_normalized}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(form_data.password, user.hashed_password):
            # Log failed login attempt - invalid password
            logger.warning(f"Login attempt with invalid password for user: {username_normalized}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username_normalized}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update login tracking information
        user.update_login_info(ip_address=None)  # TODO: Extract IP from request
        db.commit()
        
        # Generate access token
        access_token = create_access_token(data={"sub": user.username})
        
        # Log successful login with account details
        logger.info(f"Successful login for user: {user.username} (ID: {user.id}, Account: {user.account_number})")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to server error"
        )


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str


class RobinhoodConnect(BaseModel):
    """Robinhood connection schema"""
    username: str
    password: str
    mfa_code: Optional[str] = None


@router.post("/login/simple", response_model=Token)
async def simple_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Simple login endpoint for frontend applications
    
    This provides the same security as the main login endpoint
    but accepts JSON data instead of form data for easier frontend integration
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Normalize username for consistent lookup
        username_normalized = login_data.username.lower().strip()
        
        # Lookup user by username
        user = db.query(User).filter(User.username == username_normalized).first()
        
        if not user:
            logger.warning(f"Simple login attempt with non-existent username: {username_normalized}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Simple login attempt with invalid password for user: {username_normalized}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Simple login attempt for inactive user: {username_normalized}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Update login tracking information
        user.update_login_info(ip_address=None)  # TODO: Extract IP from request
        db.commit()
        
        # Generate access token
        access_token = create_access_token(data={"sub": user.username})
        
        # Log successful login with account details
        logger.info(f"Successful simple login for user: {user.username} (ID: {user.id}, Account: {user.account_number})")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during simple login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to server error"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user
    
    Note: Since we're using stateless JWT tokens, logout is primarily
    handled on the client side by removing the token from storage.
    
    In a full implementation with session tracking, this would:
    - Invalidate the current JWT token (requires token blacklist)
    - Clear session data from database
    - Log the logout event
    
    For now, this endpoint serves as a logout confirmation and logging point.
    """
    logger = logging.getLogger(__name__)
    
    # Log the logout event
    logger.info(f"User logged out: {current_user.username} (ID: {current_user.id})")
    
    return {
        "message": "Successfully logged out",
        "user_id": current_user.id,
        "username": current_user.username
    }


@router.post("/robinhood/connect")
async def connect_robinhood(
    robinhood_data: RobinhoodConnect,
    current_user: User = Depends(get_current_user)
):
    """Connect Robinhood account"""
    
    try:
        # TODO: Implement actual Robinhood connection logic
        # For now, just return success if credentials are provided
        if robinhood_data.username and robinhood_data.password:
            return {
                "message": "Robinhood connected successfully",
                "status": "connected"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password required"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Robinhood: {str(e)}"
        )


@router.post("/robinhood/disconnect")
async def disconnect_robinhood(
    current_user: User = Depends(get_current_user)
):
    """Disconnect Robinhood account"""
    
    # TODO: Implement actual Robinhood disconnection logic
    return {
        "message": "Robinhood disconnected successfully",
        "status": "disconnected"
    }