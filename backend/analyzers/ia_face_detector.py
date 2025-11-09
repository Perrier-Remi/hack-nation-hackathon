import cv2
import numpy as np
from ultralytics import YOLO
from typing import List
import os
from skimage.restoration import denoise_bilateral

class IAFaceDetector():
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.images = self._extract_images()
        self.yolo_model = self._load_face_model()
        self.is_face_model = self._check_if_face_model()
    
    def _load_face_model(self):
        face_model_paths = ['yolov8n-face.pt', 'models/yolov8n-face.pt']
        for model_path in face_model_paths:
            if os.path.exists(model_path):
                return YOLO(model_path)
        return YOLO('yolov8n.pt')
    
    def _check_if_face_model(self):
        try:
            model_path = str(self.yolo_model.ckpt_path if hasattr(self.yolo_model, 'ckpt_path') else '')
            return 'face' in model_path.lower()
        except:
            return False
    
    def _extract_images(self, sample_interval: int = 3):
        images = []
        video = cv2.VideoCapture(self.video_path)
        fps = max(video.get(cv2.CAP_PROP_FPS), 30)
        frame_interval = int(fps * sample_interval)
        frame_count = 0
        
        success, frame = video.read()
        while success:
            if frame_count % frame_interval == 0:
                h, w = frame.shape[:2]
                if w > 640:
                    scale = 640 / w
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                images.append(frame)
            success, frame = video.read()
            frame_count += 1
        video.release()
        return images

    def detect_and_extract_faces(self, images: List[np.ndarray]) -> List[np.ndarray]:
        face_images = []
        for image in images:
            results = self.yolo_model(image, verbose=False, imgsz=640, conf=0.5, device='cpu')
            for result in results:
                if result.boxes is None or len(result.boxes) == 0:
                    continue
                for box in result.boxes:
                    if float(box.conf[0]) <= 0.5:
                        continue
                    cls = int(box.cls[0])
                    if not self.is_face_model and cls != 0:
                        continue
                    
                    x1, y1, x2, y2 = [int(x) for x in box.xyxy[0].cpu().numpy()]
                    h, w = image.shape[:2]
                    x1, y1, x2 = max(0, x1), max(0, y1), min(w, x2)
                    
                    if self.is_face_model:
                        y2 = min(h, y2)
                    else:
                        y2 = min(h, y1 + int((y2 - y1) * 0.4))
                    
                    face_region = image[y1:y2, x1:x2]
                    if face_region.size > 0 and face_region.shape[0] > 20 and face_region.shape[1] > 20:
                        face_images.append(face_region)
        return face_images

    def _extract_noise_residual(self, face_image: np.ndarray) -> np.ndarray:
        img = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY) if len(face_image.shape) == 3 else face_image
        img = cv2.resize(img, (128, 128))
        denoised = denoise_bilateral(img, sigma_color=0.1, sigma_spatial=10, channel_axis=None)
        residual = img.astype(np.float32) - denoised.astype(np.float32)
        return (residual - residual.mean()) / (residual.std() + 1e-8)
    
    def _compute_prnu_score(self, residual: np.ndarray) -> float:
        f = np.fft.fft2(residual)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = np.abs(fshift)
        
        rows, cols = residual.shape
        crow, ccol = rows // 2, cols // 2
        high_freq = magnitude_spectrum.copy()
        high_freq[crow-20:crow+20, ccol-20:ccol+20] = 0
        
        hf_ratio = np.sum(high_freq**2) / (np.sum(magnitude_spectrum**2) + 1e-8)
        normalized = np.clip((hf_ratio - 0.1) / 0.4, 0, 1)
        return float(normalized)
    
    def _analyze_face_ai_vs_human(self, face_image: np.ndarray) -> float:
        try:
            residual = self._extract_noise_residual(face_image)
            realness_score = self._compute_prnu_score(residual)
            ai_score = 1.0 - realness_score
            
            # More sensitive to AI: lower threshold, more aggressive transformation
            # Push human scores (lower) towards 0, AI scores (higher) towards 1
            min_observed = 0.7  # Lower threshold - more permissive for AI detection
            max_observed = 1.0
            
            if ai_score <= min_observed:
                normalized = 0.0
            elif ai_score >= max_observed:
                normalized = 1.0
            else:
                normalized = (ai_score - min_observed) / (max_observed - min_observed)
            
            # More aggressive power function - pushes extremes more strongly
            power = 0.15  # Lower power = more aggressive separation
            return float(np.clip(np.power(normalized, power), 0.0, 1.0))
        except:
            return 0.0

    def run(self, max_faces_to_analyze: int = 10):
        faces = self.detect_and_extract_faces(self.images)
        if not faces:
            return 0.0
        
        faces_to_analyze = faces[:max_faces_to_analyze]
        ai_scores = [self._analyze_face_ai_vs_human(face) for face in faces_to_analyze]
        faces_above_threshold = sum(1 for score in ai_scores if score >= 1.0)
        return float(faces_above_threshold / len(ai_scores)) if ai_scores else 0.0
