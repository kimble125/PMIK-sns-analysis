#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PM-International Korea PM 전용 카페 크롤러 v1.4 (Test 버전)

🎯 목적:
PM 사업자 전용 카페를 발굴하고, 해당 카페의 게시물 + 카페소개 정보를 수집

🔒 주요 기능:
1. 📍 PM 전용 카페 발굴 - 카페명에 PM 키워드가 있는 카페 검색
2. 📄 카페소개 수집 - iframe 처리로 정확한 카페 정보 추출
3. 📝 공개 게시물 전체 수집 - 카페당 최대 500개
4. 🔄 카페 순환 - 한 카페에서 과도한 수집 방지
5. 🛡️ 중복 제거 - Track 1 (기존 크롤러)과 중복 방지

📊 출력 테이블:
- naver_cafe_pm_info_v1_4_*.csv: PM 전용 카페 목록 + 카페소개 정보
- naver_cafe_pm_posts_v1_4_*.csv: 해당 카페들의 공개 게시물

⚠️ 법적 고지:
- 본 크롤러는 공개된 정보만 수집합니다
- 로그인이 필요한 카페/게시판은 수집하지 않습니다
- robots.txt 및 네이버 이용약관을 준수합니다

작성자: PMI Korea 데이터 분석팀
버전: 1.4.0 (Test)
최종 수정일: 2025-12-01

v1.4 수정사항 (2025-12-01):
- 파일명 변경: targeting → pm (카페 수집 목적 명확화)
- PM 카페 게시물 전체 수집 (필터링 제거)
- is_pm_keyword 컴럼 추가 (PM 키워드 포함 여부 태깅)
- cafe_type 컴럼 추가 (pm_exclusive)
- max_posts_per_cafe: 100 → 500
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
from dataclasses import dataclass, asdict, field
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
    """기본 설정 반환"""
    return {
        'execution_mode': {
            'test_mode': True,
            'max_duration_minutes': 60,
            'checkpoint_interval_minutes': 10
        },
        'targeting': {
            'cafe_search_keywords': [
                '피엠인터내셔널', '독일피엠', 'PM인터내셔널', '피트라인',
                '피엠코리아', 'PM코리아', '핏라인'
            ],
            'max_cafes_per_keyword': 20,
            'max_posts_per_cafe': 30,
            'cool_down_between_cafes': 5,
            'revisit_interval_hours': 24
        },
        'crawling': {
            'page_load_timeout': 15,
            'request_delay_min': 2.0,
            'request_delay_max': 4.0,
            'max_retries': 3,
            'headless': True,
            'scroll_wait_seconds': 2,
            'dynamic_load_timeout': 10
        },
        'filters': {
            'pm_brand_keywords': [
                '피엠인터내셔널', 'PM인터내셔널', 'PM International', 'PMInternational',
                'PMIK', '독일PM', '독일피엠', 'FitLine', '핏라인', '피트라인', '피엠코리아'
            ],
            'product_keywords': [
                '피트라인', '엑티바이즈', 'Activize', '뮤노겐', 'Munogen',
                '파워칵테일', 'PowerCocktail', '레스토레이트', 'Restorate'
            ]
        },
        'user_agents': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
    """로깅 설정 (v1.4: 강제 파일 핸들러 추가)"""
    log_dir = CONFIG.get('logging', {}).get('log_dir', 'logs')
    Path(log_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"{log_dir}/cafe_pm_{timestamp}.log"
    
    # 로거 가져오기 (모듈별 독립 로거)
    logger = logging.getLogger('naver_cafe_pm_v1_4')
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
class PMCafe:
    """PM 전용 카페 데이터 클래스 (카페소개 페이지에서 수집)"""
    cafe_id: str = ""                # 카페 URL ID (예: ondalprince)
    cafe_name: str = ""              # 카페 이름
    cafe_url: str = ""               # 카페 URL
    
    # 카페소개 정보 (이미지 참고)
    established_date: str = ""       # 카페 설립일 (Since 2012.10.22)
    cafe_topic: str = ""             # 주제 (건강/다이어트 > 건강관리/건강식품)
    cafe_description: str = ""       # 카페 설명
    cafe_keywords: str = ""          # 카페 검색어
    cafe_character: str = ""         # 카페 성격 (공개/비공개)
    join_method: str = ""            # 가입 방식
    
    # 운영진 정보 (v1.1 추가)
    cafe_manager: str = ""           # 카페 매니저
    cafe_staff: str = ""             # 카페 스탭
    
    # 통계 정보
    member_count: int = 0            # 카페멤버 수
    total_posts: int = 0             # 전체 게시글 수
    total_visitors: int = 0          # 총 방문자 수
    cafe_ranking: str = ""           # 카페 랭킹 (가지5단계)
    app_downloads: int = 0           # 앱 추가수 (v1.1 추가)
    
    # 검색 결과 정보
    search_keyword: str = ""         # 이 카페를 찾은 검색 키워드
    is_accessible: bool = True       # 공개 접근 가능 여부
    
    # 메타 필드
    collected_datetime: str = ""
    posts_collected: int = 0         # 이 카페에서 수집된 게시물 수

@dataclass
class CafePost:
    """게시물 데이터 클래스 (v1.4: cafe_type, is_pm_keyword 추가)"""
    platform: str = "naver_cafe"
    cafe_id: str = ""
    cafe_name: str = ""
    article_id: str = ""
    url: str = ""
    title: str = ""
    content: str = ""
    author_nickname: str = ""
    published_datetime: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    
    # PM 특화 필드
    sponsor_phone: str = ""
    sponsor_partner_id: str = ""
    hashtags: str = ""
    
    # 미디어 URL
    image_urls: str = ""
    video_urls: str = ""
    
    # 메타 필드
    collected_datetime: str = ""
    is_public: bool = True
    
    # v1.4 신규 필드
    cafe_type: str = "pm_exclusive"      # PM 전용 카페
    is_pm_keyword: bool = True           # PM 키워드 포함 여부

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
        return (time.time() - self.start_time) >= self.max_duration_seconds
    
    def get_elapsed_minutes(self) -> float:
        return (time.time() - self.start_time) / 60
    
    def get_remaining_minutes(self) -> float:
        remaining = self.max_duration_seconds - (time.time() - self.start_time)
        return max(0, remaining / 60)
    
    def should_checkpoint(self, interval_minutes: int) -> bool:
        if (time.time() - self.last_checkpoint) >= (interval_minutes * 60):
            self.last_checkpoint = time.time()
            return True
        return False

class DuplicateChecker:
    """중복 체커 클래스"""
    
    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_cafe_ids: Set[str] = set()
    
    def is_url_duplicate(self, url: str) -> bool:
        normalized = self._normalize_url(url)
        return normalized in self.seen_urls
    
    def add_url(self, url: str):
        normalized = self._normalize_url(url)
        self.seen_urls.add(normalized)
    
    def is_cafe_duplicate(self, cafe_id: str) -> bool:
        return cafe_id in self.seen_cafe_ids
    
    def add_cafe(self, cafe_id: str):
        self.seen_cafe_ids.add(cafe_id)
    
    def _normalize_url(self, url: str) -> str:
        """URL 정규화 - 쿼리 파라미터 제거"""
        parsed = urlparse(url)
        # cafe_id와 article_id만 추출
        match = re.search(r'cafe\.naver\.com/([^/\?]+)/(\d+)', url)
        if match:
            return f"{match.group(1)}_{match.group(2)}"
        return url
    
    def load_existing_urls(self, csv_path: str):
        """기존 CSV에서 URL 로드 (Track 1과 중복 방지)"""
        try:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                if 'url' in df.columns:
                    for url in df['url'].dropna():
                        self.add_url(url)
                    logger.info(f"  → 기존 URL {len(self.seen_urls)}개 로드됨")
        except Exception as e:
            logger.warning(f"기존 URL 로드 실패: {e}")

class CrawlStats:
    """크롤링 통계 클래스"""
    
    def __init__(self):
        self.cafes_found = 0
        self.cafes_accessible = 0
        self.cafes_private = 0
        self.posts_collected = 0
        self.posts_skipped_duplicate = 0
        self.posts_skipped_private = 0
        self.posts_skipped_no_keyword = 0  # v1.2: 키워드 없는 게시물 스킵
        self.errors = 0
    
    def print_stats(self, elapsed_minutes: float):
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 크롤링 통계")
        logger.info("=" * 60)
        logger.info(f"⏰ 실행 시간: {elapsed_minutes:.1f}분")
        logger.info(f"🏠 발견된 카페: {self.cafes_found}")
        logger.info(f"  ✅ 접근 가능: {self.cafes_accessible}")
        logger.info(f"  🔒 비공개: {self.cafes_private}")
        logger.info(f"📝 수집된 게시물: {self.posts_collected}")
        logger.info(f"  🔄 중복 스킵: {self.posts_skipped_duplicate}")
        logger.info(f"  🔒 비공개 스킵: {self.posts_skipped_private}")
        logger.info(f"  🔍 키워드 없음 스킵: {self.posts_skipped_no_keyword}")  # v1.2
        logger.info(f"❌ 에러: {self.errors}")
        logger.info("=" * 60)

# =============================================================================
# 메인 크롤러 클래스
# =============================================================================

class PMCafeTargetingCrawler:
    """PM 전용 카페 타겟팅 크롤러"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.driver = None
        
        # 데이터 저장
        self.pm_cafes: List[PMCafe] = []
        self.posts: List[CafePost] = []
        
        # 유틸리티
        exec_config = config.get('execution_mode', {})
        self.time_manager = TimeManager(exec_config.get('max_duration_minutes', 60))
        self.duplicate_checker = DuplicateChecker()
        self.stats = CrawlStats()
        
        # 설정
        targeting_config = config.get('targeting', {})
        self.max_posts_per_cafe = targeting_config.get('max_posts_per_cafe', 30)
        self.cool_down = targeting_config.get('cool_down_between_cafes', 5)
        
        # 시간 기록
        self.start_datetime = datetime.now()
        self.end_datetime = None
        
        # 에러 로그
        self.error_logs: List[str] = []
        
        # v1.2: 키워드 필터링용 리스트
        self.filter_keywords = self._load_filter_keywords()
    
    def _load_filter_keywords(self) -> List[str]:
        """config_cafe.yaml에서 필터링 키워드 로드"""
        keywords = []
        filters = self.config.get('filters', {})
        
        # PM 브랜드 키워드
        keywords.extend(filters.get('pm_brand_keywords', []))
        # 제품 키워드
        keywords.extend(filters.get('product_keywords', []))
        # 판매원 관련 키워드
        keywords.extend(filters.get('sales_keywords', []))
        
        # 중복 제거 및 소문자 변환 (대소문자 무시 매칭용)
        unique_keywords = list(set(keywords))
        logger.info(f"  → 필터링 키워드 {len(unique_keywords)}개 로드됨")
        return unique_keywords
    
    def _contains_pm_keyword(self, text: str) -> bool:
        """텍스트에 PM 관련 키워드가 포함되어 있는지 확인"""
        if not text:
            return False
        text_lower = text.lower()
        for keyword in self.filter_keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def setup_driver(self):
        """Selenium WebDriver 설정"""
        crawl_config = self.config.get('crawling', {})
        
        options = Options()
        if crawl_config.get('headless', True):
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        user_agents = self.config.get('user_agents', [])
        if user_agents:
            options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(crawl_config.get('page_load_timeout', 15))
        
        logger.info("✅ Chrome 드라이버 초기화 완료")
    
    def random_delay(self, min_delay: float = None, max_delay: float = None):
        """랜덤 딜레이"""
        crawl_config = self.config.get('crawling', {})
        min_d = min_delay or crawl_config.get('request_delay_min', 2.0)
        max_d = max_delay or crawl_config.get('request_delay_max', 4.0)
        time.sleep(random.uniform(min_d, max_d))
    
    # =========================================================================
    # 카페 검색 및 목록 수집
    # =========================================================================
    
    def search_pm_cafes(self, keyword: str) -> List[Dict]:
        """네이버 카페 홈에서 PM 관련 카페 검색"""
        cafes = []
        
        # 카페 검색 URL (이미지에서 확인한 구조)
        search_url = f"https://section.cafe.naver.com/ca-fe/home/search/cafes?q={quote(keyword)}"
        
        logger.info(f"🔍 카페 검색: '{keyword}'")
        
        try:
            self.driver.get(search_url)
            self.random_delay(2, 4)
            
            # 동적 로딩 대기
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.cafe_list, .CafeList, .cafe_item'))
                )
            except TimeoutException:
                logger.warning(f"  → 카페 목록 로딩 타임아웃")
            
            # 스크롤하여 더 많은 결과 로드
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 카페 목록 추출 (여러 셀렉터 시도)
            cafe_items = soup.select('.cafe_list .cafe_item, .CafeList .CafeItem, .cafe_info, [class*="CafeItem"]')
            
            if not cafe_items:
                # 대안 셀렉터
                cafe_items = soup.select('a[href*="cafe.naver.com"]')
            
            for item in cafe_items:
                try:
                    # 카페 URL 추출
                    cafe_link = item.select_one('a[href*="cafe.naver.com"]')
                    if not cafe_link:
                        cafe_link = item if item.name == 'a' else None
                    
                    if not cafe_link:
                        continue
                    
                    href = cafe_link.get('href', '')
                    match = re.search(r'cafe\.naver\.com/([^/\?\s]+)', href)
                    if not match:
                        continue
                    
                    cafe_id = match.group(1)
                    
                    # 중복 체크
                    if self.duplicate_checker.is_cafe_duplicate(cafe_id):
                        continue
                    
                    # 카페 이름 추출
                    cafe_name = ""
                    name_elem = item.select_one('.cafe_name, .name, .tit, [class*="name"]')
                    if name_elem:
                        cafe_name = name_elem.get_text(strip=True)
                    elif cafe_link:
                        cafe_name = cafe_link.get_text(strip=True)
                    
                    # 멤버 수 추출
                    member_count = 0
                    member_elem = item.select_one('.member_count, .member, [class*="member"]')
                    if member_elem:
                        member_text = member_elem.get_text(strip=True)
                        member_match = re.search(r'[\d,]+', member_text)
                        if member_match:
                            member_count = int(member_match.group().replace(',', ''))
                    
                    cafes.append({
                        'cafe_id': cafe_id,
                        'cafe_name': cafe_name,
                        'cafe_url': f"https://cafe.naver.com/{cafe_id}",
                        'member_count': member_count,
                        'search_keyword': keyword
                    })
                    
                    self.duplicate_checker.add_cafe(cafe_id)
                    
                except Exception as e:
                    continue
            
            logger.info(f"  → {len(cafes)}개 카페 발견")
            
        except Exception as e:
            logger.error(f"카페 검색 오류: {e}")
            self.error_logs.append(f"카페 검색 오류 ({keyword}): {e}")
        
        return cafes
    
    # =========================================================================
    # 카페소개 페이지 수집 (개선된 버전)
    # =========================================================================
    
    def fetch_cafe_intro(self, cafe_id: str) -> Optional[PMCafe]:
        """카페소개 페이지에서 상세 정보 수집 (iframe 처리)"""
        
        cafe = PMCafe(
            cafe_id=cafe_id,
            cafe_url=f"https://cafe.naver.com/{cafe_id}",
            collected_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        try:
            # 1. 먼저 카페 메인 페이지 접근
            self.driver.get(f"https://cafe.naver.com/{cafe_id}")
            self.random_delay(2, 3)
            
            # 접근 가능 여부 확인
            if self._check_login_required():
                cafe.is_accessible = False
                logger.info(f"  → 🔒 {cafe_id}: 로그인 필요 (스킵)")
                return cafe
            
            # 2. 카페소개 페이지로 이동 (여러 방법 시도)
            intro_url = f"https://cafe.naver.com/CafeProfileView.nhn?clubid=0&cluburl={cafe_id}"
            # 대안 URL
            intro_urls = [
                f"https://cafe.naver.com/{cafe_id}?iframe_url=/CafeProfileView.nhn%3Fcluburl={cafe_id}",
                f"https://cafe.naver.com/CafeProfileView.nhn?cluburl={cafe_id}"
            ]
            
            # 카페소개 링크 찾기
            try:
                intro_link = self.driver.find_element(By.CSS_SELECTOR, 'a[href*="CafeProfileView"], a.link_cafe_intro, a[href*="카페소개"]')
                intro_link.click()
                self.random_delay(2, 3)
            except:
                # 직접 URL로 시도
                self.driver.get(intro_urls[0])
                self.random_delay(2, 3)
            
            # 3. iframe 처리 - 카페소개는 iframe 내부에 있을 수 있음
            try:
                # cafe_main iframe으로 전환
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                for iframe in iframes:
                    iframe_id = iframe.get_attribute('id') or ''
                    iframe_name = iframe.get_attribute('name') or ''
                    if 'cafe_main' in iframe_id or 'cafe_main' in iframe_name:
                        self.driver.switch_to.frame(iframe)
                        break
            except:
                pass
            
            # 동적 로딩 대기
            time.sleep(2)
            
            # 4. 페이지 소스 파싱
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 5. 카페 정보 추출 (이미지에서 확인한 구조)
            self._extract_cafe_info_from_soup(soup, cafe)
            
            # iframe에서 빠져나오기
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            if cafe.cafe_name:
                logger.info(f"  → ✅ {cafe_id}: {cafe.cafe_name} (멤버 {cafe.member_count:,}명)")
            
        except Exception as e:
            logger.error(f"카페소개 수집 오류 ({cafe_id}): {e}")
            self.error_logs.append(f"카페소개 오류 ({cafe_id}): {e}")
            
            try:
                self.driver.switch_to.default_content()
            except:
                pass
        
        return cafe
    
    def _extract_cafe_info_from_soup(self, soup: BeautifulSoup, cafe: PMCafe):
        """BeautifulSoup에서 카페 정보 추출 (이미지 구조 참고)"""
        
        # 카페 이름 - 여러 셀렉터 시도
        name_selectors = [
            '.cafe_name', '.tit_cafe', 'h2.cafe_name', '.cafe_title',
            'strong.tit', '.CafeName', '[class*="cafeName"]',
            'h1', 'h2'
        ]
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text(strip=True):
                text = elem.get_text(strip=True)
                if len(text) > 2 and len(text) < 100:
                    cafe.cafe_name = text
                    break
        
        # 테이블 형태 데이터 추출 (이미지에서 확인: 카페 설립일, 주제, 카페 활동 등)
        # dt/dd 패턴 또는 th/td 패턴
        
        # 방법 1: dt/dd 형태
        dts = soup.select('dt, .tit, .info_tit')
        dds = soup.select('dd, .txt, .info_txt')
        
        for i, dt in enumerate(dts):
            label = dt.get_text(strip=True)
            
            # 다음 dd 찾기
            dd = dt.find_next('dd') if dt.name == 'dt' else None
            if not dd and i < len(dds):
                dd = dds[i] if i < len(dds) else None
            
            if not dd:
                continue
            
            value = dd.get_text(strip=True)
            self._map_cafe_field(cafe, label, value)
        
        # 방법 2: 테이블 행 형태
        rows = soup.select('tr, .info_row, .row')
        for row in rows:
            cells = row.select('th, td, .cell')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                self._map_cafe_field(cafe, label, value)
        
        # 방법 3: 특정 클래스에서 직접 추출
        # 카페 활동 정보 (멤버수, 게시글, 방문자)
        activity_elem = soup.select_one('.cafe_activity, .activity, [class*="activity"]')
        if activity_elem:
            activity_text = activity_elem.get_text()
            
            # 멤버 수
            member_match = re.search(r'(?:카페멤버|멤버)[:\s]*([0-9,]+)', activity_text)
            if member_match:
                cafe.member_count = int(member_match.group(1).replace(',', ''))
            
            # 전체 게시글
            posts_match = re.search(r'(?:전체\s*게시[글물]|게시글)[:\s]*([0-9,]+)', activity_text)
            if posts_match:
                cafe.total_posts = int(posts_match.group(1).replace(',', ''))
            
            # 총 방문자
            visitors_match = re.search(r'(?:총\s*방문자|방문자)[:\s]*([0-9,]+)', activity_text)
            if visitors_match:
                cafe.total_visitors = int(visitors_match.group(1).replace(',', ''))
        
        # 전체 페이지에서 패턴 매칭으로 추출 (백업)
        full_text = soup.get_text()
        
        if cafe.member_count == 0:
            member_match = re.search(r'(?:카페멤버|멤버)\s*[:\s]\s*([0-9,]+)\s*명', full_text)
            if member_match:
                cafe.member_count = int(member_match.group(1).replace(',', ''))
        
        if cafe.total_posts == 0:
            posts_match = re.search(r'(?:전체\s*게시[글물]|게시글)\s*[:\s]\s*([0-9,]+)\s*개', full_text)
            if posts_match:
                cafe.total_posts = int(posts_match.group(1).replace(',', ''))
        
        if cafe.total_visitors == 0:
            visitors_match = re.search(r'(?:총\s*방문자)\s*[:\s]\s*([0-9,]+)\s*명', full_text)
            if visitors_match:
                cafe.total_visitors = int(visitors_match.group(1).replace(',', ''))
        
        if not cafe.established_date:
            date_match = re.search(r'Since\s*(\d{4}\.\d{2}\.\d{2})', full_text)
            if date_match:
                cafe.established_date = date_match.group(1)
        
        if not cafe.cafe_ranking:
            ranking_match = re.search(r'(가지\d단계|씨앗\d단계|새싹\d단계|나무\d단계)', full_text)
            if ranking_match:
                cafe.cafe_ranking = ranking_match.group(1)
        
        # 추가 수정: 앱 추가수 추출 (p.txt 셀렉터)
        # HTML 예시: <p class="txt"><strong>우리 카페 바로가기 앱 추가수</strong>...1회</p>
        if cafe.app_downloads == 0:
            for p_elem in soup.select('p.txt'):
                p_text = p_elem.get_text()
                if '앱 추가수' in p_text:
                    app_match = re.search(r'(\d+)\s*회', p_text)
                    if app_match:
                        cafe.app_downloads = int(app_match.group(1))
                        break
    
    def _map_cafe_field(self, cafe: PMCafe, label: str, value: str):
        """레이블에 따라 카페 필드 매핑 (v1.1 개선)"""
        label = label.strip()
        value = value.strip()
        
        if '카페 이름' in label or '카페명' in label:
            cafe.cafe_name = value
        elif '카페 설립' in label or '설립일' in label:
            # v1.1: ".카페연혁보기" 등 불필요한 텍스트 제거
            clean_date = value.replace('Since', '').strip()
            date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', clean_date)
            cafe.established_date = date_match.group(1) if date_match else clean_date
        elif '주제' in label:
            cafe.cafe_topic = value
        elif '카페 설명' in label or '설명' in label:
            cafe.cafe_description = value[:500]  # 최대 500자
        elif '카페 검색어' in label or '검색어' in label:
            cafe.cafe_keywords = value
        elif '카페 성격' in label or '성격' in label:
            cafe.cafe_character = value
        elif '가입 방식' in label or '가입' in label:
            cafe.join_method = value
        elif '매니저' in label:
            cafe.cafe_manager = value
        elif '스탭' in label or '스태프' in label:
            cafe.cafe_staff = value
        elif '앱 추가' in label or '바로가기' in label:
            # v1.1: 앱 추가수 추출
            app_match = re.search(r'([0-9,]+)', value)
            if app_match:
                cafe.app_downloads = int(app_match.group(1).replace(',', ''))
        elif '카페 활동' in label or '활동' in label:
            # 카페멤버 : 5,192명   전체 게시물 : 1,475개   총 방문자 : 36,747명
            member_match = re.search(r'([0-9,]+)\s*명', value)
            if member_match:
                cafe.member_count = int(member_match.group(1).replace(',', ''))
            posts_match = re.search(r'게시[글물]\s*[:\s]*([0-9,]+)', value)
            if posts_match:
                cafe.total_posts = int(posts_match.group(1).replace(',', ''))
            visitors_match = re.search(r'방문자\s*[:\s]*([0-9,]+)', value)
            if visitors_match:
                cafe.total_visitors = int(visitors_match.group(1).replace(',', ''))
        elif '카페 랭킹' in label or '랭킹' in label:
            # v1.1: "현재랭킹 :" 등 불필요한 텍스트 제거
            ranking_match = re.search(r'(가지\d단계|씨앗\d단계|새싹\d단계|나무\d단계)', value)
            cafe.cafe_ranking = ranking_match.group(1) if ranking_match else value
    
    def _check_login_required(self) -> bool:
        """로그인 필요 여부 확인 (개선됨)"""
        try:
            page_source = self.driver.page_source.lower()
            
            # 명확한 차단 메시지만 확인
            block_indicators = [
                '멤버만 이용할 수 있습니다',
                '카페 멤버만 볼 수 있습니다',
                '비공개 카페입니다',
                '카페 가입 후 이용',
                'login required'
            ]
            
            for indicator in block_indicators:
                if indicator in page_source:
                    return True
            
            # 게시물 목록이나 본문이 있으면 공개
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 게시물 목록 확인
            article_list = soup.select('a.article, .article-board, .board-list, .article_wrap')
            if article_list:
                return False
            
            # 본문 내용 확인
            content = soup.select('.article_viewer, .content, .se-main-container')
            if content:
                return False
            
            return False  # 기본값은 접근 가능으로
            
        except:
            return False
    
    # =========================================================================
    # 카페 게시물 수집
    # =========================================================================
    
    def fetch_cafe_posts(self, cafe: PMCafe) -> List[CafePost]:
        """카페의 공개 게시물 수집"""
        posts = []
        
        try:
            # 카페 메인 페이지 접근
            self.driver.get(cafe.cafe_url)
            self.random_delay(2, 3)
            
            if self._check_login_required():
                logger.info(f"  → 🔒 {cafe.cafe_id}: 게시물 접근 불가")
                return posts
            
            # iframe 처리
            try:
                iframe = self.driver.find_element(By.ID, 'cafe_main')
                self.driver.switch_to.frame(iframe)
            except:
                pass
            
            # 게시물 목록 추출
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 게시물 링크 추출
            article_links = []
            link_selectors = [
                'a.article', 'a[href*="articleid"]', 'a[href*="/"]',
                '.article-board a', '.board-list a'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if re.search(r'/\d+$', href) or 'articleid' in href:
                        full_url = f"https://cafe.naver.com{href}" if href.startswith('/') else href
                        if not self.duplicate_checker.is_url_duplicate(full_url):
                            article_links.append(full_url)
                
                if article_links:
                    break
            
            # iframe에서 빠져나오기
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            # 게시물 수집 (최대 개수 제한)
            collected = 0
            for url in article_links[:self.max_posts_per_cafe]:
                if self.time_manager.is_time_exceeded():
                    break
                
                post = self._fetch_single_post(url, cafe)
                if post:
                    posts.append(post)
                    self.duplicate_checker.add_url(url)
                    collected += 1
                
                self.random_delay(1, 2)
            
            if collected > 0:
                logger.info(f"  → 📝 {cafe.cafe_id}: {collected}개 게시물 수집")
        
        except Exception as e:
            logger.error(f"게시물 수집 오류 ({cafe.cafe_id}): {e}")
            self.error_logs.append(f"게시물 수집 오류 ({cafe.cafe_id}): {e}")
            
            try:
                self.driver.switch_to.default_content()
            except:
                pass
        
        return posts
    
    def _fetch_single_post(self, url: str, cafe: PMCafe) -> Optional[CafePost]:
        """단일 게시물 수집"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # 로그인 필요 확인
            if self._check_login_required():
                self.stats.posts_skipped_private += 1
                return None
            
            # iframe 처리
            try:
                iframe = self.driver.find_element(By.ID, 'cafe_main')
                self.driver.switch_to.frame(iframe)
            except:
                pass
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            post = CafePost(
                cafe_id=cafe.cafe_id,
                cafe_name=cafe.cafe_name,
                url=url,
                collected_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # article_id 추출 (v1.1 개선: articleid= 형식도 지원)
            # URL 예: /1429 또는 articleid=1429
            match = re.search(r'articleid[=:](\d+)', url, re.IGNORECASE)
            if match:
                post.article_id = match.group(1)
            else:
                match = re.search(r'/(\d+)(?:\?|$)', url)
                if match:
                    post.article_id = match.group(1)
            
            # 제목
            title_elem = soup.select_one('.title_text, .article_title, h3.title')
            if title_elem:
                post.title = title_elem.get_text(strip=True)
            
            # 본문
            content_elem = soup.select_one('.article_viewer, .content, .se-main-container')
            if content_elem:
                post.content = content_elem.get_text(strip=True)[:10000]
            
            # 작성자
            author_elem = soup.select_one('.nickname, .nick, .user_info .name')
            if author_elem:
                post.author_nickname = author_elem.get_text(strip=True)
            
            # 작성일
            date_elem = soup.select_one('.date, .datetime, .article_info .date')
            if date_elem:
                post.published_datetime = date_elem.get_text(strip=True)
            
            # 조회수 (개선된 셀렉터)
            view_selectors = ['.count', '.view_count', '.article_info .count', 'span[class*="count"]']
            for selector in view_selectors:
                elem = soup.select_one(selector)
                if elem:
                    text = elem.get_text()
                    match = re.search(r'조회\s*(\d+)', text)
                    if match:
                        post.view_count = int(match.group(1))
                        break
            
            # 좋아요 수 (개선: 정확한 위치에서 추출)
            like_elem = soup.select_one('.u_cnt._count, .like_article .count, .sympathy_cnt .u_cnt')
            if like_elem:
                like_text = like_elem.get_text(strip=True)
                if like_text.isdigit():
                    post.like_count = int(like_text)
            
            # 댓글 수 (추가 수정: strong.num 셀렉터 우선 사용)
            # HTML 예시: <strong class="num">1</strong>
            comment_elem = soup.select_one('strong.num')
            if comment_elem:
                comment_text = comment_elem.get_text(strip=True)
                if comment_text.isdigit():
                    post.comment_count = int(comment_text)
            
            # 해시태그 (v1.2 추가 수정: a.tag_link 셀렉터 추가)
            # HTML 예시: <a class="tag_link">#부업</a>
            hashtag_selectors = ['a.tag_link', '.tag_area a', 'a.tag', '.article_tag a', 'a[href*="tag"]']
            hashtags = []
            for selector in hashtag_selectors:
                tags = soup.select(selector)
                for tag in tags:
                    text = tag.get_text(strip=True)
                    if text and (text.startswith('#') or text):
                        hashtags.append(text if text.startswith('#') else f'#{text}')
                if hashtags:  # 첫 번째 성공한 셀렉터에서 중단
                    break
            post.hashtags = ', '.join(hashtags[:20])
            
            # 이미지 URL
            image_urls = []
            for img in soup.select('img.se-image-resource, img[src*="cafeptthumb"], img[src*="postfiles"]'):
                src = img.get('src') or img.get('data-src')
                if src and 'http' in src:
                    image_urls.append(src)
            post.image_urls = ' | '.join(image_urls[:10])
            
            # 영상 URL
            video_urls = []
            for iframe in soup.select('iframe[src*="tv.naver"], iframe[src*="youtube"]'):
                src = iframe.get('src')
                if src:
                    video_urls.append(src)
            post.video_urls = ' | '.join(video_urls[:5])
            
            # PM 후원 정보 추출 (v1.1 개선: 다양한 형식 지원)
            content_text = post.content
            
            # 전화번호: 010-1234-5678, 010.1234.5678, 010 1234 5678 등
            phone_patterns = [
                r'010[-.\s]?\d{4}[-.\s]?\d{4}',  # 010-1234-5678, 010.1234.5678
                r'☎\s*010[-.\s]?\d{4}[-.\s]?\d{4}',  # ☎ 010-1234-5678
            ]
            for pattern in phone_patterns:
                phone_match = re.search(pattern, content_text)
                if phone_match:
                    phone = phone_match.group().replace('☎', '').strip()
                    # 정규화: 점/공백을 하이픈으로
                    post.sponsor_phone = re.sub(r'[-.\s]+', '-', phone)
                    break
            
            # 후원코드/추천인: 다양한 패턴 지원
            partner_patterns = [
                r'(?:후원코드|추천인|후원인|파트너)[:\s]*[가-힣*]*?(\d{6,10})',  # 후원코드:이*훈20589722
                r'(?:추천인번호|후원번호|파트너코드)[:\s]*(\d{6,10})',
                r'(\d{8})\s*입력',  # 20589722입력
            ]
            for pattern in partner_patterns:
                partner_match = re.search(pattern, content_text)
                if partner_match:
                    post.sponsor_partner_id = partner_match.group(1)
                    break
            
            # iframe에서 빠져나오기
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            # v1.4: 키워드 필터링 제거 → is_pm_keyword 태깅으로 변경
            combined_text = f"{post.title} {post.content}"
            post.is_pm_keyword = self._contains_pm_keyword(combined_text)
            post.cafe_type = "pm_exclusive"
            
            return post
            
        except Exception as e:
            self.stats.errors += 1
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return None
    
    # =========================================================================
    # 저장 및 리포트
    # =========================================================================
    
    def save_results(self):
        """결과 저장 (v1.4: 파일명/경로 변경)"""
        output_config = self.config.get('output', {})
        encoding = output_config.get('csv_encoding', 'utf-8-sig')
        
        # v1.4: data_pm 폴더에 저장
        data_dir = 'data_pm'
        Path(data_dir).mkdir(exist_ok=True)
        
        # 타임스탬프 (YYMMDD_HHMMSS 형식)
        test_mode = self.config.get('execution_mode', {}).get('test_mode', True)
        mode_str = 'test' if test_mode else 'final'
        timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
        
        # v1.4: 파일명 형식 변경 (targeting → pm)
        # 카페 정보 저장
        if self.pm_cafes:
            cafes_df = pd.DataFrame([asdict(c) for c in self.pm_cafes])
            cafes_filename = f"{data_dir}/naver_cafe_pm_info_v1_4_{mode_str}_{timestamp}.csv"
            cafes_df.to_csv(cafes_filename, index=False, encoding=encoding)
            logger.info(f"💾 카페 정보 저장: {cafes_filename} ({len(self.pm_cafes)}개)")
        
        # 게시물 저장
        if self.posts:
            posts_df = pd.DataFrame([asdict(p) for p in self.posts])
            posts_filename = f"{data_dir}/naver_cafe_pm_posts_v1_4_{mode_str}_{timestamp}.csv"
            posts_df.to_csv(posts_filename, index=False, encoding=encoding)
            logger.info(f"💾 게시물 저장: {posts_filename} ({len(self.posts)}개)")
        
        self.end_datetime = datetime.now()
        self.generate_report(timestamp, mode_str)
    
    def generate_report(self, timestamp: str, mode_str: str):
        """리포트 생성 (v1.4)"""
        # v1.4: data_pm 폴더 사용
        data_dir = 'data_pm'
        
        elapsed = self.time_manager.get_elapsed_minutes()
        
        report_lines = [
            "=" * 70,
            "📊 PM 전용 카페 크롤러 v1.4 결과 보고서",
            f"   실행 ID: {timestamp}",
            "=" * 70,
            "",
            f"⏱️ 시작: {self.start_datetime.strftime('%Y-%m-%d %H:%M:%S')}",
            f"⏱️ 종료: {self.end_datetime.strftime('%Y-%m-%d %H:%M:%S')}",
            f"⏱️ 총 실행 시간: {elapsed:.1f}분",
            "",
            "📈 수집 성과",
            "-" * 70,
            f"• 발견된 PM 카페: {self.stats.cafes_found}개",
            f"  - 접근 가능: {self.stats.cafes_accessible}개",
            f"  - 비공개: {self.stats.cafes_private}개",
            f"• 수집된 게시물: {self.stats.posts_collected}개",
            f"  - 중복 스킵: {self.stats.posts_skipped_duplicate}개",
            f"  - 비공개 스킵: {self.stats.posts_skipped_private}개",
            f"  - PM 키워드 있음: {sum(1 for p in self.posts if p.is_pm_keyword)}개",  # v1.4
            f"• 에러: {self.stats.errors}개",
            "",
        ]
        
        if self.pm_cafes:
            report_lines.extend([
                "🏠 수집된 PM 카페 목록 (상위 10개)",
                "-" * 70,
            ])
            for cafe in self.pm_cafes[:10]:
                report_lines.append(
                    f"• {cafe.cafe_name[:30]} ({cafe.cafe_id}) - 멤버 {cafe.member_count:,}명"
                )
        
        if self.error_logs:
            report_lines.extend([
                "",
                "⚠️ 에러 로그 (최근 10개)",
                "-" * 70,
            ])
            for error in self.error_logs[-10:]:
                report_lines.append(f"• {error[:80]}")
        
        report_lines.extend(["", "=" * 70])
        
        report_path = f"{data_dir}/naver_cafe_pm_report_v1_4_{mode_str}_{timestamp}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"📝 리포트 저장: {report_path}")
        
        # 콘솔 출력
        for line in report_lines:
            logger.info(line)
    
    # =========================================================================
    # 메인 실행
    # =========================================================================
    
    def signal_handler(self, signum, frame):
        """종료 시그널 핸들러"""
        logger.info("\n⚠️ 종료 신호 감지! 결과 저장 중...")
        self.save_results()
        sys.exit(0)
    
    def run(self):
        """메인 실행"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("=" * 70)
        logger.info("🎯 PM 전용 카페 크롤러 v1.4 시작")
        logger.info("=" * 70)
        
        exec_config = self.config.get('execution_mode', {})
        targeting_config = self.config.get('targeting', {})
        
        logger.info(f"⏰ 최대 실행 시간: {exec_config.get('max_duration_minutes', 60)}분")
        logger.info(f"📝 카페당 최대 수집: {self.max_posts_per_cafe}개")
        logger.info("")
        
        try:
            self.setup_driver()
            
            # 기존 데이터 로드 (중복 방지) - v1.4: data_pm 폴더도 확인
            for data_dir in ['data', 'data_targeting', 'data_pm', 'data_posts']:
                if Path(data_dir).exists():
                    for csv_file in Path(data_dir).glob('*posts*.csv'):
                        self.duplicate_checker.load_existing_urls(str(csv_file))
            
            # 카페 검색 키워드
            keywords = targeting_config.get('cafe_search_keywords', [
                '피엠인터내셔널', '독일피엠', 'PM인터내셔널', '피트라인'
            ])
            
            # 1단계: PM 전용 카페 검색
            logger.info("\n📍 [1단계] PM 전용 카페 검색")
            logger.info("-" * 50)
            
            all_cafe_infos = []
            for keyword in keywords:
                if self.time_manager.is_time_exceeded():
                    logger.info("⏰ 시간 초과")
                    break
                
                cafes = self.search_pm_cafes(keyword)
                all_cafe_infos.extend(cafes)
                self.random_delay(3, 5)
            
            self.stats.cafes_found = len(all_cafe_infos)
            
            # 2단계: 각 카페 상세 정보 및 게시물 수집
            logger.info(f"\n🏠 [2단계] 카페 상세 정보 및 게시물 수집 ({len(all_cafe_infos)}개)")
            logger.info("-" * 50)
            
            for i, cafe_info in enumerate(all_cafe_infos):
                if self.time_manager.is_time_exceeded():
                    logger.info("⏰ 시간 초과")
                    break
                
                logger.info(f"\n[{i+1}/{len(all_cafe_infos)}] {cafe_info['cafe_id']}")
                
                # 카페소개 수집
                cafe = self.fetch_cafe_intro(cafe_info['cafe_id'])
                if cafe:
                    cafe.search_keyword = cafe_info['search_keyword']
                    
                    if cafe.is_accessible:
                        self.stats.cafes_accessible += 1
                        self.pm_cafes.append(cafe)
                        
                        # 게시물 수집
                        posts = self.fetch_cafe_posts(cafe)
                        if posts:
                            self.posts.extend(posts)
                            cafe.posts_collected = len(posts)
                            self.stats.posts_collected += len(posts)
                    else:
                        self.stats.cafes_private += 1
                
                # 카페 간 쿨다운
                if i < len(all_cafe_infos) - 1:
                    logger.info(f"  ⏳ {self.cool_down}초 대기...")
                    time.sleep(self.cool_down)
                
                # 남은 시간 표시
                remaining = self.time_manager.get_remaining_minutes()
                logger.info(f"  ⏰ 남은 시간: {remaining:.1f}분")
        
        except Exception as e:
            logger.error(f"❌ 크롤링 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        finally:
            self.save_results()
            self.stats.print_stats(self.time_manager.get_elapsed_minutes())
            
            if self.driver:
                self.driver.quit()
                logger.info("🔚 드라이버 종료 완료")

# =============================================================================
# 메인 실행
# =============================================================================

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PM 전용 카페 크롤러 v1.4')
    parser.add_argument('--config', type=str, default='config_cafe.yaml',
                        help='설정 파일 경로')
    parser.add_argument('--duration', type=int, default=None,
                        help='실행 시간 (분)')
    parser.add_argument('--max-posts', type=int, default=None,
                        help='카페당 최대 게시물 수')
    parser.add_argument('--final', action='store_true',
                        help='최종 모드로 실행 (test → final)')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    # 설정 키가 없을 경우 기본값 설정
    config.setdefault('execution_mode', {})
    config.setdefault('targeting', {})
    
    if args.duration:
        config['execution_mode']['max_duration_minutes'] = args.duration
    if args.max_posts:
        config['targeting']['max_posts_per_cafe'] = args.max_posts
    if args.final:
        config['execution_mode']['test_mode'] = False
    
    crawler = PMCafeTargetingCrawler(config)
    crawler.run()

if __name__ == "__main__":
    main()
