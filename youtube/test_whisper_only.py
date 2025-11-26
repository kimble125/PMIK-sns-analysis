#!/usr/bin/env python3
"""
Quick test of just the Whisper AI functionality
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the updated function
from youtube_crawler_v3_test import get_whisper_transcript

def test_whisper_quick():
    """Quick test of Whisper AI with improved implementation"""
    test_url = "https://www.youtube.com/watch?v=Ybg30FpRVuw"  # Short video
    
    print("🎤 Testing Improved Whisper AI")
    print("=" * 50)
    print(f"Video: {test_url}")
    
    result = get_whisper_transcript(test_url)
    
    print(f"\nStatus: {result['status']}")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    
    if result['status'] == 'success':
        transcript = result['transcript']
        print(f"Transcript Length: {len(transcript)} characters")
        print(f"Full Transcript: {transcript}")
        return True
    else:
        print("❌ Whisper failed")
        return False

if __name__ == "__main__":
    success = test_whisper_quick()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
