#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 카페 크롤러 v2.5 (Test 버전)

🔒 v2.5 핵심 변경사항 (from v2.4):
1. 🔧 검색 페이지네이션 버그 수정: start 파라미터 → 무한 스크롤 방식
   - 네이버 통합검색에서 start 파라미터가 미작동 (동일 결과 반환)
   - 무한 스크롤로 변경하여 더 많은 결과 수집 가능
2. 🗑️ Sponsor CSV 제거: posts CSV에 sponsor_phone 컬럼 이미 포함
3. 📊 연속 빈 결과 체크 개선: 5회 연속 새 결과 없을 때만 종료

이전 버전 (v2.4) 주요 기능:
- published_datetime ISO 형식 정규화
- 댓글 셀렉터 개선 (strong.num)
- 해시태그 추출 개선: HTML 셀렉터 a.tag_link 사용

📊 출력 테이블:
- posts: 게시물 데이터 (sponsor_phone, sponsor_partner_id 컬럼 포함)

⚠️ 법적 고지:
- 본 크롤러는 공개된 정보만 수집합니다
- 로그인이 필요한 카페/게시판은 수집하지 않습니다
- robots.txt 및 네이버 이용약관을 준수합니다

작성자: PMI Korea 데이터 분석팀
버전: 2.5.0 (Test)
최종 수정일: 2025-12-01
"""

import os
import re
import json
import time
import random
import logging
import signal
import sys
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, unquote, quote
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict

import yaml
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

# =============================================================================
# 설정 로드
# =============================================================================

def load_config(config_path: str = "config_cafe.yaml") -> Dict:
    """YAML 설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"⚠️ 설정 파일을 찾을 수 없습니다: {config_path}")
        print("기본 설정으로 실행합니다.")
        return get_default_config()
    except yaml.YAMLError as e:
        print(f"⚠️ YAML 파싱 오류: {e}")
        return get_default_config()

def get_default_config() -> Dict:
    """기본 설정 반환 (v2.3: 확장된 키워드 및 설정)"""
    return {
        'execution_mode': {
            'test_mode': True,
            'max_duration_minutes': 60,
            'max_posts_per_cafe': 10000,
            'checkpoint_interval_minutes': 10
        },
        'crawling': {
            'page_load_timeout': 15,
            'request_delay_min': 2.0,
            'request_delay_max': 4.0,
            'max_pages_per_keyword': 30,  # v2.3: 30페이지로 증가
            'max_retries': 3,
            'headless': True,
            'scroll_wait_seconds': 2,      # v2.3: 스크롤 후 대기 시간
            'dynamic_load_timeout': 10     # v2.3: 동적 로딩 대기 타임아웃
        },
        'keywords': {
            'primary': [
                {'keyword': '피엠인터내셔널', 'target': 300},
                {'keyword': '독일피엠', 'target': 300},
                {'keyword': 'PM인터내셔널', 'target': 300},
                {'keyword': '피엠코리아', 'target': 300}
            ],
            'secondary': [
                {'keyword': '피트라인', 'target': 200},
                {'keyword': '탑쉐이프', 'target': 200},
                {'keyword': '프로쉐이프', 'target': 200},
                {'keyword': '디드링크', 'target': 200},
                {'keyword': '뮤노겐', 'target': 200},
                {'keyword': '엑티바이즈', 'target': 200},
                {'keyword': '파워칵테일', 'target': 200},
                {'keyword': '레스토레이트', 'target': 200}
            ]
        },
        'filters': {
            'pm_brand_keywords': [
                '피엠인터내셔널', 'PM인터내셔널', 'PM International', 'PMInternational',
                'PMIK', '독일PM', '독일피엠', 'FitLine', '핏라인', '피트라인', '피엠코리아'
            ],
            'product_keywords': [
                '피트라인', '엑티바이즈', 'Activize', '뮤노겐', 'Munogen',
                '파워칵테일', 'PowerCocktail', '레스토레이트', 'Restorate',
                '프로쉐이프', 'ProShape', '탑쉐이프', 'TopShape', '디드링크', 'D-Drink'
            ],
            'sales_keywords': [
                '추천인', '추천인코드', '추천인번호', '파트너', '파트너코드',
                '파트너번호', '팀파트너', '후원인', '등록', '가입', '문의'
            ],
            'exclude_keywords': [
                '뉴스', '기사', '보도', '공지', '아카데미', '세미나', '기자', '취재',
                '혼수가구', '신혼가구', '팽창탱크', '배관', '이력서', 'salary', 'job',
                'recruit', '근무환경', 'IR', '공시'
            ],
            'exclude_keyword_threshold': 5  # v2.3: 제외 키워드 5개 이상 시 필터링
        },
        'user_agents': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ],
        'output': {
            'data_dir': 'data',
            'csv_encoding': 'utf-8-sig',
            'max_content_length': 10000
        }
    }

# 설정 로드
CONFIG = load_config()

# =============================================================================
# 로깅 설정
# =============================================================================

def setup_logging() -> logging.Logger:
    """로깅 설정 (v2.5: 강제 파일 핸들러 추가)"""
    log_dir = CONFIG.get('logging', {}).get('log_dir', 'logs')
    Path(log_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"{log_dir}/cafe_posts_{timestamp}.log"
    
    # 로거 가져오기 (모듈별 독립 로거)
    logger = logging.getLogger('naver_cafe_posts_v2_5')
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 (항상 기록)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 억제
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info(f"📝 로그 파일: {log_file}")
    return logger

logger = setup_logging()

# =============================================================================
# 데이터 클래스 정의
# =============================================================================

@dataclass
class CafePost:
    """게시물 데이터 클래스 (v2.5 - cafe_type, is_pm_keyword 추가)"""
    platform: str = "naver_cafe"
    cafe_id: str = ""                # URL 경로에서 추출 (예: joonggonara)
    cafe_name: str = ""              # 카페 이름
    article_id: str = ""             # URL 경로에서 추출 (예: 1111306637)
    url: str = ""
    title: str = ""
    content: str = ""                # 원본 그대로 저장 (후처리로 정제)
    author_nickname: str = ""        # author_id 삭제, nickname만 유지
    published_datetime: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    
    # PM 특화 필드
    sponsor_phone: str = ""
    sponsor_partner_id: str = ""
    hashtags: str = ""               # 해시태그 유지
    
    # 미디어 URL (v2.3 신규)
    image_urls: str = ""             # 이미지 URL 목록 (| 구분)
    video_urls: str = ""             # 영상 URL 목록 (| 구분)
    
    # 메타 필드
    collected_datetime: str = ""
    is_public: bool = True
    
    # v2.5 신규 필드
    cafe_type: str = "general"       # 일반 카페 (Phase 2)
    is_pm_keyword: bool = True       # PM 키워드 포함 여부

@dataclass  
class CafeInfo:
    """카페 정보 데이터 클래스 (카페소개 페이지에서 수집)"""
    cafe_id: str = ""                # 카페 URL ID (예: joonggonara)
    cafe_name: str = ""              # 카페 이름
    cafe_url: str = ""               # 카페 URL
    
    # 카페소개 정보
    established_date: str = ""       # 카페 설립일
    cafe_topic: str = ""             # 주제
    cafe_description: str = ""       # 카페 설명
    cafe_keywords: str = ""          # 카페 검색어
    join_method: str = ""            # 가입 방식
    
    # 통계 정보
    member_count: int = 0            # 카페멤버 수
    total_posts: int = 0             # 전체 게시글 수
    total_visitors: int = 0          # 총 방문자 수
    cafe_ranking: str = ""           # 카페 랭킹
    
    # 메타 필드
    collected_datetime: str = ""
    pm_posts_collected: int = 0      # 이 카페에서 수집된 PM 관련 게시물 수

# =============================================================================
# 유틸리티 클래스
# =============================================================================

class TimeManager:
    """시간 관리 클래스"""
    
    def __init__(self, max_duration_minutes: int):
        self.start_time = time.time()
        self.max_duration_seconds = max_duration_minutes * 60
        self.last_checkpoint = time.time()
    
    def is_time_exceeded(self) -> bool:
        """시간 초과 여부"""
        return time.time() - self.start_time >= self.max_duration_seconds
    
    def get_elapsed_minutes(self) -> float:
        """경과 시간 (분)"""
        return (time.time() - self.start_time) / 60
    
    def get_remaining_minutes(self) -> float:
        """남은 시간 (분)"""
        remaining = self.max_duration_seconds - (time.time() - self.start_time)
        return max(0, remaining / 60)
    
    def should_checkpoint(self, interval_minutes: int) -> bool:
        """체크포인트 저장 시점 여부"""
        if time.time() - self.last_checkpoint >= interval_minutes * 60:
            self.last_checkpoint = time.time()
            return True
        return False

class DuplicateChecker:
    """중복 체크 관리자"""
    
    def __init__(self):
        self.post_ids: Set[str] = set()
        self.urls: Set[str] = set()
        self.fingerprints: Set[str] = set()
    
    def is_duplicate(self, post_id: str = None, url: str = None, 
                     title: str = None, content: str = None) -> bool:
        """중복 여부 확인"""
        if post_id and post_id in self.post_ids:
            return True
        if url and url in self.urls:
            return True
        
        # 제목+내용 일부로 fingerprint 생성
        if title and content:
            fingerprint = f"{title}_{content[:100]}"
            if fingerprint in self.fingerprints:
                return True
        
        return False
    
    def add(self, post_id: str = None, url: str = None,
            title: str = None, content: str = None):
        """수집 데이터 추가"""
        if post_id:
            self.post_ids.add(post_id)
        if url:
            self.urls.add(url)
        if title and content:
            self.fingerprints.add(f"{title}_{content[:100]}")

class CrawlStats:
    """크롤링 통계"""
    
    def __init__(self):
        self.total_attempts = 0
        self.success = 0
        self.filtered = 0
        self.duplicates = 0
        self.errors = 0
        self.skipped_private = 0     # 비공개로 스킵된 수
    
    def print_stats(self, elapsed_minutes: float):
        """통계 출력"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 크롤링 통계")
        logger.info("=" * 70)
        logger.info(f"⏰ 실행 시간: {elapsed_minutes:.1f}분")
        logger.info(f"📝 총 시도: {self.total_attempts}")
        logger.info(f"✅ 성공: {self.success}")
        logger.info(f"🔍 필터링: {self.filtered}")
        logger.info(f"🔄 중복: {self.duplicates}")
        logger.info(f"🔒 비공개 스킵: {self.skipped_private}")
        logger.info(f"❌ 에러: {self.errors}")
        if self.success > 0 and elapsed_minutes > 0:
            logger.info(f"⚡ 수집 속도: {self.success / elapsed_minutes:.1f}개/분")
        logger.info("=" * 70)

# =============================================================================
# 추출기 클래스
# =============================================================================

class DataExtractor:
    """데이터 추출 유틸리티"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.pm_keywords = config.get('filters', {}).get('pm_brand_keywords', [])
        self.product_keywords = config.get('filters', {}).get('product_keywords', [])
        self.sales_keywords = config.get('filters', {}).get('sales_keywords', [])
        self.exclude_keywords = config.get('filters', {}).get('exclude_keywords', [])
    
    def extract_sponsor_phone(self, text: str) -> str:
        """전화번호 추출 (v2.4 개선: 점/공백 구분 지원)"""
        if not text:
            return ""
        
        # 010-XXXX-XXXX, 010.XXXX.XXXX, 010 XXXX XXXX 등 다양한 패턴
        patterns = [
            r'010[-.\s]?\d{4}[-.\s]?\d{4}',  # 010-1234-5678, 010.1234.5678
            r'☎\s*010[-.\s]?\d{4}[-.\s]?\d{4}',  # ☎ 010-1234-5678
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = re.sub(r'\D', '', match.group(0))
                if len(phone) == 11 and phone.startswith('010'):
                    return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
        return ""
    
    def extract_sponsor_partner_id(self, text: str) -> str:
        """파트너 ID 추출 (v2.4 개선: 7-8자리, 이름 뒤 번호 지원)"""
        if not text:
            return ""
        
        patterns = [
            r'후원코드[:\s]*[가-힣*]*?\s*(\d{7,8})',  # 후원코드: 이*훈 20589722
            r'추천인?\s*(?:코드|번호|ID)?[:\s：]*[가-힣*]*?\s*(\d{7,8})',
            r'파트너\s*(?:코드|번호|ID)?[:\s：]*(\d{7,8})',
            r'후원\s*(?:코드|번호|ID)?[:\s：]*(\d{7,8})',
            r'(?:PM|피엠)\s*(?:코드|번호)?[:\s：]*(\d{7,8})',
            r'(\d{8})\s*입력',  # 20589722 입력
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def extract_hashtags(self, text: str) -> str:
        """해시태그 추출"""
        if not text:
            return ""
        
        hashtags = re.findall(r'#[\w가-힣]+', text)
        return ', '.join(hashtags[:20])  # 최대 20개
    
    def find_keywords(self, text: str, keyword_list: List[str]) -> List[str]:
        """키워드 매칭"""
        if not text:
            return []
        
        text_lower = text.lower()
        found = []
        for kw in keyword_list:
            if kw.lower() in text_lower:
                found.append(kw)
        return found
    
    def count_media(self, soup: BeautifulSoup) -> Tuple[int, int, int]:
        """이미지, 비디오, 링크 수 카운트"""
        image_count = len(soup.find_all('img'))
        video_count = len(soup.find_all(['video', 'iframe']))
        link_count = len(soup.find_all('a', href=True))
        return image_count, video_count, link_count
    
    def should_filter(self, title: str, content: str) -> Tuple[bool, str]:
        """필터링 여부 판단 (v2.3: 제외 키워드 5개 이상 시만 필터링)"""
        full_text = f"{title} {content}".lower()
        
        # 제외 키워드 체크 (v2.3: 5개 이상 매칭 시만 필터링)
        exclude_threshold = self.config.get('filters', {}).get('exclude_keyword_threshold', 5)
        exclude_count = 0
        matched_excludes = []
        
        for kw in self.exclude_keywords:
            if kw.lower() in full_text:
                exclude_count += 1
                matched_excludes.append(kw)
        
        if exclude_count >= exclude_threshold:
            return True, f"제외 키워드 {exclude_count}개 매칭: {', '.join(matched_excludes[:5])}"
        
        # PM 관련 키워드 체크 (최소 1개 필요)
        has_pm = any(kw.lower() in full_text for kw in self.pm_keywords)
        has_product = any(kw.lower() in full_text for kw in self.product_keywords)
        
        if not has_pm and not has_product:
            return True, "PM/제품 키워드 없음"
        
        return False, "통과"

# =============================================================================
# 메인 크롤러 클래스
# =============================================================================

class NaverCafePublicCrawler:
    """네이버 카페 공개 게시판 크롤러"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        
        # 매니저 초기화
        test_mode = config.get('execution_mode', {})
        max_duration = test_mode.get('max_duration_minutes', 60)
        self.time_manager = TimeManager(max_duration)
        self.duplicate_checker = DuplicateChecker()
        self.stats = CrawlStats()
        self.extractor = DataExtractor(config)
        
        # 데이터 저장소
        self.posts: List[CafePost] = []
        self.cafe_infos: Dict[str, CafeInfo] = {}  # cafe_id -> CafeInfo
        
        # v2.3: sponsor 정보 있는 카페 추적 (2차 수집용)
        self.sponsor_cafes: Dict[str, Dict] = {}  # cafe_id -> {cafe_name, post_count, phones, partner_ids}
        
        # 시작/종료 시간 기록
        self.start_datetime = datetime.now()
        self.end_datetime = None
        
        # 버그/에러 로그
        self.error_logs: List[str] = []
        
        # 설정값
        self.max_posts = test_mode.get('max_posts_per_cafe', 100)
        self.checkpoint_interval = test_mode.get('checkpoint_interval_minutes', 10)
        
        # v2.3: Exponential Backoff 설정
        self.retry_delay = 5  # 초기 재시도 대기 시간
        self.max_retry_delay = 120  # 최대 재시도 대기 시간
        self.consecutive_errors = 0  # 연속 에러 카운트
        
        # 종료 플래그
        self.should_stop = False
    
    def setup_driver(self):
        """Selenium 드라이버 설정"""
        chrome_options = Options()
        
        crawl_config = self.config.get('crawling', {})
        if crawl_config.get('headless', True):
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        
        # User-Agent 설정
        user_agents = self.config.get('user_agents', [])
        if user_agents:
            chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(crawl_config.get('page_load_timeout', 15))
            logger.info("✅ Chrome 드라이버 초기화 완료")
        except Exception as e:
            logger.error(f"❌ 드라이버 초기화 실패: {e}")
            raise
    
    def random_delay(self):
        """랜덤 딜레이"""
        crawl_config = self.config.get('crawling', {})
        delay = random.uniform(
            crawl_config.get('request_delay_min', 2.0),
            crawl_config.get('request_delay_max', 4.0)
        )
        time.sleep(delay)
    
    def check_captcha(self) -> bool:
        """캡차 감지 (v2.3 신규) - 실제 캡차 페이지만 감지"""
        try:
            # 실제 캡차 차단 페이지인지 확인 (검색 결과가 없고 캡차 폼이 있는 경우)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 정상적인 검색 결과가 있으면 캡차 아님
            if soup.select('a.title_link') or soup.select('a.api_txt_lines'):
                return False
            
            # 캡차 입력 폼 확인
            captcha_forms = soup.select('form[action*="captcha"], #captcha, .captcha_wrap')
            if captcha_forms:
                logger.warning("🚫 캡차 입력 폼 감지!")
                return True
            
            # 접근 차단 메시지 확인
            page_text = soup.get_text().lower()
            block_indicators = ['자동입력방지', '보안문자 입력', '로봇이 아닙니다', '자동등록방지문자']
            for indicator in block_indicators:
                if indicator in page_text:
                    logger.warning(f"🚫 차단 메시지 감지: {indicator}")
                    return True
            
            return False
        except:
            return False
    
    def handle_rate_limit(self):
        """Exponential Backoff으로 rate limit 처리 (v2.3 신규)"""
        self.consecutive_errors += 1
        wait_time = min(self.retry_delay * (2 ** self.consecutive_errors), self.max_retry_delay)
        logger.warning(f"⚠️ Rate limit 감지! {wait_time}초 대기 후 재시도...")
        self.error_logs.append(f"Rate limit - {wait_time}초 대기")
        time.sleep(wait_time)
    
    def reset_rate_limit(self):
        """성공 시 rate limit 카운터 리셋"""
        self.consecutive_errors = 0
        self.retry_delay = 5
    
    def scroll_and_wait(self):
        """스크롤 다운 후 동적 콘텐츠 로딩 대기 (v2.3 신규)"""
        crawl_config = self.config.get('crawling', {})
        scroll_wait = crawl_config.get('scroll_wait_seconds', 2)
        
        # 페이지 끝까지 스크롤
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_wait)
        
        # 다시 위로 스크롤 (일부 사이트는 스크롤 업 시 추가 로딩)
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
    
    def search_cafe_posts_via_naver(self, keyword: str, max_results: int = 50) -> List[Dict]:
        """
        네이버 통합검색(카페 탭)을 통해 공개 게시글 URL 수집
        v2.5: 무한 스크롤 방식으로 변경 (start 파라미터 미작동 문제 해결)
        """
        results = []
        collected_keys = set()  # 전체 검색에서 중복 체크용
        max_scrolls = self.config.get('crawling', {}).get('max_pages_per_keyword', 30)
        consecutive_empty = 0
        
        logger.info(f"🔍 네이버 카페 검색: {keyword} (목표: {max_results}개, 최대 {max_scrolls}회 스크롤)")
        
        try:
            # 네이버 카페 검색 URL (최신순 정렬)
            encoded_keyword = quote(keyword)
            search_url = f"https://search.naver.com/search.naver?where=article&query={encoded_keyword}&sort=date"
            
            self.driver.get(search_url)
            
            # 초기 로딩 대기
            try:
                dynamic_timeout = self.config.get('crawling', {}).get('dynamic_load_timeout', 10)
                WebDriverWait(self.driver, dynamic_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.total_wrap, .api_subject_bx, .lst_total'))
                )
            except TimeoutException:
                logger.debug(f"  → 초기 로딩 타임아웃")
            
            # 캡차 감지
            if self.check_captcha():
                logger.warning("🚫 캡차 감지! Exponential Backoff 적용")
                self.handle_rate_limit()
                return results
            
            # v2.5: 무한 스크롤로 결과 수집
            for scroll_num in range(max_scrolls):
                if len(results) >= max_results:
                    break
                
                # 현재 페이지 파싱
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 카페 글 결과 찾기 (다중 백업 선택자)
                selector_list = [
                    'a.title_link',
                    'a.api_txt_lines.total_tit',
                    '.total_area a.api_txt_lines',
                    '.cafe_area a.title',
                    'a.link_txt',
                ]
                
                articles = []
                for selector in selector_list:
                    articles = soup.select(selector)
                    if articles:
                        logger.debug(f"  → 선택자 '{selector}' 사용 ({len(articles)}개)")
                        break
                
                if not articles:
                    # 최후의 수단: 모든 cafe.naver.com 링크 찾기
                    all_links = soup.find_all('a', href=True)
                    articles = [a for a in all_links if 'cafe.naver.com' in a.get('href', '') 
                               and re.search(r'/\d+', a.get('href', ''))]
                
                if not articles:
                    logger.info(f"  → 스크롤 {scroll_num+1}: 검색 결과 없음")
                    break
                
                # 새 URL 수집
                new_found = 0
                for article in articles:
                    if len(results) >= max_results:
                        break
                    
                    href = article.get('href', '')
                    if 'cafe.naver.com' in href:
                        # URL 키 추출 (cafe_id + article_id)
                        url_key_match = re.search(r'cafe\.naver\.com/([\w-]+)/(\d+)', href)
                        url_key = f"{url_key_match.group(1)}_{url_key_match.group(2)}" if url_key_match else href
                        
                        if url_key not in collected_keys:
                            results.append({'url': href, 'keyword': keyword})
                            collected_keys.add(url_key)
                            new_found += 1
                
                if new_found == 0:
                    consecutive_empty += 1
                    logger.info(f"  → 스크롤 {scroll_num+1}: 새로운 결과 없음 (연속 {consecutive_empty}회)")
                    if consecutive_empty >= 10:
                        logger.info(f"  → 10회 연속 새 결과 없음, '{keyword}' 검색 종료")
                        break
                else:
                    consecutive_empty = 0
                    logger.info(f"  → 스크롤 {scroll_num+1}: {new_found}개 추가 (총 {len(results)}개)")
                
                # 스크롤 다운으로 추가 콘텐츠 로딩
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 로딩 대기
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # 더 이상 스크롤 불가 (끝에 도달)
                    logger.info(f"  → 페이지 끝 도달, '{keyword}' 검색 종료")
                    break
                
                self.random_delay()
                
        except Exception as e:
            logger.error(f"검색 오류 ({keyword}): {e}")
            self.error_logs.append(f"검색 오류: {keyword} - {str(e)[:100]}")
            self.handle_rate_limit()
        
        logger.info(f"  → '{keyword}' 검색 완료: {len(results)}개 URL 수집")
        return results
    
    def is_public_accessible(self, url: str) -> bool:
        """
        URL이 로그인 없이 접근 가능한지 확인
        """
        try:
            self.driver.get(url)
            time.sleep(2)
            
            page_source = self.driver.page_source.lower()
            
            # 로그인 필요 메시지 체크
            login_indicators = [
                '로그인이 필요합니다',
                '카페 가입 후',
                '멤버만 볼 수 있습니다',
                '비공개 게시판',
                '가입 후 이용',
                'login_required'
            ]
            
            for indicator in login_indicators:
                if indicator in page_source:
                    return False
            
            return True
            
        except Exception as e:
            logger.debug(f"접근성 체크 실패: {e}")
            return False
    
    def extract_post_data(self, url: str, keyword: str) -> Optional[CafePost]:
        """
        게시글 데이터 추출
        """
        try:
            self.driver.get(url)
            self.random_delay()
            
            # iframe 처리 (네이버 카페 구조)
            try:
                self.driver.switch_to.frame('cafe_main')
            except:
                pass  # iframe이 없는 경우도 있음
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 기본 정보 추출
            post = CafePost()
            post.url = url
            post.collected_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # URL에서 카페/게시글 ID 추출 (v2.2 수정: 두 가지 URL 형식 지원)
            # 형식1: cafe.naver.com/cafeid/articleid?q=...
            # 형식2: cafe.naver.com/cafeid?articleid=...
            url_match = re.search(r'cafe\.naver\.com/([\w-]+)/(\d+)', url)
            if url_match:
                post.cafe_id = url_match.group(1)
                post.article_id = url_match.group(2)
            else:
                # 백업 패턴: articleid 파라미터 형식
                url_match2 = re.search(r'cafe\.naver\.com/([\w-]+).*?articleid=(\d+)', url, re.IGNORECASE)
                if url_match2:
                    post.cafe_id = url_match2.group(1)
                    post.article_id = url_match2.group(2)
            
            # 제목 추출
            title_selectors = [
                'h3.title_text',
                '.article_title',
                '.tit-box .b',
                'h2.title'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    post.title = title_elem.get_text(strip=True)
                    break
            
            # 내용 추출 (원본 그대로 저장)
            content_selectors = [
                '.article_viewer',
                '.ArticleContentBox', 
                '#tbody',
                '.se-main-container',
                '.content_view',
                'div.article_container'
            ]
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    post.content = content_elem.get_text(strip=True)
                    max_len = self.config.get('output', {}).get('max_content_length', 10000)
                    post.content = post.content[:max_len]
                    break
            
            # 작성자 정보 (author_nickname만 수집)
            author_selectors = [
                '.nickname',
                '.profile_info .nick',
                '.WriterInfo .nick',
                'a.nick',
                '.article_writer .nick'
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    post.author_nickname = author_elem.get_text(strip=True)
                    break
            
            # 작성일 (v2.4: ISO 형식 정규화)
            date_selectors = [
                '.date',
                '.article_info .date',
                'span.datetime'
            ]
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    raw_date = date_elem.get_text(strip=True)
                    # 2025.10.15. 10:59 → 2025-10-15 10:59:00
                    date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})\.\s*(\d{2}):(\d{2})', raw_date)
                    if date_match:
                        post.published_datetime = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)} {date_match.group(4)}:{date_match.group(5)}:00"
                    else:
                        post.published_datetime = raw_date
                    break
            
            # 조회수 (v2.2 개선: 더 많은 선택자)
            view_selectors = [
                '.article_info .count',
                'span.count',
                '.info_area .count',
                '.view_count',
                '.article_header .count'
            ]
            for selector in view_selectors:
                view_elem = soup.select_one(selector)
                if view_elem:
                    view_text = view_elem.get_text()
                    view_match = re.search(r'(\d[\d,]*)', view_text)
                    if view_match:
                        post.view_count = int(view_match.group(1).replace(',', ''))
                    break
            
            # 좋아요 수 (v2.2 신규)
            like_selectors = [
                '.u_cnt._count',
                '.like_article .u_cnt',
                '.sympathy_cnt',
                'em.u_cnt._count',
                '.like_btn .count'
            ]
            for selector in like_selectors:
                like_elem = soup.select_one(selector)
                if like_elem:
                    like_text = like_elem.get_text(strip=True)
                    like_match = re.search(r'(\d+)', like_text.replace(',', ''))
                    if like_match:
                        post.like_count = int(like_match.group(1))
                    break
            
            # 댓글 수 (v2.4 개선: strong.num 셀렉터)
            # HTML 예시: <strong class="num">1</strong>
            comment_elem = soup.select_one('strong.num')
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                if comment_text.isdigit():
                    post.comment_count = int(comment_text)
            
            # 카페 이름 추출 (v2.2 신규)
            cafe_name_selectors = [
                '.cafe_name',
                '.cafe_title',
                'h1.cafe_name',
                '.cafe-info .name'
            ]
            for selector in cafe_name_selectors:
                cafe_name_elem = soup.select_one(selector)
                if cafe_name_elem:
                    post.cafe_name = cafe_name_elem.get_text(strip=True)
                    break
            
            # PM 특화 데이터 추출
            full_text = f"{post.title} {post.content}"
            post.sponsor_phone = self.extractor.extract_sponsor_phone(full_text)
            post.sponsor_partner_id = self.extractor.extract_sponsor_partner_id(full_text)
            
            # v2.4 추가 수정: 해시태그 추출 개선 (HTML 셀렉터 + 텍스트 fallback)
            # HTML 예시: <a class="tag_link">#부업</a>
            hashtags = []
            for tag_elem in soup.select('a.tag_link'):
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    hashtags.append(tag_text if tag_text.startswith('#') else f'#{tag_text}')
            # fallback: 텍스트에서 추출
            if not hashtags:
                hashtags = re.findall(r'#[\w가-힣]+', full_text)
            post.hashtags = ', '.join(hashtags[:20])
            
            # v2.3: 이미지 URL 수집
            image_urls = []
            img_selectors = [
                'img.se-image-resource',      # 스마트에디터
                'img.article_img',            # 기본 에디터
                'img[src*="cafeptthumb"]',    # 카페 썸네일
                'img[src*="postfiles"]',      # 포스트 파일
                '.article_viewer img',        # 게시글 뷰어 내 이미지
                '.se-main-container img'      # SE 컨테이너
            ]
            for selector in img_selectors:
                for img in soup.select(selector):
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src:
                        # 상대 경로 처리
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif not src.startswith('http'):
                            continue
                        # 중복 제거 및 유효한 이미지만
                        if src not in image_urls and 'blank' not in src.lower():
                            image_urls.append(src)
            post.image_urls = ' | '.join(image_urls[:20])  # 최대 20개
            
            # v2.3: 영상 URL 수집
            video_urls = []
            # 네이버 TV
            for iframe in soup.select('iframe[src*="tv.naver"], iframe[src*="serviceapi.nmv"]'):
                src = iframe.get('src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    video_urls.append(src)
            # YouTube
            for iframe in soup.select('iframe[src*="youtube"], iframe[src*="youtu.be"]'):
                src = iframe.get('src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    video_urls.append(src)
            # HTML5 video
            for video in soup.select('video source'):
                src = video.get('src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    video_urls.append(src)
            post.video_urls = ' | '.join(video_urls[:10])  # 최대 10개
            
            # 기본 프레임으로 복귀
            self.driver.switch_to.default_content()
            
            return post
            
        except Exception as e:
            logger.error(f"게시글 추출 실패 ({url}): {e}")
            self.driver.switch_to.default_content()
            return None
    
    def update_cafe_info(self, post: CafePost):
        """카페 정보 업데이트 (v2.3: sponsor 추적 추가)"""
        cafe_id = post.cafe_id
        
        if not cafe_id:
            return
        
        if cafe_id not in self.cafe_infos:
            # 새 카페 정보 생성
            cafe_info = CafeInfo()
            cafe_info.cafe_id = cafe_id
            cafe_info.cafe_name = post.cafe_name
            cafe_info.cafe_url = f"https://cafe.naver.com/{cafe_id}"
            cafe_info.collected_datetime = post.collected_datetime
            cafe_info.pm_posts_collected = 1
            
            self.cafe_infos[cafe_id] = cafe_info
        else:
            # 기존 카페 정보 업데이트
            cafe_info = self.cafe_infos[cafe_id]
            cafe_info.pm_posts_collected += 1
            if not cafe_info.cafe_name and post.cafe_name:
                cafe_info.cafe_name = post.cafe_name
        
        # v2.3: sponsor 정보가 있는 카페 추적 (2차 수집용)
        if post.sponsor_phone or post.sponsor_partner_id:
            if cafe_id not in self.sponsor_cafes:
                self.sponsor_cafes[cafe_id] = {
                    'cafe_name': post.cafe_name,
                    'cafe_url': f"https://cafe.naver.com/{cafe_id}",
                    'post_count': 1,
                    'phones': set(),
                    'partner_ids': set()
                }
            else:
                self.sponsor_cafes[cafe_id]['post_count'] += 1
            
            if post.sponsor_phone:
                self.sponsor_cafes[cafe_id]['phones'].add(post.sponsor_phone)
            if post.sponsor_partner_id:
                self.sponsor_cafes[cafe_id]['partner_ids'].add(post.sponsor_partner_id)
    
    def fetch_cafe_intro(self, cafe_id: str) -> bool:
        """
        카페소개 페이지에서 카페 정보 수집 (v2.3 신규)
        각 cafe_id당 한 번만 방문
        """
        # 이미 상세 정보가 있으면 스킵
        if cafe_id in self.cafe_infos and self.cafe_infos[cafe_id].established_date:
            return True
        
        try:
            cafe_url = f"https://cafe.naver.com/{cafe_id}"
            self.driver.get(cafe_url)
            time.sleep(2)
            
            # iframe으로 전환
            try:
                self.driver.switch_to.frame('cafe_main')
            except:
                pass
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 카페 정보 객체 가져오기/생성
            if cafe_id not in self.cafe_infos:
                cafe_info = CafeInfo()
                cafe_info.cafe_id = cafe_id
                cafe_info.cafe_url = cafe_url
                cafe_info.collected_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.cafe_infos[cafe_id] = cafe_info
            else:
                cafe_info = self.cafe_infos[cafe_id]
            
            # 카페 이름
            name_selectors = ['.cafe_name', '.cafe-title', 'h1.tit_cafe', '.cafe_info_tit']
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    cafe_info.cafe_name = elem.get_text(strip=True)
                    break
            
            # 멤버 수
            member_selectors = ['.mem_cnt', '.member_cnt', 'em.num']
            for selector in member_selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text()
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        cafe_info.member_count = int(match.group(1).replace(',', ''))
                        break
            
            # 카페 설명/주제
            desc_selectors = ['.cafe_intro_txt', '.cafe_desc', '.intro_txt']
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    cafe_info.cafe_description = elem.get_text(strip=True)[:500]
                    break
            
            # 설립일
            date_patterns = [
                r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})',  # YYYY-MM-DD
                r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일'   # YYYY년 MM월 DD일
            ]
            page_text = soup.get_text()
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    cafe_info.established_date = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    break
            
            self.driver.switch_to.default_content()
            logger.debug(f"  → 카페 정보 수집: {cafe_id} ({cafe_info.cafe_name})")
            return True
            
        except Exception as e:
            logger.debug(f"카페 정보 수집 실패 ({cafe_id}): {e}")
            self.driver.switch_to.default_content()
            return False
    
    def save_checkpoint(self):
        """체크포인트 저장"""
        if not self.posts:
            return
        
        output_config = self.config.get('output', {})
        data_dir = output_config.get('data_dir', 'data')
        Path(data_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        encoding = output_config.get('csv_encoding', 'utf-8-sig')
        
        # 게시물 저장
        posts_df = pd.DataFrame([asdict(p) for p in self.posts])
        posts_path = f"{data_dir}/checkpoint_posts_{timestamp}.csv"
        posts_df.to_csv(posts_path, index=False, encoding=encoding)
        
        # 카페 정보 저장
        if self.cafe_infos:
            cafe_df = pd.DataFrame([asdict(c) for c in self.cafe_infos.values()])
            cafe_path = f"{data_dir}/checkpoint_cafe_info_{timestamp}.csv"
            cafe_df.to_csv(cafe_path, index=False, encoding=encoding)
        
        logger.info(f"💾 체크포인트 저장: {len(self.posts)}개 게시물, {len(self.cafe_infos)}개 카페")
    
    def save_final_results(self):
        """최종 결과 저장 (v2.4: 경로/파일명 변경, 카페정보 제거)"""
        if not self.posts:
            logger.warning("⚠️ 저장할 데이터가 없습니다")
            return
        
        output_config = self.config.get('output', {})
        # v2.4: data_posts 폴더에 저장
        data_dir = 'data_posts'
        Path(data_dir).mkdir(exist_ok=True)
        
        # v2.4: YYMMDD_HHMMSS 형식 (연도 앞 20 생략)
        test_mode = self.config.get('execution_mode', {}).get('test_mode', True)
        mode_str = 'test' if test_mode else 'final'
        timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
        encoding = output_config.get('csv_encoding', 'utf-8-sig')
        
        # 게시물 저장
        posts_df = pd.DataFrame([asdict(p) for p in self.posts])
        posts_filename = f"{data_dir}/naver_cafe_posts_v2_5_{mode_str}_{timestamp}.csv"
        posts_df.to_csv(posts_filename, index=False, encoding=encoding)
        logger.info(f"💾 게시물 저장: {posts_filename} ({len(self.posts)}개)")
        
        # v2.4: sponsor CSV 제거 (전화번호는 게시물 본문에서 추출되므로 중복)
        # sponsor_phone, sponsor_partner_id 컬럼이 posts CSV에 이미 포함됨
        
        # 종료 시간 기록
        self.end_datetime = datetime.now()
        
        # 통계 리포트
        self.generate_report(timestamp, mode_str)
    
    def generate_report(self, timestamp: str, mode_str: str = 'test'):
        """실행 리포트 생성 (v2.5)"""
        # v2.5: data_posts 폴더 사용
        data_dir = 'data_posts'
        
        elapsed = self.time_manager.get_elapsed_minutes()
        start_str = self.start_datetime.strftime('%Y-%m-%d %H:%M:%S')
        end_str = self.end_datetime.strftime('%Y-%m-%d %H:%M:%S') if self.end_datetime else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report_lines = [
            "=" * 80,
            "📊 PM-International 네이버 카페 크롤러 v2.5 결과 보고서",
            f"   실행 ID: {timestamp}",
            "=" * 80,
            "",
            "⏱️  실행 시간",
            "-" * 80,
            f"• 시작 시간: {start_str}",
            f"• 종료 시간: {end_str}",
            f"• 총 실행 시간: {elapsed:.1f}분",
            f"• 테스트 모드: {self.config.get('execution_mode', {}).get('test_mode', True)}",
            "",
            "📈 수집 성과",
            "-" * 80,
            f"• 총 수집 게시물: {len(self.posts)}개",
            f"• 수집된 카페 수: {len(self.cafe_infos)}개",
            f"• Sponsor 정보 있는 카페: {len(self.sponsor_cafes)}개",
            f"• 수집 속도: {len(self.posts) / max(elapsed, 0.1):.1f}개/분",
            "",
            "✅ 처리 통계",
            "-" * 80,
            f"• 총 시도: {self.stats.total_attempts}",
            f"• ✅ 성공: {self.stats.success}",
            f"• 🔍 필터링: {self.stats.filtered}",
            f"• 🔄 중복: {self.stats.duplicates}",
            f"• 🔒 비공개 스킵: {self.stats.skipped_private}",
            f"• ❌ 에러: {self.stats.errors}",
            "",
            "🎯 PM 데이터 추출",
            "-" * 80,
        ]
        
        if self.posts:
            posts_df = pd.DataFrame([asdict(p) for p in self.posts])
            phone_rate = (posts_df['sponsor_phone'] != '').sum() / len(posts_df) * 100
            partner_rate = (posts_df['sponsor_partner_id'] != '').sum() / len(posts_df) * 100
            image_rate = (posts_df['image_urls'] != '').sum() / len(posts_df) * 100
            video_rate = (posts_df['video_urls'] != '').sum() / len(posts_df) * 100
            
            report_lines.extend([
                f"• 전화번호 수집률: {phone_rate:.1f}%",
                f"• 후원번호 수집률: {partner_rate:.1f}%",
                f"• 이미지 URL 수집률: {image_rate:.1f}%",
                f"• 영상 URL 수집률: {video_rate:.1f}%",
            ])
        
        # v2.3: Sponsor 카페 목록
        if self.sponsor_cafes:
            report_lines.extend([
                "",
                "📞 Sponsor 정보 있는 카페 (2차 수집 대상)",
                "-" * 80,
            ])
            for cafe_id, info in list(self.sponsor_cafes.items())[:10]:
                report_lines.append(f"• {info['cafe_name']} ({cafe_id}): {info['post_count']}개 게시물")
        
        # 버그/에러 로그 추가
        if self.error_logs:
            report_lines.extend([
                "",
                "⚠️ 버그/에러 로그",
                "-" * 80,
            ])
            for error in self.error_logs[-10:]:
                report_lines.append(f"• {error}")
        
        report_lines.extend([
            "",
            "=" * 80,
        ])
        
        report_path = f"{data_dir}/naver_cafe_report_v2_5_{mode_str}_{timestamp}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"📝 리포트 저장: {report_path}")
        
        # 콘솔 출력
        print('\n'.join(report_lines))
    
    def signal_handler(self, signum, frame):
        """종료 신호 처리"""
        logger.info("\n🔔 종료 신호 감지! 데이터 저장 중...")
        self.should_stop = True
        self.save_final_results()
        sys.exit(0)
    
    def run(self):
        """메인 실행"""
        # 종료 신호 핸들러 설정
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("=" * 80)
        logger.info("🚀 PM-International 네이버 카페 크롤러 v2.3 (공개 게시판 전용)")
        logger.info("=" * 80)
        
        test_mode = self.config.get('execution_mode', {})
        logger.info(f"⏰ 최대 실행 시간: {test_mode.get('max_duration_minutes', 60)}분")
        logger.info(f"📝 카페당 최대 수집: {self.max_posts}개")
        logger.info("⚠️ 공개 게시판만 수집합니다 (로그인 필요 게시판 제외)")
        logger.info("")
        
        try:
            self.setup_driver()
            
            # 키워드 목록 구성
            keywords_config = self.config.get('keywords', {})
            all_keywords = []
            all_keywords.extend(keywords_config.get('primary', []))
            all_keywords.extend(keywords_config.get('secondary', []))
            
            total_collected = 0
            
            for kw_info in all_keywords:
                if self.should_stop or self.time_manager.is_time_exceeded():
                    logger.info("⏰ 시간 초과 또는 종료 요청")
                    break
                
                keyword = kw_info.get('keyword', '')
                target = kw_info.get('target', 30)
                
                logger.info(f"\n🔍 키워드 검색 시작: '{keyword}' (목표: {target}개)")
                
                # 네이버 검색으로 URL 수집
                search_results = self.search_cafe_posts_via_naver(keyword, max_results=target * 2)
                
                collected_for_keyword = 0
                
                for result in search_results:
                    if self.should_stop or self.time_manager.is_time_exceeded():
                        break
                    
                    if collected_for_keyword >= target:
                        break
                    
                    if total_collected >= self.max_posts:
                        logger.info(f"📊 최대 수집량 도달: {self.max_posts}개")
                        break
                    
                    url = result['url']
                    self.stats.total_attempts += 1
                    
                    # 중복 체크
                    if self.duplicate_checker.is_duplicate(url=url):
                        self.stats.duplicates += 1
                        continue
                    
                    # 공개 접근성 체크
                    if not self.is_public_accessible(url):
                        self.stats.skipped_private += 1
                        logger.debug(f"🔒 비공개 스킵: {url}")
                        continue
                    
                    # 데이터 추출
                    post = self.extract_post_data(url, keyword)
                    
                    if not post or not post.title:
                        self.stats.errors += 1
                        continue
                    
                    # 필터링 체크
                    should_filter, reason = self.extractor.should_filter(post.title, post.content)
                    if should_filter:
                        self.stats.filtered += 1
                        logger.debug(f"🔍 필터링: {reason}")
                        continue
                    
                    # 저장
                    self.posts.append(post)
                    self.update_cafe_info(post)
                    
                    # 중복 체커에 추가 (cafe_id + article_id 조합으로 고유 식별)
                    post_unique_id = f"{post.cafe_id}_{post.article_id}" if post.cafe_id and post.article_id else url
                    self.duplicate_checker.add(
                        post_id=post_unique_id,
                        url=url,
                        title=post.title,
                        content=post.content
                    )
                    
                    self.stats.success += 1
                    collected_for_keyword += 1
                    total_collected += 1
                    
                    logger.info(f"✅ [{total_collected}] {post.title[:40]}...")
                    
                    # 체크포인트 확인
                    if self.time_manager.should_checkpoint(self.checkpoint_interval):
                        self.save_checkpoint()
                
                logger.info(f"📊 '{keyword}' 완료: {collected_for_keyword}/{target}개 수집")
                
                # 남은 시간 표시
                remaining = self.time_manager.get_remaining_minutes()
                logger.info(f"⏰ 남은 시간: {remaining:.1f}분")
            
        except Exception as e:
            logger.error(f"❌ 크롤링 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            # v2.4: 카페소개 수집 제거 (posts만 수집)
            # 최종 저장
            self.save_final_results()
            
            # 통계 출력
            self.stats.print_stats(self.time_manager.get_elapsed_minutes())
            
            # 드라이버 종료
            if self.driver:
                self.driver.quit()
                logger.info("🔚 드라이버 종료 완료")

# =============================================================================
# 메인 실행
# =============================================================================

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PM-International 네이버 카페 크롤러 v2.4')
    parser.add_argument('--config', type=str, default='config_cafe.yaml',
                        help='설정 파일 경로')
    parser.add_argument('--duration', type=int, default=None,
                        help='실행 시간 (분) - 설정 파일 값 오버라이드')
    parser.add_argument('--max-posts', type=int, default=None,
                        help='최대 수집 게시물 수 - 설정 파일 값 오버라이드')
    
    args = parser.parse_args()
    
    # 설정 로드
    config = load_config(args.config)
    
    # 명령줄 인자로 오버라이드
    if args.duration:
        config['execution_mode']['max_duration_minutes'] = args.duration
    if args.max_posts:
        config['execution_mode']['max_posts_per_cafe'] = args.max_posts
    
    # 크롤러 실행
    crawler = NaverCafePublicCrawler(config)
    crawler.run()

if __name__ == "__main__":
    main()
