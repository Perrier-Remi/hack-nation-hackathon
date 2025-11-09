"""
Veo Video Enhancement Module

Uses Google's Veo 2 model to generate enhanced video clips based on:
- LLM recommendations and follow-up prompts
- Extracted keyframes from original scenes (optional)
- Quality analysis results
"""

import os
import time
import glob
from typing import Dict, List, Optional
from google import genai
from google.genai import types
from config import GOOGLE_AI_STUDIO_API_KEY


class VeoEnhancer:
    """
    Enhances video scenes using Google Veo 2 model.
    
    Spec Compliance (Official Gemini API - Veo 2):
    - Model: veo-2.0-generate-001 (stable release)
    - prompt: Required text description
    - aspectRatio: Optional ("16:9" or "9:16")
    - durationSeconds: Optional integer (5 - 8 seconds)
    - numberOfVideos: Optional integer (1 or 2)
    
    Notes:
    - Python SDK uses camelCase parameter names (e.g., durationSeconds, not duration_seconds)
    - generateAudio parameter does NOT exist (audio is produced automatically)
    """
    
    def __init__(self, video_hash: str, api_key: Optional[str] = None):
        """
        Initialize Veo enhancer.
        
        Args:
            video_hash: Hash/ID of the original video
            api_key: Google AI Studio API key
        """
        self.video_hash = video_hash
        self.api_key = api_key or GOOGLE_AI_STUDIO_API_KEY
        
        if not self.api_key:
            raise ValueError("API key required for Veo integration")
        
        # Initialize Veo client
        os.environ['GOOGLE_API_KEY'] = self.api_key
        self.client = genai.Client(api_key=self.api_key)
        
        # Paths
        self.frames_dir = f"uploads/frames/{video_hash}/scenes"
        self.output_dir = f"uploads/enhanced/{video_hash}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✓ Veo 2 enhancer initialized for video: {video_hash}")
    
    def enhance_scene(
        self,
        scene_index: int,
        enhancement_prompt: str,
        reference_keyframes: Optional[List[str]] = None,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 6,
        video_count: int = 1
    ) -> Dict:
        """
        Generate enhanced video for a specific scene using Veo 2.
        
        Args:
            scene_index: Scene number to enhance
            enhancement_prompt: Prompt from LLM with improvement suggestions
            reference_keyframes: Paths to keyframes for reference (optional, not required)
            aspect_ratio: Video aspect ratio ("16:9" or "9:16")
            duration_seconds: Target duration in seconds (5 - 8 supported by Veo 2)
            video_count: Number of videos to request (1 or 2)
            
        Returns:
            Dict with enhanced video info
        """
        print(f"🎬 Enhancing scene {scene_index} with Veo 2...")
        
        # Validate aspect ratio
        if aspect_ratio not in ["16:9", "9:16"]:
            print(f"⚠️  Invalid aspect ratio '{aspect_ratio}', falling back to 16:9")
            aspect_ratio = "16:9"
        
        # Validate duration
        if duration_seconds not in [5, 6, 7, 8]:
            print(f"⚠️  Invalid duration {duration_seconds}s, using 6s")
            duration_seconds = 6
        
        # Validate video count
        if video_count not in [1, 2]:
            print(f"⚠️  Invalid video_count {video_count}, using 1")
            video_count = 1
        
        # Get keyframes if not provided
        if reference_keyframes is None:
            scene_dir = os.path.join(self.frames_dir, f"scene_{scene_index:04d}")
            reference_keyframes = sorted(glob.glob(os.path.join(scene_dir, "keyframe_*.jpg")))
        
        # Build enhanced prompt
        full_prompt = self._build_veo_prompt(
            enhancement_prompt,
            scene_index,
            len(reference_keyframes)
        )
        
        try:
            # Log reference keyframe usage (not sent to Veo 2 API)
            print(f"   📷 Reference keyframes available: {len(reference_keyframes)} (not sent to API)")
            print(f"   📝 Prompt: {full_prompt[:100]}...")
            
            # Build Veo 2 config with supported parameters
            config = types.GenerateVideosConfig(
                aspectRatio=aspect_ratio,
                durationSeconds=duration_seconds,
                numberOfVideos=video_count
            )
            
            # Generate video with Veo 2
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=full_prompt,
                config=config,
            )
            
            # Poll until video is ready
            print(f"   ⏳ Generating video (this may take 1-5 minutes)...")
            poll_count = 0
            while not operation.done:
                time.sleep(10)
                operation = self.client.operations.get(operation)
                poll_count += 1
                if poll_count % 6 == 0:  # Every minute
                    print(f"      Still generating... ({poll_count * 10}s elapsed)")
            
            # Download the video
            generated_video = operation.response.generated_videos[0]
            enhanced_video_path = os.path.join(
                self.output_dir,
                f"scene_{scene_index:04d}_enhanced.mp4"
            )
            
            self.client.files.download(file=generated_video.video)
            generated_video.video.save(enhanced_video_path)
            
            print(f"   ✅ Scene {scene_index} enhanced: {enhanced_video_path}")
            
            return {
                "scene_index": scene_index,
                "status": "generated",
                "enhanced_video_path": enhanced_video_path,
                "prompt_used": full_prompt,
                "reference_frames_count": len(reference_keyframes),
                "aspect_ratio": aspect_ratio,
                "duration_seconds": duration_seconds,
                "video_count": video_count,
                "file_size_mb": os.path.getsize(enhanced_video_path) / (1024 * 1024)
            }
            
        except Exception as e:
            print(f"   ❌ Error enhancing scene {scene_index}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "scene_index": scene_index,
                "status": "failed",
                "error": str(e),
                "enhanced_video_path": None
            }
    
    def enhance_all_scenes(
        self,
        llm_summary: Dict,
        max_scenes: int = 3,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 6,
        video_count: int = 1
    ) -> List[Dict]:
        """
        Enhance multiple scenes using LLM recommendations.
        
        Args:
            llm_summary: LLM analysis summary with follow_up_prompt
            max_scenes: Maximum number of scenes to enhance
            
        Returns:
            List of enhancement results
        """
        print(f"\n🚀 Starting batch scene enhancement (max: {max_scenes})")
        print(f"   • aspect_ratio: {aspect_ratio} | duration_seconds: {duration_seconds} | video_count: {video_count}")
        
        # Get follow-up prompt from LLM
        follow_up_prompt = llm_summary.get('follow_up_prompt', '')
        recommendations = llm_summary.get('recommendations', [])
        
        if not follow_up_prompt:
            print("⚠️  No follow-up prompt available")
            return []
        
        # Get available scenes
        if not os.path.exists(self.frames_dir):
            print(f"❌ Frames directory not found: {self.frames_dir}")
            return []
        
        scene_dirs = sorted(glob.glob(os.path.join(self.frames_dir, "scene_*")))
        scenes_to_enhance = scene_dirs[:max_scenes]
        
        print(f"📊 Found {len(scene_dirs)} scenes, enhancing {len(scenes_to_enhance)}")
        
        # Enhance each scene
        results = []
        for scene_dir in scenes_to_enhance:
            scene_index = int(os.path.basename(scene_dir).split('_')[1])
            
            # Build scene-specific prompt
            scene_prompt = self._build_scene_prompt(
                follow_up_prompt,
                recommendations,
                scene_index
            )
            
            # Get keyframes for this scene
            keyframes = sorted(glob.glob(os.path.join(scene_dir, "keyframe_*.jpg")))
            
            # Enhance scene
            result = self.enhance_scene(
                scene_index=scene_index,
                enhancement_prompt=scene_prompt,
                reference_keyframes=keyframes,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                video_count=video_count
            )
            
            results.append(result)
            
            # Rate limiting - wait between requests
            time.sleep(2)
        
        print(f"\n✅ Batch enhancement complete: {len(results)} scenes processed")
        return results
    
    def _build_veo_prompt(
        self,
        enhancement_prompt: str,
        scene_index: int,
        frame_count: int
    ) -> str:
        """
        Build optimized prompt for Veo 2 following Gemini API guidance.
        
        Prompt structure should include:
        - Subject: What's in the scene
        - Action: What's happening
        - Style: Visual aesthetic
        - Camera: Movement and positioning
        - Composition: Framing
        - Ambiance: Lighting and mood
        - Audio: Desired sound design (Veo generates audio automatically)
        """
        
        # Prompt components: Subject, Action, Style, Camera, Composition, Ambiance, Audio
        prompt = f"""A cinematic, high-quality commercial video. {enhancement_prompt}

The camera uses smooth, professional movements with controlled panning or tracking. 
Shot in 16:9 widescreen format with shallow depth of field for cinematic quality.
Warm, natural lighting with high production value. Sharp focus, vibrant colors, and modern color grading.
Professional advertising cinematography with engaging visual storytelling.
Ambient background music with clear, professional audio mixing."""
        
        return prompt.strip()
    
    def _build_scene_prompt(
        self,
        base_prompt: str,
        recommendations: List[str],
        scene_index: int
    ) -> str:
        """Build scene-specific prompt combining LLM suggestions."""
        
        rec_text = "\n".join(f"- {rec}" for rec in recommendations[:3]) if recommendations else ""
        
        prompt = f"""Scene {scene_index} Enhancement:

Base improvements:
{base_prompt}

Key recommendations:
{rec_text}

Apply these improvements to create a higher quality version of this scene."""
        
        return prompt


def enhance_video_from_analysis(
    video_hash: str,
    llm_summary: Dict,
    max_scenes: int = 3,
    aspect_ratio: str = "16:9",
    duration_seconds: int = 6,
    video_count: int = 1
) -> Dict:
    """
    Main entry point: Enhance video scenes based on LLM analysis.
    
    Args:
        video_hash: Video identifier
        llm_summary: LLM analysis results with recommendations
        max_scenes: Number of scenes to enhance
        
    Returns:
        Enhancement results summary
    """
    try:
        enhancer = VeoEnhancer(video_hash)
        results = enhancer.enhance_all_scenes(
            llm_summary=llm_summary,
            max_scenes=max_scenes,
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            video_count=video_count
        )
        
        success_count = sum(1 for r in results if r.get('status') == 'generated')
        
        return {
            "success": True,
            "video_hash": video_hash,
            "total_scenes_enhanced": len(results),
            "successful": success_count,
            "failed": len(results) - success_count,
            "model": "veo-2.0-generate-001",
            "enhancements": results,
            "aspect_ratio": aspect_ratio,
            "duration_seconds": duration_seconds,
            "video_count": video_count,
            "llm_follow_up_prompt": llm_summary.get('follow_up_prompt'),
            "output_directory": f"uploads/enhanced/{video_hash}"
        }
        
    except Exception as e:
        print(f"❌ Enhancement pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "video_hash": video_hash
        }

