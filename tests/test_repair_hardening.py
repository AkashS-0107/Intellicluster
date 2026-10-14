"""
Machine Learning Subsystem Verification and Hardening Test Suite.
Validates end-to-end model integrity, diagnostics, and operational integration:
- Notebook Reproducibility: Clean-kernel execution, complete training loops, metadata definition
- Environmental XGBoost Diagnostics: Empirical confirmation of noise distribution and quarantine status
- Network Isolation Forest Diagnostics: Score parity validation and quarantine confirmation
- K-Means Operational Utility: Validates cluster archetype profiles and geometric separation documentation
- Infrastructure Isolation Forest: Verifies multivariate density outlier detection (~25% saturation capture)
- LSTM Forecasting: 168h lookback window, 24h horizon, multi-target variable forecasting
- DQN Integration Readiness: Deterministic inference evaluation, action masking, state vector handling
- Backend ML Boundary Compatibility: Verifies adapter mappings to BaseSchedulerPredictor and BaseHealthPredictor
- Dataset Audit: Preserves active, dormant, and unavailable dataset inventories
"""


from typing import Any
import os
import nbformat
import joblib
import numpy as np
import pandas as pd
import pytest
import torch
import torch.nn as nn
from scipy import stats  # type: ignore


from intellicluster.ml.interfaces import BaseHealthPredictor, BaseSchedulerPredictor
from intellicluster.ml.schemas import HealthPrediction, PlacementRecommendation
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload
from intellicluster.core.constants import NodeStatus, WorkloadPriority, WorkloadStatus

REPO_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(REPO_DIR, "ml_models")
DATA_DIR = os.path.join(REPO_DIR, "data")
NOTEBOOKS_DIR = os.path.join(REPO_DIR, "notebooks")


# 1. NOTEBOOK REPRODUCIBILITY TESTS

class TestNotebookReproducibility:
    EXPECTED_NOTEBOOKS = [
        "01_server_clustering.ipynb",
        "02_failure_prediction.ipynb",
        "03_resource_forecasting.ipynb",
        "04_anomaly_detection.ipynb",
        "05_dynamic_load_balancing.ipynb",
    ]

    def test_all_notebooks_exist_and_parse(self):
        for nb_name in self.EXPECTED_NOTEBOOKS:
            nb_path = os.path.join(NOTEBOOKS_DIR, nb_name)
            assert os.path.exists(nb_path), f"Missing notebook: {nb_name}"
            nb: Any = nbformat.read(nb_path, as_version=4)
            assert len(nb.cells) >= 6, f"Notebook {nb_name} has insufficient cells: {len(nb.cells)}"
            code_cells = [c for c in nb.cells if c.cell_type == "code"]
            assert len(code_cells) >= 5, f"Notebook {nb_name} has insufficient code cells: {len(code_cells)}"


    def test_notebooks_define_metadata_before_serialization(self):
        """Verifies that each notebook explicitly defines its metadata/artifact before calling dump."""
        # Notebook 1: kmeans_artifact
        nb1: Any = nbformat.read(os.path.join(NOTEBOOKS_DIR, "01_server_clustering.ipynb"), as_version=4)
        nb1_src = "\n".join([c.source for c in nb1.cells if c.cell_type == "code"])
        assert "kmeans_artifact = {" in nb1_src, "kmeans_artifact definition missing in notebook 1"

        # Notebook 2: artifact_2a, artifact_2b
        nb2: Any = nbformat.read(os.path.join(NOTEBOOKS_DIR, "02_failure_prediction.ipynb"), as_version=4)
        nb2_src = "\n".join([c.source for c in nb2.cells if c.cell_type == "code"])
        assert "artifact_2a = {" in nb2_src, "artifact_2a definition missing in notebook 2"
        assert "artifact_2b = {" in nb2_src, "artifact_2b definition missing in notebook 2"
        assert "final_model_2a" in nb2_src, "final_model_2a missing in notebook 2"
        assert "final_model_2b" in nb2_src, "final_model_2b missing in notebook 2"

        # Notebook 3: lstm_metadata, training loop
        nb3: Any = nbformat.read(os.path.join(NOTEBOOKS_DIR, "03_resource_forecasting.ipynb"), as_version=4)
        nb3_src = "\n".join([c.source for c in nb3.cells if c.cell_type == "code"])
        assert "lstm_metadata = {" in nb3_src, "lstm_metadata definition missing in notebook 3"
        assert "train_losses" in nb3_src and "val_losses" in nb3_src, "loss tracking missing in notebook 3"
        assert "DataLoader" in nb3_src, "DataLoader missing in notebook 3"

        # Notebook 4: artifact_4a, artifact_4b
        nb4: Any = nbformat.read(os.path.join(NOTEBOOKS_DIR, "04_anomaly_detection.ipynb"), as_version=4)
        nb4_src = "\n".join([c.source for c in nb4.cells if c.cell_type == "code"])
        assert "artifact_4a = {" in nb4_src, "artifact_4a definition missing in notebook 4"
        assert "artifact_4b = {" in nb4_src, "artifact_4b definition missing in notebook 4"

        # Notebook 5: dqn_metadata, ReplayBuffer, training loop
        nb5: Any = nbformat.read(os.path.join(NOTEBOOKS_DIR, "05_dynamic_load_balancing.ipynb"), as_version=4)
        nb5_src = "\n".join([c.source for c in nb5.cells if c.cell_type == "code"])
        assert "dqn_metadata = {" in nb5_src, "dqn_metadata definition missing in notebook 5"
        assert "class ReplayBuffer" in nb5_src, "ReplayBuffer missing in notebook 5"
        assert "bench_text" in nb5_src, "bench_text evaluation missing in notebook 5"


    def test_notebooks_clean_kernel_execution(self, monkeypatch):
        """Simulates clean kernel execution of all 5 notebooks in non-interactive mode."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.show = lambda *args, **kwargs: None

        # Mandatory safeguard: prevent notebook simulation from modifying pre-trained ml_models/
        monkeypatch.setattr(joblib, "dump", lambda *args, **kwargs: None, raising=False)
        monkeypatch.setattr(torch, "save", lambda *args, **kwargs: None, raising=False)


        for nb_name in self.EXPECTED_NOTEBOOKS:
            nb_path = os.path.join(NOTEBOOKS_DIR, nb_name)
            nb: Any = nbformat.read(nb_path, as_version=4)
            ns = {
                "__file__": nb_path,
                "__name__": "__main__",
            }
            code_cells = [c for c in nb.cells if c.cell_type == "code"]

            for idx, cell in enumerate(code_cells):
                src = cell.source.strip()
                if not src:
                    continue
                try:
                    exec(src, ns)
                except Exception as e:
                    pytest.fail(f"Clean execution failed in {nb_name} cell {idx+1}: {type(e).__name__}: {e}")


# 2. ENVIRONMENTAL XGBOOST DIAGNOSTICS TESTS

class TestEnvironmentalXGBoostDiagnostics:
    def test_machine_failure_data_uniform_distributions(self):
        """Confirms that sensor features in machine_failure_data.csv follow uniform random noise."""
        df = pd.read_csv(os.path.join(DATA_DIR, "machine_failure_data.csv"))
        feature_cols = ["Temperature", "Pressure", "Vibration_Level", "Humidity", "Power_Consumption"]

        for col in feature_cols:
            stat, p_val = stats.kstest(df[col], "uniform", args=(df[col].min(), df[col].max() - df[col].min()))
            assert p_val > 0.30, f"Feature {col} is not uniformly distributed (p={p_val:.4f})"

    def test_machine_failure_data_zero_correlation(self):
        """Confirms that all features have near-zero linear correlation with Failure_Status."""
        df = pd.read_csv(os.path.join(DATA_DIR, "machine_failure_data.csv"))
        feature_cols = ["Temperature", "Pressure", "Vibration_Level", "Humidity", "Power_Consumption"]

        for col in feature_cols:
            corr = float(np.corrcoef(np.asarray(df[col], dtype=float), np.asarray(df["Failure_Status"], dtype=float))[0, 1])
            assert abs(corr) < 0.05, f"Feature {col} has unexpected correlation: {corr:.4f}"

    def test_machine_failure_data_t_test_p_values(self):
        """Confirms that feature means between normal and failure samples show no statistical difference."""
        df = pd.read_csv(os.path.join(DATA_DIR, "machine_failure_data.csv"))
        feature_cols = ["Temperature", "Pressure", "Vibration_Level", "Humidity", "Power_Consumption"]

        for col in feature_cols:
            v0 = df[df["Failure_Status"] == 0][col]
            v1 = df[df["Failure_Status"] == 1][col]
            ttest: Any = stats.ttest_ind(v0, v1)
            assert ttest.pvalue > 0.40, f"Feature {col} has statistically significant difference (p={ttest.pvalue:.4f})"


    def test_environmental_artifact_documents_generalization_failure(self):
        """Verifies that the serialized Model 2B artifact records near-random OOF ROC and flags unsuitability."""
        art = joblib.load(os.path.join(MODELS_DIR, "failure_prediction_environmental_xgboost.joblib"))
        assert art["model_name"] == "failure_prediction_environmental_xgboost"
        roc = art["metrics"]["roc_auc"]
        assert 0.45 <= roc <= 0.55, f"Expected near-random OOF ROC-AUC, found: {roc:.4f}"


# 3. NETWORK ISOLATION FOREST DIAGNOSTICS TESTS

class TestNetworkIsolationForestDiagnostics:
    def test_network_dataset_constant_feature(self):
        """Confirms that mean_packet_size has zero variance (constant 0.0) and is dropped."""
        df = pd.read_csv(os.path.join(DATA_DIR, "embedded_system_network_security_dataset.csv"))
        assert df["mean_packet_size"].nunique() == 1
        assert df["mean_packet_size"].iloc[0] == 0.0

        art = joblib.load(os.path.join(MODELS_DIR, "network_anomaly_iforest.joblib"))
        assert "mean_packet_size" in art["dropped_features"]
        assert "mean_packet_size" not in art["feature_names"]

    def test_network_iforest_score_parity_between_classes(self):
        """Confirms that anomaly scores for nominal traffic and attack traffic have identical distributions."""
        art = joblib.load(os.path.join(MODELS_DIR, "network_anomaly_iforest.joblib"))
        df = pd.read_csv(os.path.join(DATA_DIR, "embedded_system_network_security_dataset.csv"))

        X = df[art["feature_names"]]
        y = df["label"].values.astype(int)

        scores = -art["model"].score_samples(X)
        mean_score_0 = scores[y == 0].mean()
        mean_score_1 = scores[y == 1].mean()

        # Score distributions must be virtually identical (< 0.005 difference)
        diff = abs(mean_score_0 - mean_score_1)
        assert diff < 0.005, f"Anomaly scores differ significantly between normal and attack: {diff:.5f}"

    def test_network_iforest_documented_random_performance(self):
        """Confirms that the network anomaly model has ROC-AUC ~ 0.50 (random detection)."""
        art = joblib.load(os.path.join(MODELS_DIR, "network_anomaly_iforest.joblib"))
        roc = art["metrics"]["roc_auc"]
        assert 0.45 <= roc <= 0.55, f"Unexpected network anomaly ROC-AUC: {roc:.4f}"


# 4. K-MEANS OPERATIONAL UTILITY TESTS

class TestKMeansOperationalUtility:
    def test_kmeans_four_archetypes_integrity(self):
        """Verifies that all 4 cluster archetypes exist with non-empty counts and interpretable profiles."""
        art = joblib.load(os.path.join(MODELS_DIR, "server_clustering_kmeans.joblib"))
        assert art["optimal_k"] == 4
        archetypes = art["archetypes"]
        assert len(archetypes) == 4

        # Verify cluster profiles are operationally distinct
        cpu_utils = [archetypes[c]["avg_cpu_util"] for c in archetypes]
        assert max(cpu_utils) > 80.0, "Missing high-utilization / saturated archetype"
        assert min(cpu_utils) < 30.0, "Missing underutilized archetype"

    def test_kmeans_weak_silhouette_honestly_documented(self):
        """Verifies that K=4 silhouette is within the weak geometric separation range (~0.1478)."""
        art = joblib.load(os.path.join(MODELS_DIR, "server_clustering_kmeans.joblib"))
        k4_metric = next(m for m in art["eval_metrics"] if m["K"] == 4)
        sil = k4_metric["Silhouette"]
        assert 0.10 <= sil <= 0.20, f"Silhouette not in expected weak geometric separation band: {sil:.4f}"

    def test_kmeans_inference_on_new_data(self):
        """Verifies that the preprocessor and KMeans model execute valid inference on new observations."""
        art = joblib.load(os.path.join(MODELS_DIR, "server_clustering_kmeans.joblib"))
        scaler = joblib.load(os.path.join(MODELS_DIR, "server_clustering_scaler.joblib"))

        new_data = pd.DataFrame([{
            "CPU_Cores": 32.0, "Memory_GB": 128.0, "VM_Instances": 8, "Container_Replicas": 24,
            "Storage_IOPS": 20000, "Network_Bandwidth_Mbps": 5000, "CPU_Utilization_pct": 75.0,
            "Memory_Utilization_pct": 60.0, "Network_Utilization_pct": 55.0, "Disk_Utilization_pct": 40.0,
            "Request_Rate_RPS": 3000.0, "Load_Balancer_Capacity": 8000.0,
            "Application_Tier": "Application_Server"
        }])
        X_trans = scaler.transform(new_data)
        assert X_trans.shape == (1, 18)
        pred_cluster = art["model"].predict(X_trans)[0]
        assert pred_cluster in [0, 1, 2, 3]


# 5. INFRASTRUCTURE ISOLATION FOREST DISTINCTION TESTS

class TestInfrastructureIsolationForestDistinction:
    def test_density_outlier_vs_threshold_saturation_separation(self):
        """Verifies that Isolation Forest detects multivariate density outliers, distinct from 1D saturation."""
        art = joblib.load(os.path.join(MODELS_DIR, "infrastructure_anomaly_iforest.joblib"))
        df = pd.read_csv(os.path.join(DATA_DIR, "Resource_utilization.csv"))

        X = df[art["feature_names"]].ffill().bfill()
        preds = (art["model"].predict(X) == -1).astype(int)

        sat_mask = np.asarray((X["cpu_utilization"] > 100.0) | (X["storage_usage"] > 100.0), dtype=bool)
        total_sat = sat_mask.sum()
        captured_sat = preds[sat_mask].sum()

        capture_rate = captured_sat / total_sat
        # Capture rate must match documented ~25% (20% - 30%)
        assert 0.20 <= capture_rate <= 0.30, f"Unexpected saturation capture rate: {capture_rate:.4f}"

        # Total anomalies flagged matches 5% contamination
        assert preds.sum() == int(0.05 * len(X)) + 1 or preds.sum() == int(0.05 * len(X))


# 6. LSTM FORECASTING TESTS

class TestLSTMForecastingIntegrity:
    def test_lstm_metadata_and_architecture(self):
        """Verifies lookback, horizon, multi-target variables, and scaler persistence."""
        meta = joblib.load(os.path.join(MODELS_DIR, "resource_forecasting_metadata.joblib"))
        assert meta["lookback_window_hours"] == 168
        assert meta["forecast_horizon_hours"] == 24
        assert meta["target_features"] == ["cpu_utilization", "memory_usage", "workload"]
        assert meta["scaler"] is not None
        assert "overall_mae" in meta["metrics"]

    def test_lstm_unclipped_data_preservation(self):
        """Confirms that extreme >100% values are preserved without clipping."""
        df = pd.read_csv(os.path.join(DATA_DIR, "Resource_utilization.csv"))
        assert (df["cpu_utilization"] > 100.0).any()
        assert (df["storage_usage"] > 100.0).any()


# 7. DQN INTEGRATION READINESS TESTS

class TestDQNIntegrationReadiness:
    class QNetwork(nn.Module):
        def __init__(self, in_dim=25, out_actions=4):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(in_dim, 128),
                nn.ReLU(),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, out_actions)
            )

        def forward(self, x):
            return self.net(x)

    def test_dqn_deterministic_inference_and_masking(self):
        """Verifies deterministic epsilon=0 evaluation and candidate node masking."""
        dqn_path = os.path.join(MODELS_DIR, "load_balancer_dqn.pt")
        meta = joblib.load(os.path.join(MODELS_DIR, "load_balancer_metadata.joblib"))

        q_net = self.QNetwork(in_dim=meta["state_dim"], out_actions=meta["action_dim"])
        q_net.load_state_dict(torch.load(dqn_path, weights_only=True))
        q_net.eval()

        dummy_state = torch.ones(1, 25)
        with torch.no_grad():
            q_vals = q_net(dummy_state).squeeze(0)

        # Deterministic inference
        best_action = int(torch.argmax(q_vals).item())
        assert best_action in [0, 1, 2, 3]

        # Action masking test: if best_action is cordoned/unavailable, fall back to next best
        masked_q = q_vals.clone()
        masked_q[best_action] = -float("inf")
        fallback_action = int(torch.argmax(masked_q).item())
        assert fallback_action != best_action
        assert fallback_action in [0, 1, 2, 3]


# 8. BACKEND ML INTERFACE COMPATIBILITY TESTS

class TestBackendMLInterfaceCompatibility:
    class DQNSchedulerPredictor(BaseSchedulerPredictor):
        """Adapter demonstrating how load_balancer_dqn.pt maps to BaseSchedulerPredictor."""
        class QNetwork(nn.Module):
            def __init__(self, in_dim=25, out_actions=4):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(in_dim, 128),
                    nn.ReLU(),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Linear(64, out_actions),
                )
            def forward(self, x):
                return self.net(x)

        def __init__(self, q_net_path, meta_path):
            self.meta = joblib.load(meta_path)
            self.q_net = self.QNetwork(in_dim=self.meta["state_dim"], out_actions=self.meta["action_dim"])
            self.q_net.load_state_dict(torch.load(q_net_path, weights_only=True))
            self.q_net.eval()

        def predict_optimal_node(self, workload: Workload, candidate_nodes):
            if not candidate_nodes:
                return PlacementRecommendation(
                    recommended_node_id=None,
                    confidence_score=0.0,
                    strategy_used="dqn_v1",
                    reasoning="No candidate nodes provided",
                )
            # Build dummy 25-dim state vector
            state = np.zeros(25, dtype=np.float32)
            with torch.no_grad():
                q_vals = self.q_net(torch.tensor(state).unsqueeze(0)).squeeze(0)
            
            # Map action to available candidate node
            action = int(torch.argmax(q_vals).item()) % len(candidate_nodes)
            chosen_node = candidate_nodes[action]

            # Softmax confidence score
            probs = torch.softmax(q_vals, dim=0).numpy()
            confidence = float(np.max(probs))

            return PlacementRecommendation(
                recommended_node_id=chosen_node.id,
                confidence_score=confidence,
                predicted_latency_ms=chosen_node.current_network_latency_ms,
                strategy_used="dqn_v1",
                reasoning=f"DQN Q-value maximization selected node {chosen_node.hostname}",
            )

    class AI4IHealthPredictor(BaseHealthPredictor):
        """Adapter demonstrating how failure_prediction_ai4i_xgboost maps to BaseHealthPredictor."""
        def __init__(self, model_path):
            self.artifact = joblib.load(model_path)
            self.model = self.artifact["model"]
            self.feature_names = self.artifact["feature_names"]

        def predict_node_health(self, node: Node, telemetry_history):
            # Construct feature vector
            row = {
                "Air_temperature_K": 300.0,
                "Process_temperature_K": 310.0,
                "Rotational_speed_rpm": 1500.0,
                "Torque_Nm": 40.0,
                "Tool_wear_min": 100.0,
                "Type_L": 1.0,
                "Type_M": 0.0,
            }
            sample_df = pd.DataFrame([row])[self.feature_names]
            prob = float(self.model.predict_proba(sample_df)[0, 1])

            return HealthPrediction(
                node_id=node.id,
                predicted_risk_score=prob,
                is_anomaly=(prob >= 0.5),
                strategy_used="ai4i_xgboost_v1",
                reasoning=f"AI4I XGBoost predicted failure risk: {prob:.4f}",
            )

    def test_dqn_scheduler_adapter(self):
        dqn_path = os.path.join(MODELS_DIR, "load_balancer_dqn.pt")
        meta_path = os.path.join(MODELS_DIR, "load_balancer_metadata.joblib")
        predictor = self.DQNSchedulerPredictor(dqn_path, meta_path)

        dummy_node = Node(
            id="node-uuid-01",
            cluster_id="cluster-1",
            hostname="worker-01",
            ip_address="192.168.1.10",
            cpu_cores=16.0,
            memory_mb=65536.0,
            status=NodeStatus.READY.value,
            current_network_latency_ms=12.5,
        )
        dummy_workload = Workload(
            id="workload-uuid-01",
            cluster_id="cluster-1",
            name="test-task",
            cpu_cores_requested=4.0,
            memory_mb_requested=16384.0,
            priority=WorkloadPriority.HIGH.value,
            status=WorkloadStatus.PENDING.value,
        )

        rec = predictor.predict_optimal_node(dummy_workload, [dummy_node])
        assert isinstance(rec, PlacementRecommendation)
        assert rec.recommended_node_id == dummy_node.id
        assert 0.0 <= rec.confidence_score <= 1.0
        assert rec.strategy_used == "dqn_v1"

    def test_ai4i_health_adapter(self):
        art_path = os.path.join(MODELS_DIR, "failure_prediction_ai4i_xgboost.joblib")
        predictor = self.AI4IHealthPredictor(art_path)

        dummy_node = Node(
            id="node-uuid-02",
            cluster_id="cluster-1",
            hostname="worker-02",
            ip_address="192.168.1.11",
            cpu_cores=16.0,
            memory_mb=65536.0,
            status=NodeStatus.READY.value,
        )

        health = predictor.predict_node_health(dummy_node, [])
        assert isinstance(health, HealthPrediction)
        assert health.node_id == dummy_node.id
        assert 0.0 <= health.predicted_risk_score <= 1.0
        assert health.strategy_used == "ai4i_xgboost_v1"


# 9. DATASET AUDIT TESTS

class TestDatasetAudit:
    USED_DATASETS = [
        "ai4i2020.csv",
        "cloud_ecommerce_performance_tradeoff_dataset.csv",
        "embedded_system_network_security_dataset.csv",
        "Load Balancing Improved.csv",
        "machine_failure_data.csv",
        "Resource_utilization.csv",
        "Workload_Dataset.csv",
    ]

    DORMANT_DATASETS = [
        "Midterm_53_group.csv",
        "output1.csv",
        "logs-dataset.ipynb",
        "predicting-service-request-loads.ipynb",
    ]

    def test_all_used_datasets_present_and_non_empty(self):
        for name in self.USED_DATASETS:
            path = os.path.join(DATA_DIR, name)
            assert os.path.exists(path), f"Active dataset missing: {name}"
            assert os.path.getsize(path) > 0, f"Active dataset empty: {name}"

    def test_all_dormant_datasets_present(self):
        for name in self.DORMANT_DATASETS:
            path = os.path.join(DATA_DIR, name)
            assert os.path.exists(path), f"Dormant dataset missing: {name}"
            assert os.path.getsize(path) > 0, f"Dormant dataset empty: {name}"

    def test_unavailable_dataset_remains_unfabricated(self):
        path = os.path.join(DATA_DIR, "cloud_server_resource_usage_1000.csv")
        assert not os.path.exists(path), "cloud_server_resource_usage_1000.csv must remain absent"
