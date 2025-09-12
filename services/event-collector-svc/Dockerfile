# BEFORE: python:3.11-slim (floating) or alpine with many unfixed CVEs
# AFTER: pin by digest; bookworm slim
# Event Collector Service Dockerfile
FROM python:3.11-slim-bookworm@sha256:edaf703dce209d351e2c8f64a2e93b73f0f3d0f2e7b7c8b0e1b2e6a5dd77a5f4

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Security updates
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*

# Keep pip/setuptools current (often fixes CVEs in resolvers/wheels)
RUN python -m pip install --upgrade pip setuptools wheel

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY protos/ ./protos/
COPY run.py ./

# Generate protobuf files and create buffer directory
RUN python -m grpc_tools.protoc \
    --python_out=. \
    --grpc_python_out=. \
    --proto_path=. \
    protos/event_collector.proto && \
    mkdir -p /app/buffer

# Create non-root user and change ownership
RUN addgroup --system --gid 10001 eventcollector && \
    adduser --system --uid 10001 --gid 10001 eventcollector && \
    chown -R eventcollector:eventcollector /app

# Switch to non-root user
USER eventcollector

# Expose ports
EXPOSE 8000 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Set environment variables
ENV PYTHONPATH=/app
ENV BUFFER_DIR=/app/buffer

# Run the application
CMD ["python", "run.py"]
