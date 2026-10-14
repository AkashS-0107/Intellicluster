"""
Cached Machine Learning Model Registry for INTELLICLUSTER.
Loads and caches trained artifacts safely from trusted repository paths.
Tracks operational status, rejection flags, and inference availability.
"""

from enum import Enum
import logging
from pathlib import Path
from typing import Any, Optional

import joblib
import torch

from intellicluster.ml.architectures import QNetwork, ResourceLSTM

logger = logging.getLogger(__name__)


class ModelOperationalStatus(str, Enum):
    """Operational status of a machine learning system in the INTELLICLUSTER catalog."""

    READY = "READY"  # Artifact loaded and verified for live runtime inference
    REJECTED = "REJECTED"  # Disqualified due to generalization failure / synthetic noise
    EXPERIMENTAL = "EXPERIMENTAL"  # Validated benchmark; comparison only, not primary scheduler
    ERROR = "ERROR"  # Artifact missing or failed deserialization
    UNAVAILABLE = "UNAVAILABLE"  # Not registered or file absent


class MLModelCatalogItem:
    """Catalog metadata and runtime handle for an individual ML model."""

    def __init__(
        self,
        model_id: str,
        name: str,
        system_role: str,
        algorithm: str,
        artifact_files: list[str],
        operational_status: ModelOperationalStatus,
        is_inference_enabled: bool,
        rejection_reason: Optional[str] = None,
        capabilities: Optional[list[str]] = None,
        limitations: Optional[str] = None,
        verified_metrics: Optional[dict[str, Any]] = None,
        schema_contract: Optional[str] = None,
    ) -> None:
        self.model_id = model_id
        self.name = name
        self.system_role = system_role
        self.algorithm = algorithm
        self.artifact_files = artifact_files
        self.operational_status = operational_status
        self.is_inference_enabled = is_inference_enabled
        self.rejection_reason = rejection_reason
        self.capabilities = capabilities or []
        self.limitations = limitations
        self.verified_metrics = verified_metrics or {}
        self.schema_contract = schema_contract
        self.loaded_artifact: Optional[Any] = None
        self.load_error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize catalog entry to dict suitable for API responses."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "system_role": self.system_role,
            "algorithm": self.algorithm,
            "artifact_files": self.artifact_files,
            "operational_status": self.operational_status.value,
            "is_inference_enabled": self.is_inference_enabled,
            "rejection_reason": self.rejection_reason,
            "capabilities": self.capabilities,
            "limitations": self.limitations,
            "verified_metrics": self.verified_metrics,
            "schema_contract": self.schema_contract,
            "is_loaded": self.loaded_artifact is not None,
            "load_error": self.load_error,
        }


class MLModelRegistry:
    """
    Singleton repository model cache.
    Loads models once at startup/on-demand and prevents loading from user-supplied paths.
    """

    _instance: Optional["MLModelRegistry"] = None

    def __init__(self, models_dir: Optional[Path] = None) -> None:
        if models_dir is None:
            # Trusted repository-relative path: repo_root / ml_models
            self.models_dir = Path(__file__).resolve().parents[2] / "ml_models"
        else:
            self.models_dir = models_dir

        self.catalog: dict[str, MLModelCatalogItem] = {}
        self._initialize_catalog()
        self._load_all_artifacts()

    @classmethod
    def get_instance(cls) -> "MLModelRegistry":
        """Retrieve or initialize the singleton registry instance."""
        if cls._instance is None:
            cls._instance = MLModelRegistry()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (primarily for testing)."""
        cls._instance = None

    def _initialize_catalog(self) -> None:
        """Declare expected catalog entries with verified empirical metadata."""
        self.catalog = {
            "model-1": MLModelCatalogItem(
                model_id="model-1",
                name="Model 1: Server Resource Clustering",
                system_role="Workload & Node Profiling",
                algorithm="K-Means (k=4)",
                artifact_files=[
                    "server_clustering_kmeans.joblib",
                    "server_clustering_scaler.joblib",
                ],
                operational_status=ModelOperationalStatus.READY,
                is_inference_enabled=True,
                capabilities=["Node archetype clustering", "Capacity profiling"],
                limitations=(
                    "Weak geometric separation (Silhouette ≈ 0.1478), but yields 4 highly stable "
                    "operational compute archetypes."
                ),
                verified_metrics={
                    "optimal_k": 4,
                    "silhouette": 0.1478,
                    "davies_bouldin": 1.9810,
                    "seed_stability": "100%",
                },
                schema_contract="Node hardware profile -> Cluster ID & Archetype metadata",
            ),
            "model-2a": MLModelCatalogItem(
                model_id="model-2a",
                name="Model 2A: Hardware Failure Prediction (AI4I)",
                system_role="Predictive Node Maintenance",
                algorithm="XGBoost Classifier (Stratified 5-Fold)",
                artifact_files=["failure_prediction_ai4i_xgboost.joblib"],
                operational_status=ModelOperationalStatus.READY,
                is_inference_enabled=True,
                capabilities=["Hardware failure probability scoring"],
                limitations=(
                    "Trained on industrial machine sensors (temperatures, RPM, torque, tool wear). "
                    "Requires explicit industrial sensor telemetry; does not automatically map "
                    "to compute server OS metrics. Lower precision (38.64%) yields false alarms."
                ),
                verified_metrics={
                    "roc_auc": 0.9748,
                    "pr_auc": 0.7281,
                    "recall": "87.32%",
                    "precision": "38.64%",
                    "prevalence": "3.39%",
                },
                schema_contract="BaseHealthPredictor -> HealthPrediction",
            ),
            "model-2b": MLModelCatalogItem(
                model_id="model-2b",
                name="Model 2B: Environmental Failure Prediction",
                system_role="Ambient Telemetry Risk Assessment",
                algorithm="XGBoost Classifier (Stratified 5-Fold)",
                artifact_files=["failure_prediction_environmental_xgboost.joblib"],
                operational_status=ModelOperationalStatus.REJECTED,
                is_inference_enabled=False,
                rejection_reason=(
                    "Disqualified for operational deployment. Severe overfitting on synthetic "
                    "uniform noise; out-of-fold ROC-AUC collapsed to 0.4891 (random coin-flip). "
                    "Production inference is strictly disabled."
                ),
                capabilities=[],
                limitations="Disqualified; zero predictive signal.",
                verified_metrics={
                    "oof_roc_auc": 0.4891,
                    "oof_pr_auc": 0.1026,
                    "in_sample_roc_auc": 0.9990,
                },
                schema_contract="REJECTED",
            ),
            "model-3": MLModelCatalogItem(
                model_id="model-3",
                name="Model 3: Temporal Resource Utilization Forecasting",
                system_role="Headroom & Load Forecasting",
                algorithm="Dual-Layer Stacked LSTM (168h Lookback -> 24h Horizon)",
                artifact_files=[
                    "resource_forecasting_lstm.pt",
                    "resource_forecasting_metadata.joblib",
                ],
                operational_status=ModelOperationalStatus.READY,
                is_inference_enabled=True,
                capabilities=["24-hour ahead multi-variable hourly resource forecasting"],
                limitations=(
                    "Requires 168 contiguous historical hourly observations (7 days) per node. "
                    "Predicts [cpu_utilization, memory_usage, workload]; storage_usage is an "
                    "input feature, not an output target."
                ),
                verified_metrics={
                    "test_mae": 14.81,
                    "persistence_mae": 22.59,
                    "improvement": ">34%",
                    "lookback_hours": 168,
                    "horizon_hours": 24,
                },
                schema_contract="168h Telemetry Series -> 24h [CPU, RAM, Workload] Forecast",
            ),
            "model-4a": MLModelCatalogItem(
                model_id="model-4a",
                name="Model 4A: Network Anomaly Detection",
                system_role="Network Packet Anomaly Filter",
                algorithm="Isolation Forest",
                artifact_files=["network_anomaly_iforest.joblib"],
                operational_status=ModelOperationalStatus.REJECTED,
                is_inference_enabled=False,
                rejection_reason=(
                    "Disqualified for operational deployment. Identical uniform score distribution "
                    "between normal traffic and attack samples (ROC-AUC ≈ 0.4980). "
                    "Production inference is strictly disabled."
                ),
                capabilities=[],
                limitations="Disqualified; normal vs attack score parity.",
                verified_metrics={"validation_roc_auc": 0.4980},
                schema_contract="REJECTED",
            ),
            "model-4b": MLModelCatalogItem(
                model_id="model-4b",
                name="Model 4B: Infrastructure Anomaly Detection",
                system_role="Host Telemetry Outlier Scoring",
                algorithm="Isolation Forest (Contamination=5%)",
                artifact_files=["infrastructure_anomaly_iforest.joblib"],
                operational_status=ModelOperationalStatus.READY,
                is_inference_enabled=True,
                capabilities=["Contextual telemetry density anomaly scoring"],
                limitations=(
                    "Detects multivariate density outliers, not simple 1D saturation. "
                    "Provides contextual advisory scoring only; must never trigger autonomous "
                    "node cordoning, deletion, or workload migration."
                ),
                verified_metrics={
                    "contamination": "5.0%",
                    "saturation_capture_rate": "25.05%",
                    "total_anomalies_flagged": 1316,
                },
                schema_contract="TelemetrySnapshot -> Contextual Anomaly Flag & Score",
            ),
            "model-5": MLModelCatalogItem(
                model_id="model-5",
                name="Model 5: Dynamic Load Balancer & Scheduler",
                system_role="Reinforcement Learning Placement Policy",
                algorithm="Deep Q-Network (DQN with Experience Replay)",
                artifact_files=[
                    "load_balancer_dqn.pt",
                    "load_balancer_metadata.joblib",
                ],
                operational_status=ModelOperationalStatus.EXPERIMENTAL,
                is_inference_enabled=True,
                capabilities=["Shadow placement recommendation & heuristic comparative analysis"],
                limitations=(
                    "Experimental reinforcement learning policy. The deterministic HeuristicSchedulerStrategy "
                    "remains the active production scheduler. DQN recommendations are strictly read-only "
                    "and will not commit database workload state changes."
                ),
                verified_metrics={
                    "mean_reward": "+81.06",
                    "placement_success": "98.3%",
                    "overload_rate": "1.62%",
                    "avg_latency_ms": 10.54,
                },
                schema_contract="BaseSchedulerPredictor -> Read-Only PlacementRecommendation",
            ),
        }

    def _load_all_artifacts(self) -> None:
        """Load and cache eligible model artifacts from disk."""
        logger.info("Initializing ML Model Registry from %s", self.models_dir)

        # 1. Model 1: KMeans
        item1 = self.catalog["model-1"]
        try:
            kmeans_path = self.models_dir / "server_clustering_kmeans.joblib"
            scaler_path = self.models_dir / "server_clustering_scaler.joblib"
            if kmeans_path.exists() and scaler_path.exists():
                kmeans_bundle = joblib.load(kmeans_path)
                scaler_bundle = joblib.load(scaler_path)
                item1.loaded_artifact = {
                    "model": kmeans_bundle["model"],
                    "preprocessor": scaler_bundle,
                    "archetypes": kmeans_bundle.get("archetypes", {}),
                    "num_features": kmeans_bundle.get("num_features", []),
                    "cat_features": kmeans_bundle.get("cat_features", []),
                }
            else:
                item1.operational_status = ModelOperationalStatus.ERROR
                item1.load_error = "Artifact file missing on disk"
        except Exception as e:
            logger.error("Failed to load Model 1 (KMeans): %s", e)
            item1.operational_status = ModelOperationalStatus.ERROR
            item1.load_error = str(e)

        # 2. Model 2A: AI4I XGBoost
        item2a = self.catalog["model-2a"]
        try:
            ai4i_path = self.models_dir / "failure_prediction_ai4i_xgboost.joblib"
            if ai4i_path.exists():
                ai4i_bundle = joblib.load(ai4i_path)
                item2a.loaded_artifact = {
                    "model": ai4i_bundle["model"],
                    "feature_names": ai4i_bundle.get("feature_names", []),
                    "metrics": ai4i_bundle.get("metrics", {}),
                }
            else:
                item2a.operational_status = ModelOperationalStatus.ERROR
                item2a.load_error = "Artifact file missing on disk"
        except Exception as e:
            logger.error("Failed to load Model 2A (AI4I): %s", e)
            item2a.operational_status = ModelOperationalStatus.ERROR
            item2a.load_error = str(e)

        # 3. Model 2B: Environmental XGBoost (Preserve for audit, mark REJECTED, do not load for inference)
        item2b = self.catalog["model-2b"]
        env_path = self.models_dir / "failure_prediction_environmental_xgboost.joblib"
        if not env_path.exists():
            item2b.load_error = "Artifact file missing on disk"

        # 4. Model 3: LSTM Resource Forecasting
        item3 = self.catalog["model-3"]
        try:
            lstm_path = self.models_dir / "resource_forecasting_lstm.pt"
            meta_path = self.models_dir / "resource_forecasting_metadata.joblib"
            if lstm_path.exists() and meta_path.exists():
                meta_bundle = joblib.load(meta_path)
                lstm_model = ResourceLSTM(
                    in_dim=meta_bundle.get("model_architecture", {}).get("input_dim", 5),
                    h1=meta_bundle.get("model_architecture", {}).get("lstm_hidden_1", 64),
                    h2=meta_bundle.get("model_architecture", {}).get("lstm_hidden_2", 32),
                    out_horizon=meta_bundle.get("forecast_horizon_hours", 24),
                    out_vars=len(meta_bundle.get("target_features", ["cpu_utilization", "memory_usage", "workload"])),
                    dropout_prob=meta_bundle.get("model_architecture", {}).get("dropout", 0.2),
                )
                lstm_model.load_state_dict(torch.load(lstm_path, weights_only=True))
                lstm_model.eval()
                item3.loaded_artifact = {
                    "model": lstm_model,
                    "metadata": meta_bundle,
                    "scaler": meta_bundle.get("scaler"),
                    "input_features": meta_bundle.get("input_features", []),
                    "target_features": meta_bundle.get("target_features", []),
                    "imputation_medians": meta_bundle.get("imputation_medians", {}),
                }
            else:
                item3.operational_status = ModelOperationalStatus.ERROR
                item3.load_error = "Artifact file missing on disk"
        except Exception as e:
            logger.error("Failed to load Model 3 (LSTM): %s", e)
            item3.operational_status = ModelOperationalStatus.ERROR
            item3.load_error = str(e)

        # 5. Model 4A: Network Anomaly IF (Preserve for audit, mark REJECTED, do not load for inference)
        item4a = self.catalog["model-4a"]
        net_path = self.models_dir / "network_anomaly_iforest.joblib"
        if not net_path.exists():
            item4a.load_error = "Artifact file missing on disk"

        # 6. Model 4B: Infrastructure Anomaly IF
        item4b = self.catalog["model-4b"]
        try:
            infra_path = self.models_dir / "infrastructure_anomaly_iforest.joblib"
            if infra_path.exists():
                infra_bundle = joblib.load(infra_path)
                item4b.loaded_artifact = {
                    "model": infra_bundle["model"],
                    "feature_names": infra_bundle.get("feature_names", []),
                    "contamination": infra_bundle.get("contamination", 0.05),
                }
            else:
                item4b.operational_status = ModelOperationalStatus.ERROR
                item4b.load_error = "Artifact file missing on disk"
        except Exception as e:
            logger.error("Failed to load Model 4B (Infra IF): %s", e)
            item4b.operational_status = ModelOperationalStatus.ERROR
            item4b.load_error = str(e)

        # 7. Model 5: DQN Load Balancer
        item5 = self.catalog["model-5"]
        try:
            dqn_path = self.models_dir / "load_balancer_dqn.pt"
            dqn_meta_path = self.models_dir / "load_balancer_metadata.joblib"
            if dqn_path.exists() and dqn_meta_path.exists():
                dqn_meta = joblib.load(dqn_meta_path)
                q_net = QNetwork(
                    in_dim=dqn_meta.get("state_dim", 25),
                    out_actions=dqn_meta.get("action_dim", 4),
                )
                q_net.load_state_dict(torch.load(dqn_path, weights_only=True))
                q_net.eval()
                item5.loaded_artifact = {
                    "model": q_net,
                    "metadata": dqn_meta,
                    "archetypes": dqn_meta.get("node_archetypes", []),
                    "state_dim": dqn_meta.get("state_dim", 25),
                    "action_dim": dqn_meta.get("action_dim", 4),
                }
            else:
                item5.operational_status = ModelOperationalStatus.ERROR
                item5.load_error = "Artifact file missing on disk"
        except Exception as e:
            logger.error("Failed to load Model 5 (DQN): %s", e)
            item5.operational_status = ModelOperationalStatus.ERROR
            item5.load_error = str(e)

    def get_catalog_list(self) -> list[dict[str, Any]]:
        """Return list of all catalog model descriptions."""
        return [item.to_dict() for item in self.catalog.values()]

    def get_catalog_item(self, model_id: str) -> Optional[MLModelCatalogItem]:
        """Retrieve catalog item by model identifier."""
        return self.catalog.get(model_id)

    def get_loaded_artifact(self, model_id: str) -> Any:
        """
        Safely fetch loaded model artifact.
        Raises ValueError if rejected or not loaded.
        """
        item = self.catalog.get(model_id)
        if not item:
            raise ValueError(f"Model ID '{model_id}' is not registered in INTELLICLUSTER catalog.")
        if item.operational_status == ModelOperationalStatus.REJECTED:
            raise PermissionError(
                f"Model '{item.name}' is REJECTED ({item.rejection_reason}). Production inference is forbidden."
            )
        if item.loaded_artifact is None:
            raise RuntimeError(
                f"Model '{item.name}' is not loaded (Status: {item.operational_status.value}, Error: {item.load_error})."
            )
        return item.loaded_artifact
