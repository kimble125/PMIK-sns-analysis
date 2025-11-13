#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 빠른 테스트 크롤러 (20분 내 결과 확인용)

목표:
- 키워드 3개만 검색
- 각 키워드당 10개 영상만 수집
- 총 30개 영상 목표
- 실행 시간: 약 2-5분
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict
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
# 설정값 (테스트용 - 간소화)
# ===========================

# YouTube API 키
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

if not YOUTUBE_API_KEY:
    logger.error("=" * 70)
    logger.error("❌ YouTube API 키가 설정되지 않았습니다!")
    logger.error("=" * 70)
    logger.error("\n다음 중 하나를 선택하세요:\n")
    logger.error("방법 1) 환경변수 설정:")
    logger.error("  export YOUTUBE_API_KEY='your_api_key_here'")
    logger.error("\n방법 2) config.py 파일 생성:")
    logger.error("  youtube/config.py 파일에 다음 내용 추가:")
    logger.error("  YOUTUBE_API_KEY = 'your_api_key_here'")
    logger.error("\n방법 3) 코드에 직접 입력 (테스트용):")
    logger.error("  이 파일 39번째 줄의 YOUTUBE_API_KEY 값 수정")
    logger.error("\n🔑 API 키 발급: https://console.cloud.google.com/")
    logger.error("=" * 70)
    exit(1)

# 테스트용 키워드 (3개만)
TEST_KEYWORDS = [
    "피엠인터내셔널",
    "독일피엠",
    "피트라인",
]

MAX_RESULTS_PER_KEYWORD = 10  # 키워드당 10개만

# ===========================
# 추천인 정보 추출
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
    """추천인 파트너 ID 추출 (8자리)"""
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

# ===========================
# YouTube 검색 및 수집
# ===========================

def get_youtube_client():
    """YouTube API 클라이언트 생성"""
    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def search_youtube_videos(youtube, keyword: str, max_results: int = 10) -> List[str]:
    """YouTube 검색"""
    try:
        logger.info(f"🔍 검색 중: '{keyword}'")
        
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
        logger.info(f"   ✅ {len(video_ids)}개 영상 발견")
        
        return video_ids
    
    except HttpError as e:
        logger.error(f"   ❌ 검색 실패: {e}")
        return []

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
            
            # 기본 정보
            video_info = {
                'platform': 'youtube',
                'video_id': item['id'],
                'url': f"https://www.youtube.com/watch?v={item['id']}",
                'channel_name': snippet['channelTitle'],
                'title': snippet['title'],
                'description': snippet.get('description', '')[:500],  # 500자만
                'published_datetime': snippet['publishedAt'],
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'collected_date': datetime.now().strftime('%Y-%m-%d'),
            }
            
            # 추천인 정보 추출
            full_text = f"{video_info['title']} {video_info['description']}"
            video_info['sponsor_phone'] = extract_sponsor_phone(full_text)
            video_info['sponsor_partner_id'] = extract_sponsor_partner_id(full_text)
            
            video_data.append(video_info)
        
        return video_data
    
    except HttpError as e:
        logger.error(f"❌ 영상 상세 정보 조회 실패: {e}")
        return []

# ===========================
# 메인 함수
# ===========================

def main():
    """메인 크롤링 함수"""
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("🎬 YouTube 빠른 테스트 크롤러 시작")
    logger.info("=" * 70)
    logger.info(f"키워드: {len(TEST_KEYWORDS)}개")
    logger.info(f"키워드당 수집: {MAX_RESULTS_PER_KEYWORD}개")
    logger.info(f"예상 총 수집: {len(TEST_KEYWORDS) * MAX_RESULTS_PER_KEYWORD}개")
    logger.info("=" * 70)
    
    # YouTube API 클라이언트
    youtube = get_youtube_client()
    
    # 수집 데이터
    all_videos = []
    seen_video_ids = set()
    
    # 키워드별 검색
    for i, keyword in enumerate(TEST_KEYWORDS, 1):
        logger.info(f"\n[{i}/{len(TEST_KEYWORDS)}] 키워드: {keyword}")
        
        # 검색
        video_ids = search_youtube_videos(youtube, keyword, MAX_RESULTS_PER_KEYWORD)
        
        # 중복 제거
        new_video_ids = [vid for vid in video_ids if vid not in seen_video_ids]
        
        if not new_video_ids:
            logger.info("   ⚠️  새로운 영상 없음 (중복)")
            continue
        
        # 상세 정보 조회
        logger.info(f"   📥 상세 정보 조회 중... ({len(new_video_ids)}개)")
        video_details = get_video_details(youtube, new_video_ids)
        
        # 수집
        for video in video_details:
            if video['video_id'] not in seen_video_ids:
                all_videos.append(video)
                seen_video_ids.add(video['video_id'])
        
        logger.info(f"   ✅ 수집 완료: {len(video_details)}개")
        logger.info(f"   📊 누적 총계: {len(all_videos)}개")
        
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
    
    # 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'youtube/youtube_test_{timestamp}.csv'
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    elapsed_time = time.time() - start_time
    
    # ===========================
    # 결과 출력
    # ===========================
    
    logger.info(f"{'='*70}")
    logger.info("✅ 테스트 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"\n📊 수집 결과:")
    logger.info(f"  - 총 영상 수: {len(df)}개")
    logger.info(f"  - 추천인 전화번호: {df['sponsor_phone'].notna().sum()}개")
    logger.info(f"  - 파트너 ID: {df['sponsor_partner_id'].notna().sum()}개")
    logger.info(f"  - 평균 조회수: {df['view_count'].mean():.0f}")
    logger.info(f"  - 평균 좋아요: {df['like_count'].mean():.0f}")
    logger.info(f"  - 평균 댓글: {df['comment_count'].mean():.0f}")
    
    logger.info(f"\n⏱️  소요 시간: {elapsed_time:.1f}초")
    logger.info(f"\n📁 저장 위치: {output_file}")
    
    # 상위 5개 영상 미리보기
    logger.info(f"\n{'='*70}")
    logger.info("📺 상위 5개 영상 미리보기:")
    logger.info(f"{'='*70}")
    
    for idx, row in df.head(5).iterrows():
        logger.info(f"\n{idx+1}. {row['title'][:50]}...")
        logger.info(f"   채널: {row['channel_name']}")
        logger.info(f"   조회수: {row['view_count']:,} | 좋아요: {row['like_count']:,}")
        logger.info(f"   URL: {row['url']}")
        if row['sponsor_phone']:
            logger.info(f"   📞 추천인: {row['sponsor_phone']}")
        if row['sponsor_partner_id']:
            logger.info(f"   🆔 파트너ID: {row['sponsor_partner_id']}")
    
    logger.info(f"\n{'='*70}")
    logger.info("🎉 테스트 성공!")
    logger.info(f"{'='*70}")
    logger.info(f"\n다음 단계:")
    logger.info(f"  1. {output_file} 파일 확인")
    logger.info(f"  2. 본격 수집: youtube_crawler_v1_sample.py 실행")
    logger.info(f"     (키워드 {len(TEST_KEYWORDS)}개 → 30개, 수집량 10개 → 50개)")

if __name__ == "__main__":
    main()
