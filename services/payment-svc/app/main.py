"""
Main FastAPI application for payment service.
"""
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional, List

import stripe
from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db, create_tables
from .models import PlanType, SubscriptionStatus
from .schemas import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    TrialStartRequest,
    Subscription,
    PricingRequest,
    PricingCalculation,
    SubscriptionSummary,
    WebhookEventResponse,
    ErrorResponse,
    MessageResponse
)
from .services import SubscriptionService, StripeService, WebhookService, PricingService


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# For testing, we'll allow missing Stripe keys
if STRIPE_API_KEY and not STRIPE_API_KEY.startswith("sk_test_"):
    # In production, we might want to validate the key format
    pass

# Initialize services conditionally
if STRIPE_API_KEY:
    stripe_service = StripeService(STRIPE_API_KEY)
    subscription_service = SubscriptionService(stripe_service)
    webhook_service = WebhookService(subscription_service)
else:
    # For testing without Stripe keys
    stripe_service = None
    subscription_service = None
    webhook_service = None

pricing_service = PricingService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting payment service...")
    await create_tables()
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down payment service...")


# Create FastAPI app
app = FastAPI(
    title="Payment Service",
    description="Payment processing service with Stripe integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "payment-svc"}


# Pricing endpoints
@app.post("/pricing/calculate", response_model=PricingCalculation)
async def calculate_pricing(request: PricingRequest):
    """
    Calculate pricing for a subscription plan.
    
    Args:
        request: Pricing calculation request
    
    Returns:
        Detailed pricing calculation
    """
    try:
        return pricing_service.calculate_pricing(
            plan_type=request.plan_type,
            seats=request.seats,
            has_sibling_discount=request.has_sibling_discount
        )
    except Exception as e:
        logger.error(f"Error calculating pricing: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Trial endpoints
@app.post("/trials/start", response_model=Subscription)
async def start_trial(
    request: TrialStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Start a trial subscription.
    
    Args:
        request: Trial start request
        db: Database session
    
    Returns:
        Created trial subscription
    """
    if not subscription_service:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    try:
        return await subscription_service.start_trial(db, request)
    except Exception as e:
        logger.error(f"Error starting trial: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Checkout endpoints
@app.post("/checkout/sessions", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription purchase.
    
    Args:
        request: Checkout session request
        db: Database session
    
    Returns:
        Checkout session details
    """
    if not subscription_service:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    try:
        session_id, session_url, subscription_id = await subscription_service.create_checkout_session(
            db, request
        )
        
        return CheckoutSessionResponse(
            session_id=session_id,
            session_url=session_url,
            subscription_id=subscription_id
        )
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Subscription endpoints
@app.get("/subscriptions/{subscription_id}", response_model=Subscription)
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get subscription by ID.
    
    Args:
        subscription_id: Subscription ID
        db: Database session
    
    Returns:
        Subscription details
    """
    if not subscription_service:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    subscription = await subscription_service.get_subscription_by_id(db, subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return subscription


@app.get("/subscriptions/tenant/{tenant_id}", response_model=List[Subscription])
async def get_tenant_subscriptions(
    tenant_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all subscriptions for a tenant.
    
    Args:
        tenant_id: Tenant ID
        db: Database session
    
    Returns:
        List of tenant subscriptions
    """
    return await subscription_service.get_subscriptions_by_tenant(db, tenant_id)


@app.get("/subscriptions/guardian/{guardian_id}", response_model=List[Subscription])
async def get_guardian_subscriptions(
    guardian_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all subscriptions for a guardian.
    
    Args:
        guardian_id: Guardian ID
        db: Database session
    
    Returns:
        List of guardian subscriptions
    """
    return await subscription_service.get_subscriptions_by_guardian(db, guardian_id)


@app.post("/subscriptions/{subscription_id}/cancel", response_model=MessageResponse)
async def cancel_subscription(
    subscription_id: int,
    at_period_end: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a subscription.
    
    Args:
        subscription_id: Subscription ID
        at_period_end: Whether to cancel at period end
        db: Database session
    
    Returns:
        Cancellation confirmation
    """
    try:
        subscription = await subscription_service.get_subscription_by_id(db, subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if not subscription.stripe_subscription_id:
            raise HTTPException(status_code=400, detail="Subscription not active in Stripe")
        
        # Cancel in Stripe
        await stripe_service.cancel_subscription(
            subscription.stripe_subscription_id,
            at_period_end=at_period_end
        )
        
        # Update local status if canceling immediately
        if not at_period_end:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
            await db.commit()
        
        message = "Subscription canceled at period end" if at_period_end else "Subscription canceled immediately"
        return MessageResponse(message=message)
        
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Webhook endpoints
@app.post("/webhooks/stripe", response_model=WebhookEventResponse)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    
    Args:
        request: HTTP request
        background_tasks: Background task runner
        db: Database session
    
    Returns:
        Webhook processing result
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Process webhook in background
    background_tasks.add_task(
        process_webhook_background,
        db,
        event["id"],
        event["type"],
        event["data"]
    )
    
    return WebhookEventResponse(
        processed=True,
        message="Webhook received and queued for processing"
    )


async def process_webhook_background(
    db: AsyncSession,
    event_id: str,
    event_type: str,
    event_data: Dict[str, Any]
):
    """Process webhook in background task."""
    try:
        await webhook_service.process_webhook(db, event_id, event_type, event_data)
    except Exception as e:
        logger.error(f"Background webhook processing failed: {str(e)}")


# Error handlers
@app.exception_handler(stripe.error.StripeError)
async def stripe_error_handler(request: Request, exc: stripe.error.StripeError):
    """Handle Stripe errors."""
    logger.error(f"Stripe error: {str(exc)}")
    return ErrorResponse(
        detail="Payment processing error",
        error_code=exc.code,
        stripe_error={
            "type": exc.__class__.__name__,
            "message": str(exc),
            "code": exc.code
        }
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """Handle general errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    return ErrorResponse(detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
