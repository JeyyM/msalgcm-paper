"""Tests for PSO random-key encoding and shared initializer seeding."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from optimize.algorithms.pso_encoding import encode_labeled_sequence, encode_permutation_by_item
from optimize.algorithms.registry import get_algorithm
from optimize.domains.registry import create_problem
from optimize.experiments.budget import EvaluationBudget

ROOT = Path(__file__).resolve().parents[1]
EIL51 = ROOT / "datasets" / "tsp" / "instances" / "eil51.tsp"


def test_tsp_encode_decode_roundtrip() -> None:
    budget = EvaluationBudget(10)
    problem = create_problem(
        "tsp",
        budget,
        {"instance_path": str(EIL51), "initial_solution": "nearest_neighbor"},
    )
    rng = np.random.default_rng(7)
    route = problem.create_initial_solution(rng)
    keys = problem.encode_for_pso(route)
    decoded = problem.decode_for_pso(keys.tolist())
    assert decoded == route


def test_tsp_pso_starts_from_nearest_neighbor_quality() -> None:
    budget = EvaluationBudget(200)
    problem = create_problem(
        "tsp",
        budget,
        {
            "instance_path": str(EIL51),
            "initial_solution": "nearest_neighbor",
            "operators": ["two_opt", "swap"],
        },
    )
    pso = get_algorithm("particle_swarm")
    pso.initialize(
        problem,
        {"swarm_size": 10, "inertia_weight": 0.6, "cognitive_coefficient": 1.5, "social_coefficient": 1.5},
        seed=42,
    )

    optimum = 426
    gap_pct = (pso.get_best_objective() - optimum) / optimum * 100.0
    assert gap_pct < 40.0
