"""Public fixtures verify real data contracts; synthetic arrays isolate edge conditions."""

import json
from pathlib import Path

import laspy
import numpy as np
import pytest
import rasterio
from affine import Affine
from rasterio.io import MemoryFile

from geoai_portfolio.io import sha256, write_json
from geoai_portfolio.lidar import coordinates, fit_catenary
from geoai_portfolio.rasters import grid, ndvi, require_same_grid, windowed_ndvi, windows
from geoai_portfolio.workflows import run_windows

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_public_fixture_integrity():
    manifest = json.loads((FIXTURES / "provenance.json").read_text())
    for name, expected in manifest["sha256"].items():
        assert sha256(FIXTURES / name) == expected


@pytest.mark.parametrize("size", [17, 32, 128])
def test_real_sentinel_ndvi_matches_independent_calibration(tmp_path, size):
    scene, scl = FIXTURES / "before.tif", FIXTURES / "before-scl.tif"
    digest = sha256(scene)
    result = windowed_ndvi(scene, scl, tmp_path / "ndvi.tif", size)
    with rasterio.open(scene) as source, rasterio.open(scl) as quality:
        raw = source.read().astype("float32")
        red, nir = raw[0] * 0.0001 - 0.1, raw[3] * 0.0001 - 0.1
        valid = (
            np.isin(quality.read(1), [4, 5, 6, 7])
            & (raw[0] != 0)
            & (raw[3] != 0)
            & (red >= 0)
            & (nir >= 0)
            & (np.abs(red + nir) >= 1e-6)
        )
        expected = (nir[valid] - red[valid]) / (nir[valid] + red[valid])
        with rasterio.open(tmp_path / "ndvi.tif") as saved:
            actual = saved.read(1, masked=True)
            assert grid(saved) == grid(source)
            np.testing.assert_array_equal(np.ma.getmaskarray(actual), ~valid)
            np.testing.assert_allclose(actual.compressed(), expected, atol=1e-6, rtol=0)
            assert saved.tags(ns="IMAGE_STRUCTURE")["LAYOUT"] == "COG"
    assert sha256(scene) == digest
    assert result["valid_pixels"] == int(valid.sum())


def test_grid_rejects_half_pixel_shift():
    with rasterio.open(FIXTURES / "before.tif") as source, MemoryFile() as memory:
        profile = source.profile.copy()
        profile["transform"] = source.transform @ Affine.translation(0.5, 0)
        with memory.open(**profile) as shifted:
            with pytest.raises(ValueError, match="Grid mismatch"):
                require_same_grid(source, shifted)


def test_index_keeps_valid_zero_and_masks_invalid_physics():
    actual = ndvi(
        np.array([0.2, 0, -0.1, np.nan, 0.1]),
        np.array([0.2, 0, 0.3, 0.2, 0.2]),
        valid=[True, True, True, True, False],
    )
    assert actual[0] == 0
    np.testing.assert_array_equal(actual.mask, [False, True, True, True, True])


def test_partial_windows_cover_every_pixel_once():
    coverage = np.zeros((37, 53), dtype=int)
    for window in windows(53, 37, 16):
        row, col = int(window.row_off), int(window.col_off)
        coverage[row : row + int(window.height), col : col + int(window.width)] += 1
    assert np.all(coverage == 1)
    with pytest.raises(ValueError, match="positive"):
        list(windows(53, 37, 0))


def test_real_batch_failure_corruption_and_parameter_invalidation(tmp_path):
    scene, scl = FIXTURES / "before.tif", FIXTURES / "before-scl.tif"
    first = run_windows(scene, scl, tmp_path, size=32, fail_at=2)
    assert first == {"executed": [0, 1], "skipped": [], "failed": 2}
    assert run_windows(scene, scl, tmp_path, size=32)["skipped"] == [0, 1]
    (tmp_path / "window-001.json").write_text("corrupted")
    assert run_windows(scene, scl, tmp_path, size=32)["executed"] == [1]
    assert run_windows(scene, scl, tmp_path, size=32, threshold=0.9)["executed"] == [0, 1, 2, 3]


def test_real_batch_invalidates_changed_input(tmp_path):
    scene = tmp_path / "input.tif"
    scene.write_bytes((FIXTURES / "before.tif").read_bytes())
    scl = FIXTURES / "before-scl.tif"
    batch = tmp_path / "batch"
    run_windows(scene, scl, batch, size=32)
    with rasterio.open(scene, "r+", IGNORE_COG_LAYOUT_BREAK="YES") as source:
        source.update_tags(test_identity="changed")
    assert run_windows(scene, scl, batch, size=32)["executed"] == [0, 1, 2, 3]


def test_atomic_json_failure_preserves_previous_value(tmp_path):
    target = tmp_path / "manifest.json"
    write_json(target, {"complete": True})
    with pytest.raises(ValueError):
        write_json(target, {"invalid": float("nan")})
    assert json.loads(target.read_text()) == {"complete": True}
    assert list(tmp_path.glob("*.tmp")) == []


def test_public_lidar_preserves_crs_coordinates_and_classification():
    cloud = laspy.read(FIXTURES / "conductors.laz")
    assert cloud.header.parse_crs().to_epsg() == 7415
    assert np.all(np.asarray(cloud.classification) == 14)
    xyz = coordinates(cloud)
    assert np.all((xyz[:, 2] > 0) & (xyz[:, 2] < 100))
    np.testing.assert_array_equal(xyz[:, 0], np.asarray(cloud.x))


def test_catenary_retains_observations_and_rejects_insufficient_support():
    along = np.linspace(-100, 100, 101)
    points = np.column_stack(
        [np.full_like(along, 170000), 446000 + along, 700 * (np.cosh(along / 700) - 1) + 25]
    )
    original = points.copy()
    fitted = fit_catenary(points)
    np.testing.assert_array_equal(points, original)
    assert fitted["rmse_m"] < 1e-5
    assert fitted["generated"][:, 1].min() >= points[:, 1].min() - 1e-8
    assert fitted["generated"][:, 1].max() <= points[:, 1].max() + 1e-8
    with pytest.raises(ValueError, match="20 XYZ"):
        fit_catenary(points[:5])
