#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 블로그 크롤러 v7.3 (최종 완성판)
모든 개선사항 통합 버전

🎯 v7.3 신규 개선 사항:
1. ✅ published_date → published_datetime (날짜+시간 정보)
2. ✅ 메모리 최적화 (가비지 컬렉션, 적응형 대기)
3. ✅ 연속 에러 시 드라이버 자동 재시작
4. ✅ 적응형 속도 조절 (성공/실패에 따라 동적 조정)
5. ✅ 컬럼 순서 명시적 정의

🔧 v7.1 유지 사항:
- sponsor_name 삭제 (오작동 방지)
- sponsor_phone: 010-xxxx-xxxx 형식만 수집
- sponsor_partner_id: 8자리 숫자만 수집
- like_count, comment_count: 별도 함수로 추출
- hashtags: # 기호 유지
- 콘텐츠 필터링: PM 키워드 + 추천인/8자리 필수
- post_id: {blog_id}_{post_id} 형식

📊 출력 컬럼 (15개):
- 기본: platform, post_id, blog_id, url, title, content, published_datetime
- 추천인: sponsor_phone, sponsor_partner_id
- 참여: like_count, comment_count
- 콘텐츠: hashtags, image_urls, video_urls
- 메타: collected_date

작성자: PMI Korea 데이터 분석팀
버전: 7.3
최종 수정일: 2025-11-06
"""

import os
import re
import json
import time
import random
import logging
import gc
from datetime import datetime
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
import config

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
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

for handler in logger.handlers:
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

# ===========================
# 설정값
# ===========================

# Naver Open API 설정
NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET

# User-Agent 목록
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]

# 검색 설정
SEARCH_KEYWORDS = ["피엠인터내셔널", "PMInternational", "FitLine"]
MAX_SEARCH_RESULTS = 100
TOTAL_TARGET = 100

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

EXCLUDE_KEYWORDS = [
    "뉴스", "기사", "보도", "공지", "아카데미", "세미나", "팽창탱크", "배관"
]

# v7.3: 크롤링 설정
PAGE_LOAD_TIMEOUT = 15
REQUEST_DELAY_MIN = 2.0
REQUEST_DELAY_MAX = 4.0
MAX_CONSECUTIVE_ERRORS = 5

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

class CrawlStats:
    """크롤링 통계"""
    
    def __init__(self):
        self.total_attempts = 0
        self.success = 0
        self.filtered = 0
        self.duplicates = 0
        self.errors = 0
        self.start_time = time.time()
    
    def add_success(self):
        self.success += 1
        self.total_attempts += 1
    
    def add_filtered(self):
        self.filtered += 1
        self.total_attempts += 1
    
    def add_duplicate(self):
        self.duplicates += 1
        self.total_attempts += 1
    
    def add_error(self):
        self.errors += 1
        self.total_attempts += 1
    
    def print_stats(self):
        elapsed = time.time() - self.start_time
        logger.info(f"\n{'='*70}")
        logger.info("📊 크롤링 통계")
        logger.info(f"{'='*70}")
        logger.info(f"총 시도: {self.total_attempts}")
        logger.info(f"✅ 성공: {self.success}")
        logger.info(f"🔍 필터링: {self.filtered}")
        logger.info(f"🔄 중복: {self.duplicates}")
        logger.info(f"❌ 에러: {self.errors}")
        logger.info(f"⏱️  소요 시간: {elapsed:.1f}초")
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
                    loaded_data = json.load(f)
                    # list인 경우 dict로 변환
                    if isinstance(loaded_data, list):
                        self.failed_urls = {}
                    elif isinstance(loaded_data, dict):
                        self.failed_urls = loaded_data
                    else:
                        self.failed_urls = {}
            except:
                self.failed_urls = {}
    
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
# v7.3: 날짜+시간 추출 함수
# ===========================

def parse_published_datetime(date_text: str) -> str:
    """발행 날짜+시간 파싱 (v7.3)"""
    if not date_text:
        return ""
    
    try:
        date_text = date_text.strip()
        now = datetime.now()
        
        # 패턴 1: YYYY.MM.DD. HH:MM
        match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})\.\s*(\d{1,2}):(\d{2})', date_text)
        if match:
            year, month, day, hour, minute = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d} {int(hour):02d}:{minute}:00"
        
        # 패턴 2: YYYY.MM.DD (시간 정보 없음)
        match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', date_text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d} 00:00:00"
        
        # 패턴 3: "N시간 전", "N분 전"
        if '시간 전' in date_text or '분 전' in date_text:
            return now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 패턴 4: "어제", "그제"
        if '어제' in date_text:
            yesterday = now - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d 00:00:00')
        elif '그제' in date_text:
            day_before = now - timedelta(days=2)
            return day_before.strftime('%Y-%m-%d 00:00:00')
        
        return ""
    except:
        return ""

# ===========================
# 데이터 추출 함수
# ===========================

def extract_sponsor_phone(text: str) -> str:
    """추천인 전화번호 추출 (v7.1: 엄격한 패턴)"""
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
    """추천인 파트너 ID 추출 (v7.1: 8자리 숫자만)"""
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
    """해시태그 추출 (v7.1: # 기호 유지, 본문 포함)"""
    hashtags = set()
    
    # 방법 1: 태그 영역에서 추출
    tag_elements = soup.select('a.link_tag, a[href*="tag"], .se_tag a')
    for elem in tag_elements:
        tag_text = elem.get_text(strip=True)
        if tag_text:
            if not tag_text.startswith('#'):
                tag_text = '#' + tag_text
            hashtags.add(tag_text)
    
    # 방법 2: 본문에서 #태그 추출
    hashtag_pattern = r'#([가-힣a-zA-Z0-9_]+)'
    matches = re.findall(hashtag_pattern, content_text)
    for match in matches:
        hashtags.add('#' + match)
    
    # 방법 3: 메타 태그
    meta_keywords = soup.find('meta', {'name': 'keywords'})
    if meta_keywords and meta_keywords.get('content'):
        keywords = meta_keywords['content'].split(',')
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword and len(keyword) > 0:
                if not keyword.startswith('#'):
                    keyword = '#' + keyword
                hashtags.add(keyword)
    
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
    """비디오 URL 추출"""
    video_urls = set()
    
    # 비디오 및 iframe 선택자
    video_elements = soup.select('video source, iframe[src*="youtube"], iframe[src*="youtu.be"], iframe[src*="vimeo"]')
    
    for elem in video_elements:
        src = elem.get('src')
        if src:
            video_urls.add(src)
    
    return ', '.join(list(video_urls)[:5]) if video_urls else ""

def extract_like_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """좋아요 수 추출 (v7.1: 별도 함수)"""
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
    """댓글 수 추출 (v7.1: 별도 함수)"""
    try:
        # 방법 1: Selenium으로 추출
        comment_selectors = [
            '.btn_comment .count',
            '.area_comment .count',
            'em.u_cnt._count',
            '.cmt_count'
        ]
        
        for selector in comment_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                comment_text = elem.text.strip()
                comment_count = int(re.sub(r'\D', '', comment_text))
                if comment_count > 0:
                    return comment_count
            except:
                continue
        
        # 방법 2: BeautifulSoup으로 추출
        page_text = soup.get_text()
        comment_patterns = [
            r'댓글\s*(\d+)',
            r'comment.*?(\d+)'
        ]
        for pattern in comment_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0
    except Exception as e:
        logger.debug(f"댓글 수 추출 실패: {str(e)}")
        return 0

# ===========================
# 필터링 함수
# ===========================

def content_passes_filter(title: str, content: str, full_text: str, 
                          sponsor_partner_id: str) -> Tuple[bool, str]:
    """콘텐츠 필터링 (v7.1 규칙)
    
    규칙:
    1. ["피엠", "피엠인터내셔널"] 중 하나 반드시 존재
    2. ["추천인" 키워드 OR 8자리 숫자] 중 하나 반드시 존재
    3. 제외 키워드 중 둘 이상 있으면 반드시 제외
    
    Returns:
        (통과여부, 실패사유)
    """
    text_lower = full_text.lower()
    
    # 규칙 1: PM 브랜드 키워드 체크
    has_pm_keyword = any(keyword.lower() in text_lower for keyword in PM_BRAND_KEYWORDS)
    if not has_pm_keyword:
        return False, "PM 브랜드 키워드 없음"
    
    # 규칙 2: 판매원 활동 키워드 OR 8자리 숫자 체크
    has_sales_keyword = any(keyword in full_text for keyword in PM_SALES_KEYWORDS)
    has_8digit = bool(sponsor_partner_id)
    
    if not (has_sales_keyword or has_8digit):
        return False, "판매원 관련 키워드 없음"
    
    # 규칙 3: 제외 키워드 체크 (둘 이상 있으면 제외)
    exclude_count = sum(1 for keyword in EXCLUDE_KEYWORDS if keyword in full_text)
    if exclude_count >= 2:
        return False, f"제외 키워드 {exclude_count}개 발견"
    
    return True, ""

# ===========================
# Selenium 드라이버 설정
# ===========================

def setup_driver() -> webdriver.Chrome:
    """Selenium 드라이버 설정 (v7.3: 메모리 최적화)"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # v7.3: 메모리 최적화
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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

def search_naver_blog(keyword: str, display: int = 100, start: int = 1) -> Optional[Dict]:
    """Naver Open Search API를 사용하여 블로그 검색"""
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
        "sort": "sim"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"검색 실패 ({keyword}): {str(e)}")
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

# ===========================
# 크롤링 함수
# ===========================

def crawl_blog_post_selenium(driver: webdriver.Chrome, url: str, blog_id: str, 
                            post_id: str, failed_url_manager: FailedURLManager) -> Optional[Dict]:
    """Selenium을 사용한 블로그 게시물 크롤링 (v7.3)"""
    try:
        logger.debug(f"크롤링 시작: {url}")
        driver.get(url)
        
        # iframe 대기 및 전환
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'mainFrame'))
            )
            driver.switch_to.frame('mainFrame')
        except TimeoutException:
            logger.debug("iframe 없음 - 본문 직접 크롤링")
        
        # 페이지 로딩 대기
        time.sleep(2)
        
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
        
        # v7.3: 발행 날짜+시간 추출
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
                published_datetime = parse_published_datetime(date_text)
                if published_datetime:
                    break
        
        # 전체 텍스트 (필터링용)
        full_text = f"{title} {content}"
        
        # 추천인 정보 추출
        sponsor_phone = extract_sponsor_phone(full_text)
        sponsor_partner_id = extract_sponsor_partner_id(full_text)
        
        # 필터링 검사
        passes, reason = content_passes_filter(title, content, full_text, sponsor_partner_id)
        if not passes:
            logger.debug(f"필터링됨: {reason} - {title[:50]}")
            failed_url_manager.add_failed(url, f"필터링: {reason}")
            return None
        
        # 해시태그 추출
        hashtags = extract_hashtags(soup, content)
        
        # 이미지/비디오 URL 추출
        image_urls = extract_image_urls(soup)
        video_urls = extract_video_urls(soup)
        
        # 좋아요/댓글 수 추출 (v7.1: 별도 함수)
        like_count = extract_like_count(driver, soup)
        comment_count = extract_comment_count(driver, soup)
        
        # 데이터 구성
        post_data = {
            'platform': 'naver_blog',
            'post_id': f"{blog_id}_{post_id}",  # v7.1 형식
            'blog_id': blog_id,
            'url': url,
            'title': title,
            'content': content,
            'published_datetime': published_datetime,  # v7.3: 시간 포함
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
    """메인 실행 함수 (v7.3)"""
    logger.info("="*70)
    logger.info("🚀 PM International 네이버 블로그 크롤러 v7.3 시작")
    logger.info("="*70)
    
    driver = setup_driver()
    stats = CrawlStats()
    failed_url_manager = FailedURLManager()
    adaptive = AdaptiveDelay()  # v7.3: 적응형 대기
    
    collected_posts = []
    collected_urls = set()
    collected_fingerprints = set()
    consecutive_errors = 0  # v7.3: 연속 에러 카운트
    crawl_count = 0  # v7.3: 크롤링 카운트
    
    try:
        # 검색 키워드별 크롤링
        for keyword in SEARCH_KEYWORDS:
            if len(collected_posts) >= TOTAL_TARGET:
                break
            
            logger.info(f"\n{'='*70}")
            logger.info(f"🔍 키워드 검색: {keyword}")
            logger.info(f"{'='*70}")
            
            # API 검색
            search_data = search_naver_blog(keyword, MAX_SEARCH_RESULTS)
            if not search_data:
                logger.warning(f"'{keyword}' 검색 결과 없음")
                continue
            
            # 결과 파싱
            search_results = parse_search_results(search_data)
            logger.info(f"📝 '{keyword}' 최종 결과: {len(search_results)}개")
            
            if not search_results:
                logger.warning(f"'{keyword}' 파싱 결과 없음")
                continue
            
            for result in search_results:
                if len(collected_posts) >= TOTAL_TARGET:
                    break
                
                blog_id = result['blog_id']
                post_id = result['post_id']
                normalized_url = normalize_blog_url(blog_id, post_id)
                
                # 중복 체크
                if normalized_url in collected_urls:
                    stats.add_duplicate()
                    continue
                
                logger.info(f"[{len(collected_posts)+1}/{TOTAL_TARGET}] 크롤링 중...")
                
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
                        stats.add_success()
                        consecutive_errors = 0  # v7.3: 성공 시 에러 카운트 리셋
                        adaptive.on_success()  # v7.3: 성공 시 대기 시간 단축
                        logger.info(f"✅ 수집 완료: {post_data['title'][:50]}")
                    else:
                        stats.add_duplicate()
                else:
                    stats.add_filtered()
                    consecutive_errors += 1  # v7.3: 에러 카운트 증가
                    adaptive.on_fail()  # v7.3: 실패 시 대기 시간 증가
                
                # v7.3: 연속 에러 시 드라이버 재시작
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.warning(f"⚠️  연속 {MAX_CONSECUTIVE_ERRORS}회 에러 - 드라이버 재시작")
                    driver.quit()
                    time.sleep(3)
                    driver = setup_driver()
                    consecutive_errors = 0
                    gc.collect()  # v7.3: 가비지 컬렉션
                
                crawl_count += 1
                
                # v7.3: 적응형 대기 시간
                delay = adaptive.get_delay()
                time.sleep(delay)
                
                # v7.3: 주기적 메모리 정리
                if crawl_count % 20 == 0:
                    gc.collect()
            
            if len(collected_posts) < TOTAL_TARGET:
                time.sleep(random.uniform(2, 4))
        
        stats.print_stats()
        
        # CSV 저장 (v7.3: 컬럼 순서 명시)
        if collected_posts:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'naver_blog_pm_v7_3_{timestamp}.csv'
            
            df = pd.DataFrame(collected_posts)
            
            # v7.3: 컬럼 순서 명시적 정의
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
