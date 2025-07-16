from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database import db_manager
from app.schemas.client import (
    ClientCreate, ClientUpdate, ClientResponse, ClientStats,
    ClientBrandAssignment, ClientBrandResponse, ClientDashboardData
)
from app.models.user import User, UserType
from app.models.client import Client, ClientBrand, ClientStatus
from app.config.pricing import PricingConfig
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class ClientService:
    """Service for managing agency clients"""
    
    def __init__(self):
        self.pricing_config = PricingConfig()
    
    async def create_client(self, user_id: str, client_data: ClientCreate) -> ClientResponse:
        """Create a new client for an agency user"""
        try:
            # Verify user is agency type
            user = await self._get_user(user_id)
            if not user.is_agency_user:
                raise ValueError("Only agency users can create clients")
            
            # Check client limits
            await self._check_client_limits(user_id, user.plan_type.value)
            
            # Create client
            client_id = str(uuid.uuid4())
            query = """
                INSERT INTO clients (
                    id, user_id, name, company_name, website_url, industry, 
                    description, contact_email, contact_name, monthly_budget,
                    status, onboarding_completed
                ) VALUES (
                    :id, :user_id, :name, :company_name, :website_url, :industry,
                    :description, :contact_email, :contact_name, :monthly_budget,
                    :status, :onboarding_completed
                ) RETURNING id
            """
            
            await db_manager.execute_query(query, {
                "id": client_id,
                "user_id": user_id,
                "name": client_data.name,
                "company_name": client_data.company_name,
                "website_url": client_data.website_url,
                "industry": client_data.industry,
                "description": client_data.description,
                "contact_email": client_data.contact_email,
                "contact_name": client_data.contact_name,
                "monthly_budget": client_data.monthly_budget,
                "status": "active",
                "onboarding_completed": False
            })
            
            # Get created client
            client = await self.get_client(user_id, client_id)
            
            logger.info(f"Client created: {client_id} for user: {user_id}")
            return client
            
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            raise
    
    async def get_client(self, user_id: str, client_id: str) -> ClientResponse:
        """Get a specific client"""
        try:
            query = """
                SELECT c.id, c.name, c.company_name, c.website_url, c.industry,
                       c.description, c.contact_email, c.contact_name, c.status,
                       c.monthly_budget, c.onboarding_completed, c.created_at, c.updated_at
                FROM clients c
                WHERE c.id = :client_id AND c.user_id = :user_id
            """
            
            client_data = await db_manager.fetch_one(query, {
                "client_id": client_id,
                "user_id": user_id
            })
            
            if not client_data:
                raise ValueError("Client not found")
            
            return ClientResponse(**dict(client_data))
            
        except Exception as e:
            logger.error(f"Error getting client: {e}")
            raise
    
    async def list_clients(self, user_id: str, status: Optional[str] = None) -> List[ClientResponse]:
        """List all clients for an agency user"""
        try:
            query = """
                SELECT c.id, c.name, c.company_name, c.website_url, c.industry,
                       c.description, c.contact_email, c.contact_name, c.status,
                       c.monthly_budget, c.onboarding_completed, c.created_at, c.updated_at
                FROM clients c
                WHERE c.user_id = :user_id
            """
            
            params = {"user_id": user_id}
            
            if status:
                query += " AND c.status = :status"
                params["status"] = status
            
            query += " ORDER BY c.created_at DESC"
            
            clients_data = await db_manager.fetch_all(query, params)
            
            return [ClientResponse(**dict(client)) for client in clients_data]
            
        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            raise
    
    async def update_client(self, user_id: str, client_id: str, client_data: ClientUpdate) -> ClientResponse:
        """Update a client"""
        try:
            # Build update query dynamically
            updates = []
            params = {"client_id": client_id, "user_id": user_id}
            
            if client_data.name is not None:
                updates.append("name = :name")
                params["name"] = client_data.name
            
            if client_data.company_name is not None:
                updates.append("company_name = :company_name")
                params["company_name"] = client_data.company_name
            
            if client_data.website_url is not None:
                updates.append("website_url = :website_url")
                params["website_url"] = client_data.website_url
            
            if client_data.industry is not None:
                updates.append("industry = :industry")
                params["industry"] = client_data.industry
            
            if client_data.description is not None:
                updates.append("description = :description")
                params["description"] = client_data.description
            
            if client_data.contact_email is not None:
                updates.append("contact_email = :contact_email")
                params["contact_email"] = client_data.contact_email
            
            if client_data.contact_name is not None:
                updates.append("contact_name = :contact_name")
                params["contact_name"] = client_data.contact_name
            
            if client_data.status is not None:
                updates.append("status = :status")
                params["status"] = client_data.status.value
            
            if client_data.monthly_budget is not None:
                updates.append("monthly_budget = :monthly_budget")
                params["monthly_budget"] = client_data.monthly_budget
            
            if client_data.onboarding_completed is not None:
                updates.append("onboarding_completed = :onboarding_completed")
                params["onboarding_completed"] = client_data.onboarding_completed
            
            if updates:
                updates.append("updated_at = :updated_at")
                params["updated_at"] = datetime.utcnow()
                
                query = f"""
                    UPDATE clients 
                    SET {', '.join(updates)} 
                    WHERE id = :client_id AND user_id = :user_id
                """
                
                await db_manager.execute_query(query, params)
            
            # Return updated client
            return await self.get_client(user_id, client_id)
            
        except Exception as e:
            logger.error(f"Error updating client: {e}")
            raise
    
    async def delete_client(self, user_id: str, client_id: str) -> bool:
        """Delete a client (soft delete by setting status to inactive)"""
        try:
            query = """
                UPDATE clients 
                SET status = 'inactive', updated_at = :updated_at
                WHERE id = :client_id AND user_id = :user_id
            """
            
            await db_manager.execute_query(query, {
                "client_id": client_id,
                "user_id": user_id,
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Client deleted: {client_id} for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting client: {e}")
            raise
    
    async def get_client_stats(self, user_id: str, client_id: str) -> ClientStats:
        """Get client statistics"""
        try:
            # Get basic client info
            client = await self.get_client(user_id, client_id)
            
            # Get stats from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            stats_query = """
                SELECT 
                    COUNT(DISTINCT tb.id) as brands_tracked,
                    COUNT(DISTINCT c.id) as total_mentions,
                    COUNT(DISTINCT CASE WHEN c.mentioned = true THEN c.id END) as ai_citations,
                    AVG(CASE WHEN c.mentioned = true THEN c.sentiment_score END) as average_sentiment,
                    COUNT(DISTINCT ri.id) as roi_investments,
                    COALESCE(SUM(ri.investment_amount), 0) as total_investment,
                    AVG(ri.actual_roi) as estimated_roi
                FROM clients cl
                LEFT JOIN client_brands cb ON cl.id = cb.client_id
                LEFT JOIN tracked_brands tb ON cb.brand_id = tb.id
                LEFT JOIN citations c ON tb.id = c.brand_id
                LEFT JOIN query_results qr ON c.query_result_id = qr.id
                LEFT JOIN roi_investments ri ON cl.id = ri.client_id
                WHERE cl.id = :client_id 
                AND cl.user_id = :user_id
                AND (qr.executed_at IS NULL OR qr.executed_at >= :thirty_days_ago)
                GROUP BY cl.id
            """
            
            stats_data = await db_manager.fetch_one(stats_query, {
                "client_id": client_id,
                "user_id": user_id,
                "thirty_days_ago": thirty_days_ago
            })
            
            if not stats_data:
                # Return empty stats if no data
                return ClientStats(
                    client_id=client_id,
                    client_name=client.name,
                    brands_tracked=0,
                    total_mentions=0,
                    ai_citations=0,
                    average_sentiment=0.0,
                    roi_investments=0,
                    total_investment=0.0,
                    estimated_roi=0.0,
                    last_updated=datetime.utcnow()
                )
            
            return ClientStats(
                client_id=client_id,
                client_name=client.name,
                brands_tracked=stats_data.brands_tracked or 0,
                total_mentions=stats_data.total_mentions or 0,
                ai_citations=stats_data.ai_citations or 0,
                average_sentiment=float(stats_data.average_sentiment or 0.0),
                roi_investments=stats_data.roi_investments or 0,
                total_investment=float(stats_data.total_investment or 0.0),
                estimated_roi=float(stats_data.estimated_roi or 0.0),
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting client stats: {e}")
            raise
    
    async def assign_brand_to_client(self, user_id: str, assignment: ClientBrandAssignment) -> ClientBrandResponse:
        """Assign a brand to a client"""
        try:
            # Verify client belongs to user
            client = await self.get_client(user_id, assignment.client_id)
            
            # Check if brand belongs to user
            brand_query = """
                SELECT id, name FROM tracked_brands 
                WHERE id = :brand_id AND user_id = :user_id
            """
            
            brand_data = await db_manager.fetch_one(brand_query, {
                "brand_id": assignment.brand_id,
                "user_id": user_id
            })
            
            if not brand_data:
                raise ValueError("Brand not found or doesn't belong to user")
            
            # Check if assignment already exists
            existing_query = """
                SELECT id FROM client_brands 
                WHERE client_id = :client_id AND brand_id = :brand_id
            """
            
            existing = await db_manager.fetch_one(existing_query, {
                "client_id": assignment.client_id,
                "brand_id": assignment.brand_id
            })
            
            if existing:
                raise ValueError("Brand already assigned to this client")
            
            # Create assignment
            assignment_id = str(uuid.uuid4())
            insert_query = """
                INSERT INTO client_brands (id, client_id, brand_id, is_primary)
                VALUES (:id, :client_id, :brand_id, :is_primary)
            """
            
            await db_manager.execute_query(insert_query, {
                "id": assignment_id,
                "client_id": assignment.client_id,
                "brand_id": assignment.brand_id,
                "is_primary": assignment.is_primary
            })
            
            # Return assignment
            return ClientBrandResponse(
                id=assignment_id,
                client_id=assignment.client_id,
                brand_id=assignment.brand_id,
                brand_name=brand_data.name,
                is_primary=assignment.is_primary,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error assigning brand to client: {e}")
            raise
    
    async def get_client_brands(self, user_id: str, client_id: str) -> List[ClientBrandResponse]:
        """Get all brands assigned to a client"""
        try:
            query = """
                SELECT cb.id, cb.client_id, cb.brand_id, tb.name as brand_name,
                       cb.is_primary, cb.created_at
                FROM client_brands cb
                JOIN tracked_brands tb ON cb.brand_id = tb.id
                WHERE cb.client_id = :client_id AND tb.user_id = :user_id
                ORDER BY cb.is_primary DESC, cb.created_at DESC
            """
            
            brands_data = await db_manager.fetch_all(query, {
                "client_id": client_id,
                "user_id": user_id
            })
            
            return [ClientBrandResponse(**dict(brand)) for brand in brands_data]
            
        except Exception as e:
            logger.error(f"Error getting client brands: {e}")
            raise
    
    async def remove_brand_from_client(self, user_id: str, client_id: str, brand_id: str) -> bool:
        """Remove a brand from a client"""
        try:
            # Verify client belongs to user
            await self.get_client(user_id, client_id)
            
            query = """
                DELETE FROM client_brands 
                WHERE client_id = :client_id 
                AND brand_id = :brand_id
                AND EXISTS (
                    SELECT 1 FROM tracked_brands 
                    WHERE id = :brand_id AND user_id = :user_id
                )
            """
            
            await db_manager.execute_query(query, {
                "client_id": client_id,
                "brand_id": brand_id,
                "user_id": user_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing brand from client: {e}")
            raise
    
    async def _get_user(self, user_id: str) -> User:
        """Get user by ID"""
        query = """
            SELECT id, email, user_type, plan_type, is_active
            FROM users WHERE id = :user_id
        """
        
        user_data = await db_manager.fetch_one(query, {"user_id": user_id})
        
        if not user_data:
            raise ValueError("User not found")
        
        return User(**dict(user_data))
    
    async def _check_client_limits(self, user_id: str, plan_type: str) -> None:
        """Check if user can create more clients"""
        # Get current client count
        query = """
            SELECT COUNT(*) as count FROM clients 
            WHERE user_id = :user_id AND status = 'active'
        """
        
        result = await db_manager.fetch_one(query, {"user_id": user_id})
        current_count = result.count if result else 0
        
        # Get plan limits
        plan_limit = self.pricing_config.get_plan_limit(plan_type, 'clients')
        
        if current_count >= plan_limit:
            raise ValueError(f"Client limit reached ({plan_limit}). Upgrade your plan to add more clients.")


# Global service instance
client_service = ClientService()