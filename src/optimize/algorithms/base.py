"""Base algorithm interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from optimize.domains.base_problem import OptimizationProblem
from optimize.experiments.models import HistoryRecord
from optimize.types import StopReason


class OptimizationAlgorithm(ABC):
    """Metaheuristic algorithm contract."""

    name: str = "unknown"

    def __init__(self) -> None:
        self.problem: OptimizationProblem | None = None
        self.config: dict[str, Any] = {}
        self.rng = None
        self._best_solution: Any = None
        self._best_objective: float = float("inf")
        self._current_solution: Any = None
        self._current_objective: float = float("inf")
        self._history: list[HistoryRecord] = []
        self._history_listener: Callable[[HistoryRecord], None] | None = None
        self._solution_listener: Callable[[Any, float], None] | None = None
        self._iterations = 0
        self._stop_reason = StopReason.COMPLETED

    @abstractmethod
    def initialize(
        self,
        problem: OptimizationProblem,
        config: dict[str, Any],
        seed: int,
    ) -> None:
        """Reset algorithm state for a new run."""

    @abstractmethod
    def step(self) -> bool:
        """Perform one iteration. Return False when the run should stop."""

    def run(self) -> None:
        if self.problem is None:
            raise RuntimeError("algorithm must be initialized before run()")
        while not self.problem.budget.exhausted():
            if not self.step():
                break
        if self.problem.budget.exhausted():
            self._stop_reason = StopReason.EVALUATION_BUDGET

    def get_best_solution(self) -> Any:
        return self._best_solution

    def get_current_solution(self) -> Any:
        return self._current_solution

    def get_best_objective(self) -> float:
        return self._best_objective

    def get_history(self) -> list[HistoryRecord]:
        return list(self._history)

    def get_stop_reason(self) -> StopReason:
        return self._stop_reason

    def set_history_listener(self, listener: Callable[[HistoryRecord], None] | None) -> None:
        self._history_listener = listener

    def set_solution_listener(self, listener: Callable[[Any, float], None] | None) -> None:
        self._solution_listener = listener

    def _record_history(self) -> None:
        if self.problem is None:
            return
        record = HistoryRecord(
            objective_evaluations=self.problem.budget.count,
            best_objective=self._best_objective,
            current_objective=self._current_objective,
            iteration=self._iterations,
        )
        self._history.append(record)
        if self._history_listener is not None:
            self._history_listener(record)

    def _consider_solution(self, solution: Any, objective: float) -> None:
        self._current_solution = solution
        self._current_objective = objective
        if objective < self._best_objective:
            self._best_objective = objective
            self._best_solution = solution
            if self._solution_listener is not None:
                self._solution_listener(solution, objective)
