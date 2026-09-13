"""A shared public-data adapter and spatially held-out classical experiments."""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class EuroSAT:
    images: np.ndarray
    samples: pd.DataFrame
    bands: list[str]

    @classmethod
    def load(cls, directory: Path):
        with np.load(directory / "chips.npz", allow_pickle=False) as archive:
            images = archive["images"]
            labels = archive["labels"]
        samples = pd.read_csv(directory / "samples.csv")
        if not np.array_equal(labels, samples.label) or len(images) != len(samples):
            raise ValueError("Image/label order mismatch")
        provenance = json.loads((directory / "provenance.json").read_text())
        return cls(images, samples, provenance["bands"])

    def mask(self, split: str):
        if split not in {"train", "val", "test"}:
            raise ValueError("Unknown split")
        return self.samples.split.eq(split).to_numpy()

    @property
    def classes(self):
        return self.samples.sort_values("label")["class"].drop_duplicates().tolist()

    def features(self, bands: list[str]) -> pd.DataFrame:
        """Chip summaries; original DN / 10,000, not calibrated C1 reflectance."""
        indices = [self.bands.index(band) for band in bands]
        # Process one chip at a time: avoid a large quantile temporary across all chips.
        result = []
        for image in self.images:
            pixels = image[indices].reshape(len(indices), -1).astype("float32") / 10000
            result.append(
                np.concatenate(
                    [pixels.mean(1), pixels.std(1), *np.quantile(pixels, [0.1, 0.5, 0.9], axis=1)]
                )
            )
        names = [
            f"{band}_{stat}" for stat in ["mean", "std", "p10", "p50", "p90"] for band in bands
        ]
        return pd.DataFrame(result, columns=names)


def fit_forest(dataset: EuroSAT, features: pd.DataFrame, seed: int = 42):
    """Fixed hyperparameters; scaler fits inside the training-only pipeline."""
    model = make_pipeline(
        StandardScaler(),
        RandomForestClassifier(
            n_estimators=160, min_samples_leaf=2, max_features="sqrt", random_state=seed, n_jobs=4
        ),
    )
    train = dataset.mask("train")
    model.fit(features.loc[train], dataset.samples.loc[train, "label"])
    return model


def report(dataset: EuroSAT, predicted, split="test"):
    truth = dataset.samples.loc[dataset.mask(split), "label"]
    return pd.DataFrame(
        classification_report(
            truth,
            predicted,
            labels=list(range(len(dataset.classes))),
            target_names=dataset.classes,
            output_dict=True,
            zero_division=0,
        )
    ).T


def scores(truth, predicted):
    return {
        "accuracy": accuracy_score(truth, predicted),
        "macro_f1": f1_score(
            truth, predicted, labels=list(range(10)), average="macro", zero_division=0
        ),
    }


def group_bootstrap(truth, predicted, groups, repetitions=300, seed=42):
    """Resample 100 km spatial groups, keeping all chips within each selected group."""
    truth, predicted, groups = map(np.asarray, (truth, predicted, groups))
    unique = np.unique(groups)
    if len(unique) < 2:
        raise ValueError("At least two spatial groups are required")
    rng = np.random.default_rng(seed)
    results = []
    for _ in range(repetitions):
        chosen = rng.choice(unique, len(unique), replace=True)
        indices = np.concatenate([np.flatnonzero(groups == group) for group in chosen])
        results.append(scores(truth[indices], predicted[indices]))
    intervals = pd.DataFrame(results).quantile([0.025, 0.5, 0.975]).T
    intervals.columns = ["2.5%", "median", "97.5%"]
    return intervals
