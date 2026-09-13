"""Sequential raster recovery with input, parameter, and output verification."""

import hashlib
import json
from pathlib import Path

import rasterio

from .io import sha256, write_json
from .rasters import scene_ndvi, windows


def run_windows(scene: Path, scl: Path, output: Path, size=128, threshold=0.4, fail_at=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    inputs = [sha256(scene), sha256(scl)]
    report = {"executed": [], "skipped": [], "failed": None}
    with rasterio.open(scene) as source:
        tasks = list(windows(source.width, source.height, size))
    for index, window in enumerate(tasks):
        identity = hashlib.sha256(
            json.dumps(
                {
                    "algorithm": "scl-ndvi-v1",
                    "inputs": inputs,
                    "threshold": threshold,
                    "window": [window.col_off, window.row_off, window.width, window.height],
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        path = output / f"window-{index:03}.json"
        saved = manifest.get(str(index), {})
        if (
            saved.get("identity") == identity
            and path.exists()
            and sha256(path) == saved.get("sha256")
        ):
            report["skipped"].append(index)
            continue
        manifest.pop(str(index), None)
        write_json(manifest_path, manifest)
        if index == fail_at:
            report["failed"] = index
            return report
        values = scene_ndvi(scene, scl, window)
        write_json(
            path,
            {
                "identity": identity,
                "window": index,
                "valid_pixels": int(values.count()),
                "mean_ndvi": float(values.mean()) if values.count() else None,
                "above_threshold": int((values > threshold).sum()) if values.count() else 0,
            },
        )
        manifest[str(index)] = {"identity": identity, "sha256": sha256(path)}
        write_json(manifest_path, manifest)
        report["executed"].append(index)
    return report
