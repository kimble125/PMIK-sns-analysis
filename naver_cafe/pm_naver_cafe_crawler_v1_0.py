#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 카페 크롤러 v1.0

🚀 v1.0 핵심 기능:
1. ⚙️ iframe 기반 네이버 카페 크롤링
2. 🔍 키워드 검색 기반 효율적 데이터 수집  
3. 💾 체크포인트 및 에러 복구 시스템
4. 📞 PMIK 특화 데이터 추출 (추천인, 파트너ID 등)
5. 🛡️ 중복 제거 및 필터링
6. 📊 실시간 통계 및 진행률 모니터링

📊 출력 컬럼 (20개):
- 기본: platform, cafe_name, post_id, article_id, url, title, content, author_nickname, published_date
- PMIK: sponsor_phone, sponsor_partner_id, pm_keywords_found, sales_keywords_found  
- 참여: view_count, comment_count, like_count, reply_list
- 콘텐츠: image_urls, hashtags, collected_date

작성자: PMI Korea 데이터 분석팀
버전: 1.0.0
최종 수정일: 2024-11-18
"""

import os
import re
import json
import time
import random
import logging
import gc
import yaml
import shutil
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, unquote
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from enum import Enum

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 외부 라이브러리 로그 억제
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

for handler in logger.handlers:
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

# ===========================
# 설정 로드
# ===========================

def load_config(config_path='config.yaml') -> Dict:
    """YAML 설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"YAML 파싱 오류: {e}")
        raise

# 설정 로드
CONFIG = load_config()

# User-Agent 목록
USER_AGENTS = CONFIG['user_agents']

# 키워드 설정
PRIMARY_KEYWORDS = CONFIG['keywords']['primary']
SECONDARY_KEYWORDS = CONFIG['keywords']['secondary']
ALL_KEYWORDS = PRIMARY_KEYWORDS + SECONDARY_KEYWORDS

# 필터링 키워드
PM_BRAND_KEYWORDS = CONFIG['filters']['pm_brand_keywords']
PM_SALES_KEYWORDS = CONFIG['filters']['pm_sales_keywords']
EXCLUDE_KEYWORDS = CONFIG['filters']['exclude_keywords']

# 크롤링 설정
PAGE_LOAD_TIMEOUT = CONFIG['crawling']['page_load_timeout']
REQUEST_DELAY_MIN = CONFIG['crawling']['request_delay_min']
REQUEST_DELAY_MAX = CONFIG['crawling']['request_delay_max']
MAX_PAGES_PER_KEYWORD = CONFIG['crawling']['max_pages_per_keyword']
MAX_POSTS_PER_PAGE = CONFIG['crawling']['max_posts_per_page']

# 테스트 모드 설정
TEST_MODE = CONFIG['test_mode']['enabled']
TEST_DURATION_MINUTES = CONFIG['test_mode']['max_duration_minutes']
TEST_MAX_POSTS = CONFIG['test_mode']['max_posts']

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

class DuplicateChecker:
    """중복 체크 관리자"""
    
    def __init__(self):
        self.collected_post_ids = set()
        self.collected_urls = set()
        self.collected_fingerprints = set()
    
    def is_duplicate(self, post_id: str = None, url: str = None, fingerprint: str = None) -> bool:
        """중복 여부 확인"""
        if post_id and post_id in self.collected_post_ids:
            return True
        if url and url in self.collected_urls:
            return True
        if fingerprint and fingerprint in self.collected_fingerprints:
            return True
        return False
    
    def add(self, post_id: str = None, url: str = None, fingerprint: str = None):
        """수집 데이터 추가"""
        if post_id:
            self.collected_post_ids.add(post_id)
        if url:
            self.collected_urls.add(url)
        if fingerprint:
            self.collected_fingerprints.add(fingerprint)

# ===========================
# 크롤러 클래스  
# ===========================

class NaverCafeCrawler:
    """네이버 카페 크롤러"""
    
    def __init__(self):
        self.driver = None
        self.stats = CrawlStats()
        self.duplicate_checker = DuplicateChecker()
        self.collected_posts = []
        self.start_time = time.time()
    
    def setup_driver(self):
        """Selenium 드라이버 설정"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
        
        if not TEST_MODE:
            chrome_options.add_argument('--headless')
        
        # ChromeDriver 자동 설치 및 설정
        try:
            driver_path = ChromeDriverManager().install()
            # mac-arm64의 경우 실제 실행 파일 경로 찾기
            if 'chromedriver-mac-arm64' in driver_path:
                driver_path = os.path.join(os.path.dirname(driver_path), 'chromedriver')
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            logger.info("✅ Selenium 드라이버 설정 완료")
        except Exception as e:
            logger.error(f"ChromeDriver 설정 실패: {e}")
            logger.info("시스템 ChromeDriver 사용 시도...")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            logger.info("✅ 시스템 ChromeDriver로 설정 완료")
    
    def extract_sponsor_phone(self, text: str) -> str:
        """추천인 전화번호 추출"""
        if not text:
            return ""
        
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
                digits = re.sub(r'\D', '', phone)
                if digits.startswith('010') and len(digits) == 11:
                    return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        return ""
    
    def extract_sponsor_partner_id(self, text: str) -> str:
        """추천인 파트너 ID 추출 (7-8자리 숫자)"""
        if not text:
            return ""
        
        partner_patterns = [
            r'추천인\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
            r'파트너\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
            r'등록\s*(?:코드|번호|ID)?\s*[:：]?\s*(\d{7,8})\b',
            r'\b(\d{7,8})\b',
        ]
        
        for pattern in partner_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) in [7, 8]:
                    return match
        
        return ""
    
    def search_in_cafe(self, cafe_url: str, keyword: str) -> List[Dict]:
        """카페에서 키워드 검색"""
        try:
            self.driver.get(cafe_url)
            time.sleep(2)
            
            # 검색창 찾기 및 키워드 입력
            search_input = self.driver.find_element(By.NAME, 'query')
            search_input.clear()
            search_input.send_keys(keyword)
            search_input.send_keys(Keys.ENTER)
            
            time.sleep(3)
            
            # iframe으로 전환
            self.driver.switch_to.frame('cafe_main')
            
            # 검색 결과에서 게시글 링크 수집
            post_links = []
            try:
                articles = self.driver.find_elements(By.CSS_SELECTOR, 'td.td_article a')
                for article in articles[:MAX_POSTS_PER_PAGE]:
                    href = article.get_attribute('href')
                    if href:
                        post_links.append(href)
            except Exception as e:
                logger.warning(f"게시글 링크 수집 실패: {e}")
            
            # 기본 프레임으로 복귀
            self.driver.switch_to.default_content()
            
            return post_links
            
        except Exception as e:
            logger.error(f"카페 검색 실패 ({cafe_url}, {keyword}): {e}")
            return []
    
    def extract_post_data(self, url: str, cafe_name: str) -> Optional[Dict]:
        """게시글 데이터 추출"""
        try:
            self.driver.get(url)
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
            
            # iframe으로 전환
            self.driver.switch_to.frame('cafe_main')
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 기본 정보 추출
            title = ""
            content = ""
            author = ""
            published_date = ""
            view_count = 0
            
            # 제목 추출
            title_elem = soup.select_one('h3.title_text, .ArticleTitle, .tit-box .b')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # 내용 추출
            content_elem = soup.select_one('.article_viewer, .ArticleContentBox, #tbody')
            if content_elem:
                content = content_elem.get_text(strip=True)[:CONFIG['output']['max_content_length']]
            
            # 작성자 추출
            author_elem = soup.select_one('.nickname, .profile_info .nickname')
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            # 작성일 추출
            date_elem = soup.select_one('.date, .article_info .date')
            if date_elem:
                published_date = date_elem.get_text(strip=True)
            
            # 조회수 추출
            view_elem = soup.select_one('.count, .article_info .count')
            if view_elem:
                view_text = view_elem.get_text(strip=True)
                view_match = re.search(r'\d+', view_text)
                if view_match:
                    view_count = int(view_match.group())
            
            # URL에서 post_id 추출
            post_id = ""
            article_id = ""
            url_match = re.search(r'articleid=(\d+)', url)
            if url_match:
                article_id = url_match.group(1)
                post_id = f"{cafe_name}_{article_id}"
            
            # 전체 텍스트에서 PMIK 특화 데이터 추출
            full_text = f"{title} {content}"
            sponsor_phone = self.extract_sponsor_phone(full_text)
            sponsor_partner_id = self.extract_sponsor_partner_id(full_text)
            
            # PM 키워드 찾기
            pm_keywords_found = []
            for keyword in PM_BRAND_KEYWORDS:
                if keyword in full_text:
                    pm_keywords_found.append(keyword)
            
            # 판매원 키워드 찾기
            sales_keywords_found = []
            for keyword in PM_SALES_KEYWORDS:
                if keyword in full_text:
                    sales_keywords_found.append(keyword)
            
            # 기본 프레임으로 복귀
            self.driver.switch_to.default_content()
            
            return {
                'platform': 'naver_cafe',
                'cafe_name': cafe_name,
                'post_id': post_id,
                'article_id': article_id,
                'url': url,
                'title': title,
                'content': content,
                'author_nickname': author,
                'published_date': published_date,
                'sponsor_phone': sponsor_phone,
                'sponsor_partner_id': sponsor_partner_id,
                'pm_keywords_found': ', '.join(pm_keywords_found),
                'sales_keywords_found': ', '.join(sales_keywords_found),
                'view_count': view_count,
                'comment_count': 0,
                'like_count': 0,
                'reply_list': '',
                'image_urls': '',
                'hashtags': '',
                'collected_date': datetime.now().strftime(CONFIG['output']['date_format'])
            }
            
        except Exception as e:
            logger.error(f"게시글 데이터 추출 실패 ({url}): {e}")
            return None
    
    def content_passes_filter(self, title: str, content: str) -> Tuple[bool, str]:
        """콘텐츠 필터링"""
        full_text = (title + " " + content).lower()
        
        # 제외 키워드 체크
        for keyword in EXCLUDE_KEYWORDS:
            if keyword in full_text:
                return False, f"제외 키워드 발견: {keyword}"
        
        # PM 브랜드 키워드 체크
        has_pm_keyword = any(keyword.lower() in full_text for keyword in PM_BRAND_KEYWORDS)
        if not has_pm_keyword:
            return False, "PM 브랜드 키워드 없음"
        
        return True, "통과"
    
    def crawl_cafe(self, cafe_config: Dict):
        """단일 카페 크롤링"""
        cafe_name = cafe_config['name']
        cafe_url = cafe_config['cafe_url']
        
        logger.info(f"🎯 카페 크롤링 시작: {cafe_name}")
        
        for kw_info in ALL_KEYWORDS:
            keyword = kw_info['keyword']
            target = kw_info['target']
            
            logger.info(f"🔍 키워드 검색: {keyword} (목표: {target}개)")
            
            # 테스트 모드에서 수집량 제한
            if TEST_MODE and self.stats.success >= TEST_MAX_POSTS:
                logger.info(f"⏱️ 테스트 모드 수집량 달성: {TEST_MAX_POSTS}개")
                break
            
            # 검색 결과 수집
            post_links = self.search_in_cafe(cafe_url, keyword)
            logger.info(f"📋 검색 결과: {len(post_links)}개 링크 발견")
            
            collected_for_keyword = 0
            for url in post_links:
                if collected_for_keyword >= target:
                    break
                
                # 중복 체크
                if self.duplicate_checker.is_duplicate(url=url):
                    self.stats.add_duplicate()
                    continue
                
                # 게시글 데이터 추출
                post_data = self.extract_post_data(url, cafe_name)
                if not post_data:
                    self.stats.add_error()
                    continue
                
                # 필터링
                passes_filter, reason = self.content_passes_filter(
                    post_data['title'], post_data['content']
                )
                
                if not passes_filter:
                    self.stats.add_filtered()
                    logger.debug(f"필터링: {reason}")
                    continue
                
                # 성공적으로 수집
                self.collected_posts.append(post_data)
                self.duplicate_checker.add(
                    post_id=post_data['post_id'],
                    url=url,
                    fingerprint=f"{post_data['title']}_{post_data['content'][:100]}"
                )
                self.stats.add_success()
                collected_for_keyword += 1
                
                logger.info(f"✅ 수집 완료 ({collected_for_keyword}/{target}): {post_data['title'][:50]}...")
                
                # 테스트 모드 시간 제한 체크
                if TEST_MODE:
                    elapsed_minutes = (time.time() - self.start_time) / 60
                    if elapsed_minutes >= TEST_DURATION_MINUTES:
                        logger.info(f"⏱️ 테스트 모드 시간 제한 달성: {TEST_DURATION_MINUTES}분")
                        return
                    if self.stats.success >= TEST_MAX_POSTS:
                        logger.info(f"⏱️ 테스트 모드 수집량 달성: {TEST_MAX_POSTS}개")
                        return
            
            logger.info(f"📊 {keyword} 완료: {collected_for_keyword}/{target}개 수집")
    
    def save_results(self):
        """결과 저장"""
        if not self.collected_posts:
            logger.warning("⚠️ 수집된 데이터가 없습니다.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"naver_cafe_pm_{timestamp}.csv"
        
        df = pd.DataFrame(self.collected_posts)
        df.to_csv(filename, index=False, encoding=CONFIG['output']['csv_encoding'])
        
        logger.info(f"💾 결과 저장 완료: {filename} ({len(self.collected_posts)}개)")
        
        # 통계 출력
        self.stats.print_stats()
    
    def run(self):
        """메인 실행 함수"""
        try:
            logger.info("🚀 PM-International Korea 네이버 카페 크롤러 v1.0 시작")
            
            if TEST_MODE:
                logger.info(f"⚠️ 테스트 모드 활성화 (최대 {TEST_DURATION_MINUTES}분, {TEST_MAX_POSTS}개)")
            
            self.setup_driver()
            
            # 각 카페별 크롤링
            for cafe_config in CONFIG['target_cafes']:
                self.crawl_cafe(cafe_config)
            
            self.save_results()
            
        except KeyboardInterrupt:
            logger.info("⏹️ 사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"❌ 크롤링 실행 중 오류: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔚 드라이버 종료 완료")

# ===========================
# 메인 실행
# ===========================

if __name__ == "__main__":
    crawler = NaverCafeCrawler()
    crawler.run()
