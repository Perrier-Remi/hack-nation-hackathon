"""
Test script for the /transcript endpoint
"""

import sys
import os
import requests

def test_transcript_endpoint():
    """Test the /transcript endpoint with a sample video"""
    
    # Find a test video
    video_path = None
    uploads_dir = "uploads"
    
    if os.path.exists(uploads_dir):
        for file in os.listdir(uploads_dir):
            if file.endswith(('.mp4', '.webm')):
                video_path = os.path.join(uploads_dir, file)
                break
    
    if not video_path or not os.path.exists(video_path):
        print("❌ No video file found in uploads/ directory")
        print("   Please upload a video to uploads/ first")
        return
    
    print(f"🎬 Testing /transcript endpoint")
    print("=" * 70)
    print(f"Video: {video_path}")
    print(f"Size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
    print("=" * 70)
    
    try:
        # Send request to endpoint
        print("\n📤 Uploading to http://localhost:8000/transcript...")
        
        with open(video_path, 'rb') as video_file:
            files = {'video': (os.path.basename(video_path), video_file, 'video/mp4')}
            response = requests.post('http://localhost:8000/transcript', files=files)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print("\n" + "=" * 70)
                print("✅ Transcription Successful!")
                if result.get('cached'):
                    print("⚡ Using CACHED transcript (instant response!)")
                print("=" * 70)
                print(f"\nLanguage: {result.get('language', 'unknown')}")
                print(f"Word Count: {result.get('word_count', 0)}")
                
                if result.get('summary'):
                    print(f"\n📋 Summary:")
                    print(f"   {result['summary'][:200]}...")
                
                if result.get('key_points'):
                    print(f"\n🔑 Key Points:")
                    for i, point in enumerate(result['key_points'][:5], 1):
                        print(f"   {i}. {point}")
                
                if result.get('transcript'):
                    print(f"\n📝 Transcript (first 500 chars):")
                    print(f"   {result['transcript'][:500]}...")
                
                if result.get('transcript_path'):
                    print(f"\n💾 Saved to: {result['transcript_path']}")
                
                print("\n" + "=" * 70)
                print("🎉 Test Passed!")
                print("=" * 70)
            else:
                print(f"\n❌ Transcription Failed:")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                print(f"   Message: {result.get('message', 'No message')}")
        else:
            print(f"\n❌ HTTP Error {response.status_code}")
            print(f"   Response: {response.text[:500]}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to http://localhost:8000")
        print("   Make sure the backend server is running:")
        print("   cd backend && uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_transcript_endpoint()

