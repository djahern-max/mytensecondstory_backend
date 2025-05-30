# MyTenSecondStory Backend Application Documentation

Generated on: 2025-05-30T08:56:56.082786

## Overview
This is a FastAPI-based backend application for MyTenSecondStory, a platform for creating and sharing 10-second personal video stories with AI-generated backgrounds.

## Application Structure

```
app/
  api/
    dependencies.py
    errors.py
    routes/
      ai_enhancement.py
      auth.py
      mobile_upload.py
      payments.py
      users.py
      videos.py
  core/
    ai_config.py
    config.py
    constants.py
    events.py
    security.py
  db/
    base.py
    session.py
  main.py
  models/
    background_template.py
    enhancement_job.py
    payment.py
    user.py
    video.py
  requirements.txt
  requirements_additions.txt
  schemas/
    enhancement.py
    mobile_upload.py
    payment.py
    user.py
    video.py
  services/
    ai_service.py
    auth.py
    background_enhancer.py
    mobile_optimizer.py
    payment.py
    storage.py
    video.py
  tasks/
    __init__.py
    enhancement_tasks.py
  utils/
    __init__.py
    ai_client.py
    mobile_utils.py
    video_processing.py

```

## Dependencies
The application uses the following main dependencies:
- fastapi>=0.95.0,<0.96.0
- uvicorn>=0.21.1,<0.22.0
- sqlalchemy>=2.0.9,<2.1.0
- psycopg2-binary>=2.9.6,<2.10.0
- alembic>=1.10.3,<1.11.0
- pydantic>=1.10.7,<2.0.0
- python-jose>=3.3.0,<3.4.0
- passlib>=1.7.4,<1.8.0
- python-multipart>=0.0.6,<0.1.0
- httpx>=0.24.0,<0.25.0
- stripe>=5.4.0,<5.5.0
- boto3>=1.26.131,<1.27.0
- python-dotenv>=1.0.0,<1.1.0
- bcrypt>=4.0.1,<4.1.0
- email-validator>=2.0.0,<2.1.0

## Database Models

### User Model
- **Classes**: OAuthProvider, User
- **Functions**: 
- **Lines of code**: 33

### Enhancement_Job Model
- **Classes**: JobStatus, EnhancementType, EnhancementJob
- **Functions**: __repr__, is_completed, is_processing, can_retry, update_progress, mark_started, mark_completed, mark_failed, mark_cancelled, increment_retry, get_estimated_completion_time, get_enhancement_summary, to_dict
- **Lines of code**: 326

### Background_Template Model
- **Classes**: BackgroundCategory, BackgroundTemplate
- **Functions**: __repr__, is_available, networking_score, increment_usage, update_success_rate, add_rating, get_processing_estimate, to_dict, get_networking_templates, get_by_category, search_templates
- **Lines of code**: 327

### Video Model
- **Classes**: Video
- **Functions**: 
- **Lines of code**: 32

### Payment Model
- **Classes**: PaymentStatus, Payment
- **Functions**: 
- **Lines of code**: 28

## API Routes

### Auth Routes
- **Functions**: 
- **Lines of code**: 106

### Mobile_Upload Routes
- **Functions**: 
- **Lines of code**: 75

### Payments Routes
- **Functions**: 
- **Lines of code**: 1

### Users Routes
- **Functions**: read_user_me, read_user, read_users
- **Lines of code**: 40

### Ai_Enhancement Routes
- **Functions**: 
- **Lines of code**: 335

### Videos Routes
- **Functions**: 
- **Lines of code**: 379

## Services

### Auth Service
- **Classes**: AuthService
- **Functions**: authenticate_user, create_tokens
- **Lines of code**: 111

### Ai_Service Service
- **Classes**: AIEnhancementService
- **Functions**: __init__, _map_background_type
- **Lines of code**: 315

### Storage Service
- **Classes**: StorageService
- **Functions**: __init__, _init_local, _init_s3, _init_gcs, _get_file_extension, get_file_url
- **Lines of code**: 452

### Background_Enhancer Service
- **Classes**: 
- **Functions**: 
- **Lines of code**: 1

### Video Service
- **Classes**: 
- **Functions**: 
- **Lines of code**: 1

### Payment Service
- **Classes**: 
- **Functions**: 
- **Lines of code**: 1

### Mobile_Optimizer Service
- **Classes**: MobileOptimizerService
- **Functions**: __init__
- **Lines of code**: 63

## Data Schemas

### Mobile_Upload Schema
- **Classes**: 
- **Lines of code**: 1

### User Schema
- **Classes**: UserBase, UserCreate, UserOAuthCreate, User, Token, TokenPayload, Config
- **Lines of code**: 46

### Video Schema
- **Classes**: 
- **Lines of code**: 632

### Payment Schema
- **Classes**: 
- **Lines of code**: 1

### Enhancement Schema
- **Classes**: EnhancementRequest, EnhancementJob, EnhancementStatus, BackgroundOption, BackgroundsResponse, Config
- **Lines of code**: 51

## Configuration

### Config
- **Classes**: Settings, Config
- **Functions**: assemble_cors_origins
- **Lines of code**: 54

### Events
- **Classes**: 
- **Functions**: 
- **Lines of code**: 1

### Security
- **Classes**: 
- **Functions**: create_access_token, create_refresh_token, verify_password, get_password_hash
- **Lines of code**: 29

### Constants
- **Classes**: 
- **Functions**: 
- **Lines of code**: 60

### Ai_Config
- **Classes**: AISettings
- **Functions**: __init__
- **Lines of code**: 109

## Main Application
- **Functions**: 
- **Lines of code**: 62


# Detailed Code Analysis

## Models Code Analysis

### user.py

```python
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
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())```

**Classes found**: OAuthProvider, User

### enhancement_job.py

```python
"""
Enhancement Job model for tracking AI video processing jobs
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class JobStatus(str, enum.Enum):
    """Enhancement job status enumeration"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EnhancementType(str, enum.Enum):
    """Types of AI enhancements"""

    BACKGROUND = "background"
    APPEARANCE = "appearance"
    QUALITY = "quality"
    COMBINED = "combined"


class EnhancementJob(Base):
    """Model for tracking AI enhancement jobs"""

    __tablename__ = "enhancement_jobs"

    # Primary fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
... (276 more lines)
```

**Classes found**: JobStatus, EnhancementType, EnhancementJob

**Functions found**: __repr__, is_completed, is_processing, can_retry, update_progress, mark_started, mark_completed, mark_failed, mark_cancelled, increment_retry, get_estimated_completion_time, get_enhancement_summary, to_dict

### background_template.py

```python
"""
Background Template model for managing AI background templates
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class BackgroundCategory(str, enum.Enum):
    """Background categories for networking contexts"""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    IMPRESSIVE = "impressive"
    CREATIVE = "creative"
    OUTDOOR = "outdoor"


class BackgroundTemplate(Base):
    """Model for AI background templates"""

    __tablename__ = "background_templates"

    # Primary fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)

    # Template details
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False, index=True)  # BackgroundCategory

    # File paths
    preview_image_path = Column(String, nullable=True)  # Preview thumbnail
    template_image_path = Column(String, nullable=True)  # Full resolution template
    mask_image_path = Column(
        String, nullable=True
    )  # Optional mask for advanced processing

    # Display properties
    display_order = Column(Integer, default=0)  # For sorting in UI
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)

... (277 more lines)
```

**Classes found**: BackgroundCategory, BackgroundTemplate

**Functions found**: __repr__, is_available, networking_score, increment_usage, update_success_rate, add_rating, get_processing_estimate, to_dict, get_networking_templates, get_by_category, search_templates

### video.py

```python
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
    published_at = Column(DateTime(timezone=True), nullable=True)```

**Classes found**: Video

### payment.py

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from app.db.session import Base
import uuid

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="usd")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    stripe_payment_id = Column(String, unique=True, index=True, nullable=True)
    stripe_customer_id = Column(String, index=True, nullable=True)
    
    description = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())```

**Classes found**: PaymentStatus, Payment

## Routes Code Analysis

### auth.py

```python
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import ValidationError

from app.api.dependencies import get_db
from app.core.config import settings
from app.schemas.user import User, Token, TokenPayload, UserCreate
from app.services.auth import auth_service
from app.models.user import User as UserModel, OAuthProvider
from app.core.security import get_password_hash

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.create_tokens(user.id)

@router.get("/google/authorize")
async def authorize_google():
    """Return the URL to redirect the user to for Google OAuth"""
    authorize_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code"
        f"&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&scope=openid%20email%20profile"
    )
    return {"authorize_url": authorize_url}

@router.get("/google/callback", response_model=Token)
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle the callback from Google OAuth"""
    result = await auth_service.authenticate_google(code, db)
    return result["tokens"]

# Similar endpoints for GitHub, LinkedIn, and Apple
# ...

... (56 more lines)
```

### mobile_upload.py

```python
"""
Mobile-optimized video upload routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

# Import your dependencies (adjust imports as needed)
# from db.session import get_db
from app.core.constants import MOBILE_VIDEO_FORMATS, MOBILE_MAX_FILE_SIZE, MOBILE_MAX_DURATION
# from api.dependencies import get_current_user
# from models.user import User
# from services.mobile_optimizer import mobile_service

# CREATE THE ROUTER - This was missing!
router = APIRouter()

@router.post("/upload")
async def upload_mobile_video(
    file: UploadFile = File(...),
    device_info: Optional[str] = Form(None),
    orientation: Optional[str] = Form("portrait"),
    # current_user: User = Depends(get_current_user),
    # db: Session = Depends(get_db)
) -> dict:
    """
    Upload video from mobile device with optimization
    """
    
    # Validate file size
    if file.size and file.size > MOBILE_MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MOBILE_MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    # Validate file format
    if file.filename:
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in MOBILE_VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Supported: {MOBILE_VIDEO_FORMATS}"
            )
    
    # For now, return a simulated response
    video_id = f"mobile_video_{file.filename}"
    
    return {
        "message": "Video uploaded successfully",
... (25 more lines)
```

### payments.py

```python
```

### users.py

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app.api.dependencies import get_db, get_current_user, get_current_active_superuser
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_user_me(current_user: User = Depends(get_current_user)):
    """Get current user"""
    return current_user

@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """Get user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.get("/", response_model=List[UserSchema])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """Get all users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users```

**Functions found**: read_user_me, read_user, read_users

### ai_enhancement.py

```python
"""
AI Enhancement API routes with Google Veo 3 integration
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

# Import your dependencies (adjust imports as needed)
# from db.session import get_db
from app.services.ai_service import ai_service
from app.core.ai_config import VEO_PROMPT_TEMPLATES, VEO_BACKGROUND_SETTINGS
from app.core.constants import AI_BACKGROUNDS

# from api.dependencies import get_current_user
# from models.user import User

# CREATE THE ROUTER
router = APIRouter()


# Pydantic models for request validation
class VideoGenerationRequest(BaseModel):
    prompt: str
    template_type: Optional[str] = "professional_intro"
    background_setting: Optional[str] = "office_modern"
    duration: Optional[int] = 10
    resolution: Optional[str] = "1080p"


class VideoEnhancementRequest(BaseModel):
    video_id: int
    background_type: str


class QualityEnhancementRequest(BaseModel):
    video_id: int
    quality_level: Optional[str] = "high"


@router.get("/backgrounds")
async def get_available_backgrounds() -> Dict[str, Any]:
    """Get list of available AI backgrounds"""
    return {
        "backgrounds": AI_BACKGROUNDS,
        "veo_backgrounds": VEO_BACKGROUND_SETTINGS,
        "count": len(AI_BACKGROUNDS),
    }

... (285 more lines)
```

**Classes found**: VideoGenerationRequest, VideoEnhancementRequest, QualityEnhancementRequest

### videos.py

```python
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
... (329 more lines)
```

## Services Code Analysis

### auth.py

```python
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.user import User, OAuthProvider
from app.schemas.user import UserCreate, UserOAuthCreate

class AuthService:
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_tokens(self, user_id: str) -> Dict[str, str]:
        access_token = create_access_token(
            subject=user_id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(subject=user_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def authenticate_google(self, code: str, db: Session) -> Dict[str, Any]:
        """Handle Google OAuth authentication"""
        # Exchange code for token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google authentication failed",
                )
            token_data = response.json()
            
... (61 more lines)
```

**Classes found**: AuthService

**Functions found**: authenticate_user, create_tokens

### ai_service.py

```python
"""
AI Enhancement service for video generation and enhancement using Google Veo 3
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.core.ai_config import ai_settings, VEO_PROMPT_TEMPLATES, VEO_BACKGROUND_SETTINGS
from app.utils.ai_client import veo_client
from app.core.constants import AI_BACKGROUNDS, ENHANCEMENT_STATUS

logger = logging.getLogger(__name__)

class AIEnhancementService:
    """Service for handling AI video generation and enhancement operations using Google Veo 3"""
    
    def __init__(self):
        self.veo_client = veo_client
        self.max_concurrent = ai_settings.max_concurrent_jobs
        self.active_jobs = {}  # Track active jobs
        
    async def generate_video_from_text(
        self,
        prompt: str,
        template_type: str = "professional_intro",
        background_setting: str = "office_modern",
        duration: int = 10,
        resolution: str = "1080p",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt using Google Veo 3
        
        Args:
            prompt: Text description of the video content
            template_type: Video template (professional_intro, casual_intro, etc.)
            background_setting: Background environment
            duration: Video duration in seconds (max 30)
            resolution: Video resolution (720p, 1080p, 4K)
            user_id: User ID for tracking
            
        Returns:
            Dict with job information
        """
        try:
            # Validate inputs
            if duration > ai_settings.max_video_duration:
                duration = ai_settings.max_video_duration
                
... (265 more lines)
```

**Classes found**: AIEnhancementService

**Functions found**: __init__, _map_background_type

### storage.py

```python
"""
Storage service for handling video uploads, processing, and serving
Supports local storage and cloud storage (AWS S3, Google Cloud)
"""

import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from google.cloud import storage as gcs
from fastapi import UploadFile, HTTPException
import ffmpeg
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Unified storage service supporting local and cloud storage"""

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE  # 'local', 's3', or 'gcs'
        self.local_storage_path = Path(settings.LOCAL_STORAGE_PATH)
        self.max_file_size = settings.MAX_FILE_SIZE  # in bytes
        self.allowed_video_types = settings.ALLOWED_VIDEO_TYPES

        # Initialize cloud storage clients
        self.s3_client = None
        self.gcs_client = None

        if self.storage_type == "s3":
            self._init_s3()
        elif self.storage_type == "gcs":
            self._init_gcs()
        else:
            self._init_local()

    def _init_local(self):
        """Initialize local storage"""
        self.local_storage_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.local_storage_path / "videos").mkdir(exist_ok=True)
... (402 more lines)
```

**Classes found**: StorageService

**Functions found**: __init__, _init_local, _init_s3, _init_gcs, _get_file_extension, get_file_url

### background_enhancer.py

```python
```

### video.py

```python
```

### payment.py

```python
```

### mobile_optimizer.py

```python
"""
Mobile video optimization service
"""
import os
import tempfile
from typing import Dict, Any, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

class MobileOptimizerService:
    """Service for optimizing mobile video uploads"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    async def process_mobile_upload(
        self,
        file: UploadFile,
        user_id: int,
        device_info: Optional[str],
        orientation: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process and optimize mobile video upload
        """
        
        # Create temporary file
        temp_path = os.path.join(self.temp_dir, f"mobile_{user_id}_{file.filename}")
        
        # Save uploaded file
        with open(temp_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # TODO: Add video processing logic here:
        # - Validate duration (10 seconds max)
        # - Optimize for web streaming
        # - Generate thumbnail
        # - Extract metadata
        
        # For now, return mock result
        video_id = f"mobile_{user_id}_{len(content)}"
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
... (13 more lines)
```

**Classes found**: MobileOptimizerService

**Functions found**: __init__

## Schemas Code Analysis

### mobile_upload.py

```python
```

### user.py

```python
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
from app.models.user import OAuthProvider

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: Optional[str] = None
    oauth_provider: Optional[OAuthProvider] = None
    oauth_id: Optional[str] = None

# Properties to receive via OAuth
class UserOAuthCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    oauth_provider: OAuthProvider
    oauth_id: str
    oauth_access_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None

# Properties to return via API
class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# Properties for authentication
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    type: Optional[str] = None```

**Classes found**: UserBase, UserCreate, UserOAuthCreate, User, Token, TokenPayload, Config

### video.py

```python
"""
Video management routes for MyTenSecondStory
Handles video CRUD operations, sharing, and metadata management
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    BackgroundTasks,
    Query,
)
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.video import Video
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoListResponse,
    ShareLinkCreate,
)
from app.services.storage import storage_service
from app.services.ai_service import ai_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new video file"""

    try:
        # Upload to storage service
... (582 more lines)
```

### payment.py

```python
```

### enhancement.py

```python
"""
Schemas for AI enhancement endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class EnhancementRequest(BaseModel):
    video_id: int = Field(..., description="ID of the video to enhance")
    background_type: str = Field(..., description="Type of AI background to apply")

class EnhancementJob(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    video_id: int = Field(..., description="ID of the source video")
    background_type: str = Field(..., description="Applied background type")
    status: str = Field(..., description="Current job status")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    
    # URLs
    original_video_url: Optional[str] = Field(None, description="URL to original video")
    enhanced_video_url: Optional[str] = Field(None, description="URL to enhanced video")
    
    # Timestamps
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        from_attributes = True

class EnhancementStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    enhanced_video_url: Optional[str] = None
    error_message: Optional[str] = None

class BackgroundOption(BaseModel):
    id: str = Field(..., description="Background identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Background description")
    category: str = Field(..., description="Background category")
    preview_url: Optional[str] = Field(None, description="Preview image URL")

class BackgroundsResponse(BaseModel):
    backgrounds: Dict[str, BackgroundOption]
    count: int
... (1 more lines)
```

**Classes found**: EnhancementRequest, EnhancementJob, EnhancementStatus, BackgroundOption, BackgroundsResponse, Config

