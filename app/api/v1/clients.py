from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse, ClientStats,
    ClientBrandAssignment, ClientBrandResponse, ClientDashboardData
)
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.services.client_service import client_service
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


@router.post("/", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(require_agency_user)
):
    """Create a new client"""
    try:
        client = await client_service.create_client(str(current_user.id), client_data)
        return client
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create client"
        )


@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    status: Optional[str] = Query(None, description="Filter by client status"),
    current_user: User = Depends(require_agency_user)
):
    """List all clients for the current agency user"""
    try:
        clients = await client_service.list_clients(str(current_user.id), status)
        return clients
    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list clients"
        )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get a specific client"""
    try:
        client = await client_service.get_client(str(current_user.id), client_id)
        return client
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get client"
        )


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    current_user: User = Depends(require_agency_user)
):
    """Update a client"""
    try:
        client = await client_service.update_client(str(current_user.id), client_id, client_data)
        return client
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update client"
        )


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Delete a client (soft delete)"""
    try:
        success = await client_service.delete_client(str(current_user.id), client_id)
        if success:
            return {"message": "Client deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
    except Exception as e:
        logger.error(f"Error deleting client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete client"
        )


@router.get("/{client_id}/stats", response_model=ClientStats)
async def get_client_stats(
    client_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get client statistics"""
    try:
        stats = await client_service.get_client_stats(str(current_user.id), client_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting client stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get client statistics"
        )


@router.post("/{client_id}/brands", response_model=ClientBrandResponse)
async def assign_brand_to_client(
    client_id: str,
    brand_assignment: ClientBrandAssignment,
    current_user: User = Depends(require_agency_user)
):
    """Assign a brand to a client"""
    try:
        # Ensure client_id matches the one in the assignment
        brand_assignment.client_id = client_id
        
        assignment = await client_service.assign_brand_to_client(
            str(current_user.id), brand_assignment
        )
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning brand to client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign brand to client"
        )


@router.get("/{client_id}/brands", response_model=List[ClientBrandResponse])
async def get_client_brands(
    client_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get all brands assigned to a client"""
    try:
        brands = await client_service.get_client_brands(str(current_user.id), client_id)
        return brands
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting client brands: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get client brands"
        )


@router.delete("/{client_id}/brands/{brand_id}")
async def remove_brand_from_client(
    client_id: str,
    brand_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Remove a brand from a client"""
    try:
        success = await client_service.remove_brand_from_client(
            str(current_user.id), client_id, brand_id
        )
        if success:
            return {"message": "Brand removed from client successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand assignment not found"
            )
    except Exception as e:
        logger.error(f"Error removing brand from client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove brand from client"
        )


@router.get("/{client_id}/dashboard", response_model=ClientDashboardData)
async def get_client_dashboard(
    client_id: str,
    current_user: User = Depends(require_agency_user)
):
    """Get comprehensive dashboard data for a client"""
    try:
        # Get client info
        client = await client_service.get_client(str(current_user.id), client_id)
        
        # Get client stats
        stats = await client_service.get_client_stats(str(current_user.id), client_id)
        
        # TODO: Get recent mentions, ROI summary, content opportunities
        # For now, return basic data
        dashboard_data = ClientDashboardData(
            client=client,
            stats=stats,
            recent_mentions=[],  # TODO: Implement
            roi_summary={},      # TODO: Implement
            content_opportunities=[]  # TODO: Implement
        )
        
        return dashboard_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting client dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get client dashboard"
        )