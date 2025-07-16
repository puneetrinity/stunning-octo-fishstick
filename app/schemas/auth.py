from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserType(str, Enum):
    BRAND = "brand"
    AGENCY = "agency"


class PlanType(str, Enum):
    # Brand tiers
    BRAND_STARTER = "brand_starter"
    BRAND_PROFESSIONAL = "brand_professional"
    
    # Agency tiers
    AGENCY_STARTER = "agency_starter"
    AGENCY_PRO = "agency_pro"
    AGENCY_ENTERPRISE = "agency_enterprise"


class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    user_type: UserType = Field(..., description="User type: brand or agency")
    plan_type: Optional[PlanType] = Field(None, description="Initial plan type")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('plan_type')
    def validate_plan_type(cls, v, values):
        if v is None:
            return v
        
        user_type = values.get('user_type')
        if user_type == UserType.BRAND:
            if v not in [PlanType.BRAND_STARTER, PlanType.BRAND_PROFESSIONAL]:
                raise ValueError('Invalid plan type for brand user')
        elif user_type == UserType.AGENCY:
            if v not in [PlanType.AGENCY_STARTER, PlanType.AGENCY_PRO, PlanType.AGENCY_ENTERPRISE]:
                raise ValueError('Invalid plan type for agency user')
        
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserProfile(BaseModel):
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="Full name")
    company_name: Optional[str] = Field(None, description="Company name")
    user_type: UserType = Field(..., description="User type: brand or agency")
    plan_type: PlanType = Field(..., description="Subscription plan type")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login date")
    
    class Config:
        from_attributes = True


class UpdateProfile(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    
    class Config:
        from_attributes = True


class PlanInfo(BaseModel):
    """Plan information for pricing display"""
    plan_type: PlanType = Field(..., description="Plan type")
    name: str = Field(..., description="Plan name")
    price_usd: int = Field(..., description="Monthly price in USD")
    target_market: str = Field(..., description="Target market description")
    description: str = Field(..., description="Plan description")
    limits: dict = Field(..., description="Plan limits")
    features: list = Field(..., description="Plan features")
    
    class Config:
        from_attributes = True


class PricingResponse(BaseModel):
    """Complete pricing information"""
    brand_plans: list[PlanInfo] = Field(..., description="Brand pricing plans")
    agency_plans: list[PlanInfo] = Field(..., description="Agency pricing plans")
    
    class Config:
        from_attributes = True


class PlanChangeRequest(BaseModel):
    """Request to change user plan"""
    new_plan_type: PlanType = Field(..., description="New plan type")
    
    @validator('new_plan_type')
    def validate_new_plan_type(cls, v):
        # Additional validation can be added here
        return v


class UserWithPlanInfo(BaseModel):
    """User profile with plan information"""
    user: UserProfile = Field(..., description="User profile")
    plan_info: PlanInfo = Field(..., description="Current plan information")
    usage_stats: dict = Field(..., description="Current usage statistics")
    
    class Config:
        from_attributes = True