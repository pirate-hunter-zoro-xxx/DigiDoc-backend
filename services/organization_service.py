from typing import List, Optional
from fastapi import HTTPException, status
from models.organization import (
    OrganizationCreate, OrganizationUpdate, 
    OrganizationResponse, OrganizationWithStats
)
from services.base_service import BaseService


class OrganizationService(BaseService):
    """Service for organization operations"""
    
    async def create_organization(
        self, 
        org_data: OrganizationCreate, 
        created_by_id: str
    ) -> OrganizationResponse:
        """Create organization (super admin only)"""
        try:
            # Check slug uniqueness
            existing = self.supabase.table("organizations")\
                .select("id")\
                .eq("slug", org_data.slug)\
                .execute()
            
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Organization with slug '{org_data.slug}' already exists"
                )
            
            # Insert organization
            result = self.supabase.table("organizations").insert({
                "name": org_data.name,
                "slug": org_data.slug,
                "description": org_data.description,
                "created_by": created_by_id,
                "is_active": True
            }).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create organization"
                )
            
            org = result.data[0]
            return OrganizationResponse(**org)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating organization: {str(e)}"
            )
    
    async def list_organizations(
        self, 
        skip: int = 0, 
        limit: int = 50,
        include_inactive: bool = False
    ):
        """List all organizations (super admin only)"""
        try:
            # Get total count
            count_query = self.supabase.table("organizations").select("id", count="exact")
            if not include_inactive:
                count_query = count_query.eq("is_active", True)
            count_result = count_query.execute()
            total = count_result.count or 0
            
            # Get paginated data
            query = self.supabase.table("organizations").select("*")
            
            # Filter active organizations by default
            if not include_inactive:
                query = query.eq("is_active", True)
            
            result = query.order("created_at", desc=True)\
                .range(skip, skip + limit - 1)\
                .execute()
            
            organizations = [OrganizationResponse(**org) for org in (result.data or [])]
            
            # Calculate pagination info
            page = (skip // limit) + 1
            total_pages = (total + limit - 1) // limit
            
            return {
                "data": organizations,
                "total": total,
                "page": page,
                "page_size": limit,
                "total_pages": total_pages
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing organizations: {str(e)}"
            )
    
    async def get_organization(
        self, 
        org_id: str,
        include_stats: bool = False
    ) -> OrganizationResponse | OrganizationWithStats:
        """Get organization by ID"""
        try:
            result = self.supabase.table("organizations")\
                .select("*")\
                .eq("id", org_id)\
                .execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            
            org = result.data[0]
            
            if not include_stats:
                return OrganizationResponse(**org)
            
            # Get stats if requested
            users_result = self.supabase.table("users")\
                .select("id, is_active", count="exact")\
                .eq("organization_id", org_id)\
                .execute()
            
            requests_result = self.supabase.table("requests")\
                .select("id, status", count="exact")\
                .eq("organization_id", org_id)\
                .execute()
            
            user_count = users_result.count if hasattr(users_result, 'count') else len(users_result.data or [])
            active_users = len([u for u in (users_result.data or []) if u.get('is_active')])
            request_count = requests_result.count if hasattr(requests_result, 'count') else len(requests_result.data or [])
            
            # Count pending requests (DRAFT or SUBMITTED status)
            pending_statuses = ['DRAFT', 'SUBMITTED']
            pending_requests = len([r for r in (requests_result.data or []) if r.get('status') in pending_statuses])
            
            return OrganizationWithStats(
                **org,
                user_count=user_count,
                active_user_count=active_users,
                request_count=request_count,
                pending_request_count=pending_requests
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting organization: {str(e)}"
            )
    
    async def update_organization(
        self, 
        org_id: str, 
        org_data: OrganizationUpdate
    ) -> OrganizationResponse:
        """Update organization"""
        try:
            # Check exists
            existing = self.supabase.table("organizations")\
                .select("id")\
                .eq("id", org_id)\
                .execute()
            
            if not existing.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            
            # Build update dict
            update_dict = org_data.model_dump(exclude_unset=True)
            
            if not update_dict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No update data provided"
                )
            
            # Update
            result = self.supabase.table("organizations")\
                .update(update_dict)\
                .eq("id", org_id)\
                .execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update organization"
                )
            
            return OrganizationResponse(**result.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating organization: {str(e)}"
            )
    
    async def deactivate_organization(
        self, 
        org_id: str
    ) -> dict:
        """Soft delete organization"""
        try:
            result = self.supabase.table("organizations")\
                .update({"is_active": False})\
                .eq("id", org_id)\
                .execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            
            return {"message": "Organization deactivated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deactivating organization: {str(e)}"
            )
    
    async def get_or_create_default_organization(self) -> str:
        """
        Get the default organization or create it if it doesn't exist.
        Used for assigning new users to a default organization.
        
        Returns:
            organization_id: UUID of the default organization
            
        Raises:
            HTTPException: If organization creation fails
        """
        DEFAULT_ORG_SLUG = "default"
        DEFAULT_ORG_NAME = "Default Organization"
        
        try:
            # Check if default organization exists
            result = self.supabase.table("organizations")\
                .select("id")\
                .eq("slug", DEFAULT_ORG_SLUG)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]["id"]
            
            # Create default organization
            new_org = self.supabase.table("organizations").insert({
                "name": DEFAULT_ORG_NAME,
                "slug": DEFAULT_ORG_SLUG,
                "description": "Default organization for all users",
                "is_active": True
            }).execute()
            
            if not new_org.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create default organization"
                )
            
            return new_org.data[0]["id"]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting/creating default organization: {str(e)}"
            )


# Singleton instance
organization_service = OrganizationService()
