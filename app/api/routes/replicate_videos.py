from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import tempfile
import os

from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.services.replicate_service import replicate_service

router = APIRouter()


@router.post("/remove-background")
async def remove_video_background(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    background_type: str = "alpha-mask",  # alpha-mask, green-screen, or black
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Remove background from video using Replicate

    background_type options:
    - alpha-mask: Transparent background
    - green-screen: Green background
    - black: Black background
    """

    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_video_path = temp_file.name
        content = await video.read()
        temp_file.write(content)

    try:
        # Process with Replicate
        result = replicate_service.remove_background(
            video_file_path=temp_video_path, background_type=background_type
        )

        # Clean up
        background_tasks.add_task(os.unlink, temp_video_path)

        return result

    except Exception as e:
        os.unlink(temp_video_path)
        raise HTTPException(status_code=500, detail=str(e))
