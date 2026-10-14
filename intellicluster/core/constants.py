"""
Centralized domain enumerations and system constants.
"""

from enum import Enum


class StrEnum(str, Enum):
    """String enumeration base class for clean serialization."""
    def __str__(self) -> str:
        return self.value


class NodeStatus(StrEnum):
    """Operational statuses for cluster nodes."""
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    BUSY = "BUSY"
    DEGRADED = "DEGRADED"
    UNREACHABLE = "UNREACHABLE"
    DRAINING = "DRAINING"
    OFFLINE = "OFFLINE"


class WorkloadStatus(StrEnum):
    """Lifecycle statuses for managed workloads and tasks."""
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkloadPriority(StrEnum):
    """Priority levels for workload scheduling."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkloadType(StrEnum):
    """Categorization of workloads for resource profiling and scheduler evaluation."""
    BATCH = "BATCH"
    REALTIME_API = "REALTIME_API"
    ML_TRAINING = "ML_TRAINING"
    BACKGROUND_JOB = "BACKGROUND_JOB"
    DATA_PROCESSING = "DATA_PROCESSING"


class ClusterStatus(StrEnum):
    """Health and administrative status of a server cluster."""
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"
