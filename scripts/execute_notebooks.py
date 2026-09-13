"""Execute each notebook in its own fresh kernel and preserve reviewable outputs."""

import argparse
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbclient import NotebookClient

from geoai_portfolio.io import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def clean_text(value: str) -> str:
    for path, label in [(str(ROOT), "<checkout>"), (str(Path.home()), "<user-home>")]:
        for variant in [path, path.replace("\\", "/"), path.replace("\\", "\\\\")]:
            value = value.replace(variant, label)
    # Temporary directories in install/reload logs are execution details, not public content.
    value = re.sub(
        r"[A-Za-z]:[\\/][^\n]*?geoai-(?:reload|wheel)-[^\s'\"]+", "<temporary-directory>", value
    )
    return value


def execute(path, destination, timeout):
    notebook = nbformat.read(path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="geoai-kernel-") as temporary:
        kernel_dir = Path(temporary) / "python3"
        kernel_dir.mkdir()
        write_json(
            kernel_dir / "kernel.json",
            {
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "GeoAI Python 3.12",
                "language": "python",
            },
        )
        manager = KernelManager(
            kernel_name="python3", kernel_spec_manager=KernelSpecManager(kernel_dirs=[temporary])
        )
        client = NotebookClient(
            notebook,
            km=manager,
            timeout=timeout,
            allow_errors=False,
            resources={"metadata": {"path": str(ROOT)}},
            record_timing=True,
        )
        try:
            client.execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    for cell in notebook.cells:
        cell.metadata.pop("execution", None)  # Machine timestamps add no explanatory value.
        for output in cell.get("outputs", []):
            if "text" in output:
                output.text = clean_text(output.text)
            for key, value in output.get("data", {}).items():
                if key.startswith("text/") and isinstance(value, str):
                    output.data[key] = clean_text(value)
    notebook.metadata["geoai"]["executed"] = True
    notebook.metadata["geoai"]["execution_seconds"] = round(time.perf_counter() - started, 2)
    notebook.metadata["geoai"]["requested_device"] = os.environ.get("GEOAI_DEVICE", "auto")
    notebook.metadata.pop("widgets", None)
    destination.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, destination)
    report = {
        "notebook": path.name,
        "seconds": notebook.metadata.geoai.execution_seconds,
        "code_cells": sum(c.cell_type == "code" for c in notebook.cells),
        "png_outputs": sum(
            "image/png" in o.get("data", {}) for c in notebook.cells for o in c.get("outputs", [])
        ),
        "sha256": sha256(destination),
    }
    write_json(
        ROOT
        / "outputs"
        / "validation"
        / (path.stem + "-" + os.environ.get("GEOAI_DEVICE", "auto") + ".json"),
        report,
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--select", nargs="*", help="Numeric prefixes, e.g. 02 03")
    parser.add_argument("--output-dir", type=Path, help="Keep alternative CPU outputs outside Git")
    parser.add_argument("--timeout", type=int, default=1200)
    args = parser.parse_args()
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
    os.environ.setdefault("DO_NOT_TRACK", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTHONUTF8", "1")
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        if args.select and path.name[:2] not in args.select:
            continue
        print(f"Executing {path.name}", flush=True)
        destination = args.output_dir / path.name if args.output_dir else path
        print(json.dumps(execute(path, destination, args.timeout)), flush=True)


if __name__ == "__main__":
    main()
