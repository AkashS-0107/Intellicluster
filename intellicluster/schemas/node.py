"""
Pydantic schemas for Node/Server operations.
"""

import ipaddress
from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator

from intellicluster.core.constants import NodeStatus
from intellicluster.schemas.common import BaseSchema


class NodeRegisterSchema(BaseSchema):
    """Schema for registering a new server/node in the cluster."""

    hostname: str = Field(
        min_length=1,
        max_length=255,
        description="Unique hostname or FQDN for the node",
        examples=["node-prod-01.local"],
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="IPv4 or IPv6 address of the node",
        examples=["192.168.1.101"],
    )
    cluster_id: Optional[str] = Field(
        default=None,
        description="ID of the cluster to attach this node to",
    )
    cpu_cores: float = Field(
        gt=0.0,
        description="Total CPU cores available on the hardware",
        examples=[8.0],
    )
    memory_mb: float = Field(
        gt=0.0,
        description="Total RAM capacity in Megabytes",
        examples=[16384.0],
    )
    storage_gb: float = Field(
        default=100.0,
        gt=0.0,
        description="Total local disk storage capacity in Gigabytes",
        examples=[500.0],
    )
    network_bandwidth_mbps: float = Field(
        default=1000.0,
        gt=0.0,
        description="Rated network interface bandwidth in Mbps",
        examples=[1000.0],
    )

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value.strip() == "":
            return None
        # Use Pydantic's IPvAnyAddress parser logic for validation
        try:
            ipaddress.ip_address(value)
            return value
        except Exception as e:
            raise ValueError(f"Invalid IP address format: '{value}'") from e


class NodeUpdateSchema(BaseSchema):
    """Schema for updating node configuration or administrative status."""

    hostname: Optional[str] = Field(default=None, min_length=1, max_length=255)
    ip_address: Optional[str] = None
    cluster_id: Optional[str] = None
    status: Optional[NodeStatus] = None
    is_cordoned: Optional[bool] = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value.strip() == "":
            return None
        try:
            ipaddress.ip_address(value)
            return value
        except Exception as e:
            raise ValueError(f"Invalid IP address format: '{value}'") from e


class NodeResponseSchema(BaseSchema):
    """Complete node representation response schema."""

    id: str
    cluster_id: Optional[str] = None
    hostname: str
    ip_address: Optional[str] = None
    status: NodeStatus

    # Hardware Capacities
    cpu_cores: float = Field(gt=0.0)
    memory_mb: float = Field(gt=0.0)
    storage_gb: float = Field(gt=0.0)
    network_bandwidth_mbps: float = Field(gt=0.0)

    # Dynamic / Cached Metrics
    current_cpu_usage_pct: float = Field(ge=0.0, le=100.0)
    current_memory_usage_mb: float = Field(ge=0.0)
    current_disk_usage_gb: float = Field(ge=0.0)
    current_network_tx_mbps: float = Field(ge=0.0)
    current_network_rx_mbps: float = Field(ge=0.0)
    current_network_latency_ms: float = Field(ge=0.0)
    active_connections: int = Field(ge=0)

    # Health & Scoring
    health_score: float = Field(ge=0.0, le=100.0)
    risk_score: float = Field(ge=0.0, le=1.0)

    # Operational Status
    active_workload_count: int = Field(ge=0)
    last_heartbeat: datetime
    is_cordoned: bool

    created_at: datetime
    updated_at: datetime


class NodeCapacitySummary(BaseSchema):
    """Allocatable vs allocated capacity breakdown for a node."""

    node_id: str
    hostname: str
    status: NodeStatus
    is_cordoned: bool
    is_allocatable: bool

    total_cpu_cores: float = Field(gt=0.0)
    allocated_cpu_cores: float = Field(ge=0.0)
    allocatable_cpu_cores: float = Field(ge=0.0)

    total_memory_mb: float = Field(gt=0.0)
    allocated_memory_mb: float = Field(ge=0.0)
    allocatable_memory_mb: float = Field(ge=0.0)

    active_workload_count: int = Field(ge=0)
    health_score: float = Field(ge=0.0, le=100.0)
