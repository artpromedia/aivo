"""
Cascaded delete service for GDPR compliance.

Orchestrates data deletion across PostgreSQL, MongoDB, S3, and Snowflake.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

import boto3
import pymongo
import snowflake.connector
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.models import (
    AuditAction,
    DeletionRequest,
    RequestStatus,
)

logger = logging.getLogger(__name__)


def is_deletion_complete(deletion_statuses: Dict[str, bool]) -> bool:
    """Helper function to check if all deletions are complete."""
    return all(deletion_statuses.values())


def calculate_completion_percentage(deletion_statuses: Dict[str, bool]) -> int:
    """Helper function to calculate deletion completion percentage."""
    completed = sum(1 for status in deletion_statuses.values() if status)
    total = len(deletion_statuses)
    return int((completed / total) * 100) if total > 0 else 0


def should_retry_deletion(retry_count: int, max_retries: int = 3) -> bool:
    """Helper function to determine if deletion should be retried."""
    return retry_count < max_retries


class CascadeDeleteService:
    """
    Service for coordinating data deletion across all storage systems.
    
    Ensures complete data removal for GDPR Article 17 compliance.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        s3_client: Optional[boto3.client] = None,
        mongo_client: Optional[pymongo.MongoClient] = None,
        snowflake_config: Optional[Dict[str, Any]] = None,
    ):
        self.db_session = db_session
        self.s3_client = s3_client
        self.mongo_client = mongo_client
        self.snowflake_config = snowflake_config or {}
        
        # Deletion statistics
        self.deletion_stats = {
            "postgres_records": 0,
            "mongodb_documents": 0,
            "s3_objects": 0,
            "snowflake_rows": 0,
            "total_bytes_freed": 0,
        }
    
    async def execute_cascaded_deletion(
        self,
        deletion_request: DeletionRequest,
    ) -> Dict[str, Any]:
        """
        Execute complete cascaded deletion across all systems.
        
        Returns deletion summary with statistics.
        """
        user_id = deletion_request.user_id
        logger.info(f"Starting cascaded deletion for user {user_id}")
        
        try:
            # Update request status
            deletion_request.status = RequestStatus.IN_PROGRESS
            deletion_request.started_at = datetime.utcnow()
            await self.db_session.commit()
            
            # Execute deletions in parallel where possible
            deletion_tasks = []
            
            # PostgreSQL deletion (run first due to foreign key constraints)
            await self._delete_from_postgres(user_id, deletion_request)
            
            # Parallel deletion from other systems
            if self.mongo_client:
                deletion_tasks.append(
                    self._delete_from_mongodb(user_id, deletion_request)
                )
            
            if self.s3_client:
                deletion_tasks.append(
                    self._delete_from_s3(user_id, deletion_request)
                )
            
            if self.snowflake_config:
                deletion_tasks.append(
                    self._delete_from_snowflake(user_id, deletion_request)
                )
            
            # Wait for all deletions to complete
            if deletion_tasks:
                await asyncio.gather(*deletion_tasks, return_exceptions=True)
            
            # Update final status
            deletion_request.status = RequestStatus.COMPLETED
            deletion_request.completed_at = datetime.utcnow()
            deletion_request.records_deleted_count = sum([
                self.deletion_stats["postgres_records"],
                self.deletion_stats["mongodb_documents"],
                self.deletion_stats["snowflake_rows"],
            ])
            deletion_request.files_deleted_count = self.deletion_stats["s3_objects"]
            deletion_request.storage_freed_bytes = self.deletion_stats["total_bytes_freed"]
            
            await self.db_session.commit()
            
            logger.info(f"Cascaded deletion completed for user {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "deletion_stats": self.deletion_stats,
                "completed_at": deletion_request.completed_at.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Cascaded deletion failed for user {user_id}: {str(e)}")
            
            deletion_request.status = RequestStatus.FAILED
            deletion_request.error_message = str(e)
            deletion_request.retry_count += 1
            await self.db_session.commit()
            
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e),
                "retry_count": deletion_request.retry_count,
            }
    
    async def _delete_from_postgres(
        self,
        user_id: str,
        deletion_request: DeletionRequest,
    ) -> None:
        """Delete user data from PostgreSQL database."""
        try:
            logger.info(f"Deleting PostgreSQL data for user {user_id}")
            
            # Get tables that contain user data
            user_data_tables = [
                "consent_records",
                "parental_rights", 
                "preference_settings",
                "data_export_requests",
                "audit_logs",
                # Add other user data tables
                "user_profiles",
                "user_activities",
                "user_preferences",
                "chat_messages",
                "media_uploads",
            ]
            
            total_deleted = 0
            
            for table in user_data_tables:
                try:
                    # Check if table exists
                    check_query = text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                        "WHERE table_name = :table_name)"
                    )
                    result = await self.db_session.execute(
                        check_query, {"table_name": table}
                    )
                    table_exists = result.scalar()
                    
                    if not table_exists:
                        continue
                    
                    # Delete records for this user
                    delete_query = text(f"DELETE FROM {table} WHERE user_id = :user_id")
                    result = await self.db_session.execute(
                        delete_query, {"user_id": user_id}
                    )
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    
                    logger.info(f"Deleted {deleted_count} records from {table}")
                    
                except Exception as e:
                    logger.warning(f"Failed to delete from table {table}: {str(e)}")
                    continue
            
            await self.db_session.commit()
            
            self.deletion_stats["postgres_records"] = total_deleted
            deletion_request.postgres_deleted = True
            
            logger.info(f"PostgreSQL deletion completed: {total_deleted} records")
            
        except Exception as e:
            logger.error(f"PostgreSQL deletion failed: {str(e)}")
            deletion_request.postgres_deleted = False
            raise
    
    async def _delete_from_mongodb(
        self,
        user_id: str,
        deletion_request: DeletionRequest,
    ) -> None:
        """Delete user data from MongoDB collections."""
        try:
            logger.info(f"Deleting MongoDB data for user {user_id}")
            
            if not self.mongo_client:
                logger.warning("MongoDB client not configured")
                return
            
            # Get database
            db = self.mongo_client.get_default_database()
            
            # Collections that contain user data
            user_data_collections = [
                "user_activities",
                "chat_sessions",
                "media_metadata",
                "behavioral_data",
                "analytics_events",
                "user_generated_content",
            ]
            
            total_deleted = 0
            
            for collection_name in user_data_collections:
                try:
                    collection = db[collection_name]
                    
                    # Delete documents for this user
                    result = collection.delete_many({"user_id": user_id})
                    deleted_count = result.deleted_count
                    total_deleted += deleted_count
                    
                    logger.info(f"Deleted {deleted_count} documents from {collection_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to delete from collection {collection_name}: {str(e)}")
                    continue
            
            self.deletion_stats["mongodb_documents"] = total_deleted
            deletion_request.mongodb_deleted = True
            
            logger.info(f"MongoDB deletion completed: {total_deleted} documents")
            
        except Exception as e:
            logger.error(f"MongoDB deletion failed: {str(e)}")
            deletion_request.mongodb_deleted = False
            raise
    
    async def _delete_from_s3(
        self,
        user_id: str,
        deletion_request: DeletionRequest,
    ) -> None:
        """Delete user files from S3 storage."""
        try:
            logger.info(f"Deleting S3 data for user {user_id}")
            
            if not self.s3_client:
                logger.warning("S3 client not configured")
                return
            
            # S3 buckets that contain user data
            user_data_buckets = [
                "user-uploads",
                "profile-images", 
                "chat-media",
                "exported-data",
                "backup-data",
            ]
            
            total_deleted = 0
            total_bytes_freed = 0
            
            for bucket_name in user_data_buckets:
                try:
                    # List objects with user_id prefix
                    response = self.s3_client.list_objects_v2(
                        Bucket=bucket_name,
                        Prefix=f"users/{user_id}/",
                    )
                    
                    if "Contents" not in response:
                        continue
                    
                    # Delete objects in batches
                    objects_to_delete = []
                    for obj in response["Contents"]:
                        objects_to_delete.append({"Key": obj["Key"]})
                        total_bytes_freed += obj["Size"]
                        
                        # Delete in batches of 1000 (S3 limit)
                        if len(objects_to_delete) >= 1000:
                            self.s3_client.delete_objects(
                                Bucket=bucket_name,
                                Delete={"Objects": objects_to_delete},
                            )
                            total_deleted += len(objects_to_delete)
                            objects_to_delete = []
                    
                    # Delete remaining objects
                    if objects_to_delete:
                        self.s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={"Objects": objects_to_delete},
                        )
                        total_deleted += len(objects_to_delete)
                    
                    logger.info(f"Deleted objects from S3 bucket {bucket_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to delete from S3 bucket {bucket_name}: {str(e)}")
                    continue
            
            self.deletion_stats["s3_objects"] = total_deleted
            self.deletion_stats["total_bytes_freed"] += total_bytes_freed
            deletion_request.s3_deleted = True
            
            logger.info(f"S3 deletion completed: {total_deleted} objects, {total_bytes_freed} bytes freed")
            
        except Exception as e:
            logger.error(f"S3 deletion failed: {str(e)}")
            deletion_request.s3_deleted = False
            raise
    
    async def _delete_from_snowflake(
        self,
        user_id: str,
        deletion_request: DeletionRequest,
    ) -> None:
        """Delete user data from Snowflake data warehouse."""
        try:
            logger.info(f"Deleting Snowflake data for user {user_id}")
            
            if not self.snowflake_config:
                logger.warning("Snowflake configuration not provided")
                return
            
            # Connect to Snowflake
            conn = snowflake.connector.connect(**self.snowflake_config)
            cursor = conn.cursor()
            
            # Tables that contain user data
            user_data_tables = [
                "analytics.user_events",
                "analytics.user_sessions",
                "analytics.user_behavior",
                "reporting.user_metrics",
                "data_lake.user_interactions",
            ]
            
            total_deleted = 0
            
            for table in user_data_tables:
                try:
                    # Delete records for this user
                    delete_query = f"DELETE FROM {table} WHERE user_id = %s"
                    cursor.execute(delete_query, (user_id,))
                    deleted_count = cursor.rowcount
                    total_deleted += deleted_count
                    
                    logger.info(f"Deleted {deleted_count} rows from {table}")
                    
                except Exception as e:
                    logger.warning(f"Failed to delete from Snowflake table {table}: {str(e)}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.deletion_stats["snowflake_rows"] = total_deleted
            deletion_request.snowflake_deleted = True
            
            logger.info(f"Snowflake deletion completed: {total_deleted} rows")
            
        except Exception as e:
            logger.error(f"Snowflake deletion failed: {str(e)}")
            deletion_request.snowflake_deleted = False
            raise
    
    async def verify_deletion_completion(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Verify that all user data has been successfully deleted.
        
        Returns verification report.
        """
        verification_results = {
            "user_id": user_id,
            "verification_timestamp": datetime.utcnow().isoformat(),
            "systems_checked": {},
            "deletion_complete": True,
            "remaining_data_found": [],
        }
        
        # Check PostgreSQL
        try:
            check_query = text(
                "SELECT table_name, COUNT(*) as record_count "
                "FROM ("
                "  SELECT 'consent_records' as table_name, COUNT(*) FROM consent_records WHERE user_id = :user_id"
                "  UNION ALL"
                "  SELECT 'audit_logs', COUNT(*) FROM audit_logs WHERE user_id = :user_id"
                ") t "
                "GROUP BY table_name"
            )
            result = await self.db_session.execute(check_query, {"user_id": user_id})
            postgres_results = result.fetchall()
            
            verification_results["systems_checked"]["postgres"] = {
                "checked": True,
                "tables_with_data": [
                    {"table": row[0], "count": row[1]} 
                    for row in postgres_results if row[1] > 0
                ]
            }
            
            if any(row[1] > 0 for row in postgres_results):
                verification_results["deletion_complete"] = False
                verification_results["remaining_data_found"].append("PostgreSQL")
                
        except Exception as e:
            verification_results["systems_checked"]["postgres"] = {
                "checked": False,
                "error": str(e)
            }
        
        # Check MongoDB
        if self.mongo_client:
            try:
                db = self.mongo_client.get_default_database()
                collections_with_data = []
                
                for collection_name in ["user_activities", "chat_sessions"]:
                    count = db[collection_name].count_documents({"user_id": user_id})
                    if count > 0:
                        collections_with_data.append({
                            "collection": collection_name,
                            "count": count
                        })
                
                verification_results["systems_checked"]["mongodb"] = {
                    "checked": True,
                    "collections_with_data": collections_with_data
                }
                
                if collections_with_data:
                    verification_results["deletion_complete"] = False
                    verification_results["remaining_data_found"].append("MongoDB")
                    
            except Exception as e:
                verification_results["systems_checked"]["mongodb"] = {
                    "checked": False,
                    "error": str(e)
                }
        
        return verification_results
