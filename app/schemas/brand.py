from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import uuid


class BrandCreate(BaseModel):
    name: str = Field(..., max_length=255, description="Brand name")
    aliases: Optional[List[str]] = Field(default=[], description="Brand aliases/alternative names")
    description: Optional[str] = Field(None, description="Brand description")
    website_url: Optional[str] = Field(None, max_length=500, description="Brand website URL")
    is_primary: Optional[bool] = Field(default=False, description="Primary brand flag")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Brand name cannot be empty')
        return v.strip()
    
    @validator('aliases')
    def validate_aliases(cls, v):
        if v:
            # Remove duplicates and empty strings
            cleaned = list(set(alias.strip() for alias in v if alias.strip()))
            if len(cleaned) > 10:
                raise ValueError('Maximum 10 aliases allowed')
            return cleaned
        return []
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v:
            v = v.strip()
            if not v.startswith(('http://', 'https://')):
                v = f'https://{v}'
            return v
        return None


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255, description="Brand name")
    aliases: Optional[List[str]] = Field(None, description="Brand aliases/alternative names")
    description: Optional[str] = Field(None, description="Brand description")
    website_url: Optional[str] = Field(None, max_length=500, description="Brand website URL")
    is_primary: Optional[bool] = Field(None, description="Primary brand flag")
    is_active: Optional[bool] = Field(None, description="Brand active status")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Brand name cannot be empty')
        return v.strip() if v else None
    
    @validator('aliases')
    def validate_aliases(cls, v):
        if v is not None:
            # Remove duplicates and empty strings
            cleaned = list(set(alias.strip() for alias in v if alias.strip()))
            if len(cleaned) > 10:
                raise ValueError('Maximum 10 aliases allowed')
            return cleaned
        return None
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v:
            v = v.strip()
            if not v.startswith(('http://', 'https://')):
                v = f'https://{v}'
            return v
        return None


class BrandResponse(BaseModel):
    id: str = Field(..., description="Brand ID")
    name: str = Field(..., description="Brand name")
    aliases: List[str] = Field(..., description="Brand aliases")
    description: Optional[str] = Field(None, description="Brand description")
    website_url: Optional[str] = Field(None, description="Brand website URL")
    is_primary: bool = Field(..., description="Primary brand flag")
    is_active: bool = Field(..., description="Brand active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class BrandStats(BaseModel):
    brand_id: str = Field(..., description="Brand ID")
    brand_name: str = Field(..., description="Brand name")
    total_mentions: int = Field(..., description="Total mentions count")
    mention_rate: float = Field(..., description="Mention rate percentage")
    average_prominence: float = Field(..., description="Average prominence score")
    average_sentiment: float = Field(..., description="Average sentiment score")
    platforms: List[str] = Field(..., description="Platforms where mentioned")
    last_mentioned: Optional[datetime] = Field(None, description="Last mention timestamp")
    
    class Config:
        from_attributes = True


class BrandBulkCreate(BaseModel):
    brands: List[BrandCreate] = Field(..., description="List of brands to create")
    
    @validator('brands')
    def validate_brands(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 brands allowed in bulk operation')
        return v


class BrandBulkResponse(BaseModel):
    created: List[BrandResponse] = Field(..., description="Successfully created brands")
    failed: List[dict] = Field(..., description="Failed brand creations with errors")
    
    class Config:
        from_attributes = True