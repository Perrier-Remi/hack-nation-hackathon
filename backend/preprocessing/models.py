"""
Data models for video preprocessing and safety checking
"""

from dataclasses import dataclass
from pydub import AudioSegment
from PIL import Image
from typing import List, Optional, Dict


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
    transcript: Optional[str] = None  # Full video transcript
    transcript_path: Optional[str] = None  # Path to saved transcript
    
    def to_dict(self) -> dict:
        """Convert to dictionary (without heavy objects like images/audio)"""
        return {
            'video_path': self.video_path,
            'duration': self.duration,
            'fps': self.fps,
            'total_scenes': len(self.scenes),
            'transcript': self.transcript,
            'transcript_path': self.transcript_path,
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


@dataclass
class SafetyReport:
    """Container for safety and ethics check results"""
    overall_score: float  # 0-100, where 100 is completely safe
    severity: str  # "safe", "warning", or "unsafe"
    nsfw_violence: Dict  # {score, flag, details, frames_analyzed, issues_found}
    bias_stereotypes: Dict  # {score, flag, details, issues_found}
    misleading_claims: Dict  # {score, flag, details, keywords_found, misleading_claims}
    checked_at: str  # ISO format timestamp
    cached: bool  # Whether result was from cache
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'overall_score': self.overall_score,
            'severity': self.severity,
            'nsfw_violence': self.nsfw_violence,
            'bias_stereotypes': self.bias_stereotypes,
            'misleading_claims': self.misleading_claims,
            'checked_at': self.checked_at,
            'cached': self.cached
        }

