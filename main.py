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
    allow_methods=["*"],
    allow_headers=["*"],
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
