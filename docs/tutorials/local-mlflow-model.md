# Package and reload a local MLflow model

[Index](../README.md) · [Article](../articles/model-artifacts-mlflow.md) · [Source](../examples/local_mlflow.py)

This example packages a tiny deterministic predictor, reloads it through MLflow, and checks its predictions. The predictor computes a weighted sum; it is not a trained model. Its purpose is to make the packaging contract visible without private weights, datasets, or services.

## Run it

From the repository root, with [uv installed](https://docs.astral.sh/uv/getting-started/installation/):

~~~text
uv sync --frozen
uv run --frozen python -m docs.examples.local_mlflow --output-dir outputs/mlflow
~~~

The locked environment includes the full MLflow package and its local database dependencies. The command explicitly selects a SQLite tracking database and a local artifact directory under the output folder, so an inherited remote tracking URI is not used.

## Understand the package

The [model source](../examples/weighted_sum_model.py) defines a PythonModel that reads two coefficients from a JSON artifact in `load_context`. Prediction expects a finite two-column array and returns its weighted sum. The source imports its own dependencies and does not depend on this repository being importable.

The logging script writes coefficients `[0.25, 0.75]`, infers an input/output signature, and records explicit MLflow and NumPy requirements. It logs the model using MLflow's models-from-code approach, then reloads the model URI and downloads the resulting package. See the official [custom Python model documentation](https://mlflow.org/docs/latest/ml/model/python_model/) for the packaging interface.

This separation is deliberate. The prediction implementation travels as source; the coefficients travel as an artifact; the signature describes the accepted interface. None of those pieces should be recovered from a developer's working directory by accident.

## Inspect the predictions

The two input rows are `[2, 6]` and `[4, 8]`. Their weighted sums are 5 and 7. `report.json` includes the expected and reloaded values and a successful equality check:

~~~json
{
  "expected": [5.0, 7.0],
  "reloaded_prediction": [5.0, 7.0],
  "prediction_equal": true
}
~~~

The output directory also contains the SQLite database, local artifacts, a downloaded package, and `package-location.json` identifying that local package. Generated paths and run identifiers stay under ignored outputs. Repeated execution creates new MLflow runs; predictions are deterministic, while timestamps, run identifiers, and package bytes need not be.

The database and artifact files serve different purposes: metadata in the database does not replace the model files. This distinction is described in MLflow's [backend-store documentation](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/).

## Verify loading outside the repository

~~~text
uv run --frozen pytest -q tests/test_examples.py -k "mlflow or model_rejects"
~~~

The integration test starts a separate Python process with isolated import-path behavior, changes its working directory to a temporary location, and loads the downloaded package. It checks the same predictions there. Other checks reject wrong input shapes and nonfinite values.

The separate process still uses the installed locked environment. This test establishes independence from project imports, not compatibility with every Python version, operating system, GPU runtime, or MLflow release. It does not demonstrate server deployment, remote authentication, registry governance, or predictive accuracy.

Model packages contain executable code. This tutorial loads only its own newly written model; the same operation should not be treated as a passive inspection of an arbitrary untrusted package.
