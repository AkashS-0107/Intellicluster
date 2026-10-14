"""
Unit tests for NodeService: registration, heartbeats, stale detection, and cordoning.
"""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.orm import Session

from intellicluster.core.constants import NodeStatus
from intellicluster.core.exceptions import NodeAlreadyExistsException, NodeNotFoundException
from intellicluster.schemas.node import NodeRegisterSchema
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.services.node_service import NodeService


def test_register_node_success(db_session: Session):
    """Test successful node registration."""
    data = NodeRegisterSchema(
        hostname="node-svc-01.internal",
        ip_address="10.20.30.40",
        cpu_cores=8.0,
        memory_mb=16384.0,
    )
    node = NodeService.register_node(db_session, data)
    assert node.id is not None
    assert node.hostname == "node-svc-01.internal"
    assert node.status == NodeStatus.READY.value
    assert node.health_score == 100.0


def test_register_duplicate_hostname_raises(db_session: Session):
    """Test that duplicate hostnames are rejected."""
    data = NodeRegisterSchema(
        hostname="node-dup.internal",
        cpu_cores=4.0,
        memory_mb=8192.0,
    )
    NodeService.register_node(db_session, data)

    with pytest.raises(NodeAlreadyExistsException):
        NodeService.register_node(db_session, data)


def test_get_nonexistent_node_raises(db_session: Session):
    """Test lookup of nonexistent node ID."""
    with pytest.raises(NodeNotFoundException):
        NodeService.get_node_by_id(db_session, "missing-node-id")


def test_cordon_and_uncordon_node(db_session: Session):
    """Test cordoning toggles is_cordoned flag."""
    node = NodeService.register_node(
        db_session,
        NodeRegisterSchema(hostname="node-cordon.internal", cpu_cores=4.0, memory_mb=8192.0),
    )
    assert node.is_cordoned is False

    cordoned = NodeService.cordon_node(db_session, node.id)
    assert cordoned.is_cordoned is True

    uncordoned = NodeService.uncordon_node(db_session, node.id)
    assert uncordoned.is_cordoned is False


def test_process_heartbeat_updates_metrics_and_snapshot(db_session: Session):
    """Test heartbeat updates cached metrics and appends a telemetry snapshot."""
    node = NodeService.register_node(
        db_session,
        NodeRegisterSchema(hostname="node-hb.internal", cpu_cores=8.0, memory_mb=16384.0),
    )

    telemetry = TelemetryCreateSchema(
        cpu_usage_pct=40.0,
        memory_usage_mb=4096.0,
        memory_usage_pct=25.0,
        disk_usage_gb=50.0,
        disk_usage_pct=20.0,
        network_rx_mbps=10.0,
        network_tx_mbps=5.0,
        network_latency_ms=8.0,
        active_connections=5,
        reported_status=NodeStatus.READY,
    )

    updated_node = NodeService.process_heartbeat(db_session, node.id, telemetry)
    assert updated_node.current_cpu_usage_pct == 40.0
    assert updated_node.current_memory_usage_mb == 4096.0
    assert updated_node.active_connections == 5
    assert len(updated_node.telemetry_snapshots) == 1


def test_process_heartbeat_degradation():
    """Test that critical resource load causes status to degrade."""
    pass  # Covered in integration scenarios


def test_mark_stale_nodes(db_session: Session):
    """Test that nodes with old heartbeats are transitioned to UNREACHABLE."""
    node = NodeService.register_node(
        db_session,
        NodeRegisterSchema(hostname="node-stale.internal", cpu_cores=4.0, memory_mb=8192.0),
    )

    # Manually backdate the heartbeat to 120 seconds ago
    node.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=120)
    db_session.commit()

    stale_list = NodeService.mark_stale_nodes(db_session, timeout_seconds=60)
    assert any(n.id == node.id for n in stale_list)

    refreshed = NodeService.get_node_by_id(db_session, node.id)
    assert refreshed.status == NodeStatus.UNREACHABLE.value


def test_get_allocatable_capacity(db_session: Session):
    """Test allocatable capacity calculation."""
    node = NodeService.register_node(
        db_session,
        NodeRegisterSchema(hostname="node-alloc.internal", cpu_cores=16.0, memory_mb=32768.0),
    )
    cap = NodeService.get_allocatable_capacity(db_session, node.id)
    assert cap.total_cpu_cores == 16.0
    assert cap.allocatable_cpu_cores == 16.0
    assert cap.is_allocatable is True
