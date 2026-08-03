"""Simulated annealing for discrete optimization problems."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from optimize.algorithms.base import OptimizationAlgorithm
from optimize.domains.base_problem import OptimizationProblem
from optimize.domains.operators import random_operator
from optimize.types import StopReason


class SimulatedAnnealing(OptimizationAlgorithm):
    name = "simulated_annealing"

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

        self._temperature = float(config.get("initial_temperature", 1000.0))
        self._final_temperature = float(config.get("final_temperature", 0.01))
        self._cooling_factor = float(config.get("cooling_factor", 0.995))
        self._moves_per_temperature = int(config.get("moves_per_temperature", 100))
        self._operators = config.get("operators", ["swap", "insertion", "inversion", "two_opt"])
        self._moves_at_temperature = 0

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

        if self._temperature <= self._final_temperature:
            self._stop_reason = StopReason.COMPLETED
            return False

        operator = random_operator(self._operators, self.rng)
        neighbor = self.problem.get_neighbors(self._current_solution, operator, self.rng)[0]
        objective = self.problem.evaluate(neighbor)
        delta = objective - self._current_objective

        accept = delta <= 0
        if not accept and self._temperature > 0:
            probability = math.exp(-delta / self._temperature)
            accept = self.rng.random() < probability

        if accept:
            self._current_solution = neighbor
            self._current_objective = objective
            self._consider_solution(neighbor, objective)

        self._moves_at_temperature += 1
        self._iterations += 1

        if self._moves_at_temperature >= self._moves_per_temperature:
            self._temperature *= self._cooling_factor
            self._moves_at_temperature = 0

        self._record_history()
        return True
