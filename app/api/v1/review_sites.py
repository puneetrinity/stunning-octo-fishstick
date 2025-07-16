"""
Review Sites API endpoints
Based on Reddit intelligence: "Review sites are extremely expensive but effective for GEO as AI likes to reference reviews"
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.review_site_service import review_site_service, ReviewSiteType
from app.database import db_manager
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class ReviewSiteMonitoringRequest(BaseModel):
    """Request model for review site monitoring"""
    brand_names: List[str] = Field(..., min_items=1, max_items=10, description="Brands to monitor")
    category: str = Field(default="software", description="Industry category")
    priority_sites: Optional[List[str]] = Field(default=None, description="Priority review sites to monitor")
    include_roi_analysis: bool = Field(default=True, description="Include ROI analysis")
    deep_analysis: bool = Field(default=False, description="Include detailed review analysis")


class ReviewSiteMonitoringResponse(BaseModel):
    """Response model for review site monitoring"""
    session_id: str
    brands_monitored: List[str]
    review_sites_covered: List[str]
    total_mentions: int
    average_rating: float
    monitoring_started: datetime
    estimated_completion: datetime
    status: str
    message: str


class ReviewSiteROIAnalysis(BaseModel):
    """ROI analysis for review sites"""
    site_name: str
    investment_cost: float
    mentions_found: int
    ai_citation_frequency: float
    estimated_value: float
    roi_percentage: float
    payback_period_months: float
    authority_score: int
    recommendation: str


class ReviewSiteResults(BaseModel):
    """Complete review site monitoring results"""
    session_id: str
    brands: List[str]
    total_mentions: int
    review_sites_covered: List[str]
    mentions_by_site: Dict[str, List[Dict[str, Any]]]
    average_rating: float
    sentiment_analysis: Dict[str, Any]
    roi_analysis: List[ReviewSiteROIAnalysis]
    recommendations: List[str]
    monitoring_duration: float
    completed_at: datetime


class ReviewSiteInvestmentRequest(BaseModel):
    """Request model for tracking review site investment"""
    brand_name: str = Field(..., description="Brand name")
    review_site_name: str = Field(..., description="Review site name")
    investment_amount: float = Field(..., gt=0, description="Investment amount")
    investment_type: str = Field(..., description="Type of investment")
    expected_roi: Optional[float] = Field(default=None, description="Expected ROI percentage")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class ReviewSiteInvestmentResponse(BaseModel):
    """Response model for review site investment tracking"""
    investment_id: str
    brand_name: str
    review_site_name: str
    investment_amount: float
    investment_date: datetime
    status: str
    message: str


@router.post("/monitor", response_model=ReviewSiteMonitoringResponse)
async def start_review_site_monitoring(
    request: ReviewSiteMonitoringRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Start monitoring brands across review sites
    Based on Reddit intelligence: Track expensive review site investments
    """
    try:
        # Generate session ID
        session_id = f"review_monitoring_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        # Validate request
        if not request.brand_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one brand name is required"
            )
        
        # Parse priority sites
        priority_sites = []
        if request.priority_sites:
            for site_name in request.priority_sites:
                try:
                    site_type = ReviewSiteType(site_name.lower())
                    priority_sites.append(site_type)
                except ValueError:
                    logger.warning(f"Invalid review site type: {site_name}")
        
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
                "category": request.category,
                "include_reddit": False,
                "include_chatgpt": False,
                "time_range": "all",
                "status": "running",
                "created_at": datetime.utcnow(),
                "current_task": "Starting review site monitoring..."
            }
        )
        
        # Start background monitoring task
        background_tasks.add_task(
            run_review_site_monitoring_task,
            session_id,
            str(current_user.id),
            request.brand_names,
            request.category,
            priority_sites,
            request.include_roi_analysis,
            request.deep_analysis
        )
        
        # Estimate completion time based on number of sites and brands
        sites_count = len(priority_sites) if priority_sites else 4  # Default: G2, Capterra, TrustRadius, Gartner
        estimated_duration = sites_count * len(request.brand_names) * 2  # 2 minutes per site per brand
        estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_duration)
        
        logger.info(f"Started review site monitoring session {session_id} for user {current_user.id}")
        
        return ReviewSiteMonitoringResponse(
            session_id=session_id,
            brands_monitored=request.brand_names,
            review_sites_covered=request.priority_sites or ["G2", "Capterra", "TrustRadius", "Gartner"],
            total_mentions=0,
            average_rating=0.0,
            monitoring_started=datetime.utcnow(),
            estimated_completion=estimated_completion,
            status="running",
            message=f"Review site monitoring started for {len(request.brand_names)} brands across {sites_count} review sites"
        )
        
    except Exception as e:
        logger.error(f"Error starting review site monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start review site monitoring"
        )


@router.get("/results/{session_id}", response_model=ReviewSiteResults)
async def get_review_site_results(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get review site monitoring results"""
    try:
        session = await db_manager.fetch_one(
            """
            SELECT id, user_id, brand_names, status, include_reddit, include_chatgpt,
                   created_at, completed_at, results_data
            FROM monitoring_sessions 
            WHERE id = :session_id AND user_id = :user_id
            """,
            {
                "session_id": session_id,
                "user_id": str(current_user.id)
            }
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review site monitoring session not found"
            )
        
        if session.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review site monitoring is not completed. Status: {session.status}"
            )
        
        # Parse results data
        import json
        results_data = json.loads(session.results_data or "{}")
        
        # Calculate monitoring duration
        duration = 0
        if session.completed_at and session.created_at:
            duration = (session.completed_at - session.created_at).total_seconds() / 60
        
        # Parse ROI analysis
        roi_analysis = []
        if "roi_analysis" in results_data:
            for site_name, roi_data in results_data["roi_analysis"].items():
                if site_name != "overall":
                    roi_analysis.append(ReviewSiteROIAnalysis(
                        site_name=site_name,
                        investment_cost=roi_data.get("investment_cost", 0),
                        mentions_found=roi_data.get("mentions_found", 0),
                        ai_citation_frequency=roi_data.get("ai_citation_frequency", 0),
                        estimated_value=roi_data.get("estimated_ai_citation_value", 0),
                        roi_percentage=roi_data.get("roi_percentage", 0),
                        payback_period_months=roi_data.get("payback_period_months", 0),
                        authority_score=roi_data.get("authority_score", 0),
                        recommendation=roi_data.get("recommendation", "")
                    ))
        
        return ReviewSiteResults(
            session_id=session_id,
            brands=session.brand_names.split(","),
            total_mentions=results_data.get("total_mentions", 0),
            review_sites_covered=results_data.get("review_sites_covered", []),
            mentions_by_site=results_data.get("mentions_by_site", {}),
            average_rating=results_data.get("average_rating", 0.0),
            sentiment_analysis=results_data.get("sentiment_analysis", {}),
            roi_analysis=roi_analysis,
            recommendations=results_data.get("recommendations", []),
            monitoring_duration=duration,
            completed_at=session.completed_at or datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review site results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get review site results"
        )


@router.post("/investment", response_model=ReviewSiteInvestmentResponse)
async def track_review_site_investment(
    request: ReviewSiteInvestmentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Track investment in review sites for ROI analysis
    Based on Reddit intelligence: Review sites are expensive but effective
    """
    try:
        investment_id = f"investment_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        # Store investment tracking
        await db_manager.execute_query(
            """
            INSERT INTO review_site_roi_tracking (id, user_id, brand_name, review_site_name, 
                                                investment_amount, investment_date, investment_type,
                                                expected_roi, status, notes, created_at)
            VALUES (:id, :user_id, :brand_name, :review_site_name, 
                   :investment_amount, :investment_date, :investment_type,
                   :expected_roi, :status, :notes, :created_at)
            """,
            {
                "id": investment_id,
                "user_id": str(current_user.id),
                "brand_name": request.brand_name,
                "review_site_name": request.review_site_name,
                "investment_amount": request.investment_amount,
                "investment_date": datetime.utcnow(),
                "investment_type": request.investment_type,
                "expected_roi": request.expected_roi,
                "status": "active",
                "notes": request.notes,
                "created_at": datetime.utcnow()
            }
        )
        
        logger.info(f"Tracked review site investment {investment_id} for user {current_user.id}")
        
        return ReviewSiteInvestmentResponse(
            investment_id=investment_id,
            brand_name=request.brand_name,
            review_site_name=request.review_site_name,
            investment_amount=request.investment_amount,
            investment_date=datetime.utcnow(),
            status="active",
            message=f"Investment tracking started for {request.brand_name} on {request.review_site_name}"
        )
        
    except Exception as e:
        logger.error(f"Error tracking review site investment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track review site investment"
        )


@router.get("/roi-analysis", response_model=List[Dict[str, Any]])
async def get_review_site_roi_analysis(
    brand_name: Optional[str] = None,
    review_site_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get ROI analysis for review site investments"""
    try:
        # Build query conditions
        conditions = ["user_id = :user_id"]
        params = {"user_id": str(current_user.id)}
        
        if brand_name:
            conditions.append("brand_name = :brand_name")
            params["brand_name"] = brand_name
        
        if review_site_name:
            conditions.append("review_site_name = :review_site_name")
            params["review_site_name"] = review_site_name
        
        where_clause = " AND ".join(conditions)
        
        # Get ROI tracking data
        investments = await db_manager.fetch_all(
            f"""
            SELECT id, brand_name, review_site_name, investment_amount, investment_date,
                   investment_type, expected_roi, actual_roi, mentions_generated,
                   ai_citations_tracked, estimated_traffic_value, payback_period_months,
                   status, notes, created_at
            FROM review_site_roi_tracking
            WHERE {where_clause}
            ORDER BY investment_date DESC
            """,
            params
        )
        
        # Calculate ROI for each investment
        roi_analysis = []
        for investment in investments:
            # Get associated mentions
            mentions = await db_manager.fetch_all(
                """
                SELECT COUNT(*) as mention_count, AVG(rating) as avg_rating,
                       AVG(sentiment_score) as avg_sentiment, SUM(estimated_traffic_value) as total_traffic_value
                FROM review_site_mentions
                WHERE user_id = :user_id AND brand_name = :brand_name AND review_site_name = :review_site_name
                AND discovered_at >= :investment_date
                """,
                {
                    "user_id": str(current_user.id),
                    "brand_name": investment.brand_name,
                    "review_site_name": investment.review_site_name,
                    "investment_date": investment.investment_date
                }
            )
            
            mention_data = mentions[0] if mentions else None
            mention_count = mention_data.mention_count if mention_data else 0
            avg_rating = float(mention_data.avg_rating) if mention_data and mention_data.avg_rating else 0.0
            avg_sentiment = float(mention_data.avg_sentiment) if mention_data and mention_data.avg_sentiment else 0.0
            total_traffic_value = float(mention_data.total_traffic_value) if mention_data and mention_data.total_traffic_value else 0.0
            
            # Calculate ROI
            roi_percentage = 0.0
            if investment.investment_amount > 0:
                roi_percentage = ((total_traffic_value - investment.investment_amount) / investment.investment_amount) * 100
            
            roi_analysis.append({
                "investment_id": investment.id,
                "brand_name": investment.brand_name,
                "review_site_name": investment.review_site_name,
                "investment_amount": float(investment.investment_amount),
                "investment_date": investment.investment_date,
                "investment_type": investment.investment_type,
                "expected_roi": float(investment.expected_roi) if investment.expected_roi else None,
                "actual_roi": roi_percentage,
                "mentions_generated": mention_count,
                "average_rating": avg_rating,
                "average_sentiment": avg_sentiment,
                "estimated_traffic_value": total_traffic_value,
                "payback_period_months": float(investment.payback_period_months) if investment.payback_period_months else None,
                "status": investment.status,
                "notes": investment.notes,
                "created_at": investment.created_at,
                "roi_status": "positive" if roi_percentage > 0 else "negative" if roi_percentage < 0 else "neutral"
            })
        
        return roi_analysis
        
    except Exception as e:
        logger.error(f"Error getting ROI analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ROI analysis"
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_review_site_summary(
    brand_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get summary of review site monitoring"""
    try:
        # Build query conditions
        conditions = ["user_id = :user_id"]
        params = {"user_id": str(current_user.id)}
        
        if brand_name:
            conditions.append("brand_name = :brand_name")
            params["brand_name"] = brand_name
        
        where_clause = " AND ".join(conditions)
        
        # Get mentions summary
        mentions_summary = await db_manager.fetch_all(
            f"""
            SELECT review_site_name, COUNT(*) as mention_count, 
                   AVG(rating) as avg_rating, AVG(sentiment_score) as avg_sentiment,
                   MAX(discovered_at) as latest_mention,
                   SUM(estimated_traffic_value) as total_traffic_value
            FROM review_site_mentions 
            WHERE {where_clause}
            GROUP BY review_site_name
            ORDER BY mention_count DESC
            """,
            params
        )
        
        # Get investment summary
        investment_summary = await db_manager.fetch_all(
            f"""
            SELECT review_site_name, COUNT(*) as investment_count,
                   SUM(investment_amount) as total_investment,
                   AVG(expected_roi) as avg_expected_roi,
                   AVG(actual_roi) as avg_actual_roi
            FROM review_site_roi_tracking
            WHERE {where_clause}
            GROUP BY review_site_name
            ORDER BY total_investment DESC
            """,
            params
        )
        
        # Build summary
        summary = {
            "total_mentions": sum(row.mention_count for row in mentions_summary),
            "sites_covered": len(mentions_summary),
            "total_investment": sum(float(row.total_investment) for row in investment_summary if row.total_investment),
            "total_investments": sum(row.investment_count for row in investment_summary),
            "by_site": {},
            "overall_roi": 0.0,
            "top_performing_sites": [],
            "recommendations": []
        }
        
        # Process mentions by site
        for row in mentions_summary:
            summary["by_site"][row.review_site_name] = {
                "mention_count": row.mention_count,
                "avg_rating": float(row.avg_rating) if row.avg_rating else None,
                "avg_sentiment": float(row.avg_sentiment) if row.avg_sentiment else None,
                "latest_mention": row.latest_mention,
                "total_traffic_value": float(row.total_traffic_value) if row.total_traffic_value else 0.0
            }
        
        # Add investment data
        for row in investment_summary:
            if row.review_site_name in summary["by_site"]:
                summary["by_site"][row.review_site_name].update({
                    "investment_count": row.investment_count,
                    "total_investment": float(row.total_investment) if row.total_investment else 0.0,
                    "avg_expected_roi": float(row.avg_expected_roi) if row.avg_expected_roi else None,
                    "avg_actual_roi": float(row.avg_actual_roi) if row.avg_actual_roi else None
                })
        
        # Calculate overall ROI
        total_investment = summary["total_investment"]
        total_traffic_value = sum(
            site_data.get("total_traffic_value", 0) 
            for site_data in summary["by_site"].values()
        )
        
        if total_investment > 0:
            summary["overall_roi"] = ((total_traffic_value - total_investment) / total_investment) * 100
        
        # Identify top performing sites
        for site_name, site_data in summary["by_site"].items():
            if site_data.get("avg_actual_roi") and site_data["avg_actual_roi"] > 0:
                summary["top_performing_sites"].append({
                    "site_name": site_name,
                    "roi": site_data["avg_actual_roi"],
                    "mentions": site_data["mention_count"]
                })
        
        summary["top_performing_sites"].sort(key=lambda x: x["roi"], reverse=True)
        summary["top_performing_sites"] = summary["top_performing_sites"][:3]
        
        # Generate recommendations
        if summary["total_mentions"] == 0:
            summary["recommendations"].append("No review site presence detected - consider investing in G2 or Capterra")
        elif summary["overall_roi"] > 50:
            summary["recommendations"].append(f"Excellent ROI ({summary['overall_roi']:.1f}%) - consider expanding review site investments")
        elif summary["overall_roi"] > 0:
            summary["recommendations"].append(f"Positive ROI ({summary['overall_roi']:.1f}%) - optimize existing investments")
        else:
            summary["recommendations"].append("Negative ROI - reevaluate review site strategy")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting review site summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get review site summary"
        )


async def run_review_site_monitoring_task(
    session_id: str,
    user_id: str,
    brand_names: List[str],
    category: str,
    priority_sites: List[ReviewSiteType],
    include_roi_analysis: bool,
    deep_analysis: bool
):
    """Background task to run review site monitoring"""
    try:
        logger.info(f"Starting review site monitoring task {session_id}")
        
        # Update status
        await update_monitoring_status(session_id, "running", 10, "Initializing review site monitoring...")
        
        results = {
            "total_mentions": 0,
            "review_sites_covered": [],
            "mentions_by_site": {},
            "average_rating": 0.0,
            "sentiment_analysis": {},
            "roi_analysis": {},
            "recommendations": [],
            "monitoring_metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "brands": brand_names,
                "category": category,
                "started_at": datetime.utcnow().isoformat()
            }
        }
        
        # Run review site monitoring
        async with review_site_service as service:
            all_ratings = []
            
            for brand_name in brand_names:
                await update_monitoring_status(session_id, "running", 30, f"Monitoring {brand_name} across review sites...")
                
                try:
                    monitoring_result = await service.monitor_brand_across_review_sites(
                        brand_name=brand_name,
                        category=category,
                        priority_sites=priority_sites,
                        include_roi_analysis=include_roi_analysis
                    )
                    
                    # Store results
                    results["total_mentions"] += monitoring_result.total_mentions
                    results["review_sites_covered"] = monitoring_result.review_sites_covered
                    
                    # Convert mentions to serializable format
                    mentions_dict = {}
                    for site_name, mentions in monitoring_result.mentions_by_site.items():
                        mentions_dict[site_name] = [
                            {
                                "url": mention.url,
                                "title": mention.title,
                                "content": mention.content,
                                "rating": mention.rating,
                                "sentiment_score": mention.sentiment_score,
                                "discovered_at": mention.discovered_at.isoformat(),
                                "mention_type": mention.mention_type
                            }
                            for mention in mentions
                        ]
                    
                    results["mentions_by_site"][brand_name] = mentions_dict
                    
                    # Collect ratings
                    if monitoring_result.average_rating > 0:
                        all_ratings.append(monitoring_result.average_rating)
                    
                    # Store sentiment analysis
                    results["sentiment_analysis"][brand_name] = monitoring_result.sentiment_analysis
                    
                    # Store ROI analysis
                    if monitoring_result.roi_metrics:
                        results["roi_analysis"][brand_name] = monitoring_result.roi_metrics
                    
                    # Store recommendations
                    results["recommendations"].extend(monitoring_result.recommendations)
                    
                    # Store mentions in database
                    await service.store_review_site_mentions(user_id, monitoring_result)
                    
                    logger.info(f"Completed review site monitoring for {brand_name}: {monitoring_result.total_mentions} mentions")
                    
                except Exception as e:
                    logger.error(f"Error monitoring {brand_name}: {e}")
                    results["mentions_by_site"][brand_name] = {}
        
        # Calculate overall average rating
        results["average_rating"] = sum(all_ratings) / len(all_ratings) if all_ratings else 0.0
        
        # Update status to completed
        await update_monitoring_status(session_id, "completed", 100, "Review site monitoring completed!")
        
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
        
        logger.info(f"Review site monitoring task {session_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in review site monitoring task {session_id}: {e}")
        
        # Update status to failed
        await update_monitoring_status(session_id, "failed", 0, f"Review site monitoring failed: {str(e)}")


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