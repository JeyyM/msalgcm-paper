"""Validate experiment output artifacts."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from optimize.domains.tsp.distance import build_distance_matrix, tour_length
from optimize.domains.tsp.loader import load_tsplib

KNOWN_OPT = 426
EXPECTED_ALGOS = ["simulated_annealing", "tabu_search", "particle_swarm"]
EXPECTED_RUNS = 10
EXPECTED_BUDGET = 100000
EXPECTED_CHARTS = [
    "convergence.png",
    "convergence_by_run.png",
    "objective_boxplot.png",
    "runtime_comparison.png",
    "tsp_route_simulated_annealing.png",
    "tsp_route_tabu_search.png",
    "tsp_route_particle_swarm.png",
    "tsp_route_best_overall.png",
]
REQUIRED_FILES = [
    "experiment_config.json",
    "environment.json",
    "seeds.csv",
    "runs.csv",
    "summary.csv",
    "statistics.csv",
    "logs/experiment.log",
]


def validate_experiment(result_dir: Path) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    passes: list[str] = []

    for rel_path in REQUIRED_FILES:
        if not (result_dir / rel_path).exists():
            issues.append(f"Missing {rel_path}")

    conv_files = list((result_dir / "convergence").glob("*.csv"))
    sol_files = list((result_dir / "solutions").glob("*.json"))
    if len(conv_files) != 30:
        issues.append(f"Expected 30 convergence CSVs, got {len(conv_files)}")
    else:
        passes.append("30 convergence CSVs")

    if len(sol_files) != 30:
        issues.append(f"Expected 30 solution JSONs, got {len(sol_files)}")
    else:
        passes.append("30 solution JSONs")

    charts_dir = result_dir / "charts"
    if charts_dir.exists():
        for chart_name in EXPECTED_CHARTS:
            chart_path = charts_dir / chart_name
            if not chart_path.exists():
                issues.append(f"Missing chart {chart_name}")
            elif chart_path.stat().st_size < 1000:
                issues.append(f"Chart too small (possibly empty): {chart_name}")
        if not issues or all("chart" not in item.lower() or "Missing chart" not in item for item in issues):
            passes.append(f"All {len(EXPECTED_CHARTS)} charts present and non-empty")
    else:
        issues.append("Missing charts/ directory")

    with (result_dir / "runs.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != 30:
        issues.append(f"runs.csv has {len(rows)} rows, expected 30")
    else:
        passes.append("runs.csv: 30 rows")

    by_algo: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_algo[row["algorithm"]].append(row)
        if row["status"] != "completed":
            issues.append(f"{row['run_id']}: status={row['status']}")
        if int(row["objective_evaluations"]) != EXPECTED_BUDGET:
            issues.append(f"{row['run_id']}: wrong eval count")
        if row["parameters"] and not row["parameters"].startswith("{"):
            issues.append(f"{row['run_id']}: parameters not JSON")

    for algo in EXPECTED_ALGOS:
        if len(by_algo[algo]) != EXPECTED_RUNS:
            issues.append(f"{algo}: expected {EXPECTED_RUNS} runs")

    instance = load_tsplib("datasets/tsp/instances/eil51.tsp")
    distance_matrix = build_distance_matrix(instance.coordinates)

    for solution_file in sol_files:
        data = json.loads(solution_file.read_text(encoding="utf-8"))
        route = data["route"]
        if sorted(route) != list(range(51)):
            issues.append(f"{solution_file.name}: invalid route")
        computed = tour_length(route, distance_matrix)
        if computed != data["distance"]:
            issues.append(f"{solution_file.name}: distance mismatch")
        run_id = solution_file.stem
        row = next(item for item in rows if item["run_id"] == run_id)
        if float(row["best_objective"]) != data["distance"]:
            issues.append(f"{run_id}: runs.csv vs solution mismatch")

    if not any("invalid route" in issue or "distance mismatch" in issue for issue in issues):
        passes.append("All routes valid, distances consistent")

    log_text = (result_dir / "logs" / "experiment.log").read_text(encoding="utf-8")
    if "completed=30" in log_text and "failed=0" in log_text:
        passes.append("All 30 runs completed successfully")
    if "charts=8" in log_text:
        passes.append("Charts auto-generated during run")

    return passes, issues


def main() -> None:
    directories = sys.argv[1:] or [
        "results/2026-08-03_000444_tsp_eil51_comparison",
        "results/2026-08-02_235730_tsp_eil51_comparison",
    ]

    for directory in directories:
        result_dir = Path(directory)
        print(f"=== {result_dir.name} ===")
        if not result_dir.exists():
            print("  [FAIL] Directory not found")
            print()
            continue

        passes, issues = validate_experiment(result_dir)
        for item in passes:
            print(f"  [OK] {item}")
        for item in issues:
            print(f"  [FAIL] {item}")
        if not issues:
            print("  Result: PASS")
        else:
            print(f"  Result: FAIL ({len(issues)} issues)")
        print()


if __name__ == "__main__":
    main()
