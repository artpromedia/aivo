# hadolint ignore=DL3007,DL3008
# Event Collector Service Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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
RUN addgroup --system --gid 1001 eventcollector && \
    adduser --system --uid 1001 --gid 1001 eventcollector && \
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
