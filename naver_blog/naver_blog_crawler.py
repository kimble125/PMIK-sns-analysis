#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 블로그 크롤러 - PM-International Korea SNS 분석 프로젝트 v5.0
========================================================

주요 기능:
1. Naver Search API로 블로그 URL 수집
2. Selenium으로 본문 크롤링 (해시태그, 이미지, 동영상 포함)
3. 타겟 해시태그 필터링
4. 이미지 OCR (EasyOCR) - 로컬 CPU/GPU
5. 동영상 스크립트 추출 (YouTube 자막)
6. 추천인 정보 자동 추출 (이름, 전화번호, 파트너번호) ⭐ NEW
7. CSV 파일 저장 (21개 컬럼, 종류별 정리)

출력 컬럼 (21개):
- 기본 정보 (6): platform, title, description, blogger_profile, post_url, author_id
- 콘텐츠 정보 (5): content_text, hashtags, image_text, video_text, postdate
- 미디어 정보 (3): image_count, video_count, video_urls
- 참여 지표 (3): view_count, like_count, comment_count
- 추천인 정보 (4): referrer_name, referrer_phone, partner_number, kakao_id
- 메타 정보 (1): collected_at

필수 라이브러리:
    pip install requests beautifulsoup4 selenium pandas easyocr Pillow youtube-transcript-api tqdm

작성자: PMI코리아 데이터 팀
버전: 5.0
최종 수정: 2025-11-01
"""

import os
import time
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from io import BytesIO
import tempfile

# 웹 크롤링
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 데이터 처리
import pandas as pd
from PIL import Image

# OCR
import easyocr

# 동영상 스크립트
from youtube_transcript_api import YouTubeTranscriptApi

# 유틸리티
from tqdm import tqdm


# ============================================================
# 설정
# ============================================================

# Naver API 인증 정보
NAVER_CLIENT_ID = "9v7cOolOk2ctSQXc73sd"
NAVER_CLIENT_SECRET = "9jHcXVNQwZ"

# 타겟 키워드 (네이버 검색용 - 넓게 검색)
SEARCH_KEYWORDS = [
    "피엠인터내셔널", "피엠코리아", "PM인터내셔널",
    "핏라인", "FitLine",
]

# 타겟 해시태그 (필터링용 - 정확한 매칭)
# 주의: 반드시 '#'로 시작해야 합니다!
TARGET_HASHTAGS = [
    '#피엠인터내셔널', '#피엠코리아', '#PM인터내셔널', '#독일피엠',
    '#핏라인', '#피트라인', '#FitLine', '#fitline',
    '#베이식스', '#베이직스', '#Basics',
    '#프로셰이프', '#프로쉐이프', '#ProShape',
    '#엑티바이즈', '#Activize',
    '#파워칵테일', '#PowerCocktail',
    '#리스토레이트', '#Restorate'
]

# 수집 설정
MAX_RESULTS_PER_KEYWORD = 100
DAYS_BACK = 30
TARGET_POST_COUNT = 500

# OCR 설정
USE_OCR = True  # EasyOCR 활성화
MAX_IMAGES_PER_POST = 5
OCR_CONFIDENCE_THRESHOLD = 0.5

# Whisper 설정 (자막 없는 영상 처리)
USE_WHISPER = False  # 메인 크롤링에서는 비활성화 (별도 스크립트로 처리)
WHISPER_MODEL = "base"  # tiny, base, small, medium, large
MAX_VIDEO_DURATION = 300  # 최대 처리 시간 (초) - 5분

# 출력 설정
OUTPUT_DIR = "output"
OUTPUT_CSV = f"{OUTPUT_DIR}/naver_blog_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
STATS_FILE = f"{OUTPUT_DIR}/crawl_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


# ============================================================
# Step 1: Naver Search API로 URL 수집
# ============================================================

class NaverBlogSearcher:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/blog.json"
    
    def search_keyword(self, keyword: str, max_results: int = 100, days_back: int = 30) -> List[Dict]:
        """
        네이버 검색 API로 블로그 URL 수집
        
        참고: 이 단계에서는 키워드가 제목/본문에 있는 모든 게시물을 수집합니다.
        실제 필터링은 크롤링 후 해시태그로 수행됩니다.
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        results = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for start in range(1, min(max_results, 1000), 100):
            params = {
                "query": keyword,
                "display": 100,
                "start": start,
                "sort": "date"
            }
            
            try:
                response = requests.get(self.base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                if not items:
                    break
                
                for item in items:
                    post_date_str = item.get('postdate', '')
                    try:
                        post_date = datetime.strptime(post_date_str, '%Y%m%d')
                        if post_date < cutoff_date:
                            continue
                    except:
                        pass
                    
                    results.append({
                        'title': self._clean_html(item.get('title', '')),
                        'link': item.get('link', ''),
                        'description': self._clean_html(item.get('description', '')),
                        'bloggername': item.get('bloggername', ''),
                        'bloggerlink': item.get('bloggerlink', ''),
                        'postdate': post_date_str
                    })
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[ERROR] Keyword '{keyword}' 검색 실패: {e}")
                break
        
        return results
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        clean = re.sub('<.*?>', '', text)
        return clean


# ============================================================
# Step 2: Selenium으로 본문 크롤링
# ============================================================

class NaverBlogCrawler:
    def __init__(self, headless: bool = True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def crawl_blog_post(self, url: str) -> Optional[Dict]:
        """
        블로그 게시물 크롤링
        
        Returns:
            Dict: 게시물 정보 (제목, 본문, 해시태그, 이미지, 동영상 등)
            None: 크롤링 실패시
        """
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # iframe으로 전환
            try:
                iframe = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'mainFrame'))
                )
                self.driver.switch_to.frame(iframe)
            except TimeoutException:
                pass
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 제목 추출
            title_elem = soup.select_one('div.se-title-text, h3.se_textarea')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 본문 추출
            content_div = soup.select_one('div.se-main-container, div.se_component_wrap')
            if not content_div:
                content_div = soup.find('body')
            
            content_text = content_div.get_text(separator='\n', strip=True) if content_div else ""
            
            # 해시태그 추출
            hashtags = self._extract_hashtags(content_text)
            
            # 이미지 URL 추출
            images = []
            for img in soup.select('img.se-image-resource, img.__se_img_el'):
                img_url = img.get('data-lazy-src') or img.get('src')
                if img_url and img_url.startswith('http'):
                    images.append(img_url)
            
            # 동영상 URL 추출
            videos = []
            for video in soup.select('iframe[src*="youtube"], iframe[src*="naver"], iframe[src*="youtu"]'):
                video_url = video.get('src')
                if video_url:
                    if not video_url.startswith('http'):
                        video_url = 'https:' + video_url
                    videos.append(video_url)
            
            # 작성자 ID 추출
            author_match = re.search(r'blog\.naver\.com/([^/]+)/', url)
            author_id = author_match.group(1) if author_match else ""
            
            # 댓글 수, 공감 수, 조회 수 추출 (동적 로딩 대기)
            time.sleep(2)  # 동적 콘텐츠 로딩 대기
            
            view_count = self._extract_view_count()
            comment_count = self._extract_comment_count()
            like_count = self._extract_like_count()
            
            self.driver.switch_to.default_content()
            
            return {
                'url': url,
                'title': title,
                'content_text': content_text,
                'hashtags': hashtags,
                'images': images,
                'videos': videos,
                'author_id': author_id,
                'view_count': view_count,
                'comment_count': comment_count,
                'like_count': like_count
            }
            
        except Exception as e:
            print(f"[ERROR] 크롤링 실패 {url}: {e}")
            return None
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """본문에서 해시태그 추출"""
        pattern = r'#[가-힣a-zA-Z0-9_]+'
        return list(set(re.findall(pattern, text)))
    
    
    def _extract_view_count(self) -> str:
        """조회 수 추출 (Selenium body 텍스트에서)"""
        try:
            # iframe 내부의 전체 텍스트에서 "조회 숫자" 패턴 찾기
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            # 패턴: "조회 1,234" 또는 "조회수 1,234"
            match = re.search(r'조회[수]?\s*([\d,]+)', body_text)
            if match:
                return match.group(1).replace(',', '')
            return ""
        except:
            return ""
    
    def _extract_comment_count(self) -> str:
        """댓글 수 추출 (Selenium body 텍스트에서)"""
        try:
            # iframe 내부의 전체 텍스트에서 "댓글 숫자" 패턴 찾기
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            match = re.search(r'댓글\s*(\d+)', body_text)
            if match:
                return match.group(1)
            return ""
        except:
            return ""
    
    def _extract_like_count(self) -> str:
        """공감 수 추출 (Selenium body 텍스트에서)"""
        try:
            # iframe 내부의 전체 텍스트에서 "공감 숫자" 패턴 찾기
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            match = re.search(r'공감\s*(\d+)', body_text)
            if match:
                return match.group(1)
            return ""
        except:
            return ""
    
    
    def close(self):
        self.driver.quit()


# ============================================================
# Step 3: 해시태그 필터링 (개선됨)
# ============================================================

def filter_by_hashtags(posts: List[Dict], target_hashtags: List[str]) -> Tuple[List[Dict], Dict]:
    """
    타겟 해시태그를 포함한 게시물만 필터링
    
    Args:
        posts: 크롤링된 게시물 리스트
        target_hashtags: 타겟 해시태그 리스트
    
    Returns:
        (filtered_posts, stats): 필터링된 게시물과 통계 정보
    """
    filtered = []
    stats = {
        'total_posts': len(posts),
        'filtered_posts': 0,
        'matched_hashtags': {},
        'posts_without_hashtags': 0
    }
    
    # 정규화된 타겟 해시태그 (소문자, 공백 제거)
    target_hashtags_normalized = [tag.lower().strip() for tag in target_hashtags]
    
    for post in posts:
        post_hashtags = post.get('hashtags', [])
        
        if not post_hashtags:
            stats['posts_without_hashtags'] += 1
            continue
        
        # 게시물 해시태그 정규화
        post_hashtags_normalized = [tag.lower().strip() for tag in post_hashtags]
        
        # 매칭되는 해시태그 찾기
        matched = [tag for tag in post_hashtags_normalized if tag in target_hashtags_normalized]
        
        if matched:
            filtered.append(post)
            # 통계 수집
            for tag in matched:
                stats['matched_hashtags'][tag] = stats['matched_hashtags'].get(tag, 0) + 1
    
    stats['filtered_posts'] = len(filtered)
    
    return filtered, stats


# ============================================================
# Step 4: 이미지 OCR (개선됨)
# ============================================================

class OCRProcessor:
    def __init__(self, languages: List[str] = ['ko', 'en'], gpu: bool = False):
        """
        EasyOCR 초기화
        
        비용: 완전 무료 (오픈소스, 로컬 실행)
        성능: CPU 1-3초/이미지
        정확도: 한글 70-85%, 영어 85-95%
        """
        print("EasyOCR 모델 로딩 중...")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        self.stats = {
            'total_images': 0,
            'successful_ocr': 0,
            'failed_ocr': 0,
            'total_time': 0,
            'avg_confidence': []
        }
        print("EasyOCR 준비 완료!")
    
    def extract_text_from_url(self, image_url: str, confidence_threshold: float = 0.5) -> Tuple[str, float]:
        """
        이미지 URL에서 텍스트 추출
        
        Returns:
            (text, processing_time): 추출된 텍스트와 처리 시간
        """
        start_time = time.time()
        self.stats['total_images'] += 1
        
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            results = self.reader.readtext(img)
            
            # 신뢰도가 높은 텍스트만 추출
            texts = []
            confidences = []
            for detection in results:
                text, confidence = detection[1], detection[2]
                if confidence >= confidence_threshold:
                    texts.append(text)
                    confidences.append(confidence)
            
            processing_time = time.time() - start_time
            self.stats['total_time'] += processing_time
            self.stats['successful_ocr'] += 1
            
            if confidences:
                avg_conf = sum(confidences) / len(confidences)
                self.stats['avg_confidence'].append(avg_conf)
            
            return '\n'.join(texts), processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats['failed_ocr'] += 1
            return "", processing_time
    
    def get_stats(self) -> Dict:
        """OCR 성능 통계 반환"""
        avg_time = self.stats['total_time'] / max(self.stats['total_images'], 1)
        avg_conf = sum(self.stats['avg_confidence']) / max(len(self.stats['avg_confidence']), 1) if self.stats['avg_confidence'] else 0
        
        return {
            'total_images': self.stats['total_images'],
            'successful': self.stats['successful_ocr'],
            'failed': self.stats['failed_ocr'],
            'success_rate': f"{self.stats['successful_ocr'] / max(self.stats['total_images'], 1) * 100:.1f}%",
            'avg_processing_time': f"{avg_time:.2f}초",
            'avg_confidence': f"{avg_conf * 100:.1f}%"
        }


# ============================================================
# Step 5: 동영상 스크립트 추출 (개선됨)
# ============================================================

class VideoTranscriptExtractor:
    def __init__(self, use_whisper: bool = False, whisper_model: str = "base"):
        """
        동영상 스크립트 추출기
        
        비용: 완전 무료
        - YouTube 자막: youtube-transcript-api (무료)
        - Whisper 음성인식: OpenAI Whisper (무료, 오픈소스)
        """
        self.use_whisper = use_whisper
        self.whisper_model = None
        
        if use_whisper:
            try:
                import whisper
                print(f"Whisper 모델 로딩 중 ({whisper_model})...")
                self.whisper_model = whisper.load_model(whisper_model)
                print("Whisper 준비 완료!")
            except ImportError:
                print("[WARN] Whisper가 설치되지 않았습니다. YouTube 자막만 사용합니다.")
                print("      설치: pip install openai-whisper")
                self.use_whisper = False
        
        self.stats = {
            'total_videos': 0,
            'youtube_subtitle_success': 0,
            'whisper_success': 0,
            'failed': 0
        }
    
    def extract_transcript(self, video_url: str) -> str:
        """
        동영상에서 스크립트 추출
        
        우선순위:
        1. YouTube 자막 (가장 빠르고 정확)
        2. Whisper 음성인식 (자막 없을 때)
        """
        self.stats['total_videos'] += 1
        
        # 1. YouTube 자막 시도
        if 'youtube' in video_url or 'youtu.be' in video_url:
            # URL 정규화 (embed → watch)
            video_url = self._normalize_youtube_url(video_url)
            
            transcript = self._extract_youtube_subtitle(video_url)
            if transcript:
                self.stats['youtube_subtitle_success'] += 1
                print(f"  ✓ YouTube 자막 추출 성공")
                return transcript
            else:
                print(f"  ⚠ YouTube 자막 없음, Whisper 시도...")
        
        # 2. Whisper 음성인식 시도 (활성화된 경우)
        if self.use_whisper and self.whisper_model:
            transcript = self._extract_with_whisper(video_url)
            if transcript:
                self.stats['whisper_success'] += 1
                print(f"  ✓ Whisper 음성인식 성공")
                return transcript
        
        self.stats['failed'] += 1
        return ""
    
    def _normalize_youtube_url(self, url: str) -> str:
        """YouTube URL을 표준 형식으로 변환"""
        # Embed URL → Watch URL
        if '/embed/' in url:
            video_id = url.split('/embed/')[1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        return url
    
    def _extract_youtube_subtitle(self, youtube_url: str) -> str:
        """YouTube 자막 추출 (무료, 빠름, 정확)"""
        video_id = self._extract_youtube_id(youtube_url)
        if not video_id:
            print(f"    [WARN] YouTube Video ID 추출 실패: {youtube_url[:50]}...")
            return ""
        
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=['ko', 'en']
            )
            full_text = ' '.join([entry['text'] for entry in transcript])
            return full_text
            
        except Exception as e:
            print(f"    [WARN] YouTube 자막 없음 (Video ID: {video_id}): {type(e).__name__}")
            return ""
    
    def _extract_with_whisper(self, video_url: str) -> str:
        """
        Whisper로 음성 인식 (무료, 느림, 자막 없을 때 사용)
        
        주의: 동영상 다운로드가 필요하므로 시간이 오래 걸립니다.
        """
        try:
            import yt_dlp
            
            print(f"    [INFO] Whisper 처리 시작: {video_url[:50]}...")
            
            # 임시 파일 경로
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_audio_path = temp_audio.name
            temp_audio.close()
            
            # FFmpeg 경로 설정 (Windows)
            ffmpeg_location = 'C:/ffmpeg/bin'  # FFmpeg 설치 경로
            
            # 동영상에서 오디오 추출
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_audio_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'ffmpeg_location': ffmpeg_location,
                'quiet': False,  # 에러 출력
                'no_warnings': False
            }
            
            print(f"    [INFO] 동영상 다운로드 중...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Whisper로 음성 인식
            print(f"    [INFO] Whisper 음성 인식 중...")
            result = self.whisper_model.transcribe(temp_audio_path, language='ko')
            
            # 임시 파일 삭제
            try:
                os.unlink(temp_audio_path)
            except:
                pass
            
            print(f"    [INFO] Whisper 성공: {len(result['text'])} 문자")
            return result['text']
            
        except Exception as e:
            print(f"    [ERROR] Whisper 실패: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """YouTube 동영상 ID 추출"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?]+)',
            r'youtube\.com/embed/([^&\n?]+)',
            r'/([a-zA-Z0-9_-]{11})(?:\?|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_stats(self) -> Dict:
        """동영상 처리 통계 반환"""
        return {
            'total_videos': self.stats['total_videos'],
            'youtube_subtitle': self.stats['youtube_subtitle_success'],
            'whisper': self.stats['whisper_success'],
            'failed': self.stats['failed'],
            'success_rate': f"{(self.stats['youtube_subtitle_success'] + self.stats['whisper_success']) / max(self.stats['total_videos'], 1) * 100:.1f}%"
        }


# ============================================================
# Step 6: 추천인 정보 추출
# ============================================================

class ReferrerExtractor:
    """본문 및 OCR 텍스트에서 추천인 정보 자동 추출"""
    
    def __init__(self):
        # 전화번호 패턴 (다양한 형식 지원)
        self.phone_patterns = [
            r'010[-\s]?\d{4}[-\s]?\d{4}',  # 010-1234-5678, 010 1234 5678, 01012345678
            r'\d{3}[-\s]?\d{4}[-\s]?\d{4}',  # 일반 전화번호
        ]
        
        # 이름 패턴 (한글 2-4자)
        self.name_patterns = [
            r'(?:문의|상담|연락처|담당|추천인|파트너)\s*[:：]?\s*([가-힣]{2,4})',
            r'([가-힣]{2,4})\s*(?:파트너|매니저|대표|팀장)',
        ]
        
        # 파트너 번호 패턴
        self.partner_patterns = [
            r'파트너\s*번호\s*[:：]?\s*([A-Z0-9-]+)',
            r'Partner\s*No\.?\s*[:：]?\s*([A-Z0-9-]+)',
            r'P[-]?\d{4,}',  # P-1234, P1234
        ]
        
        # 카카오톡 ID 패턴 (참고용)
        self.kakao_patterns = [
            r'카카오톡?\s*(?:ID|아이디)?\s*[:：]?\s*([a-zA-Z0-9_]+)',
            r'카톡\s*[:：]?\s*([a-zA-Z0-9_]+)',
        ]
    
    def extract_phone(self, text: str) -> str:
        """전화번호 추출"""
        if not text:
            return ''
        
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                # 숫자만 추출 후 포맷팅
                phone = re.sub(r'[^0-9]', '', match.group(0))
                if len(phone) == 10 or len(phone) == 11:
                    # 010-1234-5678 형식으로 통일
                    if len(phone) == 11:
                        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                    else:
                        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
        return ''
    
    def extract_name(self, text: str) -> str:
        """이름 추출"""
        if not text:
            return ''
        
        for pattern in self.name_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1) if match.lastindex >= 1 else match.group(0)
                # 한글 2-4자 검증
                if re.match(r'^[가-힣]{2,4}$', name):
                    return name
        return ''
    
    def extract_partner_number(self, text: str) -> str:
        """파트너 번호 추출"""
        if not text:
            return ''
        
        for pattern in self.partner_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.lastindex >= 1 else match.group(0)
        return ''
    
    def extract_kakao(self, text: str) -> str:
        """카카오톡 ID 추출 (참고용)"""
        if not text:
            return ''
        
        for pattern in self.kakao_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''
    
    def extract_all(self, content_text: str, ocr_text: str = '') -> Dict[str, str]:
        """
        본문과 OCR 텍스트에서 모든 추천인 정보 추출
        
        Args:
            content_text: 게시물 본문
            ocr_text: OCR 추출 텍스트
        
        Returns:
            {'name': str, 'phone': str, 'partner_number': str, 'kakao': str}
        """
        # 본문과 OCR 텍스트 결합
        combined_text = f"{content_text}\n{ocr_text}"
        
        return {
            'name': self.extract_name(combined_text),
            'phone': self.extract_phone(combined_text),
            'partner_number': self.extract_partner_number(combined_text),
            'kakao': self.extract_kakao(combined_text)
        }


# ============================================================
# Step 7: 데이터 저장
# ============================================================

def save_to_csv(posts: List[Dict], filename: str) -> pd.DataFrame:
    """게시물 데이터를 CSV로 저장 (추천인 정보 자동 추출 포함)"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 추천인 정보 추출기 초기화
    extractor = ReferrerExtractor()
    
    print("\n추천인 정보 자동 추출 중...")
    extraction_stats = {'name': 0, 'phone': 0, 'partner_number': 0}
    
    rows = []
    for post in posts:
        # 본문과 OCR 텍스트에서 추천인 정보 추출
        content_text = post.get('content_text', '')
        ocr_text = post.get('ocr_text', '')
        referrer_info = extractor.extract_all(content_text, ocr_text)
        
        # 추출 통계
        if referrer_info['name']:
            extraction_stats['name'] += 1
        if referrer_info['phone']:
            extraction_stats['phone'] += 1
        if referrer_info['partner_number']:
            extraction_stats['partner_number'] += 1
        
        row = {
            # 기본 정보
            'platform': 'Naver Blog',
            'title': post['title'],
            'description': post.get('description', ''),
            'blogger_profile': post.get('blogger_profile', ''),
            'post_url': post['url'],
            'author_id': post.get('author_id', ''),
            
            # 콘텐츠 정보
            'content_text': content_text,
            'hashtags': ', '.join(post.get('hashtags', [])),
            'image_text': ocr_text,
            'video_text': post.get('video_transcripts', ''),
            'postdate': post.get('post_date', ''),
            
            # 미디어 정보
            'image_count': len(post.get('images', [])),
            'video_count': len(post.get('videos', [])),
            'video_urls': '|||'.join(post.get('videos', [])),
            
            # 참여 지표
            'view_count': post.get('view_count', ''),
            'like_count': post.get('like_count', ''),
            'comment_count': post.get('comment_count', ''),
            
            # 추천인 정보 (자동 추출)
            'referrer_name': referrer_info['name'],
            'referrer_phone': referrer_info['phone'],
            'partner_number': referrer_info['partner_number'],
            'kakao_id': referrer_info['kakao'],
            
            # 메타 정보
            'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        rows.append(row)
    
    # 추출 통계 출력
    print(f"✓ 추천인 정보 추출 완료:")
    print(f"  • 이름: {extraction_stats['name']}개 ({extraction_stats['name']/len(posts)*100:.1f}%)")
    print(f"  • 전화번호: {extraction_stats['phone']}개 ({extraction_stats['phone']/len(posts)*100:.1f}%)")
    print(f"  • 파트너번호: {extraction_stats['partner_number']}개 ({extraction_stats['partner_number']/len(posts)*100:.1f}%)")
    
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"\n✓ {len(df)}개 게시물을 {filename}에 저장했습니다")
    
    return df


def save_stats(stats: Dict, filename: str):
    """통계 정보를 JSON으로 저장"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 통계 정보를 {filename}에 저장했습니다")


# ============================================================
# 메인 실행 함수
# ============================================================

def main():
    print("=" * 70)
    print(" 네이버 블로그 크롤러 - PM-International Korea (개선 버전)")
    print("=" * 70)
    print(f"타겟 키워드: {len(SEARCH_KEYWORDS)}개")
    print(f"타겟 해시태그: {len(TARGET_HASHTAGS)}개")
    print(f"목표: 최소 100개 필터링된 게시물")
    print(f"OCR: {'사용' if USE_OCR else '미사용'}")
    print(f"Whisper: {'사용' if USE_WHISPER else '미사용'}")
    print("=" * 70)
    
    overall_stats = {
        'start_time': datetime.now().isoformat(),
        'config': {
            'search_keywords': SEARCH_KEYWORDS,
            'target_hashtags': TARGET_HASHTAGS,
            'use_ocr': USE_OCR,
            'use_whisper': USE_WHISPER
        }
    }
    
    # 동적 days_back 증가 로직
    days_back = DAYS_BACK
    filtered_posts = []
    all_crawled_posts = []
    
    while len(filtered_posts) < 100 and days_back <= 180:  # 최대 180일
        print(f"\n[Phase 1] URL 수집 중 (최근 {days_back}일)...")
        print("참고: 이 단계에서는 키워드가 제목/본문에 있는 모든 게시물을 수집합니다.")
        print("      실제 필터링은 크롤링 후 해시태그로 수행됩니다.\n")
        
        searcher = NaverBlogSearcher(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
        
        all_blog_urls = []
        for keyword in tqdm(SEARCH_KEYWORDS, desc="검색 중"):
            results = searcher.search_keyword(keyword, max_results=MAX_RESULTS_PER_KEYWORD, days_back=days_back)
            all_blog_urls.extend(results)
            
            if len(all_blog_urls) >= TARGET_POST_COUNT * 3:  # 여유있게 수집
                break
        
        # 중복 제거
        unique_urls = {item['link']: item for item in all_blog_urls}
        all_blog_urls = list(unique_urls.values())
        
        print(f"✓ 총 {len(all_blog_urls)}개 URL 수집 완료\n")
        
        # Phase 2: 본문 크롤링
        print("[Phase 2] 본문 크롤링 중...")
        print("참고: 해시태그를 추출하여 타겟 해시태그와 비교합니다.\n")
        
        crawler = NaverBlogCrawler(headless=True)
        
        crawled_posts = []
        for blog_info in tqdm(all_blog_urls, desc="크롤링 중"):
            post_data = crawler.crawl_blog_post(blog_info['link'])
            if post_data:
                post_data.update({
                    'post_date': blog_info['postdate'],
                    'author_name': blog_info['bloggername'],
                    'description': blog_info.get('description', ''),
                    'blogger_profile': blog_info.get('bloggerlink', '')
                })
                crawled_posts.append(post_data)
            time.sleep(0.5)
        
        crawler.close()
        
        print(f"✓ {len(crawled_posts)}개 게시물 크롤링 완료\n")
        
        # Phase 3: 해시태그 필터링
        print("[Phase 3] 해시태그 필터링 중...")
        print("참고: 타겟 해시태그가 실제로 포함된 게시물만 선별합니다.\n")
        
        filtered_posts, filter_stats = filter_by_hashtags(crawled_posts, TARGET_HASHTAGS)
        all_crawled_posts.extend(crawled_posts)
        
        print(f"✓ 필터링 전: {filter_stats['total_posts']}개")
        print(f"✓ 필터링 후: {filter_stats['filtered_posts']}개")
        
        if len(filtered_posts) >= 100:
            print(f"\n✅ 목표 달성! {len(filtered_posts)}개 수집 완료")
            break
        else:
            print(f"\n⚠️  현재 {len(filtered_posts)}개 수집됨. 기간을 30일 연장합니다...")
            days_back += 30
    
    overall_stats['final_days_back'] = days_back
    overall_stats['phase1_collected_urls'] = len(all_blog_urls)
    overall_stats['phase2_crawled_posts'] = len(all_crawled_posts)
    overall_stats['phase3_filtering'] = filter_stats
    
    print(f"✓ 필터링 전: {filter_stats['total_posts']}개")
    print(f"✓ 필터링 후: {filter_stats['filtered_posts']}개")
    print(f"✓ 해시태그 없는 게시물: {filter_stats['posts_without_hashtags']}개")
    print(f"✓ 필터링 비율: {filter_stats['filtered_posts'] / max(filter_stats['total_posts'], 1) * 100:.1f}%")
    
    if filter_stats['matched_hashtags']:
        print("\n매칭된 해시태그 TOP 5:")
        sorted_tags = sorted(filter_stats['matched_hashtags'].items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:5]:
            print(f"  {tag}: {count}개")
    
    if len(filtered_posts) == 0:
        print("\n[경고] 타겟 해시태그를 포함한 게시물이 없습니다!")
        print("해결 방법:")
        print("  1. TARGET_HASHTAGS 설정을 확인하세요")
        print("  2. SEARCH_KEYWORDS를 더 넓게 설정하세요")
        print("  3. DAYS_BACK 기간을 늘려보세요")
        return
    
    print()
    
    # Phase 4: OCR
    if USE_OCR:
        print("[Phase 4] 이미지 OCR 처리 중...")
        print("비용: 무료 (EasyOCR, 로컬 실행)")
        print("성능: CPU 1-3초/이미지, GPU 0.1-0.5초/이미지\n")
        
        ocr = OCRProcessor(languages=['ko', 'en'], gpu=False)
        
        for post in tqdm(filtered_posts, desc="OCR 처리"):
            ocr_texts = []
            for img_url in post['images'][:MAX_IMAGES_PER_POST]:
                text, proc_time = ocr.extract_text_from_url(img_url, OCR_CONFIDENCE_THRESHOLD)
                if text:
                    ocr_texts.append(text)
            post['ocr_text'] = '\n---\n'.join(ocr_texts)
        
        ocr_stats = ocr.get_stats()
        overall_stats['phase4_ocr'] = ocr_stats
        
        print("\nOCR 성능 통계:")
        for key, value in ocr_stats.items():
            print(f"  {key}: {value}")
        print()
    
    # Phase 5: 동영상 스크립트
    print("[Phase 5] 동영상 스크립트 추출 중...")
    print("비용: 무료")
    print("  - YouTube 자막: youtube-transcript-api")
    if USE_WHISPER:
        print(f"  - Whisper 음성인식: {WHISPER_MODEL} 모델")
    print()
    
    video_extractor = VideoTranscriptExtractor(use_whisper=USE_WHISPER, whisper_model=WHISPER_MODEL)
    
    for post in tqdm(filtered_posts, desc="동영상 처리"):
        transcripts = []
        for video_url in post['videos']:
            transcript = video_extractor.extract_transcript(video_url)
            if transcript:
                transcripts.append(transcript)
        post['video_transcripts'] = '\n---\n'.join(transcripts)
    
    video_stats = video_extractor.get_stats()
    overall_stats['phase5_video'] = video_stats
    
    print("\n동영상 처리 통계:")
    for key, value in video_stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Phase 6: 저장
    print("[Phase 6] 데이터 저장 중...")
    df = save_to_csv(filtered_posts, OUTPUT_CSV)
    
    overall_stats['end_time'] = datetime.now().isoformat()
    overall_stats['final_post_count'] = len(filtered_posts)
    
    save_stats(overall_stats, STATS_FILE)
    
    # 최종 요약
    print("\n" + "=" * 70)
    print(" 수집 완료!")
    print("=" * 70)
    print(f"✓ 검색된 URL: {overall_stats['phase1_collected_urls']}개")
    print(f"✓ 크롤링 성공: {overall_stats['phase2_crawled_posts']}개")
    print(f"✓ 해시태그 필터링 후: {len(filtered_posts)}개")
    print(f"✓ 필터링 비율: {len(filtered_posts) / max(overall_stats['phase2_crawled_posts'], 1) * 100:.1f}%")
    print(f"\n✓ CSV 파일: {OUTPUT_CSV}")
    print(f"✓ 통계 파일: {STATS_FILE}")
    print("=" * 70)
    
    # 성능 평가 가이드
    print("\n[성능 평가 가이드]")
    print("1. OCR 정확도 확인:")
    print("   - output CSV에서 ocr_text 컬럼을 확인하세요")
    print("   - 샘플 이미지와 비교하여 정확도를 측정하세요")
    print("   - 평균 신뢰도(confidence)를 참고하세요")
    print("\n2. 동영상 스크립트 확인:")
    print("   - output CSV에서 video_transcripts 컬럼을 확인하세요")
    print("   - YouTube 자막은 거의 100% 정확합니다")
    print("   - Whisper는 85-95% 정확도입니다")
    print("\n3. 필터링 정확도 확인:")
    print("   - 통계 파일에서 매칭된 해시태그를 확인하세요")
    print("   - 샘플 게시물을 직접 확인하여 검증하세요")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n작업이 중단되었습니다.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()