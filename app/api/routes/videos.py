# app/api/routes/payments.py
"""Payment processing endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import stripe
from datetime import datetime

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentConfirm,
    PaymentResponse,
    PaymentListResponse,
)
from app.services.payment import PaymentService
from app.core.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()
payment_service = PaymentService()


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a payment intent for processing"""
    try:
        # Validate amount
        if payment_data.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than 0",
            )

        # Create payment intent with Stripe
        intent = stripe.PaymentIntent.create(
            amount=int(payment_data.amount * 100),  # Convert to cents
            currency=payment_data.currency.lower(),
            customer=(
                current_user.stripe_customer_id
                if hasattr(current_user, "stripe_customer_id")
                else None
            ),
            metadata={
                "user_id": str(current_user.id),
                "payment_type": payment_data.payment_type,
                "video_id": (
                    str(payment_data.video_id) if payment_data.video_id else None
                ),
            },
        )

        # Create payment record in database
        db_payment = Payment(
            user_id=current_user.id,
            stripe_payment_intent_id=intent.id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            payment_type=payment_data.payment_type,
            video_id=payment_data.video_id,
            status=PaymentStatus.PENDING,
        )

        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            payment_id=db_payment.id,
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}",
        )


@router.post("/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_confirm: PaymentConfirm,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Confirm payment completion"""
    try:
        # Get payment from database
        payment = (
            db.query(Payment)
            .filter(
                Payment.stripe_payment_intent_id == payment_confirm.payment_intent_id,
                Payment.user_id == current_user.id,
            )
            .first()
        )

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )

        # Retrieve payment intent from Stripe
        intent = stripe.PaymentIntent.retrieve(payment_confirm.payment_intent_id)

        if intent.status == "succeeded":
            # Update payment status
            payment.status = PaymentStatus.COMPLETED
            payment.stripe_charge_id = intent.latest_charge
            payment.completed_at = datetime.utcnow()

            # Process payment completion (e.g., unlock features)
            background_tasks.add_task(
                payment_service.process_payment_completion, payment.id
            )

        elif intent.status == "requires_action":
            payment.status = PaymentStatus.PENDING
        else:
            payment.status = PaymentStatus.FAILED

        db.commit()
        db.refresh(payment)

        return PaymentResponse.from_orm(payment)

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm payment: {str(e)}",
        )


@router.get("/history", response_model=PaymentListResponse)
async def get_payment_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's payment history"""
    try:
        # Get total count
        total = db.query(Payment).filter(Payment.user_id == current_user.id).count()

        # Get payments with pagination
        payments = (
            db.query(Payment)
            .filter(Payment.user_id == current_user.id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return PaymentListResponse(
            payments=payments, total=total, skip=skip, limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment history: {str(e)}",
        )


@router.get("/pricing")
async def get_pricing():
    """Get current pricing information"""
    try:
        pricing = payment_service.get_payment_pricing()
        return {"pricing": pricing}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pricing: {str(e)}",
        )


@router.post("/webhook")
async def stripe_webhook(
    request: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """Handle Stripe webhooks"""
    try:
        event = request

        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]

            # Find payment in database
            payment = (
                db.query(Payment)
                .filter(Payment.stripe_payment_intent_id == payment_intent["id"])
                .first()
            )

            if payment:
                payment.status = PaymentStatus.COMPLETED
                payment.stripe_charge_id = payment_intent.get("latest_charge")
                payment.completed_at = datetime.utcnow()

                # Process payment completion
                background_tasks.add_task(
                    payment_service.process_payment_completion, payment.id
                )

                db.commit()

        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]

            payment = (
                db.query(Payment)
                .filter(Payment.stripe_payment_intent_id == payment_intent["id"])
                .first()
            )

            if payment:
                payment.status = PaymentStatus.FAILED
                db.commit()

        elif event["type"] == "customer.subscription.created":
            # Handle subscription creation
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]

            # Find user by Stripe customer ID
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                user.is_premium = True
                db.commit()

        elif event["type"] == "customer.subscription.deleted":
            # Handle subscription cancellation
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]

            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                user.is_premium = False
                db.commit()

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}",
        )


@router.post("/create-customer")
async def create_stripe_customer(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Create a Stripe customer for the current user"""
    try:
        # Check if user already has a Stripe customer ID
        if (
            hasattr(current_user, "stripe_customer_id")
            and current_user.stripe_customer_id
        ):
            return {"customer_id": current_user.stripe_customer_id}

        # Create customer with Stripe
        customer = stripe.Customer.create(
            email=current_user.email,
            name=getattr(current_user, "full_name", None),
            metadata={"user_id": str(current_user.id)},
        )

        # Update user with Stripe customer ID
        current_user.stripe_customer_id = customer.id
        db.commit()

        return {"customer_id": customer.id}

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create customer: {str(e)}",
        )


@router.post("/cancel-payment/{payment_id}")
async def cancel_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending payment"""
    try:
        # Get payment
        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id, Payment.user_id == current_user.id)
            .first()
        )

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )

        if payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment cannot be cancelled",
            )

        # Cancel with Stripe
        stripe.PaymentIntent.cancel(payment.stripe_payment_intent_id)

        # Update payment status
        payment.status = PaymentStatus.CANCELLED
        db.commit()

        return {"message": "Payment cancelled successfully"}

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel payment: {str(e)}",
        )


@router.get("/subscription/status")
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Get user's subscription status"""
    try:
        is_premium = getattr(current_user, "is_premium", False)
        premium_expires = getattr(current_user, "premium_expires_at", None)

        return {
            "is_premium": is_premium,
            "premium_expires_at": premium_expires,
            "subscription_active": is_premium
            and (premium_expires is None or premium_expires > datetime.utcnow()),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription status: {str(e)}",
        )
