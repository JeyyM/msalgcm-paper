"""Integration tests for mock problem + algorithm."""

from optimize.experiments.runner import ExperimentRunner


def test_mock_single_run_respects_budget():
    runner = ExperimentRunner()
    result = runner.run_single(
        algorithm_name="mock_random_search",
        problem_domain="mock",
        instance="sphere_5d",
        seed=42,
        evaluation_budget=50,
        domain_config={"dimension": 5},
    )

    assert result.status.value == "completed"
    assert result.objective_evaluations <= 50
    assert result.best_objective >= 0
    assert len(result.history) > 0


def test_same_seed_produces_same_result():
    runner = ExperimentRunner()
    kwargs = dict(
        algorithm_name="mock_random_search",
        problem_domain="mock",
        instance="sphere_5d",
        seed=123,
        evaluation_budget=100,
        domain_config={"dimension": 5},
    )
    first = runner.run_single(**kwargs)
    second = runner.run_single(**kwargs)
    assert first.best_objective == second.best_objective
    assert first.best_solution == second.best_solution
