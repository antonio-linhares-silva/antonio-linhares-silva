"""Build and install a wheel in a separate environment outside the checkout."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import rasterio

from .io import sha256
from .rasters import scene_ndvi


def verify_wheel(checkout: Path, satellite: Path, output: Path):
    uv = os.environ.get("UV_EXE") or shutil.which("uv")
    if uv is None:
        raise FileNotFoundError("Install uv or set UV_EXE to the uv executable")
    checkout, satellite, output = [Path(p).resolve() for p in (checkout, satellite, output)]
    output.mkdir(parents=True, exist_ok=True)

    def run(command, cwd):
        return subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=900,
            env={**os.environ, "UV_LINK_MODE": "copy"},
        )

    with tempfile.TemporaryDirectory(prefix="geoai-wheel-") as temporary:
        external = Path(temporary)
        wheel_dir = external / "wheels"
        run([uv, "build", "--wheel", "--out-dir", str(wheel_dir)], checkout)
        wheel = next(wheel_dir.glob("*.whl"))
        requirements = external / "requirements.txt"
        run(
            [
                uv,
                "export",
                "--frozen",
                "--no-dev",
                "--no-hashes",
                "--no-emit-project",
                "--output-file",
                str(requirements),
            ],
            checkout,
        )
        environment = external / "environment"
        run([uv, "venv", "--python", "3.12", str(environment)], external)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run(
            [uv, "pip", "install", "--python", str(python), "-r", str(requirements), str(wheel)],
            external,
        )
        target = output / "installed-ndvi.tif"
        result = run(
            [
                str(python),
                "-I",
                "-m",
                "geoai_portfolio.cli",
                "ndvi",
                "--scene",
                str(satellite / "before.tif"),
                "--scl",
                str(satellite / "before-scl.tif"),
                "--output",
                str(target),
            ],
            external,
        )
        with rasterio.open(target) as source:
            actual = source.read(1, masked=True)
        expected = scene_ndvi(satellite / "before.tif", satellite / "before-scl.tif")
        np.testing.assert_array_equal(actual.mask, expected.mask)
        np.testing.assert_allclose(actual.compressed(), expected.compressed(), rtol=0, atol=1e-6)
        shutil.copy2(wheel, output / wheel.name)
        return {
            "wheel": wheel.name,
            "wheel_sha256": sha256(wheel),
            "environment": "separate venv, locked base dependencies, outside checkout",
            "array_matches_reference": True,
            **json.loads(result.stdout),
        }
