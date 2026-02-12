"""
GOAL OF THIS FILE
-----------------
Expose a trained ML model via an HTTP API.

Key principles:
- Model artifact is loaded deterministically from disk
- Requests are stateless
- Input/output are strictly validated (Pydantic)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

APP_DIR = Path(__file__).resolve().parent
MODEL_PATH = APP_DIR / "model.pkl"

app = FastAPI(title="Model Serving API", version="1.0.0")


def _load_artifact(path: Path) -> dict[str, Any]:
    """
    Supports either:
      1) a dict artifact: {"model": estimator, "target_names": [...], ...}
      2) a bare estimator saved directly via joblib.dump(model, ...)
    """
    obj = joblib.load(path)

    if isinstance(obj, dict):
        if "model" not in obj:
            raise ValueError("Artifact dict must contain a 'model' key.")
        return obj

    # Bare estimator
    return {"model": obj}


@lru_cache(maxsize=1)
def get_model_bundle() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"model.pkl not found at {MODEL_PATH}. "
            "Place model.pkl next to main.py (and include it in your Docker image)."
        )
    return _load_artifact(MODEL_PATH)


def _expected_n_features(model: Any) -> Optional[int]:
    # scikit-learn estimators commonly expose n_features_in_
    return int(getattr(model, "n_features_in_", 0) or 0) or None


# -----------------------------
# Schemas
# -----------------------------
class PredictionRequest(BaseModel):
    features: List[float] = Field(
        ...,
        description="Numeric feature vector used by the model (order matters).",
    )

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: List[float]) -> List[float]:
        if len(v) == 0:
            raise ValueError("features must be a non-empty list of numbers.")
        return v


class PredictionResponse(BaseModel):
    prediction: str
    confidence: Optional[float] = None
    model_version: str = "v1"
    n_features: Optional[int] = None


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def health_check():
    # Basic liveness + model load check
    _ = get_model_bundle()
    return {"status": "ok", "model_loaded": True}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    try:
        bundle = get_model_bundle()
        model = bundle["model"]

        # Validate feature length if the model exposes it
        n_expected = _expected_n_features(model)
        if n_expected is not None and len(request.features) != n_expected:
            raise HTTPException(
                status_code=422,
                detail=f"Expected {n_expected} features, got {len(request.features)}.",
            )

        X = np.array(request.features, dtype=float).reshape(1, -1)

        # Prediction
        pred = model.predict(X)[0]

        # Convert prediction to a human-readable label if we can
        label: str
        target_names = bundle.get("target_names")

        if target_names is not None:
            # If pred is an int index, map it; else stringify pred
            try:
                label = str(target_names[int(pred)])
            except Exception:
                label = str(pred)
        else:
            # If model has classes_, try mapping index->class label when pred is index-like
            classes_ = getattr(model, "classes_", None)
            if classes_ is not None:
                try:
                    # If pred is already a class label, this will just stringify it
                    label = str(pred)
                except Exception:
                    label = str(pred)
            else:
                label = str(pred)

        # Confidence (only if predict_proba exists)
        confidence: Optional[float] = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            # If pred is an index, use it; otherwise take max prob
            try:
                confidence = float(proba[int(pred)])
            except Exception:
                confidence = float(np.max(proba))

        return PredictionResponse(
            prediction=label,
            confidence=confidence,
            model_version=str(bundle.get("model_version", "v1")),
            n_features=n_expected,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Entry point for direct execution ---
if __name__ == "__main__":
    import os
    import uvicorn

    # Read port from environment (Cloud Run sets $PORT)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)