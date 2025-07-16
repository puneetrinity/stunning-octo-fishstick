from sqlalchemy import Column, String, Boolean, DateTime, Enum, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class PlanType(str, enum.Enum):
    # Brand tiers
    BRAND_STARTER = "brand_starter"
    BRAND_PROFESSIONAL = "brand_professional"
    
    # Agency tiers
    AGENCY_STARTER = "agency_starter"
    AGENCY_PRO = "agency_pro"
    AGENCY_ENTERPRISE = "agency_enterprise"


class UserType(str, enum.Enum):
    BRAND = "brand"
    AGENCY = "agency"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    user_type = Column(Enum(UserType), default=UserType.BRAND, nullable=False)
    plan_type = Column(Enum(PlanType), default=PlanType.BRAND_STARTER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    brands = relationship("TrackedBrand", back_populates="user", cascade="all, delete-orphan")
    query_templates = relationship("QueryTemplate", back_populates="user", cascade="all, delete-orphan")
    query_results = relationship("QueryResult", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    
    # Agency-specific relationships
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    content_gaps = relationship("ContentGap", back_populates="user", cascade="all, delete-orphan")
    competitor_content = relationship("CompetitorContent", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', type='{self.user_type}', plan='{self.plan_type}')>"
    
    @property
    def is_agency_user(self):
        return self.user_type == UserType.AGENCY
    
    @property
    def is_brand_user(self):
        return self.user_type == UserType.BRAND