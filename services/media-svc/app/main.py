"""
FastAPI media service application with video upload,
HLS transcoding, and Zoom LTI integration.
"""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import boto3
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session
from .lti.zoom_integration import ZoomLTIError, ZoomLTIHandler
from .models import LiveSession, MediaUpload, ZoomLTIConfig
from .proxy.hls_proxy import HLSProxyError, PlaylistWhitelistProxy
from .schemas import (
    LiveSessionCreate,
    LiveSessionResponse,
    LTILaunchRequest,
    MediaUploadResponse,
    PresignedUploadResponse,
    ZoomLTIConfigCreate,
    ZoomLTIConfigResponse,
)
from .workers.transcode import transcode_to_hls

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration (in production, use environment variables)
AWS_REGION = "us-east-1"
S3_BUCKET = "media-service-bucket"
S3_CDN_URL = "https://d1234567890abcdef.cloudfront.net"
HLS_PROXY_SECRET = os.getenv("HLS_PROXY_SECRET", "your-secret-key-here")
ZOOM_WEBHOOK_SECRET = os.getenv("ZOOM_WEBHOOK_SECRET", "zoom-webhook-secret")

# Global objects
zoom_lti_handler: ZoomLTIHandler | None = None
hls_proxy: PlaylistWhitelistProxy | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    global zoom_lti_handler, hls_proxy

    # Initialize services
    zoom_lti_handler = ZoomLTIHandler()
    hls_proxy = PlaylistWhitelistProxy(HLS_PROXY_SECRET, S3_CDN_URL)

    logger.info("Media service started")
    yield

    # Cleanup
    if zoom_lti_handler:
        await zoom_lti_handler.cleanup()
    if hls_proxy:
        await hls_proxy.cleanup()

    logger.info("Media service stopped")


# Create FastAPI app
app = FastAPI(
    title="Media Service",
    description="Video upload, HLS transcoding, and Zoom LTI integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Media Upload Endpoints


@app.post("/api/v1/media/presigned-upload", response_model=PresignedUploadResponse)
async def generate_presigned_upload(
    filename: str,
    content_type: str,
    file_size: int,
    session: AsyncSession = Depends(get_session),
) -> PresignedUploadResponse:
    """Generate presigned URL for direct S3 upload."""
    try:
        # Validate content type
        allowed_types = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"]
        if content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported video format")

        # Validate file size (max 5GB)
        max_size = 5 * 1024 * 1024 * 1024  # 5GB
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit")

        # Generate unique file key
        upload_id = uuid.uuid4()
        file_extension = filename.split(".")[-1] if "." in filename else "mp4"
        s3_key = f"uploads/{upload_id}.{file_extension}"

        # Create S3 client
        s3_client = boto3.client("s3", region_name=AWS_REGION)

        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,  # 1 hour
        )

        # Create upload record
        upload = MediaUpload(
            id=upload_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            s3_key=s3_key,
            s3_bucket=S3_BUCKET,
            status="pending",
        )
        session.add(upload)
        await session.commit()

        logger.info("Generated presigned upload URL for %s", filename)

        return PresignedUploadResponse(
            upload_id=upload_id,
            presigned_url=presigned_url,
            s3_key=s3_key,
            expires_in=3600,
        )

    except Exception as e:
        logger.error("Failed to generate presigned upload URL: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate upload URL") from e


@app.post("/api/v1/media/uploads/{upload_id}/complete")
async def complete_upload(
    upload_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Mark upload as complete and start transcoding."""
    try:
        # Get upload record
        result = await session.execute(select(MediaUpload).where(MediaUpload.id == upload_id))
        upload = result.scalar_one_or_none()

        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        # Update status
        upload.status = "uploaded"
        upload.uploaded_at = datetime.utcnow()
        await session.commit()

        # Start transcoding task
        task = transcode_to_hls.delay(str(upload_id))

        logger.info("Started transcoding for upload %s (task: %s)", upload_id, task.id)

        return {
            "upload_id": str(upload_id),
            "status": "uploaded",
            "transcoding_task_id": task.id,
        }

    except Exception as e:
        logger.error("Failed to complete upload: %s", e)
        raise HTTPException(status_code=500, detail="Failed to complete upload") from e


@app.get("/api/v1/media/uploads", response_model=list[MediaUploadResponse])
async def list_uploads(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[MediaUploadResponse]:
    """List media uploads with optional filtering."""
    try:
        query = select(MediaUpload).offset(offset).limit(limit)

        if status:
            query = query.where(MediaUpload.status == status)

        result = await session.execute(query.order_by(MediaUpload.created_at.desc()))
        uploads = result.scalars().all()

        return [MediaUploadResponse.model_validate(upload) for upload in uploads]

    except Exception as e:
        logger.error("Failed to list uploads: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list uploads") from e


@app.get("/api/v1/media/uploads/{upload_id}", response_model=MediaUploadResponse)
async def get_upload(
    upload_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> MediaUploadResponse:
    """Get specific upload details."""
    try:
        result = await session.execute(select(MediaUpload).where(MediaUpload.id == upload_id))
        upload = result.scalar_one_or_none()

        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")

        return MediaUploadResponse.model_validate(upload)

    except Exception as e:
        logger.error("Failed to get upload: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get upload") from e


# HLS Playback Endpoints


@app.get("/api/v1/media/hls/{video_id}/access-token")
async def generate_hls_access_token(
    video_id: uuid.UUID,
    user_id: uuid.UUID,
    expires_in: int = 3600,
) -> dict[str, Any]:
    """Generate access token for HLS content."""
    try:
        if not hls_proxy:
            raise HTTPException(status_code=500, detail="HLS proxy not initialized")

        token = hls_proxy.generate_access_token(video_id, user_id, expires_in)

        return {
            "access_token": token,
            "video_id": str(video_id),
            "expires_in": expires_in,
        }

    except Exception as e:
        logger.error("Failed to generate access token: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate access token") from e


@app.get("/api/v1/media/hls/{video_id}/master.m3u8")
async def get_master_playlist(
    video_id: uuid.UUID,
    token: str,
    request: Request,
) -> FastAPIResponse:
    """Proxy master HLS playlist with access control."""
    try:
        if not hls_proxy:
            raise HTTPException(status_code=500, detail="HLS proxy not initialized")

        result = await hls_proxy.proxy_master_playlist(video_id, token, request)

        return FastAPIResponse(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Cache-Control": result["cache_control"]},
        )

    except HLSProxyError as e:
        logger.warning("HLS proxy error: %s", e)
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to serve master playlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to serve playlist") from e


@app.get("/api/v1/media/hls/{video_id}/variant/{variant_path:path}")
async def get_variant_playlist(
    video_id: uuid.UUID,
    variant_path: str,
    token: str,
    request: Request,
) -> FastAPIResponse:
    """Proxy variant HLS playlist with access control."""
    try:
        if not hls_proxy:
            raise HTTPException(status_code=500, detail="HLS proxy not initialized")

        result = await hls_proxy.proxy_variant_playlist(video_id, variant_path, token, request)

        return FastAPIResponse(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Cache-Control": result["cache_control"]},
        )

    except HLSProxyError as e:
        logger.warning("HLS proxy error: %s", e)
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to serve variant playlist: %s", e)
        raise HTTPException(status_code=500, detail="Failed to serve playlist") from e


@app.get("/api/v1/media/hls/{video_id}/segment/{segment_path:path}")
async def get_segment(
    video_id: uuid.UUID,
    segment_path: str,
    token: str,
) -> FastAPIResponse:
    """Proxy HLS segment with access control."""
    try:
        if not hls_proxy:
            raise HTTPException(status_code=500, detail="HLS proxy not initialized")

        result = await hls_proxy.proxy_segment(video_id, segment_path, token)

        return FastAPIResponse(
            content=result["content"],
            media_type=result["content_type"],
            headers={"Cache-Control": result["cache_control"]},
        )

    except HLSProxyError as e:
        logger.warning("HLS proxy error: %s", e)
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to serve segment: %s", e)
        raise HTTPException(status_code=500, detail="Failed to serve segment") from e


# Zoom LTI Endpoints


@app.post("/api/v1/lti/config", response_model=ZoomLTIConfigResponse)
async def create_lti_config(
    config_data: ZoomLTIConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> ZoomLTIConfigResponse:
    """Create Zoom LTI configuration."""
    try:
        config = ZoomLTIConfig(**config_data.model_dump())
        session.add(config)
        await session.commit()

        logger.info("Created LTI config for organization %s", config.organization_id)

        return ZoomLTIConfigResponse.model_validate(config)

    except Exception as e:
        logger.error("Failed to create LTI config: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create LTI config") from e


@app.post("/api/v1/lti/launch")
async def handle_lti_launch(
    launch_data: LTILaunchRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Handle LTI 1.3 launch request."""
    try:
        if not zoom_lti_handler:
            raise HTTPException(status_code=500, detail="LTI handler not initialized")

        # Get LTI configuration
        result = await session.execute(
            select(ZoomLTIConfig).where(
                ZoomLTIConfig.organization_id == launch_data.organization_id
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="LTI configuration not found")

        # Verify LTI launch
        claims = await zoom_lti_handler.verify_lti_launch(launch_data.id_token, config)

        logger.info("LTI launch verified for user %s", claims["sub"])

        return {
            "user_id": claims["sub"],
            "organization_id": str(launch_data.organization_id),
            "launch_verified": True,
        }

    except ZoomLTIError as e:
        logger.warning("LTI launch error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to handle LTI launch: %s", e)
        raise HTTPException(status_code=500, detail="Failed to handle LTI launch") from e


@app.post("/api/v1/live-sessions", response_model=LiveSessionResponse)
async def create_live_session(
    session_data: LiveSessionCreate,
    db_session: AsyncSession = Depends(get_session),
) -> LiveSessionResponse:
    """Create live session with Zoom meeting."""
    try:
        if not zoom_lti_handler:
            raise HTTPException(status_code=500, detail="LTI handler not initialized")

        # Get LTI configuration
        result = await db_session.execute(
            select(ZoomLTIConfig).where(ZoomLTIConfig.id == session_data.lti_config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="LTI configuration not found")

        # Create Zoom meeting
        meeting_data = {
            "session_name": session_data.session_name,
            "scheduled_start": session_data.scheduled_start,
            "scheduled_end": session_data.scheduled_end,
            "description": session_data.description,
            "zoom_host_id": session_data.zoom_host_id,
            "requires_registration": session_data.requires_registration,
            "is_recorded": session_data.is_recorded,
        }

        zoom_meeting = await zoom_lti_handler.create_zoom_meeting(meeting_data, config)

        # Create live session record
        live_session = LiveSession(
            session_name=session_data.session_name,
            description=session_data.description,
            scheduled_start=session_data.scheduled_start,
            scheduled_end=session_data.scheduled_end,
            zoom_meeting_id=zoom_meeting["meeting_id"],
            zoom_meeting_uuid=zoom_meeting["meeting_uuid"],
            zoom_join_url=zoom_meeting["join_url"],
            zoom_start_url=zoom_meeting["start_url"],
            zoom_password=zoom_meeting.get("password"),
            zoom_host_id=session_data.zoom_host_id,
            lti_config_id=session_data.lti_config_id,
            requires_registration=session_data.requires_registration,
            is_recorded=session_data.is_recorded,
            status="scheduled",
        )

        db_session.add(live_session)
        await db_session.commit()

        logger.info(
            "Created live session %s with Zoom meeting %s",
            live_session.id,
            zoom_meeting["meeting_id"],
        )

        return LiveSessionResponse.model_validate(live_session)

    except ZoomLTIError as e:
        logger.warning("Zoom LTI error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to create live session: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create live session") from e


@app.post("/api/v1/webhooks/zoom")
async def handle_zoom_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Handle Zoom webhook events."""
    try:
        if not zoom_lti_handler:
            raise HTTPException(status_code=500, detail="LTI handler not initialized")

        # Get request body and signature
        # body = await request.body()  # Not used, commenting out
        payload = await request.json()
        signature = request.headers.get("authorization", "").replace("Bearer ", "")

        # Get all LTI configurations (in production, you might want to identify which one to use)
        result = await session.execute(select(ZoomLTIConfig))
        configs = result.scalars().all()

        # Process webhook for each config (you might want to refine this logic)
        for config in configs:
            try:
                await zoom_lti_handler.handle_zoom_webhook(payload, signature, config)
            except ZoomLTIError as e:
                logger.warning("Failed to process webhook for config %s: %s", config.id, e)
                continue

        return {"status": "processed"}

    except Exception as e:
        logger.error("Failed to handle Zoom webhook: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process webhook") from e


@app.get("/api/v1/live-sessions/{session_id}/attendance", response_model=dict[str, Any])
async def get_attendance_report(
    session_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get attendance report for live session."""
    try:
        if not zoom_lti_handler:
            raise HTTPException(status_code=500, detail="LTI handler not initialized")

        report = await zoom_lti_handler.get_attendance_report(session_id)
        return report

    except ZoomLTIError as e:
        logger.warning("Zoom LTI error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to get attendance report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to get attendance report") from e


# Health Check
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "media-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",  # Bind to localhost only for security
        port=8000,
        reload=True,
        log_level="info",
    )
