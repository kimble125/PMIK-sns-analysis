#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International Korea 네이버 블로그 크롤러 v10.4 (Test 버전)

🔄 v10.4 Changes (from v10.3.1):
1. Profile URL 버그 수정 (ProfileOf.nhn으로 정정)
2. OCR 라이브러리 PaddleOCR로 교체
3. 연도 확장을 모든 키워드에 적용
4. 콘텐츠 타입 분류기 제거 (analysis/content_type_classifier.py로 이동)
5. 배제된 데이터 수집 시스템 추가
6. 시간대 한국 시간(KST)으로 고정
7. 리포트 시스템 개선 (단일 파일에 누적)
8. API 요청 제한 100개 (⚠️ TEST 버전 전용)

상세 변경사항: CHANGELOG_naver_blog.md 참조

작성자: PMI Korea 데이터 분석팀
버전: 10.4.0
최종 수정일: 2025-11-26
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
import traceback
import signal
import atexit
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, unquote
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from enum import Enum
from collections import defaultdict, Counter

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
import numpy as np

# v10.4: PaddleOCR로 교체 (한국어 인식 성능 향상)
try:
    from paddleocr import PaddleOCR
    from PIL import Image, ImageEnhance
    from io import BytesIO
    OCR_AVAILABLE = True
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    IMAGE_PROCESSING_AVAILABLE = False
    print("⚠️  PaddleOCR 또는 PIL을 설치하지 않았습니다. OCR 기능이 비활성화됩니다.")
    print("설치: pip install paddlepaddle paddleocr pillow")

# ===========================
# 설정 로드
# ===========================

def load_config(config_path: str = "config.yaml") -> Dict:
    """YAML 설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"⚠️  설정 파일을 찾을 수 없습니다: {config_path}")
        return {}
    except Exception as e:
        print(f"⚠️  설정 파일 로드 실패: {e}")
        return {}

# 설정 로드
CONFIG = load_config()

# ===========================
# v10.4: 시간 제한 설정 (5시간) - 장시간 테스트
# ===========================
MAX_DURATION_SECONDS = 5 * 60 * 60  # 5시간 = 18000초

# v10.4: 한국 시간(KST) 사용
import pytz
KST = pytz.timezone('Asia/Seoul')
START_TIME = time.time()

def check_time_limit():
    """시간 제한 확인"""
    elapsed = time.time() - START_TIME
    if elapsed >= MAX_DURATION_SECONDS:
        return True
    return False

# ===========================
# 환경 변수 및 전역 설정
# ===========================

# Naver API 키 (v10.3.1: config.py 우선, 환경 변수 폴백)
# 주의: logger 정의 전이므로 print 사용
try:
    import config
    NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
    NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET
    print("✅ config.py에서 Naver API 키 로드 완료")
except (ImportError, AttributeError) as e:
    NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')
    NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')
    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        print("✅ 환경 변수에서 Naver API 키 로드 완료")
    else:
        print("⚠️  Naver API 키가 설정되지 않았습니다.")

# v10.4: 키워드당 수집량 증가 (100→1000)
MAX_SEARCH_RESULTS = CONFIG.get('targets', {}).get('max_search_results', 1000)
TARGET_KEYWORDS = {
    'primary': ['피엠인터내셔널', '독일피엠', 'PM인터내셔널', '피엠코리아'],
    'secondary': ['피트라인', '탑쉐이프', '프로쉐이프', '디드링크', '뮤노겐', '엑티바이즈', '파워칵테일'],
    'product_test': ['레스토레이트']
}

# v10.4: 연도 확장을 모든 키워드에 적용 (중복 필터링이 있어 문제없음)
YEARS = list(range(2018, 2026))  # 2018-2025

# 딜레이 설정 (v10.4: 타임아웃 증가)
PAGE_LOAD_TIMEOUT = CONFIG.get('crawling', {}).get('page_load_timeout', 15)  # 10→15초
MIN_DELAY = CONFIG.get('crawling', {}).get('request_delay_min', 1.5)
MAX_DELAY = CONFIG.get('crawling', {}).get('request_delay_max', 2.5)

# User-Agent 목록
USER_AGENTS = CONFIG.get('user_agents', [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
])

# PM 브랜드 키워드
PM_BRAND_KEYWORDS = CONFIG.get('filters', {}).get('pm_brand_keywords', [])
PM_BRAND_KEYWORDS_EXTENDED = PM_BRAND_KEYWORDS

# 제품 키워드
PRODUCT_KEYWORDS = CONFIG.get('filters', {}).get('product_keywords', [])

# 판매원 키워드
PM_SALES_KEYWORDS = CONFIG.get('filters', {}).get('pm_sales_keywords', [])

# 제외 키워드
EXCLUDE_KEYWORDS = CONFIG.get('filters', {}).get('exclude_keywords', [])

# 제외 블로그 ID
EXCLUDED_BLOG_IDS = CONFIG.get('filters', {}).get('excluded_blog_ids', [])

# 언론 스타일 패턴
MEDIA_TITLE_PATTERNS = CONFIG.get('filters', {}).get('media_title_patterns', [])

# ===========================
# 로깅 설정
# ===========================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# v10.3.1: API 키 로드 상태 로깅
if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
    logger.info(f"✅ Naver API 키 로드 완료 (Client ID: {NAVER_CLIENT_ID[:10]}...)")
else:
    logger.warning("⚠️  Naver API 키가 설정되지 않았습니다.")

# ===========================
# v10.4: 콘텐츠 타입 분류기 제거됨
# ===========================
# 분석용 모듈로 분리: analysis/content_type_classifier.py
# 크롤러에서는 원시 데이터만 수집합니다.

# ===========================
# v10.4: PaddleOCR 기반 OCR 처리 시스템
# ===========================

class OCRProcessor:
    """이미지 OCR 처리 매니저 (v10.4: PaddleOCR로 교체)"""
    
    def __init__(self):
        """OCR 프로세서 초기화"""
        self.ocr_engine = None
        if OCR_AVAILABLE:
            try:
                logger.info("🔧 PaddleOCR 모델 초기화 중... (최초 1회, 1-2분 소요)")
                # v10.4: PaddleOCR - 한국어 인식 성능 향상
                # use_angle_cls=True: 회전된 텍스트도 인식
                # show_log=False: 불필요한 로그 숨김
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True, 
                    lang='korean',
                    use_gpu=True  # GPU 가용 시 자동 사용
                )
                logger.info("✅ PaddleOCR 초기화 완료")
            except Exception as e:
                logger.error(f"PaddleOCR 초기화 실패: {e}")
                # CPU 모드로 재시도
                try:
                    self.ocr_engine = PaddleOCR(
                        use_angle_cls=True, 
                        lang='korean',
                        use_gpu=False
                    )
                    logger.info("✅ PaddleOCR 초기화 완료 (CPU 모드)")
                except Exception as e2:
                    logger.error(f"PaddleOCR CPU 모드 초기화도 실패: {e2}")
                    self.ocr_engine = None
    
    def download_image(self, url: str, timeout: int = 15) -> Optional[str]:
        """이미지 다운로드 후 임시 파일 경로 반환 (v10.4: 파일 경로 반환)"""
        if not IMAGE_PROCESSING_AVAILABLE:
            return None
        
        try:
            # URL 정리 (네이버 이미지 URL 처리)
            url = url.strip()
            if url.startswith('//'):
                url = 'https:' + url
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': 'https://blog.naver.com/',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # 임시 파일로 저장 (PaddleOCR는 파일 경로 선호)
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name
                
        except Exception as e:
            logger.debug(f"이미지 다운로드 실패 ({url[:50]}...): {e}")
            return None
    
    def perform_ocr(self, image_path: str) -> Tuple[str, float]:
        """OCR 수행 (v10.4: PaddleOCR)"""
        if not self.ocr_engine:
            return "", 0.0
        
        try:
            result = self.ocr_engine.ocr(image_path, cls=True)
            
            if not result or result[0] is None:
                return "", 0.0
            
            # 텍스트 추출 및 신뢰도 계산
            extracted_texts = []
            confidences = []
            
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                
                # 신뢰도 0.6 이상인 텍스트만 수집 (노이즈 제거)
                if confidence > 0.6:
                    extracted_texts.append(text)
                    confidences.append(confidence)
            
            combined_text = ' '.join(extracted_texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return combined_text, avg_confidence
            
        except Exception as e:
            logger.debug(f"OCR 처리 실패: {e}")
            return "", 0.0
        finally:
            # 임시 파일 정리
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except:
                pass
    
    def process_image_urls(self, image_urls_str: str, max_images: int = 3) -> str:
        """이미지 URL 리스트를 OCR 처리 (v10.4: PaddleOCR)"""
        if not self.ocr_engine or not image_urls_str:
            return ""
        
        urls = [url.strip() for url in image_urls_str.split(',')][:max_images]
        all_ocr_texts = []
        
        logger.debug(f"OCR 시작: {len(urls)}개 이미지")
        
        for idx, url in enumerate(urls, 1):
            image_path = self.download_image(url)
            if image_path is not None:
                ocr_text, confidence = self.perform_ocr(image_path)
                if ocr_text:
                    all_ocr_texts.append(ocr_text)
                    logger.debug(f"  [{idx}/{len(urls)}] OCR 성공: {len(ocr_text)} chars, 신뢰도 {confidence:.2f}")
                else:
                    logger.debug(f"  [{idx}/{len(urls)}] OCR 실패: 텍스트 없음")
            else:
                logger.debug(f"  [{idx}/{len(urls)}] 이미지 다운로드 실패")
        
        result = ' | '.join(all_ocr_texts) if all_ocr_texts else ""
        logger.debug(f"OCR 완료: 총 {len(result)} chars")
        return result

# ===========================
# v9.1: 중복 체크 시스템
# ===========================

class DuplicateChecker:
    """중복 체크 관리자"""
    
    def __init__(self):
        self.collected_post_ids = set()
        self.collected_urls = set()
        self.collected_fingerprints = set()
        self.partner_id_stats = {'7자리': 0, '8자리': 0, '패턴_예시': []}
    
    def load_previous_data(self, csv_pattern: str = "naver_blog_pm_*.csv"):
        """이전 실행 결과 로드"""
        try:
            csv_files = list(Path('.').glob(csv_pattern))
            if not csv_files:
                logger.info("이전 실행 결과가 없습니다. 처음부터 시작합니다.")
                return
            
            latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
            df = pd.read_csv(latest_csv, encoding='utf-8-sig')
            
            self.collected_post_ids = set(df['post_id'].dropna().astype(str))
            self.collected_urls = set(df['url'].dropna())
            
            for _, row in df.iterrows():
                fingerprint = f"{row.get('title', '')}_{row.get('blog_id', '')}"
                self.collected_fingerprints.add(fingerprint)
            
            logger.info(f"✅ 이전 데이터 로드: {len(self.collected_post_ids)}개 게시물")
        except Exception as e:
            logger.warning(f"이전 데이터 로드 실패: {e}")
    
    def is_duplicate(self, post_id: str, url: str, title: str, blog_id: str) -> bool:
        """중복 여부 확인"""
        if post_id in self.collected_post_ids:
            return True
        if url in self.collected_urls:
            return True
        
        fingerprint = f"{title}_{blog_id}"
        if fingerprint in self.collected_fingerprints:
            return True
        
        return False
    
    def add(self, post_id: str, url: str, title: str, blog_id: str):
        """수집 완료 데이터 추가"""
        self.collected_post_ids.add(post_id)
        self.collected_urls.add(url)
        fingerprint = f"{title}_{blog_id}"
        self.collected_fingerprints.add(fingerprint)

# ===========================
# 실패 URL 관리자
# ===========================

class FailedURLManager:
    """실패한 URL 관리"""
    
    def __init__(self, json_path: str = "failed_urls.json"):
        self.json_path = json_path
        self.failed_urls = {}
        self.load()
    
    def load(self):
        """저장된 실패 URL 로드"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.failed_urls = json.load(f)
                logger.info(f"✅ 실패 URL 로드: {len(self.failed_urls)}개")
        except Exception as e:
            logger.warning(f"실패 URL 로드 실패: {e}")
    
    def save(self):
        """실패 URL 저장"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.failed_urls, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"실패 URL 저장 실패: {e}")
    
    def add_failed(self, url: str, reason: str):
        """실패 URL 추가"""
        self.failed_urls[url] = {
            'reason': reason,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def is_failed(self, url: str) -> bool:
        """이전에 실패한 URL인지 확인"""
        return url in self.failed_urls

# ===========================
# v10.4: 세션 로그 시스템 (이름 변경: VM → Session)
# ===========================

class SessionLoggingManager:
    """세션 작업 로그 관리 (v10.4: VM/로컬 모두 지원)"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        # v10.4: 한국 시간 사용
        self.start_time = datetime.now(KST)
        self.session_id = self.start_time.strftime('%Y%m%d_%H%M%S')
        self.session_log_path = self.log_dir / f"session_{self.session_id}.log"
        
        self.collected_count = 0
        self.filtered_count = 0
        self.duplicate_count = 0
        self.error_count = 0
        self.failed_posts = []
        
        self.write_session_start()
    
    def write_session_start(self):
        """세션 시작 로그"""
        with open(self.session_log_path, 'w', encoding='utf-8') as f:
            f.write(f"=== PM-International 네이버 블로그 크롤러 v10.4 ===\n")
            f.write(f"시작 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} (KST)\n")
            f.write(f"세션 ID: {self.session_id}\n\n")
    
    def log_failed_post(self, url: str, reason: str):
        """실패 게시물 기록"""
        self.failed_posts.append({
            'url': url,
            'reason': reason,
            'timestamp': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
        })
        self.error_count += 1
    
    def write_session_end(self, stats: Dict):
        """세션 종료 로그"""
        end_time = datetime.now(KST)
        duration = end_time - self.start_time
        
        with open(self.session_log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n=== 세션 종료 ===\n")
            f.write(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (KST)\n")
            f.write(f"실행 시간: {duration}\n\n")
            
            f.write(f"=== 수집 통계 ===\n")
            for key, value in stats.items():
                f.write(f"{key}: {value}\n")
            
            if self.failed_posts:
                f.write(f"\n=== 실패 게시물 ({len(self.failed_posts)}개) ===\n")
                for item in self.failed_posts[:20]:  # 최대 20개만
                    f.write(f"- {item['url']}\n")
                    f.write(f"  사유: {item['reason']}\n")
                    f.write(f"  시간: {item['timestamp']}\n\n")


# ===========================
# v10.4: 배제된 데이터 수집 시스템
# ===========================

class ExcludedDataManager:
    """배제된 게시물 데이터 관리 (필터링 검증용)"""
    
    def __init__(self, json_path: str = "data/excluded_posts.json"):
        self.json_path = Path(json_path)
        self.json_path.parent.mkdir(exist_ok=True)
        self.excluded_posts = []
        self.load()
    
    def load(self):
        """저장된 배제 데이터 로드"""
        try:
            if self.json_path.exists():
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.excluded_posts = json.load(f)
                logger.info(f"✅ 배제 데이터 로드: {len(self.excluded_posts)}개")
        except Exception as e:
            logger.warning(f"배제 데이터 로드 실패: {e}")
            self.excluded_posts = []
    
    def save(self):
        """배제 데이터 저장"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.excluded_posts, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 배제 데이터 저장: {len(self.excluded_posts)}개")
        except Exception as e:
            logger.error(f"배제 데이터 저장 실패: {e}")
    
    def add_excluded(self, url: str, title: str, blog_id: str, reason: str, 
                     matched_keywords: List[str] = None):
        """배제된 게시물 추가"""
        self.excluded_posts.append({
            'url': url,
            'title': title[:100] if title else '',
            'blog_id': blog_id,
            'reason': reason,
            'matched_keywords': matched_keywords or [],
            'timestamp': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def export_to_csv(self, csv_path: str = None):
        """배제 데이터를 CSV로 내보내기"""
        if not self.excluded_posts:
            return
        
        csv_path = csv_path or f"data/excluded_posts_{datetime.now(KST).strftime('%Y%m%d')}.csv"
        df = pd.DataFrame(self.excluded_posts)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"💾 배제 데이터 CSV 저장: {csv_path}")

# ===========================
# 텍스트 정제 함수
# ===========================

def clean_text(text: str) -> str:
    """텍스트 정제"""
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
    
    return text

# ===========================
# URL 파싱 함수
# ===========================

def extract_blog_info_from_url(url: str) -> Optional[Dict]:
    """URL에서 blog_id와 post_id 추출"""
    try:
        parsed = urlparse(url)
        
        if 'blog.naver.com' not in parsed.netloc:
            return None
        
        path_match = re.search(r'/([^/]+)/(\d+)', parsed.path)
        if path_match:
            blog_id = path_match.group(1)
            post_id = path_match.group(2)
            return {'blog_id': blog_id, 'post_id': post_id}
        
        query_params = parse_qs(parsed.query)
        blog_id = query_params.get('blogId', [None])[0]
        post_id = query_params.get('logNo', [None])[0]
        
        if blog_id and post_id:
            return {'blog_id': blog_id, 'post_id': post_id}
        
        return None
    except Exception as e:
        logger.debug(f"URL 파싱 실패 ({url}): {e}")
        return None

# ===========================
# v10.3: 향상된 프로필 정보 추출
# ===========================

def extract_profile_info(driver: webdriver.Chrome, soup: BeautifulSoup, blog_id: str) -> Dict:
    """블로거 프로필 정보 추출 (v10.3: 개선됨)"""
    profile_data = {
        'profile_nickname': '',
        'profile_intro': '',
        'blogger_member_id': '',
        'profile_url': ''
    }
    
    try:
        # iframe에서 복귀 (이미 복귀했을 수도 있음)
        try:
            driver.switch_to.default_content()
        except:
            pass
        
        # 프로필 페이지로 이동
        # v10.4: 버그 수정 - 정확한 URL: ProfileOf.nhn (이전 ProlieOf.nhn은 오타였음)
        profile_url = f"https://blog.naver.com/ProfileOf.nhn?blogId={blog_id}"
        logger.debug(f"프로필 페이지 이동: {profile_url}")
        
        driver.get(profile_url)
        
        # v10.3: 페이지 로딩 대기 시간 증가
        time.sleep(2)
        
        # v10.3: JavaScript 실행 대기
        driver.execute_script("return document.readyState") == "complete"
        
        # v10.3: 스크롤하여 콘텐츠 로딩
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # HTML 파싱
        soup_profile = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 닉네임 추출
        nickname_selectors = [
            '.nick_name', '.nickname', '.blog_name', 
            '.profile_name', 'h3.nick_name',
            '.blog-title', '.blogger-name'
        ]
        
        for selector in nickname_selectors:
            elem = soup_profile.select_one(selector)
            if elem:
                nickname = clean_text(elem.get_text())
                if nickname:
                    profile_data['profile_nickname'] = nickname
                    logger.debug(f"닉네임 수집: {nickname}")
                    break
        
        # v10.3: 소개글 추출 (더 많은 선택자)
        intro_selectors = [
            '.blog_intro', '.profile_intro', '.intro_text',
            '.blog_introduction', '.user_intro', 'p.intro',
            '.profile-intro', '.blogger-intro',
            '.se-text-paragraph',  # 스마트에디터
            '#nickNameArea + div',  # 닉네임 다음 div
            '.area_profile .intro'  # 프로필 영역의 소개
        ]
        
        intro_text = ''
        for selector in intro_selectors:
            elems = soup_profile.select(selector)
            for elem in elems:
                text = clean_text(elem.get_text())
                if text and len(text) > 10:  # 최소 10자 이상
                    intro_text = text
                    logger.debug(f"소개글 수집 ({selector}): {intro_text[:50]}...")
                    break
            if intro_text:
                break
        
        # v10.3: 선택자로 못 찾으면 전체 프로필 영역에서 추출
        if not intro_text:
            profile_areas = [
                '#content-area',
                '.profile_area',
                '.blog_1depth',
                '.profile-content',
                'body'  # 최후의 수단
            ]
            
            for area_selector in profile_areas:
                profile_area = soup_profile.select_one(area_selector)
                if profile_area:
                    # 모든 텍스트 추출
                    all_text = clean_text(profile_area.get_text())
                    
                    # "프로필" 또는 "소개" 이후의 텍스트 추출
                    patterns = [
                        r'소개\s*[:：]?\s*(.{10,200})',
                        r'프로필\s*[:：]?\s*(.{10,200})',
                        r'자기소개\s*[:：]?\s*(.{10,200})',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, all_text)
                        if match:
                            intro_text = match.group(1).strip()
                            logger.debug(f"소개글 수집 (패턴): {intro_text[:50]}...")
                            break
                    
                    if intro_text:
                        break
        
        # 프로필 정보 저장 및 파싱
        if intro_text:
            profile_data['profile_intro'] = intro_text
            
            # 프로필에서 회원번호 추출 (pm8073590 형식)
            member_id_match = re.search(r'\bpm\d{7,8}\b', intro_text, re.IGNORECASE)
            if member_id_match:
                profile_data['blogger_member_id'] = member_id_match.group(0)
                logger.debug(f"회원번호 수집: {profile_data['blogger_member_id']}")
            
            # 프로필에서 URL 추출
            url_match = re.search(r'https?://[^\s]+', intro_text)
            if url_match:
                profile_data['profile_url'] = url_match.group(0)
                logger.debug(f"프로필 URL 수집: {profile_data['profile_url']}")
        
        if not profile_data['profile_intro']:
            logger.debug(f"소개글 수집 실패: {blog_id}")
    
    except Exception as e:
        logger.debug(f"프로필 정보 추출 실패 ({blog_id}): {e}")
        logger.debug(traceback.format_exc())
    
    return profile_data

# ===========================
# v10.3: 파생 컬럼 제거 (원시 데이터만 수집)
# ===========================
# calculate_derived_columns 함수 제거
# merge_sponsor_info 함수는 유지 (추천인 정보 통합)

def merge_sponsor_info(post_data: Dict, profile_data: Dict, ocr_text: str) -> Dict:
    """추천인 정보 통합 (기존 + 프로필 + OCR)"""
    # 전화번호 통합
    if not post_data.get('sponsor_phone'):
        profile_intro = profile_data.get('profile_intro', '')
        phone = extract_sponsor_phone(profile_intro)
        if phone:
            post_data['sponsor_phone'] = phone
        else:
            ocr_phone = extract_sponsor_phone(ocr_text)
            if ocr_phone:
                post_data['sponsor_phone'] = ocr_phone
    
    # 파트너 ID 통합
    if not post_data.get('content_sponsor_id'):
        blogger_member_id = profile_data.get('blogger_member_id', '')
        if blogger_member_id:
            partner_id = re.sub(r'\D', '', blogger_member_id)
            if len(partner_id) in [7, 8]:
                post_data['content_sponsor_id'] = partner_id
        else:
            ocr_partner_id = extract_sponsor_partner_id(ocr_text)
            if ocr_partner_id:
                post_data['content_sponsor_id'] = ocr_partner_id
    
    return post_data

# ===========================
# v7.4: 필터링 함수들
# ===========================

def is_excluded_blog(blog_id: str) -> bool:
    """제외 대상 블로그인지 확인"""
    return blog_id in EXCLUDED_BLOG_IDS

def is_media_style_title(title: str) -> bool:
    """언론 스타일 제목인지 확인"""
    for pattern in MEDIA_TITLE_PATTERNS:
        if re.search(pattern, title):
            return True
    return False

# ===========================
# 날짜 추출 함수
# ===========================

def parse_published_date(date_text: str) -> str:
    """날짜 파싱"""
    if not date_text:
        return ""
    
    try:
        date_text = re.sub(r'\s+', ' ', date_text.strip())
        
        # 패턴 1: YYYY. MM. DD. HH:MM
        match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*\d{1,2}:\d{2}', date_text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 패턴 2: YYYY. MM. DD.
        match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.', date_text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 패턴 3: YYYY-MM-DD
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

def extract_sponsor_partner_id(text: str) -> str:
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

def extract_hashtags(soup: BeautifulSoup, content_text: str) -> str:
    """해시태그 추출"""
    hashtags = set()
    
    meta_tags = {'#태그', '#tag', '#해시태그', '#hashtag', '#tags'}
    
    # 태그 영역에서 추출
    tag_elements = soup.select('a.link_tag, a[href*="tag"], .se_tag a, .post_tag a')
    for elem in tag_elements:
        tag_text = elem.get_text(strip=True)
        if tag_text:
            if not tag_text.startswith('#'):
                tag_text = '#' + tag_text
            if tag_text.lower() not in meta_tags:
                hashtags.add(tag_text)
    
    # 본문에서 추출
    hashtag_pattern = r'#([가-힣a-zA-Z0-9_]+)'
    matches = re.findall(hashtag_pattern, content_text)
    for match in matches:
        tag_text = '#' + match
        if tag_text.lower() not in meta_tags:
            hashtags.add(tag_text)
    
    return ', '.join(sorted(list(hashtags))) if hashtags else ""

def extract_image_urls(soup: BeautifulSoup) -> str:
    """이미지 URL 추출"""
    image_urls = set()
    
    img_elements = soup.select('img[src], img[data-src], .se-image-resource')
    
    for img in img_elements:
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if src and ('blogfiles.naver.net' in src or 'pstatic.net' in src):
            src = re.sub(r'\?type=\w\d+', '', src)
            image_urls.add(src)
    
    return ', '.join(list(image_urls)[:10]) if image_urls else ""

def extract_video_urls(soup: BeautifulSoup) -> str:
    """비디오 URL 추출"""
    video_urls = set()
    
    video_selectors = [
        'video source',
        'video[src]',
        'iframe[src*="youtube"]',
        'iframe[src*="youtu.be"]',
        'iframe[src*="vimeo"]',
        'iframe[src*="tv.naver"]',
        'iframe[src*="naver.com/video"]',
        'iframe[src*="blog.naver.com/PostView"]',
        '.se-video iframe',
        '.se-component-content[data-type="video"] iframe'
    ]
    
    for selector in video_selectors:
        elements = soup.select(selector)
        for elem in elements:
            src = elem.get('src') or elem.get('data-src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://blog.naver.com' + src
                video_urls.add(src)
    
    return ', '.join(list(video_urls)[:10]) if video_urls else ""

def extract_like_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """좋아요 수 추출"""
    try:
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
                if like_text.isdigit():
                    return int(like_text)
            except:
                continue
        
        # BeautifulSoup로 재시도
        for selector in like_selectors:
            elem = soup.select_one(selector)
            if elem:
                like_text = elem.get_text(strip=True)
                if like_text.isdigit():
                    return int(like_text)
        
        return 0
    except Exception as e:
        logger.debug(f"좋아요 수 추출 실패: {e}")
        return 0

def extract_comment_count(driver: webdriver.Chrome, soup: BeautifulSoup) -> int:
    """댓글 수 추출"""
    try:
        comment_selectors = [
            '.area_comment .count',
            '.cmt_count',
            'em.u_cnt._count.pcol3',
            '.comment_count'
        ]
        
        for selector in comment_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                comment_text = elem.text.strip()
                if comment_text.isdigit():
                    return int(comment_text)
            except:
                continue
        
        # BeautifulSoup로 재시도
        for selector in comment_selectors:
            elem = soup.select_one(selector)
            if elem:
                comment_text = elem.get_text(strip=True)
                if comment_text.isdigit():
                    return int(comment_text)
        
        return 0
    except Exception as e:
        logger.debug(f"댓글 수 추출 실패: {e}")
        return 0

def content_passes_filter(title: str, content: str, full_text: str, blog_id: str, sponsor_id: str) -> Tuple[bool, str, List[str]]:
    """콘텐츠 필터링 검사 (v10.4: 매칭된 키워드도 반환)"""
    matched_exclude_keywords = []
    
    # 블랙리스트 체크
    if is_excluded_blog(blog_id):
        return False, f"제외 대상 블로그: {blog_id}", [blog_id]
    
    # v10.4: 제외 키워드 검사 (복합 키워드 AND 로직 지원)
    # 예: "피엠코리아+침대"는 두 단어가 모두 있을 때만 배제
    for keyword in EXCLUDE_KEYWORDS:
        if '+' in keyword:
            # 복합 키워드 (AND 로직): 모든 부분이 있어야 배제
            parts = [p.strip() for p in keyword.split('+')]
            if all(part in full_text for part in parts):
                matched_exclude_keywords.append(keyword)
        else:
            # 단일 키워드
            if keyword in full_text:
                matched_exclude_keywords.append(keyword)
    
    # v10.4: 제외 키워드 4개 이상 발견 시 배제
    if len(matched_exclude_keywords) >= 4:
        return False, f"제외 키워드 {len(matched_exclude_keywords)}개 발견", matched_exclude_keywords
    
    # PM 브랜드 키워드 체크
    text_lower = full_text.lower()
    has_pm_keyword = any(keyword.lower() in text_lower for keyword in PM_BRAND_KEYWORDS)
    if not has_pm_keyword:
        return False, "PM 브랜드 키워드 없음", []
    
    # 언론 스타일 제목 체크
    if is_media_style_title(title):
        return False, "언론 스타일 제목", []
    
    return True, "", []

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
    
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--single-process')
    
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    # v10.3.1: OCR을 위해 이미지 로딩 활성화 (주석 처리)
    # chrome_options.add_argument('--disable-images')
    # chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    
    user_agent = random.choice(USER_AGENTS)
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        logger.warning(f"자동 드라이버 실패, webdriver-manager 사용: {e}")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
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
        logger.warning("⚠️  Naver API 키가 없습니다.")
        return None
    
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
        "sort": "date"
    }
    
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

def search_keyword(keyword: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict]:
    """키워드로 검색 (API 우선, 실패 시 스크래핑)"""
    all_results = []
    
    # v10.3: API 요청 개수 제한 (100개)
    num_calls = min(max_results // 100, 1)
    
    for i in range(num_calls):
        start = i * 100 + 1
        search_data = search_naver_blog_api(keyword, display=100, start=start)
        
        if not search_data:
            break
        
        results = parse_search_results(search_data)
        if not results:
            break
        
        all_results.extend(results)
        logger.debug(f"'{keyword}' API 호출 {i+1}/{num_calls}: +{len(results)}개 (누적: {len(all_results)}개)")
        
        time.sleep(0.1)
        
        if len(results) < 100:
            break
    
    if all_results:
        logger.info(f"🔍 '{keyword}' API 검색 완료: {len(all_results)}개")
    
    return all_results

# ===========================
# 크롤링 함수
# ===========================

def crawl_blog_post_selenium(driver: webdriver.Chrome, url: str, blog_id: str, 
                            post_id: str, failed_url_manager: FailedURLManager,
                            session_logger: SessionLoggingManager,
                            ocr_processor: Optional[OCRProcessor] = None,
                            excluded_manager: Optional[ExcludedDataManager] = None) -> Optional[Dict]:
    """Selenium을 사용한 블로그 게시물 크롤링 (v10.4: 콘텐츠 분류기 제거, 배제 데이터 수집 추가)"""
    try:
        logger.debug(f"크롤링 시작: {url}")
        driver.get(url)
        
        # v10.4: iframe 대기 및 전환 (강화됨)
        try:
            WebDriverWait(driver, 5).until(  # 3→5초
                EC.presence_of_element_located((By.ID, 'mainFrame'))
            )
            driver.switch_to.frame('mainFrame')
        except TimeoutException:
            # 대체 iframe 시도
            try:
                driver.switch_to.frame('postViewArea')
            except:
                logger.debug("iframe 없음 - 본문 직접 크롤링")
        
        # 페이지 로딩 대기
        time.sleep(1.5)  # 1→1.5초
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 제목 추출 (v10.4: 셀렉터 추가)
        title = ""
        title_selectors = [
            '.se-title-text', '.pcol1', '.se_title', 
            '.post-view .tit', '.tit_h3', 'h3.se_title',
            '.se-fs-', '.blog-title', '.post_title', 'h2.title'  # v10.4: 추가
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = clean_text(title_elem.get_text())
                break
        
        if not title:
            failed_url_manager.add_failed(url, "제목 없음")
            session_logger.log_failed_post(url, "제목 없음")
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
            session_logger.log_failed_post(url, "본문 없음")
            return None
        
        # 발행 날짜 추출
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
        
        full_text = f"{title} {content}"
        
        # 추천인 정보 추출
        sponsor_phone = extract_sponsor_phone(full_text)
        content_sponsor_id = extract_sponsor_partner_id(full_text)
        
        # 필터링 검사 (v10.4: 배제 데이터 수집)
        passes, reason, matched_keywords = content_passes_filter(title, content, full_text, blog_id, content_sponsor_id)
        if not passes:
            logger.debug(f"필터링됨: {reason} - {title[:50]}")
            failed_url_manager.add_failed(url, f"필터링: {reason}")
            session_logger.log_failed_post(url, f"필터링: {reason}")
            # v10.4: 배제된 데이터 수집
            if excluded_manager:
                excluded_manager.add_excluded(url, title, blog_id, reason, matched_keywords)
            return None
        
        # 해시태그 추출
        hashtags = extract_hashtags(soup, content)
        
        # 이미지/비디오 URL 추출
        image_urls = extract_image_urls(soup)
        video_urls = extract_video_urls(soup)
        
        # 좋아요/댓글 수 추출
        like_count = extract_like_count(driver, soup)
        comment_count = extract_comment_count(driver, soup)
        
        # 기본 데이터 구성
        post_data = {
            'platform': 'naver_blog',
            'post_id': post_id,
            'blog_id': blog_id,
            'url': url,
            'title': title,
            'content': content,
            'published_datetime': published_datetime,
            'sponsor_phone': sponsor_phone,
            'content_sponsor_id': content_sponsor_id,
            'like_count': like_count,
            'comment_count': comment_count,
            'hashtags': hashtags,
            'image_urls': image_urls,
            'video_urls': video_urls,
            'collected_date': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')  # v10.4: KST
        }
        
        # iframe 복귀
        driver.switch_to.default_content()
        
        # ===========================
        # v10.4: 프로필 정보 수집 (URL 버그 수정됨)
        # ===========================
        profile_data = extract_profile_info(driver, soup, blog_id)
        post_data.update(profile_data)
        
        # ===========================
        # v10.4: 이미지 OCR 처리 (PaddleOCR)
        # ===========================
        image_ocr_text = ""
        if ocr_processor and image_urls:
            try:
                logger.debug(f"OCR 처리 시작: {blog_id}/{post_id}")
                image_ocr_text = ocr_processor.process_image_urls(image_urls, max_images=3)
                if image_ocr_text:
                    logger.info(f"✅ OCR 성공: {blog_id}/{post_id} ({len(image_ocr_text)} chars)")
                else:
                    logger.debug(f"OCR 결과 없음: {blog_id}/{post_id}")
            except Exception as e:
                logger.warning(f"OCR 실패: {blog_id}/{post_id} - {e}")
        
        post_data['image_ocr_text'] = image_ocr_text
        
        # ===========================
        # 추천인 정보 통합
        # ===========================
        post_data = merge_sponsor_info(post_data, profile_data, image_ocr_text)
        
        # v10.4: 콘텐츠 타입 분류는 analysis/content_type_classifier.py로 이동됨
        # 크롤러에서는 원시 데이터만 수집
        
        return post_data
    
    except TimeoutException:
        failed_url_manager.add_failed(url, "페이지 로딩 시간 초과")
        session_logger.log_failed_post(url, "페이지 로딩 시간 초과")
        return None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        failed_url_manager.add_failed(url, error_msg)
        session_logger.log_failed_post(url, error_msg)
        logger.error(f"크롤링 실패 ({url}): {error_msg}")
        return None

# ===========================
# 메인 크롤링 로직
# ===========================

def main():
    """메인 크롤링 함수"""
    logger.info("=" * 80)
    logger.info("📊 PM-International Korea 네이버 블로그 크롤러 v10.4 시작")
    logger.info("=" * 80)
    
    # v10.4: 한국 시간(KST) 사용
    global START_TIME
    START_TIME = time.time()
    start_datetime = datetime.now(KST)
    logger.info(f"⏰ 시작 시간: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
    logger.info(f"⏱️  최대 실행 시간: {MAX_DURATION_SECONDS/3600:.1f}시간 ({MAX_DURATION_SECONDS/60:.0f}분)")
    
    # 매니저 초기화
    duplicate_checker = DuplicateChecker()
    duplicate_checker.load_previous_data()
    
    failed_url_manager = FailedURLManager()
    session_logger = SessionLoggingManager()  # v10.4: 이름 변경
    excluded_manager = ExcludedDataManager()  # v10.4: 배제 데이터 수집
    
    # v10.4: PaddleOCR 프로세서 초기화
    ocr_processor = None
    if OCR_AVAILABLE:
        ocr_processor = OCRProcessor()
        if not ocr_processor.ocr_engine:
            logger.warning("⚠️  OCR 초기화 실패, OCR 기능 비활성화")
            ocr_processor = None
    else:
        logger.warning("⚠️  PaddleOCR이 설치되지 않았습니다. OCR 기능 비활성화")
    
    # v10.4: 콘텐츠 분류기는 analysis 모듈로 이동됨
    
    # 드라이버 초기화
    logger.info("🔧 Selenium 드라이버 초기화 중...")
    driver = setup_driver()
    logger.info("✅ Selenium 드라이버 준비 완료")
    
    # 수집 데이터
    all_posts = []
    all_bloggers = {}  # blog_id를 키로 하는 딕셔너리
    
    # 통계
    stats = {
        'total_attempted': 0,
        'collected': 0,
        'filtered': 0,
        'duplicates': 0,
        'errors': 0
    }
    
    try:
        # v10.4: 키워드 생성 (모든 키워드에 연도 확장 적용)
        all_keywords = []
        all_base_keywords = []
        
        # 모든 기본 키워드 수집
        all_base_keywords.extend(TARGET_KEYWORDS['primary'])
        all_base_keywords.extend(TARGET_KEYWORDS['secondary'])
        all_base_keywords.extend(TARGET_KEYWORDS['product_test'])
        
        # 연도 없는 키워드 먼저 추가
        all_keywords.extend(all_base_keywords)
        
        # v10.4: 모든 키워드에 연도 확장 적용 (중복 필터링이 있어 문제없음)
        for base_keyword in all_base_keywords:
            for year in YEARS:
                all_keywords.append(f"{base_keyword} {year}")
        
        logger.info(f"🔍 총 {len(all_keywords)}개 키워드로 검색 시작")
        
        # 키워드별 검색 및 크롤링
        for keyword_idx, keyword in enumerate(all_keywords, 1):
            # v10.3: 시간 제한 확인
            if check_time_limit():
                logger.info("⏰ 시간 제한 도달, 크롤링 중단")
                break
            
            logger.info(f"\n[{keyword_idx}/{len(all_keywords)}] 키워드: '{keyword}' 검색 중...")
            
            search_results = search_keyword(keyword, MAX_SEARCH_RESULTS)
            
            if not search_results:
                logger.warning(f"⚠️  '{keyword}' 검색 결과 없음")
                continue
            
            logger.info(f"📝 '{keyword}' 검색 결과: {len(search_results)}개")
            
            # 각 게시물 크롤링
            for idx, result in enumerate(search_results, 1):
                # v10.3: 시간 제한 확인
                if check_time_limit():
                    logger.info("⏰ 시간 제한 도달, 현재 키워드 처리 완료 후 종료")
                    break
                
                url = result['url']
                blog_id = result['blog_id']
                post_id = result['post_id']
                
                stats['total_attempted'] += 1
                
                # 중복 체크
                if duplicate_checker.is_duplicate(post_id, url, result.get('title', ''), blog_id):
                    logger.debug(f"[{idx}/{len(search_results)}] 중복: {post_id}")
                    stats['duplicates'] += 1
                    continue
                
                # 실패 이력 체크
                if failed_url_manager.is_failed(url):
                    logger.debug(f"[{idx}/{len(search_results)}] 이전 실패: {post_id}")
                    stats['errors'] += 1
                    continue
                
                logger.info(f"[{idx}/{len(search_results)}] 크롤링: {blog_id}/{post_id}")
                
                # 크롤링 실행
                post_data = crawl_blog_post_selenium(
                    driver, url, blog_id, post_id,
                    failed_url_manager, session_logger,
                    ocr_processor, excluded_manager
                )
                
                if post_data:
                    all_posts.append(post_data)
                    duplicate_checker.add(post_id, url, post_data['title'], blog_id)
                    stats['collected'] += 1
                    
                    # 블로거 정보 저장
                    if blog_id not in all_bloggers:
                        all_bloggers[blog_id] = {
                            'blog_id': blog_id,
                            'profile_nickname': post_data.get('profile_nickname', ''),
                            'profile_intro': post_data.get('profile_intro', ''),
                            'blogger_member_id': post_data.get('blogger_member_id', ''),
                            'profile_url': post_data.get('profile_url', '')
                        }
                    
                    logger.info(f"✅ 수집 완료: {blog_id}/{post_id} (총 {stats['collected']}개)")
                else:
                    stats['filtered'] += 1
                
                # 딜레이
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                
                # 정기 저장 (100개마다)
                if stats['collected'] > 0 and stats['collected'] % 100 == 0:
                    save_checkpoint(all_posts, all_bloggers)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  사용자 중단 (Ctrl+C)")
    
    except Exception as e:
        logger.error(f"❌ 크롤링 중 오류: {e}")
        logger.error(traceback.format_exc())
    
    finally:
        # 드라이버 종료
        try:
            driver.quit()
            logger.info("✅ Selenium 드라이버 종료")
        except:
            pass
        
        # 최종 저장
        if all_posts:
            save_final_results(all_posts, all_bloggers, stats, start_datetime)
        
        # 세션 로그 저장
        session_logger.write_session_end(stats)
        
        # 실패 URL 저장
        failed_url_manager.save()
        
        # v10.4: 배제 데이터 저장
        excluded_manager.save()
        excluded_manager.export_to_csv()
        
        # 최종 통계 출력
        print_final_statistics(stats, start_datetime)

def save_checkpoint(posts: List[Dict], bloggers: Dict):
    """체크포인트 저장"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 게시물 저장
    posts_df = pd.DataFrame(posts)
    checkpoint_path = f"checkpoint_posts_{timestamp}.csv"
    posts_df.to_csv(checkpoint_path, index=False, encoding='utf-8-sig')
    logger.info(f"💾 체크포인트 저장: {checkpoint_path} ({len(posts)}개)")

def save_final_results(posts: List[Dict], bloggers: Dict, stats: Dict, start_datetime: datetime):
    """최종 결과 저장"""
    timestamp = datetime.now(KST).strftime('%Y%m%d_%H%M%S')
    
    # v10.4: 게시물 저장 (원시 데이터, 콘텐츠 분류는 analysis에서 처리)
    posts_df = pd.DataFrame(posts)
    posts_filename = f"data/naver_blog_pm_v10_4_posts_{timestamp}.csv"
    Path("data").mkdir(exist_ok=True)
    posts_df.to_csv(posts_filename, index=False, encoding='utf-8-sig')
    logger.info(f"💾 게시물 저장: {posts_filename} ({len(posts)}개)")
    
    # 블로거 저장 (프로필 정보는 여기에만 저장, posts CSV에서 제외됨)
    if bloggers:
        bloggers_df = pd.DataFrame(list(bloggers.values()))
        bloggers_filename = f"data/naver_blog_pm_v10_4_bloggers_{timestamp}.csv"
        bloggers_df.to_csv(bloggers_filename, index=False, encoding='utf-8-sig')
        logger.info(f"💾 블로거 저장: {bloggers_filename} ({len(bloggers)}개)")
    
    # 리포트 생성
    generate_report(stats, posts_df, start_datetime, timestamp)

def generate_report(stats: Dict, posts_df: pd.DataFrame, start_datetime: datetime, timestamp: str):
    """실행 리포트 생성 (v10.4: 단일 파일 누적 방식)"""
    end_datetime = datetime.now(KST)
    duration = end_datetime - start_datetime
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f"📊 PM-International 네이버 블로그 크롤러 v10.4 테스트 결과")
    report_lines.append(f"   실행: {timestamp}")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # 실행 시간
    report_lines.append("⏱️  실행 시간")
    report_lines.append("-" * 80)
    report_lines.append(f"• 총 실행 시간: {duration.total_seconds()/60:.1f}분 ({int(duration.total_seconds())}초)")
    report_lines.append(f"• 시작 시간: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
    report_lines.append(f"• 종료 시간: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
    report_lines.append("")
    
    # 수집 성과
    report_lines.append("📈 수집 성과")
    report_lines.append("-" * 80)
    report_lines.append(f"• 총 수집 게시물: {stats['collected']}개")
    if duration.total_seconds() > 0:
        report_lines.append(f"• 수집 속도: {stats['collected']/(duration.total_seconds()/60):.2f}개/분")
        report_lines.append(f"• 게시물당 평균 소요 시간: {duration.total_seconds()/max(stats['collected'], 1):.1f}초")
    report_lines.append("")
    
    # 성공률 분석
    report_lines.append("✅ 성공률 분석")
    report_lines.append("-" * 80)
    report_lines.append(f"• 총 시도: {stats['total_attempted']}회")
    if stats['total_attempted'] > 0:
        report_lines.append(f"• ✅ 성공: {stats['collected']}회 ({stats['collected']/stats['total_attempted']*100:.1f}%)")
        report_lines.append(f"• 🔍 필터링: {stats['filtered']}회 ({stats['filtered']/stats['total_attempted']*100:.1f}%)")
        report_lines.append(f"• 🔄 중복: {stats['duplicates']}회 ({stats['duplicates']/stats['total_attempted']*100:.1f}%)")
        report_lines.append(f"• ❌ 에러: {stats['errors']}회 ({stats['errors']/stats['total_attempted']*100:.1f}%)")
    report_lines.append("")
    
    # v10.4 기능 성과
    if len(posts_df) > 0:
        report_lines.append("🆕 v10.4 수집 성과")
        report_lines.append("-" * 80)
        
        # 프로필 정보
        if 'profile_nickname' in posts_df.columns:
            nickname_rate = (posts_df['profile_nickname'].notna() & (posts_df['profile_nickname'] != '')).sum() / len(posts_df) * 100
            intro_rate = (posts_df['profile_intro'].notna() & (posts_df['profile_intro'] != '')).sum() / len(posts_df) * 100
            report_lines.append("[프로필 정보 수집]")
            report_lines.append(f"• 닉네임 수집률: {nickname_rate:.1f}%")
            report_lines.append(f"• 소개글 수집률: {intro_rate:.1f}%")
            report_lines.append("")
        
        # OCR
        if 'image_ocr_text' in posts_df.columns:
            ocr_rate = (posts_df['image_ocr_text'].notna() & (posts_df['image_ocr_text'] != '')).sum() / len(posts_df) * 100
            report_lines.append("[이미지 OCR 처리 (PaddleOCR)]")
            report_lines.append(f"• OCR 처리 성공률: {ocr_rate:.1f}%")
            report_lines.append("")
        
        # 콘텐츠 분석 통계
        report_lines.append("📊 콘텐츠 분석 통계")
        report_lines.append("-" * 80)
        if 'content' in posts_df.columns:
            avg_length = posts_df['content'].str.len().mean()
            max_length = posts_df['content'].str.len().max()
            min_length = posts_df['content'].str.len().min()
            report_lines.append(f"• 평균 본문 글자수: {avg_length:.0f}자")
            report_lines.append(f"• 최대 본문 글자수: {max_length:.0f}자")
            report_lines.append(f"• 최소 본문 글자수: {min_length:.0f}자")
        
        if 'hashtags' in posts_df.columns:
            hashtag_rate = (posts_df['hashtags'].notna() & (posts_df['hashtags'] != '')).sum() / len(posts_df) * 100
            report_lines.append(f"• 해시태그 포함률: {hashtag_rate:.1f}%")
        
        if 'image_urls' in posts_df.columns:
            image_rate = (posts_df['image_urls'].notna() & (posts_df['image_urls'] != '')).sum() / len(posts_df) * 100
            report_lines.append(f"• 이미지 포함률: {image_rate:.1f}%")
        
        # 추천인 정보
        phone_rate = (posts_df['sponsor_phone'].notna() & (posts_df['sponsor_phone'] != '')).sum() / len(posts_df) * 100
        sponsor_rate = (posts_df['content_sponsor_id'].notna() & (posts_df['content_sponsor_id'] != '')).sum() / len(posts_df) * 100
        report_lines.append("")
        report_lines.append("[추천인 정보 추출]")
        report_lines.append(f"• 전화번호 수집률: {phone_rate:.1f}%")
        report_lines.append(f"• 후원번호 수집률: {sponsor_rate:.1f}%")
    
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # v10.4: 단일 리포트 파일에 누적 저장
    report_filename = "data/naver_blog_reports.txt"
    Path("data").mkdir(exist_ok=True)
    
    # 기존 파일에 추가 (없으면 새로 생성)
    mode = 'a' if Path(report_filename).exists() else 'w'
    with open(report_filename, mode, encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        f.write('\n')
    
    logger.info(f"💾 리포트 저장: {report_filename}")
    
    # 콘솔 출력
    print()
    for line in report_lines:
        print(line)

def print_final_statistics(stats: Dict, start_datetime: datetime):
    """최종 통계 출력"""
    end_datetime = datetime.now()
    duration = end_datetime - start_datetime
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 최종 통계")
    logger.info("=" * 80)
    logger.info(f"⏰ 총 실행 시간: {duration.total_seconds()/60:.1f}분")
    logger.info(f"✅ 수집 성공: {stats['collected']}개")
    logger.info(f"🔍 필터링: {stats['filtered']}개")
    logger.info(f"🔄 중복: {stats['duplicates']}개")
    logger.info(f"❌ 에러: {stats['errors']}개")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
