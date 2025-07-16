from sqlalchemy import Column, String, Boolean, DateTime, UUID, ForeignKey, ARRAY, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class TrackedBrand(Base):
    __tablename__ = "tracked_brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    aliases = Column(ARRAY(String), default=[], nullable=False)
    description = Column(Text, nullable=True)
    website_url = Column(String(500), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="brands")
    citations = relationship("Citation", back_populates="brand", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TrackedBrand(id={self.id}, name='{self.name}', user_id={self.user_id})>"