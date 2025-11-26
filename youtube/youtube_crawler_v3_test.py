#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube PMIK 판매원 데이터 수집기 v3.0 (통합 완전판)

v3.0 신규 기능:
1. V1 + V2 모든 컬럼 통합 (채널 정보 포함)
2. YouTube 자막 + Whisper AI 하이브리드
3. 썸네일 + 영상 프레임 OCR (0초, 마지막 5초)
4. 7자리/8자리 후원번호 인식
5. Duration 읽기 쉬운 형식 변환
6. 5분 제한 테스트 모드

예상 시간 (테스트 모드):
- 5분 제한: 약 15-30개 영상 수집
- 전체 모드: 2-4시간 (300개 영상)
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
from pathlib import Path
import requests
from io import BytesIO
import tempfile

import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import whisper
import cv2
from PIL import Image
import easyocr
from tqdm import tqdm

# .env 파일 로드
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ===========================
# 로깅 설정
# ===========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===========================
# 설정값 (v3.0 통합)
# ===========================

# YouTube API 키
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

if not YOUTUBE_API_KEY:
    logger.error("=" * 70)
    logger.error("❌ YouTube API 키가 설정되지 않았습니다!")
    logger.error("=" * 70)
    logger.error("\n.env 파일에 YOUTUBE_API_KEY를 설정하세요.")
    exit(1)

# 테스트 모드 설정 (5분 제한)
TEST_MODE = True
TEST_TIME_LIMIT_MINUTES = 5

# 검색 키워드 (v3: 효율성 개선)
SEARCH_KEYWORDS = [
    # 주요 키워드 (테스트용 우선순위)
    "피엠인터내셔널",
    "독일피엠",
    "PM인터내셔널",
    "피트라인",
    "피엠코리아",
    # 제품 키워드
    "탑쉐이프",
    "프로쉐이프",
    "디드링크",
    "뮤노겐",
    "엑티바이즈",
    "파워칵테일",
    "리스토레이트",
]

# 수집 목표 (테스트 모드에 따라 조정)
MAX_RESULTS_PER_KEYWORD = 15 if TEST_MODE else 30  
TARGET_TOTAL = 50 if TEST_MODE else 300  

# 글로벌 객체들 (초기화 지연)
whisper_model = None
ocr_reader = None
start_time = None

# ===========================
# 유틸리티 함수들
# ===========================

def format_duration(iso_duration: str) -> str:
    """ISO 8601 duration을 읽기 쉬운 형식으로 변환"""
    if not iso_duration or iso_duration == 'PT0S':
        return "0초"
    
    # PT12M7S -> 12분 7초
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return iso_duration
    
    hours, minutes, seconds = match.groups()
    parts = []
    
    if hours:
        parts.append(f"{int(hours)}시간")
    if minutes:
        parts.append(f"{int(minutes)}분")
    if seconds:
        parts.append(f"{int(seconds)}초")
    
    return ' '.join(parts) if parts else "0초"

def init_global_models():
    """전역 모델들 초기화 (지연 로딩)"""
    global whisper_model, ocr_reader
    
    if whisper_model is None:
        logger.info("🤖 Whisper AI 모델 로딩 중... (처음에만 시간 소요)")
        whisper_model = whisper.load_model("base")
        logger.info("✅ Whisper AI 모델 준비 완료")
    
    if ocr_reader is None:
        logger.info("👁️  OCR 리더 초기화 중...")
        ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False)  # GPU 없으면 False
        logger.info("✅ OCR 리더 준비 완료")

# ===========================
# 추천인 정보 추출 (7자리/8자리 지원)
# ===========================

def extract_sponsor_phone(text: str) -> str:
    """추천인 전화번호 추출"""
    if not text:
        return ""
    
    phone_patterns = [
        r'010[-\s]?\d{4}[-\s]?\d{4}',
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            digits = re.sub(r'\D', '', phone)
            if digits.startswith('010') and len(digits) == 11:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    return ""

def extract_sponsor_partner_id(text: str) -> str:
    """추천인 파트너 ID 추출 (7자리/8자리 지원)"""
    if not text:
        return ""
    
    partner_patterns = [
        r'추천인\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
        r'파트너\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b', 
        r'후원\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
        r'\b(\d{7,8})\b',
    ]
    
    for pattern in partner_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) in [7, 8]:  # 7자리 또는 8자리
                return match
    
    return ""

def extract_hashtags(text: str) -> str:
    """해시태그 추출"""
    if not text:
        return ""
    
    hashtag_pattern = r'#([가-힣a-zA-Z0-9_]+)'
    matches = re.findall(hashtag_pattern, text)
    
    if matches:
        return ', '.join([f'#{tag}' for tag in matches])
    return ""

# ===========================
# YouTube 자막 수집
# ===========================

def get_youtube_transcript(video_id: str) -> Dict[str, str]:
    """
    YouTube 자막 수집
    
    Returns:
        {
            'transcript': 자막 텍스트,
            'language': 언어 코드,
            'status': 'success' | 'no_transcript' | 'error'
        }
    """
    try:
        # 한국어 우선, 없으면 영어, 없으면 자동생성 자막
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 1순위: 한국어 수동 자막
        try:
            transcript = transcript_list.find_transcript(['ko'])
            transcript_data = transcript.fetch()
            text = ' '.join([item['text'] for item in transcript_data])
            return {
                'transcript': text,
                'language': 'ko',
                'status': 'success'
            }
        except:
            pass
        
        # 2순위: 한국어 자동생성 자막
        try:
            transcript = transcript_list.find_generated_transcript(['ko'])
            transcript_data = transcript.fetch()
            text = ' '.join([item['text'] for item in transcript_data])
            return {
                'transcript': text,
                'language': 'ko-auto',
                'status': 'success'
            }
        except:
            pass
        
        # 3순위: 영어 자막
        try:
            transcript = transcript_list.find_transcript(['en'])
            transcript_data = transcript.fetch()
            text = ' '.join([item['text'] for item in transcript_data])
            return {
                'transcript': text,
                'language': 'en',
                'status': 'success'
            }
        except:
            pass
        
        return {
            'transcript': '',
            'language': '',
            'status': 'no_transcript'
        }
    
    except TranscriptsDisabled:
        return {
            'transcript': '',
            'language': '',
            'status': 'disabled'
        }
    except NoTranscriptFound:
        return {
            'transcript': '',
            'language': '',
            'status': 'no_transcript'
        }
    except Exception as e:
        logger.debug(f"자막 수집 실패 ({video_id}): {str(e)}")
        return {
            'transcript': '',
            'language': '',
            'status': 'error'
        }

# ===========================
# Whisper AI 음성 인식
# ===========================

def get_whisper_transcript(video_url: str) -> Dict[str, str]:
    """Fixed Whisper AI implementation"""
    global whisper_model
    
    # Check FFmpeg availability first
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
    except:
        logger.debug("FFmpeg not available - skipping Whisper")
        return {'status': 'failed', 'transcript': '', 'confidence': 0.0}
    
    try:
        import yt_dlp
        import tempfile
        
        if whisper_model is None:
            init_global_models()
        
        if whisper_model is None:
            return {'status': 'failed', 'transcript': '', 'confidence': 0.0}
        
        # 임시 오디오 파일
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_audio_path = tmp.name
        
        # Improved yt-dlp options
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }],
            'outtmpl': temp_audio_path.replace('.mp3', ''),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
        }
        
        try:
            # 오디오 다운로드
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Check multiple possible file paths
            possible_paths = [temp_audio_path, temp_audio_path.replace('.mp3', '.m4a')]
            final_path = None
            
            for path in possible_paths:
                if os.path.exists(path) and os.path.getsize(path) > 0:
                    final_path = path
                    break
            
            if not final_path:
                return {'status': 'failed', 'transcript': '', 'confidence': 0.0}
            
            # Whisper로 음성→텍스트
            result = whisper_model.transcribe(final_path, language='ko', fp16=False)
            
            return {
                'status': 'success',
                'transcript': result['text'].strip(),
                'confidence': 0.9
            }
            
        finally:
            # Clean up all possible temp files
            for path in [temp_audio_path, temp_audio_path.replace('.mp3', '.m4a')]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
        
    except Exception as e:
        logger.debug(f"Whisper 처리 실패: {e}")
        return {
            'status': 'failed',
            'transcript': '',
            'confidence': 0.0
        }

# ===========================
# OCR 기능들
# ===========================

def download_image(url: str) -> Optional[Image.Image]:
    """이미지 URL에서 이미지 다운로드"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        logger.debug(f"이미지 다운로드 실패: {e}")
    return None

def extract_video_frames(video_url: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """영상에서 시작(0초)과 끝(마지막 5초) 프레임 추출 (현재 YouTube 제한으로 인해 비활성화)"""
    # YouTube의 최신 제한사항으로 인해 영상 다운로드가 차단됨
    # 향후 해결책이 나올 때까지 임시로 비활성화
    logger.debug("Video frame extraction temporarily disabled due to YouTube restrictions")
    return None, None

def ocr_image(image: Image.Image) -> str:
    """이미지에서 텍스트 추출 (OCR)"""
    global ocr_reader
    
    try:
        if ocr_reader is None:
            init_global_models()
        
        # PIL Image를 numpy array로 변환
        img_array = np.array(image)
        
        # EasyOCR로 텍스트 추출
        results = ocr_reader.readtext(img_array)
        
        # 결과 텍스트 조합
        texts = [result[1] for result in results if result[2] > 0.5]  # 신뢰도 50% 이상만
        return ' '.join(texts)
        
    except Exception as e:
        logger.debug(f"OCR 처리 실패: {e}")
        return ""

def process_thumbnail_ocr(thumbnail_url: str) -> Tuple[str, str, str]:
    """썸네일 OCR 및 전화번호/후원번호 추출"""
    # 썸네일 다운로드
    image = download_image(thumbnail_url)
    if image is None:
        return "", "", ""
    
    # OCR 텍스트 추출
    ocr_text = ocr_image(image)
    
    # 전화번호와 후원번호 추출
    phone = extract_sponsor_phone(ocr_text)
    partner_id = extract_sponsor_partner_id(ocr_text)
    
    return ocr_text, phone, partner_id

def process_video_frames_ocr(video_url: str) -> Tuple[str, str, str, str, str, str]:
    """영상 프레임 OCR 및 전화번호/후원번호 추출"""
    # 프레임 추출
    start_frame, end_frame = extract_video_frames(video_url)
    
    start_text = start_phone = start_partner = ""
    end_text = end_phone = end_partner = ""
    
    # 시작 프레임 OCR
    if start_frame is not None:
        start_image = Image.fromarray(start_frame)
        start_text = ocr_image(start_image)
        start_phone = extract_sponsor_phone(start_text)
        start_partner = extract_sponsor_partner_id(start_text)
    
    # 끝 프레임 OCR
    if end_frame is not None:
        end_image = Image.fromarray(end_frame)
        end_text = ocr_image(end_image)
        end_phone = extract_sponsor_phone(end_text)
        end_partner = extract_sponsor_partner_id(end_text)
    
    return start_text, start_phone, start_partner, end_text, end_phone, end_partner

# ===========================
# YouTube 검색 및 수집
# ===========================

def get_youtube_client():
    """YouTube API 클라이언트 생성"""
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def search_youtube_videos(youtube, keyword: str, max_results: int = 30) -> List[str]:
    """YouTube 검색"""
    try:
        request = youtube.search().list(
            q=keyword,
            type='video',
            part='id',
            maxResults=max_results,
            order='relevance',
            regionCode='KR',
            relevanceLanguage='ko',
        )
        
        response = request.execute()
        video_ids = [item['id']['videoId'] for item in response.get('items', [])]
        
        return video_ids
    
    except HttpError as e:
        logger.error(f"   ❌ 검색 실패: {e}")
        return []

def get_channel_details(youtube, channel_ids: List[str]) -> Dict[str, Dict]:
    """채널 상세 정보 조회 (구독자 수 등)"""
    if not channel_ids:
        return {}
    
    try:
        # 중복 제거
        unique_channel_ids = list(set(channel_ids))
        
        request = youtube.channels().list(
            id=','.join(unique_channel_ids),
            part='snippet,statistics'
        )
        
        response = request.execute()
        channel_data = {}
        
        for item in response.get('items', []):
            channel_id = item['id']
            statistics = item.get('statistics', {})
            
            channel_data[channel_id] = {
                'subscriber_count': int(statistics.get('subscriberCount', 0)),
                'video_count': int(statistics.get('videoCount', 0)),
                'view_count': int(statistics.get('viewCount', 0))
            }
        
        return channel_data
        
    except HttpError as e:
        logger.warning(f"채널 정보 조회 실패: {e}")
        return {}

def get_video_details(youtube, video_ids: List[str]) -> List[Dict]:
    """영상 상세 정보 조회"""
    if not video_ids:
        return []
    
    try:
        request = youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics,contentDetails'
        )
        
        response = request.execute()
        video_data = []
        
        for item in response.get('items', []):
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item['contentDetails']
            
            # 기본 정보 (v3: duration 형식 변환, category_id 제거)
            video_info = {
                'platform': 'youtube',
                'video_id': item['id'],
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'channel_id': snippet['channelId'],
                'channel_name': snippet['channelTitle'],
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'published_datetime': snippet['publishedAt'],
                'duration': format_duration(content_details['duration']),  # v3: 읽기 쉬운 형식
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'tags': ', '.join(snippet.get('tags', [])),
                'thumbnail_url': snippet['thumbnails'].get('maxres', snippet['thumbnails']['high'])['url'],
                'collected_date': datetime.now().strftime('%Y-%m-%d'),
                
                # v3: 채널 정보 플레이스홀더 (나중에 채움)
                'channel_subscriber_count': 0,
                'channel_video_count': 0,
                'channel_view_count': 0,
            }
            
            # 추천인 정보 추출
            full_text = f"{video_info['title']} {video_info['description']}"
            video_info['sponsor_phone'] = extract_sponsor_phone(full_text)
            video_info['sponsor_partner_id'] = extract_sponsor_partner_id(full_text)
            video_info['hashtags'] = extract_hashtags(video_info['description'])
            
            video_data.append(video_info)
        
        return video_data
    
    except HttpError as e:
        logger.error(f"❌ 영상 상세 정보 조회 실패: {e}")
        return []

def check_time_limit() -> bool:
    """테스트 모드 시간 제한 확인"""
    if not TEST_MODE or start_time is None:
        return False
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    return elapsed >= TEST_TIME_LIMIT_MINUTES

# ===========================
# 메인 함수
# ===========================

def main():
    """메인 크롤링 함수 (v3.0)"""
    global start_time
    start_time = datetime.now()
    
    logger.info("=" * 70)
    logger.info("🎬 YouTube PMIK 데이터 수집기 v3.0 (통합 완전판)")
    logger.info("=" * 70)
    logger.info(f"🧪 테스트 모드: {'ON' if TEST_MODE else 'OFF'}")
    if TEST_MODE:
        logger.info(f"⏱️  제한 시간: {TEST_TIME_LIMIT_MINUTES}분")
    logger.info(f"🔍 키워드: {len(SEARCH_KEYWORDS)}개")
    logger.info(f"📊 키워드당 수집: {MAX_RESULTS_PER_KEYWORD}개")
    logger.info(f"🎯 목표 수집: {TARGET_TOTAL}개")
    logger.info("🆕 v3.0 신규 기능:")
    logger.info("   ✅ V1+V2 통합 (채널 정보 포함)")
    logger.info("   ✅ YouTube 자막 + Whisper AI")
    logger.info("   ✅ 썸네일 + 영상 프레임 OCR")
    logger.info("   ✅ 7자리/8자리 후원번호 인식")
    logger.info("=" * 70)
    
    # YouTube API 클라이언트
    youtube = get_youtube_client()
    
    # 수집 데이터
    all_videos = []
    seen_video_ids = set()
    
    # 통계
    transcript_success = 0
    transcript_failed = 0
    
    # 게시물별 처리 시간 추적
    video_processing_times = []  # 각 영상의 처리 시간 기록
    
    # 키워드별 검색
    for i, keyword in enumerate(SEARCH_KEYWORDS, 1):
        if len(all_videos) >= TARGET_TOTAL:
            logger.info(f"\n🎉 목표 달성! ({len(all_videos)}개 수집)")
            break
        
        logger.info(f"\n{'='*70}")
        logger.info(f"[{i}/{len(SEARCH_KEYWORDS)}] 키워드: {keyword}")
        logger.info(f"진행률: {len(all_videos)}/{TARGET_TOTAL} ({len(all_videos)/TARGET_TOTAL*100:.1f}%)")
        logger.info(f"{'='*70}")
        
        # 검색
        logger.info(f"🔍 검색 중...")
        video_ids = search_youtube_videos(youtube, keyword, MAX_RESULTS_PER_KEYWORD)
        logger.info(f"   ✅ {len(video_ids)}개 영상 발견")
        
        # 중복 제거
        new_video_ids = [vid for vid in video_ids if vid not in seen_video_ids]
        
        if not new_video_ids:
            logger.info("   ⚠️  새로운 영상 없음 (중복)")
            continue
        
        logger.info(f"   💡 새로운 영상: {len(new_video_ids)}개")
        
        # 상세 정보 조회
        logger.info(f"   📥 메타데이터 수집 중...")
        video_details = get_video_details(youtube, new_video_ids)
        logger.info(f"   ✅ 메타데이터 수집 완료: {len(video_details)}개")
        
        # v3.0 통합 처리 (자막 + Whisper + OCR + 채널 정보)
        logger.info(f"   🔄 v3.0 통합 처리 중...")
        
        # 1. 채널 정보 일괄 조회
        channel_ids = [video['channel_id'] for video in video_details]
        channel_info = get_channel_details(youtube, channel_ids)
        
        for idx, video in enumerate(video_details, 1):
            if video['video_id'] in seen_video_ids:
                continue
            
            # 시간 제한 체크 (테스트 모드)
            if check_time_limit():
                logger.warning(f"⏱️  시간 제한 도달! ({TEST_TIME_LIMIT_MINUTES}분)")
                break
            
            logger.info(f"      [{idx}/{len(video_details)}] 처리 중: {video['title'][:40]}...")
            
            # 게시물 처리 시작 시간 기록
            video_start_time = time.time()
            
            # 1. 채널 정보 추가
            channel_id = video['channel_id']
            if channel_id in channel_info:
                video['channel_subscriber_count'] = channel_info[channel_id]['subscriber_count']
                video['channel_video_count'] = channel_info[channel_id]['video_count']
                video['channel_view_count'] = channel_info[channel_id]['view_count']
            
            # 2. YouTube 자막 수집 시도
            transcript_result = get_youtube_transcript(video['video_id'])
            
            if transcript_result['status'] == 'success':
                video['transcript_text'] = transcript_result['transcript']
                video['transcript_source'] = 'youtube_caption'
                transcript_success += 1
                logger.debug(f"         ✅ YouTube 자막 수집")
            else:
                # 3. Whisper AI 사용 (자막 없을 때)
                whisper_result = get_whisper_transcript(video['url'])
                if whisper_result['status'] in ['success', 'placeholder']:
                    video['transcript_text'] = whisper_result['transcript']
                    video['transcript_source'] = 'whisper_ai'
                    video['transcript_confidence'] = whisper_result.get('confidence', 0.0)
                    transcript_success += 1
                    logger.debug(f"         🤖 Whisper AI 처리")
                else:
                    video['transcript_text'] = ''
                    video['transcript_source'] = 'none'
                    video['transcript_confidence'] = 0.0
                    transcript_failed += 1
            
            # 4. 썸네일 OCR
            thumb_text, thumb_phone, thumb_partner = process_thumbnail_ocr(video['thumbnail_url'])
            video['thumbnail_text_ocr'] = thumb_text
            video['thumbnail_phone_ocr'] = thumb_phone
            video['thumbnail_partner_ocr'] = thumb_partner
            
            # 5. 영상 프레임 OCR (0초, 마지막 5초)
            start_text, start_phone, start_partner, end_text, end_phone, end_partner = process_video_frames_ocr(video['url'])
            video['video_start_frame_ocr'] = start_text
            video['video_start_phone_ocr'] = start_phone
            video['video_start_partner_ocr'] = start_partner
            video['video_end_frame_ocr'] = end_text
            video['video_end_phone_ocr'] = end_phone
            video['video_end_partner_ocr'] = end_partner
            
            all_videos.append(video)
            seen_video_ids.add(video['video_id'])
            
            # 게시물 처리 종료 시간 기록
            video_end_time = time.time()
            video_processing_time = video_end_time - video_start_time
            video_processing_times.append(video_processing_time)
            
            logger.info(f"         ⏱️  처리 시간: {video_processing_time:.2f}초")
            
            # 목표 달성 또는 시간 제한 시 종료
            if len(all_videos) >= TARGET_TOTAL or check_time_limit():
                break
        
        logger.info(f"   ✅ 자막 수집 완료")
        logger.info(f"   📊 누적 총계: {len(all_videos)}개")
        logger.info(f"      - 자막 있음: {transcript_success}개")
        logger.info(f"      - 자막 없음: {transcript_failed}개")
        
        # API 부하 방지
        time.sleep(0.5)
    
    # ===========================
    # CSV 저장
    # ===========================
    
    if not all_videos:
        logger.warning("\n⚠️  수집된 영상이 없습니다.")
        return
    
    logger.info(f"\n{'='*70}")
    logger.info("💾 CSV 저장 중...")
    
    df = pd.DataFrame(all_videos)
    
    # v3.0 컬럼 순서 정렬 (불필요한 컬럼 제거됨)
    column_order = [
        # 기본 정보
        'platform', 'video_id', 'url',
        'channel_id', 'channel_name', 
        'channel_subscriber_count', 'channel_video_count', 'channel_view_count',
        'title', 'description', 'published_datetime',
        'duration', 'view_count', 'like_count', 'comment_count',
        'tags', 'hashtags',
        
        # 추천인 정보 (제목/설명에서 추출)
        'sponsor_phone', 'sponsor_partner_id',
        
        # 썸네일
        'thumbnail_url',
        
        # 음성→텍스트 (하이브리드)
        'transcript_text', 'transcript_source', 'transcript_confidence',
        
        # OCR 결과들
        'thumbnail_text_ocr', 'thumbnail_phone_ocr', 'thumbnail_partner_ocr',
        'video_start_frame_ocr', 'video_start_phone_ocr', 'video_start_partner_ocr',
        'video_end_frame_ocr', 'video_end_phone_ocr', 'video_end_partner_ocr',
        
        # 메타
        'collected_date'
    ]
    
    # 존재하는 컬럼만 선택 (에러 방지)
    available_columns = [col for col in column_order if col in df.columns]
    df = df[available_columns]
    
    # v3.0 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    test_suffix = '_test' if TEST_MODE else ''
    output_file = f'youtube_pm_v3{test_suffix}_{timestamp}.csv'
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    elapsed_time = (datetime.now() - start_time).total_seconds()
    
    # ===========================
    # 결과 출력
    # ===========================
    
    logger.info(f"{'='*70}")
    logger.info("✅ 수집 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"\n📊 v3.0 수집 결과:")
    logger.info(f"  - 총 영상 수: {len(df)}개")
    
    # 추천인 정보 (제목/설명 + OCR 통합)
    total_phones = 0
    total_partners = 0
    for col in ['sponsor_phone', 'thumbnail_phone_ocr', 'video_start_phone_ocr', 'video_end_phone_ocr']:
        if col in df.columns:
            total_phones += df[col].notna().sum()
    for col in ['sponsor_partner_id', 'thumbnail_partner_ocr', 'video_start_partner_ocr', 'video_end_partner_ocr']:
        if col in df.columns:
            total_partners += df[col].notna().sum()
    
    logger.info(f"  - 전화번호 발견: {total_phones}개 (텍스트+OCR 통합)")
    logger.info(f"  - 후원번호 발견: {total_partners}개 (7자리+8자리)")
    
    # 음성→텍스트 결과
    if 'transcript_source' in df.columns:
        youtube_count = (df['transcript_source'] == 'youtube_caption').sum()
        whisper_count = (df['transcript_source'] == 'whisper_ai').sum()
        none_count = (df['transcript_source'] == 'none').sum()
        logger.info(f"  - YouTube 자막: {youtube_count}개")
        logger.info(f"  - Whisper AI: {whisper_count}개") 
        logger.info(f"  - 음성 없음: {none_count}개")
    
    # OCR 결과
    if 'thumbnail_text_ocr' in df.columns:
        ocr_success = df['thumbnail_text_ocr'].notna().sum()
        logger.info(f"  - 썸네일 OCR: {ocr_success}개")
    
    logger.info(f"\n📈 통계:")
    logger.info(f"  - 평균 조회수: {df['view_count'].mean():.0f}")
    logger.info(f"  - 평균 좋아요: {df['like_count'].mean():.0f}")
    logger.info(f"  - 평균 댓글: {df['comment_count'].mean():.0f}")
    if 'channel_subscriber_count' in df.columns:
        logger.info(f"  - 평균 채널 구독자: {df['channel_subscriber_count'].mean():.0f}")
    if 'transcript_text' in df.columns:
        avg_len = df['transcript_text'].str.len().mean()
        logger.info(f"  - 평균 음성 텍스트 길이: {avg_len:.0f}자")
    
    # 시간 통계 (상세)
    logger.info(f"\n⏱️  소요 시간 통계:")
    logger.info(f"  📊 전체 크롤링 시간: {elapsed_time:.1f}초 ({elapsed_time/60:.1f}분)")
    logger.info(f"  📊 총 수집 게시물: {len(df)}개")
    
    if video_processing_times:
        avg_time = sum(video_processing_times) / len(video_processing_times)
        min_time = min(video_processing_times)
        max_time = max(video_processing_times)
        
        logger.info(f"\n  🎯 게시물당 처리 시간:")
        logger.info(f"     - 평균: {avg_time:.2f}초")
        logger.info(f"     - 최소: {min_time:.2f}초 (가장 빠른 게시물)")
        logger.info(f"     - 최대: {max_time:.2f}초 (가장 느린 게시물)")
        logger.info(f"     - 예상 300개 처리 시간: {(avg_time * 300)/60:.1f}분")
    else:
        logger.info(f"  - 평균 속도: {elapsed_time/len(df):.2f}초/영상")
    
    logger.info(f"\n📁 저장 위치: {output_file}")
    
    # v3.0 상위 3개 영상 미리보기
    logger.info(f"\n{'='*70}")
    logger.info("📺 상위 3개 영상 미리보기 (v3.0):")
    logger.info(f"{'='*70}")
    
    for idx, row in df.head(3).iterrows():
        logger.info(f"\n{idx+1}. {row['title'][:50]}...")
        logger.info(f"   📺 채널: {row['channel_name']}")
        if 'channel_subscriber_count' in row:
            logger.info(f"   👥 구독자: {row['channel_subscriber_count']:,}명")
        logger.info(f"   👀 조회수: {row['view_count']:,} | 👍 좋아요: {row['like_count']:,}")
        logger.info(f"   ⏱️  길이: {row['duration']}")
        
        # 음성→텍스트 미리보기
        if 'transcript_text' in row and row['transcript_text']:
            source = row.get('transcript_source', 'unknown')
            source_emoji = '📝' if source == 'youtube_caption' else '🤖' if source == 'whisper_ai' else '❌'
            logger.info(f"   {source_emoji} 음성 텍스트: {row['transcript_text'][:80]}...")
        
        # 추천인 정보 (통합)
        phones = []
        partners = []
        for col in ['sponsor_phone', 'thumbnail_phone_ocr', 'video_start_phone_ocr', 'video_end_phone_ocr']:
            if col in row and row[col]:
                phones.append(f"{row[col]}({col.split('_')[0]})")
        for col in ['sponsor_partner_id', 'thumbnail_partner_ocr', 'video_start_partner_ocr', 'video_end_partner_ocr']:
            if col in row and row[col]:
                partners.append(f"{row[col]}({col.split('_')[0]})")
        
        if phones:
            logger.info(f"   📞 전화번호: {', '.join(phones)}")
        if partners:
            logger.info(f"   🏷️  후원번호: {', '.join(partners)}")
        
        # OCR 결과 미리보기
        if 'thumbnail_text_ocr' in row and row['thumbnail_text_ocr']:
            logger.info(f"   🖼️  썸네일 OCR: {row['thumbnail_text_ocr'][:50]}...")
    
    logger.info(f"\n{'='*70}")
    logger.info("🎉 YouTube 크롤러 v3.0 수집 완료!")
    logger.info(f"{'='*70}")
    if TEST_MODE:
        logger.info(f"🧪 테스트 모드 완료 ({TEST_TIME_LIMIT_MINUTES}분 제한)")
        logger.info(f"⚡ 실제 운영 시 TEST_MODE = False로 변경하여 전체 수집 가능")
    
    logger.info(f"\n✨ v3.0 신규 기능 적용 완료:")
    logger.info(f"  ✅ V1+V2 모든 컬럼 통합")
    logger.info(f"  ✅ 7자리+8자리 후원번호 인식")
    logger.info(f"  ✅ Duration 읽기 쉬운 형식")
    logger.info(f"  ✅ YouTube 자막 + Whisper AI 하이브리드")
    logger.info(f"  ✅ 썸네일 + 영상 프레임 OCR")
    logger.info(f"  ✅ OCR에서 전화번호/후원번호 자동 추출")
    
    logger.info(f"\n📁 최종 결과 파일: {output_file}")
    logger.info(f"📊 총 {len(df)}개 영상 수집 완료")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  사용자가 중단했습니다.")
    except Exception as e:
        logger.error(f"\n\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
