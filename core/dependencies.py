from typing import Optional, Callable
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.security import verify_token
from core.database import get_supabase_client
from models.user import UserInDB, UserRole

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    """
    Dependency to get the current authenticated user from JWT token.
    NO DATABASE QUERY - All user data embedded in JWT for performance.
    
    Args:
        credentials: The HTTP Bearer token credentials
        
    Returns:
        The authenticated user constructed from JWT claims
        
    Raises:
        HTTPException: If token is invalid or user is inactive
    """
    token = credentials.credentials
    
    # Verify and decode token
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract required fields from token
    email: Optional[str] = payload.get("sub")
    user_id: Optional[str] = payload.get("user_id")
    name: Optional[str] = payload.get("name")
    role: Optional[str] = payload.get("role")
    is_active: Optional[bool] = payload.get("is_active")
    organization_id: Optional[str] = payload.get("organization_id")
    
    if email is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active (from JWT claim)
    if is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Construct user from JWT claims (NO DATABASE QUERY!)
    try:
        user = UserInDB(
            id=user_id,
            email=email,
            name=name or "Unknown",
            role=UserRole(role) if role else UserRole.USER,
            is_active=is_active if is_active is not None else True,
            password_hash="",  # Not needed for auth checks
            created_at=datetime.utcnow().isoformat(),  # Not critical for auth
            organization_id=organization_id
        )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token data: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Dependency to ensure the current user is active
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        The active user
        
    Raises:
        HTTPException: If user is inactive
    """
    # is_active check is now performed in get_current_user
    return current_user


def check_permission(user: UserInDB, required_role: UserRole) -> bool:
    """
    Check if a user has the required permission level
    
    Args:
        user: The user to check
        required_role: The minimum required role
        
    Returns:
        True if user has sufficient permissions
    """
    role_hierarchy = {
        UserRole.USER: 0,
        UserRole.ADMIN: 1,
        UserRole.SUPER_ADMIN: 2
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level


def require_role(required_role: UserRole) -> Callable:
    """
    Factory function to create role-based permission dependencies
    
    Args:
        required_role: The minimum required role
        
    Returns:
        A FastAPI dependency function that checks role permissions
    """
    async def role_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if not check_permission(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role(UserRole.ADMIN)
require_super_admin = require_role(UserRole.SUPER_ADMIN)
