"""
Constants for AI video enhancement
"""

# Available AI backgrounds
AI_BACKGROUNDS = {
    "mount_everest": {
        "name": "Mount Everest",
        "description": "Snow-capped peaks with blowing snow",
        "category": "nature",
        "prompt": "snow covered mountain peaks, blizzard, himalayan landscape"
    },
    "boardroom": {
        "name": "Executive Boardroom", 
        "description": "Professional glass conference room",
        "category": "professional",
        "prompt": "modern glass conference room, city skyline, professional lighting"
    },
    "space_station": {
        "name": "Space Station",
        "description": "Floating in orbit with Earth below", 
        "category": "futuristic",
        "prompt": "space station interior, earth view, zero gravity, sci-fi"
    },
    "jungle": {
        "name": "Jungle Adventure",
        "description": "Dense rainforest with wildlife sounds",
        "category": "nature", 
        "prompt": "dense rainforest, tropical plants, wildlife, adventure"
    },
    "ocean": {
        "name": "Ocean Depths",
        "description": "Underwater scene with coral reef",
        "category": "nature",
        "prompt": "underwater coral reef, tropical fish, clear blue water"
    }
}

# Enhancement status options
ENHANCEMENT_STATUS = {
    "PENDING": "pending",
    "PROCESSING": "processing", 
    "COMPLETED": "completed",
    "FAILED": "failed"
}

# Supported video formats for mobile
MOBILE_VIDEO_FORMATS = ["webm", "mp4", "mov"]
MOBILE_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MOBILE_MAX_DURATION = 10  # seconds

# Video processing constants
VIDEO_FORMATS = ["mp4", "webm", "mov", "avi"]
MAX_VIDEO_DURATION = 10  # seconds
MIN_VIDEO_DURATION = 1   # seconds

# AI processing constants
DEFAULT_AI_TIMEOUT = 300  # 5 minutes
MAX_CONCURRENT_JOBS = 5
