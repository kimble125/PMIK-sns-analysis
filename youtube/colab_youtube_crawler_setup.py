#!/usr/bin/env python3
"""
Google Colab용 YouTube 크롤러 설치 및 실행 스크립트
1시간 실행 + 백그라운드 처리 + 체크포인트 기능
"""

# Colab 초기 설정 스크립트
COLAB_SETUP_CODE = '''
# [셀 1] GPU 확인 및 기본 라이브러리 설치
!nvidia-smi
!pip install -q yt-dlp openai-whisper easyocr opencv-python-headless 
!pip install -q youtube-transcript-api tqdm pandas pillow requests google-api-python-client

# Google Drive 마운트
from google.colab import drive
drive.mount('/content/drive')

# 작업 디렉토리 생성
!mkdir -p /content/youtube_data
!mkdir -p /content/drive/MyDrive/youtube_crawl_results

print("✅ 기본 설정 완료!")
'''

MAIN_CRAWLER_CODE = '''
# [셀 2] YouTube 크롤러 메인 코드
import os
import json
import time
import logging
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
from pathlib import Path
import requests
from io import BytesIO

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
from tqdm.notebook import tqdm
import signal
import sys

# =================================
# 설정
# =================================

# YouTube API Key (Colab에서 직접 입력)
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"  # 실제 키로 교체

# 크롤링 설정
TOTAL_RUNTIME_HOURS = 1.0  # 1시간
CHECKPOINT_INTERVAL = 300  # 5분마다 저장
TARGET_VIDEOS = 300  # 목표 수집량

KEYWORDS = [
    "피엠인터내셔널", "독일피엠", "PM인터내셔널", "피트라인", "피엠코리아",
    "탑쉐이프", "프로쉐이프", "디드링크", "뮤노겐", "엑티바이즈", "파워칵테일", "리스토레이트"
]

# 글로벌 변수
whisper_model = None
ocr_reader = None
youtube_client = None
start_time = None
collected_videos = []
processed_count = 0

# =================================
# 체크포인트 및 상태 관리
# =================================

def save_checkpoint(data, filename="checkpoint.json"):
    """중간 결과 저장"""
    checkpoint_path = f"/content/drive/MyDrive/youtube_crawl_results/{filename}"
    try:
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'processed_count': len(data),
                'data': data,
                'runtime_minutes': (datetime.now() - start_time).total_seconds() / 60
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 체크포인트 저장: {len(data)}개 ({checkpoint_path})")
    except Exception as e:
        print(f"❌ 체크포인트 저장 실패: {e}")

def load_checkpoint(filename="checkpoint.json"):
    """기존 결과 로드"""
    checkpoint_path = f"/content/drive/MyDrive/youtube_crawl_results/{filename}"
    try:
        if os.path.exists(checkpoint_path):
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"✅ 체크포인트 로드: {len(checkpoint['data'])}개")
            return checkpoint['data']
    except Exception as e:
        print(f"⚠️ 체크포인트 로드 실패: {e}")
    return []

def signal_handler(signum, frame):
    """종료 신호 처리"""
    print(f"\\n🔔 종료 신호 감지! 현재까지 수집된 데이터 저장 중...")
    save_final_results(collected_videos)
    sys.exit(0)

def check_time_limit():
    """시간 제한 확인"""
    if start_time is None:
        return False
    elapsed = (datetime.now() - start_time).total_seconds() / 3600
    return elapsed >= TOTAL_RUNTIME_HOURS

# =================================
# YouTube API 및 검색
# =================================

def init_youtube_client():
    """YouTube API 클라이언트 초기화"""
    global youtube_client
    if YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        raise ValueError("YouTube API 키를 설정하세요!")
    youtube_client = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    print("✅ YouTube API 클라이언트 준비 완료")

def search_videos(keyword: str, max_results: int = 25):
    """YouTube 비디오 검색"""
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
        return [item['id']['videoId'] for item in response.get('items', [])]
    except HttpError as e:
        print(f"❌ 검색 실패 ({keyword}): {e}")
        return []

def get_video_details(video_ids: List[str]):
    """비디오 상세 정보 조회"""
    if not video_ids:
        return []
    
    try:
        request = youtube_client.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics,contentDetails'
        )
        response = request.execute()
        
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
            
            # 기본 텍스트 추출
            full_text = f"{video_info['title']} {video_info['description']}"
            video_info['sponsor_phone'] = extract_sponsor_phone(full_text)
            video_info['sponsor_partner_id'] = extract_sponsor_partner_id(full_text)
            video_info['hashtags'] = extract_hashtags(video_info['description'])
            
            videos.append(video_info)
        
        return videos
        
    except HttpError as e:
        print(f"❌ 비디오 상세 정보 조회 실패: {e}")
        return []

# =================================
# 유틸리티 함수들
# =================================

def format_duration(iso_duration: str) -> str:
    """ISO 8601 duration을 읽기 쉬운 형식으로 변환"""
    if not iso_duration or iso_duration == 'PT0S':
        return "0초"
    
    match = re.match(r'PT(?:(\\d+)H)?(?:(\\d+)M)?(?:(\\d+)S)?', iso_duration)
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
    
    phone_patterns = [r'010[-\\s]?\\d{4}[-\\s]?\\d{4}']
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            digits = re.sub(r'\\D', '', phone)
            if digits.startswith('010') and len(digits) == 11:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return ""

def extract_sponsor_partner_id(text: str) -> str:
    """파트너 ID 추출 (7자리/8자리)"""
    if not text:
        return ""
    
    patterns = [
        r'추천인\\s*(?:코드|번호|ID)?\\s*[:：]?\\s*(\\d{7,8})\\b',
        r'파트너\\s*(?:코드|번호|ID)?\\s*[:：]?\\s*(\\d{7,8})\\b', 
        r'후원\\s*(?:코드|번호|ID)?\\s*[:：]?\\s*(\\d{7,8})\\b',
        r'\\b(\\d{7,8})\\b'
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
# 멀티미디어 처리 (개선된 버전)
# =================================

def init_models():
    """AI 모델들 초기화"""
    global whisper_model, ocr_reader
    
    try:
        if whisper_model is None:
            print("🤖 Whisper 모델 로딩...")
            whisper_model = whisper.load_model("base")
            print("✅ Whisper 준비 완료")
    except Exception as e:
        print(f"❌ Whisper 초기화 실패: {e}")
    
    try:
        if ocr_reader is None:
            print("👁️ OCR 리더 초기화...")
            ocr_reader = easyocr.Reader(['ko', 'en'], gpu=True)
            print("✅ OCR 준비 완료")
    except Exception as e:
        print(f"❌ OCR 초기화 실패: {e}")

def get_youtube_transcript_safe(video_id: str):
    """안전한 YouTube 자막 수집"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 한국어 우선
        for lang_code in ['ko', 'en']:
            try:
                transcript = transcript_list.find_transcript([lang_code])
                transcript_data = transcript.fetch()
                text = ' '.join([item['text'] for item in transcript_data])
                return {'transcript': text, 'source': 'youtube_caption', 'language': lang_code}
            except:
                continue
        
        # 자동생성 자막 시도
        try:
            transcript = transcript_list.find_generated_transcript(['ko'])
            transcript_data = transcript.fetch()
            text = ' '.join([item['text'] for item in transcript_data])
            return {'transcript': text, 'source': 'youtube_auto', 'language': 'ko-auto'}
        except:
            pass
            
    except Exception as e:
        pass
    
    return {'transcript': '', 'source': 'none', 'language': ''}

def get_whisper_transcript_safe(video_url: str):
    """안전한 Whisper 음성인식"""
    if whisper_model is None:
        return {'transcript': '', 'source': 'none', 'confidence': 0.0}
    
    # FFmpeg 확인
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
    except:
        return {'transcript': '', 'source': 'none', 'confidence': 0.0}
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_path = tmp.name
        
        # yt-dlp로 오디오 추출
        cmd = [
            'yt-dlp', '-x', '--audio-format', 'mp3', '--audio-quality', '64K',
            '-o', temp_path.replace('.mp3', ''), video_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=180)
        
        # 파일 확인
        audio_files = [temp_path, temp_path.replace('.mp3', '.m4a')]
        final_path = None
        for path in audio_files:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                final_path = path
                break
        
        if final_path:
            result = whisper_model.transcribe(final_path, language='ko', fp16=False)
            transcript = result['text'].strip()
            
            # 정리
            for path in audio_files:
                if os.path.exists(path):
                    os.remove(path)
            
            return {'transcript': transcript, 'source': 'whisper_ai', 'confidence': 0.9}
        
    except Exception as e:
        pass
    
    # 정리
    for path in [temp_path, temp_path.replace('.mp3', '.m4a')]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
    
    return {'transcript': '', 'source': 'failed', 'confidence': 0.0}

def process_thumbnail_ocr_safe(thumbnail_url: str):
    """안전한 썸네일 OCR"""
    if ocr_reader is None:
        return "", "", ""
    
    try:
        response = requests.get(thumbnail_url, timeout=10)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            img_array = np.array(image)
            
            # OCR 실행
            results = ocr_reader.readtext(img_array)
            texts = [result[1] for result in results if result[2] > 0.3]
            ocr_text = ' '.join(texts)
            
            # 정보 추출
            phone = extract_sponsor_phone(ocr_text)
            partner_id = extract_sponsor_partner_id(ocr_text)
            
            return ocr_text, phone, partner_id
    except Exception as e:
        pass
    
    return "", "", ""

def process_single_video(video_info: dict):
    """단일 비디오 완전 처리"""
    video_id = video_info['video_id']
    video_url = video_info['url']
    
    print(f"  🔄 처리 중: {video_info['title'][:40]}...")
    
    # 1. YouTube 자막 시도
    transcript_result = get_youtube_transcript_safe(video_id)
    
    if transcript_result['transcript']:
        video_info.update({
            'transcript_text': transcript_result['transcript'],
            'transcript_source': transcript_result['source'],
            'transcript_confidence': 1.0
        })
        print(f"    ✅ 자막 수집 성공")
    else:
        # 2. Whisper AI 사용
        whisper_result = get_whisper_transcript_safe(video_url)
        video_info.update({
            'transcript_text': whisper_result['transcript'],
            'transcript_source': whisper_result['source'],
            'transcript_confidence': whisper_result['confidence']
        })
        if whisper_result['transcript']:
            print(f"    🤖 Whisper 성공")
        else:
            print(f"    ❌ 음성인식 실패")
    
    # 3. 썸네일 OCR
    thumb_text, thumb_phone, thumb_partner = process_thumbnail_ocr_safe(video_info['thumbnail_url'])
    video_info.update({
        'thumbnail_text_ocr': thumb_text,
        'thumbnail_phone_ocr': thumb_phone,
        'thumbnail_partner_ocr': thumb_partner,
        # 영상 프레임 OCR은 YouTube 제한으로 비활성화
        'video_start_frame_ocr': '',
        'video_start_phone_ocr': '',
        'video_start_partner_ocr': '',
        'video_end_frame_ocr': '',
        'video_end_phone_ocr': '',
        'video_end_partner_ocr': ''
    })
    
    if thumb_text:
        print(f"    👁️ 썸네일 OCR 성공")
    
    return video_info

# =================================
# 메인 크롤링 로직
# =================================

def main_crawling_loop():
    """메인 크롤링 루프"""
    global collected_videos, processed_count, start_time
    
    # 기존 데이터 로드
    collected_videos = load_checkpoint()
    processed_count = len(collected_videos)
    seen_video_ids = set(v['video_id'] for v in collected_videos)
    
    print(f"🎯 목표: {TARGET_VIDEOS}개 (기존: {processed_count}개)")
    print(f"⏱️ 제한시간: {TOTAL_RUNTIME_HOURS}시간")
    print(f"💾 체크포인트: {CHECKPOINT_INTERVAL}초마다")
    
    last_checkpoint = time.time()
    
    for keyword in KEYWORDS:
        if check_time_limit():
            print(f"⏱️ 시간 제한 도달!")
            break
        
        if len(collected_videos) >= TARGET_VIDEOS:
            print(f"🎉 목표 달성!")
            break
        
        print(f"\\n🔍 검색 중: {keyword}")
        video_ids = search_videos(keyword, 20)
        new_video_ids = [vid for vid in video_ids if vid not in seen_video_ids]
        
        if not new_video_ids:
            print(f"  ⚠️ 새로운 비디오 없음")
            continue
        
        print(f"  📥 메타데이터 수집: {len(new_video_ids)}개")
        video_details = get_video_details(new_video_ids)
        
        for video in video_details:
            if check_time_limit() or len(collected_videos) >= TARGET_VIDEOS:
                break
            
            # 완전 처리
            processed_video = process_single_video(video)
            collected_videos.append(processed_video)
            seen_video_ids.add(video['video_id'])
            processed_count += 1
            
            # 주기적 체크포인트
            if time.time() - last_checkpoint > CHECKPOINT_INTERVAL:
                save_checkpoint(collected_videos, f"checkpoint_{datetime.now().strftime('%H%M')}.json")
                last_checkpoint = time.time()
            
            # 진행상황 출력
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            print(f"  📊 진행: {len(collected_videos)}/{TARGET_VIDEOS} ({elapsed:.1f}분 경과)")
            
            time.sleep(1)  # API 부하 방지
    
    return collected_videos

def save_final_results(videos: List[dict]):
    """최종 결과 저장"""
    if not videos:
        print("❌ 저장할 데이터가 없습니다.")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # CSV 저장
    df = pd.DataFrame(videos)
    csv_path = f"/content/drive/MyDrive/youtube_crawl_results/youtube_pm_v3_1_colab_{timestamp}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # JSON 백업
    json_path = f"/content/drive/MyDrive/youtube_crawl_results/youtube_pm_v3_1_backup_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    total_videos = len(df)
    with_transcript = df['transcript_text'].notna().sum()
    with_thumbnail_ocr = df['thumbnail_text_ocr'].notna().sum()
    
    print(f"\\n🎉 최종 결과 저장 완료!")
    print(f"📁 CSV: {csv_path}")
    print(f"📁 JSON: {json_path}")
    print(f"📊 수집: {total_videos}개")
    print(f"🎤 음성인식: {with_transcript}개")
    print(f"👁️ OCR: {with_thumbnail_ocr}개")
    
    return csv_path

# =================================
# 메인 실행
# =================================

def run_crawler():
    """크롤러 실행"""
    global start_time
    
    print("="*80)
    print("🚀 YouTube Crawler v3.1 (Google Colab 백그라운드 버전)")
    print("="*80)
    
    start_time = datetime.now()
    
    # 종료 신호 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 초기화
        print("🔧 초기화 중...")
        init_youtube_client()
        init_models()
        
        # 메인 루프
        print("\\n🎬 크롤링 시작!")
        final_videos = main_crawling_loop()
        
        # 최종 저장
        csv_path = save_final_results(final_videos)
        
        elapsed = (datetime.now() - start_time).total_seconds() / 60
        print(f"\\n✅ 크롤링 완료! 총 소요시간: {elapsed:.1f}분")
        
        return csv_path
        
    except Exception as e:
        print(f"\\n💥 크롤링 중 오류 발생: {e}")
        if collected_videos:
            print("🔄 현재까지 수집된 데이터 저장 중...")
            save_final_results(collected_videos)
        raise

# 실행
if __name__ == "__main__":
    result_path = run_crawler()
'''

print("📝 Google Colab 설정 코드:")
print("=" * 60)
print(COLAB_SETUP_CODE)
print("\n📝 메인 크롤러 코드:")
print("=" * 60)
print("코드가 너무 길어서 파일로 저장했습니다.")
print("youtube_crawler_v3_1_test.py 파일을 확인하세요.")
