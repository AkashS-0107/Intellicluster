"""
Domain service for Cluster lifecycle and aggregate capacity management.
"""

from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from intellicluster.core.constants import ClusterStatus, NodeStatus, WorkloadStatus
from intellicluster.core.exceptions import (
    ClusterAlreadyExistsException,
    ClusterNotFoundException,
)
from intellicluster.core.logging import logger
from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.workload import Workload
from intellicluster.schemas.cluster import (
    ClusterCapacitySummary,
    ClusterCreateSchema,
    ClusterUpdateSchema,
)


class ClusterService:
    """Business logic for clusters."""

    @staticmethod
    def create_cluster(session: Session, data: ClusterCreateSchema) -> Cluster:
        """Create a new cluster after verifying uniqueness of name."""
        stmt = select(Cluster).where(Cluster.name == data.name)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            raise ClusterAlreadyExistsException(identifier=data.name)

        cluster = Cluster(
            name=data.name,
            description=data.description,
            status=data.status.value,
        )
        session.add(cluster)
        session.commit()
        session.refresh(cluster)
        logger.info("Cluster created successfully", extra={"cluster_id": cluster.id, "name": cluster.name})
        return cluster

    @staticmethod
    def get_cluster_by_id(session: Session, cluster_id: str) -> Cluster:
        """Retrieve cluster by ID or raise ClusterNotFoundException."""
        cluster = session.get(Cluster, cluster_id)
        if not cluster:
            raise ClusterNotFoundException(cluster_id=cluster_id)
        return cluster

    @staticmethod
    def list_clusters(
        session: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[ClusterStatus] = None,
    ) -> list[Cluster]:
        """List clusters with pagination and optional status filter."""
        stmt = select(Cluster).offset(skip).limit(limit)
        if status:
            stmt = stmt.where(Cluster.status == status.value)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_cluster(session: Session, cluster_id: str, data: ClusterUpdateSchema) -> Cluster:
        """Update cluster metadata or status."""
        cluster = ClusterService.get_cluster_by_id(session, cluster_id)
        if data.name is not None and data.name != cluster.name:
            stmt = select(Cluster).where(Cluster.name == data.name)
            conflict = session.execute(stmt).scalar_one_or_none()
            if conflict:
                raise ClusterAlreadyExistsException(identifier=data.name)
            cluster.name = data.name

        if data.description is not None:
            cluster.description = data.description
        if data.status is not None:
            cluster.status = data.status.value

        session.commit()
        session.refresh(cluster)
        logger.info("Cluster updated", extra={"cluster_id": cluster.id})
        return cluster

    @staticmethod
    def calculate_cluster_capacity(session: Session, cluster_id: str) -> ClusterCapacitySummary:
        """
        Calculates aggregate hardware capacity, allocated resources, and current utilization.
        """
        cluster = ClusterService.get_cluster_by_id(session, cluster_id)

        nodes_stmt = select(Node).where(Node.cluster_id == cluster_id)
        nodes = list(session.execute(nodes_stmt).scalars().all())

        total_nodes = len(nodes)
        ready_nodes = sum(1 for n in nodes if n.status == NodeStatus.READY.value and not n.is_cordoned)
        total_cpu = sum(n.cpu_cores for n in nodes)
        total_mem = sum(n.memory_mb for n in nodes)

        active_statuses = [WorkloadStatus.SCHEDULED.value, WorkloadStatus.RUNNING.value]
        node_ids = [n.id for n in nodes]
        if node_ids:
            workloads_stmt = select(Workload).where(
                (Workload.cluster_id == cluster_id) | (Workload.assigned_node_id.in_(node_ids)),
                Workload.status.in_(active_statuses),
            )
        else:
            workloads_stmt = select(Workload).where(
                Workload.cluster_id == cluster_id,
                Workload.status.in_(active_statuses),
            )
        active_workloads = list(session.execute(workloads_stmt).scalars().all())

        allocated_cpu = sum(w.cpu_cores_requested for w in active_workloads)
        allocated_mem = sum(w.memory_mb_requested for w in active_workloads)

        allocatable_cpu = max(0.0, total_cpu - allocated_cpu)
        allocatable_mem = max(0.0, total_mem - allocated_mem)

        avg_cpu_pct = (sum(n.current_cpu_usage_pct for n in nodes) / total_nodes) if total_nodes > 0 else 0.0
        avg_mem_pct = (
            (sum((n.current_memory_usage_mb / n.memory_mb * 100.0) for n in nodes if n.memory_mb > 0) / total_nodes)
            if total_nodes > 0
            else 0.0
        )

        return ClusterCapacitySummary(
            cluster_id=cluster.id,
            cluster_name=cluster.name,
            total_nodes=total_nodes,
            ready_nodes=ready_nodes,
            total_cpu_cores=round(total_cpu, 2),
            allocated_cpu_cores=round(allocated_cpu, 2),
            allocatable_cpu_cores=round(allocatable_cpu, 2),
            total_memory_mb=round(total_mem, 2),
            allocated_memory_mb=round(allocated_mem, 2),
            allocatable_memory_mb=round(allocatable_mem, 2),
            average_cpu_usage_pct=round(avg_cpu_pct, 2),
            average_memory_usage_pct=round(avg_mem_pct, 2),
            active_workload_count=len(active_workloads),
        )
