"""
Enhancement Job model for tracking AI video processing jobs
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class JobStatus(str, enum.Enum):
    """Enhancement job status enumeration"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EnhancementType(str, enum.Enum):
    """Types of AI enhancements"""

    BACKGROUND = "background"
    APPEARANCE = "appearance"
    QUALITY = "quality"
    COMBINED = "combined"


class EnhancementJob(Base):
    """Model for tracking AI enhancement jobs"""

    __tablename__ = "enhancement_jobs"

    # Primary fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    video_id = Column(String, ForeignKey("videos.id"), nullable=True, index=True)

    # Job details
    job_type = Column(String, nullable=False)  # EnhancementType
    status = Column(String, default=JobStatus.PENDING, index=True)  # JobStatus
    priority = Column(Integer, default=0)  # Higher numbers = higher priority

    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    current_step = Column(String, nullable=True)
    total_steps = Column(Integer, default=1)
    completed_steps = Column(Integer, default=0)

    # Input/Output
    input_file_path = Column(String, nullable=True)
    output_file_path = Column(String, nullable=True)
    input_parameters = Column(JSON, nullable=True)  # Enhancement settings
    output_metadata = Column(JSON, nullable=True)  # Result metadata

    # Processing details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Resource usage
    estimated_duration = Column(Float, nullable=True)  # seconds
    actual_duration = Column(Float, nullable=True)  # seconds
    cpu_time = Column(Float, nullable=True)  # seconds
    memory_peak_mb = Column(Float, nullable=True)  # MB

    # Quality metrics
    quality_score_before = Column(Float, nullable=True)
    quality_score_after = Column(Float, nullable=True)
    enhancement_strength = Column(Float, default=1.0)  # 0.0 to 1.0

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # When to clean up temp files

    # Additional metadata
    metadata_ = Column("metadata", JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="enhancement_jobs")
    video = relationship("Video", back_populates="enhancement_jobs")

    def __repr__(self):
        return f"<EnhancementJob(id={self.id}, type={self.job_type}, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """Check if job is in a completed state"""
        return self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]

    @property
    def is_processing(self) -> bool:
        """Check if job is currently processing"""
        return self.status == JobStatus.PROCESSING

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.status == JobStatus.FAILED and self.retry_count < self.max_retries

    def update_progress(self, progress: float, step: str = None):
        """Update job progress"""
        self.progress = max(0.0, min(100.0, progress))
        if step:
            self.current_step = step
        self.updated_at = datetime.utcnow()

    def mark_started(self):
        """Mark job as started"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_completed(self, output_path: str = None, metadata: dict = None):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress = 100.0

        if output_path:
            self.output_file_path = output_path

        if metadata:
            self.output_metadata = metadata

        # Calculate processing time
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.processing_time_seconds = delta.total_seconds()

        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

        # Calculate processing time if started
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.processing_time_seconds = delta.total_seconds()

        self.updated_at = datetime.utcnow()

    def mark_cancelled(self):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_retry(self):
        """Increment retry count and reset for retry"""
        if self.can_retry:
            self.retry_count += 1
            self.status = JobStatus.PENDING
            self.error_message = None
            self.progress = 0.0
            self.current_step = None
            self.started_at = None
            self.completed_at = None
            self.updated_at = datetime.utcnow()
            return True
        return False

    def get_estimated_completion_time(self):
        """Get estimated completion time based on progress"""
        if not self.started_at or self.progress <= 0:
            return None

        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        if self.progress >= 100:
            return self.completed_at or datetime.utcnow()

        estimated_total_time = elapsed / (self.progress / 100)
        remaining_time = estimated_total_time - elapsed

        from datetime import timedelta

        return datetime.utcnow() + timedelta(seconds=remaining_time)

    def get_enhancement_summary(self) -> dict:
        """Get summary of enhancement results"""
        if not self.is_completed or self.status != JobStatus.COMPLETED:
            return {}

        summary = {
            "job_id": self.id,
            "enhancement_type": self.job_type,
            "processing_time": self.processing_time_seconds,
            "quality_improvement": None,
            "enhancements_applied": [],
            "file_paths": {
                "input": self.input_file_path,
                "output": self.output_file_path,
            },
        }

        # Calculate quality improvement
        if self.quality_score_before and self.quality_score_after:
            summary["quality_improvement"] = (
                self.quality_score_after - self.quality_score_before
            )

        # Extract applied enhancements from parameters
        if self.input_parameters:
            params = self.input_parameters

            if self.job_type == EnhancementType.BACKGROUND:
                summary["enhancements_applied"].append(
                    {
                        "type": "background_replacement",
                        "background": params.get("background_type"),
                        "intensity": params.get("intensity", 80),
                    }
                )

            elif self.job_type == EnhancementType.APPEARANCE:
                appearance_enhancements = []
                if params.get("skin_smoothing", 0) > 0:
                    appearance_enhancements.append(
                        f"Skin smoothing: {params['skin_smoothing']}%"
                    )
                if params.get("teeth_whitening", 0) > 0:
                    appearance_enhancements.append(
                        f"Teeth whitening: {params['teeth_whitening']}%"
                    )
                if params.get("eye_enhancement", 0) > 0:
                    appearance_enhancements.append(
                        f"Eye enhancement: {params['eye_enhancement']}%"
                    )

                summary["enhancements_applied"].extend(appearance_enhancements)

            elif self.job_type == EnhancementType.QUALITY:
                quality_enhancements = []
                if params.get("upscale_factor", 1) > 1:
                    quality_enhancements.append(f"Upscaled {params['upscale_factor']}x")
                if params.get("denoise"):
                    quality_enhancements.append("Noise reduction")
                if params.get("sharpen"):
                    quality_enhancements.append("Sharpening")

                summary["enhancements_applied"].extend(quality_enhancements)

        return summary

    def to_dict(self, include_metadata: bool = False) -> dict:
        """Convert job to dictionary representation"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "video_id": self.video_id,
            "job_type": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "processing_time_seconds": self.processing_time_seconds,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "estimated_completion": None,
        }

        # Add estimated completion time
        if self.is_processing:
            est_time = self.get_estimated_completion_time()
            if est_time:
                data["estimated_completion"] = est_time.isoformat()

        # Include detailed metadata if requested
        if include_metadata:
            data.update(
                {
                    "input_parameters": self.input_parameters,
                    "output_metadata": self.output_metadata,
                    "quality_score_before": self.quality_score_before,
                    "quality_score_after": self.quality_score_after,
                    "enhancement_summary": self.get_enhancement_summary(),
                    "resource_usage": {
                        "cpu_time": self.cpu_time,
                        "memory_peak_mb": self.memory_peak_mb,
                        "actual_duration": self.actual_duration,
                    },
                }
            )

        return data


# Add relationship to User model (add this to your User model)
# enhancement_jobs = relationship("EnhancementJob", back_populates="user", cascade="all, delete-orphan")

# Add relationship to Video model (add this to your Video model)
# enhancement_jobs = relationship("EnhancementJob", back_populates="video", cascade="all, delete-orphan")
