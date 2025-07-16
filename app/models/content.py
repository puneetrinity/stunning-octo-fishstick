from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Integer, Numeric, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class ContentType(str, enum.Enum):
    BLOG_POST = "blog_post"
    COMPARISON = "comparison"
    TUTORIAL = "tutorial"
    CASE_STUDY = "case_study"
    FAQ = "faq"
    REVIEW = "review"
    OTHER = "other"


class ContentGap(Base):
    """Track content gaps and opportunities"""
    __tablename__ = "content_gaps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)  # For agency users
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(Enum(ContentType), nullable=False)
    industry = Column(String(100), nullable=True)
    target_keywords = Column(Text, nullable=True)  # JSON array of keywords
    competitor_content = Column(Text, nullable=True)  # JSON array of competitor content
    opportunity_score = Column(Numeric(3, 1), nullable=True)  # 0-10 scale
    ai_citation_potential = Column(Numeric(3, 1), nullable=True)  # 0-10 scale
    difficulty_score = Column(Numeric(3, 1), nullable=True)  # 0-10 scale
    status = Column(String(50), default="identified", nullable=False)  # 'identified', 'planned', 'in_progress', 'completed'
    assigned_to = Column(String(255), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    client = relationship("Client")
    content_recommendations = relationship("ContentRecommendation", back_populates="content_gap", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ContentGap(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class ContentRecommendation(Base):
    """AI-generated content recommendations"""
    __tablename__ = "content_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_gap_id = Column(UUID(as_uuid=True), ForeignKey("content_gaps.id"), nullable=False)
    recommendation_type = Column(String(50), nullable=False)  # 'outline', 'title', 'keywords', 'structure'
    recommendation_text = Column(Text, nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0-1 scale
    ai_model_used = Column(String(100), nullable=True)  # 'gpt-4', 'claude-3', etc.
    is_approved = Column(Boolean, default=False, nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content_gap = relationship("ContentGap", back_populates="content_recommendations")
    
    def __repr__(self):
        return f"<ContentRecommendation(id={self.id}, content_gap_id={self.content_gap_id}, type='{self.recommendation_type}')>"


class CompetitorContent(Base):
    """Track competitor content and performance"""
    __tablename__ = "competitor_content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    competitor_name = Column(String(255), nullable=False)
    competitor_domain = Column(String(255), nullable=True)
    content_url = Column(String(1000), nullable=True)
    content_title = Column(String(500), nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    content_summary = Column(Text, nullable=True)
    publish_date = Column(DateTime(timezone=True), nullable=True)
    ai_citation_count = Column(Integer, default=0, nullable=False)
    last_ai_citation = Column(DateTime(timezone=True), nullable=True)
    estimated_traffic = Column(Integer, nullable=True)
    social_shares = Column(Integer, default=0, nullable=False)
    backlinks_count = Column(Integer, default=0, nullable=False)
    content_quality_score = Column(Numeric(3, 1), nullable=True)  # 0-10 scale
    is_active = Column(Boolean, default=True, nullable=False)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<CompetitorContent(id={self.id}, competitor='{self.competitor_name}', title='{self.content_title}')>"


class AuthoritySource(Base):
    """Track authoritative sources in different industries"""
    __tablename__ = "authority_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    industry = Column(String(100), nullable=False)
    authority_score = Column(Integer, nullable=True)  # Domain authority score
    ai_citation_frequency = Column(Numeric(3, 2), nullable=True)  # How often AI cites this source
    content_types = Column(Text, nullable=True)  # JSON array of content types they publish
    contact_email = Column(String(255), nullable=True)
    submission_guidelines = Column(Text, nullable=True)
    average_response_time = Column(Integer, nullable=True)  # In days
    success_rate = Column(Numeric(3, 2), nullable=True)  # Success rate for getting published
    cost_estimate = Column(String(100), nullable=True)  # e.g., "Free", "$500-1000", "High"
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    authority_mentions = relationship("AuthorityMention", back_populates="authority_source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AuthoritySource(id={self.id}, name='{self.name}', domain='{self.domain}')>"


class AuthorityMention(Base):
    """Track mentions from authoritative sources"""
    __tablename__ = "authority_mentions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authority_source_id = Column(UUID(as_uuid=True), ForeignKey("authority_sources.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("tracked_brands.id"), nullable=False)
    mention_url = Column(String(1000), nullable=True)
    mention_title = Column(String(500), nullable=True)
    mention_content = Column(Text, nullable=True)
    publish_date = Column(DateTime(timezone=True), nullable=True)
    ai_citation_count = Column(Integer, default=0, nullable=False)
    last_ai_citation = Column(DateTime(timezone=True), nullable=True)
    sentiment_score = Column(Numeric(3, 2), nullable=True)
    prominence_score = Column(Numeric(3, 1), nullable=True)
    estimated_reach = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    authority_source = relationship("AuthoritySource", back_populates="authority_mentions")
    brand = relationship("TrackedBrand")
    
    def __repr__(self):
        return f"<AuthorityMention(id={self.id}, authority_source_id={self.authority_source_id}, brand_id={self.brand_id})>"