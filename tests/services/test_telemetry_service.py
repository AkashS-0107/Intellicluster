"""
Unit tests for TelemetryService.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from intellicluster.core.constants import NodeStatus
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.services.telemetry_service import TelemetryService


def test_record_and_get_telemetry_history(db_session: Session):
    """Test recording telemetry and retrieving time-series history."""
    node = Node(
        hostname="telemetry-node-01.local",
        status=NodeStatus.READY.value,
        cpu_cores=8.0,
        memory_mb=16384.0,
    )
    db_session.add(node)
    db_session.commit()

    sample = TelemetryCreateSchema(
        cpu_usage_pct=33.3,
        memory_usage_mb=4096.0,
        memory_usage_pct=25.0,
        disk_usage_gb=60.0,
        disk_usage_pct=15.0,
        network_rx_mbps=12.0,
        network_tx_mbps=8.0,
        network_latency_ms=4.5,
        active_connections=14,
        reported_status=NodeStatus.READY,
    )

    snapshot = TelemetryService.record_telemetry(db_session, node.id, sample)
    assert snapshot.id is not None
    assert snapshot.cpu_usage_pct == 33.3
    assert snapshot.node_id == node.id

    history = TelemetryService.get_node_telemetry_history(db_session, node.id)
    assert len(history) >= 1
    assert history[0].id == snapshot.id


def test_get_cluster_aggregated_metrics(db_session: Session):
    """Test cluster-wide aggregated telemetry calculation."""
    n1 = Node(
        hostname="node-agg-1",
        cpu_cores=8.0,
        memory_mb=16384.0,
        current_cpu_usage_pct=40.0,
        current_memory_usage_mb=8192.0,
        current_network_latency_ms=10.0,
        active_connections=20,
    )
    n2 = Node(
        hostname="node-agg-2",
        cpu_cores=8.0,
        memory_mb=16384.0,
        current_cpu_usage_pct=60.0,
        current_memory_usage_mb=8192.0,
        current_network_latency_ms=20.0,
        active_connections=30,
    )
    db_session.add_all([n1, n2])
    db_session.commit()

    summary = TelemetryService.get_cluster_aggregated_metrics(db_session)
    assert summary.total_reporting_nodes == 2
    assert summary.avg_cpu_usage_pct == 50.0  # (40 + 60) / 2
    assert summary.max_cpu_usage_pct == 60.0
    assert summary.avg_latency_ms == 15.0  # (10 + 20) / 2
    assert summary.total_active_connections == 50  # 20 + 30


# ==============================================================================
# HOURLY HISTORY VALIDATION & SAMPLING TESTS
# ==============================================================================

def test_validate_node_hourly_history_zero_snapshots(db_session: Session):
    """Zero snapshots returns not ready with 0 valid hours."""
    node = Node(hostname="zero-snap-node", cpu_cores=4.0, memory_mb=8192.0)
    db_session.add(node)
    db_session.commit()

    is_ready, readiness, matrix = TelemetryService.validate_node_hourly_history(
        db_session, node.id, required_hours=168
    )
    assert is_ready is False
    assert readiness.valid_hourly_observations == 0
    assert readiness.readiness_percentage == 0.0
    assert readiness.estimated_hours_remaining == 168.0
    assert "Zero historical snapshots found" in readiness.validation_reason
    assert matrix is None


def test_validate_node_hourly_history_multiple_heartbeats_in_one_hour(db_session: Session):
    """168 snapshots sent in the same 1 hour count as only 1 hourly bucket."""
    node = Node(hostname="one-hour-node", cpu_cores=4.0, memory_mb=8192.0)
    db_session.add(node)
    db_session.commit()

    # 168 snapshots all occurring within the same hour bucket (10:00 to 10:59)
    base_time = datetime(2026, 10, 10, 10, 0, 0, tzinfo=timezone.utc)
    for i in range(168):
        snap = TelemetrySnapshot(
            node_id=node.id,
            recorded_at=base_time + timedelta(seconds=i * 10),
            cpu_usage_pct=40.0 + (i % 5),
            memory_usage_mb=4096.0,
            memory_usage_pct=50.0,
            disk_usage_gb=50.0,
            disk_usage_pct=25.0,
            network_rx_mbps=10.0,
            network_tx_mbps=10.0,
            network_latency_ms=5.0,
            active_connections=10,
            reported_status="READY",
            workload=90.0,
            resource_allocation=60.0,
        )
        db_session.add(snap)
    db_session.commit()

    is_ready, readiness, matrix = TelemetryService.validate_node_hourly_history(
        db_session, node.id, required_hours=168
    )
    assert is_ready is False
    assert readiness.total_raw_snapshots == 168
    # Critical guarantee: exactly 1 hourly bucket
    assert readiness.valid_hourly_observations == 1
    assert readiness.readiness_percentage == 0.6  # 1 / 168
    assert readiness.estimated_hours_remaining == 167.0
    assert matrix is None


def test_validate_node_hourly_history_167_hours_fails(db_session: Session):
    """167 contiguous hours fails validation with 1 hour remaining."""
    node = Node(hostname="167-hour-node", cpu_cores=4.0, memory_mb=8192.0)
    db_session.add(node)
    db_session.commit()

    start_time = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(167):
        snap = TelemetrySnapshot(
            node_id=node.id,
            recorded_at=start_time + timedelta(hours=i),
            cpu_usage_pct=50.0,
            memory_usage_mb=4096.0,
            memory_usage_pct=50.0,
            disk_usage_gb=50.0,
            disk_usage_pct=25.0,
            network_rx_mbps=10.0,
            network_tx_mbps=10.0,
            network_latency_ms=5.0,
            active_connections=10,
            reported_status="READY",
            workload=90.0,
            resource_allocation=60.0,
        )
        db_session.add(snap)
    db_session.commit()

    is_ready, readiness, matrix = TelemetryService.validate_node_hourly_history(
        db_session, node.id, required_hours=168
    )
    assert is_ready is False
    assert readiness.valid_hourly_observations == 167
    assert readiness.estimated_hours_remaining == 1.0
    assert "Remaining time needed: 1 hour(s)" in readiness.validation_reason
    assert matrix is None


def test_validate_node_hourly_history_missing_hours_gap(db_session: Session):
    """Missing hourly gap breaks contiguity and is reported."""
    node = Node(hostname="gap-node", cpu_cores=4.0, memory_mb=8192.0)
    db_session.add(node)
    db_session.commit()

    start_time = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
    # First 10 hours: 0..9
    for i in range(10):
        db_session.add(
            TelemetrySnapshot(
                node_id=node.id,
                recorded_at=start_time + timedelta(hours=i),
                cpu_usage_pct=50.0,
                memory_usage_mb=4096.0,
                memory_usage_pct=50.0,
                disk_usage_gb=50.0,
                disk_usage_pct=25.0,
                network_rx_mbps=10.0,
                network_tx_mbps=10.0,
                network_latency_ms=5.0,
                active_connections=10,
                reported_status="READY",
                workload=90.0,
                resource_allocation=60.0,
            )
        )
    # 5-hour gap: next observations start at hour 15..20 (6 hours)
    for i in range(15, 21):
        db_session.add(
            TelemetrySnapshot(
                node_id=node.id,
                recorded_at=start_time + timedelta(hours=i),
                cpu_usage_pct=50.0,
                memory_usage_mb=4096.0,
                memory_usage_pct=50.0,
                disk_usage_gb=50.0,
                disk_usage_pct=25.0,
                network_rx_mbps=10.0,
                network_tx_mbps=10.0,
                network_latency_ms=5.0,
                active_connections=10,
                reported_status="READY",
                workload=90.0,
                resource_allocation=60.0,
            )
        )
    db_session.commit()

    is_ready, readiness, matrix = TelemetryService.validate_node_hourly_history(
        db_session, node.id, required_hours=168
    )
    assert is_ready is False
    # Contiguous run ending at latest snapshot is only 6 hours
    assert readiness.valid_hourly_observations == 6
    assert readiness.missing_intervals_count == 5
    assert len(readiness.missing_ranges) == 1
    assert "gap(s) totaling 5 missing hour(s)" in readiness.validation_reason


def test_validate_node_hourly_history_missing_feature(db_session: Session):
    """168 contiguous hours but missing workload metric fails feature validation."""
    node = Node(hostname="missing-feat-node", cpu_cores=4.0, memory_mb=8192.0)
    db_session.add(node)
    db_session.commit()

    start_time = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(168):
        db_session.add(
            TelemetrySnapshot(
                node_id=node.id,
                recorded_at=start_time + timedelta(hours=i),
                cpu_usage_pct=50.0,
                memory_usage_mb=4096.0,
                memory_usage_pct=50.0,
                disk_usage_gb=50.0,
                disk_usage_pct=25.0,
                network_rx_mbps=10.0,
                network_tx_mbps=10.0,
                network_latency_ms=5.0,
                active_connections=10,
                reported_status="READY",
                workload=None,  # Missing workload!
                resource_allocation=60.0,
            )
        )
    db_session.commit()

    is_ready, readiness, matrix = TelemetryService.validate_node_hourly_history(
        db_session, node.id, required_hours=168
    )
    assert is_ready is False
    assert readiness.valid_hourly_observations == 168
    assert readiness.feature_readiness["workload"] is False
    assert "required features are unavailable: workload" in readiness.validation_reason
    assert matrix is None


def test_validate_node_hourly_history_168_contiguous_success(db_session: Session):
    """Exactly 168 contiguous hourly snapshots with all 5 features succeeds."""
    node = Node(hostname="perfect-168-node", cpu_cores=8.0, memory_mb=16384.0)
    db_session.add(node)
    db_session.commit()

    start_time = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(168):
        # Even if multiple snapshots exist in hour i, deterministic aggregation averages them
        for sub in range(2):
            db_session.add(
                TelemetrySnapshot(
                    node_id=node.id,
                    recorded_at=start_time + timedelta(hours=i, minutes=sub * 20),
                    cpu_usage_pct=50.0 + (sub * 2.0),
                    memory_usage_mb=8192.0,
                    memory_usage_pct=50.0,
                    disk_usage_gb=100.0,
                    disk_usage_pct=25.0,
                    network_rx_mbps=10.0,
                    network_tx_mbps=10.0,
                    network_latency_ms=5.0,
                    active_connections=15,
                    reported_status="READY",
                    workload=92.5,
                    resource_allocation=60.0,
                )
            )
    db_session.commit()

    is_ready, readiness, matrix = TelemetryService.validate_node_hourly_history(
        db_session, node.id, required_hours=168
    )
    assert is_ready is True
    assert readiness.valid_hourly_observations == 168
    assert readiness.readiness_percentage == 100.0
    assert readiness.estimated_hours_remaining == 0.0
    assert readiness.total_raw_snapshots == 336  # 168 * 2
    assert readiness.missing_intervals_count == 0
    assert "history fully qualified" in readiness.validation_reason

    # Verify extracted matrix shape and features
    assert matrix is not None
    assert len(matrix) == 168
    assert len(matrix[0]) == 5
    # CPU averaged from 50.0 and 52.0 = 51.0
    assert matrix[0][0] == 51.0
    assert matrix[0][3] == 92.5  # workload
    assert matrix[0][4] == 60.0  # resource_allocation


# ==============================================================================
# TELEMETRY SIMULATOR SERVICE TESTS
# ==============================================================================

import pytest

@pytest.mark.asyncio
async def test_telemetry_simulator_start_stop_duplicate_protection(db_session: Session):
    """Simulator supports explicit start/stop and prevents duplicate starts."""
    from intellicluster.services.telemetry_simulator_service import (
        TelemetrySimulatorService,
        SimulatorAlreadyRunningException,
    )

    sim = TelemetrySimulatorService.get_instance()
    await sim.stop()  # Ensure clean starting state

    status = sim.get_status()
    assert status["is_running"] is False

    # 1. Start simulator
    start_res = await sim.start(interval_seconds=10)
    assert start_res["is_running"] is True
    assert start_res["interval_seconds"] == 10

    # 2. Duplicate start must raise SimulatorAlreadyRunningException
    with pytest.raises(SimulatorAlreadyRunningException):
        await sim.start(interval_seconds=5)

    # 3. Stop simulator
    stop_res = await sim.stop()
    assert stop_res["is_running"] is False
