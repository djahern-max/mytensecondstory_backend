
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class EmailSignup(Base):
    __tablename__ = "email_signups"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    is_notified = Column(Boolean, default=False)  # For when you launch
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
