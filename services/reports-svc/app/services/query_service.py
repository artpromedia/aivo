"""Query service for executing queries against ClickHouse."""

import clickhouse_connect
import structlog
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import json

from ..schemas import QueryConfig, QueryFilter, QuerySort

logger = structlog.get_logger()

class QueryService:
    """Service for executing and validating queries against ClickHouse."""

    def __init__(self):
        self.clickhouse_host = os.getenv("CLICKHOUSE_HOST", "localhost")
        self.clickhouse_port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
        self.clickhouse_username = os.getenv("CLICKHOUSE_USERNAME", "default")
        self.clickhouse_password = os.getenv("CLICKHOUSE_PASSWORD", "")
        self.clickhouse_database = os.getenv("CLICKHOUSE_DATABASE", "analytics")

        # Allowed tables per tenant - this would come from configuration
        self.tenant_tables = {
            "default": ["usage_events", "user_sessions", "device_metrics", "billing_events"]
        }

    def get_client(self) -> clickhouse_connect.driver.Client:
        """Get ClickHouse client connection."""
        return clickhouse_connect.get_client(
            host=self.clickhouse_host,
            port=self.clickhouse_port,
            username=self.clickhouse_username,
            password=self.clickhouse_password,
            database=self.clickhouse_database
        )

    async def validate_query(self, query_config: QueryConfig, tenant_id: str) -> bool:
        """Validate a query configuration without executing it."""
        # Check if table is allowed for tenant
        if query_config.table not in self.tenant_tables.get(tenant_id, []):
            raise ValueError(f"Table '{query_config.table}' not accessible for tenant '{tenant_id}'")

        # Validate field names (basic check)
        if not query_config.fields:
            raise ValueError("At least one field must be selected")

        # Validate joins if present
        if query_config.joins:
            for join in query_config.joins:
                if "table" not in join or "on" not in join:
                    raise ValueError("Join must specify 'table' and 'on' conditions")

                if join["table"] not in self.tenant_tables.get(tenant_id, []):
                    raise ValueError(f"Join table '{join['table']}' not accessible for tenant '{tenant_id}'")

        # Validate filters
        if query_config.filters:
            for filter_item in query_config.filters:
                self._validate_filter(filter_item)

        # Try to build the query to check for syntax issues
        try:
            self._build_query(query_config, tenant_id, validate_only=True)
        except Exception as e:
            raise ValueError(f"Query syntax error: {str(e)}")

        return True

    async def execute_query(self, query_config: QueryConfig, tenant_id: str) -> Dict[str, Any]:
        """Execute a query and return results."""
        start_time = datetime.utcnow()

        # Validate query first
        await self.validate_query(query_config, tenant_id)

        # Build SQL query
        sql_query = self._build_query(query_config, tenant_id)

        try:
            client = self.get_client()

            # Execute query
            logger.info("Executing query", tenant_id=tenant_id, query=sql_query)
            result = client.query(sql_query)

            # Convert to list of dictionaries
            columns = [col[0] for col in result.column_names]
            data = []

            for row in result.result_rows:
                row_dict = {}
                for i, value in enumerate(row):
                    # Convert ClickHouse types to JSON-serializable types
                    if isinstance(value, datetime):
                        row_dict[columns[i]] = value.isoformat()
                    elif hasattr(value, 'isoformat'):  # Date objects
                        row_dict[columns[i]] = value.isoformat()
                    else:
                        row_dict[columns[i]] = value
                data.append(row_dict)

            # Get total count if not limited
            total_rows = len(data)
            if query_config.limit and len(data) == query_config.limit:
                # Query without limit to get total count
                count_query = self._build_count_query(query_config, tenant_id)
                count_result = client.query(count_query)
                total_rows = count_result.result_rows[0][0] if count_result.result_rows else 0

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "data": data,
                "columns": columns,
                "total_rows": total_rows,
                "execution_time_ms": int(execution_time)
            }

        except Exception as e:
            logger.error("Query execution failed", tenant_id=tenant_id, error=str(e))
            raise Exception(f"Query execution failed: {str(e)}")

    def _validate_filter(self, filter_item: QueryFilter):
        """Validate a single filter."""
        valid_operators = ["eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "like", "between"]

        if filter_item.operator not in valid_operators:
            raise ValueError(f"Invalid filter operator: {filter_item.operator}")

        if filter_item.operator == "between" and not isinstance(filter_item.value, list):
            raise ValueError("Between operator requires array value with two elements")

        if filter_item.operator in ["in", "not_in"] and not isinstance(filter_item.value, list):
            raise ValueError(f"Operator '{filter_item.operator}' requires array value")

    def _build_query(self, query_config: QueryConfig, tenant_id: str, validate_only: bool = False) -> str:
        """Build SQL query from query configuration."""
        # SELECT clause
        fields_str = ", ".join(query_config.fields)
        query_parts = [f"SELECT {fields_str}"]

        # FROM clause with tenant isolation
        query_parts.append(f"FROM {query_config.table}")

        # Add tenant filter for multi-tenant tables
        where_conditions = [f"tenant_id = '{tenant_id}'"]

        # JOIN clauses
        if query_config.joins:
            for join in query_config.joins:
                join_type = join.get("type", "INNER")
                join_table = join["table"]
                join_on = join["on"]
                query_parts.append(f"{join_type} JOIN {join_table} ON {join_on}")

        # WHERE clause
        if query_config.filters:
            for filter_item in query_config.filters:
                condition = self._build_filter_condition(filter_item)
                where_conditions.append(condition)

        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        # GROUP BY clause
        if query_config.group_by:
            group_fields = ", ".join(query_config.group_by)
            query_parts.append(f"GROUP BY {group_fields}")

        # ORDER BY clause
        if query_config.sort:
            sort_clauses = []
            for sort_item in query_config.sort:
                sort_clauses.append(f"{sort_item.field} {sort_item.direction.upper()}")
            query_parts.append("ORDER BY " + ", ".join(sort_clauses))

        # LIMIT clause (only if not validating)
        if not validate_only and query_config.limit:
            query_parts.append(f"LIMIT {query_config.limit}")

        return " ".join(query_parts)

    def _build_count_query(self, query_config: QueryConfig, tenant_id: str) -> str:
        """Build count query to get total rows."""
        query_parts = ["SELECT COUNT(*)"]

        # FROM clause
        query_parts.append(f"FROM {query_config.table}")

        # Add tenant filter
        where_conditions = [f"tenant_id = '{tenant_id}'"]

        # JOIN clauses
        if query_config.joins:
            for join in query_config.joins:
                join_type = join.get("type", "INNER")
                join_table = join["table"]
                join_on = join["on"]
                query_parts.append(f"{join_type} JOIN {join_table} ON {join_on}")

        # WHERE clause
        if query_config.filters:
            for filter_item in query_config.filters:
                condition = self._build_filter_condition(filter_item)
                where_conditions.append(condition)

        if where_conditions:
            query_parts.append("WHERE " + " AND ".join(where_conditions))

        return " ".join(query_parts)

    def _build_filter_condition(self, filter_item: QueryFilter) -> str:
        """Build SQL condition from filter."""
        field = filter_item.field
        operator = filter_item.operator
        value = filter_item.value

        if operator == "eq":
            return f"{field} = '{value}'"
        elif operator == "ne":
            return f"{field} != '{value}'"
        elif operator == "gt":
            return f"{field} > '{value}'"
        elif operator == "gte":
            return f"{field} >= '{value}'"
        elif operator == "lt":
            return f"{field} < '{value}'"
        elif operator == "lte":
            return f"{field} <= '{value}'"
        elif operator == "like":
            return f"{field} LIKE '%{value}%'"
        elif operator == "in":
            values_str = "', '".join([str(v) for v in value])
            return f"{field} IN ('{values_str}')"
        elif operator == "not_in":
            values_str = "', '".join([str(v) for v in value])
            return f"{field} NOT IN ('{values_str}')"
        elif operator == "between":
            return f"{field} BETWEEN '{value[0]}' AND '{value[1]}'"
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    async def get_table_schema(self, table_name: str, tenant_id: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        if table_name not in self.tenant_tables.get(tenant_id, []):
            raise ValueError(f"Table '{table_name}' not accessible for tenant '{tenant_id}'")

        try:
            client = self.get_client()

            # Get table schema
            schema_query = f"DESCRIBE TABLE {table_name}"
            result = client.query(schema_query)

            columns = []
            for row in result.result_rows:
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "1" if len(row) > 2 else False,
                    "default": row[3] if len(row) > 3 and row[3] else None
                })

            return {
                "table": table_name,
                "columns": columns
            }

        except Exception as e:
            raise Exception(f"Failed to get table schema: {str(e)}")

    async def get_available_tables(self, tenant_id: str) -> List[str]:
        """Get list of tables available to a tenant."""
        return self.tenant_tables.get(tenant_id, [])
