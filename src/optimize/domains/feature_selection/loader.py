"""Load equal-width (EW) feature-selection benchmark CSV files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class FeatureSelectionDataset:
    name: str
    feature_names: tuple[str, ...]
    features: np.ndarray
    labels: np.ndarray

    @property
    def num_features(self) -> int:
        return self.features.shape[1]

    @property
    def num_samples(self) -> int:
        return self.features.shape[0]

    @property
    def num_classes(self) -> int:
        return len(np.unique(self.labels))


def load_ew_dataset(path: str | Path) -> FeatureSelectionDataset:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"feature-selection dataset not found: {file_path}")

    with file_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if len(header) < 2 or header[-1] != "class":
            raise ValueError(f"expected EW CSV with final 'class' column: {file_path}")

        feature_names = tuple(header[:-1])
        feature_rows: list[list[float]] = []
        labels: list[int] = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(f"row width mismatch in {file_path}: {row!r}")
            feature_rows.append([float(value) for value in row[:-1]])
            labels.append(int(float(row[-1])))

    if not feature_rows:
        raise ValueError(f"no data rows in {file_path}")

    features = np.asarray(feature_rows, dtype=float)
    label_array = np.asarray(labels, dtype=int)
    return FeatureSelectionDataset(
        name=file_path.stem,
        feature_names=feature_names,
        features=features,
        labels=label_array,
    )
