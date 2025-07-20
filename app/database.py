from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from databases import Database
from app.config import settings
import asyncio


# SQLAlchemy 2.0 Base class
class Base(DeclarativeBase):
    metadata = MetaData()


# SQLAlchemy setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async database connection
database = Database(settings.database_url)


async def get_database():
    """Get database connection for dependency injection"""
    return database


async def connect_db():
    """Connect to database on startup"""
    try:
        await database.connect()
        # Test the connection
        await database.fetch_one("SELECT 1")
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Database connection failed: {e}")
        raise


async def disconnect_db():
    """Disconnect from database on shutdown"""
    try:
        if database.is_connected:
            await database.disconnect()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error during database disconnect: {e}")


# Database session dependency
def get_db():
    """Get database session (sync)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self):
        self.database = database
    
    async def execute_query(self, query: str, values: dict = None):
        """Execute a query with optional values"""
        if values:
            return await self.database.execute(query, values)
        return await self.database.execute(query)
    
    async def fetch_one(self, query: str, values: dict = None):
        """Fetch single row"""
        if values:
            return await self.database.fetch_one(query, values)
        return await self.database.fetch_one(query)
    
    async def fetch_all(self, query: str, values: dict = None):
        """Fetch all rows"""
        if values:
            return await self.database.fetch_all(query, values)
        return await self.database.fetch_all(query)
    
    async def execute_many(self, query: str, values: list):
        """Execute query with multiple value sets"""
        return await self.database.execute_many(query, values)


# Global database manager instance
db_manager = DatabaseManager()