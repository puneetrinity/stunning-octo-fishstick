from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Integer, Numeric, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class ROIInvestment(Base):
    """Track ROI investments for agency clients"""
    __tablename__ = "roi_investments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Agency user
    investment_type = Column(String(50), nullable=False)  # 'review_site', 'content', 'other'
    platform = Column(String(100), nullable=False)  # 'g2', 'capterra', 'trustradius', etc.
    investment_amount = Column(Numeric(10, 2), nullable=False)  # Amount in dollars
    currency = Column(String(3), default="USD", nullable=False)
    investment_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=True)
    expected_roi = Column(Numeric(5, 2), nullable=True)  # Expected ROI percentage
    actual_roi = Column(Numeric(5, 2), nullable=True)  # Calculated ROI percentage
    status = Column(String(50), default="active", nullable=False)  # 'active', 'completed', 'cancelled'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="roi_investments")
    user = relationship("User")
    performance_metrics = relationship("ROIPerformanceMetric", back_populates="investment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ROIInvestment(id={self.id}, client_id={self.client_id}, platform='{self.platform}', amount={self.investment_amount})>"


class ROIPerformanceMetric(Base):
    """Track performance metrics for ROI investments"""
    __tablename__ = "roi_performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investment_id = Column(UUID(as_uuid=True), ForeignKey("roi_investments.id"), nullable=False)
    metric_date = Column(DateTime(timezone=True), nullable=False)
    mentions_generated = Column(Integer, default=0, nullable=False)
    ai_citations = Column(Integer, default=0, nullable=False)
    estimated_traffic = Column(Integer, default=0, nullable=False)
    estimated_traffic_value = Column(Numeric(10, 2), default=0, nullable=False)
    brand_visibility_score = Column(Numeric(3, 1), nullable=True)  # 0-10 scale
    sentiment_score = Column(Numeric(3, 2), nullable=True)  # -1 to 1 scale
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    investment = relationship("ROIInvestment", back_populates="performance_metrics")
    
    def __repr__(self):
        return f"<ROIPerformanceMetric(id={self.id}, investment_id={self.investment_id}, mentions={self.mentions_generated})>"


class ReviewSite(Base):
    """Track review sites and their properties"""
    __tablename__ = "review_sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), nullable=False)  # 'software', 'services', 'general'
    authority_score = Column(Integer, nullable=True)  # Domain authority score
    average_cost_per_review = Column(Numeric(8, 2), nullable=True)
    ai_citation_frequency = Column(Numeric(3, 2), nullable=True)  # How often AI mentions this site
    is_active = Column(Boolean, default=True, nullable=False)
    scraping_enabled = Column(Boolean, default=False, nullable=False)
    api_available = Column(Boolean, default=False, nullable=False)
    api_documentation = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    review_mentions = relationship("ReviewMention", back_populates="review_site", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ReviewSite(id={self.id}, name='{self.name}', domain='{self.domain}')>"


class ReviewMention(Base):
    """Track mentions from review sites"""
    __tablename__ = "review_mentions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_site_id = Column(UUID(as_uuid=True), ForeignKey("review_sites.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("tracked_brands.id"), nullable=False)
    mention_url = Column(String(1000), nullable=True)
    mention_title = Column(String(500), nullable=True)
    mention_content = Column(Text, nullable=True)
    rating = Column(Numeric(3, 1), nullable=True)  # Review rating if available
    review_date = Column(DateTime(timezone=True), nullable=True)
    ai_citation_count = Column(Integer, default=0, nullable=False)
    last_ai_citation = Column(DateTime(timezone=True), nullable=True)
    sentiment_score = Column(Numeric(3, 2), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    review_site = relationship("ReviewSite", back_populates="review_mentions")
    brand = relationship("TrackedBrand")
    
    def __repr__(self):
        return f"<ReviewMention(id={self.id}, review_site_id={self.review_site_id}, brand_id={self.brand_id})>"