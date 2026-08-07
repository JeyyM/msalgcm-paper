"""Discrete particle swarm optimization using random-key encoding."""

from __future__ import annotations

from typing import Any

import numpy as np

from optimize.algorithms.base import OptimizationAlgorithm
from optimize.algorithms.pso_encoding import perturb_keys
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
        self._positions = np.zeros((self._swarm_size, self._dimension))
        self._velocities = self.rng.uniform(-1.0, 1.0, (self._swarm_size, self._dimension))
        self._personal_best_positions = self._positions.copy()
        self._personal_best_objectives = np.full(self._swarm_size, float("inf"))

        self._global_best_position = self._positions[0].copy()
        self._global_best_objective = float("inf")
        self._best_solution = None
        self._best_objective = float("inf")

        canonical = problem.create_initial_solution(self.rng)
        canonical_keys = problem.encode_for_pso(canonical)
        canonical_solution = problem.decode_for_pso(canonical_keys.tolist())
        if not problem.is_valid(canonical_solution):
            canonical_keys = None

        if canonical_keys is not None:
            self._positions[0] = canonical_keys
            n_perturbed = max(1, self._swarm_size // 4)
            for index in range(1, min(n_perturbed, self._swarm_size)):
                self._positions[index] = perturb_keys(canonical_keys, self.rng)
            for index in range(n_perturbed, self._swarm_size):
                self._positions[index] = self.rng.random(self._dimension)
        else:
            self._positions = self.rng.random((self._swarm_size, self._dimension))

        self._personal_best_positions = self._positions.copy()

        for index in range(self._swarm_size):
            if self.problem.budget.exhausted():
                break
            decoded = problem.decode_for_pso(self._positions[index].tolist())
            objective = problem.evaluate(decoded)
            self._personal_best_objectives[index] = objective
            if objective < self._global_best_objective:
                self._global_best_objective = objective
                self._global_best_position = self._positions[index].copy()
                self._best_solution = decoded
                self._best_objective = objective

        if self._best_solution is None:
            fallback = problem.create_initial_solution(self.rng)
            fallback_objective = problem.evaluate(fallback)
            self._best_solution = fallback
            self._best_objective = fallback_objective
            self._global_best_objective = fallback_objective

        self._current_solution = self._best_solution
        self._current_objective = self._best_objective
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

            decoded = self.problem.decode_for_pso(self._positions[index].tolist())
            objective = self.problem.evaluate(decoded)

            if objective < self._personal_best_objectives[index]:
                self._personal_best_objectives[index] = objective
                self._personal_best_positions[index] = self._positions[index].copy()

            if objective < self._global_best_objective:
                self._global_best_objective = objective
                self._global_best_position = self._positions[index].copy()
                self._consider_solution(decoded, objective)

        self._current_solution = self._best_solution
        self._current_objective = self._best_objective
        self._iterations += 1
        self._record_history()
        return True
