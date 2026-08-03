"""Tabu search for discrete optimization problems."""

from __future__ import annotations

from collections import deque
from typing import Any

import numpy as np

from optimize.algorithms.base import OptimizationAlgorithm
from optimize.domains.base_problem import OptimizationProblem
from optimize.domains.operators import random_operator
from optimize.types import StopReason


class TabuSearch(OptimizationAlgorithm):
    name = "tabu_search"

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

        self._tabu_tenure = int(config.get("tabu_tenure", 15))
        self._candidate_list_size = int(config.get("candidate_list_size", 20))
        self._operators = config.get("operators", ["swap", "insertion", "inversion", "two_opt"])
        self._tabu_queue: deque[tuple[int, int]] = deque(maxlen=self._tabu_tenure)
        self._tabu_set: set[tuple[int, int]] = set()

        initial = problem.create_initial_solution(self.rng)
        objective = problem.evaluate(initial)
        self._best_solution = initial
        self._best_objective = objective
        self._current_solution = initial
        self._current_objective = objective
        self._record_history()

    def _move_signature(self, current: list[int], candidate: list[int]) -> tuple[int, int]:
        changed = [index for index, (a, b) in enumerate(zip(current, candidate)) if a != b]
        if len(changed) >= 2:
            return tuple(sorted((changed[0], changed[1])))
        if changed:
            return (changed[0], changed[0])
        return (-1, -1)

    def _add_tabu(self, move: tuple[int, int]) -> None:
        if move == (-1, -1):
            return
        if len(self._tabu_queue) == self._tabu_queue.maxlen:
            old = self._tabu_queue.popleft()
            self._tabu_set.discard(old)
        self._tabu_queue.append(move)
        self._tabu_set.add(move)

    def step(self) -> bool:
        assert self.problem is not None and self.rng is not None

        if self.problem.budget.exhausted():
            self._stop_reason = StopReason.EVALUATION_BUDGET
            return False

        best_candidate = None
        best_objective = float("inf")
        best_move = (-1, -1)

        for _ in range(self._candidate_list_size):
            if self.problem.budget.exhausted():
                break

            operator = random_operator(self._operators, self.rng)
            candidate = self.problem.get_neighbors(self._current_solution, operator, self.rng)[0]
            objective = self.problem.evaluate(candidate)
            move = self._move_signature(self._current_solution, candidate)

            is_tabu = move in self._tabu_set
            aspiration = objective < self._best_objective
            if is_tabu and not aspiration:
                continue

            if objective < best_objective:
                best_objective = objective
                best_candidate = candidate
                best_move = move

        if best_candidate is None:
            self._iterations += 1
            self._record_history()
            return True

        self._current_solution = best_candidate
        self._current_objective = best_objective
        self._consider_solution(best_candidate, best_objective)
        self._add_tabu(best_move)
        self._iterations += 1
        self._record_history()
        return True
