# Analytics Schema Documentation

## Overview

This document describes the analytics data schema for the Aivo learning
platform. The schema is designed to support real-time analytics, business
intelligence, and data science workflows through a scalable Snowflake data
warehouse.

## Architecture

```text
Redpanda (events_raw topic) 
    ↓
S3 (Parquet files)
    ↓
Snowpipe (auto-ingestion)
    ↓
Snowflake RAW schema
    ↓
dbt/SQL transformations
    ↓
Snowflake ANALYTICS schema
    ↓
Looker dashboards
```

## Data Retention

- **Raw Events**: 18 months
- **Aggregated Data**: 7 years
- **Real-time Views**: Last 90 days (for performance)

## Schemas

### RAW Schema

Contains raw, unprocessed data as ingested from source systems.

#### `raw_events`

Primary table for all learner events ingested via Snowpipe from S3.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `learner_id` | STRING | Unique learner identifier | "learner_123" |
| `event_type` | STRING | Type of event | "lesson_complete" |
| `event_id` | STRING | Unique event identifier | "evt_456" |
| `session_id` | STRING | Session identifier | "session_789" |
| `timestamp` | TIMESTAMP_NTZ | Event timestamp (UTC) | 2025-09-05 10:30:00 |
| `data` | VARIANT | Event payload (JSON) | {"lesson_id": "lesson_001", "score": 85} |
| `metadata` | VARIANT | Event metadata (JSON) | {"source": "web_app", "ip": "192.168.1.1"} |
| `version` | STRING | Event schema version | "1.0" |
| `processed_at` | TIMESTAMP_NTZ | ETL processing time | 2025-09-05 10:31:00 |
| `partition_date` | DATE | Partition date (for clustering) | 2025-09-05 |
| `s3_path` | STRING | Source S3 file path | "events/2025/09/05/events_123.parquet" |

**Partitioning**: By `partition_date`
**Clustering**: By `partition_date, learner_id`

### ANALYTICS Schema

Contains processed, aggregated data optimized for analytics and reporting.

#### `minute_metrics`

Minute-level aggregated learner activity metrics.

| Column | Type | Description |
|--------|------|-------------|
| `learner_id` | STRING | Unique learner identifier |
| `minute_timestamp` | TIMESTAMP_NTZ | Minute boundary timestamp |
| `session_id` | STRING | Session identifier |
| `total_events` | NUMBER(10,0) | Total events in this minute |
| `page_views` | NUMBER(10,0) | Page view events |
| `interactions` | NUMBER(10,0) | Interaction events |
| `assessments_started` | NUMBER(10,0) | Assessments started |
| `assessments_completed` | NUMBER(10,0) | Assessments completed |
| `lessons_started` | NUMBER(10,0) | Lessons started |
| `lessons_completed` | NUMBER(10,0) | Lessons completed |
| `errors` | NUMBER(10,0) | Error events |
| `time_spent_seconds` | NUMBER(10,2) | Estimated time spent |
| `created_at` | TIMESTAMP_NTZ | Record creation time |
| `partition_date` | DATE | Partition date |

**Use Cases**:

- Real-time activity monitoring
- Time-on-task analysis
- Activity heatmaps
- Engagement trends

#### `session_metrics`

Session-level aggregated metrics and KPIs.

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | STRING | Unique session identifier |
| `learner_id` | STRING | Learner identifier |
| `session_start` | TIMESTAMP_NTZ | Session start time |
| `session_end` | TIMESTAMP_NTZ | Session end time |
| `duration_seconds` | NUMBER(10,2) | Total session duration |
| `total_events` | NUMBER(10,0) | Total events in session |
| `unique_pages` | NUMBER(10,0) | Unique pages visited |
| `total_interactions` | NUMBER(10,0) | Total interactions |
| `lessons_attempted` | NUMBER(10,0) | Lessons started |
| `lessons_completed` | NUMBER(10,0) | Lessons completed |
| `assessments_attempted` | NUMBER(10,0) | Assessments started |
| `assessments_completed` | NUMBER(10,0) | Assessments completed |
| `avg_assessment_score` | NUMBER(5,2) | Average assessment score |
| `completion_rate` | NUMBER(5,4) | Content completion rate (0-1) |
| `is_active` | BOOLEAN | Is session currently active |
| `last_activity` | TIMESTAMP_NTZ | Last activity timestamp |
| `created_at` | TIMESTAMP_NTZ | Record creation time |
| `updated_at` | TIMESTAMP_NTZ | Record update time |
| `partition_date` | DATE | Partition date |

**Use Cases**:

- Session analytics
- Learning progression tracking
- Completion rate analysis
- Performance dashboards

#### `mastery_deltas`

Tracks changes in learner mastery levels for content/skills.

| Column | Type | Description |
|--------|------|-------------|
| `learner_id` | STRING | Learner identifier |
| `content_id` | STRING | Content/skill identifier |
| `content_type` | STRING | Type of content (lesson, skill, assessment) |
| `previous_mastery` | NUMBER(5,4) | Previous mastery level (0-1) |
| `current_mastery` | NUMBER(5,4) | Current mastery level (0-1) |
| `mastery_delta` | NUMBER(5,4) | Change in mastery |
| `trigger_event_id` | STRING | Event that triggered the change |
| `trigger_event_type` | STRING | Type of trigger event |
| `session_id` | STRING | Session identifier |
| `confidence_score` | NUMBER(5,4) | Confidence in mastery calculation |
| `evidence_count` | NUMBER(10,0) | Number of evidence points |
| `timestamp` | TIMESTAMP_NTZ | When mastery changed |
| `created_at` | TIMESTAMP_NTZ | Record creation time |
| `partition_date` | DATE | Partition date |

**Use Cases**:

- Adaptive learning algorithms
- Mastery tracking
- Learning analytics
- Personalization engines

#### `etl_job_status`

Tracks ETL job execution status and metrics.

| Column | Type | Description |
|--------|------|-------------|
| `job_id` | STRING | Unique job identifier |
| `job_type` | STRING | Type of ETL job |
| `status` | STRING | Job status (pending, running, completed, failed) |
| `started_at` | TIMESTAMP_NTZ | Job start time |
| `completed_at` | TIMESTAMP_NTZ | Job completion time |
| `records_processed` | NUMBER(15,0) | Records processed |
| `records_failed` | NUMBER(15,0) | Records that failed |
| `bytes_processed` | NUMBER(20,0) | Bytes processed |
| `error_message` | STRING | Error message if failed |
| `retry_count` | NUMBER(5,0) | Number of retries |
| `created_at` | TIMESTAMP_NTZ | Record creation time |
| `updated_at` | TIMESTAMP_NTZ | Record update time |

## Views for Looker

### `learner_activity_summary`

Daily aggregated learner activity for the last 90 days.

```sql
SELECT 
    learner_id,
    activity_date,
    daily_events,
    hours_spent,
    sessions,
    lessons_completed,
    assessments_completed
FROM ANALYTICS.learner_activity_summary;
```

### `content_mastery_trends`

Content mastery trends for the last 30 days.

```sql
SELECT 
    content_id,
    content_type,
    mastery_date,
    learners_affected,
    avg_mastery_change,
    avg_current_mastery,
    avg_confidence
FROM ANALYTICS.content_mastery_trends;
```

## Data Validation

### Seed Fixtures

Test data fixtures are provided for validation:

#### `test_raw_events.csv`

Sample raw events covering all event types for testing transformations.

#### `test_minute_metrics.csv`

Expected minute-level aggregations for validation.

#### `test_session_metrics.csv`

Expected session metrics for validation.

#### `test_mastery_deltas.csv`

Expected mastery changes for validation.

### Validation Queries

```sql
-- Validate event counts match between raw and aggregated
SELECT 
    DATE(timestamp) as event_date,
    COUNT(*) as raw_count,
    SUM(mm.total_events) as aggregated_count
FROM RAW.raw_events re
LEFT JOIN ANALYTICS.minute_metrics mm ON 
    re.learner_id = mm.learner_id 
    AND DATE_TRUNC('MINUTE', re.timestamp) = mm.minute_timestamp
GROUP BY DATE(timestamp)
HAVING raw_count != aggregated_count;

-- Validate session duration calculations
SELECT 
    session_id,
    DATEDIFF('second', MIN(timestamp), MAX(timestamp)) as calculated_duration,
    sm.duration_seconds as stored_duration
FROM RAW.raw_events re
JOIN ANALYTICS.session_metrics sm ON re.session_id = sm.session_id
GROUP BY session_id, sm.duration_seconds
HAVING ABS(calculated_duration - stored_duration) > 60; -- Allow 1 minute tolerance
```

## Performance Optimization

### Clustering Keys

- All tables are clustered by `partition_date` for optimal pruning
- Secondary clustering on `learner_id` for learner-centric queries

### Materialized Views

- Consider materializing frequently accessed aggregations
- Use incremental refresh for large tables

### Query Patterns

- Always include `partition_date` filters for better performance
- Use `learner_id` filters when possible for clustering benefits
- Leverage warehouse auto-suspend for cost optimization

## ETL Pipeline

### Data Flow

1. Events → Redpanda → S3 (Parquet)
2. Snowpipe auto-ingestion → RAW schema
3. Daily transformation jobs → ANALYTICS schema
4. Real-time views for current day data

### Processing Schedule

- **Snowpipe**: Continuous (1-2 minute latency)
- **Analytics Refresh**: Daily at 4 AM UTC
- **Cleanup Jobs**: Weekly (raw data), Monthly (aggregates)

### Monitoring

- ETL job status tracking in `etl_job_status` table
- Data quality checks via validation queries
- Warehouse credit usage monitoring
- Snowpipe performance metrics

## Looker Integration

### Connection

- Connect Looker to Snowflake ANALYTICS schema
- Use service account with read-only permissions
- Enable query results caching

### LookML Models

- Create explores for each analytics table
- Define measures and dimensions for common KPIs
- Set up drill-down paths for detailed analysis

### Dashboard Examples

- Learner engagement overview
- Content performance metrics
- Session quality analysis
- Mastery progression tracking

## Security & Compliance

### Data Classification

- **Public**: Aggregated, anonymized metrics
- **Internal**: Learner activity data (pseudonymized)
- **Restricted**: Raw event data with PII

### Access Control

- Role-based access to schemas
- Row-level security for multi-tenant data
- Audit logging for data access

### Privacy

- Learner IDs are pseudonymized
- PII is filtered from event payloads
- Right to be forgotten compliance procedures
