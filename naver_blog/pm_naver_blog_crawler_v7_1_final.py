#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 블로그 크롤러 v7.1 (최종 완성판)

🎯 주요 개선 사항:
1. ✅ sponsor_name 삭제 (오작동 방지)
2. ✅ sponsor_phone: 010-xxxx-xxxx 형식만 엄격하게 수집
3. ✅ sponsor_partner_id: 정확히 8자리 숫자만 수집
4. ✅ like_count, comment_count: v6.6의 검증된 로직 복원 (별도 함수)
5. ✅ hashtags: # 기호 유지, 본문 내 해시태그도 모두 추출
6. ✅ 콘텐츠 필터링: 
    - ["피엠", "피엠인터내셔널"] 중 하나 반드시 존재
    - ["추천인" 또는 8자리 숫자] 중 하나 반드시 존재
    - 제외 키워드 둘 이상 시 반드시 제외
7. ✅ post_id: {blog_id}_{post_id} 형식으로 변경
8. ✅ platform 컬럼 추가

📊 출력 컬럼 (15개):
- 기본: platform, post_id, blog_id, url, title, content, published_date
- 추천인: sponsor_phone, sponsor_partner_id
- 참여: like_count, comment_count
- 콘텐츠: hashtags, image_urls, video_urls
- 메타: collected_date

작성자: PMI Korea 데이터 분석팀
버전: 7.1
최종 수정일: 2025-11-06
"""

import os
import re
import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urlparse, parse_qs, unquote

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
        'DEBUG': '\033[94m',    # 파란색
        'INFO': '\033[92m',     # 초록색
        'WARNING': '\033[93m',  # 노란색
        'ERROR': '\033[91m',    # 빨간색
        'CRITICAL': '\033[95m', # 보라색
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

logging.basicConfig(
    level=logging.DEBUG,  # INFO → DEBUG로 변경
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.propagate = False

# Ensure at least one handler exists and apply colored formatter safely
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # INFO → DEBUG로 변경
    console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
else:
    # Update the first handler's formatter
    logger.handlers[0].setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))

# ===========================
# 설정
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

# 검색 키워드
SEARCH_KEYWORDS = [
    "피엠인터내셔널",
    "피엠코리아",
    "PM인터내셔널",
    "핏라인",
    "FitLine"
]

# 필수 포함 키워드 (v7.1: 브랜드 키워드)
PM_BRAND_KEYWORDS = ["피엠", "피엠인터내셔널", "PM", "PM인터내셔널", "PM-International"]

# 필수 포함 키워드 (v7.1: 판매원 활동 키워드)
PM_SALES_KEYWORDS = ["추천인", "파트너번호", "회원번호", "파트너ID", "등록번호"]

# 제외 키워드 (v7.1: 사용자 정의 - 크롤링하면서 확장)
EXCLUDE_KEYWORDS = [
    "뉴스", "기사", "보도", "공지",
    "아카데미", "세미나", "팽창탱크", "배관"
]

# 수집 설정
POSTS_PER_KEYWORD = 20
TOTAL_TARGET = 100
MAX_SEARCH_RESULTS = 50

# 타이밍 설정
SELENIUM_WAIT_TIMEOUT = 10
IFRAME_WAIT_TIMEOUT = 15
REQUEST_DELAY_MIN = 1.5
REQUEST_DELAY_MAX = 3.0

# ===========================
# 유틸리티 클래스
# ===========================

class CrawlStats:
    """크롤링 통계"""
    def __init__(self):
        self.total_searched = 0
        self.total_collected = 0
        self.total_duplicates = 0
        self.total_filtered = 0
        self.total_errors = 0
        self.start_time = time.time()
    
    def add_success(self):
        self.total_collected += 1
    
    def add_duplicate(self):
        self.total_duplicates += 1
    
    def add_filtered(self):
        self.total_filtered += 1
    
    def add_error(self):
        self.total_errors += 1
    
    def print_stats(self):
        elapsed = time.time() - self.start_time
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 크롤링 통계")
        logger.info(f"{'='*70}")
        logger.info(f"✅ 수집 성공: {self.total_collected}개")
        logger.info(f"🔄 중복 제거: {self.total_duplicates}개")
        logger.info(f"🚫 필터링: {self.total_filtered}개")
        logger.info(f"❌ 오류: {self.total_errors}개")
        logger.info(f"⏱️  소요 시간: {elapsed:.1f}초")
        logger.info(f"{'='*70}\n")

class FailedURLManager:
    """실패한 URL 관리"""
    def __init__(self):
        self.failed_urls: List[Dict] = []
    
    def add_failed_url(self, url: str, reason: str, error: str = ""):
        self.failed_urls.append({
            'url': url,
            'reason': reason,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
    
    def save_to_file(self, filename: str = 'failed_urls.json'):
        if self.failed_urls:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.failed_urls, f, ensure_ascii=False, indent=2)
    
    def get_failed_count(self) -> int:
        return len(self.failed_urls)

# ===========================
# 헬퍼 함수
# ===========================

def normalize_blog_url(blog_id: str, post_id: str) -> str:
    """블로그 URL 정규화"""
    return f"https://blog.naver.com/{blog_id}/{post_id}"

def generate_post_fingerprint(post_data: Dict) -> str:
    """게시물 고유 지문 생성"""
    title = post_data.get('title', '')
    content = post_data.get('content', '')[:200]
    return f"{title}_{content}"

def extract_blog_info_from_url(url: str) -> Optional[Dict[str, str]]:
    """URL에서 blog_id와 post_id 추출
    
    지원 형식:
    - https://blog.naver.com/blog_id/post_id
    - https://blog.naver.com/PostView.nhn?blogId=blog_id&logNo=post_id
    - https://m.blog.naver.com/blog_id/post_id
    
    Returns:
        {'blog_id': str, 'post_id': str} 또는 None
    """
    try:
        parsed_url = urlparse(url)
        
        # 형식 1: /blog_id/post_id
        path_match = re.match(r'/([^/]+)/(\d+)', parsed_url.path)
        if path_match:
            return {
                'blog_id': path_match.group(1),
                'post_id': path_match.group(2)
            }
        
        # 형식 2: PostView.nhn?blogId=...&logNo=...
        if 'PostView' in parsed_url.path:
            query_params = parse_qs(parsed_url.query)
            blog_id = query_params.get('blogId', [None])[0]
            post_id = query_params.get('logNo', [None])[0]
            if blog_id and post_id:
                return {
                    'blog_id': blog_id,
                    'post_id': post_id
                }
        
        return None
    except Exception as e:
        logger.error(f"URL 파싱 실패: {url} - {str(e)}")
        return None

def parse_korean_date(date_str: str) -> Optional[str]:
    """한국어 날짜 문자열을 ISO 형식으로 변환
    
    예: '2024. 11. 5. 14:30' -> '2024-11-05'
    """
    try:
        # 불필요한 공백 및 특수문자 제거
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        # 패턴 1: YYYY. MM. DD. HH:MM
        match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*\d{1,2}:\d{2}', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 패턴 2: YYYY. MM. DD.
        match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 패턴 3: YYYY-MM-DD
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        return None
    except Exception as e:
        logger.debug(f"날짜 파싱 실패: {date_str} - {str(e)}")
        return None

def extract_sponsor_phone(text: str) -> str:
    """추천인 전화번호 추출 (010-xxxx-xxxx 형식만)"""
    if not text:
        return ""
    
    # 010-xxxx-xxxx 형식만 추출 (정확히 11자리)
    pattern = r'010[-\s]?\d{4}[-\s]?\d{4}'
    matches = re.findall(pattern, text)
    
    if matches:
        # 하이픈 정규화
        phone = re.sub(r'\s', '', matches[0])
        phone = re.sub(r'(\d{3})(\d{4})(\d{4})', r'\1-\2-\3', phone)
        return phone
    
    return ""

def extract_sponsor_partner_id(text: str) -> str:
    """추천인 파트너 ID 추출 (정확히 8자리 숫자만)"""
    if not text:
        return ""
    
    # 정확히 8자리 숫자만 (앞뒤에 숫자가 없어야 함)
    pattern = r'(?<!\d)(\d{8})(?!\d)'
    matches = re.findall(pattern, text)
    
    if matches:
        return matches[0]
    
    return ""

def has_eight_digit_number(text: str) -> bool:
    """텍스트에 8자리 숫자가 있는지 확인"""
    if not text:
        return False
    pattern = r'(?<!\d)(\d{8})(?!\d)'
    return bool(re.search(pattern, text))

def extract_hashtags(soup: BeautifulSoup, content_text: str) -> str:
    """해시태그 추출 (# 기호 포함, 본문 내 해시태그도 추출)"""
    hashtags_set = set()
    
    # 방법 1: HTML 태그에서 추출
    tag_selectors = [
        'a.link_tag',
        'a[href*="tag"]',
        'span.ell',
        'div.post_tag a',
        'div.tag_area a'
    ]
    
    for selector in tag_selectors:
        tags = soup.select(selector)
        for tag in tags:
            tag_text = tag.get_text(strip=True)
            if tag_text and not tag_text.startswith('#'):
                tag_text = f"#{tag_text}"
            if tag_text:
                hashtags_set.add(tag_text)
    
    # 방법 2: 본문 텍스트에서 # 패턴 추출
    if content_text:
        # #로 시작하고 공백이나 특수문자 전까지
        hashtag_pattern = r'#[^\s#,،]+' 
        matches = re.findall(hashtag_pattern, content_text)
        for match in matches:
            # 끝의 특수문자 제거
            cleaned = re.sub(r'[.,!?;:\)]+$', '', match)
            if len(cleaned) > 1:  # # 다음에 문자가 있는 경우만
                hashtags_set.add(cleaned)
    
    return ', '.join(sorted(hashtags_set)) if hashtags_set else ""

def extract_like_count(driver, soup) -> int:
    """좋아요 수 추출 (v6.6 로직 복원)"""
    try:
        # Selenium으로 시도
        like_selectors = [
            'span.u_cnt._count',
            'span.cnt_like',
            'em.u_cnt',
            'span.like_count',
            'a.btn_empathy span.u_cnt',
            'div.end_btn span.u_cnt',
            'span#printLog'
        ]
        
        for selector in like_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and text.isdigit():
                        return int(text)
            except:
                continue
        
        # BeautifulSoup로 시도
        for selector in like_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and text.isdigit():
                    return int(text)
        
        # 텍스트에서 정규표현식으로 추출
        page_text = soup.get_text()
        like_patterns = [
            r'좋아요\s*(\d+)',
            r'공감\s*(\d+)',
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

def extract_comment_count(driver, soup) -> int:
    """댓글 수 추출 (v6.6 로직 복원)"""
    try:
        # Selenium으로 시도
        comment_selectors = [
            'span.u_cnt._count.ccmtcnt',
            'span.cnt_cmt',
            'em.u_cmt',
            'span.comment_count',
            'a.btn_comment span.u_cnt',
            'div.end_btn span.u_cnt',
            'span.num'
        ]
        
        for selector in comment_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    # 댓글 버튼에 '댓글 N' 형식일 수 있음
                    number_match = re.search(r'\d+', text)
                    if number_match:
                        return int(number_match.group())
            except:
                continue
        
        # BeautifulSoup로 시도
        for selector in comment_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                number_match = re.search(r'\d+', text)
                if number_match:
                    return int(number_match.group())
        
        # 텍스트에서 정규표현식으로 추출
        page_text = soup.get_text()
        comment_patterns = [
            r'댓글\s*(\d+)',
            r'코멘트\s*(\d+)',
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

def content_passes_filter(title: str, content: str, full_text: str) -> Tuple[bool, str]:
    """콘텐츠 필터링 (v7.1 강화된 로직)
    
    규칙:
    1. ["피엠", "피엠인터내셔널"] 중 하나 반드시 존재
    2. ["추천인" 또는 8자리 숫자] 중 하나 반드시 존재
    3. 제외 키워드 중 둘 이상 있으면 반드시 제외
    
    Returns:
        (통과여부, 실패사유)
    """
    # 전체 텍스트 준비
    text_lower = full_text.lower()
    
    # 규칙 1: PM 브랜드 키워드 체크
    has_pm_keyword = any(keyword.lower() in text_lower for keyword in PM_BRAND_KEYWORDS)
    if not has_pm_keyword:
        return False, "PM 브랜드 키워드 없음"
    
    # 규칙 2: 판매원 활동 키워드 또는 8자리 숫자 체크
    has_sales_keyword = any(keyword in full_text for keyword in PM_SALES_KEYWORDS)
    has_eight_digit = has_eight_digit_number(full_text)
    
    if not (has_sales_keyword or has_eight_digit):
        return False, "판매원 관련 키워드/번호 없음"
    
    # 규칙 3: 제외 키워드 체크 (둘 이상 있으면 제외)
    exclude_count = sum(1 for keyword in EXCLUDE_KEYWORDS if keyword in full_text)
    if exclude_count >= 2:
        return False, f"제외 키워드 {exclude_count}개 발견"
    
    return True, ""

# ===========================
# 크롤링 함수
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
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Homebrew chromedriver 우선 사용 (macOS Gatekeeper 문제 해결)
    homebrew_chromedriver = '/opt/homebrew/bin/chromedriver'
    
    if os.path.exists(homebrew_chromedriver):
        service = Service(homebrew_chromedriver)
        logger.info("✅ Homebrew ChromeDriver 사용")
    else:
        service = Service(ChromeDriverManager().install())
        logger.info("✅ webdriver-manager ChromeDriver 사용")
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 자동화 감지 우회
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver

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
        logger.debug("검색 데이터 없음")
        return results
    
    total_items = len(search_data['items'])
    logger.debug(f"API 응답: {total_items}개 아이템")
    
    for idx, item in enumerate(search_data['items'], 1):
        try:
            url = item.get('link', '')
            logger.debug(f"[{idx}/{total_items}] URL: {url}")
            
            if not url:
                logger.debug("  → URL 없음, 스킵")
                continue
                
            if 'blog.naver.com' not in url:
                logger.debug(f"  → 네이버 블로그 아님, 스킵")
                continue
            
            # blog_id와 post_id 추출
            blog_info = extract_blog_info_from_url(url)
            if not blog_info:
                logger.debug(f"  → blog_info 추출 실패, 스킵")
                continue
            
            logger.debug(f"  → ✅ 추가: {blog_info['blog_id']}/{blog_info['post_id']}")
            
            results.append({
                'url': url,
                'blog_id': blog_info['blog_id'],
                'post_id': blog_info['post_id'],
                'postdate': item.get('postdate', ''),
                'bloggername': item.get('bloggername', '')
            })
        except Exception as e:
            logger.debug(f"  → 파싱 오류: {str(e)}")
            continue
    
    logger.debug(f"최종 파싱 결과: {len(results)}개")
    return results

def crawl_blog_post_selenium(
    driver: webdriver.Chrome,
    url: str,
    blog_id: str,
    post_id: str,
    failed_url_manager: FailedURLManager
) -> Optional[Dict]:
    """Selenium을 사용한 블로그 게시물 크롤링"""
    
    try:
        driver.get(url)
        time.sleep(2)
        
        # iframe 대기 및 전환
        try:
            WebDriverWait(driver, IFRAME_WAIT_TIMEOUT).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
            )
        except TimeoutException:
            logger.warning(f"⚠️  iframe 로드 실패: {url}")
            failed_url_manager.add_failed_url(url, "iframe_timeout")
            return None
        
        # 페이지 로딩 대기
        WebDriverWait(driver, SELENIUM_WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # HTML 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 제목 추출
        title = ""
        title_selectors = [
            'div.se-title-text',
            'span.se-fs-',
            'div.se-component-content',
            'h3.se_textarea'
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title:
                    break
        
        if not title:
            title_elem = soup.find(['h1', 'h2', 'h3'])
            if title_elem:
                title = title_elem.get_text(strip=True)
        
        if not title:
            logger.warning(f"⚠️  제목 없음: {url}")
            failed_url_manager.add_failed_url(url, "no_title")
            driver.switch_to.default_content()
            return None
        
        # 본문 추출
        content = ""
        content_selectors = [
            'div.se-main-container',
            'div#postViewArea',
            'div.se-component-content',
            'div.post-view',
            'div.__se_component_area'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(separator=' ', strip=True)
                if len(content) > 50:
                    break
        
        if not content or len(content) < 20:
            logger.warning(f"⚠️  본문 없음 또는 너무 짧음: {url}")
            failed_url_manager.add_failed_url(url, "no_content")
            driver.switch_to.default_content()
            return None
        
        # 전체 텍스트 (필터링용)
        full_text = f"{title} {content}"
        
        # 콘텐츠 필터링
        passes, reason = content_passes_filter(title, content, full_text)
        if not passes:
            logger.debug(f"🚫 필터링: {title[:30]}... ({reason})")
            driver.switch_to.default_content()
            return None
        
        # 날짜 추출
        published_date = ""
        date_selectors = [
            'span.se_publishDate',
            'span.date',
            'p.date',
            'div.post_date',
            'span.p_date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_date = parse_korean_date(date_text)
                if published_date:
                    break
        
        # 추천인 정보 추출
        sponsor_phone = extract_sponsor_phone(full_text)
        sponsor_partner_id = extract_sponsor_partner_id(full_text)
        
        # 좋아요/댓글 수 추출 (v6.6 로직 사용)
        like_count = extract_like_count(driver, soup)
        comment_count = extract_comment_count(driver, soup)
        
        # 해시태그 추출
        hashtags = extract_hashtags(soup, content)
        
        # 이미지 URL 추출
        image_urls = []
        img_tags = soup.select('img.se-image-resource, img.__se_img_el, div.se-component-content img')
        for img in img_tags[:10]:  # 최대 10개
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http'):
                image_urls.append(src)
        
        # 비디오 URL 추출
        video_urls = []
        video_tags = soup.select('video source, iframe[src*="youtube"], iframe[src*="youtu.be"]')
        for video in video_tags[:5]:  # 최대 5개
            src = video.get('src')
            if src and src.startswith('http'):
                video_urls.append(src)
        
        # iframe에서 나가기
        driver.switch_to.default_content()
        
        # 데이터 구성 (v7.1: post_id 형식 변경, platform 추가)
        post_data = {
            'platform': 'naver_blog',
            'post_id': f"{blog_id}_{post_id}",  # v7.1: 복합 ID
            'blog_id': blog_id,
            'url': url,
            'title': title,
            'content': content,
            'published_date': published_date,
            'sponsor_phone': sponsor_phone,
            'sponsor_partner_id': sponsor_partner_id,
            'like_count': like_count,
            'comment_count': comment_count,
            'hashtags': hashtags,
            'image_urls': ', '.join(image_urls) if image_urls else "",
            'video_urls': ', '.join(video_urls) if video_urls else "",
            'collected_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        return post_data
    
    except TimeoutException:
        logger.warning(f"⚠️  타임아웃: {url}")
        failed_url_manager.add_failed_url(url, "timeout")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return None
    
    except Exception as e:
        logger.error(f"❌ 크롤링 오류: {url} - {str(e)}")
        failed_url_manager.add_failed_url(url, "crawl_error", str(e))
        try:
            driver.switch_to.default_content()
        except:
            pass
        return None

# ===========================
# 메인 함수
# ===========================

def main():
    """메인 실행 함수"""
    logger.info("="*70)
    logger.info("🚀 PM International 네이버 블로그 크롤러 v7.1 시작")
    logger.info("="*70)
    
    # 초기화
    driver = setup_driver()
    stats = CrawlStats()
    failed_url_manager = FailedURLManager()
    
    collected_posts = []
    collected_urls: Set[str] = set()
    collected_fingerprints: Set[str] = set()
    
    try:
        for keyword in SEARCH_KEYWORDS:
            if len(collected_posts) >= TOTAL_TARGET:
                logger.info(f"✅ 목표 달성 ({TOTAL_TARGET}개)")
                break
            
            logger.info(f"\n🔍 키워드 검색: '{keyword}'")
            
            # 검색
            search_data = search_naver_blog(keyword, MAX_SEARCH_RESULTS)
            if not search_data:
                logger.warning(f"⚠️  검색 결과 없음: {keyword}")
                continue
            
            # 검색 결과 파싱
            search_results = parse_search_results(search_data)
            logger.info(f"📋 검색 결과: {len(search_results)}개")
            
            # 크롤링
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
                        logger.info(f"✅ 수집 완료: {post_data['title'][:50]}...")
                    else:
                        stats.add_duplicate()
                        logger.debug(f"🔄 중복 (지문): {post_data['title'][:30]}...")
                else:
                    stats.add_filtered()
                
                # 요청 간 지연
                time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
            
            # 키워드 간 대기
            if len(collected_posts) < TOTAL_TARGET:
                time.sleep(random.uniform(2, 4))
        
        # 통계 출력
        stats.print_stats()
        
        # CSV로 저장
        if collected_posts:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'naver_blog_pm_v7_1_{timestamp}.csv'
            
            df = pd.DataFrame(collected_posts)
            
            # 컬럼 순서 정의
            column_order = [
                'platform', 'post_id', 'blog_id', 'url', 'title', 'content',
                'published_date', 'sponsor_phone', 'sponsor_partner_id',
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
        
        # 실패 URL 저장
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
