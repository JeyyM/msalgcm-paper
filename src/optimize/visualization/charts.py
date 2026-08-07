"""Generate experiment charts."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from optimize.experiments.models import ExperimentConfig, RunResult

ALGORITHM_LABELS = {
    "simulated_annealing": "Simulated Annealing",
    "tabu_search": "Tabu Search",
    "particle_swarm": "Particle Swarm",
    "mock_random_search": "Mock Random Search",
}


def _require_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "matplotlib is required for chart generation. Install with: pip install '.[viz]'"
        ) from exc
    return plt


def _algorithm_label(name: str) -> str:
    return ALGORITHM_LABELS.get(name, name.replace("_", " ").title())


def _downsample(
    x_values: list[float],
    y_values: list[float],
    max_points: int = 300,
) -> tuple[list[float], list[float]]:
    """Keep endpoints and best-improvement steps, then uniform fill."""
    if len(x_values) <= max_points:
        return x_values, y_values

    keep: set[int] = {0, len(x_values) - 1}
    best = float("inf")
    for index, value in enumerate(y_values):
        if value < best - 1e-9:
            best = value
            keep.add(index)

    remaining = max_points - len(keep)
    if remaining > 0:
        step = max(1, len(x_values) // remaining)
        for index in range(0, len(x_values), step):
            keep.add(index)

    ordered = sorted(keep)
    if len(ordered) > max_points:
        step = max(1, len(ordered) // max_points)
        ordered = sorted({ordered[index] for index in range(0, len(ordered), step)} | {0, len(x_values) - 1})

    ordered = ordered[: max_points - 1] + [len(x_values) - 1]
    return [x_values[index] for index in ordered], [y_values[index] for index in ordered]


def _y_limits(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    ymin = min(values)
    ymax = max(values)
    span = ymax - ymin
    pad = span * 0.08 if span > 1e-9 else max(abs(ymin) * 0.05, 1.0)
    return ymin - pad, ymax + pad


def _load_convergence_from_csv(path: Path) -> tuple[list[int], list[float]]:
    evaluations: list[int] = []
    bests: list[float] = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            evaluations.append(int(row["objective_evaluations"]))
            bests.append(float(row["best_objective"]))
    return evaluations, bests


def _mean_convergence_curve(
    run_histories: list[tuple[list[int], list[float]]],
    budget: int,
    n_bins: int = 200,
) -> tuple[list[int], list[float]]:
    if not run_histories:
        return [], []

    bin_edges = [int(budget * index / n_bins) for index in range(n_bins + 1)]
    bin_means: list[float] = []

    for edge in bin_edges:
        values_at_edge: list[float] = []
        for evaluations, bests in run_histories:
            best_so_far = bests[0]
            for evaluation, best in zip(evaluations, bests, strict=True):
                if evaluation <= edge:
                    best_so_far = best
                else:
                    break
            values_at_edge.append(best_so_far)
        bin_means.append(sum(values_at_edge) / len(values_at_edge))

    return bin_edges, bin_means


def _group_results(results: list[RunResult]) -> dict[str, list[RunResult]]:
    grouped: dict[str, list[RunResult]] = defaultdict(list)
    for result in results:
        grouped[result.algorithm].append(result)
    return grouped


def plot_convergence(
    experiment_dir: Path,
    results: list[RunResult],
    config: ExperimentConfig,
    output_path: Path,
) -> None:
    plt = _require_matplotlib()
    grouped = _group_results(results)
    convergence_dir = experiment_dir / "convergence"

    figure, axis = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10.colors
    y_values_for_axis: list[float] = []

    for index, (algorithm, runs) in enumerate(sorted(grouped.items())):
        histories: list[tuple[list[int], list[float]]] = []
        for run in runs:
            if run.history:
                evaluations = [record.objective_evaluations for record in run.history]
                bests = [record.best_objective for record in run.history]
            else:
                csv_path = convergence_dir / f"{run.run_id}.csv"
                if csv_path.exists():
                    evaluations, bests = _load_convergence_from_csv(csv_path)
                else:
                    continue
            histories.append((evaluations, bests))
            y_values_for_axis.extend([bests[0], bests[-1]])

        if not histories:
            continue

        x_values, y_values = _mean_convergence_curve(histories, config.evaluation_budget)
        y_values_for_axis.extend(y_values)
        axis.plot(
            x_values,
            y_values,
            label=_algorithm_label(algorithm),
            color=colors[index % len(colors)],
            linewidth=2,
            drawstyle="steps-post",
        )

    axis.set_xlabel("Objective Evaluations")
    axis.set_ylabel("Best Objective")
    axis.set_title(f"Convergence — {config.instance} ({config.domain})")
    if y_values_for_axis:
        axis.set_ylim(_y_limits(y_values_for_axis))
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_convergence_by_algorithm(
    experiment_dir: Path,
    results: list[RunResult],
    config: ExperimentConfig,
    output_path: Path,
) -> None:
    plt = _require_matplotlib()
    grouped = _group_results(results)
    convergence_dir = experiment_dir / "convergence"
    algorithms = sorted(grouped)
    figure, axes = plt.subplots(
        len(algorithms),
        1,
        figsize=(10, 3.5 * len(algorithms)),
        sharex=True,
        squeeze=False,
    )

    for row_index, algorithm in enumerate(algorithms):
        axis = axes[row_index, 0]
        y_values_for_axis: list[float] = []
        for run in grouped[algorithm]:
            if run.history:
                evaluations = [record.objective_evaluations for record in run.history]
                bests = [record.best_objective for record in run.history]
            else:
                csv_path = convergence_dir / f"{run.run_id}.csv"
                if not csv_path.exists():
                    continue
                evaluations, bests = _load_convergence_from_csv(csv_path)

            y_values_for_axis.extend([bests[0], bests[-1]])
            x_values, y_values = _downsample(
                [float(value) for value in evaluations],
                bests,
            )
            axis.plot(
                x_values,
                y_values,
                alpha=0.35,
                linewidth=1,
                drawstyle="steps-post",
            )

        axis.set_ylabel("Best Objective")
        axis.set_title(_algorithm_label(algorithm))
        axis.grid(True, alpha=0.3)
        if y_values_for_axis:
            axis.set_ylim(_y_limits(y_values_for_axis))

    axes[-1, 0].set_xlabel("Objective Evaluations")
    figure.suptitle(f"Convergence by Run — {config.instance}", y=1.01)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_objective_boxplot(
    results: list[RunResult],
    config: ExperimentConfig,
    output_path: Path,
) -> None:
    plt = _require_matplotlib()
    grouped = _group_results(results)
    labels: list[str] = []
    data: list[list[float]] = []

    for algorithm in sorted(grouped):
        objectives = [run.best_objective for run in grouped[algorithm]]
        if objectives:
            labels.append(_algorithm_label(algorithm))
            data.append(objectives)

    if not data:
        return

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.boxplot(data, tick_labels=labels)
    axis.set_ylabel("Best Objective")
    axis.set_title(f"Best Objective Distribution — {config.instance}")
    axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_runtime_comparison(
    results: list[RunResult],
    config: ExperimentConfig,
    output_path: Path,
) -> None:
    plt = _require_matplotlib()
    grouped = _group_results(results)
    labels: list[str] = []
    means: list[float] = []
    stds: list[float] = []

    for algorithm in sorted(grouped):
        runtimes = [run.runtime_seconds for run in grouped[algorithm]]
        if not runtimes:
            continue
        labels.append(_algorithm_label(algorithm))
        mean_value = sum(runtimes) / len(runtimes)
        means.append(mean_value)
        if len(runtimes) > 1:
            variance = sum((value - mean_value) ** 2 for value in runtimes) / len(runtimes)
            stds.append(variance**0.5)
        else:
            stds.append(0.0)

    if not labels:
        return

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(labels, means, yerr=stds, capsize=4, color=plt.cm.tab10.colors[: len(labels)])
    axis.set_ylabel("Runtime (seconds)")
    axis.set_title(f"Mean Runtime — {config.instance}")
    axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_tsp_route(
    route: list[int],
    coordinates: list[tuple[float, float]],
    config: ExperimentConfig,
    algorithm: str,
    distance: float,
    output_path: Path,
    known_optimum: int | None = None,
) -> None:
    plt = _require_matplotlib()
    figure, axis = plt.subplots(figsize=(8, 8))

    xs = [coordinates[city][0] for city in route] + [coordinates[route[0]][0]]
    ys = [coordinates[city][1] for city in route] + [coordinates[route[0]][1]]

    axis.plot(xs, ys, "-", color="#2563eb", linewidth=1, alpha=0.8)
    axis.scatter(
        [coord[0] for coord in coordinates],
        [coord[1] for coord in coordinates],
        c="#dc2626",
        s=20,
        zorder=3,
    )

    title = f"Best TSP Route — {_algorithm_label(algorithm)} ({config.instance})\n"
    title += f"Distance: {distance:.0f}"
    if known_optimum is not None:
        gap = ((distance - known_optimum) / known_optimum) * 100
        title += f"  |  Optimum: {known_optimum}  |  Gap: {gap:.1f}%"
    axis.set_title(title)
    axis.set_xlabel("X")
    axis.set_ylabel("Y")
    axis.set_aspect("equal", adjustable="datalim")
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_jsp_gantt(
    operations: list[dict[str, Any]],
    config: ExperimentConfig,
    algorithm: str,
    makespan: float,
    output_path: Path,
    known_optimum: int | None = None,
) -> None:
    plt = _require_matplotlib()
    figure, axis = plt.subplots(figsize=(10, max(4, len({op["job"] for op in operations}) * 0.35)))

    jobs = sorted({int(op["job"]) for op in operations})
    job_positions = {job: index for index, job in enumerate(jobs)}
    colors = plt.cm.tab20.colors

    for operation in operations:
        job = int(operation["job"])
        machine = int(operation["machine"])
        start = int(operation["start"])
        duration = int(operation["processing_time"])
        y_pos = job_positions[job]
        axis.barh(
            y_pos,
            duration,
            left=start,
            height=0.6,
            color=colors[machine % len(colors)],
            edgecolor="black",
            linewidth=0.3,
        )

    axis.set_yticks(list(job_positions.values()))
    axis.set_yticklabels([f"Job {job}" for job in jobs])
    axis.set_xlabel("Time")
    title = f"JSP Gantt — {_algorithm_label(algorithm)} ({config.instance})\n"
    title += f"Makespan: {makespan:.0f}"
    if known_optimum is not None:
        gap = ((makespan - known_optimum) / known_optimum) * 100
        title += f"  |  Best known: {known_optimum}  |  Gap: {gap:.1f}%"
    axis.set_title(title)
    axis.grid(True, axis="x", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_feature_selection_summary(
    solution: dict[str, Any],
    config: ExperimentConfig,
    algorithm: str,
    output_path: Path,
) -> None:
    plt = _require_matplotlib()
    figure, axis = plt.subplots(figsize=(8, 4))

    labels = ["Selected", "Removed"]
    selected = int(solution.get("selected_feature_count", 0))
    total = len(solution.get("feature_mask", [])) or selected
    removed = max(total - selected, 0)
    axis.bar(labels, [selected, removed], color=["#2563eb", "#94a3b8"])
    axis.set_ylabel("Feature count")
    title = (
        f"Feature Selection — {_algorithm_label(algorithm)} ({config.instance})\n"
        f"CV score: {solution.get('cv_score', 0):.3f}  |  "
        f"Test score: {solution.get('test_score', 0):.3f}  |  "
        f"Selected: {selected}/{total}"
    )
    axis.set_title(title)
    axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def _best_run_per_algorithm(results: list[RunResult]) -> dict[str, RunResult]:
    best: dict[str, RunResult] = {}
    for result in results:
        current = best.get(result.algorithm)
        if current is None or result.best_objective < current.best_objective:
            best[result.algorithm] = result
    return best


def generate_experiment_charts(
    experiment_dir: Path,
    results: list[RunResult],
    config: ExperimentConfig,
) -> list[Path]:
    """Generate standard charts for an experiment directory."""
    charts_dir = experiment_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    generated: list[Path] = []

    chart_specs: list[tuple[str, Any]] = [
        ("convergence.png", plot_convergence),
        ("convergence_by_run.png", plot_convergence_by_algorithm),
        ("objective_boxplot.png", plot_objective_boxplot),
        ("runtime_comparison.png", plot_runtime_comparison),
    ]

    for filename, plotter in chart_specs:
        output_path = charts_dir / filename
        if plotter in {plot_convergence, plot_convergence_by_algorithm}:
            plotter(experiment_dir, results, config, output_path)
        else:
            plotter(results, config, output_path)
        generated.append(output_path)

    if config.domain == "tsp" and config.instance_path:
        from optimize.domains.tsp.loader import load_tsplib

        instance = load_tsplib(config.instance_path)
        for algorithm, run in _best_run_per_algorithm(results).items():
            solution = run.best_solution
            if not isinstance(solution, dict) or "route" not in solution:
                continue
            route_path = charts_dir / f"tsp_route_{algorithm}.png"
            plot_tsp_route(
                route=solution["route"],
                coordinates=instance.coordinates,
                config=config,
                algorithm=algorithm,
                distance=float(solution.get("distance", run.best_objective)),
                output_path=route_path,
                known_optimum=solution.get("known_optimum"),
            )
            generated.append(route_path)

        overall_best = min(results, key=lambda item: item.best_objective)
        if isinstance(overall_best.best_solution, dict) and "route" in overall_best.best_solution:
            best_path = charts_dir / "tsp_route_best_overall.png"
            solution = overall_best.best_solution
            plot_tsp_route(
                route=solution["route"],
                coordinates=instance.coordinates,
                config=config,
                algorithm=overall_best.algorithm,
                distance=float(solution.get("distance", overall_best.best_objective)),
                output_path=best_path,
                known_optimum=solution.get("known_optimum"),
            )
            generated.append(best_path)

    if config.domain == "scheduling":
        for algorithm, run in _best_run_per_algorithm(results).items():
            solution = run.best_solution
            if not isinstance(solution, dict) or "operations" not in solution:
                continue
            gantt_path = charts_dir / f"jsp_gantt_{algorithm}.png"
            plot_jsp_gantt(
                operations=solution["operations"],
                config=config,
                algorithm=algorithm,
                makespan=float(solution.get("makespan", run.best_objective)),
                output_path=gantt_path,
                known_optimum=solution.get("known_optimum"),
            )
            generated.append(gantt_path)

        overall_best = min(results, key=lambda item: item.best_objective)
        if isinstance(overall_best.best_solution, dict) and "operations" in overall_best.best_solution:
            best_path = charts_dir / "jsp_gantt_best_overall.png"
            solution = overall_best.best_solution
            plot_jsp_gantt(
                operations=solution["operations"],
                config=config,
                algorithm=overall_best.algorithm,
                makespan=float(solution.get("makespan", overall_best.best_objective)),
                output_path=best_path,
                known_optimum=solution.get("known_optimum"),
            )
            generated.append(best_path)

    if config.domain == "feature_selection":
        for algorithm, run in _best_run_per_algorithm(results).items():
            solution = run.best_solution
            if not isinstance(solution, dict) or "selected_feature_count" not in solution:
                continue
            chart_path = charts_dir / f"fs_selected_features_{algorithm}.png"
            plot_feature_selection_summary(
                solution=solution,
                config=config,
                algorithm=algorithm,
                output_path=chart_path,
            )
            generated.append(chart_path)

    return generated
