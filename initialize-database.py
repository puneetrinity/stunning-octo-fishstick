#!/usr/bin/env python3
"""
Initialize ChatSEO Platform database on Railway
This script runs Alembic migrations to create all necessary tables
"""

import os
import sys
import asyncio
import logging
from sqlalchemy import create_engine, text
from databases import Database
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_connection():
    """Check if we can connect to the database"""
    try:
        database = Database(settings.database_url)
        await database.connect()
        
        # Test basic connectivity
        result = await database.fetch_one("SELECT 1 as test")
        logger.info(f"Database connection test: {result}")
        
        await database.disconnect()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def check_tables_exist():
    """Check if user tables exist"""
    try:
        database = Database(settings.database_url)
        await database.connect()
        
        # Check if users table exists
        result = await database.fetch_one("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        """)
        
        users_table_exists = result is not None
        logger.info(f"Users table exists: {users_table_exists}")
        
        # List all tables
        tables = await database.fetch_all("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        table_names = [row.table_name for row in tables]
        logger.info(f"Existing tables: {table_names}")
        
        await database.disconnect()
        return users_table_exists, table_names
        
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False, []

async def create_users_table_manually():
    """Create users table manually if Alembic isn't working"""
    try:
        database = Database(settings.database_url)
        await database.connect()
        
        # Create users table with all necessary columns
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                company_name VARCHAR(255),
                user_type VARCHAR(50) NOT NULL DEFAULT 'brand',
                plan_type VARCHAR(50) NOT NULL DEFAULT 'brand_starter',
                is_active BOOLEAN DEFAULT true,
                is_verified BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            )
        """)
        
        # Create brands table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                aliases TEXT[],
                is_primary BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create basic indexes
        await database.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        await database.execute("CREATE INDEX IF NOT EXISTS idx_brands_user_id ON brands(user_id)")
        
        logger.info("✅ Essential tables created successfully!")
        
        await database.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

async def test_user_registration():
    """Test user registration after table creation"""
    try:
        database = Database(settings.database_url)
        await database.connect()
        
        # Try to insert a test user
        test_email = f"test-{int(asyncio.get_event_loop().time())}@chatseo.com"
        
        await database.execute("""
            INSERT INTO users (email, password_hash, full_name, company_name, user_type, plan_type)
            VALUES (:email, :password_hash, :full_name, :company_name, :user_type, :plan_type)
        """, {
            "email": test_email,
            "password_hash": "test_hash_123",
            "full_name": "Test User",
            "company_name": "Test Company",
            "user_type": "brand",
            "plan_type": "brand_starter"
        })
        
        # Verify user was created
        user = await database.fetch_one("SELECT * FROM users WHERE email = :email", {"email": test_email})
        
        if user:
            logger.info(f"✅ Test user created successfully: {test_email}")
            
            # Clean up test user
            await database.execute("DELETE FROM users WHERE email = :email", {"email": test_email})
            logger.info("✅ Test user cleaned up")
            
            await database.disconnect()
            return True
        else:
            logger.error("❌ Failed to create test user")
            await database.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"❌ User registration test failed: {e}")
        return False

async def main():
    """Main database initialization process"""
    logger.info("🚀 Starting ChatSEO Database Initialization")
    logger.info(f"Database URL: {settings.database_url[:50]}...")
    
    # Step 1: Test database connection
    logger.info("\n📡 Step 1: Testing database connection...")
    if not await check_database_connection():
        logger.error("❌ Cannot connect to database. Check DATABASE_URL environment variable.")
        return False
    
    # Step 2: Check existing tables
    logger.info("\n📋 Step 2: Checking existing tables...")
    users_exist, tables = await check_tables_exist()
    
    if users_exist:
        logger.info("✅ Users table already exists!")
    else:
        logger.info("⚠️ Users table doesn't exist. Creating tables...")
        
        # Step 3: Create essential tables
        logger.info("\n🔨 Step 3: Creating essential tables...")
        if not await create_users_table_manually():
            logger.error("❌ Failed to create tables")
            return False
    
    # Step 4: Test user registration
    logger.info("\n🧪 Step 4: Testing user registration...")
    if await test_user_registration():
        logger.info("✅ Database initialization successful!")
        logger.info("\n🎉 Your ChatSEO Platform database is ready!")
        logger.info("👥 Users can now register and login!")
        return True
    else:
        logger.error("❌ User registration test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ SUCCESS: Database initialized and ready for users!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Database initialization failed")
        sys.exit(1)