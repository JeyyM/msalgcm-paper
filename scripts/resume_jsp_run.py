"""Resume an interrupted JSP comparison batch in its existing results folder.

Usage:
    python scripts/resume_jsp_run.py <instance> <algorithm> [experiment_dir]
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from optimize.api.services.jsp_catalog import get_jsp_batch
from optimize.api.services.results_reader import results_root
from optimize.experiments.models import ExperimentConfig, RunResult
from optimize.experiments.runner import ExperimentRunner
from optimize.experiments.seed_manager import SeedManager
from optimize.storage.writer import LiveConvergenceWriter, finalize_experiment, write_run_result
from optimize.types import RunStatus, StopReason


def _load_config(experiment_dir: Path) -> ExperimentConfig:
    payload = json.loads((experiment_dir / "experiment_config.json").read_text(encoding="utf-8"))
    return ExperimentConfig.model_validate(payload["config"])


def _completed_run_count(experiment_dir: Path) -> int:
    runs_path = experiment_dir / "runs.csv"
    if not runs_path.exists():
        return 0
    with runs_path.open(encoding="utf-8") as handle:
        return sum(1 for row in csv.DictReader(handle) if row.get("status") == "completed")


def _load_results_from_csv(experiment_dir: Path) -> list[RunResult]:
    runs_path = experiment_dir / "runs.csv"
    results: list[RunResult] = []
    with runs_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            params = row.get("parameters") or "{}"
            if isinstance(params, str):
                params = json.loads(params)
            results.append(
                RunResult(
                    experiment_name=row["experiment_name"],
                    run_id=row["run_id"],
                    algorithm=row["algorithm"],
                    domain=row["domain"],
                    instance=row["instance"],
                    seed=int(row["seed"]),
                    status=RunStatus(row["status"]),
                    stop_reason=StopReason(row["stop_reason"]),
                    initial_objective=float(row["initial_objective"]),
                    best_objective=float(row["best_objective"]),
                    final_objective=float(row["final_objective"]),
                    runtime_seconds=float(row["runtime_seconds"]),
                    objective_evaluations=int(row["objective_evaluations"]),
                    iterations=int(row["iterations"]),
                    parameters=params,
                    error_message=row.get("error_message") or None,
                )
            )
    return results


def main() -> None:
    if len(sys.argv) not in {3, 4}:
        print("usage: resume_jsp_run.py <instance> <algorithm> [experiment_dir]", file=sys.stderr)
        raise SystemExit(2)

    instance, algorithm = sys.argv[1], sys.argv[2]
    if len(sys.argv) == 4:
        experiment_dir = Path(sys.argv[3])
    else:
        batch = get_jsp_batch(instance, algorithm)
        if batch is None or batch.done:
            print(f"No incomplete batch found for {instance} {algorithm}", file=sys.stderr)
            raise SystemExit(1)
        experiment_dir = results_root() / batch.experiment_id

    if not experiment_dir.exists():
        print(f"Experiment folder not found: {experiment_dir}", file=sys.stderr)
        raise SystemExit(1)

    config = _load_config(experiment_dir)
    completed = _completed_run_count(experiment_dir)
    if completed >= config.runs:
        print(f"Already complete: {completed}/{config.runs} in {experiment_dir.name}")
        return

    seeds = SeedManager(config.seed_policy.base_seed).generate(config.runs)
    domain_config = dict(config.domain_config)
    if config.instance_path:
        domain_config["instance_path"] = config.instance_path
    domain_config.setdefault("instance", config.instance)

    algo_config = dict(config.algorithm_configs.get(algorithm, {}))
    if "operators" not in algo_config:
        algo_config["operators"] = domain_config.get("operators")

    runner = ExperimentRunner()
    print(f"Resuming {experiment_dir.name}: {completed}/{config.runs} done")

    for run_index in range(completed + 1, config.runs + 1):
        seed = seeds[run_index - 1]
        run_id = f"{algorithm}_run_{run_index:03d}"
        print(f"  Running {run_id} (seed {seed})")

        convergence_path = experiment_dir / "convergence" / f"{run_id}.csv"
        live_solution_path = experiment_dir / "solutions" / f"{run_id}.live.json"
        live_writer = LiveConvergenceWriter(convergence_path)
        try:
            result = runner.run_single(
                algorithm_name=algorithm,
                problem_domain=config.domain,
                instance=config.instance,
                seed=seed,
                evaluation_budget=config.evaluation_budget,
                algorithm_config=algo_config,
                domain_config=domain_config,
                experiment_name=config.experiment_name,
                run_id=run_id,
                history_listener=live_writer.append,
                live_solution_path=live_solution_path,
            )
        finally:
            live_writer.close()
        write_run_result(result, experiment_dir)

    results = _load_results_from_csv(experiment_dir)
    finalize_experiment(experiment_dir, results, config)
    print(f"DONE {instance} {algorithm} -> {experiment_dir} ({len(results)}/{config.runs})")


if __name__ == "__main__":
    main()
