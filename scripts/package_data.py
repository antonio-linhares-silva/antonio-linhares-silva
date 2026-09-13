"""Build deterministic, attributed release packs and small public CI fixtures."""

import json
import shutil
import zipfile
from pathlib import Path

import laspy
import numpy as np
import rasterio
from rasterio.windows import Window

from geoai_portfolio.io import sha256, write_json
from geoai_portfolio.rasters import write_cog

RELEASE = "public-data-v1"
URL = (
    f"https://github.com/antonio-linhares-silva/antonio-linhares-silva/releases/download/{RELEASE}/"
)


def package():
    release_dir = Path("outputs/releases")
    release_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"version": 1, "release": RELEASE, "packs": {}}
    for name in ["satellite", "eurosat", "ahn"]:
        directory = Path("data/prepared") / name
        if name == "eurosat":
            (directory / "licenses").mkdir(exist_ok=True)
            for licence in Path("data/licenses").glob("*.txt"):
                shutil.copy2(licence, directory / "licenses" / licence.name)
        paths = sorted(p for p in directory.rglob("*") if p.is_file())
        attribution = {
            "satellite": "Contains modified Copernicus Sentinel data (2020, 2021). "
            "ESA WorldCover 2021 v200, CC BY 4.0, ESA WorldCover consortium.",
            "eurosat": "EuroSAT by Patrick Helber et al., MIT, contains Copernicus "
            "Sentinel data. Spatial splits by TorchGeo contributors, MIT.",
            "ahn": "AHN4, CC0 1.0. Orthophoto: Beeldmateriaal Nederland / "
            "beeldmateriaal.nl, 2022, CC BY 4.0.",
        }[name]
        write_json(
            directory / "ATTRIBUTION.json",
            {
                "attribution": attribution,
                "documentation": "https://github.com/antonio-linhares-silva/"
                "antonio-linhares-silva/blob/main/docs/DATA_SOURCES.md",
            },
        )
        paths = sorted(p for p in directory.rglob("*") if p.is_file())
        archive = release_dir / f"{name}.zip"
        with zipfile.ZipFile(
            archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as bundle:
            for path in paths:
                info = zipfile.ZipInfo(
                    path.relative_to(directory).as_posix(), (2026, 9, 13, 0, 0, 0)
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, path.read_bytes())
        manifest["packs"][name] = {
            "url": URL + archive.name,
            "sha256": sha256(archive),
            "bytes": archive.stat().st_size,
            "attribution": attribution,
            "files": {p.relative_to(directory).as_posix(): sha256(p) for p in paths},
        }
    write_json(Path("data/manifest.json"), manifest)
    fixtures = Path("data/fixtures")
    fixtures.mkdir(parents=True, exist_ok=True)
    for name in ["before.tif", "before-scl.tif"]:
        with rasterio.open(Path("data/prepared/satellite") / name) as source:
            window = Window(64, 64, 64, 64)
            write_cog(
                fixtures / name,
                source.read(window=window, masked=True),
                source.window_transform(window),
                source.crs,
                source.nodata,
                source.descriptions,
                source.scales,
                source.offsets,
            )
    points = laspy.read("data/prepared/ahn/corridor.laz")
    selected = np.flatnonzero(np.asarray(points.classification) == 14)[::10]
    small = laspy.LasData(points.header)
    small.points = points.points[selected].copy()
    small.write(fixtures / "conductors.laz")
    write_json(
        fixtures / "provenance.json",
        {
            "satellite": "64x64 pixel crop from satellite pack, pixel offset (64,64)",
            "lidar": (
                "Every tenth class-14 observation from AHN corridor pack; coordinates unchanged"
            ),
            "source_manifest": "../manifest.json",
            "license_documentation": "../../docs/DATA_SOURCES.md",
            "sha256": {
                p.name: sha256(p) for p in fixtures.iterdir() if p.suffix in {".tif", ".laz"}
            },
        },
    )
    print(json.dumps({name: value["bytes"] for name, value in manifest["packs"].items()}))


if __name__ == "__main__":
    package()
