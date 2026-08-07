"""Run protocol-v2 reruns as fast as possible (parallel, no charts).

Reruns invalidated by the PSO initializer fix and FS objective v2:
  - TSP: particle_swarm on all 6 TSPLIB instances (3 tuning + 3 held-out)
  - FS:  all 3 algorithms on 4 comparison datasets (12 jobs)

Hand this script to whoever is running the reruns on a machine with the full repo.

Usage (from repo root):
    python scripts/rerun_protocol_fix_experiments.py
    python scripts/rerun_protocol_fix_experiments.py --tsp-only
    python scripts/rerun_protocol_fix_experiments.py --tsp-only --tsp-instances eil51 berlin52 st70
    python scripts/rerun_protocol_fix_experiments.py --fs-only
    python scripts/rerun_protocol_fix_experiments.py --workers 4
    python scripts/rerun_protocol_fix_experiments.py --dry-run

Requirements:
    pip install -e ".[ml,viz,web]"
    datasets/ present (same as original experiments)

Output:
    results/{timestamp}_tsp_{instance}_particle_swarm/   (6 folders)
    results/{timestamp}_fs_{dataset}_{algorithm}/       (12 folders)
    results/.launch_logs_protocol_reruns.log

Charts are skipped during the run (OPTIMIZE_SKIP_CHARTS=1). Regenerate later:
    python scripts/generate_charts.py results/<experiment_folder>
"""

from __future__ import annotations

import argparse
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

FS_ALGORITHMS = [
    "simulated_annealing",
    "tabu_search",
    "particle_swarm",
]


@dataclass(frozen=True)
class Job:
    domain: str  # "tsp" | "fs"
    instance: str
    algorithm: str

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
) -> list[Job]:
    jobs: list[Job] = []
    if run_tsp:
        jobs.extend(
            Job(domain="tsp", instance=instance, algorithm=TSP_ALGORITHM)
            for instance in tsp_instances
        )
    if run_fs:
        jobs.extend(
            Job(domain="fs", instance=dataset, algorithm=algorithm)
            for dataset in FS_COMPARISON_DATASETS
            for algorithm in FS_ALGORITHMS
        )
    return jobs


def _run_one_job(job: Job) -> JobResult:
    """Worker entry point — must be top-level for Windows multiprocessing."""
    os.environ["OPTIMIZE_SKIP_CHARTS"] = "1"
    sys.path.insert(0, str(ROOT / "src"))
    start = time.perf_counter()
    try:
        from optimize.experiments.runner import ExperimentRunner

        runner = ExperimentRunner()
        if job.domain == "tsp":
            from optimize.api.services.tsp_catalog import prepare_tsp_launch, write_tsp_config_file

            prepare_tsp_launch(job.instance, job.algorithm)
            config_path = write_tsp_config_file(job.instance, job.algorithm)
        elif job.domain == "fs":
            from optimize.api.services.fs_catalog import prepare_fs_launch, write_fs_config_file

            prepare_fs_launch(job.instance, job.algorithm)
            config_path = write_fs_config_file(job.instance, job.algorithm)
        else:
            raise ValueError(f"unknown domain: {job.domain}")

        result_dir = runner.run(config_path)
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
    parser.add_argument("--fs-only", action="store_true", help="FS comparison only (12 jobs)")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Parallel jobs (default: min(job count, CPU count))",
    )
    args = parser.parse_args()

    if args.tsp_only and args.fs_only:
        parser.error("use at most one of --tsp-only and --fs-only")

    run_tsp = not args.fs_only
    run_fs = not args.tsp_only

    tsp_instances = list(args.tsp_instances)
    unknown = [name for name in tsp_instances if name not in TSP_PSO_INSTANCES]
    if unknown:
        parser.error(f"unknown tsp instances: {unknown} (valid: {TSP_PSO_INSTANCES})")

    jobs = _build_jobs(run_tsp=run_tsp, run_fs=run_fs, tsp_instances=tsp_instances)
    if not jobs:
        parser.error("no jobs selected")

    workers = args.workers if args.workers is not None else min(len(jobs), os.cpu_count() or 4)
    workers = max(1, min(workers, len(jobs)))

    _log("=== protocol-v2 reruns ===")
    _log(f"jobs={len(jobs)} workers={workers} skip_charts=1")
    _log(f"tsp={run_tsp} fs={run_fs}")

    if args.dry_run:
        for job in jobs:
            _log(f"DRY RUN would launch {job.label}")
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

    _log("All reruns complete. Regenerate charts later if needed:")
    _log("  python scripts/generate_charts.py results/<experiment_folder>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
