"""Mock problem for framework smoke tests."""

from __future__ import annotations

from typing import Any

import numpy as np

from optimize.domains.base_problem import OptimizationProblem
from optimize.experiments.budget import EvaluationBudget


class MockSphereProblem(OptimizationProblem):
    """Minimize sum of squares of a binary vector (discrete stand-in for sphere)."""

    domain_name = "mock"

    def __init__(self, budget: EvaluationBudget, dimension: int = 5) -> None:
        super().__init__(budget)
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension

    def create_initial_solution(self, rng: np.random.Generator) -> list[int]:
        return rng.integers(0, 2, size=self.dimension).tolist()

    def evaluate(self, solution: list[int]) -> float:
        value = float(sum(x * x for x in solution))
        return self._evaluate_with_budget(solution, value)

    def is_valid(self, solution: list[int]) -> bool:
        return (
            isinstance(solution, list)
            and len(solution) == self.dimension
            and all(x in (0, 1) for x in solution)
        )

    def get_neighbors(
        self,
        solution: list[int],
        operator: str,
        rng: np.random.Generator,
    ) -> list[list[int]]:
        if operator != "flip":
            raise ValueError(f"unsupported operator: {operator}")
        idx = int(rng.integers(0, self.dimension))
        neighbor = solution.copy()
        neighbor[idx] = 1 - neighbor[idx]
        return [neighbor]

    def decode_for_pso(self, position: Any) -> list[int]:
        if not isinstance(position, list):
            raise TypeError("position must be a list")
        return [1 if x >= 0.5 else 0 for x in position]

    def serialize_solution(self, solution: list[int]) -> dict[str, Any]:
        return {"vector": solution, "dimension": self.dimension}

    def domain_metrics(self, solution: list[int]) -> dict[str, Any]:
        return {"ones_count": sum(solution)}
