"""
Pydantic v2 schemas for INTELLICLUSTER Machine Learning APIs (/api/v1/ml/).
Enforces strict input validation, bounds checking, finite numeric guarantees,
and structured inference responses.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
import math


class ModelCatalogItemSchema(BaseModel):
    """Catalog entry describing a machine learning system."""

    model_id: str
    name: str
    system_role: str
    algorithm: str
    artifact_files: list[str]
    operational_status: str
    is_inference_enabled: bool
    rejection_reason: Optional[str] = None
    capabilities: list[str] = []
    limitations: Optional[str] = None
    verified_metrics: dict[str, Any] = {}
    schema_contract: Optional[str] = None
    is_loaded: bool = False
    load_error: Optional[str] = None


class ModelCatalogResponseSchema(BaseModel):
    """Response containing list of all registered models."""

    total_models: int
    models: list[ModelCatalogItemSchema]


# Model 1: KMeans Server Clustering Schemas

class KMeansInferenceRequestSchema(BaseModel):
    """Request payload for Model 1 (KMeans Server Archetype Profiling)."""

    cpu_cores: float = Field(gt=0, description="Physical/vCPU count (e.g. 16.0)")
    memory_gb: float = Field(gt=0, description="System RAM in Gigabytes (e.g. 64.0)")
    vm_instances: int = Field(ge=0, description="Virtual machine instance count (e.g. 4)")
    container_replicas: int = Field(ge=0, description="Active container replicas (e.g. 12)")
    storage_iops: int = Field(ge=0, description="Target storage IOPS limit (e.g. 10000)")
    network_bandwidth_mbps: float = Field(gt=0, description="Network throughput in Mbps (e.g. 2500.0)")
    cpu_utilization_pct: float = Field(ge=0.0, le=100.0, description="Current CPU load % (e.g. 50.0)")
    memory_utilization_pct: float = Field(ge=0.0, le=100.0, description="Current RAM load % (e.g. 30.0)")
    network_utilization_pct: float = Field(ge=0.0, le=100.0, description="Current Network load % (e.g. 40.0)")
    disk_utilization_pct: float = Field(ge=0.0, le=100.0, description="Current Disk load % (e.g. 25.0)")
    request_rate_rps: float = Field(ge=0.0, description="Incoming requests per second (e.g. 1500.0)")
    load_balancer_capacity: float = Field(gt=0, description="Load balancer throughput capacity (e.g. 5000.0)")
    application_tier: str = Field(
        default="Application_Server",
        description="Application tier: 'Application_Server', 'Database', 'Frontend', 'Cache', etc.",
    )

    @field_validator(
        "cpu_cores",
        "memory_gb",
        "network_bandwidth_mbps",
        "cpu_utilization_pct",
        "memory_utilization_pct",
        "network_utilization_pct",
        "disk_utilization_pct",
        "request_rate_rps",
        "load_balancer_capacity",
    )
    @classmethod
    def check_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Numeric values must be finite numbers.")
        return v


class KMeansInferenceResponseSchema(BaseModel):
    """Response payload for Model 1 (KMeans)."""

    predicted_cluster: int
    archetype_name: str
    archetype_profile: dict[str, Any]
    transformed_feature_dim: int = 18
    strategy_used: str = "kmeans_v1"


# Model 2A: AI4I Failure Prediction Schemas

class AI4IInferenceRequestSchema(BaseModel):
    """
    Request payload for Model 2A (Hardware Failure Prediction).
    CRITICAL: Validated on industrial sensor metrics (UCI AI4I 2020 dataset).
    """

    air_temperature_k: float = Field(gt=0, description="Ambient air temperature in Kelvin (e.g. 300.0)")
    process_temperature_k: float = Field(gt=0, description="Process temperature in Kelvin (e.g. 310.0)")
    rotational_speed_rpm: float = Field(gt=0, description="Rotational tool speed in RPM (e.g. 1500.0)")
    torque_nm: float = Field(ge=0, description="Drive torque in Newton-meters (e.g. 40.0)")
    tool_wear_min: float = Field(ge=0, description="Accumulated tool wear in minutes (e.g. 100.0)")
    machine_type: str = Field(
        default="L",
        description="Machine quality type: 'L' (Low), 'M' (Medium), or 'H' (High)",
    )

    @field_validator(
        "air_temperature_k",
        "process_temperature_k",
        "rotational_speed_rpm",
        "torque_nm",
        "tool_wear_min",
    )
    @classmethod
    def check_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Numeric sensor values must be finite numbers.")
        return v


class AI4IInferenceResponseSchema(BaseModel):
    """Response payload for Model 2A (AI4I)."""

    failure_probability: float = Field(ge=0.0, le=1.0)
    predicted_class: int = Field(description="0 (Normal) or 1 (Imminent Failure)")
    threshold_used: float = 0.50
    risk_level: str = Field(description="LOW, ELEVATED, HIGH, or CRITICAL")
    domain_advisory: str = Field(
        default=(
            "Trained on industrial milling sensor measurements. Does not directly map to server OS "
            "metrics. Low precision (38.64%) produces false alarms; evaluate alongside health score."
        )
    )
    strategy_used: str = "ai4i_xgboost_v1"


# Model 3: LSTM Resource Forecasting Schemas

class ForecastStepSchema(BaseModel):
    """Hourly forecast prediction step."""

    step_hour: int
    predicted_cpu_utilization: float
    predicted_memory_usage: float
    predicted_workload: float


class LSTMDirectForecastingRequestSchema(BaseModel):
    """
    Request for direct LSTM inference providing a 168x5 observation matrix.
    Lookback window: exactly 168 sequential time steps.
    Features per step: [cpu_utilization, memory_usage, storage_usage, workload, Resource Allocation].
    """

    sequence: list[list[float]] = Field(
        description="Matrix of shape (168, 5) representing 168 hourly time steps of 5 metrics."
    )

    @field_validator("sequence")
    @classmethod
    def validate_matrix_shape(cls, seq: list[list[float]]) -> list[list[float]]:
        if len(seq) != 168:
            raise ValueError(f"LSTM input requires exactly 168 hourly sequence steps. Received {len(seq)}.")
        for idx, step in enumerate(seq):
            if len(step) != 5:
                raise ValueError(
                    f"Step {idx+1} has {len(step)} features. Exactly 5 features required: "
                    "[cpu_utilization, memory_usage, storage_usage, workload, Resource Allocation]."
                )
            for val in step:
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"Step {idx+1} contains non-finite values (NaN/Inf).")
        return seq


class LSTMNodeForecastingRequestSchema(BaseModel):
    """Request to generate forecast from a persisted node's historical telemetry."""

    node_id: str


class LSTMForecastingResponseSchema(BaseModel):
    """Response payload for Model 3 (Multivariate LSTM)."""

    forecast_horizon_hours: int = 24
    lookback_window_hours: int = 168
    target_variables: list[str] = ["cpu_utilization", "memory_usage", "workload"]
    input_features_used: list[str] = [
        "cpu_utilization",
        "memory_usage",
        "storage_usage",
        "workload",
        "Resource Allocation",
    ]
    predictions: list[ForecastStepSchema]
    historical_snapshots_evaluated: int
    node_id: Optional[str] = None
    strategy_used: str = "multivariate_lstm_v1"


class OfflineEvaluationRequestSchema(BaseModel):
    """Request payload for evaluating Model 3 on verified historical dataset (Resource_utilization.csv)."""

    start_hour_index: int = Field(
        default=0,
        ge=0,
        description="Starting row offset in Resource_utilization.csv (must leave at least 168 rows)",
    )


class OfflineEvaluationResponseSchema(BaseModel):
    """Response payload for offline dataset LSTM forecasting evaluation."""

    dataset_name: str = "Resource_utilization.csv"
    dataset_total_records: int = 26305
    evaluation_range: str
    forecast_horizon_hours: int = 24
    lookback_window_hours: int = 168
    target_variables: list[str] = ["cpu_utilization", "memory_usage", "workload"]
    input_features_used: list[str] = [
        "cpu_utilization",
        "memory_usage",
        "storage_usage",
        "workload",
        "Resource Allocation",
    ]
    predictions: list[ForecastStepSchema]
    is_offline_benchmark: bool = True
    advisory: str = (
        "OFFLINE DATASET BENCHMARK: Inference executed against genuine historical dataset "
        "(data/Resource_utilization.csv). This does NOT represent live node telemetry and zero database state is modified."
    )
    strategy_used: str = "multivariate_lstm_v1_offline_dataset"


# Model 4B: Infrastructure Anomaly Isolation Forest Schemas

class InfrastructureAnomalyRequestSchema(BaseModel):
    """Request payload for Model 4B (Infrastructure Anomaly Detection)."""

    cpu_utilization: float = Field(ge=0.0, description="CPU utilization value (e.g. 85.0)")
    memory_usage: float = Field(ge=0.0, description="Memory usage metric (e.g. 70.0)")
    storage_usage: float = Field(ge=0.0, description="Storage usage metric (e.g. 60.0)")
    workload: float = Field(ge=0.0, description="Workload demand score (e.g. 95.0)")
    resource_allocation: float = Field(ge=0.0, description="Resource allocation metric (e.g. 80.0)")

    @field_validator(
        "cpu_utilization",
        "memory_usage",
        "storage_usage",
        "workload",
        "resource_allocation",
    )
    @classmethod
    def check_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Numeric metrics must be finite numbers.")
        return v


class InfrastructureAnomalyResponseSchema(BaseModel):
    """Response payload for Model 4B (Isolation Forest)."""

    anomaly_score: float = Field(description="Negative anomaly score; higher values indicate greater anomaly")
    is_anomaly: bool = Field(description="True if flagged as multivariate density outlier (-1 label)")
    contamination_rate: float = 0.05
    advisory: str = (
        "Contextual outlier indicator only. Captures multivariate density anomalies (25% of extreme saturation). "
        "Must NOT be used to trigger autonomous node cordoning, node deletion, or workload migration."
    )
    strategy_used: str = "infrastructure_iforest_v1"


# Model 5: DQN Load Balancing Benchmark Schemas

class DQNPlacementRequestSchema(BaseModel):
    """
    Request for Model 5 (DQN Load Balancer Shadow Benchmark).
    Accepts either an explicit 25-dim state vector or an existing workload_id with candidate node IDs.
    """

    state_vector: Optional[list[float]] = Field(
        default=None,
        description="Optional explicit 25-dim state vector for synthetic/simulation testing.",
    )
    workload_id: Optional[str] = Field(
        default=None,
        description="Optional existing workload ID to construct state vector against candidates.",
    )
    candidate_node_ids: Optional[list[str]] = Field(
        default=None,
        description="Optional list of candidate node IDs (up to 4 nodes) to evaluate.",
    )

    @field_validator("state_vector")
    @classmethod
    def validate_state_vector(cls, v: Optional[list[float]]) -> Optional[list[float]]:
        if v is not None:
            if len(v) != 25:
                raise ValueError(f"DQN state vector must be exactly 25 dimensions. Received {len(v)}.")
            for val in v:
                if math.isnan(val) or math.isinf(val):
                    raise ValueError("State vector contains non-finite values (NaN/Inf).")
        return v


class DQNPlacementResponseSchema(BaseModel):
    """Response payload for Model 5 (DQN). Read-only; zero database mutation."""

    recommended_action: int = Field(description="Selected node archetype index (0 to 3)")
    recommended_archetype_name: str
    archetype_profile: dict[str, Any]
    q_values: list[float] = Field(description="Predicted Q-values for all 4 actions")
    confidence_score: float = Field(description="Softmax probability of recommended action")
    is_state_mutated: bool = Field(
        default=False,
        description="Affirmation that this recommendation is read-only and did not schedule or mutate workloads.",
    )
    active_scheduler_policy: str = "HeuristicSchedulerStrategy remains the active production scheduler."
    heuristic_comparison: Optional[dict[str, Any]] = None
    strategy_used: str = "dqn_v1_shadow_benchmark"
