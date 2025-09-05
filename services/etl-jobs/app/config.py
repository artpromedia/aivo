"""Configuration settings for ETL jobs service."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ETL Jobs configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Basic service settings
    service_name: str = "etl-jobs"
    version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")

    # Kafka/Redpanda settings
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    kafka_topic_events_raw: str = Field(
        default="events_raw",
        description="Source topic for raw events",
    )
    kafka_consumer_group: str = Field(
        default="etl-snowflake",
        description="Consumer group for ETL processing",
    )
    kafka_auto_offset_reset: str = Field(
        default="earliest",
        description="Auto offset reset policy",
    )

    # AWS S3 settings
    aws_access_key_id: str = Field(default="", description="AWS access key")
    aws_secret_access_key: str = Field(
        default="", description="AWS secret key"
    )
    aws_region: str = Field(default="us-west-2", description="AWS region")
    s3_bucket_raw_events: str = Field(
        default="aivo-data-raw",
        description="S3 bucket for raw events",
    )
    s3_prefix_events: str = Field(
        default="events/",
        description="S3 prefix for event files",
    )

    # Parquet settings
    parquet_compression: str = Field(
        default="snappy",
        description="Parquet compression algorithm",
    )
    parquet_row_group_size: int = Field(
        default=100000,
        description="Parquet row group size",
    )
    batch_size: int = Field(
        default=10000,
        description="Batch size for processing events",
    )
    flush_interval_seconds: int = Field(
        default=300,  # 5 minutes
        description="How often to flush batches to S3",
    )

    # Snowflake settings
    snowflake_account: str = Field(
        default="",
        description="Snowflake account identifier",
    )
    snowflake_username: str = Field(
        default="",
        description="Snowflake username",
    )
    snowflake_password: str = Field(
        default="",
        description="Snowflake password",
    )
    snowflake_database: str = Field(
        default="AIVO_ANALYTICS",
        description="Snowflake database name",
    )
    snowflake_warehouse: str = Field(
        default="COMPUTE_WH",
        description="Snowflake warehouse name",
    )
    snowflake_schema_raw: str = Field(
        default="RAW",
        description="Schema for raw data",
    )
    snowflake_schema_analytics: str = Field(
        default="ANALYTICS",
        description="Schema for analytics models",
    )

    # Data retention settings
    raw_data_retention_months: int = Field(
        default=18,
        description="Raw data retention in months",
    )
    aggregate_data_retention_years: int = Field(
        default=7,
        description="Aggregate data retention in years",
    )

    # Processing settings
    worker_count: int = Field(
        default=4,
        description="Number of worker processes",
    )
    max_memory_mb: int = Field(
        default=2048,
        description="Maximum memory usage in MB",
    )


settings = Settings()
