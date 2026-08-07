"""Experiment runner."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from collections.abc import Callable

from optimize.algorithms.registry import get_algorithm
from optimize.config.loader import load_experiment_config, validate_experiment_config
from optimize.domains.registry import create_problem
from optimize.experiments.budget import EvaluationBudget
from optimize.experiments.models import ExperimentConfig, RunResult
from optimize.experiments.progress import RunProgress
from optimize.experiments.seed_manager import SeedManager
from optimize.storage.writer import (
    LiveConvergenceWriter,
    finalize_experiment,
    write_environment,
    write_experiment_config,
    write_live_route_snapshot,
    write_run_result,
    write_seeds_csv,
)
from optimize.types import RunStatus, StopReason


class ExperimentRunner:
    """Orchestrates single and batch experiment execution."""

    def validate(self, config: ExperimentConfig) -> list[str]:
        return validate_experiment_config(config)

    def _build_domain_config(self, config: ExperimentConfig) -> dict[str, Any]:
        domain_config = dict(config.domain_config)
        if config.instance_path:
            domain_config["instance_path"] = config.instance_path
        domain_config.setdefault("instance", config.instance)
        if config.domain == "feature_selection":
            domain_config.setdefault("split_seed", config.seed_policy.base_seed)
        return domain_config

    def run_single(
        self,
        algorithm_name: str,
        problem_domain: str,
        instance: str,
        seed: int,
        evaluation_budget: int,
        algorithm_config: dict[str, Any] | None = None,
        domain_config: dict[str, Any] | None = None,
        experiment_name: str = "single_run",
        run_id: str | None = None,
        history_listener: Callable[[Any], None] | None = None,
        live_solution_path: Path | None = None,
    ) -> RunResult:
        budget = EvaluationBudget(evaluation_budget)
        merged_domain_config = domain_config or {}
        problem = create_problem(problem_domain, budget, merged_domain_config)
        algorithm = get_algorithm(algorithm_name)

        algo_config = dict(algorithm_config or {})
        if problem_domain in {"tsp", "scheduling", "feature_selection"} and "operators" not in algo_config:
            algo_config["operators"] = merged_domain_config.get("operators")

        start = time.perf_counter()
        status = RunStatus.COMPLETED
        error_message: str | None = None
        stop_reason = StopReason.COMPLETED
        initial_objective = float("inf")
        best_objective = float("inf")
        best_solution: dict | None = None
        history = []
        iterations = 0

        last_written_evaluations = -1
        # feature_selection's serialize_solution() re-runs a full k-fold CV plus a
        # held-out test evaluation (multiple classifier fits) on every call, unlike
        # tsp/scheduling where it's a cheap distance/makespan recomputation. Writing
        # a live snapshot every 5 evaluations there was adding a real, avoidable
        # compute tax on top of the (already budgeted) search evaluations themselves.
        live_route_interval = 5 if problem_domain != "feature_selection" else 100

        try:
            algorithm.initialize(problem, algo_config, seed)

            def combined_history_listener(record: Any) -> None:
                nonlocal last_written_evaluations
                if history_listener is not None:
                    history_listener(record)
                if live_solution_path is None:
                    return
                evals = record.objective_evaluations
                if evals <= last_written_evaluations:
                    return
                if (
                    last_written_evaluations >= 0
                    and evals - last_written_evaluations < live_route_interval
                ):
                    return
                last_written_evaluations = evals
                try:
                    write_live_route_snapshot(
                        live_solution_path,
                        problem,
                        algorithm,
                        evals,
                    )
                except OSError:
                    pass

            algorithm.set_history_listener(combined_history_listener)
            if live_solution_path is not None:
                last_written_evaluations = budget.count
                try:
                    write_live_route_snapshot(
                        live_solution_path,
                        problem,
                        algorithm,
                        budget.count,
                    )
                except OSError:
                    pass

            initial_objective = algorithm._current_objective  # noqa: SLF001
            algorithm.run()
            stop_reason = algorithm.get_stop_reason()
            best_objective = algorithm.get_best_objective()
            iterations = algorithm._iterations  # noqa: SLF001
            history = algorithm.get_history()
            solution = algorithm.get_best_solution()
            if solution is not None:
                best_solution = problem.serialize_solution(solution)
        except Exception as exc:  # noqa: BLE001
            status = RunStatus.FAILED
            stop_reason = StopReason.ERROR
            error_message = str(exc)
        finally:
            algorithm.set_history_listener(None)
            algorithm.set_solution_listener(None)
            if (
                live_solution_path is not None
                and budget.count > last_written_evaluations
            ):
                try:
                    write_live_route_snapshot(
                        live_solution_path,
                        problem,
                        algorithm,
                        budget.count,
                    )
                except OSError:
                    pass

        runtime = time.perf_counter() - start

        return RunResult(
            experiment_name=experiment_name,
            run_id=run_id or f"{algorithm_name}_seed_{seed}",
            algorithm=algorithm_name,
            domain=problem_domain,
            instance=instance,
            seed=seed,
            status=status,
            stop_reason=stop_reason,
            initial_objective=initial_objective,
            best_objective=best_objective,
            final_objective=best_objective,
            runtime_seconds=runtime,
            objective_evaluations=budget.count,
            iterations=iterations,
            parameters=algo_config,
            best_solution=best_solution,
            history=history,
            error_message=error_message,
        )

    def run(
        self,
        config_path: str | Path,
        progress_callback: Callable[[RunProgress], None] | None = None,
    ) -> Path:
        config = load_experiment_config(config_path)
        errors = self.validate(config)
        if errors:
            raise ValueError("invalid experiment config: " + "; ".join(errors))

        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
        experiment_dir = (
            Path(config.output.directory)
            / f"{timestamp}_{config.experiment_name}"
        )
        experiment_dir.mkdir(parents=True, exist_ok=True)

        seeds = SeedManager(config.seed_policy.base_seed).generate(config.runs)
        domain_config = self._build_domain_config(config)
        config_path = Path(config_path)
        total_runs = len(config.algorithms) * config.runs

        write_experiment_config(experiment_dir, config_path, config)
        write_environment(experiment_dir)
        write_seeds_csv(experiment_dir, config, seeds)

        progress = RunProgress(
            status="running",
            experiment_name=config.experiment_name,
            total_runs=total_runs,
            experiment_dir=experiment_dir.name,
            message="Starting experiment",
        )
        if progress_callback:
            progress_callback(progress)

        results: list[RunResult] = []
        completed = 0
        for algorithm_name in config.algorithms:
            algo_config = config.algorithm_configs.get(algorithm_name, {})
            for run_index, seed in enumerate(seeds, start=1):
                run_id = f"{algorithm_name}_run_{run_index:03d}"
                progress.current_algorithm = algorithm_name
                progress.current_run_index = run_index
                progress.current_run_id = run_id
                progress.message = f"Running {run_id}"
                if progress_callback:
                    progress_callback(progress)

                convergence_path = experiment_dir / "convergence" / f"{run_id}.csv"
                live_solution_path = experiment_dir / "solutions" / f"{run_id}.live.json"
                live_writer = LiveConvergenceWriter(convergence_path)
                last_progress_update = time.perf_counter()

                def history_listener(record: Any) -> None:
                    nonlocal last_progress_update
                    live_writer.append(record)
                    progress.current_best_objective = record.best_objective
                    now = time.perf_counter()
                    if progress_callback and now - last_progress_update >= 0.5:
                        last_progress_update = now
                        progress_callback(progress)

                try:
                    result = self.run_single(
                        algorithm_name=algorithm_name,
                        problem_domain=config.domain,
                        instance=config.instance,
                        seed=seed,
                        evaluation_budget=config.evaluation_budget,
                        algorithm_config=algo_config,
                        domain_config=domain_config,
                        experiment_name=config.experiment_name,
                        run_id=run_id,
                        history_listener=history_listener,
                        live_solution_path=live_solution_path,
                    )
                finally:
                    live_writer.close()
                write_run_result(result, experiment_dir)
                results.append(result)
                completed += 1
                progress.completed_runs = completed
                progress.current_best_objective = result.best_objective
                progress.log.append(
                    f"{run_id}: best={result.best_objective:.4f} status={result.status.value}"
                )
                if progress_callback:
                    progress_callback(progress)

        finalize_experiment(experiment_dir, results, config)
        progress.status = "completed"
        progress.message = "Experiment finalized"
        if progress_callback:
            progress_callback(progress)
        return experiment_dir
