"""
Unit tests validating the ML abstraction boundary, interfaces, and heuristic strategy.
"""

from intellicluster.core.constants import NodeStatus
from intellicluster.ml.heuristic import (
    HeuristicHealthPredictor,
    HeuristicSchedulerStrategy,
    calculate_deterministic_health_score,
)
from intellicluster.ml.interfaces import BaseHealthPredictor, BaseSchedulerPredictor
from intellicluster.ml.schemas import PlacementRecommendation
from intellicluster.models.node import Node
from intellicluster.models.workload import Workload


def test_heuristic_scheduler_implements_interface():
    """Verify that HeuristicSchedulerStrategy correctly implements BaseSchedulerPredictor."""
    strategy = HeuristicSchedulerStrategy()
    assert isinstance(strategy, BaseSchedulerPredictor)


def test_heuristic_health_implements_interface():
    """Verify that HeuristicHealthPredictor implements BaseHealthPredictor."""
    predictor = HeuristicHealthPredictor()
    assert isinstance(predictor, BaseHealthPredictor)


def test_deterministic_health_score_calculation():
    """Verify deterministic health calculation math."""
    # Optimal conditions: 0% CPU, 0% Memory, low latency (<= 20ms)
    optimal_score = calculate_deterministic_health_score(0.0, 0.0, 5.0)
    assert optimal_score == 100.0

    # 50% CPU (-20 pts), 50% Mem (-17.5 pts), 10ms latency (0 pts) -> 62.5
    score_mid = calculate_deterministic_health_score(50.0, 50.0, 10.0)
    assert score_mid == 62.5

    # 100% CPU (-40 pts), 100% Mem (-35 pts), 70ms latency (-25 pts) -> 0.0
    score_critical = calculate_deterministic_health_score(100.0, 100.0, 70.0)
    assert score_critical == 0.0


def test_heuristic_scheduler_node_selection():
    """Verify that the heuristic scheduler picks the best candidate node."""
    strategy = HeuristicSchedulerStrategy()

    workload = Workload(
        name="test-job",
        cpu_cores_requested=2.0,
        memory_mb_requested=4096.0,
        max_latency_tolerance_ms=50.0,
    )

    # Node 1: High load, low health
    n1 = Node(
        id="node-1",
        hostname="n1",
        status=NodeStatus.READY.value,
        cpu_cores=8.0,
        memory_mb=16384.0,
        current_cpu_usage_pct=85.0,
        current_memory_usage_mb=12000.0,
        current_network_latency_ms=10.0,
        health_score=45.0,
    )

    # Node 2: Low load, high health, lower latency
    n2 = Node(
        id="node-2",
        hostname="n2",
        status=NodeStatus.READY.value,
        cpu_cores=8.0,
        memory_mb=16384.0,
        current_cpu_usage_pct=15.0,
        current_memory_usage_mb=2048.0,
        current_network_latency_ms=5.0,
        health_score=92.0,
    )

    recommendation = strategy.predict_optimal_node(workload, [n1, n2])
    assert isinstance(recommendation, PlacementRecommendation)
    assert recommendation.recommended_node_id == "node-2"
    assert recommendation.confidence_score > 0.5
    assert "n2" in recommendation.reasoning
