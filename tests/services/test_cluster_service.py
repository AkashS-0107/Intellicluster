"""
Unit tests for ClusterService.
"""

import pytest
from sqlalchemy.orm import Session

from intellicluster.core.constants import ClusterStatus
from intellicluster.core.exceptions import (
    ClusterAlreadyExistsException,
    ClusterNotFoundException,
)
from intellicluster.models.node import Node
from intellicluster.models.workload import Workload
from intellicluster.schemas.cluster import ClusterCreateSchema, ClusterUpdateSchema
from intellicluster.services.cluster_service import ClusterService


def test_create_and_get_cluster(db_session: Session):
    """Test successful cluster creation and lookup."""
    schema = ClusterCreateSchema(name="production-east", description="East coast compute")
    cluster = ClusterService.create_cluster(db_session, schema)

    assert cluster.id is not None
    assert cluster.name == "production-east"
    assert cluster.status == ClusterStatus.ACTIVE.value

    fetched = ClusterService.get_cluster_by_id(db_session, cluster.id)
    assert fetched.id == cluster.id


def test_duplicate_cluster_name_raises(db_session: Session):
    """Test that creating a cluster with an existing name raises exception."""
    schema = ClusterCreateSchema(name="duplicate-cluster")
    ClusterService.create_cluster(db_session, schema)

    with pytest.raises(ClusterAlreadyExistsException):
        ClusterService.create_cluster(db_session, schema)


def test_get_nonexistent_cluster_raises(db_session: Session):
    """Test lookup of non-existent cluster ID."""
    with pytest.raises(ClusterNotFoundException):
        ClusterService.get_cluster_by_id(db_session, "missing-cluster-id")


def test_list_and_update_cluster(db_session: Session):
    """Test cluster listing and update."""
    c1 = ClusterService.create_cluster(db_session, ClusterCreateSchema(name="cluster-1"))
    c2 = ClusterService.create_cluster(db_session, ClusterCreateSchema(name="cluster-2"))

    clusters = ClusterService.list_clusters(db_session)
    assert len(clusters) >= 2

    updated = ClusterService.update_cluster(
        db_session,
        c1.id,
        ClusterUpdateSchema(status=ClusterStatus.DEGRADED),
    )
    assert updated.status == ClusterStatus.DEGRADED.value


def test_calculate_cluster_capacity(db_session: Session):
    """Test capacity aggregation with attached nodes and active workloads."""
    cluster = ClusterService.create_cluster(db_session, ClusterCreateSchema(name="capacity-cluster"))

    node = Node(
        cluster_id=cluster.id,
        hostname="node-cap-01",
        cpu_cores=16.0,
        memory_mb=32768.0,
        current_cpu_usage_pct=20.0,
        current_memory_usage_mb=4096.0,
    )
    db_session.add(node)
    db_session.commit()

    summary = ClusterService.calculate_cluster_capacity(db_session, cluster.id)
    assert summary.total_nodes == 1
    assert summary.ready_nodes == 1
    assert summary.total_cpu_cores == 16.0
    assert summary.total_memory_mb == 32768.0
    assert summary.allocatable_cpu_cores == 16.0
