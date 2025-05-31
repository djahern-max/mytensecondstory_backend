# MyTenSecondStory Backend Application Documentation

Generated on: 2025-05-30T20:37:16.419699

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
- **Lines of code**: 462

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
- **Lines of code**: 357

### Storage Service
- **Classes**: StorageService
- **Functions**: __init__, _init_local, _init_s3, _init_gcs, _get_file_extension, get_file_url
- **Lines of code**: 452

### Background_Enhancer Service
- **Classes**: BackgroundRemovalService
- **Functions**: __init__, get_video_info
- **Lines of code**: 273

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
