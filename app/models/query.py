from sqlalchemy import Column, String, Boolean, DateTime, UUID, ForeignKey, Integer, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class QueryPriority(int, enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class Platform(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"


class QueryTemplate(Base):
    __tablename__ = "query_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    query_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    priority = Column(Enum(QueryPriority), default=QueryPriority.MEDIUM, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="query_templates")
    query_results = relationship("QueryResult", back_populates="query_template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QueryTemplate(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class QueryResult(Base):
    __tablename__ = "query_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query_template_id = Column(UUID(as_uuid=True), ForeignKey("query_templates.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    response_text = Column(Text, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    status = Column(String(50), default="completed", nullable=False)
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="query_results")
    query_template = relationship("QueryTemplate", back_populates="query_results")
    citations = relationship("Citation", back_populates="query_result", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QueryResult(id={self.id}, platform='{self.platform}', user_id={self.user_id})>"