"""Demonstrate preprocessing isolation on synthetic spatial regions, without training a model."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from .common import write_json

SEED = 42


def fit_statistics(values: np.ndarray, train_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Fit channel means and scales only on selected finite training pixels.

    Args:
        values: Height by width by channel array.
        train_mask: Boolean height by width region mask.

    Returns:
        Per-channel means and population standard deviations; constants use scale one.

    Raises:
        ValueError: Shapes or mask types are invalid, or training data are empty/non-finite.
    """
    if values.ndim != 3 or train_mask.shape != values.shape[:2]:
        raise ValueError("Expected a spatial array and a matching region mask")
    if train_mask.dtype != np.bool_:
        raise ValueError("Training mask must be boolean")
    train = values[train_mask]
    if train.size == 0 or not np.all(np.isfinite(train)):
        raise ValueError("Training region must contain finite observations")
    mean, scale = train.mean(axis=0), train.std(axis=0)
    return mean, np.where(scale == 0, 1.0, scale)


def make_regions() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create a fictional grid with separated train and test column ranges."""
    rng = np.random.default_rng(SEED)
    values = rng.normal(size=(24, 40, 3))
    values += np.linspace(0, 4, 40)[None, :, None]
    train = np.zeros(values.shape[:2], dtype=bool)
    test = np.zeros_like(train)
    train[:, :16] = True
    test[:, 24:] = True
    return values, train, test


def run(output_dir: Path) -> dict[str, Any]:
    """Show that perturbing held-out pixels leaves training statistics unchanged."""
    values, train, test = make_regions()
    # No test observation contributes to preprocessing statistics. The eight-column
    # gap is illustrative; it is not a claim about a real autocorrelation range.
    mean, scale = fit_statistics(values, train)
    changed = values.copy()
    changed[test] += 10000
    changed_mean, changed_scale = fit_statistics(changed, train)
    np.testing.assert_array_equal(mean, changed_mean)
    np.testing.assert_array_equal(scale, changed_scale)
    standardized = (values - mean) / scale
    np.testing.assert_allclose(standardized[train].mean(axis=0), 0, atol=1e-12)
    report = {
        "seed": SEED,
        "train_pixels": int(train.sum()),
        "test_pixels": int(test.sum()),
        "excluded_pixels": int((~(train | test)).sum()),
        "gap_columns": 8,
        "train_test_overlap": int((train & test).sum()),
        "train_mean": mean.tolist(),
        "train_scale": scale.tolist(),
        "held_out_perturbation_changes_fit": False,
        "global_mean_changes": bool(not np.allclose(values.mean((0, 1)), changed.mean((0, 1)))),
        "model_trained": False,
    }
    write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    """Run the synthetic preprocessing check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/train-only"))
    print(run(parser.parse_args().output_dir))


if __name__ == "__main__":
    main()
