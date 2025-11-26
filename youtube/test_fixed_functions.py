#!/usr/bin/env python3
"""
Test script for the fixed multimedia functions
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the fixed functions
from multimedia_functions_fixed import (
    test_fixed_functions,
    check_ffmpeg_availability,
    get_whisper_transcript_fixed,
    extract_video_frames_fixed,
    process_video_frames_ocr_fixed
)

def main():
    print("🔧 Testing Fixed Multimedia Functions")
    print("=" * 60)
    
    # Check prerequisites
    print("📋 Checking Prerequisites:")
    ffmpeg_available = check_ffmpeg_availability()
    print(f"   FFmpeg: {'✅ Available' if ffmpeg_available else '❌ Not Available'}")
    
    if not ffmpeg_available:
        print("\n⚠️  FFmpeg is required for Whisper AI. Please install it:")
        print("   brew install ffmpeg")
        print("\nContinuing with video frame tests only...")
    
    print("\n" + "=" * 60)
    
    # Run comprehensive tests
    print("🧪 Running Comprehensive Tests:")
    
    test_url = "https://www.youtube.com/watch?v=Ybg30FpRVuw"  # Short 58-second video
    
    # Test 1: Whisper AI
    print(f"\n1️⃣  Testing Whisper AI with: {test_url}")
    whisper_result = get_whisper_transcript_fixed(test_url)
    print(f"   Status: {whisper_result['status']}")
    
    if whisper_result['status'] == 'success':
        transcript = whisper_result['transcript']
        print(f"   Transcript Length: {len(transcript)} characters")
        print(f"   Preview: {transcript[:100]}...")
        print(f"   Language: {whisper_result.get('language', 'unknown')}")
    else:
        print(f"   Error: {whisper_result.get('error', 'Unknown error')}")
    
    # Test 2: Video Frame Extraction
    print(f"\n2️⃣  Testing Video Frame Extraction")
    start_frame, end_frame = extract_video_frames_fixed(test_url)
    
    print(f"   Start Frame: {'✅ Extracted' if start_frame is not None else '❌ Failed'}")
    if start_frame is not None:
        print(f"      Shape: {start_frame.shape}")
    
    print(f"   End Frame: {'✅ Extracted' if end_frame is not None else '❌ Failed'}")
    if end_frame is not None:
        print(f"      Shape: {end_frame.shape}")
    
    # Test 3: Complete Video Frame OCR
    print(f"\n3️⃣  Testing Video Frame OCR Pipeline")
    start_text, start_phone, start_partner, end_text, end_phone, end_partner = process_video_frames_ocr_fixed(test_url)
    
    print(f"   Start Frame OCR:")
    print(f"      Text: '{start_text[:80]}{'...' if len(start_text) > 80 else ''}'" if start_text else "      Text: (empty)")
    print(f"      Phone: '{start_phone}'" if start_phone else "      Phone: (none)")
    print(f"      Partner ID: '{start_partner}'" if start_partner else "      Partner ID: (none)")
    
    print(f"   End Frame OCR:")
    print(f"      Text: '{end_text[:80]}{'...' if len(end_text) > 80 else ''}'" if end_text else "      Text: (empty)")
    print(f"      Phone: '{end_phone}'" if end_phone else "      Phone: (none)")
    print(f"      Partner ID: '{end_partner}'" if end_partner else "      Partner ID: (none)")
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print("=" * 60)
    
    whisper_success = whisper_result['status'] == 'success'
    frames_success = start_frame is not None or end_frame is not None
    ocr_success = bool(start_text or end_text)
    phone_success = bool(start_phone or end_phone)
    partner_success = bool(start_partner or end_partner)
    
    print(f"✅ Whisper AI:        {'WORKING' if whisper_success else 'FAILED'}")
    print(f"✅ Frame Extraction:  {'WORKING' if frames_success else 'FAILED'}")
    print(f"✅ Frame OCR:         {'WORKING' if ocr_success else 'FAILED'}")
    print(f"✅ Phone Detection:   {'WORKING' if phone_success else 'FAILED'}")
    print(f"✅ Partner Detection: {'WORKING' if partner_success else 'FAILED'}")
    
    overall_success = whisper_success and frames_success and ocr_success
    print(f"\n🎯 Overall Status: {'SUCCESS - Ready for full crawling!' if overall_success else 'NEEDS MORE WORK'}")
    
    if overall_success:
        print("\n🚀 All systems working! You can now run the full crawler with:")
        print("   python3 youtube_crawler_v3_fixed.py")
    else:
        if not ffmpeg_available:
            print("\n💡 Next step: Install FFmpeg for Whisper AI")
        print("💡 Check the detailed error messages above for specific issues")

if __name__ == "__main__":
    main()
