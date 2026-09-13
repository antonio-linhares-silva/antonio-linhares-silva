"""Package a deterministic arithmetic model using only local MLflow storage."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import mlflow
import mlflow.pyfunc
import numpy as np
from mlflow.models import infer_signature

from .common import write_json


def run(output_dir: Path) -> dict[str, Any]:
    """Log, reload and check the model without contacting a tracking server."""
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "weights.json", {"weights": [0.25, 0.75]})
    database = output_dir / "tracking.sqlite"
    mlflow.set_tracking_uri("sqlite:///" + database.as_posix())
    experiment_name = "synthetic-model-packaging"
    experiment = mlflow.get_experiment_by_name(experiment_name)
    experiment_id = (
        experiment.experiment_id
        if experiment
        else mlflow.create_experiment(
            experiment_name,
            artifact_location=(output_dir / "artifacts").as_uri(),
        )
    )
    values = np.array([[2.0, 6.0], [4.0, 8.0]], dtype=np.float64)
    expected = np.array([5.0, 7.0])
    with mlflow.start_run(experiment_id=experiment_id):
        mlflow.log_param("purpose", "synthetic packaging demonstration; no training")
        info = mlflow.pyfunc.log_model(
            name="weighted-sum",
            python_model=str(Path(__file__).with_name("weighted_sum_model.py")),
            artifacts={"weights": str(output_dir / "weights.json")},
            signature=infer_signature(values, expected),
            input_example=values,
            pip_requirements=["mlflow==3.16.0", "numpy==2.5.3"],
        )
    model = mlflow.pyfunc.load_model(info.model_uri)
    prediction = model.predict(values)
    np.testing.assert_array_equal(prediction, expected)
    # Store the package locally for the independent-process readback test.
    package_path = mlflow.artifacts.download_artifacts(
        artifact_uri=info.model_uri,
        dst_path=str(output_dir / "downloaded"),
    )
    report = {
        "expected": expected.tolist(),
        "reloaded_prediction": prediction.tolist(),
        "prediction_equal": True,
        "model_trained": False,
        "storage": "local SQLite and files",
    }
    write_json(output_dir / "report.json", report)
    write_json(output_dir / "package-location.json", {"path": str(Path(package_path).resolve())})
    return report


def main() -> None:
    """Run the local model packaging example."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/mlflow"))
    print(run(parser.parse_args().output_dir))


if __name__ == "__main__":
    main()
