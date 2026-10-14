"""
Domain service for Telemetry ingestion, historical time-series queries, and cluster aggregations.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from intellicluster.core.exceptions import ClusterNotFoundException, NodeNotFoundException
from intellicluster.core.logging import logger
from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.schemas.telemetry import (
    AggregatedMetricsSummary,
    NodeHistoryReadinessSchema,
    TelemetryCreateSchema,
)
from intellicluster.services.node_service import NodeService
from intellicluster.utils.datetime_utils import utcnow


class TelemetryService:
    """Business logic for telemetry ingestion and aggregation."""

    @staticmethod
    def record_telemetry(
        session: Session,
        node_id: str,
        data: TelemetryCreateSchema,
    ) -> TelemetrySnapshot:
        """
        Record a telemetry sample from a node.
        Delegates updating node live metrics and health score, and saves the snapshot.
        """
        NodeService.process_heartbeat(session, node_id, data)

        stmt = (
            select(TelemetrySnapshot)
            .where(TelemetrySnapshot.node_id == node_id)
            .order_by(desc(TelemetrySnapshot.recorded_at))
            .limit(1)
        )
        snapshot = session.execute(stmt).scalar_one()
        logger.debug("Recorded telemetry snapshot", extra={"snapshot_id": snapshot.id, "node_id": node_id})
        return snapshot

    @staticmethod
    def get_node_telemetry_history(
        session: Session,
        node_id: str,
        limit: int = 100,
    ) -> list[TelemetrySnapshot]:
        """
        Retrieve historical telemetry snapshots for a node, ordered chronologically descending.
        """
        node = session.get(Node, node_id)
        if not node:
            raise NodeNotFoundException(node_id=node_id)

        stmt = (
            select(TelemetrySnapshot)
            .where(TelemetrySnapshot.node_id == node_id)
            .order_by(desc(TelemetrySnapshot.recorded_at))
            .limit(limit)
        )
        return list(session.execute(stmt).scalars().all())

    @staticmethod
    def get_cluster_aggregated_metrics(
        session: Session,
        cluster_id: Optional[str] = None,
    ) -> AggregatedMetricsSummary:
        """
        Compute real-time cluster-wide aggregated utilization and latency metrics
        across active reporting nodes.
        """
        if cluster_id:
            cluster = session.get(Cluster, cluster_id)
            if not cluster:
                raise ClusterNotFoundException(cluster_id=cluster_id)

        stmt = select(Node)
        if cluster_id:
            stmt = stmt.where(Node.cluster_id == cluster_id)
        nodes = list(session.execute(stmt).scalars().all())

        total_nodes = len(nodes)
        if total_nodes == 0:
            return AggregatedMetricsSummary(
                cluster_id=cluster_id,
                total_reporting_nodes=0,
                avg_cpu_usage_pct=0.0,
                max_cpu_usage_pct=0.0,
                avg_memory_usage_pct=0.0,
                max_memory_usage_pct=0.0,
                avg_latency_ms=0.0,
                total_active_connections=0,
                recorded_at=utcnow(),
            )

        cpu_usages = [n.current_cpu_usage_pct for n in nodes]
        mem_usages = [
            (n.current_memory_usage_mb / n.memory_mb * 100.0) if n.memory_mb > 0 else 0.0
            for n in nodes
        ]
        latencies = [n.current_network_latency_ms for n in nodes]
        connections = sum(n.active_connections for n in nodes)

        return AggregatedMetricsSummary(
            cluster_id=cluster_id,
            total_reporting_nodes=total_nodes,
            avg_cpu_usage_pct=round(sum(cpu_usages) / total_nodes, 2),
            max_cpu_usage_pct=round(max(cpu_usages), 2),
            avg_memory_usage_pct=round(sum(mem_usages) / total_nodes, 2),
            max_memory_usage_pct=round(max(mem_usages), 2),
            avg_latency_ms=round(sum(latencies) / total_nodes, 2),
            total_active_connections=connections,
            recorded_at=utcnow(),
        )

    @staticmethod
    def validate_node_hourly_history(
        session: Session,
        node_id: str,
        required_hours: int = 168,
    ) -> tuple[bool, NodeHistoryReadinessSchema, Optional[list[list[float]]]]:
        """
        Validate historical telemetry for node against strict hourly LSTM lookback requirements:
        1. Selects the correct node and verifies existence.
        2. Normalizes all snapshot timestamps to timezone-aware UTC.
        3. Groups observations into 1-hour UTC buckets (e.g., 14:00:00Z to 14:59:59Z).
        4. Applies deterministic aggregation: arithmetic mean of features across samples in each hour.
           Multiple heartbeats in a single hour are aggregated into exactly ONE hourly observation;
           they NEVER count as multiple hourly observations.
        5. Verifies contiguity: checks that exactly required_hours consecutive 1-hour intervals are present
           without missing intervals or gaps up to the latest observation.
        6. Validates feature readiness for all 5 required LSTM features:
           [cpu_utilization, memory_usage, storage_usage, workload, Resource Allocation].
        7. Returns (is_ready, readiness_schema, observation_matrix_or_none).
        """
        node = session.get(Node, node_id)
        if not node:
            raise NodeNotFoundException(node_id=node_id)

        # Fetch all snapshots chronologically ascending
        stmt = (
            select(TelemetrySnapshot)
            .where(TelemetrySnapshot.node_id == node_id)
            .order_by(TelemetrySnapshot.recorded_at.asc())
        )
        snapshots = list(session.execute(stmt).scalars().all())

        total_raw = len(snapshots)
        if total_raw == 0:
            readiness = NodeHistoryReadinessSchema(
                node_id=node_id,
                is_ready=False,
                valid_hourly_observations=0,
                required_observations=required_hours,
                readiness_percentage=0.0,
                total_raw_snapshots=0,
                earliest_usable_timestamp=None,
                latest_usable_timestamp=None,
                missing_intervals_count=required_hours,
                missing_ranges=[],
                validation_reason=(
                    f"Zero historical snapshots found for node '{node.hostname}' ({node_id}). "
                    f"Model requires {required_hours} contiguous hourly snapshots (7 days). "
                    "Transmit periodic heartbeats to begin historical timeline accumulation."
                ),
                estimated_hours_remaining=float(required_hours),
                collector_active=False,
                is_simulated=False,
                feature_readiness={
                    "cpu_utilization": False,
                    "memory_usage": False,
                    "storage_usage": False,
                    "workload": False,
                    "resource_allocation": False,
                },
            )
            return False, readiness, None

        # 1. Normalize timestamps to UTC and bin into hourly buckets
        hourly_buckets: dict[datetime, list[TelemetrySnapshot]] = defaultdict(list)
        for s in snapshots:
            dt = s.recorded_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            # Truncate to hour boundary (YYYY-MM-DD HH:00:00 UTC)
            hour_key = dt.replace(minute=0, second=0, microsecond=0)
            hourly_buckets[hour_key].append(s)

        sorted_hours = sorted(hourly_buckets.keys())
        earliest_dt = sorted_hours[0]
        latest_dt = sorted_hours[-1]

        # 2. Deterministic aggregation per bucket
        aggregated_hours: dict[datetime, dict[str, Any]] = {}
        has_simulated = False
        for h, snaps in hourly_buckets.items():
            avg_cpu = sum(s.cpu_usage_pct for s in snaps) / len(snaps)
            avg_mem = sum(s.memory_usage_pct for s in snaps) / len(snaps)
            avg_disk = sum(s.disk_usage_pct for s in snaps) / len(snaps)

            # Workload & Resource Allocation feature availability
            workloads = [s.workload for s in snaps if s.workload is not None]
            avg_workload = (sum(workloads) / len(workloads)) if workloads else None

            allocations = [s.resource_allocation for s in snaps if s.resource_allocation is not None]
            avg_allocation = (sum(allocations) / len(allocations)) if allocations else None

            if any(s.workload is not None or s.resource_allocation is not None for s in snaps):
                has_simulated = True

            aggregated_hours[h] = {
                "cpu": avg_cpu,
                "memory": avg_mem,
                "storage": avg_disk,
                "workload": avg_workload,
                "allocation": avg_allocation,
                "sample_count": len(snaps),
            }

        # 3. Detect all gaps across entire recorded history
        missing_intervals_count = 0
        missing_ranges: list[str] = []
        for i in range(len(sorted_hours) - 1):
            h_curr = sorted_hours[i]
            h_next = sorted_hours[i + 1]
            diff_hours = int((h_next - h_curr).total_seconds() // 3600)
            if diff_hours > 1:
                gap = diff_hours - 1
                missing_intervals_count += gap
                start_gap = (h_curr + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
                end_gap = (h_next - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
                missing_ranges.append(f"{start_gap} to {end_gap} ({gap}h missing)")

        # 4. Measure contiguous run ending at latest bucket
        contiguous_run = 1
        for i in range(len(sorted_hours) - 1, 0, -1):
            if sorted_hours[i] - sorted_hours[i - 1] == timedelta(hours=1):
                contiguous_run += 1
            else:
                break

        # Check feature readiness over the contiguous run ending at latest_dt
        candidate_hours = sorted_hours[-contiguous_run:]
        missing_workload_hours = sum(1 for h in candidate_hours if aggregated_hours[h]["workload"] is None)
        missing_alloc_hours = sum(1 for h in candidate_hours if aggregated_hours[h]["allocation"] is None)

        feat_ready = {
            "cpu_utilization": True,
            "memory_usage": True,
            "storage_usage": True,
            "workload": missing_workload_hours == 0,
            "resource_allocation": missing_alloc_hours == 0,
        }
        all_features_ready = all(feat_ready.values())

        is_ready = (contiguous_run >= required_hours) and all_features_ready
        readiness_pct = round(min(100.0, (contiguous_run / required_hours) * 100.0), 1)
        hours_remaining = max(0.0, float(required_hours - contiguous_run))

        # Check simulator state if service exists
        collector_active = False
        try:
            from intellicluster.services.telemetry_simulator_service import TelemetrySimulatorService
            collector_active = TelemetrySimulatorService.get_instance().get_status().get("is_running", False)
        except Exception:
            pass

        # Build precise validation reason
        earliest_iso = earliest_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        latest_iso = latest_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        if contiguous_run < required_hours:
            reason = (
                f"Node '{node.hostname}' has {contiguous_run} valid contiguous hourly observation(s) "
                f"(range: {earliest_iso} to {latest_iso}). Model requires exactly {required_hours} "
                f"contiguous hourly snapshots (7 days). Remaining time needed: {int(hours_remaining)} hour(s) "
                f"of continuous hourly collection."
            )
            if missing_intervals_count > 0:
                reason += (
                    f" Historical timeline has {len(missing_ranges)} gap(s) totaling "
                    f"{missing_intervals_count} missing hour(s)."
                )
        elif not all_features_ready:
            missing_names = [k for k, v in feat_ready.items() if not v]
            reason = (
                f"Node '{node.hostname}' satisfies {contiguous_run} contiguous hours, but required features are unavailable: "
                f"{', '.join(missing_names)}. Ensure telemetry reports explicit workload demand and allocation values."
            )
        else:
            reason = (
                f"Node '{node.hostname}' history fully qualified: {contiguous_run} contiguous hourly observations "
                f"ready for 24h LSTM multivariate forecasting."
            )

        readiness = NodeHistoryReadinessSchema(
            node_id=node_id,
            is_ready=is_ready,
            valid_hourly_observations=contiguous_run,
            required_observations=required_hours,
            readiness_percentage=readiness_pct,
            total_raw_snapshots=total_raw,
            earliest_usable_timestamp=earliest_dt,
            latest_usable_timestamp=latest_dt,
            missing_intervals_count=missing_intervals_count,
            missing_ranges=missing_ranges[:5],
            validation_reason=reason,
            estimated_hours_remaining=hours_remaining,
            collector_active=collector_active,
            is_simulated=has_simulated,
            feature_readiness=feat_ready,
        )

        matrix = None
        if is_ready:
            # Build exactly 168x5 sequence chronologically from the last 168 hours
            target_hours = sorted_hours[-required_hours:]
            matrix = []
            for h in target_hours:
                agg = aggregated_hours[h]
                matrix.append([
                    float(agg["cpu"]),
                    float(agg["memory"]),
                    float(agg["storage"]),
                    float(agg["workload"]),
                    float(agg["allocation"]),
                ])

        return is_ready, readiness, matrix
