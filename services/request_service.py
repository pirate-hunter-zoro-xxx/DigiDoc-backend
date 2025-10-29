"""
Request Service - Business logic for request management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from core.database import get_supabase_client
from models.request import (
    RequestCreate, RequestUpdate, RequestResponse, RequestDetailResponse,
    WorkflowStageCreate, WorkflowStageResponse,
    RequestStatus, StageStatus, CommentCreate, CommentResponse
)


class RequestService:
    """Service for handling request operations"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def create_request(
        self,
        request_data: RequestCreate,
        creator_id: str
    ) -> RequestDetailResponse:
        """
        Create a new request with workflow stages
        
        Args:
            request_data: Request creation data
            creator_id: ID of the user creating the request
            
        Returns:
            Created request with workflow stages
        """
        try:
            # Create the request
            request_insert = {
                "title": request_data.title,
                "description": request_data.description,
                "creator_id": creator_id,
                "status": RequestStatus.DRAFT.value
            }
            
            result = self.supabase.table("requests").insert(request_insert).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create request"
                )
            
            request = result.data[0]
            request_id = request["id"]
            
            # Create workflow stages if provided
            workflow_stages = []
            if request_data.workflow_stages:
                # Validate order indices are sequential
                order_indices = [stage.order_index for stage in request_data.workflow_stages]
                if sorted(order_indices) != list(range(1, len(order_indices) + 1)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Workflow stage order indices must be sequential starting from 1"
                    )
                
                # Validate assigned users exist
                user_ids = [stage.assigned_user_id for stage in request_data.workflow_stages]
                users_result = self.supabase.table("users").select("id, name, email").in_("id", user_ids).execute()
                
                if len(users_result.data) != len(user_ids):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more assigned users not found"
                    )
                
                # Create workflow stages
                stages_to_insert = [
                    {
                        "request_id": request_id,
                        "stage_type": stage.stage_type.value,
                        "assigned_user_id": stage.assigned_user_id,
                        "order_index": stage.order_index,
                        "status": StageStatus.PENDING.value
                    }
                    for stage in request_data.workflow_stages
                ]
                
                stages_result = self.supabase.table("workflow_stages").insert(stages_to_insert).execute()
                
                if stages_result.data:
                    workflow_stages = await self._format_workflow_stages(stages_result.data)
            
            # Get creator info
            creator_result = self.supabase.table("users").select("name, email").eq("id", creator_id).execute()
            creator = creator_result.data[0] if creator_result.data else {"name": "Unknown", "email": ""}
            
            # Format response
            return RequestDetailResponse(
                id=request["id"],
                title=request["title"],
                description=request.get("description"),
                creator_id=creator_id,
                creator_name=creator["name"],
                creator_email=creator["email"],
                status=RequestStatus(request["status"]),
                current_stage_id=request.get("current_stage_id"),
                created_at=request["created_at"],
                updated_at=request["updated_at"],
                submitted_at=request.get("submitted_at"),
                completed_at=request.get("completed_at"),
                workflow_stages=workflow_stages,
                can_edit=True,
                can_submit=len(workflow_stages) > 0,
                can_cancel=False
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create request: {str(e)}"
            )

    async def get_request(
        self,
        request_id: str,
        user_id: str
    ) -> RequestDetailResponse:
        """
        Get a request by ID with workflow stages
        
        Args:
            request_id: ID of the request
            user_id: ID of the user requesting the data
            
        Returns:
            Request with workflow stages
        """
        try:
            # Get request
            result = self.supabase.table("requests").select("*").eq("id", request_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )
            
            request = result.data[0]
            
            # Check if user has access (creator or part of workflow)
            has_access = await self._check_user_access(request_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this request"
                )
            
            # Get creator info
            creator_result = self.supabase.table("users").select("name, email").eq("id", request["creator_id"]).execute()
            creator = creator_result.data[0] if creator_result.data else {"name": "Unknown", "email": ""}
            
            # Get workflow stages
            stages_result = self.supabase.table("workflow_stages").select("*").eq("request_id", request_id).order("order_index").execute()
            workflow_stages = await self._format_workflow_stages(stages_result.data if stages_result.data else [])
            
            # Determine user permissions
            is_creator = request["creator_id"] == user_id
            request_status = RequestStatus(request["status"])
            
            can_edit = is_creator and request_status == RequestStatus.DRAFT
            can_submit = is_creator and request_status == RequestStatus.DRAFT and len(workflow_stages) > 0
            can_cancel = is_creator and request_status not in [RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED]
            
            return RequestDetailResponse(
                id=request["id"],
                title=request["title"],
                description=request.get("description"),
                creator_id=request["creator_id"],
                creator_name=creator["name"],
                creator_email=creator["email"],
                status=request_status,
                current_stage_id=request.get("current_stage_id"),
                created_at=request["created_at"],
                updated_at=request["updated_at"],
                submitted_at=request.get("submitted_at"),
                completed_at=request.get("completed_at"),
                workflow_stages=workflow_stages,
                can_edit=can_edit,
                can_submit=can_submit,
                can_cancel=can_cancel
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get request: {str(e)}"
            )

    async def list_user_requests(
        self,
        user_id: str,
        status_filter: Optional[RequestStatus] = None,
        page: int = 1,
        page_size: int = 10,
        created_by_me: bool = True
    ) -> Dict[str, Any]:
        """
        List requests for a user (created by them or assigned to them)
        
        Args:
            user_id: ID of the user
            status_filter: Optional status filter
            page: Page number (1-indexed)
            page_size: Number of items per page
            created_by_me: If True, show only requests created by user. If False, include assigned requests.
            
        Returns:
            Dictionary with requests list and pagination info
        """
        try:
            # Get requests where user is creator
            query = self.supabase.table("requests").select("*", count="exact")
            
            # Add creator filter
            query = query.eq("creator_id", user_id)
            
            # Add status filter if provided
            if status_filter:
                query = query.eq("status", status_filter.value)
            
            # Calculate pagination
            offset = (page - 1) * page_size
            
            # Execute query with pagination
            result = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
            
            requests_data = result.data if result.data else []
            total = result.count if hasattr(result, 'count') else len(requests_data)
            
            # Only include assigned requests if created_by_me is False
            if not created_by_me:
                # Get requests where user is part of workflow
                workflow_result = self.supabase.table("workflow_stages").select("request_id").eq("assigned_user_id", user_id).execute()
                
                if workflow_result.data:
                    workflow_request_ids = list(set([stage["request_id"] for stage in workflow_result.data]))
                    
                    # Get these requests
                    workflow_query = self.supabase.table("requests").select("*").in_("id", workflow_request_ids)
                    
                    if status_filter:
                        workflow_query = workflow_query.eq("status", status_filter.value)
                    
                    workflow_requests_result = workflow_query.order("created_at", desc=True).execute()
                    
                    if workflow_requests_result.data:
                        # Merge and deduplicate
                        all_requests = {req["id"]: req for req in requests_data}
                        for req in workflow_requests_result.data:
                            if req["id"] not in all_requests:
                                all_requests[req["id"]] = req
                        
                        requests_data = list(all_requests.values())
                        requests_data.sort(key=lambda x: x["created_at"], reverse=True)
                        
                        # Apply pagination to merged list
                        requests_data = requests_data[offset:offset + page_size]
                        total = len(all_requests)
            
            # Format requests
            formatted_requests = []
            for request in requests_data:
                # Get creator info
                creator_result = self.supabase.table("users").select("name, email").eq("id", request["creator_id"]).execute()
                creator = creator_result.data[0] if creator_result.data else {"name": "Unknown", "email": ""}
                
                formatted_requests.append(RequestResponse(
                    id=request["id"],
                    title=request["title"],
                    description=request.get("description"),
                    creator_id=request["creator_id"],
                    creator_name=creator["name"],
                    creator_email=creator["email"],
                    status=RequestStatus(request["status"]),
                    current_stage_id=request.get("current_stage_id"),
                    created_at=request["created_at"],
                    updated_at=request["updated_at"],
                    submitted_at=request.get("submitted_at"),
                    completed_at=request.get("completed_at")
                ))
            
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return {
                "requests": formatted_requests,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list requests: {str(e)}"
            )

    async def update_request(
        self,
        request_id: str,
        user_id: str,
        update_data: RequestUpdate
    ) -> RequestDetailResponse:
        """
        Update a request (only allowed in DRAFT status)
        
        Args:
            request_id: ID of the request
            user_id: ID of the user updating the request
            update_data: Update data
            
        Returns:
            Updated request
        """
        try:
            # Get request
            result = self.supabase.table("requests").select("*").eq("id", request_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )
            
            request = result.data[0]
            
            # Check if user is creator
            if request["creator_id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the creator can update the request"
                )
            
            # Check if request is in DRAFT status
            if request["status"] != RequestStatus.DRAFT.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only draft requests can be updated"
                )
            
            # Prepare update data
            update_dict = update_data.model_dump(exclude_unset=True)
            
            if not update_dict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No update data provided"
                )
            
            # Update request
            update_result = self.supabase.table("requests").update(update_dict).eq("id", request_id).execute()
            
            if not update_result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update request"
                )
            
            # Return updated request
            return await self.get_request(request_id, user_id)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update request: {str(e)}"
            )

    async def delete_request(
        self,
        request_id: str,
        user_id: str
    ) -> Dict[str, str]:
        """
        Delete a request (only allowed in DRAFT status)
        
        Args:
            request_id: ID of the request
            user_id: ID of the user deleting the request
            
        Returns:
            Success message
        """
        try:
            # Get request
            result = self.supabase.table("requests").select("*").eq("id", request_id).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )
            
            request = result.data[0]
            
            # Check if user is creator
            if request["creator_id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the creator can delete the request"
                )
            
            # Check if request is in DRAFT status
            if request["status"] != RequestStatus.DRAFT.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only draft requests can be deleted"
                )
            
            # Delete request (cascade will delete workflow stages)
            self.supabase.table("requests").delete().eq("id", request_id).execute()
            
            return {"message": "Request deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete request: {str(e)}"
            )

    async def add_comment(
        self,
        request_id: str,
        user_id: str,
        comment_data: CommentCreate
    ) -> CommentResponse:
        """Add a comment to a request"""
        try:
            # Check if user has access to request
            has_access = await self._check_user_access(request_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this request"
                )
            
            # Create comment
            comment_insert = {
                "request_id": request_id,
                "user_id": user_id,
                "comment": comment_data.comment
            }
            
            result = self.supabase.table("request_comments").insert(comment_insert).execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to add comment"
                )
            
            comment = result.data[0]
            
            # Get user info
            user_result = self.supabase.table("users").select("name, email").eq("id", user_id).execute()
            user = user_result.data[0] if user_result.data else {"name": "Unknown", "email": ""}
            
            return CommentResponse(
                id=comment["id"],
                request_id=comment["request_id"],
                user_id=comment["user_id"],
                user_name=user["name"],
                user_email=user["email"],
                comment=comment["comment"],
                created_at=comment["created_at"],
                updated_at=comment["updated_at"]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add comment: {str(e)}"
            )

    async def get_comments(
        self,
        request_id: str,
        user_id: str
    ) -> List[CommentResponse]:
        """Get all comments for a request"""
        try:
            # Check if user has access to request
            has_access = await self._check_user_access(request_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this request"
                )
            
            # Get comments
            result = self.supabase.table("request_comments").select("*").eq("request_id", request_id).order("created_at").execute()
            
            comments_data = result.data if result.data else []
            
            # Format comments with user info
            formatted_comments = []
            for comment in comments_data:
                user_result = self.supabase.table("users").select("name, email").eq("id", comment["user_id"]).execute()
                user = user_result.data[0] if user_result.data else {"name": "Unknown", "email": ""}
                
                formatted_comments.append(CommentResponse(
                    id=comment["id"],
                    request_id=comment["request_id"],
                    user_id=comment["user_id"],
                    user_name=user["name"],
                    user_email=user["email"],
                    comment=comment["comment"],
                    created_at=comment["created_at"],
                    updated_at=comment["updated_at"]
                ))
            
            return formatted_comments
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get comments: {str(e)}"
            )

    # Helper methods
    
    async def _check_user_access(self, request_id: str, user_id: str) -> bool:
        """Check if user has access to a request"""
        # Check if user is creator
        request_result = self.supabase.table("requests").select("creator_id").eq("id", request_id).execute()
        
        if request_result.data and request_result.data[0]["creator_id"] == user_id:
            return True
        
        # Check if user is part of workflow
        workflow_result = self.supabase.table("workflow_stages").select("id").eq("request_id", request_id).eq("assigned_user_id", user_id).execute()
        
        return bool(workflow_result.data)

    async def _format_workflow_stages(self, stages_data: List[Dict]) -> List[WorkflowStageResponse]:
        """Format workflow stages with user info"""
        formatted_stages = []
        
        for stage in stages_data:
            # Get assigned user info
            user_result = self.supabase.table("users").select("name, email").eq("id", stage["assigned_user_id"]).execute()
            user = user_result.data[0] if user_result.data else {"name": "Unknown", "email": ""}
            
            formatted_stages.append(WorkflowStageResponse(
                id=stage["id"],
                request_id=stage["request_id"],
                stage_type=stage["stage_type"],
                assigned_user_id=stage["assigned_user_id"],
                assigned_user_name=user["name"],
                assigned_user_email=user["email"],
                order_index=stage["order_index"],
                status=stage["status"],
                comments=stage.get("comments"),
                action=stage.get("action"),
                action_at=stage.get("action_at"),
                created_at=stage["created_at"]
            ))
        
        return formatted_stages
