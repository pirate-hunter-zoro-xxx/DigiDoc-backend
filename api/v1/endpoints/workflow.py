"""
Workflow API Endpoints
"""
from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from core.dependencies import get_current_active_user
from models.user import UserResponse
from models.request import (
    WorkflowStageUpdate, WorkflowStageResponse, RequestSubmitResponse,
    RequestCancelResponse, PendingActionsListResponse, StageType
)
from services.workflow_service import WorkflowService

router = APIRouter()


@router.post(
    "/requests/{request_id}/submit",
    response_model=RequestSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit request for review",
    description="Submit a request to start the workflow process. Moves from DRAFT to SUBMITTED/IN_REVIEW."
)
async def submit_request(
    request_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Submit a request for review
    
    - Only creator can submit
    - Only DRAFT requests can be submitted
    - Must have workflow stages defined
    - Notifies first person in workflow
    - Returns next stage information
    """
    service = WorkflowService()
    return await service.submit_request(request_id, current_user.id)


@router.post(
    "/requests/{request_id}/cancel",
    response_model=RequestCancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel request",
    description="Cancel a request at any stage before completion."
)
async def cancel_request(
    request_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Cancel a request
    
    - Only creator can cancel
    - Cannot cancel APPROVED, REJECTED, or CANCELLED requests
    - Marks all pending stages as SKIPPED
    - Notifies all workflow participants
    """
    service = WorkflowService()
    return await service.cancel_request(request_id, current_user.id)


@router.get(
    "/pending",
    response_model=PendingActionsListResponse,
    summary="Get pending actions",
    description="Get all requests waiting for action by the current user"
)
async def get_pending_actions(
    stage_type: Optional[StageType] = Query(None, description="Filter by stage type (RECOMMEND or APPROVE)"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get all pending actions for current user
    
    - Shows requests where user needs to take action
    - Includes request details and workflow context
    - Can filter by stage type (recommendations vs approvals)
    - Shows days pending for each action
    """
    service = WorkflowService()
    return await service.get_pending_actions(current_user.id, stage_type)


@router.post(
    "/stages/{stage_id}/action",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Take action on workflow stage",
    description="Recommend, approve, or reject a workflow stage"
)
async def take_action(
    stage_id: str,
    action_data: WorkflowStageUpdate,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Take action on a workflow stage
    
    - **action**: RECOMMENDED (for RECOMMEND stages) or APPROVED/REJECTED (for APPROVE stages)
    - **comments**: Optional comments explaining the decision
    
    Actions:
    - RECOMMEND stages: Can only use RECOMMENDED action
    - APPROVE stages: Can use APPROVED or REJECTED action
    - REJECTED: Immediately rejects the entire request
    - APPROVED: Moves to next stage or completes the request
    
    Returns next stage information if workflow continues.
    """
    service = WorkflowService()
    return await service.take_action(stage_id, current_user.id, action_data)


@router.get(
    "/requests/{request_id}/history",
    response_model=list[WorkflowStageResponse],
    summary="Get workflow history",
    description="Get complete workflow history for a request"
)
async def get_workflow_history(
    request_id: str,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get workflow history for a request
    
    - Shows all workflow stages in order
    - Includes actions taken, comments, and timestamps
    - Shows current status of each stage
    - Available to creator and workflow participants
    """
    service = WorkflowService()
    return await service.get_workflow_history(request_id, current_user.id)
