from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db, db_manager
from app.auth.security import security_manager
from app.models.user import User


# HTTP Bearer token scheme
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    """Get current authenticated user from JWT token"""
    
    # Extract user ID from token
    user_id = security_manager.extract_user_id(credentials.credentials)
    
    # Get user from database
    query = """
        SELECT id, email, full_name, company_name, plan_type, is_active, is_verified, 
               created_at, updated_at, last_login
        FROM users 
        WHERE id = :user_id AND is_active = true
    """
    
    user_data = await db_manager.fetch_one(query, {"user_id": user_id})
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(**dict(user_data))


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (additional check for active status)"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email address"
        )
    return current_user


def require_plan(required_plan: str):
    """Decorator to require specific plan level"""
    
    plan_hierarchy = {
        "starter": 1,
        "professional": 2,
        "agency": 3,
        "enterprise": 4
    }
    
    async def plan_checker(current_user: User = Depends(get_current_verified_user)):
        user_plan_level = plan_hierarchy.get(current_user.plan_type.value, 0)
        required_plan_level = plan_hierarchy.get(required_plan, 999)
        
        if user_plan_level < required_plan_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {required_plan} plan or higher"
            )
        
        return current_user
    
    return plan_checker


# Common dependency combinations
get_professional_user = require_plan("professional")
get_agency_user = require_plan("agency")
get_enterprise_user = require_plan("enterprise")