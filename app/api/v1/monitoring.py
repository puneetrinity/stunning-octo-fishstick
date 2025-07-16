"""
Monitoring API endpoints
Core feature: Track brand mentions across ChatGPT and Reddit
Based on Reddit intelligence: Primary monitoring functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.openai_service import openai_service
from app.services.reddit_service import reddit_service
from app.database import db_manager
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class MonitoringRequest(BaseModel):
    """Request model for monitoring"""
    brand_names: List[str] = Field(..., min_items=1, max_items=10, description="Brands to monitor")
    category: str = Field(..., description="Industry category (saas, b2b, tech, fintech, martech)")
    competitors: Optional[List[str]] = Field(default=[], description="Competitor brands for comparison")
    include_reddit: bool = Field(default=True, description="Include Reddit monitoring (6% of ChatGPT sources)")
    include_chatgpt: bool = Field(default=True, description="Include ChatGPT monitoring")
    time_range: str = Field(default="week", description="Time range for Reddit monitoring")


class MonitoringResponse(BaseModel):
    """Response model for monitoring results"""
    session_id: str
    user_id: str
    brands_monitored: List[str]
    monitoring_started: datetime
    estimated_completion: datetime
    status: str
    message: str


class MonitoringStatus(BaseModel):
    """Status model for monitoring progress"""
    session_id: str
    status: str  # 'running', 'completed', 'failed'
    progress_percentage: float
    current_task: str
    results_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class MonitoringResults(BaseModel):
    """Complete monitoring results"""
    session_id: str
    brands: List[str]
    chatgpt_results: Optional[Dict[str, Any]] = None
    reddit_results: Optional[Dict[str, Any]] = None
    combined_analytics: Dict[str, Any]
    recommendations: List[str]
    monitoring_duration: float
    total_mentions: int
    completed_at: datetime


@router.post("/start", response_model=MonitoringResponse)
async def start_monitoring(
    request: MonitoringRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Start brand monitoring across ChatGPT and Reddit
    Based on Reddit intelligence: Core monitoring functionality
    """
    try:
        # Generate session ID
        session_id = f"monitoring_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        # Validate request
        if not request.brand_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one brand name is required"
            )
        
        if not request.include_chatgpt and not request.include_reddit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one monitoring source must be enabled"
            )
        
        # Store monitoring session
        await db_manager.execute_query(
            """
            INSERT INTO monitoring_sessions (id, user_id, brand_names, category, competitors, 
                                           include_reddit, include_chatgpt, time_range, 
                                           status, created_at)
            VALUES (:id, :user_id, :brand_names, :category, :competitors, 
                    :include_reddit, :include_chatgpt, :time_range, 
                    :status, :created_at)
            """,
            {
                "id": session_id,
                "user_id": str(current_user.id),
                "brand_names": ",".join(request.brand_names),
                "category": request.category,
                "competitors": ",".join(request.competitors) if request.competitors else "",
                "include_reddit": request.include_reddit,
                "include_chatgpt": request.include_chatgpt,
                "time_range": request.time_range,
                "status": "running",
                "created_at": datetime.utcnow()
            }
        )
        
        # Start background monitoring task
        background_tasks.add_task(
            run_monitoring_task,
            session_id,
            str(current_user.id),
            request.brand_names,
            request.category,
            request.competitors,
            request.include_reddit,
            request.include_chatgpt,
            request.time_range
        )
        
        # Estimate completion time
        estimated_duration = 5  # Base duration
        if request.include_chatgpt:
            estimated_duration += len(request.brand_names) * 2  # 2 minutes per brand
        if request.include_reddit:
            estimated_duration += len(request.brand_names) * 3  # 3 minutes per brand
        
        estimated_completion = datetime.utcnow() + timedelta(minutes=estimated_duration)
        
        logger.info(f"Started monitoring session {session_id} for user {current_user.id}")
        
        return MonitoringResponse(
            session_id=session_id,
            user_id=str(current_user.id),
            brands_monitored=request.brand_names,
            monitoring_started=datetime.utcnow(),
            estimated_completion=estimated_completion,
            status="running",
            message=f"Monitoring started for {len(request.brand_names)} brands across {'ChatGPT' if request.include_chatgpt else ''}{',' if request.include_chatgpt and request.include_reddit else ''}{'Reddit' if request.include_reddit else ''}"
        )
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start monitoring"
        )


@router.get("/status/{session_id}", response_model=MonitoringStatus)
async def get_monitoring_status(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get monitoring session status"""
    try:
        session = await db_manager.fetch_one(
            """
            SELECT id, user_id, status, progress_percentage, current_task, 
                   error_message, created_at
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
                detail="Monitoring session not found"
            )
        
        # Get results summary if completed
        results_summary = None
        if session.status == "completed":
            results_summary = await get_monitoring_results_summary(session_id)
        
        return MonitoringStatus(
            session_id=session_id,
            status=session.status,
            progress_percentage=session.progress_percentage or 0.0,
            current_task=session.current_task or "Starting monitoring...",
            results_summary=results_summary,
            error_message=session.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitoring status"
        )


@router.get("/results/{session_id}", response_model=MonitoringResults)
async def get_monitoring_results(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get complete monitoring results"""
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
                detail="Monitoring session not found"
            )
        
        if session.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Monitoring session is not completed. Status: {session.status}"
            )
        
        # Parse results data
        import json
        results_data = json.loads(session.results_data or "{}")
        
        # Calculate monitoring duration
        duration = 0
        if session.completed_at and session.created_at:
            duration = (session.completed_at - session.created_at).total_seconds() / 60
        
        # Generate recommendations based on results
        recommendations = generate_monitoring_recommendations(results_data)
        
        return MonitoringResults(
            session_id=session_id,
            brands=session.brand_names.split(","),
            chatgpt_results=results_data.get("chatgpt_results"),
            reddit_results=results_data.get("reddit_results"),
            combined_analytics=results_data.get("combined_analytics", {}),
            recommendations=recommendations,
            monitoring_duration=duration,
            total_mentions=results_data.get("total_mentions", 0),
            completed_at=session.completed_at or datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monitoring results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitoring results"
        )


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_monitoring_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get monitoring session history"""
    try:
        sessions = await db_manager.fetch_all(
            """
            SELECT id, brand_names, category, status, created_at, completed_at
            FROM monitoring_sessions 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
            """,
            {
                "user_id": str(current_user.id),
                "limit": limit
            }
        )
        
        return [
            {
                "session_id": session.id,
                "brands": session.brand_names.split(","),
                "category": session.category,
                "status": session.status,
                "created_at": session.created_at,
                "completed_at": session.completed_at
            }
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"Error getting monitoring history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitoring history"
        )


async def run_monitoring_task(
    session_id: str,
    user_id: str,
    brand_names: List[str],
    category: str,
    competitors: List[str],
    include_reddit: bool,
    include_chatgpt: bool,
    time_range: str
):
    """
    Background task to run monitoring
    Based on Reddit intelligence: Comprehensive monitoring across sources
    """
    try:
        logger.info(f"Starting monitoring task {session_id}")
        
        # Update status
        await update_monitoring_status(session_id, "running", 10, "Initializing monitoring...")
        
        results = {
            "chatgpt_results": None,
            "reddit_results": None,
            "combined_analytics": {},
            "total_mentions": 0,
            "monitoring_metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "brands": brand_names,
                "category": category,
                "competitors": competitors,
                "started_at": datetime.utcnow().isoformat()
            }
        }
        
        # Run ChatGPT monitoring
        if include_chatgpt:
            await update_monitoring_status(session_id, "running", 30, "Monitoring ChatGPT mentions...")
            
            try:
                chatgpt_results = await openai_service.run_monitoring_session(
                    user_id, brand_names, category, competitors
                )
                results["chatgpt_results"] = chatgpt_results
                results["total_mentions"] += chatgpt_results.get("total_mentions", 0)
                
                logger.info(f"ChatGPT monitoring completed for {session_id}")
                
            except Exception as e:
                logger.error(f"Error in ChatGPT monitoring: {e}")
                results["chatgpt_results"] = {"error": str(e)}
        
        # Run Reddit monitoring
        if include_reddit:
            await update_monitoring_status(session_id, "running", 60, "Monitoring Reddit mentions...")
            
            try:
                reddit_results = {}
                
                for brand_name in brand_names:
                    brand_reddit_results = await reddit_service.monitor_brand_across_subreddits(
                        brand_name, category, time_range
                    )
                    
                    reddit_results[brand_name] = brand_reddit_results
                    results["total_mentions"] += brand_reddit_results.get("total_mentions", 0)
                    
                    # Store Reddit mentions
                    await reddit_service.store_reddit_mentions(user_id, brand_reddit_results)
                
                results["reddit_results"] = reddit_results
                
                logger.info(f"Reddit monitoring completed for {session_id}")
                
            except Exception as e:
                logger.error(f"Error in Reddit monitoring: {e}")
                results["reddit_results"] = {"error": str(e)}
        
        # Generate combined analytics
        await update_monitoring_status(session_id, "running", 90, "Generating analytics...")
        
        combined_analytics = generate_combined_analytics(
            results["chatgpt_results"],
            results["reddit_results"],
            brand_names
        )
        results["combined_analytics"] = combined_analytics
        
        # Store final results
        await update_monitoring_status(session_id, "completed", 100, "Monitoring completed!")
        
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
        
        logger.info(f"Monitoring task {session_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in monitoring task {session_id}: {e}")
        
        # Update status to failed
        await update_monitoring_status(session_id, "failed", 0, f"Monitoring failed: {str(e)}")


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


def generate_combined_analytics(chatgpt_results: Dict, reddit_results: Dict, brand_names: List[str]) -> Dict[str, Any]:
    """Generate combined analytics from ChatGPT and Reddit results"""
    analytics = {
        "summary": {
            "total_chatgpt_mentions": 0,
            "total_reddit_mentions": 0,
            "combined_mentions": 0,
            "brands_with_mentions": 0,
            "reddit_chatgpt_correlation": "Based on Reddit intelligence: 6% of ChatGPT sources are Reddit"
        },
        "brand_breakdown": {},
        "insights": []
    }
    
    try:
        # Process ChatGPT results
        if chatgpt_results and "brand_results" in chatgpt_results:
            for brand, data in chatgpt_results["brand_results"].items():
                analytics["summary"]["total_chatgpt_mentions"] += data.get("total_mentions", 0)
                
                if brand not in analytics["brand_breakdown"]:
                    analytics["brand_breakdown"][brand] = {
                        "chatgpt_mentions": 0,
                        "reddit_mentions": 0,
                        "combined_mentions": 0,
                        "chatgpt_sentiment": 0,
                        "reddit_sentiment": 0
                    }
                
                analytics["brand_breakdown"][brand]["chatgpt_mentions"] = data.get("total_mentions", 0)
                analytics["brand_breakdown"][brand]["chatgpt_sentiment"] = data.get("avg_sentiment", 0)
        
        # Process Reddit results
        if reddit_results:
            for brand, data in reddit_results.items():
                analytics["summary"]["total_reddit_mentions"] += data.get("total_mentions", 0)
                
                if brand not in analytics["brand_breakdown"]:
                    analytics["brand_breakdown"][brand] = {
                        "chatgpt_mentions": 0,
                        "reddit_mentions": 0,
                        "combined_mentions": 0,
                        "chatgpt_sentiment": 0,
                        "reddit_sentiment": 0
                    }
                
                analytics["brand_breakdown"][brand]["reddit_mentions"] = data.get("total_mentions", 0)
                analytics["brand_breakdown"][brand]["reddit_sentiment"] = data.get("sentiment_analysis", {}).get("average_sentiment", 0)
        
        # Calculate combined metrics
        analytics["summary"]["combined_mentions"] = analytics["summary"]["total_chatgpt_mentions"] + analytics["summary"]["total_reddit_mentions"]
        
        for brand, data in analytics["brand_breakdown"].items():
            data["combined_mentions"] = data["chatgpt_mentions"] + data["reddit_mentions"]
            if data["combined_mentions"] > 0:
                analytics["summary"]["brands_with_mentions"] += 1
        
        # Generate insights
        if analytics["summary"]["total_reddit_mentions"] > 0:
            analytics["insights"].append("Reddit mentions detected - important for ChatGPT visibility (6% of sources)")
        
        if analytics["summary"]["total_chatgpt_mentions"] > analytics["summary"]["total_reddit_mentions"]:
            analytics["insights"].append("Higher ChatGPT visibility than Reddit presence")
        
        if analytics["summary"]["combined_mentions"] == 0:
            analytics["insights"].append("No mentions found - consider improving content strategy")
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error generating combined analytics: {e}")
        return analytics


def generate_monitoring_recommendations(results_data: Dict) -> List[str]:
    """Generate recommendations based on monitoring results"""
    recommendations = []
    
    try:
        total_mentions = results_data.get("total_mentions", 0)
        reddit_results = results_data.get("reddit_results", {})
        chatgpt_results = results_data.get("chatgpt_results", {})
        
        # Based on Reddit intelligence
        if total_mentions == 0:
            recommendations.append("Consider building authority through review sites (G2, Capterra) - expensive but effective for AI visibility")
            recommendations.append("Focus on Reddit community building - 6% of ChatGPT sources are Reddit")
            recommendations.append("Create detailed comparison content and FAQs")
        
        if reddit_results:
            reddit_mentions = sum(brand_data.get("total_mentions", 0) for brand_data in reddit_results.values())
            if reddit_mentions > 0:
                recommendations.append("Reddit mentions detected - these directly influence ChatGPT responses")
            else:
                recommendations.append("No Reddit mentions found - consider targeted subreddit engagement")
        
        if chatgpt_results:
            chatgpt_mentions = chatgpt_results.get("total_mentions", 0)
            if chatgpt_mentions > 0:
                recommendations.append("ChatGPT mentions found - track these for ROI measurement")
            else:
                recommendations.append("No ChatGPT mentions - focus on authoritative third-party mentions")
        
        # Add general recommendations based on Reddit intelligence
        recommendations.append("Monitor competitor mentions to identify content gaps")
        recommendations.append("Track review site ROI - these are expensive but effective investments")
        recommendations.append("Build mentions from 'totally unconnected authoritative sources'")
        
        return recommendations[:5]  # Return top 5 recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return ["Contact support for personalized recommendations"]


async def get_monitoring_results_summary(session_id: str) -> Dict[str, Any]:
    """Get summary of monitoring results"""
    try:
        session = await db_manager.fetch_one(
            "SELECT results_data FROM monitoring_sessions WHERE id = :session_id",
            {"session_id": session_id}
        )
        
        if not session or not session.results_data:
            return {}
        
        import json
        results_data = json.loads(session.results_data)
        
        return {
            "total_mentions": results_data.get("total_mentions", 0),
            "chatgpt_mentions": results_data.get("chatgpt_results", {}).get("total_mentions", 0),
            "reddit_mentions": sum(
                brand_data.get("total_mentions", 0) 
                for brand_data in results_data.get("reddit_results", {}).values()
            ),
            "brands_monitored": len(results_data.get("monitoring_metadata", {}).get("brands", [])),
            "monitoring_sources": {
                "chatgpt": results_data.get("chatgpt_results") is not None,
                "reddit": results_data.get("reddit_results") is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting results summary: {e}")
        return {}