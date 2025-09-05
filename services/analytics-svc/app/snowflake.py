"""Snowflake client for analytics queries."""

import logging
from typing import Any

import snowflake.connector
from snowflake.connector import DictCursor

from app.config import Settings

logger = logging.getLogger(__name__)


class SnowflakeClient:
    """Snowflake database client."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Snowflake client."""
        self.settings = settings
        self.connection = None

    async def connect(self) -> None:
        """Establish Snowflake connection."""
        try:
            self.connection = snowflake.connector.connect(
                account=self.settings.snowflake_account,
                user=self.settings.snowflake_user,
                password=self.settings.snowflake_password,
                warehouse=self.settings.snowflake_warehouse,
                database=self.settings.snowflake_database,
                schema=self.settings.snowflake_schema,
                role=self.settings.snowflake_role,
            )
            logger.info("Connected to Snowflake successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test Snowflake connection."""
        if not self.connection:
            await self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Snowflake connection test failed: {e}")
            return False

    async def close(self) -> None:
        """Close Snowflake connection."""
        if self.connection:
            self.connection.close()
            logger.info("Snowflake connection closed")

    async def execute_query(
        self, query: str, params: dict = None
    ) -> list[dict]:
        """Execute a query and return results as list of dictionaries."""
        if not self.connection:
            await self.connect()

        try:
            cursor = self.connection.cursor(DictCursor)
            cursor.execute(query, params or {})
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def get_summary_metrics(
        self,
        tenant_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Get summary learning metrics for a tenant."""
        date_filter = ""
        params = {"tenant_id": tenant_id}

        if start_date:
            date_filter += " AND DATE(created_at) >= %(start_date)s"
            params["start_date"] = start_date

        if end_date:
            date_filter += " AND DATE(created_at) <= %(end_date)s"
            params["end_date"] = end_date

        query = f"""
        WITH learner_stats AS (
            SELECT
                COUNT(DISTINCT learner_id) as total_learners,
                COUNT(DISTINCT CASE
                    WHEN DATE(created_at) = CURRENT_DATE()
                    THEN learner_id
                END) as active_learners_today,
                COUNT(DISTINCT CASE
                    WHEN created_at >= DATEADD(day, -7, CURRENT_DATE())
                    THEN learner_id
                END) as active_learners_week
            FROM minute_analytics
            WHERE tenant_id = %(tenant_id)s {date_filter}
        ),
        session_stats AS (
            SELECT
                COUNT(*) as total_sessions,
                AVG(total_duration_minutes) as avg_session_duration_minutes
            FROM session_analytics
            WHERE tenant_id = %(tenant_id)s {date_filter}
        ),
        answer_stats AS (
            SELECT
                SUM(correct_answers) as total_correct_answers,
                SUM(incorrect_answers) as total_incorrect_answers,
                AVG(accuracy_rate) as overall_accuracy
            FROM minute_analytics
            WHERE tenant_id = %(tenant_id)s {date_filter}
        ),
        mastery_stats AS (
            SELECT
                COUNT(DISTINCT concept_id) as concepts_mastered,
                AVG(mastery_score) as avg_mastery_score
            FROM mastery_analytics
            WHERE tenant_id = %(tenant_id)s
                AND mastery_score >= 0.8 {date_filter}
        )
        SELECT
            l.total_learners,
            l.active_learners_today,
            l.active_learners_week,
            s.total_sessions,
            s.avg_session_duration_minutes,
            a.total_correct_answers,
            a.total_incorrect_answers,
            a.overall_accuracy,
            m.concepts_mastered,
            m.avg_mastery_score
        FROM learner_stats l
        CROSS JOIN session_stats s
        CROSS JOIN answer_stats a
        CROSS JOIN mastery_stats m
        """

        results = await self.execute_query(query, params)
        return results[0] if results else {}

    async def get_mastery_metrics(
        self,
        tenant_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get mastery progression metrics for a tenant."""
        date_filter = ""
        params = {"tenant_id": tenant_id, "limit": limit}

        if start_date:
            date_filter += " AND DATE(last_updated) >= %(start_date)s"
            params["start_date"] = start_date

        if end_date:
            date_filter += " AND DATE(last_updated) <= %(end_date)s"
            params["end_date"] = end_date

        query = f"""
        SELECT
            learner_id,
            concept_id,
            concept_name,
            mastery_score,
            total_attempts as attempts,
            correct_answers,
            incorrect_answers,
            accuracy_rate as accuracy,
            first_attempt,
            last_attempt,
            mastery_achieved_at
        FROM mastery_analytics
        WHERE tenant_id = %(tenant_id)s {date_filter}
        ORDER BY mastery_score DESC, last_attempt DESC
        LIMIT %(limit)s
        """

        return await self.execute_query(query, params)

    async def get_streak_metrics(
        self,
        tenant_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get learning streak metrics for a tenant."""
        date_filter = ""
        params = {"tenant_id": tenant_id, "limit": limit}

        if start_date:
            date_filter += " AND DATE(last_learning_date) >= %(start_date)s"
            params["start_date"] = start_date

        if end_date:
            date_filter += " AND DATE(last_learning_date) <= %(end_date)s"
            params["end_date"] = end_date

        query = f"""
        WITH learner_streaks AS (
            SELECT
                learner_id,
                COUNT(DISTINCT DATE(created_at)) as total_learning_days,
                MAX(DATE(created_at)) as last_learning_date,
                AVG(total_sessions) as avg_sessions_per_day
            FROM minute_analytics
            WHERE tenant_id = %(tenant_id)s {date_filter}
            GROUP BY learner_id
        ),
        streak_calculation AS (
            SELECT
                ls.learner_id,
                ls.total_learning_days,
                ls.last_learning_date,
                ls.avg_sessions_per_day,
                -- Calculate current streak (simplified)
                CASE
                    WHEN DATEDIFF(
                        day, ls.last_learning_date, CURRENT_DATE()
                    ) <= 1
                    THEN 7  -- Placeholder for actual streak calculation
                    ELSE 0
                END as current_streak,
                14 as longest_streak,  -- Placeholder for actual calculation
                DATEADD(day, -7, ls.last_learning_date) as streak_start_date
            FROM learner_streaks ls
        )
        SELECT
            learner_id,
            current_streak,
            longest_streak,
            total_learning_days,
            streak_start_date,
            last_learning_date,
            avg_sessions_per_day
        FROM streak_calculation
        WHERE current_streak > 0 OR longest_streak > 0
        ORDER BY current_streak DESC, longest_streak DESC
        LIMIT %(limit)s
        """

        return await self.execute_query(query, params)
