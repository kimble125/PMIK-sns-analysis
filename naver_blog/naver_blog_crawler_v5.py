#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 블로그 크롤러 v5.0 - PM-International Korea SNS 분석
========================================================

주요 변경사항:
1. 키워드 검색 제거 → 해시태그 직접 검색만 사용
2. OCR/동영상 처리 제거 → URL만 수집 (Colab에서 별도 처리)
3. 추천인 정보 자동 추출 추가
4. 경량화된 빠른 수집

출력 컬럼 (17개):
- 기본 정보 (6): platform, title, description, blogger_profile, post_url, author_id
- 콘텐츠 정보 (3): content_text, hashtags, postdate
- 미디어 정보 (3): image_count, video_count, image_urls, video_urls
- 참여 지표 (3): view_count, like_count, comment_count
- 추천인 정보 (4): referrer_name, referrer_phone, partner_number, kakao_id
- 메타 정보 (1): collected_at

필수 라이브러리:
    pip install requests beautifulsoup4 selenium pandas tqdm

작성자: PMI코리아 데이터 팀
버전: 5.0
최종 수정: 2025-11-01
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
from selenium.common.exceptions import TimeoutException

# 데이터 처리
import pandas as pd
from tqdm import tqdm

# ============================================================
# 설정
# ============================================================

# Naver API 인증 정보
# 방법 1: config.py 파일에서 로드 (권장)
# 방법 2: 환경 변수에서 로드
# 방법 3: 직접 입력 (테스트용)

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
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            # BOM 제거하여 읽기
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
    
    # 모든 방법 실패
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
        "    NAVER_CLIENT_SECRET=your_client_secret\n\n"
        "방법 3: 환경 변수 설정\n"
        "  Windows PowerShell:\n"
        "    $env:NAVER_CLIENT_ID='your_client_id'\n"
        "    $env:NAVER_CLIENT_SECRET='your_client_secret'\n"
        "="*70
    )

# API 키 로드
NAVER_CLIENT_ID, NAVER_CLIENT_SECRET = load_api_credentials()

# 타겟 해시태그 (한글만 - 영어는 해시태그 한정 검색이 안되어 허수가 다수)
TARGET_HASHTAGS = [
    # 브랜드명
    '#피엠인터내셔널',
    '#피엠코리아', 
    '#독일피엠',
    '#PM인터내셔널',
    
    # 주력 제품 라인
    '#핏라인',
    '#피트라인',
    
    # 개별 제품명
    '#베이식스',
    '#베이직스',
    '#베이식',        # 추가: 줄임말 (많이 사용됨)
    '#프로셰이프',
    '#프로쉐이프',
    '#엑티바이즈',
    '#파워칵테일',    # 최다 게시물 (54,173개)
    '#리스토레이트',
    
    # 신제품/추가 제품
    '#뮤니티',
    '#옵티멀셋',
    '#셀플러스'
]

# 수집 설정
MAX_RESULTS_PER_HASHTAG = 1000  # 해시태그당 최대 수집 개수 (Naver API 제한: 1000)

# 출력 설정
OUTPUT_DIR = "output"
OUTPUT_CSV = f"{OUTPUT_DIR}/naver_blog_crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
STATS_FILE = f"{OUTPUT_DIR}/crawl_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"


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
                "query": hashtag,  # 해시태그 직접 검색
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
# Step 2: Selenium으로 본문 크롤링 (URL만 수집)
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
        """블로그 게시물 크롤링 (URL만 수집, OCR/동영상 처리 제외)"""
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
            
            # 이미지 URL 수집 (OCR 처리는 Colab에서)
            image_urls = []
            for img in soup.select('img.se-image-resource, img.__se_img_el'):
                img_url = img.get('data-lazy-src') or img.get('src')
                if img_url and img_url.startswith('http'):
                    image_urls.append(img_url)
            
            # 동영상 URL 수집 (스크립트 추출은 Colab에서)
            video_urls = []
            for video in soup.select('iframe[src*="youtube"], iframe[src*="naver"], iframe[src*="youtu"]'):
                video_url = video.get('src')
                if video_url:
                    if not video_url.startswith('http'):
                        video_url = 'https:' + video_url
                    video_urls.append(video_url)
            
            # 작성자 ID 추출
            author_match = re.search(r'blog\.naver\.com/([^/]+)/', url)
            author_id = author_match.group(1) if author_match else ""
            
            # 조회수, 댓글, 공감 추출
            time.sleep(2)
            view_count = self._extract_view_count()
            comment_count = self._extract_comment_count()
            like_count = self._extract_like_count()
            
            self.driver.switch_to.default_content()
            
            return {
                'url': url,
                'title': title,
                'content_text': content_text,
                'hashtags': hashtags,
                'image_urls': image_urls,  # URL만 저장
                'video_urls': video_urls,  # URL만 저장
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
        """조회수 추출"""
        try:
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            match = re.search(r'조회[수]?\s*([\d,]+)', body_text)
            if match:
                return match.group(1).replace(',', '')
            return ""
        except:
            return ""
    
    def _extract_comment_count(self) -> str:
        """댓글수 추출"""
        try:
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            match = re.search(r'댓글\s*(\d+)', body_text)
            if match:
                return match.group(1)
            return ""
        except:
            return ""
    
    def _extract_like_count(self) -> str:
        """공감수 추출"""
        try:
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
# Step 3: 추천인 정보 자동 추출
# ============================================================

class ReferrerExtractor:
    """본문에서 추천인 정보 자동 추출"""
    
    def __init__(self):
        # 전화번호 패턴
        self.phone_patterns = [
            r'010[-\s]?\d{4}[-\s]?\d{4}',
            r'\d{3}[-\s]?\d{4}[-\s]?\d{4}',
        ]
        
        # 이름 패턴
        self.name_patterns = [
            r'(?:문의|상담|연락처|담당|추천인|파트너)\s*[:：]?\s*([가-힣]{2,4})',
            r'([가-힣]{2,4})\s*(?:파트너|매니저|대표|팀장)',
        ]
        
        # 파트너 번호 패턴
        self.partner_patterns = [
            r'파트너\s*번호\s*[:：]?\s*([A-Z0-9-]+)',
            r'Partner\s*No\.?\s*[:：]?\s*([A-Z0-9-]+)',
            r'P[-]?\d{4,}',
        ]
        
        # 카카오톡 ID 패턴
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
                phone = re.sub(r'[^0-9]', '', match.group(0))
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
# Step 4: 데이터 저장
# ============================================================

def save_to_csv(posts: List[Dict], filename: str) -> pd.DataFrame:
    """게시물 데이터를 CSV로 저장"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # 추천인 정보 추출기 초기화
    extractor = ReferrerExtractor()
    
    print("\n추천인 정보 자동 추출 중...")
    extraction_stats = {'name': 0, 'phone': 0, 'partner_number': 0}
    
    rows = []
    for post in posts:
        # 본문에서 추천인 정보 추출
        content_text = post.get('content_text', '')
        referrer_info = extractor.extract_all(content_text)
        
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
            'postdate': post.get('post_date', ''),
            
            # 미디어 정보 (URL만)
            'image_count': len(post.get('image_urls', [])),
            'video_count': len(post.get('video_urls', [])),
            'image_urls': '|||'.join(post.get('image_urls', [])),
            'video_urls': '|||'.join(post.get('video_urls', [])),
            
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
    print(" 네이버 블로그 크롤러 v5.0 - 해시태그 직접 검색")
    print("=" * 70)
    print(f"타겟 해시태그: {len(TARGET_HASHTAGS)}개")
    print(f"해시태그당 최대 수집: {MAX_RESULTS_PER_HASHTAG}개")
    print("=" * 70)
    
    overall_stats = {
        'start_time': datetime.now().isoformat(),
        'config': {
            'target_hashtags': TARGET_HASHTAGS,
            'max_results_per_hashtag': MAX_RESULTS_PER_HASHTAG
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
    
    # Phase 2: 본문 크롤링
    print(f"\n[Phase 2] 본문 크롤링 중 (총 {len(all_blog_urls)}개 URL)...")
    
    crawler = NaverBlogCrawler(headless=True)
    
    crawled_posts = []
    for blog_info in tqdm(all_blog_urls, desc="크롤링"):  # 모든 URL 크롤링
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
