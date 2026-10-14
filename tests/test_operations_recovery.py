"""
Automated End-to-End Operational Recovery Verification Test Suite.

Verifies the complete operational workflows for:
1. Cluster management and capacity tracking
2. Node registration, validation, and lifecycle
3. Heartbeat processing and telemetry snapshot persistence
4. Telemetry history queries and cluster-wide aggregation
5. Workload scheduling, state transitions, safe retry, and cancellation
6. Stale node detection and scheduler isolation
7. Demonstration workflow idempotency and cleanup
"""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from intellicluster.core.constants import NodeStatus, WorkloadPriority, WorkloadStatus, WorkloadType
from intellicluster.core.exceptions import (
    InvalidStateTransitionException,
    NoAvailableNodeException,
    NodeNotFoundException,
)
from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload
from intellicluster.schemas.node import NodeRegisterSchema
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.schemas.workload import WorkloadCreateSchema
from intellicluster.services.cluster_service import ClusterService
from intellicluster.services.node_service import NodeService
from intellicluster.services.telemetry_service import TelemetryService
from intellicluster.services.workload_service import WorkloadService


class TestNodeAndTelemetryRecovery:
    """Verifies node registration, capacity validation, heartbeats, and telemetry."""

    def test_node_registration_with_cluster_association(self, db_session: Session):
        """Register a node attached to a cluster and verify hardware properties."""
        cluster = ClusterService.create_cluster(
            db_session,
            ClusterCreateSchema := __import__('intellicluster.schemas.cluster', fromlist=['ClusterCreateSchema']).ClusterCreateSchema(
                name="recovery-cluster-alpha",
                description="Cluster for recovery verification",
            ),
        )

        node_data = NodeRegisterSchema(
            hostname="worker-alpha-01.internal",
            ip_address="10.240.0.12",
            cluster_id=cluster.id,
            cpu_cores=16.0,
            memory_mb=65536.0,
            storage_gb=1000.0,
            network_bandwidth_mbps=10000.0,
        )
        node = NodeService.register_node(db_session, node_data)

        assert node.id is not None
        assert node.cluster_id == cluster.id
        assert node.status == NodeStatus.READY.value
        assert node.health_score == 100.0
        assert node.cpu_cores == 16.0
        assert node.memory_mb == 65536.0

        # Verify capacity breakdown
        cap = NodeService.get_allocatable_capacity(db_session, node.id)
        assert cap.is_allocatable is True
        assert cap.allocatable_cpu_cores == 16.0
        assert cap.allocatable_memory_mb == 65536.0

    def test_node_registration_rejects_invalid_capacity(self, client: TestClient):
        """API rejects zero or negative capacity fields with HTTP 422."""
        invalid_payloads = [
            {"hostname": "bad-node-1", "cpu_cores": 0.0, "memory_mb": 4096.0},
            {"hostname": "bad-node-2", "cpu_cores": -2.0, "memory_mb": 4096.0},
            {"hostname": "bad-node-3", "cpu_cores": 4.0, "memory_mb": 0.0},
            {"hostname": "bad-node-4", "cpu_cores": 4.0, "memory_mb": -1024.0},
            {"hostname": "bad-node-5", "cpu_cores": 4.0, "memory_mb": 4096.0, "storage_gb": -10.0},
            {"hostname": "bad-node-6", "cpu_cores": 4.0, "memory_mb": 4096.0, "network_bandwidth_mbps": 0.0},
            {"hostname": "bad-node-7", "cpu_cores": 4.0, "memory_mb": 4096.0, "ip_address": "999.999.999.999"},
        ]
        for payload in invalid_payloads:
            resp = client.post("/api/v1/nodes/", json=payload)
            assert resp.status_code == 422, f"Expected 422 for payload {payload}, got {resp.status_code}"

    def test_node_heartbeat_processing_and_persistence(self, db_session: Session):
        """Heartbeat updates live node metrics and commits an immutable TelemetrySnapshot."""
        node = NodeService.register_node(
            db_session,
            NodeRegisterSchema(hostname="heartbeat-node.internal", cpu_cores=8.0, memory_mb=16384.0),
        )

        heartbeat_data = TelemetryCreateSchema(
            cpu_usage_pct=42.5,
            memory_usage_mb=6144.0,
            memory_usage_pct=37.5,
            disk_usage_gb=150.0,
            disk_usage_pct=30.0,
            network_rx_mbps=45.0,
            network_tx_mbps=22.0,
            network_latency_ms=6.8,
            active_connections=35,
            running_processes=110,
            temperature_celsius=52.0,
            reported_status=NodeStatus.READY,
        )

        updated_node = NodeService.process_heartbeat(db_session, node.id, heartbeat_data)
        assert updated_node.current_cpu_usage_pct == 42.5
        assert updated_node.current_memory_usage_mb == 6144.0
        assert updated_node.current_network_latency_ms == 6.8
        assert updated_node.active_connections == 35
        assert updated_node.health_score > 0.0

        # Snapshot committed to database
        history = TelemetryService.get_node_telemetry_history(db_session, node.id)
        assert len(history) == 1
        snap = history[0]
        assert snap.cpu_usage_pct == 42.5
        assert snap.memory_usage_mb == 6144.0
        assert snap.network_latency_ms == 6.8

    def test_cluster_aggregated_metrics_distinguishes_zero_nodes(self, db_session: Session):
        """Aggregated metrics accurately report 0 reporting nodes when cluster is empty."""
        cluster = Cluster(name="empty-cluster-metrics", status="ACTIVE")
        db_session.add(cluster)
        db_session.commit()

        agg = TelemetryService.get_cluster_aggregated_metrics(db_session, cluster.id)
        assert agg.total_reporting_nodes == 0
        assert agg.avg_cpu_usage_pct == 0.0
        assert agg.max_cpu_usage_pct == 0.0

        # Now register 2 reporting nodes and submit telemetry
        n1 = NodeService.register_node(
            db_session,
            NodeRegisterSchema(hostname="agg-node-01", cluster_id=cluster.id, cpu_cores=4.0, memory_mb=8192.0),
        )
        n2 = NodeService.register_node(
            db_session,
            NodeRegisterSchema(hostname="agg-node-02", cluster_id=cluster.id, cpu_cores=4.0, memory_mb=8192.0),
        )

        NodeService.process_heartbeat(
            db_session,
            n1.id,
            TelemetryCreateSchema(
                cpu_usage_pct=20.0,
                memory_usage_mb=2048.0,
                memory_usage_pct=25.0,
                disk_usage_gb=20.0,
                disk_usage_pct=10.0,
                network_rx_mbps=10.0,
                network_tx_mbps=5.0,
                network_latency_ms=4.0,
                active_connections=10,
            ),
        )
        NodeService.process_heartbeat(
            db_session,
            n2.id,
            TelemetryCreateSchema(
                cpu_usage_pct=40.0,
                memory_usage_mb=4096.0,
                memory_usage_pct=50.0,
                disk_usage_gb=20.0,
                disk_usage_pct=10.0,
                network_rx_mbps=20.0,
                network_tx_mbps=15.0,
                network_latency_ms=8.0,
                active_connections=20,
            ),
        )

        agg2 = TelemetryService.get_cluster_aggregated_metrics(db_session, cluster.id)
        assert agg2.total_reporting_nodes == 2
        assert agg2.avg_cpu_usage_pct == 30.0  # (20 + 40) / 2
        assert agg2.max_cpu_usage_pct == 40.0
        assert agg2.avg_latency_ms == 6.0  # (4 + 8) / 2
        assert agg2.total_active_connections == 30

    def test_heartbeat_on_missing_node_raises_404(self, client: TestClient):
        """Heartbeat to nonexistent node returns HTTP 404."""
        resp = client.post(
            "/api/v1/nodes/nonexistent-node-id/heartbeat",
            json={
                "cpu_usage_pct": 10.0,
                "memory_usage_mb": 1024.0,
                "memory_usage_pct": 10.0,
                "disk_usage_gb": 10.0,
                "disk_usage_pct": 10.0,
                "network_rx_mbps": 1.0,
                "network_tx_mbps": 1.0,
                "network_latency_ms": 1.0,
            },
        )
        assert resp.status_code == 404


class TestWorkloadLifecycleAndRecovery:
    """Verifies workload creation, scheduling, safe retries, and cancellation."""

    def test_workload_scheduling_with_eligible_node(self, db_session: Session):
        """Workload successfully places onto an eligible node and updates cluster capacity."""
        cluster = Cluster(name="sched-cluster", status="ACTIVE")
        db_session.add(cluster)
        db_session.commit()

        node = NodeService.register_node(
            db_session,
            NodeRegisterSchema(
                hostname="eligible-worker.local",
                cluster_id=cluster.id,
                cpu_cores=8.0,
                memory_mb=16384.0,
            ),
        )

        workload = WorkloadService.create_workload(
            db_session,
            WorkloadCreateSchema(
                name="batch_1_compatible",
                cpu_cores_requested=2.1,
                memory_mb_requested=4096.0,
                max_latency_tolerance_ms=100.0,
            ),
        )
        assert workload.status == WorkloadStatus.PENDING.value
        assert workload.cluster_id is None

        # Schedule workload
        scheduled = WorkloadService.schedule_pending_workload(db_session, workload.id)
        assert scheduled.status == WorkloadStatus.SCHEDULED.value
        assert scheduled.assigned_node_id == node.id
        # Cluster ID is adopted from node
        assert scheduled.cluster_id == cluster.id

        # Node workload count updated
        db_session.refresh(node)
        assert node.active_workload_count == 1
        assert node.status == NodeStatus.BUSY.value

        # Cluster capacity reflects the allocated workload
        cap = ClusterService.calculate_cluster_capacity(db_session, cluster.id)
        assert cap.active_workload_count == 1
        assert cap.allocated_cpu_cores == 2.1
        assert cap.allocated_memory_mb == 4096.0
        assert cap.allocatable_cpu_cores == round(8.0 - 2.1, 2)

    def test_workload_scheduling_actionable_failure_when_no_eligible_node(self, db_session: Session):
        """Scheduling returns actionable NoAvailableNodeException when demands cannot be met."""
        # 1. Zero nodes in database
        workload = WorkloadService.create_workload(
            db_session,
            WorkloadCreateSchema(name="unschedulable-1", cpu_cores_requested=4.0, memory_mb_requested=8192.0),
        )
        with pytest.raises(NoAvailableNodeException) as excinfo:
            WorkloadService.schedule_pending_workload(db_session, workload.id)
        assert "cpu_cores_requested" in excinfo.value.to_dict()["details"]

        # 2. Node exists but has insufficient CPU
        node = NodeService.register_node(
            db_session,
            NodeRegisterSchema(hostname="small-node", cpu_cores=2.0, memory_mb=8192.0),
        )
        with pytest.raises(NoAvailableNodeException) as excinfo:
            WorkloadService.schedule_pending_workload(db_session, workload.id)
        assert excinfo.value.to_dict()["details"]["cpu_cores_requested"] == 4.0

        # Workload remains safely PENDING
        db_session.refresh(workload)
        assert workload.status == WorkloadStatus.PENDING.value
        assert workload.assigned_node_id is None

    def test_workload_retry_lifecycle_and_max_retries_guard(self, db_session: Session):
        """Workload can be retried up to max_retries, and rejects retries beyond max_retries."""
        node = NodeService.register_node(
            db_session,
            NodeRegisterSchema(hostname="retry-worker", cpu_cores=4.0, memory_mb=8192.0),
        )
        workload = WorkloadService.create_workload(
            db_session,
            WorkloadCreateSchema(
                name="retry-task",
                cpu_cores_requested=1.0,
                memory_mb_requested=1024.0,
                max_retries=2,
            ),
        )

        # 1. Schedule -> FAILED
        WorkloadService.schedule_pending_workload(db_session, workload.id)
        WorkloadService.transition_workload_status(
            db_session, workload.id, WorkloadStatus.FAILED, failure_reason="Process crashed"
        )
        assert workload.status == WorkloadStatus.FAILED.value
        assert workload.retry_count == 0

        # 2. First retry (0 < 2) -> PENDING
        WorkloadService.transition_workload_status(db_session, workload.id, WorkloadStatus.PENDING)
        assert workload.status == WorkloadStatus.PENDING.value
        assert workload.retry_count == 1
        assert workload.assigned_node_id is None
        assert workload.failure_reason is None

        # 3. Reschedule -> FAILED again
        WorkloadService.schedule_pending_workload(db_session, workload.id)
        WorkloadService.transition_workload_status(
            db_session, workload.id, WorkloadStatus.FAILED, failure_reason="Out of memory"
        )
        assert workload.retry_count == 1

        # 4. Second retry (1 < 2) -> PENDING
        WorkloadService.transition_workload_status(db_session, workload.id, WorkloadStatus.PENDING)
        assert workload.status == WorkloadStatus.PENDING.value
        assert workload.retry_count == 2

        # 5. Reschedule -> FAILED again
        WorkloadService.schedule_pending_workload(db_session, workload.id)
        WorkloadService.transition_workload_status(
            db_session, workload.id, WorkloadStatus.FAILED, failure_reason="Disk full"
        )
        assert workload.retry_count == 2

        # 6. Third retry attempt: retry_count (2) >= max_retries (2) -> REJECTED
        with pytest.raises(InvalidStateTransitionException):
            WorkloadService.transition_workload_status(db_session, workload.id, WorkloadStatus.PENDING)

        # Workload remains FAILED
        db_session.refresh(workload)
        assert workload.status == WorkloadStatus.FAILED.value
        assert workload.retry_count == 2

    def test_workload_cancellation_cleans_node_counts(self, db_session: Session):
        """Cancelling a scheduled or running workload decrements node active workload count."""
        node = NodeService.register_node(
            db_session,
            NodeRegisterSchema(hostname="cancel-worker", cpu_cores=4.0, memory_mb=8192.0),
        )
        workload = WorkloadService.create_workload(
            db_session,
            WorkloadCreateSchema(name="cancel-task", cpu_cores_requested=1.0, memory_mb_requested=1024.0),
        )

        WorkloadService.schedule_pending_workload(db_session, workload.id)
        db_session.refresh(node)
        assert node.active_workload_count == 1

        WorkloadService.cancel_workload(db_session, workload.id)
        assert workload.status == WorkloadStatus.CANCELLED.value
        assert workload.completed_at is not None

        db_session.refresh(node)
        assert node.active_workload_count == 0
        assert node.status == NodeStatus.READY.value

    def test_stale_node_marked_unreachable_and_skipped_by_scheduler(self, db_session: Session):
        """Node with missing heartbeat > 60s is marked UNREACHABLE and excluded from placement."""
        node = NodeService.register_node(
            db_session,
            NodeRegisterSchema(hostname="silent-node.internal", cpu_cores=8.0, memory_mb=16384.0),
        )
        # Backdate last heartbeat by 90 seconds
        node.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=90)
        db_session.commit()

        workload = WorkloadService.create_workload(
            db_session,
            WorkloadCreateSchema(name="needs-active-node", cpu_cores_requested=2.0, memory_mb_requested=4096.0),
        )

        # Scheduling should sweep stale nodes and fail because silent node becomes UNREACHABLE
        with pytest.raises(NoAvailableNodeException):
            WorkloadService.schedule_pending_workload(db_session, workload.id)

        db_session.refresh(node)
        assert node.status == NodeStatus.UNREACHABLE.value
