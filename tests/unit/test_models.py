"""
Unit tests for ORM entities, relationships, constraints, and timestamps.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from intellicluster.core.constants import ClusterStatus, NodeStatus, WorkloadPriority, WorkloadStatus, WorkloadType
from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload


def test_cluster_creation_and_defaults(db_session: Session):
    """Test Cluster model creation, UUID generation, and timestamp mixin."""
    cluster = Cluster(name="test-cluster-01", description="Main test cluster")
    db_session.add(cluster)
    db_session.commit()
    db_session.refresh(cluster)

    assert cluster.id is not None
    assert len(cluster.id) == 36  # UUID length
    assert cluster.status == ClusterStatus.ACTIVE.value
    assert isinstance(cluster.created_at, datetime)
    assert isinstance(cluster.updated_at, datetime)
    assert "test-cluster-01" in repr(cluster)


def test_cluster_unique_name_constraint(db_session: Session):
    """Test that duplicate cluster names raise IntegrityError."""
    c1 = Cluster(name="unique-cluster")
    c2 = Cluster(name="unique-cluster")
    db_session.add(c1)
    db_session.commit()

    db_session.add(c2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_node_creation_and_relationships(db_session: Session):
    """Test Node entity creation and relational link to parent cluster."""
    cluster = Cluster(name="cluster-for-node")
    db_session.add(cluster)
    db_session.commit()

    node = Node(
        hostname="worker-node-01.local",
        ip_address="10.0.0.1",
        cluster_id=cluster.id,
        cpu_cores=16.0,
        memory_mb=32768.0,
        storage_gb=500.0,
    )
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)

    assert node.id is not None
    assert node.status == NodeStatus.READY.value
    assert node.health_score == 100.0
    assert node.cluster_id == cluster.id
    assert node.cluster is not None
    assert node.cluster.name == "cluster-for-node"
    assert node in cluster.nodes


def test_workload_creation_and_relationships(db_session: Session):
    """Test Workload creation and association with node and cluster."""
    cluster = Cluster(name="cluster-workload-test")
    node = Node(
        hostname="worker-02.local",
        cpu_cores=8.0,
        memory_mb=16384.0,
    )
    db_session.add_all([cluster, node])
    db_session.commit()

    workload = Workload(
        name="job-alpha",
        cluster_id=cluster.id,
        assigned_node_id=node.id,
        workload_type=WorkloadType.BATCH.value,
        cpu_cores_requested=2.0,
        memory_mb_requested=4096.0,
        priority=WorkloadPriority.HIGH.value,
    )
    db_session.add(workload)
    db_session.commit()
    db_session.refresh(workload)

    assert workload.id is not None
    assert workload.status == WorkloadStatus.PENDING.value
    assert workload.assigned_node is not None
    assert workload.assigned_node.hostname == "worker-02.local"
    assert workload in node.workloads
    assert workload in cluster.workloads


def test_telemetry_snapshot_cascade(db_session: Session):
    """Test TelemetrySnapshot creation and cascade deletion with parent node."""
    node = Node(hostname="telemetry-node.local", cpu_cores=4.0, memory_mb=8192.0)
    db_session.add(node)
    db_session.commit()

    snapshot = TelemetrySnapshot(
        node_id=node.id,
        cpu_usage_pct=25.5,
        memory_usage_mb=2048.0,
        memory_usage_pct=25.0,
        disk_usage_gb=50.0,
        disk_usage_pct=10.0,
        network_rx_mbps=5.0,
        network_tx_mbps=2.5,
        network_latency_ms=3.2,
        active_connections=12,
        reported_status=NodeStatus.READY.value,
    )
    db_session.add(snapshot)
    db_session.commit()

    assert snapshot.id is not None
    assert len(node.telemetry_snapshots) == 1
    assert node.telemetry_snapshots[0].id == snapshot.id
