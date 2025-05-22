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
            
            # Get user info
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            response = await client.get(user_info_url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Google",
                )
            user_info = response.json()
            
        # Create or update user
        user = db.query(User).filter(
            User.oauth_provider == OAuthProvider.GOOGLE,
            User.oauth_id == user_info["id"]
        ).first()
        
        if not user:
            # Check if email exists
            existing_user = db.query(User).filter(User.email == user_info["email"]).first()
            if existing_user:
                # Link OAuth to existing account
                existing_user.oauth_provider = OAuthProvider.GOOGLE
                existing_user.oauth_id = user_info["id"]
                existing_user.oauth_access_token = token_data.get("access_token")
                existing_user.oauth_refresh_token = token_data.get("refresh_token")
                db.commit()
                user = existing_user
            else:
                # Create new user
                user_data = UserOAuthCreate(
                    email=user_info["email"],
                    full_name=user_info.get("name"),
                    oauth_provider=OAuthProvider.GOOGLE,
                    oauth_id=user_info["id"],
                    oauth_access_token=token_data.get("access_token"),
                    oauth_refresh_token=token_data.get("refresh_token")
                )
                user = User(
                    email=user_data.email,
                    full_name=user_data.full_name,
                    oauth_provider=user_data.oauth_provider,
                    oauth_id=user_data.oauth_id,
                    oauth_access_token=user_data.oauth_access_token,
                    oauth_refresh_token=user_data.oauth_refresh_token
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
        # Generate tokens
        tokens = self.create_tokens(user.id)
        return {
            "tokens": tokens,
            "user": user
        }

    # Similar methods for other OAuth providers (GitHub, LinkedIn, Apple)
    # ...

auth_service = AuthService()