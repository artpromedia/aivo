"""Video transcoding tasks using FFmpeg for HLS output."""
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import boto3
import ffmpeg
from celery import current_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from .celery_app import celery_app
from ..database import DATABASE_URL
from ..models import HLSOutput, MediaUpload

logger = logging.getLogger(__name__)

# AWS S3 client
s3_client = boto3.client("s3")

# Database engine for workers
engine = create_async_engine(DATABASE_URL)


class TranscodingError(Exception):
    """Custom exception for transcoding errors."""
    pass


class HLSTranscoder:
    """FFmpeg-based HLS transcoder."""

    def __init__(self, temp_dir: Optional[str] = None) -> None:
        """Initialize transcoder.
        
        Args:
            temp_dir: Temporary directory for processing
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.supported_formats = {
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/webm",
            "video/x-ms-wmv",
            "video/x-flv",
        }

    def validate_input(self, file_path: str) -> Dict[str, any]:
        """Validate and probe input video file.
        
        Args:
            file_path: Path to input video file
            
        Returns:
            Video metadata dictionary
            
        Raises:
            TranscodingError: If file is invalid or unsupported
        """
        try:
            probe = ffmpeg.probe(file_path)
            
            # Find video stream
            video_stream = None
            for stream in probe["streams"]:
                if stream["codec_type"] == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                raise TranscodingError("No video stream found in input file")
            
            # Extract metadata
            metadata = {
                "duration": float(probe["format"].get("duration", 0)),
                "bitrate": int(probe["format"].get("bit_rate", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                "codec": video_stream.get("codec_name", "unknown"),
                "format": probe["format"].get("format_name", "unknown"),
            }
            
            logger.info("Video metadata: %s", metadata)
            return metadata
            
        except ffmpeg.Error as e:
            logger.error("FFmpeg probe failed: %s", e)
            raise TranscodingError(f"Failed to probe input file: {e}")
        except Exception as e:
            logger.error("Unexpected error during probe: %s", e)
            raise TranscodingError(f"Unexpected error: {e}")

    def create_hls_variants(
        self,
        input_path: str,
        output_dir: str,
        variants: List[Dict[str, any]],
        segment_duration: float = 10.0,
    ) -> Dict[str, any]:
        """Create HLS variants with adaptive bitrate streaming.
        
        Args:
            input_path: Path to input video file
            output_dir: Directory for output files
            variants: List of quality variant configurations
            segment_duration: HLS segment duration in seconds
            
        Returns:
            Dictionary with transcoding results
        """
        try:
            # Validate input
            input_metadata = self.validate_input(input_path)
            
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Build FFmpeg command for multi-variant HLS
            input_stream = ffmpeg.input(input_path)
            
            # Create video streams for each variant
            video_streams = []
            variant_playlists = []
            
            for i, variant in enumerate(variants):
                quality_label = variant["quality_label"]
                width = variant["resolution_width"]
                height = variant["resolution_height"]
                bitrate = variant["bitrate"]
                
                # Scale video to target resolution
                video = input_stream.video.filter(
                    "scale",
                    width,
                    height,
                    force_original_aspect_ratio="decrease",
                    force_divisible_by=2,
                )
                
                # Set video encoding parameters
                video_encoded = video.output(
                    f"{output_dir}/variant_{i}.m3u8",
                    vcodec="libx264",
                    acodec="aac",
                    video_bitrate=bitrate,
                    audio_bitrate="128k",
                    format="hls",
                    hls_time=segment_duration,
                    hls_playlist_type="vod",
                    hls_segment_filename=f"{output_dir}/variant_{i}_%03d.ts",
                    preset="medium",
                    crf=23,
                    maxrate=int(bitrate * 1.2),
                    bufsize=int(bitrate * 2),
                    x264opts="keyint=48:min-keyint=48:scenecut=-1",
                )
                
                video_streams.append(video_encoded)
                variant_playlists.append({
                    "quality_label": quality_label,
                    "playlist_file": f"variant_{i}.m3u8",
                    "resolution": f"{width}x{height}",
                    "bitrate": bitrate,
                })
            
            # Run FFmpeg transcoding
            logger.info("Starting FFmpeg transcoding for %d variants", len(variants))
            
            # Execute all variants in parallel
            for stream in video_streams:
                ffmpeg.run(stream, overwrite_output=True, quiet=False)
                
                # Update progress
                if current_task:
                    progress = (video_streams.index(stream) + 1) / len(video_streams) * 80
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "progress": progress,
                            "stage": f"Transcoding {variant_playlists[video_streams.index(stream)]['quality_label']}",
                        },
                    )
            
            # Create master playlist
            master_playlist_content = self._create_master_playlist(
                variant_playlists,
                input_metadata,
            )
            
            master_playlist_path = f"{output_dir}/master.m3u8"
            with open(master_playlist_path, "w") as f:
                f.write(master_playlist_content)
            
            # Count segments for each variant
            segment_counts = {}
            for i, variant in enumerate(variants):
                playlist_path = f"{output_dir}/variant_{i}.m3u8"
                segment_count = self._count_segments(playlist_path)
                segment_counts[f"variant_{i}"] = segment_count
            
            logger.info("HLS transcoding completed successfully")
            
            return {
                "master_playlist": "master.m3u8",
                "variant_playlists": variant_playlists,
                "segment_counts": segment_counts,
                "input_metadata": input_metadata,
                "output_directory": output_dir,
            }
            
        except ffmpeg.Error as e:
            logger.error("FFmpeg transcoding failed: %s", e)
            raise TranscodingError(f"Transcoding failed: {e}")
        except Exception as e:
            logger.error("Unexpected error during transcoding: %s", e)
            raise TranscodingError(f"Unexpected error: {e}")

    def _create_master_playlist(
        self,
        variants: List[Dict[str, any]],
        metadata: Dict[str, any],
    ) -> str:
        """Create HLS master playlist content.
        
        Args:
            variants: List of variant configurations
            metadata: Input video metadata
            
        Returns:
            Master playlist content as string
        """
        lines = ["#EXTM3U", "#EXT-X-VERSION:6"]
        
        for i, variant in enumerate(variants):
            # Add stream info
            lines.append(
                f"#EXT-X-STREAM-INF:BANDWIDTH={variant['bitrate']},"
                f"RESOLUTION={variant['resolution']},"
                f"CODECS=\"avc1.640028,mp4a.40.2\""
            )
            lines.append(variant["playlist_file"])
        
        return "\n".join(lines) + "\n"

    def _count_segments(self, playlist_path: str) -> int:
        """Count segments in an HLS playlist.
        
        Args:
            playlist_path: Path to playlist file
            
        Returns:
            Number of segments
        """
        try:
            with open(playlist_path, "r") as f:
                content = f.read()
            
            # Count .ts files referenced in playlist
            return content.count(".ts")
            
        except Exception as e:
            logger.warning("Failed to count segments in %s: %s", playlist_path, e)
            return 0


@celery_app.task(bind=True)
def transcode_to_hls(
    self,
    upload_id: str,
    quality_variants: List[Dict[str, any]],
    segment_duration: float = 10.0,
) -> Dict[str, any]:
    """Celery task to transcode video to HLS format.
    
    Args:
        upload_id: UUID of media upload
        quality_variants: List of quality variant configurations
        segment_duration: HLS segment duration in seconds
        
    Returns:
        Transcoding results dictionary
    """
    try:
        self.update_state(
            state="PROGRESS",
            meta={"progress": 0, "stage": "Initializing transcoding"},
        )
        
        # Create async session for database operations
        async def update_upload_status(status: str, error: Optional[str] = None) -> None:
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(MediaUpload).where(MediaUpload.id == uuid.UUID(upload_id))
                )
                upload = result.scalar_one_or_none()
                
                if upload:
                    upload.processing_status = status
                    if error:
                        upload.processing_error = error
                    if status == "processing":
                        upload.processing_started_at = datetime.utcnow()
                    elif status in ["completed", "failed"]:
                        upload.processing_completed_at = datetime.utcnow()
                    
                    await session.commit()
        
        # Update status to processing
        import asyncio
        asyncio.run(update_upload_status("processing"))
        
        self.update_state(
            state="PROGRESS",
            meta={"progress": 5, "stage": "Downloading source video"},
        )
        
        # Get upload record from database
        async def get_upload() -> Optional[MediaUpload]:
            async with AsyncSession(engine) as session:
                result = await session.execute(
                    select(MediaUpload).where(MediaUpload.id == uuid.UUID(upload_id))
                )
                return result.scalar_one_or_none()
        
        upload = asyncio.run(get_upload())
        if not upload:
            raise TranscodingError(f"Upload {upload_id} not found")
        
        # Create temporary directories
        temp_input_dir = tempfile.mkdtemp(prefix="media_input_")
        temp_output_dir = tempfile.mkdtemp(prefix="media_output_")
        
        try:
            # Download source file from S3
            input_file_path = os.path.join(temp_input_dir, upload.original_filename)
            
            logger.info("Downloading %s from S3", upload.s3_key)
            s3_client.download_file(
                upload.s3_bucket,
                upload.s3_key,
                input_file_path,
            )
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 15, "stage": "Starting transcoding"},
            )
            
            # Initialize transcoder
            transcoder = HLSTranscoder(temp_output_dir)
            
            # Transcode to HLS
            transcoding_results = transcoder.create_hls_variants(
                input_file_path,
                temp_output_dir,
                quality_variants,
                segment_duration,
            )
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 85, "stage": "Uploading HLS files to S3"},
            )
            
            # Upload HLS files to S3
            s3_upload_results = await upload_hls_to_s3(
                temp_output_dir,
                upload.s3_bucket,
                f"hls/{upload_id}",
                transcoding_results,
            )
            
            self.update_state(
                state="PROGRESS",
                meta={"progress": 95, "stage": "Saving HLS records to database"},
            )
            
            # Save HLS outputs to database
            async def save_hls_outputs() -> List[str]:
                async with AsyncSession(engine) as session:
                    output_ids = []
                    
                    for i, variant in enumerate(quality_variants):
                        hls_output = HLSOutput(
                            upload_id=upload.id,
                            quality_label=variant["quality_label"],
                            resolution_width=variant["resolution_width"],
                            resolution_height=variant["resolution_height"],
                            bitrate=variant["bitrate"],
                            master_playlist_s3_key=s3_upload_results["master_playlist_key"],
                            variant_playlist_s3_key=s3_upload_results["variant_keys"][f"variant_{i}"],
                            segment_prefix=s3_upload_results["segment_prefix"],
                            segment_count=transcoding_results["segment_counts"][f"variant_{i}"],
                            segment_duration=segment_duration,
                            transcoding_completed_at=datetime.utcnow(),
                        )
                        
                        session.add(hls_output)
                        output_ids.append(str(hls_output.id))
                    
                    await session.commit()
                    return output_ids
            
            hls_output_ids = asyncio.run(save_hls_outputs())
            
            # Update upload metadata
            async def update_upload_metadata() -> None:
                async with AsyncSession(engine) as session:
                    result = await session.execute(
                        select(MediaUpload).where(MediaUpload.id == uuid.UUID(upload_id))
                    )
                    upload_record = result.scalar_one_or_none()
                    
                    if upload_record:
                        metadata = transcoding_results["input_metadata"]
                        upload_record.duration_seconds = metadata.get("duration")
                        upload_record.resolution_width = metadata.get("width")
                        upload_record.resolution_height = metadata.get("height")
                        upload_record.frame_rate = metadata.get("fps")
                        upload_record.bitrate = metadata.get("bitrate")
                        upload_record.codec = metadata.get("codec")
                        upload_record.processing_status = "completed"
                        upload_record.processing_completed_at = datetime.utcnow()
                        
                        await session.commit()
            
            asyncio.run(update_upload_metadata())
            
            self.update_state(
                state="SUCCESS",
                meta={"progress": 100, "stage": "Transcoding completed"},
            )
            
            logger.info("HLS transcoding completed for upload %s", upload_id)
            
            return {
                "upload_id": upload_id,
                "status": "completed",
                "hls_output_ids": hls_output_ids,
                "master_playlist_key": s3_upload_results["master_playlist_key"],
                "variant_count": len(quality_variants),
                "transcoding_results": transcoding_results,
            }
            
        finally:
            # Schedule cleanup task
            cleanup_temp_files.delay([temp_input_dir, temp_output_dir])
    
    except Exception as e:
        logger.error("Transcoding failed for upload %s: %s", upload_id, e)
        
        # Update upload status to failed
        try:
            asyncio.run(update_upload_status("failed", str(e)))
        except Exception as db_e:
            logger.error("Failed to update upload status: %s", db_e)
        
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "stage": "Transcoding failed"},
        )
        
        raise TranscodingError(str(e))


async def upload_hls_to_s3(
    local_dir: str,
    bucket: str,
    s3_prefix: str,
    transcoding_results: Dict[str, any],
) -> Dict[str, any]:
    """Upload HLS files to S3.
    
    Args:
        local_dir: Local directory containing HLS files
        bucket: S3 bucket name
        s3_prefix: S3 key prefix
        transcoding_results: Results from transcoding
        
    Returns:
        Dictionary with S3 upload results
    """
    try:
        upload_results = {
            "master_playlist_key": f"{s3_prefix}/master.m3u8",
            "variant_keys": {},
            "segment_prefix": s3_prefix,
            "uploaded_files": [],
        }
        
        # Upload master playlist
        master_playlist_path = os.path.join(local_dir, "master.m3u8")
        s3_client.upload_file(
            master_playlist_path,
            bucket,
            upload_results["master_playlist_key"],
            ExtraArgs={"ContentType": "application/vnd.apple.mpegurl"},
        )
        upload_results["uploaded_files"].append(upload_results["master_playlist_key"])
        
        # Upload variant playlists and segments
        for i, variant in enumerate(transcoding_results["variant_playlists"]):
            variant_key = f"{s3_prefix}/variant_{i}.m3u8"
            variant_path = os.path.join(local_dir, f"variant_{i}.m3u8")
            
            # Upload variant playlist
            s3_client.upload_file(
                variant_path,
                bucket,
                variant_key,
                ExtraArgs={"ContentType": "application/vnd.apple.mpegurl"},
            )
            upload_results["variant_keys"][f"variant_{i}"] = variant_key
            upload_results["uploaded_files"].append(variant_key)
            
            # Upload segments for this variant
            segment_files = [
                f for f in os.listdir(local_dir)
                if f.startswith(f"variant_{i}_") and f.endswith(".ts")
            ]
            
            for segment_file in segment_files:
                segment_path = os.path.join(local_dir, segment_file)
                segment_key = f"{s3_prefix}/{segment_file}"
                
                s3_client.upload_file(
                    segment_path,
                    bucket,
                    segment_key,
                    ExtraArgs={"ContentType": "video/MP2T"},
                )
                upload_results["uploaded_files"].append(segment_key)
        
        logger.info(
            "Uploaded %d HLS files to S3 bucket %s",
            len(upload_results["uploaded_files"]),
            bucket,
        )
        
        return upload_results
        
    except Exception as e:
        logger.error("Failed to upload HLS files to S3: %s", e)
        raise TranscodingError(f"S3 upload failed: {e}")


@celery_app.task
def cleanup_temp_files(directories: List[str]) -> None:
    """Clean up temporary directories.
    
    Args:
        directories: List of directory paths to clean up
    """
    for directory in directories:
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                logger.info("Cleaned up temporary directory: %s", directory)
        except Exception as e:
            logger.warning("Failed to clean up directory %s: %s", directory, e)


@celery_app.task
def monitor_transcoding_progress() -> None:
    """Monitor and update transcoding progress for stuck tasks."""
    # This task can be scheduled to run periodically to check
    # for stuck transcoding tasks and update their status
    logger.info("Monitoring transcoding progress")
    
    # Implementation would check for uploads with processing status
    # that have been stuck for too long and mark them as failed
