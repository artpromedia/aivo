"""
Data export service for GDPR Article 20 compliance.

Handles data portability requests with 10 days completion requirement.
"""
import asyncio
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import boto3
import pymongo
import snowflake.connector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    AuditAction,
    DataExportRequest,
    RequestStatus,
)

import logging

logger = logging.getLogger(__name__)


def is_export_overdue(requested_at: datetime, max_days: int = 10) -> bool:
    """Helper function to check if export request is overdue."""
    return datetime.utcnow() > requested_at + timedelta(days=max_days)


def calculate_days_remaining(requested_at: datetime, max_days: int = 10) -> int:
    """Helper function to calculate days remaining for export completion."""
    due_date = requested_at + timedelta(days=max_days)
    remaining = due_date - datetime.utcnow()
    return max(0, remaining.days)


def format_export_filename(user_id: str, request_id: UUID, format_type: str) -> str:
    """Helper function to generate standardized export filename."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"data_export_{user_id}_{request_id}_{timestamp}.{format_type}"


class DataExportService:
    """
    Service for handling user data export requests.
    
    Ensures GDPR Article 20 compliance with 10 days completion.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        export_storage_path: Path,
        s3_client: Optional[boto3.client] = None,
        mongo_client: Optional[pymongo.MongoClient] = None,
        snowflake_config: Optional[Dict[str, Any]] = None,
    ):
        self.db_session = db_session
        self.export_storage_path = export_storage_path
        self.s3_client = s3_client
        self.mongo_client = mongo_client
        self.snowflake_config = snowflake_config or {}
        
        # Ensure export directory exists
        self.export_storage_path.mkdir(parents=True, exist_ok=True)
    
    async def create_export_request(
        self,
        user_id: str,
        requestor_email: str,
        request_type: str = "full_export",
        data_categories: Optional[List[str]] = None,
        format_preference: str = "json",
        is_parental_request: bool = False,
        parent_email: Optional[str] = None,
    ) -> DataExportRequest:
        """
        Create new data export request.
        
        Automatically schedules export for completion within 10 days.
        """
        logger.info(f"Creating data export request for user {user_id}")
        
        # Validate request
        if is_parental_request and not parent_email:
            raise ValueError("Parent email required for parental requests")
        
        # Create export request
        export_request = DataExportRequest(
            user_id=user_id,
            requestor_email=requestor_email,
            request_type=request_type,
            data_categories=data_categories or [],
            format_preference=format_preference,
            is_parental_request=is_parental_request,
            parent_email=parent_email,
            parent_verified=False if is_parental_request else True,
        )
        
        self.db_session.add(export_request)
        await self.db_session.flush()
        
        # Create audit log
        from app.services.consent_service import ConsentService
        consent_service = ConsentService(self.db_session)
        
        await consent_service._create_audit_log(
            action=AuditAction.DATA_EXPORT_REQUESTED,
            user_id=user_id,
            export_request_id=export_request.id,
            actor_id=requestor_email,
            actor_type="parent" if is_parental_request else "user",
            details={
                "request_type": request_type,
                "format_preference": format_preference,
                "data_categories": data_categories or [],
                "is_parental_request": is_parental_request,
            },
        )
        
        await self.db_session.commit()
        
        # Schedule export processing (would be handled by Celery in production)
        logger.info(f"Export request {export_request.id} created, scheduling processing")
        
        return export_request
    
    async def process_export_request(
        self,
        request_id: UUID,
    ) -> DataExportRequest:
        """
        Process data export request by collecting data from all systems.
        
        Must complete within 10 days of request.
        """
        # Get export request
        stmt = select(DataExportRequest).where(DataExportRequest.id == request_id)
        result = await self.db_session.execute(stmt)
        export_request = result.scalar_one_or_none()
        
        if not export_request:
            raise ValueError(f"Export request {request_id} not found")
        
        if export_request.status != RequestStatus.PENDING:
            raise ValueError(f"Export request {request_id} is not pending")
        
        user_id = export_request.user_id
        logger.info(f"Processing export request {request_id} for user {user_id}")
        
        # Check if request is overdue
        if is_export_overdue(export_request.requested_at):
            export_request.status = RequestStatus.FAILED
            export_request.error_message = "Export request exceeded 10-day deadline"
            await self.db_session.commit()
            raise RuntimeError("Export request exceeded 10-day deadline")
        
        try:
            # Update status
            export_request.status = RequestStatus.IN_PROGRESS
            export_request.started_at = datetime.utcnow()
            await self.db_session.commit()
            
            # Collect data from all systems
            export_data = await self._collect_user_data(user_id, export_request)
            
            # Generate export file
            export_file_path = await self._generate_export_file(
                user_id, request_id, export_data, export_request.format_preference
            )
            
            # Update export request with file details
            export_request.export_file_path = str(export_file_path)
            export_request.export_file_size_bytes = export_file_path.stat().st_size
            export_request.status = RequestStatus.COMPLETED
            export_request.completed_at = datetime.utcnow()
            
            # Generate download URL (expires in 30 days)
            download_url = self._generate_download_url(export_file_path)
            export_request.download_url = download_url
            export_request.download_expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Mark data sources as exported
            export_request.postgres_exported = True
            export_request.mongodb_exported = bool(self.mongo_client)
            export_request.s3_exported = bool(self.s3_client)
            export_request.snowflake_exported = bool(self.snowflake_config)
            
            await self.db_session.commit()
            
            # Create completion audit log
            from app.services.consent_service import ConsentService
            consent_service = ConsentService(self.db_session)
            
            await consent_service._create_audit_log(
                action=AuditAction.DATA_EXPORT_COMPLETED,
                user_id=user_id,
                export_request_id=export_request.id,
                actor_id="system",
                actor_type="system",
                details={
                    "export_file_size": export_request.export_file_size_bytes,
                    "completion_time_hours": (
                        export_request.completed_at - export_request.started_at
                    ).total_seconds() / 3600,
                    "data_sources": {
                        "postgres": export_request.postgres_exported,
                        "mongodb": export_request.mongodb_exported,
                        "s3": export_request.s3_exported,
                        "snowflake": export_request.snowflake_exported,
                    },
                },
            )
            
            logger.info(f"Export request {request_id} completed successfully")
            return export_request
            
        except Exception as e:
            logger.error(f"Export request {request_id} failed: {str(e)}")
            
            export_request.status = RequestStatus.FAILED
            export_request.error_message = str(e)
            export_request.retry_count += 1
            await self.db_session.commit()
            
            raise
    
    async def _collect_user_data(
        self,
        user_id: str,
        export_request: DataExportRequest,
    ) -> Dict[str, Any]:
        """Collect user data from all configured systems."""
        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "request_details": {
                "request_type": export_request.request_type,
                "data_categories": export_request.data_categories,
                "format": export_request.format_preference,
            },
            "data_sources": {},
        }
        
        # Collect from PostgreSQL
        try:
            postgres_data = await self._collect_postgres_data(user_id)
            export_data["data_sources"]["postgresql"] = postgres_data
            logger.info(f"Collected PostgreSQL data for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to collect PostgreSQL data: {str(e)}")
            export_data["data_sources"]["postgresql"] = {"error": str(e)}
        
        # Collect from MongoDB
        if self.mongo_client:
            try:
                mongodb_data = await self._collect_mongodb_data(user_id)
                export_data["data_sources"]["mongodb"] = mongodb_data
                logger.info(f"Collected MongoDB data for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to collect MongoDB data: {str(e)}")
                export_data["data_sources"]["mongodb"] = {"error": str(e)}
        
        # Collect from S3
        if self.s3_client:
            try:
                s3_data = await self._collect_s3_data(user_id)
                export_data["data_sources"]["s3"] = s3_data
                logger.info(f"Collected S3 data for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to collect S3 data: {str(e)}")
                export_data["data_sources"]["s3"] = {"error": str(e)}
        
        # Collect from Snowflake
        if self.snowflake_config:
            try:
                snowflake_data = await self._collect_snowflake_data(user_id)
                export_data["data_sources"]["snowflake"] = snowflake_data
                logger.info(f"Collected Snowflake data for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to collect Snowflake data: {str(e)}")
                export_data["data_sources"]["snowflake"] = {"error": str(e)}
        
        return export_data
    
    async def _collect_postgres_data(self, user_id: str) -> Dict[str, Any]:
        """Collect user data from PostgreSQL database."""
        postgres_data = {}
        
        # Tables to export
        user_tables = [
            "consent_records",
            "preference_settings",
            "parental_rights",
            "audit_logs",
            # Add other user data tables
            "user_profiles",
            "user_activities",
            "chat_messages",
        ]
        
        for table in user_tables:
            try:
                # Check if table exists and has user_id column
                check_query = text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = :table_name AND column_name = 'user_id'"
                )
                result = await self.db_session.execute(check_query, {"table_name": table})
                has_user_id = result.scalar() is not None
                
                if not has_user_id:
                    continue
                
                # Export user data from table
                export_query = text(f"SELECT * FROM {table} WHERE user_id = :user_id")
                result = await self.db_session.execute(export_query, {"user_id": user_id})
                
                rows = []
                for row in result:
                    row_dict = {}
                    for key, value in row._mapping.items():
                        # Convert non-serializable types
                        if isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                        elif hasattr(value, '__dict__'):  # Enum or custom objects
                            row_dict[key] = str(value)
                        else:
                            row_dict[key] = value
                    rows.append(row_dict)
                
                postgres_data[table] = {
                    "record_count": len(rows),
                    "records": rows,
                }
                
            except Exception as e:
                logger.warning(f"Failed to export table {table}: {str(e)}")
                postgres_data[table] = {"error": str(e)}
        
        return postgres_data
    
    async def _collect_mongodb_data(self, user_id: str) -> Dict[str, Any]:
        """Collect user data from MongoDB collections."""
        mongodb_data = {}
        
        if not self.mongo_client:
            return {"error": "MongoDB client not configured"}
        
        db = self.mongo_client.get_default_database()
        
        # Collections to export
        user_collections = [
            "user_activities",
            "chat_sessions",
            "media_metadata",
            "behavioral_data",
            "analytics_events",
        ]
        
        for collection_name in user_collections:
            try:
                collection = db[collection_name]
                
                # Find documents for this user
                documents = list(collection.find({"user_id": user_id}))
                
                # Convert ObjectIds to strings
                for doc in documents:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    # Convert datetime objects
                    for key, value in doc.items():
                        if isinstance(value, datetime):
                            doc[key] = value.isoformat()
                
                mongodb_data[collection_name] = {
                    "document_count": len(documents),
                    "documents": documents,
                }
                
            except Exception as e:
                logger.warning(f"Failed to export collection {collection_name}: {str(e)}")
                mongodb_data[collection_name] = {"error": str(e)}
        
        return mongodb_data
    
    async def _collect_s3_data(self, user_id: str) -> Dict[str, Any]:
        """Collect user files from S3 storage."""
        s3_data = {"files": [], "total_size_bytes": 0}
        
        if not self.s3_client:
            return {"error": "S3 client not configured"}
        
        # S3 buckets with user data
        user_buckets = [
            "user-uploads",
            "profile-images",
            "chat-media",
            "exported-data",
        ]
        
        for bucket_name in user_buckets:
            try:
                # List objects with user_id prefix
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    Prefix=f"users/{user_id}/",
                )
                
                if "Contents" in response:
                    for obj in response["Contents"]:
                        file_info = {
                            "bucket": bucket_name,
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"].isoformat(),
                            "download_url": f"s3://{bucket_name}/{obj['Key']}",
                        }
                        s3_data["files"].append(file_info)
                        s3_data["total_size_bytes"] += obj["Size"]
                
            except Exception as e:
                logger.warning(f"Failed to list S3 bucket {bucket_name}: {str(e)}")
                s3_data[f"bucket_{bucket_name}_error"] = str(e)
        
        return s3_data
    
    async def _collect_snowflake_data(self, user_id: str) -> Dict[str, Any]:
        """Collect user data from Snowflake data warehouse."""
        snowflake_data = {}
        
        if not self.snowflake_config:
            return {"error": "Snowflake configuration not provided"}
        
        try:
            # Connect to Snowflake
            conn = snowflake.connector.connect(**self.snowflake_config)
            cursor = conn.cursor()
            
            # Tables to export
            user_tables = [
                "analytics.user_events",
                "analytics.user_sessions", 
                "reporting.user_metrics",
                "data_lake.user_interactions",
            ]
            
            for table in user_tables:
                try:
                    # Export user data
                    query = f"SELECT * FROM {table} WHERE user_id = %s"
                    cursor.execute(query, (user_id,))
                    
                    # Get column names
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Fetch all rows
                    rows = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    records = []
                    for row in rows:
                        record = {}
                        for i, value in enumerate(row):
                            if isinstance(value, datetime):
                                record[columns[i]] = value.isoformat()
                            else:
                                record[columns[i]] = value
                        records.append(record)
                    
                    snowflake_data[table] = {
                        "record_count": len(records),
                        "records": records,
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to export Snowflake table {table}: {str(e)}")
                    snowflake_data[table] = {"error": str(e)}
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            return {"error": str(e)}
        
        return snowflake_data
    
    async def _generate_export_file(
        self,
        user_id: str,
        request_id: UUID,
        export_data: Dict[str, Any],
        format_preference: str,
    ) -> Path:
        """Generate export file in requested format."""
        filename = format_export_filename(user_id, request_id, format_preference)
        export_file_path = self.export_storage_path / filename
        
        if format_preference == "json":
            with open(export_file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
        elif format_preference == "zip":
            # Create ZIP file with JSON data and metadata
            with zipfile.ZipFile(export_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add main data file
                data_json = json.dumps(export_data, indent=2, ensure_ascii=False)
                zipf.writestr("user_data.json", data_json)
                
                # Add metadata file
                metadata = {
                    "export_info": {
                        "user_id": user_id,
                        "request_id": str(request_id),
                        "generated_at": datetime.utcnow().isoformat(),
                        "format": format_preference,
                        "gdpr_article": "Article 20 - Right to data portability",
                    }
                }
                metadata_json = json.dumps(metadata, indent=2)
                zipf.writestr("export_metadata.json", metadata_json)
        
        else:
            raise ValueError(f"Unsupported export format: {format_preference}")
        
        logger.info(f"Generated export file: {export_file_path}")
        return export_file_path
    
    def _generate_download_url(self, export_file_path: Path) -> str:
        """Generate secure download URL for export file."""
        # In production, this would generate a signed URL or secure token
        filename = export_file_path.name
        return f"/api/exports/download/{filename}"
    
    async def get_export_status(self, request_id: UUID) -> Dict[str, Any]:
        """Get status and progress of export request."""
        stmt = select(DataExportRequest).where(DataExportRequest.id == request_id)
        result = await self.db_session.execute(stmt)
        export_request = result.scalar_one_or_none()
        
        if not export_request:
            raise ValueError(f"Export request {request_id} not found")
        
        # Calculate progress information
        days_remaining = calculate_days_remaining(export_request.requested_at)
        is_overdue = is_export_overdue(export_request.requested_at)
        
        return {
            "request_id": str(export_request.id),
            "status": export_request.status.value,
            "requested_at": export_request.requested_at.isoformat(),
            "started_at": export_request.started_at.isoformat() if export_request.started_at else None,
            "completed_at": export_request.completed_at.isoformat() if export_request.completed_at else None,
            "days_remaining": days_remaining,
            "is_overdue": is_overdue,
            "file_size_bytes": export_request.export_file_size_bytes,
            "download_url": export_request.download_url,
            "download_expires_at": export_request.download_expires_at.isoformat() if export_request.download_expires_at else None,
            "data_sources_exported": {
                "postgres": export_request.postgres_exported,
                "mongodb": export_request.mongodb_exported,
                "s3": export_request.s3_exported,
                "snowflake": export_request.snowflake_exported,
            },
            "error_message": export_request.error_message,
        }
