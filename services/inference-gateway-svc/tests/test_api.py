"""
Tests for FastAPI endpoints and integration.
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient


class TestHealthAPI:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client: AsyncClient, mock_openai_client):
        """Test successful health check."""
        with patch('app.main.openai_service.client', mock_openai_client):
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["healthy", "degraded"]
            assert data["service"] == "inference-gateway"
            assert data["version"] == "1.0.0"
            assert "dependencies" in data


class TestGenerationAPI:
    """Test text generation endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_text_success(
        self, 
        client: AsyncClient, 
        sample_generate_request: dict,
        mock_openai_client
    ):
        """Test successful text generation."""
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/generate", json=sample_generate_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["object"] == "text_completion"
            assert len(data["choices"]) == 1
            assert data["moderation_result"] == "passed"
            assert data["context"]["subject"] == "Science"
            assert data["context"]["grade_level"] == "5th"
    
    @pytest.mark.asyncio
    async def test_generate_text_with_pii(
        self, 
        client: AsyncClient,
        mock_openai_client
    ):
        """Test text generation with PII in prompt."""
        request_data = {
            "prompt": "My email is john.doe@example.com. Explain gravity.",
            "max_tokens": 50
        }
        
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/generate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["pii_detected"] == True
            assert data["pii_scrubbed"] == True
            assert len(data["pii_entities"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_text_blocked_content(
        self, 
        client: AsyncClient,
        mock_flagged_moderation
    ):
        """Test text generation with blocked content."""
        request_data = {
            "prompt": "Generate harmful content with hate speech",
            "max_tokens": 50
        }
        
        with patch('app.moderation_service.OpenAI', return_value=mock_flagged_moderation):
            with patch('app.openai_service.OpenAI'):
                response = await client.post("/v1/generate", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["moderation_result"] == "blocked"
                assert "[Content blocked due to policy violation]" in data["choices"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_generate_text_validation_error(self, client: AsyncClient):
        """Test validation error for invalid request."""
        invalid_request = {
            "prompt": "",  # Empty prompt
            "temperature": 3.0,  # Invalid temperature
        }
        
        response = await client.post("/v1/generate", json=invalid_request)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generate_text_with_educational_context(
        self, 
        client: AsyncClient,
        mock_openai_client
    ):
        """Test text generation with full educational context envelope."""
        request_data = {
            "prompt": "Explain the water cycle",
            "context": {
                "subject": "Earth Science",
                "grade_level": "6th",
                "learning_objective": "Understand water cycle processes",
                "content_type": "explanation"
            }
        }
        
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/generate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            context = data["context"]
            assert context["subject"] == "Earth Science"
            assert context["grade_level"] == "6th"
            assert context["learning_objective"] == "Understand water cycle processes"
            assert context["content_type"] == "explanation"


class TestEmbeddingAPI:
    """Test embedding generation endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_success(
        self, 
        client: AsyncClient,
        sample_embedding_request: dict,
        mock_openai_client
    ):
        """Test successful embedding generation."""
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/embeddings", json=sample_embedding_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["object"] == "list"
            assert len(data["data"]) == 1
            assert len(data["data"][0]["embedding"]) == 5
            assert data["context"]["subject"] == "Science"
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(
        self, 
        client: AsyncClient,
        mock_openai_client
    ):
        """Test batch embedding generation."""
        request_data = {
            "input": ["Text 1", "Text 2", "Text 3"],
            "model": "text-embedding-ada-002"
        }
        
        # Mock multiple embeddings
        mock_openai_client.embeddings.create.return_value.data = [
            type('MockEmbedding', (), {'embedding': [0.1, 0.2]})(),
            type('MockEmbedding', (), {'embedding': [0.3, 0.4]})(),
            type('MockEmbedding', (), {'embedding': [0.5, 0.6]})()
        ]
        
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/embeddings", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 3
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_with_pii(
        self, 
        client: AsyncClient,
        mock_openai_client
    ):
        """Test embedding generation with PII scrubbing."""
        request_data = {
            "input": "Contact teacher at teacher@school.edu for help"
        }
        
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/embeddings", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["pii_detected"] == True
            assert data["pii_scrubbed"] == True


class TestModerationAPI:
    """Test content moderation endpoints."""
    
    @pytest.mark.asyncio
    async def test_moderate_content_safe(
        self, 
        client: AsyncClient,
        sample_moderation_request: dict,
        mock_openai_client
    ):
        """Test moderation of safe content."""
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/moderate", json=sample_moderation_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["results"]) == 1
            assert data["results"][0]["flagged"] == False
    
    @pytest.mark.asyncio
    async def test_moderate_content_harmful(
        self, 
        client: AsyncClient,
        mock_flagged_moderation
    ):
        """Test moderation of harmful content."""
        request_data = {
            "input": "This contains hate speech and violence",
            "threshold": 0.8
        }
        
        with patch('app.openai_service.OpenAI', return_value=mock_flagged_moderation):
            response = await client.post("/v1/moderate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["results"][0]["flagged"] == True
            assert data["results"][0]["category_scores"]["hate"] > 0.8
    
    @pytest.mark.asyncio
    async def test_moderate_content_batch(
        self, 
        client: AsyncClient,
        mock_openai_client
    ):
        """Test batch content moderation."""
        request_data = {
            "input": [
                "Safe content 1",
                "Safe content 2",
                "Safe content 3"
            ]
        }
        
        # Mock multiple results
        mock_result = type('MockResult', (), {
            'flagged': False,
            'categories': type('MockCategories', (), {'__dict__': {"hate": False}})(),
            'category_scores': type('MockScores', (), {'__dict__': {"hate": 0.1}})()
        })()
        
        mock_openai_client.moderations.create.return_value.results = [mock_result] * 3
        
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/moderate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 3


class TestIntegrationWorkflows:
    """Test complete integration workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_generation_workflow(
        self, 
        client: AsyncClient,
        mock_openai_client
    ):
        """Test complete generation workflow with all features."""
        request_data = {
            "prompt": "Create a lesson plan about photosynthesis for 5th graders. Email questions to teacher@school.edu",
            "max_tokens": 200,
            "temperature": 0.7,
            "context": {
                "subject": "Science",
                "grade_level": "5th",
                "learning_objective": "Understand photosynthesis basics",
                "content_type": "lesson_plan"
            },
            "skip_moderation": False,
            "skip_pii_scrubbing": False
        }
        
        with patch('app.openai_service.OpenAI', return_value=mock_openai_client):
            response = await client.post("/v1/generate", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify all features are working
            assert data["moderation_result"] == "passed"
            assert data["pii_detected"] == True  # Email detected
            assert data["pii_scrubbed"] == True  # Email scrubbed
            assert data["context"]["subject"] == "Science"
            assert len(data["choices"]) == 1
    
    @pytest.mark.asyncio
    async def test_policy_enforcement_workflow(
        self, 
        client: AsyncClient,
        mock_flagged_moderation
    ):
        """Test policy enforcement blocks harmful content."""
        request_data = {
            "prompt": "Generate content that promotes violence and hate",
            "context": {
                "subject": "Ethics",
                "grade_level": "High School"
            }
        }
        
        with patch('app.moderation_service.OpenAI', return_value=mock_flagged_moderation):
            with patch('app.openai_service.OpenAI'):
                response = await client.post("/v1/generate", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                
                # Content should be blocked
                assert data["moderation_result"] == "blocked"
                assert "blocked due to policy violation" in data["choices"][0]["text"].lower()
                assert data["context"]["subject"] == "Ethics"  # Context preserved
