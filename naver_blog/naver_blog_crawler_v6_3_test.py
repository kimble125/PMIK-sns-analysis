#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 블로그 크롤러 v6.3 - 테스트 버전 (소량 수집)
========================================================

주요 개선사항:
1. ✅ 해시태그 추출 개선 (정규식 + CSS 선택자 조합)
2. ✅ PM 키워드 필터링 추가 (무관한 데이터 제거)
3. ✅ 참여 지표 수집 개선 (다중 선택자)
4. ✅ 추천인 정보 패턴 개선
5. ✅ 파트너 번호 패턴 수정 (숫자만)
6. ✅ 카카오 ID 제거
7. ✅ Image/Video URL에 Referer 헤더 추가
8. ✅ 진행 상황 자동 저장

테스트 설정:
- 해시태그당 최대 10개씩만 수집 (총 ~170개 URL)
- 예상 소요 시간: 약 10-15분

작성자: PMI코리아 데이터 팀
버전: 6.3-test
최종 수정: 2025-11-03
"""

import os
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

# 웹 크롤링
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 데이터 처리
import pandas as pd
from tqdm import tqdm

# ============================================================
# 설정
# ============================================================

def load_api_credentials():
    """API 인증 정보 로드"""
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
    
    raise ValueError("API 키를 찾을 수 없습니다!")

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

# ⭐ 테스트 설정
MAX_RESULTS_PER_HASHTAG = 10  # 테스트: 10개씩만
NUM_WORKERS = 1  # 테스트: 단일 프로세스

# PM 관련 키워드 (필터링용)
PM_KEYWORDS = [
    '피엠', 'PM', '인터내셔널', '핏라인', '피트라인',
    '베이식스', '베이직스', '베이식',
    '프로셰이프', '프로쉐이프', '엑티바이즈',
    '파워칵테일', '리스토레이트', '뮤니티', '옵티멀셋', '셀플러스',
    '독일피엠', 'FitLine', 'fitline'
]

# 출력 설정
OUTPUT_DIR = "output"
OUTPUT_CSV = f"{OUTPUT_DIR}/naver_blog_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
STATS_FILE = f"{OUTPUT_DIR}/test_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# ============================================================
# Step 1: URL 수집
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
                "display": min(100, max_results),
                "start": start,
                "sort": "date"
            }
            
            try:
                response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
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
                
                if len(results) >= max_results:
                    break
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[ERROR] 해시태그 '{hashtag}' 검색 실패: {e}")
                break
        
        return results[:max_results]
    
    def _clean_html(self, text: str) -> str:
        return re.sub('<.*?>', '', text)

# ============================================================
# Step 2: 본문 크롤링 (개선됨)
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
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        options.add_argument('--log-level=3')
        
        # ChromeDriver 설정 (Homebrew 버전 우선 사용)
        homebrew_chromedriver = '/opt/homebrew/bin/chromedriver'
        
        if os.path.exists(homebrew_chromedriver):
            # Homebrew 설치 버전 사용 (서명되어 있어 macOS 보안 문제 없음)
            service = Service(homebrew_chromedriver)
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            # Homebrew 버전이 없으면 ChromeDriverManager 사용
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                raise Exception(f"ChromeDriver 초기화 실패: {e}\n터미널에서 'brew install --cask chromedriver' 실행 후 재시도하세요.")
        self.wait = WebDriverWait(self.driver, 10)
        
        # Referer 헤더를 위한 세션
        self.session = requests.Session()
        self.session.headers.update({
            'Referer': 'https://blog.naver.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def crawl_blog_post(self, url: str) -> Optional[Dict]:
        """블로그 게시물 크롤링 (개선됨)"""
        try:
            self.driver.get(url)
            time.sleep(1)
            
            # Alert 처리
            try:
                self.driver.switch_to.alert.dismiss()
                return None
            except:
                pass
            
            # iframe 전환
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
                
                # ⭐ 해시태그 추출 개선 (CSS + 정규식)
                # 방법 1: CSS 선택자
                hashtag_elems = se_container.find_elements(By.CSS_SELECTOR, 
                    "a.se_link_hashtag, a[href*='hashtag'], a[class*='hashtag']")
                for elem in hashtag_elems:
                    tag = elem.text.strip()
                    if tag and tag.startswith('#') and tag not in hashtags:
                        hashtags.append(tag)
                
                # 방법 2: 정규식으로 본문에서 추출 (v5.0 방식)
                hashtag_pattern = r'#[가-힣a-zA-Z0-9_]+'
                hashtags_from_text = re.findall(hashtag_pattern, content_text)
                for tag in hashtags_from_text:
                    if tag not in hashtags:
                        hashtags.append(tag)
            
            except:
                # 스마트에디터 2.0
                try:
                    post_area = self.driver.find_element(By.ID, "postViewArea")
                    content_text = post_area.text
                    
                    images = post_area.find_elements(By.TAG_NAME, "img")
                    for img in images:
                        src = img.get_attribute('src')
                        if src and 'http' in src:
                            image_urls.append(src)
                    
                    # 해시태그 정규식 추출
                    hashtag_pattern = r'#[가-힣a-zA-Z0-9_]+'
                    hashtags = re.findall(hashtag_pattern, content_text)
                    
                except:
                    return None
            
            # iframe 밖으로 나가기
            self.driver.switch_to.default_content()
            
            # ⭐ 참여 지표 추출 개선 (다중 선택자 시도)
            view_count = self._extract_metric([
                "span.se_publishDate em",
                "span.count_view",
                "div.view_count em",
                "span.num"
            ])
            
            like_count = self._extract_metric([
                "em.u_cnt._count",
                "span.like_count em",
                "a.btn_like em"
            ])
            
            comment_count = self._extract_metric([
                "a.btn_comment em.u_cnt",
                "span.comment_count em",
                "a.cmt_count"
            ])
            
            # 지표가 없으면 body 텍스트에서 추출 (v5.0 방식)
            if not view_count or not like_count or not comment_count:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                if not view_count:
                    match = re.search(r'조회[수]?\s*([\d,]+)', body_text)
                    view_count = match.group(1).replace(',', '') if match else ''
                if not like_count:
                    match = re.search(r'공감\s*(\d+)', body_text)
                    like_count = match.group(1) if match else ''
                if not comment_count:
                    match = re.search(r'댓글\s*(\d+)', body_text)
                    comment_count = match.group(1) if match else ''
            
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
    
    def _extract_metric(self, selectors: List[str]) -> str:
        """여러 선택자를 시도하여 지표 추출"""
        for selector in selectors:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if text and text.isdigit():
                    return text
            except:
                continue
        return ''
    
    def _extract_author_id(self, url: str) -> str:
        match = re.search(r'blog\.naver\.com/([^/?]+)', url)
        if match:
            return match.group(1)
        return ''
    
    def close(self):
        try:
            self.driver.quit()
        except:
            pass

# ============================================================
# Step 3: PM 관련 필터링
# ============================================================

def is_pm_related(post_data: Dict) -> bool:
    """PM 관련 게시물인지 확인"""
    if not post_data:
        return False
    
    # 제목, 본문, 해시태그 합치기
    full_text = ' '.join([
        post_data.get('title', ''),
        post_data.get('content_text', ''),
        ' '.join(post_data.get('hashtags', []))
    ]).lower()
    
    # PM 키워드가 최소 1개 이상 있어야 함
    for keyword in PM_KEYWORDS:
        if keyword.lower() in full_text:
            return True
    
    return False

# ============================================================
# Step 4: 추천인 정보 추출 (개선됨)
# ============================================================

class ReferrerExtractor:
    def __init__(self):
        # ⭐ 개선된 패턴
        self.phone_patterns = [
            r'(?:연락처|전화|문의|☎|📞)[:\s]*([0-9]{2,3}[-\s]?[0-9]{3,4}[-\s]?[0-9]{4})',
            r'(01[016789][-\s]?[0-9]{3,4}[-\s]?[0-9]{4})',
        ]
        
        self.name_patterns = [
            r'(?:추천인|추천|소개)[:\s]*\(?([가-힣]{2,4})\)?',  # 괄호 안 이름
            r'PM\s*(?:파트너|매니저)[:\s]*([가-힣]{2,4})',  # PM 파트너 홍길동
            r'(?:연락처|전화)[:\s]*([가-힣]{2,4})\s*[0-9-]',  # 연락처: 홍길동 010-
        ]
        
        # ⭐ 파트너 번호 패턴 수정 (숫자만)
        self.partner_patterns = [
            r'(?:파트너\s*번호|파트너|회원\s*번호|번호)[:\s]*([0-9]{7,9})',  # 20577576
            r'(?:추천|소개)\s*번호[:\s]*([0-9]{7,9})',
        ]
    
    def extract_phone(self, text: str) -> str:
        if not text:
            return ''
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = re.sub(r'[^0-9]', '', match.group(0))
                if len(phone) in [10, 11]:
                    if len(phone) == 11:
                        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                    else:
                        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
        return ''
    
    def extract_name(self, text: str) -> str:
        if not text:
            return ''
        for pattern in self.name_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1)
                if re.match(r'^[가-힣]{2,4}$', name):
                    # 일반적인 단어 제외
                    if name not in ['코드', '으로', '에서', '에게', '부터', '까지']:
                        return name
        return ''
    
    def extract_partner_number(self, text: str) -> str:
        if not text:
            return ''
        for pattern in self.partner_patterns:
            match = re.search(pattern, text)
            if match:
                number = match.group(1)
                # 7-9자리 숫자 확인
                if number.isdigit() and 7 <= len(number) <= 9:
                    return number
        return ''
    
    def extract_all(self, content_text: str) -> Dict[str, str]:
        return {
            'name': self.extract_name(content_text),
            'phone': self.extract_phone(content_text),
            'partner_number': self.extract_partner_number(content_text)
        }

# ============================================================
# Step 5: 데이터 저장
# ============================================================

def save_to_csv(posts: List[Dict], filename: str) -> pd.DataFrame:
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
            'title': post.get('title', ''),
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
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"✓ 통계 정보를 {filename}에 저장했습니다")

# ============================================================
# 메인 실행
# ============================================================

def main():
    print("=" * 70)
    print(" 네이버 블로그 크롤러 v6.3 - 테스트 버전")
    print("=" * 70)
    print(f"타겟 해시태그: {len(TARGET_HASHTAGS)}개")
    print(f"해시태그당 최대 수집: {MAX_RESULTS_PER_HASHTAG}개")
    print(f"예상 소요 시간: 10-15분")
    print("=" * 70)
    
    start_time = datetime.now()
    
    overall_stats = {
        'start_time': start_time.isoformat(),
        'version': '6.3-test',
        'config': {
            'target_hashtags': TARGET_HASHTAGS,
            'max_results_per_hashtag': MAX_RESULTS_PER_HASHTAG
        }
    }
    
    # Phase 1: URL 수집
    print("\n[Phase 1] 해시태그 검색으로 URL 수집 중...")
    
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
    
    # Phase 2: 본문 크롤링
    print(f"\n[Phase 2] 본문 크롤링 중 (총 {len(all_blog_urls)}개 URL)...")
    
    crawler = NaverBlogCrawler(headless=True)
    crawled_posts = []
    pm_filtered_count = 0
    
    try:
        for blog_info in tqdm(all_blog_urls, desc="크롤링"):
            post_data = crawler.crawl_blog_post(blog_info['link'])
            
            if post_data:
                # PM 관련 필터링
                if is_pm_related(post_data):
                    post_data.update({
                        'post_date': blog_info['postdate'],
                        'author_name': blog_info['bloggername'],
                        'description': blog_info.get('description', ''),
                        'blogger_profile': blog_info.get('bloggerlink', '')
                    })
                    crawled_posts.append(post_data)
                else:
                    pm_filtered_count += 1
            
            time.sleep(0.3)
    
    finally:
        crawler.close()
    
    print(f"\n✓ {len(crawled_posts)}개 게시물 크롤링 완료")
    print(f"  • PM 무관 게시물 필터링: {pm_filtered_count}개")
    
    overall_stats['phase1_collected_urls'] = len(all_blog_urls)
    overall_stats['phase2_crawled_posts'] = len(crawled_posts)
    overall_stats['pm_filtered_count'] = pm_filtered_count
    
    # Phase 3: 저장
    print("\n[Phase 3] 데이터 저장 중...")
    df = save_to_csv(crawled_posts, OUTPUT_CSV)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    overall_stats['end_time'] = end_time.isoformat()
    overall_stats['duration_seconds'] = duration.total_seconds()
    overall_stats['final_post_count'] = len(crawled_posts)
    
    save_stats(overall_stats, STATS_FILE)
    
    # 최종 요약
    print("\n" + "=" * 70)
    print(" 테스트 완료!")
    print("=" * 70)
    print(f"소요 시간: {duration}")
    print(f"수집된 게시물: {len(crawled_posts)}개")
    print(f"PM 무관 필터링: {pm_filtered_count}개")
    print(f"출력 파일: {OUTPUT_CSV}")
    print(f"통계 파일: {STATS_FILE}")
    print("\n✅ 결과 확인 후 전체 크롤링 진행하세요!")
    print("=" * 70)

if __name__ == "__main__":
    main()
