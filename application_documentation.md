# MyTenSecondStory Backend Application Documentation

Generated on: 2025-05-31T18:20:27.214304

## Overview
This is a FastAPI-based backend application for MyTenSecondStory, a platform for creating and sharing 10-second personal video stories with AI-generated backgrounds.

## Application Structure

```
app/
  api/
    dependencies.py
    routes/
      ai_enhancement.py
      auth.py
      replicate_videos.py
      users.py
      videos.py
  core/
    config.py
    security.py
  db/
    base.py
    session.py
  main.py
  models/
    user.py
  schemas/
    user.py
  services/
    ai_service.py
    auth.py
    background_enhancer.py
    replicate_service.py
  utils/
    __init__.py
    ai_client.py

```

## Dependencies
The application uses the following main dependencies:
- alembic==1.10.4
- annotated-types==0.7.0
- anyio==4.9.0
- attrs==25.3.0
- bcrypt==4.0.1
- boto3==1.26.165
- botocore==1.29.165
- cachetools==5.5.2
- certifi==2025.4.26
- charset-normalizer==3.4.2
- click==8.2.1
- coloredlogs==15.0.1
- distro==1.9.0
- dnspython==2.7.0
- docstring_parser==0.16
- ecdsa==0.19.1
- email-validator==2.0.0.post2
- fastapi==0.115.12
- ffmpeg-python==0.2.0
- flatbuffers==25.2.10
... and 76 more dependencies

## Database Models

### User Model
- **Classes**: OAuthProvider, User
- **Functions**: 
- **Lines of code**: 33

## API Routes

### Auth Routes
- **Functions**: 
- **Lines of code**: 106

### Users Routes
- **Functions**: read_user_me, read_user, read_users
- **Lines of code**: 40

### Replicate_Videos Routes
- **Functions**: 
- **Lines of code**: 1

### Ai_Enhancement Routes
- **Functions**: 
- **Lines of code**: 462

### Videos Routes
- **Functions**: 
- **Lines of code**: 58

## Services

### Auth Service
- **Classes**: AuthService
- **Functions**: authenticate_user, create_tokens
- **Lines of code**: 111

### Ai_Service Service
- **Classes**: AIEnhancementService
- **Functions**: __init__, _map_background_type
- **Lines of code**: 357

### Background_Enhancer Service
- **Classes**: BackgroundRemovalService
- **Functions**: __init__, get_video_info
- **Lines of code**: 214

### Replicate_Service Service
- **Classes**: 
- **Functions**: 
- **Lines of code**: 1

## Data Schemas

### User Schema
- **Classes**: UserBase, UserCreate, UserOAuthCreate, User, Token, TokenPayload, Config
- **Lines of code**: 46

## Configuration

### Config
- **Classes**: Settings, Config
- **Functions**: assemble_cors_origins
- **Lines of code**: 54

### Security
- **Classes**: 
- **Functions**: create_access_token, create_refresh_token, verify_password, get_password_hash
- **Lines of code**: 33

## Main Application
- **Functions**: 
- **Lines of code**: 57
