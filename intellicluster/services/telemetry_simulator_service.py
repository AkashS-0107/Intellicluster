"""
Opt-in Development & Demonstration Telemetry Simulator Service.
Provides controlled, configurable periodic heartbeat emission for compute nodes.

Lifecycle & Architecture Guarantees:
- Strictly opt-in: NEVER starts automatically on FastAPI application startup.
- Duplicate-start protection: Raises error if already active.
- Explicit start, stop, and status control via API and CLI.
- Emits genuine, timestamped TelemetrySnapshots via NodeService.process_heartbeat.
- Generates realistic operational metrics aligned with trained model distributions:
  - cpu_usage_pct: 35.0% - 75.0%
  - memory_usage_pct: 40.0% - 70.0%
  - disk_usage_pct: 20.0% - 35.0%
  - workload: 75.0 - 110.0 (aligned with Resource_utilization.csv distribution)
  - resource_allocation: 50.0% - 70.0% (aligned with Resource_utilization.csv distribution)
- Does not overwrite or backdate existing historical telemetry.
- Clean shutdown on application termination.
"""

import asyncio
from datetime import datetime, timezone
import math
import random
from typing import Any, Optional

from sqlalchemy.orm import Session

from intellicluster.core.constants import NodeStatus
from intellicluster.core.exceptions import IntelliClusterException, NodeNotFoundException
from intellicluster.core.logging import logger
from intellicluster.db.session import SessionLocal
from intellicluster.models.node import Node
from intellicluster.schemas.telemetry import TelemetryCreateSchema
from intellicluster.services.node_service import NodeService
from intellicluster.utils.datetime_utils import utcnow


class SimulatorAlreadyRunningException(IntelliClusterException):
    """Raised when an attempt is made to start an already running simulator."""

    def __init__(self) -> None:
        super().__init__(
            message="Telemetry collection simulator is already running.",
            error_code="SIMULATOR_ALREADY_RUNNING",
        )


class TelemetrySimulatorService:
    """
    Singleton manager for opt-in background telemetry simulation.
    Runs an asynchronous generator loop emitting realistic periodic heartbeats.
    """

    _instance: Optional["TelemetrySimulatorService"] = None

    def __init__(self) -> None:
        self._is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._interval_seconds: int = 60
        self._target_node_id: Optional[str] = None
        self._snapshots_emitted: int = 0
        self._started_at: Optional[datetime] = None
        self._tick_counter: int = 0
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "TelemetrySimulatorService":
        """Retrieve or initialize the singleton simulator service."""
        if cls._instance is None:
            cls._instance = TelemetrySimulatorService()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (primarily for testing)."""
        if cls._instance and cls._instance._is_running:
            if cls._instance._task:
                cls._instance._task.cancel()
        cls._instance = None

    def get_status(self) -> dict[str, Any]:
        """Return current simulator operational state."""
        return {
            "is_running": self._is_running,
            "interval_seconds": self._interval_seconds,
            "target_node_id": self._target_node_id,
            "snapshots_emitted": self._snapshots_emitted,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "collector_mode": "opt_in_development_simulator",
        }

    async def start(
        self,
        interval_seconds: int = 60,
        target_node_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Start the telemetry simulator background loop with duplicate-start prevention.
        """
        async with self._lock:
            if self._is_running:
                raise SimulatorAlreadyRunningException()

            # If target node specified, verify node exists in database
            if target_node_id:
                db: Session = SessionLocal()
                try:
                    node = db.get(Node, target_node_id)
                    if not node:
                        raise NodeNotFoundException(node_id=target_node_id)
                finally:
                    db.close()

            self._interval_seconds = max(1, interval_seconds)
            self._target_node_id = target_node_id
            self._snapshots_emitted = 0
            self._started_at = utcnow()
            self._tick_counter = 0
            self._is_running = True

            self._task = asyncio.create_task(self._collection_loop())
            logger.info(
                "Telemetry simulator started",
                extra={
                    "interval_sec": self._interval_seconds,
                    "target_node_id": self._target_node_id,
                },
            )
            return self.get_status()

    async def stop(self) -> dict[str, Any]:
        """Stop the running telemetry simulator and cleanly terminate background task."""
        async with self._lock:
            if not self._is_running:
                return self.get_status()

            self._is_running = False
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None

            logger.info(
                "Telemetry simulator stopped",
                extra={"snapshots_emitted": self._snapshots_emitted},
            )
            return self.get_status()

    async def _collection_loop(self) -> None:
        """Core collection loop emitting realistic telemetry on the configured cadence."""
        try:
            while self._is_running:
                self._emit_telemetry_tick()
                await asyncio.sleep(self._interval_seconds)
        except asyncio.CancelledError:
            logger.debug("Simulator task received cancellation.")
        except Exception as e:
            logger.error("Unexpected error in telemetry simulator loop: %s", e, exc_info=True)
            self._is_running = False

    def _emit_telemetry_tick(self) -> None:
        """Synchronously persist a telemetry snapshot for eligible nodes."""
        db: Session = SessionLocal()
        try:
            nodes_to_poll: list[Node] = []
            if self._target_node_id:
                node = db.get(Node, self._target_node_id)
                if node:
                    nodes_to_poll.append(node)
            else:
                nodes_to_poll = list(
                    db.query(Node)
                    .filter(Node.status.in_([NodeStatus.READY.value, NodeStatus.BUSY.value]))
                    .all()
                )

            self._tick_counter += 1
            t = self._tick_counter

            for node in nodes_to_poll:
                # Generate realistic oscillating operational telemetry within training data bounds
                # Base sine wave + small noise
                base_cycle = math.sin(t * 0.1) * 12.0
                cpu = round(min(95.0, max(15.0, 52.0 + base_cycle + random.uniform(-4.0, 4.0))), 2)
                mem = round(min(90.0, max(20.0, 50.0 + base_cycle * 0.7 + random.uniform(-3.0, 3.0))), 2)
                disk = round(min(80.0, max(15.0, 26.0 + (t * 0.02) % 15.0 + random.uniform(-1.0, 1.0))), 2)

                # Workload demand matching Resource_utilization.csv mean ~92.5, range 70-120
                workload_val = round(max(40.0, 92.5 + base_cycle * 1.2 + random.uniform(-5.0, 5.0)), 2)
                # Resource allocation ratio matching Resource_utilization.csv mean ~59.2%, range 45-75
                allocation_val = round(min(98.0, max(25.0, 59.2 + base_cycle * 0.6 + random.uniform(-3.0, 3.0))), 2)

                mem_mb = round((mem / 100.0) * node.memory_mb, 2)
                disk_gb = round((disk / 100.0) * node.storage_gb, 2)

                telemetry = TelemetryCreateSchema(
                    cpu_usage_pct=cpu,
                    memory_usage_mb=mem_mb,
                    memory_usage_pct=mem,
                    disk_usage_gb=disk_gb,
                    disk_usage_pct=disk,
                    network_rx_mbps=round(random.uniform(5.0, 25.0), 2),
                    network_tx_mbps=round(random.uniform(5.0, 20.0), 2),
                    network_latency_ms=round(random.uniform(2.0, 8.0), 2),
                    active_connections=max(5, 20 + int(base_cycle * 0.5) + random.randint(-3, 3)),
                    running_processes=60 + int(base_cycle) + random.randint(-5, 5),
                    temperature_celsius=round(42.0 + cpu * 0.15, 1),
                    reported_status=NodeStatus.READY,
                    workload=workload_val,
                    resource_allocation=allocation_val,
                )

                NodeService.process_heartbeat(db, node.id, telemetry)
                self._snapshots_emitted += 1

            db.commit()
        except Exception as e:
            logger.error("Failed to emit telemetry heartbeat tick: %s", e)
            db.rollback()
        finally:
            db.close()
