"""Aggregate final-comparison results for the results dashboard (TSP + JSP)."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

from optimize.api.services.jsp_catalog import (
    ALGORITHM_LABELS,
    JSP_ALGORITHMS,
    JSP_COMPARISON_INSTANCES,
    JSP_EVALUATION_BUDGET,
    JSP_RUNS,
    _batch_stats,
    _iter_managed_experiments,
)
from optimize.api.services.tsp_catalog import (
    TSP_ALGORITHMS,
    TSP_EVALUATION_BUDGET,
    TSP_RUNS,
    _iter_managed_experiments as _iter_tsp_experiments,
    load_tsp_instances,
)

TSP_COMPARISON_INSTANCES = [
    "eil51",
    "berlin52",
    "st70",
    "kroA100",
    "ch130",
    "rat195",
]

ALGORITHM_LABELS_UNIFIED = ALGORITHM_LABELS


def _pick_best_batch(summaries: list[Any]) -> Any | None:
    """Prefer a finished batch; otherwise the folder with the most completed runs."""
    if not summaries:
        return None
    complete = [item for item in summaries if item.done]
    if complete:
        return max(complete, key=lambda item: item.experiment_id)
    return max(summaries, key=lambda item: (item.completed_runs, item.experiment_id))


def _gap_pct(objective: float, optimum: float | None) -> float | None:
    if optimum is None or optimum == 0:
        return None
    return (objective - optimum) / optimum * 100.0


def _stats_from_runs(
    experiment_dir: Path,
    known_optimum: float | None,
) -> dict[str, float | int | None]:
    runs_path = experiment_dir / "runs.csv"
    if not runs_path.exists():
        return {
            "successful_runs": 0,
            "failed_runs": 0,
            "best_objective": None,
            "mean_objective": None,
            "std_objective": None,
            "best_gap_percentage": None,
            "mean_gap_percentage": None,
            "mean_runtime_seconds": None,
        }

    objectives: list[float] = []
    runtimes: list[float] = []
    successful = 0
    failed = 0
    with runs_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") == "completed":
                successful += 1
                if row.get("best_objective"):
                    objectives.append(float(row["best_objective"]))
                if row.get("runtime_seconds"):
                    runtimes.append(float(row["runtime_seconds"]))
            else:
                failed += 1

    if not objectives:
        return {
            "successful_runs": successful,
            "failed_runs": failed,
            "best_objective": None,
            "mean_objective": None,
            "std_objective": None,
            "best_gap_percentage": None,
            "mean_gap_percentage": None,
            "mean_runtime_seconds": statistics.mean(runtimes) if runtimes else None,
        }

    best = min(objectives)
    mean = statistics.mean(objectives)
    gaps = [_gap_pct(value, known_optimum) for value in objectives]
    gaps_finite = [g for g in gaps if g is not None]

    return {
        "successful_runs": successful,
        "failed_runs": failed,
        "best_objective": best,
        "mean_objective": mean,
        "std_objective": statistics.pstdev(objectives) if len(objectives) > 1 else 0.0,
        "best_gap_percentage": _gap_pct(best, known_optimum),
        "mean_gap_percentage": statistics.mean(gaps_finite) if gaps_finite else None,
        "mean_runtime_seconds": statistics.mean(runtimes) if runtimes else None,
    }


def _algorithm_result(
    batch: Any | None,
    results_dir: Path,
    target_runs: int,
    known_optimum: float | None,
) -> dict[str, Any]:
    if batch is None:
        return {
            "experiment_id": None,
            "completed_runs": 0,
            "target_runs": target_runs,
            "done": False,
            "best_objective": None,
            "mean_objective": None,
            "std_objective": None,
            "best_gap_percentage": None,
            "mean_gap_percentage": None,
            "mean_runtime_seconds": None,
        }

    experiment_dir = results_dir / batch.experiment_id
    summary_stats = _batch_stats(experiment_dir)
    run_stats = _stats_from_runs(experiment_dir, known_optimum)

    # Prefer summary gaps when the batch is complete; fill gaps from runs otherwise.
    best_gap = summary_stats.get("best_gap_percentage")
    if best_gap is None:
        best_gap = run_stats["best_gap_percentage"]

    mean_gap = run_stats["mean_gap_percentage"]
    if batch.done and summary_stats.get("mean_objective") is not None:
        summary_path = experiment_dir / "summary.csv"
        if summary_path.exists():
            with summary_path.open(encoding="utf-8") as handle:
                row = next(csv.DictReader(handle), None)
            if row and row.get("mean_gap_percentage"):
                mean_gap = float(row["mean_gap_percentage"])

    return {
        "experiment_id": batch.experiment_id,
        "completed_runs": batch.completed_runs,
        "target_runs": target_runs,
        "done": batch.done,
        "best_objective": run_stats["best_objective"] or summary_stats.get("best_objective"),
        "mean_objective": run_stats["mean_objective"] or summary_stats.get("mean_objective"),
        "std_objective": run_stats["std_objective"],
        "best_gap_percentage": best_gap,
        "mean_gap_percentage": mean_gap,
        "mean_runtime_seconds": run_stats["mean_runtime_seconds"],
    }


def _instance_metadata(instances: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for item in instances:
        if item["name"] == name:
            return item
    return {"name": name}


def _build_domain_block(
    *,
    domain_id: str,
    label: str,
    objective: str,
    evaluation_budget: int,
    target_runs: int,
    instance_names: list[str],
    metadata_instances: list[dict[str, Any]],
    algorithms: list[str],
    iter_experiments,
    results_dir: Path,
    optimum_key: str,
    optimum_label: str,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for instance_name in instance_names:
        meta = _instance_metadata(metadata_instances, instance_name)
        known_optimum = meta.get(optimum_key) or meta.get("known_optimum")
        problem_size = meta.get("jobs") or meta.get("num_cities") or meta.get("machines")
        if meta.get("jobs") and meta.get("machines"):
            problem_size_label = f"{meta['jobs']}×{meta['machines']}"
        elif meta.get("num_cities"):
            problem_size_label = f"{meta['num_cities']} cities"
        else:
            problem_size_label = str(problem_size) if problem_size else "—"

        algorithm_results: dict[str, Any] = {}
        for algorithm in algorithms:
            batch = _pick_best_batch(iter_experiments(results_dir, instance_name, algorithm))
            algorithm_results[algorithm] = _algorithm_result(
                batch,
                results_dir,
                target_runs,
                float(known_optimum) if known_optimum is not None else None,
            )

        rows.append(
            {
                "instance": instance_name,
                "problem_size": problem_size,
                "problem_size_label": problem_size_label,
                "known_optimum": known_optimum,
                "optimum_label": optimum_label,
                "results": algorithm_results,
            }
        )

    return {
        "id": domain_id,
        "label": label,
        "objective": objective,
        "evaluation_budget": evaluation_budget,
        "target_runs": target_runs,
        "instances": rows,
        "algorithms": [
            {"id": algorithm, "label": ALGORITHM_LABELS_UNIFIED[algorithm]}
            for algorithm in algorithms
        ],
    }


def comparison_dashboard(results_dir: Path | None = None) -> dict[str, Any]:
    from optimize.api.services.jsp_catalog import _load_jsp_all_instances
    from optimize.api.services.results_reader import results_root

    root = results_dir or results_root()
    tsp_meta = load_tsp_instances()
    jsp_meta = _load_jsp_all_instances()

    domains = [
        _build_domain_block(
            domain_id="tsp",
            label="Travelling Salesman Problem",
            objective="minimize tour length",
            evaluation_budget=TSP_EVALUATION_BUDGET,
            target_runs=TSP_RUNS,
            instance_names=TSP_COMPARISON_INSTANCES,
            metadata_instances=tsp_meta,
            algorithms=TSP_ALGORITHMS,
            iter_experiments=_iter_tsp_experiments,
            results_dir=root,
            optimum_key="known_optimum",
            optimum_label="Known optimum",
        ),
        _build_domain_block(
            domain_id="jsp",
            label="Job Shop Scheduling",
            objective="minimize makespan",
            evaluation_budget=JSP_EVALUATION_BUDGET,
            target_runs=JSP_RUNS,
            instance_names=JSP_COMPARISON_INSTANCES,
            metadata_instances=jsp_meta,
            algorithms=JSP_ALGORITHMS,
            iter_experiments=_iter_managed_experiments,
            results_dir=root,
            optimum_key="best_known_makespan",
            optimum_label="Best known makespan",
        ),
    ]

    return {
        "feature_selection_included": False,
        "feature_selection_note": "Feature Selection omitted — PSO comparison runs still in progress.",
        "algorithms": [
            {"id": algorithm, "label": ALGORITHM_LABELS_UNIFIED[algorithm]}
            for algorithm in TSP_ALGORITHMS
        ],
        "domains": domains,
    }
