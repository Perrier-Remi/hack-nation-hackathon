from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pipeline.video_pipeline import VideoPipeline
from preprocessing.audio_processor import AudioProcessor
from analyzers.transcription_service import TranscriptionService
import os
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Créer le dossier uploads s'il n'existe pas
os.makedirs("uploads", exist_ok=True)

@app.post("/analyze-video")
async def upload_video(video: UploadFile = File(...)):
    """
    Analyze video for ad scoring.
    Reuses existing video file if available.
    """
    # Calculate hash before saving
    content = await video.read()
    file_hash = hashlib.md5(content).hexdigest()
    video_path = f"uploads/{file_hash}.mp4"
    
    # Only save video if it doesn't exist
    if os.path.exists(video_path):
        print(f"✓ Video already exists: {video_path}")
    else:
        print(f"💾 Saving new video: {video_path}")
        with open(video_path, "wb") as buffer:
            buffer.write(content)
    
    video_pipeline = VideoPipeline(video_path)
    result = video_pipeline.run()
    
    return result

@app.post("/transcript")
async def transcribe_video(video: UploadFile = File(...)):
    """
    Transcribe audio from uploaded video using Gemini API.
    Reuses existing audio and transcript files if available.
    """
    video_path = None
    video_existed = False
    
    try:
        # Validate file type
        if not video.content_type or not video.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Calculate hash before saving
        content = await video.read()
        file_hash = hashlib.md5(content).hexdigest()
        video_path = f"uploads/{file_hash}.mp4"
        
        # Only save video if it doesn't exist
        if os.path.exists(video_path):
            print(f"✓ Video already exists: {video_path}")
            video_existed = True
        else:
            print(f"💾 Saving new video: {video_path}")
            with open(video_path, "wb") as buffer:
                buffer.write(content)
        
        # Setup paths
        base_dir = os.path.dirname(video_path) or "."
        audio_dir = os.path.join(base_dir, "audio")
        full_audio_path = os.path.join(audio_dir, f"{file_hash}_audio.mp3")
        output_dir = os.path.join(base_dir, "transcripts")
        transcript_path = os.path.join(output_dir, f"{file_hash}_audio_transcript.json")
        
        # Check if transcript already exists
        if os.path.exists(transcript_path):
            print(f"✓ Using existing transcript: {transcript_path}")
            import json
            with open(transcript_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            # Return cached transcript
            return JSONResponse(content={
                "success": True,
                "transcript": result.get('transcript', ''),
                "summary": result.get('summary', ''),
                "key_points": result.get('key_points', []),
                "language": result.get('language', 'unknown'),
                "word_count": len(result.get('transcript', '').split()),
                "transcript_path": transcript_path,
                "cached": True
            })
        
        # Extract audio if not exists
        if not os.path.exists(full_audio_path):
            print(f"🎵 Extracting audio from video...")
            audio_processor = AudioProcessor(video_path)
            video_data = audio_processor.process(save_segments=False, threshold=27.0)
            print(f"✓ Audio extracted: {full_audio_path}")
        else:
            print(f"✓ Using existing audio: {full_audio_path}")
        
        # Transcribe audio (only if transcript doesn't exist)
        print(f"🎙️  Transcribing audio...")
        transcription_service = TranscriptionService()
        
        result = transcription_service.transcribe_with_retry(
            full_audio_path,
            save_transcript=True,
            output_dir=output_dir,
            max_retries=2
        )
        
        # Return transcript with metadata
        return JSONResponse(content={
            "success": True,
            "transcript": result.get('transcript', ''),
            "summary": result.get('summary', ''),
            "key_points": result.get('key_points', []),
            "language": result.get('language', 'unknown'),
            "word_count": len(result.get('transcript', '').split()),
            "transcript_path": result.get('transcript_path', ''),
            "cached": False
        })
        
    except Exception as e:
        # Only clean up if we created the video in this request
        if not video_existed and video_path and os.path.exists(video_path):
            try:
                print(f"🧹 Cleaning up failed upload: {video_path}")
                os.remove(video_path)
            except:
                pass
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Transcription failed. Please check if GOOGLE_AI_STUDIO_API_KEY is set in .env file."
            }
        )

