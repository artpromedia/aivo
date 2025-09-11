"""OpenAI Whisper integration for audio transcription."""
import asyncio
import io
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import boto3
import httpx
from openai import AsyncOpenAI
from pydub import AudioSegment

from ..schemas import WhisperConfig

logger = logging.getLogger(__name__)


class WhisperExtractor:
    """OpenAI Whisper client for audio transcription."""

    def __init__(
        self,
        openai_api_key: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ) -> None:
        """Initialize Whisper extractor.
        
        Args:
            openai_api_key: OpenAI API key
            aws_access_key_id: AWS access key ID for S3 access
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name
        """
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
            )
        except Exception as e:
            logger.warning("S3 client initialization failed: %s", e)
            self.s3_client = None

        # Supported audio formats for Whisper
        self.supported_formats = {
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/wave",
            "audio/flac",
            "audio/m4a",
            "audio/aac",
            "audio/ogg",
            "audio/webm",
            "video/mp4",
            "video/mpeg",
            "video/quicktime",
            "video/webm",
        }

        # Max file size for Whisper API (25MB)
        self.max_file_size = 25 * 1024 * 1024

    async def transcribe_from_s3(
        self,
        bucket: str,
        key: str,
        config: Optional[WhisperConfig] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Transcribe audio file from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            config: Whisper configuration
            
        Returns:
            Tuple of (transcribed_text, metadata)
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If transcription fails
        """
        if config is None:
            config = WhisperConfig()

        if not self.s3_client:
            raise RuntimeError("S3 client not available")

        try:
            # Get file metadata
            metadata = await self._get_s3_metadata(bucket, key)
            file_size = metadata.get("ContentLength", 0)
            content_type = metadata.get("ContentType", "")

            logger.info(
                "Processing audio: %s/%s (size: %d, type: %s)",
                bucket,
                key,
                file_size,
                content_type,
            )

            # Validate file format
            if not self._is_supported_format(content_type):
                raise ValueError(f"Unsupported audio format: {content_type}")

            # Download and process file
            if file_size > self.max_file_size:
                return await self._transcribe_large_file(bucket, key, config)
            else:
                return await self._transcribe_small_file(bucket, key, config)

        except Exception as e:
            logger.error("Audio transcription failed: %s", e)
            raise

    async def transcribe_from_url(
        self,
        url: str,
        config: Optional[WhisperConfig] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Transcribe audio from URL.
        
        Args:
            url: URL to audio file
            config: Whisper configuration
            
        Returns:
            Tuple of (transcribed_text, metadata)
        """
        if config is None:
            config = WhisperConfig()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                
                audio_data = response.content
                content_type = response.headers.get("content-type", "")

                if not self._is_supported_format(content_type):
                    raise ValueError(f"Unsupported audio format: {content_type}")

                if len(audio_data) > self.max_file_size:
                    return await self._transcribe_large_audio_data(
                        audio_data,
                        config,
                    )
                else:
                    return await self._transcribe_audio_data(audio_data, config)

        except Exception as e:
            logger.error("URL transcription failed: %s", e)
            raise

    async def _get_s3_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get S3 object metadata."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.s3_client.head_object,
            {"Bucket": bucket, "Key": key},
        )
        return response

    async def _download_from_s3(self, bucket: str, key: str) -> bytes:
        """Download file from S3."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.s3_client.get_object,
            {"Bucket": bucket, "Key": key},
        )
        return response["Body"].read()

    async def _transcribe_small_file(
        self,
        bucket: str,
        key: str,
        config: WhisperConfig,
    ) -> Tuple[str, Dict[str, Any]]:
        """Transcribe small audio file directly."""
        audio_data = await self._download_from_s3(bucket, key)
        return await self._transcribe_audio_data(audio_data, config)

    async def _transcribe_large_file(
        self,
        bucket: str,
        key: str,
        config: WhisperConfig,
    ) -> Tuple[str, Dict[str, Any]]:
        """Transcribe large audio file by chunking."""
        audio_data = await self._download_from_s3(bucket, key)
        return await self._transcribe_large_audio_data(audio_data, config)

    async def _transcribe_audio_data(
        self,
        audio_data: bytes,
        config: WhisperConfig,
    ) -> Tuple[str, Dict[str, Any]]:
        """Transcribe audio data using Whisper API."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = Path(temp_file.name)

        try:
            with open(temp_file_path, "rb") as audio_file:
                transcription_params = {
                    "file": audio_file,
                    "model": config.model,
                    "response_format": config.response_format,
                    "temperature": config.temperature,
                }

                if config.language:
                    transcription_params["language"] = config.language

                if (
                    config.response_format == "verbose_json"
                    and config.timestamp_granularities
                ):
                    transcription_params["timestamp_granularities"] = (
                        config.timestamp_granularities
                    )

                response = await self.openai_client.audio.transcriptions.create(
                    **transcription_params,
                )

                return self._process_whisper_response(response, config)

        finally:
            # Clean up temporary file
            temp_file_path.unlink(missing_ok=True)

    async def _transcribe_large_audio_data(
        self,
        audio_data: bytes,
        config: WhisperConfig,
    ) -> Tuple[str, Dict[str, Any]]:
        """Transcribe large audio by splitting into chunks."""
        # Load audio using pydub
        audio = AudioSegment.from_file(io.BytesIO(audio_data))
        
        # Split into 20-minute chunks (Whisper works best with shorter segments)
        chunk_length_ms = 20 * 60 * 1000  # 20 minutes
        chunks = [
            audio[i : i + chunk_length_ms]
            for i in range(0, len(audio), chunk_length_ms)
        ]

        logger.info("Splitting large audio into %d chunks", len(chunks))

        all_transcripts = []
        all_segments = []
        total_duration = 0.0
        chunk_metadata = []

        for i, chunk in enumerate(chunks):
            try:
                # Export chunk to temporary file
                with tempfile.NamedTemporaryFile(
                    suffix=".wav",
                    delete=False,
                ) as temp_file:
                    chunk.export(temp_file.name, format="wav")
                    temp_file_path = Path(temp_file.name)

                try:
                    with open(temp_file_path, "rb") as audio_file:
                        transcription_params = {
                            "file": audio_file,
                            "model": config.model,
                            "response_format": config.response_format,
                            "temperature": config.temperature,
                        }

                        if config.language:
                            transcription_params["language"] = config.language

                        if (
                            config.response_format == "verbose_json"
                            and config.timestamp_granularities
                        ):
                            transcription_params["timestamp_granularities"] = (
                                config.timestamp_granularities
                            )

                        response = await self.openai_client.audio.transcriptions.create(
                            **transcription_params,
                        )

                        chunk_text, chunk_meta = self._process_whisper_response(
                            response,
                            config,
                        )

                        all_transcripts.append(chunk_text)
                        chunk_metadata.append(
                            {
                                "chunk_index": i,
                                "chunk_duration": len(chunk) / 1000.0,
                                "start_time": total_duration,
                                "metadata": chunk_meta,
                            },
                        )

                        # Adjust timestamps for segments
                        if "segments" in chunk_meta:
                            for segment in chunk_meta["segments"]:
                                segment["start"] += total_duration
                                segment["end"] += total_duration
                                all_segments.append(segment)

                        total_duration += len(chunk) / 1000.0

                finally:
                    temp_file_path.unlink(missing_ok=True)

            except Exception as e:
                logger.error("Failed to transcribe chunk %d: %s", i, e)
                all_transcripts.append(f"[TRANSCRIPTION ERROR: {e}]")

        # Combine results
        full_transcript = " ".join(all_transcripts)
        
        combined_metadata = {
            "transcription_method": "chunked",
            "total_chunks": len(chunks),
            "total_duration": total_duration,
            "chunks": chunk_metadata,
            "segments": all_segments,
            "language": chunk_metadata[0]["metadata"].get("language") if chunk_metadata else None,
            "model": config.model,
        }

        logger.info(
            "Large file transcription completed: %.2f minutes, %d chunks",
            total_duration / 60,
            len(chunks),
        )

        return full_transcript, combined_metadata

    def _process_whisper_response(
        self,
        response: Any,
        config: WhisperConfig,
    ) -> Tuple[str, Dict[str, Any]]:
        """Process Whisper API response."""
        if config.response_format == "verbose_json":
            transcript = response.text
            metadata = {
                "transcription_method": "direct",
                "language": getattr(response, "language", None),
                "duration": getattr(response, "duration", None),
                "segments": getattr(response, "segments", []),
                "words": getattr(response, "words", []) if hasattr(response, "words") else [],
                "model": config.model,
                "temperature": config.temperature,
            }
        else:
            transcript = str(response)
            metadata = {
                "transcription_method": "direct",
                "model": config.model,
                "temperature": config.temperature,
                "response_format": config.response_format,
            }

        return transcript, metadata

    def _is_supported_format(self, content_type: str) -> bool:
        """Check if content type is supported by Whisper."""
        return content_type.lower() in self.supported_formats

    async def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages for Whisper.
        
        Returns:
            Dictionary mapping language codes to language names
        """
        # Whisper supported languages
        languages = {
            "af": "Afrikaans",
            "ar": "Arabic",
            "hy": "Armenian",
            "az": "Azerbaijani",
            "be": "Belarusian",
            "bs": "Bosnian",
            "bg": "Bulgarian",
            "ca": "Catalan",
            "zh": "Chinese",
            "hr": "Croatian",
            "cs": "Czech",
            "da": "Danish",
            "nl": "Dutch",
            "en": "English",
            "et": "Estonian",
            "fi": "Finnish",
            "fr": "French",
            "gl": "Galician",
            "de": "German",
            "el": "Greek",
            "he": "Hebrew",
            "hi": "Hindi",
            "hu": "Hungarian",
            "is": "Icelandic",
            "id": "Indonesian",
            "it": "Italian",
            "ja": "Japanese",
            "kn": "Kannada",
            "kk": "Kazakh",
            "ko": "Korean",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "mk": "Macedonian",
            "ms": "Malay",
            "mr": "Marathi",
            "mi": "Maori",
            "ne": "Nepali",
            "no": "Norwegian",
            "fa": "Persian",
            "pl": "Polish",
            "pt": "Portuguese",
            "ro": "Romanian",
            "ru": "Russian",
            "sr": "Serbian",
            "sk": "Slovak",
            "sl": "Slovenian",
            "es": "Spanish",
            "sw": "Swahili",
            "sv": "Swedish",
            "tl": "Tagalog",
            "ta": "Tamil",
            "th": "Thai",
            "tr": "Turkish",
            "uk": "Ukrainian",
            "ur": "Urdu",
            "vi": "Vietnamese",
            "cy": "Welsh",
        }
        
        return languages
