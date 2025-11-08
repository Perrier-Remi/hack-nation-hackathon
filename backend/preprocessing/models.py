"""
Data models for video preprocessing
"""

from dataclasses import dataclass
from pydub import AudioSegment
from PIL import Image
from typing import List, Optional


@dataclass
class SceneSegment:
    """Represents a detected scene with multiple keyframes and audio"""
    scene_index: int
    start_time: float  # in seconds
    end_time: float    # in seconds
    audio: AudioSegment
    keyframes: List[Image.Image]  # 5 keyframes at 0%, 25%, 50%, 75%, 100%
    audio_path: Optional[str] = None  # Path to saved audio segment
    keyframe_paths: Optional[List[str]] = None  # Paths to saved keyframes
    
    @property
    def duration(self) -> float:
        """Duration of the scene in seconds"""
        return self.end_time - self.start_time
    

@dataclass
class VideoAnalysisData:
    """Container for all preprocessed video data"""
    video_path: str
    duration: float
    fps: float
    scenes: List[SceneSegment]
    
    def to_dict(self) -> dict:
        """Convert to dictionary (without heavy objects like images/audio)"""
        return {
            'video_path': self.video_path,
            'duration': self.duration,
            'fps': self.fps,
            'total_scenes': len(self.scenes),
            'scenes_info': [
                {
                    'scene_index': scene.scene_index,
                    'start_time': scene.start_time,
                    'end_time': scene.end_time,
                    'duration': scene.duration,
                    'audio_path': scene.audio_path,
                    'keyframe_paths': scene.keyframe_paths,
                    'num_keyframes': len(scene.keyframes) if scene.keyframes else 0
                }
                for scene in self.scenes
            ]
        }

