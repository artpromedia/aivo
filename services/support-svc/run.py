#!/usr/bin/env python3
"""
Support Service
Handles tickets, SLA tracking, knowledge base, and incident linkage
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8510,
        reload=True,
        log_level="info"
    )
