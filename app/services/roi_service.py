from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from app.database import db_manager
from app.schemas.roi import (
    ROIInvestmentCreate, ROIInvestmentUpdate, ROIInvestmentResponse,
    ROIPerformanceMetricCreate, ROIPerformanceMetricResponse,
    ROICalculationResult, ROIDashboardData, ROIReportData,
    ReviewSiteResponse, ReviewMentionResponse, ROIInvestmentWithMetrics
)
from app.services.client_service import client_service
from app.models.user import User
import uuid
import logging

logger = logging.getLogger(__name__)


class ROIService:
    """Service for managing ROI tracking and calculations"""
    
    def __init__(self):
        self.client_service = client_service
    
    async def create_investment(self, user_id: str, investment_data: ROIInvestmentCreate) -> ROIInvestmentResponse:
        """Create a new ROI investment"""
        try:
            # Verify client belongs to user
            await self.client_service.get_client(user_id, investment_data.client_id)
            
            # Create investment
            investment_id = str(uuid.uuid4())
            query = """
                INSERT INTO roi_investments (
                    id, client_id, user_id, investment_type, platform, 
                    investment_amount, currency, investment_date, description,
                    expected_roi, notes, status
                ) VALUES (
                    :id, :client_id, :user_id, :investment_type, :platform,
                    :investment_amount, :currency, :investment_date, :description,
                    :expected_roi, :notes, :status
                ) RETURNING id
            """
            
            await db_manager.execute_query(query, {
                "id": investment_id,
                "client_id": investment_data.client_id,
                "user_id": user_id,
                "investment_type": investment_data.investment_type.value,
                "platform": investment_data.platform,
                "investment_amount": investment_data.investment_amount,
                "currency": investment_data.currency,
                "investment_date": investment_data.investment_date,
                "description": investment_data.description,
                "expected_roi": investment_data.expected_roi,
                "notes": investment_data.notes,
                "status": "active"
            })
            
            # Get created investment
            investment = await self.get_investment(user_id, investment_id)
            
            logger.info(f"ROI investment created: {investment_id} for user: {user_id}")
            return investment
            
        except Exception as e:
            logger.error(f"Error creating ROI investment: {e}")
            raise
    
    async def get_investment(self, user_id: str, investment_id: str) -> ROIInvestmentResponse:
        """Get a specific ROI investment"""
        try:
            query = """
                SELECT ri.id, ri.client_id, ri.investment_type, ri.platform,
                       ri.investment_amount, ri.currency, ri.investment_date,
                       ri.description, ri.expected_roi, ri.actual_roi,
                       ri.status, ri.notes, ri.created_at, ri.updated_at
                FROM roi_investments ri
                WHERE ri.id = :investment_id AND ri.user_id = :user_id
            """
            
            investment_data = await db_manager.fetch_one(query, {
                "investment_id": investment_id,
                "user_id": user_id
            })
            
            if not investment_data:
                raise ValueError("Investment not found")
            
            return ROIInvestmentResponse(**dict(investment_data))
            
        except Exception as e:
            logger.error(f"Error getting ROI investment: {e}")
            raise
    
    async def list_investments(self, user_id: str, client_id: Optional[str] = None) -> List[ROIInvestmentResponse]:
        """List ROI investments for a user or specific client"""
        try:
            query = """
                SELECT ri.id, ri.client_id, ri.investment_type, ri.platform,
                       ri.investment_amount, ri.currency, ri.investment_date,
                       ri.description, ri.expected_roi, ri.actual_roi,
                       ri.status, ri.notes, ri.created_at, ri.updated_at
                FROM roi_investments ri
                WHERE ri.user_id = :user_id
            """
            
            params = {"user_id": user_id}
            
            if client_id:
                query += " AND ri.client_id = :client_id"
                params["client_id"] = client_id
            
            query += " ORDER BY ri.created_at DESC"
            
            investments_data = await db_manager.fetch_all(query, params)
            
            return [ROIInvestmentResponse(**dict(inv)) for inv in investments_data]
            
        except Exception as e:
            logger.error(f"Error listing ROI investments: {e}")
            raise
    
    async def update_investment(self, user_id: str, investment_id: str, investment_data: ROIInvestmentUpdate) -> ROIInvestmentResponse:
        """Update an ROI investment"""
        try:
            # Build update query dynamically
            updates = []
            params = {"investment_id": investment_id, "user_id": user_id}
            
            if investment_data.investment_type is not None:
                updates.append("investment_type = :investment_type")
                params["investment_type"] = investment_data.investment_type.value
            
            if investment_data.platform is not None:
                updates.append("platform = :platform")
                params["platform"] = investment_data.platform
            
            if investment_data.investment_amount is not None:
                updates.append("investment_amount = :investment_amount")
                params["investment_amount"] = investment_data.investment_amount
            
            if investment_data.investment_date is not None:
                updates.append("investment_date = :investment_date")
                params["investment_date"] = investment_data.investment_date
            
            if investment_data.description is not None:
                updates.append("description = :description")
                params["description"] = investment_data.description
            
            if investment_data.expected_roi is not None:
                updates.append("expected_roi = :expected_roi")
                params["expected_roi"] = investment_data.expected_roi
            
            if investment_data.actual_roi is not None:
                updates.append("actual_roi = :actual_roi")
                params["actual_roi"] = investment_data.actual_roi
            
            if investment_data.status is not None:
                updates.append("status = :status")
                params["status"] = investment_data.status.value
            
            if investment_data.notes is not None:
                updates.append("notes = :notes")
                params["notes"] = investment_data.notes
            
            if updates:
                updates.append("updated_at = :updated_at")
                params["updated_at"] = datetime.utcnow()
                
                query = f"""
                    UPDATE roi_investments 
                    SET {', '.join(updates)} 
                    WHERE id = :investment_id AND user_id = :user_id
                """
                
                await db_manager.execute_query(query, params)
            
            # Return updated investment
            return await self.get_investment(user_id, investment_id)
            
        except Exception as e:
            logger.error(f"Error updating ROI investment: {e}")
            raise
    
    async def add_performance_metric(self, user_id: str, metric_data: ROIPerformanceMetricCreate) -> ROIPerformanceMetricResponse:
        """Add a performance metric to an investment"""
        try:
            # Verify investment belongs to user
            await self.get_investment(user_id, metric_data.investment_id)
            
            # Create performance metric
            metric_id = str(uuid.uuid4())
            query = """
                INSERT INTO roi_performance_metrics (
                    id, investment_id, metric_date, mentions_generated,
                    ai_citations, estimated_traffic, estimated_traffic_value,
                    brand_visibility_score, sentiment_score, notes
                ) VALUES (
                    :id, :investment_id, :metric_date, :mentions_generated,
                    :ai_citations, :estimated_traffic, :estimated_traffic_value,
                    :brand_visibility_score, :sentiment_score, :notes
                ) RETURNING id
            """
            
            await db_manager.execute_query(query, {
                "id": metric_id,
                "investment_id": metric_data.investment_id,
                "metric_date": metric_data.metric_date,
                "mentions_generated": metric_data.mentions_generated,
                "ai_citations": metric_data.ai_citations,
                "estimated_traffic": metric_data.estimated_traffic,
                "estimated_traffic_value": metric_data.estimated_traffic_value,
                "brand_visibility_score": metric_data.brand_visibility_score,
                "sentiment_score": metric_data.sentiment_score,
                "notes": metric_data.notes
            })
            
            # Get created metric
            metric = await self.get_performance_metric(user_id, metric_id)
            
            # Update investment's actual ROI
            await self._update_investment_roi(user_id, metric_data.investment_id)
            
            logger.info(f"Performance metric added: {metric_id} for investment: {metric_data.investment_id}")
            return metric
            
        except Exception as e:
            logger.error(f"Error adding performance metric: {e}")
            raise
    
    async def get_performance_metric(self, user_id: str, metric_id: str) -> ROIPerformanceMetricResponse:
        """Get a specific performance metric"""
        try:
            query = """
                SELECT rpm.id, rpm.investment_id, rpm.metric_date,
                       rpm.mentions_generated, rpm.ai_citations, rpm.estimated_traffic,
                       rpm.estimated_traffic_value, rpm.brand_visibility_score,
                       rpm.sentiment_score, rpm.notes, rpm.created_at
                FROM roi_performance_metrics rpm
                JOIN roi_investments ri ON rpm.investment_id = ri.id
                WHERE rpm.id = :metric_id AND ri.user_id = :user_id
            """
            
            metric_data = await db_manager.fetch_one(query, {
                "metric_id": metric_id,
                "user_id": user_id
            })
            
            if not metric_data:
                raise ValueError("Performance metric not found")
            
            return ROIPerformanceMetricResponse(**dict(metric_data))
            
        except Exception as e:
            logger.error(f"Error getting performance metric: {e}")
            raise
    
    async def get_investment_metrics(self, user_id: str, investment_id: str) -> List[ROIPerformanceMetricResponse]:
        """Get all performance metrics for an investment"""
        try:
            query = """
                SELECT rpm.id, rpm.investment_id, rpm.metric_date,
                       rpm.mentions_generated, rpm.ai_citations, rpm.estimated_traffic,
                       rpm.estimated_traffic_value, rpm.brand_visibility_score,
                       rpm.sentiment_score, rpm.notes, rpm.created_at
                FROM roi_performance_metrics rpm
                JOIN roi_investments ri ON rpm.investment_id = ri.id
                WHERE rpm.investment_id = :investment_id AND ri.user_id = :user_id
                ORDER BY rpm.metric_date DESC
            """
            
            metrics_data = await db_manager.fetch_all(query, {
                "investment_id": investment_id,
                "user_id": user_id
            })
            
            return [ROIPerformanceMetricResponse(**dict(metric)) for metric in metrics_data]
            
        except Exception as e:
            logger.error(f"Error getting investment metrics: {e}")
            raise
    
    async def calculate_roi(self, user_id: str, investment_id: str) -> ROICalculationResult:
        """Calculate ROI for an investment"""
        try:
            # Get investment
            investment = await self.get_investment(user_id, investment_id)
            
            # Get performance metrics
            metrics = await self.get_investment_metrics(user_id, investment_id)
            
            # Calculate total value generated
            total_value = sum(float(metric.estimated_traffic_value) for metric in metrics)
            
            # Calculate ROI
            investment_amount = float(investment.investment_amount)
            roi_absolute = total_value - investment_amount
            roi_percentage = (roi_absolute / investment_amount) * 100 if investment_amount > 0 else 0
            
            # Calculate payback period
            payback_period_days = None
            break_even_date = None
            
            if metrics:
                cumulative_value = 0
                for metric in sorted(metrics, key=lambda x: x.metric_date):
                    cumulative_value += float(metric.estimated_traffic_value)
                    if cumulative_value >= investment_amount:
                        days_diff = (metric.metric_date - investment.investment_date).days
                        payback_period_days = days_diff
                        break_even_date = metric.metric_date
                        break
            
            # Determine performance trend
            if len(metrics) >= 2:
                recent_metrics = sorted(metrics, key=lambda x: x.metric_date, reverse=True)[:2]
                if recent_metrics[0].estimated_traffic_value > recent_metrics[1].estimated_traffic_value:
                    trend = "improving"
                elif recent_metrics[0].estimated_traffic_value < recent_metrics[1].estimated_traffic_value:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            return ROICalculationResult(
                investment_id=investment_id,
                total_investment=investment.investment_amount,
                current_value=Decimal(str(total_value)),
                roi_percentage=Decimal(str(roi_percentage)),
                roi_absolute=Decimal(str(roi_absolute)),
                payback_period_days=payback_period_days,
                break_even_date=break_even_date,
                performance_trend=trend
            )
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            raise
    
    async def get_roi_dashboard(self, user_id: str, client_id: Optional[str] = None) -> ROIDashboardData:
        """Get ROI dashboard data"""
        try:
            # Get investments
            investments = await self.list_investments(user_id, client_id)
            
            if not investments:
                return ROIDashboardData(
                    client_id=client_id or "",
                    total_investments=0,
                    total_invested=Decimal("0"),
                    current_value=Decimal("0"),
                    overall_roi=Decimal("0"),
                    active_investments=0,
                    top_performing_platform=None,
                    monthly_trend=[],
                    investment_breakdown=[]
                )
            
            # Calculate aggregated metrics
            total_invested = sum(inv.investment_amount for inv in investments)
            active_investments = len([inv for inv in investments if inv.status == "active"])
            
            # Get all performance metrics
            total_value = Decimal("0")
            platform_performance = {}
            
            for investment in investments:
                metrics = await self.get_investment_metrics(user_id, investment.id)
                investment_value = sum(float(metric.estimated_traffic_value) for metric in metrics)
                total_value += Decimal(str(investment_value))
                
                # Track platform performance
                if investment.platform not in platform_performance:
                    platform_performance[investment.platform] = {
                        'invested': Decimal("0"),
                        'value': Decimal("0")
                    }
                
                platform_performance[investment.platform]['invested'] += investment.investment_amount
                platform_performance[investment.platform]['value'] += Decimal(str(investment_value))
            
            # Calculate overall ROI
            overall_roi = ((total_value - total_invested) / total_invested) * 100 if total_invested > 0 else Decimal("0")
            
            # Find top performing platform
            top_platform = None
            best_roi = Decimal("-100")
            
            for platform, perf in platform_performance.items():
                if perf['invested'] > 0:
                    platform_roi = ((perf['value'] - perf['invested']) / perf['invested']) * 100
                    if platform_roi > best_roi:
                        best_roi = platform_roi
                        top_platform = platform
            
            # TODO: Generate monthly trend and investment breakdown
            monthly_trend = []
            investment_breakdown = []
            
            return ROIDashboardData(
                client_id=client_id or "",
                total_investments=len(investments),
                total_invested=total_invested,
                current_value=total_value,
                overall_roi=overall_roi,
                active_investments=active_investments,
                top_performing_platform=top_platform,
                monthly_trend=monthly_trend,
                investment_breakdown=investment_breakdown
            )
            
        except Exception as e:
            logger.error(f"Error getting ROI dashboard: {e}")
            raise
    
    async def _update_investment_roi(self, user_id: str, investment_id: str) -> None:
        """Update investment's actual ROI based on performance metrics"""
        try:
            roi_calc = await self.calculate_roi(user_id, investment_id)
            
            query = """
                UPDATE roi_investments 
                SET actual_roi = :actual_roi, updated_at = :updated_at
                WHERE id = :investment_id AND user_id = :user_id
            """
            
            await db_manager.execute_query(query, {
                "actual_roi": roi_calc.roi_percentage,
                "updated_at": datetime.utcnow(),
                "investment_id": investment_id,
                "user_id": user_id
            })
            
        except Exception as e:
            logger.error(f"Error updating investment ROI: {e}")
            # Don't raise here as this is a background update


# Global service instance
roi_service = ROIService()