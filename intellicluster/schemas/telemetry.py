"""
Pydantic schemas for Telemetry ingestion, querying, and cluster-wide metrics.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field

from intellicluster.core.constants import NodeStatus
from intellicluster.schemas.common import BaseSchema


class TelemetryCreateSchema(BaseSchema):
    """Payload for submitting a periodic telemetry heartbeat from a node agent."""

    cpu_usage_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Current CPU usage percentage",
        examples=[45.2],
    )
    memory_usage_mb: float = Field(
        ge=0.0,
        description="Current memory used in Megabytes",
        examples=[8192.0],
    )
    memory_usage_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Current memory used percentage",
        examples=[50.0],
    )
    disk_usage_gb: float = Field(
        ge=0.0,
        description="Current disk storage used in Gigabytes",
        examples=[120.5],
    )
    disk_usage_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Current disk storage used percentage",
        examples=[24.1],
    )
    network_rx_mbps: float = Field(
        ge=0.0,
        description="Inbound network traffic rate in Mbps",
        examples=[12.4],
    )
    network_tx_mbps: float = Field(
        ge=0.0,
        description="Outbound network traffic rate in Mbps",
        examples=[8.1],
    )
    network_latency_ms: float = Field(
        ge=0.0,
        description="Round-trip ping/latency in milliseconds",
        examples=[4.2],
    )
    active_connections: int = Field(
        default=0,
        ge=0,
        description="Number of active network connections",
        examples=[18],
    )
    running_processes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of currently running processes/threads",
    )
    temperature_celsius: Optional[float] = Field(
        default=None,
        description="Hardware package temperature in Celsius",
        examples=[54.0],
    )
    reported_status: NodeStatus = Field(
        default=NodeStatus.READY,
        description="Current node operational self-assessment",
    )
    workload: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Operational workload demand metric matching training distribution",
        examples=[92.5],
    )
    resource_allocation: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Capacity allocation ratio percentage matching training distribution",
        examples=[60.0],
    )


class TelemetryResponseSchema(BaseSchema):
    """Schema for serializing a single telemetry snapshot."""

    id: str
    node_id: str
    recorded_at: datetime

    cpu_usage_pct: float = Field(ge=0.0, le=100.0)
    memory_usage_mb: float = Field(ge=0.0)
    memory_usage_pct: float = Field(ge=0.0, le=100.0)
    disk_usage_gb: float = Field(ge=0.0)
    disk_usage_pct: float = Field(ge=0.0, le=100.0)
    network_rx_mbps: float = Field(ge=0.0)
    network_tx_mbps: float = Field(ge=0.0)
    network_latency_ms: float = Field(ge=0.0)
    active_connections: int = Field(ge=0)
    running_processes: Optional[int] = None
    temperature_celsius: Optional[float] = None
    reported_status: NodeStatus
    workload: Optional[float] = None
    resource_allocation: Optional[float] = None


class AggregatedMetricsSummary(BaseSchema):
    """Aggregated telemetry metrics for a cluster or group of nodes."""

    cluster_id: Optional[str] = None
    total_reporting_nodes: int = Field(ge=0)
    avg_cpu_usage_pct: float = Field(ge=0.0, le=100.0)
    max_cpu_usage_pct: float = Field(ge=0.0, le=100.0)
    avg_memory_usage_pct: float = Field(ge=0.0, le=100.0)
    max_memory_usage_pct: float = Field(ge=0.0, le=100.0)
    avg_latency_ms: float = Field(ge=0.0)
    total_active_connections: int = Field(ge=0)
    recorded_at: datetime


class NodeHistoryReadinessSchema(BaseSchema):
    """Readiness breakdown of historical hourly telemetry for LSTM forecasting."""

    node_id: str
    is_ready: bool
    valid_hourly_observations: int
    required_observations: int = 168
    readiness_percentage: float
    total_raw_snapshots: int
    earliest_usable_timestamp: Optional[datetime] = None
    latest_usable_timestamp: Optional[datetime] = None
    missing_intervals_count: int = 0
    missing_ranges: list[str] = Field(default_factory=list)
    validation_reason: str
    estimated_hours_remaining: float
    collector_active: bool = False
    is_simulated: bool = False
    feature_readiness: dict[str, bool] = Field(default_factory=dict)


class SimulatorStatusSchema(BaseSchema):
    """Status of the opt-in development/demo telemetry collection simulator."""

    is_running: bool
    interval_seconds: int
    target_node_id: Optional[str] = None
    snapshots_emitted: int
    started_at: Optional[datetime] = None
    collector_mode: str = "opt_in_development_simulator"


class SimulatorStartRequestSchema(BaseSchema):
    """Configuration for launching the opt-in background telemetry simulator."""

    interval_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Heartbeat generation interval in seconds",
    )
    target_node_id: Optional[str] = Field(
        default=None,
        description="Optional target node ID (None simulates all ready nodes)",
    )
