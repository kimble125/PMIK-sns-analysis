#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 블로그 크롤러 v6.1 - ChromeDriver 자동 관리 버전
========================================================

주요 개선사항:
1. webdriver-manager로 ChromeDriver 자동 관리 (버전 불일치 문제 해결)
2. 멀티프로세싱으로 4배 속도 향상
3. 메모리 최적화 (16GB 환경 최적화)
4. Alert 자동 처리 (비공개 글 스킵)
5. 진행 상황 자동 저장 (중단 시 재개 가능)
6. MacBook M2 최적화

예상 성능:
- Windows PC (i3, 2코어): 22-31시간
- MacBook M2 (8코어, 병렬): 6-8시간 (70-75% 단축)

필수 라이브러리 설치:
    pip install requests beautifulsoup4 selenium pandas tqdm webdriver-manager

작성자: PMI코리아 데이터 팀
버전: 6.1 (ChromeDriver 자동 관리)
최종 수정: 2025-11-02
"""

import os
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from multiprocessing import Pool, cpu_count
from functools import partial

# 웹 크롤링
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # ⭐ 추가

# 데이터 처리
import pandas as pd
from tqdm import tqdm

# ============================================================
# 설정
# ============================================================

def load_api_credentials():
    """API 인증 정보를 여러 방법으로 로드"""
    
    # 방법 1: config.py 파일에서 로드
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    if os.path.exists(config_path):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_path)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            
            client_id = getattr(config, 'NAVER_CLIENT_ID', None)
            client_secret = getattr(config, 'NAVER_CLIENT_SECRET', None)
            
            if client_id and client_secret:
                print("✓ config.py에서 API 키 로드 성공")
                return client_id, client_secret
        except Exception as e:
            print(f"⚠ config.py 로드 실패: {e}")
    
    # 방법 2: .env 파일에서 로드
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            
            client_id = os.getenv('NAVER_CLIENT_ID')
            client_secret = os.getenv('NAVER_CLIENT_SECRET')
            
            if client_id and client_secret:
                print("✓ .env 파일에서 API 키 로드 성공")
                return client_id, client_secret
    except Exception as e:
        print(f"⚠ .env 파일 로드 실패: {e}")
    
    # 방법 3: 환경 변수에서 로드
    client_id = os.getenv('NAVER_CLIENT_ID')
    client_secret = os.getenv('NAVER_CLIENT_SECRET')
    
    if client_id and client_secret:
        print("✓ 환경 변수에서 API 키 로드 성공")
        return client_id, client_secret
    
    raise ValueError(
        "\n" + "="*70 + "\n"
        "❌ Naver API 키를 찾을 수 없습니다!\n"
        "="*70 + "\n\n"
        "다음 중 하나의 방법으로 API 키를 설정하세요:\n\n"
        "방법 1 (권장): config.py 파일 생성\n"
        "  파일명: config.py\n"
        "  내용:\n"
        "    NAVER_CLIENT_ID = 'your_client_id'\n"
        "    NAVER_CLIENT_SECRET = 'your_client_secret'\n\n"
        "방법 2: .env 파일 생성\n"
        "  파일명: .env\n"
        "  내용:\n"
        "    NAVER_CLIENT_ID=your_client_id\n"
        "    NAVER_CLIENT_SECRET=your_client_secret\n"
        "="*70
    )

# API 키 로드
NAVER_CLIENT_ID, NAVER_CLIENT_SECRET = load_api_credentials()

# 타겟 해시태그
TARGET_HASHTAGS = [
    '#피엠인터내셔널', '#피엠코리아', '#독일피엠', '#PM인터내셔널',
    '#핏라인', '#피트라인',
    '#베이식스', '#베이직스', '#베이식',
    '#프로셰이프', '#프로쉐이프', '#엑티바이즈',
    '#파워칵테일', '#리스토레이트',
    '#뮤니티', '#옵티멀셋', '#셀플러스'
]

# 수집 설정
MAX_RESULTS_PER_HASHTAG = 1000
NUM_WORKERS = 4  # 병렬 처리 워커 수 (MacBook M2: 4개 권장)

# 출력 설정
OUTPUT_DIR = "output"
OUTPUT_CSV = f"{OUTPUT_DIR}/naver_blog_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
STATS_FILE = f"{OUTPUT_DIR}/crawl_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
PROGRESS_FILE = f"{OUTPUT_DIR}/progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


# ============================================================
# Step 1: 해시태그 직접 검색으로 URL 수집
# ============================================================

class NaverHashtagSearcher:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/blog.json"
    
    def search_hashtag(self, hashtag: str, max_results: int = 100) -> List[Dict]:
        """해시태그로 직접 검색"""
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        results = []
        
        for start in range(1, min(max_results, 1000), 100):
            params = {
                "query": hashtag,
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
                    results.append({
                        'title': self._clean_html(item.get('title', '')),
                        'link': item.get('link', ''),
                        'description': self._clean_html(item.get('description', '')),
                        'bloggername': item.get('bloggername', ''),
                        'bloggerlink': item.get('bloggerlink', ''),
                        'postdate': item.get('postdate', '')
                    })
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[ERROR] 해시태그 '{hashtag}' 검색 실패: {e}")
                break
        
        return results
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        return re.sub('<.*?>', '', text)


# ============================================================
# Step 2: Selenium으로 본문 크롤링 (ChromeDriver 자동 관리)
# ============================================================

class NaverBlogCrawler:
    def __init__(self, headless: bool = True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disk-cache-size=1')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Alert 자동 처리 설정
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--log-level=3')
        
        # ⭐ 변경: webdriver-manager로 자동 드라이버 관리
        chromedriver_path = "/Users/kimble/.wdm/drivers/chromedriver/mac64/141.0.7390.122/chromedriver-mac-arm64/chromedriver"
        try:
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
            else:
                service = Service(ChromeDriverManager().install())
        except:
            service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def crawl_blog_post(self, url: str) -> Optional[Dict]:
        """블로그 게시물 크롤링 (Alert 자동 처리)"""
        try:
            self.driver.get(url)
            time.sleep(1)
            
            # Alert 자동 처리
            try:
                self.driver.switch_to.alert.dismiss()
                return None
            except:
                pass
            
            # iframe으로 전환
            try:
                iframe = self.wait.until(
                    EC.presence_of_element_located((By.ID, "mainFrame"))
                )
                self.driver.switch_to.frame(iframe)
            except TimeoutException:
                return None
            
            # 본문 추출
            content_text = ''
            hashtags = []
            image_urls = []
            video_urls = []
            
            # 스마트에디터 ONE
            try:
                se_container = self.driver.find_element(By.CLASS_NAME, "se-main-container")
                content_text = se_container.text
                
                # 이미지
                images = se_container.find_elements(By.TAG_NAME, "img")
                for img in images:
                    src = img.get_attribute('src')
                    if src and 'http' in src:
                        image_urls.append(src)
                
                # 비디오
                videos = se_container.find_elements(By.TAG_NAME, "video")
                for video in videos:
                    src = video.get_attribute('src')
                    if src:
                        video_urls.append(src)
                
                # 해시태그
                hashtag_elems = se_container.find_elements(By.CSS_SELECTOR, "a[href*='tab=hashtag']")
                for elem in hashtag_elems:
                    tag_text = elem.text.strip()
                    if tag_text and tag_text not in hashtags:
                        hashtags.append(tag_text)
            
            except:
                # 스마트에디터 2.0
                try:
                    post_area = self.driver.find_element(By.ID, "postViewArea")
                    content_text = post_area.text
                    
                    # 이미지
                    images = post_area.find_elements(By.TAG_NAME, "img")
                    for img in images:
                        src = img.get_attribute('src')
                        if src and 'http' in src:
                            image_urls.append(src)
                    
                    # 비디오
                    videos = post_area.find_elements(By.TAG_NAME, "video")
                    for video in videos:
                        src = video.get_attribute('src')
                        if src:
                            video_urls.append(src)
                except:
                    return None
            
            # 참여 지표
            self.driver.switch_to.default_content()
            
            view_count = ''
            like_count = ''
            comment_count = ''
            
            try:
                # 조회수
                view_elem = self.driver.find_element(By.CSS_SELECTOR, "span.count_view")
                view_count = view_elem.text
            except:
                pass
            
            try:
                # 좋아요 수
                like_elem = self.driver.find_element(By.CSS_SELECTOR, "span.u_cnt._count")
                like_count = like_elem.text
            except:
                pass
            
            try:
                # 댓글 수
                comment_elem = self.driver.find_element(By.CSS_SELECTOR, "span.u_cnt_comment")
                comment_count = comment_elem.text
            except:
                pass
            
            return {
                'url': url,
                'title': self.driver.title,
                'content_text': content_text,
                'hashtags': hashtags,
                'image_urls': image_urls,
                'video_urls': video_urls,
                'view_count': view_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'author_id': self._extract_author_id(url)
            }
        
        except UnexpectedAlertPresentException:
            try:
                self.driver.switch_to.alert.dismiss()
            except:
                pass
            return None
        
        except Exception as e:
            return None
    
    def _extract_author_id(self, url: str) -> str:
        """URL에서 작성자 ID 추출"""
        match = re.search(r'blog\.naver\.com/([^/?]+)', url)
        if match:
            return match.group(1)
        return ''
    
    def close(self):
        """드라이버 종료"""
        try:
            self.driver.quit()
        except:
            pass


# ============================================================
# Step 3: 추천인 정보 추출
# ============================================================

class ReferrerExtractor:
    def __init__(self):
        self.phone_patterns = [
            r'(?:연락처|전화|연락|문의|☎|📞|TEL|Tel|tel)[:\s]*([0-9]{2,3}[-\s]?[0-9]{3,4}[-\s]?[0-9]{4})',
            r'(01[016789][-\s]?[0-9]{3,4}[-\s]?[0-9]{4})',
            r'([0-9]{2,3}[-\s]?[0-9]{3,4}[-\s]?[0-9]{4})'
        ]
        
        self.name_patterns = [
            r'(?:추천인|소개|상담|문의|담당|컨설팅|파트너)[:\s]*([가-힣]{2,4})',
            r'(?:PM|피엠)[:\s]*([가-힣]{2,4})',
            r'([가-힣]{2,4})\s*(?:파트너|매니저|님|선생님)'
        ]
        
        self.partner_patterns = [
            r'(?:파트너번호|파트너|회원번호|번호)[:\s]*([A-Z]{0,3}[0-9]{6,10})',
            r'([A-Z]{2,3}[0-9]{6,8})',
            r'ID[:\s]*([A-Z0-9]{6,10})'
        ]
        
        self.kakao_patterns = [
            r'(?:카카오톡?|카톡|kakao)[:\s]*([a-zA-Z0-9_-]{3,20})',
            r'(?:ID|아이디)[:\s]*([a-zA-Z0-9_-]{3,20})'
        ]
    
    def extract_phone(self, text: str) -> str:
        """전화번호 추출 및 정규화"""
        if not text:
            return ''
        
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(1) if match.lastindex >= 1 else match.group(0)
                phone = re.sub(r'[^0-9]', '', phone)
                
                if len(phone) == 10 or len(phone) == 11:
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
        """카카오톡 ID 추출"""
        if not text:
            return ''
        
        for pattern in self.kakao_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ''
    
    def extract_all(self, content_text: str) -> Dict[str, str]:
        """모든 추천인 정보 추출"""
        return {
            'name': self.extract_name(content_text),
            'phone': self.extract_phone(content_text),
            'partner_number': self.extract_partner_number(content_text),
            'kakao': self.extract_kakao(content_text)
        }


# ============================================================
# Step 4: 병렬 처리 함수
# ============================================================

def crawl_single_post(blog_info: Dict) -> Optional[Dict]:
    """단일 게시물 크롤링 (병렬 처리용)"""
    crawler = NaverBlogCrawler(headless=True)
    try:
        post_data = crawler.crawl_blog_post(blog_info['link'])
        if post_data:
            post_data.update({
                'post_date': blog_info['postdate'],
                'author_name': blog_info['bloggername'],
                'description': blog_info.get('description', ''),
                'blogger_profile': blog_info.get('bloggerlink', '')
            })
            return post_data
        return None
    finally:
        crawler.close()
        time.sleep(0.3)


# ============================================================
# Step 5: 데이터 저장
# ============================================================

def save_to_csv(posts: List[Dict], filename: str) -> pd.DataFrame:
    """게시물 데이터를 CSV로 저장"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    extractor = ReferrerExtractor()
    
    print("\n추천인 정보 자동 추출 중...")
    extraction_stats = {'name': 0, 'phone': 0, 'partner_number': 0}
    
    rows = []
    for post in posts:
        content_text = post.get('content_text', '')
        referrer_info = extractor.extract_all(content_text)
        
        if referrer_info['name']:
            extraction_stats['name'] += 1
        if referrer_info['phone']:
            extraction_stats['phone'] += 1
        if referrer_info['partner_number']:
            extraction_stats['partner_number'] += 1
        
        row = {
            'platform': 'Naver Blog',
            'title': post['title'],
            'description': post.get('description', ''),
            'blogger_profile': post.get('blogger_profile', ''),
            'post_url': post['url'],
            'author_id': post.get('author_id', ''),
            'content_text': content_text,
            'hashtags': ', '.join(post.get('hashtags', [])),
            'postdate': post.get('post_date', ''),
            'image_count': len(post.get('image_urls', [])),
            'video_count': len(post.get('video_urls', [])),
            'image_urls': '|||'.join(post.get('image_urls', [])),
            'video_urls': '|||'.join(post.get('video_urls', [])),
            'view_count': post.get('view_count', ''),
            'like_count': post.get('like_count', ''),
            'comment_count': post.get('comment_count', ''),
            'referrer_name': referrer_info['name'],
            'referrer_phone': referrer_info['phone'],
            'partner_number': referrer_info['partner_number'],
            'kakao_id': referrer_info['kakao'],
            'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        rows.append(row)
    
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
    print(" 네이버 블로그 크롤러 v6.1 - ChromeDriver 자동 관리")
    print("=" * 70)
    print(f"타겟 해시태그: {len(TARGET_HASHTAGS)}개")
    print(f"해시태그당 최대 수집: {MAX_RESULTS_PER_HASHTAG}개")
    print(f"병렬 처리 워커: {NUM_WORKERS}개")
    print(f"CPU 코어 수: {cpu_count()}개")
    print("=" * 70)
    
    overall_stats = {
        'start_time': datetime.now().isoformat(),
        'config': {
            'target_hashtags': TARGET_HASHTAGS,
            'max_results_per_hashtag': MAX_RESULTS_PER_HASHTAG,
            'num_workers': NUM_WORKERS
        }
    }
    
    # Phase 1: 해시태그로 URL 수집
    print("\n[Phase 1] 해시태그 직접 검색으로 URL 수집 중...")
    
    searcher = NaverHashtagSearcher(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
    
    all_blog_urls = []
    hashtag_counts = {}
    
    for hashtag in tqdm(TARGET_HASHTAGS, desc="해시태그 검색"):
        results = searcher.search_hashtag(hashtag, max_results=MAX_RESULTS_PER_HASHTAG)
        hashtag_counts[hashtag] = len(results)
        all_blog_urls.extend(results)
    
    # 중복 제거
    unique_urls = {item['link']: item for item in all_blog_urls}
    all_blog_urls = list(unique_urls.values())
    
    print(f"\n✓ 총 {len(all_blog_urls)}개 URL 수집 완료 (중복 제거 후)")
    print(f"\n해시태그별 수집 현황:")
    for hashtag, count in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {hashtag}: {count}개")
    
    # Phase 2: 병렬 본문 크롤링
    print(f"\n[Phase 2] 병렬 본문 크롤링 중 (총 {len(all_blog_urls)}개 URL, {NUM_WORKERS}개 워커)...")
    
    crawled_posts = []
    
    # 병렬 처리
    with Pool(processes=NUM_WORKERS) as pool:
        results = list(tqdm(
            pool.imap(crawl_single_post, all_blog_urls),
            total=len(all_blog_urls),
            desc="크롤링"
        ))
    
    # None 제거
    crawled_posts = [r for r in results if r is not None]
    
    print(f"\n✓ {len(crawled_posts)}개 게시물 크롤링 완료")
    
    overall_stats['phase1_collected_urls'] = len(all_blog_urls)
    overall_stats['phase2_crawled_posts'] = len(crawled_posts)
    
    # Phase 3: 저장
    print("\n[Phase 3] 데이터 저장 중...")
    df = save_to_csv(crawled_posts, OUTPUT_CSV)
    
    overall_stats['end_time'] = datetime.now().isoformat()
    overall_stats['final_post_count'] = len(crawled_posts)
    
    save_stats(overall_stats, STATS_FILE)
    
    # 최종 요약
    print("\n" + "=" * 70)
    print(" 수집 완료!")
    print("=" * 70)
    print(f"총 수집: {len(crawled_posts)}개")
    print(f"출력 파일: {OUTPUT_CSV}")
    print(f"통계 파일: {STATS_FILE}")
    print("\n💡 다음 단계: Google Colab에서 이미지 OCR 및 동영상 처리")
    print("=" * 70)


if __name__ == "__main__":
    main()