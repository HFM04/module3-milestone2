# ML Inference Service – Operational Runbook

---

## 1. Purpose

This runbook provides operational guidance for the FastAPI-based ML inference service. It covers:

- Deployment procedures
- Health verification
- Logging and monitoring
- Troubleshooting with real error examples
- Incident response and rollback procedures

---

## 2. Deployment Procedures

### Run Tests

```bash
pytest -q
```

Expected output:

```
================= 15 passed in 1.42s =================
```

If tests fail, do not proceed.

---

### Start API Locally

```bash
uvicorn app.app:app --host 0.0.0.0 --port 8000
```

Verify readiness:

```bash
curl http://localhost:8000/
```

Expected:

```json
{
  "status": "ok",
  "model_loaded": true
}
```

---

### Build Docker Image

```bash
docker build -t flower-service:local .
```

---

### Run Docker Container

```bash
docker run --rm -p 8000:8000 flower-service:local
```

Verify liveness:

```bash
curl http://localhost:8000/healthz
```

Expected:

```json
{"status":"ok"}
```

---

### Publish New Version (CI/CD)

```bash
git tag v1.0.0
git push origin v1.0.0
```

Image will be published to:

```
us-central1-docker.pkg.dev/ml-deployment-486403/ml-repo/flower-service:<TAG>
```

---

## 3. Logging

### View Docker Logs

```bash
docker ps
docker logs <container_id>
```

Example startup log:

```
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 4. Troubleshooting

### Model File Missing

Error example:

```
RuntimeError: model.pkl not found at /app/model.pkl
```

Cause:
Model artifact missing or excluded from Docker image.

Fix:

```bash
ls app/model.pkl
docker build --no-cache -t flower-service:local .
```

---

### 422 Error on `/predict`

Error example:

```json
{
  "detail": "Expected 4 features, got 3."
}
```

Cause:
Incorrect feature vector length.

Fix:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}'
```

---

### 500 Internal Server Error

Error example:

```json
{
  "detail": "could not convert string to float"
}
```

Cause:
Non-numeric values in input.

Fix:
Ensure all features are numeric.

---

### CI Publish Permission Denied

Error example:

```
denied: Permission "artifactregistry.repositories.uploadArtifacts" denied
```

Cause:
Service account missing role.

Fix:
Grant:

```
roles/artifactregistry.writer
```

Then re-tag:

```bash
git tag v1.0.1
git push origin v1.0.1
```

---

## 5. Rollback Procedure

If deployment fails:

1. Identify last stable tag (e.g., v1.0.0)
2. Redeploy that image from Artifact Registry

Images are immutable.

---

## 6. Security Controls

- No credentials in repository
- Service account stored in GitHub Secrets
- Container runs as non-root user
- Strict Pydantic validation
- Inference-only service

---

## 7. Operational Summary

This service provides:

- Deterministic model loading
- Strict validation
- Container reproducibility
- Automated CI/CD
- Versioned image publishing
- Clear recovery procedures
```
