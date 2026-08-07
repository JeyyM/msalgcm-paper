"""Feature-selection optimization problem."""

from __future__ import annotations

from typing import Any

import numpy as np

from optimize.domains.base_problem import OptimizationProblem
from optimize.domains.feature_selection.evaluator import FeatureSubsetEvaluator
from optimize.domains.feature_selection.loader import FeatureSelectionDataset, load_ew_dataset
from optimize.algorithms.pso_encoding import encode_binary_mask
from optimize.domains.feature_selection.neighborhoods import apply_operator, random_operator
from optimize.experiments.budget import EvaluationBudget


class FeatureSelectionProblem(OptimizationProblem):
    domain_name = "feature_selection"

    def __init__(
        self,
        budget: EvaluationBudget,
        dataset: FeatureSelectionDataset,
        evaluator: FeatureSubsetEvaluator,
        performance_weight: float,
        reduction_weight: float,
        operators: list[str] | None = None,
        initial_solution: str = "random",
        min_selected_features: int = 1,
        standardize_features: bool = True,
    ) -> None:
        super().__init__(budget)
        self.dataset = dataset
        self.evaluator = evaluator
        self.performance_weight = performance_weight
        self.reduction_weight = reduction_weight
        self.operators = operators or ["flip", "swap"]
        self.initial_solution = initial_solution
        self.min_selected_features = min_selected_features
        self.standardize_features = standardize_features

    @classmethod
    def from_config(cls, budget: EvaluationBudget, config: dict[str, Any]) -> FeatureSelectionProblem:
        instance_path = config.get("instance_path")
        if not instance_path:
            raise ValueError("feature_selection domain requires instance_path in domain config")

        if "performance_weight" not in config or "reduction_weight" not in config:
            raise ValueError(
                "feature_selection requires explicit performance_weight and reduction_weight "
                "in domain_config (no silent defaults)",
            )

        performance_weight = float(config["performance_weight"])
        reduction_weight = float(config["reduction_weight"])
        if performance_weight < 0 or reduction_weight < 0:
            raise ValueError("objective weights must be non-negative")
        if performance_weight + reduction_weight <= 0:
            raise ValueError("performance_weight + reduction_weight must be positive")

        dataset = load_ew_dataset(instance_path)
        evaluator = FeatureSubsetEvaluator.from_dataset(
            dataset,
            test_size=float(config.get("test_size", 0.3)),
            split_seed=int(config.get("split_seed", 0)),
            k_neighbors=int(config.get("k_neighbors", 5)),
            cv_folds=int(config.get("cv_folds", 5)),
            metric=config.get("metric"),
            standardize_features=bool(config.get("standardize_features", True)),
        )
        operators = config.get("operators")
        initial_solution = config.get("initial_solution", "random")
        min_selected_features = int(config.get("min_selected_features", 1))
        standardize_features = bool(config.get("standardize_features", True))
        return cls(
            budget=budget,
            dataset=dataset,
            evaluator=evaluator,
            performance_weight=performance_weight,
            reduction_weight=reduction_weight,
            operators=operators,
            initial_solution=initial_solution,
            min_selected_features=min_selected_features,
            standardize_features=standardize_features,
        )

    @property
    def dimension(self) -> int:
        """Number of binary decision variables (features) — used by PSO to size the swarm."""
        return self.dataset.num_features

    def create_initial_solution(self, rng: np.random.Generator) -> list[int]:
        n = self.dataset.num_features
        if self.initial_solution == "all_features":
            return [1] * n

        if self.initial_solution == "half":
            mask = [1 if rng.random() < 0.5 else 0 for _ in range(n)]
        else:
            mask = [1 if rng.random() < 0.3 else 0 for _ in range(n)]

        return self.repair(mask, rng)

    def repair(self, solution: list[int], rng: np.random.Generator | None = None) -> list[int]:
        repaired = [1 if value else 0 for value in solution]
        selected = sum(repaired)
        if selected >= self.min_selected_features:
            return repaired

        generator = rng or np.random.default_rng()
        indices = list(range(len(repaired)))
        generator.shuffle(indices)
        for index in indices:
            if selected >= self.min_selected_features:
                break
            if repaired[index] == 0:
                repaired[index] = 1
                selected += 1
        if selected == 0 and repaired:
            repaired[int(generator.integers(0, len(repaired)))] = 1
        return repaired

    def _objective_value(self, solution: list[int]) -> float:
        repaired = self.repair(solution)
        cv_loss = self.evaluator.cross_validation_loss(repaired)
        reduction = self.evaluator.selected_feature_ratio(repaired)
        return (self.performance_weight * cv_loss) + (self.reduction_weight * reduction)

    def evaluate(self, solution: list[int]) -> float:
        if self.budget.exhausted():
            return self._objective_value(solution)
        objective = self._objective_value(solution)
        return float(self._evaluate_with_budget(solution, objective))

    def is_valid(self, solution: list[int]) -> bool:
        if len(solution) != self.dataset.num_features:
            return False
        if any(value not in {0, 1} for value in solution):
            return False
        return sum(solution) >= self.min_selected_features

    def get_neighbors(
        self,
        solution: list[int],
        operator: str,
        rng: np.random.Generator,
    ) -> list[list[int]]:
        if operator == "random":
            operator = random_operator(self.operators, rng)
        neighbor = apply_operator(solution, operator, rng)
        return [self.repair(neighbor, rng)]

    def decode_for_pso(self, position: list[float]) -> list[int]:
        mask = [1 if value >= 0.5 else 0 for value in position]
        return self.repair(mask)

    def encode_for_pso(self, solution: list[int]) -> np.ndarray:
        return encode_binary_mask(self.repair(solution))

    def serialize_solution(self, solution: list[int]) -> dict[str, Any]:
        mask = self.repair(solution)
        selected_indices = [index for index, selected in enumerate(mask) if selected]
        selected_names = [self.dataset.feature_names[index] for index in selected_indices]
        cv_loss = self.evaluator.cross_validation_loss(mask)
        cv_score = 1.0 - cv_loss
        test_score = self.evaluator.test_performance(mask)
        selected_count = len(selected_indices)
        total_features = self.dataset.num_features
        return {
            "instance": self.dataset.name,
            "feature_mask": mask,
            "selected_feature_indices": selected_indices,
            "selected_feature_names": selected_names,
            "selected_feature_count": selected_count,
            "selected_feature_ratio": selected_count / total_features,
            "performance_weight": self.performance_weight,
            "reduction_weight": self.reduction_weight,
            "metric": self.evaluator.metric,
            "cv_score": cv_score,
            "cv_loss": cv_loss,
            "test_score": test_score,
            "objective_value": (
                self.performance_weight * cv_loss
                + self.reduction_weight * (selected_count / total_features)
            ),
        }

    def domain_metrics(self, solution: list[int]) -> dict[str, Any]:
        mask = self.repair(solution)
        cv_loss = self.evaluator.cross_validation_loss(mask)
        return {
            "cv_score": 1.0 - cv_loss,
            "test_score": self.evaluator.test_performance(mask),
            "selected_feature_count": sum(mask),
            "selected_feature_ratio": sum(mask) / len(mask),
        }
