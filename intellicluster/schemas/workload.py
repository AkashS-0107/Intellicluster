"""
Pydantic schemas for Workload operations.
Maintains schema compatibility with machine learning model feature definitions.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field

from intellicluster.core.constants import WorkloadPriority, WorkloadStatus, WorkloadType
from intellicluster.schemas.common import BaseSchema


class WorkloadCreateSchema(BaseSchema):
    """Schema for submitting a new workload or compute job."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Descriptive identifier for the task",
        examples=["matrix-multiplication-job-01"],
    )
    cluster_id: Optional[str] = Field(
        default=None,
        description="Target cluster ID to run this workload within",
    )
    workload_type: WorkloadType = Field(
        default=WorkloadType.BATCH,
        description="Workload profile category",
    )

    # Resource Requirements (ML feature inputs)
    cpu_cores_requested: float = Field(
        gt=0.0,
        description="CPU cores required for execution",
        examples=[2.0],
    )
    memory_mb_requested: float = Field(
        gt=0.0,
        description="RAM required in Megabytes",
        examples=[4096.0],
    )
    storage_gb_requested: float = Field(
        default=0.0,
        ge=0.0,
        description="Disk space required in Gigabytes",
        examples=[10.0],
    )
    network_mbps_requested: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated network bandwidth demand in Mbps",
        examples=[50.0],
    )
    max_latency_tolerance_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Maximum network round-trip latency permitted (ms)",
        examples=[100.0],
    )
    estimated_duration_sec: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Anticipated execution duration in seconds",
        examples=[300.0],
    )

    # Priority & Fault Tolerance
    priority: WorkloadPriority = Field(
        default=WorkloadPriority.NORMAL,
        description="Scheduling urgency level",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts upon failure",
    )


class WorkloadUpdateSchema(BaseSchema):
    """Schema for updating workload properties or reassigning nodes."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    assigned_node_id: Optional[str] = None
    priority: Optional[WorkloadPriority] = None
    max_retries: Optional[int] = Field(default=None, ge=0, le=10)


class WorkloadTransitionSchema(BaseSchema):
    """Schema for transitioning workload lifecycle state."""

    target_status: WorkloadStatus
    failure_reason: Optional[str] = None


class WorkloadResponseSchema(BaseSchema):
    """Complete workload representation response schema."""

    id: str
    cluster_id: Optional[str] = None
    assigned_node_id: Optional[str] = None
    name: str
    workload_type: WorkloadType

    # Demands
    cpu_cores_requested: float = Field(gt=0.0)
    memory_mb_requested: float = Field(gt=0.0)
    storage_gb_requested: float = Field(ge=0.0)
    network_mbps_requested: float = Field(ge=0.0)
    max_latency_tolerance_ms: Optional[float] = Field(default=None, ge=0.0)
    estimated_duration_sec: Optional[float] = Field(default=None, gt=0.0)

    # Priority & Status
    priority: WorkloadPriority
    status: WorkloadStatus
    failure_reason: Optional[str] = None
    retry_count: int = Field(ge=0)
    max_retries: int = Field(ge=0)

    # Timestamps
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime
