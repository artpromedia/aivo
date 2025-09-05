# ETL Jobs Service

High-performance ETL pipeline for ingesting learner events from Redpanda,
processing them through S3 Parquet files, and loading them into Snowflake for
analytics.

## Architecture

```text
Redpanda (events_raw) → ETL Jobs → S3 (Parquet) → Snowpipe → Snowflake → Looker
```

## Features

- **Real-time Processing**: Consumes events from Redpanda with configurable
  batching
- **Parquet Storage**: Efficient columnar storage in S3 with compression and
  partitioning
- **Auto-ingestion**: Snowpipe automatically loads new files into Snowflake
- **Analytics Models**: Pre-built aggregations for minutes, sessions, and
  mastery tracking
- **Data Validation**: Comprehensive test fixtures and validation queries
- **Monitoring**: Health checks, metrics, and ETL job status tracking

## Components

### Core Services

- **Kafka Consumer** (`app/services/kafka_consumer.py`): Consumes events from Redpanda
- **S3 Writer** (`app/services/s3_writer.py`): Writes Parquet files to S3
- **ETL Processor** (`app/main.py`): Main orchestration service

### Data Models

- **Minute Metrics**: Minute-level activity aggregations
- **Session Metrics**: Session-level performance and completion tracking  
- **Mastery Deltas**: Learning mastery changes over time

### Infrastructure

- **Snowflake Setup** (`infra/snowflake/setup.sql`): Database, schemas, tables,
  and Snowpipe
- **Data Models** (`infra/snowflake/models.sql`): Transformation logic and
  stored procedures

## Configuration

### Environment Variables

```bash
# Kafka/Redpanda
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_EVENTS_RAW=events_raw
KAFKA_CONSUMER_GROUP=etl-snowflake

# AWS S3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2
S3_BUCKET_RAW_EVENTS=aivo-data-raw

# Snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USERNAME=your_username  
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=AIVO_ANALYTICS

# Processing
BATCH_SIZE=10000
FLUSH_INTERVAL_SECONDS=300
PARQUET_COMPRESSION=snappy
```

## Data Retention

- **Raw Events**: 18 months (automatic cleanup)
- **Aggregated Data**: 7 years  
- **Real-time Views**: Last 90 days for performance

## Development

### Setup

```bash
# Install dependencies
poetry install

# Setup pre-commit hooks
pre-commit install

# Run tests
poetry run pytest

# Run ETL processor
poetry run etl-jobs
```

### Data Validation

Test fixtures are provided in `fixtures/` for validation:

- `test_raw_events.csv` - Sample raw events
- `test_minute_metrics.csv` - Expected minute aggregations
- `test_session_metrics.csv` - Expected session metrics  
- `test_mastery_deltas.csv` - Expected mastery changes

## Deployment

### Infrastructure Setup

1. **Snowflake**: Run `infra/snowflake/setup.sql` to create database and schemas
2. **S3**: Create bucket and configure IAM permissions
3. **Snowpipe**: Configure S3 event notifications

### Service Deployment  

```bash
# Build container
docker build -t etl-jobs .

# Run with environment variables
docker run --env-file .env etl-jobs
```

## Monitoring

### Health Checks

```bash
# Check overall health
curl http://localhost:8080/health

# Get metrics  
curl http://localhost:8080/metrics
```

### ETL Job Status

Query `ANALYTICS.etl_job_status` table for job execution metrics:

```sql
SELECT 
    job_type,
    status,
    records_processed,
    started_at,
    completed_at
FROM ANALYTICS.etl_job_status
ORDER BY started_at DESC
LIMIT 10;
```

## Analytics Integration

### Looker Connection

1. Connect Looker to Snowflake `ANALYTICS` schema
2. Use pre-built views: `learner_activity_summary`, `content_mastery_trends`
3. Configure caching and performance optimization

### Key Metrics

- **Learner Engagement**: Daily events, time spent, session frequency
- **Content Performance**: Completion rates, assessment scores, mastery progression
- **System Health**: Processing latency, error rates, data quality

## Troubleshooting

### Common Issues

1. **Kafka Connection**: Check bootstrap servers and consumer group settings
2. **S3 Permissions**: Verify IAM roles and bucket policies  
3. **Snowpipe Issues**: Check file format and stage configuration
4. **Data Quality**: Run validation queries against test fixtures

### Logs

Structured logging with configurable levels:

```bash
# Set log level
export LOG_LEVEL=DEBUG

# View logs
docker logs etl-jobs -f
```
