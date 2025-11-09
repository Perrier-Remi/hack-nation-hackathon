"""
Test script for speech extraction and transcription
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from preprocessing.audio_processor import AudioProcessor
from analyzers.transcription_service import TranscriptionService


def test_transcription():
    """Test audio extraction and transcription"""
    
    # Path to test video
    video_path = "uploads/UE-sgtF8PZU8aZZ2.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"\n🚀 Testing Audio Extraction & Transcription")
    print("=" * 70)
    print(f"Video: {video_path}")
    print("=" * 70)
    
    try:
        # Step 1: Extract audio from video
        print("\n[1/2] Extracting audio from video...")
        audio_processor = AudioProcessor(video_path)
        video_uuid = video_path.split("/")[-1].split(".")[0]
        base_dir = os.path.dirname(video_path) or "."
        
        # Get full audio path (AudioProcessor extracts it during scene processing)
        audio_dir = os.path.join(base_dir, "audio")
        full_audio_path = os.path.join(audio_dir, f"{video_uuid}_audio.mp3")
        
        # If audio doesn't exist, extract it first
        if not os.path.exists(full_audio_path):
            print("   Audio not found, running scene detection to extract audio...")
            video_data = audio_processor.process(save_segments=False, threshold=27.0)
            print(f"   ✓ Extracted audio from {len(video_data.scenes)} scenes")
        else:
            print(f"   ✓ Using existing audio: {full_audio_path}")
        
        # Step 2: Transcribe the audio directly
        print("\n[2/2] Transcribing audio...")
        transcription_service = TranscriptionService()
        
        output_dir = os.path.join(base_dir, "transcripts")
        result = transcription_service.transcribe_with_retry(
            full_audio_path,
            save_transcript=True,
            output_dir=output_dir
        )
        
        # Display results
        print("\n" + "=" * 70)
        print("📊 Transcription Results")
        print("=" * 70)
        
        transcript = result.get('transcript', '')
        print(f"\n📝 Transcript ({len(transcript)} characters):")
        print("-" * 70)
        print(transcript[:500])
        if len(transcript) > 500:
            print("...")
            print(f"\n(Full transcript saved to file)")
        
        if result.get('summary'):
            print(f"\n📋 Summary:")
            print(result['summary'])
        
        if result.get('key_points'):
            print(f"\n🔑 Key Points:")
            for point in result['key_points']:
                print(f"   • {point}")
        
        if result.get('transcript_path'):
            print(f"\n💾 Saved to: {result['transcript_path']}")
        
        print("\n" + "=" * 70)
        print("✅ Transcription Test Complete!")
        print("=" * 70)
        print("\n💡 Files created:")
        print(f"   - Audio: {full_audio_path}")
        print(f"   - Transcript: {result.get('transcript_path', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️  Make sure you have set GOOGLE_AI_STUDIO_API_KEY in your .env file!")
    print("   Get your API key from: https://makersuite.google.com/app/apikey\n")
    
    test_transcription()

