"""Analyze tuning results and select frozen parameters (TSP, JSP, or FS).

Generalized version of analyze_tsp_tuning.py. Supports two selection metrics:

- "mean_gap_percentage": requires a known optimum; reads gap_percentage from
  each run's solution JSON (TSP distance, JSP makespan — both domains compute
  this automatically in serialize_solution when known_optimum is resolvable).
- "mean_best_objective": no known optimum needed; reads best_objective
  directly from runs.csv (lower is better). Used for feature selection, whose
  objective is already a bounded [0,1] weighted CV-loss + reduction score.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

EXAMPLES_DIR = ROOT / "config" / "examples"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _gap_from_runs(experiment_dir: Path) -> list[float]:
    gaps: list[float] = []
    for run in _read_csv(experiment_dir / "runs.csv"):
        run_id = run["run_id"]
        solution_path = experiment_dir / "solutions" / f"{run_id}.json"
        if not solution_path.exists():
            continue
        payload = json.loads(solution_path.read_text(encoding="utf-8"))
        gap = payload.get("gap_percentage")
        if gap is not None:
            gaps.append(float(gap))
    return gaps


def _find_experiment_dir(output_root: Path, experiment_name: str) -> Path | None:
    experiments_root = output_root / "experiments"
    if not experiments_root.exists():
        return None
    matches = sorted(experiments_root.glob(f"*_{experiment_name}"))
    return matches[-1] if matches else None


def collect_tuning_rows(protocol: dict, tuning_root: Path) -> list[dict]:
    rows: list[dict] = []
    prefix = protocol.get("experiment_prefix", "tuning")
    metric = protocol.get("selection_metric", "mean_gap_percentage")

    for algorithm, algo_block in protocol["algorithms"].items():
        for config_entry in algo_block["configs"]:
            for instance in protocol["tuning_instances"]:
                experiment_name = f"{prefix}_{config_entry['id']}_{instance['name']}"
                experiment_dir = _find_experiment_dir(tuning_root, experiment_name)
                if experiment_dir is None:
                    rows.append(
                        {
                            "algorithm": algorithm,
                            "config_id": config_entry["id"],
                            "config_label": config_entry["label"],
                            "instance": instance["name"],
                            "known_optimum": instance.get("known_optimum"),
                            "status": "missing",
                        }
                    )
                    continue

                runs = _read_csv(experiment_dir / "runs.csv")
                objectives = [float(row["best_objective"]) for row in runs if row.get("best_objective")]
                runtimes = [float(row["runtime_seconds"]) for row in runs if row.get("runtime_seconds")]

                row: dict = {
                    "algorithm": algorithm,
                    "config_id": config_entry["id"],
                    "config_label": config_entry["label"],
                    "instance": instance["name"],
                    "known_optimum": instance.get("known_optimum"),
                    "experiment_dir": experiment_dir.name,
                    "status": "complete" if runs else "empty",
                    "runs": len(runs),
                    "successful_runs": sum(1 for r in runs if r.get("status") == "completed"),
                    "mean_objective": statistics.mean(objectives) if objectives else None,
                    "std_objective": statistics.pstdev(objectives) if len(objectives) > 1 else 0.0,
                    "best_objective_value": min(objectives) if objectives else None,
                    "mean_runtime_seconds": statistics.mean(runtimes) if runtimes else None,
                    "parameters": json.dumps(config_entry["params"], sort_keys=True),
                }

                if metric == "mean_gap_percentage":
                    gaps = _gap_from_runs(experiment_dir)
                    row["mean_gap_percentage"] = statistics.mean(gaps) if gaps else None
                    row["std_gap_percentage"] = statistics.pstdev(gaps) if len(gaps) > 1 else 0.0
                    row["best_gap_percentage"] = min(gaps) if gaps else None

                rows.append(row)
    return rows


def _metric_value(row: dict, metric: str) -> float | None:
    if metric == "mean_gap_percentage":
        return row.get("mean_gap_percentage")
    return row.get("mean_objective")


def _metric_std(row: dict, metric: str) -> float:
    if metric == "mean_gap_percentage":
        return row.get("std_gap_percentage") or 0.0
    return row.get("std_objective") or 0.0


def aggregate_by_config(rows: list[dict], metric: str) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        if row.get("status") != "complete" or _metric_value(row, metric) is None:
            continue
        key = (row["algorithm"], row["config_id"])
        grouped.setdefault(key, []).append(row)

    aggregates: list[dict] = []
    for (algorithm, config_id), group in sorted(grouped.items()):
        values = [float(_metric_value(item, metric)) for item in group]
        runtimes = [
            float(item["mean_runtime_seconds"]) for item in group if item.get("mean_runtime_seconds") is not None
        ]
        per_instance = {item["instance"]: _metric_value(item, metric) for item in group}
        aggregates.append(
            {
                "algorithm": algorithm,
                "config_id": config_id,
                "config_label": group[0]["config_label"],
                "instances_used": [item["instance"] for item in group],
                "instance_count": len(group),
                "aggregate_mean_metric": statistics.mean(values),
                "aggregate_std_metric": statistics.pstdev(values) if len(values) > 1 else 0.0,
                "per_instance_metric": per_instance,
                "mean_runtime_seconds": statistics.mean(runtimes) if runtimes else None,
                "parameters": group[0]["parameters"],
            }
        )

    aggregates.sort(
        key=lambda item: (
            item["aggregate_mean_metric"],
            item["aggregate_std_metric"],
            item["mean_runtime_seconds"] if item["mean_runtime_seconds"] is not None else float("inf"),
        )
    )
    return aggregates


def select_winners(aggregates: list[dict]) -> dict[str, dict]:
    winners: dict[str, dict] = {}
    for algorithm in sorted({item["algorithm"] for item in aggregates}):
        candidates = [item for item in aggregates if item["algorithm"] == algorithm]
        if candidates:
            winners[algorithm] = candidates[0]
    return winners


def write_detail_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_aggregate_csv(aggregates: list[dict], path: Path) -> None:
    flat_rows = []
    for item in aggregates:
        row = dict(item)
        row["per_instance_metric"] = json.dumps(item["per_instance_metric"])
        flat_rows.append(row)
    if not flat_rows:
        return
    fieldnames = list(flat_rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)


def apply_winners_to_comparison_configs(
    protocol: dict,
    winners: dict[str, dict],
    runs: int | None = None,
) -> list[str]:
    updated: list[str] = []
    domain_config = protocol.get("domain_config", {})
    config_prefix = protocol.get("config_prefix", "tsp")
    for path in sorted(EXAMPLES_DIR.glob(f"{config_prefix}_*_comparison.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        if payload.get("domain_config") != domain_config:
            payload["domain_config"] = dict(domain_config)
            changed = True
        if runs is not None and payload.get("runs") != runs:
            payload["runs"] = runs
            changed = True
        for algorithm, winner in winners.items():
            params = json.loads(winner["parameters"])
            if payload.get("algorithm_configs", {}).get(algorithm) != params:
                payload.setdefault("algorithm_configs", {})[algorithm] = params
                changed = True
        if changed:
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            updated.append(str(path.relative_to(ROOT)))
    return updated


def analyze(
    protocol_path: Path,
    tuning_root: Path,
    apply_configs: bool = True,
    final_runs: int | None = 30,
) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    metric = protocol.get("selection_metric", "mean_gap_percentage")
    rows = collect_tuning_rows(protocol, tuning_root)
    aggregates = aggregate_by_config(rows, metric)
    winners = select_winners(aggregates)

    tuning_root.mkdir(parents=True, exist_ok=True)
    write_detail_csv(rows, tuning_root / "tuning_results_detail.csv")
    write_aggregate_csv(aggregates, tuning_root / "tuning_results_aggregate.csv")

    selected = {
        "protocol": protocol.get("protocol_name", protocol_path.stem),
        "domain": protocol.get("domain"),
        "initial_solution": protocol.get("domain_config", {}).get("initial_solution"),
        "selection_metric": metric,
        "tie_breakers": protocol.get("tie_breakers", []),
        "winners": {
            algorithm: {
                "config_id": winner["config_id"],
                "config_label": winner["config_label"],
                "aggregate_mean_metric": winner["aggregate_mean_metric"],
                "per_instance_metric": winner["per_instance_metric"],
                "parameters": json.loads(winner["parameters"]),
            }
            for algorithm, winner in winners.items()
        },
        "all_configs_ranked": aggregates,
    }

    if apply_configs and winners:
        selected["updated_comparison_configs"] = apply_winners_to_comparison_configs(
            protocol,
            winners,
            runs=final_runs,
        )
        config_prefix = protocol.get("config_prefix", "tsp")
        canonical = ROOT / "results" / "tuning" / f"{config_prefix}_selected_parameters.json"
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text(json.dumps(selected, indent=2), encoding="utf-8")

    selected_path = tuning_root / "selected_parameters.json"
    selected_path.write_text(json.dumps(selected, indent=2), encoding="utf-8")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze tuning results (TSP/JSP/FS)")
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=ROOT / "results" / "tuning")
    parser.add_argument("--no-apply", action="store_true", help="Do not update comparison configs")
    parser.add_argument("--final-runs", type=int, default=30)
    args = parser.parse_args()

    result = analyze(
        protocol_path=args.protocol,
        tuning_root=args.input,
        apply_configs=not args.no_apply,
        final_runs=args.final_runs,
    )
    print(json.dumps(result["winners"], indent=2))
    print(f"Wrote analysis to {args.input}")


if __name__ == "__main__":
    main()
