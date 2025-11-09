# Cleanup Guide - Managing Generated Files

## Overview

The application generates several types of files during operation:
- **Videos**: Uploaded video files (stored by MD5 hash)
- **Audio**: Extracted audio from videos
- **Frames**: Keyframes extracted from scenes
- **Transcripts**: Generated transcripts (JSON and TXT)

## Smart File Reuse ✅

The application now **automatically reuses existing files** to save time and API costs:

1. **Video Files**: If the same video is uploaded again (based on MD5 hash), it won't be saved twice
2. **Audio Files**: Audio extraction is skipped if the audio already exists
3. **Transcripts**: If a transcript exists, it's returned immediately without calling the Gemini API

### How It Works

```
Upload Video (hash: abc123)
    ↓
Check: uploads/abc123.mp4 exists? → Yes: Reuse ✓ | No: Save
    ↓
Check: uploads/audio/abc123_audio.mp3 exists? → Yes: Reuse ✓ | No: Extract
    ↓
Check: uploads/transcripts/abc123_audio_transcript.json exists? → Yes: Return cached ✓ | No: Transcribe
```

### Visual Feedback

- **Backend logs**: Shows what's being reused vs. generated
  ```
  ✓ Video already exists: uploads/abc123.mp4
  ✓ Using existing audio: uploads/audio/abc123_audio.mp3
  ✓ Using existing transcript: uploads/transcripts/abc123_audio_transcript.json
  ```

- **Frontend**: Shows a blue banner when cached transcript is used
  ```
  ⚡ Using cached transcript (file already processed)
  ```

## Cleanup Commands

Use the Makefile for easy cleanup:

### Check Disk Usage

```bash
make list-artifacts
```

Shows disk space used by each category:
```
📊 Disk usage of generated files:

🎵 Audio files: 45M
🖼️  Frame files: 128M
📝 Transcripts: 2.1M
🎬 Videos: 67M

Total uploads directory: 242M
```

### Selective Cleanup

Clean specific categories while preserving others:

```bash
# Remove only audio files
make clean-audio

# Remove only extracted frames
make clean-frames

# Remove only transcripts
make clean-transcripts

# Remove only uploaded videos
make clean-videos
```

### Bulk Cleanup

```bash
# Remove audio + frames + transcripts (keeps videos)
make clean-artifacts

# Remove EVERYTHING including videos and Python cache
make clean-all
```

## Recommended Cleanup Strategy

### During Development

```bash
# Check what's taking space
make list-artifacts

# Clean artifacts but keep videos for testing
make clean-artifacts
```

### Before Deployment

```bash
# Clean everything for a fresh start
make clean-all
```

### Regular Maintenance

```bash
# Remove old transcripts if you've improved the prompts
make clean-transcripts

# Remove frames if you're not using scene analysis
make clean-frames
```

## Manual Cleanup

If you prefer manual control:

```bash
# Remove all audio
rm -rf uploads/audio/

# Remove all frames
rm -rf uploads/frames/

# Remove all transcripts
rm -rf uploads/transcripts/

# Remove specific video
rm uploads/abc123.mp4

# Find large files
du -h uploads/* | sort -hr | head -10
```

## File Regeneration

If you clean a file, it will be automatically regenerated on next request:

1. **Clean transcript**: Next upload will transcribe again (costs API credits)
2. **Clean audio**: Next upload will extract audio again (fast, no API cost)
3. **Clean video**: Next upload will save the video again

## Disk Space Optimization Tips

1. **Use cached transcripts**: Uploading the same video twice uses the cached transcript (instant + free)

2. **Clean frames if not needed**: Frame extraction creates many files
   ```bash
   make clean-frames
   ```

3. **Periodically remove old videos**:
   ```bash
   # Find videos older than 7 days
   find uploads -maxdepth 1 -name "*.mp4" -mtime +7 -ls
   
   # Delete them
   find uploads -maxdepth 1 -name "*.mp4" -mtime +7 -delete
   ```

4. **Keep transcripts, clean everything else**:
   ```bash
   make clean-audio
   make clean-frames
   make clean-videos
   ```

## .gitignore Configuration

The following are already ignored in git:

```
uploads/audio/
uploads/frames/
uploads/transcripts/
audio/
transcripts/
*.mp3
*.mp4
*.webm
.env
```

This means generated files won't be committed to version control.

## Storage Estimates

Approximate sizes per 1-minute video:

- **Video (MP4)**: ~5-10 MB
- **Audio (MP3)**: ~1-2 MB
- **Frames** (5 per scene, ~10 scenes): ~500 KB
- **Transcript** (JSON + TXT): ~5-50 KB

### Example: 10-minute video
- Video: 50-100 MB
- Audio: 10-20 MB
- Frames: 5 MB
- Transcript: 50 KB
- **Total**: ~65-125 MB per video with all artifacts

## Automated Cleanup (Optional)

For production, consider adding a cron job:

```bash
# Add to crontab (clean artifacts older than 7 days, daily at 2 AM)
0 2 * * * cd /path/to/backend && make clean-artifacts
```

Or use a cleanup script:

```python
# cleanup_old_files.py
import os
import time

DAYS_OLD = 7
UPLOADS_DIR = "uploads"

cutoff = time.time() - (DAYS_OLD * 86400)

for root, dirs, files in os.walk(UPLOADS_DIR):
    for file in files:
        filepath = os.path.join(root, file)
        if os.path.getmtime(filepath) < cutoff:
            os.remove(filepath)
            print(f"Deleted: {filepath}")
```

## Summary

✅ **Files are now reused automatically** - no duplicate processing  
✅ **Granular cleanup commands** - clean what you need  
✅ **Disk usage monitoring** - `make list-artifacts`  
✅ **Safe defaults** - `clean-artifacts` keeps videos for testing  

**Best practice**: Run `make list-artifacts` weekly and `make clean-artifacts` when space is low.

