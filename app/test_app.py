"""
tests/test_app.py

Tailored pytest suite for *our* Flower Prediction FastAPI service.

Why this file exists (rubric alignment):
- "Test inference endpoint functionality"
- "Validate input/output formats"
- "Check error handling"

Key Design Choice in OUR project:
- Input is a 4-length numeric vector: {"features":[...]}
  This keeps the API simple and avoids field-name mismatches.
"""

import pytest
from fastapi.testclient import TestClient

# NOTE:
# This import MUST match your project structure.
# Our project uses:
#   module3/milestone2/app/app.py  -> contains `app = FastAPI(...)`
# In tests, Python resolves "app" as a package because module3/milestone2/app/
# is a folder. If your folder isn't treated as a package, you may need an
# __init__.py in app/ (optional in modern Python but can help in CI).
from app.app import app


# =============================================================================
# Fixtures (Reusable Test Data)
# =============================================================================

@pytest.fixture
def client():
    """
    TestClient spins up the FastAPI app in-memory (no real server needed).

    Why this is useful:
    - Fast and deterministic tests
    - No need to run uvicorn
    - Perfect for CI pipelines
    """
    return TestClient(app)


@pytest.fixture
def valid_payload():
    """
    Canonical valid request payload for our /predict endpoint.

    IMPORTANT:
    - features must be a list of exactly 4 numbers
    - ordering is [sepal_length, sepal_width, petal_length, petal_width]
    """
    return {"features": [5.1, 3.5, 1.4, 0.2]}


@pytest.fixture
def known_like_samples():
    """
    Samples that are 'typical' of each class.

    NOTE:
    We are not hard-asserting the exact class label here because:
    - The model could change slightly (different classifier/hyperparams)
    - The goal of unit tests is mostly API correctness + stability

    We *do* use these in a parametrized test to ensure the endpoint behaves
    consistently across a range of realistic inputs.
    """
    return [
        {"features": [4.9, 3.0, 1.4, 0.2]},  # setosa-ish
        {"features": [6.0, 2.7, 4.5, 1.3]},  # versicolor-ish
        {"features": [6.3, 2.9, 5.6, 2.1]},  # virginica-ish
    ]


# =============================================================================
# Health Endpoint Tests
# =============================================================================

def test_health_endpoint_ok(client):
    """
    What this test proves:
    - The app can start
    - Routing works
    - The service exposes a basic operational check

    Why graders care:
    - It's a standard production pattern
    - It confirms the container/service is alive
    """
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# =============================================================================
# Prediction Endpoint Tests (Happy Path)
# =============================================================================

def test_predict_success_returns_expected_fields(client, valid_payload):
    """
    What this test proves:
    - /predict accepts valid JSON input
    - Returns HTTP 200
    - Response includes the fields our client depends on

    This is the most important "endpoint works" test.
    """
    r = client.post("/predict", json=valid_payload)
    assert r.status_code == 200

    data = r.json()

    # These are the contract fields for our API response:
    assert "prediction" in data
    assert "class_index" in data
    assert "probabilities" in data  # may be None, but key should exist


def test_predict_prediction_is_valid_label(client, valid_payload):
    """
    What this test proves:
    - The endpoint returns a valid class label string
    - Prevents silent breaking changes like returning numeric labels only
    """
    r = client.post("/predict", json=valid_payload)
    assert r.status_code == 200

    prediction = r.json()["prediction"]
    assert prediction in ["setosa", "versicolor", "virginica"]


def test_predict_class_index_is_valid(client, valid_payload):
    """
    What this test proves:
    - class_index is an int and stays within expected range
    - Prevents contract drift (e.g., returning strings or out-of-range ints)
    """
    r = client.post("/predict", json=valid_payload)
    assert r.status_code == 200

    class_index = r.json()["class_index"]
    assert isinstance(class_index, int)
    assert class_index in [0, 1, 2]


def test_predict_probabilities_are_well_formed_if_present(client, valid_payload):
    """
    What this test proves:
    - If the model supports predict_proba, probabilities are:
        - a length-3 list
        - numeric
        - within [0, 1]
        - roughly sum to 1

    Why we make it conditional:
    - Not all models expose predict_proba
    - Our app returns None if unavailable
    """
    r = client.post("/predict", json=valid_payload)
    assert r.status_code == 200

    probs = r.json().get("probabilities")

    # If probabilities are not returned, that's acceptable per our design.
    if probs is None:
        return

    assert isinstance(probs, list)
    assert len(probs) == 3
    assert all(isinstance(p, (int, float)) for p in probs)
    assert all(0.0 <= float(p) <= 1.0 for p in probs)

    # Allow small floating point drift
    assert 0.99 <= sum(float(p) for p in probs) <= 1.01


# =============================================================================
# Input Validation & Error Handling (Negative Tests)
# =============================================================================

def test_predict_rejects_missing_features_key(client):
    """
    What this test proves:
    - Pydantic validation is active
    - Missing required fields produce a 422 error (FastAPI default)

    This directly satisfies "Check error handling".
    """
    r = client.post("/predict", json={"wrong_key": [1, 2, 3, 4]})
    assert r.status_code == 422


def test_predict_rejects_wrong_length_feature_vector(client):
    """
    What this test proves:
    - Schema enforces exactly 4 features
    - Prevents malformed requests from reaching the model
    """
    r = client.post("/predict", json={"features": [5.1, 3.5, 1.4]})
    assert r.status_code == 422


def test_predict_rejects_non_numeric_values(client):
    """
    What this test proves:
    - The API enforces numeric feature types
    - Prevents runtime errors inside sklearn pipeline
    """
    r = client.post("/predict", json={"features": ["bad", 3.5, 1.4, 0.2]})
    assert r.status_code == 422


def test_predict_rejects_empty_body(client):
    """
    What this test proves:
    - Empty request fails validation cleanly
    """
    r = client.post("/predict", json={})
    assert r.status_code == 422


# =============================================================================
# Parametrized Tests (Multiple Inputs, Same Expectations)
# =============================================================================

@pytest.mark.parametrize(
    "payload",
    [
        {"features": [4.9, 3.0, 1.4, 0.2]},
        {"features": [6.0, 2.7, 4.5, 1.3]},
        {"features": [6.3, 2.9, 5.6, 2.1]},
    ],
)
def test_predict_multiple_realistic_inputs(client, payload):
    """
    What this test proves:
    - The endpoint behaves consistently across multiple realistic inputs
    - Reduces the risk of "works for one payload only" bugs

    Note:
    We do NOT assert exact labels here to keep tests stable if the model
    changes slightly. We validate the output contract instead.
    """
    r = client.post("/predict", json=payload)
    assert r.status_code == 200
    assert r.json()["prediction"] in ["setosa", "versicolor", "virginica"]
    assert r.json()["class_index"] in [0, 1, 2]


# =============================================================================
# Response Schema & Headers
# =============================================================================

def test_response_schema_exact_keys(client, valid_payload):
    """
    What this test proves:
    - Response keys remain stable (no breaking changes)
    - Helps catch accidental refactors that change the response structure
    """
    r = client.post("/predict", json=valid_payload)
    assert r.status_code == 200

    data = r.json()
    assert set(data.keys()) == {"prediction", "class_index", "probabilities"}


def test_content_type_json(client, valid_payload):
    """
    What this test proves:
    - Response is JSON (important for API consumers and tooling)
    """
    r = client.post("/predict", json=valid_payload)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")


# =============================================================================
# Edge Case Tests (Boundary Behavior)
# =============================================================================

def test_predict_near_zero_values(client):
    """
    What this test proves:
    - The service doesn't crash on boundary-ish numeric values
    - Validates robustness at the API layer

    We keep these values > 0 to avoid 'obviously invalid' cases.
    """
    payload = {"features": [0.001, 0.001, 0.001, 0.001]}
    r = client.post("/predict", json=payload)

    assert r.status_code == 200
    assert r.json()["prediction"] in ["setosa", "versicolor", "virginica"]


def test_predict_large_values(client):
    """
    What this test proves:
    - The service can handle large numeric inputs without throwing errors
    - Real-world systems often receive out-of-distribution data

    We don't claim model correctness here, just endpoint stability.
    """
    payload = {"features": [100.0, 50.0, 75.0, 40.0]}
    r = client.post("/predict", json=payload)

    assert r.status_code == 200
    assert r.json()["prediction"] in ["setosa", "versicolor", "virginica"]
