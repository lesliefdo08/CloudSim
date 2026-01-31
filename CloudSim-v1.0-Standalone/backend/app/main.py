"""
CloudSim Backend - Main Application Entry Point
Production-ready FastAPI application with proper middleware and configuration
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.database import close_db
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.api.router import setup_routers
from app.schemas.common import HealthCheckResponse
from app.core.exception_handlers import register_exception_handlers


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.LOG_FORMAT == "text"
           else '{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting CloudSim backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Version: {settings.APP_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    # Start background workers
    from app.workers.metrics_collector import start_metrics_collector
    from app.workers.alarm_evaluator import start_alarm_evaluator
    
    start_metrics_collector()
    logger.info("CloudWatch metrics collector started")
    
    start_alarm_evaluator()
    logger.info("CloudWatch alarm evaluator started")
    
    # TODO: Initialize other services
    # - Database connection pool
    # - Redis connection
    # - Docker client
    
    logger.info("CloudSim backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CloudSim backend...")
    
    # Stop background workers
    from app.workers.metrics_collector import stop_metrics_collector
    from app.workers.alarm_evaluator import stop_alarm_evaluator
    
    stop_metrics_collector()
    logger.info("CloudWatch metrics collector stopped")
    
    stop_alarm_evaluator()
    logger.info("CloudWatch alarm evaluator stopped")
    
    # Close database connections
    await close_db()
    
    # TODO: Cleanup other services
    # - Close Redis connections
    # - Close Docker client
    
    logger.info("CloudSim backend shut down successfully")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AWS-like cloud simulator for learning and practice",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)


# ============================================
# MIDDLEWARE CONFIGURATION
# ============================================

# 1. CORS Middleware - Must be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 2. GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Custom Error Handler - Must be last
app.add_middleware(ErrorHandlerMiddleware)


# ============================================
# EXCEPTION HANDLERS
# ============================================

# Register custom exception handlers for AWS-style error responses
register_exception_handlers(app)


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["System"],
    summary="Health check endpoint"
)
async def health_check(request: Request) -> HealthCheckResponse:
    """
    Check application health and dependent services status
    
    Returns:
        HealthCheckResponse with status of all services
    """
    services_status = {}
    
    # TODO: Check dependent services
    # - Database: Try to execute simple query
    # - Redis: Try to ping
    # - Docker: Try to get client info
    
    # Placeholder status
    services_status["database"] = "not_checked"
    services_status["redis"] = "not_checked"
    services_status["docker"] = "not_checked"
    
    overall_status = "healthy"  # Change to "unhealthy" if any service is down
    
    return HealthCheckResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        services=services_status
    )


@app.get(
    "/",
    tags=["System"],
    summary="API root endpoint"
)
async def root() -> dict:
    """
    API root endpoint
    Provides basic information about the API
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_version": "v1",
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health"
    }


# ============================================
# REGISTER API ROUTERS
# ============================================

setup_routers(app)


# ============================================
# REQUEST LOGGING (Development Only)
# ============================================

if settings.DEBUG:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all requests in debug mode"""
        logger.info(f"{request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Status: {response.status_code}")
        return response


# ============================================
# APPLICATION ENTRY POINT
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG
    )
