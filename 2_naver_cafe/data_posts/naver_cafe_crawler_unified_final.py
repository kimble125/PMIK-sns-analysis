#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International 네이버 카페 통합 크롤러 v1.0 (Test 버전)

🔒 순차 통합 방식:
1. Phase 1: PM 전용 카페 발굴 (Track 2: targeting v1.3)
   → PM 키워드가 카페명에 있는 카페 검색
   → 카페소개 + 게시물 수집
   → data_targeting/에 저장

2. Phase 2: 키워드 기반 일반 검색 (Track 1: posts v2.5)
   → PM 키워드로 일반 게시물 검색
   → Phase 1에서 수집된 카페 중복 제거
   → data_posts/에 저장

📊 출력:
- data_targeting/naver_cafe_targeting_v1_3_*.csv (카페 info)
- data_targeting/naver_cafe_targeting_posts_v1_3_*.csv (카페 posts)
- data_posts/naver_cafe_posts_v2_5_*.csv (일반 posts)

작성자: PMI Korea 데이터 분석팀
버전: 1.0.0 (Test)
최종 수정일: 2025-12-01
"""

import os
import sys
import yaml
import logging
import argparse
from datetime import datetime
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_unified_crawler(config_path: str = 'config_cafe.yaml', duration: int = None):
    """순차 통합 크롤러 실행"""
    
    logger.info("=" * 80)
    logger.info("🚀 PM-International 네이버 카페 통합 크롤러 v1.0")
    logger.info("=" * 80)
    
    # 설정 로드
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 시간 분배 (기본: 총 시간의 40% targeting, 60% posts)
    total_duration = duration or config.get('execution_mode', {}).get('max_duration_minutes', 30)
    targeting_duration = int(total_duration * 0.4)
    posts_duration = int(total_duration * 0.6)
    
    logger.info(f"⏰ 총 실행 시간: {total_duration}분")
    logger.info(f"   → Phase 1 (Targeting): {targeting_duration}분")
    logger.info(f"   → Phase 2 (Posts): {posts_duration}분")
    logger.info("")
    
    collected_cafe_ids = set()
    collected_urls = set()
    new_posts_count = 0
    
    # =========================================================================
    # Phase 1: PM 전용 카페 발굴 (Track 2)
    # =========================================================================
    logger.info("=" * 80)
    logger.info("📍 Phase 1: PM 전용 카페 발굴 시작")
    logger.info("=" * 80)
    
    try:
        from naver_cafe_targeting_v1_2 import PMCafeTargetingCrawler
        
        # 설정 수정: 시간 제한
        config['execution_mode']['max_duration_minutes'] = targeting_duration
        
        targeting_crawler = PMCafeTargetingCrawler(config)
        targeting_crawler.run()
        
        # 수집된 카페 ID와 URL 추출
        if hasattr(targeting_crawler, 'pm_cafes') and targeting_crawler.pm_cafes:
            collected_cafe_ids = set(c.cafe_id for c in targeting_crawler.pm_cafes)
            logger.info(f"✅ Phase 1 완료: {len(collected_cafe_ids)}개 PM 카페 발굴")
        
        if hasattr(targeting_crawler, 'posts') and targeting_crawler.posts:
            collected_urls = set(p.url for p in targeting_crawler.posts)
            logger.info(f"   → {len(collected_urls)}개 게시물 URL 수집")
        
    except Exception as e:
        logger.error(f"❌ Phase 1 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("")
    
    # =========================================================================
    # Phase 2: 키워드 기반 일반 검색 (Track 1)
    # =========================================================================
    logger.info("=" * 80)
    logger.info("🔍 Phase 2: 키워드 기반 일반 검색 시작")
    logger.info(f"   → {len(collected_cafe_ids)}개 카페, {len(collected_urls)}개 URL 중복 제거 예정")
    logger.info("=" * 80)
    
    try:
        from naver_cafe_posts_v2_4_test import NaverCafePublicCrawler
        
        # 설정 재로드 및 수정
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        config['execution_mode']['max_duration_minutes'] = posts_duration
        
        posts_crawler = NaverCafePublicCrawler(config)
        
        # 중복 제거: Phase 1에서 수집된 URL 추가
        if collected_urls:
            posts_crawler.duplicate_checker.urls.update(collected_urls)
            logger.info(f"   → {len(collected_urls)}개 URL 중복 목록에 추가됨")
        
        posts_crawler.run()
        
        new_posts_count = len(posts_crawler.posts) if hasattr(posts_crawler, 'posts') else 0
        logger.info(f"✅ Phase 2 완료: {new_posts_count}개 새 게시물 수집")
        
    except Exception as e:
        logger.error(f"❌ Phase 2 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # =========================================================================
    # 최종 리포트
    # =========================================================================
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 통합 크롤링 완료")
    logger.info("=" * 80)
    logger.info(f"• Phase 1 (Targeting): {len(collected_cafe_ids)}개 카페, {len(collected_urls)}개 게시물")
    logger.info(f"• Phase 2 (Posts): {new_posts_count}개 새 게시물")
    logger.info(f"• 총 게시물: {len(collected_urls) + new_posts_count}개")
    logger.info("=" * 80)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='PM-International 네이버 카페 통합 크롤러 v1.0')
    parser.add_argument('--config', type=str, default='config_cafe.yaml',
                        help='설정 파일 경로')
    parser.add_argument('--duration', type=int, default=None,
                        help='총 실행 시간 (분)')
    
    args = parser.parse_args()
    
    run_unified_crawler(args.config, args.duration)


if __name__ == '__main__':
    main()
