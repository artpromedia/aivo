"""Main FastAPI application for Evidence Service."""
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .extractors.textract import TextractExtractor
from .extractors.whisper import WhisperExtractor
from .linkage.iep_goals import IEPGoalLinker
from .models import EvidenceUpload, IEPGoal, IEPGoalLinkage
from .processors.audit_chain import AuditChain
from .processors.keywords import KeywordExtractor
from .schemas import (
    EvidenceExtractionResponse,
    EvidenceUploadCreate,
    EvidenceUploadResponse,
    IEPGoalCreate,
    IEPGoalLinkageResponse,
    IEPGoalResponse,
    KeywordExtractionResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize global components
textract_extractor = None
whisper_extractor = None
keyword_extractor = None
iep_goal_linker = None
audit_chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global textract_extractor, whisper_extractor, keyword_extractor
    global iep_goal_linker, audit_chain
    
    # Startup
    logger.info("Starting Evidence Service")
    
    # Initialize extractors
    textract_extractor = TextractExtractor(
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        s3_bucket=os.getenv("S3_BUCKET", "evidence-uploads"),
    )
    
    whisper_extractor = WhisperExtractor(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        s3_bucket=os.getenv("S3_BUCKET", "evidence-uploads"),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
    )
    
    # Initialize processors
    keyword_extractor = KeywordExtractor()
    iep_goal_linker = IEPGoalLinker()
    
    # Initialize audit chain
    audit_chain = AuditChain(
        private_key_path=os.getenv("AUDIT_PRIVATE_KEY_PATH"),
        public_key_path=os.getenv("AUDIT_PUBLIC_KEY_PATH"),
    )
    
    logger.info("Evidence Service initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Evidence Service")


# Create FastAPI app
app = FastAPI(
    title="Evidence Service",
    description="Extract keywords from uploads/recordings and attach evidence to IEP goals",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "evidence-svc"}


@app.post("/uploads", response_model=EvidenceUploadResponse)
async def upload_evidence(
    file: UploadFile = File(...),
    learner_id: str = "",
    uploaded_by: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Upload evidence file for processing.
    
    Args:
        file: Uploaded file
        learner_id: ID of learner
        uploaded_by: ID of user uploading
        db: Database session
        
    Returns:
        Upload details
    """
    try:
        # Validate required fields
        if not learner_id or not uploaded_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="learner_id and uploaded_by are required",
            )

        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have a filename",
            )

        # Read file content
        content = await file.read()
        
        # Determine file type
        file_extension = file.filename.split(".")[-1].lower()
        
        supported_document_types = ["pdf", "png", "jpg", "jpeg", "tiff", "bmp"]
        supported_audio_types = ["mp3", "wav", "m4a", "aac", "flac", "ogg"]
        
        if file_extension in supported_document_types:
            file_type = "document"
        elif file_extension in supported_audio_types:
            file_type = "audio"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}",
            )

        # Generate content hash for audit trail
        content_hash = audit_chain.generate_content_hash(content)

        # Create upload record
        upload_data = EvidenceUploadCreate(
            learner_id=uuid.UUID(learner_id),
            original_filename=file.filename,
            file_type=file_type,
            file_size=len(content),
            uploaded_by=uuid.UUID(uploaded_by),
            content_hash=content_hash,
        )

        # Save to database
        upload = EvidenceUpload(**upload_data.model_dump())
        db.add(upload)
        await db.commit()
        await db.refresh(upload)

        # Store file in S3 (using upload ID as key)
        s3_key = f"uploads/{upload.learner_id}/{upload.id}/{file.filename}"
        
        # Update S3 key in database
        upload.s3_key = s3_key
        await db.commit()

        # Create audit entry for upload
        await audit_chain.audit_upload_action(
            db=db,
            upload=upload,
            action_type="UPLOAD",
            performed_by=uuid.UUID(uploaded_by),
        )

        # Start async processing (in background)
        # Note: In production, this would be handled by a task queue
        try:
            await process_evidence_async(upload.id, db)
        except Exception as e:
            logger.error("Background processing failed for upload %s: %s", upload.id, e)

        logger.info(
            "File uploaded successfully: %s (ID: %s, Type: %s)",
            file.filename,
            upload.id,
            file_type,
        )

        return EvidenceUploadResponse.model_validate(upload)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


async def process_evidence_async(upload_id: uuid.UUID, db: AsyncSession):
    """Process uploaded evidence asynchronously.
    
    Args:
        upload_id: ID of uploaded evidence
        db: Database session
    """
    try:
        # Get upload record
        result = await db.execute(
            select(EvidenceUpload).where(EvidenceUpload.id == upload_id),
        )
        upload = result.scalar_one_or_none()
        
        if not upload:
            logger.error("Upload not found: %s", upload_id)
            return

        # Extract content based on file type
        extracted_text = ""
        extraction_metadata = {}

        if upload.file_type == "document":
            # Use Textract for documents
            extraction_result = await textract_extractor.extract_text_async(
                s3_key=upload.s3_key,
                upload_id=upload.id,
                analyze_document=True,
            )
            extracted_text = extraction_result.text
            extraction_metadata = extraction_result.metadata

        elif upload.file_type == "audio":
            # Use Whisper for audio
            extraction_result = await whisper_extractor.transcribe_async(
                s3_key=upload.s3_key,
                upload_id=upload.id,
                language="auto",
            )
            extracted_text = extraction_result.text
            extraction_metadata = extraction_result.metadata

        if not extracted_text:
            logger.warning("No text extracted from upload %s", upload_id)
            return

        # Extract keywords
        keyword_result = await keyword_extractor.extract_keywords_async(
            text=extracted_text,
            upload_id=upload.id,
        )

        # Link to IEP goals
        linkage_results = await iep_goal_linker.link_evidence_to_goals(
            db=db,
            upload_id=upload.id,
            extracted_text=extracted_text,
            keywords=keyword_result.keywords,
            subject_tags=keyword_result.subject_tags,
        )

        # Create audit entries for processing
        await audit_chain.create_audit_entry(
            db=db,
            upload_id=upload.id,
            learner_id=upload.learner_id,
            action_type="EXTRACT",
            action_details={
                "extraction_method": upload.file_type,
                "text_length": len(extracted_text),
                "keywords_count": len(keyword_result.keywords),
                "subject_tags": keyword_result.subject_tags,
                **extraction_metadata,
            },
            performed_by=upload.uploaded_by,
            content=extracted_text,
        )

        await audit_chain.create_audit_entry(
            db=db,
            upload_id=upload.id,
            learner_id=upload.learner_id,
            action_type="LINK",
            action_details={
                "linked_goals_count": len(linkage_results),
                "average_confidence": (
                    sum(r.confidence_score for r in linkage_results) / len(linkage_results)
                    if linkage_results else 0
                ),
            },
            performed_by=upload.uploaded_by,
        )

        logger.info(
            "Evidence processing completed for upload %s: %d keywords, %d goal links",
            upload_id,
            len(keyword_result.keywords),
            len(linkage_results),
        )

    except Exception as e:
        logger.error("Evidence processing failed for upload %s: %s", upload_id, e)
        
        # Create error audit entry
        await audit_chain.create_audit_entry(
            db=db,
            upload_id=upload_id,
            learner_id=upload.learner_id if upload else uuid.uuid4(),
            action_type="ERROR",
            action_details={
                "error_message": str(e),
                "processing_stage": "extraction_or_linking",
            },
            performed_by=upload.uploaded_by if upload else uuid.uuid4(),
        )


@app.get("/uploads/{upload_id}", response_model=EvidenceUploadResponse)
async def get_upload(upload_id: str, db: AsyncSession = Depends(get_db)):
    """Get upload details by ID.
    
    Args:
        upload_id: Upload ID
        db: Database session
        
    Returns:
        Upload details
    """
    try:
        result = await db.execute(
            select(EvidenceUpload).where(EvidenceUpload.id == uuid.UUID(upload_id)),
        )
        upload = result.scalar_one_or_none()
        
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found",
            )

        return EvidenceUploadResponse.model_validate(upload)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload ID format",
        )


@app.get("/uploads/{upload_id}/extraction", response_model=EvidenceExtractionResponse)
async def get_extraction(upload_id: str, db: AsyncSession = Depends(get_db)):
    """Get extraction results for an upload.
    
    Args:
        upload_id: Upload ID
        db: Database session
        
    Returns:
        Extraction results
    """
    try:
        # Implementation would query EvidenceExtraction table
        # For now, return placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Extraction endpoint not yet implemented",
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload ID format",
        )


@app.get("/uploads/{upload_id}/keywords", response_model=KeywordExtractionResponse)
async def get_keywords(upload_id: str, db: AsyncSession = Depends(get_db)):
    """Get keyword extraction results for an upload.
    
    Args:
        upload_id: Upload ID
        db: Database session
        
    Returns:
        Keyword extraction results
    """
    try:
        # Implementation would query keyword extraction results
        # For now, return placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Keywords endpoint not yet implemented",
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload ID format",
        )


@app.post("/iep-goals", response_model=IEPGoalResponse)
async def create_iep_goal(
    goal_data: IEPGoalCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new IEP goal.
    
    Args:
        goal_data: IEP goal data
        db: Database session
        
    Returns:
        Created IEP goal
    """
    try:
        goal = IEPGoal(**goal_data.model_dump())
        db.add(goal)
        await db.commit()
        await db.refresh(goal)

        logger.info("Created IEP goal %s for learner %s", goal.id, goal.learner_id)

        return IEPGoalResponse.model_validate(goal)

    except Exception as e:
        logger.error("Failed to create IEP goal: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create IEP goal: {str(e)}",
        )


@app.get("/learners/{learner_id}/iep-goals", response_model=List[IEPGoalResponse])
async def get_learner_iep_goals(
    learner_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get IEP goals for a learner.
    
    Args:
        learner_id: Learner ID
        db: Database session
        
    Returns:
        List of IEP goals
    """
    try:
        result = await db.execute(
            select(IEPGoal)
            .where(IEPGoal.learner_id == uuid.UUID(learner_id))
            .where(IEPGoal.is_active == True),
        )
        goals = result.scalars().all()

        return [IEPGoalResponse.model_validate(goal) for goal in goals]

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid learner ID format",
        )


@app.get("/uploads/{upload_id}/linkages", response_model=List[IEPGoalLinkageResponse])
async def get_upload_linkages(
    upload_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get IEP goal linkages for an upload.
    
    Args:
        upload_id: Upload ID
        db: Database session
        
    Returns:
        List of goal linkages
    """
    try:
        result = await db.execute(
            select(IEPGoalLinkage)
            .where(IEPGoalLinkage.upload_id == uuid.UUID(upload_id)),
        )
        linkages = result.scalars().all()

        return [IEPGoalLinkageResponse.model_validate(linkage) for linkage in linkages]

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload ID format",
        )


@app.post("/linkages/{linkage_id}/validate")
async def validate_linkage(
    linkage_id: str,
    is_valid: bool,
    validated_by: str,
    db: AsyncSession = Depends(get_db),
):
    """Validate an IEP goal linkage.
    
    Args:
        linkage_id: Linkage ID
        is_valid: Whether linkage is valid
        validated_by: ID of user validating
        db: Database session
        
    Returns:
        Validation result
    """
    try:
        result = await db.execute(
            select(IEPGoalLinkage)
            .where(IEPGoalLinkage.id == uuid.UUID(linkage_id)),
        )
        linkage = result.scalar_one_or_none()
        
        if not linkage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Linkage not found",
            )

        # Update linkage validation
        linkage.teacher_validated = is_valid
        linkage.validated_by = uuid.UUID(validated_by) if validated_by else None
        linkage.validation_timestamp = None  # Would be set automatically by database
        
        await db.commit()

        # Create audit entry for validation
        await audit_chain.create_audit_entry(
            db=db,
            upload_id=linkage.upload_id,
            learner_id=linkage.learner_id,
            action_type="VALIDATE",
            action_details={
                "linkage_id": str(linkage.id),
                "is_valid": is_valid,
                "confidence_score": linkage.confidence_score,
            },
            performed_by=uuid.UUID(validated_by),
        )

        logger.info(
            "Linkage %s validated as %s by %s",
            linkage_id,
            "valid" if is_valid else "invalid",
            validated_by,
        )

        return {
            "status": "success",
            "linkage_id": linkage_id,
            "is_valid": is_valid,
            "validated_by": validated_by,
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format",
        )


@app.get("/learners/{learner_id}/audit-trail")
async def get_audit_trail(
    learner_id: str,
    action_type: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get audit trail for a learner.
    
    Args:
        learner_id: Learner ID
        action_type: Optional action type filter
        limit: Maximum entries to return
        db: Database session
        
    Returns:
        Audit trail entries
    """
    try:
        entries = await audit_chain.get_audit_trail(
            db=db,
            learner_id=uuid.UUID(learner_id),
            action_type=action_type,
            limit=limit,
        )

        return {
            "learner_id": learner_id,
            "total_entries": len(entries),
            "entries": [
                {
                    "id": str(entry.id),
                    "upload_id": str(entry.upload_id),
                    "action_type": entry.action_type,
                    "action_details": entry.action_details,
                    "performed_by": str(entry.performed_by),
                    "timestamp": entry.timestamp.isoformat(),
                    "chain_hash": entry.chain_hash,
                    "has_signature": bool(entry.signature),
                }
                for entry in entries
            ],
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid learner ID format",
        )


@app.get("/learners/{learner_id}/audit-verification")
async def verify_audit_chain(
    learner_id: str,
    verify_signatures: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Verify audit chain integrity for a learner.
    
    Args:
        learner_id: Learner ID
        verify_signatures: Whether to verify signatures
        db: Database session
        
    Returns:
        Chain verification results
    """
    try:
        verification = await audit_chain.verify_chain_integrity(
            db=db,
            learner_id=uuid.UUID(learner_id),
            verify_signatures=verify_signatures,
        )

        return {
            "learner_id": learner_id,
            "verification": verification,
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid learner ID format",
        )


@app.get("/audit/statistics")
async def get_audit_statistics(
    learner_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get audit chain statistics.
    
    Args:
        learner_id: Optional learner filter
        db: Database session
        
    Returns:
        Audit statistics
    """
    try:
        learner_uuid = uuid.UUID(learner_id) if learner_id else None
        
        stats = await audit_chain.get_audit_statistics(
            db=db,
            learner_id=learner_uuid,
        )

        return stats

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid learner ID format",
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
