"""
TelemetrySnapshot ORM entity representing historical time-series performance data.
Append-only log designed for operational observability and telemetry analysis.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from intellicluster.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from intellicluster.models.node import Node


class TelemetrySnapshot(Base, UUIDPrimaryKeyMixin):
    """Append-only time-series telemetry snapshot model."""

    __tablename__ = "telemetry_snapshots"

    node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Resource Utilization Metrics
    cpu_usage_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="CPU utilization percentage at sample time",
    )
    memory_usage_mb: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Used memory in Megabytes",
    )
    memory_usage_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Used memory percentage",
    )
    disk_usage_gb: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Used disk in Gigabytes",
    )
    disk_usage_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Used disk percentage",
    )
    network_rx_mbps: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Inbound network rate in Mbps",
    )
    network_tx_mbps: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Outbound network rate in Mbps",
    )
    network_latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Round-trip latency to control plane / gateway in ms",
    )
    active_connections: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of active network connections",
    )
    running_processes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Count of currently active OS processes/tasks",
    )
    temperature_celsius: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Hardware CPU/package temperature in Celsius if available",
    )
    reported_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        doc="Node status reported by node agent at snapshot time",
    )
    workload: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Operational workload demand metric",
    )
    resource_allocation: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Capacity allocation ratio percentage",
    )

    # Relationships
    node: Mapped["Node"] = relationship(
        "Node",
        back_populates="telemetry_snapshots",
    )

    __table_args__ = (
        Index("idx_telemetry_node_recorded_at", "node_id", "recorded_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<TelemetrySnapshot(id='{self.id}', node_id='{self.node_id}', "
            f"cpu={self.cpu_usage_pct:.1f}%, time='{self.recorded_at.isoformat()}')>"
        )
