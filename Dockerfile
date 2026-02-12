# =========================
# Builder Stage
# =========================
# Use a slim Python base image to reduce image size while retaining compatibility
# with common Python wheels (safer than Alpine for ML dependencies).
FROM python:3.11-slim AS builder

# Set a dedicated working directory for build-time operations.
# This directory is discarded after the builder stage completes.
WORKDIR /build

# Disable pip version checks and caching to:
# - Reduce noise in CI logs
# - Prevent unnecessary cache files that increase image size
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Copy only the dependency manifest first.
# This enables Docker layer caching so dependencies are not reinstalled
# unless requirements.txt changes.
COPY app/requirements.txt .

# Install Python dependencies into a temporary prefix directory (/install).
# This isolates dependencies from the base image and allows us to copy
# only the required runtime artifacts into the final image.
RUN pip install --prefix=/install -r requirements.txt


# =========================
# Runtime Stage
# =========================
# Start from a fresh slim Python image to ensure a minimal runtime environment.
# No build tools or compilers are included, reducing attack surface.
FROM python:3.11-slim

# Set the working directory where the application will live at runtime.
WORKDIR /app

# Create a non-root user to follow container security best practices.
# Running as non-root limits the impact of potential container compromise.
RUN useradd -m appuser

# Copy only the installed runtime dependencies from the builder stage.
# This avoids carrying over build-time files and keeps the final image small.
COPY --from=builder /install /usr/local

# Copy the application source code and model artifact (.pkl) into the container.
# At this point, the image contains only:
# - Python runtime
# - Required dependencies
# - Application code
# - Model artifact
COPY app/ /app/

# Expose the application port.
# This documents the intended runtime port for orchestration tools
# such as Docker Compose or Kubernetes.
EXPOSE 8000

# Switch to the non-root user for application execution.
USER appuser

# Define the container entrypoint.
# Uvicorn is used as an ASGI server to serve the FastAPI inference service.
# Binding to 0.0.0.0 allows the service to be accessible outside the container.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
