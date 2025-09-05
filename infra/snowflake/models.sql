-- Snowflake data models for analytics
-- These are the core transformation queries that build our analytics tables

-- 1. Minute-level aggregations
-- This model aggregates raw events into minute-level metrics
CREATE OR REPLACE VIEW minute_metrics_staging AS
SELECT 
    learner_id,
    DATE_TRUNC('MINUTE', timestamp) as minute_timestamp,
    session_id,
    DATE(timestamp) as partition_date,
    
    -- Event counts by type
    COUNT(*) as total_events,
    COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as page_views,
    COUNT(CASE WHEN event_type = 'interaction' THEN 1 END) as interactions,
    COUNT(CASE WHEN event_type = 'assessment_start' THEN 1 END) as assessments_started,
    COUNT(CASE WHEN event_type = 'assessment_complete' THEN 1 END) as assessments_completed,
    COUNT(CASE WHEN event_type = 'lesson_start' THEN 1 END) as lessons_started,
    COUNT(CASE WHEN event_type = 'lesson_complete' THEN 1 END) as lessons_completed,
    COUNT(CASE WHEN event_type = 'error' THEN 1 END) as errors,
    
    -- Time spent calculation (rough estimate based on event frequency)
    CASE 
        WHEN COUNT(*) > 1 THEN 
            GREATEST(0, DATEDIFF('second', MIN(timestamp), MAX(timestamp)))
        ELSE 60  -- Default 1 minute for single events
    END as time_spent_seconds,
    
    CURRENT_TIMESTAMP() as created_at

FROM RAW.raw_events
WHERE partition_date >= DATEADD(DAY, -7, CURRENT_DATE()) -- Process last 7 days
GROUP BY 
    learner_id, 
    DATE_TRUNC('MINUTE', timestamp),
    session_id,
    DATE(timestamp);

-- 2. Session metrics aggregation
-- This model creates session-level summaries
CREATE OR REPLACE VIEW session_metrics_staging AS
SELECT 
    session_id,
    learner_id,
    MIN(timestamp) as session_start,
    MAX(timestamp) as session_end,
    DATEDIFF('second', MIN(timestamp), MAX(timestamp)) as duration_seconds,
    DATE(MIN(timestamp)) as partition_date,
    
    -- Activity metrics
    COUNT(*) as total_events,
    COUNT(DISTINCT CASE 
        WHEN data:page_id IS NOT NULL THEN data:page_id::STRING 
        ELSE NULL 
    END) as unique_pages,
    COUNT(CASE WHEN event_type = 'interaction' THEN 1 END) as total_interactions,
    
    -- Learning metrics
    COUNT(CASE WHEN event_type = 'lesson_start' THEN 1 END) as lessons_attempted,
    COUNT(CASE WHEN event_type = 'lesson_complete' THEN 1 END) as lessons_completed,
    COUNT(CASE WHEN event_type = 'assessment_start' THEN 1 END) as assessments_attempted,
    COUNT(CASE WHEN event_type = 'assessment_complete' THEN 1 END) as assessments_completed,
    
    -- Performance metrics
    AVG(CASE 
        WHEN event_type = 'assessment_complete' AND data:score IS NOT NULL 
        THEN data:score::FLOAT 
        ELSE NULL 
    END) as avg_assessment_score,
    
    -- Completion rate
    CASE 
        WHEN COUNT(CASE WHEN event_type IN ('lesson_start', 'assessment_start') THEN 1 END) > 0
        THEN COUNT(CASE WHEN event_type IN ('lesson_complete', 'assessment_complete') THEN 1 END)::FLOAT 
             / COUNT(CASE WHEN event_type IN ('lesson_start', 'assessment_start') THEN 1 END)::FLOAT
        ELSE 0.0
    END as completion_rate,
    
    -- Session status (active if last event was within 30 minutes)
    CASE 
        WHEN MAX(timestamp) > DATEADD('MINUTE', -30, CURRENT_TIMESTAMP()) THEN TRUE
        ELSE FALSE
    END as is_active,
    
    MAX(timestamp) as last_activity,
    CURRENT_TIMESTAMP() as created_at,
    CURRENT_TIMESTAMP() as updated_at

FROM RAW.raw_events
WHERE 
    session_id IS NOT NULL 
    AND partition_date >= DATEADD(DAY, -7, CURRENT_DATE())
GROUP BY session_id, learner_id, DATE(MIN(timestamp));

-- 3. Mastery delta calculation
-- This model calculates mastery changes based on assessment events
CREATE OR REPLACE VIEW mastery_deltas_staging AS
WITH assessment_events AS (
    SELECT 
        learner_id,
        event_id,
        session_id,
        timestamp,
        event_type,
        data:assessment_id::STRING as content_id,
        'assessment' as content_type,
        data:score::FLOAT as score,
        data:max_score::FLOAT as max_score,
        DATE(timestamp) as partition_date
    FROM RAW.raw_events
    WHERE 
        event_type = 'assessment_complete'
        AND data:assessment_id IS NOT NULL
        AND data:score IS NOT NULL
        AND partition_date >= DATEADD(DAY, -7, CURRENT_DATE())
),
normalized_scores AS (
    SELECT 
        *,
        CASE 
            WHEN max_score > 0 THEN score / max_score
            ELSE score / 100.0  -- Assume percentage if max_score not provided
        END as normalized_score
    FROM assessment_events
    WHERE normalized_score BETWEEN 0 AND 1
),
previous_scores AS (
    SELECT 
        learner_id,
        content_id,
        timestamp,
        normalized_score,
        LAG(normalized_score) OVER (
            PARTITION BY learner_id, content_id 
            ORDER BY timestamp
        ) as previous_mastery
    FROM normalized_scores
)
SELECT 
    ps.learner_id,
    ps.content_id,
    'assessment' as content_type,
    ps.previous_mastery,
    ps.normalized_score as current_mastery,
    ps.normalized_score - COALESCE(ps.previous_mastery, 0) as mastery_delta,
    ae.event_id as trigger_event_id,
    ae.event_type as trigger_event_type,
    ae.session_id,
    
    -- Confidence score based on number of attempts and score consistency
    CASE 
        WHEN ps.previous_mastery IS NOT NULL 
        THEN LEAST(1.0, 0.5 + (ABS(ps.normalized_score - ps.previous_mastery) * 0.5))
        ELSE 0.7  -- Default confidence for first attempt
    END as confidence_score,
    
    1 as evidence_count,  -- Each assessment is one evidence point
    ps.timestamp,
    CURRENT_TIMESTAMP() as created_at,
    ae.partition_date

FROM previous_scores ps
JOIN assessment_events ae ON 
    ps.learner_id = ae.learner_id 
    AND ps.content_id = ae.content_id 
    AND ps.timestamp = ae.timestamp
WHERE ps.normalized_score != COALESCE(ps.previous_mastery, -1); -- Only include actual changes

-- 4. Stored procedures for incremental updates
-- These procedures handle the incremental loading of analytics tables

CREATE OR REPLACE PROCEDURE load_minute_metrics(start_date DATE, end_date DATE)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Delete existing data for the date range
    DELETE FROM ANALYTICS.minute_metrics 
    WHERE partition_date BETWEEN start_date AND end_date;
    
    -- Insert new aggregated data
    INSERT INTO ANALYTICS.minute_metrics
    SELECT * FROM minute_metrics_staging
    WHERE partition_date BETWEEN start_date AND end_date;
    
    RETURN 'Successfully loaded minute metrics for ' || start_date || ' to ' || end_date;
END;
$$;

CREATE OR REPLACE PROCEDURE load_session_metrics(start_date DATE, end_date DATE)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Delete existing data for the date range
    DELETE FROM ANALYTICS.session_metrics 
    WHERE partition_date BETWEEN start_date AND end_date;
    
    -- Insert new aggregated data
    INSERT INTO ANALYTICS.session_metrics
    SELECT * FROM session_metrics_staging
    WHERE partition_date BETWEEN start_date AND end_date;
    
    RETURN 'Successfully loaded session metrics for ' || start_date || ' to ' || end_date;
END;
$$;

CREATE OR REPLACE PROCEDURE load_mastery_deltas(start_date DATE, end_date DATE)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    -- Delete existing data for the date range
    DELETE FROM ANALYTICS.mastery_deltas 
    WHERE partition_date BETWEEN start_date AND end_date;
    
    -- Insert new mastery changes
    INSERT INTO ANALYTICS.mastery_deltas
    SELECT * FROM mastery_deltas_staging
    WHERE partition_date BETWEEN start_date AND end_date;
    
    RETURN 'Successfully loaded mastery deltas for ' || start_date || ' to ' || end_date;
END;
$$;

-- 5. Daily aggregation task
-- This task runs daily to update all analytics tables
CREATE OR REPLACE TASK daily_analytics_refresh
WAREHOUSE = COMPUTE_WH
SCHEDULE = 'USING CRON 0 4 * * *' -- Daily at 4 AM
AS
BEGIN
    -- Process yesterday's data
    CALL load_minute_metrics(DATEADD(DAY, -1, CURRENT_DATE()), CURRENT_DATE());
    CALL load_session_metrics(DATEADD(DAY, -1, CURRENT_DATE()), CURRENT_DATE());
    CALL load_mastery_deltas(DATEADD(DAY, -1, CURRENT_DATE()), CURRENT_DATE());
    
    -- Log completion
    INSERT INTO ANALYTICS.etl_job_status (
        job_id,
        job_type,
        status,
        started_at,
        completed_at,
        created_at,
        updated_at
    )
    VALUES (
        'daily_analytics_' || TO_VARCHAR(CURRENT_DATE(), 'YYYY-MM-DD'),
        'daily_analytics_refresh',
        'completed',
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP()
    );
END;

-- Start the task (uncomment when ready)
-- ALTER TASK daily_analytics_refresh RESUME;
