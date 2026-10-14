"""
Unit tests for Pydantic schemas and input validation constraints.
"""

import pytest
from pydantic import ValidationError

from intellicluster.core.constants import ClusterStatus, NodeStatus, WorkloadPriority, WorkloadType
from intellicluster.schemas.cluster import ClusterCreateSchema
from intellicluster.schemas.node import NodeRegisterSchema
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.schemas.workload import WorkloadCreateSchema


def test_valid_node_register_schema():
    """Verify that a valid node registration payload passes validation."""
    data = NodeRegisterSchema(
        hostname="valid-node-01.local",
        ip_address="192.168.1.50",
        cpu_cores=8.0,
        memory_mb=16384.0,
        storage_gb=256.0,
    )
    assert data.hostname == "valid-node-01.local"
    assert data.cpu_cores == 8.0


def test_invalid_node_cpu_rejected():
    """Verify that zero or negative CPU cores raise validation error."""
    with pytest.raises(ValidationError):
        NodeRegisterSchema(
            hostname="invalid-node",
            cpu_cores=0.0,  # gt=0.0 constraint
            memory_mb=1024.0,
        )


def test_invalid_node_ip_rejected():
    """Verify that a malformed IP address string raises validation error."""
    with pytest.raises(ValidationError) as exc:
        NodeRegisterSchema(
            hostname="bad-ip-node",
            ip_address="999.999.999.999",  # Invalid IPv4
            cpu_cores=4.0,
            memory_mb=4096.0,
        )
    assert "Invalid IP address" in str(exc.value)


def test_valid_workload_create_schema():
    """Verify valid workload creation payload."""
    data = WorkloadCreateSchema(
        name="computation-task",
        cpu_cores_requested=4.0,
        memory_mb_requested=8192.0,
        priority=WorkloadPriority.CRITICAL,
        workload_type=WorkloadType.DATA_PROCESSING,
    )
    assert data.priority == WorkloadPriority.CRITICAL
    assert data.cpu_cores_requested == 4.0


def test_workload_negative_memory_rejected():
    """Verify that negative memory requirement fails validation."""
    with pytest.raises(ValidationError):
        WorkloadCreateSchema(
            name="bad-mem-task",
            cpu_cores_requested=2.0,
            memory_mb_requested=-100.0,
        )


def test_telemetry_percentage_bounds():
    """Verify that percentage values above 100 or below 0 fail validation."""
    with pytest.raises(ValidationError):
        TelemetryCreateSchema(
            cpu_usage_pct=105.0,  # le=100.0
            memory_usage_mb=4096.0,
            memory_usage_pct=50.0,
            disk_usage_gb=100.0,
            disk_usage_pct=25.0,
            network_rx_mbps=10.0,
            network_tx_mbps=5.0,
            network_latency_ms=2.0,
            reported_status=NodeStatus.READY,
        )
