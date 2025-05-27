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
       "count": len(AI_BACKGROUNDS)
   }

@router.get("/templates")
async def get_video_templates() -> Dict[str, Any]:
   """Get available video generation templates"""
   result = await ai_service.get_available_templates()
   return result

@router.post("/generate-video")
async def generate_video_from_text(
   request: VideoGenerationRequest,
   background_tasks: BackgroundTasks,
   # current_user: User = Depends(get_current_user),
   # db: Session = Depends(get_db)
) -> Dict[str, Any]:
   """Generate video from text prompt using Google Veo 3"""
   
   try:
       # Validate template type
       if request.template_type not in VEO_PROMPT_TEMPLATES:
           raise HTTPException(
               status_code=400, 
               detail=f"Invalid template type. Available: {list(VEO_PROMPT_TEMPLATES.keys())}"
           )
       
       # Validate background setting
       if request.background_setting not in VEO_BACKGROUND_SETTINGS:
           raise HTTPException(
               status_code=400,
               detail=f"Invalid background setting. Available: {list(VEO_BACKGROUND_SETTINGS.keys())}"
           )
       
       # Validate duration
       if request.duration > 30:
           raise HTTPException(
               status_code=400,
               detail="Maximum video duration is 30 seconds"
           )
       
       # Start video generation
       result = await ai_service.generate_video_from_text(
           prompt=request.prompt,
           template_type=request.template_type,
           background_setting=request.background_setting,
           duration=request.duration,
           resolution=request.resolution,
           user_id=1  # Replace with current_user.id
       )
       
       # Schedule cleanup task
       background_tasks.add_task(ai_service.cleanup_completed_jobs)
       
       return {
           "message": "Video generation started",
           "job_id": result["job_id"],
           "status": result["status"],
           "prompt": request.prompt,
           "template": VEO_PROMPT_TEMPLATES[request.template_type],
           "background": VEO_BACKGROUND_SETTINGS[request.background_setting],
           "estimated_completion_seconds": result["estimated_completion_seconds"]
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-background")
async def enhance_video_background(
   request: VideoEnhancementRequest,
   background_tasks: BackgroundTasks,
   # current_user: User = Depends(get_current_user),
   # db: Session = Depends(get_db)
) -> Dict[str, Any]:
   """Start AI background enhancement job for a video"""
   
   try:
       # Validate background type
       if request.background_type not in AI_BACKGROUNDS:
           raise HTTPException(
               status_code=400, 
               detail=f"Invalid background type. Available: {list(AI_BACKGROUNDS.keys())}"
           )
       
       # TODO: Get actual video file path from video_id
       video_file_path = f"/tmp/videos/video_{request.video_id}.mp4"
       
       # Start background enhancement
       result = await ai_service.enhance_video_background(
           video_file_path=video_file_path,
           background_type=request.background_type,
           user_id=1  # Replace with current_user.id
       )
       
       # Schedule cleanup task
       background_tasks.add_task(ai_service.cleanup_completed_jobs)
       
       return {
           "message": "Background enhancement job started",
           "job_id": result["job_id"],
           "status": result["status"],
           "background_type": request.background_type,
           "veo_background": result["veo_background"],
           "estimated_completion_seconds": result["estimated_completion_seconds"]
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-quality")
async def enhance_video_quality(
   request: QualityEnhancementRequest,
   background_tasks: BackgroundTasks,
   # current_user: User = Depends(get_current_user),
   # db: Session = Depends(get_db)
) -> Dict[str, Any]:
   """Enhance video quality using AI"""
   
   try:
       # TODO: Get actual video file path from video_id
       video_file_path = f"/tmp/videos/video_{request.video_id}.mp4"
       
       # Start quality enhancement
       result = await ai_service.enhance_video_quality(
           video_file_path=video_file_path,
           quality_level=request.quality_level,
           user_id=1  # Replace with current_user.id
       )
       
       # Schedule cleanup task
       background_tasks.add_task(ai_service.cleanup_completed_jobs)
       
       return {
           "message": "Quality enhancement job started",
           "job_id": result["job_id"],
           "status": result["status"],
           "quality_level": request.quality_level,
           "estimated_completion_seconds": result["estimated_completion_seconds"]
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-enhance")
async def upload_and_enhance_video(
   file: UploadFile = File(...),
   enhancement_type: str = "quality",
   background_type: Optional[str] = None,
   # current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
   """Upload video file and start enhancement"""
   
   try:
       # Validate file type
       if not file.content_type.startswith('video/'):
           raise HTTPException(
               status_code=400,
               detail="File must be a video"
           )
       
       # Save uploaded file
       import os
       import uuid
       temp_filename = f"{uuid.uuid4().hex}.mp4"
       temp_path = f"/tmp/videos/{temp_filename}"
       
       # Ensure directory exists
       os.makedirs(os.path.dirname(temp_path), exist_ok=True)
       
       # Save file
       with open(temp_path, "wb") as buffer:
           content = await file.read()
           buffer.write(content)
       
       # Start appropriate enhancement
       if enhancement_type == "background" and background_type:
           if background_type not in AI_BACKGROUNDS:
               raise HTTPException(
                   status_code=400,
                   detail=f"Invalid background type. Available: {list(AI_BACKGROUNDS.keys())}"
               )
           
           result = await ai_service.enhance_video_background(
               video_file_path=temp_path,
               background_type=background_type,
               user_id=1  # Replace with current_user.id
           )
       else:
           result = await ai_service.enhance_video_quality(
               video_file_path=temp_path,
               quality_level="high",
               user_id=1  # Replace with current_user.id
           )
       
       return {
           "message": f"Video uploaded and {enhancement_type} enhancement started",
           "job_id": result["job_id"],
           "status": result["status"],
           "enhancement_type": enhancement_type,
           "filename": file.filename,
           "estimated_completion_seconds": result["estimated_completion_seconds"]
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}")
async def get_enhancement_status(
   job_id: str,
   # current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
   """Check the status of an enhancement or generation job"""
   
   try:
       result = await ai_service.get_enhancement_status(job_id)
       return result
       
   except Exception as e:
       raise HTTPException(status_code=404, detail=str(e))

@router.delete("/cancel/{job_id}")
async def cancel_enhancement(
   job_id: str,
   # current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
   """Cancel an ongoing enhancement job"""
   
   try:
       success = await ai_service.cancel_enhancement(job_id)
       
       if success:
           return {"message": "Enhancement job cancelled successfully"}
       else:
           raise HTTPException(status_code=400, detail="Failed to cancel job")
           
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/history")
async def get_user_job_history(
   limit: int = 10,
   # current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
   """Get user's AI job history"""
   
   try:
       jobs = await ai_service.get_user_job_history(
           user_id=1,  # Replace with current_user.id
           limit=limit
       )
       
       return {
           "jobs": jobs,
           "count": len(jobs)
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance")  # Keep legacy endpoint for backward compatibility
async def enhance_video_legacy(
   video_id: int,
   background_type: str,
   # background_tasks: BackgroundTasks,
   # current_user: User = Depends(get_current_user),
   # db: Session = Depends(get_db)
) -> Dict[str, Any]:
   """Legacy endpoint for video enhancement (backward compatibility)"""
   
   # Validate background type
   if background_type not in AI_BACKGROUNDS:
       raise HTTPException(
           status_code=400, 
           detail=f"Invalid background type. Available: {list(AI_BACKGROUNDS.keys())}"
       )
   
   try:
       # Convert to new format
       request = VideoEnhancementRequest(
           video_id=video_id,
           background_type=background_type
       )
       
       return await enhance_video_background(request, BackgroundTasks())
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))
