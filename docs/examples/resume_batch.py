"""A sequential, local batch that verifies saved results before skipping work."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .common import write_json

ALGORITHM_VERSION = "weighted-square-v1"


def fingerprint(value: int, multiplier: int) -> str:
    """Identify the input and all result-affecting parameters of this toy task."""
    encoded = json.dumps([ALGORITHM_VERSION, value, multiplier]).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_batch(
    output_dir: Path,
    values: list[int],
    multiplier: int = 2,
    fail_at: int | None = None,
) -> dict[str, Any]:
    """Execute integer tasks, skip verified results and record durable completion.

    Args:
        output_dir: Dedicated directory for this example's outputs and manifest.
        values: Synthetic task inputs in a stable order.
        multiplier: An integer parameter that changes the output.
        fail_at: Zero-based task index to fail before writing its result.

    Returns:
        Indices of executed and skipped tasks, plus an optional failed task.

    Raises:
        ValueError: Manifest structure is unsupported or inputs are not integers.

    Only one process may write this directory. This is not a distributed queue.
    """
    if type(multiplier) is not int or any(type(value) is not int for value in values):
        raise ValueError("Task values and multiplier must be integers")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest = {"version": 1, "completed": {}}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("version") != 1 or not isinstance(manifest.get("completed"), dict):
            raise ValueError("Unsupported manifest; use a new example output directory")
    executed: list[int] = []
    skipped: list[int] = []
    for index, value in enumerate(values):
        key = str(index)
        identity = fingerprint(value, multiplier)
        result_path = output_dir / f"task-{index}.json"
        expected = {"fingerprint": identity, "value": multiplier * value * value}
        valid_output = False
        if manifest["completed"].get(key) == identity and result_path.exists():
            try:
                valid_output = json.loads(result_path.read_text(encoding="utf-8")) == expected
            except (json.JSONDecodeError, UnicodeDecodeError):
                valid_output = False
        if valid_output:
            skipped.append(index)
            continue
        # Remove stale completion before any new attempt can fail.
        manifest["completed"].pop(key, None)
        write_json(manifest_path, manifest)
        if index == fail_at:
            return {"executed": executed, "skipped": skipped, "failed": index}
        write_json(result_path, expected)
        # Completion is persisted only after the output has been replaced successfully.
        manifest["completed"][key] = identity
        write_json(manifest_path, manifest)
        executed.append(index)
    return {"executed": executed, "skipped": skipped, "failed": None}


def main() -> None:
    """Run a local batch, optionally simulating a failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/batch"))
    parser.add_argument("--values", type=int, nargs="+", default=[2, 3, 4])
    parser.add_argument("--multiplier", type=int, default=2)
    parser.add_argument("--fail-at", type=int)
    args = parser.parse_args()
    report = run_batch(args.output_dir, args.values, args.multiplier, args.fail_at)
    print(report)
    raise SystemExit(1 if report["failed"] is not None else 0)


if __name__ == "__main__":
    main()
