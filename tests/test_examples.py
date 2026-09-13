"""Behavioral checks for the public synthetic demonstrations."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio

from docs.examples.common import write_json
from docs.examples.raster_windows import (
    NODATA,
    create_source,
    normalized_difference,
    process_windows,
)
from docs.examples.raster_windows import run as run_raster
from docs.examples.resume_batch import run_batch
from docs.examples.train_only import fit_statistics, make_regions
from docs.examples.train_only import run as run_train


@pytest.mark.parametrize("window_size", [7, 16, 200])
def test_raster_readback_and_partial_edges(tmp_path: Path, window_size: int) -> None:
    report = run_raster(tmp_path, window_size)
    assert report["shape"] == [67, 83]
    assert report["invalid_pixels"] == 25
    assert report["valid_pixels"] == 5536
    with rasterio.open(tmp_path / "synthetic-index.tif") as result:
        assert result.read(1)[11, 11] == 0
        assert result.read_masks(1)[11, 11] == 255
        assert result.read(1)[-1, -1] != NODATA


def test_raster_all_invalid_and_input_preserved(tmp_path: Path) -> None:
    source, target = tmp_path / "source.tif", tmp_path / "target.tif"
    create_source(source, all_invalid=True)
    before = source.read_bytes()
    process_windows(source, target, 13)
    assert source.read_bytes() == before
    with rasterio.open(target) as result:
        assert not result.read_masks(1).any()
        assert np.all(result.read(1) == NODATA)


def test_index_valid_zero_undefined_and_missing() -> None:
    red = np.array([1, 0, 1, np.nan, 2], dtype=np.float32)
    nir = np.array([1, 0, 3, 1, 4], dtype=np.float32)
    actual = normalized_difference(red, nir, np.array([True, True, True, True, False]))
    np.testing.assert_array_equal(actual, [0, NODATA, 0.5, NODATA, NODATA])


def test_raster_rejects_unsafe_or_invalid_parameters(tmp_path: Path) -> None:
    source = tmp_path / "source.tif"
    create_source(source)
    with pytest.raises(ValueError, match="different"):
        process_windows(source, source)
    with pytest.raises(ValueError, match="positive"):
        process_windows(source, tmp_path / "out.tif", 0)


def test_train_regions_and_held_out_perturbation(tmp_path: Path) -> None:
    values, train, test = make_regions()
    assert not (train & test).any()
    assert not (train | test)[:, 16:24].any()
    assert values.shape == (24, 40, 3)
    report = run_train(tmp_path)
    assert report["train_pixels"] == report["test_pixels"] == 384
    assert report["excluded_pixels"] == 192
    assert report["held_out_perturbation_changes_fit"] is False
    assert report["global_mean_changes"] is True


def test_constant_features_have_defined_scale() -> None:
    values = np.full((2, 3, 2), 5.0)
    mean, scale = fit_statistics(values, np.ones((2, 3), dtype=bool))
    np.testing.assert_array_equal(mean, [5, 5])
    np.testing.assert_array_equal(scale, [1, 1])


def test_empty_or_nonfinite_train_rejected_but_test_is_not_read() -> None:
    values, train, test = make_regions()
    with pytest.raises(ValueError, match="finite"):
        fit_statistics(values, np.zeros_like(train))
    values[test] = np.nan
    fit_statistics(values, train)
    values[train] = np.nan
    with pytest.raises(ValueError, match="finite"):
        fit_statistics(values, train)


def test_preprocessing_shapes_and_mask_types() -> None:
    values, train, _ = make_regions()
    with pytest.raises(ValueError, match="matching"):
        fit_statistics(values, train[:-1])
    with pytest.raises(ValueError, match="boolean"):
        fit_statistics(values, train.astype(int))


def test_batch_failure_resume_and_no_duplicate_work(tmp_path: Path) -> None:
    assert run_batch(tmp_path, [2, 3, 4], fail_at=1) == {
        "executed": [0],
        "skipped": [],
        "failed": 1,
    }
    assert not (tmp_path / "task-1.json").exists()
    assert run_batch(tmp_path, [2, 3, 4]) == {
        "executed": [1, 2],
        "skipped": [0],
        "failed": None,
    }
    before = (tmp_path / "task-0.json").read_bytes()
    assert run_batch(tmp_path, [2, 3, 4])["executed"] == []
    assert (tmp_path / "task-0.json").read_bytes() == before


def test_batch_changed_input_and_parameter_invalidate(tmp_path: Path) -> None:
    run_batch(tmp_path, [2, 3, 4])
    assert run_batch(tmp_path, [7, 3, 4])["executed"] == [0]
    assert run_batch(tmp_path, [7, 3, 4], multiplier=3)["executed"] == [0, 1, 2]
    assert json.loads((tmp_path / "task-0.json").read_text(encoding="utf-8"))["value"] == 147


@pytest.mark.parametrize("damage", ["missing", "malformed", "wrong-result", "orphan"])
def test_batch_reconciles_artifact_and_manifest(tmp_path: Path, damage: str) -> None:
    run_batch(tmp_path, [2, 3])
    output = tmp_path / "task-0.json"
    if damage == "missing":
        output.unlink()
    elif damage == "malformed":
        output.write_text("{broken", encoding="utf-8")
    elif damage == "wrong-result":
        payload = json.loads(output.read_text(encoding="utf-8"))
        payload["value"] = -100
        write_json(output, payload)
    else:
        payload = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        payload["completed"].pop("0")
        write_json(tmp_path / "manifest.json", payload)
    assert run_batch(tmp_path, [2, 3])["executed"] == [0]
    assert json.loads(output.read_text(encoding="utf-8"))["value"] == 8


def test_batch_failed_replacement_drops_stale_completion(tmp_path: Path) -> None:
    run_batch(tmp_path, [2])
    assert run_batch(tmp_path, [3], fail_at=0)["failed"] == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert "0" not in manifest["completed"]


def test_empty_batch_and_bad_manifest(tmp_path: Path) -> None:
    assert run_batch(tmp_path, []) == {"executed": [], "skipped": [], "failed": None}
    write_json(tmp_path / "manifest.json", {"version": 2, "completed": {}})
    with pytest.raises(ValueError, match="Unsupported"):
        run_batch(tmp_path, [1])


def test_json_failed_serialization_keeps_previous_document(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    write_json(path, {"ok": 1})
    before = path.read_bytes()
    with pytest.raises(ValueError):
        write_json(path, {"bad": float("nan")})
    assert path.read_bytes() == before
    assert not list(tmp_path.glob(".pending-*"))


def test_mlflow_package_loads_outside_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MLFLOW_DISABLE_AGENT_HINT", "1")
    monkeypatch.setenv("GIT_PYTHON_REFRESH", "quiet")
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    from docs.examples.local_mlflow import run

    assert run(tmp_path)["prediction_equal"] is True
    package = json.loads((tmp_path / "package-location.json").read_text(encoding="utf-8"))["path"]
    program = (
        "import sys, mlflow.pyfunc, numpy as np; "
        "model=mlflow.pyfunc.load_model(sys.argv[1]); "
        "np.testing.assert_array_equal("
        "model.predict(np.array([[2.,6.],[4.,8.]])), [5.,7.]); "
        "print('isolated-package-ok')"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", program, package],
        cwd=tmp_path,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "isolated-package-ok" in result.stdout


def test_model_rejects_wrong_shape_and_nonfinite() -> None:
    from docs.examples.weighted_sum_model import WeightedSum

    model = WeightedSum()
    model.weights = np.array([0.25, 0.75])
    with pytest.raises(ValueError, match="column"):
        model.predict(None, np.ones((2, 3)))
    with pytest.raises(ValueError, match="finite"):
        model.predict(None, np.array([[1, np.inf]]))
