"""
Unit tests for domain exception hierarchy.
"""

from intellicluster.core.exceptions import (
    CapacityExceededException,
    ClusterNotFoundException,
    EntityNotFoundException,
    IntelliClusterException,
    InvalidStateTransitionException,
    NoAvailableNodeException,
    NodeAlreadyExistsException,
    NodeNotFoundException,
    WorkloadNotFoundException,
)


def test_exception_inheritance():
    """Verify that domain exceptions properly inherit from IntelliClusterException."""
    err = NodeNotFoundException(node_id="node-123")
    assert isinstance(err, EntityNotFoundException)
    assert isinstance(err, IntelliClusterException)
    assert err.error_code == "NODE_NOT_FOUND"
    assert err.details["entity_id"] == "node-123"


def test_no_available_node_exception():
    """Verify NoAvailableNodeException details structure."""
    err = NoAvailableNodeException(
        workload_id="workload-456",
        cpu_needed=8.0,
        mem_needed=16384.0,
    )
    assert err.error_code == "NO_AVAILABLE_NODE"
    assert err.details["cpu_cores_requested"] == 8.0
    assert err.details["memory_mb_requested"] == 16384.0

    d = err.to_dict()
    assert d["error_code"] == "NO_AVAILABLE_NODE"
    assert "workload-456" in d["message"]


def test_invalid_state_transition_exception():
    """Verify InvalidStateTransitionException attributes."""
    err = InvalidStateTransitionException(
        entity_type="Workload",
        entity_id="task-1",
        current_state="COMPLETED",
        target_state="RUNNING",
    )
    assert err.error_code == "INVALID_STATE_TRANSITION"
    assert err.details["current_state"] == "COMPLETED"
    assert err.details["target_state"] == "RUNNING"
