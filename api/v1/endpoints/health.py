from fastapi import APIRouter, status
from core.database import test_database_connection
from core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    
    Returns: Service status
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint with database connectivity test
    
    Returns: Service readiness status including database connection
    """
    db_connected = test_database_connection()
    
    return {
        "status": "ready" if db_connected else "not_ready",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if db_connected else "disconnected"
    }
