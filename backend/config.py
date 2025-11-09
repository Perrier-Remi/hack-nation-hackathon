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

def validate_config():
    """Validate that required configuration is present"""
    if not GOOGLE_AI_STUDIO_API_KEY:
        raise ValueError(
            "GOOGLE_AI_STUDIO_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )
    return True

