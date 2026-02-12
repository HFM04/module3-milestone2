# RUNBOOK.md
# Milestone 2 – Containerization & CI/CD Pipeline
# Flower Prediction ML Service

---

## 1. Overview

This runbook documents the operational architecture, containerization strategy,
CI/CD automation, versioning approach, and troubleshooting procedures for the
Flower Prediction ML Service.

The service exposes a REST inference endpoint that loads a pre-trained
scikit-learn model artifact (`model.pkl`) and performs classification on
flower feature inputs.

The system is built using:
- Python 3.11
- FastAPI (inference service)
- Docker (multi-stage containerization)
- GitHub Actions (CI/CD automation)
- Container Registry (versioned image storage)

This document enables reproducibility, operational transparency, and
troubleshooting without requiring direct code inspection.

---

## 2. Dependency Pinning & Reproducibility Strategy

All Python dependencies are strictly version-pinned in `requirements.txt`.

Example:
    fastapi==0.115.0
    scikit-learn==1.5.2
    joblib==1.4.2

Why this matters:
- Prevents unexpected behavior from upstream package changes
- Ensures CI, local development, and production environments are identical
- Enables deterministic Docker image builds

Reproducibility guarantees:
- Same base image (`python:3.11-slim`)
- Same pinned Python dependencies
- Model artifact committed as `model.pkl`
- Immutable semantic version image tags

---

## 3. Docker Image Architecture

The container uses a **multi-stage build** to optimize size, security,
and reproducibility.

### 3.1 Builder Stage

Purpose:
- Install Python dependencies
- Isolate build-time operations

Mechanism:
- Uses `python:3.11-slim`
- Installs dependencies into `/install`
- Caches dependency layer separately from application code

Benefits:
- Faster rebuilds when application code changes
- No build tools carried into runtime image
- Reduced final image size

---

### 3.2 Runtime Stage

Purpose:
- Run the inference service in a minimal environment

Mechanism:
- Fresh `python:3.11-slim` base image
- Copies only installed runtime dependencies
- Copies application code and model artifact
- Executes service as non-root user

Security Measures:
- No compilers or development packages included
- Non-root execution (`appuser`)
- Minimal dependency footprint

Outcome:
- Reduced attack surface
- Smaller, production-ready image
- Clear separation between build and runtime environments

---

## 4. Image Optimization Techniques

Optimization strategies applied:

1. Multi-stage build
2. Slim base image selection
3. Layer caching by copying `requirements.txt` first
4. Disabling pip cache during install
5. No development dependencies in runtime

Estimated impact:
- Significant size reduction compared to single-stage builds
- Faster CI builds due to cached dependency layer
- Improved runtime security posture

To inspect image size:
    docker images

---

## 5. Security Considerations

Security best practices implemented:

- No hardcoded credentials in repository
- Registry credentials stored as GitHub Secrets
- Non-root container execution
- Minimal runtime base image
- Dependency version pinning
- No unnecessary OS packages installed

This approach reduces vulnerability exposure and prevents
privilege escalation inside the container.

---

## 6. CI/CD Workflow

The CI/CD pipeline is implemented using GitHub Actions.

Workflow steps:

1. Triggered on push or version tag
2. Checkout repository
3. Set up Python environment
4. Install dependencies
5. Run pytest test suite
6. Build Docker image
7. Authenticate with container registry
8. Push image with semantic version tag

Pipeline guarantees:

- Image builds only if tests pass
- Registry push occurs only after successful test execution
- Versioned images are immutable
- No manual deployment steps required

To view CI status:
- Navigate to GitHub → Actions tab

---

## 7. Versioning Strategy

Semantic Versioning format:
    vMAJOR.MINOR.PATCH

Example:
    v1.0.0

Version rules:
- MAJOR: Breaking API changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes or small improvements

Images are tagged using:
    docker build -t registry/namespace/ml-service:v1.0.0 .
    docker push registry/namespace/ml-service:v1.0.0

Benefits:
- Clear deployment history
- Reproducible rollbacks
- Traceability between Git tag and container image

---

## 8. Running the Service Locally

Build image:
    docker build -t flower-service:local .

Run container:
    docker run -p 8000:8000 flower-service:local

Health check:
    curl http://localhost:8000/health

Prediction example:
    curl -X POST http://localhost:8000/predict \
         -H "Content-Type: application/json" \
         -d '{"features":[5.1,3.5,1.4,0.2]}'

---

## 9. Troubleshooting Guide

### Issue: Docker build fails

Possible causes:
- Dependency version conflict
- Incorrect requirements.txt formatting

Solution:
- Verify pinned versions
- Rebuild without cache:
    docker build --no-cache -t flower-service:local .

---

### Issue: CI passes locally but fails in GitHub Actions

Possible causes:
- Environment-specific paths
- Missing dependency in requirements.txt

Solution:
- Ensure all imports exist in requirements.txt
- Confirm Python version matches Docker base image

---

### Issue: Image push fails with authentication error

Possible causes:
- GitHub Secrets not configured
- Incorrect registry URL

Solution:
- Verify repository secrets
- Confirm registry namespace and permissions

---

## 10. Operational Summary

This deployment pipeline ensures:

- Deterministic container builds
- Secure runtime execution
- Automated test enforcement
- Version-controlled container releases
- Registry-backed artifact storage

The system is fully reproducible and production-ready.

---
