"""Resume an interrupted experiment folder in place.

Removes artifacts from a chosen run_id onward, re-executes those runs with the
same seeds, and re-finalizes summary/statistics.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from optimize.experiments.models import ExperimentConfig, RunResult  # noqa: E402
from optimize.experiments.runner import ExperimentRunner  # noqa: E402
from optimize.storage.writer import finalize_experiment, write_run_result  # noqa: E402
from optimize.types import RunStatus, StopReason  # noqa: E402


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _load_config(experiment_dir: Path) -> ExperimentConfig:
    payload = json.loads((experiment_dir / "experiment_config.json").read_text(encoding="utf-8"))
    return ExperimentConfig.model_validate(payload["config"])


def _seed_rows(experiment_dir: Path) -> list[dict[str, str]]:
    return _read_csv(experiment_dir / "seeds.csv")


def _run_artifacts(experiment_dir: Path, run_id: str) -> list[Path]:
    return [
        experiment_dir / "convergence" / f"{run_id}.csv",
        experiment_dir / "solutions" / f"{run_id}.json",
        experiment_dir / "solutions" / f"{run_id}.live.json",
    ]


def _run_is_complete(experiment_dir: Path, run_id: str, runs_by_id: dict[str, dict[str, str]]) -> bool:
    row = runs_by_id.get(run_id)
    if row is None or row.get("status") != RunStatus.COMPLETED.value:
        return False
    solution_path = experiment_dir / "solutions" / f"{run_id}.json"
    convergence_path = experiment_dir / "convergence" / f"{run_id}.csv"
    if not solution_path.exists() or not convergence_path.exists():
        return False
    return convergence_path.stat().st_size > 100


def find_first_incomplete(experiment_dir: Path) -> str | None:
    runs_by_id = {row["run_id"]: row for row in _read_csv(experiment_dir / "runs.csv")}
    for row in _seed_rows(experiment_dir):
        run_id = row["run_id"]
        if not _run_is_complete(experiment_dir, run_id, runs_by_id):
            return run_id
    return None


def find_resume_from_completed_count(experiment_dir: Path, completed_count: int) -> str:
    """Return the first run_id to regenerate after ``completed_count`` fully finished runs."""
    seed_rows = _seed_rows(experiment_dir)
    if completed_count < 0 or completed_count >= len(seed_rows):
        raise ValueError(
            f"completed_count must be between 0 and {len(seed_rows) - 1}, got {completed_count}"
        )
    return seed_rows[completed_count]["run_id"]


def remove_run_rows(experiment_dir: Path, run_ids: set[str]) -> None:
    runs_csv = experiment_dir / "runs.csv"
    rows = _read_csv(runs_csv)
    if not rows:
        return
    kept = [row for row in rows if row["run_id"] not in run_ids]
    fieldnames = list(rows[0].keys())
    _write_csv(runs_csv, kept, fieldnames)
    for run_id in run_ids:
        for path in _run_artifacts(experiment_dir, run_id):
            path.unlink(missing_ok=True)


def load_run_result(experiment_dir: Path, row: dict[str, str]) -> RunResult:
    solution_path = experiment_dir / "solutions" / f"{row['run_id']}.json"
    best_solution = None
    if solution_path.exists():
        best_solution = json.loads(solution_path.read_text(encoding="utf-8"))
    parameters = json.loads(row["parameters"]) if row.get("parameters") else {}
    return RunResult(
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
        parameters=parameters,
        best_solution=best_solution,
        history=[],
        error_message=row.get("error_message") or None,
    )


def resume_experiment(
    experiment_dir: Path,
    from_run_id: str,
) -> None:
    config = _load_config(experiment_dir)
    seed_rows = _seed_rows(experiment_dir)
    run_order = [row["run_id"] for row in seed_rows]
    if from_run_id not in run_order:
        raise ValueError(f"Unknown run_id: {from_run_id}")

    start_index = run_order.index(from_run_id)
    redo_run_ids = run_order[start_index:]
    print(f"Regenerating {len(redo_run_ids)} runs from {from_run_id} in {experiment_dir.name}")

    remove_run_rows(experiment_dir, set(redo_run_ids))

    runner = ExperimentRunner()
    domain_config = runner._build_domain_config(config)
    seed_by_run_id = {row["run_id"]: int(row["seed"]) for row in seed_rows}

    for row in seed_rows[start_index:]:
        run_id = row["run_id"]
        algorithm_name = row["algorithm"]
        seed = seed_by_run_id[run_id]
        run_index = int(row["run_index"])
        algo_config = config.algorithm_configs.get(algorithm_name, {})

        print(f"  RUN {run_id} (seed={seed})", flush=True)
        convergence_path = experiment_dir / "convergence" / f"{run_id}.csv"
        live_solution_path = experiment_dir / "solutions" / f"{run_id}.live.json"
        from optimize.storage.writer import LiveConvergenceWriter  # noqa: WPS433

        live_writer = LiveConvergenceWriter(convergence_path)
        try:
            result = runner.run_single(
                algorithm_name=algorithm_name,
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

    rows = _read_csv(experiment_dir / "runs.csv")
    seed_order = {row["run_id"]: index for index, row in enumerate(seed_rows)}
    rows.sort(key=lambda item: seed_order[item["run_id"]])
    fieldnames = list(rows[0].keys())
    _write_csv(experiment_dir / "runs.csv", rows, fieldnames)

    results = [load_run_result(experiment_dir, row) for row in rows]
    finalize_experiment(experiment_dir, results, config)
    print(f"Resume complete: {experiment_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume an interrupted experiment in place")
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        required=True,
        help="Existing experiment directory under results/",
    )
    parser.add_argument(
        "--from-run-id",
        type=str,
        default=None,
        help="First run_id to regenerate (inclusive). Default: first incomplete run.",
    )
    parser.add_argument(
        "--after-completed-count",
        type=int,
        default=None,
        help="Regenerate from the first run after this many fully completed runs (e.g. 68 -> run #69).",
    )
    args = parser.parse_args()

    experiment_dir = args.experiment_dir.resolve()
    if not experiment_dir.exists():
        raise SystemExit(f"Experiment directory not found: {experiment_dir}")

    if args.from_run_id:
        from_run_id = args.from_run_id
    elif args.after_completed_count is not None:
        from_run_id = find_resume_from_completed_count(experiment_dir, args.after_completed_count)
    else:
        from_run_id = find_first_incomplete(experiment_dir)
        if from_run_id is None:
            raise SystemExit(
                "All runs look complete. Pass --from-run-id or --after-completed-count "
                "to regenerate from a specific boundary run."
            )

    resume_experiment(experiment_dir, from_run_id)


if __name__ == "__main__":
    main()
