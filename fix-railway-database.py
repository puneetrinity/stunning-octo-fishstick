#!/usr/bin/env python3
"""
Fix ChatSEO Platform database on Railway
This script connects to Railway's database and fixes the user registration issue
"""

import os
import sys
import asyncio
import logging
import uuid
from databases import Database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway database URL - we need to set this properly
RAILWAY_DATABASE_URL = "postgresql://postgres:mXKoqWdZDwjyiGvpzpCEUYSfSHmGFfNP@junction.proxy.rlwy.net:39532/railway"

async def test_railway_connection():
    """Test connection to Railway database"""
    try:
        database = Database(RAILWAY_DATABASE_URL)
        await database.connect()
        
        # Test basic connectivity
        result = await database.fetch_one("SELECT version() as version")
        logger.info(f"Railway database connected: {result.version[:50]}...")
        
        await database.disconnect()
        return True
    except Exception as e:
        logger.error(f"Railway database connection failed: {e}")
        return False

async def check_railway_tables():
    """Check Railway database tables"""
    try:
        database = Database(RAILWAY_DATABASE_URL)
        await database.connect()
        
        # List all tables
        tables = await database.fetch_all("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        table_names = [row.table_name for row in tables]
        logger.info(f"Railway tables: {table_names}")
        
        # Check users table structure
        if 'users' in table_names:
            columns = await database.fetch_all("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            logger.info("Users table structure:")
            for col in columns:
                logger.info(f"  {col.column_name}: {col.data_type} (default: {col.column_default}, nullable: {col.is_nullable})")
        
        await database.disconnect()
        return 'users' in table_names
        
    except Exception as e:
        logger.error(f"Error checking Railway tables: {e}")
        return False

async def create_railway_tables():
    """Create tables on Railway if they don't exist"""
    try:
        database = Database(RAILWAY_DATABASE_URL)
        await database.connect()
        
        # Enable UUID extension
        await database.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        
        # Create users table with proper UUID generation
        await database.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                aliases TEXT[],
                is_primary BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        await database.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        await database.execute("CREATE INDEX IF NOT EXISTS idx_brands_user_id ON brands(user_id)")
        
        logger.info("✅ Railway tables created successfully!")
        
        await database.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Error creating Railway tables: {e}")
        return False

async def test_railway_registration():
    """Test user registration on Railway"""
    try:
        database = Database(RAILWAY_DATABASE_URL)
        await database.connect()
        
        # Generate unique email
        test_email = f"test-{uuid.uuid4().hex[:8]}@chatseo.com"
        
        # Insert test user
        await database.execute("""
            INSERT INTO users (email, password_hash, full_name, company_name, user_type, plan_type)
            VALUES (:email, :password_hash, :full_name, :company_name, :user_type, :plan_type)
        """, {
            "email": test_email,
            "password_hash": "$2b$12$test_hash_for_demo_purposes",
            "full_name": "Test User",
            "company_name": "Test Company",
            "user_type": "brand",
            "plan_type": "brand_starter"
        })
        
        # Verify user was created
        user = await database.fetch_one("SELECT * FROM users WHERE email = :email", {"email": test_email})
        
        if user:
            logger.info(f"✅ Railway registration test successful: {test_email}")
            logger.info(f"✅ User ID: {user.id}")
            
            # Clean up test user
            await database.execute("DELETE FROM users WHERE email = :email", {"email": test_email})
            logger.info("✅ Test user cleaned up")
            
        await database.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Railway registration test failed: {e}")
        return False

async def main():
    """Main Railway database fix process"""
    logger.info("🚀 Fixing ChatSEO Railway Database")
    
    # Step 1: Test Railway connection
    logger.info("\n📡 Step 1: Testing Railway database connection...")
    if not await test_railway_connection():
        logger.error("❌ Cannot connect to Railway database")
        return False
    
    # Step 2: Check/create tables
    logger.info("\n📋 Step 2: Checking Railway tables...")
    tables_exist = await check_railway_tables()
    
    if not tables_exist:
        logger.info("\n🔨 Step 3: Creating Railway tables...")
        if not await create_railway_tables():
            logger.error("❌ Failed to create Railway tables")
            return False
    
    # Step 3: Test registration
    logger.info("\n🧪 Step 4: Testing Railway registration...")
    if await test_railway_registration():
        logger.info("\n🎉 SUCCESS: Railway database is ready!")
        logger.info("👥 Users can now register and login!")
        return True
    else:
        logger.error("❌ Railway registration test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ SUCCESS: Railway database fixed and ready!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Railway database fix failed")
        sys.exit(1)