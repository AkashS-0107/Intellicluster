"""
HTTP Integration tests for INTELLICLUSTER Machine Learning APIs (/api/v1/ml/*).
Verifies:
- Model catalog retrieval and operational status reporting
- Real KMeans server clustering inference
- Real AI4I failure prediction inference
- Real Multivariate LSTM sequence forecasting
- Insufficient historical telemetry rejection (422) for node forecasts
- Real Infrastructure Isolation Forest anomaly scoring
- Read-only DQN shadow benchmark without database mutation
- Quarantine and rejection enforcement for Model 2B and Model 4A
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from intellicluster.models.cluster import Cluster
from intellicluster.models.node import Node
from intellicluster.models.workload import Workload
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.core.constants import ClusterStatus, NodeStatus, WorkloadPriority, WorkloadStatus
from datetime import timedelta
from intellicluster.utils.datetime_utils import utcnow


# ==============================================================================
# 1. MODEL CATALOG TESTS
# ==============================================================================
def test_get_ml_models_catalog(client: TestClient):
    """GET /api/v1/ml/models returns all 7 models with correct operational statuses."""
    response = client.get("/api/v1/ml/models")
    assert response.status_code == 200
    data = response.json()
    assert data["total_models"] == 7

    models = {m["model_id"]: m for m in data["models"]}
    assert "model-1" in models
    assert "model-2a" in models
    assert "model-2b" in models
    assert "model-3" in models
    assert "model-4a" in models
    assert "model-4b" in models
    assert "model-5" in models

    # Check operational statuses
    assert models["model-1"]["operational_status"] == "READY"
    assert models["model-1"]["is_inference_enabled"] is True

    assert models["model-2a"]["operational_status"] == "READY"
    assert models["model-2a"]["is_inference_enabled"] is True

    assert models["model-2b"]["operational_status"] == "REJECTED"
    assert models["model-2b"]["is_inference_enabled"] is False
    assert "Disqualified" in models["model-2b"]["rejection_reason"]

    assert models["model-3"]["operational_status"] == "READY"
    assert models["model-3"]["is_inference_enabled"] is True

    assert models["model-4a"]["operational_status"] == "REJECTED"
    assert models["model-4a"]["is_inference_enabled"] is False
    assert "Disqualified" in models["model-4a"]["rejection_reason"]

    assert models["model-4b"]["operational_status"] == "READY"
    assert models["model-4b"]["is_inference_enabled"] is True

    assert models["model-5"]["operational_status"] == "EXPERIMENTAL"
    assert models["model-5"]["is_inference_enabled"] is True


# ==============================================================================
# 2. K-MEANS SERVER CLUSTERING INFERENCE TESTS
# ==============================================================================
def test_kmeans_server_clustering_inference_success(client: TestClient):
    """POST /api/v1/ml/cluster-archetype executes real KMeans prediction."""
    payload = {
        "cpu_cores": 16.0,
        "memory_gb": 64.0,
        "vm_instances": 4,
        "container_replicas": 12,
        "storage_iops": 10000,
        "network_bandwidth_mbps": 2500.0,
        "cpu_utilization_pct": 50.0,
        "memory_utilization_pct": 30.0,
        "network_utilization_pct": 40.0,
        "disk_utilization_pct": 25.0,
        "request_rate_rps": 1500.0,
        "load_balancer_capacity": 5000.0,
        "application_tier": "Application_Server",
    }
    response = client.post("/api/v1/ml/cluster-archetype", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["predicted_cluster"] in [0, 1, 2, 3]
    assert data["transformed_feature_dim"] == 18
    assert "archetype_name" in data
    assert "archetype_profile" in data
    assert data["strategy_used"] == "kmeans_v1"


def test_kmeans_inference_validation_error(client: TestClient):
    """POST /api/v1/ml/cluster-archetype rejects negative CPU cores with 422."""
    payload = {
        "cpu_cores": -4.0,  # Invalid
        "memory_gb": 64.0,
        "vm_instances": 4,
        "container_replicas": 12,
        "storage_iops": 10000,
        "network_bandwidth_mbps": 2500.0,
        "cpu_utilization_pct": 50.0,
        "memory_utilization_pct": 30.0,
        "network_utilization_pct": 40.0,
        "disk_utilization_pct": 25.0,
        "request_rate_rps": 1500.0,
        "load_balancer_capacity": 5000.0,
        "application_tier": "Application_Server",
    }
    response = client.post("/api/v1/ml/cluster-archetype", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 3. AI4I XGBOOST FAILURE PREDICTION TESTS
# ==============================================================================
def test_ai4i_predict_failure_success(client: TestClient):
    """POST /api/v1/ml/predict-failure executes real AI4I XGBoost probability."""
    payload = {
        "air_temperature_k": 300.0,
        "process_temperature_k": 310.0,
        "rotational_speed_rpm": 1500.0,
        "torque_nm": 40.0,
        "tool_wear_min": 100.0,
        "machine_type": "L",
    }
    response = client.post("/api/v1/ml/predict-failure", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert 0.0 <= data["failure_probability"] <= 1.0
    assert data["predicted_class"] in [0, 1]
    assert data["threshold_used"] == 0.50
    assert data["risk_level"] in ["LOW", "ELEVATED", "HIGH", "CRITICAL"]
    assert "industrial milling" in data["domain_advisory"]


def test_ai4i_predict_failure_high_stress(client: TestClient):
    """POST /api/v1/ml/predict-failure evaluates elevated risk on extreme wear/torque."""
    payload = {
        "air_temperature_k": 304.0,
        "process_temperature_k": 313.0,
        "rotational_speed_rpm": 1200.0,
        "torque_nm": 75.0,
        "tool_wear_min": 240.0,
        "machine_type": "H",
    }
    response = client.post("/api/v1/ml/predict-failure", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert 0.0 <= data["failure_probability"] <= 1.0


# ==============================================================================
# 4. MULTIVARIATE LSTM RESOURCE FORECASTING TESTS
# ==============================================================================
def test_lstm_direct_sequence_forecasting_success(client: TestClient):
    """POST /api/v1/ml/forecast-resources forecasts 24 hours given 168x5 sequence."""
    # Build valid 168-step sequence of 5 features
    seq = [[50.0, 45.0, 60.0, 80.0, 55.0] for _ in range(168)]
    response = client.post("/api/v1/ml/forecast-resources", json={"sequence": seq})
    assert response.status_code == 200
    data = response.json()

    assert data["forecast_horizon_hours"] == 24
    assert data["lookback_window_hours"] == 168
    assert len(data["predictions"]) == 24
    assert data["target_variables"] == ["cpu_utilization", "memory_usage", "workload"]

    first_step = data["predictions"][0]
    assert first_step["step_hour"] == 1
    assert isinstance(first_step["predicted_cpu_utilization"], float)
    assert isinstance(first_step["predicted_memory_usage"], float)
    assert isinstance(first_step["predicted_workload"], float)


def test_lstm_direct_sequence_invalid_length(client: TestClient):
    """POST /api/v1/ml/forecast-resources rejects sequences with != 168 steps with 422."""
    seq = [[50.0, 45.0, 60.0, 80.0, 55.0] for _ in range(50)]  # Only 50 steps
    response = client.post("/api/v1/ml/forecast-resources", json={"sequence": seq})
    assert response.status_code == 422


def test_lstm_node_forecasting_insufficient_history(client: TestClient, db_session: Session):
    """POST /api/v1/ml/forecast-node/{id} returns 422 when node has < 168 snapshots."""
    # Create cluster and node with only 5 snapshots
    cluster = Cluster(name="lstm-test-cluster", status=ClusterStatus.ACTIVE.value)
    db_session.add(cluster)
    db_session.commit()

    node = Node(
        hostname="lstm-test-node",
        cluster_id=cluster.id,
        cpu_cores=16.0,
        memory_mb=32768.0,
        status=NodeStatus.READY.value,
    )
    db_session.add(node)
    db_session.commit()

    # Add 5 snapshots
    now = utcnow()
    for _ in range(5):
        snap = TelemetrySnapshot(
            node_id=node.id,
            recorded_at=now,
            cpu_usage_pct=40.0,
            memory_usage_mb=16384.0,
            memory_usage_pct=50.0,
            disk_usage_gb=100.0,
            disk_usage_pct=20.0,
            network_rx_mbps=10.0,
            network_tx_mbps=10.0,
            network_latency_ms=5.0,
            active_connections=12,
            running_processes=80,
            temperature_celsius=45.0,
            reported_status="READY",
        )
        db_session.add(snap)
    db_session.commit()

    response = client.post(f"/api/v1/ml/forecast-node/{node.id}")
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INSUFFICIENT_TELEMETRY_HISTORY"
    assert "168 contiguous hourly snapshots" in data["message"]


def test_lstm_node_forecasting_valid_168_hours_success(client: TestClient, db_session: Session):
    """POST /api/v1/ml/forecast-node/{id} succeeds with 24-step forecast when 168 contiguous hourly snapshots exist."""
    cluster = Cluster(name="lstm-valid-cluster", status=ClusterStatus.ACTIVE.value)
    db_session.add(cluster)
    db_session.commit()

    node = Node(
        hostname="lstm-valid-node",
        cluster_id=cluster.id,
        cpu_cores=16.0,
        memory_mb=32768.0,
        status=NodeStatus.READY.value,
    )
    db_session.add(node)
    db_session.commit()

    # Seed exactly 168 contiguous hourly snapshots
    start_time = utcnow() - timedelta(hours=168)
    for i in range(168):
        snap = TelemetrySnapshot(
            node_id=node.id,
            recorded_at=start_time + timedelta(hours=i),
            cpu_usage_pct=52.0 + (i % 5),
            memory_usage_mb=16384.0,
            memory_usage_pct=48.0,
            disk_usage_gb=100.0,
            disk_usage_pct=55.0,
            network_rx_mbps=15.0,
            network_tx_mbps=12.0,
            network_latency_ms=4.0,
            active_connections=20,
            running_processes=90,
            temperature_celsius=42.0,
            reported_status="READY",
            workload=91.5 + (i % 3),
            resource_allocation=58.0 + (i % 4),
        )
        db_session.add(snap)
    db_session.commit()

    response = client.post(f"/api/v1/ml/forecast-node/{node.id}")
    assert response.status_code == 200
    data = response.json()

    assert data["forecast_horizon_hours"] == 24
    assert data["lookback_window_hours"] == 168
    assert len(data["predictions"]) == 24
    assert data["target_variables"] == ["cpu_utilization", "memory_usage", "workload"]

    # Verify predictions format
    for step in data["predictions"]:
        assert 1 <= step["step_hour"] <= 24
        assert isinstance(step["predicted_cpu_utilization"], float)
        assert isinstance(step["predicted_memory_usage"], float)
        assert isinstance(step["predicted_workload"], float)


def test_lstm_offline_evaluation_success(client: TestClient, db_session: Session):
    """POST /api/v1/ml/offline-evaluation runs offline dataset evaluation without mutating operational database."""
    # Count snapshots before
    initial_snapshots_count = db_session.query(TelemetrySnapshot).count()
    initial_nodes_count = db_session.query(Node).count()

    payload = {"start_hour_index": 0}
    response = client.post("/api/v1/ml/offline-evaluation", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["dataset_name"] == "Resource_utilization.csv"
    assert data["lookback_window_hours"] == 168
    assert data["forecast_horizon_hours"] == 24
    assert len(data["predictions"]) == 24
    assert data["target_variables"] == ["cpu_utilization", "memory_usage", "workload"]
    assert "OFFLINE DATASET BENCHMARK" in data["advisory"]

    # Verify zero database mutation
    db_session.expire_all()
    assert db_session.query(TelemetrySnapshot).count() == initial_snapshots_count
    assert db_session.query(Node).count() == initial_nodes_count


# ==============================================================================
# 5. INFRASTRUCTURE ANOMALY ISOLATION FOREST TESTS
# ==============================================================================
def test_infrastructure_anomaly_detection_nominal(client: TestClient):
    """POST /api/v1/ml/detect-anomaly scores normal resource metrics."""
    payload = {
        "cpu_utilization": 45.0,
        "memory_usage": 50.0,
        "storage_usage": 40.0,
        "workload": 60.0,
        "resource_allocation": 55.0,
    }
    response = client.post("/api/v1/ml/detect-anomaly", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["anomaly_score"], float)
    assert isinstance(data["is_anomaly"], bool)
    assert data["contamination_rate"] == 0.05
    assert "Contextual outlier indicator" in data["advisory"]


def test_infrastructure_anomaly_detection_extreme(client: TestClient):
    """POST /api/v1/ml/detect-anomaly handles extreme saturation values without error."""
    payload = {
        "cpu_utilization": 135.0,  # Legitimate saturation peak
        "memory_usage": 98.0,
        "storage_usage": 115.0,
        "workload": 250.0,
        "resource_allocation": 120.0,
    }
    response = client.post("/api/v1/ml/detect-anomaly", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["is_anomaly"], bool)


# ==============================================================================
# 6. DQN LOAD BALANCER SHADOW BENCHMARK TESTS
# ==============================================================================
def test_dqn_placement_benchmark_explicit_state(client: TestClient):
    """POST /api/v1/ml/dqn-placement-recommendation evaluates explicit 25-dim state."""
    state = [1.0] * 25
    response = client.post("/api/v1/ml/dqn-placement-recommendation", json={"state_vector": state})
    assert response.status_code == 200
    data = response.json()

    assert data["recommended_action"] in [0, 1, 2, 3]
    assert len(data["q_values"]) == 4
    assert 0.0 <= data["confidence_score"] <= 1.0
    assert data["is_state_mutated"] is False
    assert "HeuristicSchedulerStrategy remains the active production scheduler" in data["active_scheduler_policy"]


def test_dqn_placement_benchmark_zero_state_mutation(client: TestClient, db_session: Session):
    """Asserts that calling DQN recommendation does NOT mutate workload state."""
    cluster = Cluster(name="dqn-test-cluster", status=ClusterStatus.ACTIVE.value)
    db_session.add(cluster)
    db_session.commit()

    node = Node(
        hostname="dqn-candidate-01",
        cluster_id=cluster.id,
        cpu_cores=16.0,
        memory_mb=32768.0,
        status=NodeStatus.READY.value,
    )
    db_session.add(node)
    db_session.commit()

    workload = Workload(
        name="test-pending-task",
        cluster_id=cluster.id,
        cpu_cores_requested=4.0,
        memory_mb_requested=8192.0,
        priority=WorkloadPriority.HIGH.value,
        status=WorkloadStatus.PENDING.value,
    )
    db_session.add(workload)
    db_session.commit()
    workload_id = workload.id

    # Call DQN shadow benchmark
    response = client.post(
        "/api/v1/ml/dqn-placement-recommendation",
        json={"workload_id": workload_id, "candidate_node_ids": [node.id]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_state_mutated"] is False
    assert data["heuristic_comparison"] is not None

    # Verify database state was NOT mutated
    db_session.expire_all()
    reloaded_workload = db_session.get(Workload, workload_id)
    assert reloaded_workload is not None
    assert reloaded_workload.status == WorkloadStatus.PENDING.value
    assert reloaded_workload.assigned_node_id is None


# ==============================================================================
# 7. REJECTED MODEL QUARANTINE ENFORCEMENT
# ==============================================================================
def test_rejected_models_inference_blocked(client: TestClient):
    """POST /api/v1/ml/models/{id}/infer explicitly rejects Model 2B and Model 4A with 403."""
    resp_2b = client.post("/api/v1/ml/models/model-2b/infer")
    assert resp_2b.status_code == 403
    assert resp_2b.json()["error_code"] == "MODEL_REJECTED"
    assert "Disqualified" in resp_2b.json()["message"]

    resp_4a = client.post("/api/v1/ml/models/model-4a/infer")
    assert resp_4a.status_code == 403
    assert resp_4a.json()["error_code"] == "MODEL_REJECTED"
    assert "Disqualified" in resp_4a.json()["message"]


# ==============================================================================
# 8. TELEMETRY READINESS & SIMULATOR LIFECYCLE APIS
# ==============================================================================
def test_node_history_readiness_api(client: TestClient, db_session: Session):
    """GET /api/v1/telemetry/nodes/{node_id}/readiness returns accurate readiness metrics."""
    cluster = Cluster(name="readiness-cluster", status=ClusterStatus.ACTIVE.value)
    db_session.add(cluster)
    db_session.commit()

    node = Node(hostname="readiness-node", cluster_id=cluster.id, cpu_cores=8.0, memory_mb=16384.0)
    db_session.add(node)
    db_session.commit()

    # Empty history
    resp = client.get(f"/api/v1/telemetry/nodes/{node.id}/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == node.id
    assert data["is_ready"] is False
    assert data["valid_hourly_observations"] == 0
    assert data["required_observations"] == 168
    assert data["readiness_percentage"] == 0.0

    # Add a single snapshot
    db_session.add(
        TelemetrySnapshot(
            node_id=node.id,
            recorded_at=utcnow(),
            cpu_usage_pct=45.0,
            memory_usage_mb=8192.0,
            memory_usage_pct=50.0,
            disk_usage_gb=100.0,
            disk_usage_pct=25.0,
            network_rx_mbps=10.0,
            network_tx_mbps=10.0,
            network_latency_ms=5.0,
            active_connections=12,
            reported_status="READY",
            workload=92.0,
            resource_allocation=60.0,
        )
    )
    db_session.commit()

    resp = client.get(f"/api/v1/telemetry/nodes/{node.id}/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_raw_snapshots"] == 1
    assert data["valid_hourly_observations"] == 1
    assert data["is_ready"] is False


def test_telemetry_simulator_api_lifecycle(client: TestClient):
    """Test GET status, POST start, duplicate start 409, and POST stop on simulator."""
    # Ensure simulator is stopped first
    client.post("/api/v1/telemetry/simulator/stop")

    # 1. Status
    resp = client.get("/api/v1/telemetry/simulator/status")
    assert resp.status_code == 200
    assert resp.json()["is_running"] is False

    # 2. Start
    start_resp = client.post("/api/v1/telemetry/simulator/start", json={"interval_seconds": 30})
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["is_running"] is True
    assert start_data["interval_seconds"] == 30

    # 3. Duplicate start -> 409
    dup_resp = client.post("/api/v1/telemetry/simulator/start", json={"interval_seconds": 15})
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error_code"] == "SIMULATOR_ALREADY_RUNNING"

    # 4. Stop
    stop_resp = client.post("/api/v1/telemetry/simulator/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["is_running"] is False
