from typing import Optional
from fastapi import APIRouter, Depends, Query
from core.dependencies import require_admin, require_super_admin, get_current_user
from models.user import (
    UserInDB, UserResponse, UserCreateByAdmin, UserUpdateByAdmin,
    UserRoleUpdate, UserStatusUpdate, UserListResponse, AdminStatsResponse
)
from services.user_management_service import user_management_service

router = APIRouter()


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_statistics(
    current_user: UserInDB = Depends(require_admin)
):
    """
    Get admin dashboard statistics
    
    **Required Role:** Admin or Super Admin
    
    Returns:
        - Total user counts
        - Users by role (super_admin, admin, user)
        - Active/inactive counts
        - New users (today, this week, this month)
        - Recent user registrations
    """
    return await user_management_service.get_admin_stats()


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    role: Optional[str] = Query(None, description="Filter by role (super_admin, admin, user)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name or email"),
    current_user: UserInDB = Depends(require_admin)
):
    """
    Get paginated list of users with optional filters
    
    **Required Role:** Admin or Super Admin
    
    Query Parameters:
        - skip: Pagination offset (default: 0)
        - limit: Page size (default: 50, max: 100)
        - role: Filter by user role
        - is_active: Filter by active status
        - search: Search by name or email (case-insensitive)
    
    Returns:
        - Paginated list of users
        - Total count
        - Page information
    """
    return await user_management_service.list_users(
        skip=skip,
        limit=limit,
        role_filter=role,
        is_active_filter=is_active,
        search_query=search
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Get detailed information about a specific user
    
    **Required Role:** Admin or Super Admin
    
    Path Parameters:
        - user_id: The unique identifier of the user
    
    Returns:
        - User details (excluding password)
    """
    return await user_management_service.get_user_by_id(user_id)


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreateByAdmin,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Create a new user (admin operation)
    
    **Required Role:** Admin or Super Admin
    
    **Permission Rules:**
        - Regular admins can only create regular users
        - Super admins can create users with any role (except super_admin via API)
        - Super admin role can only be assigned via direct SQL
    
    Request Body:
        - email: User's email address (must be unique)
        - name: User's full name
        - password: User's password (will be hashed)
        - role: User role (user, admin - super_admin not allowed)
    
    Returns:
        - Created user details (excluding password)
    """
    return await user_management_service.create_user_by_admin(user_data, current_user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdateByAdmin,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Update user details (admin operation)
    
    **Required Role:** Admin or Super Admin
    
    **Permission Rules:**
        - Regular admins can only update regular users
        - Super admins can update any user
        - Cannot update your own account through this endpoint
    
    Path Parameters:
        - user_id: The unique identifier of the user to update
    
    Request Body (all optional):
        - name: Updated name
        - email: Updated email (must be unique if changed)
        - password: New password (will be hashed)
    
    Returns:
        - Updated user details
    """
    return await user_management_service.update_user(user_id, user_data, current_user)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    role_data: UserRoleUpdate,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Change a user's role (admin operation)
    
    **Required Role:** Admin or Super Admin
    
    **Permission Rules:**
        - Regular admins can only change roles for regular users (to 'user' only)
        - Super admins can promote users to admin (but not super_admin via API)
        - Cannot change your own role
        - Super admin role can only be assigned via direct SQL
    
    Path Parameters:
        - user_id: The unique identifier of the user
    
    Request Body:
        - role: New role (user, admin)
    
    Returns:
        - Updated user details with new role
    """
    return await user_management_service.update_user_role(user_id, role_data, current_user)


@router.put("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    current_user: UserInDB = Depends(require_admin)
):
    """
    Activate or deactivate a user account
    
    **Required Role:** Admin or Super Admin
    
    **Permission Rules:**
        - Regular admins can only deactivate regular users
        - Super admins can deactivate any user (except themselves)
        - Cannot deactivate your own account
        - Inactive users cannot log in
    
    Path Parameters:
        - user_id: The unique identifier of the user
    
    Request Body:
        - is_active: true to activate, false to deactivate
    
    Returns:
        - Updated user details with new status
    """
    return await user_management_service.update_user_status(user_id, status_data, current_user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    permanent: bool = Query(False, description="If true, permanently delete; if false, deactivate"),
    current_user: UserInDB = Depends(require_super_admin)
):
    """
    Delete a user account (soft or hard delete)
    
    **Required Role:** Super Admin only
    
    **Permission Rules:**
        - Only super admins can delete users
        - Soft delete (permanent=false): Deactivates the user account
        - Hard delete (permanent=true): Permanently removes user from database
        - Cannot delete your own account
        - Cannot delete other super admin accounts
    
    Path Parameters:
        - user_id: The unique identifier of the user
    
    Query Parameters:
        - permanent: true for hard delete, false for soft delete (default: false)
    
    Returns:
        - Success message
    """
    return await user_management_service.delete_user(user_id, current_user, permanent)
