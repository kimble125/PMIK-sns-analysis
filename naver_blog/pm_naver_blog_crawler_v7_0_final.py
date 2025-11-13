#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 블로그 크롤러 v7.0 (최종 완성판)

🎯 주요 개선 사항:
1. ✅ hashtags: 이전 버전의 간단하고 효과적인 로직으로 복원 (# 기호 유지)
2. ✅ blogger_name 삭제 → sponsor_name만 사용
3. ✅ view_count: 완전 삭제 (수집 불가능)
4. ✅ sponsor_phone, sponsor_partner_id: 패턴 대폭 강화
5. ✅ 안정성 및 속도 최적화

📊 출력 컬럼 (16개):
- 기본: platform, post_id, blog_id, url, title, content, published_date
- 추천인: sponsor_name, sponsor_phone, sponsor_partner_id
- 참여: like_count, comment_count
- 콘텐츠: hashtags, image_urls, video_urls
- 메타: collected_date

작성자: PMI Korea 데이터 분석팀
버전: 7.0
최종 수정일: 2025-11-05
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
    "피트라인",
    "FitLine",
    "베이식스",
    "베이직스",
    "프로셰이프",
    "프로쉐이프",
    "엑티바이즈",
    "파워칵테일",
    "리스토레이트",
    "탑쉐이프"
]

# PM 관련 필수 키워드 (최소 1개 이상 포함)
PM_REQUIRED_KEYWORDS = [
    "피엠", "PM", "피엠인터내셔널", "피엠코리아", "pm인터내셔널",
    "핏라인", "피트라인", "fitline", "FitLine",
    "탑쉐이프", "TopShape", "topshape",
    "독일피엠", "pmkorea", "pm코리아"
]

# 크롤링 설정
MAX_RESULTS_PER_KEYWORD = 20  # 키워드당 최대 수집 개수
TOTAL_TARGET = 100             # 전체 목표 수집 개수
REQUEST_DELAY_MIN = 2.0        # 최소 대기 시간 (초)
REQUEST_DELAY_MAX = 4.0        # 최대 대기 시간 (초)
MAX_RETRIES = 3                # 최대 재시도 횟수
PAGE_LOAD_TIMEOUT = 15         # 페이지 로딩 타임아웃 (초)
ELEMENT_WAIT_TIMEOUT = 10      # 요소 대기 타임아웃 (초)

# ===========================
# Selenium 드라이버 설정
# ===========================

def create_driver() -> webdriver.Chrome:
    """Selenium Chrome 드라이버 생성"""
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 이미지 로딩 비활성화 (속도 향상)
        prefs = {
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2
        }
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Homebrew chromedriver 우선 사용 (macOS Gatekeeper 문제 해결)
        homebrew_chromedriver = '/opt/homebrew/bin/chromedriver'
        
        if os.path.exists(homebrew_chromedriver):
            service = Service(homebrew_chromedriver)
            logger.info("✅ Homebrew ChromeDriver 사용")
        else:
            service = Service(ChromeDriverManager().install())
            logger.info("✅ webdriver-manager ChromeDriver 사용")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        
        logger.info("✅ Selenium 드라이버 생성 완료")
        return driver
        
    except Exception as e:
        logger.error(f"❌ 드라이버 생성 실패: {str(e)}")
        raise

# ===========================
# 유틸리티 함수
# ===========================

def normalize_blog_url(blog_id: str, post_id: str) -> str:
    """블로그 URL 정규화"""
    return f"https://blog.naver.com/{blog_id}/{post_id}"

def extract_blog_info(url: str) -> Optional[Dict[str, str]]:
    """
    URL에서 blog_id와 post_id 추출
    
    Args:
        url: 네이버 블로그 URL
        
    Returns:
        {'blog_id': str, 'post_id': str} 또는 None
    """
    try:
        # 정규 URL: https://blog.naver.com/blog_id/post_id
        pattern1 = r'blog\.naver\.com/([^/]+)/(\d+)'
        match = re.search(pattern1, url)
        
        if match:
            return {
                'blog_id': match.group(1),
                'post_id': match.group(2)
            }
        
        # 쿼리 파라미터 방식
        parsed = urlparse(url)
        if 'blog.naver.com' in parsed.netloc:
            query = parse_qs(parsed.query)
            if 'blogId' in query and 'logNo' in query:
                return {
                    'blog_id': query['blogId'][0],
                    'post_id': query['logNo'][0]
                }
        
        return None
        
    except Exception as e:
        logger.debug(f"URL 파싱 실패: {url}, {str(e)}")
        return None

def parse_date(date_str: str) -> Optional[str]:
    """
    날짜 문자열 파싱 및 표준화
    
    Args:
        date_str: 날짜 문자열
        
    Returns:
        'YYYY-MM-DD HH:MM:SS' 형식 또는 None
    """
    try:
        date_str = date_str.strip()
        
        # 패턴 1: "2024. 11. 5. 14:30"
        pattern1 = r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{1,2}):(\d{2})'
        match = re.search(pattern1, date_str)
        if match:
            year, month, day, hour, minute = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)} {hour.zfill(2)}:{minute}:00"
        
        # 패턴 2: "2024.11.05"
        pattern2 = r'(\d{4})\.(\d{1,2})\.(\d{1,2})'
        match = re.search(pattern2, date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)} 00:00:00"
        
        # 패턴 3: "11. 5." (올해)
        pattern3 = r'(\d{1,2})\.\s*(\d{1,2})\.'
        match = re.search(pattern3, date_str)
        if match:
            month, day = match.groups()
            year = datetime.now().year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)} 00:00:00"
        
        return None
        
    except Exception as e:
        logger.debug(f"날짜 파싱 실패: {date_str}, {str(e)}")
        return None

def extract_sponsor_info(text: str) -> Dict[str, Optional[str]]:
    """
    추천인 정보 추출 (sponsor_name, sponsor_phone, sponsor_partner_id)
    
    Args:
        text: 게시물 본문
        
    Returns:
        {'sponsor_name': str, 'sponsor_phone': str, 'sponsor_partner_id': str}
    """
    result = {
        'sponsor_name': None,
        'sponsor_phone': None,
        'sponsor_partner_id': None
    }
    
    if not text:
        return result
    
    # sponsor_name 추출 패턴 (강화)
    name_patterns = [
        r'(?:추천인|후원인|스폰서|추천|referrer|sponsor)[\s:：]*([가-힣]{2,4})',
        r'(?:문의|연락|상담)[\s:：]*([가-힣]{2,4})',
        r'([가-힣]{2,4})[\s]*(?:팀파트너|파트너|님)',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['sponsor_name'] = match.group(1).strip()
            break
    
    # sponsor_phone 추출 패턴 (대폭 강화)
    phone_patterns = [
        r'(?:010|011|016|017|018|019)[-\s]*\d{3,4}[-\s]*\d{4}',  # 010-1234-5678
        r'(?:010|011|016|017|018|019)\d{7,8}',                    # 01012345678
        r'\d{2,3}[-\s]*\d{3,4}[-\s]*\d{4}',                       # 02-123-4567
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            # 전화번호 정규화 (하이픈 추가)
            phone = re.sub(r'[^\d]', '', phone)
            if len(phone) == 11:
                result['sponsor_phone'] = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
            elif len(phone) == 10:
                if phone.startswith('02'):
                    result['sponsor_phone'] = f"{phone[:2]}-{phone[2:6]}-{phone[6:]}"
                else:
                    result['sponsor_phone'] = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
            else:
                result['sponsor_phone'] = phone
            break
    
    # sponsor_partner_id 추출 패턴 (강화)
    partner_id_patterns = [
        r'(?:파트너\s*ID|추천인\s*ID|ID)[\s:：]*([A-Za-z0-9]+)',
        r'(?:추천인\s*번호|파트너\s*번호)[\s:：]*(\d+)',
        r'ID[\s:：]*([A-Za-z0-9]{4,20})',
    ]
    
    for pattern in partner_id_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['sponsor_partner_id'] = match.group(1).strip()
            break
    
    return result

def extract_hashtags(text: str, soup: BeautifulSoup = None) -> str:
    """
    해시태그 추출 (이전 버전의 간단하고 효과적인 로직 복원)
    
    Args:
        text: 게시물 본문
        soup: BeautifulSoup 객체 (선택)
        
    Returns:
        쉼표로 구분된 해시태그 문자열 (# 기호 포함)
    """
    hashtags = set()
    
    if not text:
        return ""
    
    # 방법 1: 본문에서 #해시태그 패턴 추출 (가장 효과적)
    # 한글, 영어, 숫자를 모두 지원하며 공백이나 특수문자 전까지 추출
    pattern = r'#([가-힣a-zA-Z0-9_]+)'
    matches = re.findall(pattern, text)
    
    for match in matches:
        # # 기호를 유지하여 저장
        hashtags.add(f"#{match}")
    
    # 방법 2: soup가 있으면 태그 영역에서 추출
    if soup:
        # 네이버 블로그 태그 영역 선택자
        tag_selectors = [
            'div.post_tag a.link___',
            'div.post-tag a',
            'span.se-fs- a',
            'div.tag_list a',
            'a[href*="/search/"]'
        ]
        
        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for tag in tag_elements:
                tag_text = tag.get_text().strip()
                if tag_text:
                    # 태그 영역에서는 # 없이 나오므로 추가
                    if not tag_text.startswith('#'):
                        tag_text = f"#{tag_text}"
                    hashtags.add(tag_text)
    
    # 리스트로 변환 후 쉼표로 결합
    return ','.join(sorted(hashtags))

def is_pm_related(title: str, content: str) -> bool:
    """
    PM International 관련 게시물 여부 확인
    
    Args:
        title: 제목
        content: 본문
        
    Returns:
        True if PM 관련, False otherwise
    """
    combined_text = f"{title} {content}".lower()
    
    for keyword in PM_REQUIRED_KEYWORDS:
        if keyword.lower() in combined_text:
            return True
    
    return False

def generate_post_fingerprint(post_data: Dict) -> str:
    """
    게시물 지문 생성 (중복 검사용)
    
    Args:
        post_data: 게시물 데이터
        
    Returns:
        지문 문자열
    """
    title = post_data.get('title', '')
    blog_id = post_data.get('blog_id', '')
    post_id = post_data.get('post_id', '')
    
    return f"{blog_id}_{post_id}_{title[:50]}"

# ===========================
# Naver API 함수
# ===========================

def search_naver_blogs(keyword: str, display: int = 100, start: int = 1) -> List[Dict]:
    """
    Naver Open API로 블로그 검색
    
    Args:
        keyword: 검색 키워드
        display: 결과 개수 (최대 100)
        start: 시작 위치
        
    Returns:
        블로그 URL 리스트
    """
    try:
        url = "https://openapi.naver.com/v1/search/blog.json"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        params = {
            "query": keyword,
            "display": min(display, 100),
            "start": start,
            "sort": "date"  # 최신순 정렬
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        logger.info(f"✅ '{keyword}' 검색 완료: {len(items)}개 발견")
        return items
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API 요청 실패 ({keyword}): {str(e)}")
        return []
    except Exception as e:
        logger.error(f"❌ 예기치 않은 오류 ({keyword}): {str(e)}")
        return []

# ===========================
# 크롤링 함수
# ===========================

def crawl_blog_post_selenium(
    driver: webdriver.Chrome,
    url: str,
    blog_id: str,
    post_id: str,
    failed_url_manager: 'FailedURLManager'
) -> Optional[Dict]:
    """
    Selenium으로 블로그 게시물 크롤링
    
    Args:
        driver: Selenium 드라이버
        url: 블로그 URL
        blog_id: 블로그 ID
        post_id: 포스트 ID
        failed_url_manager: 실패 URL 관리자
        
    Returns:
        게시물 데이터 딕셔너리 또는 None
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver.get(url)
            time.sleep(2)  # 페이지 로딩 대기
            
            # iframe으로 전환
            try:
                iframe = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "mainFrame"))
                )
                driver.switch_to.frame(iframe)
            except TimeoutException:
                logger.debug(f"iframe 없음 (시도 {attempt}/{MAX_RETRIES})")
            
            # BeautifulSoup로 파싱
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # 1. 제목 추출
            title_selectors = [
                'div.se-title-text',
                'div.pcol1 h3.se_textarea',
                'h3.se_textarea',
                'span.se-fs-',
                'div.se-module-text h3'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    if title:
                        break
            
            if not title:
                logger.debug(f"제목 없음: {url}")
                driver.switch_to.default_content()
                if attempt == MAX_RETRIES:
                    failed_url_manager.add_failed_url(url, blog_id, post_id, "제목 추출 실패")
                continue
            
            # 2. 본문 추출
            content_selectors = [
                'div.se-main-container',
                'div.se-component',
                'div#postViewArea',
                'div.post-view'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(separator=' ', strip=True)
                    if content:
                        break
            
            # 3. PM 관련 여부 확인
            if not is_pm_related(title, content):
                logger.debug(f"PM 관련 없음: {title[:30]}")
                driver.switch_to.default_content()
                return None
            
            # 4. 발행일 추출
            published_date = None
            date_selectors = [
                'span.se_publishDate',
                'span.date',
                'span.se-ff-nanummyeongjo span',
                'p.date',
                'div.post_date',
                'span.blog2_series'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text().strip()
                    published_date = parse_date(date_text)
                    if published_date:
                        break
            
            # 5. 추천인 정보 추출
            sponsor_info = extract_sponsor_info(content)
            
            # 6. 좋아요 수 추출
            like_count = 0
            like_selectors = [
                'em.u_cnt._count',
                'span.u_cnt',
                'em.cnt_like',
                'span.like_count'
            ]
            
            for selector in like_selectors:
                like_elem = soup.select_one(selector)
                if like_elem:
                    like_text = like_elem.get_text().strip()
                    try:
                        like_count = int(re.sub(r'[^\d]', '', like_text))
                        if like_count > 0:
                            break
                    except (ValueError, AttributeError):
                        pass
            
            # 7. 댓글 수 추출
            comment_count = 0
            comment_selectors = [
                'span.u_cnt._count',
                'span.num_cmt',
                'em.cnt_cmt',
                'span.comment_count'
            ]
            
            for selector in comment_selectors:
                comment_elem = soup.select_one(selector)
                if comment_elem:
                    comment_text = comment_elem.get_text().strip()
                    try:
                        comment_count = int(re.sub(r'[^\d]', '', comment_text))
                        if comment_count > 0:
                            break
                    except (ValueError, AttributeError):
                        pass
            
            # 8. 해시태그 추출
            hashtags = extract_hashtags(content, soup)
            
            # 9. 이미지 URL 추출
            image_urls = []
            img_elements = soup.select('img.se-image-resource')
            for img in img_elements:
                img_url = img.get('data-lazy-src') or img.get('src')
                if img_url and img_url.startswith('http'):
                    image_urls.append(img_url)
            
            # 10. 동영상 URL 추출
            video_urls = []
            video_elements = soup.select('div.se-video')
            for video in video_elements:
                video_url = video.get('data-src') or video.get('src')
                if video_url and video_url.startswith('http'):
                    video_urls.append(video_url)
            
            # 데이터 구성
            post_data = {
                'platform': 'naver_blog',
                'post_id': f"{blog_id}_{post_id}",
                'blog_id': blog_id,
                'url': url,
                'title': title,
                'content': content[:5000],  # 5000자 제한
                'published_date': published_date,
                'sponsor_name': sponsor_info['sponsor_name'],
                'sponsor_phone': sponsor_info['sponsor_phone'],
                'sponsor_partner_id': sponsor_info['sponsor_partner_id'],
                'like_count': like_count,
                'comment_count': comment_count,
                'hashtags': hashtags,
                'image_urls': json.dumps(image_urls, ensure_ascii=False),
                'video_urls': json.dumps(video_urls, ensure_ascii=False),
                'collected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.debug(f"✅ 크롤링 성공: {title[:30]}")
            driver.switch_to.default_content()
            return post_data
            
        except TimeoutException as e:
            logger.warning(f"⏱️  타임아웃 (시도 {attempt}/{MAX_RETRIES}): {url}")
            driver.switch_to.default_content()
            if attempt == MAX_RETRIES:
                failed_url_manager.add_failed_url(url, blog_id, post_id, f"TimeoutException: {str(e)}")
        
        except WebDriverException as e:
            logger.warning(f"🌐 WebDriver 오류 (시도 {attempt}/{MAX_RETRIES}): {str(e)}")
            driver.switch_to.default_content()
            if attempt == MAX_RETRIES:
                failed_url_manager.add_failed_url(url, blog_id, post_id, f"WebDriverException: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ 예기치 않은 오류 (시도 {attempt}/{MAX_RETRIES}): {str(e)}")
            driver.switch_to.default_content()
            if attempt == MAX_RETRIES:
                failed_url_manager.add_failed_url(url, blog_id, post_id, f"Exception: {str(e)}")
        
        # 재시도 전 대기 (지수 백오프)
        if attempt < MAX_RETRIES:
            wait_time = 2 ** attempt
            time.sleep(wait_time)
    
    return None

# ===========================
# 실패 URL 관리
# ===========================

class FailedURLManager:
    """실패한 URL 관리 클래스"""
    
    def __init__(self, filename: str = "failed_urls.json"):
        self.filename = filename
        self.failed_urls = []
    
    def add_failed_url(self, url: str, blog_id: str, post_id: str, reason: str):
        """실패 URL 추가"""
        self.failed_urls.append({
            'url': url,
            'blog_id': blog_id,
            'post_id': post_id,
            'reason': reason,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def save_to_file(self):
        """JSON 파일로 저장"""
        if self.failed_urls:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.failed_urls, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 실패 URL 저장: {self.filename} ({len(self.failed_urls)}개)")
    
    def get_failed_count(self) -> int:
        """실패 URL 개수 반환"""
        return len(self.failed_urls)

# ===========================
# 통계 클래스
# ===========================

class CrawlingStats:
    """크롤링 통계 관리 클래스"""
    
    def __init__(self):
        self.total_attempted = 0
        self.success_count = 0
        self.failed_count = 0
        self.filtered_count = 0
        self.duplicate_count = 0
        self.start_time = time.time()
    
    def add_success(self):
        self.total_attempted += 1
        self.success_count += 1
    
    def add_failed(self):
        self.total_attempted += 1
        self.failed_count += 1
    
    def add_filtered(self):
        self.total_attempted += 1
        self.filtered_count += 1
    
    def add_duplicate(self):
        self.total_attempted += 1
        self.duplicate_count += 1
    
    def print_stats(self):
        """통계 출력"""
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        success_rate = (self.success_count / self.total_attempted * 100) if self.total_attempted > 0 else 0
        
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 크롤링 통계")
        logger.info(f"{'='*70}")
        logger.info(f"총 시도: {self.total_attempted}개")
        logger.info(f"✅ 성공: {self.success_count}개 ({success_rate:.1f}%)")
        logger.info(f"❌ 실패: {self.failed_count}개")
        logger.info(f"🚫 필터링: {self.filtered_count}개 (PM 관련 없음)")
        logger.info(f"🔁 중복: {self.duplicate_count}개")
        logger.info(f"⏱️  소요 시간: {minutes}분 {seconds}초")
        logger.info(f"{'='*70}\n")

# ===========================
# 메인 함수
# ===========================

def main():
    """메인 실행 함수"""
    logger.info(f"\n{'='*70}")
    logger.info(f"🚀 PM-International Korea 네이버 블로그 크롤러 v7.0")
    logger.info(f"{'='*70}\n")
    
    driver = create_driver()
    failed_url_manager = FailedURLManager()
    stats = CrawlingStats()
    
    collected_posts = []
    collected_urls = set()
    collected_fingerprints = set()
    
    try:
        for keyword in SEARCH_KEYWORDS:
            if len(collected_posts) >= TOTAL_TARGET:
                break
            
            logger.info(f"\n🔍 키워드: '{keyword}' 검색 중...")
            
            # API로 URL 목록 수집
            blog_items = search_naver_blogs(keyword, display=MAX_RESULTS_PER_KEYWORD)
            
            if not blog_items:
                continue
            
            for item in blog_items:
                if len(collected_posts) >= TOTAL_TARGET:
                    break
                
                blog_url = item.get('link', '')
                
                # URL에서 blog_id, post_id 추출
                blog_info = extract_blog_info(blog_url)
                if not blog_info:
                    continue
                
                blog_id = blog_info['blog_id']
                post_id = blog_info['post_id']
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
                        logger.info(f"✅ 수집 완료: {post_data['title'][:50]}")
                    else:
                        stats.add_duplicate()
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
            filename = f'naver_blog_pm_{timestamp}.csv'
            
            df = pd.DataFrame(collected_posts)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            logger.info(f"\n{'='*70}")
            logger.info(f"💾 저장 완료: {filename}")
            logger.info(f"📊 총 수집: {len(collected_posts)}개")
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
        stats.print_stats()
    
    finally:
        driver.quit()
        logger.info("✅ 드라이버 종료")

if __name__ == "__main__":
    main()
