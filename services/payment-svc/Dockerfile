# BEFORE: python:3.11-slim (floating) or alpine with many unfixed CVEs
# AFTER: pin by digest; bookworm slim
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

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r -g 10001 payment && useradd -r -g payment -u 10001 payment
RUN chown -R payment:payment /app
USER payment

# Expose port
EXPOSE 8083

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8083/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8083"]
