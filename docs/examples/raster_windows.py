"""Compare windowed and whole-array arithmetic on a tiny synthetic raster."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.shutil import copy as copy_raster
from rasterio.transform import Affine
from rasterio.windows import Window

from .common import write_json

NODATA = -9999.0
SEED = 42


def normalized_difference(red: np.ndarray, nir: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Compute a normalized difference, retaining invalid cells as NoData.

    Args:
        red: Red-band values, with a shape matching the other arrays.
        nir: Near-infrared values in the same units as red.
        valid: Boolean mask where True means that both measurements are usable.

    Returns:
        Float32 index values; zero denominators and non-finite inputs become NoData.

    Raises:
        ValueError: Shapes differ or the validity mask is not boolean.
    """
    if red.shape != nir.shape or red.shape != valid.shape or valid.dtype != np.bool_:
        raise ValueError("Bands and boolean validity mask must have identical shapes")
    red = np.asarray(red, dtype=np.float32)
    nir = np.asarray(nir, dtype=np.float32)
    denominator = nir + red
    usable = valid & np.isfinite(red) & np.isfinite(nir) & (denominator != 0)
    result = np.full(red.shape, NODATA, dtype=np.float32)
    np.divide(nir - red, denominator, out=result, where=usable)
    result[~np.isfinite(result)] = NODATA
    return result


def create_source(path: Path, *, all_invalid: bool = False) -> None:
    """Create invented red/NIR measurements on a documented synthetic grid."""
    rng = np.random.default_rng(SEED)
    bands = rng.uniform(0.05, 0.9, (2, 67, 83)).astype("float32")
    bands[:, :4, :6] = NODATA
    bands[:, 10, 10] = 0  # Valid measurements, undefined normalized difference.
    bands[:, 11, 11] = 0.4  # A valid index value of zero must remain valid.
    if all_invalid:
        bands[:] = NODATA
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=67,
        width=83,
        count=2,
        dtype="float32",
        crs="EPSG:32631",
        transform=Affine.translation(500000, 1000) @ Affine.scale(2, -2),
        nodata=NODATA,
        tiled=True,
        blockxsize=32,
        blockysize=32,
    ) as destination:
        destination.write(bands)
        destination.set_band_description(1, "synthetic_red")
        destination.set_band_description(2, "synthetic_nir")
        destination.update_tags(DATA_ORIGIN="synthetic; no surveyed location", SEED=str(SEED))


def process_windows(source: Path, destination: Path, window_size: int = 16) -> None:
    """Process with bounded working arrays and preserve the complete input grid.

    This pointwise operation needs no halo. The temporary TIFF is converted to a COG.
    Working array size is O(window_size squared); GDAL caches are additional memory.
    """
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different files")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.stem + ".working.tif")
    if temporary.exists():
        raise FileExistsError(f"Temporary output already exists: {temporary.name}")
    try:
        with rasterio.open(source) as src:
            if src.count != 2 or src.crs is None:
                raise ValueError("Example expects two bands and an explicit CRS")
            profile = src.profile.copy()
            profile.update(count=1, dtype="float32", nodata=NODATA)
            with rasterio.open(temporary, "w", **profile) as dst:
                for row in range(0, src.height, window_size):
                    for col in range(0, src.width, window_size):
                        window = Window(
                            col,
                            row,
                            min(window_size, src.width - col),
                            min(window_size, src.height - row),
                        )
                        values = src.read((1, 2), window=window)
                        valid = np.all(src.read_masks((1, 2), window=window) > 0, axis=0)
                        dst.write(normalized_difference(*values, valid), 1, window=window)
                dst.set_band_description(1, "synthetic_normalized_difference")
                dst.update_tags(DATA_ORIGIN="synthetic; no surveyed location", SEED=str(SEED))
        copy_raster(temporary, destination, driver="COG", compress="DEFLATE", blocksize=128)
    finally:
        temporary.unlink(missing_ok=True)


def run(output_dir: Path, window_size: int = 16) -> dict[str, Any]:
    """Generate, process and independently compare a small synthetic raster."""
    source = output_dir / "synthetic-source.tif"
    destination = output_dir / "synthetic-index.tif"
    create_source(source)
    process_windows(source, destination, window_size)
    with rasterio.open(source) as src, rasterio.open(destination) as dst:
        # Whole-array reading is an oracle for this tiny fixture, not the scalable path.
        expected = normalized_difference(*src.read(), np.all(src.read_masks() > 0, axis=0))
        actual = dst.read(1)
        np.testing.assert_array_equal(actual, expected)
        if (src.crs, src.transform, src.width, src.height) != (
            dst.crs,
            dst.transform,
            dst.width,
            dst.height,
        ):
            raise AssertionError("Output grid changed")
        np.testing.assert_array_equal(dst.read_masks(1) > 0, expected != NODATA)
        if dst.tags(ns="IMAGE_STRUCTURE").get("LAYOUT") != "COG":
            raise AssertionError("Expected a COG output")
        report = {
            "seed": SEED,
            "shape": list(actual.shape),
            "window_size": window_size,
            "valid_pixels": int(np.count_nonzero(actual != NODATA)),
            "invalid_pixels": int(np.count_nonzero(actual == NODATA)),
            "whole_array_equal": True,
            "grid_preserved": True,
            "cog_layout": True,
        }
    write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    """Run the synthetic demonstration from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/raster"))
    parser.add_argument("--window-size", type=int, default=16)
    args = parser.parse_args()
    print(run(args.output_dir, args.window_size))


if __name__ == "__main__":
    main()
