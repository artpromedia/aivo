"""S3 service for writing Parquet files."""

import asyncio
import io
import uuid
from datetime import datetime
from typing import Any

import boto3

# pylint: disable=import-error
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

# pylint: disable=import-error,no-name-in-module
from app.config import settings
from app.models import RawEvent
from botocore.exceptions import ClientError, NoCredentialsError

logger = structlog.get_logger(__name__)


class S3ParquetWriter:
    """S3 service for writing events as Parquet files."""

    def __init__(self) -> None:
        """Initialize S3 client."""
        self.s3_client = None
        self._session = None
        self._initialize_client()

        # Metrics
        self._metrics = {
            "files_written": 0,
            "events_written": 0,
            "bytes_written": 0,
            "write_errors": 0,
            "last_write_time": None,
        }

    def _initialize_client(self) -> None:
        """Initialize boto3 S3 client."""
        try:
            self._session = boto3.Session(
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
            )
            self.s3_client = self._session.client("s3")
            logger.info("S3 client initialized", region=settings.aws_region)
        except NoCredentialsError:
            logger.warning("AWS credentials not found, using default provider chain")
            self.s3_client = boto3.client("s3", region_name=settings.aws_region)
        except Exception as e:
            logger.error("Failed to initialize S3 client", error=str(e))
            raise

    async def write_events_to_s3(self, events: list[RawEvent]) -> str | None:
        """Write events to S3 as Parquet file.

        Args:
            events: List of events to write

        Returns:
            S3 key of written file or None if failed
        """
        if not events:
            return None

        try:
            # Generate S3 key with partitioning
            partition_date = events[0].partition_date or datetime.now().strftime("%Y-%m-%d")
            batch_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            s3_key = (
                f"{settings.s3_prefix_events}"
                f"year={partition_date[:4]}/"
                f"month={partition_date[5:7]}/"
                f"day={partition_date[8:10]}/"
                f"events_{timestamp}_{batch_id}.parquet"
            )

            # Convert events to DataFrame
            event_dicts = [event.model_dump() for event in events]
            df = pd.DataFrame(event_dicts)

            # Optimize data types
            df = self._optimize_dataframe(df)

            # Convert to Parquet
            parquet_buffer = io.BytesIO()
            table = pa.Table.from_pandas(df)

            pq.write_table(
                table,
                parquet_buffer,
                compression=settings.parquet_compression,
                row_group_size=settings.parquet_row_group_size,
                use_dictionary=True,
                write_statistics=True,
            )

            # Upload to S3
            parquet_buffer.seek(0)
            file_size = len(parquet_buffer.getvalue())

            await asyncio.get_event_loop().run_in_executor(
                None,
                self._upload_to_s3,
                settings.s3_bucket_raw_events,
                s3_key,
                parquet_buffer.getvalue(),
                file_size,
            )

            # Update metrics
            self._metrics["files_written"] += 1
            self._metrics["events_written"] += len(events)
            self._metrics["bytes_written"] += file_size
            self._metrics["last_write_time"] = datetime.now()

            logger.info(
                "Successfully wrote events to S3",
                s3_key=s3_key,
                event_count=len(events),
                file_size_bytes=file_size,
                bucket=settings.s3_bucket_raw_events,
            )

            return s3_key

        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Failed to write events to S3", error=str(e), event_count=len(events))
            self._metrics["write_errors"] += 1
            return None

    def _upload_to_s3(self, bucket: str, key: str, data: bytes, size: int) -> None:
        """Upload data to S3 (synchronous)."""
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType="application/octet-stream",
                Metadata={
                    "source": "etl-jobs",
                    "format": "parquet",
                    "compression": settings.parquet_compression,
                    "size_bytes": str(size),
                },
            )
        except ClientError as e:
            logger.error("S3 upload failed", error=str(e), bucket=bucket, key=key, size_bytes=size)
            raise

    def _optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame for Parquet storage."""
        # Convert timestamp columns to proper datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        if "processed_at" in df.columns:
            df["processed_at"] = pd.to_datetime(df["processed_at"])

        # Convert string columns to category where appropriate
        categorical_columns = ["event_type", "version", "partition_date"]
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype("category")

        # Ensure consistent data types
        if "learner_id" in df.columns:
            df["learner_id"] = df["learner_id"].astype("string")
        if "event_id" in df.columns:
            df["event_id"] = df["event_id"].astype("string")
        if "session_id" in df.columns:
            df["session_id"] = df["session_id"].astype("string")

        return df

    async def health_check(self) -> dict[str, Any]:
        """Check S3 connectivity."""
        try:
            # Try to list objects in the bucket (limit 1 to minimize cost)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.s3_client.list_objects_v2(
                    Bucket=settings.s3_bucket_raw_events, MaxKeys=1
                ),
            )

            return {
                "status": "healthy",
                "s3_connected": True,
                "bucket": settings.s3_bucket_raw_events,
                "metrics": self._metrics.copy(),
            }
        # pylint: disable=broad-exception-caught
        except Exception as e:
            return {
                "status": "unhealthy",
                "s3_connected": False,
                "error": str(e),
                "bucket": settings.s3_bucket_raw_events,
                "metrics": self._metrics.copy(),
            }

    def get_metrics(self) -> dict[str, Any]:
        """Get S3 writer metrics."""
        return self._metrics.copy()
