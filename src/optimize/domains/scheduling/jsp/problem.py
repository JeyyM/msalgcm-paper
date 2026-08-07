"""Classic job-shop scheduling optimization problem."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from optimize.domains.base_problem import OptimizationProblem
from optimize.domains.scheduling.jsp.decoder import (
    build_operation_labels,
    compute_makespan,
    decode_schedule,
)
from optimize.domains.scheduling.jsp.loader import JSPInstance, load_jsp
from optimize.algorithms.pso_encoding import encode_labeled_sequence
from optimize.domains.scheduling.jsp.neighborhoods import apply_operator, random_operator
from optimize.experiments.budget import EvaluationBudget


class JSPProblem(OptimizationProblem):
    domain_name = "scheduling"

    def __init__(
        self,
        budget: EvaluationBudget,
        instance: JSPInstance,
        operators: list[str] | None = None,
        known_optimum: int | None = None,
        initial_solution: str = "random",
    ) -> None:
        super().__init__(budget)
        self.instance = instance
        self.operators = operators or ["swap", "insertion", "inversion"]
        self.known_optimum = known_optimum
        self.initial_solution = initial_solution
        self._operation_labels = build_operation_labels(instance.num_jobs, instance.num_machines)

    @classmethod
    def from_config(cls, budget: EvaluationBudget, config: dict[str, Any]) -> JSPProblem:
        instance_path = config.get("instance_path")
        if not instance_path:
            raise ValueError("scheduling domain requires instance_path in domain config")

        instance = load_jsp(instance_path)
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
            value = config["known_optimum"]
            return int(value) if value is not None else None

        metadata_path = config.get("metadata_path", "datasets/scheduling/metadata.json")
        path = Path(metadata_path)
        if not path.exists():
            return None

        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data.get("instances", []):
            if entry.get("name") == instance_name:
                value = entry.get("best_known_makespan")
                return int(value) if value is not None else None
        return None

    def create_initial_solution(self, rng: np.random.Generator) -> list[int]:
        if self.initial_solution == "longest_processing_time":
            job_order = sorted(
                range(self.instance.num_jobs),
                key=lambda job: sum(self.instance.processing_times[job]),
                reverse=True,
            )
            sequence: list[int] = []
            for job in job_order:
                sequence.extend([job] * self.instance.num_machines)
            return sequence

        sequence = self._operation_labels.copy()
        rng.shuffle(sequence)
        return sequence

    def evaluate(self, solution: list[int]) -> float:
        if self.budget.exhausted():
            return float(compute_makespan(self.instance, solution))
        makespan = compute_makespan(self.instance, solution)
        return float(self._evaluate_with_budget(solution, makespan))

    def is_valid(self, solution: list[int]) -> bool:
        if len(solution) != self.instance.num_operations:
            return False
        counts = Counter(solution)
        return all(counts.get(job, 0) == self.instance.num_machines for job in range(self.instance.num_jobs))

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
        order = np.argsort(position)
        return [self._operation_labels[index] for index in order]

    def encode_for_pso(self, solution: list[int]) -> np.ndarray:
        return encode_labeled_sequence(solution, self._operation_labels)

    def serialize_solution(self, solution: list[int]) -> dict[str, Any]:
        schedule = decode_schedule(self.instance, solution)
        payload: dict[str, Any] = {
            "instance": self.instance.name,
            "operation_sequence": solution,
            "makespan": schedule.makespan,
            "operations": [
                {
                    "job": operation.job,
                    "operation_index": operation.operation_index,
                    "machine": operation.machine,
                    "processing_time": operation.processing_time,
                    "start": operation.start,
                    "finish": operation.finish,
                }
                for operation in schedule.operations
            ],
        }
        if self.known_optimum is not None and self.known_optimum > 0:
            gap = ((schedule.makespan - self.known_optimum) / self.known_optimum) * 100.0
            payload["known_optimum"] = self.known_optimum
            payload["gap_percentage"] = gap
        return payload

    def domain_metrics(self, solution: list[int]) -> dict[str, Any]:
        makespan = compute_makespan(self.instance, solution)
        metrics: dict[str, Any] = {"makespan": makespan}
        if self.known_optimum is not None:
            metrics["known_optimum"] = self.known_optimum
            metrics["gap_percentage"] = (
                (makespan - self.known_optimum) / self.known_optimum
            ) * 100.0
        return metrics
