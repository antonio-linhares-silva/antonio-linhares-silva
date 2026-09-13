"""Rebuild small Sentinel-2 C1 L2A and ESA WorldCover packs from public COGs."""

import json
import os
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds

from geoai_portfolio.io import download, session, sha256, write_json
from geoai_portfolio.rasters import write_cog

ITEMS = {"before": "S2A_T10TFK_20200812T185701_L2A", "after": "S2A_T10TFK_20210827T185458_L2A"}
OUT = Path("data/prepared/satellite")
OUT.mkdir(parents=True, exist_ok=True)


def raster_source(url, checksum=None):
    """Avoid a Windows GDAL/libcurl shutdown hang by caching source COGs locally.

    Normal notebooks fetch only the small release pack. Unix maintainers retain
    range-based remote reads; Windows rebuilds need additional source-cache space.
    """
    if os.name != "nt":
        return url
    relative = url.split("/")[-2:]
    path = Path("data/cache/satellite-sources") / "-".join(relative)
    expected = checksum[4:] if checksum and checksum.startswith("1220") else None
    return download(url, path, expected)


def prepare():
    client = session()
    provenance = []
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        GDAL_HTTP_MAX_RETRY="4",
        GDAL_HTTP_RETRY_DELAY="2",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    ):
        for date, item_id in ITEMS.items():
            url = f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-c1-l2a/items/{item_id}"
            response = client.get(url, timeout=60)
            response.raise_for_status()
            item = response.json()
            arrays, scales, offsets, sources = [], [], [], []
            for band in ["red", "green", "blue", "nir"]:
                asset = item["assets"][band]
                with rasterio.open(
                    raster_source(asset["href"], asset.get("file:checksum"))
                ) as source:
                    # Stable pixel-aligned 5.12 km crop, north of Lake Almanor.
                    x, y = rasterio.warp.transform("EPSG:4326", source.crs, [-121.085], [40.1])
                    row, col = source.index(x[0], y[0])
                    window = Window(col - 256, row - 256, 512, 512)
                    arrays.append(source.read(1, window=window))
                    affine, crs = source.window_transform(window), source.crs
                metadata = asset["raster:bands"][0]
                scales.append(metadata["scale"])
                offsets.append(metadata["offset"])
                sources.append(
                    {
                        "band": band,
                        "url": asset["href"],
                        "scale": metadata["scale"],
                        "offset": metadata["offset"],
                        "source_checksum": asset.get("file:checksum"),
                    }
                )
            path = write_cog(
                OUT / f"{date}.tif",
                np.stack(arrays),
                affine,
                crs,
                0,
                ["red", "green", "blue", "nir"],
                scales,
                offsets,
            )
            with rasterio.open(path) as reference:
                bounds = reference.bounds
            for band in ["scl", "swir22"]:
                asset = item["assets"][band]
                with rasterio.open(
                    raster_source(asset["href"], asset.get("file:checksum"))
                ) as source:
                    window = from_bounds(*bounds, source.transform)
                    if band == "scl":
                        values = source.read(
                            1, window=window, out_shape=(512, 512), resampling=Resampling.nearest
                        )
                        write_cog(OUT / f"{date}-scl.tif", values, affine, crs, 0, ["SCL"])
                    elif date == "before":
                        window = window.round_offsets().round_lengths()
                        values = source.read(1, window=window)
                        meta = asset["raster:bands"][0]
                        write_cog(
                            OUT / "swir20m.tif",
                            values,
                            source.window_transform(window),
                            crs,
                            0,
                            ["B12"],
                            [meta["scale"]],
                            [meta["offset"]],
                        )
                sources.append(
                    {
                        "band": band,
                        "url": asset["href"],
                        "resampling": "nearest" if band == "scl" else "native",
                    }
                )
            props = item["properties"]
            provenance.append(
                {
                    "id": item_id,
                    "metadata_url": url,
                    "datetime": props["datetime"],
                    "processing_baseline": props["s2:processing_baseline"],
                    "sun_elevation": props["view:sun_elevation"],
                    "sun_azimuth": props["view:sun_azimuth"],
                    "scene_cloud_percent": props["eo:cloud_cover"],
                    "assets": sources,
                    "bounds": list(bounds),
                    "crs": str(crs),
                }
            )
            print(date, item_id, flush=True)
        url = (
            "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
            "ESA_WorldCover_10m_2021_v200_N39W123_Map.tif"
        )
        with rasterio.open(raster_source(url)) as source:
            native_bounds = transform_bounds(crs, source.crs, *bounds, densify_pts=21)
            window = from_bounds(*native_bounds, source.transform).round_offsets().round_lengths()
            values = source.read(1, window=window)
            write_cog(
                OUT / "worldcover.tif",
                values,
                source.window_transform(window),
                source.crs,
                0,
                ["ESA WorldCover 2021 v200 class"],
            )
        write_json(
            OUT / "provenance.json",
            {
                "sentinel": provenance,
                "worldcover": {"url": url, "year": 2021, "version": "v200", "license": "CC-BY-4.0"},
                "files": {p.name: sha256(p) for p in OUT.glob("*.tif")},
            },
        )
        print(json.dumps({p.name: p.stat().st_size for p in OUT.glob("*.tif")}))


if __name__ == "__main__":
    prepare()
