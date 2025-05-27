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
