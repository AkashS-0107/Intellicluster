"""
API routes for Cluster management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from intellicluster.api.deps import get_db
from intellicluster.core.constants import ClusterStatus
from intellicluster.schemas.cluster import (
    ClusterCapacitySummary,
    ClusterCreateSchema,
    ClusterResponseSchema,
    ClusterUpdateSchema,
)
from intellicluster.services.cluster_service import ClusterService

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.post(
    "/",
    response_model=ClusterResponseSchema,
    status_code=201,
    summary="Create a new cluster",
    description="Creates a new compute cluster with a unique name and optional description.",
)
def create_cluster(
    data: ClusterCreateSchema,
    db: Session = Depends(get_db),
):
    cluster = ClusterService.create_cluster(db, data)
    return cluster


@router.get(
    "/",
    response_model=list[ClusterResponseSchema],
    summary="List clusters",
    description="Returns a list of clusters with optional status filtering and pagination.",
)
def list_clusters(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum items to return"),
    status: Optional[ClusterStatus] = Query(default=None, description="Filter by cluster status"),
    db: Session = Depends(get_db),
):
    clusters = ClusterService.list_clusters(db, skip=skip, limit=limit, status=status)
    return clusters


@router.get(
    "/{cluster_id}",
    response_model=ClusterResponseSchema,
    summary="Get cluster details",
    description="Retrieves detailed information for a specific cluster by ID.",
)
def get_cluster(
    cluster_id: str,
    db: Session = Depends(get_db),
):
    cluster = ClusterService.get_cluster_by_id(db, cluster_id)
    return cluster


@router.put(
    "/{cluster_id}",
    response_model=ClusterResponseSchema,
    summary="Update cluster",
    description="Updates cluster metadata such as name, description, or operational status.",
)
def update_cluster(
    cluster_id: str,
    data: ClusterUpdateSchema,
    db: Session = Depends(get_db),
):
    cluster = ClusterService.update_cluster(db, cluster_id, data)
    return cluster


@router.get(
    "/{cluster_id}/capacity",
    response_model=ClusterCapacitySummary,
    summary="Get cluster capacity summary",
    description=(
        "Calculates aggregate hardware capacity, allocated resources, "
        "and utilization metrics across all nodes in the cluster."
    ),
)
def get_cluster_capacity(
    cluster_id: str,
    db: Session = Depends(get_db),
):
    return ClusterService.calculate_cluster_capacity(db, cluster_id)
