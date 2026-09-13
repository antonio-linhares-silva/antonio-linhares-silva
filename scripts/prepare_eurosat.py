"""Deterministic, class-balanced subset of TorchGeo's longitude-based EuroSAT splits."""

import hashlib
import io
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box

from geoai_portfolio.io import download, sha256, write_json

BASE = (
    "https://huggingface.co/datasets/torchgeo/eurosat/resolve/"
    "1ce6f1bfb56db63fd91b6ecc466ea67f2509774c/"
)
BANDS = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B10", "B11", "B12", "B8A"]


def prepare():
    out = Path("data/prepared/eurosat")
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)
    rows, images, split_sources = [], [], []
    with zipfile.ZipFile("data/cache/EuroSATallBands.zip") as archive:
        members = {Path(name).name: name for name in archive.namelist() if name.endswith(".tif")}
        for split, count in [("train", 200), ("val", 50), ("test", 50)]:
            name = f"eurosat-spatial-{split}.txt"
            path = download(BASE + name, Path("data/cache") / name)
            split_sources.append({"url": BASE + name, "sha256": sha256(path)})
            names = [
                Path(x.strip()).name.replace(".jpg", ".tif")
                for x in path.read_text().splitlines()
                if x.strip()
            ]
            classes = sorted({name.rsplit("_", 1)[0] for name in names})
            for label, category in enumerate(classes):
                candidates = sorted(n for n in names if n.rsplit("_", 1)[0] == category)
                chosen = rng.choice(candidates, min(count, len(candidates)), replace=False)
                for sample in sorted(chosen):
                    content = archive.read(members[sample])
                    with rasterio.open(io.BytesIO(content)) as source:
                        values = source.read()
                        if values.shape != (13, 64, 64) or source.crs is None:
                            raise ValueError(f"Unexpected EuroSAT chip: {sample}")
                        bounds = transform_bounds(source.crs, "EPSG:4326", *source.bounds)
                        images.append(values)
                        rows.append(
                            {
                                "sample": sample,
                                "label": label,
                                "class": category,
                                "split": split,
                                "longitude": (bounds[0] + bounds[2]) / 2,
                                "latitude": (bounds[1] + bounds[3]) / 2,
                                "source_crs": str(source.crs),
                                "bounds": list(source.bounds),
                                "transform": list(source.transform)[:6],
                                "sha256": hashlib.sha256(content).hexdigest(),
                                "geometry": box(*bounds),
                            }
                        )
                print(split, category, len(chosen), flush=True)
    frame = gpd.GeoDataFrame(rows, crs=4326).to_crs(3035)
    # Exclude held-out footprints within 2 km of any earlier partition footprint.
    keep = np.ones(len(frame), dtype=bool)
    audit = []
    for split, previous in [("val", ["train"]), ("test", ["train", "val"])]:
        reference = frame[frame.split.isin(previous) & keep]
        for index, row in frame[frame.split == split].iterrows():
            candidates = reference.sindex.query(row.geometry, predicate="dwithin", distance=2000)
            if len(candidates):
                keep[index] = False
                audit.append({"sample": row["sample"], "reason": "within 2 km of earlier split"})
    retained = frame.loc[keep].copy()
    counts = retained.groupby(["split", "class"]).size()
    if len(counts) != 30 or counts.min() < 30:
        raise ValueError("Insufficient classes after spatial exclusion")
    retained["spatial_group"] = (
        np.floor(retained.geometry.centroid.x / 100000).astype(int).astype(str)
        + "_"
        + np.floor(retained.geometry.centroid.y / 100000).astype(int).astype(str)
    )
    features = retained.drop(columns="geometry")
    # Structured geometry survives separately; portable metadata uses scalar/string columns.
    features["bounds"] = features["bounds"].map(str)
    features["transform"] = features["transform"].map(str)
    features.to_csv(out / "samples.csv", index=False)
    retained[["sample", "split", "class", "spatial_group", "geometry"]].to_file(
        out / "footprints.gpkg", layer="chips", driver="GPKG"
    )
    np.savez_compressed(
        out / "chips.npz",
        images=np.stack(images)[keep],
        labels=retained.label.to_numpy(dtype="int64"),
    )
    write_json(
        out / "provenance.json",
        {
            "dataset": "EuroSAT multispectral",
            "source": BASE + "EuroSATallBands.zip",
            "source_sha256": sha256(Path("data/cache/EuroSATallBands.zip")),
            "license": "MIT; contains Copernicus Sentinel data",
            "bands": BANDS,
            "stored_units": "Original EuroSAT digital numbers; no C1 L2A offset applied",
            "sampling_seed": 42,
            "split_sources": split_sources,
            "buffer_m": 2000,
            "distance_crs": "EPSG:3035",
            "excluded": audit,
            "counts": counts.reset_index(name="count").to_dict("records"),
        },
    )
    print(f"Prepared {len(retained)} chips; excluded {len(audit)}", flush=True)


if __name__ == "__main__":
    prepare()
