"""
Pydantic schemas for Cluster operations.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field

from intellicluster.core.constants import ClusterStatus
from intellicluster.schemas.common import BaseSchema


class ClusterCreateSchema(BaseSchema):
    """Schema for creating a new cluster."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Unique cluster identifier name",
        examples=["primary-compute-cluster"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Human-readable description of cluster purpose",
    )
    status: ClusterStatus = Field(
        default=ClusterStatus.ACTIVE,
        description="Initial operational status",
    )


class ClusterUpdateSchema(BaseSchema):
    """Schema for updating an existing cluster."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    status: Optional[ClusterStatus] = None


class ClusterResponseSchema(BaseSchema):
    """Schema for serializing cluster details."""

    id: str
    name: str
    description: Optional[str] = None
    status: ClusterStatus
    created_at: datetime
    updated_at: datetime


class ClusterCapacitySummary(BaseSchema):
    """Aggregated capacity and utilization summary for a cluster."""

    cluster_id: str
    cluster_name: str
    total_nodes: int = Field(ge=0)
    ready_nodes: int = Field(ge=0)
    total_cpu_cores: float = Field(ge=0.0)
    allocated_cpu_cores: float = Field(ge=0.0)
    allocatable_cpu_cores: float = Field(ge=0.0)
    total_memory_mb: float = Field(ge=0.0)
    allocated_memory_mb: float = Field(ge=0.0)
    allocatable_memory_mb: float = Field(ge=0.0)
    average_cpu_usage_pct: float = Field(ge=0.0, le=100.0)
    average_memory_usage_pct: float = Field(ge=0.0, le=100.0)
    active_workload_count: int = Field(ge=0)
