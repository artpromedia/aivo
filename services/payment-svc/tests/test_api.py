"""
API endpoint tests for payment service.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock


class TestPricingAPI:
    """Test pricing API endpoints."""
    
    @pytest.mark.asyncio
    async def test_calculate_pricing_monthly(self, client, sample_pricing_request):
        """Test pricing calculation for monthly plan."""
        request_data = {
            "plan_type": "monthly",
            "seats": 5,
            "has_sibling_discount": False
        }
        
        response = await client.post("/pricing/calculate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plan_type"] == "monthly"
        assert data["seats"] == 5
        assert data["base_amount"] == "200.00"  # 5 seats * $40
        assert data["final_amount"] == "200.00"  # No discounts
        assert data["plan_discount_percentage"] == "0"
        assert data["sibling_discount_percentage"] == "0"
    
    @pytest.mark.asyncio
    async def test_calculate_pricing_yearly_with_sibling_discount(self, client):
        """Test pricing calculation for yearly plan with sibling discount."""
        request_data = {
            "plan_type": "yearly",
            "seats": 10,
            "has_sibling_discount": True
        }
        
        response = await client.post("/pricing/calculate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["plan_type"] == "yearly"
        assert data["seats"] == 10
        assert float(data["plan_discount_percentage"]) == 50.0  # 50% off for yearly
        assert float(data["sibling_discount_percentage"]) == 10.0  # 10% sibling discount
        assert float(data["final_amount"]) < float(data["base_amount"])
    
    @pytest.mark.asyncio
    async def test_calculate_pricing_invalid_seats(self, client):
        """Test pricing calculation with invalid seat count."""
        request_data = {
            "plan_type": "monthly",
            "seats": 0,  # Invalid
            "has_sibling_discount": False
        }
        
        response = await client.post("/pricing/calculate", json=request_data)
        
        assert response.status_code == 422  # Validation error


class TestTrialAPI:
    """Test trial API endpoints."""
    
    @pytest.mark.asyncio
    async def test_start_trial_tenant(self, client, sample_trial_request):
        """Test starting a trial for a tenant."""
        response = await client.post("/trials/start", json=sample_trial_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tenant_id"] == 1
        assert data["seats"] == 3
        assert data["plan_type"] == "monthly"
        assert data["status"] == "trial"
        assert data["trial_start"] is not None
        assert data["trial_end"] is not None
    
    @pytest.mark.asyncio
    async def test_start_trial_guardian(self, client):
        """Test starting a trial for a guardian."""
        request_data = {
            "guardian_id": "guardian123",
            "seats": 5
        }
        
        response = await client.post("/trials/start", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["guardian_id"] == "guardian123"
        assert data["tenant_id"] is None
        assert data["seats"] == 5
        assert data["status"] == "trial"
    
    @pytest.mark.asyncio
    async def test_start_trial_missing_identifier(self, client):
        """Test starting a trial without tenant_id or guardian_id."""
        request_data = {
            "seats": 5
        }
        
        response = await client.post("/trials/start", json=request_data)
        
        assert response.status_code == 422  # Validation error


class TestCheckoutAPI:
    """Test checkout API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_checkout_session(self, client, sample_checkout_request):
        """Test creating a checkout session."""
        with patch('app.main.subscription_service') as mock_service:
            mock_service.create_checkout_session = AsyncMock(return_value=(
                "cs_test123",
                "https://checkout.stripe.com/pay/cs_test123",
                1
            ))
            
            response = await client.post("/checkout/sessions", json=sample_checkout_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["session_id"] == "cs_test123"
            assert data["session_url"] == "https://checkout.stripe.com/pay/cs_test123"
            assert data["subscription_id"] == 1
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_with_sibling_discount(self, client):
        """Test creating checkout session with sibling discount."""
        request_data = {
            "tenant_id": 1,
            "plan_type": "yearly",
            "seats": 10,
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
            "has_sibling_discount": True
        }
        
        with patch('app.main.subscription_service') as mock_service:
            mock_service.create_checkout_session = AsyncMock(return_value=(
                "cs_test123",
                "https://checkout.stripe.com/pay/cs_test123",
                2
            ))
            
            response = await client.post("/checkout/sessions", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["session_id"] == "cs_test123"
            assert data["subscription_id"] == 2


class TestSubscriptionAPI:
    """Test subscription API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_subscription_by_id(self, client, db_session):
        """Test retrieving subscription by ID."""
        # First create a subscription
        trial_request = {"tenant_id": 1, "seats": 5}
        trial_response = await client.post("/trials/start", json=trial_request)
        subscription_id = trial_response.json()["id"]
        
        # Retrieve the subscription
        response = await client.get(f"/subscriptions/{subscription_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == subscription_id
        assert data["tenant_id"] == 1
        assert data["seats"] == 5
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_subscription(self, client):
        """Test retrieving non-existent subscription."""
        response = await client.get("/subscriptions/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_tenant_subscriptions(self, client):
        """Test retrieving subscriptions by tenant."""
        # Create multiple subscriptions for the same tenant
        requests = [
            {"tenant_id": 1, "seats": 3},
            {"tenant_id": 1, "seats": 5},
            {"tenant_id": 2, "seats": 7}  # Different tenant
        ]
        
        for request_data in requests:
            await client.post("/trials/start", json=request_data)
        
        # Get subscriptions for tenant 1
        response = await client.get("/subscriptions/tenant/1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert all(sub["tenant_id"] == 1 for sub in data)
    
    @pytest.mark.asyncio
    async def test_get_guardian_subscriptions(self, client):
        """Test retrieving subscriptions by guardian."""
        # Create subscriptions for different guardians
        requests = [
            {"guardian_id": "guardian1", "seats": 2},
            {"guardian_id": "guardian1", "seats": 4},
            {"guardian_id": "guardian2", "seats": 6}
        ]
        
        for request_data in requests:
            await client.post("/trials/start", json=request_data)
        
        # Get subscriptions for guardian1
        response = await client.get("/subscriptions/guardian/guardian1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert all(sub["guardian_id"] == "guardian1" for sub in data)
    
    @pytest.mark.asyncio
    async def test_cancel_subscription(self, client):
        """Test canceling a subscription."""
        # Create a subscription first
        trial_request = {"tenant_id": 1, "seats": 5}
        trial_response = await client.post("/trials/start", json=trial_request)
        subscription_id = trial_response.json()["id"]
        
        # Mock the subscription to have a Stripe ID
        with patch('app.main.subscription_service') as mock_service:
            mock_subscription = Mock()
            mock_subscription.stripe_subscription_id = "sub_test123"
            mock_service.get_subscription_by_id = AsyncMock(return_value=mock_subscription)
            
            with patch('app.main.stripe_service') as mock_stripe:
                mock_stripe.cancel_subscription = AsyncMock(return_value=Mock(id="sub_test123"))
                
                response = await client.post(f"/subscriptions/{subscription_id}/cancel")
                
                assert response.status_code == 200
                data = response.json()
                assert "canceled" in data["message"].lower()


class TestWebhookAPI:
    """Test webhook API endpoints."""
    
    @pytest.mark.asyncio
    async def test_stripe_webhook_missing_signature(self, client):
        """Test webhook with missing signature."""
        response = await client.post("/webhooks/stripe", json={"test": "data"})
        
        assert response.status_code == 400
        assert "signature" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_stripe_webhook_with_signature(self, client, sample_stripe_webhook_event):
        """Test webhook with valid signature."""
        headers = {"stripe-signature": "test_signature"}
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = sample_stripe_webhook_event
            
            with patch('app.main.process_webhook_background') as mock_process:
                response = await client.post(
                    "/webhooks/stripe",
                    json=sample_stripe_webhook_event,
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["processed"] is True
                assert "queued" in data["message"].lower()


class TestHealthAPI:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "payment-svc"
