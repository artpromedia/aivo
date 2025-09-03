"""
FastAPI application for the Notification Service.
"""
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import get_settings
from .schemas import (
    NotificationRequest, NotificationResponse,
    BulkNotificationRequest, BulkNotificationResponse,
    TemplateListResponse, RenderTemplateRequest, RenderTemplateResponse,
    HealthResponse
)
from .template_service import TemplateService
from .email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services and settings
settings = get_settings()
template_service = TemplateService()
email_service = EmailService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Notification Service...")
    await template_service.initialize()
    logger.info("Notification Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Notification Service...")


# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Email notification service with MJML templates",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key dependency (if configured)
def get_api_key(api_key: str = None) -> str:
    """Validate API key if configured."""
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "service": "Notification Service",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        smtp_configured=email_service.is_configured(),
        templates_loaded=len(template_service.list_templates())
    )


@app.post("/notify", response_model=NotificationResponse)
async def send_notification(
    request: NotificationRequest,
    api_key: str = Depends(get_api_key)
):
    """Send a single notification email."""
    try:
        # Render template
        rendered = await template_service.render_template(
            template_id=request.template_id,
            data=request.data
        )
        
        # Use custom subject if provided
        subject = request.subject or rendered["subject"]
        
        # Send email
        result = await email_service.send_email(
            to_email=request.to,
            subject=subject,
            html_content=rendered["html"],
            from_email=request.from_email,
            from_name=request.from_name,
            metadata={
                "template_id": request.template_id.value,
                "tenant_id": request.tenant_id,
                "user_id": request.user_id,
                "reference_id": request.reference_id
            }
        )
        
        return NotificationResponse(
            success=result["success"],
            message_id=result.get("message_id"),
            error=result.get("error")
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/notify/bulk", response_model=BulkNotificationResponse)
async def send_bulk_notification(
    request: BulkNotificationRequest,
    api_key: str = Depends(get_api_key)
):
    """Send bulk notification emails."""
    try:
        # Validate recipient count
        if len(request.to) > settings.max_recipients_per_request:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many recipients. Maximum: {settings.max_recipients_per_request}"
            )
        
        # Render template
        rendered = await template_service.render_template(
            template_id=request.template_id,
            data=request.data
        )
        
        # Use custom subject if provided
        subject = request.subject or rendered["subject"]
        
        # Send bulk emails
        result = await email_service.send_bulk_emails(
            to_emails=request.to,
            subject=subject,
            html_content=rendered["html"],
            from_email=request.from_email,
            from_name=request.from_name,
            metadata={
                "template_id": request.template_id.value,
                "tenant_id": request.tenant_id
            }
        )
        
        return BulkNotificationResponse(
            total_sent=result["total_sent"],
            successful=result["successful"],
            failed=result["failed"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send bulk notification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/templates", response_model=TemplateListResponse)
async def list_templates():
    """List available email templates."""
    templates = template_service.list_templates()
    return TemplateListResponse(templates=templates)


@app.post("/templates/render", response_model=RenderTemplateResponse)
async def render_template(request: RenderTemplateRequest):
    """Render a template for testing/preview."""
    try:
        rendered = await template_service.render_template(
            template_id=request.template_id,
            data=request.data
        )
        
        return RenderTemplateResponse(
            html=rendered["html"],
            subject=rendered["subject"],
            template_id=request.template_id
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Development endpoints (only available in dev mode)
if settings.dev_mode:
    @app.get("/dev/emails")
    async def get_dev_emails(limit: int = 50):
        """Get recent development emails."""
        emails = await email_service.get_dev_emails(limit=limit)
        return {"emails": emails, "count": len(emails)}
