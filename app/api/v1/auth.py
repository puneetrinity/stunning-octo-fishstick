from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, UserProfile, 
    UpdateProfile, ChangePasswordRequest, RefreshTokenRequest
)
from app.auth.security import security_manager
from app.auth.dependencies import get_current_user
from app.database import db_manager
from app.models.user import User
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db_manager.fetch_one(
            "SELECT id FROM users WHERE email = :email",
            {"email": user_data.email}
        )
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password
        password_hash = security_manager.hash_password(user_data.password)
        
        # Determine default plan type if not provided
        if user_data.plan_type is None:
            default_plan = "brand_starter" if user_data.user_type.value == "brand" else "agency_starter"
        else:
            default_plan = user_data.plan_type.value
        
        # Create user
        user_id = str(uuid.uuid4())
        query = """
            INSERT INTO users (id, email, password_hash, full_name, company_name, user_type, plan_type, is_active, is_verified)
            VALUES (:id, :email, :password_hash, :full_name, :company_name, :user_type, :plan_type, :is_active, :is_verified)
            RETURNING id
        """
        
        await db_manager.execute_query(query, {
            "id": user_id,
            "email": user_data.email,
            "password_hash": password_hash,
            "full_name": user_data.full_name,
            "company_name": user_data.company_name,
            "user_type": user_data.user_type.value,
            "plan_type": default_plan,
            "is_active": True,
            "is_verified": False  # TODO: Implement email verification
        })
        
        # Generate tokens
        access_token = security_manager.create_access_token(user_id)
        refresh_token = security_manager.create_refresh_token(user_id)
        
        # Update last login
        await db_manager.execute_query(
            "UPDATE users SET last_login = :last_login WHERE id = :user_id",
            {"last_login": datetime.utcnow(), "user_id": user_id}
        )
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=security_manager.expiration_hours * 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    """Login user"""
    try:
        # Get user from database
        user = await db_manager.fetch_one(
            "SELECT id, email, password_hash, is_active FROM users WHERE email = :email",
            {"email": user_credentials.email}
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not security_manager.verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Generate tokens
        access_token = security_manager.create_access_token(user.id)
        refresh_token = security_manager.create_refresh_token(user.id)
        
        # Update last login
        await db_manager.execute_query(
            "UPDATE users SET last_login = :last_login WHERE id = :user_id",
            {"last_login": datetime.utcnow(), "user_id": user.id}
        )
        
        logger.info(f"User logged in successfully: {user_credentials.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=security_manager.expiration_hours * 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = security_manager.verify_token(refresh_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("user_id")
        
        # Verify user still exists and is active
        user = await db_manager.fetch_one(
            "SELECT id, is_active FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        access_token = security_manager.create_access_token(user_id)
        new_refresh_token = security_manager.create_refresh_token(user_id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=security_manager.expiration_hours * 3600
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        plan_type=current_user.plan_type.value,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/me", response_model=UserProfile)
async def update_profile(
    profile_data: UpdateProfile,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    try:
        # Build update query dynamically
        updates = []
        values = {"user_id": current_user.id}
        
        if profile_data.full_name is not None:
            updates.append("full_name = :full_name")
            values["full_name"] = profile_data.full_name
        
        if profile_data.company_name is not None:
            updates.append("company_name = :company_name")
            values["company_name"] = profile_data.company_name
        
        if updates:
            updates.append("updated_at = :updated_at")
            values["updated_at"] = datetime.utcnow()
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = :user_id"
            await db_manager.execute_query(query, values)
        
        # Get updated user data
        updated_user = await db_manager.fetch_one(
            """
            SELECT id, email, full_name, company_name, user_type, plan_type, is_active, 
                   is_verified, created_at, last_login 
            FROM users WHERE id = :user_id
            """,
            {"user_id": current_user.id}
        )
        
        return UserProfile(**dict(updated_user))
        
    except Exception as e:
        logger.error(f"Profile update error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Get current password hash
        user_data = await db_manager.fetch_one(
            "SELECT password_hash FROM users WHERE id = :user_id",
            {"user_id": current_user.id}
        )
        
        # Verify current password
        if not security_manager.verify_password(password_data.current_password, user_data.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = security_manager.hash_password(password_data.new_password)
        
        # Update password
        await db_manager.execute_query(
            "UPDATE users SET password_hash = :password_hash, updated_at = :updated_at WHERE id = :user_id",
            {
                "password_hash": new_password_hash,
                "updated_at": datetime.utcnow(),
                "user_id": current_user.id
            }
        )
        
        logger.info(f"Password changed for user: {current_user.email}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client-side token invalidation)"""
    # Note: Since we're using stateless JWT tokens, logout is handled client-side
    # by removing the token from storage. In a more secure implementation,
    # you would maintain a token blacklist.
    
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}