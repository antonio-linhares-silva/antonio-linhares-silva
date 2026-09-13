"""Crop public AHN4 observations without changing coordinates or classifications."""

import copy
import io
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import laspy
import numpy as np
import rasterio
from PIL import Image
from pyproj import CRS
from rasterio.transform import from_bounds
from rasterio.windows import from_bounds as window_bounds

from geoai_portfolio.io import session, sha256, write_json
from geoai_portfolio.rasters import write_cog

BBOXES = {"trees": (174650, 447600, 174906, 447856), "corridor": (170880, 446000, 171020, 446600)}
OUT = Path("data/prepared/ahn")


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    dates = {key: [float("inf"), float("-inf")] for key in BBOXES}
    writers = {}
    try:
        with laspy.open("data/cache/C_39FN1.LAZ") as source:
            for name in BBOXES:
                header = copy.deepcopy(source.header)
                # Upstream header omits CRS; AHN provider documents compound EPSG:7415.
                header.add_crs(CRS.from_epsg(7415))
                writers[name] = laspy.open(
                    OUT / f"{name}.laz", mode="w", header=header, do_compress=True
                )
            for index, points in enumerate(source.chunk_iterator(2_000_000)):
                x, y = np.asarray(points.x), np.asarray(points.y)
                for name, (left, bottom, right, top) in BBOXES.items():
                    mask = (x >= left) & (x < right) & (y >= bottom) & (y < top)
                    if mask.any():
                        writers[name].write_points(points[mask])
                        dates[name][0] = min(dates[name][0], float(points.gps_time[mask].min()))
                        dates[name][1] = max(dates[name][1], float(points.gps_time[mask].max()))
                if index % 100 == 0:
                    print("LAZ chunks", index, flush=True)
    finally:
        for writer in writers.values():
            writer.close()
    for product, filename in [("dtm", "M_39FN1.zip"), ("dsm", "R_39FN1.zip")]:
        with zipfile.ZipFile(Path("data/cache") / filename) as archive:
            member = next(name for name in archive.namelist() if name.lower().endswith(".tif"))
            path = Path("data/cache") / Path(member).name
            if not path.exists():
                with archive.open(member) as stream, path.open("wb") as target:
                    import shutil

                    shutil.copyfileobj(stream, target)
        with rasterio.open(path) as source:
            for name, bbox in BBOXES.items():
                window = window_bounds(*bbox, source.transform).round_offsets().round_lengths()
                values = source.read(1, window=window, masked=True)
                write_cog(
                    OUT / f"{name}-{product}.tif",
                    values.astype("float32"),
                    source.window_transform(window),
                    "EPSG:28992",
                    -9999,
                    [f"AHN4 {product.upper()} metres NAP"],
                )
    bbox = BBOXES["trees"]
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": "2022_ortho25",
        "STYLES": "",
        "SRS": "EPSG:28992",
        "BBOX": ",".join(map(str, bbox)),
        "WIDTH": 1024,
        "HEIGHT": 1024,
        "FORMAT": "image/png",
    }
    response = session().get(
        "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0", params=params, timeout=120
    )
    response.raise_for_status()
    image = np.asarray(Image.open(io.BytesIO(response.content)).convert("RGB"))
    write_cog(
        OUT / "trees-rgb.tif",
        image.transpose(2, 0, 1),
        from_bounds(*bbox, 1024, 1024),
        "EPSG:28992",
        None,
        ["red display DN", "green display DN", "blue display DN"],
    )
    date_strings = {
        name: [
            (datetime(1980, 1, 6) + timedelta(seconds=value + 1e9 - 18)).isoformat() + "Z"
            for value in values
        ]
        for name, values in dates.items()
    }
    write_json(
        OUT / "provenance.json",
        {
            "dataset": "AHN4 original TOP tile 39FN1",
            "license": "CC0-1.0",
            "source_url": "https://basisdata.nl/hwh-ahn/ahn4/01_LAZ/C_39FN1.LAZ",
            "source_sha256": sha256(Path("data/cache/C_39FN1.LAZ")),
            "bounds": BBOXES,
            "horizontal_crs": "EPSG:28992",
            "vertical_crs": "EPSG:5709",
            "compound_crs": "EPSG:7415",
            "crs_evidence": "https://www.ahn.nl/dataroom",
            "crs_action": (
                "Original LAS header lacks CRS; assigned provider-documented CRS, no transform"
            ),
            "coordinates": "metres, original observations retained",
            "gps_utc_ranges": date_strings,
            "gps_conversion": "adjusted GPS standard time + 1e9 seconds; GPS-UTC=18 s during 2022",
            "elevation_products": {
                "method": "AHN4 original 0.5m weighted IDW DTM/DSM",
                "urls": [
                    "https://basisdata.nl/hwh-ahn/ahn4/02a_DTM_0.5m/M_39FN1.zip",
                    "https://basisdata.nl/hwh-ahn/ahn4/03a_DSM_0.5m/R_39FN1.zip",
                ],
            },
            "orthophoto": {
                "url": response.url,
                "year": 2022,
                "license": "CC-BY-4.0",
                "attribution": "Beeldmateriaal Nederland / beeldmateriaal.nl",
                "resolution_m": 0.25,
                "season": "leaf-on",
                "exact_flight_date": None,
                "processing": "WMS RGB rendering, georeferenced from explicit request grid",
            },
            "temporal_limit": "Winter 2022 LiDAR and leaf-on 2022 mosaic are not simultaneous",
            "files": {p.name: sha256(p) for p in OUT.iterdir() if p.suffix in {".tif", ".laz"}},
        },
    )
    print("Prepared AHN", date_strings, flush=True)


if __name__ == "__main__":
    prepare()
