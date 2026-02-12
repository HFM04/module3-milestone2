# FastAPI ML Inference Service – Iris Flower Classifier

[![CI-CD (Test, Build, Push to GAR)](../../actions/workflows/build.yml/badge.svg)](../../actions/workflows/build.yml)

A production-style FastAPI application that serves a trained scikit-learn Iris classification model (`model.pkl`) via HTTP.

This project demonstrates:

- Deterministic model artifact loading
- Strict request/response validation with Pydantic
- Unit testing with pytest
- Multi-stage Docker containerization
- Automated CI/CD with GitHub Actions
- Deployment to Google Artifact Registry (GAR)

---

# Table of Contents

- [Architecture (for grading)](#architecture-for-grading)
- [Repository Structure](#repository-structure)
- [API Endpoints](#api-endpoints)
- [Local Development](#local-development)
- [Docker Usage](#docker-usage)
- [CI/CD Pipeline](#cicd-pipeline)
- [Publishing to Google Artifact Registry](#publishing-to-google-artifact-registry)
- [Troubleshooting](#troubleshooting)
- [Tech Stack](#tech-stack)

---

# Architecture (for grading)

## What this service does

- **Loads a serialized model artifact from disk**  
  The trained model is stored as `app/model.pkl` and loaded using `joblib`.  
  The load path is deterministic and relative to the application directory inside the container.

- **Exposes an HTTP API via FastAPI**
  - `GET /` — readiness check that also confirms the model can load successfully.
  - `GET /healthz` — lightweight liveness check.
  - `POST /predict` — prediction endpoint that:
    - validates input using Pydantic,
    - enforces feature length consistency,
    - returns a structured, typed response model.

- **Packages everything into a reproducible Docker image**
  - Uses a multi-stage Docker build.
  - Separates dependency installation from runtime.
  - Ensures consistent behavior across environments.

- **Uses GitHub Actions for CI/CD automation**
  - Runs unit tests (`pytest`)
  - Builds the Docker image
  - Authenticates securely to Google Cloud using GitHub Secrets
  - Pushes the image to Google Artifact Registry (GAR) on semantic version tags only

---

## Why this is “production style”

- **Deterministic model load**  
  The model artifact is loaded from a fixed, known path inside the container, eliminating environment ambiguity.

- **Stateless requests**  
  Each request includes all required input (`features`) and does not rely on in-memory session state.

- **Strict validation**  
  Request and response schemas are enforced with Pydantic models, reducing contract drift and runtime ambiguity.

- **Fast failure on bad input**  
  Invalid requests produce explicit `422 Unprocessable Entity` responses instead of silent incorrect predictions.

- **Reproducible runtime**  
  The Docker image contains pinned dependencies and the model artifact, ensuring consistent behavior across local, CI, and cloud environments.

---

# Repository Structure

```bash
.
├── .github/workflows/
│   └── build.yml              # CI/CD pipeline (test → build → auth → push)
├── app/
│   ├── app.py                 # FastAPI service
│   ├── model.pkl              # Trained model artifact
│   ├── requirements.txt       # Runtime dependencies
│   └── __init__.py
├── tests/
│   └── test_app.py            # Unit tests
├── Dockerfile                 # Multi-stage build
├── docker-compose.yml
├── RUNBOOK.md
└── README.md


GitHub renders that as literal code.

---

### ✅ What you actually want in README.md

Just this — no outer code fence:

---

## API Endpoints

### Health Checks

#### `GET /`
Readiness endpoint (also verifies model load).

**Example:**
```bash
curl -s http://localhost:8000/ | python -m json.tool
```

**Expected output:**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

---

#### `GET /healthz`

```bash
curl -s http://localhost:8000/healthz | python -m json.tool
```

**Expected output:**
```json
{
  "status": "ok"
}
```

---

### Prediction

#### `POST /predict`

##### Request
```json
{
  "features": [5.1, 3.5, 1.4, 0.2]
}
```

**Feature order:**
1. sepal_length  
2. sepal_width  
3. petal_length  
4. petal_width  

---

##### Successful Example
```bash
curl -s -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}' | python -m json.tool
```

**Example output:**
```json
{
  "prediction": "setosa",
  "confidence": 0.9808127381969152,
  "model_version": "v1",
  "n_features": 4
}
```

---

##### Invalid Example (wrong feature length)
```bash
curl -s -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4]}' | python -m json.tool
```

**Example output:**
```json
{
  "detail": "Expected 4 features, got 3."
}
```

---

## Local Development

### Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r app/requirements.txt
pip install pytest httpx
```

### Run tests
```bash
pytest -q
```

### Run API locally
```bash
uvicorn app.app:app --host 0.0.0.0 --port 8000
```

Open Swagger UI:

`http://localhost:8000/docs`

---

## Docker Usage

### Build image
```bash
docker build -t flower-service:local .
```

### Run container
```bash
docker run --rm -p 8000:8000 flower-service:local
```

---

## CI/CD Pipeline

### Pipeline Stages
- **Test** – run pytest  
- **Build** – build Docker image  
- **Authenticate** – login to Google Cloud  
- **Push** – publish image to Artifact Registry  

### Trigger Rules
- PR to `main` → Test + Build  
- Push to `main` → Test + Build  
- Push tag `vX.Y.Z` → Test → Build → Authenticate → Push  

---

## Publishing to Google Artifact Registry

### Target image
```
us-central1-docker.pkg.dev/ml-deployment-486403/ml-repo/flower-service:<TAG>
```

### Required GitHub Secret
`GCP_SA_KEY`

Must contain full JSON of a Service Account with:

`roles/artifactregistry.writer`

### Publish a new version
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## Troubleshooting

**422 error on `/predict`**  
Ensure exactly 4 numeric features are provided.

**Model not found**  
Confirm `app/model.pkl` exists and is included in the Docker image.

**Publish stage skipped**  
Only runs on semantic tags (`vX.Y.Z`).

**Permission denied on push**  
Ensure service account has `Artifact Registry Writer`.

---

## Tech Stack

- Python 3.11  
- FastAPI  
- scikit-learn + joblib  
- Docker (multi-stage)  
- GitHub Actions  
- Google Artifact Registry  

---

### Bottom Line

For a README file:
- ❌ Do NOT wrap the whole file in triple backticks.
- ✅ Only use backticks for commands and code blocks.
- ✅ Let headings render naturally.

If you want, I can now give you the **entire final README cleanly formatted exactly as it should appear in GitHub** (fully polished, production-ready).
