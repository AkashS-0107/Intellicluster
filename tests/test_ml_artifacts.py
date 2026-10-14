"""
Automated validation tests for ML model artifacts and datasets.
Verifies data integrity, artifact deserialization, inference validity,
and compatibility with IntelliCluster boundaries.
"""

import os
import pytest
import numpy as np
import pandas as pd
import joblib
import torch
import torch.nn as nn


class TestDatasetIntegrity:
    """Verifies that all required datasets exist, have non-zero rows, and expected schemas."""

    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    def test_required_datasets_exist(self):
        expected_files = [
            "ai4i2020.csv",
            "cloud_ecommerce_performance_tradeoff_dataset.csv",
            "embedded_system_network_security_dataset.csv",
            "Load Balancing Improved.csv",
            "machine_failure_data.csv",
            "Midterm_53_group.csv",
            "output1.csv",
            "Resource_utilization.csv",
            "Workload_Dataset.csv",
        ]
        for fname in expected_files:
            path = os.path.join(self.DATA_DIR, fname)
            assert os.path.exists(path), f"Missing expected dataset: {fname}"
            assert os.path.getsize(path) > 0, f"Dataset is empty: {fname}"

    def test_workload_dataset_extraction_accuracy(self):
        path = os.path.join(self.DATA_DIR, "Workload_Dataset.csv")
        df = pd.read_csv(path)
        assert len(df) == 100, f"Workload_Dataset.csv must have 100 rows, found {len(df)}"
        expected_cols = ["Server_ID", "Workload_Type", "Requests_per_sec", "Active_Users", "CPU_Usage"]
        assert list(df.columns) == expected_cols, f"Column mismatch in Workload_Dataset: {list(df.columns)}"

    def test_missing_dataset_remains_absent(self):
        """cloud_server_resource_usage_1000.csv must remain formally absent and un-fabricated."""
        path = os.path.join(self.DATA_DIR, "cloud_server_resource_usage_1000.csv")
        assert not os.path.exists(path), "cloud_server_resource_usage_1000.csv must not be fabricated."


class TestModelArtifacts:
    """Verifies artifact serialization, metadata schemas, and inference bounds."""

    MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")

    def test_all_expected_artifacts_exist(self):
        expected_artifacts = [
            "server_clustering_kmeans.joblib",
            "server_clustering_scaler.joblib",
            "failure_prediction_ai4i_xgboost.joblib",
            "failure_prediction_environmental_xgboost.joblib",
            "resource_forecasting_lstm.pt",
            "resource_forecasting_metadata.joblib",
            "network_anomaly_iforest.joblib",
            "infrastructure_anomaly_iforest.joblib",
            "load_balancer_dqn.pt",
            "load_balancer_metadata.joblib",
        ]
        for art in expected_artifacts:
            path = os.path.join(self.MODELS_DIR, art)
            assert os.path.exists(path), f"Missing expected model artifact: {art}"
            assert os.path.getsize(path) > 0, f"Artifact is empty: {art}"

    def test_model_1_kmeans_inference(self):
        art_path = os.path.join(self.MODELS_DIR, "server_clustering_kmeans.joblib")
        scaler_path = os.path.join(self.MODELS_DIR, "server_clustering_scaler.joblib")

        artifact = joblib.load(art_path)
        preprocessor = joblib.load(scaler_path)

        assert artifact["algorithm"] == "KMeans"
        assert artifact["optimal_k"] == 4
        assert "archetypes" in artifact
        assert len(artifact["archetypes"]) == 4

        # Test inference with dummy sample
        df_sample = pd.DataFrame([{
            "CPU_Cores": 16.0, "Memory_GB": 64.0, "VM_Instances": 4, "Container_Replicas": 12,
            "Storage_IOPS": 10000, "Network_Bandwidth_Mbps": 2500, "CPU_Utilization_pct": 50.0,
            "Memory_Utilization_pct": 30.0, "Network_Utilization_pct": 40.0, "Disk_Utilization_pct": 25.0,
            "Request_Rate_RPS": 1500.0, "Load_Balancer_Capacity": 5000.0,
            "Application_Tier": "Application_Server"
        }])
        X_trans = preprocessor.transform(df_sample)
        cluster_id = artifact["model"].predict(X_trans)[0]
        assert cluster_id in [0, 1, 2, 3], f"Invalid cluster label: {cluster_id}"

    def test_model_2a_ai4i_failure_prediction(self):
        art_path = os.path.join(self.MODELS_DIR, "failure_prediction_ai4i_xgboost.joblib")
        artifact = joblib.load(art_path)

        assert artifact["model_name"] == "failure_prediction_ai4i_xgboost"
        assert artifact["metrics"]["roc_auc"] > 0.90
        assert artifact["metrics"]["pr_auc"] > 0.50

        # Test inference on sample vector
        feature_names = artifact["feature_names"]
        sample_df = pd.DataFrame(np.zeros((1, len(feature_names))), columns=feature_names)
        sample_df["Air_temperature_K"] = 300.0
        sample_df["Process_temperature_K"] = 310.0
        sample_df["Rotational_speed_rpm"] = 1500.0
        sample_df["Torque_Nm"] = 40.0
        sample_df["Tool_wear_min"] = 100.0

        prob = artifact["model"].predict_proba(sample_df)[0, 1]
        assert 0.0 <= prob <= 1.0, f"Probability out of bounds: {prob}"
        assert not np.isnan(prob) and not np.isinf(prob)

    def test_model_2b_environmental_failure_prediction(self):
        art_path = os.path.join(self.MODELS_DIR, "failure_prediction_environmental_xgboost.joblib")
        artifact = joblib.load(art_path)

        assert artifact["model_name"] == "failure_prediction_environmental_xgboost"
        feature_names = artifact["feature_names"]
        sample_df = pd.DataFrame([[50.0, 300.0, 5.0, 60.0, 50.0]], columns=feature_names)

        prob = artifact["model"].predict_proba(sample_df)[0, 1]
        assert 0.0 <= prob <= 1.0, f"Probability out of bounds: {prob}"
        assert not np.isnan(prob) and not np.isinf(prob)

    def test_model_3_lstm_forecasting(self):
        meta_path = os.path.join(self.MODELS_DIR, "resource_forecasting_metadata.joblib")
        model_path = os.path.join(self.MODELS_DIR, "resource_forecasting_lstm.pt")

        metadata = joblib.load(meta_path)
        assert metadata["algorithm"] == "Multivariate_LSTM"
        assert metadata["lookback_window_hours"] == 168
        assert metadata["forecast_horizon_hours"] == 24
        assert len(metadata["target_features"]) == 3

        # Reconstruct LSTM class
        class ResourceLSTM(nn.Module):
            def __init__(self, in_dim=5, h1=64, h2=32, out_horizon=24, out_vars=3):
                super().__init__()
                self.lstm1 = nn.LSTM(in_dim, h1, batch_first=True)
                self.dropout = nn.Dropout(0.2)
                self.lstm2 = nn.LSTM(h1, h2, batch_first=True)
                self.fc = nn.Linear(h2, out_horizon * out_vars)
                self.out_horizon = out_horizon
                self.out_vars = out_vars

            def forward(self, x):
                out, _ = self.lstm1(x)
                out = self.dropout(out)
                out, _ = self.lstm2(out)
                last_step = out[:, -1, :]
                preds = self.fc(last_step)
                return preds.view(-1, self.out_horizon, self.out_vars)

        model = ResourceLSTM()
        model.load_state_dict(torch.load(model_path, weights_only=True))
        model.eval()

        dummy_seq = torch.randn(2, 168, 5) # Batch of 2, 168 hours, 5 features
        with torch.no_grad():
            output = model(dummy_seq)

        assert output.shape == (2, 24, 3), f"Unexpected LSTM output shape: {output.shape}"
        assert not torch.isnan(output).any() and not torch.isinf(output).any()

    def test_model_4_isolation_forest_anomalies(self):
        net_path = os.path.join(self.MODELS_DIR, "network_anomaly_iforest.joblib")
        infra_path = os.path.join(self.MODELS_DIR, "infrastructure_anomaly_iforest.joblib")

        net_art = joblib.load(net_path)
        infra_art = joblib.load(infra_path)

        assert net_art["domain"] == "Network_Security"
        assert infra_art["domain"] == "Infrastructure_Resource"

        # Domain A test
        dummy_net = pd.DataFrame(np.zeros((1, len(net_art["feature_names"]))), columns=net_art["feature_names"])
        score_net = -net_art["model"].score_samples(dummy_net)[0]
        assert not np.isnan(score_net) and not np.isinf(score_net)

        # Domain B test
        dummy_infra = pd.DataFrame([[50.0, 40.0, 60.0, 100.0, 75.0]], columns=infra_art["feature_names"])
        score_infra = -infra_art["model"].score_samples(dummy_infra)[0]
        assert not np.isnan(score_infra) and not np.isinf(score_infra)

    def test_model_5_dqn_load_balancing(self):
        dqn_path = os.path.join(self.MODELS_DIR, "load_balancer_dqn.pt")
        meta_path = os.path.join(self.MODELS_DIR, "load_balancer_metadata.joblib")

        metadata = joblib.load(meta_path)
        assert metadata["algorithm"] == "Deep_Q_Network"
        assert metadata["state_dim"] == 25
        assert metadata["action_dim"] == 4
        assert len(metadata["node_archetypes"]) == 4

        # Reconstruct Q-Network
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

        q_net = QNetwork()
        q_net.load_state_dict(torch.load(dqn_path, weights_only=True))
        q_net.eval()

        dummy_state = torch.randn(1, 25)
        with torch.no_grad():
            q_vals = q_net(dummy_state)
            action = int(torch.argmax(q_vals).item())

        assert action in [0, 1, 2, 3], f"Invalid node action: {action}"
        assert q_vals.shape == (1, 4)
        assert not torch.isnan(q_vals).any()
