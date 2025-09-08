"""Event buffer service for reliable event storage and batching."""

import asyncio
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
import orjson  # pylint: disable=no-member
import structlog
from pendulum import now

from app.config import settings
from app.models import BufferStats, LearnerEvent

logger = structlog.get_logger(__name__)


class EventBuffer:
    """Manages on-disk buffering of events with 24h retention."""

    def __init__(self) -> None:
        """Initialize event buffer."""
        self.buffer_dir = Path(settings.buffer_directory)
        self.buffer_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._current_file: Path | None = None
        self._current_file_size = 0
        self._stats_cache: BufferStats | None = None
        self._stats_cache_time: datetime | None = None

    async def start(self) -> None:
        """Start the buffer service."""
        logger.info("Starting event buffer service")
        await self._cleanup_old_files()

        # Start background tasks
        asyncio.create_task(self._periodic_cleanup())
        asyncio.create_task(self._periodic_flush())

    async def add_events(self, events: list[LearnerEvent]) -> bool:
        """Add events to buffer."""
        if not events:
            return True

        async with self._lock:
            try:
                # Prepare event data
                event_data = {
                    "timestamp": now().isoformat(),
                    "batch_id": str(uuid.uuid4()),
                    "events": [event.dict() for event in events],
                }

                # Serialize to JSON
                # pylint: disable-next=no-member
                serialized = orjson.dumps(event_data)

                # Check if we need a new file
                if (
                    self._current_file is None
                    or self._current_file_size + len(serialized)
                    > settings.max_event_size_bytes
                ):
                    await self._rotate_file()

                # Write to current file
                async with aiofiles.open(self._current_file, "ab") as f:
                    await f.write(serialized + b"\n")

                self._current_file_size += len(serialized) + 1

                # Clear stats cache
                self._stats_cache = None

                logger.debug(
                    "Added events to buffer",
                    event_count=len(events),
                    file=str(self._current_file),
                    size=len(serialized),
                )

                return True

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to add events to buffer", error=str(e))
                return False

    async def get_batches(self, max_batches: int = 10) -> list[dict[str, Any]]:
        """Get batches of events from buffer for processing."""
        batches = []

        async with self._lock:
            # Get all buffer files (oldest first)
            files = sorted(
                self.buffer_dir.glob("events_*.jsonl"),
                key=lambda f: f.stat().st_mtime,
            )

            for file_path in files[:max_batches]:
                try:
                    async with aiofiles.open(file_path) as f:
                        content = await f.read()

                    # Parse JSON lines
                    for line in content.strip().split("\n"):
                        if line:
                            # pylint: disable-next=no-member
                            batch = orjson.loads(line)
                            batch["file_path"] = str(file_path)
                            batches.append(batch)

                            if len(batches) >= max_batches:
                                break

                    if len(batches) >= max_batches:
                        break

                # pylint: disable=broad-exception-caught
                except Exception as e:
                    logger.error(
                        "Failed to read buffer file",
                        file=str(file_path),
                        error=str(e),
                    )

        return batches

    async def remove_batch(self, file_path: str, batch_id: str) -> bool:
        """Remove a specific batch from buffer after successful processing."""
        try:
            path = Path(file_path)
            if not path.exists():
                return True  # Already removed

            # Read file content
            async with aiofiles.open(path) as f:
                lines = (await f.read()).strip().split("\n")

            # Filter out the processed batch
            remaining_lines = []
            for line in lines:
                if line:
                    try:
                        # pylint: disable-next=no-member
                        batch = orjson.loads(line)
                        if batch.get("batch_id") != batch_id:
                            remaining_lines.append(line)
                    # pylint: disable=broad-exception-caught
                    except Exception:
                        # Keep malformed lines for manual review
                        remaining_lines.append(line)

            if not remaining_lines:
                # Remove empty file
                path.unlink(missing_ok=True)
                logger.debug("Removed empty buffer file", file=str(path))
            else:
                # Write back remaining content
                async with aiofiles.open(path, "w") as f:
                    await f.write("\n".join(remaining_lines) + "\n")

            # Clear stats cache
            self._stats_cache = None

            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to remove batch from buffer",
                file_path=file_path,
                batch_id=batch_id,
                error=str(e),
            )
            return False

    async def get_stats(self) -> BufferStats:
        """Get buffer statistics."""
        # Use cached stats if recent
        if (
            self._stats_cache
            and self._stats_cache_time
            and (datetime.utcnow() - self._stats_cache_time).seconds < 30
        ):
            return self._stats_cache

        try:
            files = list(self.buffer_dir.glob("events_*.jsonl"))
            total_events = 0
            total_size = 0
            oldest_event = None
            newest_event = None

            for file_path in files:
                try:
                    stat = file_path.stat()
                    total_size += stat.st_size

                    # Sample first and last events for time range
                    async with aiofiles.open(file_path) as f:
                        lines = (await f.read()).strip().split("\n")

                    for line in lines:
                        if line:
                            try:
                                # pylint: disable-next=no-member
                                batch = orjson.loads(line)
                                total_events += len(batch.get("events", []))

                                # Track time range
                                timestamp_str = batch.get("timestamp")
                                if timestamp_str:
                                    timestamp = datetime.fromisoformat(
                                        timestamp_str.replace("Z", "+00:00")
                                    )
                                    if (
                                        oldest_event is None
                                        or timestamp < oldest_event
                                    ):
                                        oldest_event = timestamp
                                    if (
                                        newest_event is None
                                        or timestamp > newest_event
                                    ):
                                        newest_event = timestamp
                            # pylint: disable=broad-exception-caught
                            except Exception:
                                continue

                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.warning(
                        "Failed to process buffer file for stats",
                        file=str(file_path),
                        error=str(e),
                    )

            stats = BufferStats(
                total_events=total_events,
                size_bytes=total_size,
                oldest_event=oldest_event,
                newest_event=newest_event,
                files_count=len(files),
            )

            # Cache stats
            self._stats_cache = stats
            self._stats_cache_time = datetime.utcnow()

            return stats

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to calculate buffer stats", error=str(e))
            return BufferStats(
                total_events=0,
                size_bytes=0,
                oldest_event=None,
                newest_event=None,
                files_count=0,
            )

    async def _rotate_file(self) -> None:
        """Rotate to a new buffer file."""
        timestamp = now().format("YYYYMMDD_HHmmss")
        filename = f"events_{timestamp}_{uuid.uuid4().hex[:8]}.jsonl"
        self._current_file = self.buffer_dir / filename
        self._current_file_size = 0

        logger.debug(
            "Rotated to new buffer file", file=str(self._current_file)
        )

    async def _cleanup_old_files(self) -> None:
        """Clean up files older than retention period."""
        cutoff_time = now().subtract(hours=settings.buffer_retention_hours)
        removed_count = 0

        for file_path in self.buffer_dir.glob("events_*.jsonl"):
            try:
                stat = file_path.stat()
                file_time = datetime.fromtimestamp(stat.st_mtime)

                if file_time < cutoff_time.naive:
                    file_path.unlink()
                    removed_count += 1
                    logger.debug(
                        "Removed old buffer file", file=str(file_path)
                    )

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    "Failed to remove old buffer file",
                    file=str(file_path),
                    error=str(e),
                )

        if removed_count > 0:
            logger.info("Cleaned up old buffer files", count=removed_count)
            self._stats_cache = None  # Clear cache

    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old files."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self._cleanup_old_files()
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error in periodic cleanup", error=str(e))

    async def _periodic_flush(self) -> None:
        """Periodic flush of buffer to ensure data persistence."""
        while True:
            try:
                await asyncio.sleep(settings.buffer_flush_interval_seconds)

                # Force rotation if current file is too old
                if self._current_file:
                    try:
                        stat = self._current_file.stat()
                        file_age = datetime.utcnow() - datetime.fromtimestamp(
                            stat.st_mtime
                        )

                        if file_age.total_seconds() > 300:  # 5 minutes
                            async with self._lock:
                                await self._rotate_file()

                    # pylint: disable=broad-exception-caught
                    except Exception:
                        pass  # File might not exist yet

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error in periodic flush", error=str(e))

    async def clear_all(self) -> None:
        """Clear all buffered events (for testing/emergency)."""
        async with self._lock:
            try:
                shutil.rmtree(self.buffer_dir)
                self.buffer_dir.mkdir(parents=True, exist_ok=True)
                self._current_file = None
                self._current_file_size = 0
                self._stats_cache = None
                logger.warning("Cleared all buffered events")
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to clear buffer", error=str(e))
