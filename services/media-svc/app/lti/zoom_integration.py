"""Zoom LTI 1.3 integration for live class sessions."""
import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import engine
from ..models import AttendanceRecord, LiveSession, ZoomLTIConfig

logger = logging.getLogger(__name__)


class ZoomLTIError(Exception):
    """Custom exception for Zoom LTI integration errors."""
    pass


class ZoomLTIHandler:
    """Handles Zoom LTI 1.3 integration and meeting management."""

    def __init__(self) -> None:
        """Initialize Zoom LTI handler."""
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def verify_lti_launch(
        self,
        id_token: str,
        config: ZoomLTIConfig,
    ) -> Dict[str, Any]:
        """Verify LTI 1.3 launch request.
        
        Args:
            id_token: JWT ID token from LTI launch
            config: LTI configuration for organization
            
        Returns:
            Decoded and verified LTI claims
            
        Raises:
            ZoomLTIError: If verification fails
        """
        try:
            # Get public keys from platform
            response = await self.http_client.get(config.key_set_url)
            response.raise_for_status()
            jwks = response.json()
            
            # Decode and verify JWT
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")
            
            # Find matching public key
            public_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    break
            
            if not public_key:
                raise ZoomLTIError(f"No matching public key found for kid: {kid}")
            
            # Verify and decode JWT
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=["RS256"],
                audience=config.client_id,
                issuer=config.issuer,
            )
            
            # Validate required LTI claims
            required_claims = [
                "iss",
                "aud",
                "sub",
                "exp",
                "iat",
                "nonce",
                "https://purl.imsglobal.org/spec/lti/claim/message_type",
                "https://purl.imsglobal.org/spec/lti/claim/version",
                "https://purl.imsglobal.org/spec/lti/claim/deployment_id",
            ]
            
            for claim in required_claims:
                if claim not in payload:
                    raise ZoomLTIError(f"Missing required LTI claim: {claim}")
            
            # Validate deployment ID
            if payload["https://purl.imsglobal.org/spec/lti/claim/deployment_id"] != config.deployment_id:
                raise ZoomLTIError("Deployment ID mismatch")
            
            # Validate message type
            message_type = payload["https://purl.imsglobal.org/spec/lti/claim/message_type"]
            if message_type != "LtiResourceLinkRequest":
                raise ZoomLTIError(f"Unsupported message type: {message_type}")
            
            logger.info("LTI launch verified successfully for user: %s", payload["sub"])
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ZoomLTIError("ID token has expired")
        except jwt.InvalidTokenError as e:
            raise ZoomLTIError(f"Invalid ID token: {e}")
        except httpx.RequestError as e:
            raise ZoomLTIError(f"Failed to fetch JWKS: {e}")
        except Exception as e:
            logger.error("LTI verification failed: %s", e)
            raise ZoomLTIError(f"LTI verification failed: {e}")

    async def create_zoom_meeting(
        self,
        session_data: Dict[str, Any],
        config: ZoomLTIConfig,
    ) -> Dict[str, Any]:
        """Create Zoom meeting for live session.
        
        Args:
            session_data: Session configuration data
            config: Zoom LTI configuration
            
        Returns:
            Zoom meeting details
        """
        try:
            # Generate Zoom JWT token
            zoom_token = self._generate_zoom_jwt(config)
            
            # Prepare meeting data
            meeting_data = {
                "topic": session_data["session_name"],
                "type": 2,  # Scheduled meeting
                "start_time": session_data["scheduled_start"].isoformat(),
                "duration": int(
                    (session_data["scheduled_end"] - session_data["scheduled_start"]).total_seconds() / 60
                ),
                "timezone": "UTC",
                "password": self._generate_meeting_password(),
                "agenda": session_data.get("description", ""),
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "cn_meeting": False,
                    "in_meeting": False,
                    "join_before_host": True,
                    "mute_upon_entry": True,
                    "watermark": False,
                    "use_pmi": False,
                    "approval_type": 0,  # Automatically approve
                    "registration_type": 1 if session_data.get("requires_registration") else 0,
                    "audio": "both",
                    "auto_recording": "cloud" if session_data.get("is_recorded") else "none",
                    "enforce_login": False,
                    "waiting_room": False,
                    "allow_multiple_devices": True,
                },
            }
            
            # API request to create meeting
            headers = {
                "Authorization": f"Bearer {zoom_token}",
                "Content-Type": "application/json",
            }
            
            response = await self.http_client.post(
                f"{config.zoom_base_url}/users/{session_data['zoom_host_id']}/meetings",
                json=meeting_data,
                headers=headers,
            )
            response.raise_for_status()
            
            meeting_response = response.json()
            
            logger.info(
                "Created Zoom meeting %s for session %s",
                meeting_response["id"],
                session_data["session_name"],
            )
            
            return {
                "meeting_id": str(meeting_response["id"]),
                "meeting_uuid": meeting_response["uuid"],
                "join_url": meeting_response["join_url"],
                "start_url": meeting_response["start_url"],
                "password": meeting_response.get("password"),
                "host_id": session_data["zoom_host_id"],
            }
            
        except httpx.HTTPStatusError as e:
            logger.error("Zoom API error: %s - %s", e.response.status_code, e.response.text)
            raise ZoomLTIError(f"Failed to create Zoom meeting: {e.response.text}")
        except Exception as e:
            logger.error("Failed to create Zoom meeting: %s", e)
            raise ZoomLTIError(f"Failed to create Zoom meeting: {e}")

    def _generate_zoom_jwt(self, config: ZoomLTIConfig) -> str:
        """Generate JWT token for Zoom API authentication.
        
        Args:
            config: Zoom LTI configuration
            
        Returns:
            JWT token string
        """
        payload = {
            "iss": config.zoom_api_key,
            "exp": int(time.time()) + 3600,  # 1 hour expiration
            "iat": int(time.time()),
            "aud": "zoom",
            "appKey": config.zoom_api_key,
            "tokenExp": int(time.time()) + 3600,
            "alg": "HS256",
        }
        
        return jwt.encode(payload, config.zoom_api_secret, algorithm="HS256")

    def _generate_meeting_password(self) -> str:
        """Generate secure meeting password.
        
        Returns:
            6-digit numeric password
        """
        return f"{secrets.randbelow(900000) + 100000:06d}"

    async def handle_zoom_webhook(
        self,
        payload: Dict[str, Any],
        signature: str,
        config: ZoomLTIConfig,
    ) -> None:
        """Handle Zoom webhook events for attendance tracking.
        
        Args:
            payload: Webhook payload data
            signature: Webhook signature for verification
            config: Zoom LTI configuration
        """
        try:
            # Verify webhook signature
            if config.zoom_webhook_secret:
                self._verify_webhook_signature(payload, signature, config.zoom_webhook_secret)
            
            event_type = payload.get("event")
            meeting_data = payload.get("payload", {}).get("object", {})
            
            logger.info("Processing Zoom webhook event: %s", event_type)
            
            # Handle different event types
            if event_type == "meeting.participant_joined":
                await self._handle_participant_joined(meeting_data, config)
            elif event_type == "meeting.participant_left":
                await self._handle_participant_left(meeting_data, config)
            elif event_type == "meeting.started":
                await self._handle_meeting_started(meeting_data)
            elif event_type == "meeting.ended":
                await self._handle_meeting_ended(meeting_data)
            else:
                logger.info("Unhandled webhook event type: %s", event_type)
                
        except Exception as e:
            logger.error("Failed to process Zoom webhook: %s", e)
            raise ZoomLTIError(f"Webhook processing failed: {e}")

    def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str,
    ) -> None:
        """Verify Zoom webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Provided signature
            secret: Webhook secret
            
        Raises:
            ZoomLTIError: If signature verification fails
        """
        expected_signature = hmac.new(
            secret.encode(),
            json.dumps(payload, separators=(",", ":")).encode(),
            hashlib.sha256,
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise ZoomLTIError("Invalid webhook signature")

    async def _handle_participant_joined(
        self,
        meeting_data: Dict[str, Any],
        config: ZoomLTIConfig,
    ) -> None:
        """Handle participant joined event.
        
        Args:
            meeting_data: Meeting data from webhook
            config: LTI configuration
        """
        try:
            meeting_id = str(meeting_data.get("id"))
            participant = meeting_data.get("participant", {})
            
            # Find corresponding live session
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(LiveSession)
                    .where(LiveSession.zoom_meeting_id == meeting_id)
                    .where(LiveSession.lti_config_id == config.id)
                )
                live_session = result.scalar_one_or_none()
                
                if not live_session:
                    logger.warning("No live session found for Zoom meeting %s", meeting_id)
                    return
                
                # Create or update attendance record
                participant_id = participant.get("id")
                user_name = participant.get("user_name", "Unknown")
                email = participant.get("email")
                join_time = datetime.fromisoformat(
                    participant.get("join_time", datetime.utcnow().isoformat())
                )
                
                # Try to find existing attendance record
                existing_result = await session.execute(
                    select(AttendanceRecord)
                    .where(AttendanceRecord.session_id == live_session.id)
                    .where(AttendanceRecord.zoom_participant_id == participant_id)
                )
                existing_record = existing_result.scalar_one_or_none()
                
                if existing_record:
                    # Update existing record
                    existing_record.joined_at = join_time
                    existing_record.left_at = None
                    existing_record.attendance_status = "present"
                else:
                    # Create new attendance record
                    attendance_record = AttendanceRecord(
                        session_id=live_session.id,
                        user_id=uuid.uuid4(),  # Would map from LTI user ID
                        zoom_participant_id=participant_id,
                        participant_name=user_name,
                        participant_email=email,
                        joined_at=join_time,
                        attendance_status="present",
                        recorded_by="zoom_webhook",
                    )
                    session.add(attendance_record)
                
                await session.commit()
                
                logger.info(
                    "Recorded participant join: %s (%s) in session %s",
                    user_name,
                    participant_id,
                    live_session.id,
                )
                
        except Exception as e:
            logger.error("Failed to handle participant joined event: %s", e)

    async def _handle_participant_left(
        self,
        meeting_data: Dict[str, Any],
        config: ZoomLTIConfig,
    ) -> None:
        """Handle participant left event.
        
        Args:
            meeting_data: Meeting data from webhook
            config: LTI configuration
        """
        try:
            meeting_id = str(meeting_data.get("id"))
            participant = meeting_data.get("participant", {})
            participant_id = participant.get("id")
            
            leave_time = datetime.fromisoformat(
                participant.get("leave_time", datetime.utcnow().isoformat())
            )
            
            # Update attendance record
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(AttendanceRecord)
                    .join(LiveSession)
                    .where(LiveSession.zoom_meeting_id == meeting_id)
                    .where(AttendanceRecord.zoom_participant_id == participant_id)
                )
                attendance_record = result.scalar_one_or_none()
                
                if attendance_record:
                    attendance_record.left_at = leave_time
                    
                    # Calculate duration
                    if attendance_record.joined_at:
                        duration = (leave_time - attendance_record.joined_at).total_seconds() / 60
                        attendance_record.duration_minutes = int(duration)
                    
                    await session.commit()
                    
                    logger.info(
                        "Updated participant leave: %s in session %s",
                        participant_id,
                        attendance_record.session_id,
                    )
                
        except Exception as e:
            logger.error("Failed to handle participant left event: %s", e)

    async def _handle_meeting_started(self, meeting_data: Dict[str, Any]) -> None:
        """Handle meeting started event.
        
        Args:
            meeting_data: Meeting data from webhook
        """
        try:
            meeting_id = str(meeting_data.get("id"))
            start_time = datetime.fromisoformat(
                meeting_data.get("start_time", datetime.utcnow().isoformat())
            )
            
            # Update live session status
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(LiveSession)
                    .where(LiveSession.zoom_meeting_id == meeting_id)
                )
                live_session = result.scalar_one_or_none()
                
                if live_session:
                    live_session.status = "started"
                    live_session.actual_start = start_time
                    await session.commit()
                    
                    logger.info("Meeting %s started at %s", meeting_id, start_time)
                    
        except Exception as e:
            logger.error("Failed to handle meeting started event: %s", e)

    async def _handle_meeting_ended(self, meeting_data: Dict[str, Any]) -> None:
        """Handle meeting ended event.
        
        Args:
            meeting_data: Meeting data from webhook
        """
        try:
            meeting_id = str(meeting_data.get("id"))
            end_time = datetime.fromisoformat(
                meeting_data.get("end_time", datetime.utcnow().isoformat())
            )
            
            # Update live session status
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(LiveSession)
                    .where(LiveSession.zoom_meeting_id == meeting_id)
                )
                live_session = result.scalar_one_or_none()
                
                if live_session:
                    live_session.status = "ended"
                    live_session.actual_end = end_time
                    await session.commit()
                    
                    logger.info("Meeting %s ended at %s", meeting_id, end_time)
                    
        except Exception as e:
            logger.error("Failed to handle meeting ended event: %s", e)

    async def get_attendance_report(
        self,
        session_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Generate attendance report for a live session.
        
        Args:
            session_id: Live session ID
            
        Returns:
            Attendance report data
        """
        try:
            async with AsyncSession(engine) as session:
                # Get session details
                session_result = await session.execute(
                    select(LiveSession).where(LiveSession.id == session_id)
                )
                live_session = session_result.scalar_one_or_none()
                
                if not live_session:
                    raise ZoomLTIError(f"Live session {session_id} not found")
                
                # Get attendance records
                attendance_result = await session.execute(
                    select(AttendanceRecord)
                    .where(AttendanceRecord.session_id == session_id)
                    .order_by(AttendanceRecord.joined_at)
                )
                attendance_records = attendance_result.scalars().all()
                
                # Calculate statistics
                total_participants = len(attendance_records)
                present_count = len([r for r in attendance_records if r.attendance_status == "present"])
                
                average_duration = 0
                if attendance_records:
                    durations = [r.duration_minutes or 0 for r in attendance_records]
                    average_duration = sum(durations) / len(durations)
                
                # Status distribution
                status_distribution = {}
                for record in attendance_records:
                    status = record.attendance_status
                    status_distribution[status] = status_distribution.get(status, 0) + 1
                
                return {
                    "session_id": str(session_id),
                    "session_name": live_session.session_name,
                    "scheduled_start": live_session.scheduled_start.isoformat(),
                    "scheduled_end": live_session.scheduled_end.isoformat(),
                    "actual_start": live_session.actual_start.isoformat() if live_session.actual_start else None,
                    "actual_end": live_session.actual_end.isoformat() if live_session.actual_end else None,
                    "status": live_session.status,
                    "total_participants": total_participants,
                    "present_count": present_count,
                    "average_duration_minutes": round(average_duration, 2),
                    "status_distribution": status_distribution,
                    "attendance_records": [
                        {
                            "participant_name": record.participant_name,
                            "participant_email": record.participant_email,
                            "joined_at": record.joined_at.isoformat(),
                            "left_at": record.left_at.isoformat() if record.left_at else None,
                            "duration_minutes": record.duration_minutes,
                            "attendance_status": record.attendance_status,
                        }
                        for record in attendance_records
                    ],
                }
                
        except Exception as e:
            logger.error("Failed to generate attendance report: %s", e)
            raise ZoomLTIError(f"Failed to generate attendance report: {e}")

    async def cleanup(self) -> None:
        """Clean up HTTP client resources."""
        await self.http_client.aclose()
