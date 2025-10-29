import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1.router import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Authentication and User Management API for SaaS Applications",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    expose_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health/health"
    }


# Debug endpoint for deployment issues
@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (remove in production)"""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "host": settings.HOST,
        "port": settings.PORT,
        "debug": settings.DEBUG,
        "supabase_url_set": bool(settings.SUPABASE_URL),
        "supabase_key_set": bool(settings.SUPABASE_KEY),
        "jwt_secret_set": bool(settings.JWT_SECRET_KEY != "your-secret-key-change-this"),
        "cors_origins": settings.BACKEND_CORS_ORIGINS,
        "environment_vars": {
            "PORT": os.getenv("PORT"),
            "HOST": os.getenv("HOST"),
            "SUPABASE_URL": "SET" if os.getenv("SUPABASE_URL") else "NOT_SET",
            "SUPABASE_KEY": "SET" if os.getenv("SUPABASE_KEY") else "NOT_SET",
        }
    }


# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Backward compatibility routes (optional - can be removed later)
@app.post("/api/register")
async def register_legacy(user_data: dict):
    """Legacy endpoint - redirects to new structure"""
    from models.user import UserCreate
    from services.auth_service import auth_service
    user = UserCreate(**user_data)
    result = await auth_service.register_user(user)
    # Return in old format for frontend compatibility
    return {
        "message": result.message,
        "user": result.user,
        "token": result.access_token
    }


@app.post("/api/login")
async def login_legacy(credentials: dict):
    """Legacy endpoint - redirects to new structure"""
    from models.user import UserLogin
    from services.auth_service import auth_service
    creds = UserLogin(**credentials)
    result = await auth_service.login_user(creds)
    # Return in old format for frontend compatibility
    return {
        "message": result.message,
        "user": result.user,
        "token": result.access_token
    }


@app.get("/health")
async def health_legacy():
    """Legacy health endpoint"""
    return {"status": "healthy"}


@app.get("/debug/database")
async def debug_database():
    """Test database connection (remove in production)"""
    try:
        from core.database import test_database_connection, get_supabase_client
        
        # Test basic client creation
        try:
            client = get_supabase_client()
            client_status = "OK"
        except Exception as e:
            client_status = f"ERROR: {str(e)}"
        
        # Test actual connection
        connection_test = test_database_connection()
        
        return {
            "supabase_client": client_status,
            "connection_test": connection_test,
            "supabase_url": settings.SUPABASE_URL[:20] + "..." if settings.SUPABASE_URL else "NOT_SET",
            "supabase_key": "SET" if settings.SUPABASE_KEY else "NOT_SET"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} starting...")
    print(f"📚 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔗 API Base URL: http://{settings.HOST}:{settings.PORT}{settings.API_V1_STR}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print(f"👋 {settings.PROJECT_NAME} shutting down...")
