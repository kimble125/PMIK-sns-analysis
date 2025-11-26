#!/usr/bin/env python3
"""
Debug script for video frame extraction issues
"""

import os
import tempfile
import cv2
import yt_dlp
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_video_download():
    """Debug video download process step by step"""
    test_url = "https://www.youtube.com/watch?v=Ybg30FpRVuw"
    
    print("🐛 Debugging Video Frame Extraction")
    print("=" * 60)
    
    # Step 1: Check video info
    print("1️⃣  Getting video info...")
    try:
        ydl_opts = {
            'quiet': False,  # Enable output
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        print(f"   Title: {info.get('title', 'Unknown')}")
        print(f"   Duration: {info.get('duration', 0)} seconds")
        print(f"   Available formats: {len(info.get('formats', []))}")
        
        # Find best video format
        video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none']
        print(f"   Video formats available: {len(video_formats)}")
        
        if video_formats:
            # Show first few formats
            for i, fmt in enumerate(video_formats[:3]):
                print(f"      Format {i+1}: {fmt.get('format_id')} - {fmt.get('resolution', 'unknown')} "
                      f"({fmt.get('ext', 'unknown')}) - {fmt.get('filesize_approx', 'unknown')} bytes")
        
    except Exception as e:
        print(f"   ❌ Failed to get video info: {e}")
        return False
    
    # Step 2: Try downloading with different formats
    formats_to_try = [
        'worst[height<=240][ext=mp4]',  # Very low quality
        'worst[ext=mp4]',               # Worst MP4
        'worst',                        # Any format
    ]
    
    for i, format_selector in enumerate(formats_to_try, 1):
        print(f"\n2️⃣  Trying format {i}: {format_selector}")
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            ydl_opts = {
                'format': format_selector,
                'outtmpl': temp_path,
                'quiet': False,
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([test_url])
            
            # Check file
            if os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                print(f"   ✅ Downloaded: {file_size} bytes")
                
                # Try opening with OpenCV
                cap = cv2.VideoCapture(temp_path)
                if cap.isOpened():
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    print(f"   ✅ OpenCV opened successfully:")
                    print(f"      Frames: {frame_count}, FPS: {fps}")
                    print(f"      Resolution: {width}x{height}")
                    
                    # Try reading first frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"   ✅ First frame read successfully: {frame.shape}")
                        cap.release()
                        os.remove(temp_path)
                        return True
                    else:
                        print(f"   ❌ Failed to read first frame")
                    
                    cap.release()
                else:
                    print(f"   ❌ OpenCV failed to open file")
            else:
                print(f"   ❌ File not downloaded")
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            continue
    
    print(f"\n❌ All format attempts failed")
    return False

def debug_specific_video_format():
    """Try a different video that might work better"""
    # Try a different video that's known to work well
    alternate_urls = [
        "https://www.youtube.com/watch?v=adb4kpt6_dM",  # 12분 7초 video from CSV
        "https://www.youtube.com/watch?v=6WnOQCYuftc",  # 37분 8초 video from CSV
    ]
    
    for i, url in enumerate(alternate_urls, 1):
        print(f"\n3️⃣  Testing alternate video {i}: {url}")
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            ydl_opts = {
                'format': 'worst[height<=360][ext=mp4]/worst[ext=mp4]',
                'outtmpl': temp_path,
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                cap = cv2.VideoCapture(temp_path)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"   ✅ Success! Frame extracted: {frame.shape}")
                        cap.release()
                        os.remove(temp_path)
                        return url
                    cap.release()
                
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    return None

if __name__ == "__main__":
    # Test original video
    success1 = debug_video_download()
    
    # Test alternate videos
    working_url = debug_specific_video_format()
    
    print(f"\n" + "=" * 60)
    print("🎯 DEBUG SUMMARY")
    print("=" * 60)
    print(f"Original video (Ybg30FpRVuw): {'✅ Working' if success1 else '❌ Failed'}")
    print(f"Alternate video found: {'✅ ' + working_url if working_url else '❌ None working'}")
    
    if working_url:
        print(f"\n💡 Recommendation: Use this working video URL for further testing")
    elif not success1:
        print(f"\n💡 Possible issues:")
        print(f"   - Video format compatibility")
        print(f"   - YouTube restrictions")
        print(f"   - Network/region restrictions")
        print(f"   - Video encoding issues")
