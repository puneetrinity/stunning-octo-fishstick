from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.schemas.roi import (
    ROIInvestmentCreate, ROIInvestmentUpdate, ROIInvestmentResponse,
    ROIPerformanceMetricCreate, ROIPerformanceMetricResponse,
    ROICalculationResult, ROIDashboardData, ROIInvestmentWithMetrics
)
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.roi_service import roi_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def require_agency_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is an agency user"""
    if not current_user.is_agency_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available to agency users"
        )
    return current_user


@router.post("/investments", response_model=ROIInvestmentResponse)
async def create_investment(
    investment_data: ROIInvestmentCreate,
    current_user: User = Depends(require_agency_user)
):
    """Create a new ROI investment"""
    try:
        investment = await roi_service.create_investment(str(current_user.id), investment_data)
        return investment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating ROI investment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ROI investment"
        )


@router.get("/investments", response_model=List[ROIInvestmentResponse])
async def list_investments(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    current_user: User = Depends(require_agency_user)
):
    """List ROI investments"""
    try:
        investments = await roi_service.list_investments(str(current_user.id), client_id)
        return investments
    except Exception as e:
        logger.error(f"Error listing ROI investments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list ROI investments"
        )


@router.get("/investments/{investment_id}", response_model=ROIInvestmentResponse)
async def get_investment(
    investment_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get a specific ROI investment"""
    try:
        investment = await roi_service.get_investment(str(current_user.id), investment_id)
        return investment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting ROI investment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ROI investment"
        )


@router.put("/investments/{investment_id}", response_model=ROIInvestmentResponse)
async def update_investment(
    investment_id: str,
    investment_data: ROIInvestmentUpdate,
    current_user: User = Depends(require_agency_user)
):
    """Update an ROI investment"""
    try:
        investment = await roi_service.update_investment(str(current_user.id), investment_id, investment_data)
        return investment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating ROI investment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ROI investment"
        )


@router.post("/investments/{investment_id}/metrics", response_model=ROIPerformanceMetricResponse)
async def add_performance_metric(
    investment_id: str,
    metric_data: ROIPerformanceMetricCreate,
    current_user: User = Depends(require_agency_user)
):
    """Add a performance metric to an investment"""
    try:
        # Ensure investment_id matches
        metric_data.investment_id = investment_id
        
        metric = await roi_service.add_performance_metric(str(current_user.id), metric_data)
        return metric
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding performance metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add performance metric"
        )


@router.get("/investments/{investment_id}/metrics", response_model=List[ROIPerformanceMetricResponse])
async def get_investment_metrics(
    investment_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get all performance metrics for an investment"""
    try:
        metrics = await roi_service.get_investment_metrics(str(current_user.id), investment_id)
        return metrics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting investment metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get investment metrics"
        )


@router.get("/investments/{investment_id}/calculate", response_model=ROICalculationResult)
async def calculate_investment_roi(
    investment_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Calculate ROI for an investment"""
    try:
        roi_result = await roi_service.calculate_roi(str(current_user.id), investment_id)
        return roi_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error calculating ROI: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate ROI"
        )


@router.get("/investments/{investment_id}/full", response_model=ROIInvestmentWithMetrics)
async def get_investment_with_metrics(
    investment_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get investment with all related data"""
    try:
        # Get investment
        investment = await roi_service.get_investment(str(current_user.id), investment_id)
        
        # Get metrics
        metrics = await roi_service.get_investment_metrics(str(current_user.id), investment_id)
        
        # Get ROI calculations
        calculations = await roi_service.calculate_roi(str(current_user.id), investment_id)
        
        # TODO: Get mentions
        mentions = []
        
        return ROIInvestmentWithMetrics(
            investment=investment,
            metrics=metrics,
            calculations=calculations,
            mentions=mentions
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting investment with metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get investment with metrics"
        )


@router.get("/dashboard", response_model=ROIDashboardData)
async def get_roi_dashboard(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    current_user: User = Depends(require_agency_user)
):
    """Get ROI dashboard data"""
    try:
        dashboard = await roi_service.get_roi_dashboard(str(current_user.id), client_id)
        return dashboard
    except Exception as e:
        logger.error(f"Error getting ROI dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get ROI dashboard"
        )


@router.get("/metrics/{metric_id}", response_model=ROIPerformanceMetricResponse)
async def get_performance_metric(
    metric_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get a specific performance metric"""
    try:
        metric = await roi_service.get_performance_metric(str(current_user.id), metric_id)
        return metric
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting performance metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metric"
        )