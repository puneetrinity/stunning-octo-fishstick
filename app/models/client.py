from sqlalchemy import Column, String, Boolean, DateTime, UUID, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum


class ClientStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Client(Base):
    """Agency client model - used only for agency users"""
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Agency user
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    website_url = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVE, nullable=False)
    monthly_budget = Column(String(50), nullable=True)  # e.g., "$5000-10000"
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="clients")
    brands = relationship("ClientBrand", back_populates="client", cascade="all, delete-orphan")
    roi_investments = relationship("ROIInvestment", back_populates="client", cascade="all, delete-orphan")
    reports = relationship("ClientReport", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class ClientBrand(Base):
    """Brands managed by agencies for their clients"""
    __tablename__ = "client_brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("tracked_brands.id"), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="brands")
    brand = relationship("TrackedBrand")
    
    def __repr__(self):
        return f"<ClientBrand(id={self.id}, client_id={self.client_id}, brand_id={self.brand_id})>"


class ClientReport(Base):
    """Generated reports for agency clients"""
    __tablename__ = "client_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Agency user
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # 'monthly', 'quarterly', 'custom'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    report_data = Column(Text, nullable=False)  # JSON data
    is_white_labeled = Column(Boolean, default=False, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="reports")
    user = relationship("User")
    
    def __repr__(self):
        return f"<ClientReport(id={self.id}, client_id={self.client_id}, type='{self.report_type}')>"