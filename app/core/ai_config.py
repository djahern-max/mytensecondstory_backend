"""
AI Configuration for Google Veo 3 integration
"""
import os
from typing import Dict, Any

class AISettings:
    """Configuration settings for AI services"""
    
    def __init__(self):
        # Google Cloud Configuration
        self.google_cloud_project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "your-project-id")
        self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Veo 3 Configuration
        self.veo_api_endpoint = os.getenv("VEO_API_ENDPOINT", "https://aiplatform.googleapis.com")
        self.veo_model_name = os.getenv("VEO_MODEL_NAME", "veo-3")
        
        # Job Management
        self.max_concurrent_jobs = int(os.getenv("AI_MAX_CONCURRENT_JOBS", "3"))
        self.default_video_duration = int(os.getenv("DEFAULT_VIDEO_DURATION", "10"))
        self.max_video_duration = int(os.getenv("MAX_VIDEO_DURATION", "30"))
        
        # Timeouts (in seconds)
        self.video_generation_timeout = int(os.getenv("VIDEO_GENERATION_TIMEOUT", "300"))
        self.enhancement_timeout = int(os.getenv("ENHANCEMENT_TIMEOUT", "180"))
        
        # Storage
        self.temp_video_storage_path = os.getenv("TEMP_VIDEO_STORAGE_PATH", "/tmp/videos")
        
        # Ensure storage directory exists
        os.makedirs(self.temp_video_storage_path, exist_ok=True)

# Veo 3 Prompt Templates
VEO_PROMPT_TEMPLATES = {
    "professional_intro": {
        "base_prompt": "A professional person in business attire introducing themselves confidently",
        "description": "Professional introduction video with formal tone",
        "duration_range": (5, 30),
        "style": "corporate"
    },
    "casual_intro": {
        "base_prompt": "A friendly person casually introducing themselves in a relaxed manner",
        "description": "Casual introduction with friendly, approachable tone",
        "duration_range": (5, 30),
        "style": "casual"
    },
    "creative_intro": {
        "base_prompt": "A creative individual introducing themselves with artistic flair and energy",
        "description": "Creative introduction with artistic and energetic style",
        "duration_range": (5, 30),
        "style": "creative"
    },
    "explainer_video": {
        "base_prompt": "A knowledgeable presenter explaining a concept clearly and engagingly",
        "description": "Educational content with clear explanations",
        "duration_range": (10, 30),
        "style": "educational"
    },
    "testimonial": {
        "base_prompt": "A satisfied customer sharing their positive experience authentically",
        "description": "Customer testimonial with authentic delivery",
        "duration_range": (10, 30),
        "style": "testimonial"
    }
}

# Veo 3 Background Settings
VEO_BACKGROUND_SETTINGS = {
    "office_modern": {
        "description": "Modern office environment with clean lines and professional lighting",
        "style": "corporate",
        "lighting": "professional"
    },
    "office_classic": {
        "description": "Traditional office setting with warm, professional atmosphere",
        "style": "traditional",
        "lighting": "warm"
    },
    "home_office": {
        "description": "Comfortable home office with personal touches and natural lighting",
        "style": "casual",
        "lighting": "natural"
    },
    "conference_room": {
        "description": "Professional conference room with modern furnishing",
        "style": "corporate",
        "lighting": "professional"
    },
    "studio_backdrop": {
        "description": "Clean studio backdrop with professional lighting setup",
        "style": "studio",
        "lighting": "studio"
    },
    "outdoor_natural": {
        "description": "Natural outdoor setting with organic lighting and environment",
        "style": "natural",
        "lighting": "natural"
    },
    "creative_space": {
        "description": "Creative workspace with artistic elements and inspiring atmosphere",
        "style": "creative",
        "lighting": "artistic"
    }
}

# Global settings instance
ai_settings = AISettings()
