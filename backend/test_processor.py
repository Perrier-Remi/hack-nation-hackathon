"""
Test script for AudioProcessor with scene-based detection
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from preprocessing.audio_processor import AudioProcessor


def test_scene_based_processing():
    """Test processing a video into scene-based segments"""
    
    # Path to test video
    video_path = "uploads/66696f2f-2fc1-41b6-81f7-5cf93602a82f.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"🎬 Testing Scene-Based Video Processing")
    print("=" * 70)
    print(f"Video: {video_path}")
    print("=" * 70)
    
    # Create processor
    processor = AudioProcessor(video_path)
    
    # Process video with scene detection
    try:
        video_data = processor.process(save_segments=True, threshold=27.0)
        
        print(f"\n" + "=" * 70)
        print(f"📹 Video Information:")
        print(f"   - Duration: {video_data.duration:.2f} seconds")
        print(f"   - FPS: {video_data.fps:.2f}")
        print(f"   - Total scenes detected: {len(video_data.scenes)}")
        print("=" * 70)
        
        print(f"\n🎞️  Scene Details:")
        for scene in video_data.scenes:
            print(f"\n   Scene {scene.scene_index}:")
            print(f"      Time: {scene.start_time:.2f}s → {scene.end_time:.2f}s ({scene.duration:.2f}s)")
            print(f"      Keyframes: {len(scene.keyframes)} frames")
            print(f"      Audio duration: {len(scene.audio)}ms")
            
            if scene.audio_path:
                print(f"      Audio: {os.path.basename(scene.audio_path)}")
            
            if scene.keyframe_paths:
                print(f"      Frames: {len(scene.keyframe_paths)} saved")
                # Show first and last keyframe names
                if len(scene.keyframe_paths) > 0:
                    print(f"         └─ {os.path.basename(scene.keyframe_paths[0])} ... {os.path.basename(scene.keyframe_paths[-1])}")
        
        # Test the to_dict method
        print(f"\n📋 Serializable summary:")
        summary = video_data.to_dict()
        print(f"   Total scenes: {summary['total_scenes']}")
        print(f"   Scene info entries: {len(summary['scenes_info'])}")
        
        # Show directory structure
        if video_data.scenes and video_data.scenes[0].audio_path:
            audio_dir = os.path.dirname(video_data.scenes[0].audio_path)
            if video_data.scenes[0].keyframe_paths:
                frame_dir = os.path.dirname(os.path.dirname(video_data.scenes[0].keyframe_paths[0]))
                print(f"\n📁 Artifacts saved to:")
                print(f"   Audio: {audio_dir}")
                print(f"   Frames: {frame_dir}")
        
        # Calculate average scene duration
        avg_duration = sum(s.duration for s in video_data.scenes) / len(video_data.scenes)
        print(f"\n📊 Statistics:")
        print(f"   Average scene duration: {avg_duration:.2f}s")
        print(f"   Shortest scene: {min(s.duration for s in video_data.scenes):.2f}s")
        print(f"   Longest scene: {max(s.duration for s in video_data.scenes):.2f}s")
        
        print("\n" + "=" * 70)
        print("✨ Test completed successfully!")
        print("=" * 70)
        print("\n💡 To clean up artifacts, run: make clean-artifacts")
        
    except Exception as e:
        print(f"\n❌ Error processing video: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_scene_based_processing()

