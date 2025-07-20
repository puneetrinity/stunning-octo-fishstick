"""Railway-specific configuration handling"""
import os
from urllib.parse import urlparse, parse_qs


def parse_railway_database_url():
    """
    Parse Railway's DATABASE_URL format and handle connection parameters.
    Railway provides DATABASE_URL in different formats that need special handling.
    """
    database_url = os.getenv("DATABASE_URL", "")
    
    if not database_url:
        # No database URL provided, return None to skip database initialization
        return None
    
    # Handle Railway's private networking URLs
    if database_url.startswith("postgresql://"):
        # Parse the URL
        parsed = urlparse(database_url)
        
        # Railway sometimes provides URLs with special parameters
        # Handle both internal and public URLs
        if ".railway.internal" in database_url:
            # Internal networking URL - needs special handling
            # Extract components and rebuild URL
            user = parsed.username or "postgres"
            password = parsed.password or ""
            host = parsed.hostname or "localhost"
            port = parsed.port or 5432
            database = parsed.path.lstrip("/") or "railway"
            
            # Rebuild URL with proper escaping
            if password:
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                database_url = f"postgresql://{user}@{host}:{port}/{database}"
        
        # Add connection pool and timeout parameters for Railway
        if "?" not in database_url:
            database_url += "?"
        else:
            database_url += "&"
        
        # Add Railway-optimized connection parameters
        database_url += "pool_size=5&max_overflow=10&pool_timeout=30&pool_recycle=1800"
        
    return database_url


def get_redis_url():
    """Get Redis URL with Railway-specific handling"""
    redis_url = os.getenv("REDIS_URL", "")
    
    if not redis_url:
        # No Redis URL provided, return None
        return None
    
    # Handle Railway's Redis URLs
    if ".railway.internal" in redis_url:
        # Parse and rebuild for internal networking
        parsed = urlparse(redis_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        password = parsed.password
        
        if password:
            redis_url = f"redis://:{password}@{host}:{port}/0"
        else:
            redis_url = f"redis://{host}:{port}/0"
    
    return redis_url


def configure_for_railway():
    """Configure application for Railway deployment"""
    # Set environment variables based on Railway's provided ones
    
    # Database configuration
    db_url = parse_railway_database_url()
    if db_url:
        os.environ["DATABASE_URL"] = db_url
    else:
        # No database URL - set a flag to skip database initialization
        os.environ["SKIP_DATABASE_INIT"] = "true"
    
    # Redis configuration
    redis_url = get_redis_url()
    if redis_url:
        os.environ["REDIS_URL"] = redis_url
        os.environ["CELERY_BROKER_URL"] = redis_url
        os.environ["CELERY_RESULT_BACKEND"] = redis_url
    else:
        # No Redis - disable features that require it
        os.environ["DISABLE_REDIS_FEATURES"] = "true"
    
    # Railway-specific settings
    os.environ["ENVIRONMENT"] = "production"
    os.environ["DEBUG"] = "false"
    
    # Use Railway's PORT if available
    if os.getenv("PORT"):
        os.environ["APP_PORT"] = os.getenv("PORT")
    
    # Set other production defaults
    if not os.getenv("JWT_SECRET_KEY"):
        # Generate a random secret key if not provided
        import secrets
        os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(32)
    
    return {
        "database_configured": bool(db_url),
        "redis_configured": bool(redis_url),
        "port": os.getenv("PORT", "8080")
    }