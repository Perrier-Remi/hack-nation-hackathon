"""
Audio Processor Module

Objective: Extract audio segments from video using scene detection.
Creates scene-based audio chunks with multiple keyframes for analysis in the critique pipeline.
"""

from pydub import AudioSegment
from moviepy.editor import VideoFileClip
from PIL import Image
from typing import List
import os
from scenedetect import open_video, SceneManager, ContentDetector
from preprocessing.models import SceneSegment, VideoAnalysisData


class AudioProcessor:
    """
    Processes video files to extract scene-based audio-frame segments.
    """

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.video = None

    def process(self, save_segments: bool = True, threshold: float = 27.0) -> VideoAnalysisData:
        """
        Process video into scene-based segments with multiple keyframes.
        
        Args:
            save_segments: Whether to save segments to disk (default: True)
            threshold: Scene detection threshold (default: 27.0, lower = more sensitive)
            
        Returns:
            VideoAnalysisData object containing all scene segments and metadata
        """
        print(f"🎬 Starting scene-based video processing...")
        
        # Step 1: Detect scenes using PySceneDetect
        print(f"🔍 Detecting scenes (threshold={threshold})...")
        scene_list = self._detect_scenes(threshold)
        
        if not scene_list:
            raise ValueError("No scenes detected in video. Try adjusting the threshold.")
        
        print(f"✓ Detected {len(scene_list)} scenes")
        
        # Step 2: Load video with MoviePy for frame extraction
        self.video = VideoFileClip(self.video_path)
        
        if self.video.audio is None:
            self.video.close()
            raise ValueError(f"No audio track found in video: {self.video_path}")
        
        # Get video properties
        fps = self.video.fps
        duration = self.video.duration
        
        # Get video UUID for directory structure
        video_uuid = self.video_path.split("/")[-1].split(".")[0]
        base_dir = os.path.dirname(self.video_path) or "."
        
        # Extract full audio once
        print(f"🎵 Extracting audio...")
        audio_path = self._extract_full_audio()
        full_audio = AudioSegment.from_file(audio_path)
        
        # Step 3: Process each scene
        print(f"📊 Processing {len(scene_list)} scenes...")
        scenes = []
        
        for scene_idx, (start_time, end_time) in enumerate(scene_list):
            # Convert FrameTimecode to seconds
            start_sec = start_time.get_seconds()
            end_sec = end_time.get_seconds()
            
            # Extract 5 keyframes at 0%, 25%, 50%, 75%, 100% positions
            keyframes = self._extract_keyframes(start_sec, end_sec, num_frames=5)
            
            # Extract audio for this scene (pydub uses milliseconds)
            scene_audio = full_audio[int(start_sec * 1000):int(end_sec * 1000)]
            
            # Save segments if requested
            audio_seg_path = None
            keyframe_paths = None
            
            if save_segments:
                audio_seg_path, keyframe_paths = self._save_scene_segments(
                    video_uuid, base_dir, scene_idx, scene_audio, keyframes
                )
            
            # Create SceneSegment object
            scene = SceneSegment(
                scene_index=scene_idx,
                start_time=start_sec,
                end_time=end_sec,
                audio=scene_audio,
                keyframes=keyframes,
                audio_path=audio_seg_path,
                keyframe_paths=keyframe_paths
            )
            
            scenes.append(scene)
            print(f"  ✓ Scene {scene_idx}: {start_sec:.2f}s - {end_sec:.2f}s ({scene.duration:.2f}s)")
        
        # Close video file
        self.video.close()
        
        if save_segments:
            print(f"✓ Saved {len(scenes)} scenes to disk")
        
        print(f"✅ Processing complete!")
        
        # Create and return VideoAnalysisData
        return VideoAnalysisData(
            video_path=self.video_path,
            duration=duration,
            fps=fps,
            scenes=scenes
        )

    

    def _detect_scenes(self, threshold: float) -> List:
        """
        Detect scenes in the video using PySceneDetect.
        
        Args:
            threshold: Content detection threshold
            
        Returns:
            List of (start_time, end_time) tuples
        """
        video = open_video(self.video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        
        # Detect scenes
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
        
        return scene_list
    
    def _extract_keyframes(self, start_time: float, end_time: float, num_frames: int = 5) -> List[Image.Image]:
        """
        Extract keyframes from a scene at evenly spaced intervals.
        
        Args:
            start_time: Scene start time in seconds
            end_time: Scene end time in seconds
            num_frames: Number of keyframes to extract (default: 5)
            
        Returns:
            List of PIL Image objects
        """
        keyframes = []
        scene_duration = end_time - start_time
        
        for i in range(num_frames):
            # Calculate position: 0%, 25%, 50%, 75%, 100%
            position = i / (num_frames - 1) if num_frames > 1 else 0.5
            timestamp = start_time + (scene_duration * position)
            
            # Ensure we don't exceed video duration
            timestamp = min(timestamp, self.video.duration - 0.01)
            
            # Extract frame
            frame_array = self.video.get_frame(timestamp)
            frame_image = Image.fromarray(frame_array)
            keyframes.append(frame_image)
        
        return keyframes
    
    def _save_scene_segments(self, video_uuid: str, base_dir: str, scene_idx: int, 
                            audio: AudioSegment, keyframes: List[Image.Image]) -> tuple:
        """
        Save scene audio and keyframes to disk.
        
        Args:
            video_uuid: Video identifier
            base_dir: Base directory for saving
            scene_idx: Scene index
            audio: AudioSegment to save
            keyframes: List of keyframe images
            
        Returns:
            Tuple of (audio_path, keyframe_paths)
        """
        # Create directory structure: audio/{video_id}/scenes/ and frames/{video_id}/scenes/scene_{N}/
        audio_dir = os.path.join(base_dir, "audio", video_uuid, "scenes")
        frames_dir = os.path.join(base_dir, "frames", video_uuid, "scenes", f"scene_{scene_idx:04d}")
        
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(frames_dir, exist_ok=True)
        
        # Save audio
        audio_path = os.path.join(audio_dir, f"scene_{scene_idx:04d}.mp3")
        audio.export(audio_path, format="mp3")
        
        # Save keyframes
        keyframe_paths = []
        for i, keyframe in enumerate(keyframes):
            keyframe_path = os.path.join(frames_dir, f"keyframe_{i}.jpg")
            keyframe.save(keyframe_path, "JPEG", quality=90)
            keyframe_paths.append(keyframe_path)
        
        return audio_path, keyframe_paths
    
    def _extract_full_audio(self) -> str:
        """
        Internal method: Extract full audio to temporary file.
        
        Returns:
            Path to the extracted audio file
        """
        video_uuid = self.video_path.split("/")[-1].split(".")[0]
        
        # Ensure audio directory exists - keep it in same parent directory
        base_dir = os.path.dirname(self.video_path) or "."
        audio_dir = os.path.join(base_dir, "audio")
        
        os.makedirs(audio_dir, exist_ok=True)
        
        audio_path = os.path.join(audio_dir, f"{video_uuid}_audio.mp3")
        self.video.audio.write_audiofile(audio_path, logger=None)
        
        return audio_path
