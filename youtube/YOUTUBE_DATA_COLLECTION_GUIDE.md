# YouTube PMIK 판매원 데이터 수집 가이드

## 📋 목차
1. [데이터 수집 방법 비교](#데이터-수집-방법-비교)
2. [추천 수집 방법](#추천-수집-방법)
3. [YouTube 데이터 컬럼 구조](#youtube-데이터-컬럼-구조)
4. [구현 로드맵](#구현-로드맵)

---

## 🔍 기존 프로젝트 분석 요약

### 1. 카카오스토리 (kakaostory_posts.json)
**수집 방법**: 웹 개발자 도구 기반 크롤링 (브라우저 Network 탭 분석)
- `user_id`, `shortcode` 기반 게시물 식별
- 이미지/비디오 URL 직접 추출
- 좋아요/댓글 수 수집

**주요 컬럼** (17개):
```
- p_num, name, user_id, shortcode, date
- media_type, media_url[], media_count
- content, content_count
- hashtag[], hashtag_count
- like_count, comment_count
```

### 2. 네이버 블로그 (pm_naver_blog_crawler_v8_4_final.py)
**수집 방법**: Naver Open API + Selenium 크롤링 (하이브리드)
- API로 검색 → URL 수집 (키워드당 1000개)
- Selenium으로 상세 크롤링 (본문, 댓글 등)
- 3단계 필터링 (블랙리스트, PM 키워드, 언론 스타일)

**주요 컬럼** (15개):
```
- platform, post_id, blog_id, url
- title, content, published_datetime
- sponsor_phone, sponsor_partner_id
- like_count, comment_count
- hashtags, image_urls, video_urls
- collected_date
```

### 3. 멀티미디어 분석 (Google Colab)
**처리 파이프라인**:
1. URL 추출 (`step1_extract_urls.py`)
2. Google Colab에서 OCR + 음성 분석
   - 이미지 OCR (Tesseract/Google Vision)
   - 비디오 프레임 OCR
   - Whisper 음성 자막 생성
   - YouTube 자막 추출
3. 결과 병합 (`merge_ocr_results.py`)

**최종 병합 데이터 컬럼** (19개):
```
기본 (15개): platform ~ collected_date
분석 (4개):
- image_ocr_text
- video_frame_ocr_text
- whisper_transcript
- youtube_transcript
```

---

## 📊 Task 1: YouTube 데이터 수집 방법 제안

### 방법 1: YouTube Data API v3 (✅ 추천 - 메인 방법)

**장점**:
- 공식 API로 안정적이고 합법적
- 검색, 채널, 영상 상세 정보 모두 제공
- 구조화된 JSON 응답
- 할당량 관리 가능 (일 10,000 units)

**단점**:
- API 키 필요 (Google Cloud Console)
- 일일 할당량 제한 (초과 시 비용 발생)
- 댓글 수집 시 할당량 소모 큼

**구현 절차**:
```python
# 1. 키워드 검색으로 영상 수집
search().list(
    q="피엠인터내셔널 OR 독일피엠 OR 피트라인",
    type="video",
    maxResults=50
)

# 2. 영상 상세 정보 조회
videos().list(
    id=video_id,
    part="snippet,statistics,contentDetails"
)

# 3. 댓글 수집
commentThreads().list(
    videoId=video_id,
    maxResults=100
)

# 4. 채널 정보 조회
channels().list(
    id=channel_id,
    part="snippet,statistics"
)
```

**할당량 최적화 전략**:
- 검색: 100 units (키워드별)
- 영상 상세: 1 unit (비디오별)
- 댓글: 1 unit (영상별)
- 일일 목표: 약 200-300개 영상 수집 가능

**네이버 블로그와의 유사점**:
- 네이버: Naver Open API → Selenium 보완
- YouTube: YouTube Data API v3 → 자막 별도 추출

---

### 방법 2: youtube-transcript-api (보조 방법)

**용도**: 자막 데이터 추출 (API 할당량 절약)

**장점**:
- API 키 불필요
- 무료, 할당량 제한 없음
- 한국어 자막 포함 모든 언어 지원

**단점**:
- 자막이 없는 영상은 수집 불가
- 영상 메타데이터는 수집 불가

```python
from youtube_transcript_api import YouTubeTranscriptApi

# 자막 추출
transcript = YouTubeTranscriptApi.get_transcript(
    video_id, 
    languages=['ko', 'en']
)
```

**활용 시나리오**:
- YouTube API로 메타데이터 수집
- transcript-api로 자막 수집 (할당량 절약)
- 자막 없는 경우 Whisper로 음성 인식

---

### 방법 3: Selenium 웹 크롤링 (❌ 비추천)

**문제점**:
- YouTube 로봇 감지 시스템이 강력함
- 빈번한 차단 및 CAPTCHA
- 동적 로딩으로 크롤링 복잡
- 법적 리스크 (이용약관 위반)

**결론**: 네이버 블로그처럼 Selenium을 사용하지 **말 것**

---

### 방법 4: 하이브리드 방식 (✅ 최종 추천)

**조합**:
```
YouTube Data API v3 (메타데이터)
    ↓
youtube-transcript-api (자막)
    ↓
Whisper (자막 없는 영상의 음성 인식)
    ↓
Google Vision API (썸네일 OCR)
```

**장점**:
- API 할당량 효율적 사용
- 합법적이고 안정적
- 네이버 블로그 파이프라인과 동일 구조
- 멀티미디어 분석 재사용 가능

**네이버 블로그 방식과의 대응**:
| 네이버 블로그 | YouTube |
|--------------|---------|
| Naver Open API | YouTube Data API v3 |
| Selenium 크롤링 | youtube-transcript-api |
| 이미지 URL 추출 | 썸네일 URL (API 제공) |
| 비디오 URL 추출 | 영상 URL (API 제공) |
| Google Colab OCR | 동일 파이프라인 재사용 |

---

## 📝 Task 2: YouTube 수집 컬럼 제안

### 기본 메타데이터 컬럼 (YouTube API 기반)

```python
# 1. 플랫폼 식별
- platform: str = "youtube"
- video_id: str  # 고유 식별자 (예: "dQw4w9WgXcQ")
- url: str  # 전체 URL

# 2. 채널 정보
- channel_id: str
- channel_name: str
- channel_subscriber_count: int  # 구독자 수
- channel_video_count: int  # 총 영상 수
- channel_view_count: int  # 총 조회수

# 3. 영상 기본 정보
- title: str
- description: str  # 영상 설명 (본문)
- published_datetime: str  # ISO 8601 형식
- duration: str  # ISO 8601 duration (예: "PT4M13S")
- duration_seconds: int  # 초 단위 변환

# 4. 영상 통계
- view_count: int  # 조회수
- like_count: int  # 좋아요
- comment_count: int  # 댓글 수
- favorite_count: int  # 즐겨찾기 (보통 0)

# 5. 콘텐츠 분류
- category_id: str  # YouTube 카테고리 ID
- tags: str  # 쉼표 구분 태그
- hashtags: str  # 설명란의 #태그 추출

# 6. 추천인 정보 (네이버 블로그와 동일)
- sponsor_phone: str  # 전화번호 추출
- sponsor_partner_id: str  # 8자리 파트너 ID

# 7. 멀티미디어
- thumbnail_url: str  # 고화질 썸네일
- has_captions: bool  # 자막 존재 여부
- caption_language: str  # 자막 언어 (ko, en 등)

# 8. 메타 정보
- collected_date: str  # 수집 날짜
```

### 멀티미디어 분석 컬럼 (Google Colab 처리)

```python
# 9. 자막 분석
- youtube_transcript: str  # 공식 자막
- whisper_transcript: str  # Whisper 음성 인식 (자막 없을 때)
- transcript_language: str  # 자막 언어

# 10. 썸네일 OCR
- thumbnail_ocr_text: str  # 썸네일 텍스트 추출
- thumbnail_ocr_confidence: float

# 11. 키프레임 분석 (선택)
- keyframe_ocr_text: str  # 영상 주요 프레임 OCR
- keyframe_timestamps: str  # OCR 수행한 타임스탬프

# 12. 댓글 분석 (상위 댓글)
- top_comments: str  # 좋아요 많은 댓글 (최대 10개)
- comment_sentiment: str  # 감성 분석 (긍정/부정/중립)
```

### 필터링 관련 컬럼

```python
# 13. 필터링 메타
- is_pm_related: bool  # PM 브랜드 키워드 포함
- is_sales_post: bool  # 판매원 게시물 여부
- filter_score: float  # 관련도 점수 (0-1)
```

---

## 📂 최종 컬럼 구조 (30개 권장)

### 카카오스토리와 비교

| 구분 | 카카오스토리 | 네이버 블로그 | YouTube (제안) |
|------|-------------|--------------|----------------|
| 기본 컬럼 | 17개 | 15개 | **22개** |
| 분석 컬럼 | 0개 | 4개 | **8개** |
| **총계** | **17개** | **19개** | **30개** |

### 컬럼 우선순위

**필수 (Phase 1)** - 22개:
```
✅ platform, video_id, url
✅ channel_id, channel_name, channel_subscriber_count
✅ title, description, published_datetime
✅ duration, duration_seconds
✅ view_count, like_count, comment_count
✅ tags, hashtags
✅ sponsor_phone, sponsor_partner_id
✅ thumbnail_url, has_captions
✅ collected_date
```

**권장 (Phase 2)** - 8개:
```
🔶 youtube_transcript, whisper_transcript
🔶 thumbnail_ocr_text, thumbnail_ocr_confidence
🔶 top_comments, comment_sentiment
🔶 is_pm_related, filter_score
```

---

## 🚀 구현 로드맵

### Phase 1: 기본 수집 (1-2주)
```python
# youtube_crawler_v1.py
1. YouTube Data API 연동
2. 키워드 검색 구현
   - "피엠인터내셔널", "독일피엠", "피트라인" 등
3. 영상 메타데이터 수집
4. CSV 저장 (22개 컬럼)
5. 중복 제거 및 필터링
```

### Phase 2: 자막 수집 (1주)
```python
# youtube_transcript_collector.py
1. youtube-transcript-api 연동
2. Phase 1 CSV에서 video_id 읽기
3. 자막 수집 (한국어 우선)
4. 자막 없으면 Whisper 대기열 추가
5. 결과 병합
```

### Phase 3: 멀티미디어 분석 (1주)
```python
# Google Colab 재사용
1. 썸네일 다운로드
2. Google Vision OCR
3. Whisper 음성 인식 (자막 없는 영상)
4. 결과 병합 (merge_youtube_analysis.py)
```

### Phase 4: 댓글 분석 (선택, 1주)
```python
# youtube_comment_analyzer.py
1. 상위 댓글 수집 (좋아요순)
2. 감성 분석 (KoBERT 등)
3. 추천인 정보 댓글에서 추출
```

---

## 💡 네이버 블로그 코드 재사용 가능 부분

### 1. 필터링 로직 (100% 재사용)
```python
# pm_naver_blog_crawler_v8_4_final.py에서
- PM_BRAND_KEYWORDS
- PM_SALES_KEYWORDS
- EXCLUDE_KEYWORDS
- content_passes_filter() 함수
→ YouTube 설명, 자막, 댓글에 동일 적용
```

### 2. 추천인 정보 추출 (100% 재사용)
```python
- extract_sponsor_phone()
- extract_sponsor_partner_id()
→ YouTube 설명란, 댓글에 적용
```

### 3. 멀티미디어 파이프라인 (90% 재사용)
```python
- step1_extract_urls.py 구조
- Google Colab OCR 노트북
- merge_ocr_results.py 로직
→ YouTube 썸네일, 자막에 적용
```

### 4. 통계 및 로깅 (100% 재사용)
```python
- CrawlStats 클래스
- KeywordStats 클래스
- ColoredFormatter 로거
→ YouTube 크롤러에 동일 적용
```

---

## ⚠️ 주의사항

### 1. API 할당량 관리
```python
# 일일 10,000 units 제한
- 검색 1회: 100 units
- 영상 조회 1회: 1 unit
- 댓글 조회 1회: 1 unit

# 최적화 전략
- 검색: 50개 키워드 × 50개 결과 = 5,000 units
- 영상 상세: 2,500개 영상 = 2,500 units
- 댓글: 500개 영상 = 500 units
→ 총 8,000 units (여유 2,000)
```

### 2. YouTube API 키 설정
```bash
# .env 파일 (네이버와 유사)
YOUTUBE_API_KEY="your_api_key_here"
```

### 3. 저작권 및 프라이버시
- 개인정보 마스킹 필수 (전화번호 부분 처리)
- 상업적 이용 시 추가 검토 필요
- YouTube 이용약관 준수

---

## 📚 참고 자료

### YouTube Data API v3
- 공식 문서: https://developers.google.com/youtube/v3
- Python 클라이언트: `google-api-python-client`
- 할당량 계산기: https://developers.google.com/youtube/v3/determine_quota_cost

### youtube-transcript-api
- GitHub: https://github.com/jdepoix/youtube-transcript-api
- 설치: `pip install youtube-transcript-api`

### Whisper (OpenAI)
- GitHub: https://github.com/openai/whisper
- 모델: `base` (빠름) ~ `large` (정확)

---

## 🎯 예상 결과

### 수집 목표 (네이버 블로그 기준)
- 네이버 블로그: 15,000~25,000개 게시물
- **YouTube 예상**: 500~2,000개 영상
  - 블로그보다 영상 제작 진입장벽이 높음
  - 품질은 높을 가능성

### 데이터 품질
| 플랫폼 | 콘텐츠 양 | 멀티미디어 | 추천인 정보 |
|--------|-----------|-----------|------------|
| 카카오스토리 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 네이버 블로그 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **YouTube** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## ✅ 결론

### 최종 추천 방법
```
YouTube Data API v3 (메인)
+ youtube-transcript-api (자막)
+ Whisper (자막 없을 때)
+ 네이버 블로그 파이프라인 재사용
```

### 시작 순서
1. **지금 바로**: YouTube Data API 키 발급
2. **Phase 1 구현**: 기본 크롤러 (youtube_crawler_v1.py)
3. **Phase 2 구현**: 자막 수집
4. **Phase 3 재사용**: 멀티미디어 분석 파이프라인

### 예상 소요 시간
- **개발**: 3-4주
- **수집**: 1-2일 (API 할당량 내)
- **분석**: 1일 (Google Colab)
- **총**: 약 4주

---

**작성일**: 2025-11-11  
**버전**: 1.0  
**작성자**: PMIK 데이터 분석팀
