#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube PMIK 판매원 데이터 수집기 v1.0 (샘플 코드)

기능:
1. YouTube Data API v3로 영상 검색
2. 영상 메타데이터 수집
3. 필터링 (네이버 블로그 로직 재사용)
4. CSV 저장

참고:
- pm_naver_blog_crawler_v8_4_final.py 구조 참고
- 필터링 로직 재사용
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re
from pathlib import Path

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

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
# 설정값
# ===========================

# YouTube API 키 (환경변수 또는 config.py에서 로드)
try:
    import config
    YOUTUBE_API_KEY = config.YOUTUBE_API_KEY
except ImportError:
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

if not YOUTUBE_API_KEY:
    logger.error("❌ YouTube API 키가 설정되지 않았습니다.")
    logger.error("   .env 파일에 YOUTUBE_API_KEY를 추가하거나")
    logger.error("   config.py에 YOUTUBE_API_KEY를 설정하세요.")
    exit(1)

# 검색 키워드 (네이버 블로그와 동일)
SEARCH_KEYWORDS = [
    "피엠인터내셔널",
    "독일피엠",
    "PM인터내셔널",
    "피트라인",
    "피엠코리아",
    "탑쉐이프",
    "프로쉐이프",
]

# 필터링 키워드 (네이버 블로그에서 재사용)
PM_BRAND_KEYWORDS = [
    "피엠", "피엠인터내셔널", "PM International", "PMInternational",
    "PM", "FitLine", "핏라인", "피트라인"
]

PM_SALES_KEYWORDS = [
    "추천인", "추천인코드", "추천인 코드", "추천인번호", "추천인 번호",
    "파트너", "파트너코드", "파트너 코드", "파트너번호", "파트너 번호",
    "등록", "가입", "문의"
]

EXCLUDE_KEYWORDS = [
    "뉴스", "기사", "보도", "공지", "채용", "구인", "구직",
    "매트리스", "침대", "주가", "주식", "상장"
]

MAX_RESULTS_PER_KEYWORD = 50  # 키워드당 최대 결과 수
TOTAL_TARGET = 1000  # 목표 수집 개수

# ===========================
# YouTube API 클라이언트
# ===========================

def get_youtube_client():
    """YouTube API 클라이언트 생성"""
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# ===========================
# 추천인 정보 추출 (네이버 블로그 재사용)
# ===========================

def extract_sponsor_phone(text: str) -> str:
    """추천인 전화번호 추출"""
    if not text:
        return ""
    
    phone_patterns = [
        r'010[-\s]?\d{4}[-\s]?\d{4}',
        r'추천인.*?010[-\s]?\d{4}[-\s]?\d{4}',
        r'문의.*?010[-\s]?\d{4}[-\s]?\d{4}',
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
    """추천인 파트너 ID 추출 (정확히 8자리)"""
    if not text:
        return ""
    
    partner_patterns = [
        r'추천인\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{8})\b',
        r'파트너\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{8})\b',
        r'\b(\d{8})\b',
    ]
    
    for pattern in partner_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) == 8:
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
# 필터링 함수 (네이버 블로그 재사용)
# ===========================

def content_passes_filter(title: str, description: str) -> tuple[bool, str]:
    """
    콘텐츠 필터링
    
    Returns:
        (통과여부, 실패사유)
    """
    full_text = f"{title} {description}".lower()
    
    # 1. 제외 키워드 체크
    exclude_count = sum(1 for keyword in EXCLUDE_KEYWORDS if keyword in full_text)
    if exclude_count >= 2:
        return False, f"제외 키워드 {exclude_count}개 발견"
    
    # 2. PM 브랜드 키워드 체크
    has_pm_keyword = any(keyword.lower() in full_text for keyword in PM_BRAND_KEYWORDS)
    if not has_pm_keyword:
        return False, "PM 브랜드 키워드 없음"
    
    return True, ""

# ===========================
# YouTube 검색 및 수집
# ===========================

def search_youtube_videos(youtube, keyword: str, max_results: int = 50) -> List[str]:
    """
    YouTube에서 키워드로 영상 검색
    
    Returns:
        video_id 리스트
    """
    try:
        logger.info(f"🔍 검색 중: '{keyword}'")
        
        request = youtube.search().list(
            q=keyword,
            type='video',
            part='id',
            maxResults=max_results,
            order='relevance',  # 관련도순
            regionCode='KR',  # 한국 지역
            relevanceLanguage='ko',  # 한국어
        )
        
        response = request.execute()
        
        video_ids = [item['id']['videoId'] for item in response.get('items', [])]
        logger.info(f"   ✅ {len(video_ids)}개 영상 발견")
        
        return video_ids
    
    except HttpError as e:
        logger.error(f"   ❌ 검색 실패: {e}")
        return []

def get_video_details(youtube, video_ids: List[str]) -> List[Dict]:
    """
    영상 상세 정보 조회
    
    Returns:
        영상 정보 딕셔너리 리스트
    """
    if not video_ids:
        return []
    
    try:
        # 최대 50개씩 배치 처리
        video_data = []
        
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            request = youtube.videos().list(
                id=','.join(batch_ids),
                part='snippet,statistics,contentDetails'
            )
            
            response = request.execute()
            
            for item in response.get('items', []):
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                content_details = item['contentDetails']
                
                # 데이터 추출
                video_info = {
                    'platform': 'youtube',
                    'video_id': item['id'],
                    'url': f"https://www.youtube.com/watch?v={item['id']}",
                    'channel_id': snippet['channelId'],
                    'channel_name': snippet['channelTitle'],
                    'title': snippet['title'],
                    'description': snippet.get('description', ''),
                    'published_datetime': snippet['publishedAt'],
                    'duration': content_details['duration'],
                    'view_count': int(statistics.get('viewCount', 0)),
                    'like_count': int(statistics.get('likeCount', 0)),
                    'comment_count': int(statistics.get('commentCount', 0)),
                    'favorite_count': int(statistics.get('favoriteCount', 0)),
                    'category_id': snippet.get('categoryId', ''),
                    'tags': ', '.join(snippet.get('tags', [])),
                    'thumbnail_url': snippet['thumbnails'].get('maxres', snippet['thumbnails']['high'])['url'],
                    'collected_date': datetime.now().strftime('%Y-%m-%d'),
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

def get_channel_statistics(youtube, channel_id: str) -> Dict:
    """채널 통계 조회"""
    try:
        request = youtube.channels().list(
            id=channel_id,
            part='statistics'
        )
        
        response = request.execute()
        
        if response.get('items'):
            stats = response['items'][0]['statistics']
            return {
                'channel_subscriber_count': int(stats.get('subscriberCount', 0)),
                'channel_video_count': int(stats.get('videoCount', 0)),
                'channel_view_count': int(stats.get('viewCount', 0)),
            }
    
    except HttpError as e:
        logger.error(f"❌ 채널 통계 조회 실패: {e}")
    
    return {
        'channel_subscriber_count': 0,
        'channel_video_count': 0,
        'channel_view_count': 0,
    }

# ===========================
# 메인 크롤링 함수
# ===========================

def main():
    """메인 크롤링 함수"""
    logger.info("=" * 70)
    logger.info("🎬 YouTube PMIK 판매원 데이터 수집 시작")
    logger.info("=" * 70)
    
    # YouTube API 클라이언트
    youtube = get_youtube_client()
    
    # 수집 데이터
    all_videos = []
    seen_video_ids = set()
    
    # 키워드별 검색
    for keyword in SEARCH_KEYWORDS:
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 키워드: {keyword}")
        logger.info(f"{'='*70}")
        
        # 검색
        video_ids = search_youtube_videos(youtube, keyword, MAX_RESULTS_PER_KEYWORD)
        
        # 중복 제거
        new_video_ids = [vid for vid in video_ids if vid not in seen_video_ids]
        logger.info(f"   💡 새로운 영상: {len(new_video_ids)}개")
        
        if not new_video_ids:
            continue
        
        # 상세 정보 조회
        logger.info(f"   📥 상세 정보 조회 중...")
        video_details = get_video_details(youtube, new_video_ids)
        
        # 필터링
        filtered_count = 0
        for video in video_details:
            # 중복 체크
            if video['video_id'] in seen_video_ids:
                continue
            
            # 필터링
            passes, reason = content_passes_filter(video['title'], video['description'])
            if not passes:
                filtered_count += 1
                logger.debug(f"   🔍 필터링: {video['title'][:30]}... ({reason})")
                continue
            
            # 채널 통계 추가
            channel_stats = get_channel_statistics(youtube, video['channel_id'])
            video.update(channel_stats)
            
            all_videos.append(video)
            seen_video_ids.add(video['video_id'])
        
        logger.info(f"   ✅ 수집: {len(video_details) - filtered_count}개")
        logger.info(f"   🔍 필터링: {filtered_count}개")
        logger.info(f"   📊 총 수집: {len(all_videos)}개")
        
        # 목표 달성 시 종료
        if len(all_videos) >= TOTAL_TARGET:
            logger.info(f"\n🎉 목표 달성! ({len(all_videos)}개 수집)")
            break
        
        # API 할당량 보호 (Rate limiting)
        time.sleep(1)
    
    # ===========================
    # CSV 저장
    # ===========================
    
    if not all_videos:
        logger.warning("⚠️  수집된 영상이 없습니다.")
        return
    
    logger.info(f"\n{'='*70}")
    logger.info("💾 CSV 저장 중...")
    logger.info(f"{'='*70}")
    
    df = pd.DataFrame(all_videos)
    
    # 컬럼 순서 정렬
    column_order = [
        'platform', 'video_id', 'url',
        'channel_id', 'channel_name', 'channel_subscriber_count', 
        'channel_video_count', 'channel_view_count',
        'title', 'description', 'published_datetime',
        'duration', 'view_count', 'like_count', 'comment_count', 
        'favorite_count', 'category_id',
        'tags', 'hashtags',
        'sponsor_phone', 'sponsor_partner_id',
        'thumbnail_url', 'collected_date'
    ]
    
    df = df[column_order]
    
    # 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'youtube_pm_v1_{timestamp}.csv'
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"✅ 저장 완료: {output_file}")
    logger.info(f"   총 {len(df)}개 영상")
    
    # ===========================
    # 통계 출력
    # ===========================
    
    logger.info(f"\n{'='*70}")
    logger.info("📊 수집 통계")
    logger.info(f"{'='*70}")
    logger.info(f"총 영상 수: {len(df)}")
    logger.info(f"추천인 전화번호 포함: {df['sponsor_phone'].notna().sum()}개")
    logger.info(f"파트너 ID 포함: {df['sponsor_partner_id'].notna().sum()}개")
    logger.info(f"평균 조회수: {df['view_count'].mean():.0f}")
    logger.info(f"평균 좋아요: {df['like_count'].mean():.0f}")
    logger.info(f"평균 댓글: {df['comment_count'].mean():.0f}")
    
    # 상위 채널
    logger.info(f"\n📺 상위 채널 (구독자순):")
    top_channels = df.groupby(['channel_name', 'channel_subscriber_count']).size().reset_index(name='영상수')
    top_channels = top_channels.sort_values('channel_subscriber_count', ascending=False).head(5)
    for _, row in top_channels.iterrows():
        logger.info(f"   - {row['channel_name']}: 구독자 {row['channel_subscriber_count']:,}명, 영상 {row['영상수']}개")
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ 수집 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"\n📁 다음 단계:")
    logger.info(f"   1. youtube_transcript_collector.py로 자막 수집")
    logger.info(f"   2. Google Colab에서 썸네일 OCR")
    logger.info(f"   3. merge_youtube_analysis.py로 결과 병합")

if __name__ == "__main__":
    main()
