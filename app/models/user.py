from sqlalchemy import Boolean, Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from app.db.session import Base
import uuid

class OAuthProvider(str, enum.Enum):
    GOOGLE = "google"
    GITHUB = "github"
    LINKEDIN = "linkedin"
    APPLE = "apple"
    EMAIL = "email"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # OAuth fields
    oauth_provider = Column(Enum(OAuthProvider), nullable=True)
    oauth_id = Column(String, nullable=True, index=True)
    oauth_access_token = Column(String, nullable=True)
    oauth_refresh_token = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())