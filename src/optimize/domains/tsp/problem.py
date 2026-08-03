"""TSP optimization problem."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from optimize.domains.base_problem import OptimizationProblem
from optimize.domains.tsp.distance import build_distance_matrix, nearest_neighbor_route, tour_length
from optimize.domains.tsp.loader import TSPInstance, load_tsplib
from optimize.domains.tsp.neighborhoods import apply_operator, random_operator
from optimize.experiments.budget import EvaluationBudget


class TSPProblem(OptimizationProblem):
    domain_name = "tsp"

    def __init__(
        self,
        budget: EvaluationBudget,
        instance: TSPInstance,
        operators: list[str] | None = None,
        known_optimum: int | None = None,
        initial_solution: str = "random",
    ) -> None:
        super().__init__(budget)
        self.instance = instance
        self.operators = operators or ["swap", "insertion", "inversion", "two_opt"]
        self.known_optimum = known_optimum
        self.initial_solution = initial_solution
        self.distance_matrix = build_distance_matrix(instance.coordinates)

    @classmethod
    def from_config(cls, budget: EvaluationBudget, config: dict[str, Any]) -> TSPProblem:
        instance_path = config.get("instance_path")
        if not instance_path:
            raise ValueError("TSP domain requires instance_path in domain config")

        instance = load_tsplib(instance_path)
        operators = config.get("operators")
        known_optimum = cls._load_known_optimum(config, instance.name)
        initial_solution = config.get("initial_solution", "random")
        return cls(
            budget=budget,
            instance=instance,
            operators=operators,
            known_optimum=known_optimum,
            initial_solution=initial_solution,
        )

    @staticmethod
    def _load_known_optimum(config: dict[str, Any], instance_name: str) -> int | None:
        if "known_optimum" in config:
            return int(config["known_optimum"])

        metadata_path = config.get("metadata_path", "datasets/tsp/metadata.json")
        path = Path(metadata_path)
        if not path.exists():
            return None

        data = json.loads(path.read_text(encoding="utf-8"))
        optima = data.get("known_optima", {})
        value = optima.get(instance_name)
        return int(value) if value is not None else None

    def create_initial_solution(self, rng: np.random.Generator) -> list[int]:
        if self.initial_solution == "nearest_neighbor":
            return nearest_neighbor_route(self.distance_matrix, rng)
        route = list(range(self.instance.num_cities))
        rng.shuffle(route)
        return route

    def evaluate(self, solution: list[int]) -> float:
        if self.budget.exhausted():
            return float(tour_length(solution, self.distance_matrix))
        length = tour_length(solution, self.distance_matrix)
        return float(self._evaluate_with_budget(solution, length))

    def is_valid(self, solution: list[int]) -> bool:
        n = self.instance.num_cities
        return sorted(solution) == list(range(n))

    def get_neighbors(
        self,
        solution: list[int],
        operator: str,
        rng: np.random.Generator,
    ) -> list[list[int]]:
        if operator == "random":
            operator = random_operator(self.operators, rng)
        return [apply_operator(solution, operator, rng)]

    def decode_for_pso(self, position: list[float]) -> list[int]:
        indices = np.argsort(position)
        return indices.tolist()

    def serialize_solution(self, solution: list[int]) -> dict[str, Any]:
        length = tour_length(solution, self.distance_matrix)
        payload: dict[str, Any] = {
            "instance": self.instance.name,
            "route": solution,
            "distance": length,
        }
        if self.known_optimum is not None and self.known_optimum > 0:
            gap = ((length - self.known_optimum) / self.known_optimum) * 100.0
            payload["known_optimum"] = self.known_optimum
            payload["gap_percentage"] = gap
        return payload

    def domain_metrics(self, solution: list[int]) -> dict[str, Any]:
        metrics = {"distance": tour_length(solution, self.distance_matrix)}
        if self.known_optimum is not None:
            metrics["known_optimum"] = self.known_optimum
            metrics["gap_percentage"] = (
                (metrics["distance"] - self.known_optimum) / self.known_optimum
            ) * 100.0
        return metrics
