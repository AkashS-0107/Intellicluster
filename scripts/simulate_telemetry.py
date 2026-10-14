"""
Standalone External Telemetry Collection Simulator CLI.

Simulates an external node agent or telemetry collector transmitting
periodic heartbeat payloads to IntelliCluster.

Usage:
    python scripts/simulate_telemetry.py [--interval SECONDS] [--node-id NODE_ID] [--url BASE_URL] [--count COUNT]

Example:
    python scripts/simulate_telemetry.py --interval 10 --count 10
"""

import argparse
import math
import random
import sys
import time
from typing import Optional
import urllib.error
import urllib.request
import json


def transmit_heartbeat(
    base_url: str,
    node_id: str,
    tick: int,
) -> bool:
    """Send a single heartbeat telemetry payload via HTTP."""
    base_cycle = math.sin(tick * 0.1) * 12.0
    cpu = round(min(95.0, max(15.0, 52.0 + base_cycle + random.uniform(-4.0, 4.0))), 2)
    mem = round(min(90.0, max(20.0, 50.0 + base_cycle * 0.7 + random.uniform(-3.0, 3.0))), 2)
    disk = round(min(80.0, max(15.0, 26.0 + (tick * 0.02) % 15.0 + random.uniform(-1.0, 1.0))), 2)
    workload = round(max(40.0, 92.5 + base_cycle * 1.2 + random.uniform(-5.0, 5.0)), 2)
    resource_allocation = round(min(98.0, max(25.0, 59.2 + base_cycle * 0.6 + random.uniform(-3.0, 3.0))), 2)

    payload = {
        "cpu_usage_pct": cpu,
        "memory_usage_mb": round((mem / 100.0) * 16384.0, 2),
        "memory_usage_pct": mem,
        "disk_usage_gb": round((disk / 100.0) * 500.0, 2),
        "disk_usage_pct": disk,
        "network_rx_mbps": round(random.uniform(5.0, 25.0), 2),
        "network_tx_mbps": round(random.uniform(5.0, 20.0), 2),
        "network_latency_ms": round(random.uniform(2.0, 8.0), 2),
        "active_connections": int(max(5, 20 + int(base_cycle * 0.5) + random.randint(-3, 3))),
        "running_processes": int(60 + int(base_cycle) + random.randint(-5, 5)),
        "temperature_celsius": round(42.0 + cpu * 0.15, 1),
        "reported_status": "READY",
        "workload": workload,
        "resource_allocation": resource_allocation,
    }

    url = f"{base_url.rstrip('/')}/api/v1/nodes/{node_id}/heartbeat"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print(
                    f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Heartbeat sent for {node_id} "
                    f"-> CPU: {cpu}%, RAM: {mem}%, Workload: {workload}, Alloc: {resource_allocation}%"
                )
                return True
    except Exception as e:
        print(f"Error sending heartbeat to {url}: {e}", file=sys.stderr)
        return False
    return False


def main():
    parser = argparse.ArgumentParser(description="External IntelliCluster Telemetry Simulator")
    parser.add_argument("--interval", type=int, default=10, help="Cadence in seconds (default: 10)")
    parser.add_argument("--node-id", type=str, default=None, help="Target node UUID")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--count", type=int, default=None, help="Total heartbeats to emit (default: infinite)")
    args = parser.parse_args()

    node_id = args.node_id
    if not node_id:
        # Fetch first node from backend
        try:
            req = urllib.request.Request(f"{args.url.rstrip('/')}/api/v1/nodes?limit=1")
            with urllib.request.urlopen(req, timeout=5) as resp:
                nodes = json.loads(resp.read().decode("utf-8"))
                if nodes:
                    node_id = nodes[0]["id"]
                    print(f"Auto-selected target node: {nodes[0]['hostname']} ({node_id})")
                else:
                    print("No nodes found in cluster. Register a node first.", file=sys.stderr)
                    sys.exit(1)
        except Exception as e:
            print(f"Could not connect to backend at {args.url}: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Starting external telemetry collection simulator on {args.url} (interval={args.interval}s)...")
    print("Press Ctrl+C to stop.")

    tick = 0
    try:
        while True:
            tick += 1
            transmit_heartbeat(args.url, node_id, tick)
            if args.count and tick >= args.count:
                print(f"Reached count limit ({args.count}). Exiting.")
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped by operator.")


if __name__ == "__main__":
    main()
