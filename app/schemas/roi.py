from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class InvestmentType(str, Enum):
    REVIEW_SITE = "review_site"
    CONTENT = "content"
    ADVERTISING = "advertising"
    PR = "pr"
    SOCIAL = "social"
    OTHER = "other"


class InvestmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ROIInvestmentCreate(BaseModel):
    client_id: str = Field(..., description="Client ID")
    investment_type: InvestmentType = Field(..., description="Investment type")
    platform: str = Field(..., max_length=100, description="Platform name")
    investment_amount: Decimal = Field(..., description="Investment amount")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    investment_date: datetime = Field(..., description="Investment date")
    description: Optional[str] = Field(None, description="Investment description")
    expected_roi: Optional[Decimal] = Field(None, description="Expected ROI percentage")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('investment_amount')
    def validate_investment_amount(cls, v):
        if v <= 0:
            raise ValueError('Investment amount must be greater than 0')
        if v > 1000000:
            raise ValueError('Investment amount cannot exceed $1,000,000')
        return v
    
    @validator('expected_roi')
    def validate_expected_roi(cls, v):
        if v is not None and (v < -100 or v > 1000):
            raise ValueError('Expected ROI must be between -100% and 1000%')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return v


class ROIInvestmentUpdate(BaseModel):
    investment_type: Optional[InvestmentType] = Field(None, description="Investment type")
    platform: Optional[str] = Field(None, max_length=100, description="Platform name")
    investment_amount: Optional[Decimal] = Field(None, description="Investment amount")
    investment_date: Optional[datetime] = Field(None, description="Investment date")
    description: Optional[str] = Field(None, description="Investment description")
    expected_roi: Optional[Decimal] = Field(None, description="Expected ROI percentage")
    actual_roi: Optional[Decimal] = Field(None, description="Actual ROI percentage")
    status: Optional[InvestmentStatus] = Field(None, description="Investment status")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('investment_amount')
    def validate_investment_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Investment amount must be greater than 0')
        return v
    
    @validator('expected_roi', 'actual_roi')
    def validate_roi(cls, v):
        if v is not None and (v < -100 or v > 1000):
            raise ValueError('ROI must be between -100% and 1000%')
        return v


class ROIInvestmentResponse(BaseModel):
    id: str = Field(..., description="Investment ID")
    client_id: str = Field(..., description="Client ID")
    investment_type: InvestmentType = Field(..., description="Investment type")
    platform: str = Field(..., description="Platform name")
    investment_amount: Decimal = Field(..., description="Investment amount")
    currency: str = Field(..., description="Currency code")
    investment_date: datetime = Field(..., description="Investment date")
    description: Optional[str] = Field(None, description="Investment description")
    expected_roi: Optional[Decimal] = Field(None, description="Expected ROI percentage")
    actual_roi: Optional[Decimal] = Field(None, description="Actual ROI percentage")
    status: InvestmentStatus = Field(..., description="Investment status")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ROIPerformanceMetricCreate(BaseModel):
    investment_id: str = Field(..., description="Investment ID")
    metric_date: datetime = Field(..., description="Metric date")
    mentions_generated: int = Field(default=0, description="Mentions generated")
    ai_citations: int = Field(default=0, description="AI citations count")
    estimated_traffic: int = Field(default=0, description="Estimated traffic")
    estimated_traffic_value: Decimal = Field(default=0, description="Estimated traffic value")
    brand_visibility_score: Optional[Decimal] = Field(None, description="Brand visibility score")
    sentiment_score: Optional[Decimal] = Field(None, description="Sentiment score")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('mentions_generated', 'ai_citations', 'estimated_traffic')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v
    
    @validator('brand_visibility_score')
    def validate_visibility_score(cls, v):
        if v is not None and (v < 0 or v > 10):
            raise ValueError('Brand visibility score must be between 0 and 10')
        return v
    
    @validator('sentiment_score')
    def validate_sentiment_score(cls, v):
        if v is not None and (v < -1 or v > 1):
            raise ValueError('Sentiment score must be between -1 and 1')
        return v


class ROIPerformanceMetricResponse(BaseModel):
    id: str = Field(..., description="Metric ID")
    investment_id: str = Field(..., description="Investment ID")
    metric_date: datetime = Field(..., description="Metric date")
    mentions_generated: int = Field(..., description="Mentions generated")
    ai_citations: int = Field(..., description="AI citations count")
    estimated_traffic: int = Field(..., description="Estimated traffic")
    estimated_traffic_value: Decimal = Field(..., description="Estimated traffic value")
    brand_visibility_score: Optional[Decimal] = Field(None, description="Brand visibility score")
    sentiment_score: Optional[Decimal] = Field(None, description="Sentiment score")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class ROICalculationResult(BaseModel):
    investment_id: str = Field(..., description="Investment ID")
    total_investment: Decimal = Field(..., description="Total investment amount")
    current_value: Decimal = Field(..., description="Current value generated")
    roi_percentage: Decimal = Field(..., description="ROI percentage")
    roi_absolute: Decimal = Field(..., description="Absolute ROI amount")
    payback_period_days: Optional[int] = Field(None, description="Payback period in days")
    break_even_date: Optional[datetime] = Field(None, description="Break-even date")
    performance_trend: str = Field(..., description="Performance trend")
    
    class Config:
        from_attributes = True


class ROIDashboardData(BaseModel):
    """ROI dashboard data for agency clients"""
    client_id: str = Field(..., description="Client ID")
    total_investments: int = Field(..., description="Total number of investments")
    total_invested: Decimal = Field(..., description="Total amount invested")
    current_value: Decimal = Field(..., description="Current value generated")
    overall_roi: Decimal = Field(..., description="Overall ROI percentage")
    active_investments: int = Field(..., description="Number of active investments")
    top_performing_platform: Optional[str] = Field(None, description="Top performing platform")
    monthly_trend: List[Dict[str, Any]] = Field(..., description="Monthly performance trend")
    investment_breakdown: List[Dict[str, Any]] = Field(..., description="Investment breakdown by type")
    
    class Config:
        from_attributes = True


class ROIReportData(BaseModel):
    """ROI report data for client reporting"""
    client_id: str = Field(..., description="Client ID")
    client_name: str = Field(..., description="Client name")
    report_period: Dict[str, datetime] = Field(..., description="Report period")
    executive_summary: Dict[str, Any] = Field(..., description="Executive summary")
    investment_performance: List[ROICalculationResult] = Field(..., description="Investment performance")
    key_metrics: Dict[str, Any] = Field(..., description="Key performance metrics")
    recommendations: List[Dict[str, Any]] = Field(..., description="Recommendations")
    next_steps: List[str] = Field(..., description="Recommended next steps")
    
    class Config:
        from_attributes = True


class ReviewSiteResponse(BaseModel):
    id: str = Field(..., description="Review site ID")
    name: str = Field(..., description="Site name")
    domain: str = Field(..., description="Site domain")
    category: str = Field(..., description="Site category")
    authority_score: Optional[int] = Field(None, description="Authority score")
    average_cost_per_review: Optional[Decimal] = Field(None, description="Average cost per review")
    ai_citation_frequency: Optional[Decimal] = Field(None, description="AI citation frequency")
    is_active: bool = Field(..., description="Active status")
    
    class Config:
        from_attributes = True


class ReviewMentionResponse(BaseModel):
    id: str = Field(..., description="Mention ID")
    review_site_id: str = Field(..., description="Review site ID")
    review_site_name: str = Field(..., description="Review site name")
    brand_id: str = Field(..., description="Brand ID")
    brand_name: str = Field(..., description="Brand name")
    mention_url: Optional[str] = Field(None, description="Mention URL")
    mention_title: Optional[str] = Field(None, description="Mention title")
    rating: Optional[Decimal] = Field(None, description="Review rating")
    review_date: Optional[datetime] = Field(None, description="Review date")
    ai_citation_count: int = Field(..., description="AI citation count")
    last_ai_citation: Optional[datetime] = Field(None, description="Last AI citation")
    sentiment_score: Optional[Decimal] = Field(None, description="Sentiment score")
    is_verified: bool = Field(..., description="Verification status")
    discovered_at: datetime = Field(..., description="Discovery timestamp")
    
    class Config:
        from_attributes = True


class ROIInvestmentWithMetrics(BaseModel):
    """ROI investment with performance metrics"""
    investment: ROIInvestmentResponse
    metrics: List[ROIPerformanceMetricResponse]
    calculations: ROICalculationResult
    mentions: List[ReviewMentionResponse]
    
    class Config:
        from_attributes = True