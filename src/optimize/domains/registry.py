"""Domain problem registry."""

from __future__ import annotations

from typing import Any

from optimize.domains.base_problem import OptimizationProblem
from optimize.domains.feature_selection.problem import FeatureSelectionProblem
from optimize.domains.mock_problem import MockSphereProblem
from optimize.domains.scheduling.jsp.problem import JSPProblem
from optimize.domains.tsp.problem import TSPProblem
from optimize.experiments.budget import EvaluationBudget

_REGISTRY: dict[str, type[OptimizationProblem]] = {
    MockSphereProblem.domain_name: MockSphereProblem,
    FeatureSelectionProblem.domain_name: FeatureSelectionProblem,
    JSPProblem.domain_name: JSPProblem,
    TSPProblem.domain_name: TSPProblem,
}


def register_problem(cls: type[OptimizationProblem]) -> type[OptimizationProblem]:
    _REGISTRY[cls.domain_name] = cls
    return cls


def create_problem(
    domain: str,
    budget: EvaluationBudget,
    domain_config: dict | None = None,
) -> OptimizationProblem:
    if domain not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"unknown domain '{domain}'. Available: {available}")

    config: dict[str, Any] = dict(domain_config or {})

    if domain == MockSphereProblem.domain_name:
        dimension = int(config.get("dimension", 5))
        return MockSphereProblem(budget=budget, dimension=dimension)

    if domain == TSPProblem.domain_name:
        return TSPProblem.from_config(budget, config)

    if domain == JSPProblem.domain_name:
        return JSPProblem.from_config(budget, config)

    if domain == FeatureSelectionProblem.domain_name:
        return FeatureSelectionProblem.from_config(budget, config)

    cls = _REGISTRY[domain]
    return cls(budget=budget)


def list_domains() -> list[str]:
    return sorted(_REGISTRY)
