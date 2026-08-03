"""Mock random-search algorithm for framework smoke tests."""

from __future__ import annotations

from typing import Any

import numpy as np

from optimize.algorithms.base import OptimizationAlgorithm
from optimize.domains.base_problem import OptimizationProblem
from optimize.types import StopReason


class MockRandomSearch(OptimizationAlgorithm):
    """Flip-one-bit random search on the mock sphere problem."""

    name = "mock_random_search"

    def initialize(
        self,
        problem: OptimizationProblem,
        config: dict[str, Any],
        seed: int,
    ) -> None:
        self.problem = problem
        self.config = config
        self.rng = np.random.default_rng(seed)
        self._history = []
        self._iterations = 0
        self._stop_reason = StopReason.COMPLETED

        initial = problem.create_initial_solution(self.rng)
        objective = problem.evaluate(initial)
        self._best_solution = initial
        self._best_objective = objective
        self._current_solution = initial
        self._current_objective = objective
        self._record_history()

    def step(self) -> bool:
        assert self.problem is not None and self.rng is not None

        if self.problem.budget.exhausted():
            self._stop_reason = StopReason.EVALUATION_BUDGET
            return False

        neighbors = self.problem.get_neighbors(
            self._current_solution,
            operator="flip",
            rng=self.rng,
        )
        candidate = neighbors[0]
        objective = self.problem.evaluate(candidate)
        self._consider_solution(candidate, objective)
        self._iterations += 1
        self._record_history()
        return True
