# Veo 2 Video Enhancement

## Overview

The Veo 2 enhancement feature uses Google's officially documented `veo-2.0-generate-001` model to create upgraded versions of your video scenes based on the LLM recommendations generated during analysis.

## How It Works

1. **Upload & Analyze** – Send a video to `/analyze-video` (UI button or direct API call).
2. **Review Findings** – The pipeline saves scene keyframes, produces a transcript, and builds an LLM summary with recommended improvements.
3. **Enhance with Veo 2** – Click **“Enhance with Veo 2”** in the UI (or call `/enhance-video`) to generate enhanced clips using the follow-up prompt.
4. **Review Output** – Enhanced clips are written to `uploads/enhanced/{video_hash}/scene_XXXX_enhanced.mp4` along with a JSON summary.

## Key Features

- **Official Model** – Uses `veo-2.0-generate-001` (stable, documented parameters).
- **Configurable Output** – Choose aspect ratio (16:9 or 9:16), duration (5-8s), and number of variations (1-2).
- **Prompt-Driven** – Automatically crafts a cinematic prompt blending scene context with LLM recommendations.
- **Batch Workflow** – Enhances the first *N* scenes (default 3) in sequence, reusing cached frames and summaries.

## API Endpoint

### POST `/enhance-video`

**Request body**
```json
{
  "video_hash": "abc123def456",
  "max_scenes": 3,
  "aspect_ratio": "16:9",
  "duration_seconds": 6,
  "video_count": 1
}
```

**Response body**
```json
{
  "success": true,
  "video_hash": "abc123def456",
  "model": "veo-2.0-generate-001",
  "total_scenes_enhanced": 3,
  "successful": 3,
  "failed": 0,
  "aspect_ratio": "16:9",
  "duration_seconds": 6,
  "video_count": 1,
  "llm_follow_up_prompt": "Polish the lighting...",
  "enhancements": [
    {
      "scene_index": 0,
      "status": "generated",
      "prompt_used": "A cinematic, high-quality commercial video...",
      "reference_frames_count": 5,
      "aspect_ratio": "16:9",
      "duration_seconds": 6,
      "video_count": 1,
      "enhanced_video_path": "uploads/enhanced/abc123/scene_0000_enhanced.mp4",
      "file_size_mb": 12.7
    }
  ],
  "output_directory": "uploads/enhanced/abc123"
}
```

## UI Usage

1. Go to the **Video Analysis** tab.
2. Upload a video and wait for analysis to complete (LLM summary + follow-up prompt).
3. Choose the Veo 2 settings:
   - **Duration** (5–8 seconds)
   - **Aspect ratio** (16:9 or 9:16)
   - **Variations** (1 or 2 clips per scene)
4. Click **“Enhance with Veo 2”** and monitor progress.
5. Download the generated clips from `uploads/enhanced/{video_hash}`.

## Technical Details

- **Model**: `veo-2.0-generate-001`
- **Supported Parameters**:
  - `prompt` (required)
  - `aspectRatio` (`"16:9"`, `"9:16"`)
  - `durationSeconds` (`5`, `6`, `7`, `8`)
  - `numberOfVideos` (`1`, `2`)
- **Audio**: Generated automatically by Veo – no extra flags required.
- **Reference Images**: Currently not sent to the API (retained locally for future use).
- **Caching**: Uploads, transcripts, and analysis summaries are reused between runs.

## Configuration

Ensure your API key is configured once:
```bash
# backend/.env
GOOGLE_AI_STUDIO_API_KEY=your_api_key_here
```

## Manual Sanity Test

1. **Start the backend**  
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Analyze a sample video**  
   ```bash
   curl -X POST http://localhost:8000/analyze-video \
     -F "video=@/path/to/sample.mp4"
   ```
   Note the `video_hash` in the JSON response.

3. **Enhance with Veo 2**  
   ```bash
   curl -X POST http://localhost:8000/enhance-video \
     -H "Content-Type: application/json" \
     -d '{
       "video_hash": "abc123def456",
       "max_scenes": 2,
       "aspect_ratio": "16:9",
       "duration_seconds": 6,
       "video_count": 1
     }'
   ```

4. **Review output**  
   ```bash
   ls uploads/enhanced/abc123def456/
   cat uploads/enhanced/abc123def456/enhancement_results.json
   ```

> **Tip:** If you run into quota or network errors, retry with fewer scenes or shorter durations.

## Troubleshooting

- **“video_hash is required”** – Make sure the request payload includes `video_hash`.
- **“Video analysis not found”** – Run `/analyze-video` first; check that `uploads/analysis_{hash}.json` exists.
- **HTTP 500** – Inspect backend logs for detailed stack traces (most common cause: missing/invalid API key).
- **Slow generation** – Veo jobs are long-running; the backend polls until completion (expect 1–5 minutes per scene).

## Future Enhancements

- [ ] Optional starting image / video extension support
- [ ] Multiple scene selection within the UI
- [ ] Progress updates via WebSockets
- [ ] Post-processing previews directly in the browser

