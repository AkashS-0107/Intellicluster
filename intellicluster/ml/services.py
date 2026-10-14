"""
Machine Learning Runtime Inference Services for INTELLICLUSTER.
Executes real inference pipelines using cached model artifacts.
Handles validation, preprocessing, inverse scaling, and strict safety guardrails.
"""

import logging
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd
import torch
from sqlalchemy.orm import Session

from intellicluster.core.exceptions import (
    IntelliClusterException,
    NoAvailableNodeException,
    WorkloadNotFoundException,
)
from intellicluster.ml.heuristic import HeuristicSchedulerStrategy
from intellicluster.ml.registry import MLModelRegistry, ModelOperationalStatus
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload
from intellicluster.schemas.ml import (
    AI4IInferenceRequestSchema,
    AI4IInferenceResponseSchema,
    DQNPlacementRequestSchema,
    DQNPlacementResponseSchema,
    ForecastStepSchema,
    InfrastructureAnomalyRequestSchema,
    InfrastructureAnomalyResponseSchema,
    KMeansInferenceRequestSchema,
    KMeansInferenceResponseSchema,
    LSTMDirectForecastingRequestSchema,
    LSTMForecastingResponseSchema,
    OfflineEvaluationRequestSchema,
    OfflineEvaluationResponseSchema,
)

logger = logging.getLogger(__name__)


# Domain ML Exceptions

class ModelNotReadyException(IntelliClusterException):
    """Raised when an artifact has not been loaded or is in an error state."""

    def __init__(self, model_id: str, reason: str) -> None:
        super().__init__(
            message=f"Model '{model_id}' is not ready for inference: {reason}",
            error_code="MODEL_NOT_READY",
            details={"model_id": model_id, "reason": reason},
        )


class ModelRejectedException(IntelliClusterException):
    """Raised when an attempt is made to execute inference on a quarantined/rejected model."""

    def __init__(self, model_id: str, reason: Optional[str] = None) -> None:
        msg = f"Model '{model_id}' is REJECTED and quarantined from production inference."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            message=msg,
            error_code="MODEL_REJECTED",
            details={"model_id": model_id, "rejection_reason": reason},
        )


class InsufficientHistoryException(IntelliClusterException):
    """Raised when a time-series model does not have sufficient history for valid inference."""

    def __init__(
        self,
        required: int,
        available: int,
        node_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        msg = (
            f"Insufficient historical telemetry: required {required} contiguous hourly snapshots, "
            f"but found {available} for node '{node_id or 'unknown'}'. Transmit additional heartbeats "
            "to build valid historical lookback window."
        )
        if reason:
            msg = reason
        super().__init__(
            message=msg,
            error_code="INSUFFICIENT_TELEMETRY_HISTORY",
            details={
                "required_snapshots": required,
                "available_snapshots": available,
                "node_id": node_id,
                "validation_reason": reason,
            },
        )


# Model 1: KMeans Server Clustering Inference Service

class KMeansInferenceService:
    """Service wrapping Model 1 (KMeans server clustering & archetype profiling)."""

    @staticmethod
    def predict_archetype(req: KMeansInferenceRequestSchema) -> KMeansInferenceResponseSchema:
        registry = MLModelRegistry.get_instance()
        artifact = registry.get_loaded_artifact("model-1")

        model = artifact["model"]
        preprocessor = artifact["preprocessor"]
        archetypes = artifact.get("archetypes", {})

        row_dict = {
            "CPU_Cores": float(req.cpu_cores),
            "Memory_GB": float(req.memory_gb),
            "VM_Instances": req.vm_instances,
            "Container_Replicas": req.container_replicas,
            "Storage_IOPS": req.storage_iops,
            "Network_Bandwidth_Mbps": float(req.network_bandwidth_mbps),
            "CPU_Utilization_pct": float(req.cpu_utilization_pct),
            "Memory_Utilization_pct": float(req.memory_utilization_pct),
            "Network_Utilization_pct": float(req.network_utilization_pct),
            "Disk_Utilization_pct": float(req.disk_utilization_pct),
            "Request_Rate_RPS": float(req.request_rate_rps),
            "Load_Balancer_Capacity": float(req.load_balancer_capacity),
            "Application_Tier": req.application_tier,
        }
        df = pd.DataFrame([row_dict])

        # Execute transformation and prediction
        X_trans = preprocessor.transform(df)
        cluster_id = int(model.predict(X_trans)[0])

        profile = archetypes.get(cluster_id, {})
        # Map cluster ID to descriptive operational archetype name
        cluster_names = {
            0: "Balanced_Worker_Tier",
            1: "Compute_Intensive_Core",
            2: "High_Utilization_Saturated",
            3: "Lightweight_Edge_Tier",
        }
        archetype_name = cluster_names.get(cluster_id, f"Cluster_Archetype_{cluster_id}")

        return KMeansInferenceResponseSchema(
            predicted_cluster=cluster_id,
            archetype_name=archetype_name,
            archetype_profile=profile,
            transformed_feature_dim=int(X_trans.shape[1]),
            strategy_used="kmeans_v1",
        )


# Model 2A: AI4I XGBoost Failure Prediction Service

class AI4IInferenceService:
    """Service wrapping Model 2A (AI4I predictive maintenance classifier)."""

    @staticmethod
    def predict_failure_risk(req: AI4IInferenceRequestSchema) -> AI4IInferenceResponseSchema:
        registry = MLModelRegistry.get_instance()
        artifact = registry.get_loaded_artifact("model-2a")

        model = artifact["model"]
        feature_names = artifact["feature_names"]

        # Map categorical machine type to One-Hot columns (drop_first on Type)
        type_upper = req.machine_type.strip().upper()
        type_l = 1.0 if type_upper == "L" else 0.0
        type_m = 1.0 if type_upper == "M" else 0.0

        row_dict = {
            "Air_temperature_K": float(req.air_temperature_k),
            "Process_temperature_K": float(req.process_temperature_k),
            "Rotational_speed_rpm": float(req.rotational_speed_rpm),
            "Torque_Nm": float(req.torque_nm),
            "Tool_wear_min": float(req.tool_wear_min),
            "Type_L": type_l,
            "Type_M": type_m,
        }
        df = pd.DataFrame([row_dict])[feature_names]

        # Predict failure probability
        prob = float(model.predict_proba(df)[0, 1])
        prob = round(max(0.0, min(1.0, prob)), 4)
        pred_class = 1 if prob >= 0.50 else 0

        if prob < 0.25:
            risk_level = "LOW"
        elif prob < 0.50:
            risk_level = "ELEVATED"
        elif prob < 0.75:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return AI4IInferenceResponseSchema(
            failure_probability=prob,
            predicted_class=pred_class,
            threshold_used=0.50,
            risk_level=risk_level,
            strategy_used="ai4i_xgboost_v1",
        )


# Model 3: Multivariate LSTM Resource Forecasting Service

class LSTMForecastingService:
    """Service wrapping Model 3 (Temporal multivariate LSTM resource forecaster)."""

    @staticmethod
    def forecast_from_matrix(sequence: list[list[float]]) -> list[ForecastStepSchema]:
        """
        Execute raw forward pass given a 168x5 sequence.
        Input features: [cpu_utilization, memory_usage, storage_usage, workload, Resource Allocation]
        Target targets: [cpu_utilization, memory_usage, workload]
        """
        registry = MLModelRegistry.get_instance()
        artifact = registry.get_loaded_artifact("model-3")

        model = artifact["model"]
        scaler = artifact["scaler"]
        input_features = artifact["input_features"]
        target_features = artifact["target_features"]
        medians = artifact.get("imputation_medians", {})

        df = pd.DataFrame(sequence, columns=input_features)
        df_imputed = df.ffill().fillna(medians)
        scaled_data = scaler.transform(df_imputed)

        tensor_in = torch.tensor(scaled_data, dtype=torch.float32).unsqueeze(0)  # (1, 168, 5)

        with torch.no_grad():
            preds_scaled = model(tensor_in).squeeze(0).numpy()  # (24, 3)

        # Invert scaling on targets
        target_indices = [input_features.index(c) for c in target_features]
        center = scaler.center_[target_indices]
        scale = scaler.scale_[target_indices]
        preds_unscaled = preds_scaled * scale + center

        forecast_steps = []
        for step_idx in range(24):
            forecast_steps.append(
                ForecastStepSchema(
                    step_hour=step_idx + 1,
                    predicted_cpu_utilization=round(float(preds_unscaled[step_idx, 0]), 2),
                    predicted_memory_usage=round(float(preds_unscaled[step_idx, 1]), 2),
                    predicted_workload=round(float(preds_unscaled[step_idx, 2]), 2),
                )
            )
        return forecast_steps

    @classmethod
    def forecast_for_node(cls, session: Session, node_id: str) -> LSTMForecastingResponseSchema:
        """
        Fetch persisted historical snapshots for node and generate 24h forecast.
        Enforces 168 valid contiguous hourly observations via TelemetryService.validate_node_hourly_history;
        raises InsufficientHistoryException if fewer exist or intervals are missing.
        """
        from intellicluster.services.telemetry_service import TelemetryService

        is_ready, readiness, matrix = TelemetryService.validate_node_hourly_history(
            session=session,
            node_id=node_id,
            required_hours=168,
        )

        if not is_ready or matrix is None:
            raise InsufficientHistoryException(
                required=readiness.required_observations,
                available=readiness.valid_hourly_observations,
                node_id=node_id,
                reason=readiness.validation_reason,
            )

        predictions = cls.forecast_from_matrix(matrix)

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
            node_id=node_id,
            strategy_used="multivariate_lstm_v1",
        )

    @classmethod
    def evaluate_offline_dataset(cls, start_index: int = 0) -> OfflineEvaluationResponseSchema:
        """
        Evaluate Model 3 against genuine historical dataset (data/Resource_utilization.csv).
        Loads exactly 168 rows starting from start_index without modifying database state.
        """
        repo_root = Path(__file__).resolve().parents[2]
        dataset_path = repo_root / "data" / "Resource_utilization.csv"
        if not dataset_path.exists():
            raise IntelliClusterException(
                message=f"Historical dataset file not found at {dataset_path}",
                error_code="DATASET_NOT_FOUND",
                details={"dataset_path": str(dataset_path)},
            )

        df = pd.read_csv(dataset_path)
        total_rows = len(df)
        if start_index + 168 > total_rows:
            start_index = max(0, total_rows - 168)

        eval_subset = df.iloc[start_index : start_index + 168]
        features = [
            "cpu_utilization",
            "memory_usage",
            "storage_usage",
            "workload",
            "Resource Allocation",
        ]
        sequence = eval_subset[features].values.tolist()

        predictions = cls.forecast_from_matrix(sequence)

        t_start = str(eval_subset["timestamp"].iloc[0])
        t_end = str(eval_subset["timestamp"].iloc[-1])

        return OfflineEvaluationResponseSchema(
            dataset_name="Resource_utilization.csv",
            dataset_total_records=total_rows,
            evaluation_range=f"{t_start} to {t_end} (168 contiguous hours)",
            forecast_horizon_hours=24,
            lookback_window_hours=168,
            target_variables=["cpu_utilization", "memory_usage", "workload"],
            input_features_used=features,
            predictions=predictions,
            is_offline_benchmark=True,
            advisory=(
                "OFFLINE DATASET BENCHMARK: Inference executed against genuine historical dataset "
                "(data/Resource_utilization.csv). This does NOT represent live node telemetry and zero database state is modified."
            ),
            strategy_used="multivariate_lstm_v1_offline_dataset",
        )


# Model 4B: Infrastructure Anomaly Isolation Forest Service

class InfrastructureAnomalyService:
    """Service wrapping Model 4B (Host telemetry density anomaly detection)."""

    @staticmethod
    def detect_anomaly(req: InfrastructureAnomalyRequestSchema) -> InfrastructureAnomalyResponseSchema:
        registry = MLModelRegistry.get_instance()
        artifact = registry.get_loaded_artifact("model-4b")

        model = artifact["model"]
        feature_names = artifact["feature_names"]

        row_dict = {
            "cpu_utilization": float(req.cpu_utilization),
            "memory_usage": float(req.memory_usage),
            "storage_usage": float(req.storage_usage),
            "workload": float(req.workload),
            "Resource Allocation": float(req.resource_allocation),
        }
        df = pd.DataFrame([row_dict])[feature_names]

        # Negative decision score: higher means more anomalous
        raw_score = float(-model.score_samples(df)[0])
        raw_label = int(model.predict(df)[0])
        is_anom = raw_label == -1

        return InfrastructureAnomalyResponseSchema(
            anomaly_score=round(raw_score, 4),
            is_anomaly=is_anom,
            contamination_rate=0.05,
            strategy_used="infrastructure_iforest_v1",
        )


# Model 5: DQN Load Balancing Benchmark Service

class DQNBenchmarkService:
    """
    Service wrapping Model 5 (DQN Reinforcement Learning Load Balancer).
    CRITICAL: Read-only shadow benchmark. Never mutates database workload state.
    """

    @staticmethod
    def evaluate_placement(session: Session, req: DQNPlacementRequestSchema) -> DQNPlacementResponseSchema:
        registry = MLModelRegistry.get_instance()
        artifact = registry.get_loaded_artifact("model-5")

        q_net = artifact["model"]
        archetypes = artifact.get("archetypes", [])

        # Scenario A: Explicit 25-dim state vector supplied
        if req.state_vector is not None:
            state = np.array(req.state_vector, dtype=np.float32)
            tensor_in = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                q_vals = q_net(tensor_in).squeeze(0)
                probs = torch.softmax(q_vals, dim=0).numpy()

            action_idx = int(torch.argmax(q_vals).item())
            confidence = round(float(probs[action_idx]), 4)
            chosen_arch = archetypes[action_idx] if action_idx < len(archetypes) else {}
            arch_name = chosen_arch.get("name", f"Archetype_{action_idx}")

            return DQNPlacementResponseSchema(
                recommended_action=action_idx,
                recommended_archetype_name=arch_name,
                archetype_profile=chosen_arch,
                q_values=[round(float(v), 4) for v in q_vals.tolist()],
                confidence_score=confidence,
                is_state_mutated=False,
                heuristic_comparison=None,
                strategy_used="dqn_v1_shadow_benchmark",
            )

        # Scenario B: Existing workload and candidate nodes comparison
        if not req.workload_id:
            # Generate default synthetic state evaluation if neither provided
            dummy_state = np.zeros(25, dtype=np.float32)
            tensor_in = torch.tensor(dummy_state, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                q_vals = q_net(tensor_in).squeeze(0)
                probs = torch.softmax(q_vals, dim=0).numpy()

            action_idx = int(torch.argmax(q_vals).item())
            chosen_arch = archetypes[action_idx] if action_idx < len(archetypes) else {}
            arch_name = chosen_arch.get("name", f"Archetype_{action_idx}")

            return DQNPlacementResponseSchema(
                recommended_action=action_idx,
                recommended_archetype_name=arch_name,
                archetype_profile=chosen_arch,
                q_values=[round(float(v), 4) for v in q_vals.tolist()],
                confidence_score=round(float(probs[action_idx]), 4),
                is_state_mutated=False,
                heuristic_comparison=None,
                strategy_used="dqn_v1_shadow_benchmark",
            )

        workload = session.get(Workload, req.workload_id)
        if not workload:
            raise WorkloadNotFoundException(req.workload_id)

        # Query candidate nodes
        if req.candidate_node_ids:
            nodes: list[Node] = []
            for nid in req.candidate_node_ids:
                node = session.get(Node, nid)
                if node is not None:
                    nodes.append(node)
        else:
            stmt = session.query(Node)
            if workload.cluster_id:
                stmt = stmt.filter(Node.cluster_id == workload.cluster_id)
            nodes = list(stmt.all())

        if not nodes:
            raise NoAvailableNodeException(
                workload_id=workload.id,
                cpu_needed=float(workload.cpu_cores_requested),
                mem_needed=float(workload.memory_mb_requested),
            )

        # Construct 25-dim state vector: 8 task features + 16 candidate features + 1 bg feature
        task_features = [
            workload.cpu_cores_requested,
            workload.memory_mb_requested / 1024.0,
            workload.storage_gb_requested,
            workload.max_latency_tolerance_ms or 50.0,
            100.0,  # IO operations estimate
            50.0,   # Disk usage estimate
            10.0,   # Num connections estimate
            1.0 if workload.priority == "HIGH" else 0.5,
        ]

        node_features = []
        for i in range(4):
            if i < len(nodes):
                n = nodes[i]
                fc = max(0.0, 1.0 - (n.current_cpu_usage_pct / 100.0))
                fm = max(0.0, 1.0 - (n.current_memory_usage_mb / n.memory_mb if n.memory_mb > 0 else 1.0))
                nl = min(1.0, n.current_network_latency_ms / 50.0)
                nt = min(1.0, n.active_workload_count / 10.0)
                node_features.extend([fc, fm, nl, nt])
            else:
                node_features.extend([0.0, 0.0, 1.0, 1.0])

        bg_feature = [0.5]  # Nominal background telemetry load
        full_state = np.array(task_features + node_features + bg_feature, dtype=np.float32)

        tensor_in = torch.tensor(full_state, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            q_vals = q_net(tensor_in).squeeze(0)
            probs = torch.softmax(q_vals, dim=0).numpy()

        action_idx = int(torch.argmax(q_vals).item())
        chosen_arch = archetypes[action_idx] if action_idx < len(archetypes) else {}
        arch_name = chosen_arch.get("name", f"Archetype_{action_idx}")

        # Compute side-by-side heuristic recommendation
        heuristic_strat = HeuristicSchedulerStrategy()
        heur_rec = heuristic_strat.predict_optimal_node(workload, nodes)

        heur_comp = {
            "heuristic_recommended_node_id": heur_rec.recommended_node_id,
            "heuristic_confidence_score": heur_rec.confidence_score,
            "heuristic_reasoning": heur_rec.reasoning,
            "policy": "HeuristicSchedulerStrategy remains the active production scheduler",
        }

        return DQNPlacementResponseSchema(
            recommended_action=action_idx,
            recommended_archetype_name=arch_name,
            archetype_profile=chosen_arch,
            q_values=[round(float(v), 4) for v in q_vals.tolist()],
            confidence_score=round(float(probs[action_idx]), 4),
            is_state_mutated=False,
            heuristic_comparison=heur_comp,
            strategy_used="dqn_v1_shadow_benchmark",
        )
