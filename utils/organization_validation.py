"""
Organization validation utilities for multi-tenant operations

Provides helpers to ensure users have valid organization_id
before performing organization-scoped operations.
"""

from typing import Any, Optional
from fastapi import HTTPException, status
from core.database import get_supabase_client


async def get_user_organization_id(user_id: str) -> str:
    """
    Get and validate user's organization_id from database.
    
    Args:
        user_id: User ID to look up
        
    Returns:
        str: User's organization ID
        
    Raises:
        HTTPException 404: If user not found
        HTTPException 403: If user has no organization
    """
    supabase = get_supabase_client()
    
    result = supabase.table("users")\
        .select("organization_id")\
        .eq("id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    org_id = result.data[0].get("organization_id")
    
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to an organization. Please contact administrator."
        )
    
    return str(org_id)


def validate_organization_access(user_org_id: str, resource_org_id: str) -> None:
    """
    Validate that user has access to a resource based on organization.
    
    Args:
        user_org_id: Organization ID from user's JWT/profile
        resource_org_id: Organization ID of the resource being accessed
        
    Raises:
        HTTPException 403: If organizations don't match
    """
    if user_org_id != resource_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Resource belongs to a different organization"
        )


def get_organization_id(user: Any) -> str:
    """
    Safely extract organization_id from user object.
    
    Args:
        user: User object (UserInDB, dict, etc.)
        
    Returns:
        str: Organization ID
        
    Raises:
        HTTPException 403: If user has no organization
    """
    # Handle dict
    if isinstance(user, dict):
        org_id = user.get('organization_id')
    # Handle object with attributes
    else:
        org_id = getattr(user, 'organization_id', None)
    
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to an organization. Please contact administrator."
        )
    
    return str(org_id)
