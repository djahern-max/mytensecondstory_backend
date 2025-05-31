from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import tempfile
import os
from pathlib import Path
from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()

# Import your background removal service
try:
    from app.services.background_enhancer import background_removal_service
except ImportError:
    background_removal_service = None

@router.post("/remove-background")
async def remove_background_endpoint(
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove background from uploaded video
    """
    if background_removal_service is None:
        raise HTTPException(status_code=500, detail="Background removal service not available")
    
    # Validate file type
    if not video.content_type or not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Create temporary file for input
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input:
        content = await video.read()
        temp_input.write(content)
        temp_input_path = temp_input.name
    
    try:
        # Process the video
        output_path = await background_removal_service.remove_background_from_video(temp_input_path)
        
        # Return the processed video
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=f"processed_{video.filename}"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
    
    finally:
        # Clean up input file
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
