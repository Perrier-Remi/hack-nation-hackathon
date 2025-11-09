"""
Safety Checker Module

Uses Google Gemini API to check video content for:
- NSFW/Violence detection
- Bias/Stereotypes in language
- Misleading claims
"""

import os
import time
import json
from typing import Optional, Dict, List
from datetime import datetime
import google.generativeai as genai
from config import GOOGLE_AI_STUDIO_API_KEY, GEMINI_MODEL


class SafetyChecker:
    """
    Checks video content for safety and ethical concerns using Gemini API.
    """
    
    # Rule-based keywords for misleading claims
    MISLEADING_KEYWORDS = [
        "guaranteed", "guarantee", "cure", "cures", "miracle", "miraculous",
        "100%", "never fails", "always works", "proven", "scientifically proven",
        "FDA approved" , "clinically tested", "instant results", "overnight",
        "secret formula", "doctors hate", "one weird trick", "lose weight fast"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SafetyChecker.
        
        Args:
            api_key: Google AI Studio API key (if not provided, uses config)
        """
        self.api_key = api_key or GOOGLE_AI_STUDIO_API_KEY
        
        if not self.api_key:
            raise ValueError(
                "API key not provided. Set GOOGLE_AI_STUDIO_API_KEY in .env file "
                "or pass it to the constructor."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        
        print(f"✓ Safety checker initialized with model: {GEMINI_MODEL}")
    
    def check_safety(
        self,
        transcript: str,
        keyframe_paths: List[str],
        max_frames: int = 10
    ) -> Dict:
        """
        Run comprehensive safety check on video content.
        
        Args:
            transcript: Full transcript text
            keyframe_paths: List of paths to keyframe images
            max_frames: Maximum number of frames to analyze (default: 10)
            
        Returns:
            Dictionary with safety analysis results
        """
        print(f"🛡️  Running comprehensive safety check...")
        
        # Sample frames if too many
        sampled_frames = self._sample_frames(keyframe_paths, max_frames)
        
        # Run all three checks
        nsfw_result = self.analyze_nsfw_violence(sampled_frames)
        bias_result = self.analyze_bias_stereotypes(transcript)
        misleading_result = self.analyze_misleading_claims(transcript)
        
        # Calculate overall score (weighted average)
        overall_score = (
            nsfw_result['score'] * 0.4 +
            bias_result['score'] * 0.3 +
            misleading_result['score'] * 0.3
        )
        
        # Determine severity based on lowest score
        min_score = min(
            nsfw_result['score'],
            bias_result['score'],
            misleading_result['score']
        )
        
        if min_score >= 80:
            severity = "safe"
        elif min_score >= 60:
            severity = "warning"
        else:
            severity = "unsafe"
        
        result = {
            'overall_score': round(overall_score, 1),
            'severity': severity,
            'nsfw_violence': nsfw_result,
            'bias_stereotypes': bias_result,
            'misleading_claims': misleading_result,
            'checked_at': datetime.now().isoformat(),
            'cached': False
        }
        
        print(f"✓ Safety check complete! Overall score: {result['overall_score']}/100 ({severity})")
        
        return result
    
    def analyze_nsfw_violence(self, image_paths: List[str]) -> Dict:
        """
        Analyze images for NSFW content and violence using Gemini Vision.
        
        Args:
            image_paths: List of paths to images
            
        Returns:
            Dictionary with score, flag, and details
        """
        print(f"   [1/3] Checking NSFW/Violence ({len(image_paths)} frames)...")
        
        if not image_paths:
            return {
                'score': 100,
                'flag': 'safe',
                'details': 'No frames to analyze',
                'frames_analyzed': 0
            }
        
        try:
            # Upload images to Gemini
            uploaded_files = []
            for path in image_paths:
                if os.path.exists(path):
                    uploaded_file = genai.upload_file(path)
                    uploaded_files.append(uploaded_file)
            
            if not uploaded_files:
                return {
                    'score': 100,
                    'flag': 'safe',
                    'details': 'No valid frames found',
                    'frames_analyzed': 0
                }
            
            # Wait for processing
            for file in uploaded_files:
                while file.state.name == "PROCESSING":
                    time.sleep(1)
                    file = genai.get_file(file.name)
            
            # Create prompt
            prompt = """
            Analyze these video frames for safety concerns. Check for:
            1. NSFW content (nudity, sexual content, explicit imagery)
            2. Violence or disturbing imagery
            3. Gore or graphic content
            4. Dangerous activities
            
            Provide your analysis in JSON format:
            {
                "score": <0-100, where 100 is completely safe>,
                "flag": "<safe/warning/unsafe>",
                "details": "<explanation of findings>",
                "issues_found": [<list of specific issues, empty if none>]
            }
            
            Be objective and consider advertising context. Rate conservatively.
            """
            
            # Generate content
            response = self.model.generate_content([prompt] + uploaded_files)
            
            # Parse response
            result = self._parse_json_response(response.text)
            result['frames_analyzed'] = len(uploaded_files)
            
            # Clean up uploaded files
            for file in uploaded_files:
                try:
                    genai.delete_file(file.name)
                except:
                    pass
            
            print(f"      ✓ NSFW/Violence: {result['score']}/100 ({result['flag']})")
            return result
            
        except Exception as e:
            print(f"      ⚠️  Error in NSFW analysis: {e}")
            return {
                'score': 50,
                'flag': 'warning',
                'details': f'Analysis error: {str(e)}',
                'frames_analyzed': len(image_paths),
                'issues_found': ['analysis_failed']
            }
    
    def analyze_bias_stereotypes(self, transcript: str) -> Dict:
        """
        Check transcript for stereotypes and biased language using Gemini.
        
        Args:
            transcript: Full transcript text
            
        Returns:
            Dictionary with score, flag, and details
        """
        print(f"   [2/3] Checking Bias/Stereotypes...")
        
        if not transcript or transcript.strip() == "":
            return {
                'score': 100,
                'flag': 'safe',
                'details': 'No transcript to analyze',
                'issues_found': []
            }
        
        try:
            prompt = f"""
            Analyze this advertisement transcript for bias, stereotypes, and non-inclusive language.
            
            Check for:
            1. Gender stereotypes
            2. Racial or ethnic stereotypes
            3. Age-based bias (ageism)
            4. Disability bias (ableism)
            5. Body shaming or appearance-based discrimination
            6. Socioeconomic bias
            7. Cultural insensitivity
            8. Heteronormative or gender-binary assumptions
            
            Transcript:
            "{transcript}"
            
            Provide your analysis in JSON format:
            {{
                "score": <0-100, where 100 is completely inclusive>,
                "flag": "<safe/warning/unsafe>",
                "details": "<explanation of findings>",
                "issues_found": [<list of specific issues like "gender_stereotype", empty if none>]
            }}
            
            Consider modern advertising standards and inclusive practices.
            """
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            print(f"      ✓ Bias/Stereotypes: {result['score']}/100 ({result['flag']})")
            return result
            
        except Exception as e:
            print(f"      ⚠️  Error in bias analysis: {e}")
            return {
                'score': 50,
                'flag': 'warning',
                'details': f'Analysis error: {str(e)}',
                'issues_found': ['analysis_failed']
            }
    
    def analyze_misleading_claims(self, transcript: str) -> Dict:
        """
        Detect misleading claims using rule-based keywords + Gemini verification.
        
        Args:
            transcript: Full transcript text
            
        Returns:
            Dictionary with score, flag, and details
        """
        print(f"   [3/3] Checking Misleading Claims...")
        
        if not transcript or transcript.strip() == "":
            return {
                'score': 100,
                'flag': 'safe',
                'details': 'No transcript to analyze',
                'keywords_found': []
            }
        
        try:
            # Step 1: Rule-based keyword detection
            transcript_lower = transcript.lower()
            found_keywords = [
                keyword for keyword in self.MISLEADING_KEYWORDS
                if keyword.lower() in transcript_lower
            ]
            
            # If no keywords, likely safe
            if not found_keywords:
                return {
                    'score': 100,
                    'flag': 'safe',
                    'details': 'No misleading claim keywords detected',
                    'keywords_found': []
                }
            
            # Step 2: Gemini verification
            prompt = f"""
            This advertisement transcript contains potentially misleading keywords: {', '.join(found_keywords)}
            
            Analyze if the transcript makes misleading, unverifiable, or false claims:
            
            Transcript:
            "{transcript}"
            
            Check for:
            1. Unverifiable health/medical claims
            2. Exaggerated effectiveness claims
            3. False guarantees or promises
            4. Misleading statistics or data
            5. Deceptive omissions
            6. "Too good to be true" offers
            
            Provide your analysis in JSON format:
            {{
                "score": <0-100, where 100 is completely truthful>,
                "flag": "<safe/warning/unsafe>",
                "details": "<explanation of findings>",
                "keywords_found": {json.dumps(found_keywords)},
                "misleading_claims": [<list of specific misleading claims, empty if none>]
            }}
            
            Consider if claims are verifiable and comply with advertising standards.
            """
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            # Ensure keywords_found is in result
            if 'keywords_found' not in result:
                result['keywords_found'] = found_keywords
            
            print(f"      ✓ Misleading Claims: {result['score']}/100 ({result['flag']})")
            return result
            
        except Exception as e:
            print(f"      ⚠️  Error in misleading claims analysis: {e}")
            return {
                'score': 50,
                'flag': 'warning',
                'details': f'Analysis error: {str(e)}',
                'keywords_found': found_keywords if 'found_keywords' in locals() else [],
                'misleading_claims': ['analysis_failed']
            }
    
    def _sample_frames(self, frame_paths: List[str], max_frames: int) -> List[str]:
        """
        Sample frames evenly from the list if there are too many.
        
        Args:
            frame_paths: List of all frame paths
            max_frames: Maximum number to return
            
        Returns:
            Sampled list of frame paths
        """
        if len(frame_paths) <= max_frames:
            return frame_paths
        
        # Sample evenly across the video
        step = len(frame_paths) / max_frames
        sampled = [frame_paths[int(i * step)] for i in range(max_frames)]
        
        return sampled
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse Gemini's JSON response, handling markdown code blocks.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed dictionary
        """
        try:
            # Try to extract JSON from response
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if '```json' in text:
                start = text.find('```json') + 7
                end = text.find('```', start)
                text = text[start:end].strip()
            elif '```' in text:
                start = text.find('```') + 3
                end = text.find('```', start)
                text = text[start:end].strip()
            
            # Parse JSON
            result = json.loads(text)
            
            # Ensure required fields exist
            if 'score' not in result:
                result['score'] = 50
            if 'flag' not in result:
                result['flag'] = 'warning'
            if 'details' not in result:
                result['details'] = 'Analysis completed'
            
            return result
            
        except json.JSONDecodeError:
            print(f"      ⚠️  Could not parse JSON response, using fallback")
            return {
                'score': 50,
                'flag': 'warning',
                'details': 'Unable to parse analysis results',
                'raw_response': response_text[:200]
            }

