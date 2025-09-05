"""Configuration settings for event collector service."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Basic service settings
    service_name: str = "event-collector-svc"
    version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Host to bind")
    port: int = Field(default=8005, description="HTTP port to bind")
    grpc_port: int = Field(default=9005, description="gRPC port to bind")

    # Redpanda/Kafka settings
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Kafka bootstrap servers",
    )
    kafka_topic_events_raw: str = Field(
        default="events_raw",
        description="Topic for raw events",
    )
    kafka_topic_dlq: str = Field(
        default="events_dlq",
        description="Dead letter queue topic",
    )
    kafka_client_id: str = Field(
        default="event-collector",
        description="Kafka client ID",
    )
    kafka_compression_type: str = Field(
        default="gzip",
        description="Kafka compression type",
    )
    kafka_batch_size: int = Field(
        default=16384,
        description="Kafka batch size in bytes",
    )
    kafka_linger_ms: int = Field(
        default=100,
        description="Kafka linger time in milliseconds",
    )
    kafka_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for Kafka operations",
    )
    kafka_retry_backoff_ms: int = Field(
        default=1000,
        description="Retry backoff time in milliseconds",
    )

    # Buffer settings
    buffer_directory: str = Field(
        default="./event_buffer",
        description="Directory for buffering events",
    )
    buffer_retention_hours: int = Field(
        default=24,
        description="Hours to retain buffered events",
    )
    buffer_max_size_mb: int = Field(
        default=1024,
        description="Maximum buffer size in MB",
    )
    buffer_flush_interval_seconds: int = Field(
        default=30,
        description="Buffer flush interval in seconds",
    )
    buffer_batch_size: int = Field(
        default=1000,
        description="Number of events to batch for processing",
    )

    # Event validation settings
    max_event_size_bytes: int = Field(
        default=1048576,  # 1MB
        description="Maximum size of a single event in bytes",
    )
    max_batch_size: int = Field(
        default=10000,
        description="Maximum number of events in a batch",
    )
    max_batch_size_bytes: int = Field(
        default=10485760,  # 10MB
        description="Maximum size of a batch in bytes",
    )

    # DLQ settings
    dlq_max_retries: int = Field(
        default=3,
        description="Maximum retries before sending to DLQ",
    )
    dlq_retry_delay_seconds: int = Field(
        default=60,
        description="Delay between DLQ retries in seconds",
    )

    # Health check settings
    health_check_interval_seconds: int = Field(
        default=30,
        description="Health check interval in seconds",
    )
    readiness_kafka_timeout_seconds: int = Field(
        default=5,
        description="Kafka readiness check timeout in seconds",
    )

    # Monitoring settings
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )
    metrics_port: int = Field(
        default=8006,
        description="Prometheus metrics port",
    )

    # Security settings
    api_key: str | None = Field(
        default=None,
        description="API key for HTTP endpoints",
    )
    grpc_auth_enabled: bool = Field(
        default=False,
        description="Enable gRPC authentication",
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)",
    )


settings = Settings()
