"""
Repeatable, non-destructive local demonstration workflow for INTELLICLUSTER.
Opt-in command providing legitimate demonstration node onboarding,
heartbeat telemetry transmission, and workload scheduling.

Usage:
    python -m intellicluster.demo
    python -m intellicluster.demo --schedule
    python -m intellicluster.demo --cleanup
    python -m intellicluster.demo --status
"""

import argparse
import sys
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from intellicluster.core.constants import NodeStatus, WorkloadStatus
from intellicluster.core.logging import logger
from intellicluster.db.session import SessionLocal
from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload
from intellicluster.schemas.node import NodeRegisterSchema
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.services.cluster_service import ClusterService
from intellicluster.services.node_service import NodeService
from intellicluster.services.workload_service import WorkloadService

DEMO_HOSTNAME = "demo-node-01.simulated"
DEMO_IP = "10.0.1.101"
DEMO_CPU_CORES = 8.0
DEMO_MEMORY_MB = 16384.0
DEMO_STORAGE_GB = 500.0
DEMO_NETWORK_MBPS = 1000.0


def print_status(session: Session) -> None:
    """Print current operational database state without modifying anything."""
    clusters = list(session.execute(select(Cluster)).scalars().all())
    nodes = list(session.execute(select(Node)).scalars().all())
    workloads = list(session.execute(select(Workload)).scalars().all())
    snapshot_count = session.execute(select(TelemetrySnapshot)).scalars().all()

    print("\n========================================================")
    print("        INTELLICLUSTER OPERATIONAL STATE SUMMARY        ")
    print("========================================================")
    print(f"Clusters ({len(clusters)}):")
    for c in clusters:
        print(f"  - [{c.id[:8]}] {c.name} ({c.status})")

    print(f"\nNodes ({len(nodes)}):")
    for n in nodes:
        print(
            f"  - [{n.id[:8]}] {n.hostname} | Status: {n.status} | "
            f"Health: {n.health_score:.1f} | CPU: {n.cpu_cores}c | "
            f"RAM: {n.memory_mb:.0f}MB | Active Tasks: {n.active_workload_count}"
        )

    print(f"\nWorkloads ({len(workloads)}):")
    for w in workloads:
        assigned = f"Node [{w.assigned_node_id[:8]}]" if w.assigned_node_id else "Unassigned"
        print(
            f"  - [{w.id[:8]}] {w.name} ({w.workload_type}) | Status: {w.status} | "
            f"Demands: {w.cpu_cores_requested}c, {w.memory_mb_requested:.0f}MB | {assigned}"
        )

    print(f"\nTelemetry Snapshots: {len(snapshot_count)} recorded")
    print("========================================================\n")


def run_demo(
    cluster_name: Optional[str] = "test-c1",
    schedule_pending: bool = False,
) -> dict[str, str]:
    """
    Non-destructive, idempotent demonstration onboarding:
    1. Finds target cluster (or first active cluster).
    2. Registers DEMO_HOSTNAME if not already registered (idempotent).
    3. Transmits an initial simulated heartbeat snapshot.
    4. Optionally schedules compatible pending workloads.
    """
    with SessionLocal() as session:
        # 1. Resolve target cluster
        cluster = None
        if cluster_name:
            stmt = select(Cluster).where(Cluster.name == cluster_name)
            cluster = session.execute(stmt).scalar_one_or_none()

        if not cluster:
            stmt = select(Cluster).where(Cluster.status == "ACTIVE")
            cluster = session.execute(stmt).scalars().first()

        if not cluster:
            print("[-] No active cluster found. Please create a cluster first.")
            return {"status": "error", "message": "No active cluster found"}

        cluster_id = cluster.id
        print(f"[+] Target cluster resolved: '{cluster.name}' (ID: {cluster_id})")

        # 2. Check if demo node already exists
        existing_node = NodeService.get_node_by_hostname(session, DEMO_HOSTNAME)
        if existing_node:
            node = existing_node
            print(f"[!] Demo node already registered: {node.hostname} (ID: {node.id})")
        else:
            print(f"[+] Registering demonstration compute node: {DEMO_HOSTNAME}...")
            register_data = NodeRegisterSchema(
                hostname=DEMO_HOSTNAME,
                ip_address=DEMO_IP,
                cluster_id=cluster_id,
                cpu_cores=DEMO_CPU_CORES,
                memory_mb=DEMO_MEMORY_MB,
                storage_gb=DEMO_STORAGE_GB,
                network_bandwidth_mbps=DEMO_NETWORK_MBPS,
            )
            node = NodeService.register_node(session, register_data)
            print(f"[+] Registered node successfully: ID={node.id}, Hostname={node.hostname}")

        # 3. Transmit simulated heartbeat
        print(f"[+] Submitting simulated demonstration heartbeat for node {node.hostname}...")
        telemetry = TelemetryCreateSchema(
            cpu_usage_pct=24.5,
            memory_usage_mb=4096.0,
            memory_usage_pct=25.0,
            disk_usage_gb=120.0,
            disk_usage_pct=24.0,
            network_rx_mbps=25.0,
            network_tx_mbps=12.5,
            network_latency_ms=4.5,
            active_connections=16,
            running_processes=42,
            temperature_celsius=48.5,
            reported_status=NodeStatus.READY,
        )
        updated_node = NodeService.process_heartbeat(session, node.id, telemetry)
        print(
            f"[+] Heartbeat processed: Status={updated_node.status}, "
            f"Health={updated_node.health_score:.1f}/100, Telemetry snapshot committed."
        )

        # 4. Schedule pending workloads if requested
        scheduled_count = 0
        if schedule_pending:
            print("[+] Checking for PENDING workloads to schedule...")
            pending_stmt = select(Workload).where(Workload.status == WorkloadStatus.PENDING.value)
            pending_workloads = list(session.execute(pending_stmt).scalars().all())

            for wl in pending_workloads:
                print(f"[+] Evaluating pending workload '{wl.name}' (CPU={wl.cpu_cores_requested}, RAM={wl.memory_mb_requested})...")
                try:
                    scheduled = WorkloadService.schedule_pending_workload(session, wl.id)
                    assigned_id = scheduled.assigned_node_id[:8] if scheduled.assigned_node_id else "unknown"
                    print(
                        f"[+] Successfully scheduled workload '{scheduled.name}' onto node "
                        f"[{assigned_id}]!"
                    )
                    scheduled_count += 1
                except Exception as e:
                    print(f"[-] Could not schedule '{wl.name}': {str(e)}")

        print_status(session)
        return {
            "status": "success",
            "cluster_id": cluster_id,
            "node_id": node.id,
            "hostname": node.hostname,
            "scheduled_workloads": str(scheduled_count),
        }


def cleanup_demo() -> None:
    """
    Cleanly remove the demonstration node and its snapshots without touching user records.
    If any workloads were assigned to the demo node, reset them back to PENDING.
    """
    with SessionLocal() as session:
        node = NodeService.get_node_by_hostname(session, DEMO_HOSTNAME)
        if not node:
            print(f"[*] No demonstration node '{DEMO_HOSTNAME}' found to clean up.")
            return

        print(f"[+] Found demonstration node '{node.hostname}' (ID: {node.id}). Cleaning up...")

        # Reset any workloads assigned to this demo node back to PENDING
        stmt = select(Workload).where(Workload.assigned_node_id == node.id)
        assigned_workloads = list(session.execute(stmt).scalars().all())
        for w in assigned_workloads:
            w.assigned_node_id = None
            w.status = WorkloadStatus.PENDING.value
            w.scheduled_at = None
            print(f"[+] Reset workload '{w.name}' back to PENDING.")

        session.delete(node)
        session.commit()
        print(f"[+] Demo node '{DEMO_HOSTNAME}' and its telemetry snapshots successfully removed.")
        print_status(session)


def main():
    parser = argparse.ArgumentParser(
        description="INTELLICLUSTER Local Demonstration & Operational Validation Workflow",
    )
    parser.add_argument(
        "--cluster",
        default="test-c1",
        help="Target cluster name to attach the demonstration node to (default: test-c1)",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Attempt heuristic scheduling of compatible pending workloads",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanly remove demonstration node and reset assigned workloads",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current operational database state without modifying anything",
    )

    args = parser.parse_args()

    if args.status:
        with SessionLocal() as session:
            print_status(session)
        sys.exit(0)

    if args.cleanup:
        cleanup_demo()
        sys.exit(0)

    run_demo(cluster_name=args.cluster, schedule_pending=args.schedule)


if __name__ == "__main__":
    main()
