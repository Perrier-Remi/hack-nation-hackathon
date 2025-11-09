# Audio Transcription Setup

## Overview

Transcribe audio from videos using Google Gemini API.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Google AI Studio API Key

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

### 3. Configure Environment

Create a `.env` file in the backend directory:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
GOOGLE_AI_STUDIO_API_KEY=your_actual_api_key_here
```

**Important**: Never commit your `.env` file to git!

## Usage

### Test Transcription

```bash
python3 test_transcription.py
```

This will:
1. Extract audio from video
2. Transcribe audio using Gemini API
3. Save transcript as JSON and TXT

### Programmatic Usage

```python
from preprocessing.audio_processor import AudioProcessor
from analyzers.transcription_service import TranscriptionService

# Extract audio
processor = AudioProcessor("uploads/video.mp4")
video_data = processor.process(save_segments=False)

# Transcribe
service = TranscriptionService()
result = service.transcribe_audio("audio/video_audio.mp3")

print(result['transcript'])
```

## Output

Transcripts are saved in `transcripts/` directory:
- `{video_id}_audio_transcript.json` - Full structured data
- `{video_id}_audio_transcript.txt` - Plain text version

## API Costs

- **Free tier**: 60 requests per minute
- Check https://ai.google.dev/pricing for current rates

---

**Date**: November 2025

