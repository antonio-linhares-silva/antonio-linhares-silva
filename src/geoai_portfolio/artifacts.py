"""Local MLflow model packages with an explicit table schema and fresh-process check."""

import importlib.metadata
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from .io import write_json


def log_forest(model, features, labels, output: Path, provenance: dict):
    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature

    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri("sqlite:///" + (output / "tracking.db").as_posix())
    experiment = mlflow.get_experiment_by_name("public-eurosat")
    experiment_id = (
        experiment.experiment_id
        if experiment
        else mlflow.create_experiment(
            "public-eurosat", artifact_location=(output / "artifacts").as_uri()
        )
    )
    with mlflow.start_run(experiment_id=experiment_id) as run:
        package = output / run.info.run_id / "model"
        example = features.iloc[:5]
        prediction = model.predict(example)
        mlflow.sklearn.save_model(
            model,
            package,
            signature=infer_signature(example, prediction),
            input_example=example,
            pip_requirements=[
                f"{name}=={importlib.metadata.version(name)}"
                for name in ["mlflow", "scikit-learn", "numpy", "pandas", "cloudpickle"]
            ],
        )
        write_json(
            package / "feature_schema.json",
            {
                "columns": features.columns.tolist(),
                "dtypes": features.dtypes.astype(str).to_dict(),
                "units": "EuroSAT DN / 10000 chip summaries",
                "split": "train-only fit",
                **provenance,
            },
        )
        mlflow.log_params(
            {
                "estimator": "RandomForestClassifier",
                "n_features": features.shape[1],
                "n_training_chips": len(features),
                "random_seed": 42,
            }
        )
        mlflow.log_dict(provenance, "data_provenance.json")
        mlflow.log_artifacts(str(package), artifact_path="model")
        mlflow.set_tag("evaluation_scope", "demonstration; spatially held-out EuroSAT subset")
    return package


def predict_table(model_dir: Path, table: pd.DataFrame):
    import json

    import mlflow.pyfunc

    schema = json.loads((Path(model_dir) / "feature_schema.json").read_text())
    if table.columns.tolist() != schema["columns"]:
        raise ValueError("Feature names and order must match the saved schema")
    if not np.isfinite(table.to_numpy()).all():
        raise ValueError("Features must be finite")
    return mlflow.pyfunc.load_model(str(model_dir)).predict(table)


def reload_in_fresh_process(model_dir: Path, table: pd.DataFrame):
    """Fresh Python interpreter, isolated flags, temporary cwd, no checkout imports."""
    code = (
        "import sys,mlflow.pyfunc,pandas as pd,numpy as np; "
        "model=mlflow.pyfunc.load_model(sys.argv[1]); "
        "x=pd.read_csv(sys.argv[2]); np.save(sys.argv[3],model.predict(x))"
    )
    with tempfile.TemporaryDirectory(prefix="geoai-reload-") as temporary:
        base = Path(temporary)
        table.to_csv(base / "input.csv", index=False)
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                code,
                str(model_dir.resolve()),
                str(base / "input.csv"),
                str(base / "predictions.npy"),
            ],
            cwd=base,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
        return np.load(base / "predictions.npy", allow_pickle=False)
