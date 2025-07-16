from typing import List, Optional, Dict, Any
from app.database import db_manager
from app.schemas.brand import (
    BrandCreate, BrandUpdate, BrandResponse, BrandStats,
    BrandBulkCreate, BrandBulkResponse
)
from app.models.user import User
from app.config.pricing import PricingConfig
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class BrandService:
    """Service for managing tracked brands"""
    
    def __init__(self):
        self.pricing_config = PricingConfig()
    
    async def create_brand(self, user_id: str, brand_data: BrandCreate) -> BrandResponse:
        """Create a new tracked brand"""
        try:
            # Check brand limits
            await self._check_brand_limits(user_id)
            
            # Create brand
            brand_id = str(uuid.uuid4())
            query = """
                INSERT INTO tracked_brands (
                    id, user_id, name, aliases, description, website_url, is_primary, is_active
                ) VALUES (
                    :id, :user_id, :name, :aliases, :description, :website_url, :is_primary, :is_active
                ) RETURNING id
            """
            
            await db_manager.execute_query(query, {
                "id": brand_id,
                "user_id": user_id,
                "name": brand_data.name,
                "aliases": brand_data.aliases,
                "description": brand_data.description,
                "website_url": brand_data.website_url,
                "is_primary": brand_data.is_primary,
                "is_active": True
            })
            
            # If this is marked as primary, unset other primary brands
            if brand_data.is_primary:
                await self._unset_other_primary_brands(user_id, brand_id)
            
            # Get created brand
            brand = await self.get_brand(user_id, brand_id)
            
            logger.info(f"Brand created: {brand_id} for user: {user_id}")
            return brand
            
        except Exception as e:
            logger.error(f"Error creating brand: {e}")
            raise
    
    async def get_brand(self, user_id: str, brand_id: str) -> BrandResponse:
        """Get a specific brand"""
        try:
            query = """
                SELECT id, name, aliases, description, website_url, is_primary, 
                       is_active, created_at, updated_at
                FROM tracked_brands
                WHERE id = :brand_id AND user_id = :user_id
            """
            
            brand_data = await db_manager.fetch_one(query, {
                "brand_id": brand_id,
                "user_id": user_id
            })
            
            if not brand_data:
                raise ValueError("Brand not found")
            
            return BrandResponse(**dict(brand_data))
            
        except Exception as e:
            logger.error(f"Error getting brand: {e}")
            raise
    
    async def list_brands(self, user_id: str, is_active: Optional[bool] = None) -> List[BrandResponse]:
        """List all brands for a user"""
        try:
            query = """
                SELECT id, name, aliases, description, website_url, is_primary,
                       is_active, created_at, updated_at
                FROM tracked_brands
                WHERE user_id = :user_id
            """
            
            params = {"user_id": user_id}
            
            if is_active is not None:
                query += " AND is_active = :is_active"
                params["is_active"] = is_active
            
            query += " ORDER BY is_primary DESC, created_at DESC"
            
            brands_data = await db_manager.fetch_all(query, params)
            
            return [BrandResponse(**dict(brand)) for brand in brands_data]
            
        except Exception as e:
            logger.error(f"Error listing brands: {e}")
            raise
    
    async def update_brand(self, user_id: str, brand_id: str, brand_data: BrandUpdate) -> BrandResponse:
        """Update a brand"""
        try:
            # Build update query dynamically
            updates = []
            params = {"brand_id": brand_id, "user_id": user_id}
            
            if brand_data.name is not None:
                updates.append("name = :name")
                params["name"] = brand_data.name
            
            if brand_data.aliases is not None:
                updates.append("aliases = :aliases")
                params["aliases"] = brand_data.aliases
            
            if brand_data.description is not None:
                updates.append("description = :description")
                params["description"] = brand_data.description
            
            if brand_data.website_url is not None:
                updates.append("website_url = :website_url")
                params["website_url"] = brand_data.website_url
            
            if brand_data.is_primary is not None:
                updates.append("is_primary = :is_primary")
                params["is_primary"] = brand_data.is_primary
            
            if brand_data.is_active is not None:
                updates.append("is_active = :is_active")
                params["is_active"] = brand_data.is_active
            
            if updates:
                updates.append("updated_at = :updated_at")
                params["updated_at"] = datetime.utcnow()
                
                query = f"""
                    UPDATE tracked_brands 
                    SET {', '.join(updates)} 
                    WHERE id = :brand_id AND user_id = :user_id
                """
                
                await db_manager.execute_query(query, params)
                
                # If this is marked as primary, unset other primary brands
                if brand_data.is_primary:
                    await self._unset_other_primary_brands(user_id, brand_id)
            
            # Return updated brand
            return await self.get_brand(user_id, brand_id)
            
        except Exception as e:
            logger.error(f"Error updating brand: {e}")
            raise
    
    async def delete_brand(self, user_id: str, brand_id: str) -> bool:
        """Delete a brand (soft delete by setting is_active = false)"""
        try:
            query = """
                UPDATE tracked_brands 
                SET is_active = false, updated_at = :updated_at
                WHERE id = :brand_id AND user_id = :user_id
            """
            
            await db_manager.execute_query(query, {
                "brand_id": brand_id,
                "user_id": user_id,
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Brand deleted: {brand_id} for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting brand: {e}")
            raise
    
    async def get_brand_stats(self, user_id: str, brand_id: str) -> BrandStats:
        """Get brand statistics"""
        try:
            # Get brand info
            brand = await self.get_brand(user_id, brand_id)
            
            # Get stats from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            stats_query = """
                SELECT 
                    COUNT(DISTINCT c.id) as total_mentions,
                    COUNT(DISTINCT CASE WHEN c.mentioned = true THEN c.id END) as mentioned_count,
                    AVG(CASE WHEN c.mentioned = true THEN c.prominence_score END) as avg_prominence,
                    AVG(CASE WHEN c.mentioned = true THEN c.sentiment_score END) as avg_sentiment,
                    array_agg(DISTINCT qr.platform) as platforms,
                    MAX(qr.executed_at) as last_mentioned
                FROM tracked_brands tb
                LEFT JOIN citations c ON tb.id = c.brand_id
                LEFT JOIN query_results qr ON c.query_result_id = qr.id
                WHERE tb.id = :brand_id 
                AND tb.user_id = :user_id
                AND (qr.executed_at IS NULL OR qr.executed_at >= :thirty_days_ago)
                GROUP BY tb.id
            """
            
            stats_data = await db_manager.fetch_one(stats_query, {
                "brand_id": brand_id,
                "user_id": user_id,
                "thirty_days_ago": thirty_days_ago
            })
            
            if not stats_data:
                # Return empty stats if no data
                return BrandStats(
                    brand_id=brand_id,
                    brand_name=brand.name,
                    total_mentions=0,
                    mention_rate=0.0,
                    average_prominence=0.0,
                    average_sentiment=0.0,
                    platforms=[],
                    last_mentioned=None
                )
            
            # Calculate mention rate
            total_mentions = stats_data.total_mentions or 0
            mentioned_count = stats_data.mentioned_count or 0
            mention_rate = (mentioned_count / total_mentions * 100) if total_mentions > 0 else 0.0
            
            # Clean up platforms array (remove nulls)
            platforms = [p for p in (stats_data.platforms or []) if p is not None]
            
            return BrandStats(
                brand_id=brand_id,
                brand_name=brand.name,
                total_mentions=total_mentions,
                mention_rate=mention_rate,
                average_prominence=float(stats_data.avg_prominence or 0.0),
                average_sentiment=float(stats_data.avg_sentiment or 0.0),
                platforms=platforms,
                last_mentioned=stats_data.last_mentioned
            )
            
        except Exception as e:
            logger.error(f"Error getting brand stats: {e}")
            raise
    
    async def bulk_create_brands(self, user_id: str, bulk_data: BrandBulkCreate) -> BrandBulkResponse:
        """Create multiple brands at once"""
        try:
            created_brands = []
            failed_brands = []
            
            for brand_data in bulk_data.brands:
                try:
                    brand = await self.create_brand(user_id, brand_data)
                    created_brands.append(brand)
                except Exception as e:
                    failed_brands.append({
                        "brand_data": brand_data.dict(),
                        "error": str(e)
                    })
            
            return BrandBulkResponse(
                created=created_brands,
                failed=failed_brands
            )
            
        except Exception as e:
            logger.error(f"Error bulk creating brands: {e}")
            raise
    
    async def get_brand_competitors(self, user_id: str, brand_id: str) -> List[Dict[str, Any]]:
        """Get competitor analysis for a brand"""
        try:
            # This would integrate with the competitor analysis features
            # For now, return placeholder data
            return []
            
        except Exception as e:
            logger.error(f"Error getting brand competitors: {e}")
            raise
    
    async def _check_brand_limits(self, user_id: str) -> None:
        """Check if user can create more brands"""
        # Get user and plan type
        user_query = """
            SELECT plan_type FROM users WHERE id = :user_id
        """
        
        user_data = await db_manager.fetch_one(user_query, {"user_id": user_id})
        
        if not user_data:
            raise ValueError("User not found")
        
        # Get current brand count
        count_query = """
            SELECT COUNT(*) as count FROM tracked_brands 
            WHERE user_id = :user_id AND is_active = true
        """
        
        result = await db_manager.fetch_one(count_query, {"user_id": user_id})
        current_count = result.count if result else 0
        
        # Get plan limits
        plan_type = user_data.plan_type
        
        # For brand users, check brands_tracked limit
        if plan_type.startswith('brand_'):
            plan_limit = self.pricing_config.get_plan_limit(plan_type, 'brands_tracked')
        else:
            # For agency users, they can create brands for their clients
            # Use a higher limit or make it unlimited
            plan_limit = 999  # Effectively unlimited for agencies
        
        if current_count >= plan_limit:
            raise ValueError(f"Brand limit reached ({plan_limit}). Upgrade your plan to add more brands.")
    
    async def _unset_other_primary_brands(self, user_id: str, current_brand_id: str) -> None:
        """Unset primary flag for other brands when setting a new primary"""
        try:
            query = """
                UPDATE tracked_brands 
                SET is_primary = false, updated_at = :updated_at
                WHERE user_id = :user_id AND id != :current_brand_id AND is_primary = true
            """
            
            await db_manager.execute_query(query, {
                "user_id": user_id,
                "current_brand_id": current_brand_id,
                "updated_at": datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Error unsetting other primary brands: {e}")
            # Don't raise here as this is a supporting operation


# Global service instance
brand_service = BrandService()