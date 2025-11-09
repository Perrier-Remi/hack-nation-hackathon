"""
Configuration management for the backend application
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google AI Studio API Key
GOOGLE_AI_STUDIO_API_KEY = os.getenv('GOOGLE_AI_STUDIO_API_KEY')

# Transcription settings
GEMINI_MODEL = 'gemini-2.5-flash'  # Best model for audio transcription
TRANSCRIPTION_OUTPUT_DIR = 'transcripts'

# Safety checker settings
SAFETY_OUTPUT_DIR = 'uploads/safety'
SAFETY_SEVERITY_THRESHOLDS = {
    'safe': 80,     # Score >= 80 is safe
    'warning': 60,  # Score >= 60 is warning
    'unsafe': 0     # Score < 60 is unsafe
}

# Misleading claims keywords
MISLEADING_KEYWORDS = [
    "guaranteed", "guarantee", "cure", "cures", "miracle", "miraculous",
    "100%", "never fails", "always works", "proven", "scientifically proven",
    "FDA approved", "clinically tested", "instant results", "overnight",
    "secret formula", "doctors hate", "one weird trick", "lose weight fast"
]

def validate_config():
    """Validate that required configuration is present"""
    if not GOOGLE_AI_STUDIO_API_KEY:
        raise ValueError(
            "GOOGLE_AI_STUDIO_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )
    return True

