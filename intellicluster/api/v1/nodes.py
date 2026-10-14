"""
API routes for Node management, heartbeats, cordoning, and capacity inspection.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from intellicluster.api.deps import get_db
from intellicluster.core.constants import NodeStatus
from intellicluster.schemas.node import (
    NodeCapacitySummary,
    NodeRegisterSchema,
    NodeResponseSchema,
    NodeUpdateSchema,
)
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.services.node_service import NodeService

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.post(
    "/",
    response_model=NodeResponseSchema,
    status_code=201,
    summary="Register a new node",
    description="Registers a new compute node with hardware capacity specifications.",
)
def register_node(
    data: NodeRegisterSchema,
    db: Session = Depends(get_db),
):
    node = NodeService.register_node(db, data)
    return node


@router.get(
    "/",
    response_model=list[NodeResponseSchema],
    summary="List nodes",
    description="Returns a list of nodes with optional cluster and status filtering.",
)
def list_nodes(
    cluster_id: Optional[str] = Query(default=None, description="Filter by cluster ID"),
    status: Optional[NodeStatus] = Query(default=None, description="Filter by node status"),
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum items to return"),
    db: Session = Depends(get_db),
):
    nodes = NodeService.list_nodes(
        db, cluster_id=cluster_id, status=status, skip=skip, limit=limit,
    )
    return nodes


@router.get(
    "/{node_id}",
    response_model=NodeResponseSchema,
    summary="Get node details",
    description="Retrieves detailed information for a specific node by ID.",
)
def get_node(
    node_id: str,
    db: Session = Depends(get_db),
):
    node = NodeService.get_node_by_id(db, node_id)
    return node


@router.put(
    "/{node_id}",
    response_model=NodeResponseSchema,
    summary="Update node",
    description="Updates node metadata, cluster attachment, or administrative status.",
)
def update_node(
    node_id: str,
    data: NodeUpdateSchema,
    db: Session = Depends(get_db),
):
    node = NodeService.update_node(db, node_id, data)
    return node


@router.post(
    "/{node_id}/heartbeat",
    response_model=NodeResponseSchema,
    summary="Process node heartbeat",
    description=(
        "Receives a heartbeat report with live telemetry metrics from a node agent. "
        "Updates the node's cached metrics, recalculates its deterministic health score, "
        "evaluates automatic status transitions, and persists a telemetry snapshot."
    ),
)
def process_heartbeat(
    node_id: str,
    data: TelemetryCreateSchema,
    db: Session = Depends(get_db),
):
    node = NodeService.process_heartbeat(db, node_id, data)
    return node


@router.post(
    "/{node_id}/cordon",
    response_model=NodeResponseSchema,
    summary="Cordon node",
    description=(
        "Cordons a node to prevent new workload scheduling. "
        "Existing workloads are not affected."
    ),
)
def cordon_node(
    node_id: str,
    db: Session = Depends(get_db),
):
    node = NodeService.cordon_node(db, node_id)
    return node


@router.post(
    "/{node_id}/uncordon",
    response_model=NodeResponseSchema,
    summary="Uncordon node",
    description="Uncordons a previously cordoned node to re-allow workload scheduling.",
)
def uncordon_node(
    node_id: str,
    db: Session = Depends(get_db),
):
    node = NodeService.uncordon_node(db, node_id)
    return node


@router.get(
    "/{node_id}/capacity",
    response_model=NodeCapacitySummary,
    summary="Get node allocatable capacity",
    description=(
        "Calculates total, allocated, and allocatable CPU and memory for a node, "
        "considering active workloads and administrative state."
    ),
)
def get_node_capacity(
    node_id: str,
    db: Session = Depends(get_db),
):
    return NodeService.get_allocatable_capacity(db, node_id)
