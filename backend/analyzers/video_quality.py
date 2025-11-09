import cv2
import numpy as np
from typing import Dict, List
from PIL import Image

class VideoQualityAnalyzer():
    def __init__(self, video_path: str):
        super().__init__(video_path)
    
    def _extract_frames(self, max_frames: int = 15, sample_interval: int = 2) -> List[np.ndarray]:
        """Extract frames from video"""
        frames = []
        video = cv2.VideoCapture(self.video_path)
        fps = max(video.get(cv2.CAP_PROP_FPS), 30)
        frame_interval = int(fps * sample_interval)
        frame_count = 0
        
        success, frame = video.read()
        while success and len(frames) < max_frames:
            if frame_count % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            success, frame = video.read()
            frame_count += 1
        
        video.release()
        return frames
    
    def _get_resolution_score(self, frame: np.ndarray) -> float:
        """Calculate resolution score (higher resolution = better, more strict)"""
        h, w = frame.shape[:2]
        total_pixels = h * w
        
        # More strict: require 1080p+ for good scores
        # 720p = 1280x720 = 921,600 pixels
        # 1080p = 1920x1080 = 2,073,600 pixels
        # 4K = 3840x2160 = 8,294,400 pixels
        
        # Score based on resolution tier (stricter thresholds)
        if total_pixels >= 8000000:  # 4K+
            return 1.0
        elif total_pixels >= 2000000:  # 1080p+
            # Only 1080p+ gets good scores
            return 0.7 + (total_pixels - 2000000) / 6000000 * 0.3
        elif total_pixels >= 900000:  # 720p+
            # 720p gets lower scores
            return 0.3 + (total_pixels - 900000) / 1100000 * 0.4
        elif total_pixels >= 300000:  # 480p+
            return 0.1 + (total_pixels - 300000) / 600000 * 0.2
        else:
            return total_pixels / 300000 * 0.1
    
    def _get_sharpness_score(self, frame: np.ndarray) -> float:
        """Calculate sharpness using Laplacian variance"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) if len(frame.shape) == 3 else frame
        
        # Resize if too large for faster processing
        h, w = gray.shape
        if w > 1280:
            scale = 1280 / w
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        
        # Calculate Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # More strict: require higher variance for good scores
        # Typical range 0-500 for good quality, but be more demanding
        # Use tanh for smooth normalization, but with higher threshold
        score = np.tanh(variance / 300.0)  # Higher threshold = more strict
        # Apply power function to make it even more strict
        score = np.power(score, 0.8)  # Lower power = more strict
        return float(score)
    
    def _get_color_balance_score(self, frame: np.ndarray) -> Dict[str, float]:
        """Calculate color balance and saturation"""
        if len(frame.shape) != 3:
            return {
                "color_balance": 0.5,
                "saturation": 0.0,
                "color_score": 0.5
            }
        
        # Convert to HSV for saturation analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        
        # Calculate saturation (S channel in HSV)
        saturation = np.mean(hsv[:, :, 1]) / 255.0
        
        # Calculate color balance (RGB channels)
        r, g, b = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
        r_mean = np.mean(r)
        g_mean = np.mean(g)
        b_mean = np.mean(b)
        
        # Color balance: how balanced are RGB channels (more strict)
        channel_means = np.array([r_mean, g_mean, b_mean])
        channel_std = np.std(channel_means)
        channel_mean = np.mean(channel_means)
        
        # Lower std relative to mean = better balance (stricter)
        cv_ratio = channel_std / (channel_mean + 1e-8)
        balance_score = 1.0 - np.tanh(cv_ratio * 3.0)  # Higher multiplier = more strict
        # Apply power to make it stricter
        balance_score = np.power(balance_score, 1.2)
        
        # Saturation score: narrower optimal range (0.35-0.65, more strict)
        # Too low (washed out) or too high (oversaturated) is less aesthetic
        if 0.35 <= saturation <= 0.65:
            saturation_score = 1.0
        elif saturation < 0.35:
            saturation_score = (saturation / 0.35) ** 1.5  # Penalize more
        else:  # saturation > 0.65
            saturation_score = (1.0 - (saturation - 0.65) / 0.35) ** 1.5  # Penalize more
        saturation_score = max(0.0, min(1.0, saturation_score))
        
        # Overall color score (both must be good)
        color_score = (balance_score * 0.65 + saturation_score * 0.35)
        
        return {
            "color_balance": float(balance_score),
            "saturation": float(saturation),
            "saturation_score": float(saturation_score),
            "color_score": float(color_score)
        }
    
    def _get_lighting_score(self, frame: np.ndarray) -> Dict[str, float]:
        """Calculate lighting quality"""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) if len(frame.shape) == 3 else frame
        
        # Mean brightness (0-255, ideal around 128, more strict)
        mean_brightness = np.mean(gray)
        brightness_ratio = mean_brightness / 255.0
        
        # Narrower optimal range: 0.42-0.58 (more strict)
        if 0.42 <= brightness_ratio <= 0.58:
            brightness_score = 1.0
        elif brightness_ratio < 0.42:
            brightness_score = (brightness_ratio / 0.42) ** 1.5  # Penalize more
        else:  # brightness_ratio > 0.58
            brightness_score = ((1.0 - (brightness_ratio - 0.58) / 0.42)) ** 1.5  # Penalize more
        brightness_score = max(0.0, min(1.0, brightness_score))
        
        # Dynamic range: difference between brightest and darkest pixels
        min_pixel = np.min(gray)
        max_pixel = np.max(gray)
        dynamic_range = (max_pixel - min_pixel) / 255.0
        
        # Stricter range: 0.75-0.92 (narrower optimal range)
        if 0.75 <= dynamic_range <= 0.92:
            dynamic_range_score = 1.0
        elif dynamic_range < 0.75:
            dynamic_range_score = (dynamic_range / 0.75) ** 1.5  # Penalize more
        else:  # dynamic_range > 0.92
            dynamic_range_score = ((1.0 - (dynamic_range - 0.92) / 0.08)) ** 1.5  # Penalize more
        dynamic_range_score = max(0.0, min(1.0, dynamic_range_score))
        
        # Check for over/under exposure (clipping) - more strict
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten() / hist.sum()
        
        overexposed = np.sum(hist[240:])  # Very bright pixels
        underexposed = np.sum(hist[:16])  # Very dark pixels
        # Higher penalty for clipping
        clipping_penalty = ((overexposed + underexposed) ** 1.5) * 0.8
        
        # Overall lighting score (more weight on brightness and dynamic range)
        lighting_score = (brightness_score * 0.45 + dynamic_range_score * 0.45 + (1.0 - clipping_penalty) * 0.1)
        # Apply power to make it stricter
        lighting_score = np.power(lighting_score, 0.9)
        
        return {
            "brightness": float(brightness_ratio),
            "brightness_score": float(brightness_score),
            "dynamic_range": float(dynamic_range),
            "dynamic_range_score": float(dynamic_range_score),
            "overexposed_ratio": float(overexposed),
            "underexposed_ratio": float(underexposed),
            "lighting_score": float(lighting_score)
        }
    
    def run(self) -> Dict:
        """Run visual quality analysis"""
        try:
            # Extract frames
            frames = self._extract_frames(max_frames=15, sample_interval=2)
            
            if not frames:
                return {
                    "resolution_score": 0.0,
                    "sharpness_score": 0.0,
                    "color_score": 0.0,
                    "lighting_score": 0.0,
                    "overall_quality": 0.0
                }
            
            # Calculate metrics for each frame
            resolution_scores = []
            sharpness_scores = []
            color_scores = []
            lighting_scores = []
            
            color_details = []
            lighting_details = []
            
            for frame in frames:
                # Resolution (same for all frames, but calculate once)
                if not resolution_scores:
                    resolution_scores.append(self._get_resolution_score(frame))
                
                # Sharpness
                sharpness_scores.append(self._get_sharpness_score(frame))
                
                # Color balance and saturation
                color_info = self._get_color_balance_score(frame)
                color_scores.append(color_info["color_score"])
                color_details.append(color_info)
                
                # Lighting
                lighting_info = self._get_lighting_score(frame)
                lighting_scores.append(lighting_info["lighting_score"])
                lighting_details.append(lighting_info)
            
            # Calculate averages
            avg_resolution = resolution_scores[0] if resolution_scores else 0.0
            avg_sharpness = np.mean(sharpness_scores) if sharpness_scores else 0.0
            avg_color = np.mean(color_scores) if color_scores else 0.0
            avg_lighting = np.mean(lighting_scores) if lighting_scores else 0.0
            
            # Overall quality (weighted average, more weight on sharpness and lighting)
            overall_quality = (
                avg_resolution * 0.15 +
                avg_sharpness * 0.35 +  # More weight on sharpness
                avg_color * 0.20 +
                avg_lighting * 0.30  # More weight on lighting
            )
            # Apply power function to make overall score stricter
            overall_quality = np.power(overall_quality, 0.85)
            
            return {
                "resolution_score": float(avg_resolution),
                "sharpness_score": float(avg_sharpness),
                "color_score": float(avg_color),
                "lighting_score": float(avg_lighting),
                "overall_quality": float(overall_quality)
            }
            
        except Exception as e:
            print(f"Error in visual quality analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                "resolution_score": 0.0,
                "sharpness_score": 0.0,
                "color_score": 0.0,
                "lighting_score": 0.0,
                "overall_quality": 0.0
            }
