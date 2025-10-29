from fastapi import APIRouter
from api.v1.endpoints import auth, users, health, requests, workflow

# Create main v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(workflow.router, prefix="/workflow", tags=["Workflow"])
