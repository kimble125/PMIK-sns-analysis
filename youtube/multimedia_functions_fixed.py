#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed multimedia processing functions for YouTube Crawler V3
Addresses the issues found in testing:
1. FFmpeg dependency for Whisper AI
2. Video download problems with yt-dlp
3. OpenCV video reading issues
4. Improved error handling and fallbacks
"""

import os
import json
import time
import logging
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import numpy as np
import cv2
from PIL import Image
import easyocr
import whisper
import yt_dlp
import requests
from io import BytesIO

# Setup logging
logger = logging.getLogger(__name__)

# Global objects (initialized once)
whisper_model = None
ocr_reader = None

def init_global_models():
    """Initialize global models with proper error handling"""
    global whisper_model, ocr_reader
    
    try:
        if whisper_model is None:
            logger.info("🤖 Initializing Whisper AI model...")
            whisper_model = whisper.load_model("base")
            logger.info("✅ Whisper AI model ready")
    except Exception as e:
        logger.error(f"❌ Whisper model initialization failed: {e}")
        whisper_model = None
    
    try:
        if ocr_reader is None:
            logger.info("👁️  Initializing OCR reader...")
            ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False)
            logger.info("✅ OCR reader ready")
    except Exception as e:
        logger.error(f"❌ OCR reader initialization failed: {e}")
        ocr_reader = None

def check_ffmpeg_availability() -> bool:
    """Check if FFmpeg is available"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        return result.returncode == 0
    except Exception:
        return False

def get_whisper_transcript_fixed(video_url: str) -> Dict[str, str]:
    """
    Fixed Whisper AI implementation with proper error handling
    """
    global whisper_model
    
    # Check FFmpeg first
    if not check_ffmpeg_availability():
        logger.warning("FFmpeg not available - skipping Whisper processing")
        return {
            'status': 'failed',
            'transcript': '',
            'confidence': 0.0,
            'error': 'FFmpeg not installed'
        }
    
    try:
        # Initialize model if needed
        if whisper_model is None:
            init_global_models()
            
        if whisper_model is None:
            return {
                'status': 'failed',
                'transcript': '',
                'confidence': 0.0,
                'error': 'Whisper model initialization failed'
            }
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_audio_path = tmp.name
        
        try:
            # Improved yt-dlp options for audio extraction
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',  # Low quality for speed
                }],
                'outtmpl': temp_audio_path.replace('.mp3', ''),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writethumbnail': False,
                'writeinfojson': False,
                'ignoreerrors': True,
            }
            
            # Download audio with timeout
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Check if file was created
            if not os.path.exists(temp_audio_path):
                # Try alternative file extension
                alt_path = temp_audio_path.replace('.mp3', '.m4a')
                if os.path.exists(alt_path):
                    temp_audio_path = alt_path
                else:
                    return {
                        'status': 'failed',
                        'transcript': '',
                        'confidence': 0.0,
                        'error': 'Audio download failed'
                    }
            
            # Transcribe with Whisper
            logger.debug(f"Transcribing audio file: {temp_audio_path}")
            result = whisper_model.transcribe(
                temp_audio_path, 
                language='ko',  # Korean preferred
                fp16=False,  # Better compatibility
                verbose=False
            )
            
            return {
                'status': 'success',
                'transcript': result['text'].strip(),
                'confidence': 0.9,  # Whisper doesn't provide confidence scores
                'language': result.get('language', 'ko')
            }
            
        finally:
            # Clean up temporary files
            for path in [temp_audio_path, temp_audio_path.replace('.mp3', '.m4a')]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        logger.debug(f"Failed to remove temp file {path}: {e}")
        
    except Exception as e:
        logger.debug(f"Whisper processing failed for {video_url}: {e}")
        return {
            'status': 'failed',
            'transcript': '',
            'confidence': 0.0,
            'error': str(e)
        }

def extract_video_frames_fixed(video_url: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Fixed video frame extraction with better download options and error handling
    """
    try:
        # Create temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            temp_video_path = tmp.name
        
        try:
            # Improved yt-dlp options for video download
            ydl_opts = {
                'format': 'worst[height<=360][ext=mp4]/worst[ext=mp4]/worst',  # Small, compatible format
                'outtmpl': temp_video_path,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'writethumbnail': False,
                'writeinfojson': False,
                'ignoreerrors': True,
                'http_chunk_size': 10485760,  # 10MB chunks
                'fragment_retries': 3,
                'retries': 3,
            }
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                # Verify download
                if not os.path.exists(temp_video_path) or os.path.getsize(temp_video_path) == 0:
                    logger.debug(f"Video download failed or empty file: {temp_video_path}")
                    return None, None
            
            # Try to open with OpenCV
            cap = cv2.VideoCapture(temp_video_path)
            
            if not cap.isOpened():
                logger.debug(f"OpenCV failed to open video: {temp_video_path}")
                return None, None
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            
            if frame_count == 0 or fps == 0:
                logger.debug(f"Invalid video properties: frames={frame_count}, fps={fps}")
                cap.release()
                return None, None
            
            # Extract start frame (0 seconds)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret1, start_frame = cap.read()
            
            # Extract end frame (last 10% or minimum 5 seconds from end)
            end_frame_pos = max(0, frame_count - int(fps * min(5, duration * 0.1)))
            cap.set(cv2.CAP_PROP_POS_FRAMES, end_frame_pos)
            ret2, end_frame = cap.read()
            
            cap.release()
            
            # Validate frames
            start_frame = start_frame if ret1 and start_frame is not None else None
            end_frame = end_frame if ret2 and end_frame is not None else None
            
            logger.debug(f"Frame extraction: start={'✅' if start_frame is not None else '❌'}, "
                        f"end={'✅' if end_frame is not None else '❌'}")
            
            return start_frame, end_frame
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception as e:
                    logger.debug(f"Failed to remove temp video: {e}")
                    
    except Exception as e:
        logger.debug(f"Video frame extraction failed for {video_url}: {e}")
        return None, None

def ocr_image_fixed(image: Image.Image) -> str:
    """Fixed OCR with better preprocessing and error handling"""
    global ocr_reader
    
    try:
        if ocr_reader is None:
            init_global_models()
            
        if ocr_reader is None:
            return ""
        
        # Convert PIL to numpy array
        img_array = np.array(image)
        
        # Preprocess image for better OCR
        if len(img_array.shape) == 3:
            # Convert to grayscale if needed
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            # Enhance contrast
            enhanced = cv2.equalizeHist(gray)
            img_array = enhanced
        
        # Run OCR with lower confidence threshold
        results = ocr_reader.readtext(img_array, detail=1)
        
        # Extract text with confidence filtering
        texts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.3:  # Lower threshold for more results
                texts.append(text)
        
        return ' '.join(texts)
        
    except Exception as e:
        logger.debug(f"OCR processing failed: {e}")
        return ""

def process_video_frames_ocr_fixed(video_url: str) -> Tuple[str, str, str, str, str, str]:
    """
    Fixed complete video frame OCR process
    """
    # Import extraction functions from main module
    from youtube_crawler_v3_test import extract_sponsor_phone, extract_sponsor_partner_id
    
    try:
        # Extract frames
        start_frame, end_frame = extract_video_frames_fixed(video_url)
        
        # Initialize return values
        start_text = start_phone = start_partner = ""
        end_text = end_phone = end_partner = ""
        
        # Process start frame
        if start_frame is not None:
            try:
                start_image = Image.fromarray(cv2.cvtColor(start_frame, cv2.COLOR_BGR2RGB))
                start_text = ocr_image_fixed(start_image)
                start_phone = extract_sponsor_phone(start_text)
                start_partner = extract_sponsor_partner_id(start_text)
                logger.debug(f"Start frame OCR: '{start_text[:50]}...'")
            except Exception as e:
                logger.debug(f"Start frame processing failed: {e}")
        
        # Process end frame
        if end_frame is not None:
            try:
                end_image = Image.fromarray(cv2.cvtColor(end_frame, cv2.COLOR_BGR2RGB))
                end_text = ocr_image_fixed(end_image)
                end_phone = extract_sponsor_phone(end_text)
                end_partner = extract_sponsor_partner_id(end_text)
                logger.debug(f"End frame OCR: '{end_text[:50]}...'")
            except Exception as e:
                logger.debug(f"End frame processing failed: {e}")
        
        return start_text, start_phone, start_partner, end_text, end_phone, end_partner
        
    except Exception as e:
        logger.debug(f"Video frame OCR failed for {video_url}: {e}")
        return "", "", "", "", "", ""

# Test function
def test_fixed_functions():
    """Test the fixed multimedia functions"""
    test_url = "https://www.youtube.com/watch?v=Ybg30FpRVuw"
    
    print("🧪 Testing Fixed Multimedia Functions")
    print("=" * 50)
    
    # Test Whisper
    print("Testing Whisper AI...")
    whisper_result = get_whisper_transcript_fixed(test_url)
    print(f"Whisper Status: {whisper_result['status']}")
    if whisper_result['status'] == 'success':
        print(f"Transcript: {whisper_result['transcript'][:100]}...")
    else:
        print(f"Error: {whisper_result.get('error', 'Unknown error')}")
    
    # Test video frames
    print("\nTesting Video Frame Extraction...")
    start_frame, end_frame = extract_video_frames_fixed(test_url)
    print(f"Start Frame: {'✅ Success' if start_frame is not None else '❌ Failed'}")
    print(f"End Frame: {'✅ Success' if end_frame is not None else '❌ Failed'}")
    
    # Test complete OCR
    print("\nTesting Video Frame OCR...")
    ocr_result = process_video_frames_ocr_fixed(test_url)
    start_text, start_phone, start_partner, end_text, end_phone, end_partner = ocr_result
    print(f"Start OCR: '{start_text}'")
    print(f"End OCR: '{end_text}'")
    
    return whisper_result, (start_frame, end_frame), ocr_result

if __name__ == "__main__":
    test_fixed_functions()
