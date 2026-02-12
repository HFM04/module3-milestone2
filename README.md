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
