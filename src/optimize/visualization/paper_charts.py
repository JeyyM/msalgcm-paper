"""Publication-quality charts aggregated across comparison experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from optimize.visualization.charts import (
    _algorithm_label,
    _load_convergence_from_csv,
    _mean_convergence_curve,
    _require_matplotlib,
    _y_limits,
)

ALGO_COLORS = {
    "simulated_annealing": "#60a5fa",
    "tabu_search": "#34d399",
    "particle_swarm": "#fbbf24",
}


def _color(algorithm: str, index: int) -> str:
    return ALGO_COLORS.get(algorithm, f"C{index}")


def plot_gap_bar_chart(
    rows: list[dict[str, Any]],
    algorithms: list[str],
    output_path: Path,
    *,
    title: str,
    ylabel: str = "Best gap from optimum (%)",
    value_key: str = "best_gap_percentage",
) -> None:
    plt = _require_matplotlib()
    import numpy as np

    instances = [row["instance"] for row in rows]
    if not instances:
        return

    x = np.arange(len(instances))
    width = 0.8 / max(len(algorithms), 1)
    figure, axis = plt.subplots(figsize=(10, 5.5))

    for index, algorithm in enumerate(algorithms):
        offsets = x - 0.4 + width / 2 + index * width
        heights: list[float] = []
        for row in rows:
            result = row["results"].get(algorithm, {})
            value = result.get(value_key)
            heights.append(float(value) if value is not None else 0.0)
        axis.bar(
            offsets,
            heights,
            width=width,
            label=_algorithm_label(algorithm),
            color=_color(algorithm, index),
            edgecolor="white",
            linewidth=0.5,
        )

    axis.set_xticks(x)
    axis.set_xticklabels(instances, rotation=25, ha="right")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend()
    axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def plot_gap_scalability(
    rows: list[dict[str, Any]],
    algorithms: list[str],
    output_path: Path,
    *,
    title: str,
    ylabel: str = "Best gap from optimum (%)",
    value_key: str = "best_gap_percentage",
) -> None:
    plt = _require_matplotlib()

    figure, axis = plt.subplots(figsize=(10, 5.5))
    plotted = False

    for index, algorithm in enumerate(algorithms):
        points: list[tuple[float, float]] = []
        for row in rows:
            size = row.get("problem_size")
            gap = row["results"].get(algorithm, {}).get(value_key)
            if size is None or gap is None:
                continue
            points.append((float(size), float(gap)))
        if not points:
            continue
        points.sort(key=lambda item: item[0])
        axis.plot(
            [point[0] for point in points],
            [point[1] for point in points],
            marker="o",
            linewidth=2,
            label=_algorithm_label(algorithm),
            color=_color(algorithm, index),
        )
        plotted = True

    if not plotted:
        plt.close(figure)
        return

    axis.set_xlabel("Problem size")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def plot_fs_best_objective_bar(
    rows: list[dict[str, Any]],
    algorithms: list[str],
    output_path: Path,
    *,
    title: str,
) -> None:
    plt = _require_matplotlib()
    import numpy as np

    instances = [row["instance"] for row in rows]
    if not instances:
        return

    x = np.arange(len(instances))
    width = 0.8 / max(len(algorithms), 1)
    figure, axis = plt.subplots(figsize=(10, 5.5))

    for index, algorithm in enumerate(algorithms):
        offsets = x - 0.4 + width / 2 + index * width
        heights: list[float] = []
        for row in rows:
            value = row["results"].get(algorithm, {}).get("best_objective")
            heights.append(float(value) if value is not None else 0.0)
        axis.bar(
            offsets,
            heights,
            width=width,
            label=_algorithm_label(algorithm),
            color=_color(algorithm, index),
            edgecolor="white",
            linewidth=0.5,
        )

    axis.set_xticks(x)
    axis.set_xticklabels(instances, rotation=20, ha="right")
    axis.set_ylabel("Best wrapper objective (lower is better)")
    axis.set_title(title)
    axis.legend()
    axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def plot_combined_convergence(
    experiment_dirs: dict[str, Path],
    evaluation_budget: int,
    output_path: Path,
    *,
    instance: str,
    domain_label: str,
) -> None:
    plt = _require_matplotlib()

    figure, axis = plt.subplots(figsize=(10, 5.5))
    y_values_for_axis: list[float] = []
    plotted = False

    for index, (algorithm, experiment_dir) in enumerate(sorted(experiment_dirs.items())):
        convergence_dir = experiment_dir / "convergence"
        runs_path = experiment_dir / "runs.csv"
        if not runs_path.exists():
            continue

        histories: list[tuple[list[int], list[float]]] = []
        import csv

        with runs_path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") != "completed":
                    continue
                csv_path = convergence_dir / f"{row['run_id']}.csv"
                if csv_path.exists():
                    histories.append(_load_convergence_from_csv(csv_path))

        if not histories:
            continue

        x_values, y_values = _mean_convergence_curve(histories, evaluation_budget)
        y_values_for_axis.extend(y_values)
        axis.plot(
            x_values,
            y_values,
            label=_algorithm_label(algorithm),
            color=_color(algorithm, index),
            linewidth=2,
            drawstyle="steps-post",
        )
        plotted = True

    if not plotted:
        plt.close(figure)
        return

    axis.set_xlabel("Objective evaluations")
    axis.set_ylabel("Mean best objective (30 seeds)")
    axis.set_title(f"Convergence — {instance} ({domain_label})")
    if y_values_for_axis:
        axis.set_ylim(_y_limits(y_values_for_axis))
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180)
    plt.close(figure)
