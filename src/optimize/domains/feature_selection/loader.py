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


def _encode_labels(raw_labels: list[str]) -> np.ndarray:
    """Convert the raw 'class' column to integer labels.

    Most EW benchmark CSVs already store numeric class codes (e.g. BreastEW's
    2/4, WineEW's 1/2/3). A few OpenML sources keep the original string class
    name (e.g. ZooEW's "mammal", SonarEW's "Rock"/"Mine", IonosphereEW's "g"/"b",
    LymphographyEW's "malign_lymph"). Numeric labels are used as-is; string
    labels are label-encoded via a sorted, deterministic string->int mapping
    so the same dataset always maps to the same integer codes across runs.
    """
    try:
        return np.asarray([int(float(value)) for value in raw_labels], dtype=int)
    except ValueError:
        classes = sorted(set(raw_labels))
        mapping = {label: index for index, label in enumerate(classes)}
        return np.asarray([mapping[value] for value in raw_labels], dtype=int)


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
        raw_labels: list[str] = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(f"row width mismatch in {file_path}: {row!r}")
            feature_rows.append([float(value) for value in row[:-1]])
            raw_labels.append(row[-1])

    if not feature_rows:
        raise ValueError(f"no data rows in {file_path}")

    labels = _encode_labels(raw_labels)

    features = np.asarray(feature_rows, dtype=float)
    label_array = np.asarray(labels, dtype=int)
    return FeatureSelectionDataset(
        name=file_path.stem,
        feature_names=feature_names,
        features=features,
        labels=label_array,
    )
