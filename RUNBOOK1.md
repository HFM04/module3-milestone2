```markdown
# ML Inference Service – Operational Runbook

## 1. Purpose

This runbook provides operational guidance for the FastAPI-based ML inference service. It covers:

- Deployment procedures  
- Health verification  
- Logging and monitoring  
- Troubleshooting with real error examples  
- Incident response and rollback procedures  

This document is intended for engineers operating, maintaining, or grading the system.

---

## 2. System Overview

### Components

| Component | Purpose |
|-----------|----------|
| FastAPI Application (`app/app.py`) | Serves HTTP endpoints |
| `model.pkl` | Serialized trained model artifact |
| Dockerfile | Builds reproducible container image |
| GitHub Actions | CI/CD automation |
| Google Artifact Registry | Stores versioned container images |

---

## 3. Deployment Procedures

### 3.1 Run Tests

Before building or deploying, always validate the code:

```bash
pytest -q
```

Expected output:

```
================= 15 passed in 1.42s =================
```

If tests fail, do not proceed to build or publish.

---

### 3.2 Start API Locally

```bash
uvicorn app.app:app --host 0.0.0.0 --port 8000
```

Verify readiness:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{
  "status": "ok",
  "model_loaded": true
}
```

---

### 3.3 Build Docker Image

```bash
docker build -t flower-service:local .
```

---

### 3.4 Run Docker Container

```bash
docker run --rm -p 8000:8000 flower-service:local
```

Verify:

```bash
curl http://localhost:8000/healthz
```

Expected:

```json
{"status":"ok"}
```

---

### 3.5 Publish New Version (CI/CD)

To trigger the publish pipeline:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Image will be published to:

```
us-central1-docker.pkg.dev/ml-deployment-486403/ml-repo/flower-service:<TAG>
```

---

## 4. Logging

### 4.1 View Local Docker Logs

```bash
docker ps
docker logs <container_id>
```

Example normal startup log:

```
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 5. Monitoring

### 5.1 Health Checks

**Liveness**

```bash
curl http://localhost:8000/healthz
```

**Readiness**

```bash
curl http://localhost:8000/
```

---

### 5.2 Key Operational Metrics

Monitor the following:

- HTTP 5xx error rate  
- HTTP 4xx error rate  
- Request latency  
- CPU utilization  
- Memory utilization  
- Container restart count  

---

## 6. Troubleshooting (With Real Error Examples)

---

### 6.1 Model File Missing

**Error Example**

Container logs show:

```
RuntimeError: model.pkl not found at /app/model.pkl
```

**Cause**

The model artifact is missing or not copied into the Docker image.

**Resolution**

Confirm file exists locally:

```bash
ls app/model.pkl
```

Ensure Dockerfile includes:

```
COPY app/ /app/
```

Rebuild image:

```bash
docker build --no-cache -t flower-service:local .
```

---

### 6.2 422 Error on /predict

**Error Example**

```json
{
  "detail": "Expected 4 features, got 3."
}
```

**Cause**

Incorrect number of features in request.

**Resolution**

Send exactly four numeric features:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}'
```

---

### 6.3 500 Internal Server Error

**Error Example**

```json
{
  "detail": "could not convert string to float"
}
```

**Cause**

Non-numeric values provided.

**Resolution**

Ensure all features are numeric.

Correct:

```json
{"features":[5.1,3.5,1.4,0.2]}
```

Incorrect:

```json
{"features":["five",3.5,1.4,0.2]}
```

---

### 6.4 CI Publish Permission Denied

**Error Example**

```
denied: Permission "artifactregistry.repositories.uploadArtifacts" denied
```

**Cause**

Service account missing required role.

**Resolution**

In Google Cloud IAM, add role:

```
roles/artifactregistry.writer
```

Re-trigger publish with new tag:

```bash
git tag v1.0.1
git push origin v1.0.1
```

---

### 6.5 Publish Job Skipped

**GitHub Actions Message**

```
Job skipped due to condition
```

**Cause**

Publish job only runs on semantic version tags.

**Resolution**

Use correct tag format:

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

### 6.6 Docker Build Failure

**Error Example**

```
ERROR: failed to solve: the Dockerfile cannot be empty
```

**Cause**

Incorrect working directory during build.

**Resolution**

Ensure you run build from project root:

```bash
docker build -t flower-service:local .
```

---

## 7. Incident Response Workflow

1. Check health endpoints.  
2. Inspect logs.  
3. Identify error category.  
4. Apply fix.  
5. Re-run tests.  
6. Redeploy with new semantic tag.  

---

## 8. Rollback Strategy

If a deployment fails:

1. Identify previous stable tag (e.g., `v1.0.0`).  
2. Redeploy that image from Artifact Registry.  

Images are immutable, ensuring safe rollback.

---

## 9. Security Controls

- No credentials stored in repository  
- Service account credentials stored in GitHub Secrets  
- Container runs as non-root user  
- Strict Pydantic input validation  
- Inference-only (no runtime training)  

---

## 10. Operational Readiness Summary

This system provides:

- Deterministic model loading  
- Strict schema validation  
- Containerized reproducibility  
- Automated CI/CD  
- Versioned image publishing  
- Clear troubleshooting procedures  
- Defined rollback strategy  

This runbook ensures the service is:

- Observable  
- Recoverable  
- Reproducible  
- Production-ready  
```
