"""
Authority Sources API endpoints
Based on Reddit intelligence: "Ideally you want a series of mentions from totally unconnected sources that are authoritive"
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.authority_source_service import authority_source_service, AuthorityLevel, SourceType
from app.database import db_manager
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class AuthorityMonitoringRequest(BaseModel):
    """Request model for authority source monitoring"""
    brand_names: List[str] = Field(..., min_items=1, max_items=10, description="Brands to monitor")
    industry: str = Field(default="saas", description="Industry category")
    authority_levels: Optional[List[str]] = Field(default=None, description="Authority levels to monitor")
    max_sources_per_tier: int = Field(default=5, ge=1, le=10, description="Max sources per tier")
    days_back: int = Field(default=30, ge=1, le=365, description="Days to look back")
    deep_analysis: bool = Field(default=False, description="Include deep content analysis")


class AuthorityMonitoringResponse(BaseModel):
    """Response model for authority monitoring"""
    session_id: str
    brands_monitored: List[str]
    sources_monitored: List[str]
    total_mentions: int
    estimated_completion: datetime
    monitoring_started: datetime
    status: str
    message: str


class AuthoritySourceResponse(BaseModel):
    """Response model for authority source"""
    id: str
    name: str
    domain: str
    industry: str
    source_type: str
    authority_level: str
    authority_score: int
    ai_citation_frequency: float
    content_types: List[str]
    contact_email: Optional[str]
    submission_guidelines: Optional[str]
    average_response_time: Optional[int]
    success_rate: Optional[float]
    cost_estimate: Optional[str]
    is_active: bool


class AuthorityMentionResponse(BaseModel):
    """Response model for authority mention"""
    id: str
    authority_source_id: str
    source_name: str
    brand_name: str
    mention_url: str
    mention_title: str
    mention_content: str
    publish_date: datetime
    author: str
    ai_citation_potential: float
    prominence_score: float
    sentiment_score: float
    estimated_reach: int
    backlink_value: float
    discovered_at: datetime
    is_verified: bool


class AuthorityAnalyticsResponse(BaseModel):
    """Response model for authority analytics"""
    total_mentions: int
    sources_covered: int
    authority_distribution: Dict[str, int]
    avg_citation_potential: float
    total_estimated_reach: int
    by_source: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime


class AuthorityOutreachRequest(BaseModel):
    """Request model for authority outreach"""
    authority_source_id: str = Field(..., description="Authority source ID")
    brand_name: str = Field(..., description="Brand name")
    outreach_type: str = Field(..., description="Type of outreach")
    contact_person: Optional[str] = Field(default=None, description="Contact person")
    contact_email: Optional[str] = Field(default=None, description="Contact email")
    subject_line: Optional[str] = Field(default=None, description="Email subject")
    message_content: Optional[str] = Field(default=None, description="Email content")
    estimated_value: Optional[float] = Field(default=None, description="Estimated value")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class AuthorityOutreachResponse(BaseModel):
    """Response model for authority outreach"""
    outreach_id: str
    authority_source_id: str
    brand_name: str
    outreach_type: str
    status: str
    created_at: datetime
    message: str


@router.post("/monitor", response_model=AuthorityMonitoringResponse)
async def start_authority_monitoring(
    request: AuthorityMonitoringRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Start monitoring brands across authority sources
    Based on Reddit intelligence: Target unconnected authoritative sources
    """
    try:
        # Generate session ID
        session_id = f"authority_monitoring_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        # Validate request
        if not request.brand_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one brand name is required"
            )
        
        # Parse authority levels
        authority_levels = []
        if request.authority_levels:
            for level_name in request.authority_levels:
                try:
                    level = AuthorityLevel(level_name.lower())
                    authority_levels.append(level)
                except ValueError:
                    logger.warning(f"Invalid authority level: {level_name}")
        
        # Get authority sources for preview
        sources_list = await authority_source_service.get_authority_sources_by_industry(request.industry)
        sources_monitored = [s["name"] for s in sources_list[:request.max_sources_per_tier * len(authority_levels or [AuthorityLevel.TIER_1, AuthorityLevel.TIER_2])]]
        
        # Store monitoring session
        await db_manager.execute_query(
            """
            INSERT INTO monitoring_sessions (id, user_id, brand_names, category, 
                                           include_reddit, include_chatgpt, time_range, 
                                           status, created_at, current_task)
            VALUES (:id, :user_id, :brand_names, :category, 
                    :include_reddit, :include_chatgpt, :time_range, 
                    :status, :created_at, :current_task)
            """,
            {
                "id": session_id,
                "user_id": str(current_user.id),
                "brand_names": ",".join(request.brand_names),
                "category": request.industry,
                "include_reddit": False,
                "include_chatgpt": False,
                "time_range": f"{request.days_back}d",
                "status": "running",
                "created_at": datetime.utcnow(),
                "current_task": "Starting authority source monitoring..."
            }
        )
        
        # Start background monitoring task
        background_tasks.add_task(
            run_authority_monitoring_task,
            session_id,
            str(current_user.id),
            request.brand_names,
            request.industry,
            authority_levels,
            request.max_sources_per_tier,
            request.days_back,
            request.deep_analysis
        )
        
        # Estimate completion time
        estimated_duration = len(request.brand_names) * len(sources_monitored) * 1  # 1 minute per source per brand
        estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_duration)
        
        logger.info(f"Started authority monitoring session {session_id} for user {current_user.id}")
        
        return AuthorityMonitoringResponse(
            session_id=session_id,
            brands_monitored=request.brand_names,
            sources_monitored=sources_monitored,
            total_mentions=0,
            estimated_completion=estimated_completion,
            monitoring_started=datetime.utcnow(),
            status="running",
            message=f"Authority monitoring started for {len(request.brand_names)} brands across {len(sources_monitored)} sources"
        )
        
    except Exception as e:
        logger.error(f"Error starting authority monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start authority monitoring"
        )


@router.get("/sources", response_model=List[AuthoritySourceResponse])
async def get_authority_sources(
    industry: str = "saas",
    authority_level: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get available authority sources for an industry"""
    try:
        sources = await authority_source_service.get_authority_sources_by_industry(industry)
        
        # Filter by authority level if specified
        if authority_level:
            sources = [s for s in sources if s["authority_level"] == authority_level]
        
        # Convert to response format
        response_sources = []
        for source in sources:
            response_sources.append(AuthoritySourceResponse(
                id=source["id"],
                name=source["name"],
                domain=source["domain"],
                industry=source["industry"],
                source_type=source["source_type"],
                authority_level=source["authority_level"],
                authority_score=source["authority_score"],
                ai_citation_frequency=source["ai_citation_frequency"],
                content_types=source["content_types"],
                contact_email=source["contact_email"],
                submission_guidelines=source["submission_guidelines"],
                average_response_time=source["average_response_time"],
                success_rate=source["success_rate"],
                cost_estimate=source["cost_estimate"],
                is_active=source["is_active"]
            ))
        
        logger.info(f"Retrieved {len(response_sources)} authority sources for industry {industry}")
        return response_sources
        
    except Exception as e:
        logger.error(f"Error getting authority sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get authority sources"
        )


@router.get("/mentions", response_model=List[AuthorityMentionResponse])
async def get_authority_mentions(
    brand_name: Optional[str] = None,
    authority_source_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get authority source mentions"""
    try:
        # Build query conditions
        conditions = ["am.user_id = :user_id"]
        params = {"user_id": str(current_user.id), "limit": limit, "offset": offset}
        
        if brand_name:
            conditions.append("am.brand_name = :brand_name")
            params["brand_name"] = brand_name
        
        if authority_source_id:
            conditions.append("am.authority_source_id = :authority_source_id")
            params["authority_source_id"] = authority_source_id
        
        where_clause = " AND ".join(conditions)
        
        # Get mentions
        mentions = await db_manager.fetch_all(
            f"""
            SELECT am.id, am.authority_source_id, aus.name as source_name, am.brand_name,
                   am.mention_url, am.mention_title, am.mention_content, am.publish_date,
                   am.author, am.ai_citation_potential, am.prominence_score, 
                   am.sentiment_score, am.estimated_reach, am.backlink_value,
                   am.discovered_at, am.is_verified
            FROM authority_mentions am
            JOIN authority_sources aus ON am.authority_source_id = aus.id
            WHERE {where_clause}
            ORDER BY am.discovered_at DESC
            LIMIT :limit OFFSET :offset
            """,
            params
        )
        
        # Convert to response format
        response_mentions = []
        for mention in mentions:
            response_mentions.append(AuthorityMentionResponse(
                id=mention.id,
                authority_source_id=mention.authority_source_id,
                source_name=mention.source_name,
                brand_name=mention.brand_name,
                mention_url=mention.mention_url,
                mention_title=mention.mention_title,
                mention_content=mention.mention_content,
                publish_date=mention.publish_date,
                author=mention.author,
                ai_citation_potential=float(mention.ai_citation_potential),
                prominence_score=float(mention.prominence_score),
                sentiment_score=float(mention.sentiment_score) if mention.sentiment_score else 0.0,
                estimated_reach=mention.estimated_reach if mention.estimated_reach else 0,
                backlink_value=float(mention.backlink_value) if mention.backlink_value else 0.0,
                discovered_at=mention.discovered_at,
                is_verified=mention.is_verified
            ))
        
        logger.info(f"Retrieved {len(response_mentions)} authority mentions")
        return response_mentions
        
    except Exception as e:
        logger.error(f"Error getting authority mentions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get authority mentions"
        )


@router.get("/analytics", response_model=AuthorityAnalyticsResponse)
async def get_authority_analytics(
    brand_name: Optional[str] = None,
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get authority source analytics"""
    try:
        # Get analytics from service
        analytics = await authority_source_service.get_authority_summary(
            str(current_user.id), brand_name or ""
        )
        
        # Get additional analytics data
        conditions = ["am.user_id = :user_id", "am.discovered_at >= NOW() - INTERVAL ':days days'"]
        params = {"user_id": str(current_user.id), "days": days}
        
        if brand_name:
            conditions.append("am.brand_name = :brand_name")
            params["brand_name"] = brand_name
        
        where_clause = " AND ".join(conditions)
        
        # Get authority distribution
        authority_dist = await db_manager.fetch_all(
            f"""
            SELECT aus.authority_level, COUNT(*) as mention_count
            FROM authority_mentions am
            JOIN authority_sources aus ON am.authority_source_id = aus.id
            WHERE {where_clause}
            GROUP BY aus.authority_level
            ORDER BY mention_count DESC
            """,
            params
        )
        
        authority_distribution = {row.authority_level: row.mention_count for row in authority_dist}
        
        # Generate recommendations
        recommendations = []
        total_mentions = analytics.get("total_mentions", 0)
        
        if total_mentions == 0:
            recommendations.append("No authority mentions found - focus on building relationships with tier 1 sources")
            recommendations.append("Target unconnected authoritative sources for AI citation potential")
        else:
            recommendations.append(f"Found {total_mentions} authority mentions - good foundation for AI citations")
        
        tier_1_count = authority_distribution.get("tier_1", 0)
        if tier_1_count == 0:
            recommendations.append("Missing tier 1 authority mentions - target Forbes, TechCrunch, Inc.")
        else:
            recommendations.append(f"Excellent: {tier_1_count} tier 1 authority mentions")
        
        avg_citation_potential = analytics.get("avg_citation_potential", 0)
        if avg_citation_potential > 0.8:
            recommendations.append("High AI citation potential from authority sources")
        elif avg_citation_potential > 0.6:
            recommendations.append("Good AI citation potential - monitor for actual citations")
        else:
            recommendations.append("Low AI citation potential - focus on higher authority sources")
        
        response = AuthorityAnalyticsResponse(
            total_mentions=analytics.get("total_mentions", 0),
            sources_covered=analytics.get("sources_covered", 0),
            authority_distribution=authority_distribution,
            avg_citation_potential=avg_citation_potential,
            total_estimated_reach=analytics.get("total_estimated_reach", 0),
            by_source=analytics.get("by_source", {}),
            recommendations=recommendations[:5],
            generated_at=datetime.utcnow()
        )
        
        logger.info(f"Generated authority analytics: {response.total_mentions} mentions")
        return response
        
    except Exception as e:
        logger.error(f"Error getting authority analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get authority analytics"
        )


@router.post("/outreach", response_model=AuthorityOutreachResponse)
async def create_authority_outreach(
    request: AuthorityOutreachRequest,
    current_user: User = Depends(get_current_user)
):
    """Create authority outreach campaign"""
    try:
        outreach_id = f"outreach_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        # Store outreach record
        await db_manager.execute_query(
            """
            INSERT INTO authority_outreach (id, user_id, authority_source_id, brand_name,
                                          outreach_type, contact_person, contact_email,
                                          subject_line, message_content, estimated_value,
                                          notes, created_at)
            VALUES (:id, :user_id, :authority_source_id, :brand_name,
                   :outreach_type, :contact_person, :contact_email,
                   :subject_line, :message_content, :estimated_value,
                   :notes, :created_at)
            """,
            {
                "id": outreach_id,
                "user_id": str(current_user.id),
                "authority_source_id": request.authority_source_id,
                "brand_name": request.brand_name,
                "outreach_type": request.outreach_type,
                "contact_person": request.contact_person,
                "contact_email": request.contact_email,
                "subject_line": request.subject_line,
                "message_content": request.message_content,
                "estimated_value": request.estimated_value,
                "notes": request.notes,
                "created_at": datetime.utcnow()
            }
        )
        
        response = AuthorityOutreachResponse(
            outreach_id=outreach_id,
            authority_source_id=request.authority_source_id,
            brand_name=request.brand_name,
            outreach_type=request.outreach_type,
            status="planned",
            created_at=datetime.utcnow(),
            message=f"Authority outreach created for {request.brand_name}"
        )
        
        logger.info(f"Created authority outreach {outreach_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating authority outreach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create authority outreach"
        )


@router.get("/outreach", response_model=List[Dict[str, Any]])
async def get_authority_outreach(
    brand_name: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get authority outreach campaigns"""
    try:
        # Build query conditions
        conditions = ["ao.user_id = :user_id"]
        params = {"user_id": str(current_user.id)}
        
        if brand_name:
            conditions.append("ao.brand_name = :brand_name")
            params["brand_name"] = brand_name
        
        if status:
            conditions.append("ao.status = :status")
            params["status"] = status
        
        where_clause = " AND ".join(conditions)
        
        # Get outreach campaigns
        campaigns = await db_manager.fetch_all(
            f"""
            SELECT ao.id, ao.authority_source_id, aus.name as source_name, ao.brand_name,
                   ao.outreach_type, ao.contact_person, ao.contact_email, ao.subject_line,
                   ao.status, ao.sent_at, ao.reply_at, ao.outcome, ao.published_url,
                   ao.estimated_value, ao.notes, ao.created_at
            FROM authority_outreach ao
            JOIN authority_sources aus ON ao.authority_source_id = aus.id
            WHERE {where_clause}
            ORDER BY ao.created_at DESC
            """,
            params
        )
        
        # Convert to response format
        response = []
        for campaign in campaigns:
            response.append({
                "outreach_id": campaign.id,
                "authority_source_id": campaign.authority_source_id,
                "source_name": campaign.source_name,
                "brand_name": campaign.brand_name,
                "outreach_type": campaign.outreach_type,
                "contact_person": campaign.contact_person,
                "contact_email": campaign.contact_email,
                "subject_line": campaign.subject_line,
                "status": campaign.status,
                "sent_at": campaign.sent_at,
                "reply_at": campaign.reply_at,
                "outcome": campaign.outcome,
                "published_url": campaign.published_url,
                "estimated_value": float(campaign.estimated_value) if campaign.estimated_value else None,
                "notes": campaign.notes,
                "created_at": campaign.created_at
            })
        
        logger.info(f"Retrieved {len(response)} authority outreach campaigns")
        return response
        
    except Exception as e:
        logger.error(f"Error getting authority outreach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get authority outreach"
        )


@router.get("/authority-levels", response_model=List[str])
async def get_authority_levels():
    """Get available authority levels"""
    return [level.value for level in AuthorityLevel]


@router.get("/source-types", response_model=List[str])
async def get_source_types():
    """Get available source types"""
    return [source_type.value for source_type in SourceType]


async def run_authority_monitoring_task(
    session_id: str,
    user_id: str,
    brand_names: List[str],
    industry: str,
    authority_levels: List[AuthorityLevel],
    max_sources_per_tier: int,
    days_back: int,
    deep_analysis: bool
):
    """Background task to run authority monitoring"""
    try:
        logger.info(f"Starting authority monitoring task {session_id}")
        
        # Update status
        await update_monitoring_status(session_id, "running", 10, "Initializing authority monitoring...")
        
        results = {
            "total_mentions": 0,
            "sources_monitored": [],
            "mentions_by_source": {},
            "authority_distribution": {},
            "ai_citation_potential": 0.0,
            "total_estimated_reach": 0,
            "recommendations": [],
            "monitoring_metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "brands": brand_names,
                "industry": industry,
                "started_at": datetime.utcnow().isoformat()
            }
        }
        
        # Run authority monitoring
        async with authority_source_service as service:
            for brand_name in brand_names:
                await update_monitoring_status(
                    session_id, "running", 30, f"Monitoring {brand_name} across authority sources..."
                )
                
                try:
                    monitoring_result = await service.monitor_brand_across_authority_sources(
                        brand_name=brand_name,
                        industry=industry,
                        authority_levels=authority_levels,
                        max_sources_per_tier=max_sources_per_tier,
                        days_back=days_back
                    )
                    
                    # Store results
                    results["total_mentions"] += monitoring_result.total_mentions
                    results["sources_monitored"] = monitoring_result.sources_monitored
                    results["mentions_by_source"][brand_name] = {}
                    
                    # Convert mentions to serializable format
                    for source_name, mentions in monitoring_result.mentions_by_source.items():
                        results["mentions_by_source"][brand_name][source_name] = [
                            {
                                "mention_url": mention.mention_url,
                                "mention_title": mention.mention_title,
                                "mention_content": mention.mention_content[:500],
                                "publish_date": mention.publish_date.isoformat(),
                                "ai_citation_potential": mention.ai_citation_potential,
                                "prominence_score": mention.prominence_score,
                                "sentiment_score": mention.sentiment_score,
                                "estimated_reach": mention.estimated_reach,
                                "backlink_value": mention.backlink_value
                            }
                            for mention in mentions
                        ]
                    
                    # Aggregate authority distribution
                    for level, count in monitoring_result.authority_distribution.items():
                        results["authority_distribution"][level] = results["authority_distribution"].get(level, 0) + count
                    
                    # Accumulate metrics
                    results["ai_citation_potential"] = max(results["ai_citation_potential"], monitoring_result.ai_citation_potential)
                    results["total_estimated_reach"] += monitoring_result.estimated_total_reach
                    results["recommendations"].extend(monitoring_result.recommendations)
                    
                    # Store mentions in database
                    await service.store_authority_mentions(user_id, monitoring_result)
                    
                    logger.info(f"Completed authority monitoring for {brand_name}: {monitoring_result.total_mentions} mentions")
                    
                except Exception as e:
                    logger.error(f"Error monitoring {brand_name}: {e}")
                    results["mentions_by_source"][brand_name] = {}
        
        # Update status to completed
        await update_monitoring_status(session_id, "completed", 100, "Authority monitoring completed!")
        
        # Store final results
        import json
        await db_manager.execute_query(
            """
            UPDATE monitoring_sessions 
            SET status = :status, progress_percentage = :progress, 
                results_data = :results_data, completed_at = :completed_at
            WHERE id = :session_id
            """,
            {
                "session_id": session_id,
                "status": "completed",
                "progress": 100.0,
                "results_data": json.dumps(results),
                "completed_at": datetime.utcnow()
            }
        )
        
        logger.info(f"Authority monitoring task {session_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in authority monitoring task {session_id}: {e}")
        
        # Update status to failed
        await update_monitoring_status(session_id, "failed", 0, f"Authority monitoring failed: {str(e)}")


async def update_monitoring_status(session_id: str, status: str, progress: float, task: str):
    """Update monitoring session status"""
    try:
        await db_manager.execute_query(
            """
            UPDATE monitoring_sessions 
            SET status = :status, progress_percentage = :progress, 
                current_task = :task, updated_at = :updated_at
            WHERE id = :session_id
            """,
            {
                "session_id": session_id,
                "status": status,
                "progress": progress,
                "task": task,
                "updated_at": datetime.utcnow()
            }
        )
    except Exception as e:
        logger.error(f"Error updating monitoring status: {e}")