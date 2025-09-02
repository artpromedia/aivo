"""
OpenAI integration service for text generation and embeddings.
"""
import logging
import time
import uuid
from typing import List, Dict, Any, Optional, Union

import openai
from openai import OpenAI

from .schemas import (
    GenerateRequest, GenerateResponse, GenerationChoice, Usage,
    EmbeddingRequest, EmbeddingResponse, EmbeddingData,
    ModerationRequest, ModerationResponse
)
from .enums import ModerationResult
from .config import settings
from .pii_service import pii_service
from .moderation_service import moderation_service

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API integration."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
    
    async def generate_text(self, request: GenerateRequest) -> GenerateResponse:
        """
        Generate text using OpenAI's completion API.
        
        Args:
            request: Generation request
            
        Returns:
            Generation response with moderation and PII handling
        """
        model = request.model or settings.default_model
        prompt = request.prompt
        
        # Process prompt for PII
        pii_detected = False
        pii_entities = []
        pii_scrubbed = False
        
        if not request.skip_pii_scrubbing:
            prompt, pii_entities, pii_scrubbed = await pii_service.process_text(prompt)
            pii_detected = len(pii_entities) > 0
            logger.info(f"PII processing: detected={pii_detected}, scrubbed={pii_scrubbed}")
        
        # Content moderation
        moderation_result = ModerationResult.PASSED
        moderation_scores = {}
        
        if not request.skip_moderation:
            moderation_result, moderation_scores = await moderation_service.moderate_content(prompt)
            
            if moderation_result == ModerationResult.BLOCKED:
                # Return blocked response
                return self._create_blocked_response(
                    model=model,
                    moderation_scores=moderation_scores,
                    pii_detected=pii_detected,
                    pii_entities=pii_entities,
                    pii_scrubbed=pii_scrubbed,
                    context=request.context
                )
        
        try:
            # Prepare OpenAI request parameters
            openai_params = {
                "model": model,
                "prompt": prompt,
                "max_tokens": min(request.max_tokens or 1000, settings.max_tokens_per_request),
                "temperature": request.temperature,
                "top_p": request.top_p,
                "frequency_penalty": request.frequency_penalty,
                "presence_penalty": request.presence_penalty,
            }
            
            if request.stop:
                openai_params["stop"] = request.stop
            
            # Call OpenAI API
            response = self.client.completions.create(**openai_params)
            
            # Convert to our response format
            choices = []
            for i, choice in enumerate(response.choices):
                # Process generated text for PII if needed
                generated_text = choice.text
                if not request.skip_pii_scrubbing and settings.pii_anonymization_enabled:
                    gen_text, gen_entities, gen_scrubbed = await pii_service.process_text(generated_text)
                    if gen_scrubbed:
                        generated_text = gen_text
                        pii_entities.extend(gen_entities)
                        pii_scrubbed = True
                
                choice_obj = GenerationChoice(
                    index=i,
                    text=generated_text,
                    finish_reason=choice.finish_reason,
                    logprobs=choice.logprobs.__dict__ if choice.logprobs else None
                )
                choices.append(choice_obj)
            
            # Create usage object
            usage = Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
            
            return GenerateResponse(
                id=response.id,
                object="text_completion",
                created=response.created,
                model=response.model,
                choices=choices,
                usage=usage,
                moderation_result=moderation_result,
                moderation_scores=moderation_scores,
                pii_detected=pii_detected,
                pii_entities=pii_entities,
                pii_scrubbed=pii_scrubbed,
                context=request.context
            )
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings using OpenAI's embeddings API.
        
        Args:
            request: Embedding request
            
        Returns:
            Embedding response with PII handling
        """
        model = request.model or settings.default_embedding_model
        
        # Handle single string or list of strings
        texts = [request.input] if isinstance(request.input, str) else request.input
        
        # Process texts for PII
        processed_texts = []
        all_pii_entities = []
        pii_detected = False
        pii_scrubbed = False
        
        if not request.skip_pii_scrubbing:
            for text in texts:
                proc_text, entities, scrubbed = await pii_service.process_text(text)
                processed_texts.append(proc_text)
                all_pii_entities.extend(entities)
                if scrubbed:
                    pii_scrubbed = True
                if entities:
                    pii_detected = True
        else:
            processed_texts = texts
        
        try:
            # Call OpenAI embeddings API
            response = self.client.embeddings.create(
                input=processed_texts,
                model=model
            )
            
            # Convert to our response format
            data = []
            for i, embedding in enumerate(response.data):
                data.append(EmbeddingData(
                    object="embedding",
                    index=i,
                    embedding=embedding.embedding
                ))
            
            usage = Usage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=None,
                total_tokens=response.usage.total_tokens
            )
            
            return EmbeddingResponse(
                object="list",
                data=data,
                model=response.model,
                usage=usage,
                pii_detected=pii_detected,
                pii_entities=all_pii_entities,
                pii_scrubbed=pii_scrubbed,
                context=request.context
            )
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def moderate_content(self, request: ModerationRequest) -> ModerationResponse:
        """
        Moderate content using OpenAI's moderation API.
        
        Args:
            request: Moderation request
            
        Returns:
            Moderation response
        """
        model = request.model or settings.moderation_model
        threshold = request.threshold or settings.moderation_threshold
        
        # Handle single string or list of strings
        texts = [request.input] if isinstance(request.input, str) else request.input
        
        try:
            # Call OpenAI moderation API
            response = self.client.moderations.create(
                input=texts,
                model=model
            )
            
            # Convert to our response format
            results = []
            for result in response.results:
                mod_result = ModerationResult(
                    flagged=result.flagged,
                    categories=result.categories.__dict__,
                    category_scores=result.category_scores.__dict__
                )
                results.append(mod_result)
            
            return ModerationResponse(
                id=response.id,
                model=response.model,
                results=results
            )
            
        except Exception as e:
            logger.error(f"Error moderating content: {e}")
            raise
    
    def _create_blocked_response(
        self,
        model: str,
        moderation_scores: Dict[str, float],
        pii_detected: bool,
        pii_entities: List,
        pii_scrubbed: bool,
        context: Optional[Any] = None
    ) -> GenerateResponse:
        """Create a blocked response for moderated content."""
        response_id = f"blocked-{uuid.uuid4().hex[:8]}"
        
        choice = GenerationChoice(
            index=0,
            text="[Content blocked due to policy violation]",
            finish_reason="content_filter",
            logprobs=None
        )
        
        usage = Usage(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0
        )
        
        return GenerateResponse(
            id=response_id,
            object="text_completion",
            created=int(time.time()),
            model=model,
            choices=[choice],
            usage=usage,
            moderation_result=ModerationResult.BLOCKED,
            moderation_scores=moderation_scores,
            pii_detected=pii_detected,
            pii_entities=pii_entities,
            pii_scrubbed=pii_scrubbed,
            context=context
        )


# Global OpenAI service instance
openai_service = OpenAIService()
