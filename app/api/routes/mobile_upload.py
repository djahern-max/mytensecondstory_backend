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
        "video_id": video_id,
        "optimized_for_mobile": True,
        "ready_for_enhancement": True,
        "file_info": {
            "original_name": file.filename,
            "size_mb": round((file.size or 0) / 1024 / 1024, 2),
            "format": file.filename.split('.')[-1].lower() if file.filename else "unknown",
            "orientation": orientation
        }
    }

@router.get("/formats")
async def get_supported_formats():
    """Get supported video formats for mobile upload"""
    return {
        "supported_formats": MOBILE_VIDEO_FORMATS,
        "max_file_size_mb": MOBILE_MAX_FILE_SIZE // 1024 // 1024,
        "max_duration_seconds": MOBILE_MAX_DURATION,
        "recommended_settings": {
            "resolution": "720p or 1080p",
            "frame_rate": "30fps",
            "orientation": "portrait for mobile, landscape for sharing"
        }
    }
