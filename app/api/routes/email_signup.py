from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.email_signup import EmailSignup
from app.schemas.email_signup import EmailSignupCreate, EmailSignup as EmailSignupSchema, EmailSignupStats
import logging

router = APIRouter(prefix="/api/v1/signup", tags=["Email Signup"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=EmailSignupSchema)
async def create_email_signup(
    signup_data: EmailSignupCreate,
    db: Session = Depends(get_db)
):
    """Create a new email signup"""
    try:
        # Check if email already exists
        existing_signup = db.query(EmailSignup).filter(
            EmailSignup.email == signup_data.email
        ).first()
        
        if existing_signup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new signup
        db_signup = EmailSignup(
            email=signup_data.email,
            full_name=signup_data.full_name
        )
        
        db.add(db_signup)
        db.commit()
        db.refresh(db_signup)
        
        logger.info(f"New email signup: {signup_data.email}")
        return db_signup
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating email signup: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register email"
        )

@router.get("/stats", response_model=EmailSignupStats)
async def get_signup_stats(db: Session = Depends(get_db)):
    """Get signup statistics"""
    try:
        # Total signups
        total_signups = db.query(func.count(EmailSignup.id)).scalar()
        
        # Recent signups (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_signups = db.query(func.count(EmailSignup.id)).filter(
            EmailSignup.created_at >= yesterday
        ).scalar()
        
        return EmailSignupStats(
            total_signups=total_signups or 0,
            recent_signups=recent_signups or 0
        )
        
    except Exception as e:
        logger.error(f"Error getting signup stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )
