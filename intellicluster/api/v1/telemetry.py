"""
API routes for Telemetry ingestion, historical queries, and cluster-wide aggregation.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from intellicluster.api.deps import get_db
from intellicluster.schemas.telemetry import (
    AggregatedMetricsSummary,
    NodeHistoryReadinessSchema,
    SimulatorStartRequestSchema,
    SimulatorStatusSchema,
    TelemetryCreateSchema,
    TelemetryResponseSchema,
)
from intellicluster.services.telemetry_service import TelemetryService
from intellicluster.services.telemetry_simulator_service import TelemetrySimulatorService

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post(
    "/nodes/{node_id}",
    response_model=TelemetryResponseSchema,
    status_code=201,
    summary="Record a telemetry snapshot",
    description=(
        "Ingests a raw telemetry snapshot from a node agent. "
        "Updates the node's cached metrics and health score, and persists the record."
    ),
)
def record_telemetry(
    node_id: str,
    data: TelemetryCreateSchema,
    db: Session = Depends(get_db),
):
    snapshot = TelemetryService.record_telemetry(db, node_id, data)
    return snapshot


@router.get(
    "/nodes/{node_id}",
    response_model=list[TelemetryResponseSchema],
    summary="Get node telemetry history",
    description="Retrieves historical telemetry snapshots for a node, ordered most recent first.",
)
def get_node_telemetry(
    node_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum snapshots to return"),
    db: Session = Depends(get_db),
):
    snapshots = TelemetryService.get_node_telemetry_history(db, node_id, limit=limit)
    return snapshots


@router.get(
    "/nodes/{node_id}/readiness",
    response_model=NodeHistoryReadinessSchema,
    summary="Get node history readiness for forecasting",
    description=(
        "Evaluates whether a compute node has sufficient valid contiguous hourly historical snapshots "
        "(168 hours / 7 days) required for Model 3 LSTM forecasting."
    ),
)
def get_node_history_readiness(
    node_id: str,
    required_hours: int = Query(default=168, ge=1, le=720, description="Required contiguous hours"),
    db: Session = Depends(get_db),
):
    _, readiness, _ = TelemetryService.validate_node_hourly_history(
        session=db,
        node_id=node_id,
        required_hours=required_hours,
    )
    return readiness


@router.get(
    "/clusters/{cluster_id}/aggregate",
    response_model=AggregatedMetricsSummary,
    summary="Get cluster aggregated metrics",
    description=(
        "Computes real-time cluster-wide aggregated utilization and latency metrics "
        "across all reporting nodes in the cluster."
    ),
)
def get_cluster_aggregated_metrics(
    cluster_id: str,
    db: Session = Depends(get_db),
):
    return TelemetryService.get_cluster_aggregated_metrics(db, cluster_id)


@router.get(
    "/simulator/status",
    response_model=SimulatorStatusSchema,
    summary="Get telemetry collection simulator status",
    description="Returns current operational status of the opt-in development/demo telemetry simulator.",
)
def get_simulator_status():
    simulator = TelemetrySimulatorService.get_instance()
    return simulator.get_status()


@router.post(
    "/simulator/start",
    response_model=SimulatorStatusSchema,
    summary="Start opt-in telemetry simulator",
    description=(
        "Explicitly initiates recurring simulated heartbeat collection on a configured interval. "
        "Protected against duplicate runs. Emits genuine timestamped TelemetrySnapshots."
    ),
)
async def start_simulator(
    payload: SimulatorStartRequestSchema = SimulatorStartRequestSchema(),
):
    simulator = TelemetrySimulatorService.get_instance()
    return await simulator.start(
        interval_seconds=payload.interval_seconds,
        target_node_id=payload.target_node_id,
    )


@router.post(
    "/simulator/stop",
    response_model=SimulatorStatusSchema,
    summary="Stop opt-in telemetry simulator",
    description="Explicitly terminates the background telemetry simulation loop.",
)
async def stop_simulator():
    simulator = TelemetrySimulatorService.get_instance()
    return await simulator.stop()
