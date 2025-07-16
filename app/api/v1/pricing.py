from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.auth import (
    PricingResponse, PlanInfo, PlanChangeRequest, UserWithPlanInfo
)
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.config.pricing import PricingConfig
from app.database import db_manager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=PricingResponse)
async def get_pricing():
    """Get all pricing plans"""
    try:
        pricing_config = PricingConfig()
        
        # Get brand plans
        brand_plans = []
        for plan_type, config in pricing_config.get_brand_plans().items():
            brand_plans.append(PlanInfo(
                plan_type=plan_type,
                name=config['target_market'],
                price_usd=config['price_usd'],
                target_market=config['target_market'],
                description=config['description'],
                limits=config['limits'],
                features=config['features']
            ))
        
        # Get agency plans
        agency_plans = []
        for plan_type, config in pricing_config.get_agency_plans().items():
            agency_plans.append(PlanInfo(
                plan_type=plan_type,
                name=config['target_market'],
                price_usd=config['price_usd'],
                target_market=config['target_market'],
                description=config['description'],
                limits=config['limits'],
                features=config['features']
            ))
        
        return PricingResponse(
            brand_plans=brand_plans,
            agency_plans=agency_plans
        )
    except Exception as e:
        logger.error(f"Error getting pricing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pricing information"
        )


@router.get("/plan/{plan_type}", response_model=PlanInfo)
async def get_plan_info(plan_type: str):
    """Get information about a specific plan"""
    try:
        pricing_config = PricingConfig()
        config = pricing_config.get_plan_config(plan_type)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        return PlanInfo(
            plan_type=plan_type,
            name=config['target_market'],
            price_usd=config['price_usd'],
            target_market=config['target_market'],
            description=config['description'],
            limits=config['limits'],
            features=config['features']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get plan information"
        )


@router.get("/my-plan", response_model=UserWithPlanInfo)
async def get_my_plan(current_user: User = Depends(get_current_user)):
    """Get current user's plan information with usage stats"""
    try:
        pricing_config = PricingConfig()
        
        # Get plan info
        plan_config = pricing_config.get_plan_config(current_user.plan_type.value)
        
        if not plan_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan configuration not found"
            )
        
        plan_info = PlanInfo(
            plan_type=current_user.plan_type.value,
            name=plan_config['target_market'],
            price_usd=plan_config['price_usd'],
            target_market=plan_config['target_market'],
            description=plan_config['description'],
            limits=plan_config['limits'],
            features=plan_config['features']
        )
        
        # Get usage stats
        usage_stats = await _get_user_usage_stats(str(current_user.id))
        
        return UserWithPlanInfo(
            user=current_user,
            plan_info=plan_info,
            usage_stats=usage_stats
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user plan info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get plan information"
        )


@router.post("/change-plan", response_model=UserWithPlanInfo)
async def change_plan(
    plan_change: PlanChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """Change user's plan"""
    try:
        pricing_config = PricingConfig()
        
        # Validate new plan
        new_plan_config = pricing_config.get_plan_config(plan_change.new_plan_type.value)
        if not new_plan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan type"
            )
        
        # Check if user can change to this plan
        current_type = 'brand' if current_user.plan_type.value.startswith('brand_') else 'agency'
        new_type = 'brand' if plan_change.new_plan_type.value.startswith('brand_') else 'agency'
        
        if current_type != new_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change between brand and agency plan types"
            )
        
        # Update user's plan
        query = """
            UPDATE users 
            SET plan_type = :new_plan_type, updated_at = :updated_at
            WHERE id = :user_id
        """
        
        await db_manager.execute_query(query, {
            "new_plan_type": plan_change.new_plan_type.value,
            "updated_at": datetime.utcnow(),
            "user_id": current_user.id
        })
        
        # Get updated user
        updated_user_query = """
            SELECT id, email, full_name, company_name, user_type, plan_type,
                   is_active, is_verified, created_at, last_login
            FROM users WHERE id = :user_id
        """
        
        updated_user_data = await db_manager.fetch_one(updated_user_query, {
            "user_id": current_user.id
        })
        
        updated_user = User(**dict(updated_user_data))
        
        # Get new plan info
        plan_info = PlanInfo(
            plan_type=plan_change.new_plan_type.value,
            name=new_plan_config['target_market'],
            price_usd=new_plan_config['price_usd'],
            target_market=new_plan_config['target_market'],
            description=new_plan_config['description'],
            limits=new_plan_config['limits'],
            features=new_plan_config['features']
        )
        
        # Get usage stats
        usage_stats = await _get_user_usage_stats(str(current_user.id))
        
        logger.info(f"User {current_user.id} changed plan to {plan_change.new_plan_type.value}")
        
        return UserWithPlanInfo(
            user=updated_user,
            plan_info=plan_info,
            usage_stats=usage_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change plan"
        )


@router.get("/compare")
async def compare_plans(
    current_plan: str,
    target_plan: str
):
    """Compare two plans"""
    try:
        pricing_config = PricingConfig()
        
        current_config = pricing_config.get_plan_config(current_plan)
        target_config = pricing_config.get_plan_config(target_plan)
        
        if not current_config or not target_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both plans not found"
            )
        
        # Calculate differences
        price_difference = target_config['price_usd'] - current_config['price_usd']
        
        # Feature differences
        current_features = set(current_config['features'])
        target_features = set(target_config['features'])
        
        added_features = list(target_features - current_features)
        removed_features = list(current_features - target_features)
        
        # Limit differences
        limit_differences = {}
        for limit_type in target_config['limits']:
            current_limit = current_config['limits'].get(limit_type, 0)
            target_limit = target_config['limits'].get(limit_type, 0)
            if current_limit != target_limit:
                limit_differences[limit_type] = {
                    'current': current_limit,
                    'target': target_limit,
                    'difference': target_limit - current_limit if isinstance(target_limit, int) else None
                }
        
        return {
            'current_plan': current_plan,
            'target_plan': target_plan,
            'price_difference': price_difference,
            'added_features': added_features,
            'removed_features': removed_features,
            'limit_differences': limit_differences,
            'can_upgrade': pricing_config.can_upgrade_to(current_plan, target_plan)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare plans"
        )


async def _get_user_usage_stats(user_id: str) -> dict:
    """Get current usage statistics for a user"""
    try:
        # Get current month usage
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        stats_query = """
            SELECT 
                COUNT(DISTINCT tb.id) as brands_tracked,
                COUNT(DISTINCT qr.id) as queries_executed,
                COUNT(DISTINCT c.id) as clients_managed,
                COUNT(DISTINCT ri.id) as roi_investments
            FROM users u
            LEFT JOIN tracked_brands tb ON u.id = tb.user_id AND tb.is_active = true
            LEFT JOIN query_results qr ON u.id = qr.user_id AND qr.executed_at >= :thirty_days_ago
            LEFT JOIN clients c ON u.id = c.user_id AND c.status = 'active'
            LEFT JOIN roi_investments ri ON u.id = ri.user_id AND ri.status = 'active'
            WHERE u.id = :user_id
            GROUP BY u.id
        """
        
        stats_data = await db_manager.fetch_one(stats_query, {
            "user_id": user_id,
            "thirty_days_ago": thirty_days_ago
        })
        
        if not stats_data:
            return {
                'brands_tracked': 0,
                'queries_executed': 0,
                'clients_managed': 0,
                'roi_investments': 0
            }
        
        return {
            'brands_tracked': stats_data.brands_tracked or 0,
            'queries_executed': stats_data.queries_executed or 0,
            'clients_managed': stats_data.clients_managed or 0,
            'roi_investments': stats_data.roi_investments or 0
        }
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return {
            'brands_tracked': 0,
            'queries_executed': 0,
            'clients_managed': 0,
            'roi_investments': 0
        }