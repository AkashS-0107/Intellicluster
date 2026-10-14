"""
Domain service for Node management, heartbeats, liveness, and capacity tracking.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from intellicluster.core.config import settings
from intellicluster.core.constants import NodeStatus, WorkloadStatus
from intellicluster.core.exceptions import (
    ClusterNotFoundException,
    NodeAlreadyExistsException,
    NodeNotFoundException,
)
from intellicluster.core.logging import logger
from intellicluster.ml.heuristic import calculate_deterministic_health_score
from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload
from intellicluster.schemas.node import (
    NodeCapacitySummary,
    NodeRegisterSchema,
    NodeUpdateSchema,
)
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.utils.datetime_utils import utcnow


class NodeService:
    """Business logic for compute nodes."""

    @staticmethod
    def register_node(session: Session, data: NodeRegisterSchema) -> Node:
        """Register a new server/node in the cluster."""
        stmt = select(Node).where(Node.hostname == data.hostname)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            raise NodeAlreadyExistsException(identifier=data.hostname)

        if data.cluster_id:
            cluster = session.get(Cluster, data.cluster_id)
            if not cluster:
                raise ClusterNotFoundException(cluster_id=data.cluster_id)

        node = Node(
            hostname=data.hostname,
            ip_address=data.ip_address,
            cluster_id=data.cluster_id,
            status=NodeStatus.READY.value,
            cpu_cores=data.cpu_cores,
            memory_mb=data.memory_mb,
            storage_gb=data.storage_gb,
            network_bandwidth_mbps=data.network_bandwidth_mbps,
            health_score=100.0,
            risk_score=0.0,
            active_workload_count=0,
            last_heartbeat=utcnow(),
            is_cordoned=False,
        )
        session.add(node)
        session.commit()
        session.refresh(node)
        logger.info(
            "Node registered successfully",
            extra={"node_id": node.id, "hostname": node.hostname, "cores": node.cpu_cores},
        )
        return node

    @staticmethod
    def get_node_by_id(session: Session, node_id: str) -> Node:
        """Retrieve node by ID or raise NodeNotFoundException."""
        node = session.get(Node, node_id)
        if not node:
            raise NodeNotFoundException(node_id=node_id)
        return node

    @staticmethod
    def get_node_by_hostname(session: Session, hostname: str) -> Optional[Node]:
        """Find node by hostname, returns None if not found."""
        stmt = select(Node).where(Node.hostname == hostname)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_nodes(
        session: Session,
        cluster_id: Optional[str] = None,
        status: Optional[NodeStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Node]:
        """List nodes with optional filtering by cluster and status."""
        NodeService.mark_stale_nodes(session)
        stmt = select(Node).offset(skip).limit(limit)
        if cluster_id:
            stmt = stmt.where(Node.cluster_id == cluster_id)
        if status:
            stmt = stmt.where(Node.status == status.value)
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def update_node(session: Session, node_id: str, data: NodeUpdateSchema) -> Node:
        """Update node metadata, cluster attachment, or cordoning."""
        node = NodeService.get_node_by_id(session, node_id)

        if data.hostname is not None and data.hostname != node.hostname:
            existing = NodeService.get_node_by_hostname(session, data.hostname)
            if existing:
                raise NodeAlreadyExistsException(identifier=data.hostname)
            node.hostname = data.hostname

        if data.ip_address is not None:
            node.ip_address = data.ip_address
        if data.cluster_id is not None:
            if data.cluster_id:
                cluster = session.get(Cluster, data.cluster_id)
                if not cluster:
                    raise ClusterNotFoundException(cluster_id=data.cluster_id)
            node.cluster_id = data.cluster_id
        if data.status is not None:
            node.status = data.status.value
        if data.is_cordoned is not None:
            node.is_cordoned = data.is_cordoned

        session.commit()
        session.refresh(node)
        logger.info("Node updated", extra={"node_id": node.id, "status": node.status})
        return node

    @staticmethod
    def cordon_node(session: Session, node_id: str) -> Node:
        """Cordon node to prevent new workloads from being scheduled."""
        node = NodeService.get_node_by_id(session, node_id)
        node.is_cordoned = True
        session.commit()
        session.refresh(node)
        logger.info("Node cordoned", extra={"node_id": node.id, "hostname": node.hostname})
        return node

    @staticmethod
    def uncordon_node(session: Session, node_id: str) -> Node:
        """Uncordon node to re-allow workload scheduling."""
        node = NodeService.get_node_by_id(session, node_id)
        node.is_cordoned = False
        session.commit()
        session.refresh(node)
        logger.info("Node uncordoned", extra={"node_id": node.id, "hostname": node.hostname})
        return node

    @staticmethod
    def process_heartbeat(
        session: Session,
        node_id: str,
        telemetry: TelemetryCreateSchema,
    ) -> Node:
        """
        Process a heartbeat report from a node agent:
        1. Validate node existence.
        2. Update last_heartbeat timestamp.
        3. Update cached current resource metrics.
        4. Calculate deterministic health score.
        5. Evaluate automatic status degradation/recovery.
        6. Append historical TelemetrySnapshot.
        7. Safely commit and return the node.
        """
        node = NodeService.get_node_by_id(session, node_id)
        now = utcnow()

        node.last_heartbeat = now
        node.current_cpu_usage_pct = telemetry.cpu_usage_pct
        node.current_memory_usage_mb = telemetry.memory_usage_mb
        node.current_disk_usage_gb = telemetry.disk_usage_gb
        node.current_network_tx_mbps = telemetry.network_tx_mbps
        node.current_network_rx_mbps = telemetry.network_rx_mbps
        node.current_network_latency_ms = telemetry.network_latency_ms
        node.active_connections = telemetry.active_connections

        node.health_score = calculate_deterministic_health_score(
            cpu_usage_pct=telemetry.cpu_usage_pct,
            memory_usage_pct=telemetry.memory_usage_pct,
            network_latency_ms=telemetry.network_latency_ms,
        )

        # Automatic status degradation or recovery if not administratively cordoned/draining
        if node.status not in (NodeStatus.DRAINING.value, NodeStatus.OFFLINE.value):
            if node.health_score < 30.0:
                node.status = NodeStatus.DEGRADED.value
            elif node.status == NodeStatus.DEGRADED.value and node.health_score >= 50.0:
                node.status = NodeStatus.READY.value
            elif node.status == NodeStatus.UNREACHABLE.value:
                node.status = NodeStatus.READY.value

        snapshot = TelemetrySnapshot(
            node_id=node.id,
            recorded_at=now,
            cpu_usage_pct=telemetry.cpu_usage_pct,
            memory_usage_mb=telemetry.memory_usage_mb,
            memory_usage_pct=telemetry.memory_usage_pct,
            disk_usage_gb=telemetry.disk_usage_gb,
            disk_usage_pct=telemetry.disk_usage_pct,
            network_rx_mbps=telemetry.network_rx_mbps,
            network_tx_mbps=telemetry.network_tx_mbps,
            network_latency_ms=telemetry.network_latency_ms,
            active_connections=telemetry.active_connections,
            running_processes=telemetry.running_processes,
            temperature_celsius=telemetry.temperature_celsius,
            reported_status=telemetry.reported_status.value,
            workload=telemetry.workload,
            resource_allocation=telemetry.resource_allocation,
        )
        session.add(snapshot)

        session.commit()
        session.refresh(node)
        logger.debug(
            "Processed heartbeat for node",
            extra={"node_id": node.id, "health": node.health_score, "status": node.status},
        )
        return node

    @staticmethod
    def mark_stale_nodes(
        session: Session,
        timeout_seconds: Optional[int] = None,
    ) -> list[Node]:
        """
        Identify nodes that have not reported a heartbeat within the timeout window
        and transition their status to UNREACHABLE.
        """
        threshold = timeout_seconds or settings.NODE_HEARTBEAT_TIMEOUT_SECONDS
        now = utcnow()

        active_statuses = [
            NodeStatus.READY.value,
            NodeStatus.BUSY.value,
            NodeStatus.DEGRADED.value,
        ]
        stmt = select(Node).where(Node.status.in_(active_statuses))
        nodes = list(session.execute(stmt).scalars().all())

        stale_nodes: list[Node] = []
        for node in nodes:
            heartbeat = node.last_heartbeat
            if heartbeat.tzinfo is None:
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            age = (now - heartbeat).total_seconds()
            if age > threshold:
                old_status = node.status
                node.status = NodeStatus.UNREACHABLE.value
                stale_nodes.append(node)
                logger.warning(
                    "Node marked UNREACHABLE due to missed heartbeats",
                    extra={"node_id": node.id, "hostname": node.hostname, "age_sec": age, "old_status": old_status},
                )

        if stale_nodes:
            session.commit()
            for n in stale_nodes:
                session.refresh(n)

        return stale_nodes

    @staticmethod
    def get_allocatable_capacity(session: Session, node_id: str) -> NodeCapacitySummary:
        """
        Calculates total vs allocated vs allocatable CPU and RAM for a node.
        """
        node = NodeService.get_node_by_id(session, node_id)

        active_statuses = [WorkloadStatus.SCHEDULED.value, WorkloadStatus.RUNNING.value]
        stmt = select(Workload).where(
            Workload.assigned_node_id == node_id,
            Workload.status.in_(active_statuses),
        )
        workloads = list(session.execute(stmt).scalars().all())

        allocated_cpu = sum(w.cpu_cores_requested for w in workloads)
        allocated_mem = sum(w.memory_mb_requested for w in workloads)

        allocatable_cpu = max(0.0, node.cpu_cores - allocated_cpu)
        allocatable_mem = max(0.0, node.memory_mb - allocated_mem)

        is_allocatable = (
            not node.is_cordoned
            and node.status in (NodeStatus.READY.value, NodeStatus.BUSY.value)
            and allocatable_cpu > 0.0
            and allocatable_mem > 0.0
        )

        return NodeCapacitySummary(
            node_id=node.id,
            hostname=node.hostname,
            status=NodeStatus(node.status),
            is_cordoned=node.is_cordoned,
            is_allocatable=is_allocatable,
            total_cpu_cores=round(node.cpu_cores, 2),
            allocated_cpu_cores=round(allocated_cpu, 2),
            allocatable_cpu_cores=round(allocatable_cpu, 2),
            total_memory_mb=round(node.memory_mb, 2),
            allocated_memory_mb=round(allocated_mem, 2),
            allocatable_memory_mb=round(allocatable_mem, 2),
            active_workload_count=len(workloads),
            health_score=round(node.health_score, 2),
        )
