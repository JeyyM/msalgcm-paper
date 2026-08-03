"""Aggregate run results into summary and statistics tables."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from typing import Any

from optimize.experiments.models import ExperimentConfig, RunResult
from optimize.types import RunStatus


def _parameters_key(parameters: dict[str, Any]) -> str:
    return json.dumps(parameters, sort_keys=True)


def _gap_values(results: list[RunResult]) -> list[float]:
    gaps: list[float] = []
    for result in results:
        if isinstance(result.best_solution, dict):
            gap = result.best_solution.get("gap_percentage")
            if gap is not None:
                gaps.append(float(gap))
    return gaps


def build_seed_rows(
    config: ExperimentConfig,
    seeds: list[int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for algorithm_name in config.algorithms:
        for run_index, seed in enumerate(seeds, start=1):
            rows.append(
                {
                    "run_id": f"{algorithm_name}_run_{run_index:03d}",
                    "algorithm": algorithm_name,
                    "seed": seed,
                    "run_index": run_index,
                }
            )
    return rows


def _problem_size(config: ExperimentConfig) -> int | None:
    if config.domain == "tsp" and config.instance_path:
        from optimize.domains.tsp.loader import load_tsplib

        instance = load_tsplib(config.instance_path)
        return instance.num_cities
    if config.domain == "scheduling" and config.instance_path:
        from optimize.domains.scheduling.jsp.loader import load_jsp

        instance = load_jsp(config.instance_path)
        return instance.num_operations
    if config.domain == "feature_selection" and config.instance_path:
        from optimize.domains.feature_selection.loader import load_ew_dataset

        dataset = load_ew_dataset(config.instance_path)
        return dataset.num_features
    return None


def build_summary_rows(
    results: list[RunResult],
    config: ExperimentConfig,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[RunResult]] = defaultdict(list)
    for result in results:
        key = (result.algorithm, _parameters_key(result.parameters))
        grouped[key].append(result)

    problem_size = _problem_size(config)
    rows: list[dict[str, Any]] = []

    for (algorithm, parameters_json), group in sorted(grouped.items()):
        objectives = [result.best_objective for result in group]
        runtimes = [result.runtime_seconds for result in group]
        evaluations = [result.objective_evaluations for result in group]
        successful = [result for result in group if result.status == RunStatus.COMPLETED]
        gaps = _gap_values(successful)

        rows.append(
            {
                "domain": config.domain,
                "instance": config.instance,
                "problem_size": problem_size,
                "algorithm": algorithm,
                "parameters": parameters_json,
                "runs": len(group),
                "successful_runs": len(successful),
                "failed_runs": len(group) - len(successful),
                "success_rate": len(successful) / len(group) if group else 0.0,
                "mean_objective": statistics.mean(objectives) if objectives else None,
                "std_objective": statistics.pstdev(objectives) if len(objectives) > 1 else 0.0,
                "median_objective": statistics.median(objectives) if objectives else None,
                "min_objective": min(objectives) if objectives else None,
                "max_objective": max(objectives) if objectives else None,
                "mean_runtime_seconds": statistics.mean(runtimes) if runtimes else None,
                "mean_objective_evaluations": statistics.mean(evaluations) if evaluations else None,
                "mean_gap_percentage": statistics.mean(gaps) if gaps else None,
                "best_gap_percentage": min(gaps) if gaps else None,
            }
        )

    return rows


def build_statistics_rows(
    results: list[RunResult],
    config: ExperimentConfig,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[RunResult]] = defaultdict(list)
    for result in results:
        grouped[result.algorithm].append(result)

    rows: list[dict[str, Any]] = []
    for algorithm, group in sorted(grouped.items()):
        objectives = sorted(result.best_objective for result in group)
        gaps = sorted(_gap_values(group))
        n = len(objectives)
        if n == 0:
            continue

        def percentile(values: list[float], pct: float) -> float:
            index = max(0, min(n - 1, int(round((pct / 100.0) * (n - 1)))))
            return values[index]

        rows.append(
            {
                "experiment_name": config.experiment_name,
                "domain": config.domain,
                "instance": config.instance,
                "algorithm": algorithm,
                "n": n,
                "mean": statistics.mean(objectives),
                "std": statistics.pstdev(objectives) if n > 1 else 0.0,
                "median": statistics.median(objectives),
                "min": objectives[0],
                "max": objectives[-1],
                "q25": percentile(objectives, 25),
                "q75": percentile(objectives, 75),
                "mean_gap_percentage": statistics.mean(gaps) if gaps else None,
                "best_gap_percentage": min(gaps) if gaps else None,
            }
        )

    return rows
