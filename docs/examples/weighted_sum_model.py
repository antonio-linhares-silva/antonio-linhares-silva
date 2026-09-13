"""Self-contained model definition copied into the MLflow package as source code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mlflow
import numpy as np


class WeightedSum(mlflow.pyfunc.PythonModel):
    """A teaching model whose coefficients are loaded from a JSON artifact."""

    def load_context(self, context: Any) -> None:
        """Load the model's small local coefficient artifact."""
        payload = json.loads(Path(context.artifacts["weights"]).read_text(encoding="utf-8"))
        self.weights = np.asarray(payload["weights"], dtype=np.float64)

    def predict(self, context: Any, model_input: np.ndarray, params: Any = None) -> np.ndarray:
        """Return one weighted sum per row, rejecting incompatible or non-finite inputs."""
        values = np.asarray(model_input, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != self.weights.size:
            raise ValueError("Expected one column per coefficient")
        if not np.all(np.isfinite(values)):
            raise ValueError("Model inputs must be finite")
        return values @ self.weights


mlflow.models.set_model(WeightedSum())
