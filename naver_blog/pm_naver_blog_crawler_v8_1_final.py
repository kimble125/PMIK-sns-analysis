#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 블로그 크롤러 v8.1 (1만개 이상 대용량 수집)

🚀 v8.1 신규 개선 사항:
1. 🎯 1만개 이상 대용량 수집 최적화
   - 연도별 키워드 조합 전략 (2023~2025)
   - 키워드당 1000개 수집 (API 최대치)
   - 예상 수집량: 15,000~18,000개
2. 🔍 기간 다양성 확보
   - sort="date" (최신순 정렬)
   - 3년치 데이터 수집으로 시계열 분석 가능
3. 🛡️ 필터링 강화
   - 매트리스 업체 '피엠코리아' 차단
   - 블랙리스트 + 제외 키워드 2중 필터
4. 📊 효율적 키워드 선택
   - v7.7 통계 기반 성공률 높은 키워드만 선택
   - 실패 키워드 7개 제외 (검색 결과 없음)

🔧 v7.7 유지 사항:
- 키워드별 상세 통계 (성공률, 필터링률, 중복률)
- 5단계 필터링 시스템
- 드라이버 재시작 임계값 50회
- published_datetime 안정적 수집

📊 출력 컬럼 (15개):
- 기본: platform, post_id, blog_id, url, title, content, published_datetime
- 추천인: sponsor_phone, sponsor_partner_id
- 참여: like_count, comment_count
- 콘텐츠: hashtags, image_urls, video_urls
- 메타: collected_date

작성자: PMI Korea 데이터 분석팀
버전: 8.1
최종 수정일: 2025-11-08
"""

import os
import re
import json
import time
import random
import logging
import gc
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, unquote
from typing import List, Dict, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# ===========================
# 로깅 설정
# ===========================

class ColoredFormatter(logging.Formatter):
    """컬러 로깅 포맷터"""
    
    COLORS = {
        'DEBUG': '\033[94m',
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[95m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,  # INFO로 복원 (DEBUG는 개발용만)
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 외부 라이브러리 로그 억제 (성능 최적화)
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

for handler in logger.handlers:
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

# ===========================
# 설정값
# ===========================

# Naver Open API 설정 (환경변수 기반)
try:
    import config
    NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
    NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET
except ImportError:
    NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')
    NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')

# User-Agent 목록 (v7.4: 로테이션 지원)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]

# v8.1: 검색 설정 (1만개 이상 대용량 수집)
# 연도별 키워드 조합 전략 (2023~2025)
# v7.7 통계 기반: 성공률 높은 키워드만 선택

# 주요 키워드 (성공률 50%+ 키워드 × 3년)
PRIMARY_KEYWORDS = [
    # 피엠인터내셔널 (성공률 62.5%)
    {"keyword": "피엠인터내셔널 2025", "target": 800},
    {"keyword": "피엠인터내셔널 2024", "target": 800},
    {"keyword": "피엠인터내셔널 2023", "target": 800},
    # 독일피엠 (성공률 65.2%)
    {"keyword": "독일피엠 2025", "target": 800},
    {"keyword": "독일피엠 2024", "target": 800},
    {"keyword": "독일피엠 2023", "target": 800},
    # PM인터내셔널 (성공률 65.9%)
    {"keyword": "PM인터내셔널 2025", "target": 800},
    {"keyword": "PM인터내셔널 2024", "target": 800},
    {"keyword": "PM인터내셔널 2023", "target": 800},
    # 피엠코리아 (성공률 50.0%, 매트리스 업체 필터링 필요)
    {"keyword": "피엠코리아 2025", "target": 800},
    {"keyword": "피엠코리아 2024", "target": 800},
    {"keyword": "피엠코리아 2023", "target": 800},
]

# 제품 키워드 (성공률 40%+ 키워드 × 3년)
SECONDARY_KEYWORDS = [
    # 피트라인 (성공률 61.2%)
    {"keyword": "피트라인 2025", "target": 800},
    {"keyword": "피트라인 2024", "target": 800},
    {"keyword": "피트라인 2023", "target": 800},
    # 탑쉐이프 (성공률 60.0%)
    {"keyword": "탑쉐이프 2025", "target": 800},
    {"keyword": "탑쉐이프 2024", "target": 800},
    {"keyword": "탑쉐이프 2023", "target": 800},
    # 프로쉐이프 (성공률 62.5%)
    {"keyword": "프로쉐이프 2025", "target": 800},
    {"keyword": "프로쉐이프 2024", "target": 800},
    {"keyword": "프로쉐이프 2023", "target": 800},
    # 디드링크 (성공률 62.5%)
    {"keyword": "디드링크 2025", "target": 800},
    {"keyword": "디드링크 2024", "target": 800},
    {"keyword": "디드링크 2023", "target": 800},
    # 뮤노겐 (성공률 57.7%)
    {"keyword": "뮤노겐 2025", "target": 800},
    {"keyword": "뮤노겐 2024", "target": 800},
    {"keyword": "뮤노겐 2023", "target": 800},
    # 엑티바이즈 (성공률 43.5%)
    {"keyword": "엑티바이즈 2025", "target": 800},
    {"keyword": "엑티바이즈 2024", "target": 800},
    {"keyword": "엑티바이즈 2023", "target": 800},
    # 파워칵테일 (성공률 42.9%)
    {"keyword": "파워칵테일 2025", "target": 800},
    {"keyword": "파워칵테일 2024", "target": 800},
    {"keyword": "파워칵테일 2023", "target": 800},
]

# v8.1: 제외 키워드 (v7.7 통계 기반 - 검색 결과 없거나 극소량)
# PMIK (성공률 23%), 리스토레이트 (중복률 29.4%), 옵티멀셋, 제너레이션50,
# 겔링핏, 젤슈츠, 액티바이즈세럼, 영케어3종, 피트라인스킨, 핏라인

# 전체 키워드 리스트
ALL_KEYWORDS = PRIMARY_KEYWORDS + SECONDARY_KEYWORDS

MAX_SEARCH_RESULTS = 1000  # v8.1: API 최대치 (키워드당 1000개)
TOTAL_TARGET = 15000  # v8.1: 1.5만개 목표 (중복 제거 후)
NUM_WORKERS = 1  # v8.1: 단일 프로세스 (안정성 우선)

# 필터링 키워드
PM_BRAND_KEYWORDS = [
    "피엠", "피엠인터내셔널", "PM International", "PMInternational",
    "PM", "FitLine", "핏라인", "피트라인"
]

PM_SALES_KEYWORDS = [
    "추천인", "추천인코드", "추천인 코드", "추천인번호", "추천인 번호",
    "파트너", "파트너코드", "파트너 코드", "파트너번호", "파트너 번호",
    "등록", "가입", "문의"
]

# v8.1: 제외 키워드 강화 (매트리스 업체 필터링)
EXCLUDE_KEYWORDS = [
    "뉴스", "기사", "보도", "공지", "아카데미", "세미나", 
    "팽창탱크", "배관", "기자",
    "매트리스", "침대", "혼수가구", "신혼가구"  # v8.1: 매트리스 업체 차단
]

# v8.1: 언론/뉴스 블로그 블랙리스트 (매트리스 업체 추가)
EXCLUDED_BLOG_IDS = [
    "ysc14",  # 마케팅 뉴스 블로그
    "embarkonsleep",  # v8.1: 매트리스 업체 '피엠코리아'
]

# v7.4: 언론 스타일 제목 패턴
MEDIA_TITLE_PATTERNS = [
    r'"[^"]+",\s*"',  # "OOO 회장", "..." 같은 인용문
    r'기자\s+',
    r'취재\s+',
]

# 크롤링 설정
PAGE_LOAD_TIMEOUT = 10  # v7.6: 타임아웃 단축 (15→10)
REQUEST_DELAY_MIN = 1.5  # v7.7: 멀티프로세싱 고려 (워커당 1.5초)
REQUEST_DELAY_MAX = 2.5  # v7.7: 멀티프로세싱 고려 (워커당 2.5초)
MAX_CONSECUTIVE_ERRORS = 50  # v7.6: 대용량 크롤링 최적화 (5→50)

# ===========================
# v7.3: 적응형 속도 조절
# ===========================

class AdaptiveDelay:
    """성공/실패에 따라 대기 시간을 동적으로 조절"""
    
    def __init__(self, initial_min=2.0, initial_max=4.0):
        self.delay_min = initial_min
        self.delay_max = initial_max
        self.success_count = 0
        self.fail_count = 0
    
    def on_success(self):
        """성공 시 대기 시간 단축 (최소 1초까지)"""
        self.success_count += 1
        if self.success_count >= 3:
            self.delay_min = max(1.0, self.delay_min - 0.2)
            self.delay_max = max(2.0, self.delay_max - 0.3)
            self.success_count = 0
    
    def on_fail(self):
        """실패 시 대기 시간 증가 (최대 10초까지)"""
        self.fail_count += 1
        if self.fail_count >= 2:
            self.delay_min = min(5.0, self.delay_min + 0.5)
            self.delay_max = min(10.0, self.delay_max + 1.0)
            self.fail_count = 0
    
    def get_delay(self) -> float:
        """현재 대기 시간 범위에서 랜덤 값 반환"""
        return random.uniform(self.delay_min, self.delay_max)

# ===========================
# 유틸리티 클래스
# ===========================

class KeywordStats:
    """v7.7: 키워드별 통계"""
    
    def __init__(self, keyword: str, target: int):
        self.keyword = keyword
        self.target = target
        self.searched = 0
        self.collected = 0
        self.filtered = 0
        self.duplicates = 0
        self.errors = 0
    
    def get_success_rate(self) -> float:
        if self.searched == 0:
            return 0.0
        return (self.collected / self.searched) * 100
    
    def get_filter_rate(self) -> float:
        if self.searched == 0:
            return 0.0
        return (self.filtered / self.searched) * 100
    
    def get_duplicate_rate(self) -> float:
        if self.searched == 0:
            return 0.0
        return (self.duplicates / self.searched) * 100
    
    def print_summary(self):
        """키워드 통계 출력"""
        progress = f"{self.collected}/{self.target}"
        success_rate = self.get_success_rate()
        filter_rate = self.get_filter_rate()
        dup_rate = self.get_duplicate_rate()
        
        logger.info(f"  [{self.keyword:15s}] {progress:8s} | "
                   f"성공률: {success_rate:5.1f}% | "
                   f"필터: {filter_rate:5.1f}% | "
                   f"중복: {dup_rate:5.1f}%")

class CrawlStats:
    """크롤링 통계"""
    
    def __init__(self):
        self.total_attempts = 0
        self.success = 0
        self.filtered = 0
        self.duplicates = 0
        self.errors = 0
        self.start_time = time.time()
        self.keyword_stats = {}  # v7.7: 키워드별 통계
    
    def init_keyword(self, keyword: str, target: int):
        """키워드 통계 초기화"""
        self.keyword_stats[keyword] = KeywordStats(keyword, target)
    
    def add_success(self, keyword: str = None):
        self.success += 1
        self.total_attempts += 1
        if keyword and keyword in self.keyword_stats:
            self.keyword_stats[keyword].collected += 1
    
    def add_filtered(self, keyword: str = None):
        self.filtered += 1
        self.total_attempts += 1
        if keyword and keyword in self.keyword_stats:
            self.keyword_stats[keyword].filtered += 1
    
    def add_duplicate(self, keyword: str = None):
        self.duplicates += 1
        self.total_attempts += 1
        if keyword and keyword in self.keyword_stats:
            self.keyword_stats[keyword].duplicates += 1
    
    def add_error(self, keyword: str = None):
        self.errors += 1
        self.total_attempts += 1
        if keyword and keyword in self.keyword_stats:
            self.keyword_stats[keyword].errors += 1
    
    def add_searched(self, keyword: str):
        """검색 시도 카운트"""
        if keyword in self.keyword_stats:
            self.keyword_stats[keyword].searched += 1
    
    def print_keyword_stats(self):
        """키워드별 통계 출력"""
        logger.info(f"\n{'='*70}")
        logger.info("📊 키워드별 수집 현황")
        logger.info(f"{'='*70}")
        
        # 주요 키워드
        logger.info("\n🎯 주요 키워드 (목표: 60개)")
        for kw_info in PRIMARY_KEYWORDS:
            keyword = kw_info["keyword"]
            if keyword in self.keyword_stats:
                self.keyword_stats[keyword].print_summary()
        
        # 나머지 키워드
        logger.info("\n📌 나머지 키워드 (목표: 30개)")
        for kw_info in SECONDARY_KEYWORDS:
            keyword = kw_info["keyword"]
            if keyword in self.keyword_stats:
                self.keyword_stats[keyword].print_summary()
    
    def print_stats(self):
        elapsed = time.time() - self.start_time
        logger.info(f"\n{'='*70}")
        logger.info("📊 전체 크롤링 통계")
        logger.info(f"{'='*70}")
        logger.info(f"총 시도: {self.total_attempts}")
        logger.info(f"✅ 성공: {self.success}")
        logger.info(f"🔍 필터링: {self.filtered}")
        logger.info(f"🔄 중복: {self.duplicates}")
        logger.info(f"❌ 에러: {self.errors}")
        logger.info(f"⏱️  소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
        if self.success > 0:
            logger.info(f"⚡ 평균 속도: {elapsed/self.success:.1f}초/개")
        logger.info(f"{'='*70}")

class FailedURLManager:
    """실패 URL 관리"""
    
    def __init__(self, filename='failed_urls.json'):
        self.filename = filename
        self.failed_urls = {}
        self.load_from_file()
    
    def add_failed(self, url: str, reason: str):
        if url not in self.failed_urls:
            self.failed_urls[url] = {
                'reason': reason,
                'count': 1,
                'last_attempt': datetime.now().isoformat()
            }
        else:
            self.failed_urls[url]['count'] += 1
            self.failed_urls[url]['last_attempt'] = datetime.now().isoformat()
    
    def load_from_file(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.failed_urls = json.load(f)
            except:
                pass
    
    def save_to_file(self):
        if self.failed_urls:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.failed_urls, f, ensure_ascii=False, indent=2)
    
    def get_failed_count(self) -> int:
        return len(self.failed_urls)

# ===========================
# 유틸리티 함수
# ===========================

def normalize_blog_url(blog_id: str, post_id: str) -> str:
    """블로그 URL 정규화"""
    return f"https://blog.naver.com/{blog_id}/{post_id}"

def generate_post_fingerprint(post_data: Dict) -> str:
    """게시물 고유 지문 생성 (중복 방지)"""
    title = post_data.get('title', '')
    content = post_data.get('content', '')[:200]
    return f"{title}_{content}"

def extract_blog_info_from_url(url: str) -> Optional[Dict[str, str]]:
    """URL에서 blog_id와 post_id 추출"""
    try:
        parsed = urlparse(url)
        
        # 방법 1: /blog_id/post_id 형식
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) >= 2:
            return {'blog_id': path_parts[0], 'post_id': path_parts[1]}
        
        # 방법 2: 쿼리 파라미터
        query_params = parse_qs(parsed.query)
        if 'blogId' in query_params and 'logNo' in query_params:
            return {
                'blog_id': query_params['blogId'][0],
                'post_id': query_params['logNo'][0]
            }
        
        return None
    except:
        return None

def clean_text(text: str) -> str:
    """텍스트 정제"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\r\n\t]', ' ', text)
    return text.strip()

# ===========================
# v7.4: 필터링 함수들
# ===========================

def is_excluded_blog(blog_id: str) -> bool:
    """제외 대상 블로그인지 확인 (v7.4)"""
    return blog_id in EXCLUDED_BLOG_IDS

def is_media_style_title(title: str) -> bool:
    """언론 스타일 제목인지 확인 (v7.4)"""
    for pattern in MEDIA_TITLE_PATTERNS:
        if re.search(pattern, title):
            return True
    return False

# ===========================
# 날짜+시간 추출 함수
# ===========================

def parse_published_date(date_text: str) -> str:
    """v7.6: v7.1의 검증된 날짜 파싱 함수 (시간 제외, 날짜만)"""
    if not date_text:
        return ""
    
    try:
        # 불필요한 공백 및 특수문자 제거
        date_text = re.sub(r'\s+', ' ', date_text.strip())
        
        # 패턴 1: YYYY. MM. DD. HH:MM (시간 포함 형식)
        match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*\d{1,2}:\d{2}', date_text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 패턴 2: YYYY. MM. DD. (점 포함 형식)
        match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.', date_text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 패턴 3: YYYY-MM-DD (하이픈 형식)
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        return ""
    except Exception as e:
        logger.debug(f"날짜 파싱 실패: {date_text} - {str(e)}")
        return ""


# ===========================
# 데이터 추출 함수
# ===========================

def extract_sponsor_phone(text: str) -> str:
    """추천인 전화번호 추출"""
    if not text:
        return ""
    
    # 010-xxxx-xxxx 형식만 수집
    phone_patterns = [
        r'010[-\s]?\d{4}[-\s]?\d{4}',
        r'추천인.*?010[-\s]?\d{4}[-\s]?\d{4}',
        r'문의.*?010[-\s]?\d{4}[-\s]?\d{4}',
        r'연락처.*?010[-\s]?\d{4}[-\s]?\d{4}',
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            # 숫자만 추출 후 010으로 시작하는지 확인
            digits = re.sub(r'\D', '', phone)
            if digits.startswith('010') and len(digits) == 11:
                return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    return ""

def extract_sponsor_partner_id(text: str) -> str:
    """추천인 파트너 ID 추출 (정확히 8자리 숫자만)"""
    if not text:
        return ""
    
    # 정확히 8자리 숫자만 추출
    partner_patterns = [
        r'추천인\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{8})\b',
        r'파트너\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{8})\b',
        r'등록\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{8})\b',
        r'\b(\d{8})\b',
    ]
    
    for pattern in partner_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # 정확히 8자리인지 확인
            if len(match) == 8:
                return match
    
    return ""

def extract_hashtags(soup: BeautifulSoup, content_text: str) -> str:
    """해시태그 추출 (v7.5: 메타 태그 필터링 강화)"""
    hashtags = set()
    
    # 제외할 메타 태그 리스트 (placeholder 태그들)
    meta_tags = {'#태그', '#tag', '#해시태그', '#hashtag', '#tags'}
    
    # 방법 1: 게시물 하단의 태그 영역에서 추출
    tag_elements = soup.select('a.link_tag, a[href*="tag"], .se_tag a, .post_tag a')
    for elem in tag_elements:
        tag_text = elem.get_text(strip=True)
        if tag_text:
            if not tag_text.startswith('#'):
                tag_text = '#' + tag_text
            # 메타 태그 필터링
            if tag_text.lower() not in meta_tags:
                hashtags.add(tag_text)
    
    # 방법 2: 본문에서 #태그 추출
    hashtag_pattern = r'#([가-힣a-zA-Z0-9_]+)'
    matches = re.findall(hashtag_pattern, content_text)
    for match in matches:
        tag_text = '#' + match
        # 메타 태그 필터링
        if tag_text.lower() not in meta_tags:
            hashtags.add(tag_text)
    
    return ', '.join(sorted(list(hashtags))) if hashtags else ""

def extract_image_urls(soup: BeautifulSoup) -> str:
    """이미지 URL 추출"""
    image_urls = set()
    
    # 다양한 이미지 선택자
    img_elements = soup.select('img[src], img[data-src], .se-image-resource')
    
    for img in img_elements:
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if src and ('blogfiles.naver.net' in src or 'pstatic.net' in src):
            # 썸네일이 아닌 원본 이미지 URL로 변환
            src = re.sub(r'\?type=\w\d+', '', src)
            image_urls.add(src)
    
    return ', '.join(list(image_urls)[:10]) if image_urls else ""

def extract_video_urls(soup: BeautifulSoup) -> str:
    """비디오 URL 추출 (v7.5: 네이버 영상 포함)"""
    video_urls = set()
    
    # 비디오 및 iframe 선택자 (YouTube + 네이버 영상)
    video_selectors = [
        'video source',
        'video[src]',
        'iframe[src*="youtube"]',
        'iframe[src*="youtu.be"]',
        'iframe[src*="vimeo"]',
        'iframe[src*="tv.naver"]',  # 네이버 TV
        'iframe[src*="naver.com/video"]',  # 네이버 동영상
        'iframe[src*="blog.naver.com/PostView"]',  # 네이버 블로그 내장 동영상
        '.se-video iframe',  # 스마트에디터 비디오
        '.se-component-content[data-type="video"] iframe'
    ]
    
    for selector in video_selectors:
        elements = soup.select(selector)
        for elem in elements:
            src = elem.get('src') or elem.get('data-src')
            if src:
                # 상대 URL을 절대 URL로 변환
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://blog.naver.com' + src
                video_urls.add(src)
    
    return ', '.join(list(video_urls)[:10]) if video_urls else ""

def extract_like_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """좋아요 수 추출"""
    try:
        # 방법 1: Selenium으로 추출
        like_selectors = [
            '.btn_empathy .count',
            '.area_like .count',
            'em.u_cnt._count',
            '.btn_like .count'
        ]
        
        for selector in like_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                like_text = elem.text.strip()
                like_count = int(re.sub(r'\D', '', like_text))
                if like_count > 0:
                    return like_count
            except:
                continue
        
        # 방법 2: BeautifulSoup으로 추출
        page_text = soup.get_text()
        like_patterns = [
            r'공감\s*(\d+)',
            r'좋아요\s*(\d+)',
            r'empathy.*?(\d+)'
        ]
        for pattern in like_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    except Exception as e:
        logger.debug(f"좋아요 수 추출 실패: {str(e)}")
        return 0

def extract_comment_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """댓글 수 추출 (v7.5: 정확도 개선)"""
    try:
        # 방법 1: 댓글 영역 특정 선택자 (가장 정확)
        comment_specific_selectors = [
            '.btn_comment em.u_cnt',  # 댓글 버튼의 카운트만
            'a.btn_comment .count',
            '.comment_count',
            '.cmt_count',
            'span[class*="comment"] em.u_cnt'
        ]
        
        for selector in comment_specific_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                comment_text = elem.text.strip()
                # 숫자만 추출
                numbers = re.findall(r'\d+', comment_text)
                if numbers:
                    count = int(numbers[0])
                    # 비정상적으로 큰 숫자 필터링 (연도 등)
                    if count < 10000:
                        return count
            except:
                continue
        
        # 방법 2: 댓글 목록에서 직접 카운트
        try:
            comment_list = driver.find_elements(By.CSS_SELECTOR, '.se-comment-item, .comment_list .comment_item, #comment_list .comment_item')
            if comment_list:
                return len(comment_list)
        except:
            pass
        
        # 방법 3: BeautifulSoup으로 댓글 영역에서만 추출 (좁은 범위)
        comment_area = soup.select_one('.se-comment-area, .comment_area, #comment, .comment-area')
        if comment_area:
            # "댓글 N개" 패턴
            text = comment_area.get_text()
            match = re.search(r'댓글\s*(\d+)', text)
            if match:
                count = int(match.group(1))
                if count < 10000:
                    return count
        
        # 방법 4: 전체 페이지에서 검색 (최후 수단)
        page_text = soup.get_text()
        # 좁은 패턴 먼저 시도
        patterns = [
            r'댓글\s*(\d{1,3})\s*개',  # "댓글 N개" (최대 3자리)
            r'댓글\s*(\d{1,3})(?!\d)',  # "댓글 N" (뒤에 숫자 없음)
        ]
        for pattern in patterns:
            match = re.search(pattern, page_text)
            if match:
                count = int(match.group(1))
                # 연도나 큰 숫자 필터링
                if count < 1000:
                    return count
        
        return 0
    except Exception as e:
        logger.debug(f"댓글 수 추출 실패: {str(e)}")
        return 0

# ===========================
# v7.4: 다층 필터링 함수
# ===========================

def content_passes_filter(title: str, content: str, full_text: str, 
                          blog_id: str, sponsor_partner_id: str) -> Tuple[bool, str]:
    """콘텐츠 필터링 (v7.4: 다층 필터링)
    
    [단계 1] 블랙리스트 blog_id 체크
    [단계 2] 언론 스타일 제목 체크
    [단계 3] PM 브랜드 키워드 체크
    [단계 4] 판매원 활동 키워드 체크
    [단계 5] 제외 키워드 체크
    
    Returns:
        (통과여부, 실패사유)
    """
    
    # [단계 1] 블랙리스트 blog_id 체크
    if is_excluded_blog(blog_id):
        return False, f"제외 대상 블로그: {blog_id}"
    
    # [단계 2] 언론 스타일 제목 체크
    if is_media_style_title(title):
        return False, "언론 스타일 제목"
    
    # [단계 3] PM 브랜드 키워드 체크
    text_lower = full_text.lower()
    has_pm_keyword = any(keyword.lower() in text_lower for keyword in PM_BRAND_KEYWORDS)
    if not has_pm_keyword:
        return False, "PM 브랜드 키워드 없음"
    
    # [단계 4] 판매원 활동 키워드 체크
    has_sales_keyword = any(keyword in full_text for keyword in PM_SALES_KEYWORDS)
    has_8digit = bool(sponsor_partner_id)
    
    if not (has_sales_keyword or has_8digit):
        return False, "판매원 관련 키워드 없음"
    
    # [단계 5] 제외 키워드 체크 (2개 이상 시 제외)
    exclude_count = sum(1 for keyword in EXCLUDE_KEYWORDS if keyword in full_text)
    if exclude_count >= 2:
        return False, f"제외 키워드 {exclude_count}개 발견"
    
    return True, ""

# ===========================
# Selenium 드라이버 설정
# ===========================

def setup_driver() -> webdriver.Chrome:
    """Selenium 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 메모리 최적화
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    
    # v7.4: User-Agent 랜덤 선택
    user_agent = random.choice(USER_AGENTS)
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    # 자동화 감지 우회
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

# ===========================
# 검색 함수
# ===========================

def search_naver_blog_api(keyword: str, display: int = 100, start: int = 1) -> Optional[Dict]:
    """Naver Open Search API를 사용하여 블로그 검색"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        logger.warning("⚠️  Naver API 키가 없습니다. 스크래핑 방식으로 폴백합니다.")
        return None
    
    # display는 최대 100개로 제한
    display = min(display, 100)
    
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        "User-Agent": random.choice(USER_AGENTS)
    }
    params = {
        "query": keyword,
        "display": display,
        "start": start,
        "sort": "date"  # v8.1: 최신순 정렬 (기간 다양성 확보)
    }
    
    logger.debug(f"API 요청: {url}")
    logger.debug(f"헤더: Client-Id={NAVER_CLIENT_ID[:10]}...")
    logger.debug(f"파라미터: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API 검색 실패 ({keyword}): {str(e)}")
        return None

def parse_search_results(search_data: Dict) -> List[Dict]:
    """API 검색 결과 파싱"""
    results = []
    
    if not search_data or 'items' not in search_data:
        return results
    
    for item in search_data['items']:
        try:
            url = item.get('link', '')
            if not url or 'blog.naver.com' not in url:
                continue
            
            blog_info = extract_blog_info_from_url(url)
            if not blog_info:
                continue
            
            results.append({
                'url': url,
                'blog_id': blog_info['blog_id'],
                'post_id': blog_info['post_id'],
                'postdate': item.get('postdate', ''),
                'bloggername': item.get('bloggername', '')
            })
        except Exception as e:
            continue
    
    logger.info(f"🔍 검색 결과 파싱: {len(results)}개")
    return results

def search_naver_blog_scraping(keyword: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict]:
    """웹 스크래핑을 사용한 블로그 검색 (폴백용)"""
    results = []
    page = 1
    
    while len(results) < max_results:
        try:
            start = (page - 1) * 10 + 1
            search_url = f"https://search.naver.com/search.naver?where=blog&query={keyword}&start={start}"
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS)
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 검색 결과 추출 (다양한 선택자 시도)
            blog_items = soup.select('.view_wrap, .total_wrap, .lst_total, .api_ani_send')
            
            # 선택자가 작동하지 않으면 직접 링크 찾기
            if not blog_items:
                blog_links = soup.select('a[href*="blog.naver.com"]')
                logger.debug(f"직접 링크 검색: {len(blog_links)}개 발견")
                
                for link in blog_links:
                    url = link.get('href', '')
                    title = link.get_text(strip=True) or link.get('title', '')
                    
                    if 'blog.naver.com' in url and title:
                        blog_info = extract_blog_info_from_url(url)
                        if blog_info:
                            results.append({
                                'title': title,
                                'url': url,
                                'blog_id': blog_info['blog_id'],
                                'post_id': blog_info['post_id']
                            })
                        
                        if len(results) >= max_results:
                            break
                
                if results:
                    continue
                else:
                    logger.debug(f"페이지 {page}: 검색 결과 없음")
                    break
            
            for item in blog_items:
                title_elem = item.select_one('.title_link, .api_txt_lines')
                url_elem = item.select_one('a.title_link, a.api_txt_lines')
                
                if title_elem and url_elem:
                    title = title_elem.get_text(strip=True)
                    url = url_elem.get('href', '')
                    
                    if 'blog.naver.com' in url:
                        blog_info = extract_blog_info_from_url(url)
                        if blog_info:
                            results.append({
                                'title': title,
                                'url': url,
                                'blog_id': blog_info['blog_id'],
                                'post_id': blog_info['post_id']
                            })
                        
                        if len(results) >= max_results:
                            break
            
            page += 1
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            logger.error(f"스크래핑 검색 오류 (키워드: {keyword}, 페이지: {page}): {str(e)}")
            break
    
    logger.info(f"🔍 '{keyword}' 스크래핑 검색 결과: {len(results)}개")
    return results

def search_naver_blog(keyword: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict]:
    """네이버 블로그 검색 (API 우선, 스크래핑 폴백)"""
    # API 방식 시도
    search_data = search_naver_blog_api(keyword, max_results)
    if search_data:
        results = parse_search_results(search_data)
        if results:
            logger.info(f"🔍 '{keyword}' API 검색 결과: {len(results)}개")
            return results
    
    # 스크래핑 방식 폴백
    logger.warning(f"⚠️  '{keyword}' API 실패 - 스크래핑으로 폴백")
    return search_naver_blog_scraping(keyword, max_results)

# ===========================
# 크롤링 함수
# ===========================

def crawl_blog_post_selenium(driver: webdriver.Chrome, url: str, blog_id: str, 
                            post_id: str, failed_url_manager: FailedURLManager) -> Optional[Dict]:
    """Selenium을 사용한 블로그 게시물 크롤링 (v7.4)"""
    try:
        logger.debug(f"크롤링 시작: {url}")
        driver.get(url)
        
        # iframe 대기 및 전환 (v7.6: 타임아웃 단축 10초→3초)
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, 'mainFrame'))
            )
            driver.switch_to.frame('mainFrame')
        except TimeoutException:
            logger.debug("iframe 없음 - 본문 직접 크롤링")
        
        # 페이지 로딩 대기 (v7.6: 2초→1초)
        time.sleep(1)
        
        # HTML 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 제목 추출
        title = ""
        title_selectors = [
            '.se-title-text', '.pcol1', '.se_title', 
            '.post-view .tit', '.tit_h3', 'h3.se_title'
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = clean_text(title_elem.get_text())
                break
        
        if not title:
            failed_url_manager.add_failed(url, "제목 없음")
            return None
        
        # 본문 추출
        content = ""
        content_selectors = [
            '.se-main-container', '.post-view', '.se_component_wrap',
            '#postViewArea', '.post_ct'
        ]
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = clean_text(content_elem.get_text())
                break
        
        if not content:
            failed_url_manager.add_failed(url, "본문 없음")
            return None
        
        # 발행 날짜+시간 추출
        published_datetime = ""
        date_selectors = [
            '.se_publishDate', '.post-view .date', '.se_date',
            '.post_info .date', 'span.se_publishDate', '.blog2_series .date',
            '.blog-category .date', '.post_date', 'p.date', 'span.date',
            '.post-meta .date', '.entry-date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_datetime = parse_published_date(date_text)
                if published_datetime:
                    break
        
        # 전체 텍스트 (필터링용)
        full_text = f"{title} {content}"
        
        # 추천인 정보 추출
        sponsor_phone = extract_sponsor_phone(full_text)
        sponsor_partner_id = extract_sponsor_partner_id(full_text)
        
        # v7.4: 다층 필터링 검사
        passes, reason = content_passes_filter(title, content, full_text, blog_id, sponsor_partner_id)
        if not passes:
            logger.debug(f"필터링됨: {reason} - {title[:50]}")
            failed_url_manager.add_failed(url, f"필터링: {reason}")
            return None
        
        # 해시태그 추출 (v7.4: 개선된 방식)
        hashtags = extract_hashtags(soup, content)
        
        # 이미지/비디오 URL 추출
        image_urls = extract_image_urls(soup)
        video_urls = extract_video_urls(soup)
        
        # 좋아요/댓글 수 추출
        like_count = extract_like_count(driver, soup)
        comment_count = extract_comment_count(driver, soup)
        
        # v7.4: 데이터 구성 (post_id 형식 변경)
        post_data = {
            'platform': 'naver_blog',
            'post_id': post_id,  # v7.4: blog_id 중복 제거
            'blog_id': blog_id,
            'url': url,
            'title': title,
            'content': content,
            'published_datetime': published_datetime,
            'sponsor_phone': sponsor_phone,
            'sponsor_partner_id': sponsor_partner_id,
            'like_count': like_count,
            'comment_count': comment_count,
            'hashtags': hashtags,
            'image_urls': image_urls,
            'video_urls': video_urls,
            'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        driver.switch_to.default_content()
        return post_data
        
    except TimeoutException:
        logger.debug(f"타임아웃: {url}")
        failed_url_manager.add_failed(url, "타임아웃")
        return None
    except Exception as e:
        logger.debug(f"크롤링 오류: {str(e)}")
        failed_url_manager.add_failed(url, f"오류: {str(e)}")
        return None
    finally:
        try:
            driver.switch_to.default_content()
        except:
            pass

# ===========================
# 메인 함수
# ===========================

def main():
    """메인 실행 함수 (v8.1)"""
    logger.info("="*70)
    logger.info(f"🚀 PM International 네이버 블로그 크롤러 v8.1 시작")
    logger.info(f"🎯 목표: 15,000개 이상 대용량 수집")
    logger.info(f"📅 기간: 2023~2025년 (3년치 데이터)")
    logger.info(f"🔍 키워드: {len(ALL_KEYWORDS)}개 (연도별 조합)")
    logger.info(f"🔋 맥북 사용자 주의: 전원을 연결하고 절전 모드를 해제해주세요!")
    logger.info(f"⚡ v8.1: 키워드당 1000개, sort=date, 매트리스 업체 필터링")
    logger.info("="*70)
    
    driver = setup_driver()
    stats = CrawlStats()
    failed_url_manager = FailedURLManager()
    adaptive = AdaptiveDelay(initial_min=REQUEST_DELAY_MIN, initial_max=REQUEST_DELAY_MAX)
    
    # v7.7: 키워드별 통계 초기화
    for kw_info in ALL_KEYWORDS:
        stats.init_keyword(kw_info["keyword"], kw_info["target"])
    
    collected_posts = []
    collected_urls = set()
    collected_fingerprints = set()
    consecutive_errors = 0
    crawl_count = 0
    keyword_collected = {}  # 키워드별 수집 개수
    
    try:
        # v7.7: 키워드별 크롤링 (목표 개수 제한)
        for kw_info in ALL_KEYWORDS:
            keyword = kw_info["keyword"]
            target = kw_info["target"]
            keyword_collected[keyword] = 0
            
            if len(collected_posts) >= TOTAL_TARGET:
                break
            
            logger.info(f"\n{'='*70}")
            logger.info(f"🔍 키워드 검색: {keyword} (목표: {target}개)")
            logger.info(f"{'='*70}")
            
            search_results = search_naver_blog(keyword, MAX_SEARCH_RESULTS)
            
            if not search_results:
                logger.warning(f"'{keyword}' 검색 결과 없음")
                continue
            
            for result in search_results:
                # 전체 목표 달성 체크
                if len(collected_posts) >= TOTAL_TARGET:
                    break
                
                # 키워드별 목표 달성 체크
                if keyword_collected[keyword] >= target:
                    logger.info(f"✅ '{keyword}' 목표 달성: {keyword_collected[keyword]}/{target}")
                    break
                
                blog_id = result['blog_id']
                post_id = result['post_id']
                normalized_url = normalize_blog_url(blog_id, post_id)
                
                # 검색 시도 카운트
                stats.add_searched(keyword)
                
                # 중복 체크
                if normalized_url in collected_urls:
                    stats.add_duplicate(keyword)
                    continue
                
                logger.info(f"[전체: {len(collected_posts)+1}/{TOTAL_TARGET}] "
                           f"[{keyword}: {keyword_collected[keyword]+1}/{target}] 크롤링 중...")
                
                # 크롤링 실행
                post_data = crawl_blog_post_selenium(
                    driver, normalized_url, blog_id, post_id, failed_url_manager
                )
                
                if post_data:
                    # 중복 체크 (지문 기반)
                    fingerprint = generate_post_fingerprint(post_data)
                    if fingerprint not in collected_fingerprints:
                        collected_posts.append(post_data)
                        collected_urls.add(normalized_url)
                        collected_fingerprints.add(fingerprint)
                        keyword_collected[keyword] += 1
                        stats.add_success(keyword)
                        consecutive_errors = 0
                        adaptive.on_success()
                        logger.info(f"✅ 수집 완료: {post_data['title'][:50]}")
                    else:
                        stats.add_duplicate(keyword)
                else:
                    stats.add_filtered(keyword)
                    consecutive_errors += 1
                    adaptive.on_fail()
                
                # 연속 에러 시 드라이버 재시작
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.warning(f"⚠️  연속 {MAX_CONSECUTIVE_ERRORS}회 에러 - 드라이버 재시작 (v7.6: 대용량 최적화)")
                    driver.quit()
                    time.sleep(3)
                    driver = setup_driver()
                    consecutive_errors = 0
                    gc.collect()
                
                crawl_count += 1
                
                # 적응형 대기 시간
                delay = adaptive.get_delay()
                time.sleep(delay)
                
                # v7.7: 주기적 통계 출력 (50개마다)
                if crawl_count % 50 == 0:
                    stats.print_keyword_stats()
                    gc.collect()
            
            # 키워드 완료 후 짧은 대기
            if len(collected_posts) < TOTAL_TARGET:
                time.sleep(random.uniform(1, 2))
        
        # v7.7: 최종 통계 출력
        stats.print_keyword_stats()
        stats.print_stats()
        
        # CSV 저장
        if collected_posts:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'naver_blog_pm_v8_1_{timestamp}.csv'
            
            df = pd.DataFrame(collected_posts)
            
            # 컬럼 순서 명시
            column_order = [
                'platform', 'post_id', 'blog_id', 'url', 'title', 'content',
                'published_datetime', 'sponsor_phone', 'sponsor_partner_id',
                'like_count', 'comment_count', 'hashtags', 'image_urls',
                'video_urls', 'collected_date'
            ]
            
            df = df[column_order]
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            logger.info(f"\n{'='*70}")
            logger.info(f"💾 저장 완료: {filename}")
            logger.info(f"📊 총 수집: {len(collected_posts)}개")
            logger.info(f"📋 컬럼: {len(column_order)}개")
            logger.info(f"{'='*70}")
        else:
            logger.warning("⚠️  수집된 게시물이 없습니다.")
        
        failed_url_manager.save_to_file()
        if failed_url_manager.get_failed_count() > 0:
            logger.info(f"❌ 실패 URL: {failed_url_manager.get_failed_count()}개 (failed_urls.json)")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  사용자 중단")
        stats.print_stats()
    
    except Exception as e:
        logger.error(f"❌ 예기치 않은 오류: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        stats.print_stats()
    
    finally:
        driver.quit()
        logger.info("✅ 드라이버 종료")
        logger.info("="*70)
        logger.info("🏁 크롤링 완료")
        logger.info("="*70)

if __name__ == "__main__":
    main()
