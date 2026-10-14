"""
Data Transfer Objects (DTOs) for the ML boundary.
Defines normalized feature contracts and prediction response envelopes.
"""

from typing import Optional
from pydantic import Field

from intellicluster.schemas.common import BaseSchema


class WorkloadPlacementFeatures(BaseSchema):
    """
    Normalized feature vector representing workload demand and candidate node state.
    """

    # Workload features
    workload_type: str
    priority_level: int = Field(ge=1, le=4)
    cpu_cores_requested: float = Field(gt=0.0)
    memory_mb_requested: float = Field(gt=0.0)
    network_mbps_requested: float = Field(ge=0.0)
    max_latency_tolerance_ms: float = Field(ge=0.0)

    # Candidate Node features
    node_id: str
    node_total_cpu: float = Field(gt=0.0)
    node_total_memory_mb: float = Field(gt=0.0)
    node_allocatable_cpu: float = Field(ge=0.0)
    node_allocatable_memory_mb: float = Field(ge=0.0)
    node_current_cpu_pct: float = Field(ge=0.0, le=100.0)
    node_current_mem_pct: float = Field(ge=0.0, le=100.0)
    node_network_latency_ms: float = Field(ge=0.0)
    node_active_workloads: int = Field(ge=0)
    node_health_score: float = Field(ge=0.0, le=100.0)


class PlacementRecommendation(BaseSchema):
    """Result of an orchestration placement evaluation."""

    recommended_node_id: Optional[str] = Field(
        default=None,
        description="ID of the selected optimal node, or None if no candidate qualifies",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level of the recommendation (0.0 to 1.0)",
    )
    predicted_latency_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Estimated execution round-trip latency on the recommended node",
    )
    strategy_used: str = Field(
        description="Name of the strategy/model providing this decision (e.g. 'heuristic', 'xgboost_v1')",
    )
    reasoning: str = Field(
        description="Human-interpretable explanation of why the node was selected or rejected",
    )


class HealthPrediction(BaseSchema):
    """Placeholder prediction result for future ML node health/anomaly forecasting."""

    node_id: str
    predicted_risk_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated probability of failure or degradation (0.0=safe, 1.0=critical)",
    )
    is_anomaly: bool = Field(
        default=False,
        description="Whether current telemetry trends indicate an anomalous pattern",
    )
    strategy_used: str = Field(
        description="Strategy or model identifier producing the prediction",
    )
    reasoning: str = Field(
        description="Diagnostic explanation of factors contributing to the risk score",
    )
