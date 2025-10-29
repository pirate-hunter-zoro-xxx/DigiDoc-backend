"""
Workflow Service - Business logic for workflow management
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status

from core.database import get_supabase_client
from models.request import (
    RequestStatus, StageStatus, StageAction, StageType,
    WorkflowStageUpdate, WorkflowStageResponse, RequestSubmitResponse,
    RequestCancelResponse, PendingActionResponse, PendingActionsListResponse
)


class WorkflowService:
    """Service for handling workflow operations"""

    def __init__(self):
        self.supabase = get_supabase_client()

    async def submit_request(
        self,
        request_id: str,
        user_id: str
    ) -> RequestSubmitResponse:
        """
        Submit a request for review (moves from DRAFT to SUBMITTED)
        
        Args:
            request_id: ID of the request
            user_id: ID of the user submitting the request
            
        Returns:
            Submit response with next stage info
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
                    detail="Only the creator can submit the request"
                )
            
            # Check if request is in DRAFT status
            if request["status"] != RequestStatus.DRAFT.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request is already {request['status']}"
                )
            
            # Check if workflow stages exist
            stages_result = self.supabase.table("workflow_stages").select("*").eq("request_id", request_id).order("order_index").execute()
            
            if not stages_result.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot submit request without workflow stages"
                )
            
            stages = stages_result.data
            first_stage = stages[0]
            
            # Determine new status based on first stage type
            new_status = RequestStatus.IN_REVIEW if first_stage["stage_type"] == StageType.RECOMMEND.value else RequestStatus.IN_APPROVAL
            
            # Update request status and set current stage
            update_data = {
                "status": new_status.value,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "current_stage_id": first_stage["id"]
            }
            
            self.supabase.table("requests").update(update_data).eq("id", request_id).execute()
            
            # Update first stage to IN_PROGRESS
            self.supabase.table("workflow_stages").update({"status": StageStatus.IN_PROGRESS.value}).eq("id", first_stage["id"]).execute()
            
            # Get next stage info with user details
            user_result = self.supabase.table("users").select("name, email").eq("id", first_stage["assigned_user_id"]).execute()
            user = user_result.data[0] if user_result.data else {"name": "Unknown", "email": ""}
            
            next_stage = WorkflowStageResponse(
                id=first_stage["id"],
                request_id=first_stage["request_id"],
                stage_type=StageType(first_stage["stage_type"]),
                assigned_user_id=first_stage["assigned_user_id"],
                assigned_user_name=user["name"],
                assigned_user_email=user["email"],
                order_index=first_stage["order_index"],
                status=StageStatus.IN_PROGRESS,
                comments=None,
                action=None,
                action_at=None,
                created_at=first_stage["created_at"]
            )
            
            # TODO: Send notification to first stage user
            
            return RequestSubmitResponse(
                message="Request submitted successfully",
                request_id=request_id,
                status=new_status,
                next_stage=next_stage
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit request: {str(e)}"
            )

    async def take_action(
        self,
        stage_id: str,
        user_id: str,
        action_data: WorkflowStageUpdate
    ) -> Dict[str, Any]:
        """
        Take action on a workflow stage (recommend, approve, or reject)
        
        Args:
            stage_id: ID of the workflow stage
            user_id: ID of the user taking action
            action_data: Action data (action type and comments)
            
        Returns:
            Action result with next stage info
        """
        try:
            # Get stage
            stage_result = self.supabase.table("workflow_stages").select("*").eq("id", stage_id).execute()
            
            if not stage_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workflow stage not found"
                )
            
            stage = stage_result.data[0]
            
            # Check if user is assigned to this stage
            if stage["assigned_user_id"] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this workflow stage"
                )
            
            # Check if stage is pending or in progress
            if stage["status"] not in [StageStatus.PENDING.value, StageStatus.IN_PROGRESS.value]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This stage is already {stage['status']}"
                )
            
            # Validate action matches stage type
            if stage["stage_type"] == StageType.RECOMMEND.value and action_data.action != StageAction.RECOMMENDED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="RECOMMEND stages can only have RECOMMENDED action"
                )
            
            if stage["stage_type"] == StageType.APPROVE.value and action_data.action not in [StageAction.APPROVED, StageAction.REJECTED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="APPROVE stages can only have APPROVED or REJECTED action"
                )
            
            request_id = stage["request_id"]
            
            # Get request
            request_result = self.supabase.table("requests").select("*").eq("id", request_id).execute()
            
            if not request_result.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Request not found"
                )
            
            request = request_result.data[0]
            
            # Check if this is the current stage
            if request["current_stage_id"] != stage_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot act on this stage yet. Previous stages must be completed first."
                )
            
            # Update stage
            stage_update = {
                "status": StageStatus.COMPLETED.value,
                "action": action_data.action.value,
                "comments": action_data.comments,
                "action_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table("workflow_stages").update(stage_update).eq("id", stage_id).execute()
            
            # Handle rejection
            if action_data.action == StageAction.REJECTED:
                # Mark request as rejected
                self.supabase.table("requests").update({
                    "status": RequestStatus.REJECTED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "current_stage_id": None
                }).eq("id", request_id).execute()
                
                # TODO: Notify creator of rejection
                
                return {
                    "message": "Request rejected",
                    "request_id": request_id,
                    "status": RequestStatus.REJECTED,
                    "next_stage": None
                }
            
            # Get all stages for this request
            all_stages_result = self.supabase.table("workflow_stages").select("*").eq("request_id", request_id).order("order_index").execute()
            all_stages = all_stages_result.data
            
            # Find next stage
            current_order = stage["order_index"]
            next_stage = None
            
            for s in all_stages:
                if s["order_index"] == current_order + 1:
                    next_stage = s
                    break
            
            if next_stage:
                # Move to next stage
                new_status = request["status"]
                
                # Update status if moving from RECOMMEND to APPROVE stages
                if stage["stage_type"] == StageType.RECOMMEND.value and next_stage["stage_type"] == StageType.APPROVE.value:
                    new_status = RequestStatus.IN_APPROVAL.value
                
                # Update request
                self.supabase.table("requests").update({
                    "status": new_status,
                    "current_stage_id": next_stage["id"]
                }).eq("id", request_id).execute()
                
                # Update next stage to IN_PROGRESS
                self.supabase.table("workflow_stages").update({
                    "status": StageStatus.IN_PROGRESS.value
                }).eq("id", next_stage["id"]).execute()
                
                # Get next stage user info
                user_result = self.supabase.table("users").select("name, email").eq("id", next_stage["assigned_user_id"]).execute()
                user = user_result.data[0] if user_result.data else {"name": "Unknown", "email": ""}
                
                next_stage_response = WorkflowStageResponse(
                    id=next_stage["id"],
                    request_id=next_stage["request_id"],
                    stage_type=StageType(next_stage["stage_type"]),
                    assigned_user_id=next_stage["assigned_user_id"],
                    assigned_user_name=user["name"],
                    assigned_user_email=user["email"],
                    order_index=next_stage["order_index"],
                    status=StageStatus.IN_PROGRESS,
                    comments=None,
                    action=None,
                    action_at=None,
                    created_at=next_stage["created_at"]
                )
                
                # TODO: Send notification to next stage user
                
                return {
                    "message": f"Action completed. Moving to next stage.",
                    "request_id": request_id,
                    "status": new_status,
                    "next_stage": next_stage_response
                }
            else:
                # No more stages - request is approved
                self.supabase.table("requests").update({
                    "status": RequestStatus.APPROVED.value,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "current_stage_id": None
                }).eq("id", request_id).execute()
                
                # TODO: Notify creator of approval
                
                return {
                    "message": "Request approved",
                    "request_id": request_id,
                    "status": RequestStatus.APPROVED,
                    "next_stage": None
                }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to take action: {str(e)}"
            )

    async def get_pending_actions(
        self,
        user_id: str,
        stage_type_filter: Optional[StageType] = None
    ) -> PendingActionsListResponse:
        """
        Get all pending actions for a user
        
        Args:
            user_id: ID of the user
            stage_type_filter: Optional filter by stage type
            
        Returns:
            List of pending actions
        """
        try:
            # Get stages assigned to user that are IN_PROGRESS
            query = self.supabase.table("workflow_stages").select("*").eq("assigned_user_id", user_id).eq("status", StageStatus.IN_PROGRESS.value)
            
            if stage_type_filter:
                query = query.eq("stage_type", stage_type_filter.value)
            
            result = query.order("created_at").execute()
            
            stages_data = result.data if result.data else []
            
            # Format pending actions
            pending_actions = []
            recommendations_pending = 0
            approvals_pending = 0
            
            for stage in stages_data:
                # Get request info
                request_result = self.supabase.table("requests").select("*").eq("id", stage["request_id"]).execute()
                
                if not request_result.data:
                    continue
                
                request = request_result.data[0]
                
                # Get creator info
                creator_result = self.supabase.table("users").select("name, email").eq("id", request["creator_id"]).execute()
                creator = creator_result.data[0] if creator_result.data else {"name": "Unknown", "email": ""}
                
                # Calculate days pending
                submitted_at = datetime.fromisoformat(request["submitted_at"].replace("Z", "+00:00")) if request.get("submitted_at") else datetime.now(timezone.utc)
                days_pending = (datetime.now(timezone.utc) - submitted_at).days
                
                pending_actions.append(PendingActionResponse(
                    stage_id=stage["id"],
                    request_id=request["id"],
                    request_title=request["title"],
                    request_description=request.get("description"),
                    creator_name=creator["name"],
                    creator_email=creator["email"],
                    stage_type=StageType(stage["stage_type"]),
                    order_index=stage["order_index"],
                    submitted_at=request.get("submitted_at"),
                    days_pending=days_pending
                ))
                
                if stage["stage_type"] == StageType.RECOMMEND.value:
                    recommendations_pending += 1
                else:
                    approvals_pending += 1
            
            return PendingActionsListResponse(
                pending_actions=pending_actions,
                total_pending=len(pending_actions),
                recommendations_pending=recommendations_pending,
                approvals_pending=approvals_pending
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get pending actions: {str(e)}"
            )

    async def cancel_request(
        self,
        request_id: str,
        user_id: str
    ) -> RequestCancelResponse:
        """
        Cancel a request
        
        Args:
            request_id: ID of the request
            user_id: ID of the user cancelling the request
            
        Returns:
            Cancel response
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
                    detail="Only the creator can cancel the request"
                )
            
            # Check if request can be cancelled
            current_status = RequestStatus(request["status"])
            if current_status in [RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot cancel request with status {current_status.value}"
                )
            
            # Update request status
            self.supabase.table("requests").update({
                "status": RequestStatus.CANCELLED.value,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "current_stage_id": None
            }).eq("id", request_id).execute()
            
            # Mark all pending stages as SKIPPED
            self.supabase.table("workflow_stages").update({
                "status": StageStatus.SKIPPED.value
            }).eq("request_id", request_id).in_("status", [StageStatus.PENDING.value, StageStatus.IN_PROGRESS.value]).execute()
            
            # TODO: Notify all workflow participants
            
            return RequestCancelResponse(
                message="Request cancelled successfully",
                request_id=request_id,
                status=RequestStatus.CANCELLED
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel request: {str(e)}"
            )

    async def get_workflow_history(
        self,
        request_id: str,
        user_id: str
    ) -> List[WorkflowStageResponse]:
        """
        Get workflow history for a request
        
        Args:
            request_id: ID of the request
            user_id: ID of the user requesting history
            
        Returns:
            List of workflow stages in order
        """
        try:
            # Check if user has access
            has_access = await self._check_user_access(request_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this request"
                )
            
            # Get workflow stages
            result = self.supabase.table("workflow_stages").select("*").eq("request_id", request_id).order("order_index").execute()
            
            stages_data = result.data if result.data else []
            
            # Format stages with user info
            formatted_stages = []
            for stage in stages_data:
                user_result = self.supabase.table("users").select("name, email").eq("id", stage["assigned_user_id"]).execute()
                user = user_result.data[0] if user_result.data else {"name": "Unknown", "email": ""}
                
                formatted_stages.append(WorkflowStageResponse(
                    id=stage["id"],
                    request_id=stage["request_id"],
                    stage_type=StageType(stage["stage_type"]),
                    assigned_user_id=stage["assigned_user_id"],
                    assigned_user_name=user["name"],
                    assigned_user_email=user["email"],
                    order_index=stage["order_index"],
                    status=StageStatus(stage["status"]),
                    comments=stage.get("comments"),
                    action=StageAction(stage["action"]) if stage.get("action") else None,
                    action_at=stage.get("action_at"),
                    created_at=stage["created_at"]
                ))
            
            return formatted_stages
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get workflow history: {str(e)}"
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
