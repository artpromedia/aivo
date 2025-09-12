"""OpenSearch service for index management and search operations."""

import logging
from typing import Any

from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError, RequestError

from app.config import settings
from app.models import (
    BulkIndexRequest,
    IndexRequest,
    SearchRequest,
    SearchResponse,
    SuggestionRequest,
    SuggestionResponse,
)

logger = logging.getLogger(__name__)


class OpenSearchService:
    """Service for OpenSearch operations."""

    def __init__(self) -> None:
        """Initialize OpenSearch client."""
        self.client = OpenSearch(
            hosts=[
                {
                    "host": settings.opensearch.host,
                    "port": settings.opensearch.port,
                }
            ],
            http_auth=(
                settings.opensearch.username,
                settings.opensearch.password,
            ),
            use_ssl=settings.opensearch.use_ssl,
            verify_certs=settings.opensearch.verify_certs,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

    async def check_health(self) -> dict[str, Any]:
        """Check OpenSearch cluster health."""
        try:
            health = self.client.cluster.health()
            return {
                "status": health.get("status", "unknown"),
                "cluster_name": health.get("cluster_name"),
                "number_of_nodes": health.get("number_of_nodes"),
                "active_primary_shards": health.get("active_primary_shards"),
                "active_shards": health.get("active_shards"),
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("OpenSearch health check failed: %s", str(e))
            return {"status": "error", "error": str(e)}

    async def create_index(self, index_name: str, mapping: dict[str, Any] | None = None) -> bool:
        """Create an index with optional mapping."""
        try:
            body = {}
            if mapping:
                body["mappings"] = mapping

            # Add index settings
            body["settings"] = {
                "number_of_shards": settings.opensearch.default_shards,
                "number_of_replicas": settings.opensearch.default_replicas,
                "analysis": {
                    "analyzer": {
                        "content_analyzer": {
                            "type": "standard",
                            "stopwords": "_english_",
                        },
                        "suggestion_analyzer": {
                            "type": "simple",
                        },
                    }
                },
            }

            response = self.client.indices.create(index=index_name, body=body)
            logger.info("Created index: %s", index_name)
            return response.get("acknowledged", False)

        except RequestError as e:
            if e.error == "resource_already_exists_exception":
                logger.info("Index %s already exists", index_name)
                return True
            logger.error("Failed to create index %s: %s", index_name, str(e))
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to create index %s: %s", index_name, str(e))
            return False

    async def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        try:
            response = self.client.indices.delete(index=index_name)
            logger.info("Deleted index: %s", index_name)
            return response.get("acknowledged", False)
        except NotFoundError:
            logger.warning("Index %s not found for deletion", index_name)
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to delete index %s: %s", index_name, str(e))
            return False

    async def index_exists(self, index_name: str) -> bool:
        """Check if an index exists."""
        try:
            return self.client.indices.exists(index=index_name)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to check index existence %s: %s", index_name, str(e))
            return False

    async def index_document(self, request: IndexRequest) -> dict[str, Any]:
        """Index a single document."""
        try:
            doc_dict = request.document.model_dump()
            params = {}
            if request.refresh:
                params["refresh"] = "true"

            response = self.client.index(
                index=request.index,
                id=request.document.id,
                body=doc_dict,
                params=params,
            )
            logger.debug("Indexed document %s", request.document.id)
            return response
        except Exception as e:
            logger.error(
                "Failed to index document %s: %s",
                request.document.id,
                str(e),
            )
            raise

    async def bulk_index_documents(self, request: BulkIndexRequest) -> dict[str, Any]:
        """Bulk index multiple documents."""
        try:
            actions = []
            for doc in request.documents:
                action = {
                    "_index": request.index,
                    "_id": doc.id,
                    "_source": doc.model_dump(),
                }
                actions.append(action)

            params = {}
            if request.refresh:
                params["refresh"] = "true"

            response = self.client.bulk(body=actions, params=params)

            # Check for errors
            errors = []
            if response.get("errors"):
                for item in response.get("items", []):
                    if "error" in item.get("index", {}):
                        errors.append(item["index"]["error"])

            logger.info("Bulk indexed %d documents", len(request.documents))
            if errors:
                logger.warning("Bulk index errors: %s", errors)

            return {
                "indexed": len(request.documents),
                "errors": errors,
                "took": response.get("took", 0),
            }

        except Exception as e:
            logger.error("Failed to bulk index documents: %s", str(e))
            raise

    async def search_documents(
        self, request: SearchRequest, rbac_filter: dict[str, Any] | None = None
    ) -> SearchResponse:
        """Search documents with optional RBAC filtering."""
        try:
            # Build search query
            query = self._build_search_query(request.q, rbac_filter)

            # Build search body
            search_body = {
                "query": query,
                "size": request.size,
                "from": request.from_,
                "highlight": {
                    "fields": {
                        "title": {},
                        "content": {"fragment_size": 150},
                    }
                },
                "_source": [
                    "id",
                    "type",
                    "title",
                    "content",
                    "metadata",
                    "created_at",
                ],
            }

            # Add aggregations
            search_body["aggs"] = {
                "types": {"terms": {"field": "type.keyword"}},
                "subjects": {"terms": {"field": "metadata.subject.keyword"}},
            }

            # Execute search
            response = self.client.search(
                index=self._get_search_indices(request.scope),
                body=search_body,
            )

            # Convert to SearchResponse
            hits = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                highlights = hit.get("highlight", {})

                search_hit = {
                    "id": source.get("id", hit["_id"]),
                    "type": source.get("type", "unknown"),
                    "title": source.get("title", ""),
                    "content": self._truncate_content(source.get("content", "")),
                    "score": hit["_score"],
                    "metadata": source.get("metadata", {}),
                    "highlighted": highlights,
                }
                hits.append(search_hit)

            return SearchResponse(
                hits=hits,
                total=response["hits"]["total"]["value"],
                took=response["took"],
                aggregations=response.get("aggregations", {}),
            )

        except Exception as e:
            logger.error("Search failed: %s", str(e))
            raise

    async def get_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Get search suggestions."""
        try:
            suggest_body = {
                "size": 0,
                "suggest": {
                    "title_suggest": {
                        "prefix": request.q,
                        "completion": {
                            "field": "title.suggest",
                            "size": request.size,
                        },
                    },
                    "content_suggest": {
                        "prefix": request.q,
                        "completion": {
                            "field": "content.suggest",
                            "size": request.size,
                        },
                    },
                },
            }

            response = self.client.search(
                index=self._get_search_indices(request.scope),
                body=suggest_body,
            )

            suggestions = []

            # Process title suggestions
            for option in response["suggest"]["title_suggest"][0]["options"]:
                suggestions.append(
                    {
                        "text": option["text"],
                        "score": option["_score"],
                        "type": "title",
                    }
                )

            # Process content suggestions
            for option in response["suggest"]["content_suggest"][0]["options"]:
                suggestions.append(
                    {
                        "text": option["text"],
                        "score": option["_score"],
                        "type": "content",
                    }
                )

            # Sort by score and remove duplicates
            unique_suggestions = {}
            for sugg in suggestions:
                key = sugg["text"].lower()
                if (
                    key not in unique_suggestions
                    or unique_suggestions[key]["score"] < sugg["score"]
                ):
                    unique_suggestions[key] = sugg

            sorted_suggestions = sorted(
                unique_suggestions.values(),
                key=lambda x: x["score"],
                reverse=True,
            )[: request.size]

            return SuggestionResponse(
                suggestions=sorted_suggestions,
                took=response["took"],
            )

        except Exception as e:
            logger.error("Suggestions failed: %s", str(e))
            raise

    def _build_search_query(
        self, query: str, rbac_filter: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build OpenSearch query with RBAC filtering."""
        # Base multi-match query
        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content", "metadata.*"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]

        # Add RBAC filter if provided
        if rbac_filter:
            must_clauses.append(rbac_filter)

        return {
            "bool": {
                "must": must_clauses,
            }
        }

    def _get_search_indices(self, scope: str) -> str:
        """Get indices to search based on scope."""
        index_map = {
            "lessons": settings.opensearch.lessons_index,
            "coursework": settings.opensearch.coursework_index,
            "learners": settings.opensearch.learners_index,
            "all": f"{settings.opensearch.lessons_index},"
            f"{settings.opensearch.coursework_index},"
            f"{settings.opensearch.learners_index}",
        }
        return index_map.get(scope, index_map["all"])

    def _truncate_content(self, content: str, max_length: int = 200) -> str:
        """Truncate content for display."""
        if len(content) <= max_length:
            return content
        return content[:max_length].rsplit(" ", 1)[0] + "..."

    async def setup_indices(self) -> dict[str, bool]:
        """Set up all required indices with proper mappings."""
        results = {}

        # Lessons index
        lessons_mapping = self._get_lessons_mapping()
        results["lessons"] = await self.create_index(
            settings.opensearch.lessons_index, lessons_mapping
        )

        # Coursework index
        coursework_mapping = self._get_coursework_mapping()
        results["coursework"] = await self.create_index(
            settings.opensearch.coursework_index, coursework_mapping
        )

        # Learners index
        learners_mapping = self._get_learners_mapping()
        results["learners"] = await self.create_index(
            settings.opensearch.learners_index, learners_mapping
        )

        return results

    def _get_lessons_mapping(self) -> dict[str, Any]:
        """Get mapping for lessons index."""
        return {
            "properties": {
                "id": {"type": "keyword"},
                "type": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "content_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {"type": "completion"},
                    },
                },
                "content": {
                    "type": "text",
                    "analyzer": "content_analyzer",
                    "fields": {"suggest": {"type": "completion"}},
                },
                "subject": {"type": "keyword"},
                "grade_level": {"type": "integer"},
                "district_id": {"type": "keyword"},
                "school_id": {"type": "keyword"},
                "teacher_id": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "difficulty_level": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "metadata": {"type": "object"},
            }
        }

    def _get_coursework_mapping(self) -> dict[str, Any]:
        """Get mapping for coursework index."""
        return {
            "properties": {
                "id": {"type": "keyword"},
                "type": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "content_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {"type": "completion"},
                    },
                },
                "content": {
                    "type": "text",
                    "analyzer": "content_analyzer",
                    "fields": {"suggest": {"type": "completion"}},
                },
                "assignment_type": {"type": "keyword"},
                "subject": {"type": "keyword"},
                "grade_level": {"type": "integer"},
                "district_id": {"type": "keyword"},
                "school_id": {"type": "keyword"},
                "class_id": {"type": "keyword"},
                "teacher_id": {"type": "keyword"},
                "due_date": {"type": "date"},
                "points_possible": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "metadata": {"type": "object"},
            }
        }

    def _get_learners_mapping(self) -> dict[str, Any]:
        """Get mapping for learners index."""
        return {
            "properties": {
                "id": {"type": "keyword"},
                "type": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "content_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {"type": "completion"},
                    },
                },
                "content": {
                    "type": "text",
                    "analyzer": "content_analyzer",
                    "fields": {"suggest": {"type": "completion"}},
                },
                "masked_name": {"type": "text"},
                "grade_level": {"type": "integer"},
                "district_id": {"type": "keyword"},
                "school_id": {"type": "keyword"},
                "class_ids": {"type": "keyword"},
                "teacher_ids": {"type": "keyword"},
                "guardian_ids": {"type": "keyword"},
                "performance_level": {"type": "keyword"},
                "interests": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "metadata": {"type": "object"},
            }
        }
