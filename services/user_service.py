from typing import Dict, List, Optional
from fastapi import HTTPException, status
from core.database import get_supabase_client
from core.security import get_password_hash, verify_password
from models.user import UserInDB, UserCreate, UserUpdate, UserPasswordChange, UserResponse


class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            UserInDB if found, None otherwise
        """
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            
            if result.data:
                return UserInDB(**result.data[0])
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user: {str(e)}"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            UserInDB if found, None otherwise
        """
        try:
            result = self.supabase.table("users").select("*").eq("email", email).execute()
            
            if result.data:
                return UserInDB(**result.data[0])
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user: {str(e)}"
            )
    
    async def search_users(
        self,
        search_term: Optional[str] = None,
        exclude_user_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, any]:
        """
        Search users by name or email
        
        Args:
            search_term: Optional search term for name or email
            exclude_user_id: Optional user ID to exclude from results
            limit: Maximum number of results (default 50)
            
        Returns:
            Dictionary with users list and total count
        """
        try:
            # Start with base query
            query = self.supabase.table("users").select("id, name, email, created_at")
            
            # Apply search filter if provided
            if search_term:
                # Search in both name and email fields (case-insensitive)
                query = query.or_(f"name.ilike.%{search_term}%,email.ilike.%{search_term}%")
            
            # Exclude specific user if provided
            if exclude_user_id:
                query = query.neq("id", exclude_user_id)
            
            # Apply limit and ordering
            query = query.order("name").limit(limit)
            
            # Execute query
            result = query.execute()
            
            return {
                "users": result.data,
                "total": len(result.data)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching users: {str(e)}"
            )
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        """
        Update user profile
        
        Args:
            user_id: User ID
            user_update: User update data
            
        Returns:
            Updated user data
            
        Raises:
            HTTPException: If update fails or email already exists
        """
        try:
            update_data = user_update.model_dump(exclude_unset=True)
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            
            # If email is being updated, check if it's already taken
            if "email" in update_data:
                existing_user = await self.get_user_by_email(update_data["email"])
                if existing_user and existing_user.id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already in use"
                    )
            
            # Update user
            result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user = result.data[0]
            return UserResponse(
                id=str(user["id"]),
                email=user["email"],
                name=user["name"],
                created_at=user["created_at"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user: {str(e)}"
            )
    
    async def change_password(self, user_id: str, password_data: UserPasswordChange) -> dict:
        """
        Change user password
        
        Args:
            user_id: User ID
            password_data: Current and new password
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If current password is wrong or update fails
        """
        try:
            # Get user
            user = await self.get_user_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not verify_password(password_data.current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Hash new password
            new_password_hash = get_password_hash(password_data.new_password)
            
            # Update password
            result = self.supabase.table("users").update({
                "password_hash": new_password_hash
            }).eq("id", user_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update password"
                )
            
            return {"message": "Password updated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error changing password: {str(e)}"
            )
    
    async def delete_user(self, user_id: str) -> dict:
        """
        Delete user account
        
        Args:
            user_id: User ID
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            result = self.supabase.table("users").delete().eq("id", user_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return {"message": "User deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting user: {str(e)}"
            )


# Create service instance
user_service = UserService()
