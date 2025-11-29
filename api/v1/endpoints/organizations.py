from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from models.user import UserInDB, UserRole
from models.organization import (
    OrganizationCreate, OrganizationUpdate,
    OrganizationResponse, OrganizationWithStats, OrganizationListResponse
)
from services.organization_service import organization_service
from core.dependencies import require_super_admin, get_current_user

router = APIRouter()


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: UserInDB = Depends(require_super_admin)
):
    """
    Create a new organization
    
    **Required Role:** Super Admin only
    
    Request Body:
        - name: Organization name (required, 1-255 characters)
        - slug: URL-safe identifier (required, lowercase alphanumeric with hyphens)
        - description: Optional description
    
    Returns:
        - Created organization details
    """
    return await organization_service.create_organization(org_data, current_user.id)


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    include_inactive: bool = Query(False, description="Include inactive organizations"),
    current_user: UserInDB = Depends(require_super_admin)
):
    """
    List all organizations
    
    **Required Role:** Super Admin only
    
    Query Parameters:
        - skip: Pagination offset (default: 0)
        - limit: Page size (default: 50, max: 100)
        - include_inactive: Include deactivated organizations (default: false)
    
    Returns:
        - Paginated list of organizations with total count and pagination info
    """
    return await organization_service.list_organizations(skip, limit, include_inactive)


@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get current user's organization
    
    **Required Role:** Any authenticated user
    
    Returns:
        - Current user's organization details
    
    Raises:
        - 404: If user is not assigned to an organization
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not assigned to an organization"
        )
    
    return await organization_service.get_organization(current_user.organization_id)


@router.get("/{org_id}", response_model=OrganizationWithStats)
async def get_organization(
    org_id: str,
    include_stats: bool = Query(True, description="Include user and request statistics"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get organization details with optional statistics
    
    **Required Role:** Authenticated user (can only access own organization unless super admin)
    
    Path Parameters:
        - org_id: Organization ID
    
    Query Parameters:
        - include_stats: Include user/request counts (default: true)
    
    Returns:
        - Organization details with stats (if requested):
            - user_count: Total users in organization
            - active_user_count: Active users count
            - request_count: Total requests count
            - pending_request_count: Pending requests count
    
    Raises:
        - 403: If non-super-admin tries to access another organization
        - 404: If organization not found
    """
    # Super admin can see any org, others only their own
    if current_user.role != UserRole.SUPER_ADMIN:
        if org_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other organizations"
            )
    
    return await organization_service.get_organization(org_id, include_stats)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    current_user: UserInDB = Depends(require_super_admin)
):
    """
    Update organization details
    
    **Required Role:** Super Admin only
    
    Path Parameters:
        - org_id: Organization ID
    
    Request Body (all optional):
        - name: Updated organization name
        - description: Updated description
        - is_active: Active status
    
    Returns:
        - Updated organization details
    
    Raises:
        - 404: If organization not found
        - 400: If no update data provided
    """
    return await organization_service.update_organization(org_id, org_data)


@router.delete("/{org_id}")
async def deactivate_organization(
    org_id: str,
    current_user: UserInDB = Depends(require_super_admin)
):
    """
    Deactivate an organization (soft delete)
    
    **Required Role:** Super Admin only
    
    Path Parameters:
        - org_id: Organization ID
    
    Note: This performs a soft delete - sets is_active to false.
    Users in this organization will not be able to perform operations.
    
    Returns:
        - Success message
    
    Raises:
        - 404: If organization not found
    """
    return await organization_service.deactivate_organization(org_id)
