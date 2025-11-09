"""
Transcription Service Module

Uses Google Gemini API to transcribe audio files.
"""

import os
import time
import json
from typing import Optional, Dict
import google.generativeai as genai
from config import GOOGLE_AI_STUDIO_API_KEY, GEMINI_MODEL, validate_config


class TranscriptionService:
    """
    Transcribes audio using Google Gemini API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize TranscriptionService.
        
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
        
        print(f"✓ Transcription service initialized with model: {GEMINI_MODEL}")
    
    def transcribe_audio(
        self,
        audio_path: str,
        save_transcript: bool = True,
        output_dir: str = "transcripts"
    ) -> Dict:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to audio file
            save_transcript: Whether to save transcript to file
            output_dir: Directory to save transcript
            
        Returns:
            Dictionary with transcript and metadata
        """
        print(f"🎙️  Transcribing: {os.path.basename(audio_path)}")
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Upload audio file
            print("   Uploading audio to Gemini...")
            audio_file = genai.upload_file(audio_path)
            
            # Wait for file to be processed
            while audio_file.state.name == "PROCESSING":
                print("   Processing...")
                time.sleep(2)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                raise ValueError(f"Audio processing failed: {audio_file.state}")
            
            print("   Generating transcript...")
            
            # Create prompt for transcription
            prompt = """
            Please transcribe this audio file completely and accurately.
            
            Provide the transcription in the following JSON format:
            {
                "transcript": "full text of what was said",
                "language": "detected language",
                "summary": "brief summary of content",
                "key_points": ["point 1", "point 2", ...]
            }
            
            If there are multiple speakers, note speaker changes.
            If there is background music or sound effects, focus only on the speech.
            """
            
            # Generate content
            response = self.model.generate_content([prompt, audio_file])
            
            # Parse response
            result = self._parse_response(response.text)
            result['audio_file'] = os.path.basename(audio_path)
            result['model'] = GEMINI_MODEL
            
            # Save transcript if requested
            if save_transcript:
                transcript_path = self._save_transcript(
                    audio_path,
                    result,
                    output_dir
                )
                result['transcript_path'] = transcript_path
            
            print(f"✓ Transcription complete!")
            print(f"   Words: ~{len(result.get('transcript', '').split())}")
            
            # Clean up uploaded file
            genai.delete_file(audio_file.name)
            
            return result
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            raise
    
    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse Gemini's response.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed dictionary
        """
        try:
            # Try to extract JSON from response
            # Gemini might wrap JSON in markdown code blocks
            text = response_text.strip()
            
            if '```json' in text:
                # Extract JSON from code block
                start = text.find('```json') + 7
                end = text.find('```', start)
                text = text[start:end].strip()
            elif '```' in text:
                # Extract from generic code block
                start = text.find('```') + 3
                end = text.find('```', start)
                text = text[start:end].strip()
            
            # Parse JSON
            result = json.loads(text)
            return result
            
        except json.JSONDecodeError:
            # If parsing fails, return raw response as transcript
            print("   ⚠️  Could not parse JSON, using raw response")
            return {
                'transcript': response_text,
                'language': 'unknown',
                'summary': '',
                'key_points': []
            }
    
    def _save_transcript(
        self,
        audio_path: str,
        result: Dict,
        output_dir: str
    ) -> str:
        """
        Save transcript to file.
        
        Args:
            audio_path: Original audio file path
            result: Transcription result
            output_dir: Output directory
            
        Returns:
            Path to saved transcript file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        basename = os.path.splitext(os.path.basename(audio_path))[0]
        transcript_path = os.path.join(output_dir, f"{basename}_transcript.json")
        
        # Save as JSON
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Also save as plain text for easy reading
        txt_path = transcript_path.replace('.json', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Transcript for: {basename}\n")
            f.write("=" * 60 + "\n\n")
            f.write(result.get('transcript', ''))
            f.write("\n\n" + "=" * 60 + "\n")
            f.write(f"\nSummary: {result.get('summary', 'N/A')}\n")
            if result.get('key_points'):
                f.write("\nKey Points:\n")
                for point in result['key_points']:
                    f.write(f"  - {point}\n")
        
        print(f"   Transcript saved: {txt_path}")
        
        return transcript_path
    
    def transcribe_with_retry(
        self,
        audio_path: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict:
        """
        Transcribe with automatic retry on failure.
        
        Args:
            audio_path: Path to audio file
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for transcribe_audio
            
        Returns:
            Transcription result
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.transcribe_audio(audio_path, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"   Retry attempt {attempt + 1}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise Exception(f"Transcription failed after {max_retries} attempts: {last_error}")

