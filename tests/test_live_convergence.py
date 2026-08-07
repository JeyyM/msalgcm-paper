"""Tests for incremental convergence logging during runs."""

from __future__ import annotations

import csv
from pathlib import Path

from optimize.experiments.models import HistoryRecord
from optimize.storage.writer import LiveConvergenceWriter


def test_live_convergence_writer_appends_rows(tmp_path: Path) -> None:
    path = tmp_path / "convergence" / "mock_run_001.csv"
    writer = LiveConvergenceWriter(path)
    writer.append(
        HistoryRecord(
            objective_evaluations=1,
            best_objective=10.0,
            current_objective=10.0,
            iteration=1,
        )
    )
    writer.append(
        HistoryRecord(
            objective_evaluations=2,
            best_objective=9.0,
            current_objective=9.5,
            iteration=2,
        )
    )
    writer.close()

    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 2
    assert rows[1]["best_objective"] == "9.0"
