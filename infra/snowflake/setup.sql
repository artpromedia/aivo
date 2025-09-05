-- Snowflake database setup for Aivo Analytics
-- This script creates the database, schemas, and core tables for the ETL pipeline

-- Create database
CREATE DATABASE IF NOT EXISTS AIVO_ANALYTICS;
USE DATABASE AIVO_ANALYTICS;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS RAW COMMENT = 'Raw data from Snowpipe ingestion';
CREATE SCHEMA IF NOT EXISTS ANALYTICS COMMENT = 'Analytics models and aggregations';
CREATE SCHEMA IF NOT EXISTS STAGING COMMENT = 'Staging area for transformations';

-- Switch to RAW schema for raw tables
USE SCHEMA RAW;

-- Raw events table (target for Snowpipe)
CREATE TABLE IF NOT EXISTS raw_events (
    learner_id STRING NOT NULL,
    event_type STRING NOT NULL,
    event_id STRING NOT NULL,
    session_id STRING,
    timestamp TIMESTAMP_NTZ NOT NULL,
    data VARIANT,
    metadata VARIANT,
    version STRING DEFAULT '1.0',
    processed_at TIMESTAMP_NTZ,
    partition_date DATE NOT NULL,
    s3_path STRING,
    -- Clustering and partitioning
    CONSTRAINT pk_raw_events PRIMARY KEY (event_id, partition_date)
) CLUSTER BY (partition_date, learner_id)
PARTITION BY (partition_date)
COMMENT = 'Raw learner events ingested from Redpanda via S3 Snowpipe';

-- Create file format for Parquet ingestion
CREATE FILE FORMAT IF NOT EXISTS parquet_format
TYPE = 'PARQUET'
COMPRESSION = 'SNAPPY'
COMMENT = 'File format for Parquet files from S3';

-- Create stage for S3 integration
CREATE STAGE IF NOT EXISTS s3_events_stage
URL = 's3://aivo-data-raw/events/'
FILE_FORMAT = parquet_format
COMMENT = 'S3 stage for event files';

-- Create Snowpipe for automatic ingestion
CREATE PIPE IF NOT EXISTS events_pipe
AUTO_INGEST = TRUE
AS
COPY INTO raw_events
FROM @s3_events_stage
PATTERN = '.*events_.*\.parquet'
FILE_FORMAT = (FORMAT_NAME = 'parquet_format');

-- Show pipe status
SELECT SYSTEM$PIPE_STATUS('events_pipe');

-- Switch to ANALYTICS schema for models
USE SCHEMA ANALYTICS;

-- Minute-level metrics table
CREATE TABLE IF NOT EXISTS minute_metrics (
    learner_id STRING NOT NULL,
    minute_timestamp TIMESTAMP_NTZ NOT NULL,
    session_id STRING,
    -- Event counts
    total_events NUMBER(10,0) DEFAULT 0,
    page_views NUMBER(10,0) DEFAULT 0,
    interactions NUMBER(10,0) DEFAULT 0,
    assessments_started NUMBER(10,0) DEFAULT 0,
    assessments_completed NUMBER(10,0) DEFAULT 0,
    lessons_started NUMBER(10,0) DEFAULT 0,
    lessons_completed NUMBER(10,0) DEFAULT 0,
    errors NUMBER(10,0) DEFAULT 0,
    -- Timing metrics
    time_spent_seconds NUMBER(10,2) DEFAULT 0.0,
    -- Meta
    created_at TIMESTAMP_NTZ NOT NULL,
    partition_date DATE NOT NULL,
    CONSTRAINT pk_minute_metrics PRIMARY KEY (learner_id, minute_timestamp, partition_date)
) CLUSTER BY (partition_date, learner_id)
PARTITION BY (partition_date)
COMMENT = 'Minute-level aggregated learner activity metrics';

-- Session metrics table
CREATE TABLE IF NOT EXISTS session_metrics (
    session_id STRING NOT NULL,
    learner_id STRING NOT NULL,
    session_start TIMESTAMP_NTZ NOT NULL,
    session_end TIMESTAMP_NTZ,
    -- Duration
    duration_seconds NUMBER(10,2),
    -- Activity metrics
    total_events NUMBER(10,0) DEFAULT 0,
    unique_pages NUMBER(10,0) DEFAULT 0,
    total_interactions NUMBER(10,0) DEFAULT 0,
    -- Learning metrics
    lessons_attempted NUMBER(10,0) DEFAULT 0,
    lessons_completed NUMBER(10,0) DEFAULT 0,
    assessments_attempted NUMBER(10,0) DEFAULT 0,
    assessments_completed NUMBER(10,0) DEFAULT 0,
    -- Performance
    avg_assessment_score NUMBER(5,2),
    completion_rate NUMBER(5,4) DEFAULT 0.0,
    -- Meta
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP_NTZ NOT NULL,
    created_at TIMESTAMP_NTZ NOT NULL,
    updated_at TIMESTAMP_NTZ NOT NULL,
    partition_date DATE NOT NULL,
    CONSTRAINT pk_session_metrics PRIMARY KEY (session_id, partition_date)
) CLUSTER BY (partition_date, learner_id)
PARTITION BY (partition_date)
COMMENT = 'Session-level aggregated learner activity and performance metrics';

-- Mastery deltas table
CREATE TABLE IF NOT EXISTS mastery_deltas (
    learner_id STRING NOT NULL,
    content_id STRING NOT NULL,
    content_type STRING NOT NULL,
    -- Mastery tracking
    previous_mastery NUMBER(5,4),
    current_mastery NUMBER(5,4) NOT NULL,
    mastery_delta NUMBER(5,4) NOT NULL,
    -- Context
    trigger_event_id STRING NOT NULL,
    trigger_event_type STRING NOT NULL,
    session_id STRING,
    -- Metadata
    confidence_score NUMBER(5,4),
    evidence_count NUMBER(10,0) DEFAULT 1,
    -- Meta
    timestamp TIMESTAMP_NTZ NOT NULL,
    created_at TIMESTAMP_NTZ NOT NULL,
    partition_date DATE NOT NULL,
    CONSTRAINT pk_mastery_deltas PRIMARY KEY (learner_id, content_id, timestamp, partition_date)
) CLUSTER BY (partition_date, learner_id, content_id)
PARTITION BY (partition_date)
COMMENT = 'Mastery level changes for learners by content/skill';

-- ETL job status tracking table
CREATE TABLE IF NOT EXISTS etl_job_status (
    job_id STRING NOT NULL,
    job_type STRING NOT NULL,
    status STRING NOT NULL,
    -- Timing
    started_at TIMESTAMP_NTZ NOT NULL,
    completed_at TIMESTAMP_NTZ,
    -- Metrics
    records_processed NUMBER(15,0) DEFAULT 0,
    records_failed NUMBER(15,0) DEFAULT 0,
    bytes_processed NUMBER(20,0) DEFAULT 0,
    -- Error tracking
    error_message STRING,
    retry_count NUMBER(5,0) DEFAULT 0,
    -- Meta
    created_at TIMESTAMP_NTZ NOT NULL,
    updated_at TIMESTAMP_NTZ NOT NULL,
    CONSTRAINT pk_etl_job_status PRIMARY KEY (job_id)
) CLUSTER BY (started_at)
COMMENT = 'ETL job execution status and metrics tracking';

-- Data retention policies
-- Raw data retention: 18 months
CREATE TASK IF NOT EXISTS cleanup_raw_events
WAREHOUSE = COMPUTE_WH
SCHEDULE = 'USING CRON 0 2 * * SUN' -- Weekly cleanup on Sundays at 2 AM
AS
DELETE FROM RAW.raw_events 
WHERE partition_date < DATEADD(MONTH, -18, CURRENT_DATE());

-- Aggregate data retention: 7 years (but we typically keep these longer)
-- This is mainly for compliance and storage optimization
CREATE TASK IF NOT EXISTS cleanup_old_aggregates
WAREHOUSE = COMPUTE_WH
SCHEDULE = 'USING CRON 0 3 1 * *' -- Monthly cleanup on 1st at 3 AM
AS
BEGIN
    DELETE FROM ANALYTICS.minute_metrics 
    WHERE partition_date < DATEADD(YEAR, -7, CURRENT_DATE());
    
    DELETE FROM ANALYTICS.session_metrics 
    WHERE partition_date < DATEADD(YEAR, -7, CURRENT_DATE());
    
    DELETE FROM ANALYTICS.mastery_deltas 
    WHERE partition_date < DATEADD(YEAR, -7, CURRENT_DATE());
END;

-- Create views for Looker
CREATE VIEW IF NOT EXISTS learner_activity_summary AS
SELECT 
    learner_id,
    DATE(minute_timestamp) as activity_date,
    SUM(total_events) as daily_events,
    SUM(time_spent_seconds)/3600.0 as hours_spent,
    COUNT(DISTINCT session_id) as sessions,
    SUM(lessons_completed) as lessons_completed,
    SUM(assessments_completed) as assessments_completed
FROM minute_metrics
WHERE partition_date >= DATEADD(DAY, -90, CURRENT_DATE()) -- Last 90 days
GROUP BY learner_id, DATE(minute_timestamp);

CREATE VIEW IF NOT EXISTS content_mastery_trends AS
SELECT 
    content_id,
    content_type,
    DATE(timestamp) as mastery_date,
    COUNT(*) as learners_affected,
    AVG(mastery_delta) as avg_mastery_change,
    AVG(current_mastery) as avg_current_mastery,
    AVG(confidence_score) as avg_confidence
FROM mastery_deltas
WHERE partition_date >= DATEADD(DAY, -30, CURRENT_DATE()) -- Last 30 days
GROUP BY content_id, content_type, DATE(timestamp);

-- Grant permissions (adjust as needed for your setup)
-- GRANT USAGE ON DATABASE AIVO_ANALYTICS TO ROLE ANALYTICS_READER;
-- GRANT USAGE ON SCHEMA RAW TO ROLE ANALYTICS_READER;
-- GRANT USAGE ON SCHEMA ANALYTICS TO ROLE ANALYTICS_READER;
-- GRANT SELECT ON ALL TABLES IN SCHEMA RAW TO ROLE ANALYTICS_READER;
-- GRANT SELECT ON ALL TABLES IN SCHEMA ANALYTICS TO ROLE ANALYTICS_READER;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA ANALYTICS TO ROLE ANALYTICS_READER;
