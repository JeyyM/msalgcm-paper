"""Base problem interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from optimize.experiments.budget import EvaluationBudget


class OptimizationProblem(ABC):
    """Domain problem contract — algorithms interact only through this interface."""

    domain_name: str = "unknown"

    def __init__(self, budget: EvaluationBudget) -> None:
        self.budget = budget

    @abstractmethod
    def create_initial_solution(self, rng: np.random.Generator) -> Any:
        """Return a valid starting solution."""

    @abstractmethod
    def evaluate(self, solution: Any) -> float:
        """Return objective value and increment the shared evaluation budget."""

    @abstractmethod
    def is_valid(self, solution: Any) -> bool:
        """Check domain constraints."""

    def repair(self, solution: Any) -> Any:
        """Optional repair — override when approved for a domain."""
        return solution

    def get_neighbors(
        self,
        solution: Any,
        operator: str,
        rng: np.random.Generator,
    ) -> list[Any]:
        """Return neighboring solutions for SA/TS. Override in domain implementations."""
        raise NotImplementedError(f"get_neighbors not implemented for {self.domain_name}")

    def decode_for_pso(self, position: Any) -> Any:
        """Decode a PSO position into a valid domain solution."""
        raise NotImplementedError(f"decode_for_pso not implemented for {self.domain_name}")

    @abstractmethod
    def serialize_solution(self, solution: Any) -> dict[str, Any]:
        """JSON-serializable representation of a solution."""

    def domain_metrics(self, solution: Any) -> dict[str, Any]:
        """Optional domain-specific metrics (gap, makespan detail, etc.)."""
        return {}

    def _evaluate_with_budget(self, solution: Any, raw_evaluate: float) -> float:
        """Helper: increment budget once per objective call."""
        if self.budget.exhausted():
            return raw_evaluate
        self.budget.increment()
        return raw_evaluate
