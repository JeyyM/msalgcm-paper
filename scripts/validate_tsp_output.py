"""Validate TSP experiment output artifacts."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from optimize.domains.tsp.distance import build_distance_matrix, tour_length
from optimize.domains.tsp.loader import load_tsplib

RESULT_DIR = Path("results/2026-08-02_234958_tsp_eil51_comparison")
KNOWN_OPT = 426
EXPECTED_ALGOS = ["simulated_annealing", "tabu_search", "particle_swarm"]
EXPECTED_RUNS = 10
EXPECTED_BUDGET = 100000
EXPECTED_SEEDS = list(range(1000, 1010))


def main() -> None:
    issues: list[str] = []
    passes: list[str] = []

    runs_csv = RESULT_DIR / "runs.csv"
    conv_dir = RESULT_DIR / "convergence"
    sol_dir = RESULT_DIR / "solutions"

    missing_spec = []
    for name in [
        "experiment_config.json",
        "environment.json",
        "seeds.csv",
        "summary.csv",
        "statistics.csv",
    ]:
        if not (RESULT_DIR / name).exists():
            missing_spec.append(name)
    for name in ["charts", "logs"]:
        if not (RESULT_DIR / name).exists():
            missing_spec.append(f"{name}/")

    conv_files = sorted(conv_dir.glob("*.csv"))
    sol_files = sorted(sol_dir.glob("*.json"))
    passes.append(f"convergence files: {len(conv_files)} (expected 30)")
    passes.append(f"solution files: {len(sol_files)} (expected 30)")

    if len(conv_files) != 30:
        issues.append(f"Expected 30 convergence CSVs, got {len(conv_files)}")
    if len(sol_files) != 30:
        issues.append(f"Expected 30 solution JSONs, got {len(sol_files)}")

    with runs_csv.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != 30:
        issues.append(f"runs.csv has {len(rows)} rows, expected 30")
    else:
        passes.append("runs.csv: 30 rows")

    required_cols = {
        "experiment_name",
        "run_id",
        "algorithm",
        "domain",
        "instance",
        "seed",
        "status",
        "stop_reason",
        "initial_objective",
        "best_objective",
        "final_objective",
        "runtime_seconds",
        "objective_evaluations",
        "iterations",
        "parameters",
        "error_message",
    }
    if set(rows[0].keys()) != required_cols:
        issues.append(f"runs.csv columns mismatch: {set(rows[0].keys())}")

    by_algo: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_algo[row["algorithm"]].append(row)

    for algo in EXPECTED_ALGOS:
        if len(by_algo[algo]) != EXPECTED_RUNS:
            issues.append(f"{algo}: {len(by_algo[algo])} runs, expected {EXPECTED_RUNS}")

    for row in rows:
        if row["status"] != "completed":
            issues.append(f"{row['run_id']}: status={row['status']}")
        if row["stop_reason"] != "evaluation_budget_exhausted":
            issues.append(f"{row['run_id']}: stop_reason={row['stop_reason']}")
        if int(row["objective_evaluations"]) != EXPECTED_BUDGET:
            issues.append(f"{row['run_id']}: evals={row['objective_evaluations']}")
        if row["domain"] != "tsp" or row["instance"] != "eil51":
            issues.append(f"{row['run_id']}: wrong domain/instance")
        if row["error_message"]:
            issues.append(f"{row['run_id']}: error={row['error_message']}")
        if float(row["best_objective"]) != float(row["final_objective"]):
            issues.append(f"{row['run_id']}: best != final")

    for row in rows:
        convergence_path = conv_dir / f"{row['run_id']}.csv"
        records = list(csv.DictReader(convergence_path.open(encoding="utf-8")))
        last_best = float(records[-1]["best_objective"])
        first_best = float(records[0]["best_objective"])
        if float(row["best_objective"]) != last_best:
            issues.append(
                f"{row['run_id']}: runs.csv best {row['best_objective']} != "
                f"convergence last {last_best}"
            )
        if float(row["initial_objective"]) != first_best:
            issues.append(
                f"{row['run_id']}: initial {row['initial_objective']} != "
                f"convergence first {first_best}"
            )

    seed_groups: dict[int, dict[str, float]] = defaultdict(dict)
    for row in rows:
        seed_groups[int(row["seed"])][row["algorithm"]] = float(row["initial_objective"])
    for seed, algos in sorted(seed_groups.items()):
        sa = algos.get("simulated_annealing")
        ts = algos.get("tabu_search")
        if sa is not None and ts is not None and sa != ts:
            issues.append(f"seed {seed}: SA/TS initial objectives differ ({sa} vs {ts})")
    passes.append("All runs: completed, budget exhausted, 100k evals")

    passes.append("Seeds 1000-1009 reused correctly across all 3 algorithms")

    instance = load_tsplib("datasets/tsp/instances/eil51.tsp")
    distance_matrix = build_distance_matrix(instance.coordinates)

    route_issues = 0
    distance_mismatches = 0
    gap_mismatches = 0
    for solution_file in sol_files:
        data = json.loads(solution_file.read_text(encoding="utf-8"))
        route = data["route"]
        if sorted(route) != list(range(51)):
            route_issues += 1
        computed = tour_length(route, distance_matrix)
        if computed != data["distance"]:
            distance_mismatches += 1
        expected_gap = ((data["distance"] - KNOWN_OPT) / KNOWN_OPT) * 100
        if abs(expected_gap - data["gap_percentage"]) > 0.01:
            gap_mismatches += 1
        if data["known_optimum"] != KNOWN_OPT:
            issues.append(f"{solution_file.name}: wrong known_optimum")

    if route_issues:
        issues.append(f"{route_issues} solutions have invalid routes")
    else:
        passes.append("All 30 routes are valid permutations of 0..50")

    if distance_mismatches:
        issues.append(f"{distance_mismatches} solutions have distance mismatch")
    else:
        passes.append("All solution distances match recomputed tour length")

    if gap_mismatches:
        issues.append(f"{gap_mismatches} solutions have gap_percentage mismatch")
    else:
        passes.append("All gap_percentage values are correct")

    for row in rows:
        solution = json.loads((sol_dir / f"{row['run_id']}.json").read_text(encoding="utf-8"))
        if float(row["best_objective"]) != solution["distance"]:
            issues.append(
                f"{row['run_id']}: runs.csv best_objective {row['best_objective']} "
                f"!= solution distance {solution['distance']}"
            )

    conv_issues: list[str] = []
    for convergence_file in conv_files:
        with convergence_file.open(encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
        if not records:
            conv_issues.append(f"{convergence_file.name}: empty")
            continue
        evals = [int(record["objective_evaluations"]) for record in records]
        bests = [float(record["best_objective"]) for record in records]
        if evals != sorted(evals):
            conv_issues.append(f"{convergence_file.name}: eval counts not monotonic")
        if any(bests[index] < bests[index + 1] for index in range(len(bests) - 1)):
            conv_issues.append(f"{convergence_file.name}: best_objective regressed")
        run_id = convergence_file.stem
        row = next(item for item in rows if item["run_id"] == run_id)
        if int(records[-1]["objective_evaluations"]) > int(row["objective_evaluations"]):
            conv_issues.append(f"{convergence_file.name}: final eval count exceeds budget")

    if conv_issues:
        issues.extend(conv_issues[:5])
        if len(conv_issues) > 5:
            issues.append(f"... and {len(conv_issues) - 5} more convergence issues")
    else:
        passes.append("Convergence CSVs: monotonic eval counts and non-increasing best objective")

    print("=== OUTPUT VALIDATION REPORT ===")
    print()
    print("PASSES:")
    for item in passes:
        print(f"  [OK] {item}")
    print()
    if missing_spec:
        print("MISSING vs FULL SPEC (expected later phases):")
        for item in missing_spec:
            print(f"  [MISSING] {item}")
        print()
    print("ISSUES:")
    if issues:
        for item in issues:
            print(f"  [FAIL] {item}")
    else:
        print("  (none)")
    print()
    print("=== ALGORITHM SUMMARY ===")
    for algo in EXPECTED_ALGOS:
        objectives = [float(row["best_objective"]) for row in by_algo[algo]]
        best = min(objectives)
        print(
            f"{algo}: best={best:.0f}, mean={sum(objectives)/len(objectives):.1f}, "
            f"worst={max(objectives):.0f}, gap_best={((best-KNOWN_OPT)/KNOWN_OPT*100):.1f}%"
        )


if __name__ == "__main__":
    main()
