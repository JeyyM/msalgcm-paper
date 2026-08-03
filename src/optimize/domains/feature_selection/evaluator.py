"""Evaluate feature subsets with k-NN and stratified cross-validation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from optimize.domains.feature_selection.loader import FeatureSelectionDataset


def _require_sklearn():
    try:
        from sklearn.metrics import accuracy_score, f1_score
        from sklearn.model_selection import StratifiedKFold, train_test_split
        from sklearn.neighbors import KNeighborsClassifier
    except ImportError as exc:
        raise ImportError(
            "scikit-learn is required for feature selection. Install with: pip install '.[ml]'"
        ) from exc
    return KNeighborsClassifier, StratifiedKFold, train_test_split, accuracy_score, f1_score


@dataclass
class FeatureSubsetEvaluator:
    dataset: FeatureSelectionDataset
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    k_neighbors: int
    cv_folds: int
    metric: str
    cv_seed: int

    @classmethod
    def from_dataset(
        cls,
        dataset: FeatureSelectionDataset,
        *,
        test_size: float,
        split_seed: int,
        k_neighbors: int,
        cv_folds: int,
        metric: str | None = None,
    ) -> FeatureSubsetEvaluator:
        _, StratifiedKFold, train_test_split, _, _ = _require_sklearn()

        resolved_metric = metric or cls._default_metric(dataset)
        X_train, X_test, y_train, y_test = train_test_split(
            dataset.features,
            dataset.labels,
            test_size=test_size,
            random_state=split_seed,
            stratify=dataset.labels,
        )
        return cls(
            dataset=dataset,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            k_neighbors=k_neighbors,
            cv_folds=cv_folds,
            metric=resolved_metric,
            cv_seed=split_seed,
        )

    @staticmethod
    def _default_metric(dataset: FeatureSelectionDataset) -> str:
        if dataset.name == "WineEW" or dataset.num_classes > 2:
            return "macro_f1"
        return "accuracy"

    def _selected_matrix(self, mask: list[int], data: np.ndarray) -> np.ndarray:
        indices = [index for index, selected in enumerate(mask) if selected]
        if not indices:
            raise ValueError("at least one feature must be selected")
        return data[:, indices]

    def _score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        _, _, _, accuracy_score, f1_score = _require_sklearn()
        if self.metric == "macro_f1":
            return float(f1_score(y_true, y_pred, average="macro"))
        if self.metric == "accuracy":
            return float(accuracy_score(y_true, y_pred))
        raise ValueError(f"unsupported feature-selection metric: {self.metric}")

    def cross_validation_loss(self, mask: list[int]) -> float:
        KNeighborsClassifier, StratifiedKFold, _, _, _ = _require_sklearn()
        X_train = self._selected_matrix(mask, self.X_train)
        splitter = StratifiedKFold(
            n_splits=self.cv_folds,
            shuffle=True,
            random_state=self.cv_seed,
        )
        scores: list[float] = []
        for train_index, validation_index in splitter.split(X_train, self.y_train):
            model = KNeighborsClassifier(n_neighbors=self.k_neighbors)
            model.fit(X_train[train_index], self.y_train[train_index])
            predictions = model.predict(X_train[validation_index])
            scores.append(self._score(self.y_train[validation_index], predictions))
        mean_score = sum(scores) / len(scores)
        return 1.0 - mean_score

    def test_performance(self, mask: list[int]) -> float:
        KNeighborsClassifier, _, _, _, _ = _require_sklearn()
        X_train = self._selected_matrix(mask, self.X_train)
        X_test = self._selected_matrix(mask, self.X_test)
        model = KNeighborsClassifier(n_neighbors=self.k_neighbors)
        model.fit(X_train, self.y_train)
        predictions = model.predict(X_test)
        return self._score(self.y_test, predictions)

    def selected_feature_ratio(self, mask: list[int]) -> float:
        return sum(mask) / len(mask)
