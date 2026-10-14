"""
API routes for Workload lifecycle management, scheduling, and state transitions.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from intellicluster.api.deps import get_db
from intellicluster.core.constants import WorkloadPriority, WorkloadStatus
from intellicluster.schemas.workload import (
    WorkloadCreateSchema,
    WorkloadResponseSchema,
    WorkloadTransitionSchema,
    WorkloadUpdateSchema,
)
from intellicluster.services.workload_service import WorkloadService

router = APIRouter(prefix="/workloads", tags=["Workloads"])


@router.post(
    "/",
    response_model=WorkloadResponseSchema,
    status_code=201,
    summary="Submit a new workload",
    description=(
        "Submits a new compute workload into the PENDING state with defined "
        "resource requirements and scheduling constraints."
    ),
)
def create_workload(
    data: WorkloadCreateSchema,
    db: Session = Depends(get_db),
):
    workload = WorkloadService.create_workload(db, data)
    return workload


@router.get(
    "/",
    response_model=list[WorkloadResponseSchema],
    summary="List workloads",
    description="Returns a list of workloads with optional filtering by cluster, node, status, and priority.",
)
def list_workloads(
    cluster_id: Optional[str] = Query(default=None, description="Filter by cluster ID"),
    assigned_node_id: Optional[str] = Query(default=None, description="Filter by assigned node ID"),
    status: Optional[WorkloadStatus] = Query(default=None, description="Filter by workload status"),
    priority: Optional[WorkloadPriority] = Query(default=None, description="Filter by priority level"),
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum items to return"),
    db: Session = Depends(get_db),
):
    workloads = WorkloadService.list_workloads(
        db,
        cluster_id=cluster_id,
        assigned_node_id=assigned_node_id,
        status=status,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    return workloads


@router.get(
    "/{workload_id}",
    response_model=WorkloadResponseSchema,
    summary="Get workload details",
    description="Retrieves detailed information for a specific workload by ID.",
)
def get_workload(
    workload_id: str,
    db: Session = Depends(get_db),
):
    workload = WorkloadService.get_workload_by_id(db, workload_id)
    return workload


@router.put(
    "/{workload_id}",
    response_model=WorkloadResponseSchema,
    summary="Update workload",
    description="Updates workload parameters such as name, priority, or maximum retries.",
)
def update_workload(
    workload_id: str,
    data: WorkloadUpdateSchema,
    db: Session = Depends(get_db),
):
    workload = WorkloadService.update_workload(db, workload_id, data)
    return workload


@router.post(
    "/{workload_id}/schedule",
    response_model=WorkloadResponseSchema,
    summary="Schedule a pending workload",
    description=(
        "Triggers scheduling placement for a PENDING workload using the active "
        "scheduling strategy. Evaluates candidate nodes for resource fitness "
        "and assigns the workload to the optimal node."
    ),
)
def schedule_workload(
    workload_id: str,
    db: Session = Depends(get_db),
):
    workload = WorkloadService.schedule_pending_workload(db, workload_id)
    return workload


@router.post(
    "/{workload_id}/status",
    response_model=WorkloadResponseSchema,
    summary="Transition workload status",
    description=(
        "Transitions a workload through its lifecycle state machine. "
        "Valid transitions are enforced (e.g. SCHEDULED → RUNNING → COMPLETED)."
    ),
)
def transition_workload_status(
    workload_id: str,
    data: WorkloadTransitionSchema,
    db: Session = Depends(get_db),
):
    workload = WorkloadService.transition_workload_status(
        db, workload_id, data.target_status, data.failure_reason,
    )
    return workload


@router.post(
    "/{workload_id}/cancel",
    response_model=WorkloadResponseSchema,
    summary="Cancel a workload",
    description="Cancels a PENDING, SCHEDULED, or RUNNING workload.",
)
def cancel_workload(
    workload_id: str,
    db: Session = Depends(get_db),
):
    workload = WorkloadService.cancel_workload(db, workload_id)
    return workload
