"""
Audit service with Merkle chain and export capabilities.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import UUID

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from motor.motor_asyncio import AsyncIOMotorClient
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from ..models import AuditEntry, ChatMessage
from ..schemas import AuditEntryResponse

logger = logging.getLogger(__name__)


class MerkleTree:
    """Merkle tree implementation for audit chain."""
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Hash data using SHA-256."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def build_merkle_root(hashes: List[str]) -> str:
        """Build Merkle root from list of hashes."""
        if not hashes:
            return ""
        
        if len(hashes) == 1:
            return hashes[0]
        
        # Pad with duplicate if odd number
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        
        # Build tree bottom-up
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                next_level.append(MerkleTree.hash_data(combined))
            hashes = next_level
        
        return hashes[0]
    
    @staticmethod
    def create_block_hash(
        message_id: str,
        content_hash: str,
        previous_hash: Optional[str],
        timestamp: datetime
    ) -> str:
        """Create block hash for audit entry."""
        block_data = {
            'message_id': message_id,
            'content_hash': content_hash,
            'previous_hash': previous_hash or "",
            'timestamp': timestamp.isoformat()
        }
        return MerkleTree.hash_data(json.dumps(block_data, sort_keys=True))


class S3ExportService:
    """S3 export service for chat data."""
    
    def __init__(self, bucket_name: str, aws_access_key_id: str, aws_secret_access_key: str, region: str = 'us-east-1'):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )
    
    async def export_to_s3(self, data: Dict[str, Any], key: str) -> bool:
        """Export data to S3."""
        try:
            # Convert to JSON string
            json_data = json.dumps(data, default=str, ensure_ascii=False)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully exported data to S3: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to export to S3: {e}")
            return False
    
    async def export_parquet(self, messages_data: List[Dict[str, Any]], key: str) -> bool:
        """Export messages to Parquet format."""
        try:
            # Create DataFrame
            df = pd.DataFrame(messages_data)
            
            # Convert to Parquet bytes
            parquet_buffer = df.to_parquet(index=False, engine='pyarrow')
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=parquet_buffer,
                ContentType='application/octet-stream',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"Successfully exported Parquet to S3: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Parquet: {e}")
            return False
    
    def generate_s3_key(self, session_id: UUID, export_type: str, timestamp: datetime) -> str:
        """Generate S3 key for export."""
        date_str = timestamp.strftime('%Y/%m/%d')
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        return f"chat-exports/{date_str}/{export_type}/{session_id}_{timestamp_str}.{export_type}"


class MongoArchiveService:
    """MongoDB archive service for long-term storage."""
    
    def __init__(self, connection_string: str, database_name: str = "aivo_archive"):
        self.client = AsyncIOMotorClient(connection_string)
        self.database = self.client[database_name]
        self.messages_collection = self.database.archived_messages
        self.sessions_collection = self.database.archived_sessions
    
    async def archive_session(self, session_data: Dict[str, Any]) -> bool:
        """Archive chat session to MongoDB."""
        try:
            await self.sessions_collection.insert_one(session_data)
            logger.info(f"Archived session {session_data.get('id')} to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to archive session: {e}")
            return False
    
    async def archive_messages(self, messages_data: List[Dict[str, Any]]) -> bool:
        """Archive messages to MongoDB."""
        try:
            if messages_data:
                await self.messages_collection.insert_many(messages_data)
                logger.info(f"Archived {len(messages_data)} messages to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to archive messages: {e}")
            return False
    
    async def close(self):
        """Close MongoDB connection."""
        self.client.close()


class AuditService:
    """Audit service for chat messages with Merkle chain."""
    
    def __init__(
        self,
        s3_service: S3ExportService,
        mongo_service: Optional[MongoArchiveService] = None
    ):
        self.s3_service = s3_service
        self.mongo_service = mongo_service
        self.merkle_tree = MerkleTree()
        
        # Generate RSA key pair for signing (in production, use proper key management)
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    async def create_audit_entry(
        self,
        db_session,
        message: ChatMessage,
        previous_entry: Optional[AuditEntry] = None
    ) -> AuditEntry:
        """Create audit entry for a message."""
        try:
            timestamp = datetime.now(timezone.utc)
            
            # Create content hash
            content_data = {
                'message_id': str(message.id),
                'sender_id': str(message.sender_id),
                'sender_role': message.sender_role.value,
                'content': message.original_content,
                'timestamp': message.created_at.isoformat()
            }
            data_hash = self.merkle_tree.hash_data(json.dumps(content_data, sort_keys=True))
            
            # Create block hash
            previous_hash = previous_entry.block_hash if previous_entry else None
            block_hash = self.merkle_tree.create_block_hash(
                str(message.id),
                data_hash,
                previous_hash,
                timestamp
            )
            
            # Create Merkle root (for now, just use block hash)
            merkle_root = self.merkle_tree.build_merkle_root([block_hash])
            
            # Sign the block hash
            signature = self._sign_data(block_hash)
            
            # Create audit entry
            audit_entry = AuditEntry(
                message_id=message.id,
                block_hash=block_hash,
                previous_hash=previous_hash,
                merkle_root=merkle_root,
                timestamp=timestamp,
                data_hash=data_hash,
                signature=signature
            )
            
            db_session.add(audit_entry)
            await db_session.commit()
            
            logger.info(f"Created audit entry for message {message.id}")
            return audit_entry
            
        except Exception as e:
            logger.error(f"Failed to create audit entry: {e}")
            await db_session.rollback()
            raise
    
    async def export_session_data(
        self,
        session_id: UUID,
        messages: List[ChatMessage],
        export_format: str = "json",
        include_pii: bool = False
    ) -> Optional[str]:
        """Export session data to S3."""
        try:
            timestamp = datetime.now(timezone.utc)
            
            # Prepare messages data
            messages_data = []
            for msg in messages:
                content = msg.original_content
                if not include_pii and msg.processed_content:
                    content = msg.processed_content
                
                message_data = {
                    'id': str(msg.id),
                    'session_id': str(msg.session_id),
                    'sender_id': str(msg.sender_id),
                    'sender_role': msg.sender_role.value,
                    'content': content,
                    'message_type': msg.message_type,
                    'created_at': msg.created_at.isoformat(),
                    'status': msg.status.value,
                    'moderation_score': msg.moderation_score,
                    'contains_pii': msg.contains_pii,
                    'pii_types': msg.pii_types
                }
                messages_data.append(message_data)
            
            # Generate S3 key
            s3_key = self.s3_service.generate_s3_key(session_id, export_format, timestamp)
            
            # Export based on format
            if export_format == "parquet":
                success = await self.s3_service.export_parquet(messages_data, s3_key)
            else:
                export_data = {
                    'session_id': str(session_id),
                    'exported_at': timestamp.isoformat(),
                    'message_count': len(messages_data),
                    'include_pii': include_pii,
                    'messages': messages_data
                }
                success = await self.s3_service.export_to_s3(export_data, s3_key)
            
            if success:
                return s3_key
            return None
            
        except Exception as e:
            logger.error(f"Failed to export session data: {e}")
            return None
    
    async def archive_session(
        self,
        db_session,
        session_id: UUID,
        messages: List[ChatMessage]
    ) -> bool:
        """Archive session to MongoDB and update audit entries."""
        try:
            if not self.mongo_service:
                logger.warning("MongoDB service not configured for archiving")
                return False
            
            # Prepare session data for archiving
            session_data = {
                'session_id': str(session_id),
                'archived_at': datetime.now(timezone.utc).isoformat(),
                'message_count': len(messages)
            }
            
            # Prepare messages data
            messages_data = []
            for msg in messages:
                message_data = {
                    'id': str(msg.id),
                    'session_id': str(msg.session_id),
                    'sender_id': str(msg.sender_id),
                    'sender_role': msg.sender_role.value,
                    'content': msg.original_content,
                    'processed_content': msg.processed_content,
                    'content_hash': msg.content_hash,
                    'message_type': msg.message_type,
                    'created_at': msg.created_at.isoformat(),
                    'status': msg.status.value,
                    'moderation_score': msg.moderation_score,
                    'contains_pii': msg.contains_pii,
                    'pii_types': msg.pii_types
                }
                messages_data.append(message_data)
            
            # Archive to MongoDB
            await self.mongo_service.archive_session(session_data)
            await self.mongo_service.archive_messages(messages_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to archive session: {e}")
            return False
    
    def _sign_data(self, data: str) -> str:
        """Sign data with private key."""
        try:
            signature = self.private_key.sign(
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return signature.hex()
        except Exception as e:
            logger.error(f"Failed to sign data: {e}")
            return ""
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verify signature with public key."""
        try:
            self.public_key.verify(
                bytes.fromhex(signature),
                data.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def verify_audit_chain(self, audit_entries: List[AuditEntry]) -> bool:
        """Verify the integrity of audit chain."""
        try:
            for i, entry in enumerate(audit_entries):
                # Verify signature
                if not self.verify_signature(entry.block_hash, entry.signature or ""):
                    logger.error(f"Invalid signature for audit entry {entry.id}")
                    return False
                
                # Verify chain linkage
                if i > 0:
                    previous_entry = audit_entries[i - 1]
                    if entry.previous_hash != previous_entry.block_hash:
                        logger.error(f"Chain break at audit entry {entry.id}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify audit chain: {e}")
            return False
