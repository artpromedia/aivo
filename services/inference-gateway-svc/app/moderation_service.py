"""
Content moderation service using OpenAI's moderation API.
"""
import logging
from typing import Dict, List, Tuple, Optional, Any

from openai import AsyncOpenAI

from .config import settings
from .enums import ModerationResult


logger = logging.getLogger(__name__)


class ModerationService:
    """Service for content moderation using OpenAI."""
    
    def __init__(self, openai_client: Optional[AsyncOpenAI] = None):
        """Initialize moderation service.
        
        Args:
            openai_client: Optional OpenAI client for dependency injection
        """
        self.client = openai_client or AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.default_threshold = settings.moderation_threshold
        self.default_model = settings.moderation_model
        logger.info("Moderation service initialized successfully")
    
    async def moderate_content(
        self,
        content: str,
        threshold: Optional[float] = None,
        model: Optional[str] = None
    ) -> Tuple[ModerationResult, Dict[str, float]]:
        """
        Moderate content using OpenAI's moderation API.
        
        Args:
            content: Text to moderate
            threshold: Moderation threshold (0.0-1.0)
            model: Moderation model to use
            
        Returns:
            Tuple of (moderation_result, category_scores)
        """
        try:
            threshold = threshold or self.default_threshold
            model = model or self.default_model
            
            # Call OpenAI moderation API
            response = await self.client.moderations.create(
                input=content,
                model=model
            )
            
            result = response.results[0]
            
            # Check if content is flagged and above threshold
            if result.flagged:
                max_score = max(result.category_scores.model_dump().values())
                if max_score >= threshold:
                    moderation_result = ModerationResult.BLOCKED
                else:
                    moderation_result = ModerationResult.PASSED
            else:
                moderation_result = ModerationResult.PASSED
                
            # Return moderation result and scores
            category_scores = result.category_scores.model_dump()
            
            logger.info(
                f"Content moderation completed: {moderation_result}, "
                f"max_score: {max(category_scores.values()):.3f}"
            )
            
            return moderation_result, category_scores
            
        except Exception as e:
            logger.error(f"Error during content moderation: {e}")
            return ModerationResult.ERROR, {}
    
    async def moderate_batch(
        self,
        contents: List[str],
        threshold: Optional[float] = None,
        model: Optional[str] = None
    ) -> List[Tuple[ModerationResult, Dict[str, float]]]:
        """
        Moderate multiple contents in batch.
        
        Args:
            contents: List of texts to moderate
            threshold: Moderation threshold
            model: Moderation model to use
            
        Returns:
            List of (moderation_result, category_scores) tuples
        """
        results = []
        for content in contents:
            result = await self.moderate_content(content, threshold, model)
            results.append(result)
        return results
    
    def get_moderation_summary(
        self,
        results: List[Tuple[ModerationResult, Dict[str, float]]]
    ) -> Dict[str, Any]:
        """
        Get summary of moderation results.
        
        Args:
            results: List of moderation results
            
        Returns:
            Summary statistics
        """
        total = len(results)
        blocked = sum(1 for r, _ in results if r == ModerationResult.BLOCKED)
        passed = sum(1 for r, _ in results if r == ModerationResult.PASSED)
        errors = sum(1 for r, _ in results if r == ModerationResult.ERROR)
        
        # Calculate average scores for each category
        all_scores = [scores for _, scores in results if scores]
        avg_scores = {}
        if all_scores:
            categories = all_scores[0].keys()
            for category in categories:
                avg_scores[category] = sum(
                    scores.get(category, 0) for scores in all_scores
                ) / len(all_scores)
        
        return {
            "total": total,
            "blocked": blocked,
            "passed": passed,
            "errors": errors,
            "block_rate": blocked / total if total > 0 else 0,
            "average_scores": avg_scores
        }


# Global moderation service instance
moderation_service = ModerationService()
