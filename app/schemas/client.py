from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ClientCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Client name")
    company_name: str = Field(..., max_length=255, description="Company name")
    website_url: Optional[str] = Field(None, max_length=500, description="Website URL")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    description: Optional[str] = Field(None, description="Client description")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact name")
    monthly_budget: Optional[str] = Field(None, max_length=50, description="Monthly budget range")
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v:
            v = v.strip()
            if not v.startswith(('http://', 'https://')):
                v = f'https://{v}'
            return v
        return None
    
    @validator('monthly_budget')
    def validate_monthly_budget(cls, v):
        if v:
            valid_ranges = [
                "$1K-5K", "$5K-10K", "$10K-25K", "$25K-50K", "$50K-100K", "$100K+"
            ]
            if v not in valid_ranges:
                raise ValueError(f'Budget must be one of: {", ".join(valid_ranges)}')
        return v


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Client name")
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    website_url: Optional[str] = Field(None, max_length=500, description="Website URL")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    description: Optional[str] = Field(None, description="Client description")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact name")
    status: Optional[ClientStatus] = Field(None, description="Client status")
    monthly_budget: Optional[str] = Field(None, max_length=50, description="Monthly budget range")
    onboarding_completed: Optional[bool] = Field(None, description="Onboarding status")
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v:
            v = v.strip()
            if not v.startswith(('http://', 'https://')):
                v = f'https://{v}'
            return v
        return None


class ClientResponse(BaseModel):
    id: str = Field(..., description="Client ID")
    name: str = Field(..., description="Client name")
    company_name: str = Field(..., description="Company name")
    website_url: Optional[str] = Field(None, description="Website URL")
    industry: Optional[str] = Field(None, description="Industry")
    description: Optional[str] = Field(None, description="Client description")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_name: Optional[str] = Field(None, description="Contact name")
    status: ClientStatus = Field(..., description="Client status")
    monthly_budget: Optional[str] = Field(None, description="Monthly budget range")
    onboarding_completed: bool = Field(..., description="Onboarding status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ClientStats(BaseModel):
    client_id: str = Field(..., description="Client ID")
    client_name: str = Field(..., description="Client name")
    brands_tracked: int = Field(..., description="Number of brands tracked")
    total_mentions: int = Field(..., description="Total mentions found")
    ai_citations: int = Field(..., description="AI citations count")
    average_sentiment: float = Field(..., description="Average sentiment score")
    roi_investments: int = Field(..., description="Number of ROI investments")
    total_investment: float = Field(..., description="Total investment amount")
    estimated_roi: float = Field(..., description="Estimated ROI percentage")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ClientBrandAssignment(BaseModel):
    client_id: str = Field(..., description="Client ID")
    brand_id: str = Field(..., description="Brand ID")
    is_primary: bool = Field(default=False, description="Primary brand flag")


class ClientBrandResponse(BaseModel):
    id: str = Field(..., description="Assignment ID")
    client_id: str = Field(..., description="Client ID")
    brand_id: str = Field(..., description="Brand ID")
    brand_name: str = Field(..., description="Brand name")
    is_primary: bool = Field(..., description="Primary brand flag")
    created_at: datetime = Field(..., description="Assignment timestamp")
    
    class Config:
        from_attributes = True


class ClientReportCreate(BaseModel):
    client_id: str = Field(..., description="Client ID")
    title: str = Field(..., max_length=255, description="Report title")
    report_type: str = Field(..., description="Report type")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    is_white_labeled: bool = Field(default=False, description="White label flag")
    
    @validator('report_type')
    def validate_report_type(cls, v):
        valid_types = ['weekly', 'monthly', 'quarterly', 'custom']
        if v not in valid_types:
            raise ValueError(f'Report type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('period_end')
    def validate_period_end(cls, v, values):
        if 'period_start' in values and v <= values['period_start']:
            raise ValueError('Period end must be after period start')
        return v


class ClientReportResponse(BaseModel):
    id: str = Field(..., description="Report ID")
    client_id: str = Field(..., description="Client ID")
    title: str = Field(..., description="Report title")
    report_type: str = Field(..., description="Report type")
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    is_white_labeled: bool = Field(..., description="White label flag")
    generated_at: datetime = Field(..., description="Generation timestamp")
    
    class Config:
        from_attributes = True


class ClientDashboardData(BaseModel):
    """Dashboard data for agency client overview"""
    client: ClientResponse
    stats: ClientStats
    recent_mentions: List[dict] = Field(..., description="Recent brand mentions")
    roi_summary: dict = Field(..., description="ROI summary data")
    content_opportunities: List[dict] = Field(..., description="Content opportunities")
    
    class Config:
        from_attributes = True


class ClientOnboardingStep(BaseModel):
    step_id: str = Field(..., description="Step identifier")
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Step description")
    is_completed: bool = Field(..., description="Completion status")
    required: bool = Field(..., description="Required flag")
    order: int = Field(..., description="Step order")


class ClientOnboardingStatus(BaseModel):
    client_id: str = Field(..., description="Client ID")
    overall_progress: float = Field(..., description="Overall progress percentage")
    steps: List[ClientOnboardingStep] = Field(..., description="Onboarding steps")
    is_completed: bool = Field(..., description="Overall completion status")
    
    class Config:
        from_attributes = True