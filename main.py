from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import logging
import os
from app.config import settings
from app.database import connect_db, disconnect_db

# Configure for Railway deployment
try:
    from app.config.railway_config import configure_for_railway
    railway_config = configure_for_railway()
    logger = logging.getLogger(__name__)
    logger.info(f"Railway configuration applied: {railway_config}")
except ImportError:
    pass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up ChatSEO Platform...")
    
    # Check if database should be skipped (for Railway without database)
    if os.getenv("SKIP_DATABASE_INIT") != "true":
        try:
            await connect_db()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            # Continue without database for demo/testing purposes
            logger.warning("Running without database connection - some features may be limited")
    else:
        logger.info("Database initialization skipped (SKIP_DATABASE_INIT=true)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ChatSEO Platform...")
    if os.getenv("SKIP_DATABASE_INIT") != "true":
        try:
            await disconnect_db()
            logger.info("Database disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting database: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for monitoring brand mentions across AI platforms",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if not settings.debug:
    # Allow Railway domains and your custom domains
    allowed_hosts = [
        "yourdomain.com", 
        "*.yourdomain.com",
        "*.up.railway.app",  # Railway domains
        "*.railway.app",     # Railway custom domains
        "stunning-octo-fishstick-production.up.railway.app"  # Your specific domain
    ]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The request data is invalid",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Add database connectivity check
    return {
        "status": "ready",
        "timestamp": time.time(),
        "components": {
            "database": "connected",
            "redis": "connected"
        }
    }


# Root endpoint - serve frontend
@app.get("/", tags=["Root"])
async def root():
    """Serve frontend interface"""
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        return {
            "message": "Welcome to ChatSEO Platform API",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else None
        }


# Import and include routers
from app.api.v1 import auth, brands, clients, roi, pricing, monitoring, review_sites, citations, authority_sources, debug

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(brands.router, prefix="/api/v1/brands", tags=["Brands"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["Clients"])
app.include_router(roi.router, prefix="/api/v1/roi", tags=["ROI Tracking"])
app.include_router(pricing.router, prefix="/api/v1/pricing", tags=["Pricing"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(review_sites.router, prefix="/api/v1/review-sites", tags=["Review Sites"])
app.include_router(citations.router, prefix="/api/v1/citations", tags=["Citations"])
app.include_router(authority_sources.router, prefix="/api/v1/authority-sources", tags=["Authority Sources"])

# Debug endpoints (only in development or for troubleshooting)
app.include_router(debug.router, prefix="/api/v1/debug", tags=["Debug"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )