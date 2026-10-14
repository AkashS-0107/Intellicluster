"""
Unit tests for INTELLICLUSTER Machine Learning runtime components:
- PyTorch architectures (ResourceLSTM, QNetwork)
- MLModelRegistry lifecycle and caching
- Direct inference pipelines (KMeans, AI4I, LSTM, Infrastructure IF, DQN)
- Quarantine and rejection enforcement
"""

import pytest
import torch
import numpy as np
import pandas as pd

from intellicluster.ml.architectures import QNetwork, ResourceLSTM
from intellicluster.ml.registry import MLModelRegistry, ModelOperationalStatus
from intellicluster.ml.services import (
    AI4IInferenceService,
    DQNBenchmarkService,
    InfrastructureAnomalyService,
    InsufficientHistoryException,
    KMeansInferenceService,
    LSTMForecastingService,
    ModelNotReadyException,
    ModelRejectedException,
)
from intellicluster.schemas.ml import (
    AI4IInferenceRequestSchema,
    DQNPlacementRequestSchema,
    InfrastructureAnomalyRequestSchema,
    KMeansInferenceRequestSchema,
)


def test_resource_lstm_forward_shape():
    """ResourceLSTM outputs (batch, 24, 3) from (batch, 168, 5) input."""
    net = ResourceLSTM()
    dummy_x = torch.randn(2, 168, 5)
    out = net(dummy_x)
    assert out.shape == (2, 24, 3)
    assert not torch.isnan(out).any()


def test_q_network_forward_shape():
    """QNetwork outputs (batch, 4) from (batch, 25) input."""
    net = QNetwork()
    dummy_x = torch.randn(3, 25)
    out = net(dummy_x)
    assert out.shape == (3, 4)
    assert not torch.isnan(out).any()


def test_ml_registry_initialization():
    """MLModelRegistry singleton loads artifacts once and caches them."""
    registry = MLModelRegistry.get_instance()
    assert len(registry.catalog) == 7

    # Check eligible models are loaded
    art1 = registry.get_loaded_artifact("model-1")
    assert "model" in art1 and "preprocessor" in art1

    art2a = registry.get_loaded_artifact("model-2a")
    assert "model" in art2a

    art3 = registry.get_loaded_artifact("model-3")
    assert "model" in art3 and "scaler" in art3

    art4b = registry.get_loaded_artifact("model-4b")
    assert "model" in art4b

    art5 = registry.get_loaded_artifact("model-5")
    assert "model" in art5

    # Check rejected models raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        registry.get_loaded_artifact("model-2b")
    assert "REJECTED" in str(exc_info.value)

    with pytest.raises(PermissionError) as exc_info:
        registry.get_loaded_artifact("model-4a")
    assert "REJECTED" in str(exc_info.value)


def test_kmeans_service_direct_inference():
    """KMeansInferenceService maps hardware features to cluster ID 0-3."""
    req = KMeansInferenceRequestSchema(
        cpu_cores=32.0,
        memory_gb=128.0,
        vm_instances=8,
        container_replicas=24,
        storage_iops=20000,
        network_bandwidth_mbps=5000.0,
        cpu_utilization_pct=60.0,
        memory_utilization_pct=45.0,
        network_utilization_pct=35.0,
        disk_utilization_pct=40.0,
        request_rate_rps=2000.0,
        load_balancer_capacity=8000.0,
        application_tier="Database",
    )
    res = KMeansInferenceService.predict_archetype(req)
    assert res.predicted_cluster in [0, 1, 2, 3]
    assert res.transformed_feature_dim == 18
    assert res.strategy_used == "kmeans_v1"


def test_ai4i_service_direct_inference():
    """AI4IInferenceService produces probability and class."""
    req = AI4IInferenceRequestSchema(
        air_temperature_k=298.1,
        process_temperature_k=308.6,
        rotational_speed_rpm=1551.0,
        torque_nm=42.8,
        tool_wear_min=0.0,
        machine_type="M",
    )
    res = AI4IInferenceService.predict_failure_risk(req)
    assert 0.0 <= res.failure_probability <= 1.0
    assert res.predicted_class in [0, 1]
    assert res.risk_level in ["LOW", "ELEVATED", "HIGH", "CRITICAL"]


def test_lstm_forecasting_direct_matrix():
    """LSTMForecastingService inverts scale and yields 24 step objects."""
    matrix = [[45.0, 50.0, 60.0, 80.0, 60.0] for _ in range(168)]
    steps = LSTMForecastingService.forecast_from_matrix(matrix)
    assert len(steps) == 24
    for idx, s in enumerate(steps):
        assert s.step_hour == idx + 1
        assert isinstance(s.predicted_cpu_utilization, float)
        assert isinstance(s.predicted_memory_usage, float)
        assert isinstance(s.predicted_workload, float)


def test_infrastructure_anomaly_service():
    """InfrastructureAnomalyService evaluates density outlier score."""
    req = InfrastructureAnomalyRequestSchema(
        cpu_utilization=50.0,
        memory_usage=50.0,
        storage_usage=50.0,
        workload=50.0,
        resource_allocation=50.0,
    )
    res = InfrastructureAnomalyService.detect_anomaly(req)
    assert isinstance(res.anomaly_score, float)
    assert isinstance(res.is_anomaly, bool)


def test_dqn_service_direct_state():
    """DQNBenchmarkService evaluates Q-values on 25-dim vector."""
    req = DQNPlacementRequestSchema(state_vector=[0.5] * 25)
    res = DQNBenchmarkService.evaluate_placement(session=None, req=req)  # type: ignore
    assert res.recommended_action in [0, 1, 2, 3]
    assert len(res.q_values) == 4
    assert 0.0 <= res.confidence_score <= 1.0
    assert res.is_state_mutated is False
