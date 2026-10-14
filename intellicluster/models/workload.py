"""
Workload ORM entity representing compute tasks and scheduled jobs.
Designed for feature compatibility with cluster scheduling strategies.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from intellicluster.core.constants import WorkloadPriority, WorkloadStatus, WorkloadType
from intellicluster.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from intellicluster.models.cluster import Cluster
    from intellicluster.models.node import Node


class Workload(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Workload database model."""

    __tablename__ = "workloads"

    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("clusters.id"),
        index=True,
        nullable=True,
    )
    assigned_node_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("nodes.id"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    workload_type: Mapped[str] = mapped_column(
        String(50),
        default=WorkloadType.BATCH.value,
        nullable=False,
    )

    # Resource Requirements (ML feature compatible)
    cpu_cores_requested: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Required CPU cores",
    )
    memory_mb_requested: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Required RAM in Megabytes",
    )
    storage_gb_requested: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Required disk storage in Gigabytes",
    )
    network_mbps_requested: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Required network bandwidth in Mbps",
    )
    max_latency_tolerance_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Maximum acceptable latency SLA in ms",
    )
    estimated_duration_sec: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Estimated workload execution duration in seconds",
    )

    # Priority & Scheduling State
    priority: Mapped[str] = mapped_column(
        String(20),
        default=WorkloadPriority.NORMAL.value,
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=WorkloadStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed explanation of failure if status is FAILED",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    # Lifecycle Timestamps
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    cluster: Mapped[Optional["Cluster"]] = relationship(
        "Cluster",
        back_populates="workloads",
    )
    assigned_node: Mapped[Optional["Node"]] = relationship(
        "Node",
        back_populates="workloads",
    )

    def __repr__(self) -> str:
        return (
            f"<Workload(id='{self.id}', name='{self.name}', "
            f"status='{self.status}', node='{self.assigned_node_id}')>"
        )
