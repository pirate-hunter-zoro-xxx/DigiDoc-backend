from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from models.user import UserInDB, UserUpdate, UserPasswordChange, UserResponse
from services.user_service import user_service
from core.dependencies import get_current_active_user

router = APIRouter()


@router.get("", response_model=dict)
async def list_users(
    search: Optional[str] = Query(None, description="Search term for name or email"),
    exclude_self: bool = Query(False, description="Exclude current user from results"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    List all users with optional search and filtering
    
    Requires: Valid access token in Authorization header
    
    Query Parameters:
    - **search**: Filter by name or email (case-insensitive)
    - **exclude_self**: Exclude current user from results (default: false)
    - **limit**: Maximum results to return (1-100, default: 50)
    
    Returns: List of users with id, name, email, created_at
    """
    exclude_user_id = current_user.id if exclude_self else None
    return await user_service.search_users(
        search_term=search,
        exclude_user_id=exclude_user_id,
        limit=limit
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current authenticated user profile
    
    Requires: Valid access token in Authorization header
    
    Returns: User profile data
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update current user's profile
    
    Requires: Valid access token in Authorization header
    
    - **name**: New name (optional)
    - **email**: New email (optional)
    
    Returns: Updated user profile
    """
    return await user_service.update_user(current_user.id, user_update)


@router.patch("/me/password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Change current user's password
    
    Requires: Valid access token in Authorization header
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 6 characters)
    
    Returns: Success message
    """
    return await user_service.change_password(current_user.id, password_data)


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_current_user(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Delete current user's account
    
    Requires: Valid access token in Authorization header
    
    Warning: This action is irreversible!
    
    Returns: Success message
    """
    return await user_service.delete_user(current_user.id)
