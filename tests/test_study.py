"""Tests for multi-instance study and scalability charts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimize.experiments.study import StudyRunner, build_scalability_summary, load_study_config

matplotlib = pytest.importorskip("matplotlib")


def test_load_study_config() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_study_config(root / "config/examples/tsp_scalability_smoke.json")
    assert config.study_name == "tsp_scalability_smoke"
    assert len(config.experiments) == 2
    assert config.experiments[0].problem_size == 51


def test_scalability_study_smoke(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    study_config = tmp_path / "study.json"
    study_config.write_text(
        json.dumps(
            {
                "study_name": "test_scalability",
                "output_directory": str(tmp_path / "results"),
                "experiments": [
                    {
                        "config": str(root / "config/examples/tsp_eil51_smoke.json"),
                        "instance": "eil51",
                        "problem_size": 51,
                    },
                    {
                        "config": str(root / "config/examples/tsp_st70_smoke.json"),
                        "instance": "st70",
                        "problem_size": 70,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    study_dir = StudyRunner().run(study_config)
    assert (study_dir / "scalability_summary.csv").exists()
    assert (study_dir / "study_manifest.json").exists()
    assert (study_dir / "charts" / "scalability_gap.png").exists()
    assert (study_dir / "charts" / "scalability_mean_gap.png").exists()
    assert (study_dir / "charts" / "scalability_best_objective.png").exists()

    manifest = json.loads((study_dir / "study_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["experiments"]) == 2
    assert len(manifest["charts"]) == 3


def test_build_scalability_summary_from_existing_run() -> None:
    root = Path(__file__).resolve().parents[1]
    experiment_dir = root / "results/2026-08-03_000444_tsp_eil51_comparison"
    if not experiment_dir.exists():
        pytest.skip("reference experiment output not available")

    from optimize.experiments.study import StudyExperiment, StudyConfig

    study_config = StudyConfig(
        study_name="reference",
        output_directory="results",
        experiments=[
            StudyExperiment(
                config_path=Path("config/examples/tsp_eil51_comparison.json"),
                instance="eil51",
                problem_size=51,
            )
        ],
    )
    rows = build_scalability_summary(study_config, [(study_config.experiments[0], experiment_dir)])
    assert len(rows) == 3
    assert all(row["instance"] == "eil51" for row in rows)
