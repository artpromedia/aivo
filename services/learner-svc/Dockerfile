# BEFORE: python:3.11-slim (floating) or alpine with many unfixed CVEs
# AFTER: pin by digest; bookworm slim
# hadolint ignore=DL3007,DL3008
FROM python:3.11-slim-bookworm@sha256:edaf703dce209d351e2c8f64a2e93b73f0f3d0f2e7b7c8b0e1b2e6a5dd77a5f4

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Security updates
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Keep pip/setuptools current (often fixes CVEs in resolvers/wheels)
RUN python -m pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies with cache mount
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user and switch to it
RUN useradd --create-home --shell /bin/bash --uid 10001 app \
    && chown -R app:app /app
USER 10001

# Expose port
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8084/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8084"]
