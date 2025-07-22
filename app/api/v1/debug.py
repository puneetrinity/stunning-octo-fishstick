"""Debug endpoints for Railway deployment"""
from fastapi import APIRouter, HTTPException
from app.database import db_manager
from app.config import settings
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/database/tables")
async def list_database_tables():
    """List all database tables"""
    try:
        tables = await db_manager.fetch_all("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        return {"tables": [row.table_name for row in tables]}
    except Exception as e:
        return {"error": str(e)}

@router.get("/database/users-table")
async def check_users_table():
    """Check users table structure"""
    try:
        columns = await db_manager.fetch_all("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        return {"columns": [dict(col) for col in columns]}
    except Exception as e:
        return {"error": str(e)}

@router.post("/database/test-insert")
async def test_user_insert():
    """Test inserting a user directly"""
    try:
        test_email = f"debug-{uuid.uuid4().hex[:8]}@chatseo.com"
        user_id = str(uuid.uuid4())
        
        # Test direct insert
        await db_manager.execute_query("""
            INSERT INTO users (id, email, password_hash, full_name, company_name, user_type, plan_type, is_active, is_verified)
            VALUES (:id, :email, :password_hash, :full_name, :company_name, :user_type, :plan_type, :is_active, :is_verified)
        """, {
            "id": user_id,
            "email": test_email,
            "password_hash": "$2b$12$test_hash",
            "full_name": "Debug User",
            "company_name": "Debug Company",
            "user_type": "brand",
            "plan_type": "brand_starter",
            "is_active": True,
            "is_verified": False
        })
        
        # Verify insert
        user = await db_manager.fetch_one(
            "SELECT * FROM users WHERE email = :email",
            {"email": test_email}
        )
        
        if user:
            # Clean up
            await db_manager.execute_query(
                "DELETE FROM users WHERE email = :email",
                {"email": test_email}
            )
            return {"success": True, "message": "Database insert/delete test passed", "user_id": user_id}
        else:
            return {"success": False, "message": "Insert test failed - user not found"}
            
    except Exception as e:
        logger.error(f"Database test insert failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@router.get("/config")
async def get_config_info():
    """Get configuration info"""
    return {
        "database_url_prefix": settings.database_url[:30] + "...",
        "debug": settings.debug,
        "environment": settings.environment,
        "app_name": settings.app_name,
        "app_version": settings.app_version
    }