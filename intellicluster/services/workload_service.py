"""
Domain service for Workload lifecycle, queueing, and intelligent scheduling execution.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from intellicluster.core.constants import NodeStatus, WorkloadPriority, WorkloadStatus
from intellicluster.core.exceptions import (
    ClusterNotFoundException,
    InvalidStateTransitionException,
    NoAvailableNodeException,
    WorkloadNotFoundException,
)
from intellicluster.core.logging import logger
from intellicluster.ml.heuristic import HeuristicSchedulerStrategy
from intellicluster.ml.interfaces import BaseSchedulerPredictor
from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.workload import Workload
from intellicluster.schemas.workload import WorkloadCreateSchema, WorkloadUpdateSchema
from intellicluster.utils.datetime_utils import utcnow


class WorkloadService:
    """Business logic for workloads and tasks."""

    VALID_TRANSITIONS: dict[str, set[str]] = {
        WorkloadStatus.PENDING.value: {
            WorkloadStatus.SCHEDULED.value,
            WorkloadStatus.CANCELLED.value,
        },
        WorkloadStatus.SCHEDULED.value: {
            WorkloadStatus.RUNNING.value,
            WorkloadStatus.CANCELLED.value,
            WorkloadStatus.FAILED.value,
        },
        WorkloadStatus.RUNNING.value: {
            WorkloadStatus.COMPLETED.value,
            WorkloadStatus.FAILED.value,
            WorkloadStatus.CANCELLED.value,
        },
        WorkloadStatus.FAILED.value: {
            WorkloadStatus.PENDING.value,  # Retry
        },
        WorkloadStatus.COMPLETED.value: set(),
        WorkloadStatus.CANCELLED.value: set(),
    }

    @staticmethod
    def create_workload(session: Session, data: WorkloadCreateSchema) -> Workload:
        """Submit a new workload into PENDING state."""
        if data.cluster_id:
            cluster = session.get(Cluster, data.cluster_id)
            if not cluster:
                raise ClusterNotFoundException(cluster_id=data.cluster_id)

        workload = Workload(
            name=data.name,
            cluster_id=data.cluster_id,
            workload_type=data.workload_type.value,
            cpu_cores_requested=data.cpu_cores_requested,
            memory_mb_requested=data.memory_mb_requested,
            storage_gb_requested=data.storage_gb_requested,
            network_mbps_requested=data.network_mbps_requested,
            max_latency_tolerance_ms=data.max_latency_tolerance_ms,
            estimated_duration_sec=data.estimated_duration_sec,
            priority=data.priority.value,
            status=WorkloadStatus.PENDING.value,
            max_retries=data.max_retries,
            retry_count=0,
        )
        session.add(workload)
        session.commit()
        session.refresh(workload)
        logger.info(
            "Workload created in PENDING state",
            extra={
                "workload_id": workload.id,
                "name": workload.name,
                "cpu": workload.cpu_cores_requested,
                "mem": workload.memory_mb_requested,
            },
        )
        return workload

    @staticmethod
    def get_workload_by_id(session: Session, workload_id: str) -> Workload:
        """Retrieve workload by ID or raise WorkloadNotFoundException."""
        workload = session.get(Workload, workload_id)
        if not workload:
            raise WorkloadNotFoundException(workload_id=workload_id)
        return workload

    @staticmethod
    def list_workloads(
        session: Session,
        cluster_id: Optional[str] = None,
        assigned_node_id: Optional[str] = None,
        status: Optional[WorkloadStatus] = None,
        priority: Optional[WorkloadPriority] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Workload]:
        """List workloads with optional filters."""
        stmt = select(Workload).offset(skip).limit(limit)
        if cluster_id:
            stmt = stmt.where(Workload.cluster_id == cluster_id)
        if assigned_node_id:
            stmt = stmt.where(Workload.assigned_node_id == assigned_node_id)
        if status:
            stmt = stmt.where(Workload.status == status.value)
        if priority:
            stmt = stmt.where(Workload.priority == priority.value)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_workload(session: Session, workload_id: str, data: WorkloadUpdateSchema) -> Workload:
        """Update workload parameters."""
        workload = WorkloadService.get_workload_by_id(session, workload_id)
        if data.name is not None:
            workload.name = data.name
        if data.assigned_node_id is not None:
            workload.assigned_node_id = data.assigned_node_id
        if data.priority is not None:
            workload.priority = data.priority.value
        if data.max_retries is not None:
            workload.max_retries = data.max_retries

        session.commit()
        session.refresh(workload)
        return workload

    @staticmethod
    def schedule_pending_workload(
        session: Session,
        workload_id: str,
        strategy: Optional[BaseSchedulerPredictor] = None,
    ) -> Workload:
        """
        Orchestrate placement for a PENDING workload onto an eligible node.
        Delegates node scoring to the provided BaseSchedulerPredictor strategy
        (active production default: HeuristicSchedulerStrategy).
        """
        workload = WorkloadService.get_workload_by_id(session, workload_id)
        if workload.status != WorkloadStatus.PENDING.value:
            raise InvalidStateTransitionException(
                entity_type="Workload",
                entity_id=workload.id,
                current_state=workload.status,
                target_state=WorkloadStatus.SCHEDULED.value,
            )

        # Ensure stale nodes are marked UNREACHABLE before placement evaluation
        from intellicluster.services.node_service import NodeService
        NodeService.mark_stale_nodes(session)

        nodes_stmt = select(Node)
        if workload.cluster_id:
            nodes_stmt = nodes_stmt.where(Node.cluster_id == workload.cluster_id)
        candidate_nodes = list(session.execute(nodes_stmt).scalars().all())

        scheduler = strategy or HeuristicSchedulerStrategy()
        recommendation = scheduler.predict_optimal_node(workload, candidate_nodes)

        if not recommendation.recommended_node_id:
            logger.warning(
                "Workload scheduling unsuccessful - no eligible node",
                extra={"workload_id": workload.id, "reason": recommendation.reasoning},
            )
            raise NoAvailableNodeException(
                workload_id=workload.id,
                cpu_needed=workload.cpu_cores_requested,
                mem_needed=workload.memory_mb_requested,
                details={"reasoning": recommendation.reasoning},
            )

        target_node = session.get(Node, recommendation.recommended_node_id)
        if not target_node:
            raise NoAvailableNodeException(
                workload_id=workload.id,
                cpu_needed=workload.cpu_cores_requested,
                mem_needed=workload.memory_mb_requested,
                details={"reason": "Selected candidate node missing"},
            )

        now = utcnow()
        workload.assigned_node_id = target_node.id
        # Associate cluster ID if workload was submitted standalone
        if workload.cluster_id is None and target_node.cluster_id is not None:
            workload.cluster_id = target_node.cluster_id
        workload.status = WorkloadStatus.SCHEDULED.value
        workload.scheduled_at = now

        target_node.active_workload_count += 1
        if target_node.active_workload_count > 0 and target_node.status == NodeStatus.READY.value:
            target_node.status = NodeStatus.BUSY.value

        session.commit()
        session.refresh(workload)
        session.refresh(target_node)

        logger.info(
            "Workload scheduled successfully",
            extra={
                "workload_id": workload.id,
                "node_id": target_node.id,
                "hostname": target_node.hostname,
                "strategy": recommendation.strategy_used,
                "confidence": recommendation.confidence_score,
            },
        )
        return workload

    @staticmethod
    def transition_workload_status(
        session: Session,
        workload_id: str,
        target_status: WorkloadStatus,
        failure_reason: Optional[str] = None,
    ) -> Workload:
        """
        Transition workload through its lifecycle state machine.
        Maintains node active workload counts and records timestamps.
        """
        workload = WorkloadService.get_workload_by_id(session, workload_id)
        current = workload.status
        target = target_status.value

        allowed = WorkloadService.VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidStateTransitionException(
                entity_type="Workload",
                entity_id=workload.id,
                current_state=current,
                target_state=target,
            )

        now = utcnow()
        workload.status = target

        if target == WorkloadStatus.RUNNING.value:
            workload.started_at = now
        elif target in (WorkloadStatus.COMPLETED.value, WorkloadStatus.CANCELLED.value):
            workload.completed_at = now
            if workload.assigned_node_id:
                node = session.get(Node, workload.assigned_node_id)
                if node and node.active_workload_count > 0:
                    node.active_workload_count -= 1
                    if node.active_workload_count == 0 and node.status == NodeStatus.BUSY.value:
                        node.status = NodeStatus.READY.value
        elif target == WorkloadStatus.FAILED.value:
            workload.completed_at = now
            workload.failure_reason = failure_reason or "Unknown failure"
            if workload.assigned_node_id:
                node = session.get(Node, workload.assigned_node_id)
                if node and node.active_workload_count > 0:
                    node.active_workload_count -= 1
                    if node.active_workload_count == 0 and node.status == NodeStatus.BUSY.value:
                        node.status = NodeStatus.READY.value

        elif target == WorkloadStatus.PENDING.value and current == WorkloadStatus.FAILED.value:
            # Retrying failed workload - enforce max_retries limit
            if workload.retry_count >= workload.max_retries:
                raise InvalidStateTransitionException(
                    entity_type="Workload",
                    entity_id=workload.id,
                    current_state=current,
                    target_state=target,
                )
            workload.retry_count += 1
            workload.assigned_node_id = None
            workload.scheduled_at = None
            workload.started_at = None
            workload.completed_at = None
            workload.failure_reason = None

        session.commit()
        session.refresh(workload)
        logger.info(
            "Workload transitioned state",
            extra={"workload_id": workload.id, "from": current, "to": target},
        )
        return workload

    @staticmethod
    def cancel_workload(session: Session, workload_id: str) -> Workload:
        """Cancel a pending, scheduled, or running workload."""
        return WorkloadService.transition_workload_status(
            session=session,
            workload_id=workload_id,
            target_status=WorkloadStatus.CANCELLED,
        )
