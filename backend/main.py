from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pipeline.video_pipeline import VideoPipeline
from preprocessing.audio_processor import AudioProcessor
from analyzers.transcription_service import TranscriptionService
from analyzers.safety_checker import SafetyChecker
import os
import hashlib
import json
import glob

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

def get_video_extension(filename: str, content_type: str) -> str:
    """
    Get the appropriate video file extension.
    Supports .mp4 and .webm files.
    """
    # Try to get extension from filename
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.mp4', '.webm']:
            return ext
    
    # Fallback to content type
    if content_type:
        if 'webm' in content_type.lower():
            return '.webm'
        elif 'mp4' in content_type.lower():
            return '.mp4'
    
    # Default to .mp4
    return '.mp4'

def convert_webm_to_mp4(webm_path: str) -> str:
    """
    Convert WebM video to MP4 using ffmpeg for better compatibility.
    Returns the path to the converted MP4 file.
    """
    import subprocess
    
    mp4_path = webm_path.rsplit('.', 1)[0] + '.mp4'
    
    if os.path.exists(mp4_path):
        print(f"✓ MP4 conversion already exists: {mp4_path}")
        return mp4_path
    
    print(f"🔄 Converting WebM to MP4 for better compatibility...")
    
    try:
        # Use ffmpeg to convert with H.264 codec
        cmd = [
            'ffmpeg', '-i', webm_path,
            '-c:v', 'libx264',  # H.264 video codec
            '-c:a', 'aac',       # AAC audio codec
            '-strict', 'experimental',
            '-b:a', '192k',
            '-y',  # Overwrite output file
            mp4_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0 and os.path.exists(mp4_path):
            print(f"✓ Successfully converted to MP4: {mp4_path}")
            return mp4_path
        else:
            print(f"❌ Conversion failed: {result.stderr.decode()}")
            raise Exception(f"FFmpeg conversion failed: {result.stderr.decode()}")
            
    except subprocess.TimeoutExpired:
        raise Exception("Video conversion timed out (>2 minutes)")
    except FileNotFoundError:
        raise Exception("FFmpeg not found. Please install ffmpeg.")

@app.post("/analyze-video")
async def upload_video(video: UploadFile = File(...)):
    """
    Analyze video for ad scoring.
    Reuses existing video file if available.
    Includes scene detection and frame extraction.
    """
    video_path = None
    
    try:
        # Calculate hash before saving
        content = await video.read()
        file_hash = hashlib.md5(content).hexdigest()
        
        # Get the correct file extension
        file_ext = get_video_extension(video.filename, video.content_type)
        video_path = f"uploads/{file_hash}{file_ext}"
        
        # Only save video if it doesn't exist
        if os.path.exists(video_path):
            print(f"✓ Video already exists: {video_path}")
        else:
            print(f"💾 Saving new video: {video_path}")
            with open(video_path, "wb") as buffer:
                buffer.write(content)
        
        # Setup paths for checking existing data
        base_dir = os.path.dirname(video_path) or "."
        frames_base_dir = os.path.join(base_dir, "frames", file_hash)
        
        # Extract scenes and frames if not already done
        if not os.path.exists(frames_base_dir) or not os.listdir(frames_base_dir):
            print(f"🎬 Preprocessing video: extracting scenes and frames...")
            
            # Try processing the video
            try:
                audio_processor = AudioProcessor(video_path)
                video_data = audio_processor.process(save_segments=True, threshold=27.0)
                print(f"✓ Extracted {len(video_data.scenes)} scenes with keyframes")
            except OSError as e:
                # If WebM fails, try converting to MP4
                if video_path.endswith('.webm') and ("failed to read" in str(e) or "MoviePy error" in str(e)):
                    print(f"⚠️  WebM processing failed, converting to MP4...")
                    video_path = convert_webm_to_mp4(video_path)
                    
                    # Retry with converted MP4
                    audio_processor = AudioProcessor(video_path)
                    video_data = audio_processor.process(save_segments=True, threshold=27.0)
                    print(f"✓ Extracted {len(video_data.scenes)} scenes with keyframes from converted video")
                else:
                    raise
        else:
            print(f"✓ Using existing frames: {frames_base_dir}")
        
        # Run the main video pipeline
        video_pipeline = VideoPipeline(video_path)
        result = video_pipeline.run()
        
        return result
        
    except OSError as e:
        print(f"❌ Video processing error: {e}")
        error_msg = str(e)
        
        if "failed to read the first frame" in error_msg or "MoviePy error" in error_msg:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Video format not supported",
                    "message": f"Unable to process this video file. The video codec may not be supported. Please try converting to H.264 MP4 format. Details: {error_msg}"
                }
            )
        raise
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Video analysis failed. Please try a different video format."
            }
        )

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
        
        # Get the correct file extension (.mp4 or .webm)
        file_ext = get_video_extension(video.filename, video.content_type)
        video_path = f"uploads/{file_hash}{file_ext}"
        
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
        frames_base_dir = os.path.join(base_dir, "frames", file_hash)
        
        # Check if transcript already exists
        if os.path.exists(transcript_path):
            print(f"✓ Using existing transcript: {transcript_path}")
            with open(transcript_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            # Return cached transcript
            return JSONResponse(content={
                "success": True,
                "video_hash": file_hash,
                "transcript": result.get('transcript', ''),
                "summary": result.get('summary', ''),
                "key_points": result.get('key_points', []),
                "language": result.get('language', 'unknown'),
                "word_count": len(result.get('transcript', '').split()),
                "transcript_path": transcript_path,
                "cached": True
            })
        
        # Extract audio and frames if not exists (always save segments for safety checker)
        frames_exist = os.path.exists(frames_base_dir) and os.listdir(frames_base_dir)
        
        if not os.path.exists(full_audio_path) or not frames_exist:
            print(f"🎵 Extracting audio from video...")
            if not frames_exist:
                print(f"🎬 Extracting scenes and frames...")
            
            # Try processing the video
            try:
                audio_processor = AudioProcessor(video_path)
                video_data = audio_processor.process(save_segments=True, threshold=27.0)
                print(f"✓ Audio extracted: {full_audio_path}")
                print(f"✓ Extracted {len(video_data.scenes)} scenes with keyframes")
            except OSError as e:
                # If WebM fails, try converting to MP4
                if video_path.endswith('.webm') and ("failed to read" in str(e) or "MoviePy error" in str(e)):
                    print(f"⚠️  WebM processing failed, converting to MP4...")
                    video_path = convert_webm_to_mp4(video_path)
                    
                    # Update paths for converted video
                    full_audio_path = os.path.join(audio_dir, f"{file_hash}_audio.mp3")
                    
                    # Retry with converted MP4
                    audio_processor = AudioProcessor(video_path)
                    video_data = audio_processor.process(save_segments=True, threshold=27.0)
                    print(f"✓ Audio extracted from converted video: {full_audio_path}")
                    print(f"✓ Extracted {len(video_data.scenes)} scenes with keyframes")
                else:
                    raise
        else:
            print(f"✓ Using existing audio: {full_audio_path}")
            print(f"✓ Using existing frames: {frames_base_dir}")
        
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
            "video_hash": file_hash,
            "transcript": result.get('transcript', ''),
            "summary": result.get('summary', ''),
            "key_points": result.get('key_points', []),
            "language": result.get('language', 'unknown'),
            "word_count": len(result.get('transcript', '').split()),
            "transcript_path": result.get('transcript_path', ''),
            "cached": False
        })
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        import traceback
        traceback.print_exc()
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

class SafetyCheckRequest(BaseModel):
    video_hash: str

@app.post("/safety-check")
async def check_video_safety(request: SafetyCheckRequest):
    """
    Check video content for safety and ethical concerns.
    Analyzes transcript and keyframes for NSFW, bias, and misleading claims.
    """
    video_hash = request.video_hash
    
    try:
        # Setup paths
        base_dir = "uploads"
        transcript_path = os.path.join(base_dir, "transcripts", f"{video_hash}_audio_transcript.json")
        safety_dir = os.path.join(base_dir, "safety")
        safety_report_path = os.path.join(safety_dir, f"{video_hash}_safety_report.json")
        frames_base_dir = os.path.join(base_dir, "frames", video_hash)
        
        # Check if safety report already cached
        if os.path.exists(safety_report_path):
            print(f"✓ Using existing safety report: {safety_report_path}")
            with open(safety_report_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            result['cached'] = True
            return JSONResponse(content={
                "success": True,
                "video_hash": video_hash,
                **result
            })
        
        # Load transcript
        if not os.path.exists(transcript_path):
            raise HTTPException(
                status_code=404,
                detail=f"Transcript not found for video hash: {video_hash}. Please run /transcript first."
            )
        
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        transcript_text = transcript_data.get('transcript', '')
        
        # Collect keyframe paths from all scenes
        keyframe_paths = []
        if os.path.exists(frames_base_dir):
            # Get all keyframes from all scenes
            scene_dirs = glob.glob(os.path.join(frames_base_dir, "scenes", "scene_*"))
            for scene_dir in sorted(scene_dirs):
                scene_keyframes = glob.glob(os.path.join(scene_dir, "keyframe_*.jpg"))
                keyframe_paths.extend(sorted(scene_keyframes))
        
        if not keyframe_paths:
            print(f"⚠️  No keyframes found for video hash: {video_hash}")
            print(f"   Searched in: {frames_base_dir}")
        
        print(f"📊 Found {len(keyframe_paths)} keyframes to analyze")
        
        # Run safety check
        safety_checker = SafetyChecker()
        result = safety_checker.check_safety(
            transcript=transcript_text,
            keyframe_paths=keyframe_paths,
            max_frames=10
        )
        
        # Save safety report
        os.makedirs(safety_dir, exist_ok=True)
        with open(safety_report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved safety report: {safety_report_path}")
        
        # Return results
        return JSONResponse(content={
            "success": True,
            "video_hash": video_hash,
            **result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Safety check error: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Safety check failed. Please check if transcript and frames exist."
            }
        )

