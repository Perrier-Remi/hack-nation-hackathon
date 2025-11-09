"""
Test script for SafetyChecker service
"""

import sys
import os
import json
import glob

sys.path.insert(0, os.path.dirname(__file__))

from analyzers.safety_checker import SafetyChecker


def test_safety_checker():
    """Test the safety checking functionality"""
    
    print(f"\n🛡️  Testing Safety Checker")
    print("=" * 70)
    
    # Find a video hash that has both transcript and frames
    transcripts_dir = "uploads/transcripts"
    frames_dir = "uploads/frames"
    
    if not os.path.exists(transcripts_dir):
        print(f"❌ Transcripts directory not found: {transcripts_dir}")
        print("   Please run test_transcription.py first")
        return
    
    # Get available transcript files
    transcript_files = glob.glob(os.path.join(transcripts_dir, "*_audio_transcript.json"))
    
    if not transcript_files:
        print(f"❌ No transcript files found in {transcripts_dir}")
        print("   Please run transcription on a video first")
        return
    
    # Use the first transcript
    transcript_file = transcript_files[0]
    video_hash = os.path.basename(transcript_file).replace("_audio_transcript.json", "").replace("_audio", "")
    
    print(f"Video hash: {video_hash}")
    print(f"Transcript: {transcript_file}")
    
    # Load transcript
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    transcript_text = transcript_data.get('transcript', '')
    print(f"Transcript length: {len(transcript_text)} characters")
    
    # Find keyframes
    video_frames_dir = os.path.join(frames_dir, video_hash)
    keyframe_paths = []
    
    if os.path.exists(video_frames_dir):
        scene_dirs = glob.glob(os.path.join(video_frames_dir, "scenes", "scene_*"))
        for scene_dir in sorted(scene_dirs):
            scene_keyframes = glob.glob(os.path.join(scene_dir, "keyframe_*.jpg"))
            keyframe_paths.extend(sorted(scene_keyframes))
    
    print(f"Keyframes found: {len(keyframe_paths)}")
    
    if not keyframe_paths:
        print(f"⚠️  No keyframes found. Scene detection may not have been run.")
        print(f"   Safety check will proceed with transcript only.")
    
    print("=" * 70)
    
    try:
        # Create safety checker
        safety_checker = SafetyChecker()
        
        # Run safety check
        result = safety_checker.check_safety(
            transcript=transcript_text,
            keyframe_paths=keyframe_paths,
            max_frames=10
        )
        
        # Display results
        print("\n" + "=" * 70)
        print("🛡️  SAFETY CHECK RESULTS")
        print("=" * 70)
        
        print(f"\n📊 Overall Assessment:")
        print(f"   Score: {result['overall_score']}/100")
        print(f"   Severity: {result['severity'].upper()}")
        
        # NSFW/Violence
        print(f"\n🔞 NSFW/Violence Check:")
        nsfw = result['nsfw_violence']
        print(f"   Score: {nsfw['score']}/100")
        print(f"   Flag: {nsfw['flag']}")
        print(f"   Details: {nsfw['details']}")
        print(f"   Frames analyzed: {nsfw.get('frames_analyzed', 0)}")
        if nsfw.get('issues_found'):
            print(f"   Issues: {', '.join(nsfw['issues_found'])}")
        
        # Bias/Stereotypes
        print(f"\n⚖️  Bias/Stereotypes Check:")
        bias = result['bias_stereotypes']
        print(f"   Score: {bias['score']}/100")
        print(f"   Flag: {bias['flag']}")
        print(f"   Details: {bias['details']}")
        if bias.get('issues_found'):
            print(f"   Issues: {', '.join(bias['issues_found'])}")
        
        # Misleading Claims
        print(f"\n⚠️  Misleading Claims Check:")
        misleading = result['misleading_claims']
        print(f"   Score: {misleading['score']}/100")
        print(f"   Flag: {misleading['flag']}")
        print(f"   Details: {misleading['details']}")
        if misleading.get('keywords_found'):
            print(f"   Keywords found: {', '.join(misleading['keywords_found'])}")
        if misleading.get('misleading_claims'):
            print(f"   Claims: {', '.join(misleading['misleading_claims'])}")
        
        print(f"\n⏰ Checked at: {result['checked_at']}")
        
        # Save test result
        test_output = os.path.join("uploads", "safety", f"{video_hash}_safety_report.json")
        os.makedirs(os.path.dirname(test_output), exist_ok=True)
        
        with open(test_output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report saved to: {test_output}")
        
        print("\n" + "=" * 70)
        print("✅ Safety Check Test Complete!")
        print("=" * 70)
        
        # Interpretation
        if result['severity'] == 'safe':
            print("\n✅ This content appears safe for advertising.")
        elif result['severity'] == 'warning':
            print("\n⚠️  This content has some concerns. Review recommended.")
        else:
            print("\n❌ This content has significant safety concerns.")
        
    except Exception as e:
        print(f"\n❌ Error during safety check: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_safety_checker()

