"""
Citations API endpoints
Core citation extraction and analysis functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.citation_extraction_service import citation_extraction_service, MentionType, SentimentType
from app.database import db_manager
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class CitationExtractionRequest(BaseModel):
    """Request model for citation extraction"""
    response_text: str = Field(..., description="AI response text to analyze")
    query_text: str = Field(..., description="Original query text")
    brand_names: List[str] = Field(..., min_items=1, max_items=20, description="Brands to extract mentions for")
    platform: str = Field(default="unknown", description="AI platform name")
    include_context: bool = Field(default=True, description="Include context around mentions")
    context_window: int = Field(default=150, description="Context window size in characters")


class BrandMentionResponse(BaseModel):
    """Response model for brand mention"""
    brand_name: str
    mentioned: bool
    position: int
    mention_text: str
    context: str
    mention_type: str
    sentiment_score: float
    sentiment_type: str
    prominence_score: float
    confidence_score: float
    extracted_at: datetime
    metadata: Dict[str, Any]


class CitationExtractionResponse(BaseModel):
    """Response model for citation extraction"""
    query_text: str
    platform: str
    total_brands_checked: int
    brands_mentioned: int
    brand_mentions: List[BrandMentionResponse]
    response_analysis: Dict[str, Any]
    extraction_metadata: Dict[str, Any]
    processed_at: datetime


class CitationAnalyticsRequest(BaseModel):
    """Request model for citation analytics"""
    brand_name: Optional[str] = Field(default=None, description="Filter by brand name")
    days: int = Field(default=30, ge=1, le=365, description="Number of days to analyze")
    platform: Optional[str] = Field(default=None, description="Filter by platform")
    mention_type: Optional[str] = Field(default=None, description="Filter by mention type")


class CitationAnalyticsResponse(BaseModel):
    """Response model for citation analytics"""
    summary: Dict[str, Any]
    sentiment_distribution: Dict[str, int]
    mention_types: Dict[str, int]
    platform_performance: List[Dict[str, Any]]
    period_days: int
    generated_at: datetime


class BrandAliasRequest(BaseModel):
    """Request model for brand alias"""
    brand_id: str = Field(..., description="Brand ID")
    alias: str = Field(..., description="Brand alias")
    alias_type: str = Field(default="manual", description="Type of alias")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")


class BrandAliasResponse(BaseModel):
    """Response model for brand alias"""
    alias_id: str
    brand_id: str
    alias: str
    alias_type: str
    is_active: bool
    confidence_score: Optional[float]
    usage_count: int
    created_at: datetime


@router.post("/extract", response_model=CitationExtractionResponse)
async def extract_citations(
    request: CitationExtractionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Extract brand citations from AI response text
    Core functionality for mention analysis
    """
    try:
        logger.info(f"Extracting citations for {len(request.brand_names)} brands from {request.platform}")
        
        # Run citation extraction
        result = await citation_extraction_service.extract_citations(
            response_text=request.response_text,
            query_text=request.query_text,
            brand_names=request.brand_names,
            platform=request.platform,
            include_context=request.include_context,
            context_window=request.context_window
        )
        
        # Store results in database
        await citation_extraction_service.store_citations(str(current_user.id), result)
        
        # Convert to response format
        brand_mentions = []
        for mention in result.brand_mentions:
            brand_mentions.append(BrandMentionResponse(
                brand_name=mention.brand_name,
                mentioned=mention.mentioned,
                position=mention.position,
                mention_text=mention.mention_text,
                context=mention.context,
                mention_type=mention.mention_type.value,
                sentiment_score=mention.sentiment_score,
                sentiment_type=mention.sentiment_type.value,
                prominence_score=mention.prominence_score,
                confidence_score=mention.confidence_score,
                extracted_at=mention.extracted_at,
                metadata=mention.metadata
            ))
        
        response = CitationExtractionResponse(
            query_text=result.query_text,
            platform=result.platform,
            total_brands_checked=result.total_brands_checked,
            brands_mentioned=result.brands_mentioned,
            brand_mentions=brand_mentions,
            response_analysis=result.response_analysis,
            extraction_metadata=result.extraction_metadata,
            processed_at=result.processed_at
        )
        
        logger.info(f"Citation extraction completed: {result.brands_mentioned}/{result.total_brands_checked} brands mentioned")
        return response
        
    except Exception as e:
        logger.error(f"Error in citation extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract citations"
        )


@router.get("/analytics", response_model=CitationAnalyticsResponse)
async def get_citation_analytics(
    brand_name: Optional[str] = None,
    days: int = 30,
    platform: Optional[str] = None,
    mention_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get citation analytics for the user"""
    try:
        logger.info(f"Getting citation analytics for user {current_user.id}")
        
        # Get analytics from service
        analytics = await citation_extraction_service.get_citation_analytics(
            user_id=str(current_user.id),
            brand_name=brand_name,
            days=days
        )
        
        # Apply additional filters if specified
        if platform or mention_type:
            analytics = await _apply_analytics_filters(
                analytics, str(current_user.id), platform, mention_type, days
            )
        
        response = CitationAnalyticsResponse(
            summary=analytics.get("summary", {}),
            sentiment_distribution=analytics.get("sentiment_distribution", {}),
            mention_types=analytics.get("mention_types", {}),
            platform_performance=analytics.get("platform_performance", []),
            period_days=analytics.get("period_days", days),
            generated_at=analytics.get("generated_at", datetime.utcnow())
        )
        
        logger.info(f"Citation analytics retrieved: {analytics.get('summary', {}).get('total_citations', 0)} citations")
        return response
        
    except Exception as e:
        logger.error(f"Error getting citation analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get citation analytics"
        )


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_citation_history(
    limit: int = 50,
    offset: int = 0,
    brand_name: Optional[str] = None,
    platform: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get citation history for the user"""
    try:
        # Build query conditions
        conditions = ["qr.user_id = :user_id"]
        params = {"user_id": str(current_user.id), "limit": limit, "offset": offset}
        
        if brand_name:
            conditions.append("c.brand_name = :brand_name")
            params["brand_name"] = brand_name
        
        if platform:
            conditions.append("qr.platform = :platform")
            params["platform"] = platform
        
        where_clause = " AND ".join(conditions)
        
        # Get citation history
        citations = await db_manager.fetch_all(
            f"""
            SELECT c.id, c.brand_name, c.mentioned, c.position, c.mention_text, 
                   c.context, c.mention_type, c.sentiment_score, c.sentiment_type,
                   c.prominence_score, c.confidence_score, c.created_at,
                   qr.query_text, qr.platform, qr.executed_at
            FROM citations c
            JOIN query_results qr ON c.query_result_id = qr.id
            WHERE {where_clause}
            ORDER BY c.created_at DESC
            LIMIT :limit OFFSET :offset
            """,
            params
        )
        
        # Format response
        history = []
        for citation in citations:
            history.append({
                "citation_id": citation.id,
                "brand_name": citation.brand_name,
                "mentioned": citation.mentioned,
                "position": citation.position,
                "mention_text": citation.mention_text,
                "context": citation.context,
                "mention_type": citation.mention_type,
                "sentiment_score": float(citation.sentiment_score) if citation.sentiment_score else None,
                "sentiment_type": citation.sentiment_type,
                "prominence_score": float(citation.prominence_score) if citation.prominence_score else None,
                "confidence_score": float(citation.confidence_score) if citation.confidence_score else None,
                "created_at": citation.created_at,
                "query_text": citation.query_text,
                "platform": citation.platform,
                "executed_at": citation.executed_at
            })
        
        logger.info(f"Retrieved {len(history)} citation history records")
        return history
        
    except Exception as e:
        logger.error(f"Error getting citation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get citation history"
        )


@router.post("/brand-aliases", response_model=BrandAliasResponse)
async def create_brand_alias(
    request: BrandAliasRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new brand alias for better mention detection"""
    try:
        # Verify brand ownership
        brand = await db_manager.fetch_one(
            "SELECT id FROM tracked_brands WHERE id = :brand_id AND user_id = :user_id",
            {"brand_id": request.brand_id, "user_id": str(current_user.id)}
        )
        
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found or not owned by user"
            )
        
        # Create alias
        alias_id = f"alias_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        await db_manager.execute_query(
            """
            INSERT INTO brand_aliases (id, user_id, brand_id, alias, alias_type, 
                                     confidence_score, created_at)
            VALUES (:id, :user_id, :brand_id, :alias, :alias_type, 
                   :confidence_score, :created_at)
            """,
            {
                "id": alias_id,
                "user_id": str(current_user.id),
                "brand_id": request.brand_id,
                "alias": request.alias,
                "alias_type": request.alias_type,
                "confidence_score": request.confidence_score,
                "created_at": datetime.utcnow()
            }
        )
        
        response = BrandAliasResponse(
            alias_id=alias_id,
            brand_id=request.brand_id,
            alias=request.alias,
            alias_type=request.alias_type,
            is_active=True,
            confidence_score=request.confidence_score,
            usage_count=0,
            created_at=datetime.utcnow()
        )
        
        logger.info(f"Created brand alias '{request.alias}' for brand {request.brand_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating brand alias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create brand alias"
        )


@router.get("/brand-aliases", response_model=List[BrandAliasResponse])
async def get_brand_aliases(
    brand_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get brand aliases for the user"""
    try:
        # Build query conditions
        conditions = ["ba.user_id = :user_id", "ba.is_active = true"]
        params = {"user_id": str(current_user.id)}
        
        if brand_id:
            conditions.append("ba.brand_id = :brand_id")
            params["brand_id"] = brand_id
        
        where_clause = " AND ".join(conditions)
        
        # Get aliases
        aliases = await db_manager.fetch_all(
            f"""
            SELECT ba.id, ba.brand_id, ba.alias, ba.alias_type, ba.is_active,
                   ba.confidence_score, ba.usage_count, ba.created_at,
                   tb.name as brand_name
            FROM brand_aliases ba
            JOIN tracked_brands tb ON ba.brand_id = tb.id
            WHERE {where_clause}
            ORDER BY ba.usage_count DESC, ba.created_at DESC
            """,
            params
        )
        
        # Format response
        response = []
        for alias in aliases:
            response.append(BrandAliasResponse(
                alias_id=alias.id,
                brand_id=alias.brand_id,
                alias=alias.alias,
                alias_type=alias.alias_type,
                is_active=alias.is_active,
                confidence_score=float(alias.confidence_score) if alias.confidence_score else None,
                usage_count=alias.usage_count,
                created_at=alias.created_at
            ))
        
        logger.info(f"Retrieved {len(response)} brand aliases")
        return response
        
    except Exception as e:
        logger.error(f"Error getting brand aliases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand aliases"
        )


@router.delete("/brand-aliases/{alias_id}")
async def delete_brand_alias(
    alias_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a brand alias"""
    try:
        # Verify ownership and deactivate
        result = await db_manager.execute_query(
            """
            UPDATE brand_aliases 
            SET is_active = false, updated_at = :updated_at
            WHERE id = :alias_id AND user_id = :user_id
            """,
            {
                "alias_id": alias_id,
                "user_id": str(current_user.id),
                "updated_at": datetime.utcnow()
            }
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand alias not found or not owned by user"
            )
        
        logger.info(f"Deleted brand alias {alias_id}")
        return {"message": "Brand alias deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting brand alias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete brand alias"
        )


@router.get("/mention-types", response_model=List[str])
async def get_mention_types():
    """Get available mention types"""
    return [mention_type.value for mention_type in MentionType]


@router.get("/sentiment-types", response_model=List[str])
async def get_sentiment_types():
    """Get available sentiment types"""
    return [sentiment_type.value for sentiment_type in SentimentType]


async def _apply_analytics_filters(
    analytics: Dict[str, Any],
    user_id: str,
    platform: Optional[str],
    mention_type: Optional[str],
    days: int
) -> Dict[str, Any]:
    """Apply additional filters to analytics data"""
    try:
        # Build query conditions
        conditions = ["qr.user_id = :user_id", "c.created_at >= NOW() - INTERVAL ':days days'"]
        params = {"user_id": user_id, "days": days}
        
        if platform:
            conditions.append("qr.platform = :platform")
            params["platform"] = platform
        
        if mention_type:
            conditions.append("c.mention_type = :mention_type")
            params["mention_type"] = mention_type
        
        where_clause = " AND ".join(conditions)
        
        # Get filtered statistics
        stats = await db_manager.fetch_one(
            f"""
            SELECT COUNT(*) as total_citations,
                   COUNT(DISTINCT c.brand_name) as brands_mentioned,
                   COUNT(DISTINCT qr.platform) as platforms_covered,
                   AVG(c.sentiment_score) as avg_sentiment,
                   AVG(c.prominence_score) as avg_prominence,
                   AVG(c.confidence_score) as avg_confidence
            FROM citations c
            JOIN query_results qr ON c.query_result_id = qr.id
            WHERE {where_clause}
            """,
            params
        )
        
        # Update analytics with filtered data
        if stats:
            analytics["summary"].update({
                "total_citations": stats.total_citations,
                "brands_mentioned": stats.brands_mentioned,
                "platforms_covered": stats.platforms_covered,
                "avg_sentiment": float(stats.avg_sentiment) if stats.avg_sentiment else 0.0,
                "avg_prominence": float(stats.avg_prominence) if stats.avg_prominence else 0.0,
                "avg_confidence": float(stats.avg_confidence) if stats.avg_confidence else 0.0
            })
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error applying analytics filters: {e}")
        return analytics