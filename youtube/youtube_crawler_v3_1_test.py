#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Colab용 YouTube 크롤러 v3.1 (1시간 백그라운드 실행)
완전한 멀티미디어 처리 + 체크포인트 + Drive 저장
"""

import os
import json
import time
import signal
import sys
import subprocess
import tempfile
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re

import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import whisper
import cv2
from PIL import Image
import easyocr
from tqdm import tqdm
import requests
from io import BytesIO

# =================================
# 설정 및 전역 변수
# =================================

# YouTube API 키 (.env 파일에서 로드)
import os
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

if not YOUTUBE_API_KEY:
    print("❌ .env 파일에 YOUTUBE_API_KEY를 설정하세요!")
    exit(1)

# 크롤링 설정
TOTAL_RUNTIME_HOURS = 0.5  # 30분
CHECKPOINT_INTERVAL = 300   # 5분마다 통계 출력
TARGET_VIDEOS = None  # 제한 없음 (시간 내 최대한 수집)
GRACEFUL_SHUTDOWN_MINUTES = 3  # 여유 시간

KEYWORDS = [
    "피엠인터내셔널", "독일피엠", "PM인터내셔널", "피트라인", "피엠코리아",
    "탑쉐이프", "프로쉐이프", "디드링크", "뮤노겐", "엑티바이즈", 
    "파워칵테일", "리스토레이트"
]

# 전역 변수
whisper_model = None
ocr_reader = None
youtube_client = None
start_time = None
collected_videos = []

# API 쿼터 추적
api_quota_used = {
    'search': 0,      # 검색: 100 units/call
    'videos': 0,      # 비디오 상세: 1 unit/call
    'channels': 0,    # 채널 정보: 1 unit/call
    'total': 0
}

# =================================
# 체크포인트 및 상태 관리
# =================================

def setup_logging():
    """로깅 설정"""
    os.makedirs('./logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('./logs/crawler.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def print_progress_stats():
    """진행 상황 통계 출력"""
    if not collected_videos:
        return
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    count = len(collected_videos)
    speed = count / elapsed if elapsed > 0 else 0
    
    # 자막 성공률
    with_transcript = sum(1 for v in collected_videos if v.get('transcript_text', '').strip())
    transcript_rate = with_transcript / count * 100 if count > 0 else 0
    
    logger.info(f"\n📊 === 진행 상황 ({elapsed:.1f}분 경과) ===")
    logger.info(f"   수집: {count}개 ({speed:.2f}개/분)")
    logger.info(f"   음성인식: {with_transcript}개 ({transcript_rate:.1f}%)")
    logger.info(f"   API 쿼터 사용: {api_quota_used['total']:,} units")
    logger.info(f"   남은 시간: {get_remaining_time():.1f}분")
    logger.info(f"========================================\n")

def signal_handler(signum, frame):
    """종료 신호 처리"""
    logger.info("🔔 종료 신호 감지! 데이터 저장 중...")
    save_final_results(collected_videos)
    sys.exit(0)

def check_time_limit():
    """시간 제한 확인"""
    if start_time is None:
        return False
    elapsed = (datetime.now() - start_time).total_seconds() / 3600
    return elapsed >= TOTAL_RUNTIME_HOURS

def check_graceful_shutdown():
    """작업 완료를 위한 여유 시간 확인"""
    if start_time is None:
        return False
    elapsed = (datetime.now() - start_time).total_seconds() / 3600
    # 8분 경과시 새로운 작업 중단, 현재 작업만 완료
    return elapsed >= (TOTAL_RUNTIME_HOURS - GRACEFUL_SHUTDOWN_MINUTES / 60)

def get_remaining_time():
    """남은 시간 계산 (분 단위)"""
    if start_time is None:
        return TOTAL_RUNTIME_HOURS * 60
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    return (TOTAL_RUNTIME_HOURS * 60) - elapsed

# =================================
# 초기화 및 API 설정
# =================================

def init_youtube_client():
    """YouTube API 클라이언트"""
    global youtube_client
    if YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        raise ValueError("❌ YouTube API 키를 설정하세요!")
    
    youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    logger.info("✅ YouTube API 준비 완료")

def init_ai_models():
    """AI 모델 초기화"""
    global whisper_model, ocr_reader
    
    try:
        logger.info("🤖 Whisper 모델 로딩...")
        whisper_model = whisper.load_model("base")
        logger.info("✅ Whisper 준비 완료")
    except Exception as e:
        logger.error(f"❌ Whisper 초기화 실패: {e}")
    
    try:
        logger.info("👁️ OCR 리더 초기화...")
        ocr_reader = easyocr.Reader(['ko', 'en'], gpu=True)
        logger.info("✅ OCR 준비 완료")
    except Exception as e:
        logger.error(f"❌ OCR 초기화 실패: {e}")

# =================================
# 유틸리티 함수들
# =================================

def format_duration(iso_duration: str) -> str:
    """ISO 8601 duration 변환"""
    if not iso_duration or iso_duration == 'PT0S':
        return "0초"
    
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

def extract_sponsor_phone(text: str) -> str:
    """전화번호 추출"""
    if not text:
        return ""
    
    pattern = r'010[-\s]?\d{4}[-\s]?\d{4}'
    match = re.search(pattern, text)
    if match:
        phone = match.group(0)
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('010') and len(digits) == 11:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return ""

def extract_sponsor_partner_id(text: str) -> str:
    """파트너 ID 추출"""
    if not text:
        return ""
    
    patterns = [
        r'추천인\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
        r'파트너\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b', 
        r'후원\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
        r'\b(\d{7,8})\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) in [7, 8]:
                return match
    return ""

def extract_hashtags(text: str) -> str:
    """해시태그 추출"""
    if not text:
        return ""
    
    matches = re.findall(r'#([가-힣a-zA-Z0-9_]+)', text)
    return ', '.join([f'#{tag}' for tag in matches]) if matches else ""

# =================================
# YouTube API 함수들
# =================================

def search_videos(keyword: str, max_results: int = 20):
    """유튜브 검색"""
    try:
        request = youtube_client.search().list(
            q=keyword,
            type='video',
            part='id',
            maxResults=max_results,
            order='relevance',
            regionCode='KR',
            relevanceLanguage='ko'
        )
        response = request.execute()
        
        # API 쿼터 기록 (search = 100 units)
        api_quota_used['search'] += 100
        api_quota_used['total'] += 100
        
        return [item['id']['videoId'] for item in response.get('items', [])]
    except HttpError as e:
        logger.error(f"❌ 검색 실패 ({keyword}): {e}")
        return []

def get_video_details(video_ids: List[str]):
    """비디오 상세 정보"""
    if not video_ids:
        return []
    
    try:
        request = youtube_client.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics,contentDetails'
        )
        response = request.execute()
        
        # API 쿼터 기록 (videos.list = 1 unit)
        api_quota_used['videos'] += 1
        api_quota_used['total'] += 1
        
        videos = []
        for item in response.get('items', []):
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item['contentDetails']
            
            video_info = {
                'platform': 'youtube',
                'video_id': item['id'],
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'channel_id': snippet['channelId'],
                'channel_name': snippet['channelTitle'],
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'published_datetime': snippet['publishedAt'],
                'duration': format_duration(content_details['duration']),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'tags': ', '.join(snippet.get('tags', [])),
                'thumbnail_url': snippet['thumbnails'].get('maxres', snippet['thumbnails']['high'])['url'],
                'collected_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            # 기본 텍스트에서 정보 추출
            full_text = f"{video_info['title']} {video_info['description']}"
            video_info['sponsor_phone'] = extract_sponsor_phone(full_text)
            video_info['sponsor_partner_id'] = extract_sponsor_partner_id(full_text)
            video_info['hashtags'] = extract_hashtags(video_info['description'])
            
            videos.append(video_info)
        
        return videos
        
    except HttpError as e:
        logger.error(f"❌ 비디오 상세 조회 실패: {e}")
        return []

# =================================
# 멀티미디어 처리
# =================================

def get_youtube_transcript(video_id: str):
    """YouTube 자막 수집"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 한국어 우선
        for lang_code in ['ko', 'en']:
            try:
                transcript = transcript_list.find_transcript([lang_code])
                transcript_data = transcript.fetch()
                text = ' '.join([item['text'] for item in transcript_data])
                logger.debug(f"✅ YouTube 자막 성공 ({lang_code}): {len(text)}자")
                return {'transcript': text, 'source': 'youtube_caption', 'confidence': 1.0}
            except Exception as e:
                logger.debug(f"언어 {lang_code} 자막 없음: {e}")
                continue
        
        # 자동생성 자막
        try:
            transcript = transcript_list.find_generated_transcript(['ko'])
            transcript_data = transcript.fetch()
            text = ' '.join([item['text'] for item in transcript_data])
            logger.debug(f"✅ 자동생성 자막 성공: {len(text)}자")
            return {'transcript': text, 'source': 'youtube_auto', 'confidence': 0.8}
        except Exception as e:
            logger.debug(f"자동생성 자막 실패: {e}")
    except Exception as e:
        logger.debug(f"❌ YouTube 자막 완전 실패 ({video_id}): {type(e).__name__} - {e}")
    
    return {'transcript': '', 'source': 'none', 'confidence': 0.0}

def get_whisper_transcript(video_url: str):
    """Whisper AI 음성인식"""
    if whisper_model is None:
        logger.warning("⚠️ Whisper 모델이 로드되지 않음")
        return {'transcript': '', 'source': 'none', 'confidence': 0.0}
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_path = tmp.name
        
        # yt-dlp로 오디오 추출 (더 많은 재시도 옵션)
        cmd = [
            'yt-dlp', '-x', '--audio-format', 'mp3', 
            '--audio-quality', '64K', '--no-warnings',
            '--retries', '3',  # 재시도 3회
            '--socket-timeout', '30',  # 소켓 타임아웃
            '-o', temp_path.replace('.mp3', ''), video_url
        ]
        
        logger.debug(f"🎵 오디오 다운로드 시작: {video_url}")
        result = subprocess.run(cmd, capture_output=True, timeout=300)  # 5분으로 증가
        
        # 다운로드 실패 체크
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            logger.warning(f"❌ yt-dlp 실패 (코드 {result.returncode}): {stderr[:200]}")
            return {'transcript': '', 'source': 'download_failed', 'confidence': 0.0}
        
        # 다양한 확장자 확인
        found_audio = False
        for ext in ['.mp3', '.m4a', '.webm', '.opus']:
            audio_path = temp_path.replace('.mp3', ext)
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                if file_size > 0:
                    found_audio = True
                    logger.debug(f"✅ 오디오 파일 확인: {ext} ({file_size:,} bytes)")
                    
                    logger.debug(f"🤖 Whisper 음성인식 시작...")
                    result = whisper_model.transcribe(audio_path, language='ko', fp16=False)
                    transcript = result['text'].strip()
                    
                    logger.debug(f"✅ Whisper 성공: {len(transcript)}자")
                    
                    # 정리
                    os.remove(audio_path)
                    return {'transcript': transcript, 'source': 'whisper_ai', 'confidence': 0.9}
                else:
                    logger.warning(f"⚠️ 오디오 파일이 비어있음: {ext}")
        
        if not found_audio:
            logger.warning(f"❌ 오디오 파일을 찾을 수 없음")
        
    except subprocess.TimeoutExpired:
        logger.warning(f"❌ Whisper 타임아웃 (300초 초과)")
    except Exception as e:
        logger.warning(f"❌ Whisper 처리 실패: {type(e).__name__} - {e}")
    
    # 정리
    if temp_path:
        for ext in ['.mp3', '.m4a', '.webm', '.opus']:
            path = temp_path.replace('.mp3', ext)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.debug(f"임시 파일 삭제 실패: {e}")
    
    return {'transcript': '', 'source': 'failed', 'confidence': 0.0}

def process_thumbnail_ocr(thumbnail_url: str):
    """썸네일 OCR"""
    if ocr_reader is None:
        return "", "", ""
    
    try:
        response = requests.get(thumbnail_url, timeout=10)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            img_array = np.array(image)
            
            results = ocr_reader.readtext(img_array)
            texts = [result[1] for result in results if result[2] > 0.3]
            ocr_text = ' '.join(texts)
            
            phone = extract_sponsor_phone(ocr_text)
            partner_id = extract_sponsor_partner_id(ocr_text)
            
            return ocr_text, phone, partner_id
    except Exception as e:
        logger.debug(f"썸네일 OCR 실패: {e}")
    
    return "", "", ""

def process_video_frame_ocr(video_url: str):
    """영상 프레임 OCR (첫 장면 + 마지막 장면)"""
    if ocr_reader is None:
        logger.warning("⚠️ OCR 리더가 초기화되지 않음")
        return "", "", "", "", "", ""
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            temp_path = tmp.name
        
        # yt-dlp로 영상 다운로드 (최저 화질로 빠르게)
        cmd = [
            'yt-dlp', '--format', 'worst[ext=mp4]',
            '--no-warnings', '--retries', '2',
            '--socket-timeout', '20',
            '-o', temp_path, video_url
        ]
        
        logger.debug(f"🎥 영상 다운로드 시작: {video_url}")
        result = subprocess.run(cmd, capture_output=True, timeout=120)  # 2분
        
        if result.returncode != 0:
            logger.debug(f"❌ 영상 다운로드 실패")
            return "", "", "", "", "", ""
        
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            logger.debug(f"❌ 영상 파일이 비어있음")
            return "", "", "", "", "", ""
        
        # OpenCV로 프레임 추출
        cap = cv2.VideoCapture(temp_path)
        
        if not cap.isOpened():
            logger.debug(f"❌ OpenCV 영상 열기 실패")
            os.remove(temp_path)
            return "", "", "", "", "", ""
        
        # 첫 장면 (0초)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret1, start_frame = cap.read()
        
        start_text = start_phone = start_partner = ""
        if ret1 and start_frame is not None:
            # OpenCV BGR -> RGB 변환
            start_frame_rgb = cv2.cvtColor(start_frame, cv2.COLOR_BGR2RGB)
            results = ocr_reader.readtext(start_frame_rgb)
            texts = [result[1] for result in results if result[2] > 0.3]
            start_text = ' '.join(texts)
            start_phone = extract_sponsor_phone(start_text)
            start_partner = extract_sponsor_partner_id(start_text)
            logger.debug(f"✅ 첫 장면 OCR: {len(start_text)}자")
        
        # 마지막 장면 (끝 5초 전)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            end_frame_pos = max(0, frame_count - int(fps * 5))
            cap.set(cv2.CAP_PROP_POS_FRAMES, end_frame_pos)
            ret2, end_frame = cap.read()
            
            end_text = end_phone = end_partner = ""
            if ret2 and end_frame is not None:
                end_frame_rgb = cv2.cvtColor(end_frame, cv2.COLOR_BGR2RGB)
                results = ocr_reader.readtext(end_frame_rgb)
                texts = [result[1] for result in results if result[2] > 0.3]
                end_text = ' '.join(texts)
                end_phone = extract_sponsor_phone(end_text)
                end_partner = extract_sponsor_partner_id(end_text)
                logger.debug(f"✅ 마지막 장면 OCR: {len(end_text)}자")
        else:
            end_text = end_phone = end_partner = ""
        
        cap.release()
        os.remove(temp_path)
        
        return start_text, start_phone, start_partner, end_text, end_phone, end_partner
        
    except subprocess.TimeoutExpired:
        logger.debug(f"❌ 영상 다운로드 타임아웃")
    except Exception as e:
        logger.debug(f"❌ 영상 프레임 OCR 실패: {type(e).__name__} - {e}")
    
    # 정리
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass
    
    return "", "", "", "", "", ""

def process_single_video(video_info: dict):
    """단일 비디오 완전 처리"""
    video_id = video_info['video_id']
    video_url = video_info['url']
    
    logger.info(f"  🔄 처리: {video_info['title'][:40]}...")
    
    # 1. 자막 시도
    transcript_result = get_youtube_transcript(video_id)
    
    if transcript_result['transcript']:
        video_info.update({
            'transcript_text': transcript_result['transcript'],
            'transcript_source': transcript_result['source'],
            'transcript_confidence': transcript_result['confidence']
        })
        logger.info(f"    ✅ 자막 성공")
    else:
        # 2. Whisper 시도
        whisper_result = get_whisper_transcript(video_url)
        video_info.update({
            'transcript_text': whisper_result['transcript'],
            'transcript_source': whisper_result['source'],
            'transcript_confidence': whisper_result['confidence']
        })
        if whisper_result['transcript']:
            logger.info(f"    🤖 Whisper 성공")
        else:
            logger.info(f"    ❌ 음성인식 실패")
    
    # 3. 썸네일 OCR
    thumb_text, thumb_phone, thumb_partner = process_thumbnail_ocr(video_info['thumbnail_url'])
    video_info.update({
        'thumbnail_text_ocr': thumb_text,
        'thumbnail_phone_ocr': thumb_phone,
        'thumbnail_partner_ocr': thumb_partner
    })
    
    if thumb_text:
        logger.info(f"    👁️ 썸네일 OCR 성공")
    
    # 4. 영상 프레임 OCR (첫 장면 + 마지막 장면)
    start_text, start_phone, start_partner, end_text, end_phone, end_partner = process_video_frame_ocr(video_url)
    video_info.update({
        'video_start_frame_ocr': start_text,
        'video_start_phone_ocr': start_phone,
        'video_start_partner_ocr': start_partner,
        'video_end_frame_ocr': end_text,
        'video_end_phone_ocr': end_phone,
        'video_end_partner_ocr': end_partner
    })
    
    if start_text or end_text:
        logger.info(f"    🎥 영상 프레임 OCR 성공")
    
    return video_info

# =================================
# 메인 크롤링 로직
# =================================

def main_crawling_loop():
    """메인 크롤링 루프 (30분 - 최대한 수집)"""
    global collected_videos
    
    collected_videos = []  # 체크포인트 복구 없음
    seen_video_ids = set()
    
    logger.info(f"🎯 목표: 시간 내 최대한 수집")
    logger.info(f"⏱️ 제한: {TOTAL_RUNTIME_HOURS * 60:.0f}분 (30분)")
    logger.info(f"🛡️ 안전 종료: {TOTAL_RUNTIME_HOURS * 60 - GRACEFUL_SHUTDOWN_MINUTES:.0f}분 후 새 작업 중단")
    
    last_stats_print = time.time()
    graceful_mode = False
    
    for keyword in KEYWORDS:
        # 시간 완전 종료 체크
        if check_time_limit():
            logger.info(f"⏱️ 30분 시간 제한 도달! 크롤링 종료")
            break
        
        # Graceful shutdown 모드 진입 체크
        if check_graceful_shutdown() and not graceful_mode:
            graceful_mode = True
            remaining = get_remaining_time()
            logger.info(f"🛡️ 안전 종료 모드 진입! 남은시간: {remaining:.1f}분")
            logger.info(f"   현재 처리중인 작업들만 완료하고 종료합니다.")
        
        # Graceful mode에서는 새로운 키워드 검색 중단
        if graceful_mode:
            logger.info(f"🛡️ 안전 종료 모드: 새로운 검색 중단")
            break
            
        logger.info(f"\n🔍 검색: {keyword}")
        remaining = get_remaining_time()
        logger.info(f"⏱️ 남은시간: {remaining:.1f}분")
        
        video_ids = search_videos(keyword)
        new_video_ids = [vid for vid in video_ids if vid not in seen_video_ids]
        
        if not new_video_ids:
            logger.info(f"  ⚠️ 새로운 비디오 없음")
            continue
        
        logger.info(f"  📥 메타데이터: {len(new_video_ids)}개")
        video_details = get_video_details(new_video_ids)
        
        for i, video in enumerate(video_details):
            # 각 비디오 처리 전에 시간 체크
            if check_time_limit():
                logger.info(f"⏱️ 시간 제한 도달! 처리 중단")
                break
            
            # Graceful shutdown 체크 (새로운 비디오 시작 금지)
            if check_graceful_shutdown():
                logger.info(f"🛡️ 안전 종료 시간: 새로운 비디오 처리 중단")
                break
            
            logger.info(f"  [{i+1}/{len(video_details)}] 처리 시작...")
            processed_video = process_single_video(video)
            collected_videos.append(processed_video)
            seen_video_ids.add(video['video_id'])
            
            # 진행 상황 통계 출력 (5분마다)
            if time.time() - last_stats_print > CHECKPOINT_INTERVAL:
                print_progress_stats()
                last_stats_print = time.time()
            
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            remaining = get_remaining_time()
            logger.info(f"  📊 진행: {len(collected_videos)}개 | 경과: {elapsed:.1f}분 | 남음: {remaining:.1f}분")
            
            # 시간이 촉박하면 sleep 줄이기
            if remaining < 10:
                time.sleep(1)
            else:
                time.sleep(2)  # API 부하 방지
    
    # 최종 통계
    final_elapsed = (datetime.now() - start_time).total_seconds() / 60
    logger.info(f"\n🏁 크롤링 루프 완료!")
    logger.info(f"⏱️ 총 소요시간: {final_elapsed:.1f}분")
    logger.info(f"📊 수집된 비디오: {len(collected_videos)}개")
    if final_elapsed > 0:
        logger.info(f"📊 수집 속도: {len(collected_videos)/final_elapsed:.2f}개/분")
    logger.info(f"📊 API 쿼터 사용: {api_quota_used['total']:,} units")
    
    return collected_videos

def generate_report(videos: List[dict], csv_path: str, elapsed_minutes: float):
    """상세 리포트 생성"""
    if not videos:
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = csv_path.replace('.csv', '_report.txt')
    
    df = pd.DataFrame(videos)
    
    # 통계 계산
    total_count = len(df)
    
    # 음성인식 통계
    with_transcript = (df['transcript_text'].notna() & (df['transcript_text'].str.strip() != '')).sum()
    transcript_rate = with_transcript / total_count * 100 if total_count > 0 else 0
    
    # 소스별 분포
    source_dist = df['transcript_source'].value_counts().to_dict()
    youtube_caption = source_dist.get('youtube_caption', 0)
    youtube_auto = source_dist.get('youtube_auto', 0)
    whisper_ai = source_dist.get('whisper_ai', 0)
    failed = source_dist.get('failed', 0) + source_dist.get('none', 0)
    
    # OCR 통계
    with_thumb_ocr = (df['thumbnail_text_ocr'].notna() & (df['thumbnail_text_ocr'].str.strip() != '')).sum()
    with_start_ocr = (df['video_start_frame_ocr'].notna() & (df['video_start_frame_ocr'].str.strip() != '')).sum()
    with_end_ocr = (df['video_end_frame_ocr'].notna() & (df['video_end_frame_ocr'].str.strip() != '')).sum()
    
    # 추천인 정보
    with_phone = (df['sponsor_phone'].notna() & (df['sponsor_phone'].str.strip() != '')).sum()
    with_partner = (df['sponsor_partner_id'].notna() & (df['sponsor_partner_id'].str.strip() != '')).sum()
    
    # OCR에서 추출한 추천인 정보
    thumb_phone = (df['thumbnail_phone_ocr'].notna() & (df['thumbnail_phone_ocr'].str.strip() != '')).sum()
    thumb_partner = (df['thumbnail_partner_ocr'].notna() & (df['thumbnail_partner_ocr'].str.strip() != '')).sum()
    start_phone = (df['video_start_phone_ocr'].notna() & (df['video_start_phone_ocr'].str.strip() != '')).sum()
    start_partner = (df['video_start_partner_ocr'].notna() & (df['video_start_partner_ocr'].str.strip() != '')).sum()
    end_phone = (df['video_end_phone_ocr'].notna() & (df['video_end_phone_ocr'].str.strip() != '')).sum()
    end_partner = (df['video_end_partner_ocr'].notna() & (df['video_end_partner_ocr'].str.strip() != '')).sum()
    
    # 기타 통계
    avg_views = df['view_count'].mean()
    avg_likes = df['like_count'].mean()
    avg_comments = df['comment_count'].mean()
    
    # API 쿼터 분석
    daily_quota = 10000  # YouTube API 일일 쿼터
    quota_used = api_quota_used['total']
    quota_remaining = daily_quota - quota_used
    quota_percent = quota_used / daily_quota * 100
    
    # 리포트 작성
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n")
        f.write("="*80 + "\n")
        f.write("📊 PM-International YouTube 크롤러 v3.1 결과 보고서\n")
        f.write("="*80 + "\n\n")
        
        # 실행 시간
        f.write("⏱️  실행 시간\n")
        f.write("-"*80 + "\n")
        f.write(f"• 총 실행 시간: {elapsed_minutes:.1f}분 ({elapsed_minutes*60:.0f}초)\n")
        f.write(f"• 시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"• 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 수집 성과
        f.write("📈 수집 성과\n")
        f.write("-"*80 + "\n")
        f.write(f"• 총 수집 비디오: {total_count}개\n")
        f.write(f"• 수집 속도: {total_count/elapsed_minutes:.2f}개/분\n")
        f.write(f"• 비디오당 평균 소요 시간: {elapsed_minutes*60/total_count:.1f}초\n\n")
        
        # 음성인식 분석
        f.write("✅ 음성인식 성공률\n")
        f.write("-"*80 + "\n")
        f.write(f"• 전체 성공률: {with_transcript}/{total_count} ({transcript_rate:.1f}%)\n\n")
        
        f.write("[소스별 분포]\n")
        f.write(f"• YouTube 자막 (수동): {youtube_caption}개 ({youtube_caption/total_count*100:.1f}%)\n")
        f.write(f"• YouTube 자막 (자동생성): {youtube_auto}개 ({youtube_auto/total_count*100:.1f}%)\n")
        f.write(f"• Whisper AI 음성인식: {whisper_ai}개 ({whisper_ai/total_count*100:.1f}%)\n")
        f.write(f"• 실패/없음: {failed}개 ({failed/total_count*100:.1f}%)\n\n")
        
        # OCR 분석
        f.write("👁️ OCR 처리 결과\n")
        f.write("-"*80 + "\n")
        f.write(f"• 썸네일 OCR 성공률: {with_thumb_ocr}/{total_count} ({with_thumb_ocr/total_count*100:.1f}%)\n")
        f.write(f"• 영상 첫 장면 OCR: {with_start_ocr}/{total_count} ({with_start_ocr/total_count*100:.1f}%)\n")
        f.write(f"• 영상 마지막 장면 OCR: {with_end_ocr}/{total_count} ({with_end_ocr/total_count*100:.1f}%)\n\n")
        
        # 추천인 정보
        f.write("🎯 추천인 정보 추출\n")
        f.write("-"*80 + "\n")
        f.write("[제목/설명에서 추출]\n")
        f.write(f"• 전화번호: {with_phone}개 ({with_phone/total_count*100:.1f}%)\n")
        f.write(f"• 후원번호: {with_partner}개 ({with_partner/total_count*100:.1f}%)\n\n")
        
        f.write("[OCR에서 추출]\n")
        f.write(f"• 썸네일 - 전화번호: {thumb_phone}개, 후원번호: {thumb_partner}개\n")
        f.write(f"• 영상 첫장면 - 전화번호: {start_phone}개, 후원번호: {start_partner}개\n")
        f.write(f"• 영상 끝장면 - 전화번호: {end_phone}개, 후원번호: {end_partner}개\n\n")
        
        total_phone_ocr = thumb_phone + start_phone + end_phone
        total_partner_ocr = thumb_partner + start_partner + end_partner
        f.write(f"• OCR 통합 추출: 전화번호 {total_phone_ocr}개, 후원번호 {total_partner_ocr}개\n\n")
        
        # 참여 지표
        f.write("💬 참여 지표\n")
        f.write("-"*80 + "\n")
        f.write(f"• 평균 조회수: {avg_views:,.0f}회\n")
        f.write(f"• 평균 좋아요: {avg_likes:,.1f}개\n")
        f.write(f"• 평균 댑글: {avg_comments:,.1f}개\n\n")
        
        # API 쿼터 분석
        f.write("📡 YouTube API 쿼터 사용량\n")
        f.write("-"*80 + "\n")
        f.write(f"• 검색 API (search): {api_quota_used['search']:,} units\n")
        f.write(f"• 비디오 상세 (videos.list): {api_quota_used['videos']:,} units\n")
        f.write(f"• 총 사용량: {quota_used:,} units\n")
        f.write(f"• 일일 할당량: {daily_quota:,} units\n")
        f.write(f"• 남은 쿼터: {quota_remaining:,} units ({100-quota_percent:.1f}%)\n")
        f.write(f"• 사용률: {quota_percent:.2f}%\n\n")
        
        if quota_remaining < 1000:
            f.write("⚠️  경고: 남은 쿼터가 부족합니다!\n\n")
        
        # 출력 파일
        f.write("💾 출력 파일 정보\n")
        f.write("-"*80 + "\n")
        f.write(f"• CSV 파일: {csv_path}\n")
        f.write(f"• 파일 크기: {os.path.getsize(csv_path):,} bytes\n")
        f.write(f"• 총 컴럼 개수: {len(df.columns)}개\n\n")
        
        # v3.1 기능 요약
        f.write("🎉 v3.1 기능 요약\n")
        f.write("-"*80 + "\n")
        f.write("✅ YouTube 자막 + Whisper AI 하이브리드 음성인식\n")
        f.write("✅ 썸네일 OCR\n")
        f.write("✅ 영상 프레임 OCR (첫 장면 + 마지막 장면)\n")
        f.write("✅ 전화번호/후원번호 자동 추출\n")
        f.write("✅ API 쿼터 추적 및 보고\n")
        f.write("✅ 30분 최대 수집 모드\n")
        f.write("✅ 상세 통계 리포트 자동 생성\n\n")
        
        f.write("="*80 + "\n")
        f.write("📝 보고서 생성 완료\n")
        f.write("="*80 + "\n")
    
    logger.info(f"📝 리포트 생성 완료: {report_path}")
    return report_path

def save_final_results(videos: List[dict]):
    """최종 결과 저장"""
    if not videos:
        logger.error("❌ 저장할 데이터가 없습니다")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        # CSV 저장
        df = pd.DataFrame(videos)
        output_dir = './output'
        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, f"youtube_pm_v3_1_local_{timestamp}.csv")
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 상세 통계
        total = len(df)
        with_transcript = (df['transcript_text'].notna() & (df['transcript_text'].str.strip() != '')).sum()
        with_ocr = (df['thumbnail_text_ocr'].notna() & (df['thumbnail_text_ocr'].str.strip() != '')).sum()
        with_phone = (df['sponsor_phone'].notna() & (df['sponsor_phone'].str.strip() != '')).sum()
        with_partner = (df['sponsor_partner_id'].notna() & (df['sponsor_partner_id'].str.strip() != '')).sum()
        
        # 자막 소스 분포
        transcript_sources = df['transcript_source'].value_counts().to_dict()
        
        logger.info(f"\n🎉 최종 결과:")
        logger.info(f"📁 파일: {csv_path}")
        logger.info(f"📊 총 수집: {total}개")
        logger.info(f"\n🎯 데이터 품질:")
        logger.info(f"  🎤 음성인식: {with_transcript}/{total} ({with_transcript/total*100:.1f}%)")
        logger.info(f"  👁️ 썸네일 OCR: {with_ocr}/{total} ({with_ocr/total*100:.1f}%)")
        logger.info(f"  📞 전화번호: {with_phone}/{total} ({with_phone/total*100:.1f}%)")
        logger.info(f"  🏷️ 후원번호: {with_partner}/{total} ({with_partner/total*100:.1f}%)")
        logger.info(f"\n📡 자막 소스 분포:")
        for source, count in transcript_sources.items():
            logger.info(f"  - {source}: {count}개 ({count/total*100:.1f}%)")
        
        # 리포트 생성
        elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
        report_path = generate_report(videos, csv_path, elapsed_minutes)
        
        return csv_path, report_path
    except Exception as e:
        logger.error(f"❌ 최종 저장 실패: {e}")
        return None

# =================================
# 메인 실행
# =================================

def main():
    """메인 함수"""
    global start_time
    
    logger.info("="*80)
    logger.info("🚀 YouTube Crawler v3.1 (30분 최대 수집 모드)")
    logger.info("="*80)
    
    start_time = datetime.now()
    
    # 종료 신호 처리
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 초기화
        logger.info("🔧 초기화...")
        logger.info("⏰ 실행시간: 30분 (27분 후 안전 종료 모드)")
        logger.info("🎯 목표: 시간 내 최대한 수집")
        logger.info("📊 API 쿼터: 10,000 units/day")
        
        init_youtube_client()
        init_ai_models()
        
        # 크롤링
        logger.info("\n🎬 크롤링 시작!")
        final_videos = main_crawling_loop()
        
        # 최종 저장
        logger.info("\n💾 최종 결과 저장 중...")
        result_paths = save_final_results(final_videos)
        
        if result_paths is None:
            logger.error("❌ 저장 실패")
            return None
        
        elapsed = (datetime.now() - start_time).total_seconds() / 60
        if elapsed >= 30:
            logger.info(f"\n⏰ 30분 완료! 모든 작업 정상 종료")
        else:
            logger.info(f"\n✅ 조기 완료! 소요시간: {elapsed:.1f}분")
        logger.info(f"🚀 수집량: {len(final_videos)}개")
        logger.info(f"📁 CSV 파일: {result_paths[0]}")
        logger.info(f"📝 리포트: {result_paths[1]}")
        return result_paths
        
    except KeyboardInterrupt:
        logger.info("\n🛑 사용자 중단")
        if collected_videos:
            save_final_results(collected_videos)
    except Exception as e:
        logger.error(f"\n💥 오류: {e}")
        if collected_videos:
            save_final_results(collected_videos)
        raise

if __name__ == "__main__":
    main()
