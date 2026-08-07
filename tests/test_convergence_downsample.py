"""Tests for convergence downsampling."""

from __future__ import annotations

from optimize.api.services.results_reader import _downsample_convergence


def test_downsample_keeps_improvement_steps() -> None:
    rows = [
        {"objective_evaluations": str(i), "best_objective": str(max(100, 200 - i // 10))}
        for i in range(1000)
    ]
    sampled = _downsample_convergence(rows, 50)
    bests = [float(row["best_objective"]) for row in sampled]

    assert sampled[0]["objective_evaluations"] == "0"
    assert sampled[-1]["objective_evaluations"] == "999"
    assert min(bests) < max(bests)
    assert len(sampled) <= 50
