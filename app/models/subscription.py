from sqlalchemy import Column, String, Boolean, DateTime, UUID, ForeignKey, Integer, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.user import PlanType, UserType
import uuid
import enum


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    plan_type = Column(Enum(PlanType), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    price_cents = Column(Integer, nullable=False)  # Price in cents
    currency = Column(String(3), default="USD", nullable=False)
    billing_cycle = Column(String(20), default="monthly", nullable=False)  # monthly, yearly
    trial_end = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{self.plan_type}', status='{self.status}')>"


class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Common metrics
    queries_executed = Column(Integer, default=0, nullable=False)
    api_calls_made = Column(Integer, default=0, nullable=False)
    
    # Brand-specific metrics
    brands_tracked = Column(Integer, default=0, nullable=False)
    
    # Agency-specific metrics
    clients_managed = Column(Integer, default=0, nullable=False)
    reports_generated = Column(Integer, default=0, nullable=False)
    roi_calculations = Column(Integer, default=0, nullable=False)
    
    # Advanced metrics
    content_gaps_identified = Column(Integer, default=0, nullable=False)
    competitor_content_analyzed = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")
    user = relationship("User")
    
    def __repr__(self):
        return f"<UsageRecord(id={self.id}, user_id={self.user_id}, queries={self.queries_executed})>"