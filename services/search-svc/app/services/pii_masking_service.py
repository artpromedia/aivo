"""PII masking service for protecting sensitive information."""

import hashlib
import logging
import re
from typing import Any

from app.config import settings
from app.models import UserContext, UserRole

logger = logging.getLogger(__name__)


class PIIMaskingService:
    """Service for masking Personally Identifiable Information."""

    def __init__(self) -> None:
        """Initialize PII masking service."""
        # Common PII patterns
        self.patterns = {
            "email": re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            "phone": re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?'
                r'([0-9]{3})[-.\s]?([0-9]{4})\b'
            ),
            "ssn": re.compile(
                r'\b(?!000|666|9\d{2})\d{3}[-.]?'
                r'(?!00)\d{2}[-.]?(?!0000)\d{4}\b'
            ),
            "credit_card": re.compile(
                r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|'
                r'3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'
            ),
            "student_id": re.compile(
                r'\b(?:student|learner|id)[-\s:]?([A-Z0-9]{6,12})\b',
                re.IGNORECASE
            ),
        }

        # Masking characters
        self.mask_char = settings.pii_masking.mask_character
        self.partial_mask_threshold = (
            settings.pii_masking.partial_mask_threshold
        )

    async def mask_document(
        self, document: dict[str, Any], user_context: UserContext
    ) -> dict[str, Any]:
        """Mask PII in a document based on user context."""
        if not settings.pii_masking.enabled:
            return document

        # Check if user has permission to see unmasked data
        if self._can_see_unmasked_data(user_context, document):
            return document

        # Create a copy to avoid modifying original
        masked_doc = document.copy()

        # Mask different fields based on document type
        doc_type = document.get("type", "")

        if doc_type == "learner":
            masked_doc = await self._mask_learner_document(
                masked_doc, user_context
            )
        elif doc_type in ["lesson", "coursework"]:
            masked_doc = await self._mask_content_document(
                masked_doc, user_context
            )
        else:
            # Generic masking for unknown types
            masked_doc = await self._mask_generic_document(
                masked_doc, user_context
            )

        return masked_doc

    async def mask_search_results(
        self, results: list[dict[str, Any]], user_context: UserContext
    ) -> list[dict[str, Any]]:
        """Mask PII in search results."""
        masked_results = []

        for result in results:
            masked_result = await self.mask_document(result, user_context)
            masked_results.append(masked_result)

        return masked_results

    async def _mask_learner_document(
        self, document: dict[str, Any], user_context: UserContext
    ) -> dict[str, Any]:
        """Mask PII in learner documents."""
        # Always mask the actual name with a consistent hash-based name
        if "title" in document:
            document["title"] = self._generate_masked_name(document["title"])

        if "masked_name" in document:
            document["masked_name"] = self._generate_masked_name(
                document["masked_name"]
            )

        # Mask content that might contain PII
        if "content" in document:
            document["content"] = await self._mask_text_content(
                document["content"], user_context
            )

        # Mask metadata
        if "metadata" in document:
            document["metadata"] = await self._mask_metadata(
                document["metadata"], user_context
            )

        return document

    async def _mask_content_document(
        self, document: dict[str, Any], user_context: UserContext
    ) -> dict[str, Any]:
        """Mask PII in lesson/coursework documents."""
        # Mask content that might reference learners
        if "content" in document:
            document["content"] = await self._mask_text_content(
                document["content"], user_context
            )

        # Mask title if it contains PII
        if "title" in document:
            document["title"] = await self._mask_text_content(
                document["title"], user_context
            )

        # Mask metadata
        if "metadata" in document:
            document["metadata"] = await self._mask_metadata(
                document["metadata"], user_context
            )

        return document

    async def _mask_generic_document(
        self, document: dict[str, Any], user_context: UserContext
    ) -> dict[str, Any]:
        """Generic PII masking for unknown document types."""
        # Mask common text fields
        for field in ["title", "content", "description"]:
            if field in document:
                document[field] = await self._mask_text_content(
                    document[field], user_context
                )

        # Mask metadata
        if "metadata" in document:
            document["metadata"] = await self._mask_metadata(
                document["metadata"], user_context
            )

        return document

    async def _mask_text_content(
        self, content: str, user_context: UserContext
    ) -> str:
        """Mask PII patterns in text content."""
        if not content or not isinstance(content, str):
            return content

        masked_content = content

        # Apply pattern-based masking
        for pattern_name, pattern in self.patterns.items():
            if pattern_name in settings.pii_masking.patterns_to_mask:
                masked_content = pattern.sub(
                    lambda m, pn=pattern_name: self._mask_match(m.group(), pn),
                    masked_content
                )

        # Mask names if enabled
        if settings.pii_masking.mask_names:
            masked_content = await self._mask_names_in_text(
                masked_content, user_context
            )

        return masked_content

    async def _mask_metadata(
        self, metadata: dict[str, Any], user_context: UserContext
    ) -> dict[str, Any]:
        """Mask PII in metadata fields."""
        masked_metadata = {}

        for key, value in metadata.items():
            if isinstance(value, str):
                # Check if this field should be masked
                if self._should_mask_field(key):
                    masked_metadata[key] = await self._mask_text_content(
                        value, user_context
                    )
                else:
                    masked_metadata[key] = value
            elif isinstance(value, dict):
                masked_metadata[key] = await self._mask_metadata(
                    value, user_context
                )
            elif isinstance(value, list):
                masked_list = []
                for item in value:
                    if isinstance(item, str) and self._should_mask_field(key):
                        masked_list.append(
                            await self._mask_text_content(item, user_context)
                        )
                    else:
                        masked_list.append(item)
                masked_metadata[key] = masked_list
            else:
                masked_metadata[key] = value

        return masked_metadata

    async def _mask_names_in_text(
        self,
        content: str,
        user_context: UserContext  # pylint: disable=unused-argument
    ) -> str:
        """Mask names in text content."""
        # Simple name pattern - this could be more sophisticated
        name_pattern = re.compile(
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'  # First Last name pattern
        )

        def mask_name(match: re.Match[str]) -> str:
            name = match.group()
            return self._generate_masked_name(name)

        return name_pattern.sub(mask_name, content)

    def _generate_masked_name(self, original_name: str) -> str:
        """Generate a consistent masked name based on hash."""
        if not original_name:
            return original_name

        # Create a hash of the name for consistency
        name_hash = hashlib.md5(
            (original_name + settings.pii_masking.salt).encode()
        ).hexdigest()[:8]

        # Generate a masked name based on length
        if len(original_name.split()) > 1:
            return f"Learner {name_hash}"
        else:
            return f"User{name_hash}"

    def _mask_match(self, match_text: str, pattern_name: str) -> str:
        """Mask a matched PII pattern."""
        if pattern_name == "email":
            # Mask email: show first char and domain
            if "@" in match_text:
                username, domain = match_text.split("@", 1)
                masked_username = (
                    username[0] + self.mask_char * (len(username) - 1)
                )
                return f"{masked_username}@{domain}"

        elif pattern_name == "phone":
            # Mask phone: show area code, mask middle digits
            digits = re.sub(r'[^\d]', '', match_text)
            if len(digits) >= 10:
                return f"({digits[:3]}) {self.mask_char * 3}-{digits[-4:]}"

        elif pattern_name == "ssn":
            # Mask SSN: show last 4 digits
            digits = re.sub(r'[^\d]', '', match_text)
            if len(digits) == 9:
                return (
                    f"{self.mask_char * 3}-{self.mask_char * 2}-{digits[-4:]}"
                )

        elif pattern_name == "credit_card":
            # Mask credit card: show last 4 digits
            digits = re.sub(r'[^\d]', '', match_text)
            return self.mask_char * (len(digits) - 4) + digits[-4:]

        # Default masking: partial mask
        if len(match_text) <= self.partial_mask_threshold:
            return self.mask_char * len(match_text)
        else:
            # Show first and last character, mask middle
            return (
                match_text[0] +
                self.mask_char * (len(match_text) - 2) +
                match_text[-1]
            )

    def _should_mask_field(self, field_name: str) -> bool:
        """Check if a field should be masked based on its name."""
        sensitive_fields = {
            "name", "full_name", "first_name", "last_name",
            "email", "phone", "address", "ssn", "student_id",
            "parent_name", "guardian_name", "emergency_contact"
        }

        return field_name.lower() in sensitive_fields

    def _can_see_unmasked_data(
        self, user_context: UserContext, document: dict[str, Any]
    ) -> bool:
        """Check if user can see unmasked data."""
        # System admins can see everything
        if user_context.role == UserRole.SYSTEM_ADMIN:
            return True

        # District admins can see unmasked data in their district
        if user_context.role == UserRole.DISTRICT_ADMIN:
            doc_district = document.get("district_id")
            return doc_district == user_context.district_id

        # Teachers can see unmasked data for their students/classes
        if user_context.role == UserRole.TEACHER:
            # Check if document is related to teacher's classes or students
            doc_teacher_id = document.get("teacher_id")
            doc_class_id = document.get("class_id")
            doc_class_ids = document.get("class_ids", [])

            if doc_teacher_id == user_context.user_id:
                return True
            if doc_class_id in user_context.class_ids:
                return True
            if any(
                class_id in user_context.class_ids
                for class_id in doc_class_ids
            ):
                return True

        # Guardians can see unmasked data for their learners
        if user_context.role == UserRole.GUARDIAN:
            doc_id = document.get("id")
            doc_guardian_ids = document.get("guardian_ids", [])

            # Can see their own learner's data
            if doc_id in user_context.learner_ids:
                return True
            # Can see data where they are listed as guardian
            if user_context.user_id in doc_guardian_ids:
                return True

        # Learners can see their own unmasked data
        if user_context.role == UserRole.LEARNER:
            doc_id = document.get("id")
            return doc_id == user_context.user_id

        return False

    async def get_masking_level(
        self, user_context: UserContext, document: dict[str, Any]
    ) -> str:
        """Get the level of masking to apply."""
        if self._can_see_unmasked_data(user_context, document):
            return "none"
        elif user_context.role in [UserRole.TEACHER, UserRole.GUARDIAN]:
            return "partial"
        else:
            return "full"
