"""
Background Template model for managing AI background templates
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class BackgroundCategory(str, enum.Enum):
    """Background categories for networking contexts"""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    IMPRESSIVE = "impressive"
    CREATIVE = "creative"
    OUTDOOR = "outdoor"


class BackgroundTemplate(Base):
    """Model for AI background templates"""

    __tablename__ = "background_templates"

    # Primary fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)

    # Template details
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False, index=True)  # BackgroundCategory

    # File paths
    preview_image_path = Column(String, nullable=True)  # Preview thumbnail
    template_image_path = Column(String, nullable=True)  # Full resolution template
    mask_image_path = Column(
        String, nullable=True
    )  # Optional mask for advanced processing

    # Display properties
    display_order = Column(Integer, default=0)  # For sorting in UI
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)

    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Success rate of enhancements
    average_rating = Column(Float, default=0.0)  # User ratings

    # Technical specifications
    recommended_resolution = Column(String, default="1280x720")
    aspect_ratio = Column(String, default="16:9")
    color_profile = Column(String, default="sRGB")

    # AI processing settings
    ai_model_version = Column(String, nullable=True)
    processing_complexity = Column(Integer, default=1)  # 1-5 scale
    estimated_processing_time = Column(Float, default=30.0)  # seconds

    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tags for searching
    settings = Column(JSON, nullable=True)  # Template-specific settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BackgroundTemplate(id={self.id}, name={self.name}, category={self.category})>"

    @property
    def is_available(self) -> bool:
        """Check if template is available for use"""
        return self.is_active and bool(self.template_image_path)

    @property
    def networking_score(self) -> float:
        """Calculate networking appropriateness score"""
        base_score = 0.5

        # Category-based scoring
        category_scores = {
            BackgroundCategory.PROFESSIONAL: 1.0,
            BackgroundCategory.CASUAL: 0.7,
            BackgroundCategory.IMPRESSIVE: 0.8,
            BackgroundCategory.CREATIVE: 0.6,
            BackgroundCategory.OUTDOOR: 0.5,
        }

        category_score = category_scores.get(self.category, 0.5)

        # Usage-based scoring
        usage_score = min(1.0, self.usage_count / 1000.0)  # Normalize to 0-1

        # Rating-based scoring
        rating_score = self.average_rating / 5.0 if self.average_rating > 0 else 0.5

        # Combined score
        final_score = (
            (category_score * 0.5) + (usage_score * 0.2) + (rating_score * 0.3)
        )

        return min(1.0, final_score)

    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.updated_at = datetime.utcnow()

    def update_success_rate(self, successful: bool):
        """Update success rate based on enhancement result"""
        if self.usage_count > 0:
            current_successes = self.success_rate * self.usage_count
            new_successes = current_successes + (1 if successful else 0)
            self.success_rate = new_successes / self.usage_count
        else:
            self.success_rate = 1.0 if successful else 0.0

        self.updated_at = datetime.utcnow()

    def add_rating(self, rating: float):
        """Add user rating (1-5 scale)"""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # Simple moving average for now
        # In production, you might want a more sophisticated rating system
        if self.average_rating == 0:
            self.average_rating = rating
        else:
            # Weight new ratings slightly less to prevent manipulation
            self.average_rating = (self.average_rating * 0.9) + (rating * 0.1)

        self.updated_at = datetime.utcnow()

    def get_processing_estimate(self, video_duration: float = 10.0) -> float:
        """Get estimated processing time for this template"""
        base_time = self.estimated_processing_time
        complexity_multiplier = 1.0 + (self.processing_complexity - 1) * 0.5
        duration_multiplier = video_duration / 10.0  # Normalize to 10 seconds

        return base_time * complexity_multiplier * duration_multiplier

    def to_dict(self, include_stats: bool = False) -> dict:
        """Convert template to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "category": self.category,
            "preview_image_path": self.preview_image_path,
            "is_featured": self.is_featured,
            "is_premium": self.is_premium,
            "recommended_resolution": self.recommended_resolution,
            "aspect_ratio": self.aspect_ratio,
            "tags": self.tags or [],
            "networking_score": self.networking_score,
            "estimated_processing_time": self.estimated_processing_time,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if include_stats:
            data.update(
                {
                    "usage_count": self.usage_count,
                    "success_rate": self.success_rate,
                    "average_rating": self.average_rating,
                    "processing_complexity": self.processing_complexity,
                }
            )

        return data

    @classmethod
    def get_networking_templates(cls, session, limit: int = 20):
        """Get templates optimized for networking"""
        return (
            session.query(cls)
            .filter(
                cls.is_active == True,
                cls.category.in_(
                    [
                        BackgroundCategory.PROFESSIONAL,
                        BackgroundCategory.IMPRESSIVE,
                        BackgroundCategory.CASUAL,
                    ]
                ),
            )
            .order_by(
                cls.is_featured.desc(),
                cls.usage_count.desc(),
                cls.average_rating.desc(),
            )
            .limit(limit)
            .all()
        )

    @classmethod
    def get_by_category(cls, session, category: BackgroundCategory, limit: int = 10):
        """Get templates by category"""
        return (
            session.query(cls)
            .filter(cls.is_active == True, cls.category == category)
            .order_by(cls.display_order.asc(), cls.usage_count.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def search_templates(
        cls, session, query: str, category: str = None, limit: int = 20
    ):
        """Search templates by name, description, or tags"""
        q = session.query(cls).filter(cls.is_active == True)

        if query:
            search_filter = cls.name.ilike(f"%{query}%") | cls.description.ilike(
                f"%{query}%"
            )
            q = q.filter(search_filter)

        if category:
            q = q.filter(cls.category == category)

        return (
            q.order_by(cls.networking_score.desc(), cls.usage_count.desc())
            .limit(limit)
            .all()
        )


# Seed data for networking backgrounds
NETWORKING_BACKGROUND_SEEDS = [
    {
        "name": "Professional Office",
        "slug": "professional-office",
        "description": "Modern office environment perfect for business networking",
        "category": BackgroundCategory.PROFESSIONAL,
        "is_featured": True,
        "tags": ["office", "business", "professional", "modern"],
        "display_order": 1,
        "recommended_resolution": "1280x720",
        "estimated_processing_time": 25.0,
        "processing_complexity": 2,
    },
    {
        "name": "Conference Room",
        "slug": "conference-room",
        "description": "Elegant conference room setting for executive presence",
        "category": BackgroundCategory.PROFESSIONAL,
        "is_featured": True,
        "tags": ["conference", "meeting", "executive", "formal"],
        "display_order": 2,
        "estimated_processing_time": 30.0,
        "processing_complexity": 3,
    },
    {
        "name": "City Skyline",
        "slug": "city-skyline",
        "description": "Impressive urban skyline backdrop for impact",
        "category": BackgroundCategory.IMPRESSIVE,
        "is_featured": True,
        "tags": ["city", "skyline", "urban", "impressive"],
        "display_order": 3,
        "estimated_processing_time": 35.0,
        "processing_complexity": 4,
    },
    {
        "name": "Modern Café",
        "slug": "modern-cafe",
        "description": "Casual yet professional café atmosphere",
        "category": BackgroundCategory.CASUAL,
        "tags": ["cafe", "casual", "friendly", "approachable"],
        "display_order": 4,
        "estimated_processing_time": 20.0,
        "processing_complexity": 2,
    },
    {
        "name": "Library Study",
        "slug": "library-study",
        "description": "Sophisticated library setting for thought leadership",
        "category": BackgroundCategory.PROFESSIONAL,
        "tags": ["library", "books", "intellectual", "sophisticated"],
        "display_order": 5,
        "estimated_processing_time": 28.0,
        "processing_complexity": 3,
    },
    {
        "name": "Tech Startup",
        "slug": "tech-startup",
        "description": "Modern tech office environment",
        "category": BackgroundCategory.CREATIVE,
        "tags": ["tech", "startup", "innovation", "modern"],
        "display_order": 6,
        "estimated_processing_time": 30.0,
        "processing_complexity": 3,
    },
    {
        "name": "Home Office",
        "slug": "home-office",
        "description": "Professional home office setup",
        "category": BackgroundCategory.CASUAL,
        "tags": ["home", "office", "remote", "comfortable"],
        "display_order": 7,
        "estimated_processing_time": 22.0,
        "processing_complexity": 2,
    },
    {
        "name": "Minimalist Studio",
        "slug": "minimalist-studio",
        "description": "Clean, minimalist background for focus",
        "category": BackgroundCategory.PROFESSIONAL,
        "tags": ["minimalist", "clean", "simple", "focus"],
        "display_order": 8,
        "estimated_processing_time": 18.0,
        "processing_complexity": 1,
    },
]
