# Backend Documentation

## Quick Start

1. **[SCENE_BASED_PROCESSING.md](SCENE_BASED_PROCESSING.md)** - Scene detection and keyframe extraction
2. **[TRANSCRIPTION.md](TRANSCRIPTION.md)** - Audio transcription setup

## Architecture Overview

### Video Processing Pipeline

```
Video Input → Scene Detection → Keyframe Extraction → Audio Extraction → Transcription
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

3. **VideoProcessor** (`preprocessing/video_processor.py`)
   - Frame sampling with blur detection
   - Extracts frames every 0.5 seconds
   - Skips blurry frames

## Features

- ✅ Intelligent scene detection
- ✅ Multiple keyframes per scene (5 frames)
- ✅ Audio extraction from video
- ✅ AI-powered transcription
- ✅ Structured data models
- ✅ Artifact management

## Testing

```bash
# Scene detection with audio
python3 test_processor.py

# Transcription
python3 test_transcription.py
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
- `google-generativeai` - Gemini API for transcription
- `moviepy` - Video processing
- `pydub` - Audio manipulation

---

**Last Updated**: November 2025

