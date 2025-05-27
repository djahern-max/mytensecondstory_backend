"""
Video management routes for MyTenSecondStory
Handles video CRUD operations, sharing, and metadata management
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    BackgroundTasks,
    Query,
)
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.video import Video
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoListResponse,
    ShareLinkCreate,
)
from app.services.storage import storage_service
from app.services.ai_service import ai_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new video file"""

    try:
        # Upload to storage service
        upload_result = await storage_service.upload_video(
            file=file, user_id=str(current_user.id), metadata=metadata
        )

        # Create video record in database
        video_data = VideoCreate(
            title=file.filename or "Untitled Video",
            description="",
            file_path=upload_result["file_path"],
            file_size=upload_result["file_size"],
            duration=upload_result.get("duration", 0),
            width=upload_result.get("width", 0),
            height=upload_result.get("height", 0),
            fps=upload_result.get("fps", 30),
            thumbnail_path=upload_result.get("thumbnail_path"),
            file_hash=upload_result["file_hash"],
            metadata_=upload_result.get("metadata", {}),
        )

        db_video = Video(**video_data.dict(), user_id=current_user.id, status="ready")

        db.add(db_video)
        db.commit()
        db.refresh(db_video)

        # Generate video access URLs
        video_url = storage_service.get_file_url(db_video.file_path)
        thumbnail_url = (
            storage_service.get_file_url(db_video.thumbnail_path)
            if db_video.thumbnail_path
            else None
        )

        response_data = VideoResponse(
            id=db_video.id,
            title=db_video.title,
            description=db_video.description,
            duration=db_video.duration,
            width=db_video.width,
            height=db_video.height,
            fps=db_video.fps,
            file_size=db_video.file_size,
            status=db_video.status,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            created_at=db_video.created_at,
            updated_at=db_video.updated_at,
            metadata=db_video.metadata_,
        )

        logger.info(
            f"Video uploaded successfully: {db_video.id} by user {current_user.id}"
        )
        return response_data

    except Exception as e:
        logger.error(f"Video upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/my-videos", response_model=VideoListResponse)
async def get_user_videos(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's videos with pagination"""

    try:
        query = db.query(Video).filter(Video.user_id == current_user.id)

        if status:
            query = query.filter(Video.status == status)

        query = query.order_by(Video.created_at.desc())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        videos = query.offset(offset).limit(limit).all()

        # Convert to response format
        video_responses = []
        for video in videos:
            video_url = storage_service.get_file_url(video.file_path)
            thumbnail_url = (
                storage_service.get_file_url(video.thumbnail_path)
                if video.thumbnail_path
                else None
            )

            video_responses.append(
                VideoResponse(
                    id=video.id,
                    title=video.title,
                    description=video.description,
                    duration=video.duration,
                    width=video.width,
                    height=video.height,
                    fps=video.fps,
                    file_size=video.file_size,
                    status=video.status,
                    video_url=video_url,
                    thumbnail_url=thumbnail_url,
                    created_at=video.created_at,
                    updated_at=video.updated_at,
                    metadata=video.metadata_,
                )
            )

        return VideoListResponse(
            videos=video_responses,
            total=total,
            page=page,
            limit=limit,
            pages=max(1, (total + limit - 1) // limit),
        )

    except Exception as e:
        logger.error(f"Failed to get user videos: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve videos")


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific video by ID"""

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id, Video.user_id == current_user.id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Generate access URLs
        video_url = storage_service.get_file_url(video.file_path)
        thumbnail_url = (
            storage_service.get_file_url(video.thumbnail_path)
            if video.thumbnail_path
            else None
        )

        return VideoResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            duration=video.duration,
            width=video.width,
            height=video.height,
            fps=video.fps,
            file_size=video.file_size,
            status=video.status,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            created_at=video.created_at,
            updated_at=video.updated_at,
            metadata=video.metadata_,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve video")


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: str,
    video_update: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update video metadata"""

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id, Video.user_id == current_user.id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Update fields
        update_data = video_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(video, field, value)

        video.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(video)

        # Generate access URLs
        video_url = storage_service.get_file_url(video.file_path)
        thumbnail_url = (
            storage_service.get_file_url(video.thumbnail_path)
            if video.thumbnail_path
            else None
        )

        return VideoResponse(
            id=video.id,
            title=video.title,
            description=video.description,
            duration=video.duration,
            width=video.width,
            height=video.height,
            fps=video.fps,
            file_size=video.file_size,
            status=video.status,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            created_at=video.created_at,
            updated_at=video.updated_at,
            metadata=video.metadata_,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update video")


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a video"""

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id, Video.user_id == current_user.id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Store file paths for cleanup
        file_path = video.file_path
        thumbnail_path = video.thumbnail_path

        # Delete from database
        db.delete(video)
        db.commit()

        # Schedule file cleanup in background
        background_tasks.add_task(cleanup_video_files, file_path, thumbnail_path)

        logger.info(f"Video deleted: {video_id} by user {current_user.id}")
        return {"message": "Video deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete video")


@router.post("/{video_id}/share")
async def create_share_link(
    video_id: str,
    share_data: ShareLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a shareable link for a video"""

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id, Video.user_id == current_user.id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Generate share token
        share_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=share_data.expires_in)

        # Create share link
        share_link = {
            "token": share_token,
            "video_id": video_id,
            "expires_at": expires_at.isoformat(),
            "password_protected": share_data.password_protected,
            "allow_download": share_data.allow_download,
            "created_by": current_user.id,
        }

        # Store in video metadata (in a real app, you'd have a separate shares table)
        if not video.metadata_:
            video.metadata_ = {}

        if "share_links" not in video.metadata_:
            video.metadata_["share_links"] = []

        video.metadata_["share_links"].append(share_link)
        video.updated_at = datetime.utcnow()

        db.commit()

        # Generate shareable URL
        share_url = f"{settings.BASE_URL}/share/{share_token}"

        return {
            "share_url": share_url,
            "token": share_token,
            "expires_at": expires_at.isoformat(),
            "password_protected": share_data.password_protected,
            "allow_download": share_data.allow_download,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create share link for video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream video content"""

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id, Video.user_id == current_user.id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Generate streaming URL
        stream_url = storage_service.get_file_url(video.file_path, expires_in=3600)

        return {"stream_url": stream_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream video")


@router.get("/{video_id}/thumbnail")
async def get_video_thumbnail(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get video thumbnail"""

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id, Video.user_id == current_user.id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if not video.thumbnail_path:
            raise HTTPException(status_code=404, detail="Thumbnail not available")

        # Generate thumbnail URL
        thumbnail_url = storage_service.get_file_url(
            video.thumbnail_path, expires_in=3600
        )

        return {"thumbnail_url": thumbnail_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get thumbnail for video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get thumbnail")


@router.post("/{video_id}/enhance")
async def enhance_video(
    video_id: str,
    enhancement_request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start AI enhancement job for a video"""

    try:
        video = (
            db.query(Video)
            .filter(Video.id == video_id, Video.user_id == current_user.id)
            .first()
        )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Start enhancement job
        job_result = await ai_service.enhance_video_background(
            video_path=video.file_path,
            enhancement_type=enhancement_request.get("type", "background"),
            options=enhancement_request.get("options", {}),
        )

        return {
            "job_id": job_result["job_id"],
            "status": "started",
            "message": "Enhancement job started successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start enhancement for video {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start enhancement")


@router.get("/stats/overview")
async def get_video_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get user's video statistics"""

    try:
        total_videos = db.query(Video).filter(Video.user_id == current_user.id).count()

        # Videos by status
        ready_videos = (
            db.query(Video)
            .filter(Video.user_id == current_user.id, Video.status == "ready")
            .count()
        )

        processing_videos = (
            db.query(Video)
            .filter(Video.user_id == current_user.id, Video.status == "processing")
            .count()
        )

        # Total storage used
        total_size = (
            db.query(db.func.sum(Video.file_size))
            .filter(Video.user_id == current_user.id)
            .scalar()
            or 0
        )

        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_videos = (
            db.query(Video)
            .filter(
                Video.user_id == current_user.id, Video.created_at >= seven_days_ago
            )
            .count()
        )

        return {
            "total_videos": total_videos,
            "ready_videos": ready_videos,
            "processing_videos": processing_videos,
            "total_storage_bytes": int(total_size),
            "total_storage_mb": round(total_size / (1024 * 1024), 2),
            "recent_videos": recent_videos,
        }

    except Exception as e:
        logger.error(f"Failed to get video stats for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video statistics")


# Background task for file cleanup
async def cleanup_video_files(file_path: str, thumbnail_path: Optional[str] = None):
    """Background task to clean up video files"""

    try:
        # Delete main video file
        if file_path:
            await storage_service.delete_file(file_path)

        # Delete thumbnail if exists
        if thumbnail_path:
            await storage_service.delete_file(thumbnail_path)

        logger.info(f"Cleaned up video files: {file_path}, {thumbnail_path}")

    except Exception as e:
        logger.error(f"Failed to cleanup video files: {e}")


# Public route for shared videos (no authentication required)
@router.get("/public/share/{share_token}")
async def get_shared_video(
    share_token: str,
    password: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Access a shared video via token"""

    try:
        # Find video with this share token
        video = db.query(Video).filter(Video.metadata_.op("?")("share_links")).all()

        target_video = None
        share_link = None

        for v in video:
            if v.metadata_ and "share_links" in v.metadata_:
                for link in v.metadata_["share_links"]:
                    if link.get("token") == share_token:
                        target_video = v
                        share_link = link
                        break
                if target_video:
                    break

        if not target_video or not share_link:
            raise HTTPException(status_code=404, detail="Share link not found")

        # Check if expired
        expires_at = datetime.fromisoformat(share_link["expires_at"])
        if datetime.utcnow() > expires_at:
            raise HTTPException(status_code=410, detail="Share link has expired")

        # Check password if required
        if share_link.get("password_protected") and not password:
            raise HTTPException(status_code=401, detail="Password required")

        # Generate access URLs
        video_url = storage_service.get_file_url(target_video.file_path)
        thumbnail_url = (
            storage_service.get_file_url(target_video.thumbnail_path)
            if target_video.thumbnail_path
            else None
        )

        return {
            "id": target_video.id,
            "title": target_video.title,
            "description": target_video.description,
            "duration": target_video.duration,
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "allow_download": share_link.get("allow_download", True),
            "created_at": target_video.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get shared video {share_token}: {e}")
        raise HTTPException(status_code=500, detail="Failed to access shared video")
