from sqlalchemy import Column, String, Boolean, DateTime, UUID, ForeignKey, Integer, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Citation(Base):
    __tablename__ = "citations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_result_id = Column(UUID(as_uuid=True), ForeignKey("query_results.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("tracked_brands.id"), nullable=False)
    brand_name = Column(String(255), nullable=False)  # Denormalized for performance
    mentioned = Column(Boolean, nullable=False)
    position = Column(Integer, nullable=True)  # Position in response (0-based)
    context = Column(Text, nullable=True)  # Surrounding text
    sentence = Column(Text, nullable=True)  # Full sentence containing mention
    sentiment_score = Column(Numeric(3, 2), nullable=True)  # -1.00 to 1.00
    prominence_score = Column(Numeric(3, 1), nullable=True)  # 0.0 to 10.0
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    entity_type = Column(String(50), nullable=True)  # ORG, PERSON, PRODUCT, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    query_result = relationship("QueryResult", back_populates="citations")
    brand = relationship("TrackedBrand", back_populates="citations")
    
    def __repr__(self):
        return f"<Citation(id={self.id}, brand='{self.brand_name}', mentioned={self.mentioned})>"