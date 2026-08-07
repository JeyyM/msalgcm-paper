"""Export curated paper figures into Paper Setup/graphs/.

Sources:
  - Matplotlib summaries from comparison dashboard data (TSP/JSP/FS)
  - Combined convergence overlays (SA + TS + PSO on one instance)
  - Per-experiment charts copied from results/{experiment_id}/charts/

Run from repo root:
    python scripts/export_paper_graphs.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from optimize.api.services.comparison_dashboard import comparison_dashboard
from optimize.api.services.fs_catalog import (
    FS_ALGORITHMS,
    FS_COMPARISON_DATASETS,
    FS_EVALUATION_BUDGET,
    get_fs_batch,
    load_fs_instances,
)
from optimize.api.services.jsp_catalog import JSP_EVALUATION_BUDGET, get_jsp_batch
from optimize.api.services.results_reader import results_root
from optimize.api.services.tsp_catalog import TSP_ALGORITHMS, TSP_EVALUATION_BUDGET, get_tsp_batch
from optimize.visualization.charts import generate_experiment_charts
from optimize.visualization.paper_charts import (
    plot_combined_convergence,
    plot_fs_best_objective_bar,
    plot_gap_bar_chart,
    plot_gap_scalability,
)

ROOT = Path(__file__).resolve().parents[1]
GRAPHS_DIR = ROOT / "Paper Setup" / "graphs"

ALGORITHMS = TSP_ALGORITHMS

# Representative instances for detailed figures
TSP_CONVERGENCE_INSTANCE = "kroA100"
TSP_ROUTE_INSTANCE = "berlin52"
JSP_CONVERGENCE_INSTANCE = "ta22"
JSP_GANTT_INSTANCE = "ta22"
FS_CONVERGENCE_DATASET = "BreastEW"
FS_FEATURES_DATASET = "BreastEW"


def _load_experiment_results(experiment_dir: Path):
    import csv

    from optimize.experiments.models import ExperimentConfig, RunResult

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


def _ensure_experiment_charts(experiment_dir: Path) -> None:
    charts_dir = experiment_dir / "charts"
    required = ["convergence.png", "objective_boxplot.png", "runtime_comparison.png"]
    if charts_dir.exists() and all((charts_dir / name).exists() for name in required):
        return
    config, results = _load_experiment_results(experiment_dir)
    generate_experiment_charts(experiment_dir, results, config)


def _copy_chart(source: Path, dest_name: str, manifest: list[dict[str, str]], caption: str) -> None:
    if not source.exists():
        print(f"  skip missing: {source.name}")
        return
    dest = GRAPHS_DIR / dest_name
    shutil.copy2(source, dest)
    manifest.append({"file": dest_name, "caption": caption, "source": str(source)})
    print(f"  copied -> {dest_name}")


def _experiment_dir(results_dir: Path, batch) -> Path | None:
    if batch is None:
        return None
    path = results_dir / batch.experiment_id
    return path if path.exists() else None


def _build_fs_rows(results_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    meta_by_name = {item["name"]: item for item in load_fs_instances()}

    for dataset in FS_COMPARISON_DATASETS:
        algorithm_results: dict[str, Any] = {}
        for algorithm in FS_ALGORITHMS:
            batch = get_fs_batch(dataset, algorithm, results_dir)
            experiment_dir = _experiment_dir(results_dir, batch)
            best_objective = None
            if experiment_dir and (experiment_dir / "runs.csv").exists():
                import csv

                objectives: list[float] = []
                with (experiment_dir / "runs.csv").open(encoding="utf-8") as handle:
                    for row in csv.DictReader(handle):
                        if row.get("status") == "completed" and row.get("best_objective"):
                            objectives.append(float(row["best_objective"]))
                if objectives:
                    best_objective = min(objectives)
            algorithm_results[algorithm] = {"best_objective": best_objective}

        meta = meta_by_name.get(dataset, {})
        rows.append(
            {
                "instance": dataset,
                "problem_size": meta.get("num_features"),
                "problem_size_label": f"{meta.get('num_features', '?')} features",
                "results": algorithm_results,
            }
        )
    return rows


def main() -> None:
    results_dir = results_root()
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    dashboard = comparison_dashboard(results_dir)
    manifest: list[dict[str, str]] = []

    tsp_domain = next(item for item in dashboard["domains"] if item["id"] == "tsp")
    jsp_domain = next(item for item in dashboard["domains"] if item["id"] == "jsp")
    fs_rows = _build_fs_rows(results_dir)

    print("Generating summary charts...")
    plot_gap_bar_chart(
        tsp_domain["instances"],
        ALGORITHMS,
        GRAPHS_DIR / "tsp_gap_by_instance.png",
        title="TSP — Best gap to known optimum by instance",
    )
    manifest.append(
        {
            "file": "tsp_gap_by_instance.png",
            "caption": "Figure 1. TSP best gap to known optimum by instance (30 seeds per algorithm).",
            "source": "generated",
        }
    )

    plot_gap_scalability(
        tsp_domain["instances"],
        ALGORITHMS,
        GRAPHS_DIR / "tsp_gap_scalability.png",
        title="TSP — Gap vs problem size",
    )
    manifest.append(
        {
            "file": "tsp_gap_scalability.png",
            "caption": "Figure 2. TSP best gap vs problem size.",
            "source": "generated",
        }
    )

    plot_gap_bar_chart(
        jsp_domain["instances"],
        ALGORITHMS,
        GRAPHS_DIR / "jsp_gap_by_instance.png",
        title="JSP — Best gap to best known makespan by instance",
        ylabel="Best gap from BKS (%)",
    )
    manifest.append(
        {
            "file": "jsp_gap_by_instance.png",
            "caption": "Figure 4. JSP best gap to best known makespan by instance.",
            "source": "generated",
        }
    )

    plot_gap_scalability(
        jsp_domain["instances"],
        ALGORITHMS,
        GRAPHS_DIR / "jsp_gap_scalability.png",
        title="JSP — Gap vs problem size",
        ylabel="Best gap from BKS (%)",
    )
    manifest.append(
        {
            "file": "jsp_gap_scalability.png",
            "caption": "Figure 5. JSP best gap vs problem size.",
            "source": "generated",
        }
    )

    plot_fs_best_objective_bar(
        fs_rows,
        FS_ALGORITHMS,
        GRAPHS_DIR / "fs_best_objective_by_dataset.png",
        title="Feature selection — Best wrapper objective by dataset",
    )
    manifest.append(
        {
            "file": "fs_best_objective_by_dataset.png",
            "caption": "Figure 7. Feature selection best wrapper objective by dataset (lower is better).",
            "source": "generated",
        }
    )

    print("Generating combined convergence charts...")
    for domain_label, instance, budget, getter, filename, caption in [
        (
            "TSP",
            TSP_CONVERGENCE_INSTANCE,
            TSP_EVALUATION_BUDGET,
            get_tsp_batch,
            "tsp_kroA100_convergence_combined.png",
            "Figure 3. Mean TSP convergence on kroA100 (100 cities, 30 seeds per algorithm).",
        ),
        (
            "JSP",
            JSP_CONVERGENCE_INSTANCE,
            JSP_EVALUATION_BUDGET,
            get_jsp_batch,
            "jsp_ta22_convergence_combined.png",
            "Figure 6. Mean JSP convergence on ta22 (20×20, 30 seeds per algorithm).",
        ),
        (
            "Feature selection",
            FS_CONVERGENCE_DATASET,
            FS_EVALUATION_BUDGET,
            get_fs_batch,
            "fs_breastew_convergence_combined.png",
            "Figure 8. Mean feature-selection convergence on BreastEW (30 seeds per algorithm).",
        ),
    ]:
        dirs: dict[str, Path] = {}
        for algorithm in ALGORITHMS:
            batch = getter(instance, algorithm, results_dir)
            experiment_dir = _experiment_dir(results_dir, batch)
            if experiment_dir is not None:
                dirs[algorithm] = experiment_dir
        if len(dirs) >= 2:
            plot_combined_convergence(
                dirs,
                budget,
                GRAPHS_DIR / filename,
                instance=instance,
                domain_label=domain_label,
            )
            manifest.append({"file": filename, "caption": caption, "source": "generated"})
            print(f"  wrote {filename}")
        else:
            print(f"  skip {filename} — insufficient experiment folders")

    print("Copying per-experiment charts...")
    copy_specs = [
        (get_tsp_batch(TSP_ROUTE_INSTANCE, "tabu_search", results_dir), "tsp_route_berlin52_ts.png", "tsp_route_best_overall.png", "Figure 9. Best TSP route on berlin52 (Tabu Search)."),
        (get_jsp_batch(JSP_GANTT_INSTANCE, "tabu_search", results_dir), "jsp_gantt_ta22_ts.png", "jsp_gantt_best_overall.png", "Figure 10. Best JSP schedule on ta22 (Tabu Search)."),
        (get_fs_batch(FS_FEATURES_DATASET, "tabu_search", results_dir), "fs_features_breastew_ts.png", "fs_selected_features_tabu_search.png", "Figure 11. Selected features on BreastEW (Tabu Search best run)."),
        (get_tsp_batch(TSP_CONVERGENCE_INSTANCE, "tabu_search", results_dir), "tsp_kroA100_boxplot.png", "objective_boxplot.png", "Figure 12. TSP objective distribution on kroA100 (Tabu Search, 30 seeds)."),
        (get_fs_batch(FS_CONVERGENCE_DATASET, "tabu_search", results_dir), "fs_breastew_boxplot.png", "objective_boxplot.png", "Figure 13. FS objective distribution on BreastEW (Tabu Search, 30 seeds)."),
    ]

    for batch, dest_name, chart_name, caption in copy_specs:
        experiment_dir = _experiment_dir(results_dir, batch)
        if experiment_dir is None:
            print(f"  skip {dest_name} — no experiment folder")
            continue
        try:
            _ensure_experiment_charts(experiment_dir)
        except Exception as exc:
            print(f"  warn: could not regenerate charts for {experiment_dir.name}: {exc}")
        _copy_chart(experiment_dir / "charts" / chart_name, dest_name, manifest, caption)

    manifest_path = GRAPHS_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    png_count = len(list(GRAPHS_DIR.glob("*.png")))
    print(f"\nDone: {png_count} PNG files in {GRAPHS_DIR}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
