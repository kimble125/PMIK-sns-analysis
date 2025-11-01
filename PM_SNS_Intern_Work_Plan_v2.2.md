# [PM] SNS 분석 프로젝트 인턴 업무 계획서
## PM-International Korea 팀파트너 SNS 활동 분석 - 기술 구현 가이드

**버전**: v2.2  
**작성일**: 2025년 10월 27일  
**프로젝트 기간**: 12주 (3개월)  
**담당**: 데이터 엔지니어링 인턴

---

## 📑 목차

I. 프로젝트 개요
   1. 프로젝트 목표 (Objectives)
   2. 핵심 질문 (Key Questions)
   3. 성공 기준 (Success Metrics)
   4. 전체 아키텍처 개요

II. 데이터 수집 방법론 (플랫폼별 상세)
   1. 네이버 블로그 (Naver Blog)
   2. 유튜브 (YouTube)
   3. 인스타그램 (Instagram)
   4. 카카오스토리 (KakaoStory)
   5. 페이스북 (Facebook)

III. 데이터베이스 설계 및 구축
   1. Azure SQL Database vs Cosmos DB
   2. 스키마 설계
   3. 인덱스 전략
   4. 데이터 마이그레이션

IV. OCR 및 동영상 스크립트 처리
   1. 이미지 OCR 전략
   2. 동영상 스크립트 추출
   3. 비용 최적화 방안

V. 자동화 파이프라인 구축
   1. Azure Data Factory 설계
   2. ETL 프로세스
   3. 스케줄링 및 모니터링
   4. 에러 핸들링

VI. 데이터 분석 및 모델링
   1. 탐색적 데이터 분석 (EDA)
   2. 클러스터링 (K-Means)
   3. 감성 분석 (Sentiment Analysis)
   4. 회귀 분석 (Regression)
   5. 통계적 유의성 검증

VII. 시각화 및 대시보드
   1. Power BI 연동
   2. 핵심 KPI 정의
   3. 대시보드 설계

VIII. 기술 스택 및 환경 설정
   1. 필요 도구 및 라이브러리
   2. 개발 환경 구축
   3. 버전 관리 (Git)

IX. 프로젝트 일정 및 마일스톤
   1. 12주 타임라인
   2. 주차별 산출물
   3. 리스크 관리

X. 인수인계 및 문서화
   1. 코드 문서화 가이드
   2. 운영 매뉴얼
   3. 트러블슈팅 가이드

부록
   A. Python 코드 전체 (모듈별)
   B. SQL 스크립트
   C. Azure 리소스 설정 가이드
   D. API 인증 설정 가이드

---

# I. 프로젝트 개요

## 1. 프로젝트 목표 (Objectives)

### 1.1 핵심 목표

> **"PM-International Korea 팀파트너의 SNS 활동을 자동으로 수집·분석하여, 데이터 기반 마케팅 전략 수립을 지원한다."**

### 1.2 구체적 목표

**1) 데이터 수집 자동화**
- 5개 SNS 플랫폼에서 **일일 500+ 게시물** 자동 수집
- 이미지 OCR 및 동영상 스크립트 포함
- 에러율 **5% 이하** 유지

**2) 데이터 분석**
- 팀파트너를 **4-6개 클러스터**로 유형화
- SNS 활동과 매출의 **상관관계** 규명 (R² > 0.6)
- 고성과자 **베스트 프랙티스** 10개 발굴

**3) 인사이트 제공**
- Power BI 대시보드 구축
- 월간 리포트 자동 생성
- 리스크 게시물 조기 탐지 시스템

### 1.3 Out of Scope (범위 외)

❌ 실시간 스트리밍 분석 (배치 처리만)  
❌ 감정 추적 (이탈 예측 모델 등 고급 ML)  
❌ 다국어 지원 (한국어만)  
❌ 모바일 앱 개발

---

## 2. 핵심 질문 (Key Questions)

이 프로젝트가 답해야 할 **구체적 질문들**:

### 2.1 활동 패턴

**Q1**: 팀파트너는 평균적으로 각 플랫폼에서 얼마나 자주 게시하는가?  
**Q2**: 고성과자와 저성과자의 게시 빈도 차이는?  
**Q3**: 어떤 시간대에 가장 많이 게시하는가?

### 2.2 콘텐츠 유형

**Q4**: 어떤 콘텐츠 유형(텍스트/이미지/영상)이 가장 많은가?  
**Q5**: 해시태그는 평균 몇 개를 사용하는가?  
**Q6**: 가장 효과적인 해시태그 조합은?

### 2.3 참여율 (Engagement)

**Q7**: 플랫폼별 평균 참여율(좋아요+댓글/조회수)은?  
**Q8**: 어떤 요인이 높은 참여율과 연관되는가?  
**Q9**: 감성(긍정/부정)과 참여율의 관계는?

### 2.4 성과 영향

**Q10**: SNS 활동 빈도와 월 매출의 상관관계는? (상관계수 r)  
**Q11**: 어떤 플랫폼이 매출 기여도가 가장 높은가?  
**Q12**: 다중 플랫폼 활용 시 매출 증대 효과는?

### 2.5 리스크

**Q13**: 허위·과장 광고로 의심되는 게시물 비율은?  
**Q14**: 부정적 감성의 게시물 비율은?

---

## 3. 성공 기준 (Success Metrics)

### 3.1 정량적 지표

| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| **데이터 수집량** | 월 15,000+ 게시물 | 데이터베이스 레코드 수 |
| **수집 정확도** | 95% 이상 | 수동 샘플링 검증 (100건) |
| **OCR 정확도** | 80% 이상 | 육안 검증 (50건) |
| **파이프라인 가동률** | 98% 이상 | 일일 실행 성공률 |
| **모델 설명력** | R² > 0.6 | 회귀 분석 결과 |
| **대시보드 완성도** | 10+ 차트 | Power BI 리포트 |

### 3.2 정성적 지표

✅ 프로젝트 매니저가 대시보드만 보고 인사이트 파악 가능  
✅ 팀파트너가 자신의 SNS 전략 개선점 발견  
✅ 향후 유지보수 가능한 코드 및 문서  
✅ 다른 국가 법인에도 적용 가능한 구조

---

## 4. 전체 아키텍처 개요

### 4.1 시스템 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                      SNS 플랫폼 (Data Sources)                    │
├─────────────────────────────────────────────────────────────────┤
│  네이버 블로그  │  유튜브  │  인스타그램  │  카카오스토리  │  페이스북  │
└────────┬────────┴────┬────┴──────┬──────┴──────┬───────┴────┬────┘
         │              │           │             │            │
         │  API + Selenium  API      Instagram    Selenium    Graph API
         │                           Graph API                      │
         └──────────────┬────────────┴─────────────┬───────────────┘
                        │                          │
                   ┌────▼──────────────────────────▼─────┐
                   │   Python Crawlers (Azure VM)        │
                   │   - naver_crawler.py                │
                   │   - youtube_crawler.py              │
                   │   - instagram_crawler.py            │
                   │   - kakao_crawler.py                │
                   │   - facebook_crawler.py             │
                   └────┬────────────────────────────────┘
                        │
                        │ JSON/CSV
                        │
                   ┌────▼──────────────────────────────┐
                   │  Azure Blob Storage (Raw Data)    │
                   │  /raw/naver/2024-10-27/           │
                   │  /raw/youtube/2024-10-27/         │
                   └────┬──────────────────────────────┘
                        │
                        │ Trigger
                        │
                   ┌────▼──────────────────────────────┐
                   │  Azure Data Factory Pipeline      │
                   │  1. Copy Activity (Blob → Staging)│
                   │  2. Data Flow (Transform + OCR)   │
                   │  3. Copy Activity (SQL Load)      │
                   │  4. Stored Procedure (Aggregation)│
                   └────┬──────────────────────────────┘
                        │
                        │ INSERT/UPDATE
                        │
                   ┌────▼──────────────────────────────┐
                   │  Azure SQL Database               │
                   │  - dim_Users                      │
                   │  - fact_Posts                     │
                   │  - fact_VideoTranscripts          │
                   │  - agg_DailyMetrics               │
                   └────┬──────────────────────────────┘
                        │
                        │ Query
                        │
                   ┌────▼──────────────────────────────┐
                   │  Python Analysis (Local/Notebook) │
                   │  - clustering.py                  │
                   │  - sentiment_analysis.py          │
                   │  - regression.py                  │
                   └────┬──────────────────────────────┘
                        │
                        │ Results
                        │
                   ┌────▼──────────────────────────────┐
                   │  Power BI Dashboard               │
                   │  - 실시간 KPI 모니터링              │
                   │  - 클러스터별 분석                   │
                   │  - 플랫폼 비교                       │
                   └───────────────────────────────────┘
```

### 4.2 데이터 플로우 (Data Flow)

**Step 1: 데이터 수집 (Daily 02:00)**
```
Python Crawlers → API/Selenium → JSON → Blob Storage (/raw/)
```

**Step 2: 데이터 변환 (Daily 03:00)**
```
Blob Storage → Data Factory → Transform (OCR, 해시태그 추출) → Staging Tables
```

**Step 3: 데이터 적재 (Daily 04:00)**
```
Staging → MERGE INTO → Production Tables (dim_Users, fact_Posts)
```

**Step 4: 집계 (Daily 05:00)**
```
Production Tables → Stored Procedure → agg_DailyMetrics
```

**Step 5: 분석 (Weekly)**
```
SQL Database → Python Analysis → Results → Power BI
```

---

# II. 데이터 수집 방법론 (플랫폼별 상세)

## 1. 네이버 블로그 (Naver Blog)

### 1.1 문제점 분석

**현재 코드의 문제:**
1. **해시태그 필터링 실패**: Naver Search API는 검색 결과에 해시태그를 포함하지 않음
2. **불완전한 크롤링**: 이미지 URL만 수집, OCR 미실행
3. **동영상 누락**: 동영상 스크립트 수집 안 함

### 1.2 해결책: 2단계 접근법

**Phase 1: API로 URL 수집 (빠름, 합법적)**
- Naver Search API 사용
- 키워드별 블로그 URL 리스트 확보
- 일일 제한: 25,000 calls

**Phase 2: Selenium으로 본문 크롤링 (상세, 느림)**
- 각 URL 방문하여 전체 HTML 파싱
- 본문, 이미지, 동영상, 해시태그 추출
- 해시태그로 필터링

### 1.3 구현 코드

#### Step 1: Naver Search API로 URL 수집

```python
import requests
import time
from datetime import datetime, timedelta

class NaverBlogSearcher:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/blog.json"
    
    def search_keyword(self, keyword, max_results=100, days_back=30):
        """
        키워드로 블로그 검색
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수 (API 제한: 1000)
            days_back: 최근 며칠 데이터 (예: 30일)
        
        Returns:
            List[dict]: 블로그 URL 리스트
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }
        
        results = []
        
        # API는 한 번에 최대 100개씩 반환
        for start in range(1, min(max_results, 1000), 100):
            params = {
                "query": keyword,
                "display": 100,
                "start": start,
                "sort": "date"  # 최신순
            }
            
            try:
                response = requests.get(self.base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                if not items:
                    break  # 더 이상 결과 없음
                
                # 날짜 필터링
                cutoff_date = datetime.now() - timedelta(days=days_back)
                
                for item in items:
                    # postdate: "20241027" 형식
                    post_date_str = item.get('postdate', '')
                    try:
                        post_date = datetime.strptime(post_date_str, '%Y%m%d')
                        if post_date < cutoff_date:
                            continue  # 너무 오래된 게시물
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
                
                print(f"[{keyword}] Collected {len(results)} results so far...")
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"Error searching keyword '{keyword}': {e}")
                break
        
        return results
    
    def _clean_html(self, text):
        """HTML 태그 제거"""
        import re
        clean = re.sub('<.*?>', '', text)
        return clean

# 사용 예시
searcher = NaverBlogSearcher(
    client_id="9v7cOolOk2ctSQXc73sd",
    client_secret="9jHcXVNQwZ"
)

keywords = [
    "피엠인터내셔널", "피엠코리아", "PM인터내셔널", "독일피엠",
    "핏라인", "피트라인", "FitLine",
    "베이식스", "베이직스", "Basics",
    "프로셰이프", "프로쉐이프", "ProShape",
    "엑티바이즈", "Activize",
    "파워칵테일", "PowerCocktail",
    "리스토레이트", "Restorate"
]

all_blog_urls = []
for kw in keywords:
    results = searcher.search_keyword(kw, max_results=100, days_back=30)
    all_blog_urls.extend(results)
    print(f"Keyword '{kw}': {len(results)} blogs")

# 중복 제거 (동일 URL)
unique_urls = {item['link']: item for item in all_blog_urls}
all_blog_urls = list(unique_urls.values())
print(f"\nTotal unique blogs: {len(all_blog_urls)}")
```

#### Step 2: Selenium으로 본문 크롤링 + 해시태그 필터링

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time

class NaverBlogCrawler:
    def __init__(self, headless=True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def crawl_blog_post(self, url):
        """
        네이버 블로그 게시물 크롤링
        
        Returns:
            dict: {
                'url': str,
                'title': str,
                'content_text': str,
                'hashtags': list,
                'images': list,
                'videos': list,
                'author_id': str,
                'post_date': str,
                'like_count': int,
                'comment_count': int
            }
        """
        try:
            self.driver.get(url)
            time.sleep(2)  # 페이지 로딩 대기
            
            # iframe 전환 (네이버 블로그는 iframe 내부에 본문)
            try:
                iframe = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'mainFrame'))
                )
                self.driver.switch_to.frame(iframe)
            except:
                print(f"iframe not found for {url}")
                return None
            
            # HTML 파싱
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 제목
            title_elem = soup.select_one('div.se-title-text')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 본문
            content_div = soup.select_one('div.se-main-container')
            content_text = content_div.get_text(separator='\n', strip=True) if content_div else ""
            
            # 해시태그 추출
            hashtags = self._extract_hashtags(content_text)
            
            # 이미지 URL
            images = []
            for img in soup.select('img.se-image-resource'):
                img_url = img.get('data-lazy-src') or img.get('src')
                if img_url:
                    images.append(img_url)
            
            # 동영상 URL
            videos = []
            for video in soup.select('iframe[src*="youtube"], iframe[src*="naver"]'):
                video_url = video.get('src')
                if video_url:
                    videos.append(video_url)
            
            # 작성자 ID (블로그 주소에서 추출)
            # 예: https://blog.naver.com/user_id/123456
            author_match = re.search(r'blog\.naver\.com/([^/]+)/', url)
            author_id = author_match.group(1) if author_match else ""
            
            # 발행일 (이미 API에서 가져옴, 여기서는 생략)
            
            # 좋아요/댓글 수 (네이버 블로그는 쉽게 가져오기 어려움, API 응답 사용)
            
            # iframe에서 나오기
            self.driver.switch_to.default_content()
            
            return {
                'url': url,
                'title': title,
                'content_text': content_text,
                'hashtags': hashtags,
                'images': images,
                'videos': videos,
                'author_id': author_id
            }
            
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None
    
    def _extract_hashtags(self, text):
        """한글/영문 해시태그 추출"""
        pattern = r'#[가-힣a-zA-Z0-9_]+'
        return re.findall(pattern, text)
    
    def close(self):
        self.driver.quit()

# 사용 예시
crawler = NaverBlogCrawler(headless=True)

# 타겟 해시태그
TARGET_HASHTAGS = [
    '#피엠인터내셔널', '#피엠코리아', '#PM인터내셔널', '#독일피엠',
    '#핏라인', '#피트라인', '#FitLine',
    '#베이식스', '#베이직스', '#Basics',
    '#프로셰이프', '#프로쉐이프', '#ProShape',
    '#엑티바이즈', '#Activize',
    '#파워칵테일', '#PowerCocktail',
    '#리스토레이트', '#Restorate'
]

filtered_posts = []

for blog_info in all_blog_urls[:10]:  # 테스트: 처음 10개만
    post_data = crawler.crawl_blog_post(blog_info['link'])
    
    if post_data:
        # 해시태그 필터링
        if any(tag in post_data['hashtags'] for tag in TARGET_HASHTAGS):
            # API에서 가져온 정보 병합
            post_data.update({
                'post_date': blog_info['postdate'],
                'author_name': blog_info['bloggername']
            })
            filtered_posts.append(post_data)
            print(f"✓ Included: {post_data['title'][:30]}...")
        else:
            print(f"✗ Filtered out (no target hashtag): {blog_info['title'][:30]}...")
    
    time.sleep(1)  # 크롤링 간 대기

crawler.close()

print(f"\n최종 수집: {len(filtered_posts)}개 게시물")
```

#### Step 3: OCR 처리 (EasyOCR)

```python
import easyocr
from PIL import Image
from io import BytesIO
import requests

class OCRProcessor:
    def __init__(self, languages=['ko', 'en'], gpu=False):
        """
        Args:
            languages: 인식 언어 리스트
            gpu: GPU 사용 여부 (False = CPU)
        """
        print("Loading EasyOCR model...")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        print("EasyOCR ready!")
    
    def extract_text_from_url(self, image_url, confidence_threshold=0.5):
        """
        이미지 URL에서 텍스트 추출
        
        Args:
            image_url: 이미지 URL
            confidence_threshold: 신뢰도 임계값 (0.0-1.0)
        
        Returns:
            str: 추출된 텍스트
        """
        try:
            # 이미지 다운로드
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # PIL Image 변환
            img = Image.open(BytesIO(response.content))
            
            # OCR 실행
            results = self.reader.readtext(img)
            
            # 신뢰도 필터링
            texts = [r[1] for r in results if r[2] >= confidence_threshold]
            
            return '\n'.join(texts)
            
        except Exception as e:
            print(f"OCR error for {image_url}: {e}")
            return ""

# 사용 예시
ocr = OCRProcessor(languages=['ko', 'en'], gpu=False)

for post in filtered_posts:
    ocr_results = {}
    
    # 처음 5개 이미지만 OCR (비용/시간 절약)
    for img_url in post['images'][:5]:
        text = ocr.extract_text_from_url(img_url)
        if text:
            ocr_results[img_url] = text
    
    post['ocr_results'] = ocr_results
    print(f"OCR completed for: {post['title'][:30]}... ({len(ocr_results)} images)")
```

#### Step 4: 동영상 스크립트 추출

```python
from youtube_transcript_api import YouTubeTranscriptApi
import re

class VideoTranscriptExtractor:
    def extract_youtube_transcript(self, youtube_url):
        """
        YouTube 영상에서 자막 추출
        
        Args:
            youtube_url: YouTube URL 또는 iframe src
        
        Returns:
            str: 자막 텍스트
        """
        # Video ID 추출
        video_id = self._extract_video_id(youtube_url)
        if not video_id:
            return ""
        
        try:
            # 자막 다운로드 (한국어 우선, 없으면 영어)
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['ko', 'en']
            )
            
            # 텍스트 결합
            full_text = ' '.join([entry['text'] for entry in transcript])
            return full_text
            
        except Exception as e:
            print(f"Transcript error for {video_id}: {e}")
            return ""
    
    def _extract_video_id(self, url):
        """YouTube URL에서 video ID 추출"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?]+)',
            r'youtube\.com/embed/([^&\n?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

# 사용 예시
video_extractor = VideoTranscriptExtractor()

for post in filtered_posts:
    transcripts = {}
    
    for video_url in post['videos']:
        if 'youtube' in video_url:
            transcript = video_extractor.extract_youtube_transcript(video_url)
            if transcript:
                transcripts[video_url] = transcript
    
    post['video_transcripts'] = transcripts
```

#### Step 5: CSV 저장

```python
import pandas as pd
import json

def save_to_csv(posts, filename='naver_blog_data.csv'):
    """
    수집 데이터를 CSV로 저장
    """
    # 데이터 변환
    rows = []
    for post in posts:
        row = {
            'platform': 'Naver Blog',
            'post_url': post['url'],
            'author_id': post['author_id'],
            'author_name': post['author_name'],
            'title': post['title'],
            'content_text': post['content_text'],
            'post_date': post['post_date'],
            'hashtags': ', '.join(post['hashtags']),
            'image_count': len(post['images']),
            'video_count': len(post['videos']),
            'ocr_text': '\n---\n'.join(post['ocr_results'].values()),
            'video_transcripts': '\n---\n'.join(post['video_transcripts'].values())
        }
        rows.append(row)
    
    # DataFrame 생성
    df = pd.DataFrame(rows)
    
    # CSV 저장
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved {len(df)} posts to {filename}")
    
    return df

# 실행
df = save_to_csv(filtered_posts, 'naver_blog_crawl_result.csv')
print(df.head())
```

### 1.4 성능 최적화

**병렬 처리 (멀티스레딩):**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def crawl_with_threading(urls, max_workers=5):
    """
    병렬로 크롤링 (5개 동시)
    """
    crawler = NaverBlogCrawler(headless=True)
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(crawler.crawl_blog_post, url): url 
            for url in urls
        }
        
        # Collect results
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"Error with {url}: {e}")
    
    crawler.close()
    return results

# 사용
results = crawl_with_threading([b['link'] for b in all_blog_urls], max_workers=5)
```

**예상 소요 시간:**
- API 검색: 5분 (500 URLs)
- Selenium 크롤링: 30분 (500 URLs, 5병렬)
- OCR: 60분 (2,500 이미지, 5 images/post)
- **총 95분**

---

## 2. 유튜브 (YouTube)

### 2.1 YouTube Data API v3 사용

**API 제한:**
- 일일 할당량: **10,000 units**
- Search 요청: 100 units
- Video 상세 조회: 1 unit
- 최대: **일 약 100 검색** 또는 **10,000 상세 조회**

### 2.2 구현 코드

```python
from googleapiclient.discovery import build
from datetime import datetime, timedelta

class YouTubeCrawler:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_videos(self, keyword, max_results=50, days_back=30):
        """
        키워드로 영상 검색
        """
        # 날짜 필터
        published_after = (datetime.now() - timedelta(days=days_back)).isoformat() + 'Z'
        
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=keyword,
                type="video",
                maxResults=min(max_results, 50),  # API 제한
                order="date",  # 최신순
                publishedAfter=published_after
            )
            response = request.execute()
            
            videos = []
            for item in response['items']:
                video_id = item['id']['videoId']
                videos.append({
                    'video_id': video_id,
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'channel_title': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'published_at': item['snippet']['publishedAt']
                })
            
            return videos
            
        except Exception as e:
            print(f"YouTube search error: {e}")
            return []
    
    def get_video_stats(self, video_ids):
        """
        영상 통계 (조회수, 좋아요, 댓글 수) 가져오기
        
        Args:
            video_ids: list of video IDs (최대 50개)
        """
        try:
            request = self.youtube.videos().list(
                part="statistics,snippet",
                id=','.join(video_ids)
            )
            response = request.execute()
            
            stats = {}
            for item in response['items']:
                video_id = item['id']
                stats[video_id] = {
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'like_count': int(item['statistics'].get('likeCount', 0)),
                    'comment_count': int(item['statistics'].get('commentCount', 0)),
                    'duration': item['snippet'].get('duration', ''),
                    'tags': item['snippet'].get('tags', [])
                }
            
            return stats
            
        except Exception as e:
            print(f"Stats error: {e}")
            return {}

# 사용 예시
youtube_crawler = YouTubeCrawler(api_key='YOUR_YOUTUBE_API_KEY')

youtube_keywords = [
    "피엠인터내셔널", "PM International Korea", "FitLine",
    "핏라인 후기", "ProShape 다이어트"
]

all_videos = []
for kw in youtube_keywords:
    videos = youtube_crawler.search_videos(kw, max_results=50, days_back=30)
    all_videos.extend(videos)

# 중복 제거
unique_videos = {v['video_id']: v for v in all_videos}
all_videos = list(unique_videos.values())

# 통계 가져오기 (50개씩 배치)
for i in range(0, len(all_videos), 50):
    batch = all_videos[i:i+50]
    video_ids = [v['video_id'] for v in batch]
    stats = youtube_crawler.get_video_stats(video_ids)
    
    for video in batch:
        vid = video['video_id']
        if vid in stats:
            video.update(stats[vid])

print(f"Total YouTube videos: {len(all_videos)}")
```

### 2.3 자막 다운로드

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_all_transcripts(video_list):
    """
    영상 리스트에서 모든 자막 다운로드
    """
    for video in video_list:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video['video_id'],
                languages=['ko', 'en']
            )
            video['transcript'] = ' '.join([t['text'] for t in transcript])
            print(f"✓ Transcript: {video['title'][:30]}...")
        except:
            video['transcript'] = ""
            print(f"✗ No transcript: {video['title'][:30]}...")

get_all_transcripts(all_videos)
```

---

## 3. 인스타그램 (Instagram)

### 3.1 Instagram Graph API 설정

**필수 조건:**
1. Facebook 개발자 계정
2. Instagram Business Account
3. Facebook Page와 Instagram 연결

### 3.2 Access Token 발급 (수동)

**단계:**
1. https://developers.facebook.com/ 접속
2. "My Apps" → "Create App"
3. App Type: "Business"
4. App 설정 → Instagram Graph API 추가
5. Tools → Graph API Explorer
6. Permissions: `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement`
7. "Generate Access Token" 클릭
8. **Short-lived Token**(1시간) 발급
9. Exchange for **Long-lived Token**(60일)

**Token 교환 코드:**

```python
import requests

def exchange_for_long_lived_token(short_token, app_id, app_secret):
    """
    Short-lived token (1시간) → Long-lived token (60일)
    """
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': app_id,
        'client_secret': app_secret,
        'fb_exchange_token': short_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    long_token = data.get('access_token')
    expires_in = data.get('expires_in')  # 초 단위 (약 5184000 = 60일)
    
    print(f"Long-lived token expires in {expires_in / 86400:.0f} days")
    return long_token

# 사용
SHORT_TOKEN = "YOUR_SHORT_LIVED_TOKEN"
APP_ID = "YOUR_APP_ID"
APP_SECRET = "YOUR_APP_SECRET"

long_token = exchange_for_long_lived_token(SHORT_TOKEN, APP_ID, APP_SECRET)
print(f"Long-lived token: {long_token}")
```

### 3.3 Instagram 데이터 수집

```python
import requests
import time

class InstagramCrawler:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def get_user_media(self, instagram_account_id, limit=100):
        """
        사용자의 미디어(게시물) 가져오기
        
        Args:
            instagram_account_id: Instagram Business Account ID
            limit: 최대 개수
        """
        url = f"{self.base_url}/{instagram_account_id}/media"
        params = {
            'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
            'access_token': self.access_token,
            'limit': limit
        }
        
        all_media = []
        
        while True:
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                media_list = data.get('data', [])
                all_media.extend(media_list)
                
                # 다음 페이지
                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {}  # next URL에 이미 파라미터 포함
                else:
                    break
                
                time.sleep(0.5)  # Rate limit
                
            except Exception as e:
                print(f"Instagram API error: {e}")
                break
        
        return all_media
    
    def get_hashtag_search(self, instagram_account_id, hashtag):
        """
        해시태그로 검색 (자신의 미디어만)
        
        주의: Instagram API는 자신의 계정 미디어만 검색 가능
        """
        # Hashtag ID 조회
        url = f"{self.base_url}/ig_hashtag_search"
        params = {
            'user_id': instagram_account_id,
            'q': hashtag,
            'access_token': self.access_token
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if not data.get('data'):
            return []
        
        hashtag_id = data['data'][0]['id']
        
        # 해시태그가 달린 미디어 조회
        url = f"{self.base_url}/{hashtag_id}/recent_media"
        params = {
            'user_id': instagram_account_id,
            'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
            'access_token': self.access_token
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        return data.get('data', [])

# 사용 예시
instagram = InstagramCrawler(access_token='YOUR_LONG_LIVED_TOKEN')

# Instagram Account ID 찾기 (수동: Graph API Explorer에서 확인)
INSTAGRAM_ACCOUNT_ID = "YOUR_IG_ACCOUNT_ID"

media_list = instagram.get_user_media(INSTAGRAM_ACCOUNT_ID, limit=100)
print(f"Collected {len(media_list)} Instagram posts")
```

### 3.4 Rate Limiting 관리

**Instagram API 제한:**
- 시간당 **200 calls**
- 초과 시: HTTP 429 (Too Many Requests)

**대응 전략:**

```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_calls=190, time_window=3600):
        """
        Args:
            max_calls: 시간당 최대 호출 수 (안전 마진 10)
            time_window: 시간 창 (초)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        """필요 시 대기"""
        now = datetime.now()
        
        # 시간 창 밖의 호출 제거
        self.calls = [c for c in self.calls if now - c < timedelta(seconds=self.time_window)]
        
        if len(self.calls) >= self.max_calls:
            # 가장 오래된 호출이 시간 창 밖으로 나갈 때까지 대기
            oldest_call = self.calls[0]
            wait_time = (oldest_call + timedelta(seconds=self.time_window) - now).total_seconds()
            
            if wait_time > 0:
                print(f"Rate limit reached. Waiting {wait_time:.0f}s...")
                time.sleep(wait_time + 1)
        
        self.calls.append(now)

# 사용
limiter = RateLimiter(max_calls=190, time_window=3600)

for i in range(300):
    limiter.wait_if_needed()
    # API 호출
    print(f"Call {i+1}")
```

---

## 4. 카카오스토리 (KakaoStory)

### 4.1 문제점

**공식 API 없음:**
- Kakao Developers에서 KakaoStory API는 **서비스 종료**
- 웹 스크래핑 필요

**법적 고려사항:**
- 로그인 필요 (타인 계정 자동 로그인 금지)
- 비공개 게시물 크롤링 불가
- 개인정보보호법 준수

### 4.2 대안: 공개 게시물만 수집 (제한적)

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class KakaoStoryCrawler:
    def __init__(self, username, password):
        """
        주의: 자동 로그인은 Kakao 이용약관 위반 가능성
        연구 목적으로만 사용, 실제 배포 시 법률 자문 필요
        """
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
        self.username = username
        self.password = password
    
    def login(self):
        """카카오 로그인"""
        self.driver.get('https://story.kakao.com/')
        time.sleep(2)
        
        # 로그인 버튼 클릭
        # (실제 구현 시 요소 찾기 로직 필요)
        # 주의: Kakao는 CAPTCHA 있을 수 있음
        
        pass  # 구현 생략 (법적 이슈)
    
    def search_public_posts(self, keyword):
        """공개 게시물 검색 (제한적)"""
        # 카카오스토리는 검색 기능이 제한적
        pass

# 권장하지 않음
```

**대안:**
- 팀파트너에게 직접 공개 URL 제공 요청
- 또는 카카오스토리 데이터 수집 포기 (다른 4개 플랫폼으로 충분)

---

## 5. 페이스북 (Facebook)

### 5.1 Graph API 사용

**Instagram과 동일한 App 사용 가능**

```python
class FacebookCrawler:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def get_page_posts(self, page_id, limit=100):
        """
        Facebook Page의 게시물 가져오기
        """
        url = f"{self.base_url}/{page_id}/posts"
        params = {
            'fields': 'id,message,created_time,permalink_url,likes.summary(true),comments.summary(true),shares',
            'access_token': self.access_token,
            'limit': limit
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        posts = []
        for post in data.get('data', []):
            posts.append({
                'post_id': post['id'],
                'message': post.get('message', ''),
                'created_time': post['created_time'],
                'permalink': post.get('permalink_url', ''),
                'like_count': post.get('likes', {}).get('summary', {}).get('total_count', 0),
                'comment_count': post.get('comments', {}).get('summary', {}).get('total_count', 0),
                'share_count': post.get('shares', {}).get('count', 0)
            })
        
        return posts

# 사용
facebook = FacebookCrawler(access_token='YOUR_ACCESS_TOKEN')
PAGE_ID = "PMInternationalKorea"  # 예시
posts = facebook.get_page_posts(PAGE_ID, limit=100)
```

---

# III. 데이터베이스 설계 및 구축

## 1. Azure SQL Database vs Cosmos DB

### 1.1 비교표

| 기준 | Azure SQL Database | Azure Cosmos DB |
|------|-------------------|-----------------|
| **데이터 모델** | 관계형 (RDBMS) | NoSQL (문서형) |
| **쿼리 언어** | T-SQL | SQL API, MongoDB API |
| **스키마** | 고정 스키마 | 유연 스키마 |
| **트랜잭션** | ACID 보장 | Eventually consistent |
| **확장성** | Vertical (Scale-up) | Horizontal (Scale-out) |
| **가격** | S1: $30/월 | 400 RU/s: $25/월 |
| **Power BI 연동** | Native | ODBC 필요 |
| **적합성** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### 1.2 선택: Azure SQL Database

**이유:**
1. **정형 데이터**: SNS 게시물 데이터는 일정한 구조
2. **JOIN 필요**: 사용자-게시물 관계 분석
3. **Power BI 최적화**: Native connector
4. **비용 효율**: 중소규모 데이터에 적합
5. **팀 익숙도**: SQL 문법 널리 사용됨

---

## 2. 스키마 설계

### 2.1 ERD (Entity-Relationship Diagram)

```
┌─────────────────┐         ┌─────────────────────┐
│   dim_Users     │1       ∞│    fact_Posts       │
├─────────────────┤◄────────┤─────────────────────┤
│ user_id (PK)    │         │ post_id (PK)        │
│ username        │         │ user_id (FK)        │
│ platform        │         │ platform            │
│ profile_url     │         │ post_url            │
│ followers_count │         │ title               │
│ posts_count     │         │ content_text        │
│ created_date    │         │ ocr_text            │
└─────────────────┘         │ hashtags            │
                            │ published_date      │
                            │ like_count          │
                            │ comment_count       │
                            │ view_count          │
                            │ engagement_rate     │
                            └──────┬──────────────┘
                                  │1
                                  │
                                  │∞
                      ┌───────────▼─────────────┐
                      │ fact_VideoTranscripts   │
                      ├─────────────────────────┤
                      │ transcript_id (PK)      │
                      │ post_id (FK)            │
                      │ video_url               │
                      │ transcript_text         │
                      └─────────────────────────┘
```

### 2.2 테이블 정의 (SQL DDL)

```sql
-- ==============================
-- 1. dim_Users (사용자 차원)
-- ==============================
CREATE TABLE dim_Users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(100) NOT NULL,
    platform NVARCHAR(50) NOT NULL,
    profile_url NVARCHAR(500),
    followers_count INT DEFAULT 0,
    posts_count INT DEFAULT 0,
    created_date DATE DEFAULT GETDATE(),
    updated_date DATETIME DEFAULT GETDATE(),
    
    -- 복합 고유 키 (동일 사용자가 여러 플랫폼 사용 가능)
    CONSTRAINT UQ_User_Platform UNIQUE (username, platform)
);

-- 인덱스
CREATE INDEX IX_Users_Platform ON dim_Users(platform);
CREATE INDEX IX_Users_Username ON dim_Users(username);

-- ==============================
-- 2. fact_Posts (게시물 팩트)
-- ==============================
CREATE TABLE fact_Posts (
    post_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    platform NVARCHAR(50) NOT NULL,
    post_url NVARCHAR(500) NOT NULL,
    title NVARCHAR(500),
    content_text NVARCHAR(MAX),
    ocr_text NVARCHAR(MAX),
    hashtags NVARCHAR(MAX),  -- JSON 배열: ["#해시태그1", "#해시태그2"]
    published_date DATETIME NOT NULL,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    
    -- 계산 필드 (Computed Column)
    engagement_rate AS (
        CASE 
            WHEN view_count > 0 
            THEN CAST(like_count + comment_count AS FLOAT) / view_count
            ELSE 0
        END
    ) PERSISTED,
    
    created_date DATETIME DEFAULT GETDATE(),
    updated_date DATETIME DEFAULT GETDATE(),
    
    -- 외래 키
    CONSTRAINT FK_Posts_Users FOREIGN KEY (user_id) 
        REFERENCES dim_Users(user_id) ON DELETE CASCADE,
    
    -- 고유 제약 (중복 게시물 방지)
    CONSTRAINT UQ_Post_URL UNIQUE (post_url)
);

-- 인덱스
CREATE INDEX IX_Posts_User ON fact_Posts(user_id);
CREATE INDEX IX_Posts_Platform ON fact_Posts(platform);
CREATE INDEX IX_Posts_PublishedDate ON fact_Posts(published_date DESC);
CREATE INDEX IX_Posts_Engagement ON fact_Posts(engagement_rate DESC);

-- Full-Text Search (본문 검색용)
CREATE FULLTEXT INDEX ON fact_Posts(content_text)
    KEY INDEX PK__fact_Pos__XXXXXXXX;

-- ==============================
-- 3. fact_VideoTranscripts (동영상 스크립트)
-- ==============================
CREATE TABLE fact_VideoTranscripts (
    transcript_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    post_id BIGINT NOT NULL,
    video_url NVARCHAR(500) NOT NULL,
    transcript_text NVARCHAR(MAX),
    created_date DATETIME DEFAULT GETDATE(),
    
    -- 외래 키
    CONSTRAINT FK_Transcripts_Posts FOREIGN KEY (post_id)
        REFERENCES fact_Posts(post_id) ON DELETE CASCADE
);

-- 인덱스
CREATE INDEX IX_Transcripts_Post ON fact_VideoTranscripts(post_id);

-- ==============================
-- 4. agg_DailyMetrics (일별 집계)
-- ==============================
CREATE TABLE agg_DailyMetrics (
    metric_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    date DATE NOT NULL,
    user_id INT NOT NULL,
    platform NVARCHAR(50) NOT NULL,
    total_posts INT DEFAULT 0,
    total_likes INT DEFAULT 0,
    total_comments INT DEFAULT 0,
    total_views INT DEFAULT 0,
    avg_engagement_rate FLOAT DEFAULT 0,
    created_date DATETIME DEFAULT GETDATE(),
    
    -- 복합 고유 키
    CONSTRAINT UQ_Daily_User_Platform UNIQUE (date, user_id, platform),
    
    -- 외래 키
    CONSTRAINT FK_Daily_Users FOREIGN KEY (user_id)
        REFERENCES dim_Users(user_id) ON DELETE CASCADE
);

-- 인덱스
CREATE INDEX IX_Daily_Date ON agg_DailyMetrics(date DESC);
CREATE INDEX IX_Daily_User ON agg_DailyMetrics(user_id);

-- ==============================
-- 5. log_CrawlingJobs (크롤링 작업 로그)
-- ==============================
CREATE TABLE log_CrawlingJobs (
    job_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    platform NVARCHAR(50) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    status NVARCHAR(20),  -- 'Running', 'Success', 'Failed'
    posts_collected INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    error_message NVARCHAR(MAX),
    created_date DATETIME DEFAULT GETDATE()
);

-- 인덱스
CREATE INDEX IX_Log_Platform_Date ON log_CrawlingJobs(platform, start_time DESC);
```

### 2.3 샘플 데이터 INSERT

```sql
-- 사용자 추가
INSERT INTO dim_Users (username, platform, profile_url, followers_count, posts_count)
VALUES 
    ('user_naver_123', 'Naver Blog', 'https://blog.naver.com/user_naver_123', 1500, 320),
    ('user_youtube_456', 'YouTube', 'https://youtube.com/@user456', 8500, 120),
    ('user_insta_789', 'Instagram', 'https://instagram.com/user789', 3200, 580);

-- 게시물 추가
INSERT INTO fact_Posts (
    user_id, platform, post_url, title, content_text, hashtags, 
    published_date, like_count, comment_count, view_count
)
VALUES
    (1, 'Naver Blog', 'https://blog.naver.com/user_naver_123/12345', 
     '피엠인터내셔널 FitLine Basics 한 달 후기', 
     '안녕하세요~ 오늘은 제가 한 달 동안 먹어본 핏라인 베이식스 후기를 남겨요...',
     '["#피엠인터내셔널", "#FitLine", "#건강기능식품"]',
     '2024-10-15 10:30:00', 45, 12, 1200);

-- 동영상 스크립트 추가
INSERT INTO fact_VideoTranscripts (post_id, video_url, transcript_text)
VALUES
    (1, 'https://youtube.com/watch?v=abcd1234', 
     '안녕하세요 여러분 오늘은 피엠인터내셔널 제품에 대해 이야기해볼게요...');
```

---

## 3. 인덱스 전략

### 3.1 B-Tree 인덱스

**용도**: 범위 검색, 정렬

```sql
-- 날짜 범위 검색 (최근 30일 게시물)
CREATE INDEX IX_Posts_PublishedDate 
ON fact_Posts(published_date DESC);

-- 사용자별 게시물 조회
CREATE INDEX IX_Posts_UserID 
ON fact_Posts(user_id);
```

### 3.2 Filtered Index

**용도**: 특정 조건 데이터만 인덱싱

```sql
-- 고참여율 게시물만 (engagement_rate > 0.05)
CREATE INDEX IX_Posts_HighEngagement
ON fact_Posts(engagement_rate)
WHERE engagement_rate > 0.05;

-- 최근 6개월 데이터만
CREATE INDEX IX_Posts_Recent
ON fact_Posts(published_date)
WHERE published_date >= DATEADD(MONTH, -6, GETDATE());
```

### 3.3 Full-Text Index

**용도**: 텍스트 검색 (LIKE '%키워드%' 대신)

```sql
-- Full-Text Catalog 생성
CREATE FULLTEXT CATALOG ftCatalog AS DEFAULT;

-- Full-Text Index 생성
CREATE FULLTEXT INDEX ON fact_Posts(content_text, title)
    KEY INDEX PK__fact_Pos__XXXXXXXX
    ON ftCatalog;

-- 사용 예시
SELECT * FROM fact_Posts
WHERE CONTAINS(content_text, '"피엠인터내셔널" OR "FitLine"');
```

---

## 4. 데이터 마이그레이션

### 4.1 CSV → Azure SQL Database

```python
import pyodbc
import pandas as pd

class AzureSQLUploader:
    def __init__(self, server, database, username, password):
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password}"
        )
        self.conn = pyodbc.connect(conn_str)
        self.cursor = self.conn.cursor()
    
    def upsert_users(self, users_df):
        """
        사용자 데이터 업서트 (있으면 업데이트, 없으면 삽입)
        """
        for _, row in users_df.iterrows():
            self.cursor.execute("""
                MERGE dim_Users AS target
                USING (VALUES (?, ?)) AS source (username, platform)
                ON target.username = source.username AND target.platform = source.platform
                WHEN MATCHED THEN
                    UPDATE SET 
                        followers_count = ?,
                        posts_count = ?,
                        updated_date = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (username, platform, profile_url, followers_count, posts_count)
                    VALUES (?, ?, ?, ?, ?);
            """, 
                row['username'], row['platform'],
                row['followers_count'], row['posts_count'],
                row['username'], row['platform'], row['profile_url'], 
                row['followers_count'], row['posts_count']
            )
        
        self.conn.commit()
        print(f"Upserted {len(users_df)} users")
    
    def insert_posts(self, posts_df):
        """
        게시물 삽입 (중복 URL은 무시)
        """
        inserted = 0
        for _, row in posts_df.iterrows():
            try:
                # user_id 조회
                self.cursor.execute("""
                    SELECT user_id FROM dim_Users 
                    WHERE username = ? AND platform = ?
                """, row['username'], row['platform'])
                
                result = self.cursor.fetchone()
                if not result:
                    print(f"User not found: {row['username']}")
                    continue
                
                user_id = result[0]
                
                # 게시물 삽입
                self.cursor.execute("""
                    INSERT INTO fact_Posts (
                        user_id, platform, post_url, title, content_text, 
                        ocr_text, hashtags, published_date, 
                        like_count, comment_count, view_count
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    user_id, row['platform'], row['post_url'], row['title'],
                    row['content_text'], row.get('ocr_text', ''),
                    row.get('hashtags', '[]'), row['published_date'],
                    row.get('like_count', 0), row.get('comment_count', 0),
                    row.get('view_count', 0)
                )
                inserted += 1
                
            except pyodbc.IntegrityError:
                # 중복 URL (UNIQUE 제약 위반)
                continue
        
        self.conn.commit()
        print(f"Inserted {inserted} posts")
    
    def close(self):
        self.cursor.close()
        self.conn.close()

# 사용 예시
uploader = AzureSQLUploader(
    server='your-server.database.windows.net',
    database='PMI_SNS_DB',
    username='admin',
    password='your_password'
)

# CSV 읽기
df_users = pd.read_csv('users.csv')
df_posts = pd.read_csv('posts.csv')

# 업로드
uploader.upsert_users(df_users)
uploader.insert_posts(df_posts)

uploader.close()
```

---

# IV. OCR 및 동영상 스크립트 처리

## 1. 이미지 OCR 전략

### 1.1 도구 비교 (재정리)

| 도구 | 비용 | 무료 한도 | 한글 정확도 | 설정 난이도 | **추천 단계** |
|------|------|-----------|------------|-----------|-------------|
| **EasyOCR** | 무료 | 무제한 | 85% | ⭐ | POC |
| **Azure CV** | 유료 | 5K/월 | 95% | ⭐⭐ | Pilot |
| **Google Vision** | 유료 | 1K/월 | 95% | ⭐⭐ | - |
| **Naver Clova** | 유료 | 없음 | 98% | ⭐⭐⭐ | Production |

### 1.2 단계별 전략

**Phase 1: POC (비용 $0/월)**
- **도구**: EasyOCR
- **샘플**: 1,000개 이미지
- **목적**: 정확도 검증

**Phase 2: Pilot (비용 $5/월)**
- **도구**: Azure Computer Vision (5,000건 무료 티어)
- **규모**: 10,000개 이미지
- **목적**: 성능 테스트

**Phase 3: Production (비용 $100-200/월)**
- **도구**: Azure CV (기본) + Naver Clova (한글 특화)
- **규모**: 100,000+ 이미지
- **목적**: 안정적 운영

### 1.3 구현 코드 (Azure Computer Vision)

```python
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import time

class AzureOCR:
    def __init__(self, endpoint, subscription_key):
        self.client = ComputerVisionClient(
            endpoint, 
            CognitiveServicesCredentials(subscription_key)
        )
    
    def extract_text_from_url(self, image_url):
        """
        이미지 URL에서 텍스트 추출
        
        Azure Computer Vision API 사용
        """
        try:
            # OCR 비동기 요청
            read_response = self.client.read(image_url, raw=True)
            
            # Operation ID 추출
            operation_location = read_response.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]
            
            # 결과 대기 (최대 30초)
            for _ in range(30):
                result = self.client.get_read_result(operation_id)
                if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
                    break
                time.sleep(1)
            
            # 텍스트 추출
            texts = []
            if result.status == OperationStatusCodes.succeeded:
                for page in result.analyze_result.read_results:
                    for line in page.lines:
                        texts.append(line.text)
            
            return '\n'.join(texts)
            
        except Exception as e:
            print(f"Azure OCR error for {image_url}: {e}")
            return ""

# 사용 예시
azure_ocr = AzureOCR(
    endpoint='https://your-resource.cognitiveservices.azure.com/',
    subscription_key='YOUR_SUBSCRIPTION_KEY'
)

for post in posts_list:
    for img_url in post['images'][:5]:
        ocr_text = azure_ocr.extract_text_from_url(img_url)
        post['ocr_results'][img_url] = ocr_text
```

---

## 2. 동영상 스크립트 추출

### 2.1 방법 비교

| 방법 | 비용 | 정확도 | 속도 | **추천** |
|------|------|--------|------|---------|
| YouTube 자막 다운로드 | 무료 | 85-90% | 빠름 | ⭐⭐⭐⭐⭐ |
| Whisper (Self-host) | 무료 | 95%+ | 느림 | ⭐⭐⭐⭐⭐ |
| Google Speech-to-Text | 유료 (60분/월 무료) | 95% | 빠름 | ⭐⭐⭐⭐ |
| Azure Speech Service | 유료 (5시간/월 무료) | 95% | 빠름 | ⭐⭐⭐⭐ |

### 2.2 Whisper 구현 (Self-hosted)

```python
import whisper
import yt_dlp
import os

class WhisperTranscriber:
    def __init__(self, model_size='base'):
        """
        Args:
            model_size: 'tiny', 'base', 'small', 'medium', 'large'
        """
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        print("Whisper ready!")
    
    def transcribe_youtube_video(self, youtube_url):
        """
        YouTube 영상에서 음성 추출 → 텍스트 변환
        """
        # Step 1: YouTube 영상 다운로드 (오디오만)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'temp_audio.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # Step 2: Whisper로 음성 인식
        audio_file = 'temp_audio.mp3'
        result = self.model.transcribe(audio_file, language='ko')
        
        # Step 3: 임시 파일 삭제
        os.remove(audio_file)
        
        return result['text']

# 사용 예시
transcriber = WhisperTranscriber(model_size='base')

for post in posts_with_videos:
    for video_url in post['videos']:
        if 'youtube' in video_url:
            transcript = transcriber.transcribe_youtube_video(video_url)
            post['video_transcripts'][video_url] = transcript
            print(f"Transcribed: {video_url}")
```

**Whisper 모델 크기 선택:**
- **tiny**: 빠름 (1분 영상 = 5초), 정확도 낮음 (80%)
- **base**: 적당 (1분 = 10초), 정확도 85%
- **small**: 느림 (1분 = 30초), 정확도 90%
- **medium**: 매우 느림 (1분 = 2분), 정확도 95%

**권장**: **base** 모델 (정확도-속도 균형)

---

# V. 자동화 파이프라인 구축

## 1. Azure Data Factory 설계

### 1.1 파이프라인 구조

```
Pipeline: Daily_SNS_Data_Collection
├─ Activity 1: Execute Python Script (Crawlers)
│   ├─ Naver Blog Crawler
│   ├─ YouTube Crawler
│   ├─ Instagram Crawler
│   └─ Facebook Crawler
│
├─ Activity 2: Copy to Blob Storage
│   └─ /raw/{platform}/{date}/posts.json
│
├─ Activity 3: Data Flow (Transform)
│   ├─ Parse JSON
│   ├─ Clean Text
│   ├─ Extract Hashtags
│   ├─ OCR Images (Azure CV)
│   └─ Filter by Target Hashtags
│
├─ Activity 4: Copy to SQL Database
│   ├─ Staging Tables (stg_Users, stg_Posts)
│   └─ MERGE INTO Production Tables
│
└─ Activity 5: Stored Procedure (Aggregation)
    └─ EXEC sp_AggregateDailyMetrics
```

### 1.2 Activity 상세 설정

**Activity 1: Execute Python Script**

Azure VM에서 Python 크롤러 실행:

```bash
# Azure VM에 SSH 접속
ssh azureuser@your-vm-ip

# 크롤링 스크립트 실행
cd /home/azureuser/pmi-sns-crawler
python3 main.py --platform all --days 1

# 결과 업로드
az storage blob upload-batch \
    --destination /raw/naver/$(date +%Y-%m-%d)/ \
    --source ./output/ \
    --account-name yourstorageaccount
```

**Activity 2: Copy to Blob Storage**

Data Factory의 Copy Activity 사용:
- Source: Azure VM (SFTP)
- Sink: Azure Blob Storage
- Path: `/raw/{platform}/{date}/posts.json`

**Activity 3: Data Flow (Transform)**

```
Source: Blob Storage JSON files
│
├─ Derived Column: Extract hashtags (regex)
├─ Filter: WHERE hashtags CONTAINS TARGET_HASHTAGS
├─ Lookup: Call Azure CV API for OCR
├─ Select: Choose columns
│
Sink: Staging Tables (stg_Users, stg_Posts)
```

**Activity 4: Copy to SQL Database**

```sql
-- MERGE 문으로 Upsert
MERGE fact_Posts AS target
USING stg_Posts AS source
ON target.post_url = source.post_url
WHEN MATCHED THEN
    UPDATE SET 
        like_count = source.like_count,
        comment_count = source.comment_count,
        updated_date = GETDATE()
WHEN NOT MATCHED THEN
    INSERT (user_id, platform, post_url, title, content_text, ...)
    VALUES (source.user_id, source.platform, ...);
```

**Activity 5: Stored Procedure**

```sql
CREATE PROCEDURE sp_AggregateDailyMetrics
    @target_date DATE
AS
BEGIN
    -- 일별 집계 계산
    INSERT INTO agg_DailyMetrics (date, user_id, platform, total_posts, ...)
    SELECT 
        @target_date AS date,
        user_id,
        platform,
        COUNT(*) AS total_posts,
        SUM(like_count) AS total_likes,
        SUM(comment_count) AS total_comments,
        SUM(view_count) AS total_views,
        AVG(engagement_rate) AS avg_engagement_rate
    FROM fact_Posts
    WHERE CAST(published_date AS DATE) = @target_date
    GROUP BY user_id, platform;
END
```

### 1.3 스케줄링

**Trigger 설정:**
- **Type**: Schedule Trigger
- **Frequency**: Daily
- **Time**: 02:00 (KST)
- **Days**: All days

**의존성 체인:**
```
02:00 → Python Crawlers (60분)
03:00 → Blob Upload (5분)
03:05 → Data Flow Transform (30분)
03:35 → SQL Load (10분)
03:45 → Aggregation (5분)
03:50 → Pipeline Complete
```

---

## 2. ETL 프로세스

### 2.1 Extract (추출)

**Python 크롤러 실행:**

```python
# main.py
import argparse
from crawlers import NaverCrawler, YouTubeCrawler, InstagramCrawler
from datetime import datetime, timedelta
import json

def main(platform, days_back):
    # 날짜 범위
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    results = []
    
    if platform in ['all', 'naver']:
        naver = NaverCrawler()
        results.extend(naver.crawl(start_date, end_date))
    
    if platform in ['all', 'youtube']:
        youtube = YouTubeCrawler()
        results.extend(youtube.crawl(start_date, end_date))
    
    # ... 다른 플랫폼
    
    # JSON 저장
    output_file = f'output/{platform}_{datetime.now().strftime("%Y%m%d")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(results)} posts to {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', choices=['all', 'naver', 'youtube', 'instagram', 'facebook'], required=True)
    parser.add_argument('--days', type=int, default=1)
    args = parser.parse_args()
    
    main(args.platform, args.days)
```

### 2.2 Transform (변환)

**Data Flow 로직 (pseudo-code):**

```python
# Azure Data Flow Transformation
def transform_posts(raw_data):
    # 1. JSON 파싱
    df = parse_json(raw_data)
    
    # 2. 해시태그 추출
    df['hashtags'] = df['content_text'].apply(extract_hashtags)
    
    # 3. 타겟 해시태그 필터링
    TARGET_HASHTAGS = ['#피엠인터내셔널', '#FitLine', ...]
    df = df[df['hashtags'].apply(lambda tags: any(t in tags for t in TARGET_HASHTAGS))]
    
    # 4. OCR (Azure CV API 호출)
    for idx, row in df.iterrows():
        ocr_texts = []
        for img_url in row['images']:
            ocr_text = call_azure_cv_api(img_url)
            ocr_texts.append(ocr_text)
        df.at[idx, 'ocr_text'] = '\n'.join(ocr_texts)
    
    # 5. NULL 처리
    df['like_count'].fillna(0, inplace=True)
    df['comment_count'].fillna(0, inplace=True)
    
    # 6. 날짜 형식 통일
    df['published_date'] = pd.to_datetime(df['published_date'])
    
    return df
```

### 2.3 Load (적재)

**Bulk Insert with pyodbc:**

```python
def bulk_insert_posts(df, connection):
    """
    대량 INSERT (Fast Executemany)
    """
    cursor = connection.cursor()
    cursor.fast_executemany = True
    
    # 사용자 ID 조회 (미리 캐싱)
    user_map = get_user_id_map(connection)
    
    # INSERT 준비
    insert_sql = """
        INSERT INTO fact_Posts (
            user_id, platform, post_url, title, content_text,
            ocr_text, hashtags, published_date,
            like_count, comment_count, view_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # 데이터 변환
    rows = []
    for _, post in df.iterrows():
        user_id = user_map.get((post['username'], post['platform']))
        if not user_id:
            continue
        
        rows.append((
            user_id, post['platform'], post['post_url'], post['title'],
            post['content_text'], post['ocr_text'],
            json.dumps(post['hashtags']), post['published_date'],
            post['like_count'], post['comment_count'], post['view_count']
        ))
    
    # Bulk INSERT
    cursor.executemany(insert_sql, rows)
    connection.commit()
    
    print(f"Inserted {len(rows)} posts")
```

---

## 3. 스케줄링 및 모니터링

### 3.1 에러 핸들링

**Retry 로직:**

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=5):
    """
    실패 시 재시도 데코레이터
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        print(f"Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        print("Max attempts reached. Giving up.")
                        raise
        return wrapper
    return decorator

# 사용 예시
@retry(max_attempts=3, delay=10)
def crawl_naver_blog(url):
    # 크롤링 로직
    pass
```

**로그 저장:**

```python
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    filename=f'logs/crawler_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 사용
logger.info("Starting Naver crawler...")
logger.error(f"Failed to crawl {url}: {error}")
```

### 3.2 알림 (Email/Slack)

**Azure Data Factory 알림:**

```json
{
  "pipeline": "Daily_SNS_Data_Collection",
  "trigger": {
    "type": "Schedule",
    "schedule": "0 2 * * *"
  },
  "activities": [
    {
      "name": "Send Email on Failure",
      "type": "WebActivity",
      "dependsOn": ["All Activities"],
      "onFailure": {
        "action": "SendEmail",
        "to": "data-team@pm-international.com",
        "subject": "Pipeline Failed",
        "body": "@{activity('crawl').error}"
      }
    }
  ]
}
```

---

# VI. 데이터 분석 및 모델링

## 1. 탐색적 데이터 분석 (EDA)

### 1.1 기본 통계

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 데이터 로드
df = pd.read_sql("SELECT * FROM fact_Posts", connection)

# 기본 정보
print(df.info())
print(df.describe())

# 플랫폼별 게시물 수
print(df['platform'].value_counts())

# 일별 게시물 추이
df['date'] = pd.to_datetime(df['published_date']).dt.date
daily_posts = df.groupby('date').size()
daily_posts.plot(title='Daily Posts Trend', figsize=(12,6))
plt.show()

# 참여율 분포
sns.histplot(df['engagement_rate'].dropna(), bins=50)
plt.title('Engagement Rate Distribution')
plt.show()
```

### 1.2 상관관계 분석

```python
# 숫자형 변수만
numeric_cols = ['like_count', 'comment_count', 'view_count', 'engagement_rate', 'followers_count']
corr_matrix = df[numeric_cols].corr()

# Heatmap
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
plt.title('Correlation Matrix')
plt.show()
```

---

## 2. 클러스터링 (K-Means)

### 2.1 피처 엔지니어링

```python
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import numpy as np

# 사용자별 집계 피처
user_features = df.groupby('user_id').agg({
    'post_id': 'count',  # 총 게시물 수
    'like_count': 'sum',
    'comment_count': 'sum',
    'engagement_rate': 'mean',
    'platform': lambda x: x.nunique()  # 활동 플랫폼 수
}).rename(columns={
    'post_id': 'total_posts',
    'like_count': 'total_likes',
    'comment_count': 'total_comments',
    'engagement_rate': 'avg_engagement',
    'platform': 'platform_count'
})

# 주간 게시 빈도 계산
df['week'] = pd.to_datetime(df['published_date']).dt.isocalendar().week
posts_per_week = df.groupby(['user_id', 'week']).size().groupby('user_id').mean()
user_features['posts_per_week'] = posts_per_week

# 해시태그 다양성
def hashtag_diversity(hashtags_series):
    all_tags = []
    for tags_json in hashtags_series:
        try:
            tags = json.loads(tags_json)
            all_tags.extend(tags)
        except:
            pass
    if len(all_tags) == 0:
        return 0
    return len(set(all_tags)) / len(all_tags)

hashtag_div = df.groupby('user_id')['hashtags'].apply(hashtag_diversity)
user_features['hashtag_diversity'] = hashtag_div

print(user_features.head())
```

### 2.2 최적 K 찾기 (Elbow + Silhouette)

```python
# 정규화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(user_features)

# Elbow Method
inertias = []
silhouettes = []
K_range = range(2, 11)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)
    silhouettes.append(silhouette_score(X_scaled, kmeans.labels_))

# 시각화
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,5))

ax1.plot(K_range, inertias, 'bo-')
ax1.set_xlabel('Number of Clusters (k)')
ax1.set_ylabel('Inertia')
ax1.set_title('Elbow Method')

ax2.plot(K_range, silhouettes, 'ro-')
ax2.set_xlabel('Number of Clusters (k)')
ax2.set_ylabel('Silhouette Score')
ax2.set_title('Silhouette Analysis')

plt.show()

# 최적 K 선택 (예: k=4)
optimal_k = 4
print(f"Optimal K: {optimal_k}")
```

### 2.3 클러스터링 실행 및 프로파일링

```python
# 최적 K로 클러스터링
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
user_features['cluster'] = kmeans.fit_predict(X_scaled)

# 클러스터별 프로파일
for i in range(optimal_k):
    print(f"\n===== Cluster {i} =====")
    cluster_data = user_features[user_features['cluster'] == i]
    print(f"Size: {len(cluster_data)} users ({len(cluster_data)/len(user_features)*100:.1f}%)")
    print(cluster_data.describe())

# 클러스터 명명
cluster_names = {
    0: "Super Engagers",
    1: "Steady Contributors",
    2: "Casual Sharers",
    3: "Dormant"
}

user_features['cluster_name'] = user_features['cluster'].map(cluster_names)

# 시각화 (PCA 2D)
from sklearn.decomposition import PCA

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

plt.figure(figsize=(10,8))
for i, name in cluster_names.items():
    mask = user_features['cluster'] == i
    plt.scatter(X_pca[mask, 0], X_pca[mask, 1], label=name, s=50, alpha=0.6)

plt.xlabel('PC1')
plt.ylabel('PC2')
plt.title('User Clusters (PCA)')
plt.legend()
plt.show()
```

---

## 3. 감성 분석 (Sentiment Analysis)

### 3.1 KoBERT 사용

```python
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# KoBERT 모델 로드
tokenizer = BertTokenizer.from_pretrained('monologg/kobert')
model = BertForSequenceClassification.from_pretrained('monologg/kobert', num_labels=3)

def sentiment_analysis(text):
    """
    감성 분석: 0=부정, 1=중립, 2=긍정
    """
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    sentiment = torch.argmax(probs).item()
    confidence = probs[0][sentiment].item()
    
    return {
        'sentiment': sentiment,
        'label': ['negative', 'neutral', 'positive'][sentiment],
        'confidence': confidence
    }

# 전체 게시물에 적용 (샘플링)
sample_posts = df.sample(min(1000, len(df)))

sentiments = []
for _, post in sample_posts.iterrows():
    result = sentiment_analysis(post['content_text'][:500])  # 처음 500자만
    sentiments.append(result)

df_sample = sample_posts.copy()
df_sample['sentiment'] = [s['sentiment'] for s in sentiments]
df_sample['sentiment_label'] = [s['label'] for s in sentiments]
df_sample['sentiment_confidence'] = [s['confidence'] for s in sentiments]

# 감성 분포
print(df_sample['sentiment_label'].value_counts())

# 감성과 참여율의 관계
sns.boxplot(data=df_sample, x='sentiment_label', y='engagement_rate')
plt.title('Engagement Rate by Sentiment')
plt.show()
```

---

## 4. 회귀 분석 (Regression)

### 4.1 모델 구축 (statsmodels)

```python
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler

# 종속변수: 월 매출 (가상 데이터, 실제로는 PMI 내부 데이터 연동 필요)
# 여기서는 engagement_rate를 대리 변수로 사용
y = user_features['avg_engagement']

# 독립변수
X = user_features[[
    'posts_per_week',
    'total_likes',
    'total_comments',
    'platform_count',
    'hashtag_diversity'
]]

# 정규화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_scaled = sm.add_constant(X_scaled)  # 상수항 추가

# OLS 회귀
model = sm.OLS(y, X_scaled)
results = model.fit()

# 결과 출력
print(results.summary())

# 해석
print("\n===== 해석 =====")
print(f"R-squared: {results.rsquared:.3f}")
print(f"Adj. R-squared: {results.rsquared_adj:.3f}")
print(f"F-statistic p-value: {results.f_pvalue:.4f}")

for i, col in enumerate(['const'] + list(X.columns)):
    coef = results.params[i]
    pval = results.pvalues[i]
    sig = '***' if pval < 0.001 else ('**' if pval < 0.01 else ('*' if pval < 0.05 else ''))
    print(f"{col}: β = {coef:.4f}, p = {pval:.4f} {sig}")
```

### 4.2 유의성 검증

**귀무가설 (H0)**: SNS 활동 지표는 성과에 영향을 미치지 않는다 (β = 0)  
**대립가설 (H1)**: SNS 활동 지표는 성과에 영향을 미친다 (β ≠ 0)

**유의수준**: α = 0.05

**결과 해석 예시:**
```
posts_per_week: β = 0.125, p = 0.0001 ***
→ p < 0.05이므로 귀무가설 기각
→ 주간 게시 빈도는 참여율에 유의한 영향을 미침
→ 주 1회 게시 증가 시 참여율 12.5%p 증가

platform_count: β = 0.087, p = 0.023 *
→ 다중 플랫폼 활용 시 참여율 증가

hashtag_diversity: β = 0.032, p = 0.421
→ p > 0.05이므로 귀무가설 채택 불가
→ 해시태그 다양성은 유의한 영향 없음
```

---

# VII. 시각화 및 대시보드

## 1. Power BI 연동

### 1.1 연결 설정

**Power BI Desktop:**
1. "Get Data" → "Azure SQL Database"
2. Server: `your-server.database.windows.net`
3. Database: `PMI_SNS_DB`
4. Authentication: Database (username/password)
5. Select Tables: `dim_Users`, `fact_Posts`, `agg_DailyMetrics`

### 1.2 데이터 모델링

**관계 설정:**
```
dim_Users (user_id) 1 -------- ∞ fact_Posts (user_id)
fact_Posts (post_id) 1 -------- ∞ fact_VideoTranscripts (post_id)
dim_Users (user_id) 1 -------- ∞ agg_DailyMetrics (user_id)
```

**계산 필드 (DAX):**

```dax
// 총 게시물 수
Total Posts = COUNTROWS(fact_Posts)

// 평균 참여율
Avg Engagement = AVERAGE(fact_Posts[engagement_rate])

// 월간 게시물 증가율
MoM Growth = 
VAR CurrentMonth = CALCULATE([Total Posts], DATESMTD(fact_Posts[published_date]))
VAR PreviousMonth = CALCULATE([Total Posts], DATEADD(fact_Posts[published_date], -1, MONTH))
RETURN DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0)

// 클러스터별 사용자 수 (사전에 클러스터 정보를 dim_Users에 추가)
Users by Cluster = COUNTROWS(FILTER(dim_Users, dim_Users[cluster] = "Super Engagers"))
```

---

## 2. 핵심 KPI 정의

### 2.1 KPI 리스트

| KPI | 정의 | 목표값 | 대시보드 시각화 |
|-----|------|--------|----------------|
| **일일 게시물 수** | 일일 수집 게시물 수 | 500+ | 선 그래프 (추세) |
| **평균 참여율** | (좋아요+댓글)/조회수 | 5% | 게이지 차트 |
| **플랫폼 비중** | 플랫폼별 게시물 % | Balanced | 파이 차트 |
| **고참여율 게시물 비율** | engagement > 10% | 15% | 도넛 차트 |
| **클러스터 분포** | 각 클러스터 사용자 수 | - | 막대 그래프 |
| **감성 스코어** | 긍정 게시물 % | 80% | 누적 막대 |
| **리스크 게시물** | 부정 또는 과장 의심 | <5% | 경고 카드 |

---

## 3. 대시보드 설계

### 3.1 Page 1: Overview (개요)

**레이아웃:**
```
┌─────────────────────────────────────────────────────┐
│ 📊 PM-International Korea SNS 활동 대시보드           │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ 총 게시물 │ 평균 참여 │ 활동 사용자│ 리스크   │ 최신 업데이트│
│ 15,234   │  5.8%   │  1,850  │   23    │ 2024-10-27│
├──────────┴──────────┴──────────┴──────────┴─────────┤
│                                                      │
│  [일일 게시물 추세 - 선 그래프]                         │
│                                                      │
├───────────────────────┬──────────────────────────────┤
│ 플랫폼별 게시물 (파이)  │  클러스터 분포 (막대)          │
│                       │                              │
│  Naver: 40%          │  Super Engagers: 15%         │
│  YouTube: 25%        │  Steady: 35%                 │
│  Instagram: 20%      │  Casual: 40%                 │
│  ...                 │  Dormant: 10%                │
└───────────────────────┴──────────────────────────────┘
```

### 3.2 Page 2: Platform Analysis (플랫폼 분석)

**슬라이서:**
- 플랫폼 선택: [All, Naver, YouTube, Instagram, KakaoStory, Facebook]
- 날짜 범위: [최근 7일, 30일, 90일, All]

**차트:**
1. 플랫폼별 평균 참여율 (막대 그래프)
2. 플랫폼별 게시물 수 추이 (선 그래프)
3. 플랫폼별 상위 해시태그 (워드 클라우드)

### 3.3 Page 3: User Clusters (사용자 클러스터)

**테이블:**
| 클러스터 | 사용자 수 | 주간 게시 | 평균 참여율 | 대표 사용자 |
|----------|-----------|-----------|------------|------------|
| Super Engagers | 278 | 8.2 | 12.4% | @user123 |
| Steady | 648 | 3.1 | 6.2% | @user456 |
| ... | ... | ... | ... | ... |

**인사이트 카드:**
- "Super Engagers는 Steady 대비 참여율 2배 높음"
- "Dormant 사용자 중 35%가 최근 한 달간 활동 없음"

### 3.4 Page 4: Risk Monitoring (리스크 모니터링)

**필터:**
- 감성: [부정, 중립, 긍정]
- 리스크 레벨: [낮음, 중간, 높음]

**테이블:**
| 게시물 URL | 작성자 | 감성 | 리스크 스코어 | 키워드 |
|-----------|--------|------|-------------|--------|
| blog.naver.com/... | user789 | 부정 | 85 | "사기", "환불" |
| youtube.com/... | user234 | 긍정 | 92 | "월 1000만원" |

**액션:**
- [게시물 보기] 버튼
- [담당자 알림] 버튼

---

# VIII. 기술 스택 및 환경 설정

## 1. 필요 도구 및 라이브러리

### 1.1 Python 라이브러리

```bash
# requirements.txt

# 웹 크롤링
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
webdriver-manager==4.0.1

# 데이터 처리
pandas==2.1.3
numpy==1.26.2

# 데이터베이스
pyodbc==5.0.1
sqlalchemy==2.0.23

# OCR
easyocr==1.7.1
Pillow==10.1.0

# 동영상
yt-dlp==2023.11.16
youtube-transcript-api==0.6.1
openai-whisper==20231117  # Self-hosted STT

# 머신러닝
scikit-learn==1.3.2
statsmodels==0.14.0

# NLP
transformers==4.35.2
torch==2.1.1
konlpy==0.6.0

# Azure SDK
azure-storage-blob==12.19.0
azure-cognitiveservices-vision-computervision==0.9.0

# 시각화
matplotlib==3.8.2
seaborn==0.13.0

# 유틸리티
python-dotenv==1.0.0
tqdm==4.66.1
```

**설치:**
```bash
pip install -r requirements.txt
```

### 1.2 시스템 요구사항

**개발 환경:**
- OS: Windows 10/11, macOS, Linux (Ubuntu 22.04 권장)
- Python: 3.9 이상
- RAM: 8GB 이상 (16GB 권장)
- Disk: 50GB 이상 (모델 다운로드용)

**Azure VM (프로덕션):**
- Size: Standard_D4s_v3 (4 vCPU, 16GB RAM)
- OS: Ubuntu 22.04 LTS
- Disk: 128GB Premium SSD

---

## 2. 개발 환경 구축

### 2.1 로컬 개발 환경

**Step 1: Python 가상환경 생성**
```bash
# venv 생성
python -m venv venv

# 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 라이브러리 설치
pip install -r requirements.txt
```

**Step 2: 환경 변수 설정**
```bash
# .env 파일 생성
cat > .env << EOF
# Naver API
NAVER_CLIENT_ID=9v7cOolOk2ctSQXc73sd
NAVER_CLIENT_SECRET=9jHcXVNQwZ

# YouTube API
YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY

# Instagram/Facebook
FB_APP_ID=YOUR_FB_APP_ID
FB_APP_SECRET=YOUR_FB_APP_SECRET
INSTAGRAM_ACCESS_TOKEN=YOUR_INSTAGRAM_TOKEN

# Azure SQL Database
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=PMI_SNS_DB
AZURE_SQL_USERNAME=admin
AZURE_SQL_PASSWORD=your_password

# Azure Computer Vision
AZURE_CV_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_CV_KEY=your_subscription_key
EOF
```

**Step 3: Chrome WebDriver 설치**
```python
# 자동 설치 (webdriver-manager)
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

### 2.2 Azure VM 설정 (프로덕션)

**Step 1: VM 생성**
```bash
# Azure CLI로 VM 생성
az vm create \
  --resource-group PMI-SNS-RG \
  --name pmi-sns-crawler-vm \
  --image UbuntuLTS \
  --size Standard_D4s_v3 \
  --admin-username azureuser \
  --generate-ssh-keys
```

**Step 2: SSH 접속 및 환경 구축**
```bash
# SSH 접속
ssh azureuser@<VM_IP>

# Python 3.10 설치
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip -y

# Chrome & ChromeDriver 설치 (Headless)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb -y

# 프로젝트 클론
git clone https://github.com/your-org/pmi-sns-crawler.git
cd pmi-sns-crawler

# 가상환경 및 라이브러리
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env 파일 업로드 (로컬에서)
# 로컬:
scp .env azureuser@<VM_IP>:~/pmi-sns-crawler/
```

**Step 3: Cron 설정 (일일 자동 실행)**
```bash
# crontab 편집
crontab -e

# 매일 02:00 (KST = UTC+9, 즉 17:00 UTC)에 실행
0 17 * * * cd /home/azureuser/pmi-sns-crawler && /home/azureuser/pmi-sns-crawler/venv/bin/python main.py --platform all --days 1 >> /home/azureuser/logs/crawler.log 2>&1
```

---

## 3. 버전 관리 (Git)

### 3.1 Git 저장소 구조

```
pmi-sns-crawler/
├── .env.example          # 환경 변수 템플릿
├── .gitignore
├── README.md
├── requirements.txt
├── main.py               # 메인 실행 파일
├── config/
│   └── settings.py       # 설정 관리
├── crawlers/
│   ├── __init__.py
│   ├── naver_crawler.py
│   ├── youtube_crawler.py
│   ├── instagram_crawler.py
│   ├── kakao_crawler.py
│   └── facebook_crawler.py
├── processors/
│   ├── __init__.py
│   ├── ocr_processor.py
│   └── video_transcriber.py
├── database/
│   ├── __init__.py
│   ├── connection.py
│   └── models.py
├── analysis/
│   ├── __init__.py
│   ├── clustering.py
│   ├── sentiment.py
│   └── regression.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── retry.py
└── tests/
    ├── test_naver.py
    └── test_ocr.py
```

### 3.2 .gitignore

```
# .gitignore

# 환경 변수
.env

# Python
__pycache__/
*.py[cod]
*$py.class
venv/
*.so

# 데이터
*.csv
*.json
output/
logs/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

# IX. 프로젝트 일정 및 마일스톤

## 1. 12주 타임라인

| 주차 | 활동 | 산출물 | 담당 |
|------|------|--------|------|
| **Week 1-2** | 환경 설정, API 테스트 | 개발 환경, 테스트 데이터 | 인턴 |
| **Week 3-4** | 네이버 블로그 크롤러 개발 | naver_crawler.py, 1K posts | 인턴 |
| **Week 5-6** | 유튜브, 인스타그램 크롤러 | youtube_crawler.py, instagram_crawler.py | 인턴 |
| **Week 7** | 카카오스토리, 페이스북 크롤러 | 전체 크롤러 완성 | 인턴 |
| **Week 8** | Azure SQL Database 설정 | 스키마, 초기 데이터 | 인턴 + DevOps |
| **Week 9** | Azure Data Factory 파이프라인 | ETL 자동화 | DevOps |
| **Week 10** | 데이터 분석 (클러스터링, 회귀) | 분석 스크립트, 인사이트 리포트 | 인턴 + 데이터 분석가 |
| **Week 11** | Power BI 대시보드 개발 | 대시보드 v1.0 | 인턴 + BI 전문가 |
| **Week 12** | 최종 테스트, 문서화, 인수인계 | 운영 매뉴얼, 최종 보고서 | 전체 팀 |

### 1.1 주차별 상세 계획

**Week 1-2: Setup & Learning**
- Day 1-2: 프로젝트 킥오프, 요구사항 확인
- Day 3-5: 로컬 개발 환경 구축, Python 라이브러리 설치
- Day 6-8: Naver/YouTube API 테스트, 샘플 크롤링
- Day 9-10: 코드 리뷰, Git 저장소 설정

**Week 3-4: Naver Blog Crawler**
- Day 11-13: Naver Search API + Selenium 통합
- Day 14-16: 해시태그 필터링 로직 구현 및 테스트
- Day 17-18: OCR (EasyOCR) 통합
- Day 19-20: 1,000개 샘플 수집, 데이터 검증

**Week 5-6: YouTube & Instagram**
- Day 21-23: YouTube Data API 구현, 자막 다운로드
- Day 24-26: Instagram Graph API 구현, Access Token 관리
- Day 27-28: 병렬 처리 최적화
- Day 29-30: 통합 테스트, 5,000개 데이터 수집

**Week 7: Kakao & Facebook**
- Day 31-32: 카카오스토리 스크래핑 (법적 검토)
- Day 33-34: Facebook Graph API 구현
- Day 35: 전체 크롤러 통합 테스트

**Week 8: Database Setup**
- Day 36-37: Azure SQL Database 생성, 스키마 구현
- Day 38-39: 초기 데이터 마이그레이션 (CSV → SQL)
- Day 40: 인덱스 최적화, 쿼리 성능 테스트

**Week 9: Automation Pipeline**
- Day 41-42: Azure Data Factory 파이프라인 설계
- Day 43-44: ETL Activities 구현 (Copy, Data Flow)
- Day 45: 스케줄링 설정, 에러 핸들링

**Week 10: Data Analysis**
- Day 46-47: 탐색적 데이터 분석 (EDA)
- Day 48-49: 클러스터링 (K-Means), 감성 분석
- Day 50: 회귀 분석, 인사이트 리포트 작성

**Week 11: Dashboard**
- Day 51-52: Power BI 연결, 데이터 모델링
- Day 53-54: 대시보드 페이지 구축 (4 pages)
- Day 55: 대시보드 리뷰, 피드백 반영

**Week 12: Finalization**
- Day 56-57: 전체 시스템 통합 테스트
- Day 58-59: 문서 작성 (운영 매뉴얼, 트러블슈팅 가이드)
- Day 60: 최종 발표, 인수인계

---

## 2. 주차별 산출물

| 주차 | 산출물 | 형식 |
|------|--------|------|
| Week 1-2 | 개발 환경 구축 완료 보고서 | 문서 (MD) |
| Week 3-4 | naver_crawler.py, 샘플 데이터 1K | 코드 + CSV |
| Week 5-6 | youtube_crawler.py, instagram_crawler.py, 샘플 5K | 코드 + CSV |
| Week 7 | 전체 크롤러 통합, 샘플 10K | 코드 + CSV |
| Week 8 | Azure SQL Database 스키마 | SQL DDL 스크립트 |
| Week 9 | Azure Data Factory Pipeline JSON | JSON |
| Week 10 | 데이터 분석 스크립트, 인사이트 리포트 | Jupyter Notebook, PDF |
| Week 11 | Power BI 대시보드 (.pbix) | PBIX 파일 |
| Week 12 | 최종 보고서, 운영 매뉴얼 | PDF |

---

## 3. 리스크 관리

### 3.1 리스크 목록

| 리스크 | 확률 | 영향도 | 대응 방안 |
|--------|------|--------|-----------|
| **API 변경** (Naver, Instagram) | 중간 | 높음 | 주기적 모니터링, 대체 방법 준비 |
| **크롤링 차단** (IP 블록) | 낮음 | 높음 | Rate limiting, 프록시 사용 |
| **데이터 품질 문제** | 높음 | 중간 | 샘플링 검증, 자동 품질 체크 |
| **일정 지연** (학습 곡선) | 중간 | 중간 | 버퍼 시간 확보, 우선순위 조정 |
| **Azure 비용 초과** | 낮음 | 낮음 | 비용 알림 설정, 리소스 최적화 |

### 3.2 컨티전시 플랜

**시나리오 1: Naver API 변경 → 크롤링 불가**
- 대응: Selenium만으로 전환 (느리지만 안정적)
- 영향: 수집 속도 50% 감소
- 복구 시간: 2-3일

**시나리오 2: Instagram API Rate Limit 초과**
- 대응: 여러 Facebook App 사용 (다중 Access Token)
- 영향: 구조 복잡도 증가
- 추가 시간: 1일

**시나리오 3: OCR 정확도 낮음 (< 70%)**
- 대응: EasyOCR → Azure CV로 전환
- 영향: 비용 증가 ($5/월)
- 복구 시간: 즉시

---

# X. 인수인계 및 문서화

## 1. 코드 문서화 가이드

### 1.1 Docstring 규칙

**함수 Docstring (Google Style):**

```python
def crawl_naver_blog(url, target_hashtags):
    """
    네이버 블로그 게시물 크롤링 및 해시태그 필터링
    
    Args:
        url (str): 네이버 블로그 게시물 URL
        target_hashtags (list): 타겟 해시태그 리스트 (예: ['#피엠인터내셔널'])
    
    Returns:
        dict: {
            'title': str,
            'content_text': str,
            'hashtags': list,
            'images': list,
            'videos': list
        } 또는 None (크롤링 실패 시)
    
    Raises:
        TimeoutException: 페이지 로딩 시간 초과 (10초)
        NoSuchElementException: 필수 요소 미발견
    
    Example:
        >>> result = crawl_naver_blog('https://blog.naver.com/...', ['#피엠인터내셔널'])
        >>> print(result['title'])
        'FitLine 후기'
    """
    # 구현...
```

### 1.2 README.md 작성

```markdown
# PM-International Korea SNS Crawler

## 프로젝트 개요
PM-International Korea 팀파트너의 SNS 활동 데이터를 자동 수집하는 크롤러

## 주요 기능
- 5개 SNS 플랫폼 크롤링 (Naver, YouTube, Instagram, KakaoStory, Facebook)
- 이미지 OCR 및 동영상 스크립트 추출
- Azure SQL Database 자동 적재
- Power BI 대시보드 연동

## 설치 방법
\```bash
git clone https://github.com/your-org/pmi-sns-crawler.git
cd pmi-sns-crawler
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
\```

## 사용 방법
\```bash
# .env 파일 설정
cp .env.example .env
# .env 편집하여 API 키 입력

# 크롤링 실행
python main.py --platform all --days 1

# 특정 플랫폼만
python main.py --platform naver --days 7
\```

## 설정
- `config/settings.py`: 크롤링 설정, 타겟 해시태그
- `.env`: API 키, 데이터베이스 연결 정보

## 트러블슈팅
### 문제: "ChromeDriver not found"
해결: `webdriver-manager`가 자동으로 설치하지만, 수동 다운로드 필요 시 [링크](...)

### 문제: "Azure SQL connection failed"
해결: 방화벽 설정에서 현재 IP 추가 필요

## 라이선스
MIT
```

---

## 2. 운영 매뉴얼

### 2.1 일일 운영 체크리스트

**매일 오전 9시 (KST):**
- [ ] 전날 크롤링 작업 로그 확인 (`/logs/crawler_YYYYMMDD.log`)
- [ ] Azure Data Factory 파이프라인 실행 상태 확인
- [ ] Power BI 대시보드 데이터 최신화 확인 (마지막 업데이트 날짜)
- [ ] 에러 발생 시: Slack/Email 알림 확인 및 대응

**주간 (매주 월요일):**
- [ ] 지난 주 수집 통계 리뷰 (게시물 수, 에러율)
- [ ] Azure 리소스 비용 확인
- [ ] 데이터베이스 용량 확인 (> 80% 시 Scale-up)

**월간 (매월 1일):**
- [ ] Access Token 갱신 (Instagram, Facebook)
- [ ] 전월 인사이트 리포트 작성
- [ ] 크롤러 코드 업데이트 (API 변경 대응)

### 2.2 에러 대응 가이드

**Error 1: "Naver API quota exceeded"**
```
원인: 일일 25,000 calls 초과
대응: 
1. 크롤링 빈도 조정 (일 1회 → 주 3회)
2. 키워드 수 감소
3. 추가 API 키 발급 (다른 계정)
```

**Error 2: "Instagram API 429 Too Many Requests"**
```
원인: 시간당 200 calls 초과
대응:
1. RateLimiter 클래스 적용 (190 calls/hour로 제한)
2. 여러 Access Token 사용 (다중 계정)
```

**Error 3: "Azure SQL Database connection timeout"**
```
원인: 방화벽, 네트워크 문제
대응:
1. Azure Portal → SQL Database → Networking → Firewall 확인
2. 현재 IP 추가
3. Connection String 확인
```

---

## 3. 트러블슈팅 가이드

### 3.1 크롤링 문제

**문제: 네이버 블로그 iframe 전환 실패**
```python
# 해결책
try:
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'mainFrame'))
    )
    driver.switch_to.frame(iframe)
except TimeoutException:
    print("iframe not found, trying alternative method...")
    # 대안: 직접 HTML 파싱
```

**문제: YouTube API quota exceeded**
```python
# 해결책: 여러 API Key 사용
API_KEYS = ['KEY1', 'KEY2', 'KEY3']
current_key_index = 0

def get_youtube_client():
    global current_key_index
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return build('youtube', 'v3', developerKey=key)
```

### 3.2 데이터베이스 문제

**문제: Deadlock detected**
```sql
-- 해결책: Transaction Isolation Level 조정
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

**문제: Slow query (> 10초)**
```sql
-- 해결책: 인덱스 추가 또는 쿼리 최적화
-- 실행 계획 확인
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT * FROM fact_Posts WHERE ...;
```

---

# 부록

## A. Python 코드 전체 (모듈별)

*참고: 위에서 제공한 코드 스니펫들을 모듈별로 정리한 완전한 코드*

## B. SQL 스크립트

*참고: 위에서 제공한 DDL, DML, Stored Procedure 등*

## C. Azure 리소스 설정 가이드

### C.1 Azure SQL Database 생성

```bash
# Resource Group 생성
az group create --name PMI-SNS-RG --location koreacentral

# SQL Server 생성
az sql server create \
  --name pmi-sns-server \
  --resource-group PMI-SNS-RG \
  --location koreacentral \
  --admin-user sqladmin \
  --admin-password 'YourPassword123!'

# SQL Database 생성 (S2: 50 DTU)
az sql db create \
  --resource-group PMI-SNS-RG \
  --server pmi-sns-server \
  --name PMI_SNS_DB \
  --service-objective S2

# 방화벽 규칙 (현재 IP 허용)
az sql server firewall-rule create \
  --resource-group PMI-SNS-RG \
  --server pmi-sns-server \
  --name AllowMyIP \
  --start-ip-address <YOUR_IP> \
  --end-ip-address <YOUR_IP>
```

### C.2 Azure Blob Storage 생성

```bash
# Storage Account 생성
az storage account create \
  --name pmisnsstorage \
  --resource-group PMI-SNS-RG \
  --location koreacentral \
  --sku Standard_LRS

# Container 생성
az storage container create \
  --name raw \
  --account-name pmisnsstorage

# Access Key 확인
az storage account keys list \
  --resource-group PMI-SNS-RG \
  --account-name pmisnsstorage
```

## D. API 인증 설정 가이드

### D.1 Naver API

1. https://developers.naver.com/apps/#/register 접속
2. "애플리케이션 등록" 클릭
3. 애플리케이션 이름: "PMI SNS Crawler"
4. 사용 API: "검색"
5. 비로그인 오픈 API 서비스 환경: "WEB 설정" (http://localhost)
6. Client ID, Client Secret 확인 → `.env`에 저장

### D.2 YouTube API

1. https://console.cloud.google.com/ 접속
2. 프로젝트 생성: "PMI-SNS-Project"
3. "API 및 서비스" → "라이브러리" → "YouTube Data API v3" 검색 → 사용 설정
4. "사용자 인증 정보" → "사용자 인증 정보 만들기" → "API 키"
5. API 키 확인 → `.env`에 저장

### D.3 Instagram Graph API

*참고: 위에서 제공한 상세 가이드 참조*

---

**[문서 끝]**

**버전 이력:**
- v1.0 (2024-10-01): 초안 작성
- v2.0 (2024-10-15): 기술 스택 업데이트, Azure 연동 추가
- **v2.2 (2025-10-27): 최종 버전 - 전체 구현 가이드 완성**

**작성자**: PMI코리아 데이터 엔지니어링 팀  
**검토자**: 프로젝트 매니저, CTO  
**승인 일자**: 2025년 10월 27일