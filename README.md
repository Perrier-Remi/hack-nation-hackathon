# Ad Scoring & Transcription Tool

> AI-powered video analysis and transcription platform for advertising content

## Features

✅ **Video Analysis** - Intelligent ad scoring and critique  
✅ **Scene Detection** - Automatic scene boundaries with keyframe extraction  
✅ **Audio Transcription** - AI-powered transcription using Google Gemini  
✅ **Smart Caching** - Automatic file reuse to save time and API costs  
✅ **Tab Navigation** - Seamless switching between analysis and transcription

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Google AI Studio API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd hack-nation-hackathon

# 2. Backend setup
cd backend
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_AI_STUDIO_API_KEY=your_api_key_here" > .env

# 3. Frontend setup
cd ../frontend
npm install

# 4. Start both servers
cd ../backend
uvicorn main:app --reload --port 8000

# In another terminal
cd frontend
npm run dev
```

Visit **http://localhost:5173** to use the application.

## Architecture

### Video Processing Pipeline

```
Video Upload
    ↓
Scene Detection (PySceneDetect)
    ↓
├─ Extract 5 Keyframes per Scene
├─ Extract Audio per Scene
└─ Full Audio Extraction
    ↓
AI Transcription (Google Gemini)
    ↓
Structured Output (Transcript + Summary + Key Points)
```

### Smart Caching System

The application intelligently reuses existing files:

- **Videos**: MD5-based deduplication
- **Audio**: Skips extraction if exists
- **Transcripts**: Returns cached results instantly

**Performance Impact:**
- First upload: ~60 seconds
- Cached upload: <1 second ⚡
- **API cost savings: 50%**

## API Endpoints

### POST /transcript
Transcribe audio from video

```bash
curl -X POST http://localhost:8000/transcript \
  -F "video=@path/to/video.mp4"
```

**Response:**
```json
{
  "success": true,
  "transcript": "Full transcript text...",
  "summary": "Brief summary of content...",
  "key_points": ["point 1", "point 2", ...],
  "language": "English",
  "word_count": 523,
  "cached": false,
  "transcript_path": "uploads/transcripts/..."
}
```

### POST /analyze-video
Analyze video for ad scoring

```bash
curl -X POST http://localhost:8000/analyze-video \
  -F "video=@path/to/video.mp4"
```

## File Management

### Check Disk Usage

```bash
cd backend
make list-artifacts
```

Output:
```
📊 Disk usage of generated files:
🎵 Audio files: 1.3M
🖼️  Frame files: 2.8M
📝 Transcripts: 28K
🎬 Videos: 7.5M
```

### Cleanup Commands

```bash
# Remove processed files (keeps videos)
make clean-artifacts

# Remove only specific types
make clean-audio        # Audio files only
make clean-frames       # Frame files only
make clean-transcripts  # Transcript files only

# Remove everything
make clean-all

# Show all commands
make help
```

## Testing

```bash
cd backend

# Test scene detection and audio extraction
python3 test_processor.py

# Test transcription service
python3 test_transcription.py

# Test transcript API endpoint
python3 test_transcript_endpoint.py
```

## Project Structure

```
hack-nation-hackathon/
├── backend/
│   ├── analyzers/              # AI analyzers
│   │   ├── transcription_service.py
│   │   ├── ia_face_detector.py
│   │   └── censor.py
│   ├── preprocessing/          # Video/audio processing
│   │   ├── audio_processor.py  # Scene detection & audio
│   │   ├── video_processor.py  # Frame extraction
│   │   └── models.py           # Data models
│   ├── pipeline/               # Processing pipelines
│   ├── docs/                   # Technical documentation
│   │   ├── README.md           # Architecture overview
│   │   ├── SCENE_BASED_PROCESSING.md
│   │   └── TRANSCRIPTION.md
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Python dependencies
│   ├── Makefile                # Cleanup commands
│   └── CLEANUP_GUIDE.md        # File management guide
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main app with tabs
│   │   ├── Transcript.tsx      # Transcription UI
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md                   # This file
```

## Key Dependencies

### Backend
- **fastapi** - Web framework
- **scenedetect[opencv]** - Scene detection
- **google-generativeai** - Gemini API
- **moviepy** - Video processing
- **pydub** - Audio manipulation
- **Pillow** - Image processing

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool

## Environment Variables

Create `backend/.env`:

```bash
GOOGLE_AI_STUDIO_API_KEY=your_gemini_api_key_here
```

## Features in Detail

### Scene Detection
- Uses PySceneDetect's ContentDetector
- Adjustable sensitivity (default threshold: 27.0)
- Extracts 5 keyframes per scene (0%, 25%, 50%, 75%, 100%)
- Preserves scene audio segments

### Audio Transcription
- Powered by Google Gemini AI
- Generates structured output:
  - Full transcript
  - Content summary
  - Key points extraction
  - Language detection
- Automatic retry on failures
- Saves JSON and TXT formats

### Frontend UI
- Tab navigation between Analysis and Transcript
- Real-time upload progress
- Cached result indicators
- Beautiful results display
- Error handling with helpful messages

## Performance & Caching

### Cache Benefits

**Without caching:**
```
Request 1: 60s (upload + process + transcribe)
Request 2: 60s (duplicate processing)
Total: 120s, 2 API calls
```

**With caching:**
```
Request 1: 60s (full processing)
Request 2: <1s (instant cached response! ⚡)
Total: 61s, 1 API call
Savings: 98% faster, 50% fewer API calls
```

### Cache Indicators

- **Backend logs:** `✓ Using existing transcript`
- **Frontend UI:** Blue banner with ⚡ icon
- **API response:** `"cached": true`

## Development

### Running Tests

```bash
cd backend

# All tests
python3 test_processor.py
python3 test_transcription.py
python3 test_transcript_endpoint.py
```

### Linting

```bash
# Backend (if configured)
cd backend
pylint analyzers/ preprocessing/ pipeline/

# Frontend
cd frontend
npm run lint
```

### Adding New Features

1. **Backend:** Add to appropriate module (analyzers, preprocessing, pipeline)
2. **Frontend:** Add component in src/
3. **Update docs:** backend/docs/ for technical details
4. **Add tests:** Create test_*.py files
5. **Update README:** Document new features here

## Troubleshooting

### "Connection Error"
Ensure backend is running on port 8000:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### "API key not found"
Check `.env` file exists and contains valid key:
```bash
cat backend/.env
```

### "Audio file not found"
Clean and retry:
```bash
make clean-audio
```

### CORS Errors
Backend allows localhost:3000 and localhost:5173. Update `main.py` CORS settings if using different port.

## Contributing

1. Create feature branch
2. Make changes
3. Run tests
4. Update documentation
5. Submit PR

## License

[Your license here]

## Support

For issues or questions, please [open an issue](link-to-issues).

---

**Built with:** Python • FastAPI • React • TypeScript • Google Gemini AI

**Last Updated:** November 2025
