"""
NEXUS V11.5 CORTEX - Workflow Control Endpoints
V11.6 KEYMAKER - Optional authentication support

Enables task execution control for CEREBRO UI:
- POST /api/workflow/start : Start a workflow (non-blocking)
- GET /api/workflow/{id} : Get workflow status
- POST /api/workflow/{id}/stop : Stop a running workflow

Authentication:
- V11.6: Optional auth - uses token tenant_id if provided, falls back to query param
- Production: Change to require_auth for mandatory authentication

Author: Claude (NEXUS V11.5 CORTEX)
Date: 2025-12-15
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from ..deps import AuthenticatedUser, get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory workflow registry (TODO: Move to Redis for multi-instance support)
_active_workflows: Dict[str, Dict[str, Any]] = {}


class WorkflowStartRequest(BaseModel):
    """Request body for starting a workflow."""
    task: str
    complexity: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Response model for workflow operations."""
    workflow_id: str
    status: str
    task: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


def _get_orchestrator():
    """
    Lazy load Orchestrator for complex tasks.

    Creates a new OrchestratorV7 instance with proper configuration.
    """
    try:
        from core.orchestration_v7 import OrchestratorV7
        from core.config import Config

        config = Config()
        gemini_info = {"model": config.gemini_pro_model, "provider": "gemini"}
        claude_info = {"model": config.claude_opus_model, "provider": "claude"}
        return OrchestratorV7(config.workspace_path, config, gemini_info, claude_info)
    except Exception as e:
        logger.error(f"Failed to create orchestrator: {e}")
        raise


@router.post("/start")
async def start_workflow(
    body: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    user: Optional[AuthenticatedUser] = Depends(get_current_user_optional),
    tenant_id: Optional[str] = Query(None, description="Tenant identifier (fallback if no auth)"),
    workspace_id: str = Query("default", description="Workspace identifier"),
) -> Dict[str, str]:
    """
    Start a workflow (non-blocking).

    Creates a background task to process the user's request.
    Returns immediately with a workflow_id for status tracking.

    Args:
        body: WorkflowStartRequest with task description
        background_tasks: FastAPI background task manager
        tenant_id: Tenant identifier (required)
        workspace_id: Workspace identifier

    Returns:
        {"workflow_id": "...", "status": "pending"}
    """
    # V11.6: Resolve tenant_id from auth token or query param
    actual_tenant_id = user.tenant_id if user else tenant_id
    if not actual_tenant_id:
        raise HTTPException(400, "tenant_id required (via auth token or query param)")

    actual_workspace_id = user.workspace_id if user else workspace_id

    workflow_id = str(uuid4())[:12]

    _active_workflows[workflow_id] = {
        "status": "pending",
        "task": body.task,
        "tenant_id": actual_tenant_id,
        "workspace_id": actual_workspace_id,
        "complexity": body.complexity,
        "result": None,
        "error": None,
    }

    async def run_workflow():
        """Background task to execute the workflow."""
        try:
            _active_workflows[workflow_id]["status"] = "running"
            logger.info(f"[CORTEX] Workflow {workflow_id} started: {body.task[:50]}...")

            # Get orchestrator and process turn
            orchestrator = _get_orchestrator()

            # V11.5: Use sync process_turn (async available but requires more setup)
            # TODO: Switch to process_turn_async when CancellationToken is integrated
            result = orchestrator.process_turn(body.task)

            _active_workflows[workflow_id]["status"] = "completed"
            _active_workflows[workflow_id]["result"] = result
            logger.info(f"[CORTEX] Workflow {workflow_id} completed")

        except Exception as e:
            _active_workflows[workflow_id]["status"] = "failed"
            _active_workflows[workflow_id]["error"] = str(e)
            logger.error(f"[CORTEX] Workflow {workflow_id} failed: {e}")

    background_tasks.add_task(run_workflow)

    logger.info(f"[CORTEX] Workflow {workflow_id} queued for tenant={actual_tenant_id}")
    return {"workflow_id": workflow_id, "status": "pending"}


@router.get("/{workflow_id}")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """
    Get workflow status.

    Args:
        workflow_id: The workflow ID from start_workflow

    Returns:
        Workflow state including status, task, result, error

    Raises:
        404: Workflow not found
    """
    if workflow_id not in _active_workflows:
        raise HTTPException(404, f"Workflow {workflow_id} not found")

    workflow = _active_workflows[workflow_id]
    return {
        "workflow_id": workflow_id,
        "status": workflow["status"],
        "task": workflow["task"],
        "result": workflow.get("result"),
        "error": workflow.get("error"),
    }


@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str) -> Dict[str, str]:
    """
    Stop a running workflow.

    Currently marks workflow as cancelled. Full CancellationToken
    integration is planned for V11.6.

    Args:
        workflow_id: The workflow ID to stop

    Returns:
        {"workflow_id": "...", "status": "cancelled"}

    Raises:
        404: Workflow not found
        400: Workflow not in stoppable state
    """
    if workflow_id not in _active_workflows:
        raise HTTPException(404, f"Workflow {workflow_id} not found")

    workflow = _active_workflows[workflow_id]

    if workflow["status"] not in ("pending", "running"):
        raise HTTPException(
            400,
            f"Workflow {workflow_id} is {workflow['status']}, cannot stop"
        )

    # Mark as cancelled
    # TODO: Integrate CancellationToken for graceful cancellation
    workflow["status"] = "cancelled"
    logger.info(f"[CORTEX] Workflow {workflow_id} cancelled")

    return {"workflow_id": workflow_id, "status": "cancelled"}


@router.get("/")
async def list_workflows(
    user: Optional[AuthenticatedUser] = Depends(get_current_user_optional),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant (fallback if no auth)"),
    status: Optional[str] = Query(None, description="Filter by status"),
) -> Dict[str, list]:
    """
    List all workflows (optionally filtered).

    Args:
        tenant_id: Optional tenant filter
        status: Optional status filter (pending, running, completed, failed, cancelled)

    Returns:
        {"workflows": [...list of workflow summaries...]}
    """
    # V11.6: Resolve tenant_id from auth token or query param
    actual_tenant_id = user.tenant_id if user else tenant_id

    workflows = []

    for wf_id, wf_data in _active_workflows.items():
        # Apply filters
        if actual_tenant_id and wf_data.get("tenant_id") != actual_tenant_id:
            continue
        if status and wf_data.get("status") != status:
            continue

        workflows.append({
            "workflow_id": wf_id,
            "status": wf_data["status"],
            "task": wf_data["task"][:50] + "..." if len(wf_data["task"]) > 50 else wf_data["task"],
            "tenant_id": wf_data.get("tenant_id"),
        })

    return {"workflows": workflows}
