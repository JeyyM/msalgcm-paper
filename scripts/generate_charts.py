"""Regenerate charts for an existing experiment directory."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from optimize.experiments.models import ExperimentConfig, RunResult
from optimize.visualization.charts import generate_experiment_charts


def load_results(experiment_dir: Path) -> tuple[ExperimentConfig, list[RunResult]]:
    config_payload = json.loads((experiment_dir / "experiment_config.json").read_text(encoding="utf-8"))
    config = ExperimentConfig.model_validate(config_payload["config"])

    results: list[RunResult] = []
    with (experiment_dir / "runs.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            solution_path = experiment_dir / "solutions" / f"{row['run_id']}.json"
            solution = (
                json.loads(solution_path.read_text(encoding="utf-8"))
                if solution_path.exists()
                else None
            )
            results.append(
                RunResult(
                    experiment_name=row["experiment_name"],
                    run_id=row["run_id"],
                    algorithm=row["algorithm"],
                    domain=row["domain"],
                    instance=row["instance"],
                    seed=int(row["seed"]),
                    status=row["status"],
                    stop_reason=row["stop_reason"],
                    initial_objective=float(row["initial_objective"]),
                    best_objective=float(row["best_objective"]),
                    final_objective=float(row["final_objective"]),
                    runtime_seconds=float(row["runtime_seconds"]),
                    objective_evaluations=int(row["objective_evaluations"]),
                    iterations=int(row["iterations"]),
                    parameters=json.loads(row["parameters"]),
                    best_solution=solution,
                    history=[],
                )
            )

    return config, results


def main() -> None:
    experiment_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "results/2026-08-02_235730_tsp_eil51_comparison")
    config, results = load_results(experiment_dir)
    paths = generate_experiment_charts(experiment_dir, results, config)
    print(f"Generated {len(paths)} charts in {experiment_dir / 'charts'}")
    for path in paths:
        print(f"  - {path.name}")


if __name__ == "__main__":
    main()
