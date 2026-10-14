"""
Node ORM entity representing a physical, virtual, or containerized compute server.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from intellicluster.core.constants import NodeStatus
from intellicluster.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from intellicluster.models.cluster import Cluster
    from intellicluster.models.telemetry import TelemetrySnapshot
    from intellicluster.models.workload import Workload


class Node(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Node/Server database model."""

    __tablename__ = "nodes"

    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("clusters.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    hostname: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=NodeStatus.READY.value,
        index=True,
        nullable=False,
    )

    # Hardware Capacities
    cpu_cores: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Total CPU core capacity",
    )
    memory_mb: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Total RAM capacity in Megabytes",
    )
    storage_gb: Mapped[float] = mapped_column(
        Float,
        default=100.0,
        nullable=False,
        doc="Total local disk storage in Gigabytes",
    )
    network_bandwidth_mbps: Mapped[float] = mapped_column(
        Float,
        default=1000.0,
        nullable=False,
        doc="Network interface bandwidth capacity in Mbps",
    )

    # Current Resource Utilization & Health (Latest cached snapshot)
    current_cpu_usage_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Current CPU utilization percentage (0.0 - 100.0)",
    )
    current_memory_usage_mb: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Current memory used in Megabytes",
    )
    current_disk_usage_gb: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Current disk storage used in Gigabytes",
    )
    current_network_tx_mbps: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Outbound transmission rate in Mbps",
    )
    current_network_rx_mbps: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Inbound reception rate in Mbps",
    )
    current_network_latency_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Network ping/round-trip latency in milliseconds",
    )
    active_connections: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of active network/socket connections",
    )

    # Health & Risk Scoring
    health_score: Mapped[float] = mapped_column(
        Float,
        default=100.0,
        nullable=False,
        doc="Composite health score (0.0 to 100.0, higher is healthier)",
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="ML risk/failure probability placeholder (0.0 to 1.0, lower is safer)",
    )

    # Operational State & Heartbeat
    active_workload_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of currently running workloads assigned to this node",
    )
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
        doc="UTC timestamp of the most recent heartbeat report",
    )
    is_cordoned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="If True, prevents new workload scheduling while allowing existing tasks to drain",
    )

    # Relationships
    cluster: Mapped[Optional["Cluster"]] = relationship(
        "Cluster",
        back_populates="nodes",
    )
    workloads: Mapped[list["Workload"]] = relationship(
        "Workload",
        back_populates="assigned_node",
    )
    telemetry_snapshots: Mapped[list["TelemetrySnapshot"]] = relationship(
        "TelemetrySnapshot",
        back_populates="node",
        cascade="all, delete-orphan",
        order_by="desc(TelemetrySnapshot.recorded_at)",
    )

    def __repr__(self) -> str:
        return (
            f"<Node(id='{self.id}', hostname='{self.hostname}', "
            f"status='{self.status}', health={self.health_score:.1f})>"
        )
