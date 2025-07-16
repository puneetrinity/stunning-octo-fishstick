from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from app.config import settings
import asyncio


# SQLAlchemy setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Async database connection
database = Database(settings.database_url)


async def get_database():
    """Get database connection for dependency injection"""
    return database


async def connect_db():
    """Connect to database on startup"""
    await database.connect()


async def disconnect_db():
    """Disconnect from database on shutdown"""
    await database.disconnect()


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