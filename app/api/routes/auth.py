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

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(...),
    db: Session = Depends(get_db)
):
    """Get a new access token using refresh token"""
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type",
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return auth_service.create_tokens(user.id)

@router.post("/register", response_model=User)
async def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password
    """
    # Check if user already exists
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = UserModel(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password) if user_in.password else None,
        full_name=user_in.full_name,
        oauth_provider=OAuthProvider.EMAIL,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user