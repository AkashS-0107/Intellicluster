"""
Deterministic heuristic implementations for workload scheduling and node health.
These provide mathematical baselines for cluster operations and workload placement.
"""

from typing import Sequence

from intellicluster.core.constants import NodeStatus
from intellicluster.core.logging import logger
from intellicluster.ml.interfaces import BaseHealthPredictor, BaseSchedulerPredictor
from intellicluster.ml.schemas import HealthPrediction, PlacementRecommendation
from intellicluster.models.node import Node
from intellicluster.models.telemetry import TelemetrySnapshot
from intellicluster.models.workload import Workload


def calculate_deterministic_health_score(
    cpu_usage_pct: float,
    memory_usage_pct: float,
    network_latency_ms: float,
) -> float:
    """
    Computes a deterministic node health score on a scale of 0.0 (critical) to 100.0 (optimal).

    Algorithm Formulation:
    -----------------------
    Base Score: 100.0
    Deductions:
      1. CPU Penalty: 0.40 * cpu_usage_pct
         - Sustained 100% CPU results in a 40 point deduction.
      2. Memory Penalty: 0.35 * memory_usage_pct
         - Sustained 100% Memory results in a 35 point deduction.
      3. Latency Penalty:
         - Latency <= 20ms: 0 deduction (normal operating condition)
         - Latency > 20ms: min(25.0, (network_latency_ms - 20) * 0.5)
         - Latency of 70ms+ caps at 25 point deduction.

    Total maximum deduction: 40 + 35 + 25 = 100 points.
    Minimum health score clamped to 0.0; maximum clamped to 100.0.
    """
    cpu_penalty = 0.40 * max(0.0, min(100.0, cpu_usage_pct))
    mem_penalty = 0.35 * max(0.0, min(100.0, memory_usage_pct))

    latency_penalty = 0.0
    if network_latency_ms > 20.0:
        latency_penalty = min(25.0, (network_latency_ms - 20.0) * 0.5)

    raw_score = 100.0 - (cpu_penalty + mem_penalty + latency_penalty)
    return round(max(0.0, min(100.0, raw_score)), 2)


class HeuristicSchedulerStrategy(BaseSchedulerPredictor):
    """
    Deterministic best-fit workload placement scheduler.
    Active production scheduler for INTELLICLUSTER.
    """

    def predict_optimal_node(
        self,
        workload: Workload,
        candidate_nodes: Sequence[Node],
    ) -> PlacementRecommendation:
        """
        Selects the best available candidate node using deterministic capacity and fitness scoring.
        """
        eligible: list[tuple[Node, float]] = []

        for node in candidate_nodes:
            # 1. State filter: Node must be active and not cordoned
            if node.is_cordoned:
                continue
            if node.status not in (NodeStatus.READY.value, NodeStatus.BUSY.value):
                continue

            # 2. Capacity filter: Check allocatable CPU & Memory headroom
            # (Node models calculate headroom using capacity minus active workload counts / cached usage)
            used_mem_pct = (node.current_memory_usage_mb / node.memory_mb * 100.0) if node.memory_mb > 0 else 100.0
            free_cpu_cores = node.cpu_cores * (1.0 - (node.current_cpu_usage_pct / 100.0))
            free_memory_mb = node.memory_mb - node.current_memory_usage_mb

            if free_cpu_cores < workload.cpu_cores_requested:
                continue
            if free_memory_mb < workload.memory_mb_requested:
                continue

            # 3. Latency SLA constraint filter
            if workload.max_latency_tolerance_ms is not None:
                if node.current_network_latency_ms > workload.max_latency_tolerance_ms:
                    continue

            # 4. Fitness calculation:
            # Rewards healthy, low-latency nodes with balanced resource availability.
            fitness = (
                (node.health_score * 0.40)
                + ((100.0 - node.current_cpu_usage_pct) * 0.30)
                + ((100.0 - used_mem_pct) * 0.20)
                - (min(50.0, node.current_network_latency_ms) * 0.20)
            )
            eligible.append((node, fitness))

        if not eligible:
            logger.warning(
                "Heuristic scheduler could not find an eligible node",
                extra={"workload_id": workload.id, "candidates_count": len(candidate_nodes)},
            )
            return PlacementRecommendation(
                recommended_node_id=None,
                confidence_score=0.0,
                predicted_latency_ms=None,
                strategy_used="heuristic_best_fit",
                reasoning=(
                    "No candidate node met resource headroom (CPU/RAM), "
                    "latency tolerance, or active health requirements."
                ),
            )

        # Sort eligible descending by fitness score
        eligible.sort(key=lambda item: item[1], reverse=True)
        best_node, best_fitness = eligible[0]

        # Normalized confidence based on fitness (0 to 100 clamped to 0.5 - 0.99 for heuristic)
        confidence = round(max(0.5, min(0.99, best_fitness / 100.0)), 2)

        reasoning = (
            f"Selected node '{best_node.hostname}' with fitness score {best_fitness:.2f}. "
            f"Headroom: CPU {best_node.current_cpu_usage_pct:.1f}% used, "
            f"Health: {best_node.health_score:.1f}, "
            f"Latency: {best_node.current_network_latency_ms:.1f}ms."
        )

        return PlacementRecommendation(
            recommended_node_id=best_node.id,
            confidence_score=confidence,
            predicted_latency_ms=best_node.current_network_latency_ms,
            strategy_used="heuristic_best_fit",
            reasoning=reasoning,
        )


class HeuristicHealthPredictor(BaseHealthPredictor):
    """
    Deterministic baseline health evaluator.
    Satisfies BaseHealthPredictor contract for cluster monitoring.
    """

    def predict_node_health(
        self,
        node: Node,
        telemetry_history: Sequence[TelemetrySnapshot],
    ) -> HealthPrediction:
        """
        Evaluates node health based on deterministic calculations.
        """
        mem_pct = (node.current_memory_usage_mb / node.memory_mb * 100.0) if node.memory_mb > 0 else 0.0
        health = calculate_deterministic_health_score(
            cpu_usage_pct=node.current_cpu_usage_pct,
            memory_usage_pct=mem_pct,
            network_latency_ms=node.current_network_latency_ms,
        )

        # Heuristic risk is inverse of health
        risk_score = round((100.0 - health) / 100.0, 3)
        is_anomaly = risk_score > 0.70

        return HealthPrediction(
            node_id=node.id,
            predicted_risk_score=risk_score,
            is_anomaly=is_anomaly,
            strategy_used="heuristic_baseline_health",
            reasoning=(
                f"Deterministic health calculation yielded {health:.1f}/100.0 "
                f"(CPU: {node.current_cpu_usage_pct:.1f}%, Mem: {mem_pct:.1f}%, "
                f"Latency: {node.current_network_latency_ms:.1f}ms)."
            ),
        )
