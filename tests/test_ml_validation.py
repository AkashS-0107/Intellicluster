"""
Validation and diagnostics test suite for machine learning systems.
Validates ML models against empirical performance criteria,
leakage checks, baseline comparisons, and architectural contracts.
Strictly non-destructive: does not retrain models or modify artifacts.
"""


from typing import Any, cast
import os
import joblib
import numpy as np

import pandas as pd
import pytest
import torch
import torch.nn as nn
from sklearn.metrics import (
    adjusted_rand_score,
    auc,
    brier_score_loss,
    calinski_harabasz_score,
    davies_bouldin_score,
    f1_score,
    normalized_mutual_info_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.cluster import KMeans

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


# 1. Model 1 — K-Means Clustering Validation

class TestModel1KMeansValidation:
    @pytest.fixture(scope="class")
    @classmethod
    def kmeans_bundle(cls):
        art_path = os.path.join(MODELS_DIR, "server_clustering_kmeans.joblib")
        scaler_path = os.path.join(MODELS_DIR, "server_clustering_scaler.joblib")
        data_path = os.path.join(DATA_DIR, "cloud_ecommerce_performance_tradeoff_dataset.csv")

        artifact = joblib.load(art_path)
        scaler = joblib.load(scaler_path)
        df = pd.read_csv(data_path)
        return artifact, scaler, df

    def test_kmeans_artifact_structure_and_dimensions(self, kmeans_bundle):
        artifact, scaler, df = kmeans_bundle
        assert artifact["algorithm"] == "KMeans"
        assert artifact["optimal_k"] == 4
        assert len(artifact["archetypes"]) == 4

        # Validate feature sets
        num_cols = artifact["num_features"]
        cat_cols = artifact["cat_features"]
        assert len(num_cols) == 12
        assert cat_cols == ["Application_Tier"]

        # Transform and verify transformed feature dimension (12 numeric + 6 OneHot tiers = 18)
        X_trans = scaler.transform(df[num_cols + cat_cols])
        assert X_trans.shape == (len(df), 18)
        assert not np.isnan(X_trans).any() and not np.isinf(X_trans).any()

    def test_kmeans_predictions_and_population_balance(self, kmeans_bundle):
        artifact, scaler, df = kmeans_bundle
        model = artifact["model"]
        num_cols = artifact["num_features"]
        cat_cols = artifact["cat_features"]
        X_trans = scaler.transform(df[num_cols + cat_cols])

        labels = model.predict(X_trans)
        assert set(np.unique(labels)) == {0, 1, 2, 3}

        # Check population balance (no collapsed or singleton clusters)
        counts = pd.Series(labels).value_counts()
        min_cluster_pct = counts.min() / len(labels)
        max_cluster_pct = counts.max() / len(labels)
        assert min_cluster_pct >= 0.10, f"Smallest cluster too small: {min_cluster_pct:.2%}"
        assert max_cluster_pct <= 0.45, f"Largest cluster too dominant: {max_cluster_pct:.2%}"

    def test_kmeans_unsupervised_metrics_characterization(self, kmeans_bundle):
        artifact, scaler, df = kmeans_bundle
        model = artifact["model"]
        num_cols = artifact["num_features"]
        cat_cols = artifact["cat_features"]
        X_trans = scaler.transform(df[num_cols + cat_cols])
        labels = model.predict(X_trans)

        # Silhouette on fixed reproducible sample (3000 rows)
        sil = silhouette_score(X_trans, labels, sample_size=3000, random_state=42)
        dbi = davies_bouldin_score(X_trans, labels)
        chi = calinski_harabasz_score(X_trans, labels)

        # Scientific check: Silhouette reflects weak geometric separation (0.10 <= sil <= 0.20)
        assert 0.10 <= sil <= 0.20, f"Unexpected Silhouette: {sil:.4f}"
        assert dbi < 2.50, f"Davies-Bouldin too high: {dbi:.4f}"
        assert chi > 1500.0, f"Calinski-Harabasz too low: {chi:.1f}"

    def test_kmeans_multiseed_stability(self, kmeans_bundle):
        artifact, scaler, df = kmeans_bundle
        trained_labels = artifact["model"].predict(
            scaler.transform(df[artifact["num_features"] + artifact["cat_features"]])
        )
        X_trans = scaler.transform(df[artifact["num_features"] + artifact["cat_features"]])

        # Stability across seeds 42, 100, 2024, 7
        for s in [42, 100, 2024, 7]:
            km_test = cast(Any, KMeans)(n_clusters=4, random_state=s, n_init=10)
            seed_labels = km_test.fit_predict(X_trans)

            ari = adjusted_rand_score(trained_labels, seed_labels)
            nmi = normalized_mutual_info_score(trained_labels, seed_labels)
            assert ari >= 0.99, f"Seed {s} unstable ARI: {ari:.4f}"
            assert nmi >= 0.99, f"Seed {s} unstable NMI: {nmi:.4f}"


# 2. Model 2 — XGBoost Failure Prediction Validation (Dual Domain)

class TestModel2FailurePredictionValidation:
    def test_model_2a_leakage_exclusion_and_performance(self):
        art_path = os.path.join(MODELS_DIR, "failure_prediction_ai4i_xgboost.joblib")
        data_path = os.path.join(DATA_DIR, "ai4i2020.csv")

        artifact = joblib.load(art_path)
        df = pd.read_csv(data_path)

        # Leakage exclusions
        forbidden_cols = ["UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]
        for col in forbidden_cols:
            assert col not in artifact["feature_names"], f"Leakage column {col} found in Model 2A features"

        # Prepare evaluation data
        rename_map = {
            "Air temperature [K]": "Air_temperature_K",
            "Process temperature [K]": "Process_temperature_K",
            "Rotational speed [rpm]": "Rotational_speed_rpm",
            "Torque [Nm]": "Torque_Nm",
            "Tool wear [min]": "Tool_wear_min",
        }
        df_clean = df.rename(columns=rename_map)
        features_base = ["Air_temperature_K", "Process_temperature_K", "Rotational_speed_rpm", "Torque_Nm", "Tool_wear_min", "Type"]
        X = pd.get_dummies(df_clean[features_base], columns=["Type"], drop_first=True)
        y = np.asarray(df_clean["Machine failure"].values, dtype=int)

        model = artifact["model"]
        probs = model.predict_proba(X)[:, 1]
        roc = roc_auc_score(y, probs)
        p, r, _ = precision_recall_curve(y, probs)
        pr_auc = auc(r, p)

        # Verify high discrimination and superiority over majority baseline
        assert roc > 0.95, f"Model 2A ROC-AUC degraded: {roc:.4f}"
        assert pr_auc > 0.70, f"Model 2A PR-AUC degraded: {pr_auc:.4f}"
        # Majority baseline PR-AUC is equal to minority prevalence (0.0339)
        assert pr_auc > 10 * float(np.mean(y)), "Model 2A fails to outperform prevalence baseline"


    def test_model_2b_diagnostics_uninformative_signal(self):
        art_path = os.path.join(MODELS_DIR, "failure_prediction_environmental_xgboost.joblib")
        data_path = os.path.join(DATA_DIR, "machine_failure_data.csv")

        artifact = joblib.load(art_path)
        df = pd.read_csv(data_path)

        # Verify leakage columns excluded
        assert "Machine_ID" not in artifact["feature_names"]
        assert "Timestamp" not in artifact["feature_names"]

        features = artifact["feature_names"]
        X = df[features]
        y = np.asarray(df["Failure_Status"].values, dtype=int)

        # Verify statistical independence (near-zero linear correlation across all features)
        for col in features:
            corr = float(np.corrcoef(np.asarray(X[col], dtype=float), y)[0, 1])
            assert abs(corr) < 0.05, f"Feature {col} unexpectedly correlated with failure: {corr}"



        # Verify recorded out-of-fold generalization failure in artifact
        recorded_roc = artifact["metrics"]["roc_auc"]
        assert recorded_roc < 0.55, f"Expected Model 2B near-random OOF ROC, found {recorded_roc}"


# 3. Model 3 — Multivariate LSTM Resource Forecasting Validation

class TestModel3LSTMForecastingValidation:
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

    @pytest.fixture(scope="class")
    @classmethod
    def lstm_bundle(cls):
        meta_path = os.path.join(MODELS_DIR, "resource_forecasting_metadata.joblib")
        model_path = os.path.join(MODELS_DIR, "resource_forecasting_lstm.pt")
        data_path = os.path.join(DATA_DIR, "Resource_utilization.csv")

        metadata = joblib.load(meta_path)
        model = cls.ResourceLSTM()
        model.load_state_dict(torch.load(model_path, weights_only=True))
        model.eval()

        df = pd.read_csv(data_path)
        return metadata, model, df

    def test_lstm_temporal_boundaries_and_robust_scaling(self, lstm_bundle):
        metadata, _, df = lstm_bundle
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Check uniform 1-hour interval
        diffs = df["timestamp"].diff().iloc[1:].dt.total_seconds().values
        assert np.all(diffs == 3600.0), "Timeline contains non-uniform time steps"

        # Check >100% preservation (no clipping)
        assert (df["cpu_utilization"] > 100.0).any(), "Telemetry missing legitimate >100% CPU points"
        assert (df["storage_usage"] > 100.0).any(), "Telemetry missing legitimate >100% storage points"

    def test_lstm_beats_naive_persistence_baseline(self, lstm_bundle):
        metadata, model, df = lstm_bundle
        features = metadata["input_features"]
        target_cols = metadata["target_features"]
        target_indices = [features.index(c) for c in target_cols]
        scaler = metadata["scaler"]

        df_imputed = df[features].ffill().fillna(metadata["imputation_medians"])
        scaled_data = scaler.transform(df_imputed)

        T, H = 168, 24
        # Build test sequences for holdout period
        start_idx = 21888 - T
        end_idx = len(scaled_data)

        # Evaluate on a reproducible sample slice of 500 test windows to keep pytest fast
        sample_step = max(1, (end_idx - T - H + 1 - start_idx) // 500)
        X_list, y_list = [], []
        for i in range(start_idx, end_idx - T - H + 1, sample_step):
            X_list.append(scaled_data[i : i + T])
            y_list.append(scaled_data[i + T : i + T + H, target_indices])

        X_test = torch.tensor(np.array(X_list), dtype=torch.float32)
        y_test = np.array(y_list)

        with torch.no_grad():
            preds_scaled = model(X_test).numpy()

        # Unscale targets
        center = scaler.center_[target_indices]
        scale = scaler.scale_[target_indices]
        actual_unscaled = y_test * scale + center
        preds_unscaled = preds_scaled * scale + center

        # Baseline A: Naive persistence (last observed value at t)
        last_obs = X_test[:, -1:, target_indices].numpy()
        persistence_unscaled = np.repeat(last_obs, H, axis=1) * scale + center

        lstm_mae = float(np.mean(np.abs(actual_unscaled - preds_unscaled)))
        pers_mae = float(np.mean(np.abs(actual_unscaled - persistence_unscaled)))

        # Assert LSTM decisively improves over persistence by >= 25%
        improvement_pct = (pers_mae - lstm_mae) / pers_mae * 100.0
        assert improvement_pct >= 25.0, f"LSTM failed to substantially beat persistence: {improvement_pct:.1f}% improvement"


# 4. Model 4 — Isolation Forest Anomaly Detection Validation

class TestModel4IsolationForestValidation:
    def test_model_4a_network_anomaly_score_orientation_and_limitation(self):
        art_path = os.path.join(MODELS_DIR, "network_anomaly_iforest.joblib")
        data_path = os.path.join(DATA_DIR, "embedded_system_network_security_dataset.csv")

        artifact = joblib.load(art_path)
        model = artifact["model"]
        df = pd.read_csv(data_path)

        # Label strictly excluded from input
        assert "label" not in artifact["feature_names"]

        X = df[artifact["feature_names"]]
        y = np.asarray(df["label"].values, dtype=int)

        # Verify anomaly score calculations
        neg_scores = np.asarray(-model.score_samples(X), dtype=float)
        roc_neg = roc_auc_score(y, neg_scores)
        roc_pos = roc_auc_score(y, -neg_scores)


        # Scientific finding: Regardless of score orientation, ROC-AUC is approximately 0.50 (+/- 0.05)
        assert 0.45 <= roc_neg <= 0.55, f"Unexpected network anomaly ROC-AUC: {roc_neg:.4f}"
        assert 0.45 <= roc_pos <= 0.55, f"Unexpected positive network anomaly ROC-AUC: {roc_pos:.4f}"

    def test_model_4b_infrastructure_saturation_detection(self):
        art_path = os.path.join(MODELS_DIR, "infrastructure_anomaly_iforest.joblib")
        data_path = os.path.join(DATA_DIR, "Resource_utilization.csv")

        artifact = joblib.load(art_path)
        model = artifact["model"]
        df = pd.read_csv(data_path)

        X = df[artifact["feature_names"]].ffill().bfill()
        is_anomaly = (model.predict(X) == -1).astype(int)

        # Ground truth extreme saturation points (>100% CPU or storage)
        sat_mask = np.asarray((X["cpu_utilization"] > 100.0) | (X["storage_usage"] > 100.0), dtype=bool)
        captured_saturation = is_anomaly[sat_mask].sum()
        total_saturation = sat_mask.sum()


        assert total_saturation > 1000, "Expected >1000 ground truth saturation observations"
        assert captured_saturation > 300, f"Saturation capture unexpectedly low: {captured_saturation}"


# 5. Model 5 — Deep Q-Network (DQN) Load Balancing Validation

class TestModel5DQNLoadBalancingValidation:
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

    def test_dqn_artifact_and_architecture_contract(self):
        dqn_path = os.path.join(MODELS_DIR, "load_balancer_dqn.pt")
        meta_path = os.path.join(MODELS_DIR, "load_balancer_metadata.joblib")

        meta = joblib.load(meta_path)
        assert meta["state_dim"] == 25
        assert meta["action_dim"] == 4
        assert len(meta["node_archetypes"]) == 4

        model = self.QNetwork()
        model.load_state_dict(torch.load(dqn_path, weights_only=True))
        model.eval()

        dummy_state = torch.randn(5, 25)
        with torch.no_grad():
            q_vals = model(dummy_state)
        assert q_vals.shape == (5, 4)
        assert not torch.isnan(q_vals).any()

    def test_dqn_beats_deterministic_baselines_on_holdout_episodes(self):
        dqn_path = os.path.join(MODELS_DIR, "load_balancer_dqn.pt")
        q_net = self.QNetwork()
        q_net.load_state_dict(torch.load(dqn_path, weights_only=True))
        q_net.eval()

        df_tasks = pd.read_csv(os.path.join(DATA_DIR, "Load Balancing Improved.csv"))
        task_cols = [
            "task_size", "cpu_demand", "memory_demand", "network_latency",
            "io_operations", "disk_usage", "num_connections", "priority_level"
        ]
        task_matrix = df_tasks[task_cols].values

        df_res = pd.read_csv(os.path.join(DATA_DIR, "Resource_utilization.csv"))
        bg_series: np.ndarray = np.asarray(df_res["cpu_utilization"].ffill().values, dtype=float) / 100.0

        node_matrix = np.array([
            [4.0, 16.0, 25.0, 15.0],
            [16.0, 64.0, 15.0, 50.0],
            [32.0, 128.0, 10.0, 110.0],
            [64.0, 256.0, 8.0, 250.0],
        ])
        K = 4

        # Run controlled comparison on 10 holdout episodes
        np.random.seed(1234)
        holdout_starts = np.random.randint(5000, len(task_matrix) - 150, size=10)
        holdout_bgs = np.random.randint(5000, len(bg_series) - 150, size=10)


        def run_sim(policy_type):
            overload_counts = 0
            for ep in range(10):
                t_idx = int(holdout_starts[ep])
                b_idx = int(holdout_bgs[ep])
                alloc_cpu = np.zeros(K)
                alloc_mem = np.zeros(K)
                active_tasks = np.zeros(K)

                for step in range(100):
                    task = task_matrix[t_idx + step]
                    bg = float(bg_series[b_idx + step])


                    if policy_type == "dqn":
                        node_states = []
                        for i in range(K):
                            fc = max(0.0, 1.0 - (alloc_cpu[i] / node_matrix[i, 0]))
                            fm = max(0.0, 1.0 - (alloc_mem[i] / node_matrix[i, 1]))
                            nl = node_matrix[i, 2] / 50.0
                            nt = active_tasks[i] / 20.0
                            node_states.extend([fc, fm, nl, nt])
                        s = np.concatenate([task, node_states, [bg]]).astype(np.float32)
                        with torch.no_grad():
                            q = q_net(torch.tensor(s).unsqueeze(0))
                            action = int(torch.argmax(q).item())
                    elif policy_type == "heuristic":
                        scores = [
                            (node_matrix[k, 0] - alloc_cpu[k]) / node_matrix[k, 0] * 40.0
                            + (node_matrix[k, 1] - alloc_mem[k]) / node_matrix[k, 1] * 30.0
                            - node_matrix[k, 2] * 0.5
                            for k in range(K)
                        ]
                        action = int(np.argmax(scores))
                    elif policy_type == "round_robin":
                        action = step % K
                    else:  # random
                        action = step % K

                    req_cpu = max(0.5, (task[1] + 3.0) * 1.5)
                    req_mem = max(1.0, (task[2] + 3.0) * 4.0)

                    if (alloc_cpu[action] + req_cpu > node_matrix[action, 0] * 0.95 or
                            alloc_mem[action] + req_mem > node_matrix[action, 1] * 0.95):
                        overload_counts += 1
                    else:
                        alloc_cpu[action] += req_cpu
                        alloc_mem[action] += req_mem
                        active_tasks[action] += 1

                    alloc_cpu *= 0.90
                    alloc_mem *= 0.90
                    active_tasks = np.maximum(0, active_tasks - 0.5)

            return overload_counts / 1000.0

        dqn_overload = run_sim("dqn")
        heur_overload = run_sim("heuristic")
        rr_overload = run_sim("round_robin")

        # DQN achieves dramatically fewer overloads than naive heuristic and round robin
        assert dqn_overload < 0.05, f"DQN overload rate too high: {dqn_overload:.1%}"
        assert dqn_overload < heur_overload, "DQN failed to beat heuristic scheduler in overload avoidance"
        assert dqn_overload < rr_overload, "DQN failed to beat round robin scheduler in overload avoidance"


# 6. ML Interface Contract Compatibility

class TestMLInterfaceContractCompatibility:
    """Verifies that trained artifacts produce payloads that fulfill existing ML schemas."""

    def test_dqn_produces_valid_placement_recommendation(self):
        from intellicluster.ml.schemas import PlacementRecommendation

        dqn_path = os.path.join(MODELS_DIR, "load_balancer_dqn.pt")
        meta_path = os.path.join(MODELS_DIR, "load_balancer_metadata.joblib")

        meta = joblib.load(meta_path)
        archetypes = meta["node_archetypes"]

        class QNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(25, 128),
                    nn.ReLU(),
                    nn.Linear(128, 64),
                    nn.ReLU(),
                    nn.Linear(64, 4),
                )

            def forward(self, x):
                return self.net(x)

        model = QNet()
        model.load_state_dict(torch.load(dqn_path, weights_only=True))
        model.eval()

        dummy_state = torch.randn(1, 25)
        with torch.no_grad():
            q_vals = model(dummy_state)
            action_idx = int(torch.argmax(q_vals).item())
            softmax_conf = float(torch.softmax(q_vals, dim=1)[0, action_idx].item())

        selected_node = archetypes[action_idx]
        rec = PlacementRecommendation(
            recommended_node_id=f"node-archetype-{action_idx}",
            confidence_score=round(softmax_conf, 4),
            predicted_latency_ms=selected_node["latency_ms"],
            strategy_used="dqn_v1",
            reasoning=f"Selected {selected_node['name']} based on highest Q-value.",
        )
        assert rec.recommended_node_id is not None
        assert 0.0 <= rec.confidence_score <= 1.0
        assert rec.strategy_used == "dqn_v1"

    def test_xgboost_and_iforest_produce_valid_health_prediction(self):
        from intellicluster.ml.schemas import HealthPrediction

        art_xgb = joblib.load(os.path.join(MODELS_DIR, "failure_prediction_ai4i_xgboost.joblib"))
        art_iforest = joblib.load(os.path.join(MODELS_DIR, "infrastructure_anomaly_iforest.joblib"))

        # Predict dummy health risk
        dummy_df_xgb = pd.DataFrame(np.zeros((1, len(art_xgb["feature_names"]))), columns=art_xgb["feature_names"])
        risk_prob = float(art_xgb["model"].predict_proba(dummy_df_xgb)[0, 1])

        # Predict dummy anomaly flag
        dummy_df_iforest = pd.DataFrame([[50.0, 50.0, 50.0, 100.0, 50.0]], columns=art_iforest["feature_names"])
        is_anom = bool(art_iforest["model"].predict(dummy_df_iforest)[0] == -1)

        health_pred = HealthPrediction(
            node_id="test-node-001",
            predicted_risk_score=round(risk_prob, 4),
            is_anomaly=is_anom,
            strategy_used="xgboost_ai4i_v1",
            reasoning=f"XGBoost risk: {risk_prob:.2%}, IForest anomaly flag: {is_anom}.",
        )
        assert health_pred.node_id == "test-node-001"
        assert 0.0 <= health_pred.predicted_risk_score <= 1.0
        assert isinstance(health_pred.is_anomaly, bool)

