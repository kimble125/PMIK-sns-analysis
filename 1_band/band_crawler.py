#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PM-International Korea Band 크롤러 v2.0

변경 사항 (v1.1 → v2.0):
- 좋아요/댓글/조회수/공유수 셀렉터 실제 HTML 구조에 맞게 수정
- share_count 컬럼 추가
- 시간 제한 없이 모든 대상 수집 완료까지 실행
- 10분 후 첫 번째 저장 (중간 확인용)
- sponsor_phone, sponsor_partner_id, hashtags 본문에서 추출 (기존 유지)

🎯 목적:
PM 사업자 관련 공개 밴드/페이지를 발굴하고 게시물을 수집

🔒 주요 기능:
1. 📍 PM 관련 밴드/페이지 검색 - Band 검색 기능 활용
2. 📄 밴드/페이지 정보 수집 - intro 페이지에서 상세 정보 추출
3. 📝 공개 게시물 수집 - 게시물 목록에서 데이터 추출
4. 📞 연락처 추출 - 전화번호, 후원인 번호 파싱
5. 💾 10분 후 첫 번째 저장 - 중간 확인용

📊 출력 테이블:
- band_info_v2_0_*.csv: 밴드/페이지 정보 (entity_type으로 구분)
- band_posts_v2_0_*.csv: 게시물 목록

⚠️ 법적 고지:
- 본 크롤러는 공개된 정보만 수집합니다
- 로그인이 필요한 밴드/게시물은 수집하지 않습니다
- Band 이용약관을 준수합니다

작성자: PMI Korea 데이터 분석팀
버전: 2.0.0
최종 수정일: 2025-12-09
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

def load_config(config_path: str = "config_band.yaml") -> Dict:
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
            'test_mode': False,
            'max_duration_minutes': 0,  # 0 = 무제한
            'max_posts_per_band': 50,
            'checkpoint_interval_minutes': 10
        },
        'crawling': {
            'page_load_timeout': 15,
            'request_delay_min': 2.0,
            'request_delay_max': 4.0,
            'scroll_wait_seconds': 2,
            'max_scroll_attempts': 10,
            'max_retries': 3,
            'headless': True,
            'max_empty_results': 5
        },
        'keywords': {
            'primary': [
                {'keyword': '피엠인터내셔널', 'target': 30},
                {'keyword': '독일피엠', 'target': 30}
            ],
            'secondary': [
                {'keyword': '피트라인', 'target': 20}
            ]
        },
        'filters': {
            'pm_brand_keywords': ['피엠인터내셔널', 'PM인터내셔널', '독일피엠', '피트라인', 'FitLine'],
            'product_keywords': ['엑티바이즈', '뮤노겐', '파워칵테일', '리스토레이트'],
            'sales_keywords': ['팀파트너', '후원인', '추천인']
        },
        'user_agents': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ],
        'output': {
            'data_dir': 'data_band',
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
    """로깅 설정"""
    log_dir = CONFIG.get('logging', {}).get('log_dir', 'logs')
    Path(log_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"{log_dir}/band_crawler_v2_{timestamp}.log"
    
    logger = logging.getLogger('band_crawler_v2')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info(f"📝 로그 파일: {log_file}")
    return logger

logger = setup_logging()

# =============================================================================
# 데이터 클래스 정의
# =============================================================================

@dataclass
class BandInfo:
    """밴드/페이지 정보 데이터 클래스"""
    platform: str = "band"
    entity_type: str = ""             # 'band' or 'page'
    entity_id: str = ""               # 밴드/페이지 ID
    entity_name: str = ""             # 밴드/페이지 이름
    url: str = ""                     # URL
    
    # 소개 정보
    description: str = ""             # 소개글
    tags: str = ""                    # 태그 (| 구분)
    category: str = ""                # 카테고리
    
    # 통계 정보
    member_count: int = 0             # 멤버수 (밴드) / 구독자수 (페이지)
    established_date: str = ""        # 개설일
    recent_join: str = ""             # 최근 가입
    recent_posts: str = ""            # 최근 새글
    recent_activity: str = ""         # 최근 활동
    
    # 연결 정보
    connected_pages: str = ""         # 연결된 페이지 (| 구분)
    connected_bands: str = ""         # 연결된 밴드 (| 구분)
    
    # 검색 정보
    search_keyword: str = ""          # 이 밴드를 찾은 검색 키워드
    is_accessible: bool = True        # 공개 접근 가능 여부
    
    # PM 특화 필드
    is_pm_keyword: bool = False       # PM 키워드 포함 여부
    
    # 메타 필드
    collected_datetime: str = ""
    posts_collected: int = 0


@dataclass
class BandPost:
    """게시물 데이터 클래스 - v2.0 share_count 추가"""
    platform: str = "band"
    entity_type: str = ""             # 'band' or 'page'
    entity_id: str = ""               # 밴드/페이지 ID
    entity_name: str = ""             # 밴드/페이지 이름
    post_id: str = ""                 # 게시물 ID
    url: str = ""                     # 게시물 URL
    
    # 게시물 내용
    title: str = ""                   # 제목 (있을 경우)
    content: str = ""                 # 본문 내용
    author_nickname: str = ""         # 작성자 닉네임
    published_datetime: str = ""      # 작성일시
    
    # 반응 - v2.0 share_count 추가
    like_count: int = 0               # 좋아요 수
    comment_count: int = 0            # 댓글 수
    view_count: int = 0               # 조회수
    share_count: int = 0              # 공유수 (v2.0 추가)
    
    # PM 특화 필드 - 본문에서 추출
    sponsor_phone: str = ""           # 후원인 전화번호
    sponsor_partner_id: str = ""      # 후원인 번호 (7-8자리)
    hashtags: str = ""                # 해시태그 (| 구분)
    
    # 미디어 URL
    image_urls: str = ""              # 이미지 URL (| 구분)
    video_urls: str = ""              # 동영상 URL (| 구분)
    
    # 메타 필드
    collected_datetime: str = ""
    is_public: bool = True
    is_pm_keyword: bool = False       # PM 키워드 포함 여부
    search_keyword: str = ""          # 검색 키워드

# =============================================================================
# 유틸리티 클래스
# =============================================================================

class TimeManager:
    """시간 관리 클래스 - v2.0 무제한 모드 지원"""
    
    def __init__(self, max_duration_minutes: int = 0):
        self.start_time = time.time()
        self.max_duration_seconds = max_duration_minutes * 60 if max_duration_minutes > 0 else 0
        self.first_save_done = False  # 10분 후 첫 저장 여부
        self.unlimited = (max_duration_minutes == 0)
    
    def is_time_exceeded(self) -> bool:
        if self.unlimited:
            return False
        return (time.time() - self.start_time) >= self.max_duration_seconds
    
    def get_elapsed_minutes(self) -> float:
        return (time.time() - self.start_time) / 60
    
    def get_remaining_minutes(self) -> float:
        if self.unlimited:
            return float('inf')
        remaining = self.max_duration_seconds - (time.time() - self.start_time)
        return max(0, remaining / 60)
    
    def should_first_save(self, interval_minutes: int) -> bool:
        """10분 후 첫 번째 저장 여부 (한 번만), 0이면 비활성화"""
        if interval_minutes <= 0:
            return False
        if self.first_save_done:
            return False
        if self.get_elapsed_minutes() >= interval_minutes:
            self.first_save_done = True
            return True
        return False


class DuplicateChecker:
    """중복 체커 클래스"""
    
    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_entity_ids: Set[str] = set()
    
    def is_url_duplicate(self, url: str) -> bool:
        normalized = self._normalize_url(url)
        return normalized in self.seen_urls
    
    def add_url(self, url: str):
        normalized = self._normalize_url(url)
        self.seen_urls.add(normalized)
    
    def is_entity_duplicate(self, entity_id: str) -> bool:
        return entity_id in self.seen_entity_ids
    
    def add_entity(self, entity_id: str):
        self.seen_entity_ids.add(entity_id)
    
    def _normalize_url(self, url: str) -> str:
        """URL 정규화"""
        match = re.search(r'band\.us/(band|page)/(\d+)(?:/post/(\d+))?', url)
        if match:
            entity_type, entity_id, post_id = match.groups()
            if post_id:
                return f"{entity_type}_{entity_id}_{post_id}"
            return f"{entity_type}_{entity_id}"
        return url
    
    def load_existing_urls(self, csv_path: str):
        """기존 CSV에서 URL 로드"""
        try:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                if 'url' in df.columns:
                    for url in df['url'].dropna():
                        self.add_url(url)
                    logger.info(f"  → 기존 URL {len(self.seen_urls)}개 로드됨")
        except Exception as e:
            logger.warning(f"기존 URL 로드 실패: {e}")


class ContentExtractor:
    """콘텐츠 추출기 클래스"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.pm_keywords = self._load_pm_keywords()
    
    def _load_pm_keywords(self) -> List[str]:
        """PM 키워드 로드"""
        keywords = []
        filters = self.config.get('filters', {})
        keywords.extend(filters.get('pm_brand_keywords', []))
        keywords.extend(filters.get('product_keywords', []))
        keywords.extend(filters.get('sales_keywords', []))
        return list(set(keywords))
    
    def contains_pm_keyword(self, text: str) -> bool:
        """텍스트에 PM 키워드 포함 여부 확인"""
        if not text:
            return False
        text_lower = text.lower()
        for keyword in self.pm_keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def extract_phone_numbers(self, text: str) -> str:
        """전화번호 추출"""
        if not text:
            return ""
        
        patterns = [
            r'010[-.\s]?\d{4}[-.\s]?\d{4}',
            r'01[1-9][-.\s]?\d{3,4}[-.\s]?\d{4}',
            r'02[-.\s]?\d{3,4}[-.\s]?\d{4}',
            r'0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}'
        ]
        
        phones = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phones.extend(matches)
        
        return '|'.join(list(set(phones))) if phones else ""
    
    def extract_sponsor_id(self, text: str) -> str:
        """후원인 번호 추출 (7-8자리)"""
        if not text:
            return ""
        
        patterns = [
            r'(?:후원인|추천인|파트너|회원)\s*(?:번호|ID|코드)?\s*[:\s]?\s*(\d{7,8})',
            r'(?:sponsor|partner)\s*(?:id|code|no)?\s*[:\s]?\s*(\d{7,8})',
            r'#?\s*(\d{7,8})\s*(?:번|번호)?'
        ]
        
        ids = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            ids.extend(matches)
        
        valid_ids = [id for id in ids if 7 <= len(id) <= 8]
        
        return '|'.join(list(set(valid_ids))) if valid_ids else ""
    
    def extract_hashtags(self, text: str) -> str:
        """해시태그 추출"""
        if not text:
            return ""
        
        pattern = r'#([^\s#]+)'
        hashtags = re.findall(pattern, text)
        
        return '|'.join(hashtags) if hashtags else ""


class CrawlStats:
    """크롤링 통계 클래스"""
    
    def __init__(self):
        self.bands_found = 0
        self.pages_found = 0
        self.bands_accessible = 0
        self.bands_private = 0
        self.posts_collected = 0
        self.posts_skipped_duplicate = 0
        self.posts_skipped_private = 0
        self.errors = 0
        self.first_save_done = False
    
    def print_stats(self, elapsed_minutes: float):
        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 크롤링 통계")
        logger.info("=" * 60)
        logger.info(f"⏰ 실행 시간: {elapsed_minutes:.1f}분")
        logger.info(f"🏠 발견된 밴드: {self.bands_found}")
        logger.info(f"📄 발견된 페이지: {self.pages_found}")
        logger.info(f"  ✅ 접근 가능: {self.bands_accessible}")
        logger.info(f"  🔒 비공개: {self.bands_private}")
        logger.info(f"📝 수집된 게시물: {self.posts_collected}")
        logger.info(f"  🔄 중복 스킵: {self.posts_skipped_duplicate}")
        logger.info(f"  🔒 비공개 스킵: {self.posts_skipped_private}")
        logger.info(f"💾 10분 저장: {'완료' if self.first_save_done else '대기중'}")
        logger.info(f"❌ 에러: {self.errors}")
        logger.info("=" * 60)

# =============================================================================
# 메인 크롤러 클래스
# =============================================================================

class BandCrawler:
    """Band 크롤러 메인 클래스 v2.0"""
    
    BASE_URL = "https://www.band.us"
    SEARCH_URL = "https://www.band.us/search"
    
    def __init__(self, config: Dict):
        self.config = config
        self.driver = None
        
        # 데이터 저장
        self.band_infos: List[BandInfo] = []
        self.posts: List[BandPost] = []
        
        # 유틸리티
        exec_config = config.get('execution_mode', {})
        max_duration = exec_config.get('max_duration_minutes', 0)
        self.time_manager = TimeManager(max_duration)
        self.duplicate_checker = DuplicateChecker()
        self.extractor = ContentExtractor(config)
        self.stats = CrawlStats()
        
        # 설정
        self.max_posts_per_band = exec_config.get('max_posts_per_band', 50)
        self.checkpoint_interval = exec_config.get('checkpoint_interval_minutes', 10)
        
        # 딜레이 설정
        crawl_config = config.get('crawling', {})
        self.delay_min = crawl_config.get('request_delay_min', 2.0)
        self.delay_max = crawl_config.get('request_delay_max', 4.0)
        self.search_scrolls = crawl_config.get('max_scroll_attempts', 10)
        self.post_scrolls = crawl_config.get('max_scroll_attempts', 10)
        self.max_empty = crawl_config.get('max_empty_results', 5)
        
        # 시간 기록
        self.start_datetime = datetime.now()
        self.end_datetime = None
        self.run_id = datetime.now().strftime('%y%m%d_%H%M%S')
        
        # 에러 로그
        self.error_logs: List[str] = []
    
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
        
        options.add_argument('--lang=ko-KR')
        options.add_experimental_option('prefs', {'intl.accept_languages': 'ko-KR,ko'})
        
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
    # 검색 및 밴드/페이지 목록 수집
    # =========================================================================
    
    def search_bands_and_pages(self, keyword: str) -> List[Dict]:
        """Band 검색으로 밴드/페이지 목록 수집"""
        results = []

        # 밴드 검색
        band_url = f"{self.SEARCH_URL}/band?keyword={quote(keyword)}&filter=all"
        logger.info(f"🔍 밴드 검색: {keyword}")

        try:
            self.driver.get(band_url)
            self.random_delay(self.delay_min, self.delay_max)

            self._scroll_to_load_more(max_scrolls=self.search_scrolls)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            band_links = soup.select('a[href*="/band/"][href*="/intro"]')
            logger.info(f"  → 밴드 링크 {len(band_links)}개 발견")

            for link in band_links:
                try:
                    href = link.get('href', '')
                    match = re.search(r'/band/(\d+)', href)
                    if match:
                        band_id = match.group(1)
                        name = link.get_text(strip=True)
                        if not name:
                            name_candidates = link.find_all(text=True, recursive=True)
                            name = ' '.join([t.strip() for t in name_candidates if t.strip()])[:100]

                        if name:
                            results.append({
                                'entity_type': 'band',
                                'entity_id': band_id,
                                'entity_name': name,
                                'search_keyword': keyword
                            })
                except Exception as e:
                    logger.debug(f"밴드 링크 파싱 오류: {e}")

            # 페이지 검색
            page_url = f"{self.SEARCH_URL}/page?keyword={quote(keyword)}&filter=all"
            logger.info(f"🔍 페이지 검색: {keyword}")

            self.driver.get(page_url)
            self.random_delay(self.delay_min, self.delay_max)

            self._scroll_to_load_more(max_scrolls=self.search_scrolls)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            page_links = soup.select('a[href*="/page/"]')
            logger.info(f"  → 페이지 링크 {len(page_links)}개 발견")

            for link in page_links:
                try:
                    href = link.get('href', '')
                    match = re.search(r'/page/(\d+)', href)
                    if match:
                        page_id = match.group(1)
                        name = link.get_text(strip=True)
                        if not name:
                            name_candidates = link.find_all(text=True, recursive=True)
                            name = ' '.join([t.strip() for t in name_candidates if t.strip()])[:100]

                        if name:
                            results.append({
                                'entity_type': 'page',
                                'entity_id': page_id,
                                'entity_name': name,
                                'search_keyword': keyword
                            })
                except Exception as e:
                    logger.debug(f"페이지 링크 파싱 오류: {e}")

        except TimeoutException:
            logger.warning(f"⏰ 검색 타임아웃: {keyword}")
            self.stats.errors += 1
        except Exception as e:
            logger.error(f"❌ 검색 오류: {e}")
            self.stats.errors += 1
            self.error_logs.append(f"검색 오류 ({keyword}): {str(e)[:100]}")

        return results

    def _scroll_to_load_more(self, max_scrolls: int = 5):
        """스크롤하여 더 많은 결과 로드"""
        crawl_config = self.config.get('crawling', {})
        scroll_wait = crawl_config.get('scroll_wait_seconds', 2)
        
        for i in range(max_scrolls):
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_wait)
            except:
                break
    
    # =========================================================================
    # 밴드/페이지 상세 정보 수집
    # =========================================================================
    
    def fetch_entity_info(self, entity_type: str, entity_id: str, search_keyword: str = "") -> Optional[BandInfo]:
        """밴드/페이지 상세 정보 수집"""
        
        if entity_type == 'band':
            intro_url = f"{self.BASE_URL}/band/{entity_id}/intro"
        else:
            intro_url = f"{self.BASE_URL}/page/{entity_id}"
        
        logger.info(f"  📋 {entity_type} 정보 수집: {entity_id}")
        
        try:
            self.driver.get(intro_url)
            self.random_delay(self.delay_min, self.delay_max)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            info = BandInfo(
                entity_type=entity_type,
                entity_id=entity_id,
                url=intro_url,
                search_keyword=search_keyword,
                collected_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # [v1.1.2 수정] 밴드/페이지 이름 - 실제 HTML 구조에 맞게 수정
            name_selectors = [
                'h1.bandName',
                'h2.bandName', '.pageName', '.bandTitle', 'h1.name', '.uBandName',
                '.bandNameText', 'strong.name', '.introName', '.coverName'
            ]
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    info.entity_name = name_elem.get_text(strip=True)
                    break
            
            # 소개글
            desc_elem = soup.select_one('p.desc')
            if desc_elem:
                for br in desc_elem.find_all('br'):
                    br.replace_with(' ')
                info.description = desc_elem.get_text(strip=True)[:self.config.get('output', {}).get('max_content_length', 10000)]
            
            # 태그
            tag_elems = soup.select('button.introOptionLink._btnBandKeyword, button._btnBandKeyword')
            tags = []
            categories = []
            for tag in tag_elems:
                tag_text = tag.get('data-keyword')
                if tag_text:
                    tags.append(tag_text)
                group = tag.get('data-group')
                if group and group not in categories:
                    categories.append(group)
            info.tags = '|'.join(tags)
            info.category = '|'.join(categories) if categories else ""
            
            # 멤버수
            member_elem = soup.select_one('span.memberCount._memberCountText, span._memberCountText')
            if member_elem:
                member_text = member_elem.get_text(strip=True)
                numbers = re.findall(r'[\d,]+', member_text)
                if numbers:
                    info.member_count = int(numbers[0].replace(',', ''))
            
            # 페이지 구독자수
            if entity_type == 'page' and info.member_count == 0:
                subscriber_elem = soup.select_one('span.total, .subscriberCount, .readMember span')
                if subscriber_elem:
                    sub_text = subscriber_elem.get_text(strip=True)
                    numbers = re.findall(r'[\d,]+', sub_text)
                    if numbers:
                        info.member_count = int(numbers[0].replace(',', ''))
            
            # 상세 정보
            desc_items = soup.select('span.introDescData')
            for item in desc_items:
                text = item.get_text(strip=True)
                if '개설' in text:
                    info.established_date = text
                elif '최근 가입' in text:
                    info.recent_join = text
                elif '최근 새글' in text:
                    info.recent_posts = text
                elif '최근 활동' in text:
                    info.recent_activity = text
            
            # 연결된 페이지
            connected_pages = soup.select('._connectedPageBandListRegion a[href*="/page/"]')
            if connected_pages:
                page_ids = []
                for cp in connected_pages:
                    cp_href = cp.get('href', '')
                    cp_match = re.search(r'/page/(\d+)', cp_href)
                    if cp_match:
                        page_ids.append(cp_match.group(1))
                info.connected_pages = '|'.join(page_ids)
            
            # PM 키워드 확인
            combined_text = f"{info.entity_name} {info.description} {info.tags}"
            info.is_pm_keyword = self.extractor.contains_pm_keyword(combined_text)
            
            info.is_accessible = True
            return info
            
        except TimeoutException:
            logger.warning(f"⏰ 정보 수집 타임아웃: {entity_id}")
            self.stats.errors += 1
            return None
        except Exception as e:
            logger.error(f"❌ 정보 수집 오류: {e}")
            self.stats.errors += 1
            self.error_logs.append(f"정보 수집 오류 ({entity_id}): {str(e)[:100]}")
            return None
    
    # =========================================================================
    # 게시물 수집
    # =========================================================================
    
    def fetch_entity_posts(self, info: BandInfo) -> List[BandPost]:
        """밴드/페이지 게시물 수집"""
        posts = []
        
        if info.entity_type == 'band':
            posts_url = f"{self.BASE_URL}/band/{info.entity_id}/post"
        else:
            posts_url = f"{self.BASE_URL}/page/{info.entity_id}/post"
        
        logger.info(f"  📝 게시물 수집 시작: {info.entity_id}")
        
        try:
            self.driver.get(posts_url)
            self.random_delay(self.delay_min, self.delay_max)
            
            collected = 0
            empty_count = 0
            max_empty = self.max_empty
            
            # 가입 필요 밴드 빠른 스킵
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            join_required = soup.select_one('._joinBtnArea, .uEmptyInnerBox, .uEmptyTitle')
            if join_required:
                join_text = join_required.get_text(strip=True)
                if 'members' in join_text.lower() or 'join' in join_text.lower():
                    logger.info(f"    → 가입 필요 밴드, 스킵")
                    self.stats.bands_private += 1
                    return posts
            
            # 스크롤하며 게시물 수집
            while collected < self.max_posts_per_band and empty_count < max_empty:
                if self.time_manager.is_time_exceeded():
                    logger.info("⏰ 시간 초과")
                    break
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 게시물 컨테이너 - 실제 HTML 구조
                post_items = soup.select('article.cContentsCard._postMainWrap, article.cContentsCard')
                
                new_posts = 0
                for item in post_items:
                    if collected >= self.max_posts_per_band:
                        break
                    
                    try:
                        post = self._parse_post_item(item, info)
                        if post and not self.duplicate_checker.is_url_duplicate(post.url):
                            posts.append(post)
                            self.duplicate_checker.add_url(post.url)
                            collected += 1
                            new_posts += 1
                    except Exception as e:
                        logger.debug(f"게시물 파싱 오류: {e}")
                
                if new_posts == 0:
                    empty_count += 1
                else:
                    empty_count = 0
                
                # 스크롤
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(self.delay_min, self.delay_max)
            
            logger.info(f"    → {collected}개 게시물 수집됨")
            
        except TimeoutException:
            logger.warning(f"⏰ 게시물 수집 타임아웃: {info.entity_id}")
            self.stats.errors += 1
        except Exception as e:
            logger.error(f"❌ 게시물 수집 오류: {e}")
            self.stats.errors += 1
            self.error_logs.append(f"게시물 수집 오류 ({info.entity_id}): {str(e)[:100]}")
        
        return posts
    
    def _parse_post_item(self, item, info: BandInfo) -> Optional[BandPost]:
        """게시물 아이템 파싱 - v2.0 셀렉터 개선"""
        post = BandPost(
            entity_type=info.entity_type,
            entity_id=info.entity_id,
            entity_name=info.entity_name,
            search_keyword=info.search_keyword,
            collected_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 게시물 URL/ID
        post_link = item.select_one('.postWriterInfoWrap a[href*="/post/"], a[href*="/post/"]')
        if post_link:
            href = post_link.get('href', '')
            post.url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
            match = re.search(r'/post/(\d+)', href)
            if match:
                post.post_id = match.group(1)
            # 공유 게시물 감지
            band_match = re.search(r'/band/(\d+)/', href)
            if band_match and band_match.group(1) != info.entity_id:
                post.sponsor_partner_id = band_match.group(1)
        
        if not post.url:
            return None
        
        # 작성자 - img의 alt 속성에서 추출
        author_img = item.select_one('.postWriter img._image[alt]')
        if author_img:
            alt_text = author_img.get('alt', '')
            if alt_text and 'anniversary' not in alt_text.lower() and 'reminder' not in alt_text.lower():
                post.author_nickname = alt_text
        
        # 본문 내용
        content_elem = item.select_one('p.txtBody, .postText .txtBody, .txtBody')
        if content_elem:
            for br in content_elem.find_all('br'):
                br.replace_with('\n')
            post.content = content_elem.get_text(strip=True)[:self.config.get('output', {}).get('max_content_length', 10000)]
        
        # 작성일
        date_elem = item.select_one('.postDate, .date, .time, .createDate')
        if date_elem:
            post.published_datetime = date_elem.get_text(strip=True)
        
        # ========================================
        # v2.0 개선: 좋아요/댓글/조회수/공유수 셀렉터
        # 실제 HTML 구조에 맞게 수정
        # ========================================
        
        # 좋아요: <button type="button" class="count _countBtn">16</button>
        like_elem = item.select_one('button.count._countBtn, button._countBtn, .emotionCount')
        if like_elem:
            like_text = like_elem.get_text(strip=True)
            numbers = re.findall(r'\d+', like_text)
            if numbers:
                post.like_count = int(numbers[0])
        
        # 댓글: <button type="button" class="count -commentCount _commentCountLayerBtn">12</button>
        comment_elem = item.select_one('button.-commentCount._commentCountLayerBtn, button.-commentCount, .commentCount')
        if comment_elem:
            comment_text = comment_elem.get_text(strip=True)
            numbers = re.findall(r'\d+', comment_text)
            if numbers:
                post.comment_count = int(numbers[0])
        
        # 조회수: <span class="readCount">588 읽음</span>
        view_elem = item.select_one('span.readCount, .viewCount, .readCount')
        if view_elem:
            view_text = view_elem.get_text(strip=True)
            numbers = re.findall(r'[\d,]+', view_text)
            if numbers:
                post.view_count = int(numbers[0].replace(',', ''))
        
        # 공유수: <button class="count -shareCount _sharedCountLayerBtn">19</button>
        share_elem = item.select_one('button.-shareCount._sharedCountLayerBtn, button.-shareCount, .shareCount')
        if share_elem:
            share_text = share_elem.get_text(strip=True)
            numbers = re.findall(r'\d+', share_text)
            if numbers:
                post.share_count = int(numbers[0])
        
        # 이미지 URL
        images = item.select('img.postImage, img.photo, img[src*="phinf"]')
        image_urls = []
        for img in images:
            src = img.get('src') or img.get('data-src')
            if src and 'phinf' in src:
                image_urls.append(src)
        post.image_urls = '|'.join(image_urls)
        
        # 동영상 URL
        videos = item.select('video source, a[href*="video"], .videoThumb')
        video_urls = []
        for video in videos:
            src = video.get('src') or video.get('href')
            if src:
                video_urls.append(src)
        post.video_urls = '|'.join(video_urls)
        
        # 해시태그 - 본문에서 추출
        post.hashtags = self.extractor.extract_hashtags(post.content)
        
        # 전화번호 - 본문에서 추출
        if not post.sponsor_phone:
            post.sponsor_phone = self.extractor.extract_phone_numbers(post.content)
        
        # 후원인 번호 - 본문에서 추출 (공유 게시물이 아닌 경우)
        if not post.sponsor_partner_id:
            post.sponsor_partner_id = self.extractor.extract_sponsor_id(post.content)
        
        # PM 키워드 포함 여부
        post.is_pm_keyword = self.extractor.contains_pm_keyword(post.content)
        
        return post
    
    # =========================================================================
    # 결과 저장
    # =========================================================================
    
    def save_results(self, is_first_save: bool = False):
        """결과 저장"""
        output_config = self.config.get('output', {})
        data_dir = output_config.get('data_dir', 'data_band')
        encoding = output_config.get('csv_encoding', 'utf-8-sig')
        
        Path(data_dir).mkdir(exist_ok=True)
        
        test_mode = self.config.get('execution_mode', {}).get('test_mode', False)
        mode_str = 'test' if test_mode else 'final'
        
        # 10분 저장이면 현재 시간, 아니면 run_id 사용
        if is_first_save:
            timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
            suffix = f"_10min_{timestamp}"
        else:
            suffix = f"_{self.run_id}"
        
        # 밴드/페이지 정보 저장
        if self.band_infos:
            infos_df = pd.DataFrame([asdict(i) for i in self.band_infos])
            infos_filename = f"{data_dir}/band_info_v2_0_{mode_str}{suffix}.csv"
            infos_df.to_csv(infos_filename, index=False, encoding=encoding)
            logger.info(f"💾 밴드/페이지 정보 저장: {infos_filename} ({len(self.band_infos)}개)")
        
        # 게시물 저장
        if self.posts:
            posts_df = pd.DataFrame([asdict(p) for p in self.posts])
            posts_filename = f"{data_dir}/band_posts_v2_0_{mode_str}{suffix}.csv"
            posts_df.to_csv(posts_filename, index=False, encoding=encoding)
            logger.info(f"💾 게시물 저장: {posts_filename} ({len(self.posts)}개)")
        
        if is_first_save:
            self.stats.first_save_done = True
            logger.info(f"📝 10분 저장 완료 - 중간 확인 가능")
        else:
            self.end_datetime = datetime.now()
            self.generate_report(self.run_id, mode_str)
    
    def generate_report(self, timestamp: str, mode_str: str):
        """리포트 생성"""
        output_config = self.config.get('output', {})
        data_dir = output_config.get('data_dir', 'data_band')
        
        elapsed = self.time_manager.get_elapsed_minutes()
        
        report_lines = [
            "=" * 70,
            "📊 Band 크롤러 v2.0 결과 보고서",
            f"   실행 ID: {timestamp}",
            "=" * 70,
            "",
            f"⏱️ 시작: {self.start_datetime.strftime('%Y-%m-%d %H:%M:%S')}",
            f"⏱️ 종료: {self.end_datetime.strftime('%Y-%m-%d %H:%M:%S') if self.end_datetime else 'N/A'}",
            f"⏱️ 총 실행 시간: {elapsed:.1f}분",
            "",
            "📈 수집 성과",
            "-" * 70,
            f"• 발견된 밴드: {self.stats.bands_found}개",
            f"• 발견된 페이지: {self.stats.pages_found}개",
            f"  - 접근 가능: {self.stats.bands_accessible}개",
            f"  - 비공개: {self.stats.bands_private}개",
            f"• 수집된 게시물: {self.stats.posts_collected}개",
            f"  - 중복 스킵: {self.stats.posts_skipped_duplicate}개",
            f"  - PM 키워드 있음: {sum(1 for p in self.posts if p.is_pm_keyword)}개",
            f"• 10분 저장: {'완료' if self.stats.first_save_done else '대기중'}",
            f"• 에러: {self.stats.errors}개",
            "",
            "🏠 수집된 밴드/페이지 목록 (상위 10개)",
            "-" * 70,
        ]
        
        for info in self.band_infos[:10]:
            report_lines.append(
                f"• [{info.entity_type}] {info.entity_name[:30]} ({info.entity_id}) - 멤버 {info.member_count}명"
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
        
        report_path = f"{data_dir}/band_report_v2_0_{mode_str}_{timestamp}.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"📝 리포트 저장: {report_path}")
        
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
        """메인 실행 - v2.0 무제한 모드 + 10분 체크포인트"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("=" * 70)
        logger.info("🎯 Band 크롤러 v2.0 시작")
        logger.info("=" * 70)
        
        exec_config = self.config.get('execution_mode', {})
        max_duration = exec_config.get('max_duration_minutes', 0)
        
        if max_duration == 0:
            logger.info("⏰ 실행 시간: 무제한 (모든 대상 수집 완료까지)")
        else:
            logger.info(f"⏰ 최대 실행 시간: {max_duration}분")
        
        logger.info(f"📝 밴드당 최대 수집: {self.max_posts_per_band}개")
        if self.checkpoint_interval > 0:
            logger.info(f"💾 {self.checkpoint_interval}분 후 첫 번째 저장 예정")
        else:
            logger.info("💾 중간 저장 비활성화 (완료 시에만 저장)")
        logger.info("")
        
        try:
            self.setup_driver()
            
            # 기존 데이터 로드 (중복 방지)
            data_dir = self.config.get('output', {}).get('data_dir', 'data_band')
            if Path(data_dir).exists():
                for csv_file in Path(data_dir).glob('*posts*.csv'):
                    self.duplicate_checker.load_existing_urls(str(csv_file))
            
            # 키워드 목록 구성
            keywords_config = self.config.get('keywords', {})
            all_keywords = []
            all_keywords.extend(keywords_config.get('primary', []))
            all_keywords.extend(keywords_config.get('secondary', []))
            
            # 1단계: 키워드로 밴드/페이지 검색
            search_start = time.time()
            
            logger.info("\n📍 [1단계] 밴드/페이지 검색")
            logger.info("-" * 50)
            
            all_entities = []
            for kw_info in all_keywords:
                if self.time_manager.is_time_exceeded():
                    logger.info("⏰ 전체 시간 초과")
                    break
                
                keyword = kw_info.get('keyword', '')
                entities = self.search_bands_and_pages(keyword)
                
                for entity in entities:
                    if not self.duplicate_checker.is_entity_duplicate(entity['entity_id']):
                        all_entities.append(entity)
                        self.duplicate_checker.add_entity(entity['entity_id'])
                        
                        if entity['entity_type'] == 'band':
                            self.stats.bands_found += 1
                        else:
                            self.stats.pages_found += 1
                
                self.random_delay(self.delay_min, self.delay_max)
            
            search_elapsed = (time.time() - search_start) / 60
            logger.info(f"\n총 {len(all_entities)}개 밴드/페이지 발견 (검색 시간: {search_elapsed:.1f}분)")
            
            # 2단계: 각 밴드/페이지 상세 정보 및 게시물 수집
            logger.info(f"\n🏠 [2단계] 상세 정보 및 게시물 수집")
            logger.info("-" * 50)
            
            for i, entity in enumerate(all_entities):
                if self.time_manager.is_time_exceeded():
                    logger.info("⏰ 시간 초과")
                    break
                
                logger.info(f"\n[{i+1}/{len(all_entities)}] {entity['entity_type']}: {entity['entity_id']}")
                
                # 정보 수집
                info = self.fetch_entity_info(
                    entity['entity_type'],
                    entity['entity_id'],
                    entity['search_keyword']
                )
                
                if info:
                    if info.is_accessible:
                        self.stats.bands_accessible += 1
                        self.band_infos.append(info)
                        
                        # 게시물 수집
                        posts = self.fetch_entity_posts(info)
                        if posts:
                            self.posts.extend(posts)
                            info.posts_collected = len(posts)
                            self.stats.posts_collected += len(posts)
                    else:
                        self.stats.bands_private += 1
                
                # 실행 시간 표시
                elapsed = self.time_manager.get_elapsed_minutes()
                if self.time_manager.unlimited:
                    logger.info(f"  ⏰ 실행 시간: {elapsed:.1f}분")
                else:
                    remaining = self.time_manager.get_remaining_minutes()
                    logger.info(f"  ⏰ 남은 시간: {remaining:.1f}분")
                
                # 10분 후 첫 번째 저장 (한 번만)
                if self.time_manager.should_first_save(self.checkpoint_interval):
                    logger.info(f"\n💾 10분 경과 - 첫 번째 저장 ({elapsed:.1f}분)...")
                    self.save_results(is_first_save=True)
                
                self.random_delay(self.delay_min, self.delay_max)
            
            logger.info("\n✅ 모든 대상 수집 완료!")
        
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
    
    parser = argparse.ArgumentParser(description='PM-International Band 크롤러 v2.0')
    parser.add_argument('--config', type=str, default='config_band.yaml',
                        help='설정 파일 경로')
    parser.add_argument('--duration', type=int, default=None,
                        help='실행 시간 (분), 0=무제한')
    parser.add_argument('--max-posts', type=int, default=None,
                        help='밴드당 최대 게시물 수')
    parser.add_argument('--checkpoint', type=int, default=None,
                        help='중간 저장 간격 (분)')
    parser.add_argument('--no-headless', action='store_true',
                        help='브라우저 창 표시 (디버깅용)')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    if args.duration is not None:
        config['execution_mode']['max_duration_minutes'] = args.duration
    if args.max_posts:
        config['execution_mode']['max_posts_per_band'] = args.max_posts
    if args.checkpoint is not None:
        config['execution_mode']['checkpoint_interval_minutes'] = args.checkpoint
    if args.no_headless:
        config['crawling']['headless'] = False
    
    crawler = BandCrawler(config)
    crawler.run()


if __name__ == "__main__":
    main()
