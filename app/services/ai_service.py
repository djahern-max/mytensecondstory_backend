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
                
            if template_type not in VEO_PROMPT_TEMPLATES:
                template_type = "professional_intro"
                
            if background_setting not in VEO_BACKGROUND_SETTINGS:
                background_setting = "office_modern"
            
            # Check concurrent job limit
            active_user_jobs = len([job for job in self.active_jobs.values() 
                                  if job.get('user_id') == user_id and job.get('status') == 'processing'])
            
            if active_user_jobs >= self.max_concurrent:
                raise Exception("Maximum concurrent jobs reached. Please wait for existing jobs to complete.")
            
            # Generate video using Veo 3
            result = await self.veo_client.generate_video_from_prompt(
                prompt=prompt,
                template_type=template_type,
                background_setting=background_setting,
                duration=duration,
                resolution=resolution,
                user_id=user_id
            )
            
            # Track the job
            self.active_jobs[result['job_id']] = result
            
            return {
                "job_id": result['job_id'],
                "status": ENHANCEMENT_STATUS["PROCESSING"],
                "prompt": prompt,
                "template_type": template_type,
                "background_setting": background_setting,
                "duration": duration,
                "resolution": resolution,
                "estimated_completion_seconds": ai_settings.video_generation_timeout,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating video from text: {e}")
            raise Exception(f"Video generation failed: {str(e)}")
    
    async def enhance_video_background(
        self, 
        video_file_path: str, 
        background_type: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Enhance video with AI background replacement using Veo 3
        
        Args:
            video_file_path: Path to the original video file
            background_type: Type of background from AI_BACKGROUNDS
            user_id: ID of the user requesting enhancement
            
        Returns:
            Dict with job_id and status
        """
        try:
            # Validate background type
            if background_type not in AI_BACKGROUNDS:
                raise ValueError(f"Invalid background type: {background_type}")
            
            # Map to Veo background setting
            veo_background = self._map_background_type(background_type)
            
            # Enhance video using Veo 3
            result = await self.veo_client.enhance_existing_video(
                video_url=video_file_path,
                enhancement_type="background",
                background_replacement=veo_background,
                user_id=user_id
            )
            
            # Track the job
            self.active_jobs[result['job_id']] = result
            
            return {
                "job_id": result['job_id'],
                "status": ENHANCEMENT_STATUS["PROCESSING"],
                "background_type": background_type,
                "veo_background": veo_background,
                "estimated_completion_seconds": ai_settings.enhancement_timeout,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enhancing video background: {e}")
            raise Exception(f"Background enhancement failed: {str(e)}")
    
    async def enhance_video_quality(
        self,
        video_file_path: str,
        quality_level: str = "high",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enhance video quality using Veo 3
        
        Args:
            video_file_path: Path to the original video file
            quality_level: Quality enhancement level (low, medium, high)
            user_id: User ID for tracking
            
        Returns:
            Dict with job information
        """
        try:
            result = await self.veo_client.enhance_existing_video(
                video_url=video_file_path,
                enhancement_type="quality",
                user_id=user_id
            )
            
            # Track the job
            self.active_jobs[result['job_id']] = result
            
            return {
                "job_id": result['job_id'],
                "status": ENHANCEMENT_STATUS["PROCESSING"],
                "enhancement_type": "quality",
                "quality_level": quality_level,
                "estimated_completion_seconds": ai_settings.enhancement_timeout,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error enhancing video quality: {e}")
            raise Exception(f"Quality enhancement failed: {str(e)}")
    
    async def get_enhancement_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of an enhancement or generation job"""
        try:
            # Check if job exists in our tracking
            if job_id not in self.active_jobs:
                raise Exception("Job not found")
            
            job_info = self.active_jobs[job_id]
            veo_job_id = job_info.get('veo_job_id')
            
            # Get status from Veo 3
            status_result = await self.veo_client.check_video_status(job_id, veo_job_id)
            
            # Update job status
            if status_result['status'] == 'completed':
                self.active_jobs[job_id]['status'] = 'completed'
                self.active_jobs[job_id]['video_url'] = status_result.get('video_url')
                self.active_jobs[job_id]['completed_at'] = datetime.now().isoformat()
            
            return {
                "job_id": job_id,
                "status": status_result['status'],
                "progress": status_result.get('progress', 0),
                "video_url": status_result.get('video_url'),
                "duration": status_result.get('duration'),
                "resolution": status_result.get('resolution'),
                "file_size_mb": status_result.get('file_size_mb'),
                "estimated_completion": status_result.get('estimated_completion')
            }
            
        except Exception as e:
            logger.error(f"Error getting enhancement status: {e}")
            raise Exception(f"Status check failed: {str(e)}")
    
    async def cancel_enhancement(self, job_id: str) -> bool:
        """Cancel an ongoing enhancement job"""
        try:
            if job_id not in self.active_jobs:
                raise Exception("Job not found")
            
            job_info = self.active_jobs[job_id]
            veo_job_id = job_info.get('veo_job_id')
            
            # Cancel the Veo job
            success = await self.veo_client.cancel_job(job_id, veo_job_id)
            
            if success:
                # Update job status
                self.active_jobs[job_id]['status'] = 'cancelled'
                self.active_jobs[job_id]['cancelled_at'] = datetime.now().isoformat()
            
            return success
            
        except Exception as e:
            logger.error(f"Error cancelling enhancement: {e}")
            return False
    
    async def get_available_templates(self) -> Dict[str, Any]:
        """Get available video generation templates"""
        return {
            "templates": VEO_PROMPT_TEMPLATES,
            "count": len(VEO_PROMPT_TEMPLATES)
        }
    
    async def get_available_backgrounds(self) -> Dict[str, Any]:
        """Get available background settings"""
        return {
            "backgrounds": VEO_BACKGROUND_SETTINGS,
            "count": len(VEO_BACKGROUND_SETTINGS)
        }
    
    async def get_user_job_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's job history"""
        user_jobs = [
            job for job in self.active_jobs.values() 
            if job.get('user_id') == user_id
        ]
        
        # Sort by creation time (most recent first)
        user_jobs.sort(
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        
        return user_jobs[:limit]
    
    def _map_background_type(self, background_type: str) -> str:
        """Map AI_BACKGROUNDS to VEO_BACKGROUND_SETTINGS"""
        background_mapping = {
            "mount_everest": "outdoor_natural",
            "boardroom": "conference_room",
            "office": "office_modern",
            "home": "home_office",
            "studio": "studio_backdrop",
            "creative": "creative_space",
            "professional": "office_modern",
            "casual": "home_office",
            "outdoor": "outdoor_natural"
        }
        
        return background_mapping.get(background_type, "office_modern")
    
    async def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs to prevent memory issues"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            jobs_to_remove = []
            for job_id, job_info in self.active_jobs.items():
                completed_at = job_info.get('completed_at')
                cancelled_at = job_info.get('cancelled_at')
                
                if completed_at or cancelled_at:
                    job_time_str = completed_at or cancelled_at
                    try:
                        job_time = datetime.fromisoformat(job_time_str)
                        if job_time < cutoff_time:
                            jobs_to_remove.append(job_id)
                    except (ValueError, TypeError):
                        # If we can't parse the date, remove old job
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.active_jobs[job_id]
            
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
            
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {e}")

# Service instance
ai_service = AIEnhancementService()

