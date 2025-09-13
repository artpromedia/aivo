from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import create_tables
from .routes import tickets, kb, sla, incidents

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Support Service",
    description="Support Center with Tickets, SLA tracking, and Knowledge Base",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets.router)
app.include_router(kb.router)
app.include_router(sla.router)
app.include_router(incidents.router)

@app.get("/")
async def root():
    return {
        "service": "Support Service",
        "version": "1.0.0",
        "description": "Support Center with Tickets, SLA tracking, and Knowledge Base",
        "endpoints": {
            "tickets": "/tickets",
            "knowledge_base": "/kb",
            "sla": "/sla",
            "incidents": "/incidents",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "support-svc"}
