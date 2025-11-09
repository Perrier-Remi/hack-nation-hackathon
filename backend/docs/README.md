# Backend Documentation

## Quick Start

1. **[SCENE_BASED_PROCESSING.md](SCENE_BASED_PROCESSING.md)** - Scene detection and keyframe extraction
2. **[TRANSCRIPTION.md](TRANSCRIPTION.md)** - Audio transcription setup
3. **[SAFETY_CHECKS.md](SAFETY_CHECKS.md)** - Safety and ethics checking

## Architecture Overview

### Video Processing Pipeline

```
Video Input → Scene Detection → Keyframe Extraction → Audio Extraction → Transcription → Safety Check
```

### Core Components

1. **AudioProcessor** (`preprocessing/audio_processor.py`)
   - Scene detection using PySceneDetect
   - Keyframe extraction (5 per scene)
   - Audio extraction per scene

2. **TranscriptionService** (`analyzers/transcription_service.py`)
   - Transcribes audio using Google Gemini API
   - Generates structured transcripts with summaries
   - Automatic retry on failures

3. **SafetyChecker** (`analyzers/safety_checker.py`)
   - NSFW/violence detection on keyframes
   - Bias/stereotype detection in transcripts
   - Misleading claims verification
   - Comprehensive safety scoring

4. **VideoProcessor** (`preprocessing/video_processor.py`)
   - Frame sampling with blur detection
   - Extracts frames every 0.5 seconds
   - Skips blurry frames

## Features

- ✅ Intelligent scene detection
- ✅ Multiple keyframes per scene (5 frames)
- ✅ Audio extraction from video
- ✅ AI-powered transcription
- ✅ Safety and ethics checking
- ✅ NSFW/violence detection
- ✅ Bias and stereotype detection
- ✅ Misleading claims verification
- ✅ Structured data models
- ✅ Artifact management
- ✅ Smart caching for performance

## Testing

```bash
# Scene detection with audio
python3 test_processor.py

# Transcription
python3 test_transcription.py

# Safety checking
python3 test_safety_checker.py
```

## Cleanup

```bash
# Remove all artifacts
make clean-artifacts

# Remove all including cache
make clean-all
```

## Documentation Files

- **SCENE_BASED_PROCESSING.md** - Detailed scene detection documentation
- **TRANSCRIPTION.md** - Audio transcription setup guide
- **SAFETY_CHECKS.md** - Safety and ethics checking guide
- **README.md** - This file

## Environment Setup

Required environment variables in `.env`:

```
GOOGLE_AI_STUDIO_API_KEY=your_api_key_here
```

See [TRANSCRIPTION.md](TRANSCRIPTION.md) for detailed setup instructions.

## Dependencies

See `requirements.txt` for full list. Key dependencies:

- `scenedetect[opencv]` - Scene detection
- `google-generativeai` - Gemini API for transcription and safety checks
- `moviepy` - Video processing
- `pydub` - Audio manipulation
- `Pillow` - Image processing

---

**Last Updated**: November 2025

