#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube PMIK 판매원 데이터 수집기 v2.0 (자막 포함)

v2.0 신규 기능:
1. YouTube 공식 자막 수집 (youtube-transcript-api)
2. 자막 없는 영상 표시 (Whisper 대기열)
3. 300개 이상 대량 수집 최적화
4. 진행률 표시

예상 시간:
- 300개 영상: 약 5-8분
- 500개 영상: 약 8-12분
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
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

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
# 설정값 (대량 수집용)
# ===========================

# YouTube API 키
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

if not YOUTUBE_API_KEY:
    logger.error("=" * 70)
    logger.error("❌ YouTube API 키가 설정되지 않았습니다!")
    logger.error("=" * 70)
    logger.error("\n.env 파일에 YOUTUBE_API_KEY를 설정하세요.")
    exit(1)

# 검색 키워드 (v2: 확장)
SEARCH_KEYWORDS = [
    # 주요 키워드
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

MAX_RESULTS_PER_KEYWORD = 30  # 키워드당 30개 (총 360개 목표)
TARGET_TOTAL = 300  # 목표 수집 개수

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
            
            # 기본 정보
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

# ===========================
# 메인 함수
# ===========================

def main():
    """메인 크롤링 함수"""
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("🎬 YouTube PMIK 데이터 수집기 v2.0 (자막 포함)")
    logger.info("=" * 70)
    logger.info(f"키워드: {len(SEARCH_KEYWORDS)}개")
    logger.info(f"키워드당 수집: {MAX_RESULTS_PER_KEYWORD}개")
    logger.info(f"목표 수집: {TARGET_TOTAL}개")
    logger.info(f"신규 기능: YouTube 자막 자동 수집")
    logger.info("=" * 70)
    
    # YouTube API 클라이언트
    youtube = get_youtube_client()
    
    # 수집 데이터
    all_videos = []
    seen_video_ids = set()
    
    # 통계
    transcript_success = 0
    transcript_failed = 0
    
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
        
        # 자막 수집
        logger.info(f"   📝 자막 수집 중...")
        for idx, video in enumerate(video_details, 1):
            if video['video_id'] in seen_video_ids:
                continue
            
            # 자막 수집
            transcript_result = get_youtube_transcript(video['video_id'])
            video['youtube_transcript'] = transcript_result['transcript']
            video['transcript_language'] = transcript_result['language']
            video['transcript_status'] = transcript_result['status']
            video['has_transcript'] = transcript_result['status'] == 'success'
            
            if transcript_result['status'] == 'success':
                transcript_success += 1
            else:
                transcript_failed += 1
            
            # 진행률 표시 (10개마다)
            if idx % 10 == 0:
                logger.info(f"      자막 수집 진행: {idx}/{len(video_details)}")
            
            all_videos.append(video)
            seen_video_ids.add(video['video_id'])
            
            # 목표 달성 시 종료
            if len(all_videos) >= TARGET_TOTAL:
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
    
    # 컬럼 순서 정렬
    column_order = [
        'platform', 'video_id', 'url',
        'channel_id', 'channel_name',
        'title', 'description', 'published_datetime',
        'duration', 'view_count', 'like_count', 'comment_count',
        'category_id', 'tags', 'hashtags',
        'sponsor_phone', 'sponsor_partner_id',
        'thumbnail_url',
        'youtube_transcript', 'transcript_language', 'transcript_status', 'has_transcript',
        'collected_date'
    ]
    
    df = df[column_order]
    
    # 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'youtube/youtube_pm_v2_{timestamp}.csv'
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    elapsed_time = time.time() - start_time
    
    # ===========================
    # 결과 출력
    # ===========================
    
    logger.info(f"{'='*70}")
    logger.info("✅ 수집 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"\n📊 수집 결과:")
    logger.info(f"  - 총 영상 수: {len(df)}개")
    logger.info(f"  - 추천인 전화번호: {df['sponsor_phone'].notna().sum()}개 ({df['sponsor_phone'].notna().sum()/len(df)*100:.1f}%)")
    logger.info(f"  - 파트너 ID: {df['sponsor_partner_id'].notna().sum()}개 ({df['sponsor_partner_id'].notna().sum()/len(df)*100:.1f}%)")
    logger.info(f"  - 자막 있음: {df['has_transcript'].sum()}개 ({df['has_transcript'].sum()/len(df)*100:.1f}%)")
    logger.info(f"  - 자막 없음 (Whisper 필요): {(~df['has_transcript']).sum()}개")
    
    logger.info(f"\n📈 통계:")
    logger.info(f"  - 평균 조회수: {df['view_count'].mean():.0f}")
    logger.info(f"  - 평균 좋아요: {df['like_count'].mean():.0f}")
    logger.info(f"  - 평균 댓글: {df['comment_count'].mean():.0f}")
    logger.info(f"  - 평균 자막 길이: {df['youtube_transcript'].str.len().mean():.0f}자")
    
    logger.info(f"\n⏱️  소요 시간: {elapsed_time:.1f}초 ({elapsed_time/60:.1f}분)")
    logger.info(f"  - 평균 속도: {elapsed_time/len(df):.2f}초/영상")
    
    logger.info(f"\n📁 저장 위치: {output_file}")
    
    # 자막 없는 영상 목록 저장
    no_transcript_df = df[~df['has_transcript']][['video_id', 'url', 'title', 'transcript_status']]
    if len(no_transcript_df) > 0:
        no_transcript_file = f'youtube/youtube_no_transcript_{timestamp}.csv'
        no_transcript_df.to_csv(no_transcript_file, index=False, encoding='utf-8-sig')
        logger.info(f"\n📋 자막 없는 영상 목록: {no_transcript_file}")
        logger.info(f"   → Google Colab Whisper로 처리 필요")
    
    # 상위 5개 영상 미리보기
    logger.info(f"\n{'='*70}")
    logger.info("📺 상위 5개 영상 미리보기:")
    logger.info(f"{'='*70}")
    
    for idx, row in df.head(5).iterrows():
        logger.info(f"\n{idx+1}. {row['title'][:60]}...")
        logger.info(f"   채널: {row['channel_name']}")
        logger.info(f"   조회수: {row['view_count']:,} | 좋아요: {row['like_count']:,}")
        logger.info(f"   자막: {'✅ 있음' if row['has_transcript'] else '❌ 없음'}")
        if row['has_transcript']:
            logger.info(f"   자막 미리보기: {row['youtube_transcript'][:100]}...")
        if row['sponsor_phone']:
            logger.info(f"   📞 추천인: {row['sponsor_phone']}")
    
    logger.info(f"\n{'='*70}")
    logger.info("🎉 v2.0 수집 완료!")
    logger.info(f"{'='*70}")
    logger.info(f"\n다음 단계:")
    logger.info(f"  1. {output_file} 파일 확인")
    logger.info(f"  2. 자막 없는 영상 → Google Colab Whisper 처리")
    logger.info(f"  3. 썸네일 OCR → Google Colab Vision API")
    logger.info(f"  4. 결과 병합 → 네이버 블로그와 통합 분석")

if __name__ == "__main__":
    main()
