#!/usr/bin/env python3
"""
Test script to debug multimedia processing issues
"""

import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import functions from the main crawler
from youtube_crawler_v3_test import get_whisper_transcript, extract_video_frames, process_video_frames_ocr

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_whisper():
    """Test Whisper AI function with a simple YouTube video"""
    print("=" * 50)
    print("🤖 Testing Whisper AI Function")
    print("=" * 50)
    
    # Use a short, simple YouTube video for testing
    test_url = "https://www.youtube.com/watch?v=Ybg30FpRVuw"  # First video from CSV (58 seconds)
    
    try:
        logger.info(f"Testing Whisper with URL: {test_url}")
        result = get_whisper_transcript(test_url)
        
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Transcript: {result.get('transcript', 'no transcript')[:200]}...")
        print(f"Confidence: {result.get('confidence', 0.0)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Whisper test failed: {e}")
        return None

def test_video_frames():
    """Test video frame extraction function"""
    print("\n" + "=" * 50)
    print("🎬 Testing Video Frame Extraction")
    print("=" * 50)
    
    # Use same test video
    test_url = "https://www.youtube.com/watch?v=Ybg30FpRVuw"
    
    try:
        logger.info(f"Testing video frames with URL: {test_url}")
        start_frame, end_frame = extract_video_frames(test_url)
        
        print(f"Start frame: {type(start_frame)} {start_frame.shape if start_frame is not None else 'None'}")
        print(f"End frame: {type(end_frame)} {end_frame.shape if end_frame is not None else 'None'}")
        
        return start_frame, end_frame
        
    except Exception as e:
        logger.error(f"Video frame test failed: {e}")
        return None, None

def test_video_frames_ocr():
    """Test complete video frame OCR process"""
    print("\n" + "=" * 50)
    print("👁️ Testing Video Frame OCR")
    print("=" * 50)
    
    test_url = "https://www.youtube.com/watch?v=Ybg30FpRVuw"
    
    try:
        logger.info(f"Testing video frame OCR with URL: {test_url}")
        result = process_video_frames_ocr(test_url)
        
        start_text, start_phone, start_partner, end_text, end_phone, end_partner = result
        
        print(f"Start frame OCR: '{start_text}'")
        print(f"Start phone: '{start_phone}'")
        print(f"Start partner: '{start_partner}'")
        print(f"End frame OCR: '{end_text}'")
        print(f"End phone: '{end_phone}'")
        print(f"End partner: '{end_partner}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Video frame OCR test failed: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Starting Multimedia Function Tests")
    print("This will help identify why Whisper and Video Frame OCR are not working")
    
    # Test each function
    whisper_result = test_whisper()
    frames_result = test_video_frames()
    ocr_result = test_video_frames_ocr()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"Whisper: {'✅ Working' if whisper_result and whisper_result.get('status') == 'success' else '❌ Failed'}")
    print(f"Frame Extraction: {'✅ Working' if frames_result[0] is not None else '❌ Failed'}")
    print(f"Frame OCR: {'✅ Working' if ocr_result and any(ocr_result[:6]) else '❌ Failed'}")
