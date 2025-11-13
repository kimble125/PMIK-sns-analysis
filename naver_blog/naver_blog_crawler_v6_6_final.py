#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 블로그 크롤러 v6.6 (최종 개선판)

주요 개선 사항:
1. ✅ view_count, like_count, comment_count 추출 재도입 (다중 선택자 시도)
2. ✅ 크롤링 안정성 강화 (3회 재시도 + 지수 백오프)
3. ✅ 데이터 검증 로직 추가
4. ✅ 중복 제거 로직 강화 (URL + 제목 + 작성자)
5. ✅ 로깅 개선 (진행률, 성공률 표시)
6. ✅ 에러 핸들링 강화
7. ✅ referrer_name, hashtags, media_urls 추출 로직 개선
8. ✅ 실패 URL 별도 저장 (failed_urls.json)
9. ✅ 속도 최적화 (이미지 로딩 비활성화, 대기 시간 조정)
"""

import os
import re
import json
import time
import random
import logging
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

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 파일 핸들러
file_handler = logging.FileHandler(
    f'naver_blog_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = ColoredFormatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ===========================
# 설정 영역
# ===========================

# Naver Open API 설정
NAVER_CLIENT_ID = "9v7cOolOk2ctSQXc73sd"
NAVER_CLIENT_SECRET = "9jHcXVNQwZ"

# 검색 키워드 (PM International 관련)
SEARCH_KEYWORDS = [
    "피엠인터내셔널",
    "피엠코리아", 
    "PM인터내셔널",
    "독일피엠",
    "핏라인",
    "FitLine",
    "베이식스",
    "프로셰이프",
    "엑티바이즈",
    "파워칵테일",
    "리스토레이트"
]

# PM 관련 필수 키워드 (최소 1개 이상 포함)
PM_REQUIRED_KEYWORDS = [
    "피엠", "PM", "pm", "핏라인", "fitline", "FitLine", 
    "팀파트너", "독일피엠", "피엠코리아", "피엠인터내셔널"
]

# 제외 키워드
EXCLUDE_KEYWORDS = [
    "채용", "구인", "구직", "알바", "아르바이트",
    "사기", "피해", "환불", "소송", "사칭"
]

# API 검색 설정
DISPLAY_PER_PAGE = 100
MAX_PAGES = 1
TOTAL_TARGET = 100

# Selenium 설정
SELENIUM_WAIT_TIME = 10
PAGE_LOAD_WAIT = 2  # 3초 → 2초로 단축 (속도 개선)
PAGE_LOAD_TIMEOUT = 15  # 페이지 로딩 최대 대기 시간
MAX_RETRY = 3  # 최대 재시도 횟수

# 요청 간 딜레이 (초)
REQUEST_DELAY_MIN = 1.5
REQUEST_DELAY_MAX = 3.5

# User-Agent
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]

# ===========================
# 통계 클래스
# ===========================

class CrawlingStats:
    """크롤링 통계 관리 클래스"""
    
    def __init__(self):
        self.total_attempts = 0
        self.success_count = 0
        self.fail_count = 0
        self.filtered_out = 0
        self.duplicate_count = 0
        self.start_time = time.time()
    
    def add_attempt(self):
        self.total_attempts += 1
    
    def add_success(self):
        self.success_count += 1
    
    def add_fail(self):
        self.fail_count += 1
    
    def add_filtered(self):
        self.filtered_out += 1
    
    def add_duplicate(self):
        self.duplicate_count += 1
    
    def get_success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return (self.success_count / self.total_attempts) * 100
    
    def get_elapsed_time(self) -> str:
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes}분 {seconds}초"
    
    def print_stats(self):
        logger.info("=" * 70)
        logger.info("📊 크롤링 통계")
        logger.info("=" * 70)
        logger.info(f"총 시도: {self.total_attempts}개")
        logger.info(f"✅ 성공: {self.success_count}개")
        logger.info(f"❌ 실패: {self.fail_count}개")
        logger.info(f"🚫 필터링: {self.filtered_out}개")
        logger.info(f"🔁 중복: {self.duplicate_count}개")
        logger.info(f"📈 성공률: {self.get_success_rate():.1f}%")
        logger.info(f"⏱️  소요 시간: {self.get_elapsed_time()}")
        logger.info("=" * 70)

# 전역 통계 객체
stats = CrawlingStats()

# ===========================
# Selenium 드라이버 초기화
# ===========================

def init_selenium_driver() -> webdriver.Chrome:
    """Selenium Chrome 드라이버 초기화"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 이미지 로딩 비활성화 (속도 향상)
    prefs = {'profile.managed_default_content_settings.images': 2}
    chrome_options.add_experimental_option('prefs', prefs)
    
    # Homebrew chromedriver 우선 사용 (macOS 보안 문제 해결)
    homebrew_chromedriver = '/opt/homebrew/bin/chromedriver'
    
    if os.path.exists(homebrew_chromedriver):
        service = Service(homebrew_chromedriver)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # 페이지 로딩 타임아웃 설정 (속도 개선)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    logger.info("✅ Selenium 드라이버 초기화 완료")
    return driver

# ===========================
# API 검색 함수
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
        logger.error(f"API 요청 실패 - 키워드: {keyword}, 에러: {str(e)}")
        return None

# ===========================
# URL 파싱 및 정규화
# ===========================

def extract_blog_info_from_url(url: str) -> Optional[Dict[str, str]]:
    """블로그 URL에서 blog_id와 post_id 추출"""
    try:
        url = unquote(url)
        parsed = urlparse(url)
        
        # 패턴 1: blog.naver.com/{blog_id}/{post_id}
        match = re.search(r'blog\.naver\.com/([^/]+)/(\d+)', url)
        if match:
            return {'blog_id': match.group(1), 'post_id': match.group(2)}
        
        # 패턴 2: PostView.nhn?blogId={blog_id}&logNo={post_id}
        if 'PostView' in url:
            query_params = parse_qs(parsed.query)
            blog_id = query_params.get('blogId', [None])[0]
            post_id = query_params.get('logNo', [None])[0]
            if blog_id and post_id:
                return {'blog_id': blog_id, 'post_id': post_id}
        
        # 패턴 3: m.blog.naver.com/{blog_id}/{post_id}
        match = re.search(r'm\.blog\.naver\.com/([^/]+)/(\d+)', url)
        if match:
            return {'blog_id': match.group(1), 'post_id': match.group(2)}
        
        return None
        
    except Exception as e:
        logger.error(f"URL 파싱 오류: {url}, {str(e)}")
        return None

def normalize_blog_url(blog_id: str, post_id: str) -> str:
    """정규화된 블로그 URL 생성"""
    return f"https://blog.naver.com/{blog_id}/{post_id}"

# ===========================
# 콘텐츠 필터링
# ===========================

def is_pm_related_content(title: str, content: str) -> bool:
    """제목 및 본문이 PM International 관련 내용인지 확인"""
    combined_text = f"{title} {content}".lower()
    
    # 제외 키워드 체크
    for exclude_kw in EXCLUDE_KEYWORDS:
        if exclude_kw.lower() in combined_text:
            logger.debug(f"제외 키워드 발견: {exclude_kw}")
            return False
    
    # PM 필수 키워드 체크
    has_required = any(kw.lower() in combined_text for kw in PM_REQUIRED_KEYWORDS)
    
    if not has_required:
        logger.debug("PM 필수 키워드 미포함")
        return False
    
    return True

# ===========================
# 데이터 추출 함수들
# ===========================

def extract_blog_name(driver: webdriver.Chrome) -> str:
    """블로그명 추출 (다중 선택자 시도)"""
    selectors = [
        "div.blog_title a",
        "div.blog2_series a.link",
        "h1.blog_title",
        "div.tit_area h3.tit",
        "div.blog_title_area a",
        "a.blog_name",
        "div.nick_area a.nick"
    ]
    
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            blog_name = element.text.strip()
            if blog_name and len(blog_name) > 0:
                logger.debug(f"블로그명 추출 성공: {blog_name}")
                return blog_name
        except NoSuchElementException:
            continue
    
    # 메타 태그 시도
    try:
        og_title = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
        content = og_title.get_attribute('content')
        if content and ' : ' in content:
            return content.split(' : ')[0].strip()
        elif content:
            return content.strip()
    except NoSuchElementException:
        pass
    
    # 페이지 타이틀
    title = driver.title
    if ' : ' in title:
        return title.split(' : ')[0].strip()
    
    logger.warning("블로그명 추출 실패")
    return "알 수 없음"

def extract_view_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """조회수 추출 (다중 선택자 시도)"""
    selectors = [
        'span.se_publishDate.pcol2 em',  # 스마트에디터 ONE
        'span.pcol2 em',
        'span.cnt_view',
        'span.view',
        'em.cnt',
        'span.count',
        'div.blog_post_view_info span.num'
    ]
    
    # Selenium 시도
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                # "조회 123" 또는 "123" 형태
                match = re.search(r'(\d[\d,]*)', text)
                if match:
                    count = int(match.group(1).replace(',', ''))
                    logger.debug(f"조회수 추출: {count}")
                    return count
        except Exception:
            continue
    
    # BeautifulSoup 시도
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text(strip=True)
            match = re.search(r'(\d[\d,]*)', text)
            if match:
                count = int(match.group(1).replace(',', ''))
                logger.debug(f"조회수 추출 (BS): {count}")
                return count
    
    # 텍스트 검색 (마지막 수단)
    page_text = soup.get_text()
    match = re.search(r'조회[:\s]*(\d[\d,]*)', page_text)
    if match:
        count = int(match.group(1).replace(',', ''))
        logger.debug(f"조회수 추출 (텍스트): {count}")
        return count
    
    logger.debug("조회수 추출 실패")
    return 0

def extract_like_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """좋아요(공감) 수 추출"""
    selectors = [
        'span.u_cnt._count',  # 공감 버튼
        'span.cnt_like',
        'em.u_cnt',
        'span.like_count',
        'a.btn_empathy span.u_cnt',
        'div.end_btn span.u_cnt'
    ]
    
    # Selenium 시도
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                match = re.search(r'(\d[\d,]*)', text)
                if match:
                    count = int(match.group(1).replace(',', ''))
                    logger.debug(f"좋아요수 추출: {count}")
                    return count
        except Exception:
            continue
    
    # BeautifulSoup 시도
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text(strip=True)
            match = re.search(r'(\d[\d,]*)', text)
            if match:
                count = int(match.group(1).replace(',', ''))
                logger.debug(f"좋아요수 추출 (BS): {count}")
                return count
    
    # 텍스트 검색
    page_text = soup.get_text()
    match = re.search(r'공감[:\s]*(\d[\d,]*)', page_text)
    if match:
        count = int(match.group(1).replace(',', ''))
        logger.debug(f"좋아요수 추출 (텍스트): {count}")
        return count
    
    logger.debug("좋아요수 추출 실패")
    return 0

def extract_comment_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """댓글 수 추출"""
    selectors = [
        'span.u_cnt._count.ccmtcnt',  # 댓글 버튼
        'span.cnt_cmt',
        'em.u_cmt',
        'span.comment_count',
        'a.btn_comment span.u_cnt',
        'div.end_btn span.u_cnt'
    ]
    
    # Selenium 시도
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                text = elem.text.strip()
                match = re.search(r'(\d[\d,]*)', text)
                if match:
                    count = int(match.group(1).replace(',', ''))
                    logger.debug(f"댓글수 추출: {count}")
                    return count
        except Exception:
            continue
    
    # BeautifulSoup 시도
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text(strip=True)
            match = re.search(r'(\d[\d,]*)', text)
            if match:
                count = int(match.group(1).replace(',', ''))
                logger.debug(f"댓글수 추출 (BS): {count}")
                return count
    
    # 텍스트 검색
    page_text = soup.get_text()
    match = re.search(r'댓글[:\s]*(\d[\d,]*)', page_text)
    if match:
        count = int(match.group(1).replace(',', ''))
        logger.debug(f"댓글수 추출 (텍스트): {count}")
        return count
    
    logger.debug("댓글수 추출 실패")
    return 0

def extract_hashtags(driver: webdriver.Chrome, soup: BeautifulSoup, content: str) -> List[str]:
    """해시태그 추출 (3단계)"""
    hashtags = set()
    
    # 1. 하단 태그 영역
    tag_selectors = [
        "div.post_tag a.link",
        "div.blog2_series a.link",
        "div.tag_area a",
        "div.post_bottom_area a.link",
        "a[href*='/PostList.naver?tag=']"
    ]
    
    for selector in tag_selectors:
        try:
            tag_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in tag_elements:
                tag_text = elem.text.strip()
                if tag_text:
                    hashtags.add(tag_text.lstrip('#'))
        except Exception:
            continue
    
    # 2. 본문 내 #해시태그
    hash_pattern = re.findall(r'#([^\s#]+)', content)
    hashtags.update(hash_pattern)
    
    # 3. 메타데이터
    try:
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords['content'].split(',')
            hashtags.update([k.strip() for k in keywords if k.strip()])
    except Exception:
        pass
    
    result = sorted(list(hashtags))[:20]
    logger.debug(f"해시태그 추출: {len(result)}개")
    return result

def extract_media_urls(driver: webdriver.Chrome, soup: BeautifulSoup) -> Tuple[List[str], List[str]]:
    """이미지 및 비디오 URL 추출"""
    image_urls = []
    video_urls = []
    
    try:
        # 동적 콘텐츠 로딩 대기
        time.sleep(2)
        
        # 이미지 추출
        img_selectors = [
            "div.se-main-container img",
            "div#postViewArea img",
            "div.se-component-content img",
            "div.post_ct img",
            "div.__se_component_area img"
        ]
        
        for selector in img_selectors:
            try:
                img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for img in img_elements:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and src.startswith('http'):
                        # 썸네일 → 원본
                        if 'type=w' in src:
                            src = re.sub(r'type=w\d+', 'type=w966', src)
                        image_urls.append(src)
            except Exception:
                continue
        
        # 비디오 추출
        video_selectors = [
            "div.se-main-container video",
            "div#postViewArea video",
            "div.se-component-content video"
        ]
        
        for selector in video_selectors:
            try:
                video_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for video in video_elements:
                    src = video.get_attribute('src') or video.get_attribute('data-src')
                    if src and src.startswith('http'):
                        video_urls.append(src)
            except Exception:
                continue
        
        # 중복 제거
        image_urls = list(dict.fromkeys(image_urls))[:10]
        video_urls = list(dict.fromkeys(video_urls))[:5]
        
        logger.debug(f"미디어 추출: 이미지 {len(image_urls)}개, 비디오 {len(video_urls)}개")
        return image_urls, video_urls
        
    except Exception as e:
        logger.error(f"미디어 URL 추출 실패: {str(e)}")
        return [], []

def parse_date(date_str: str) -> Optional[str]:
    """날짜 문자열 파싱"""
    try:
        date_str = re.sub(r'[^\d\-\.\s:]', '', date_str).strip()
        
        patterns = [
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{1,2})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})',
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                if len(groups) == 5:
                    year, month, day, hour, minute = groups
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute.zfill(2)}:00"
                else:
                    year, month, day = groups
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)} 00:00:00"
        
        return None
        
    except Exception as e:
        logger.error(f"날짜 파싱 오류: {date_str}, {str(e)}")
        return None

# ===========================
# 데이터 검증
# ===========================

def validate_post_data(post_data: Dict) -> bool:
    """수집된 게시물 데이터 유효성 검증"""
    required_fields = ['post_id', 'blog_id', 'url', 'title', 'content']
    
    for field in required_fields:
        if not post_data.get(field):
            logger.warning(f"필수 필드 누락: {field}")
            return False
    
    # 제목 길이 체크
    if len(post_data['title']) < 2:
        logger.warning(f"제목이 너무 짧음: {post_data['title']}")
        return False
    
    # 본문 길이 체크
    if len(post_data['content']) < 50:
        logger.warning(f"본문이 너무 짧음: {len(post_data['content'])}자")
        return False
    
    return True

# ===========================
# 재시도 로직
# ===========================

def retry_with_backoff(func, *args, **kwargs):
    """지수 백오프를 사용한 재시도"""
    for attempt in range(MAX_RETRY):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < MAX_RETRY - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"재시도 {attempt + 1}/{MAX_RETRY}: {wait_time:.1f}초 대기 - {str(e)}")
                time.sleep(wait_time)
            else:
                logger.error(f"최종 실패: {str(e)}")
                raise

# ===========================
# 메인 크롤링 함수
# ===========================

def crawl_blog_post_selenium(driver: webdriver.Chrome, url: str, blog_id: str, post_id: str, 
                             failed_url_manager=None) -> Optional[Dict]:
    """Selenium을 사용하여 블로그 게시물 크롤링 (재시도 포함)"""
    
    def _crawl():
        logger.debug(f"크롤링 시작: {url}")
        driver.get(url)
        time.sleep(PAGE_LOAD_WAIT)
        
        # iframe 처리
        try:
            WebDriverWait(driver, SELENIUM_WAIT_TIME).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
            )
            logger.debug("mainFrame 전환 완료")
        except TimeoutException:
            logger.debug("mainFrame 없음 - 메인 페이지 크롤링")
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 블로그명
        referrer_name = extract_blog_name(driver)
        
        # 제목
        title_selectors = [
            'div.se-title-text',
            'div.pcol1 span.se-fs-',
            'div#viewTypeSelector span.se-fs-',
            'h3.se-title-text',
            'span.pcol1.itemSubjectBoldfont'
        ]
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                title = title_elem.get_text(strip=True)
                break
        
        if not title:
            logger.warning(f"제목 없음: {url}")
            title = "제목 없음"
        
        # 본문
        content_selectors = [
            'div.se-main-container',
            'div#postViewArea',
            'div.se-component-content'
        ]
        content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(separator='\n', strip=True)
                break
        
        if not content:
            logger.warning(f"본문 없음: {url}")
            return None
        
        # PM 필터링
        if not is_pm_related_content(title, content):
            logger.debug(f"PM 무관: {title}")
            stats.add_filtered()
            return None
        
        # 발행일
        published_date = None
        date_selectors = [
            'span.se_publishDate',
            'span.se-publishDate',
            'div.se_publishDate',
            'span.post_date',
            'p.date'
        ]
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_date = parse_date(date_text)
                break
        
        # 조회수, 좋아요수, 댓글수 추출
        view_count = extract_view_count(driver, soup)
        like_count = extract_like_count(driver, soup)
        comment_count = extract_comment_count(driver, soup)
        
        # 해시태그
        hashtags = extract_hashtags(driver, soup, content)
        
        # 미디어 URL
        image_urls, video_urls = extract_media_urls(driver, soup)
        
        # 결과 구성
        post_data = {
            'post_id': post_id,
            'blog_id': blog_id,
            'url': url,
            'title': title,
            'content': content[:5000],
            'published_date': published_date,
            'referrer_name': referrer_name,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'hashtags': ', '.join(hashtags) if hashtags else '',
            'image_urls': json.dumps(image_urls, ensure_ascii=False) if image_urls else '',
            'video_urls': json.dumps(video_urls, ensure_ascii=False) if video_urls else '',
            'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 데이터 검증
        if not validate_post_data(post_data):
            logger.warning(f"데이터 검증 실패: {title}")
            return None
        
        logger.info(f"✅ 크롤링 완료: {title[:30]}... (조회:{view_count}, 좋아요:{like_count}, 댓글:{comment_count})")
        return post_data
    
    # 재시도 로직 적용
    stats.add_attempt()
    try:
        result = retry_with_backoff(_crawl)
        if result:
            stats.add_success()
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"크롤링 최종 실패: {url}, {error_msg}")
        stats.add_fail()
        
        # 실패 URL 기록
        if failed_url_manager:
            failed_url_manager.add_failed_url(url, error_msg, blog_id, post_id)
        
        return None
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

# ===========================
# 중복 체크
# ===========================

def generate_post_fingerprint(post_data: Dict) -> str:
    """게시물 고유 지문 생성 (URL + 제목 + 작성자)"""
    return f"{post_data['url']}_{post_data['title']}_{post_data['blog_id']}"

# ===========================
# 에러 게시물 관리
# ===========================

class FailedURLManager:
    """실패한 URL 관리 클래스"""
    
    def __init__(self, filename='failed_urls.json'):
        self.filename = filename
        self.failed_urls = []
    
    def add_failed_url(self, url: str, reason: str, blog_id: str = '', post_id: str = ''):
        """실패한 URL 추가"""
        self.failed_urls.append({
            'url': url,
            'blog_id': blog_id,
            'post_id': post_id,
            'reason': reason,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def save_to_file(self):
        """실패한 URL을 파일에 저장"""
        if self.failed_urls:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.failed_urls, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 실패 URL 저장: {self.filename} ({len(self.failed_urls)}개)")
    
    def get_failed_count(self) -> int:
        return len(self.failed_urls)

# ===========================
# 메인 함수
# ===========================

def main():
    """메인 실행 함수"""
    logger.info("=" * 70)
    logger.info("🚀 PM-International Korea 네이버 블로그 크롤러 v6.6 시작")
    logger.info("=" * 70)
    
    driver = init_selenium_driver()
    failed_url_manager = FailedURLManager()
    
    collected_posts = []
    collected_urls = set()
    collected_fingerprints = set()
    
    try:
        for keyword in SEARCH_KEYWORDS:
            logger.info(f"\n🔍 키워드 검색: '{keyword}'")
            
            for page in range(1, MAX_PAGES + 1):
                start = (page - 1) * DISPLAY_PER_PAGE + 1
                logger.info(f"📄 페이지 {page} 검색 중... (start={start})")
                
                search_result = search_naver_blog(keyword, DISPLAY_PER_PAGE, start)
                
                if not search_result or 'items' not in search_result:
                    logger.warning(f"검색 결과 없음")
                    break
                
                items = search_result['items']
                logger.info(f"📋 검색 결과: {len(items)}개")
                
                if len(items) == 0:
                    break
                
                for idx, item in enumerate(items, 1):
                    if len(collected_posts) >= TOTAL_TARGET:
                        logger.info(f"🎯 목표 달성: {TOTAL_TARGET}개")
                        break
                    
                    link = item.get('link', '')
                    if not link or link in collected_urls:
                        stats.add_duplicate()
                        continue
                    
                    blog_info = extract_blog_info_from_url(link)
                    if not blog_info:
                        continue
                    
                    blog_id = blog_info['blog_id']
                    post_id = blog_info['post_id']
                    normalized_url = normalize_blog_url(blog_id, post_id)
                    
                    if normalized_url in collected_urls:
                        stats.add_duplicate()
                        continue
                    
                    logger.info(f"[{len(collected_posts)+1}/{TOTAL_TARGET}] 크롤링 중...")
                    
                    post_data = crawl_blog_post_selenium(driver, normalized_url, blog_id, post_id, failed_url_manager)
                    
                    if post_data:
                        fingerprint = generate_post_fingerprint(post_data)
                        if fingerprint not in collected_fingerprints:
                            collected_posts.append(post_data)
                            collected_urls.add(normalized_url)
                            collected_fingerprints.add(fingerprint)
                        else:
                            logger.debug("중복 게시물 (fingerprint)")
                            stats.add_duplicate()
                    
                    time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
                
                if len(collected_posts) >= TOTAL_TARGET:
                    break
                
                time.sleep(random.uniform(2, 4))
            
            if len(collected_posts) >= TOTAL_TARGET:
                break
        
        # 통계 출력
        stats.print_stats()
        
        # 결과 저장
        if collected_posts:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'naver_blog_test_{timestamp}.csv'
            
            df = pd.DataFrame(collected_posts)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            logger.info(f"\n{'=' * 70}")
            logger.info(f"💾 저장 완료: {filename}")
            logger.info(f"📊 총 수집: {len(collected_posts)}개")
            logger.info(f"{'=' * 70}")
        else:
            logger.warning("⚠️  수집된 게시물이 없습니다.")
        
        # 실패 URL 저장
        failed_url_manager.save_to_file()
        if failed_url_manager.get_failed_count() > 0:
            logger.info(f"❌ 실패한 URL: {failed_url_manager.get_failed_count()}개 (failed_urls.json 참조)")
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  사용자 중단")
        stats.print_stats()
    
    except Exception as e:
        logger.error(f"❌ 예기치 않은 오류: {str(e)}")
        stats.print_stats()
    
    finally:
        driver.quit()
        logger.info("✅ 드라이버 종료")

if __name__ == "__main__":
    main()
