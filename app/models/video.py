from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    # Storage info
    storage_path = Column(String, nullable=False)
    public_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    
    # Video metadata
    duration = Column(Integer, nullable=True)  # in seconds
    format = Column(String, nullable=True)
    size = Column(Integer, nullable=True)  # in bytes
    
    # Status and visibility
    is_published = Column(Boolean, default=False)
    is_private = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)