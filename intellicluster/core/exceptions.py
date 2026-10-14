"""
Domain exception hierarchy for IntelliCluster.
Decoupled from HTTP transport layers and mapped to standard API error responses.
"""

from typing import Any, Optional


class IntelliClusterException(Exception):
    """Base exception for all IntelliCluster domain errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary representation."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# Entity Lookup Exceptions

class EntityNotFoundException(IntelliClusterException):
    """Base class for entities that cannot be located."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        message: Optional[str] = None,
    ) -> None:
        msg = message or f"{entity_type} with identifier '{entity_id}' was not found."
        super().__init__(
            message=msg,
            error_code=f"{entity_type.upper()}_NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )


class NodeNotFoundException(EntityNotFoundException):
    def __init__(self, node_id: str) -> None:
        super().__init__(entity_type="Node", entity_id=node_id)


class WorkloadNotFoundException(EntityNotFoundException):
    def __init__(self, workload_id: str) -> None:
        super().__init__(entity_type="Workload", entity_id=workload_id)


class ClusterNotFoundException(EntityNotFoundException):
    def __init__(self, cluster_id: str) -> None:
        super().__init__(entity_type="Cluster", entity_id=cluster_id)


# Entity Conflict Exceptions

class EntityAlreadyExistsException(IntelliClusterException):
    """Base class for uniqueness or conflict violations."""

    def __init__(
        self,
        entity_type: str,
        identifier: str,
        message: Optional[str] = None,
    ) -> None:
        msg = message or f"{entity_type} with identifier '{identifier}' already exists."
        super().__init__(
            message=msg,
            error_code=f"{entity_type.upper()}_ALREADY_EXISTS",
            details={"entity_type": entity_type, "identifier": identifier},
        )


class NodeAlreadyExistsException(EntityAlreadyExistsException):
    def __init__(self, identifier: str) -> None:
        super().__init__(entity_type="Node", identifier=identifier)


class ClusterAlreadyExistsException(EntityAlreadyExistsException):
    def __init__(self, identifier: str) -> None:
        super().__init__(entity_type="Cluster", identifier=identifier)


# Scheduling & Orchestration Exceptions

class SchedulingException(IntelliClusterException):
    """Base class for orchestration and scheduling failures."""

    def __init__(
        self,
        workload_id: str,
        reason: str,
        error_code: str = "SCHEDULING_FAILED",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        merged_details = {"workload_id": workload_id, "reason": reason}
        if details:
            merged_details.update(details)
        super().__init__(
            message=f"Failed to schedule workload '{workload_id}': {reason}",
            error_code=error_code,
            details=merged_details,
        )


class NoAvailableNodeException(SchedulingException):
    """Raised when no node in the cluster satisfies the workload requirements."""

    def __init__(
        self,
        workload_id: str,
        cpu_needed: float = 0.0,
        mem_needed: float = 0.0,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            workload_id=workload_id,
            reason="No eligible node with sufficient capacity or healthy status found.",
            error_code="NO_AVAILABLE_NODE",
            details={
                "cpu_cores_requested": cpu_needed,
                "memory_mb_requested": mem_needed,
                **(details or {}),
            },
        )


class IncompatibleNodeException(SchedulingException):
    """Raised when a specific node cannot host a workload due to constraints."""

    def __init__(self, workload_id: str, node_id: str, reason: str) -> None:
        super().__init__(
            workload_id=workload_id,
            reason=f"Node '{node_id}' is incompatible: {reason}",
            error_code="INCOMPATIBLE_NODE",
            details={"node_id": node_id},
        )


# State & Capacity Exceptions

class InvalidStateTransitionException(IntelliClusterException):
    """Raised when an illegal lifecycle transition is attempted."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        current_state: str,
        target_state: str,
    ) -> None:
        message = (
            f"Cannot transition {entity_type} '{entity_id}' from state "
            f"'{current_state}' to '{target_state}'."
        )
        super().__init__(
            message=message,
            error_code="INVALID_STATE_TRANSITION",
            details={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "current_state": current_state,
                "target_state": target_state,
            },
        )


class CapacityExceededException(IntelliClusterException):
    """Raised when a node or cluster capacity threshold is breached."""

    def __init__(
        self,
        resource_name: str,
        requested: float,
        available: float,
    ) -> None:
        message = (
            f"Capacity exceeded for {resource_name}: requested {requested}, "
            f"available {available}."
        )
        super().__init__(
            message=message,
            error_code="CAPACITY_EXCEEDED",
            details={
                "resource_name": resource_name,
                "requested": requested,
                "available": available,
            },
        )


class ConfigurationException(IntelliClusterException):
    """Raised when environment or runtime configuration is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
        )
