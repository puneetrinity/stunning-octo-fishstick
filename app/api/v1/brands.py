from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.schemas.brand import (
    BrandCreate, BrandUpdate, BrandResponse, BrandStats,
    BrandBulkCreate, BrandBulkResponse
)
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.brand_service import brand_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=BrandResponse)
async def create_brand(
    brand_data: BrandCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new tracked brand"""
    try:
        brand = await brand_service.create_brand(str(current_user.id), brand_data)
        return brand
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create brand"
        )


@router.get("/", response_model=List[BrandResponse])
async def list_brands(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user)
):
    """List all brands for the current user"""
    try:
        brands = await brand_service.list_brands(str(current_user.id), is_active)
        return brands
    except Exception as e:
        logger.error(f"Error listing brands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list brands"
        )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific brand"""
    try:
        brand = await brand_service.get_brand(str(current_user.id), brand_id)
        return brand
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand"
        )


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: str,
    brand_data: BrandUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a brand"""
    try:
        brand = await brand_service.update_brand(str(current_user.id), brand_id, brand_data)
        return brand
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update brand"
        )


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a brand (soft delete)"""
    try:
        success = await brand_service.delete_brand(str(current_user.id), brand_id)
        if success:
            return {"message": "Brand deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
    except Exception as e:
        logger.error(f"Error deleting brand: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete brand"
        )


@router.get("/{brand_id}/stats", response_model=BrandStats)
async def get_brand_stats(
    brand_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get brand statistics"""
    try:
        stats = await brand_service.get_brand_stats(str(current_user.id), brand_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting brand stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand statistics"
        )


@router.post("/bulk", response_model=BrandBulkResponse)
async def bulk_create_brands(
    bulk_data: BrandBulkCreate,
    current_user: User = Depends(get_current_user)
):
    """Create multiple brands at once"""
    try:
        result = await brand_service.bulk_create_brands(str(current_user.id), bulk_data)
        return result
    except Exception as e:
        logger.error(f"Error bulk creating brands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create brands"
        )


@router.get("/{brand_id}/competitors")
async def get_brand_competitors(
    brand_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get competitor analysis for a brand"""
    try:
        competitors = await brand_service.get_brand_competitors(str(current_user.id), brand_id)
        return {"competitors": competitors}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting brand competitors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get brand competitors"
        )