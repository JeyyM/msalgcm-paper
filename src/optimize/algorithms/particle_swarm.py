"""Discrete particle swarm optimization using random-key encoding."""

from __future__ import annotations

from typing import Any

import numpy as np

from optimize.algorithms.base import OptimizationAlgorithm
from optimize.domains.base_problem import OptimizationProblem
from optimize.types import StopReason


class ParticleSwarmOptimization(OptimizationAlgorithm):
    name = "particle_swarm"

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

        self._swarm_size = int(config.get("swarm_size", 30))
        self._inertia = float(config.get("inertia_weight", 0.7))
        self._cognitive = float(config.get("cognitive_coefficient", 1.5))
        self._social = float(config.get("social_coefficient", 1.5))

        self._dimension = self._infer_dimension(problem)
        self._positions = self.rng.random((self._swarm_size, self._dimension))
        self._velocities = self.rng.uniform(-1.0, 1.0, (self._swarm_size, self._dimension))
        self._personal_best_positions = self._positions.copy()
        self._personal_best_objectives = np.full(self._swarm_size, float("inf"))

        self._global_best_position = self._positions[0].copy()
        self._global_best_objective = float("inf")

        for index in range(self._swarm_size):
            if self.problem.budget.exhausted():
                break
            route = problem.decode_for_pso(self._positions[index].tolist())
            objective = problem.evaluate(route)
            self._personal_best_objectives[index] = objective
            if objective < self._global_best_objective:
                self._global_best_objective = objective
                self._global_best_position = self._positions[index].copy()
                self._best_solution = route
                self._best_objective = objective

        initial = self._best_solution
        initial_objective = self._best_objective
        if initial is None:
            initial = problem.create_initial_solution(self.rng)
            initial_objective = problem.evaluate(initial)
            self._best_solution = initial
            self._best_objective = initial_objective

        self._current_solution = initial
        self._current_objective = initial_objective
        self._record_history()

    @staticmethod
    def _infer_dimension(problem: OptimizationProblem) -> int:
        if hasattr(problem, "instance"):
            instance = problem.instance  # type: ignore[attr-defined]
            if hasattr(instance, "num_operations"):
                return int(instance.num_operations)
            if hasattr(instance, "num_features"):
                return int(instance.num_features)
            if hasattr(instance, "num_cities"):
                return int(instance.num_cities)
        if hasattr(problem, "dimension"):
            return int(problem.dimension)  # type: ignore[attr-defined]
        raise ValueError("unable to infer PSO dimension from problem")

    def step(self) -> bool:
        assert self.problem is not None and self.rng is not None

        if self.problem.budget.exhausted():
            self._stop_reason = StopReason.EVALUATION_BUDGET
            return False

        r1 = self.rng.random((self._swarm_size, self._dimension))
        r2 = self.rng.random((self._swarm_size, self._dimension))

        self._velocities = (
            self._inertia * self._velocities
            + self._cognitive * r1 * (self._personal_best_positions - self._positions)
            + self._social * r2 * (self._global_best_position - self._positions)
        )
        self._positions = np.clip(self._positions + self._velocities, 0.0, 1.0)

        for index in range(self._swarm_size):
            if self.problem.budget.exhausted():
                break

            route = self.problem.decode_for_pso(self._positions[index].tolist())
            objective = self.problem.evaluate(route)

            if objective < self._personal_best_objectives[index]:
                self._personal_best_objectives[index] = objective
                self._personal_best_positions[index] = self._positions[index].copy()

            if objective < self._global_best_objective:
                self._global_best_objective = objective
                self._global_best_position = self._positions[index].copy()
                self._consider_solution(route, objective)

        self._current_solution = self._best_solution
        self._current_objective = self._best_objective
        self._iterations += 1
        self._record_history()
        return True
