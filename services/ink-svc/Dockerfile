# BEFORE: python:3.11-slim (floating) or alpine with many unfixed CVEs
# AFTER: pin by digest; bookworm slim
FROM python:3.11-slim-bookworm@sha256:edaf703dce209d351e2c8f64a2e93b73f0f3d0f2e7b7c8b0e1b2e6a5dd77a5f4

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Security updates
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*

# Keep pip/setuptools current (often fixes CVEs in resolvers/wheels)
RUN python -m pip install --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml ./

# Install poetry and dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY app/ ./app/

# Create non-root user with fixed UID
RUN useradd --create-home --shell /bin/bash --uid 10001 app \
    && chown -R app:app /app
USER 10001

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run application
CMD ["python", "-m", "app.main"]
