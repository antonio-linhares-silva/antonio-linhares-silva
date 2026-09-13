"""Explicit grid, scale, mask, and bounded-memory raster operations."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from rasterio.windows import Window

SCL_VALID = (4, 5, 6, 7)  # vegetation, bare soil, water, unclassified (inspect visually)


def grid(dataset) -> dict:
    return {
        "crs": str(dataset.crs),
        "shape": (dataset.height, dataset.width),
        "transform": tuple(dataset.transform)[:6],
    }


def require_same_grid(*datasets) -> None:
    first = grid(datasets[0])
    if datasets[0].crs is None:
        raise ValueError("Missing CRS")
    for dataset in datasets[1:]:
        if grid(dataset) != first:
            raise ValueError("Grid mismatch: CRS, shape, or affine transform differs")


def windows(width: int, height: int, size: int = 128):
    if size <= 0:
        raise ValueError("Window size must be positive")
    for row in range(0, height, size):
        for col in range(0, width, size):
            yield Window(col, row, min(size, width - col), min(size, height - row))


def reflectance(dataset, band: int, window=None):
    raw = dataset.read(band, window=window, masked=True).astype("float32")
    return raw * dataset.scales[band - 1] + dataset.offsets[band - 1]


def ndvi(red, nir, valid=None):
    red, nir = np.ma.asarray(red), np.ma.asarray(nir)
    denominator = red + nir
    mask = (
        np.ma.getmaskarray(red)
        | np.ma.getmaskarray(nir)
        | ~np.isfinite(red.data)
        | ~np.isfinite(nir.data)
        | (np.abs(denominator.data) < 1e-6)
        | (red.data < 0)
        | (nir.data < 0)
    )
    if valid is not None:
        mask |= ~np.asarray(valid, dtype=bool)
    result = np.zeros(red.shape, dtype="float32")
    np.divide(nir.data - red.data, denominator.data, out=result, where=~mask)
    return np.ma.array(result, mask=mask)


def write_cog(
    path: Path, array, transform, crs, nodata, descriptions=None, scales=None, offsets=None
):
    array = np.ma.asarray(array)
    if array.ndim == 2:
        array = array[np.newaxis]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="COG",
        width=array.shape[2],
        height=array.shape[1],
        count=array.shape[0],
        dtype=array.dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress="DEFLATE",
        blocksize=128,
        overview_resampling="nearest",
    ) as destination:
        destination.write(array.filled(nodata))
        if descriptions:
            destination.descriptions = tuple(descriptions)
        if scales:
            destination.scales = tuple(scales)
        if offsets:
            destination.offsets = tuple(offsets)
    return path


def align(source_path: Path, reference_path: Path, categorical: bool = False):
    with rasterio.open(source_path) as source, rasterio.open(reference_path) as reference:
        destination = np.full((reference.height, reference.width), np.nan, dtype="float32")
        source_array = source.read(1, masked=True).astype("float32").filled(np.nan)
        reproject(
            source_array,
            destination,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=reference.transform,
            dst_crs=reference.crs,
            src_nodata=np.nan,
            dst_nodata=np.nan,
            resampling=Resampling.nearest if categorical else Resampling.bilinear,
        )
        return np.ma.masked_invalid(destination)


def scene_ndvi(scene: Path, scl: Path, window=None):
    with rasterio.open(scene) as source, rasterio.open(scl) as quality:
        require_same_grid(source, quality)
        classes = quality.read(1, window=window, masked=True)
        valid = np.isin(classes.data, SCL_VALID) & ~np.ma.getmaskarray(classes)
        return ndvi(reflectance(source, 1, window), reflectance(source, 4, window), valid)


def windowed_ndvi(scene: Path, scl: Path, output: Path, size: int = 128) -> dict:
    """Write tiled scratch then translate to COG; no full-scene array is allocated."""
    from rasterio.shutil import copy

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    scratch = output.with_suffix(".working.tif")
    tasks = 0
    valid_pixels = 0
    try:
        with rasterio.open(scene) as source, rasterio.open(scl) as quality:
            require_same_grid(source, quality)
            profile = source.profile.copy()
            profile.update(
                driver="GTiff",
                count=1,
                dtype="float32",
                nodata=-9999,
                tiled=True,
                blockxsize=128,
                blockysize=128,
                compress="deflate",
            )
            with rasterio.open(scratch, "w", **profile) as destination:
                for window in windows(source.width, source.height, size):
                    classes = quality.read(1, window=window, masked=True)
                    valid = np.isin(classes.data, SCL_VALID) & ~np.ma.getmaskarray(classes)
                    values = ndvi(
                        reflectance(source, 1, window), reflectance(source, 4, window), valid
                    )
                    destination.write(values.filled(-9999), 1, window=window)
                    valid_pixels += int(values.count())
                    tasks += 1
                destination.set_band_description(1, "NDVI (unitless)")
            copy(
                scratch,
                output,
                driver="COG",
                compress="DEFLATE",
                blocksize=128,
                overview_resampling="nearest",
            )
    finally:
        scratch.unlink(missing_ok=True)
    return {
        "windows": tasks,
        "valid_pixels": valid_pixels,
        "window_size": size,
        "largest_input_pixels": min(size, source.width) * min(size, source.height),
    }


def map_array(ax, values, dataset, title, cmap="viridis", vmin=None, vmax=None):
    """North-up metric raster, explicit axes; callers provide a meaningful colorbar."""
    if dataset.transform.b or dataset.transform.d:
        raise ValueError("Plot helper requires a north-up raster")
    bounds = dataset.bounds
    image = ax.imshow(
        values,
        extent=(bounds.left, bounds.right, bounds.bottom, bounds.top),
        origin="upper",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )
    ax.set(title=title, xlabel=f"Easting ({dataset.crs}; m)", ylabel="Northing (m)")
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.tick_params(labelsize=7)
    return image
