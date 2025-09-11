"""AWS Textract integration for text extraction from documents."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from ..schemas import TextractConfig

logger = logging.getLogger(__name__)


class TextractExtractor:
    """AWS Textract client for document text extraction."""

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ) -> None:
        """Initialize Textract client.
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key  
            region_name: AWS region name
        """
        try:
            self.textract_client = boto3.client(
                "textract",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
            )
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name,
            )
        except NoCredentialsError as e:
            logger.error("AWS credentials not found: %s", e)
            raise
        except Exception as e:
            logger.error("Failed to initialize Textract client: %s", e)
            raise

    async def extract_text_from_s3(
        self,
        bucket: str,
        key: str,
        config: Optional[TextractConfig] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract text from document stored in S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            config: Textract configuration
            
        Returns:
            Tuple of (extracted_text, metadata)
            
        Raises:
            ClientError: If AWS service call fails
            ValueError: If document format is not supported
        """
        if config is None:
            config = TextractConfig()

        try:
            # Check file type and size
            metadata = await self._get_s3_metadata(bucket, key)
            file_size = metadata.get("ContentLength", 0)
            content_type = metadata.get("ContentType", "")

            logger.info(
                "Processing document: %s/%s (size: %d, type: %s)",
                bucket,
                key,
                file_size,
                content_type,
            )

            if file_size > 500 * 1024 * 1024:  # 500MB limit
                raise ValueError("Document size exceeds Textract limit")

            # Determine processing method based on document complexity
            if config.analyze_document and self._needs_analysis(content_type):
                return await self._analyze_document(bucket, key, config)
            else:
                return await self._detect_text(bucket, key, config)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error("AWS Textract error (%s): %s", error_code, e)
            raise
        except Exception as e:
            logger.error("Text extraction failed: %s", e)
            raise

    async def _get_s3_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        """Get S3 object metadata."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self.s3_client.head_object,
            {"Bucket": bucket, "Key": key},
        )
        return response

    async def _detect_text(
        self,
        bucket: str,
        key: str,
        config: TextractConfig,
    ) -> Tuple[str, Dict[str, Any]]:
        """Use Textract DetectDocumentText for simple text extraction."""
        loop = asyncio.get_event_loop()
        
        response = await loop.run_in_executor(
            None,
            self.textract_client.detect_document_text,
            {
                "Document": {
                    "S3Object": {
                        "Bucket": bucket,
                        "Name": key,
                    },
                },
            },
        )

        text_blocks = []
        metadata = {
            "extraction_method": "detect_document_text",
            "blocks_detected": len(response.get("Blocks", [])),
            "confidence_scores": [],
            "textract_job_id": None,
        }

        for block in response.get("Blocks", []):
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "")
                confidence = block.get("Confidence", 0)
                
                if confidence >= (config.confidence_threshold * 100):
                    text_blocks.append(text)
                    metadata["confidence_scores"].append(confidence)

        extracted_text = "\n".join(text_blocks)
        metadata["average_confidence"] = (
            sum(metadata["confidence_scores"]) / len(metadata["confidence_scores"])
            if metadata["confidence_scores"]
            else 0
        )

        logger.info(
            "Text detection completed: %d lines, avg confidence: %.2f",
            len(text_blocks),
            metadata["average_confidence"],
        )

        return extracted_text, metadata

    async def _analyze_document(
        self,
        bucket: str,
        key: str,
        config: TextractConfig,
    ) -> Tuple[str, Dict[str, Any]]:
        """Use Textract AnalyzeDocument for advanced extraction."""
        loop = asyncio.get_event_loop()

        analyze_params = {
            "Document": {
                "S3Object": {
                    "Bucket": bucket,
                    "Name": key,
                },
            },
            "FeatureTypes": config.feature_types,
        }

        response = await loop.run_in_executor(
            None,
            self.textract_client.analyze_document,
            analyze_params,
        )

        text_blocks = []
        tables = []
        forms = []
        signatures = []
        
        metadata = {
            "extraction_method": "analyze_document",
            "blocks_detected": len(response.get("Blocks", [])),
            "feature_types": config.feature_types,
            "confidence_scores": [],
            "tables_found": 0,
            "forms_found": 0,
            "signatures_found": 0,
            "textract_job_id": None,
        }

        blocks_by_id = {
            block["Id"]: block 
            for block in response.get("Blocks", [])
        }

        for block in response.get("Blocks", []):
            block_type = block.get("BlockType")
            confidence = block.get("Confidence", 0)

            if confidence < (config.confidence_threshold * 100):
                continue

            metadata["confidence_scores"].append(confidence)

            if block_type == "LINE":
                text_blocks.append(block.get("Text", ""))
            elif block_type == "TABLE":
                table_text = self._extract_table_text(block, blocks_by_id)
                if table_text:
                    tables.append(table_text)
                    metadata["tables_found"] += 1
            elif block_type == "KEY_VALUE_SET":
                form_text = self._extract_form_text(block, blocks_by_id)
                if form_text:
                    forms.append(form_text)
                    metadata["forms_found"] += 1
            elif block_type == "SIGNATURE":
                signatures.append("SIGNATURE_DETECTED")
                metadata["signatures_found"] += 1

        # Combine all extracted text
        all_text = []
        all_text.extend(text_blocks)
        
        if tables:
            all_text.append("\n=== TABLES ===")
            all_text.extend(tables)
            
        if forms:
            all_text.append("\n=== FORMS ===")
            all_text.extend(forms)
            
        if signatures:
            all_text.append("\n=== SIGNATURES ===")
            all_text.extend(signatures)

        extracted_text = "\n".join(all_text)
        metadata["average_confidence"] = (
            sum(metadata["confidence_scores"]) / len(metadata["confidence_scores"])
            if metadata["confidence_scores"]
            else 0
        )

        logger.info(
            "Document analysis completed: %d lines, %d tables, %d forms, %d sigs",
            len(text_blocks),
            metadata["tables_found"],
            metadata["forms_found"],
            metadata["signatures_found"],
        )

        return extracted_text, metadata

    def _extract_table_text(
        self,
        table_block: Dict[str, Any],
        blocks_by_id: Dict[str, Dict[str, Any]],
    ) -> str:
        """Extract text from table blocks."""
        if not table_block.get("Relationships"):
            return ""

        cells = []
        for relationship in table_block["Relationships"]:
            if relationship.get("Type") == "CHILD":
                for cell_id in relationship.get("Ids", []):
                    cell_block = blocks_by_id.get(cell_id)
                    if cell_block and cell_block.get("BlockType") == "CELL":
                        cell_text = self._get_cell_text(cell_block, blocks_by_id)
                        row_index = cell_block.get("RowIndex", 0)
                        col_index = cell_block.get("ColumnIndex", 0)
                        cells.append((row_index, col_index, cell_text))

        if not cells:
            return ""

        # Sort cells by row and column
        cells.sort(key=lambda x: (x[0], x[1]))
        
        # Group by rows
        rows = {}
        for row_idx, col_idx, text in cells:
            if row_idx not in rows:
                rows[row_idx] = {}
            rows[row_idx][col_idx] = text

        # Build table text
        table_lines = []
        for row_idx in sorted(rows.keys()):
            row_cells = [
                rows[row_idx].get(col_idx, "") 
                for col_idx in sorted(rows[row_idx].keys())
            ]
            table_lines.append(" | ".join(row_cells))

        return "\n".join(table_lines)

    def _get_cell_text(
        self,
        cell_block: Dict[str, Any],
        blocks_by_id: Dict[str, Dict[str, Any]],
    ) -> str:
        """Extract text from a cell block."""
        if not cell_block.get("Relationships"):
            return ""

        texts = []
        for relationship in cell_block["Relationships"]:
            if relationship.get("Type") == "CHILD":
                for word_id in relationship.get("Ids", []):
                    word_block = blocks_by_id.get(word_id)
                    if word_block and word_block.get("BlockType") == "WORD":
                        texts.append(word_block.get("Text", ""))

        return " ".join(texts)

    def _extract_form_text(
        self,
        kvs_block: Dict[str, Any],
        blocks_by_id: Dict[str, Dict[str, Any]],
    ) -> str:
        """Extract text from key-value set blocks."""
        entity_types = kvs_block.get("EntityTypes", [])
        
        if "KEY" in entity_types:
            key_text = self._get_kvs_text(kvs_block, blocks_by_id)
            value_text = self._get_kvs_value_text(kvs_block, blocks_by_id)
            if key_text and value_text:
                return f"{key_text}: {value_text}"
            elif key_text:
                return key_text
        
        return ""

    def _get_kvs_text(
        self,
        kvs_block: Dict[str, Any],
        blocks_by_id: Dict[str, Dict[str, Any]],
    ) -> str:
        """Get text from key-value set block."""
        if not kvs_block.get("Relationships"):
            return ""

        texts = []
        for relationship in kvs_block["Relationships"]:
            if relationship.get("Type") == "CHILD":
                for word_id in relationship.get("Ids", []):
                    word_block = blocks_by_id.get(word_id)
                    if word_block and word_block.get("BlockType") == "WORD":
                        texts.append(word_block.get("Text", ""))

        return " ".join(texts)

    def _get_kvs_value_text(
        self,
        kvs_block: Dict[str, Any],
        blocks_by_id: Dict[str, Dict[str, Any]],
    ) -> str:
        """Get value text for a key block."""
        if not kvs_block.get("Relationships"):
            return ""

        for relationship in kvs_block["Relationships"]:
            if relationship.get("Type") == "VALUE":
                for value_id in relationship.get("Ids", []):
                    value_block = blocks_by_id.get(value_id)
                    if value_block:
                        return self._get_kvs_text(value_block, blocks_by_id)

        return ""

    def _needs_analysis(self, content_type: str) -> bool:
        """Determine if document needs advanced analysis."""
        # Complex document types that benefit from AnalyzeDocument
        complex_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/msword",
        }
        return content_type in complex_types

    async def start_async_job(
        self,
        bucket: str,
        key: str,
        config: Optional[TextractConfig] = None,
    ) -> str:
        """Start asynchronous document analysis job.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            config: Textract configuration
            
        Returns:
            Job ID for tracking
        """
        if config is None:
            config = TextractConfig()

        loop = asyncio.get_event_loop()
        
        job_params = {
            "DocumentLocation": {
                "S3Object": {
                    "Bucket": bucket,
                    "Name": key,
                },
            },
            "FeatureTypes": config.feature_types,
        }

        response = await loop.run_in_executor(
            None,
            self.textract_client.start_document_analysis,
            job_params,
        )

        job_id = response["JobId"]
        logger.info("Started async Textract job: %s", job_id)
        return job_id

    async def get_async_job_result(self, job_id: str) -> Dict[str, Any]:
        """Get result of asynchronous job.
        
        Args:
            job_id: Job ID returned from start_async_job
            
        Returns:
            Job result including status and extracted data
        """
        loop = asyncio.get_event_loop()
        
        response = await loop.run_in_executor(
            None,
            self.textract_client.get_document_analysis,
            {"JobId": job_id},
        )

        return response
