from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from core.database import get_supabase_client
from core.security import get_password_hash
from models.user import (
    UserRole, UserInDB, UserResponse, UserCreateByAdmin,
    UserUpdateByAdmin, UserRoleUpdate, UserStatusUpdate,
    UserListResponse, AdminStatsResponse
)


class UserManagementService:
    """Service for admin user management operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role_filter: Optional[str] = None,
        is_active_filter: Optional[bool] = None,
        search_query: Optional[str] = None
    ) -> UserListResponse:
        """
        Get paginated list of users with optional filters
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            role_filter: Filter by role (super_admin, admin, user)
            is_active_filter: Filter by active status
            search_query: Search in name or email
            
        Returns:
            UserListResponse with total count and user list
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            # Build query
            query = self.supabase.table("users").select("*", count="exact")
            
            # Apply filters
            if role_filter:
                query = query.eq("role", role_filter)
            
            if is_active_filter is not None:
                query = query.eq("is_active", is_active_filter)
            
            if search_query:
                # Search in name or email (case-insensitive)
                query = query.or_(f"name.ilike.%{search_query}%,email.ilike.%{search_query}%")
            
            # Get total count
            count_result = query.execute()
            total = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            
            # Apply pagination and ordering
            result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
            
            # Convert to UserResponse objects (excluding password_hash)
            users = []
            for user_data in result.data:
                user_dict = {k: v for k, v in user_data.items() if k != "password_hash"}
                users.append(UserResponse(**user_dict))
            
            # Calculate pagination info
            page = (skip // limit) + 1
            total_pages = (total + limit - 1) // limit  # Ceiling division
            
            return UserListResponse(
                total=total,
                users=users,
                page=page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching users: {str(e)}"
            )
    
    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """
        Get a single user by ID
        
        Args:
            user_id: The user's unique identifier
            
        Returns:
            UserResponse with user details
            
        Raises:
            HTTPException: If user not found or database error
        """
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user_data = result.data[0]
            # Exclude password_hash
            user_dict = {k: v for k, v in user_data.items() if k != "password_hash"}
            
            return UserResponse(**user_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user: {str(e)}"
            )
    
    async def create_user_by_admin(
        self,
        user_data: UserCreateByAdmin,
        admin_user: UserInDB
    ) -> UserResponse:
        """
        Create a new user (admin operation)
        
        Args:
            user_data: User creation data with role
            admin_user: The admin creating the user
            
        Returns:
            UserResponse with created user details
            
        Raises:
            HTTPException: If validation fails or email exists
        """
        try:
            # Validate admin has permission to create user with this role
            user_data.validate_role_permission(admin_user.role)
            
            # Check if email already exists
            existing = self.supabase.table("users").select("id").eq("email", user_data.email).execute()
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            password_hash = get_password_hash(user_data.password)
            
            # Prepare user data
            new_user_data = {
                "email": user_data.email,
                "name": user_data.name,
                "password_hash": password_hash,
                "role": user_data.role.value,
                "is_active": True,
                "created_by": str(admin_user.id)
            }
            
            # Insert user
            result = self.supabase.table("users").insert(new_user_data).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
            
            created_user = result.data[0]
            user_dict = {k: v for k, v in created_user.items() if k != "password_hash"}
            
            return UserResponse(**user_dict)
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )
    
    async def update_user(
        self,
        user_id: str,
        user_data: UserUpdateByAdmin,
        admin_user: UserInDB
    ) -> UserResponse:
        """
        Update user details (admin operation)
        
        Args:
            user_id: The user's unique identifier
            user_data: Updated user data
            admin_user: The admin performing the update
            
        Returns:
            UserResponse with updated user details
            
        Raises:
            HTTPException: If validation fails or user not found
        """
        try:
            # Fetch existing user
            existing_result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not existing_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            existing_user = existing_result.data[0]
            
            # Check if admin can modify this user
            if not self._check_can_modify_user(admin_user, existing_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to modify this user"
                )
            
            # Prepare update data
            update_data = {
                "updated_by": str(admin_user.id),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Update name if provided
            if user_data.name is not None:
                update_data["name"] = user_data.name
            
            # Update email if provided and different
            if user_data.email is not None and user_data.email != existing_user["email"]:
                # Check email uniqueness
                email_check = self.supabase.table("users").select("id").eq("email", user_data.email).execute()
                if email_check.data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already in use"
                    )
                update_data["email"] = user_data.email
            
            # Update password if provided
            if user_data.password is not None:
                update_data["password_hash"] = get_password_hash(user_data.password)
            
            # Execute update
            result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user"
                )
            
            updated_user = result.data[0]
            user_dict = {k: v for k, v in updated_user.items() if k != "password_hash"}
            
            return UserResponse(**user_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user: {str(e)}"
            )
    
    async def update_user_role(
        self,
        user_id: str,
        role_data: UserRoleUpdate,
        admin_user: UserInDB
    ) -> UserResponse:
        """
        Update user role (admin operation)
        
        Args:
            user_id: The user's unique identifier
            role_data: New role data
            admin_user: The admin performing the update
            
        Returns:
            UserResponse with updated user details
            
        Raises:
            HTTPException: If validation fails or user not found
        """
        try:
            # Validate admin has permission for this role change
            role_data.validate_role_permission(admin_user.role)
            
            # Prevent self-role modification
            if str(admin_user.id) == user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify your own role"
                )
            
            # Fetch existing user
            existing_result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not existing_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            existing_user = existing_result.data[0]
            
            # Check if admin can modify this user
            if not self._check_can_modify_user(admin_user, existing_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to modify this user's role"
                )
            
            # Update role
            update_data = {
                "role": role_data.role.value,
                "updated_by": str(admin_user.id),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user role"
                )
            
            updated_user = result.data[0]
            user_dict = {k: v for k, v in updated_user.items() if k != "password_hash"}
            
            return UserResponse(**user_dict)
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user role: {str(e)}"
            )
    
    async def update_user_status(
        self,
        user_id: str,
        status_data: UserStatusUpdate,
        admin_user: UserInDB
    ) -> UserResponse:
        """
        Update user active status (admin operation)
        
        Args:
            user_id: The user's unique identifier
            status_data: New status data
            admin_user: The admin performing the update
            
        Returns:
            UserResponse with updated user details
            
        Raises:
            HTTPException: If validation fails or user not found
        """
        try:
            # Prevent self-deactivation
            if str(admin_user.id) == user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify your own status"
                )
            
            # Fetch existing user
            existing_result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not existing_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            existing_user = existing_result.data[0]
            target_role = UserRole(existing_user.get("role", "user"))
            
            # Check permissions: regular admins cannot deactivate admins or super_admins
            if admin_user.role == UserRole.ADMIN:
                if target_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions to modify this user's status"
                    )
            
            # Update status
            update_data = {
                "is_active": status_data.is_active,
                "updated_by": str(admin_user.id),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user status"
                )
            
            updated_user = result.data[0]
            user_dict = {k: v for k, v in updated_user.items() if k != "password_hash"}
            
            return UserResponse(**user_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user status: {str(e)}"
            )
    
    async def delete_user(
        self,
        user_id: str,
        admin_user: UserInDB,
        permanent: bool = False
    ) -> Dict[str, str]:
        """
        Delete user (soft or hard delete)
        
        Args:
            user_id: The user's unique identifier
            admin_user: The admin performing the deletion
            permanent: If True, permanently delete; if False, soft delete (deactivate)
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If validation fails or user not found
        """
        try:
            # Prevent self-deletion
            if str(admin_user.id) == user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete your own account"
                )
            
            # Fetch existing user
            existing_result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if not existing_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            existing_user = existing_result.data[0]
            target_role = UserRole(existing_user.get("role", "user"))
            
            # Check permissions
            if admin_user.role == UserRole.ADMIN:
                # Regular admins can only soft-delete regular users
                if target_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions to delete this user"
                    )
                if permanent:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only super admins can permanently delete users"
                    )
            
            if permanent:
                # Hard delete
                result = self.supabase.table("users").delete().eq("id", user_id).execute()
                return {"message": "User permanently deleted successfully"}
            else:
                # Soft delete (deactivate)
                update_data = {
                    "is_active": False,
                    "updated_by": str(admin_user.id),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
                return {"message": "User deactivated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting user: {str(e)}"
            )
    
    async def get_admin_stats(self) -> AdminStatsResponse:
        """
        Get dashboard statistics for admin
        
        Returns:
            AdminStatsResponse with user counts and metrics
            
        Raises:
            HTTPException: If database query fails
        """
        try:
            # Get all users
            all_users_result = self.supabase.table("users").select("*").execute()
            all_users = all_users_result.data
            
            # Calculate stats
            total_users = len(all_users)
            
            # Count by role
            super_admin_count = sum(1 for u in all_users if u.get("role") == "super_admin")
            admin_count = sum(1 for u in all_users if u.get("role") == "admin")
            user_count = sum(1 for u in all_users if u.get("role") == "user")
            
            # Count active/inactive
            active_users = sum(1 for u in all_users if u.get("is_active", True))
            inactive_users = total_users - active_users
            
            # Count new users (today, this week, this month)
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            month_start = today_start.replace(day=1)
            
            new_users_today = 0
            new_users_week = 0
            new_users_month = 0
            
            for user in all_users:
                created_at_str = user.get("created_at")
                if created_at_str:
                    # Parse ISO format datetime
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if created_at >= today_start:
                        new_users_today += 1
                    if created_at >= week_start:
                        new_users_week += 1
                    if created_at >= month_start:
                        new_users_month += 1
            
            # Get request counts (from requests table)
            try:
                requests_result = self.supabase.table("requests").select("id, status", count="exact").execute()
                total_requests = requests_result.count if hasattr(requests_result, 'count') else len(requests_result.data) if requests_result.data else 0
                
                # Count pending approvals (requests with status = 'pending')
                pending_result = self.supabase.table("requests").select("id", count="exact").eq("status", "pending").execute()
                pending_approvals = pending_result.count if hasattr(pending_result, 'count') else len(pending_result.data) if pending_result.data else 0
            except:
                # If requests table doesn't exist or error, use 0
                total_requests = 0
                pending_approvals = 0
            
            return AdminStatsResponse(
                total_users=total_users,
                active_users=active_users,
                inactive_users=inactive_users,
                users_by_role={
                    "super_admin": super_admin_count,
                    "admin": admin_count,
                    "user": user_count
                },
                total_requests=total_requests,
                pending_approvals=pending_approvals,
                recent_signups=new_users_week  # Last 7 days as per model spec
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching admin stats: {str(e)}"
            )
    
    def _check_can_modify_user(self, admin: UserInDB, target_user: Dict) -> bool:
        """
        Check if admin has permission to modify target user
        
        Args:
            admin: The admin user
            target_user: The target user dict from database
            
        Returns:
            True if admin can modify, False otherwise
        """
        target_role = UserRole(target_user.get("role", "user"))
        
        # Super admin can modify anyone except themselves (checked separately)
        if admin.role == UserRole.SUPER_ADMIN:
            return True
        
        # Regular admin cannot modify admins or super_admins
        if target_role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            return False
        
        return True


# Create service instance
user_management_service = UserManagementService()
