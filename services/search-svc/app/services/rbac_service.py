"""RBAC service for access control and filtering."""

import logging
from typing import Any, TYPE_CHECKING

from app.config import settings
from app.models import UserContext, UserRole

if TYPE_CHECKING:
    from app.models import SearchRequest, SuggestionRequest

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

    def _build_district_filter(self, user_context: UserContext) -> dict[str, Any]:
        """Build filter for district admin access."""
        if not user_context.district_id:
            return {"bool": {"must_not": {"match_all": {}}}}

        return {"term": {"district_id": user_context.district_id}}

    def _build_teacher_filter(self, user_context: UserContext) -> dict[str, Any]:
        """Build filter for teacher access."""
        should_clauses = []

        # Teacher can access their own content
        should_clauses.append({"term": {"teacher_id": user_context.user_id}})

        # Teacher can access content in their classes
        if user_context.class_ids:
            should_clauses.append({"terms": {"class_id": user_context.class_ids}})
            should_clauses.append({"terms": {"class_ids": user_context.class_ids}})

        # Teacher can access content in their school
        if user_context.school_id:
            should_clauses.append({"term": {"school_id": user_context.school_id}})

        # District level access if specified
        if user_context.district_id:
            should_clauses.append({"term": {"district_id": user_context.district_id}})

        return {"bool": {"should": should_clauses, "minimum_should_match": 1}}

    def _build_guardian_filter(self, user_context: UserContext) -> dict[str, Any]:
        """Build filter for guardian access."""
        should_clauses = []

        # Guardian can access content related to their learners
        if user_context.learner_ids:
            # Direct learner access
            should_clauses.append({"terms": {"id": user_context.learner_ids}})

            # Access to content where guardian is listed
            should_clauses.append({"terms": {"guardian_ids": [user_context.user_id]}})

            # Access to coursework/lessons for learner's classes
            # This would require additional context about learner's classes
            # For now, we'll use a more restrictive approach

        # If no learner IDs, guardian has very limited access
        if not should_clauses:
            return {"bool": {"must_not": {"match_all": {}}}}

        return {"bool": {"should": should_clauses, "minimum_should_match": 1}}

    def _build_learner_filter(self, user_context: UserContext) -> dict[str, Any]:
        """Build filter for learner access."""
        should_clauses = []

        # Learner can access their own profile (masked)
        should_clauses.append({"term": {"id": user_context.user_id}})

        # Learner can access content in their classes
        if user_context.class_ids:
            should_clauses.append({"terms": {"class_id": user_context.class_ids}})

        # Learner can access general lessons in their district/school
        if user_context.district_id:
            should_clauses.append(
                {
                    "bool": {
                        "must": [
                            {"term": {"type": "lesson"}},
                            {"term": {"district_id": user_context.district_id}},
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
                        matches_clause = self._document_matches_filter(document, clause)
                        if not matches_clause:
                            return False
                else:
                    matches_clause = self._document_matches_filter(document, must_clauses)
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

    async def get_user_accessible_indices(self, user_context: UserContext) -> list[str]:
        """Get list of indices the user can access."""
        accessible_indices = []

        # System admin can access all indices
        if user_context.role == UserRole.SYSTEM_ADMIN:
            return [
                settings.opensearch.lessons_index,
                settings.opensearch.coursework_index,
                settings.opensearch.learners_index,
                settings.opensearch.get("admin_users_index", "admin_users"),
                settings.opensearch.get("admin_devices_index", "admin_devices"),
                settings.opensearch.get("admin_subscriptions_index", "admin_subscriptions"),
                settings.opensearch.get("admin_invoices_index", "admin_invoices"),
                settings.opensearch.get("admin_reports_index", "admin_reports"),
                settings.opensearch.get("admin_audit_logs_index", "admin_audit_logs"),
            ]

        # District admin can access all content in their district
        if user_context.role == UserRole.DISTRICT_ADMIN:
            accessible_indices = [
                settings.opensearch.lessons_index,
                settings.opensearch.coursework_index,
                settings.opensearch.learners_index,
                settings.opensearch.get("admin_users_index", "admin_users"),
                settings.opensearch.get("admin_devices_index", "admin_devices"),
                settings.opensearch.get("admin_subscriptions_index", "admin_subscriptions"),
                settings.opensearch.get("admin_invoices_index", "admin_invoices"),
                settings.opensearch.get("admin_reports_index", "admin_reports"),
                settings.opensearch.get("admin_audit_logs_index", "admin_audit_logs"),
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

    async def build_admin_search_filter(
        self, user_context: UserContext, admin_entity_types: list[str] | None = None
    ) -> dict[str, Any]:
        """Build OpenSearch filter for admin_all scope searches."""
        # Only admin roles can use admin_all scope
        if user_context.role not in [UserRole.SYSTEM_ADMIN, UserRole.DISTRICT_ADMIN]:
            return {"bool": {"must_not": {"match_all": {}}}}

        filters = []

        # System admin has access to all admin data
        if user_context.role == UserRole.SYSTEM_ADMIN:
            base_filter = {"match_all": {}}
        else:
            # District admin filter - limit to their district
            if user_context.district_id:
                base_filter = {"term": {"district_id": user_context.district_id}}
            else:
                return {"bool": {"must_not": {"match_all": {}}}}

        filters.append(base_filter)

        # Filter by admin entity types if specified
        if admin_entity_types:
            entity_filter = {"terms": {"type": admin_entity_types}}
            filters.append(entity_filter)
        else:
            # Default to all admin entity types
            admin_types = ["user", "device", "subscription", "invoice", "report", "audit_log"]
            entity_filter = {"terms": {"type": admin_types}}
            filters.append(entity_filter)

        # Combine filters
        if len(filters) == 1:
            return filters[0]
        else:
            return {"bool": {"must": filters}}

    async def filter_search_request(
        self, request: "SearchRequest", user_context: UserContext
    ) -> "SearchRequest":
        """Filter search request based on user permissions and scope."""
        from app.models import SearchRequest, SearchScope

        # Handle admin_all scope
        if request.scope == SearchScope.ADMIN_ALL:
            # Check if user has admin privileges
            if user_context.role not in [UserRole.SYSTEM_ADMIN, UserRole.DISTRICT_ADMIN]:
                # Return empty results for non-admin users
                empty_request = SearchRequest(
                    q=request.q,
                    scope=request.scope,
                    size=0,
                    from_=request.from_,
                    filters={"bool": {"must_not": {"match_all": {}}}},
                )
                return empty_request

            # Build admin search filter
            admin_filter = await self.build_admin_search_filter(user_context)

            # Merge with existing filters
            combined_filters = request.filters.copy() if request.filters else {}
            if admin_filter:
                if "bool" in combined_filters:
                    if "must" in combined_filters["bool"]:
                        if isinstance(combined_filters["bool"]["must"], list):
                            combined_filters["bool"]["must"].append(admin_filter)
                        else:
                            combined_filters["bool"]["must"] = [combined_filters["bool"]["must"], admin_filter]
                    else:
                        combined_filters["bool"]["must"] = admin_filter
                else:
                    combined_filters = admin_filter

            return SearchRequest(
                q=request.q,
                scope=request.scope,
                size=request.size,
                from_=request.from_,
                filters=combined_filters,
            )

        # Handle other scopes with existing RBAC filter
        rbac_filter = await self.build_rbac_filter(user_context)

        # Merge with existing filters
        combined_filters = request.filters.copy() if request.filters else {}
        if rbac_filter:
            if "bool" in combined_filters:
                if "must" in combined_filters["bool"]:
                    if isinstance(combined_filters["bool"]["must"], list):
                        combined_filters["bool"]["must"].append(rbac_filter)
                    else:
                        combined_filters["bool"]["must"] = [combined_filters["bool"]["must"], rbac_filter]
                else:
                    combined_filters["bool"]["must"] = rbac_filter
            else:
                combined_filters = rbac_filter

        return SearchRequest(
            q=request.q,
            scope=request.scope,
            size=request.size,
            from_=request.from_,
            filters=combined_filters,
        )

    async def filter_suggestion_request(
        self, request: "SuggestionRequest", user_context: UserContext
    ) -> "SuggestionRequest":
        """Filter suggestion request based on user permissions."""
        # For now, suggestions don't need complex filtering
        # In production, you might want to apply similar RBAC filtering
        return request

    def get_role_level(self, role: UserRole) -> int:
        """Get numeric level for role hierarchy."""
        return self.role_hierarchy.get(role, 0)

    def can_role_access_role(self, accessor_role: UserRole, target_role: UserRole) -> bool:
        """Check if one role can access data from another role."""
        accessor_level = self.get_role_level(accessor_role)
        target_level = self.get_role_level(target_role)

        # Higher level roles can access lower level role data
        return accessor_level >= target_level
