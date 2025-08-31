"""FastAPI sanity service for monorepo health checks."""

from fastapi import FastAPI

app = FastAPI(title="Hello Service", version="0.1.0")


@app.get("/healthz")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/ping")
def ping() -> str:
    """Ping endpoint that returns pong."""
    return "pong"