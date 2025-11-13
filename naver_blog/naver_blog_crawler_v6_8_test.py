#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 블로그 크롤러 v6.8 (최종 개선판)

🔧 주요 개선 사항:
1. ✅ published_date: API postdate 활용 (v5 방식 복원)
2. ✅ blogger_name: sponsor_name과 통합 (추천인 정보 우선, 없으면 블로거명)
3. ✅ hashtags: 페이지 소스 전체 검색으로 개선
4. ✅ 이미지 로딩 비활성화 (속도 향상)
5. ✅ 재시도 로직 최적화 (3회→2회, 대기시간 단축)
6. ✅ post_id: 게시물 고유 ID (키값으로 사용 가능)
7. ⚠️  view_count: 네이버 블로그에 조회수 미표시로 컬럼 제거
8. ⚠️  image_urls: 네이버 Referer 정책으로 외부 접근 제한 (향후 OCR 처리 필요)

출력 컬럼 (16개):
- 기본: platform, post_id, blog_id, url, title, content, published_date
- 작성자: blogger_name (추천인 우선, 없으면 블로거명)
- 추천인: sponsor_phone, sponsor_partner_id
- 참여: like_count, comment_count (조회수 제외)
- 콘텐츠: hashtags, image_urls, video_urls
- 메타: collected_date
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

# Naver Open API 설정 (from config.py)
NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET

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
MAX_RETRY = 2  # 최대 재시도 횟수 (1회 시도 + 1회 재시도)

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

def extract_blogger_name(driver: webdriver.Chrome) -> str:
    """블로그 운영자 이름 추출 (2-4자 한글 이름만)"""
    selectors = [
        "div.blog_title a",
        "div.blog2_series a.link",
        "h1.blog_title",
        "div.tit_area h3.tit",
        "div.blog_title_area a",
        "a.blog_name",
        "div.nick_area a.nick",
        "div.blog_info a.blog_id",
        "span.nick",
        "a.NPI=a:blog.title"
    ]
    
    # 제외할 일반 단어들
    exclude_words = ['블로그', '마케팅', '뉴스', '공식', '사업', '코리아', '인터내셔널', 
                     '코드', '으로', '에서', '에게', '부터', '까지', '문의', '연락', '점']
    
    for selector in selectors:
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
            blog_name = element.text.strip()
            
            # 2-4자 한글 이름 추출 시도
            if blog_name:
                # 공백으로 분리하여 각 단어 검사
                words = blog_name.split()
                for word in words:
                    # 2-4자 한글만 (숫자, 영문, 특수문자 제외)
                    if re.match(r'^[가-힣]{2,4}$', word):
                        # 제외 단어가 아닌 경우
                        if not any(ex in word for ex in exclude_words):
                            logger.debug(f"블로거 이름 추출: {word}")
                            return word
        except NoSuchElementException:
            continue
    
    # 메타 태그 시도
    try:
        og_title = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
        content = og_title.get_attribute('content')
        if content:
            # 2-4자 한글 추출
            names = re.findall(r'[가-힣]{2,4}', content)
            for name in names:
                if not any(ex in name for ex in exclude_words):
                    logger.debug(f"블로거 이름 추출 (메타): {name}")
                    return name
    except NoSuchElementException:
        pass
    
    # 페이지 타이틀
    title = driver.title
    if title:
        names = re.findall(r'[가-힣]{2,4}', title)
        for name in names:
            if not any(ex in name for ex in exclude_words):
                logger.debug(f"블로거 이름 추출 (타이틀): {name}")
                return name
    
    logger.debug("블로거 이름 추출 실패")
    return ""

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
    """댓글수 추출"""
    selectors = [
        'span.u_cnt_comment',
        'span.cnt_cmt',
        'em.comment_count',
        'span.comment_count',
        'a.btn_cmt span.u_cnt'
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

def extract_sponsor_info(content: str) -> Dict[str, str]:
    """추천인 정보 추출 (이름, 전화번호, 파트너번호)"""
    name_patterns = [
        r'(?:추천인|추천|소개|문의)[:\s]*\(?([가-힣]{2,4})\)?',
        r'PM\s*(?:파트너|매니저)[:\s]*([가-힣]{2,4})',
        r'(?:연락처|전화)[:\s]*([가-힣]{2,4})\s*[0-9-]'
    ]
    phone_patterns = [
        r'(?:연락처|전화|문의|☎|📞)[:\s]*([0-9]{2,3}[-\s]?[0-9]{3,4}[-\s]?[0-9]{4})',
        r'(01[016789][-\s]?[0-9]{3,4}[-\s]?[0-9]{4})'
    ]
    partner_patterns = [
        r'(?:파트너\s*번호|파트너|회원\s*번호|번호)[:\s]*([0-9]{7,9})',
        r'(?:추천|소개)\s*번호[:\s]*([0-9]{7,9})'
    ]
    
    result = {'name': '', 'phone': '', 'partner_id': ''}
    
    for pattern in name_patterns:
        match = re.search(pattern, content)
        if match:
            name = match.group(1)
            if re.match(r'^[가-힣]{2,4}$', name) and name not in ['코드', '으로', '에서', '에게', '부터', '까지', '문의', '연락']:
                result['name'] = name
                break
    
    for pattern in phone_patterns:
        match = re.search(pattern, content)
        if match:
            phone = re.sub(r'[^0-9]', '', match.group(0))
            if len(phone) in [10, 11]:
                result['phone'] = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}" if len(phone) == 11 else f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                break
    
    for pattern in partner_patterns:
        match = re.search(pattern, content)
        if match:
            number = match.group(1)
            if number.isdigit() and 7 <= len(number) <= 9:
                result['partner_id'] = number
                break
    
    return result

def extract_hashtags(driver: webdriver.Chrome, soup: BeautifulSoup, content: str) -> List[str]:
    """해시태그 추출 - 우선순위: 태그영역 > 본문 > 메타데이터"""
    hashtags = set()
    
    # 1. 하단 태그 영역 (가장 신뢰도 높음)
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
                    if not tag_text.startswith('#'):
                        tag_text = '#' + tag_text
                    hashtags.add(tag_text)
        except Exception:
            continue
    
    # 2. 본문 텍스트에서 해시태그 추출 (태그 영역에서 못 찾은 경우만)
    if len(hashtags) < 5:  # 태그가 5개 미만이면 본문에서 추가 검색
        # 본문에서 # 패턴 추출
        hash_in_content = re.findall(r'#([가-힣a-zA-Z0-9_]+)', content)
        for tag in hash_in_content:
            if len(tag) >= 2 and len(tag) <= 20:  # 2~20자 사이
                hashtags.add('#' + tag)
    
    # 3. 메타데이터 (태그가 거의 없는 경우만)
    if len(hashtags) < 3:
        try:
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                keywords = meta_keywords['content'].split(',')
                for k in keywords:
                    k = k.strip()
                    if k and 2 <= len(k) <= 20:
                        if not k.startswith('#'):
                            k = '#' + k
                        hashtags.add(k)
        except Exception:
            pass
    
    # 중복 제거 및 정렬 (제한 없음)
    result = sorted(list(hashtags))
    if result:
        logger.debug(f"해시태그 추출: {len(result)}개 - {result[:3]}...")
    else:
        logger.debug("해시태그 없음")
    return result

def extract_media_urls(driver: webdriver.Chrome, soup: BeautifulSoup) -> Tuple[List[str], List[str]]:
    """이미지 및 비디오 URL 추출
    
    ⚠️ 주의: 수집된 이미지 URL은 네이버의 보안 정책상 외부에서 직접 접근 시 404 에러가 발생할 수 있습니다.
    이는 크롤러의 문제가 아니라 네이버가 Referer 헤더를 체크하거나 세션 토큰을 요구하기 때문입니다.
    실제 이미지를 다운로드하려면 브라우저 세션을 유지하거나 적절한 헤더를 설정해야 합니다.
    """
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
    """재시도 로직 (빠른 실패)"""
    for attempt in range(MAX_RETRY):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < MAX_RETRY - 1:
                wait_time = 1.0 + random.uniform(0, 0.5)  # 1~1.5초만 대기
                logger.warning(f"재시도 {attempt + 1}/{MAX_RETRY}: {wait_time:.1f}초 대기 - {str(e)[:50]}")
                time.sleep(wait_time)
            else:
                logger.error(f"최종 실패: {str(e)[:50]}")
                raise

# ===========================
# 메인 크롤링 함수
# ===========================

def crawl_blog_post_selenium(driver: webdriver.Chrome, url: str, blog_id: str, post_id: str, 
                             api_data: Dict = None, failed_url_manager=None) -> Optional[Dict]:
    """Selenium을 사용하여 블로그 게시물 크롤링 (재시도 포함) - 개선됨
    
    Args:
        api_data: API 검색 결과 데이터 (postdate, bloggername 등 포함)
    """
    
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
        
        # 본문 (content를 먼저 추출해야 함)
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
        
        # 블로거 이름 (API 데이터 우선, 없으면 페이지에서 추출)
        blogger_name = ''
        if api_data and api_data.get('bloggername'):
            blogger_name = api_data['bloggername']
        else:
            blogger_name = extract_blogger_name(driver)
        
        # 추천인 정보 추출 (본문에서)
        sponsor_info = extract_sponsor_info(content)
        # sponsor_name이 없으면 blogger_name 사용
        if not sponsor_info['name'] and blogger_name:
            sponsor_info['name'] = blogger_name
        
        # PM 필터링
        if not is_pm_related_content(title, content):
            logger.debug(f"PM 무관: {title}")
            stats.add_filtered()
            return None
        
        # 발행일: API 데이터 우선 사용 (v5 방식)
        published_date = ''
        if api_data and api_data.get('postdate'):
            # API postdate 형식: "20231219" -> "2023-12-19"
            postdate = api_data['postdate']
            if len(postdate) == 8:
                published_date = f"{postdate[:4]}-{postdate[4:6]}-{postdate[6:8]}"
                logger.debug(f"발행일 (API): {published_date}")
        
        # API 데이터가 없으면 페이지에서 추출 시도
        if not published_date:
            published_date = extract_published_date(driver, soup)
            if published_date:
                logger.debug(f"발행일 (페이지): {published_date}")
        
        # 좋아요수, 댓글수 추출 (조회수는 네이버 블로그에 표시 안됨)
        like_count = extract_like_count(driver, soup)
        comment_count = extract_comment_count(driver, soup)
        
        # 해시태그
        hashtags = extract_hashtags(driver, soup, content)
        
        # 미디어 URL
        image_urls, video_urls = extract_media_urls(driver, soup)
        
        # 결과 구성
        post_data = {
            'platform': 'Naver Blog',
            'post_id': post_id,  # 게시물 고유 ID (키값)
            'blog_id': blog_id,
            'url': url,
            'title': title,
            'content': content[:5000],
            'published_date': published_date,
            'blogger_name': sponsor_info['name'] if sponsor_info['name'] else blogger_name,  # 통합
            'sponsor_phone': sponsor_info['phone'],
            'sponsor_partner_id': sponsor_info['partner_id'],
            'like_count': like_count,
            'comment_count': comment_count,
            'hashtags': ', '.join(hashtags) if hashtags else '',
            'image_urls': '|'.join(image_urls) if image_urls else '',
            'video_urls': '|'.join(video_urls) if video_urls else '',
            'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 데이터 검증
        if not validate_post_data(post_data):
            logger.warning(f"데이터 검증 실패: {title}")
            return None
        
        logger.info(f"✅ 크롤링 완료: {title[:30]}... (좋아요:{like_count}, 댓글:{comment_count}, 해시태그:{len(hashtags)}개)")
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
    logger.info("🚀 PM-International Korea 네이버 블로그 크롤러 v6.7 시작")
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
                    
                    # API 데이터 전달 (postdate, bloggername 포함)
                    api_item_data = {
                        'postdate': item.get('postdate', ''),
                        'bloggername': item.get('bloggername', '')
                    }
                    
                    post_data = crawl_blog_post_selenium(driver, normalized_url, blog_id, post_id, api_item_data, failed_url_manager)
                    
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
            filename = f'naver_blog_fixed_{timestamp}.csv'
            
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
