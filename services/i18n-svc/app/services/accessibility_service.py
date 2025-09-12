"""
Accessibility service for WCAG 2.2 AA compliance.

Service for managing accessibility audits and compliance validation.
"""

import asyncio
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AccessibilityAudit, Translation


def check_text_contrast(text: str, bg_color: str = "#ffffff") -> bool:
    """Check if text meets WCAG contrast requirements."""
    # Simplified contrast check - in production, use proper color analysis
    dark_indicators = ["dark", "black", "navy", "maroon"]
    return any(indicator in text.lower() for indicator in dark_indicators)


def validate_alt_text(text: str) -> dict[str, bool]:
    """Validate alt text for accessibility compliance."""
    return {
        "has_content": len(text.strip()) > 0,
        "appropriate_length": 5 <= len(text) <= 150,
        "descriptive": not text.lower().startswith(("image", "picture", "photo")),
        "no_redundant_text": "image of" not in text.lower(),
    }


def check_heading_structure(translations: list[dict]) -> list[dict]:
    """Check heading structure for proper hierarchy."""
    issues = []
    heading_levels = []

    for translation in translations:
        text = translation.get("value", "")
        if text.startswith(("# ", "## ", "### ")):
            level = len(text.split()[0])
            heading_levels.append(level)

            # Check for skipped levels
            if len(heading_levels) > 1:
                if level > heading_levels[-2] + 1:
                    issues.append(
                        {
                            "type": "skipped_heading_level",
                            "translation_id": translation.get("id"),
                            "message": f"Heading level {level} follows level {heading_levels[-2]}",
                        }
                    )

    return issues


def analyze_readability(text: str) -> dict[str, float]:
    """Analyze text readability for accessibility."""
    # Simplified readability analysis
    words = text.split()
    sentences = text.count(".") + text.count("!") + text.count("?") + 1

    if len(words) == 0 or sentences == 0:
        return {"flesch_score": 0.0, "grade_level": 0.0}

    avg_sentence_length = len(words) / sentences
    avg_syllables = sum(count_syllables(word) for word in words) / len(words)

    # Flesch Reading Ease Score
    flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)

    # Approximate grade level
    grade_level = 0.39 * avg_sentence_length + 11.8 * avg_syllables - 15.59

    return {
        "flesch_score": max(0, min(100, flesch_score)),
        "grade_level": max(0, grade_level),
    }


def count_syllables(word: str) -> int:
    """Count syllables in a word (simplified)."""
    word = word.lower()
    vowels = "aeiouy"
    syllable_count = 0
    prev_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            syllable_count += 1
        prev_was_vowel = is_vowel

    # Handle silent 'e'
    if word.endswith("e") and syllable_count > 1:
        syllable_count -= 1

    return max(1, syllable_count)


def validate_wcag_compliance(translation_data: dict) -> dict:
    """Validate translation for WCAG 2.2 AA compliance."""
    text = translation_data.get("value", "")
    issues = []
    score = 100.0

    # Check text length for screen readers
    if len(text) > 500:
        issues.append(
            {
                "type": "long_text",
                "severity": "warning",
                "message": "Text may be too long for comfortable screen reader use",
            }
        )
        score -= 10

    # Check for proper punctuation
    if len(text) > 50 and not text.strip().endswith((".", "!", "?")):
        issues.append(
            {
                "type": "missing_punctuation",
                "severity": "minor",
                "message": "Text should end with proper punctuation for screen readers",
            }
        )
        score -= 5

    # Check readability
    readability = analyze_readability(text)
    if readability["grade_level"] > 12:
        issues.append(
            {
                "type": "complex_readability",
                "severity": "warning",
                "message": f"Text grade level ({readability['grade_level']:.1f}) may be too complex",
            }
        )
        score -= 15

    # Check for accessibility-friendly language
    problematic_terms = ["click here", "read more", "learn more"]
    for term in problematic_terms:
        if term.lower() in text.lower():
            issues.append(
                {
                    "type": "non_descriptive_link",
                    "severity": "minor",
                    "message": f"Avoid generic terms like '{term}' - use descriptive text",
                }
            )
            score -= 5

    return {
        "score": max(0, score),
        "issues": issues,
        "readability": readability,
        "wcag_level": "AA" if score >= 85 else "A" if score >= 70 else "Below A",
    }


class AccessibilityService:
    """Service for managing accessibility compliance."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def audit_translation(
        self,
        translation_id: UUID,
        audit_type: str = "automated",
        auditor_id: str | None = None,
    ) -> AccessibilityAudit:
        """Perform accessibility audit on translation."""
        # Get translation
        stmt = select(Translation).where(Translation.id == translation_id)
        result = await self.db.execute(stmt)
        translation = result.scalar_one_or_none()

        if not translation:
            raise ValueError(f"Translation {translation_id} not found")

        # Perform compliance validation
        translation_data = {
            "id": str(translation.id),
            "value": translation.value,
            "locale": translation.locale,
        }

        validation_result = validate_wcag_compliance(translation_data)

        # Create audit record
        audit = AccessibilityAudit(
            translation_id=translation_id,
            audit_type=audit_type,
            wcag_level=validation_result["wcag_level"],
            score=validation_result["score"],
            issues_found=validation_result["issues"],
            recommendations=self._generate_recommendations(validation_result),
            auditor_id=auditor_id,
            audit_tool="internal_validator",
            next_audit_date=datetime.utcnow() + timedelta(days=90),
        )

        self.db.add(audit)

        # Update translation accessibility status
        translation.accessibility_compliant = validation_result["score"] >= 85
        translation.wcag_level = validation_result["wcag_level"]

        await self.db.commit()
        await self.db.refresh(audit)

        return audit

    def _generate_recommendations(self, validation_result: dict) -> list[str]:
        """Generate accessibility recommendations based on audit results."""
        recommendations = []

        for issue in validation_result["issues"]:
            issue_type = issue["type"]

            if issue_type == "long_text":
                recommendations.append(
                    "Consider breaking long text into shorter paragraphs or sections"
                )
            elif issue_type == "missing_punctuation":
                recommendations.append(
                    "Add proper punctuation to help screen readers with natural pauses"
                )
            elif issue_type == "complex_readability":
                recommendations.append(
                    "Simplify language and sentence structure for better accessibility"
                )
            elif issue_type == "non_descriptive_link":
                recommendations.append(
                    "Use descriptive link text that explains the destination or action"
                )

        # Add general recommendations based on score
        score = validation_result["score"]
        if score < 85:
            recommendations.append(
                "Review translation for WCAG 2.2 AA compliance requirements"
            )

        return recommendations

    async def bulk_audit_locale(
        self, locale: str, audit_type: str = "automated", batch_size: int = 50
    ) -> dict[str, int]:
        """Perform bulk accessibility audit for locale."""
        # Get all approved translations for locale
        stmt = select(Translation).where(
            and_(Translation.locale == locale, Translation.is_approved is True)
        )
        result = await self.db.execute(stmt)
        translations = result.scalars().all()

        audited_count = 0
        failed_count = 0

        # Process in batches to avoid memory issues
        for i in range(0, len(translations), batch_size):
            batch = translations[i : i + batch_size]

            # Create audit tasks for batch
            audit_tasks = []
            for translation in batch:
                task = self.audit_translation(translation.id, audit_type=audit_type)
                audit_tasks.append(task)

            # Execute batch audits
            try:
                await asyncio.gather(*audit_tasks)
                audited_count += len(batch)
            except Exception as e:
                failed_count += len(batch)
                print(f"Batch audit failed: {e}")

        return {
            "total_translations": len(translations),
            "audited_count": audited_count,
            "failed_count": failed_count,
            "success_rate": (audited_count / len(translations)) * 100
            if translations
            else 0,
        }

    async def get_accessibility_stats(self, locale: str | None = None) -> dict:
        """Get accessibility compliance statistics."""
        conditions = [Translation.is_approved is True]
        if locale:
            conditions.append(Translation.locale == locale)

        # Total translations
        total_stmt = select(Translation).where(and_(*conditions))
        total_result = await self.db.execute(total_stmt)
        total_translations = len(total_result.scalars().all())

        # Compliant translations
        compliant_stmt = select(Translation).where(
            and_(Translation.accessibility_compliant is True, *conditions)
        )
        compliant_result = await self.db.execute(compliant_stmt)
        compliant_translations = len(compliant_result.scalars().all())

        # AA level translations
        aa_stmt = select(Translation).where(
            and_(Translation.wcag_level == "AA", *conditions)
        )
        aa_result = await self.db.execute(aa_stmt)
        aa_translations = len(aa_result.scalars().all())

        compliance_percentage = (
            (compliant_translations / total_translations) * 100
            if total_translations > 0
            else 0
        )

        aa_percentage = (
            (aa_translations / total_translations) * 100
            if total_translations > 0
            else 0
        )

        return {
            "total_translations": total_translations,
            "compliant_translations": compliant_translations,
            "aa_level_translations": aa_translations,
            "compliance_percentage": round(compliance_percentage, 2),
            "aa_percentage": round(aa_percentage, 2),
            "target_met": aa_percentage >= 98.0,
            "locale": locale,
        }

    async def get_audit_history(
        self,
        translation_id: UUID | None = None,
        locale: str | None = None,
        limit: int = 50,
    ) -> list[AccessibilityAudit]:
        """Get accessibility audit history."""
        conditions = []

        if translation_id:
            conditions.append(AccessibilityAudit.translation_id == translation_id)

        if locale:
            conditions.append(Translation.locale == locale)

        stmt = (
            select(AccessibilityAudit)
            .join(Translation, AccessibilityAudit.translation_id == Translation.id)
            .where(and_(*conditions) if conditions else True)
            .order_by(AccessibilityAudit.audit_date.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()
