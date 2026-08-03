"""Scalability charts across multiple TSP instances."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from optimize.visualization.charts import _algorithm_label, _require_matplotlib


def plot_scalability_gap(
    rows: list[dict[str, Any]],
    output_path: Path,
    study_name: str,
) -> None:
    plt = _require_matplotlib()
    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)

    for row in rows:
        gap = row.get("best_gap_percentage")
        if gap is None:
            continue
        grouped[row["algorithm"]].append((int(row["problem_size"]), float(gap)))

    if not grouped:
        return

    figure, axis = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10.colors

    for index, (algorithm, points) in enumerate(sorted(grouped.items())):
        points.sort(key=lambda item: item[0])
        x_values = [point[0] for point in points]
        y_values = [point[1] for point in points]
        axis.plot(
            x_values,
            y_values,
            marker="o",
            linewidth=2,
            label=_algorithm_label(algorithm),
            color=colors[index % len(colors)],
        )

    axis.set_xlabel("Problem Size (number of cities)")
    axis.set_ylabel("Best Gap from Optimum (%)")
    axis.set_title(f"TSP Scalability — Gap vs Problem Size ({study_name})")
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_scalability_mean_gap(
    rows: list[dict[str, Any]],
    output_path: Path,
    study_name: str,
) -> None:
    plt = _require_matplotlib()
    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)

    for row in rows:
        gap = row.get("mean_gap_percentage")
        if gap is None:
            continue
        grouped[row["algorithm"]].append((int(row["problem_size"]), float(gap)))

    if not grouped:
        return

    figure, axis = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10.colors

    for index, (algorithm, points) in enumerate(sorted(grouped.items())):
        points.sort(key=lambda item: item[0])
        x_values = [point[0] for point in points]
        y_values = [point[1] for point in points]
        axis.plot(
            x_values,
            y_values,
            marker="o",
            linewidth=2,
            label=_algorithm_label(algorithm),
            color=colors[index % len(colors)],
        )

    axis.set_xlabel("Problem Size (number of cities)")
    axis.set_ylabel("Mean Gap from Optimum (%)")
    axis.set_title(f"TSP Scalability — Mean Gap vs Problem Size ({study_name})")
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_scalability_best_objective(
    rows: list[dict[str, Any]],
    output_path: Path,
    study_name: str,
) -> None:
    plt = _require_matplotlib()
    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)

    for row in rows:
        grouped[row["algorithm"]].append((int(row["problem_size"]), float(row["min_objective"])))

    figure, axis = plt.subplots(figsize=(10, 6))
    colors = plt.cm.tab10.colors

    for index, (algorithm, points) in enumerate(sorted(grouped.items())):
        points.sort(key=lambda item: item[0])
        x_values = [point[0] for point in points]
        y_values = [point[1] for point in points]
        axis.plot(
            x_values,
            y_values,
            marker="o",
            linewidth=2,
            label=_algorithm_label(algorithm),
            color=colors[index % len(colors)],
        )

    axis.set_xlabel("Problem Size (number of cities)")
    axis.set_ylabel("Best Objective Found")
    axis.set_yscale("log")
    axis.set_title(f"TSP Scalability — Best Objective vs Problem Size ({study_name})")
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def generate_scalability_charts(
    study_dir: Path,
    rows: list[dict[str, Any]],
) -> list[Path]:
    charts_dir = study_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    study_name = rows[0]["study_name"] if rows else study_dir.name

    chart_specs = [
        ("scalability_gap.png", plot_scalability_gap),
        ("scalability_mean_gap.png", plot_scalability_mean_gap),
        ("scalability_best_objective.png", plot_scalability_best_objective),
    ]

    generated: list[Path] = []
    for filename, plotter in chart_specs:
        output_path = charts_dir / filename
        plotter(rows, output_path, study_name)
        generated.append(output_path)

    return generated
