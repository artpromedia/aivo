"""RBAC service for access control and filtering."""

import logging
from typing import Any

from app.config import settings
from app.models import UserContext, UserRole

logger = logging.getLogger(__name__)


class RBACService:
    """Service for Role-Based Access Control filtering."""

    def __init__(self) -> None:
        """Initialize RBAC service."""
        self.role_hierarchy = {
            UserRole.SYSTEM_ADMIN: 5,
            UserRole.DISTRICT_ADMIN: 4,
            UserRole.TEACHER: 3,
            UserRole.GUARDIAN: 2,
            UserRole.LEARNER: 1,
        }

    async def build_rbac_filter(
        self, user_context: UserContext, document_type: str | None = None
    ) -> dict[str, Any]:
        """Build OpenSearch filter based on user context and role."""
        filters = []

        # System admin has access to everything
        if user_context.role == UserRole.SYSTEM_ADMIN:
            return {"match_all": {}}

        # District admin filter
        if user_context.role == UserRole.DISTRICT_ADMIN:
            filters.append(self._build_district_filter(user_context))

        # Teacher filter
        elif user_context.role == UserRole.TEACHER:
            filters.append(self._build_teacher_filter(user_context))

        # Guardian filter
        elif user_context.role == UserRole.GUARDIAN:
            filters.append(self._build_guardian_filter(user_context))

        # Learner filter
        elif user_context.role == UserRole.LEARNER:
            filters.append(self._build_learner_filter(user_context))

        # Add document type filter if specified
        if document_type:
            filters.append({"term": {"type": document_type}})

        # Combine filters
        if len(filters) == 1:
            return filters[0]
        elif len(filters) > 1:
            return {"bool": {"must": filters}}
        else:
            # No specific filters, deny all
            return {"bool": {"must_not": {"match_all": {}}}}

    def _build_district_filter(
        self,
        user_context: UserContext
    ) -> dict[str, Any]:
        """Build filter for district admin access."""
        if not user_context.district_id:
            return {"bool": {"must_not": {"match_all": {}}}}

        return {"term": {"district_id": user_context.district_id}}

    def _build_teacher_filter(
        self,
        user_context: UserContext
    ) -> dict[str, Any]:
        """Build filter for teacher access."""
        should_clauses = []

        # Teacher can access their own content
        should_clauses.append(
            {"term": {"teacher_id": user_context.user_id}}
        )

        # Teacher can access content in their classes
        if user_context.class_ids:
            should_clauses.append(
                {"terms": {"class_id": user_context.class_ids}}
            )
            should_clauses.append(
                {"terms": {"class_ids": user_context.class_ids}}
            )

        # Teacher can access content in their school
        if user_context.school_id:
            should_clauses.append(
                {"term": {"school_id": user_context.school_id}}
            )

        # District level access if specified
        if user_context.district_id:
            should_clauses.append(
                {"term": {"district_id": user_context.district_id}}
            )

        return {"bool": {"should": should_clauses, "minimum_should_match": 1}}

    def _build_guardian_filter(
        self, user_context: UserContext
    ) -> dict[str, Any]:
        """Build filter for guardian access."""
        should_clauses = []

        # Guardian can access content related to their learners
        if user_context.learner_ids:
            # Direct learner access
            should_clauses.append({"terms": {"id": user_context.learner_ids}})

            # Access to content where guardian is listed
            should_clauses.append(
                {"terms": {"guardian_ids": [user_context.user_id]}}
            )

            # Access to coursework/lessons for learner's classes
            # This would require additional context about learner's classes
            # For now, we'll use a more restrictive approach

        # If no learner IDs, guardian has very limited access
        if not should_clauses:
            return {"bool": {"must_not": {"match_all": {}}}}

        return {"bool": {"should": should_clauses, "minimum_should_match": 1}}

    def _build_learner_filter(
        self, user_context: UserContext
    ) -> dict[str, Any]:
        """Build filter for learner access."""
        should_clauses = []

        # Learner can access their own profile (masked)
        should_clauses.append({"term": {"id": user_context.user_id}})

        # Learner can access content in their classes
        if user_context.class_ids:
            should_clauses.append(
                {"terms": {"class_id": user_context.class_ids}}
            )

        # Learner can access general lessons in their district/school
        if user_context.district_id:
            should_clauses.append(
                {
                    "bool": {
                        "must": [
                            {"term": {"type": "lesson"}},
                            {
                                "term": {
                                    "district_id": user_context.district_id
                                }
                            },
                        ]
                    }
                }
            )

        if not should_clauses:
            return {"bool": {"must_not": {"match_all": {}}}}

        return {"bool": {"should": should_clauses, "minimum_should_match": 1}}

    async def can_access_document(
        self, user_context: UserContext, document: dict[str, Any]
    ) -> bool:
        """Check if user can access a specific document."""
        # Build filter and check if document would match
        rbac_filter = await self.build_rbac_filter(user_context)

        # Simple implementation - in production this would be more
        # sophisticated
        return self._document_matches_filter(document, rbac_filter)

    def _document_matches_filter(
        self, document: dict[str, Any], filter_dict: dict[str, Any]
    ) -> bool:
        """Check if a document matches the RBAC filter."""
        # Simplified filter matching - in production this would be more
        # complete

        if "match_all" in filter_dict:
            return True

        if "bool" in filter_dict:
            bool_query = filter_dict["bool"]

            # Handle must_not
            if "must_not" in bool_query:
                must_not_clause = bool_query["must_not"]
                if self._document_matches_filter(document, must_not_clause):
                    return False

            # Handle must
            if "must" in bool_query:
                must_clauses = bool_query["must"]
                if isinstance(must_clauses, list):
                    for clause in must_clauses:
                        matches_clause = self._document_matches_filter(
                            document, clause
                        )
                        if not matches_clause:
                            return False
                else:
                    matches_clause = self._document_matches_filter(
                        document, must_clauses
                    )
                    if not matches_clause:
                        return False

            # Handle should
            if "should" in bool_query:
                should_clauses = bool_query["should"]
                min_should_match = bool_query.get("minimum_should_match", 1)
                matches = 0

                for clause in should_clauses:
                    if self._document_matches_filter(document, clause):
                        matches += 1

                return matches >= min_should_match

        # Handle term queries
        if "term" in filter_dict:
            for field, value in filter_dict["term"].items():
                if document.get(field) != value:
                    return False

        # Handle terms queries
        if "terms" in filter_dict:
            for field, values in filter_dict["terms"].items():
                doc_value = document.get(field)
                if doc_value not in values:
                    return False

        return True

    async def filter_search_results(
        self, user_context: UserContext, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Additional filtering of search results if needed."""
        filtered_results = []

        for result in results:
            if await self.can_access_document(user_context, result):
                filtered_results.append(result)

        return filtered_results

    async def get_user_accessible_indices(
        self, user_context: UserContext
    ) -> list[str]:
        """Get list of indices the user can access."""
        accessible_indices = []

        # System admin can access all indices
        if user_context.role == UserRole.SYSTEM_ADMIN:
            return [
                settings.opensearch.lessons_index,
                settings.opensearch.coursework_index,
                settings.opensearch.learners_index,
            ]

        # District admin can access all content in their district
        if user_context.role == UserRole.DISTRICT_ADMIN:
            accessible_indices = [
                settings.opensearch.lessons_index,
                settings.opensearch.coursework_index,
                settings.opensearch.learners_index,
            ]

        # Teacher can access lessons and coursework
        elif user_context.role == UserRole.TEACHER:
            accessible_indices = [
                settings.opensearch.lessons_index,
                settings.opensearch.coursework_index,
            ]
            # Teachers can also access learner data for their students
            if user_context.learner_ids:
                accessible_indices.append(settings.opensearch.learners_index)

        # Guardian can access limited content
        elif user_context.role == UserRole.GUARDIAN:
            if user_context.learner_ids:
                accessible_indices = [
                    settings.opensearch.lessons_index,
                    settings.opensearch.coursework_index,
                    settings.opensearch.learners_index,
                ]

        # Learner can access public lessons and their own data
        elif user_context.role == UserRole.LEARNER:
            accessible_indices = [
                settings.opensearch.lessons_index,
                settings.opensearch.learners_index,
            ]

        return accessible_indices

    def get_role_level(self, role: UserRole) -> int:
        """Get numeric level for role hierarchy."""
        return self.role_hierarchy.get(role, 0)

    def can_role_access_role(
        self, accessor_role: UserRole, target_role: UserRole
    ) -> bool:
        """Check if one role can access data from another role."""
        accessor_level = self.get_role_level(accessor_role)
        target_level = self.get_role_level(target_role)

        # Higher level roles can access lower level role data
        return accessor_level >= target_level
