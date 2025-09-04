"""CDN and asset management service."""
# pylint: disable=import-error

import logging
from uuid import UUID

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    # Mock classes for when boto3 is not available
    boto3 = None  # type: ignore
    Config = None  # type: ignore

    class ClientError(Exception):  # type: ignore
        """Mock ClientError when boto3 is not available."""

    class NoCredentialsError(Exception):  # type: ignore
        """Mock NoCredentialsError when boto3 is not available."""

    BOTO3_AVAILABLE = False

from .config import settings

logger = logging.getLogger(__name__)


class CDNService:
    """CDN service for managing asset URLs and presigning."""

    def __init__(self) -> None:
        """Initialize CDN service."""
        self.s3_client = None
        self.bucket_name = settings.s3_bucket
        self.cloudfront_domain = settings.cloudfront_domain
        self.url_expiry = settings.asset_url_expiry

        # Initialize S3 client
        self._init_s3_client()

    def _init_s3_client(self) -> None:
        """Initialize S3 client."""
        try:
            config = Config(
                region_name=settings.aws_region,
                retries={'max_attempts': 3}
            )

            # Configure for MinIO if endpoint URL is provided
            if settings.s3_endpoint_url:
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=settings.s3_endpoint_url,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    config=config,
                )
            else:
                # Use regular AWS S3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    config=config,
                )

            logger.info("S3 client initialized successfully")

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            self.s3_client = None
        except (ClientError, ValueError, TypeError) as e:
            logger.error("Failed to initialize S3 client: %s", e)
            self.s3_client = None

    async def generate_presigned_url(
        self,
        s3_key: str,
        method: str = 'GET',
        expires_in: int | None = None
    ) -> str | None:
        """Generate a presigned URL for an S3 object."""
        if not self.s3_client:
            logger.warning("S3 client not initialized")
            return None

        try:
            expiry = expires_in or self.url_expiry

            # Use CloudFront domain if available for GET requests
            if method == 'GET' and self.cloudfront_domain:
                # For CloudFront, we might need signed URLs with
                # custom policies. For now, return the CloudFront URL
                # (assuming public access)
                return f"https://{self.cloudfront_domain}/{s3_key}"

            # Generate presigned URL for S3
            url = self.s3_client.generate_presigned_url(
                f's3:{method.lower()}_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiry
            )

            logger.debug("Generated presigned URL for %s", s3_key)
            return url

        except ClientError as e:
            logger.error("Failed to generate presigned URL for %s: %s",
                         s3_key, e)
            return None
        except (ValueError, TypeError) as e:
            logger.error("Unexpected error generating presigned URL: %s", e)
            return None

    async def generate_upload_url(
        self,
        s3_key: str,
        content_type: str | None = None
    ) -> dict | None:
        """Generate a presigned URL for uploading an object."""
        if not self.s3_client:
            logger.warning("S3 client not initialized")
            return None

        try:
            conditions = []
            fields = {}

            if content_type:
                conditions.append({"Content-Type": content_type})
                fields["Content-Type"] = content_type

            # Generate presigned POST
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=self.url_expiry
            )

            logger.debug("Generated upload URL for %s", s3_key)
            return response

        except ClientError as e:
            logger.error("Failed to generate upload URL for %s: %s",
                         s3_key, e)
            return None
        except (ValueError, TypeError) as e:
            logger.error("Unexpected error generating upload URL: %s", e)
            return None

    async def check_object_exists(self, s3_key: str) -> bool:
        """Check if an object exists in S3."""
        if not self.s3_client:
            return False

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error("Error checking object existence for %s: %s",
                         s3_key, e)
            return False
        except (ValueError, TypeError) as e:
            logger.error("Unexpected error checking object existence: %s", e)
            return False

    async def delete_object(self, s3_key: str) -> bool:
        """Delete an object from S3."""
        if not self.s3_client:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info("Deleted object: %s", s3_key)
            return True
        except ClientError as e:
            logger.error("Failed to delete object %s: %s", s3_key, e)
            return False
        except (ValueError, TypeError) as e:
            logger.error("Unexpected error deleting object: %s", e)
            return False

    def generate_asset_key(
        self,
        lesson_id: UUID,
        version_id: UUID,
        filename: str
    ) -> str:
        """Generate a consistent S3 key for an asset."""
        # Format: lessons/{lesson_id}/versions/{version_id}/assets/{filename}
        return f"lessons/{lesson_id}/versions/{version_id}/assets/{filename}"

    async def health_check(self) -> bool:
        """Check if the CDN service is healthy."""
        if not self.s3_client:
            return False

        try:
            # Try to list objects in the bucket (limited to 1)
            self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )
            return True
        except (ClientError, NoCredentialsError, ValueError, TypeError) as e:
            logger.error("CDN health check failed: %s", e)
            return False


# Global CDN service instance
cdn_service = CDNService()
