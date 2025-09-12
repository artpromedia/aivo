"""HLS playlist whitelist proxy for access control."""

import hashlib
import hmac
import logging
import secrets
import time
import uuid
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import engine
from ..models import HLSOutput, MediaUpload

logger = logging.getLogger(__name__)


class HLSProxyError(Exception):
    """Custom exception for HLS proxy errors."""

    pass


class PlaylistWhitelistProxy:
    """Proxy for HLS playlists with access control and token validation."""

    def __init__(self, secret_key: str, cdn_base_url: str) -> None:
        """Initialize HLS playlist proxy.

        Args:
            secret_key: Secret key for token generation/validation
            cdn_base_url: Base URL for CDN/S3 bucket
        """
        self.secret_key = secret_key.encode()
        self.cdn_base_url = cdn_base_url.rstrip("/")
        self.http_client = httpx.AsyncClient(timeout=30.0)

    def generate_access_token(
        self,
        video_id: uuid.UUID,
        user_id: uuid.UUID,
        expires_in: int = 3600,
    ) -> str:
        """Generate secure access token for HLS content.

        Args:
            video_id: Video UUID
            user_id: User UUID
            expires_in: Token expiration in seconds

        Returns:
            Signed access token
        """
        expiry = int(time.time()) + expires_in
        nonce = secrets.token_hex(16)

        # Create payload
        payload = f"{video_id}:{user_id}:{expiry}:{nonce}"

        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key,
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"{payload}:{signature}"

    def verify_access_token(self, token: str) -> dict[str, Any]:
        """Verify and decode access token.

        Args:
            token: Access token to verify

        Returns:
            Decoded token data

        Raises:
            HLSProxyError: If token is invalid or expired
        """
        try:
            parts = token.split(":")
            if len(parts) != 5:
                raise HLSProxyError("Invalid token format")

            video_id, user_id, expiry_str, nonce, signature = parts

            # Verify signature
            payload = f"{video_id}:{user_id}:{expiry_str}:{nonce}"
            expected_signature = hmac.new(
                self.secret_key,
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                raise HLSProxyError("Invalid token signature")

            # Check expiration
            expiry = int(expiry_str)
            if time.time() > expiry:
                raise HLSProxyError("Token has expired")

            return {
                "video_id": uuid.UUID(video_id),
                "user_id": uuid.UUID(user_id),
                "expires_at": datetime.fromtimestamp(expiry),
                "nonce": nonce,
            }

        except (ValueError, TypeError) as e:
            raise HLSProxyError(f"Invalid token: {e}") from e

    async def check_video_access(
        self,
        video_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Check if user has access to video content.

        Args:
            video_id: Video UUID
            user_id: User UUID

        Returns:
            True if user has access
        """
        try:
            async with AsyncSession(engine) as session:
                # Get video details
                result = await session.execute(
                    select(MediaUpload).where(MediaUpload.id == video_id)
                )
                video = result.scalar_one_or_none()

                if not video:
                    logger.warning("Video %s not found", video_id)
                    return False

                # Check if video is available
                if video.status != "completed":
                    logger.warning("Video %s not ready (status: %s)", video_id, video.status)
                    return False

                # TODO: Implement organization/course-level access control
                # For now, allow access if video exists and is completed
                return True

        except Exception as e:
            logger.error("Failed to check video access: %s", e)
            return False

    async def proxy_master_playlist(
        self,
        video_id: uuid.UUID,
        token: str,
        request: Request,
    ) -> dict[str, Any]:
        """Proxy master HLS playlist with token validation.

        Args:
            video_id: Video UUID
            token: Access token
            request: FastAPI request object

        Returns:
            Playlist response data
        """
        try:
            # Verify access token
            token_data = self.verify_access_token(token)
            if token_data["video_id"] != video_id:
                raise HLSProxyError("Token video ID mismatch")

            # Check video access
            if not await self.check_video_access(video_id, token_data["user_id"]):
                raise HLSProxyError("Access denied")

            # Get HLS output details
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(HLSOutput).where(HLSOutput.upload_id == video_id)
                )
                hls_output = result.scalar_one_or_none()

                if not hls_output or not hls_output.master_playlist_url:
                    raise HLSProxyError("HLS playlist not available")

            # Fetch original playlist
            response = await self.http_client.get(hls_output.master_playlist_url)
            response.raise_for_status()

            original_playlist = response.text

            # Rewrite playlist URLs to include proxy
            proxied_playlist = self._rewrite_master_playlist(
                original_playlist,
                video_id,
                token,
                request,
            )

            return {
                "content": proxied_playlist,
                "content_type": "application/vnd.apple.mpegurl",
                "cache_control": "no-cache, no-store, must-revalidate",
            }

        except httpx.RequestError as e:
            logger.error("Failed to fetch master playlist: %s", e)
            raise HLSProxyError("Failed to fetch playlist") from e
        except Exception as e:
            logger.error("Master playlist proxy error: %s", e)
            raise HLSProxyError(f"Proxy error: {e}") from e

    async def proxy_variant_playlist(
        self,
        video_id: uuid.UUID,
        variant_path: str,
        token: str,
        request: Request,
    ) -> dict[str, Any]:
        """Proxy variant HLS playlist with token validation.

        Args:
            video_id: Video UUID
            variant_path: Path to variant playlist
            token: Access token
            request: FastAPI request object

        Returns:
            Playlist response data
        """
        try:
            # Verify access token
            token_data = self.verify_access_token(token)
            if token_data["video_id"] != video_id:
                raise HLSProxyError("Token video ID mismatch")

            # Check video access
            if not await self.check_video_access(video_id, token_data["user_id"]):
                raise HLSProxyError("Access denied")

            # Construct full URL to variant playlist
            playlist_url = f"{self.cdn_base_url}/{variant_path}"

            # Fetch original playlist
            response = await self.http_client.get(playlist_url)
            response.raise_for_status()

            original_playlist = response.text

            # Rewrite segment URLs to include proxy
            proxied_playlist = self._rewrite_variant_playlist(
                original_playlist,
                video_id,
                variant_path,
                token,
                request,
            )

            return {
                "content": proxied_playlist,
                "content_type": "application/vnd.apple.mpegurl",
                "cache_control": "no-cache, no-store, must-revalidate",
            }

        except httpx.RequestError as e:
            logger.error("Failed to fetch variant playlist: %s", e)
            raise HLSProxyError("Failed to fetch playlist") from e
        except Exception as e:
            logger.error("Variant playlist proxy error: %s", e)
            raise HLSProxyError(f"Proxy error: {e}") from e

    async def proxy_segment(
        self,
        video_id: uuid.UUID,
        segment_path: str,
        token: str,
    ) -> dict[str, Any]:
        """Proxy HLS segment with token validation.

        Args:
            video_id: Video UUID
            segment_path: Path to segment file
            token: Access token

        Returns:
            Segment response data
        """
        try:
            # Verify access token
            token_data = self.verify_access_token(token)
            if token_data["video_id"] != video_id:
                raise HLSProxyError("Token video ID mismatch")

            # Check video access
            if not await self.check_video_access(video_id, token_data["user_id"]):
                raise HLSProxyError("Access denied")

            # Construct full URL to segment
            segment_url = f"{self.cdn_base_url}/{segment_path}"

            # Fetch segment
            response = await self.http_client.get(segment_url)
            response.raise_for_status()

            return {
                "content": response.content,
                "content_type": "video/mp2t",
                "cache_control": "public, max-age=31536000",  # Cache segments for 1 year
            }

        except httpx.RequestError as e:
            logger.error("Failed to fetch segment: %s", e)
            raise HLSProxyError("Failed to fetch segment") from e
        except Exception as e:
            logger.error("Segment proxy error: %s", e)
            raise HLSProxyError(f"Proxy error: {e}") from e

    def _rewrite_master_playlist(
        self,
        playlist: str,
        video_id: uuid.UUID,
        token: str,
        request: Request,
    ) -> str:
        """Rewrite master playlist URLs to proxy through our service.

        Args:
            playlist: Original master playlist content
            video_id: Video UUID
            token: Access token
            request: FastAPI request object

        Returns:
            Rewritten playlist content
        """
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        lines = playlist.split("\n")
        rewritten_lines = []

        for line in lines:
            if line.startswith("#") or not line.strip():
                # Keep comments and empty lines as-is
                rewritten_lines.append(line)
            elif line.endswith(".m3u8"):
                # Rewrite variant playlist URLs
                variant_path = self._extract_relative_path(line)
                proxied_url = (
                    f"{base_url}/api/v1/media/hls/{video_id}/variant/{variant_path}?token={token}"
                )
                rewritten_lines.append(proxied_url)
            else:
                # Keep other lines as-is
                rewritten_lines.append(line)

        return "\n".join(rewritten_lines)

    def _rewrite_variant_playlist(
        self,
        playlist: str,
        video_id: uuid.UUID,
        variant_path: str,
        token: str,
        request: Request,
    ) -> str:
        """Rewrite variant playlist URLs to proxy through our service.

        Args:
            playlist: Original variant playlist content
            video_id: Video UUID
            variant_path: Path to variant playlist
            token: Access token
            request: FastAPI request object

        Returns:
            Rewritten playlist content
        """
        base_url = f"{request.url.scheme}://{request.url.netloc}"
        variant_dir = "/".join(variant_path.split("/")[:-1])

        lines = playlist.split("\n")
        rewritten_lines = []

        for line in lines:
            if line.startswith("#") or not line.strip():
                # Keep comments and empty lines as-is
                rewritten_lines.append(line)
            elif line.endswith(".ts"):
                # Rewrite segment URLs
                segment_path = f"{variant_dir}/{line}" if variant_dir else line
                proxied_url = (
                    f"{base_url}/api/v1/media/hls/{video_id}/segment/{segment_path}?token={token}"
                )
                rewritten_lines.append(proxied_url)
            else:
                # Keep other lines as-is
                rewritten_lines.append(line)

        return "\n".join(rewritten_lines)

    def _extract_relative_path(self, url: str) -> str:
        """Extract relative path from URL.

        Args:
            url: Full or relative URL

        Returns:
            Relative path
        """
        if url.startswith("http"):
            parsed = urlparse(url)
            return parsed.path.lstrip("/")
        return url

    async def cleanup(self) -> None:
        """Clean up HTTP client resources."""
        await self.http_client.aclose()
