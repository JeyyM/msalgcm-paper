"""Run protocol-v2 reruns as fast as possible (parallel, no charts).

Reruns invalidated by the PSO initializer fix and FS objective v2:
  - TSP: particle_swarm on all 6 TSPLIB instances (3 tuning + 3 held-out)
  - FS:  all 3 algorithms on comparison datasets (default: fast trio, 15 runs)

Hand this script to whoever is running the reruns on a machine with the full repo.

Usage (from repo root):
    python scripts/rerun_protocol_fix_experiments.py --tsp-only
    python scripts/rerun_protocol_fix_experiments.py --fs-only
    python scripts/rerun_protocol_fix_experiments.py --fs-only --workers 3
    python scripts/rerun_protocol_fix_experiments.py --fs-only --fs-extend-to 30
    python scripts/rerun_protocol_fix_experiments.py --dry-run

Requirements:
    pip install -e ".[ml,viz,web]"
    datasets/ present (same as original experiments)

Output:
    results/{timestamp}_fs_{dataset}_{algorithm}/
    results/.launch_logs_protocol_reruns.log

Charts are skipped during the run (OPTIMIZE_SKIP_CHARTS=1). Regenerate later:
    python scripts/generate_charts.py results/<experiment_folder>
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "results" / ".launch_logs_protocol_reruns.log"

TSP_PSO_INSTANCES = [
    "eil51",
    "berlin52",
    "st70",
    "kroA100",
    "ch130",
    "rat195",
]

TSP_ALGORITHM = "particle_swarm"

FS_COMPARISON_DATASETS = [
    "BreastEW",
    "WineEW",
    "LymphographyEW",
    "SpectEW",
]

# Smaller comparison sets — skip BreastEW (569×30) for survival runs.
FS_FAST_DATASETS = [
    "WineEW",
    "LymphographyEW",
    "SpectEW",
]

FS_ALGORITHMS = [
    "simulated_annealing",
    "tabu_search",
    "particle_swarm",
]

FS_ALGO_SHORT = {
    "simulated_annealing": "SA",
    "tabu_search": "TS",
    "particle_swarm": "PSO",
}

DEFAULT_FS_RUNS = 15


@dataclass(frozen=True)
class Job:
    domain: str  # "tsp" | "fs"
    instance: str
    algorithm: str
    fs_runs: int = DEFAULT_FS_RUNS
    fs_extend_to: int | None = None

    @property
    def label(self) -> str:
        return f"{self.domain}_{self.instance}_{self.algorithm}"


@dataclass
class JobResult:
    job: Job
    ok: bool
    result_dir: str | None
    elapsed_seconds: float
    error: str | None = None


def _build_jobs(
    *,
    run_tsp: bool,
    run_fs: bool,
    tsp_instances: list[str],
    fs_datasets: list[str],
    fs_runs: int,
    fs_extend_to: int | None,
) -> list[Job]:
    jobs: list[Job] = []
    if run_tsp:
        jobs.extend(
            Job(domain="tsp", instance=instance, algorithm=TSP_ALGORITHM)
            for instance in tsp_instances
        )
    if run_fs:
        jobs.extend(
            Job(
                domain="fs",
                instance=dataset,
                algorithm=algorithm,
                fs_runs=fs_runs,
                fs_extend_to=fs_extend_to,
            )
            for dataset in fs_datasets
            for algorithm in FS_ALGORITHMS
        )
    return jobs


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _append_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _load_run_result_from_row(experiment_dir: Path, row: dict[str, str]):
    from optimize.experiments.models import RunResult
    from optimize.types import RunStatus, StopReason

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


def _is_protocol_v2_config(config: dict) -> bool:
    domain_config = config.get("domain_config") or {}
    if not domain_config.get("standardize_features"):
        return False
    performance = domain_config.get("performance_weight")
    reduction = domain_config.get("reduction_weight")
    return performance == 0.99 and reduction == 0.01


def _fs_experiment_dirs(instance: str, algorithm: str) -> list[Path]:
    expected_suffix = f"_fs_{instance.lower()}_{algorithm}"
    results_dir = ROOT / "results"
    if not results_dir.exists():
        return []
    return sorted(
        (path for path in results_dir.iterdir() if path.is_dir() and path.name.endswith(expected_suffix)),
        key=lambda path: path.name,
    )


def _batch_counts(experiment_dir: Path) -> tuple[int, int, int, bool]:
    config_path = experiment_dir / "experiment_config.json"
    if not config_path.exists():
        return 0, 0, 0, False
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    config = payload.get("config", {})
    if not _is_protocol_v2_config(config):
        return 0, 0, 0, False
    seeds = len(_read_csv(experiment_dir / "seeds.csv"))
    completed = sum(
        1 for row in _read_csv(experiment_dir / "runs.csv") if row.get("status") == "completed"
    )
    config_runs = int(config.get("runs") or 0)
    return seeds, completed, config_runs, True


def _find_protocol_v2_batch(instance: str, algorithm: str, *, target_runs: int) -> Path | None:
    """Newest protocol-v2 folder whose config targets ``target_runs``."""
    candidates: list[tuple[str, Path]] = []
    for experiment_dir in _fs_experiment_dirs(instance, algorithm):
        seeds, _completed, config_runs, is_v2 = _batch_counts(experiment_dir)
        if not is_v2 or config_runs != target_runs or seeds != target_runs:
            continue
        candidates.append((experiment_dir.name, experiment_dir))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _find_extend_batch(instance: str, algorithm: str, *, initial_runs: int) -> Path | None:
    """Protocol-v2 batch with exactly ``initial_runs`` completed (ready to extend)."""
    candidates: list[tuple[str, Path]] = []
    for experiment_dir in _fs_experiment_dirs(instance, algorithm):
        seeds, completed, config_runs, is_v2 = _batch_counts(experiment_dir)
        if not is_v2:
            continue
        if seeds == initial_runs and completed == initial_runs and config_runs == initial_runs:
            candidates.append((experiment_dir.name, experiment_dir))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _make_fs_progress_printer(job: Job, *, baseline_completed: int = 0):
    algo_label = FS_ALGO_SHORT.get(job.algorithm, job.algorithm)
    target_runs = job.fs_extend_to or job.fs_runs
    last_completed = baseline_completed

    def _print_progress(completed_runs: int, phase: str) -> None:
        line = f"[{job.instance} | {algo_label}] {completed_runs}/{target_runs} {phase}"
        print(line, flush=True)
        _log(line)

    def progress_callback(progress) -> None:
        nonlocal last_completed
        completed = progress.completed_runs + baseline_completed
        if completed > last_completed:
            last_completed = completed
            _print_progress(completed, "done")

    return progress_callback, lambda: _print_progress(baseline_completed, "starting")


def _continue_fs_experiment(job: Job, experiment_dir: Path) -> JobResult:
    """Run only missing/incomplete seeds — no artifact deletion (Windows-safe)."""
    sys.path.insert(0, str(ROOT / "src"))
    start = time.perf_counter()
    try:
        from optimize.experiments.models import ExperimentConfig
        from optimize.experiments.runner import ExperimentRunner
        from optimize.storage.writer import LiveConvergenceWriter, finalize_experiment, write_run_result

        payload = json.loads((experiment_dir / "experiment_config.json").read_text(encoding="utf-8"))
        config = ExperimentConfig.model_validate(payload["config"])
        seed_rows = _read_csv(experiment_dir / "seeds.csv")
        runs_by_id = {row["run_id"]: row for row in _read_csv(experiment_dir / "runs.csv")}

        _seeds, baseline_completed, target_runs, _ = _batch_counts(experiment_dir)
        progress_callback, print_start = _make_fs_progress_printer(job, baseline_completed=baseline_completed)
        print_start()

        runner = ExperimentRunner()
        domain_config = runner._build_domain_config(config)

        for row in seed_rows:
            run_id = row["run_id"]
            if runs_by_id.get(run_id, {}).get("status") == "completed":
                continue

            algorithm_name = row["algorithm"]
            seed = int(row["seed"])
            algo_config = config.algorithm_configs.get(algorithm_name, {})
            convergence_path = experiment_dir / "convergence" / f"{run_id}.csv"
            live_solution_path = experiment_dir / "solutions" / f"{run_id}.live.json"
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

            completed_now = sum(
                1
                for item in _read_csv(experiment_dir / "runs.csv")
                if item.get("status") == "completed"
            )
            line = f"[{job.instance} | {FS_ALGO_SHORT[job.algorithm]}] {completed_now}/{target_runs} done"
            print(line, flush=True)
            _log(line)

        rows = _read_csv(experiment_dir / "runs.csv")
        seed_order = {item["run_id"]: index for index, item in enumerate(seed_rows)}
        rows.sort(key=lambda item: seed_order[item["run_id"]])
        fieldnames = list(rows[0].keys())
        with (experiment_dir / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        results = [_load_run_result_from_row(experiment_dir, row) for row in rows]
        finalize_experiment(experiment_dir, results, config)

        return JobResult(
            job=job,
            ok=True,
            result_dir=str(experiment_dir),
            elapsed_seconds=time.perf_counter() - start,
        )
    except Exception as exc:  # noqa: BLE001
        return JobResult(
            job=job,
            ok=False,
            result_dir=None,
            elapsed_seconds=time.perf_counter() - start,
            error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        )


def _resume_fs_experiment(job: Job, experiment_dir: Path) -> JobResult:
    _seeds, completed, config_runs, _ = _batch_counts(experiment_dir)
    if completed >= config_runs:
        _log(f"SKIP resume {job.label}: already {completed}/{config_runs}")
        return JobResult(
            job=job,
            ok=True,
            result_dir=str(experiment_dir),
            elapsed_seconds=0.0,
        )
    return _continue_fs_experiment(job, experiment_dir)


def _extend_fs_experiment(job: Job) -> JobResult:
    """Append runs to an existing FS batch (e.g. 15 -> 30)."""
    sys.path.insert(0, str(ROOT / "src"))
    start = time.perf_counter()
    target_runs = job.fs_extend_to
    if target_runs is None:
        raise ValueError("fs_extend_to is required for extend mode")

    try:
        from optimize.experiments.aggregate import build_seed_rows
        from optimize.experiments.models import ExperimentConfig
        from optimize.experiments.runner import ExperimentRunner
        from optimize.experiments.seed_manager import SeedManager
        from optimize.storage.writer import LiveConvergenceWriter, finalize_experiment, write_run_result

        experiment_dir = _find_extend_batch(job.instance, job.algorithm, initial_runs=job.fs_runs)
        if experiment_dir is None:
            raise FileNotFoundError(
                f"no completed {job.fs_runs}-run protocol-v2 batch for "
                f"{job.instance} {job.algorithm} — finish the initial runs first"
            )
        payload = json.loads((experiment_dir / "experiment_config.json").read_text(encoding="utf-8"))
        config = ExperimentConfig.model_validate(payload["config"])

        seed_rows = _read_csv(experiment_dir / "seeds.csv")
        completed_rows = [row for row in _read_csv(experiment_dir / "runs.csv") if row.get("status") == "completed"]
        current_runs = len(seed_rows)
        completed_count = len(completed_rows)

        if completed_count < current_runs:
            raise RuntimeError(
                f"batch incomplete ({completed_count}/{current_runs}) — resume before extending"
            )
        if current_runs >= target_runs:
            _log(f"SKIP extend {job.label}: already at {current_runs}/{target_runs}")
            return JobResult(
                job=job,
                ok=True,
                result_dir=str(experiment_dir),
                elapsed_seconds=time.perf_counter() - start,
            )

        all_seeds = SeedManager(config.seed_policy.base_seed).generate(target_runs)
        all_seed_rows = build_seed_rows(config, all_seeds)
        append_rows = all_seed_rows[current_runs:]

        _append_csv_rows(
            experiment_dir / "seeds.csv",
            append_rows,
            ["run_id", "algorithm", "seed", "run_index"],
        )

        config.runs = target_runs
        payload["config"] = config.model_dump()
        (experiment_dir / "experiment_config.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

        runner = ExperimentRunner()
        domain_config = runner._build_domain_config(config)
        algo_config = config.algorithm_configs.get(job.algorithm, {})

        for row in append_rows:
            run_id = row["run_id"]
            seed = int(row["seed"])

            convergence_path = experiment_dir / "convergence" / f"{run_id}.csv"
            live_solution_path = experiment_dir / "solutions" / f"{run_id}.live.json"
            live_writer = LiveConvergenceWriter(convergence_path)
            try:
                result = runner.run_single(
                    algorithm_name=job.algorithm,
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

            completed_now = len(_read_csv(experiment_dir / "runs.csv"))
            line = f"[{job.instance} | {FS_ALGO_SHORT[job.algorithm]}] {completed_now}/{target_runs} done"
            print(line, flush=True)
            _log(line)

        rows = _read_csv(experiment_dir / "runs.csv")
        seed_order = {row["run_id"]: index for index, row in enumerate(_read_csv(experiment_dir / "seeds.csv"))}
        rows.sort(key=lambda item: seed_order[item["run_id"]])
        fieldnames = list(rows[0].keys())
        with (experiment_dir / "runs.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        results = [_load_run_result_from_row(experiment_dir, row) for row in rows]
        finalize_experiment(experiment_dir, results, config)

        return JobResult(
            job=job,
            ok=True,
            result_dir=str(experiment_dir),
            elapsed_seconds=time.perf_counter() - start,
        )
    except Exception as exc:  # noqa: BLE001
        return JobResult(
            job=job,
            ok=False,
            result_dir=None,
            elapsed_seconds=time.perf_counter() - start,
            error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        )


def _run_one_job(job: Job) -> JobResult:
    """Worker entry point — must be top-level for Windows multiprocessing."""
    os.environ["OPTIMIZE_SKIP_CHARTS"] = "1"
    sys.path.insert(0, str(ROOT / "src"))
    start = time.perf_counter()

    if job.domain == "fs" and job.fs_extend_to is not None:
        return _extend_fs_experiment(job)

    try:
        from optimize.experiments.progress import RunProgress
        from optimize.experiments.runner import ExperimentRunner

        runner = ExperimentRunner()
        progress_callback = None
        print_start = None

        if job.domain == "tsp":
            from optimize.api.services.tsp_catalog import prepare_tsp_launch, write_tsp_config_file

            prepare_tsp_launch(job.instance, job.algorithm)
            config_path = write_tsp_config_file(job.instance, job.algorithm)
        elif job.domain == "fs":
            from optimize.api.services.fs_catalog import prepare_fs_launch, write_fs_config_file

            existing = _find_protocol_v2_batch(job.instance, job.algorithm, target_runs=job.fs_runs)
            if existing is not None:
                seeds, completed, config_runs, _ = _batch_counts(existing)
                if completed >= config_runs:
                    _log(f"SKIP {job.label}: already {completed}/{config_runs} at {existing.name}")
                    return JobResult(
                        job=job,
                        ok=True,
                        result_dir=str(existing),
                        elapsed_seconds=time.perf_counter() - start,
                    )
                if completed > 0:
                    return _resume_fs_experiment(job, existing)

            prepare_fs_launch(job.instance, job.algorithm)
            config_path = write_fs_config_file(job.instance, job.algorithm, runs=job.fs_runs)
            progress_callback, print_start = _make_fs_progress_printer(job)
            print_start()
        else:
            raise ValueError(f"unknown domain: {job.domain}")

        def on_progress(progress: RunProgress) -> None:
            if progress_callback is not None:
                progress_callback(progress)

        result_dir = runner.run(config_path, progress_callback=on_progress)
        return JobResult(
            job=job,
            ok=True,
            result_dir=str(result_dir),
            elapsed_seconds=time.perf_counter() - start,
        )
    except Exception as exc:  # noqa: BLE001
        return JobResult(
            job=job,
            ok=False,
            result_dir=None,
            elapsed_seconds=time.perf_counter() - start,
            error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
        )


def _log(line: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{stamp}] {line}"
    print(message, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parallel protocol-v2 reruns (TSP PSO + FS comparison).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan only")
    parser.add_argument("--tsp-only", action="store_true", help="TSP PSO only (6 jobs)")
    parser.add_argument(
        "--tsp-instances",
        nargs="*",
        default=TSP_PSO_INSTANCES,
        metavar="INSTANCE",
        help="TSP subset when using --tsp-only (default: all six)",
    )
    parser.add_argument("--fs-only", action="store_true", help="FS comparison only")
    parser.add_argument(
        "--fs-datasets",
        nargs="*",
        default=FS_FAST_DATASETS,
        help=f"FS datasets (default: fast trio {FS_FAST_DATASETS})",
    )
    parser.add_argument(
        "--fs-runs",
        type=int,
        default=DEFAULT_FS_RUNS,
        help=f"Independent FS runs per algorithm (default: {DEFAULT_FS_RUNS})",
    )
    parser.add_argument(
        "--fs-extend-to",
        type=int,
        default=None,
        metavar="N",
        help="Append runs on existing FS batches up to N total (e.g. 30 after an initial 15)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Parallel jobs (default: min(job count, CPU count))",
    )
    args = parser.parse_args()

    if args.tsp_only and args.fs_only:
        parser.error("use at most one of --tsp-only and --fs-only")
    if args.fs_runs <= 0:
        parser.error("--fs-runs must be positive")
    if args.fs_extend_to is not None and args.fs_extend_to <= args.fs_runs:
        parser.error("--fs-extend-to must be greater than --fs-runs")

    run_tsp = not args.fs_only
    run_fs = not args.tsp_only

    tsp_instances = list(args.tsp_instances)
    unknown_tsp = [name for name in tsp_instances if name not in TSP_PSO_INSTANCES]
    if unknown_tsp:
        parser.error(f"unknown tsp instances: {unknown_tsp} (valid: {TSP_PSO_INSTANCES})")

    fs_datasets = list(args.fs_datasets)
    unknown_fs = [name for name in fs_datasets if name not in FS_COMPARISON_DATASETS]
    if unknown_fs:
        parser.error(f"unknown fs datasets: {unknown_fs} (valid: {FS_COMPARISON_DATASETS})")

    jobs = _build_jobs(
        run_tsp=run_tsp,
        run_fs=run_fs,
        tsp_instances=tsp_instances,
        fs_datasets=fs_datasets,
        fs_runs=args.fs_runs,
        fs_extend_to=args.fs_extend_to,
    )
    if not jobs:
        parser.error("no jobs selected")

    workers = args.workers if args.workers is not None else min(len(jobs), os.cpu_count() or 4)
    workers = max(1, min(workers, len(jobs)))

    _log("=== protocol-v2 reruns ===")
    _log(f"jobs={len(jobs)} workers={workers} skip_charts=1")
    _log(f"tsp={run_tsp} fs={run_fs}")
    if run_fs:
        mode = f"extend_to={args.fs_extend_to}" if args.fs_extend_to else f"runs={args.fs_runs}"
        _log(f"fs_datasets={fs_datasets} {mode}")

    if args.dry_run:
        for job in jobs:
            if job.fs_extend_to:
                _log(f"DRY RUN would extend {job.label} -> {job.fs_extend_to} total runs")
            else:
                suffix = f" ({job.fs_runs} runs)" if job.domain == "fs" else ""
                _log(f"DRY RUN would launch {job.label}{suffix}")
        _log("DRY RUN complete")
        return 0

    os.chdir(ROOT)
    os.environ["OPTIMIZE_SKIP_CHARTS"] = "1"
    started = time.perf_counter()
    results: list[JobResult] = []

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_run_one_job, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                outcome = future.result()
            except Exception as exc:  # noqa: BLE001
                outcome = JobResult(
                    job=job,
                    ok=False,
                    result_dir=None,
                    elapsed_seconds=0.0,
                    error=f"{type(exc).__name__}: {exc}",
                )
            results.append(outcome)
            if outcome.ok:
                _log(f"OK {job.label} -> {outcome.result_dir} ({outcome.elapsed_seconds:.1f}s)")
            else:
                _log(f"FAIL {job.label} ({outcome.elapsed_seconds:.1f}s)\n{outcome.error}")

    elapsed = time.perf_counter() - started
    ok_count = sum(1 for item in results if item.ok)
    _log(f"Finished {ok_count}/{len(jobs)} in {elapsed:.1f}s wall time")
    _log(f"Log file: {LOG_PATH}")

    if ok_count < len(jobs):
        _log("Some jobs failed — re-run failed jobs only or check errors above.")
        return 1

    if run_fs and args.fs_extend_to is None:
        _log("To add 15 more runs later (reach 30 total):")
        _log("  python scripts/rerun_protocol_fix_experiments.py --fs-only --fs-extend-to 30")

    _log("Regenerate charts later if needed:")
    _log("  python scripts/generate_charts.py results/<experiment_folder>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
