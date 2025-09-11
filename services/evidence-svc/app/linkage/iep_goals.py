"""IEP Goal linkage system for connecting evidence to learning objectives."""
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EvidenceExtraction, IEPGoal, IEPGoalLinkage
from ..schemas import BulkLinkageRequest, IEPGoalLinkageCreate

logger = logging.getLogger(__name__)


class IEPGoalLinker:
    """Service for linking evidence extractions to IEP goals."""

    def __init__(self) -> None:
        """Initialize IEP goal linker."""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8,
        )
        self.min_linkage_strength = 0.3
        self.similarity_weights = {
            "keyword_overlap": 0.4,
            "text_similarity": 0.3,
            "subject_match": 0.2,
            "context_match": 0.1,
        }

    async def create_automatic_linkages(
        self,
        db: AsyncSession,
        extraction_id: uuid.UUID,
        learner_id: uuid.UUID,
        min_strength: float = 0.5,
    ) -> List[IEPGoalLinkage]:
        """Create automatic linkages for an evidence extraction.
        
        Args:
            db: Database session
            extraction_id: ID of evidence extraction
            learner_id: ID of learner
            min_strength: Minimum linkage strength threshold
            
        Returns:
            List of created linkages
        """
        # Get the extraction
        extraction_result = await db.execute(
            select(EvidenceExtraction).where(
                EvidenceExtraction.id == extraction_id,
            ),
        )
        extraction = extraction_result.scalar_one_or_none()
        
        if not extraction:
            logger.warning("Extraction %s not found", extraction_id)
            return []

        # Get active IEP goals for the learner
        goals_result = await db.execute(
            select(IEPGoal).where(
                and_(
                    IEPGoal.learner_id == learner_id,
                    IEPGoal.is_active == True,  # noqa: E712
                ),
            ),
        )
        iep_goals = goals_result.scalars().all()

        if not iep_goals:
            logger.info("No active IEP goals found for learner %s", learner_id)
            return []

        # Calculate linkage strengths
        linkage_data = await self._calculate_linkage_strengths(
            extraction,
            iep_goals,
        )

        # Create linkages above threshold
        created_linkages = []
        for goal_id, strength, matching_keywords, reason in linkage_data:
            if strength >= min_strength:
                linkage = IEPGoalLinkage(
                    extraction_id=extraction_id,
                    iep_goal_id=goal_id,
                    linkage_strength=strength,
                    matching_keywords=matching_keywords,
                    linkage_reason=reason,
                )
                db.add(linkage)
                created_linkages.append(linkage)

        await db.commit()

        logger.info(
            "Created %d automatic linkages for extraction %s (min_strength=%.2f)",
            len(created_linkages),
            extraction_id,
            min_strength,
        )

        return created_linkages

    async def process_bulk_linkages(
        self,
        db: AsyncSession,
        request: BulkLinkageRequest,
    ) -> Dict[str, Any]:
        """Process bulk linkage creation for a learner.
        
        Args:
            db: Database session
            request: Bulk linkage request
            
        Returns:
            Summary of linkage creation results
        """
        # Get unlinked extractions for learner
        query = (
            select(EvidenceExtraction)
            .join(EvidenceExtraction.upload)
            .where(
                and_(
                    EvidenceExtraction.upload.has(learner_id=request.learner_id),
                    ~EvidenceExtraction.linkages.any(),  # No existing linkages
                ),
            )
        )
        
        if request.subject_areas:
            query = query.where(
                EvidenceExtraction.subject_tags.op("&&")(request.subject_areas),
            )

        extractions_result = await db.execute(query)
        extractions = extractions_result.scalars().all()

        # Get IEP goals for learner
        goals_query = select(IEPGoal).where(
            and_(
                IEPGoal.learner_id == request.learner_id,
                IEPGoal.is_active == True,  # noqa: E712
            ),
        )
        
        if request.subject_areas:
            goals_query = goals_query.where(
                IEPGoal.subject_area.in_(request.subject_areas),
            )

        goals_result = await db.execute(goals_query)
        iep_goals = goals_result.scalars().all()

        # Process each extraction
        total_linkages = 0
        auto_validated = 0
        results_by_extraction = {}

        for extraction in extractions:
            linkage_data = await self._calculate_linkage_strengths(
                extraction,
                iep_goals,
            )

            extraction_linkages = 0
            for goal_id, strength, matching_keywords, reason in linkage_data:
                if strength >= request.min_linkage_strength:
                    validated = strength >= request.auto_validate_threshold
                    
                    linkage = IEPGoalLinkage(
                        extraction_id=extraction.id,
                        iep_goal_id=goal_id,
                        linkage_strength=strength,
                        matching_keywords=matching_keywords,
                        linkage_reason=reason,
                        validated_by_teacher=validated if validated else None,
                    )
                    db.add(linkage)
                    
                    extraction_linkages += 1
                    total_linkages += 1
                    
                    if validated:
                        auto_validated += 1

            results_by_extraction[str(extraction.id)] = {
                "linkages_created": extraction_linkages,
                "extraction_type": extraction.extraction_type,
                "subject_tags": extraction.subject_tags,
            }

        await db.commit()

        return {
            "learner_id": str(request.learner_id),
            "extractions_processed": len(extractions),
            "total_linkages_created": total_linkages,
            "auto_validated_linkages": auto_validated,
            "pending_validation": total_linkages - auto_validated,
            "min_strength_used": request.min_linkage_strength,
            "auto_validate_threshold": request.auto_validate_threshold,
            "results_by_extraction": results_by_extraction,
        }

    async def _calculate_linkage_strengths(
        self,
        extraction: EvidenceExtraction,
        iep_goals: List[IEPGoal],
    ) -> List[Tuple[uuid.UUID, float, List[str], str]]:
        """Calculate linkage strengths between extraction and IEP goals.
        
        Args:
            extraction: Evidence extraction
            iep_goals: List of IEP goals
            
        Returns:
            List of tuples (goal_id, strength, matching_keywords, reason)
        """
        if not iep_goals:
            return []

        linkage_results = []

        for goal in iep_goals:
            # Calculate different similarity metrics
            keyword_score = self._calculate_keyword_overlap(extraction, goal)
            text_score = await self._calculate_text_similarity(extraction, goal)
            subject_score = self._calculate_subject_match(extraction, goal)
            context_score = self._calculate_context_match(extraction, goal)

            # Weighted combination
            total_strength = (
                keyword_score * self.similarity_weights["keyword_overlap"]
                + text_score * self.similarity_weights["text_similarity"]
                + subject_score * self.similarity_weights["subject_match"]
                + context_score * self.similarity_weights["context_match"]
            )

            # Get matching keywords
            matching_keywords = self._get_matching_keywords(extraction, goal)

            # Generate reason
            reason = self._generate_linkage_reason(
                keyword_score,
                text_score,
                subject_score,
                context_score,
                matching_keywords,
            )

            if total_strength >= self.min_linkage_strength:
                linkage_results.append((
                    goal.id,
                    total_strength,
                    matching_keywords,
                    reason,
                ))

        # Sort by strength (descending)
        linkage_results.sort(key=lambda x: x[1], reverse=True)
        
        return linkage_results

    def _calculate_keyword_overlap(
        self,
        extraction: EvidenceExtraction,
        goal: IEPGoal,
    ) -> float:
        """Calculate keyword overlap score."""
        extraction_keywords = set(kw.lower() for kw in extraction.keywords)
        goal_keywords = set(kw.lower() for kw in goal.keywords)

        if not extraction_keywords or not goal_keywords:
            return 0.0

        # Calculate Jaccard similarity
        intersection = extraction_keywords.intersection(goal_keywords)
        union = extraction_keywords.union(goal_keywords)

        jaccard_score = len(intersection) / len(union) if union else 0.0

        # Also check partial matches
        partial_matches = 0
        for ext_kw in extraction_keywords:
            for goal_kw in goal_keywords:
                if (
                    ext_kw in goal_kw
                    or goal_kw in ext_kw
                    or self._are_similar_keywords(ext_kw, goal_kw)
                ):
                    partial_matches += 1
                    break

        partial_score = partial_matches / max(len(extraction_keywords), len(goal_keywords))

        # Combine scores
        return (jaccard_score * 0.7 + partial_score * 0.3)

    async def _calculate_text_similarity(
        self,
        extraction: EvidenceExtraction,
        goal: IEPGoal,
    ) -> float:
        """Calculate text similarity using TF-IDF."""
        extraction_text = extraction.extracted_text or ""
        goal_text = goal.goal_text

        if not extraction_text.strip() or not goal_text.strip():
            return 0.0

        try:
            # Create TF-IDF vectors
            documents = [extraction_text, goal_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)

        except Exception as e:
            logger.error("Text similarity calculation failed: %s", e)
            return 0.0

    def _calculate_subject_match(
        self,
        extraction: EvidenceExtraction,
        goal: IEPGoal,
    ) -> float:
        """Calculate subject area match score."""
        extraction_subjects = set(tag.lower() for tag in extraction.subject_tags)
        goal_subject = goal.subject_area.lower()

        if not extraction_subjects:
            return 0.0

        # Direct match
        if goal_subject in extraction_subjects:
            return 1.0

        # Partial match
        for subject in extraction_subjects:
            if (
                subject in goal_subject
                or goal_subject in subject
                or self._are_related_subjects(subject, goal_subject)
            ):
                return 0.7

        return 0.0

    def _calculate_context_match(
        self,
        extraction: EvidenceExtraction,
        goal: IEPGoal,
    ) -> float:
        """Calculate contextual match score."""
        score = 0.0

        # Check extraction metadata for additional context
        if extraction.extraction_metadata:
            metadata = extraction.extraction_metadata

            # Check confidence scores
            confidence = metadata.get("confidence_score", 0)
            if confidence > 0.8:
                score += 0.3

            # Check extraction method quality
            method = metadata.get("extraction_method", "")
            if method in ["analyze_document", "verbose_json"]:
                score += 0.2

            # Check if multiple extraction types agree
            if metadata.get("multi_method_agreement", False):
                score += 0.2

        # Check goal category alignment
        goal_category = goal.category.lower()
        if any(tag.lower() in goal_category for tag in extraction.subject_tags):
            score += 0.3

        return min(score, 1.0)

    def _get_matching_keywords(
        self,
        extraction: EvidenceExtraction,
        goal: IEPGoal,
    ) -> List[str]:
        """Get list of matching keywords between extraction and goal."""
        extraction_keywords = set(kw.lower() for kw in extraction.keywords)
        goal_keywords = set(kw.lower() for kw in goal.keywords)

        # Direct matches
        direct_matches = extraction_keywords.intersection(goal_keywords)
        
        # Partial matches
        partial_matches = set()
        for ext_kw in extraction_keywords:
            for goal_kw in goal_keywords:
                if (
                    ext_kw != goal_kw
                    and (ext_kw in goal_kw or goal_kw in ext_kw)
                ):
                    partial_matches.add(f"{ext_kw}~{goal_kw}")

        all_matches = list(direct_matches) + list(partial_matches)
        return sorted(all_matches)

    def _generate_linkage_reason(
        self,
        keyword_score: float,
        text_score: float,
        subject_score: float,
        context_score: float,
        matching_keywords: List[str],
    ) -> str:
        """Generate human-readable linkage reason."""
        reasons = []

        if keyword_score > 0.5:
            reasons.append(f"Strong keyword overlap ({keyword_score:.2f})")
        elif keyword_score > 0.2:
            reasons.append(f"Moderate keyword overlap ({keyword_score:.2f})")

        if text_score > 0.3:
            reasons.append(f"High text similarity ({text_score:.2f})")

        if subject_score > 0.5:
            reasons.append("Subject area match")

        if context_score > 0.3:
            reasons.append("Contextual alignment")

        if matching_keywords:
            key_matches = matching_keywords[:3]  # Show top 3
            reasons.append(f"Key terms: {', '.join(key_matches)}")

        if not reasons:
            reasons.append("Basic pattern matching")

        return "; ".join(reasons)

    def _are_similar_keywords(self, kw1: str, kw2: str) -> bool:
        """Check if two keywords are semantically similar."""
        # Simple similarity checks
        if len(kw1) < 4 or len(kw2) < 4:
            return False

        # Check for common stems or roots
        if kw1[:3] == kw2[:3]:  # Same first 3 characters
            return True

        # Check for common educational term patterns
        educational_patterns = [
            ("math", "mathematics"),
            ("reading", "literacy"),
            ("writing", "composition"),
            ("science", "scientific"),
            ("social", "history"),
            ("motor", "movement"),
            ("communication", "speech"),
            ("behavior", "conduct"),
        ]

        for pattern1, pattern2 in educational_patterns:
            if (pattern1 in kw1 and pattern2 in kw2) or (pattern2 in kw1 and pattern1 in kw2):
                return True

        return False

    def _are_related_subjects(self, subject1: str, subject2: str) -> bool:
        """Check if two subjects are related."""
        subject_relationships = {
            "mathematics": ["math", "arithmetic", "algebra", "geometry"],
            "language_arts": ["reading", "writing", "literacy", "english"],
            "science": ["biology", "chemistry", "physics", "scientific"],
            "social_studies": ["history", "geography", "civics", "social"],
            "motor_skills": ["physical", "movement", "coordination"],
            "communication": ["speech", "language", "social"],
            "behavior": ["social", "emotional", "conduct"],
        }

        for main_subject, related in subject_relationships.items():
            if (
                (main_subject in subject1 or subject1 in main_subject)
                and any(rel in subject2 for rel in related)
            ) or (
                (main_subject in subject2 or subject2 in main_subject)
                and any(rel in subject1 for rel in related)
            ):
                return True

        return False

    async def validate_linkage(
        self,
        db: AsyncSession,
        linkage_id: uuid.UUID,
        teacher_id: uuid.UUID,
        is_valid: bool,
        notes: Optional[str] = None,
    ) -> Optional[IEPGoalLinkage]:
        """Validate or reject a linkage by a teacher.
        
        Args:
            db: Database session
            linkage_id: ID of linkage to validate
            teacher_id: ID of validating teacher
            is_valid: Whether the linkage is valid
            notes: Optional teacher notes
            
        Returns:
            Updated linkage or None if not found
        """
        result = await db.execute(
            select(IEPGoalLinkage).where(IEPGoalLinkage.id == linkage_id),
        )
        linkage = result.scalar_one_or_none()

        if not linkage:
            return None

        linkage.validated_by_teacher = is_valid
        linkage.teacher_notes = notes

        await db.commit()

        logger.info(
            "Linkage %s %s by teacher %s",
            linkage_id,
            "validated" if is_valid else "rejected",
            teacher_id,
        )

        return linkage

    async def get_linkage_analytics(
        self,
        db: AsyncSession,
        learner_id: Optional[uuid.UUID] = None,
        subject_area: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get analytics about linkages.
        
        Args:
            db: Database session
            learner_id: Optional learner filter
            subject_area: Optional subject area filter
            
        Returns:
            Analytics dictionary
        """
        # Base query
        query = select(IEPGoalLinkage)
        
        if learner_id:
            query = query.join(IEPGoalLinkage.iep_goal).where(
                IEPGoal.learner_id == learner_id,
            )
        
        if subject_area:
            query = query.join(IEPGoalLinkage.iep_goal).where(
                IEPGoal.subject_area == subject_area,
            )

        result = await db.execute(query)
        linkages = result.scalars().all()

        # Calculate analytics
        total_linkages = len(linkages)
        if total_linkages == 0:
            return {
                "total_linkages": 0,
                "validated_linkages": 0,
                "pending_validation": 0,
                "average_strength": 0.0,
                "subject_distribution": {},
                "strength_distribution": {},
            }

        validated_count = sum(1 for l in linkages if l.validated_by_teacher is True)
        pending_count = sum(1 for l in linkages if l.validated_by_teacher is None)
        
        strengths = [l.linkage_strength for l in linkages]
        avg_strength = sum(strengths) / len(strengths)

        # Subject distribution
        subject_query = (
            select(IEPGoal.subject_area, func.count())
            .join(IEPGoalLinkage)
            .group_by(IEPGoal.subject_area)
        )
        
        if learner_id:
            subject_query = subject_query.where(IEPGoal.learner_id == learner_id)

        subject_result = await db.execute(subject_query)
        subject_distribution = dict(subject_result.fetchall())

        # Strength distribution
        strength_ranges = {
            "0.3-0.5": sum(1 for s in strengths if 0.3 <= s < 0.5),
            "0.5-0.7": sum(1 for s in strengths if 0.5 <= s < 0.7),
            "0.7-0.9": sum(1 for s in strengths if 0.7 <= s < 0.9),
            "0.9-1.0": sum(1 for s in strengths if s >= 0.9),
        }

        return {
            "total_linkages": total_linkages,
            "validated_linkages": validated_count,
            "pending_validation": pending_count,
            "average_strength": avg_strength,
            "subject_distribution": subject_distribution,
            "strength_distribution": strength_ranges,
        }
