"""General-purpose audit for TSP comparison result folders.

Checks (mapped to audit_checklist.md):
  P0-03  completeness: 90 rows, 30 per algorithm, all completed
  P0-04  same seeds reused across all 3 algorithms
  P0-05  evaluation budget exactly 100000 for every run
  P0-06  gap_percentage recomputes correctly from distance + known_optimum
  P0-07  route is a valid permutation; stored distance matches recomputed tour length
  P1-09  convergence CSV: monotonic eval counts, non-increasing best_objective,
         final value matches runs.csv, never exceeds budget
  P2-08  stop_reason distribution (flags non-budget-exhausted stops)
  P0-01  algorithm_configs in experiment_config.json match frozen selected_parameters.json

Usage:
  python scripts/audit_tsp_results.py <results_dir> [<results_dir> ...]
  python scripts/audit_tsp_results.py --all-canonical
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optimize.domains.tsp.distance import build_distance_matrix, tour_length  # noqa: E402
from optimize.domains.tsp.loader import load_tsplib  # noqa: E402

METADATA_PATH = ROOT / "datasets" / "tsp" / "metadata.json"
SELECTED_PARAMS_PATH = ROOT / "results" / "tuning" / "selected_parameters.json"
EXPECTED_ALGOS = ["simulated_annealing", "tabu_search", "particle_swarm"]
EXPECTED_RUNS_PER_ALGO = 30
EXPECTED_BUDGET = 100_000

CANONICAL_FOLDERS = [
    "2026-08-06_214444_tsp_kroA100_comparison",
    "2026-08-06_220149_tsp_ch130_comparison",
    "2026-08-06_215320_tsp_rat195_comparison",
]


def known_optima() -> dict[str, int]:
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))["known_optima"]


def frozen_params() -> dict[str, dict]:
    return json.loads(SELECTED_PARAMS_PATH.read_text(encoding="utf-8"))["winners"]


class AuditResult:
    def __init__(self, folder: str) -> None:
        self.folder = folder
        self.passes: list[str] = []
        self.fails: list[str] = []
        self.warnings: list[str] = []

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def fail(self, msg: str) -> None:
        self.fails.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def clean(self) -> bool:
        return not self.fails


def audit_folder(exp_dir: Path) -> AuditResult:
    result = AuditResult(exp_dir.name)

    config_path = exp_dir / "experiment_config.json"
    runs_path = exp_dir / "runs.csv"
    conv_dir = exp_dir / "convergence"
    sol_dir = exp_dir / "solutions"

    if not config_path.exists():
        result.fail("experiment_config.json missing")
        return result
    if not runs_path.exists():
        result.fail("runs.csv missing")
        return result

    config = json.loads(config_path.read_text(encoding="utf-8"))["config"]
    instance_name = config["instance"]
    opt_table = known_optima()
    if instance_name not in opt_table:
        result.fail(f"no known_optimum for instance {instance_name} in metadata.json")
        return result
    known_opt = opt_table[instance_name]

    # --- P0-01: params match frozen selection ---
    winners = frozen_params()
    for algo, winner in winners.items():
        expected = winner["parameters"]
        actual = config.get("algorithm_configs", {}).get(algo, {})
        if actual != expected:
            result.fail(f"P0-01 {algo}: config params {actual} != frozen {expected}")
    if config.get("domain_config", {}).get("initial_solution") != "nearest_neighbor":
        result.fail(
            f"P0-01 domain_config.initial_solution="
            f"{config.get('domain_config', {}).get('initial_solution')!r}, expected nearest_neighbor",
        )
    if not result.fails:
        result.ok("P0-01 algorithm_configs + initial_solution match results/tuning/selected_parameters.json")

    # --- Load runs.csv ---
    with runs_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    by_algo: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_algo[row["algorithm"]].append(row)

    # --- P0-03: completeness ---
    if len(rows) != len(EXPECTED_ALGOS) * EXPECTED_RUNS_PER_ALGO:
        result.fail(f"P0-03 runs.csv has {len(rows)} rows, expected {len(EXPECTED_ALGOS) * EXPECTED_RUNS_PER_ALGO}")
    for algo in EXPECTED_ALGOS:
        n = len(by_algo.get(algo, []))
        if n != EXPECTED_RUNS_PER_ALGO:
            result.fail(f"P0-03 {algo}: {n} runs, expected {EXPECTED_RUNS_PER_ALGO}")
    non_completed = [r["run_id"] for r in rows if r["status"] != "completed"]
    if non_completed:
        result.fail(f"P0-03 {len(non_completed)} runs not status=completed: {non_completed[:5]}")
    error_rows = [r["run_id"] for r in rows if r.get("error_message")]
    if error_rows:
        result.fail(f"P0-03 {len(error_rows)} runs have error_message set: {error_rows[:5]}")
    if not (non_completed or error_rows) and len(rows) == 90:
        result.ok(f"P0-03 completeness: 90/90 rows, all status=completed, no errors")

    # --- P0-05: evaluation budget ---
    bad_budget = [r["run_id"] for r in rows if int(r["objective_evaluations"]) != EXPECTED_BUDGET]
    if bad_budget:
        result.fail(f"P0-05 {len(bad_budget)} runs != {EXPECTED_BUDGET} evaluations: {bad_budget[:5]}")
    else:
        result.ok(f"P0-05 all {len(rows)} runs used exactly {EXPECTED_BUDGET} evaluations")

    # --- P2-08: stop_reason distribution ---
    stop_reasons = defaultdict(int)
    for r in rows:
        stop_reasons[r["stop_reason"]] += 1
    non_budget = {k: v for k, v in stop_reasons.items() if k != "evaluation_budget_exhausted"}
    if non_budget:
        result.warn(f"P2-08 stop_reason distribution includes non-budget stops: {dict(stop_reasons)}")
    else:
        result.ok(f"P2-08 all runs stopped via evaluation_budget_exhausted")

    # --- P0-04: seed consistency across algorithms ---
    seeds_path = exp_dir / "seeds.csv"
    if seeds_path.exists():
        with seeds_path.open(encoding="utf-8") as handle:
            seed_rows = list(csv.DictReader(handle))
        by_algo_seeds: dict[str, list[int]] = defaultdict(list)
        for r in seed_rows:
            by_algo_seeds[r["algorithm"]].append(int(r["seed"]))
        seed_sets = {algo: sorted(v) for algo, v in by_algo_seeds.items()}
        reference = next(iter(seed_sets.values())) if seed_sets else []
        mismatched = [algo for algo, seeds in seed_sets.items() if seeds != reference]
        if mismatched:
            result.fail(f"P0-04 seed mismatch across algorithms: {mismatched}")
        else:
            result.ok(f"P0-04 identical {len(reference)} seeds reused across all algorithms")
    else:
        result.warn("P0-04 seeds.csv missing, cannot verify")

    # --- P0-07: tour validity + distance recompute ---
    instance_path = ROOT / config["instance_path"]
    tsp_instance = load_tsplib(instance_path)
    distance_matrix = build_distance_matrix(tsp_instance.coordinates)
    n_cities = tsp_instance.num_cities

    all_sol_files = sorted(sol_dir.glob("*.json")) if sol_dir.exists() else []
    live_files = [f for f in all_sol_files if f.name.endswith(".live.json")]
    sol_files = [f for f in all_sol_files if not f.name.endswith(".live.json")]
    if live_files:
        result.warn(
            f"P2-hygiene {len(live_files)} stale .live.json snapshot files not cleaned up "
            f"after completion (solutions/ dir has {len(all_sol_files)} files for {len(rows)} runs)",
        )
    if len(sol_files) != len(rows):
        result.fail(f"P0-07 {len(sol_files)} solution files, expected {len(rows)}")

    route_issues = 0
    dist_mismatches = 0
    gap_mismatches = 0
    opt_mismatches = 0
    linkage_mismatches = 0
    row_by_id = {r["run_id"]: r for r in rows}

    for sol_file in sol_files:
        data = json.loads(sol_file.read_text(encoding="utf-8"))
        route = data["route"]
        if sorted(route) != list(range(n_cities)):
            route_issues += 1
            continue
        computed = tour_length(route, distance_matrix)
        if computed != data["distance"]:
            dist_mismatches += 1
        if data["known_optimum"] != known_opt:
            opt_mismatches += 1
        expected_gap = ((data["distance"] - known_opt) / known_opt) * 100
        if abs(expected_gap - data["gap_percentage"]) > 0.01:
            gap_mismatches += 1
        run_id = sol_file.stem
        row = row_by_id.get(run_id)
        if row and float(row["best_objective"]) != float(data["distance"]):
            linkage_mismatches += 1

    if route_issues:
        result.fail(f"P0-07 {route_issues} solutions are not valid permutations of 0..{n_cities - 1}")
    else:
        result.ok(f"P0-07 all {len(sol_files)} routes are valid permutations")
    if dist_mismatches:
        result.fail(f"P0-07 {dist_mismatches} solutions: stored distance != recomputed tour length")
    else:
        result.ok("P0-07 all stored distances match recomputed tour length from raw coordinates")
    if opt_mismatches:
        result.fail(f"P0-06 {opt_mismatches} solutions have wrong known_optimum stored")
    if gap_mismatches:
        result.fail(f"P0-06 {gap_mismatches} solutions: gap_percentage does not match formula")
    else:
        result.ok(f"P0-06 gap_percentage recomputes correctly for all {len(sol_files)} solutions "
                   f"(known_optimum={known_opt})")
    if linkage_mismatches:
        result.fail(f"P0-07 {linkage_mismatches} solutions: distance != runs.csv best_objective")
    else:
        result.ok("P0-07 solution distance matches runs.csv best_objective for all runs")

    # --- P1-09: convergence consistency ---
    conv_files = sorted(conv_dir.glob("*.csv")) if conv_dir.exists() else []
    if len(conv_files) != len(rows):
        result.fail(f"P1-09 {len(conv_files)} convergence files, expected {len(rows)}")

    non_monotonic_evals = 0
    regressed_best = 0
    exceeds_budget = 0
    final_mismatch = 0
    initial_mismatch = 0

    for conv_file in conv_files:
        with conv_file.open(encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
        if not records:
            continue
        evals = [int(rec["objective_evaluations"]) for rec in records]
        bests = [float(rec["best_objective"]) for rec in records]
        if evals != sorted(evals):
            non_monotonic_evals += 1
        if any(bests[i] < bests[i + 1] for i in range(len(bests) - 1)):
            regressed_best += 1
        run_id = conv_file.stem
        row = row_by_id.get(run_id)
        if row:
            if evals[-1] > int(row["objective_evaluations"]):
                exceeds_budget += 1
            if float(row["best_objective"]) != bests[-1]:
                final_mismatch += 1
            if float(row["initial_objective"]) != bests[0]:
                initial_mismatch += 1

    if non_monotonic_evals:
        result.fail(f"P1-09 {non_monotonic_evals} convergence files: eval counts not monotonic")
    if regressed_best:
        result.fail(f"P1-09 {regressed_best} convergence files: best_objective increased (regressed)")
    if exceeds_budget:
        result.fail(f"P1-09 {exceeds_budget} convergence files: final eval count exceeds budget")
    if final_mismatch:
        result.fail(f"P1-09 {final_mismatch} convergence files: last best != runs.csv best_objective")
    if initial_mismatch:
        result.fail(f"P1-09 {initial_mismatch} convergence files: first best != runs.csv initial_objective")
    if not any([non_monotonic_evals, regressed_best, exceeds_budget, final_mismatch, initial_mismatch]) and conv_files:
        result.ok(f"P1-09 all {len(conv_files)} convergence CSVs are monotonic and consistent with runs.csv")

    return result


def print_report(result: AuditResult) -> None:
    print(f"\n{'=' * 70}")
    print(f"AUDIT: {result.folder}")
    print("=" * 70)
    for msg in result.passes:
        print(f"  [PASS] {msg}")
    for msg in result.warnings:
        print(f"  [WARN] {msg}")
    for msg in result.fails:
        print(f"  [FAIL] {msg}")
    status = "CLEAN" if result.clean else f"{len(result.fails)} FAILURE(S)"
    print(f"  --> {status}")


def main() -> None:
    args = sys.argv[1:]
    if not args or args == ["--all-canonical"]:
        folders = CANONICAL_FOLDERS
    else:
        folders = args

    results_root = ROOT / "results"
    all_results = []
    for folder in folders:
        exp_dir = results_root / folder if not Path(folder).is_absolute() else Path(folder)
        if not exp_dir.exists():
            print(f"\n[SKIP] {folder}: directory not found")
            continue
        result = audit_folder(exp_dir)
        print_report(result)
        all_results.append(result)

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    total_fails = sum(len(r.fails) for r in all_results)
    for r in all_results:
        status = "CLEAN" if r.clean else f"{len(r.fails)} failures"
        print(f"  {r.folder}: {status}")
    print(f"\nTotal failures across all folders: {total_fails}")
    sys.exit(1 if total_fails else 0)


if __name__ == "__main__":
    main()
