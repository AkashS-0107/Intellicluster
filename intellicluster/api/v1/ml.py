"""
API routes for INTELLICLUSTER Machine Learning Model operationalization (/api/v1/ml/).
Exposes model catalog, real KMeans clustering, AI4I failure prediction,
multivariate LSTM resource forecasting, infrastructure anomaly detection,
and read-only DQN placement recommendations.
"""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from intellicluster.api.deps import get_db
from intellicluster.ml.registry import MLModelRegistry
from intellicluster.ml.services import (
    AI4IInferenceService,
    DQNBenchmarkService,
    InfrastructureAnomalyService,
    KMeansInferenceService,
    LSTMForecastingService,
    ModelRejectedException,
)
from intellicluster.schemas.ml import (
    AI4IInferenceRequestSchema,
    AI4IInferenceResponseSchema,
    DQNPlacementRequestSchema,
    DQNPlacementResponseSchema,
    InfrastructureAnomalyRequestSchema,
    InfrastructureAnomalyResponseSchema,
    KMeansInferenceRequestSchema,
    KMeansInferenceResponseSchema,
    LSTMDirectForecastingRequestSchema,
    LSTMForecastingResponseSchema,
    ModelCatalogItemSchema,
    ModelCatalogResponseSchema,
    OfflineEvaluationRequestSchema,
    OfflineEvaluationResponseSchema,
)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get(
    "/models",
    response_model=ModelCatalogResponseSchema,
    summary="Get ML Model Catalog",
    description=(
        "Returns catalog of all registered machine learning systems, including their "
        "operational status (READY, REJECTED, EXPERIMENTAL, ERROR), capabilities, "
        "verified offline metrics, and documented limitations."
    ),
)
def get_model_catalog() -> ModelCatalogResponseSchema:
    registry = MLModelRegistry.get_instance()
    items = registry.get_catalog_list()
    return ModelCatalogResponseSchema(
        total_models=len(items),
        models=[ModelCatalogItemSchema(**item) for item in items],
    )


@router.post(
    "/cluster-archetype",
    response_model=KMeansInferenceResponseSchema,
    summary="KMeans Server Archetype Profiling",
    description=(
        "Executes real inference on Model 1 (KMeans server clustering). Preprocesses "
        "the 13-feature input vector into the 18-dimensional space and maps the observation "
        "to one of 4 stable compute archetypes."
    ),
)
def predict_cluster_archetype(
    payload: KMeansInferenceRequestSchema,
) -> KMeansInferenceResponseSchema:
    return KMeansInferenceService.predict_archetype(payload)


@router.post(
    "/predict-failure",
    response_model=AI4IInferenceResponseSchema,
    summary="AI4I Predictive Component Failure Risk",
    description=(
        "Executes real inference on Model 2A (AI4I XGBoost classifier). Evaluates industrial "
        "sensor measurements to predict component failure probability. Note domain limitation: "
        "this model expects physical machinery sensors, not server OS metrics."
    ),
)
def predict_hardware_failure(
    payload: AI4IInferenceRequestSchema,
) -> AI4IInferenceResponseSchema:
    return AI4IInferenceService.predict_failure_risk(payload)


@router.post(
    "/forecast-resources",
    response_model=LSTMForecastingResponseSchema,
    summary="LSTM Direct Sequence Resource Forecasting",
    description=(
        "Executes real forward pass on Model 3 (Multivariate LSTM) given an exact 168x5 "
        "observation matrix. Predicts 24 hours ahead for [cpu_utilization, memory_usage, workload]."
    ),
)
def forecast_resources_direct(
    payload: LSTMDirectForecastingRequestSchema,
) -> LSTMForecastingResponseSchema:
    predictions = LSTMForecastingService.forecast_from_matrix(payload.sequence)
    return LSTMForecastingResponseSchema(
        forecast_horizon_hours=24,
        lookback_window_hours=168,
        target_variables=["cpu_utilization", "memory_usage", "workload"],
        input_features_used=[
            "cpu_utilization",
            "memory_usage",
            "storage_usage",
            "workload",
            "Resource Allocation",
        ],
        predictions=predictions,
        historical_snapshots_evaluated=168,
        node_id=None,
        strategy_used="multivariate_lstm_v1",
    )


@router.post(
    "/forecast-node/{node_id}",
    response_model=LSTMForecastingResponseSchema,
    summary="LSTM 24h Node Resource Forecasting",
    description=(
        "Retrieves persisted historical telemetry snapshots for a node and executes the "
        "multivariate LSTM 24h forecast. Requires exactly 168 contiguous hourly snapshots (7 days). "
        "Returns 422 Unprocessable Entity if fewer snapshots exist."
    ),
)
def forecast_node_telemetry(
    node_id: str = Path(description="Target node UUID"),
    db: Session = Depends(get_db),
) -> LSTMForecastingResponseSchema:
    return LSTMForecastingService.forecast_for_node(db, node_id)


@router.post(
    "/offline-evaluation",
    response_model=OfflineEvaluationResponseSchema,
    summary="Model 3 Offline Dataset Benchmark Evaluation",
    description=(
        "Executes 24h LSTM inference against genuine historical dataset (data/Resource_utilization.csv). "
        "Evaluates a continuous 168-hour sequence from the training/test corpus. Zero database state "
        "is modified and outputs are clearly labeled as an offline dataset benchmark."
    ),
)
def evaluate_offline_dataset_forecast(
    payload: OfflineEvaluationRequestSchema = OfflineEvaluationRequestSchema(),
) -> OfflineEvaluationResponseSchema:
    return LSTMForecastingService.evaluate_offline_dataset(payload.start_hour_index)


@router.post(
    "/detect-anomaly",
    response_model=InfrastructureAnomalyResponseSchema,
    summary="Infrastructure Telemetry Anomaly Scoring",
    description=(
        "Executes real scoring on Model 4B (Infrastructure Isolation Forest). Returns "
        "contextual anomaly score and binary flag. Advisory signal only; does NOT trigger "
        "autonomous node cordoning or workload eviction."
    ),
)
def detect_infrastructure_anomaly(
    payload: InfrastructureAnomalyRequestSchema,
) -> InfrastructureAnomalyResponseSchema:
    return InfrastructureAnomalyService.detect_anomaly(payload)


@router.post(
    "/dqn-placement-recommendation",
    response_model=DQNPlacementResponseSchema,
    summary="DQN Shadow Placement Recommendation",
    description=(
        "Executes shadow benchmark evaluation using Model 5 (Deep Q-Network). Evaluates "
        "a 25-dimensional state vector and returns recommended action and Q-values alongside "
        "the heuristic baseline. Read-only; zero database workload state is modified. "
        "HeuristicSchedulerStrategy remains the active scheduler."
    ),
)
def evaluate_dqn_placement(
    payload: DQNPlacementRequestSchema,
    db: Session = Depends(get_db),
) -> DQNPlacementResponseSchema:
    return DQNBenchmarkService.evaluate_placement(db, payload)


@router.post(
    "/models/{model_id}/infer",
    summary="Generic Model Inference Gateway",
    description="Validates model availability. Rejects disqualified models (Models 2B and 4A).",
)
def generic_model_infer(
    model_id: str = Path(description="Model identifier"),
) -> dict:
    registry = MLModelRegistry.get_instance()
    item = registry.get_catalog_item(model_id)
    if not item:
        raise ModelRejectedException(model_id, reason="Model ID is not registered.")
    if item.operational_status.value == "REJECTED":
        raise ModelRejectedException(model_id, reason=item.rejection_reason)
    return {"message": f"Model {model_id} is ready. Use specialized endpoint for typed inference."}
