"""
Unit tests for WorkloadService: lifecycle, state machine, and heuristic scheduling.
"""

import pytest
from sqlalchemy.orm import Session

from intellicluster.core.constants import NodeStatus, WorkloadPriority, WorkloadStatus, WorkloadType
from intellicluster.core.exceptions import (
    InvalidStateTransitionException,
    NoAvailableNodeException,
    WorkloadNotFoundException,
)
from intellicluster.models.node import Node
from intellicluster.schemas.workload import WorkloadCreateSchema
from intellicluster.services.workload_service import WorkloadService


def test_create_workload_pending(db_session: Session):
    """Test workload creation starts in PENDING status."""
    schema = WorkloadCreateSchema(
        name="batch-indexing-job",
        cpu_cores_requested=2.0,
        memory_mb_requested=4096.0,
        workload_type=WorkloadType.BATCH,
        priority=WorkloadPriority.NORMAL,
    )
    workload = WorkloadService.create_workload(db_session, schema)
    assert workload.id is not None
    assert workload.status == WorkloadStatus.PENDING.value
    assert workload.assigned_node_id is None


def test_get_nonexistent_workload_raises(db_session: Session):
    """Test lookup of non-existent workload ID."""
    with pytest.raises(WorkloadNotFoundException):
        WorkloadService.get_workload_by_id(db_session, "missing-workload")


def test_schedule_workload_success(db_session: Session):
    """Test scheduling pending workload assigns node and updates count."""
    node = Node(
        hostname="compute-node-10.local",
        status=NodeStatus.READY.value,
        cpu_cores=8.0,
        memory_mb=16384.0,
        current_cpu_usage_pct=10.0,
        current_memory_usage_mb=2048.0,
        health_score=95.0,
    )
    db_session.add(node)
    db_session.commit()

    workload = WorkloadService.create_workload(
        db_session,
        WorkloadCreateSchema(
            name="ml-infer-job",
            cpu_cores_requested=2.0,
            memory_mb_requested=4096.0,
        ),
    )

    scheduled = WorkloadService.schedule_pending_workload(db_session, workload.id)
    assert scheduled.status == WorkloadStatus.SCHEDULED.value
    assert scheduled.assigned_node_id == node.id
    assert scheduled.scheduled_at is not None

    db_session.refresh(node)
    assert node.active_workload_count == 1


def test_schedule_workload_no_capacity_raises(db_session: Session):
    """Test scheduling raises NoAvailableNodeException when resources are insufficient."""
    # Only a small node available
    node = Node(
        hostname="tiny-node.local",
        status=NodeStatus.READY.value,
        cpu_cores=1.0,
        memory_mb=1024.0,
        current_cpu_usage_pct=0.0,
        current_memory_usage_mb=0.0,
    )
    db_session.add(node)
    db_session.commit()

    workload = WorkloadService.create_workload(
        db_session,
        WorkloadCreateSchema(
            name="giant-workload",
            cpu_cores_requested=16.0,  # Exceeds node
            memory_mb_requested=32768.0,
        ),
    )

    with pytest.raises(NoAvailableNodeException):
        WorkloadService.schedule_pending_workload(db_session, workload.id)


def test_workload_lifecycle_transitions(db_session: Session):
    """Test valid state transitions: PENDING -> SCHEDULED -> RUNNING -> COMPLETED."""
    node = Node(
        hostname="worker-lifecycle.local",
        status=NodeStatus.READY.value,
        cpu_cores=4.0,
        memory_mb=8192.0,
    )
    db_session.add(node)
    db_session.commit()

    workload = WorkloadService.create_workload(
        db_session,
        WorkloadCreateSchema(name="lifecycle-task", cpu_cores_requested=1.0, memory_mb_requested=1024.0),
    )

    # 1. Schedule
    WorkloadService.schedule_pending_workload(db_session, workload.id)
    assert workload.status == WorkloadStatus.SCHEDULED.value

    # 2. Start running
    WorkloadService.transition_workload_status(db_session, workload.id, WorkloadStatus.RUNNING)
    assert workload.status == WorkloadStatus.RUNNING.value
    assert workload.started_at is not None

    # 3. Complete
    WorkloadService.transition_workload_status(db_session, workload.id, WorkloadStatus.COMPLETED)
    assert workload.status == WorkloadStatus.COMPLETED.value
    assert workload.completed_at is not None

    db_session.refresh(node)
    assert node.active_workload_count == 0


def test_illegal_state_transition_raises(db_session: Session):
    """Test that illegal transition raises InvalidStateTransitionException."""
    workload = WorkloadService.create_workload(
        db_session,
        WorkloadCreateSchema(name="illegal-task", cpu_cores_requested=1.0, memory_mb_requested=512.0),
    )

    # Attempting to move directly from PENDING to RUNNING without scheduling
    with pytest.raises(InvalidStateTransitionException):
        WorkloadService.transition_workload_status(db_session, workload.id, WorkloadStatus.RUNNING)
