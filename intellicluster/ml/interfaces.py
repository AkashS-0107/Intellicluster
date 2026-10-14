"""
Abstract interfaces and protocols defining the ML integration boundary.
Ensures the backend remains ML-ready without being ML-dependent.
"""

from abc import ABC, abstractmethod
from typing import Sequence

from intellicluster.ml.schemas import HealthPrediction, PlacementRecommendation
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload


class BaseSchedulerPredictor(ABC):
    """
    Contract for workload placement decision engines.
    Implemented by HeuristicSchedulerStrategy (active production) and ML models.
    """

    @abstractmethod
    def predict_optimal_node(
        self,
        workload: Workload,
        candidate_nodes: Sequence[Node],
    ) -> PlacementRecommendation:
        """
        Evaluate candidate nodes against workload requirements and recommend the optimal placement.

        :param workload: The Workload entity requiring scheduling.
        :param candidate_nodes: Eligible nodes with capacity and active status.
        :return: PlacementRecommendation containing recommended node ID, confidence, and reasoning.
        """
        pass


class BaseHealthPredictor(ABC):
    """
    Contract for predictive node health, failure forecasting, and anomaly detection.
    """

    @abstractmethod
    def predict_node_health(
        self,
        node: Node,
        telemetry_history: Sequence[TelemetrySnapshot],
    ) -> HealthPrediction:
        """
        Analyze current node state and recent telemetry history to predict failure probability.

        :param node: The Node entity to assess.
        :param telemetry_history: Recent sequence of TelemetrySnapshot entries for the node.
        :return: HealthPrediction containing risk score, anomaly flag, and diagnosis.
        """
        pass
