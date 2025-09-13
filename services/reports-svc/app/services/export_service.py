"""Export service for generating CSV, PDF, and Excel reports."""

import os
import io
import csv
import boto3
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from uuid import UUID
import structlog

from .query_service import QueryService
from ..schemas import QueryConfig

logger = structlog.get_logger()

class ExportService:
    """Service for generating and managing export files."""

    def __init__(self):
        self.query_service = QueryService()
        self.s3_bucket = os.getenv("REPORTS_S3_BUCKET", "aivo-reports")
        self.s3_region = os.getenv("AWS_REGION", "us-east-1")
        self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "/tmp/reports")
        self.use_s3 = os.getenv("USE_S3_STORAGE", "false").lower() == "true"

        # Ensure local storage directory exists
        os.makedirs(self.local_storage_path, exist_ok=True)

    async def generate_export(
        self,
        export_id: UUID,
        query_config: Dict[str, Any],
        format: str,
        tenant_id: str,
        report_name: str,
        row_limit: int = 10000
    ) -> Dict[str, Any]:
        """Generate an export file and return file information."""
        start_time = datetime.utcnow()

        try:
            # Parse query configuration
            query_obj = QueryConfig(**query_config)

            # Apply row limit
            if not query_obj.limit or query_obj.limit > row_limit:
                query_obj.limit = row_limit

            # Execute query to get data
            query_result = await self.query_service.execute_query(query_obj, tenant_id)

            # Generate file based on format
            if format == "csv":
                file_content, content_type = self._generate_csv(query_result)
                file_extension = "csv"
            elif format == "pdf":
                file_content, content_type = self._generate_pdf(query_result, report_name)
                file_extension = "pdf"
            elif format == "xlsx":
                file_content, content_type = self._generate_excel(query_result, report_name)
                file_extension = "xlsx"
            else:
                raise ValueError(f"Unsupported export format: {format}")

            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_name}_{timestamp}_{export_id}.{file_extension}"
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")

            # Store file
            file_path, download_url = await self._store_file(
                file_content,
                safe_filename,
                content_type,
                tenant_id
            )

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "file_path": file_path,
                "file_size": len(file_content),
                "row_count": len(query_result["data"]),
                "download_url": download_url,
                "expires_at": datetime.utcnow() + timedelta(hours=24),  # 24 hour expiry
                "execution_time_ms": int(execution_time)
            }

        except Exception as e:
            logger.error("Export generation failed", export_id=str(export_id), error=str(e))
            raise

    def _generate_csv(self, query_result: Dict[str, Any]) -> Tuple[bytes, str]:
        """Generate CSV file from query result."""
        output = io.StringIO()

        if not query_result["data"]:
            return b"", "text/csv"

        # Write CSV
        writer = csv.DictWriter(output, fieldnames=query_result["columns"])
        writer.writeheader()
        writer.writerows(query_result["data"])

        csv_content = output.getvalue()
        return csv_content.encode('utf-8'), "text/csv"

    def _generate_excel(self, query_result: Dict[str, Any], report_name: str) -> Tuple[bytes, str]:
        """Generate Excel file from query result."""
        output = io.BytesIO()

        # Create DataFrame
        df = pd.DataFrame(query_result["data"])

        # Write to Excel with formatting
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report Data', index=False)

            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Report Data']

            # Add title
            worksheet.insert_rows(1)
            worksheet['A1'] = report_name
            worksheet['A1'].font = workbook.create_font(size=16, bold=True)

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def _generate_pdf(self, query_result: Dict[str, Any], report_name: str) -> Tuple[bytes, str]:
        """Generate PDF file from query result."""
        output = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(output, pagesize=A4)
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.black,
            spaceAfter=20
        )

        # Add title
        title = Paragraph(report_name, title_style)
        story.append(title)

        # Add metadata
        metadata = Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}<br/>"
            f"Total Records: {len(query_result['data'])}<br/>"
            f"Execution Time: {query_result.get('execution_time_ms', 0)}ms",
            styles['Normal']
        )
        story.append(metadata)
        story.append(Spacer(1, 20))

        if query_result["data"]:
            # Prepare table data
            table_data = [query_result["columns"]]  # Headers

            # Add data rows (limit for PDF readability)
            max_rows_per_page = 25
            rows_added = 0

            for row in query_result["data"]:
                if rows_added >= max_rows_per_page:
                    # Create table for current page
                    table = Table(table_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))

                    story.append(table)
                    story.append(PageBreak())

                    # Reset for next page
                    table_data = [query_result["columns"]]
                    rows_added = 0

                # Convert row values to strings and truncate if too long
                row_values = []
                for col in query_result["columns"]:
                    value = str(row.get(col, ""))
                    if len(value) > 50:
                        value = value[:47] + "..."
                    row_values.append(value)

                table_data.append(row_values)
                rows_added += 1

            # Add final table if there's remaining data
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                story.append(table)
        else:
            story.append(Paragraph("No data available", styles['Normal']))

        # Build PDF
        doc.build(story)

        return output.getvalue(), "application/pdf"

    async def _store_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        tenant_id: str
    ) -> Tuple[str, str]:
        """Store file in S3 or local storage and return path and download URL."""

        if self.use_s3:
            return await self._store_in_s3(file_content, filename, content_type, tenant_id)
        else:
            return await self._store_locally(file_content, filename, tenant_id)

    async def _store_in_s3(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        tenant_id: str
    ) -> Tuple[str, str]:
        """Store file in S3 and return S3 path and presigned URL."""
        try:
            s3_client = boto3.client('s3', region_name=self.s3_region)

            # S3 key with tenant isolation
            s3_key = f"exports/{tenant_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"

            # Upload file
            s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )

            # Generate presigned URL (valid for 24 hours)
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=86400  # 24 hours
            )

            return f"s3://{self.s3_bucket}/{s3_key}", download_url

        except Exception as e:
            logger.error("Failed to store file in S3", filename=filename, error=str(e))
            raise

    async def _store_locally(
        self,
        file_content: bytes,
        filename: str,
        tenant_id: str
    ) -> Tuple[str, str]:
        """Store file locally and return file path and URL."""
        try:
            # Create tenant directory
            tenant_dir = os.path.join(self.local_storage_path, tenant_id)
            os.makedirs(tenant_dir, exist_ok=True)

            # File path
            file_path = os.path.join(tenant_dir, filename)

            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # For local storage, the download URL would be served by the API
            download_url = f"/api/v1/exports/files/{tenant_id}/{filename}"

            return file_path, download_url

        except Exception as e:
            logger.error("Failed to store file locally", filename=filename, error=str(e))
            raise

    async def get_export_file(self, file_path: str, format: str) -> Tuple[bytes, str, str]:
        """Retrieve export file content for download."""
        try:
            if file_path.startswith("s3://"):
                return await self._get_file_from_s3(file_path)
            else:
                return await self._get_file_locally(file_path, format)
        except Exception as e:
            logger.error("Failed to retrieve export file", file_path=file_path, error=str(e))
            raise

    async def _get_file_from_s3(self, s3_path: str) -> Tuple[bytes, str, str]:
        """Get file from S3."""
        # Parse S3 path
        parts = s3_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        s3_client = boto3.client('s3', region_name=self.s3_region)

        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        content_type = response.get('ContentType', 'application/octet-stream')
        filename = os.path.basename(key)

        return file_content, content_type, filename

    async def _get_file_locally(self, file_path: str, format: str) -> Tuple[bytes, str, str]:
        """Get file from local storage."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Export file not found: {file_path}")

        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Determine content type
        content_types = {
            "csv": "text/csv",
            "pdf": "application/pdf",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        content_type = content_types.get(format, "application/octet-stream")
        filename = os.path.basename(file_path)

        return file_content, content_type, filename

    async def delete_export_file(self, file_path: str):
        """Delete an export file from storage."""
        try:
            if file_path.startswith("s3://"):
                await self._delete_file_from_s3(file_path)
            else:
                await self._delete_file_locally(file_path)
        except Exception as e:
            logger.error("Failed to delete export file", file_path=file_path, error=str(e))
            raise

    async def _delete_file_from_s3(self, s3_path: str):
        """Delete file from S3."""
        parts = s3_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        s3_client = boto3.client('s3', region_name=self.s3_region)
        s3_client.delete_object(Bucket=bucket, Key=key)

    async def _delete_file_locally(self, file_path: str):
        """Delete file from local storage."""
        if os.path.exists(file_path):
            os.remove(file_path)
