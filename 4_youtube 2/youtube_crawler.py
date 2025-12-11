#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 크롤러 v5
- OCR 제거 (URL만 수집)
- 채널/비디오 CSV 분리
- config_youtube.yaml 기반 설정
- 중복 제거 (체크포인트 기반)
- 시간 제한 없음 (모든 데이터 수집 완료까지)
- 10분 후 중간 저장
"""

import os
import json
import time
import signal
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
import re
import yaml

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# =============================================================================
# 설정 로드
# =============================================================================

def load_config(config_path: str = None) -> dict:
    """YAML 설정 파일 로드"""
    if config_path is None:
        config_path = Path(__file__).parent / 'config_youtube.yaml'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"⚠️ 설정 파일 로드 실패: {e}, 기본값 사용")
        return get_default_config()

def get_default_config() -> dict:
    """기본 설정 반환"""
    return {
        'execution_mode': {
            'test_mode': False,
            'max_duration_minutes': 0,  # 0 = 무제한
            'checkpoint_interval_minutes': 10,  # 10분마다 저장
            'first_save_minutes': 10  # 첫 저장 10분 후
        },
        'api': {
            'daily_quota_limit': 10000,
            'max_results_per_search': 50,
            'max_pages_per_keyword': 5,  # 5페이지 (쿼터 고려)
            'region_code': 'KR',
            'relevance_language': 'ko'
        },
        'keywords': {
            'primary': ["피엠인터내셔널", "독일피엠", "PM인터내셔널", "PM International", "피엠코리아"],
            'secondary': ["피트라인", "액티바이즈", "리스토레이트", "셀액티브", "이뮨플러스"]
        },
        'output': {
            'data_dir': 'output',
            'channels_filename': 'youtube_pm_channels',
            'videos_filename': 'youtube_pm_videos'
        },
        'checkpoint': {
            'enabled': True,
            'checkpoint_dir': 'checkpoints',
            'checkpoint_file': 'youtube_checkpoint.json'
        },
        'logging': {'level': 'INFO', 'log_dir': 'logs'}
    }

CONFIG = load_config()

# =============================================================================
# 전역 변수
# =============================================================================

youtube_client = None
logger = None
collected_videos: List[Dict] = []
collected_channel_ids: Set[str] = set()
processed_video_ids: Set[str] = set()
api_quota_used = {'search': 0, 'videos': 0, 'channels': 0, 'total': 0}
start_time = None
graceful_shutdown = False
first_save_done = False

# =============================================================================
# 로깅 설정
# =============================================================================

def setup_logging():
    """로깅 설정"""
    global logger
    
    log_config = CONFIG.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_dir = Path(log_config.get('log_dir', 'logs'))
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'youtube_crawler_v5_{timestamp}.log'
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    return logger

# =============================================================================
# 시그널 핸들러
# =============================================================================

def signal_handler(signum, frame):
    """안전 종료 핸들러"""
    global graceful_shutdown
    logger.info("\n⚠️ 종료 신호 수신, 안전하게 종료 중...")
    graceful_shutdown = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# =============================================================================
# 체크포인트
# =============================================================================

def load_checkpoint() -> Set[str]:
    """체크포인트 로드"""
    checkpoint_config = CONFIG.get('checkpoint', {})
    if not checkpoint_config.get('enabled', True):
        return set()
    
    checkpoint_dir = Path(checkpoint_config.get('checkpoint_dir', 'checkpoints'))
    checkpoint_file = checkpoint_dir / checkpoint_config.get('checkpoint_file', 'youtube_checkpoint.json')
    
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
                return set(data.get('processed_video_ids', []))
        except Exception as e:
            logger.warning(f"⚠️ 체크포인트 로드 실패: {e}")
    
    return set()

def save_checkpoint():
    """체크포인트 저장"""
    checkpoint_config = CONFIG.get('checkpoint', {})
    if not checkpoint_config.get('enabled', True):
        return
    
    checkpoint_dir = Path(checkpoint_config.get('checkpoint_dir', 'checkpoints'))
    checkpoint_dir.mkdir(exist_ok=True)
    checkpoint_file = checkpoint_dir / checkpoint_config.get('checkpoint_file', 'youtube_checkpoint.json')
    
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump({
                'processed_video_ids': list(processed_video_ids),
                'last_updated': datetime.now().isoformat()
            }, f)
    except Exception as e:
        logger.warning(f"⚠️ 체크포인트 저장 실패: {e}")

# =============================================================================
# YouTube API 초기화
# =============================================================================

def init_youtube_client():
    """YouTube API 클라이언트 초기화"""
    global youtube_client
    
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("❌ YOUTUBE_API_KEY 환경변수가 설정되지 않았습니다.")
    
    youtube_client = build('youtube', 'v3', developerKey=api_key)
    logger.info("✅ YouTube API 클라이언트 초기화 완료")
    return youtube_client

# =============================================================================
# 유틸리티 함수
# =============================================================================

def format_duration(iso_duration: str) -> str:
    """ISO 8601 duration을 읽기 쉬운 형식으로 변환"""
    if not iso_duration:
        return ""
    
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
    if not match:
        return iso_duration
    
    hours, minutes, seconds = match.groups()
    parts = []
    if hours:
        parts.append(f"{hours}시간")
    if minutes:
        parts.append(f"{minutes}분")
    if seconds:
        parts.append(f"{seconds}초")
    
    return ' '.join(parts) if parts else "0초"

def extract_sponsor_phone(text: str) -> str:
    """전화번호 추출"""
    if not text:
        return ""
    
    patterns = [
        r'010[-.\s]?\d{4}[-.\s]?\d{4}',
        r'01[1-9][-.\s]?\d{3,4}[-.\s]?\d{4}',
    ]
    
    for pattern in patterns:
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
        r'후원인\s*(?:번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
        r'ID\s*[:：]?\s*(\d{7,8})\b',
        r'\((\d{7,8})\)',
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

# =============================================================================
# YouTube API 함수
# =============================================================================

def get_all_keywords() -> List[str]:
    """모든 키워드 반환"""
    keywords_config = CONFIG.get('keywords', {})
    primary = keywords_config.get('primary', [])
    secondary = keywords_config.get('secondary', [])
    return primary + secondary

def search_videos(keyword: str, page_token: str = None) -> Tuple[List[str], str]:
    """유튜브 검색 (페이지네이션 지원)"""
    api_config = CONFIG.get('api', {})
    max_results = api_config.get('max_results_per_search', 50)
    
    try:
        request_params = {
            'q': keyword,
            'type': 'video',
            'part': 'id',
            'maxResults': max_results,
            'order': 'relevance',
            'regionCode': api_config.get('region_code', 'KR'),
            'relevanceLanguage': api_config.get('relevance_language', 'ko')
        }
        
        if page_token:
            request_params['pageToken'] = page_token
        
        request = youtube_client.search().list(**request_params)
        response = request.execute()
        
        # API 쿼터 기록 (search = 100 units)
        api_quota_used['search'] += 100
        api_quota_used['total'] += 100
        
        video_ids = [item['id']['videoId'] for item in response.get('items', [])]
        next_page_token = response.get('nextPageToken', '')
        
        return video_ids, next_page_token
        
    except HttpError as e:
        logger.error(f"❌ 검색 실패 ({keyword}): {e}")
        return [], ''

def get_video_details(video_ids: List[str]) -> List[Dict]:
    """비디오 상세 정보 조회"""
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
            content_details = item.get('contentDetails', {})
            
            video_id = item['id']
            title = snippet['title']
            description = snippet.get('description', '')
            full_text = f"{title} {description}"
            
            # 채널 ID 수집
            channel_id = snippet['channelId']
            collected_channel_ids.add(channel_id)
            
            video_info = {
                'platform': 'youtube',
                'video_id': video_id,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'channel_id': channel_id,
                'channel_name': snippet['channelTitle'],
                'title': title,
                'description': description,
                'published_datetime': snippet['publishedAt'],
                'duration': format_duration(content_details.get('duration', '')),
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'tags': ', '.join(snippet.get('tags', [])),
                'thumbnail_url': snippet['thumbnails'].get('high', {}).get('url', ''),
                'collected_date': datetime.now().strftime('%Y-%m-%d'),
                'sponsor_phone': extract_sponsor_phone(full_text),
                'sponsor_partner_id': extract_sponsor_partner_id(full_text),
                'hashtags': extract_hashtags(full_text)
            }
            
            videos.append(video_info)
        
        return videos
        
    except HttpError as e:
        logger.error(f"❌ 비디오 상세 조회 실패: {e}")
        return []

def get_channel_details(channel_ids: List[str]) -> List[Dict]:
    """채널 상세 정보 일괄 조회"""
    if not channel_ids:
        return []
    
    all_channels = []
    
    # 50개씩 배치 처리 (API 제한)
    for i in range(0, len(channel_ids), 50):
        batch_ids = channel_ids[i:i+50]
        
        try:
            request = youtube_client.channels().list(
                id=','.join(batch_ids),
                part='snippet,statistics,brandingSettings'
            )
            response = request.execute()
            
            # API 쿼터 기록 (channels.list = 1 unit)
            api_quota_used['channels'] += 1
            api_quota_used['total'] += 1
            
            for item in response.get('items', []):
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                branding = item.get('brandingSettings', {}).get('channel', {})
                
                description = snippet.get('description', '')
                
                channel_info = {
                    'channel_id': item['id'],
                    'channel_name': snippet['title'],
                    'channel_url': f"https://www.youtube.com/channel/{item['id']}",
                    'custom_url': snippet.get('customUrl', ''),
                    'description': description,
                    'joined_date': snippet['publishedAt'],
                    'subscriber_count': int(statistics.get('subscriberCount', 0)),
                    'video_count': int(statistics.get('videoCount', 0)),
                    'view_count': int(statistics.get('viewCount', 0)),
                    'thumbnail_url': snippet['thumbnails'].get('high', {}).get('url', ''),
                    'banner_url': branding.get('image', {}).get('bannerExternalUrl', ''),
                    'collected_date': datetime.now().strftime('%Y-%m-%d'),
                    'sponsor_phone': extract_sponsor_phone(description),
                    'sponsor_partner_id': extract_sponsor_partner_id(description)
                }
                
                all_channels.append(channel_info)
                
        except HttpError as e:
            logger.error(f"❌ 채널 상세 조회 실패: {e}")
    
    return all_channels

# =============================================================================
# 결과 저장
# =============================================================================

def save_results(suffix: str = ""):
    """결과 저장"""
    global first_save_done
    
    output_config = CONFIG.get('output', {})
    output_dir = Path(output_config.get('data_dir', 'output'))
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Videos CSV 저장 (OCR 컬럼 제거)
    if collected_videos:
        videos_df = pd.DataFrame(collected_videos)
        
        # v5 컬럼 순서 (OCR 컬럼 제거됨)
        video_columns = [
            'platform', 'video_id', 'url', 'channel_id', 'channel_name',
            'title', 'description', 'published_datetime', 'duration',
            'view_count', 'like_count', 'comment_count', 'tags', 'thumbnail_url',
            'collected_date', 'sponsor_phone', 'sponsor_partner_id', 'hashtags'
        ]
        
        # 존재하는 컬럼만 선택
        existing_cols = [col for col in video_columns if col in videos_df.columns]
        videos_df = videos_df[existing_cols]
        
        videos_filename = f"{output_config.get('videos_filename', 'youtube_pm_videos')}_{timestamp}{suffix}.csv"
        videos_path = output_dir / videos_filename
        videos_df.to_csv(videos_path, index=False, encoding='utf-8-sig')
        logger.info(f"📁 Videos 저장: {videos_path} ({len(videos_df)}개)")
    
    # Channels CSV 저장 (country 컬럼 제거됨)
    if collected_channel_ids:
        logger.info(f"\n📺 채널 정보 수집: {len(collected_channel_ids)}개")
        channels_data = get_channel_details(list(collected_channel_ids))
        
        if channels_data:
            channels_df = pd.DataFrame(channels_data)
            
            # v5 컬럼 순서 (country 제거됨)
            channel_columns = [
                'channel_id', 'channel_name', 'channel_url', 'custom_url',
                'description', 'joined_date', 'subscriber_count', 'video_count',
                'view_count', 'thumbnail_url', 'banner_url', 'collected_date',
                'sponsor_phone', 'sponsor_partner_id'
            ]
            
            existing_cols = [col for col in channel_columns if col in channels_df.columns]
            channels_df = channels_df[existing_cols]
            
            channels_filename = f"{output_config.get('channels_filename', 'youtube_pm_channels')}_{timestamp}{suffix}.csv"
            channels_path = output_dir / channels_filename
            channels_df.to_csv(channels_path, index=False, encoding='utf-8-sig')
            logger.info(f"📁 Channels 저장: {channels_path} ({len(channels_df)}개)")
    
    # 리포트 저장
    save_report(output_dir, timestamp, suffix)
    
    # 체크포인트 저장
    save_checkpoint()
    
    first_save_done = True

def save_report(output_dir: Path, timestamp: str, suffix: str = ""):
    """리포트 저장"""
    elapsed_minutes = (time.time() - start_time) / 60
    
    report = f"""================================================================================
📊 PM-International YouTube 크롤러 v5 결과 보고서
================================================================================

⏱️ 실행 정보
--------------------------------------------------------------------------------
• 총 실행 시간: {elapsed_minutes:.1f}분
• 시작 시간: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}
• 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 수집 성과
--------------------------------------------------------------------------------
• 수집된 영상: {len(collected_videos)}개
• 수집된 채널: {len(collected_channel_ids)}개
• 수집 속도: {len(collected_videos)/elapsed_minutes:.2f}개/분

🎯 추천인 정보 추출
--------------------------------------------------------------------------------
• 전화번호: {sum(1 for v in collected_videos if v.get('sponsor_phone'))}개 ({sum(1 for v in collected_videos if v.get('sponsor_phone'))/len(collected_videos)*100:.1f}%)
• 후원번호: {sum(1 for v in collected_videos if v.get('sponsor_partner_id'))}개 ({sum(1 for v in collected_videos if v.get('sponsor_partner_id'))/len(collected_videos)*100:.1f}%)

📡 YouTube API 쿼터 사용량
--------------------------------------------------------------------------------
• 검색 API: {api_quota_used['search']:,} units
• 비디오 API: {api_quota_used['videos']:,} units
• 채널 API: {api_quota_used['channels']:,} units
• 총 사용량: {api_quota_used['total']:,} / 10,000 units

🎉 v5 기능 요약
--------------------------------------------------------------------------------
✅ URL만 수집 (OCR 제거)
✅ 채널/영상 CSV 분리
✅ 중복 제거 (체크포인트 기반)
✅ config_youtube.yaml 설정
✅ 페이지네이션 (키워드당 최대 250개)
✅ 시간 제한 없음

================================================================================
"""
    
    report_path = output_dir / f"youtube_pm_report_{timestamp}{suffix}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"📝 리포트 저장: {report_path}")

# =============================================================================
# 메인 크롤링 루프
# =============================================================================

def main_crawling_loop():
    """메인 크롤링 루프"""
    global collected_videos, processed_video_ids, first_save_done
    
    keywords = get_all_keywords()
    api_config = CONFIG.get('api', {})
    max_pages = api_config.get('max_pages_per_keyword', 5)
    first_save_minutes = CONFIG.get('execution_mode', {}).get('first_save_minutes', 10)
    
    logger.info(f"🔍 검색 키워드: {len(keywords)}개")
    logger.info(f"📄 키워드당 최대 페이지: {max_pages}")
    logger.info(f"💾 첫 저장: {first_save_minutes}분 후")
    
    for keyword in tqdm(keywords, desc="키워드 처리"):
        if graceful_shutdown:
            break
        
        # API 쿼터 체크
        if api_quota_used['total'] >= api_config.get('daily_quota_limit', 10000) - 200:
            logger.warning("⚠️ API 쿼터 한도 근접, 중단")
            break
        
        logger.info(f"\n🔎 검색: '{keyword}'")
        
        page_token = None
        for page in range(max_pages):
            if graceful_shutdown:
                break
            
            # 10분 후 첫 저장
            elapsed_minutes = (time.time() - start_time) / 60
            if not first_save_done and elapsed_minutes >= first_save_minutes:
                logger.info(f"\n⏰ {first_save_minutes}분 경과, 중간 저장...")
                save_results(suffix="_interim")
            
            video_ids, next_page_token = search_videos(keyword, page_token)
            
            if not video_ids:
                break
            
            # 중복 제거
            new_video_ids = [vid for vid in video_ids if vid not in processed_video_ids]
            
            if new_video_ids:
                videos = get_video_details(new_video_ids)
                
                for video in videos:
                    collected_videos.append(video)
                    processed_video_ids.add(video['video_id'])
                    logger.info(f"   🔄 처리: {video['title'][:50]}...")
                    logger.info(f"   📊 진행: {len(collected_videos)}개")
            
            if not next_page_token:
                break
            page_token = next_page_token
            
            time.sleep(0.1)  # API 레이트 리밋 방지
    
    return len(collected_videos)

# =============================================================================
# 메인 함수
# =============================================================================

def main():
    global start_time, processed_video_ids, logger
    
    start_time = time.time()
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("🚀 YouTube 크롤러 v5 시작")
    logger.info("=" * 60)
    
    # 초기화
    init_youtube_client()
    processed_video_ids = load_checkpoint()
    logger.info(f"📋 이전 체크포인트: {len(processed_video_ids)}개 영상 처리됨")
    
    # 크롤링 실행
    total_videos = main_crawling_loop()
    
    # 최종 결과 저장
    logger.info("\n💾 최종 결과 저장 중...")
    save_results(suffix="_final")
    
    # 완료
    elapsed_minutes = (time.time() - start_time) / 60
    logger.info(f"\n✅ 완료! 소요시간: {elapsed_minutes:.1f}분")
    logger.info(f"📊 수집량: 영상 {len(collected_videos)}개, 채널 {len(collected_channel_ids)}개")

if __name__ == '__main__':
    main()
