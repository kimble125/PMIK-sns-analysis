# YouTube PMIK 판매원 데이터 수집 프로젝트

## 📌 프로젝트 개요

PM-International Korea의 YouTube 판매원 게시물 및 영상 데이터를 수집하는 프로젝트입니다.

## 🎯 목표

- YouTube에서 PMIK 판매원의 홍보 영상 500~2,000개 수집
- 영상 메타데이터, 자막, 썸네일 OCR 등 종합 데이터 확보
- 네이버 블로그 파이프라인과 통합 가능한 형태로 구조화

## 📁 파일 구조

```
youtube/
├── README.md                           # 본 파일
├── YOUTUBE_DATA_COLLECTION_GUIDE.md    # 상세 가이드 (필독!)
├── youtube_columns_schema.csv          # 컬럼 구조 정의
├── youtube_crawler_v1_sample.py        # 샘플 크롤러 코드
├── requirements.txt                    # 필요 패키지
└── config.py.example                   # API 키 설정 예시
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 패키지 설치
pip install -r requirements.txt

# API 키 설정
cp config.py.example config.py
# config.py 파일을 열어 YOUTUBE_API_KEY 입력
```

### 2. YouTube API 키 발급

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성
3. YouTube Data API v3 활성화
4. API 키 생성
5. `config.py`에 키 입력

### 3. 데이터 수집 실행

```bash
python youtube_crawler_v1_sample.py
```

## 📊 수집 데이터 구조

### Phase 1: 기본 메타데이터 (22개 컬럼)
- 영상 정보: video_id, title, description, duration 등
- 채널 정보: channel_name, subscriber_count 등
- 통계: view_count, like_count, comment_count
- 추천인: sponsor_phone, sponsor_partner_id

### Phase 2: 자막 데이터
- youtube_transcript (공식 자막)
- whisper_transcript (음성 인식)

### Phase 3: 멀티미디어 분석
- thumbnail_ocr_text (썸네일 OCR)
- 기타 분석 데이터

자세한 내용은 `youtube_columns_schema.csv` 참고

## 🔄 데이터 파이프라인

```
1. YouTube Data API
   ↓ (youtube_crawler_v1.py)
   youtube_pm_v1_YYYYMMDD.csv (22 columns)
   ↓
2. 자막 수집
   ↓ (youtube_transcript_collector.py)
   youtube_pm_v1_with_transcript.csv
   ↓
3. Google Colab 분석
   ↓ (썸네일 OCR, Whisper)
   youtube_pm_v1_with_ocr.csv (30+ columns)
```

## 📖 주요 문서

### 필독 문서
- **YOUTUBE_DATA_COLLECTION_GUIDE.md**: 전체 가이드 (40쪽 분량)
  - 데이터 수집 방법 4가지 비교
  - 추천 방법 및 근거
  - 컬럼 구조 상세 설명
  - 네이버 블로그/카카오스토리와 비교
  - 구현 로드맵
  - 코드 재사용 가능 부분

### 참고 파일
- **youtube_columns_schema.csv**: 컬럼별 상세 명세
- **youtube_crawler_v1_sample.py**: 실행 가능한 샘플 코드

## 🎓 기존 프로젝트 참고

본 YouTube 수집 프로젝트는 다음 기존 프로젝트를 참고하여 설계되었습니다:

### 1. 네이버 블로그 (pm_naver_blog_crawler_v8_4_final.py)
- **참고 부분**: API + 크롤링 하이브리드 방식
- **재사용**: 필터링 로직, 추천인 정보 추출
- **적용**: YouTube API + transcript-api

### 2. 카카오스토리 (kakaostory_posts.json)
- **참고 부분**: JSON 데이터 구조
- **재사용**: 해시태그, 멀티미디어 URL 구조
- **적용**: YouTube 메타데이터 저장 형식

### 3. 멀티미디어 분석 (multimedia-process/)
- **참고 부분**: OCR, 음성 인식 파이프라인
- **재사용**: Google Colab 노트북, 병합 스크립트
- **적용**: 썸네일 OCR, Whisper 음성 인식

## ⚙️ API 할당량 관리

YouTube Data API v3는 일일 10,000 units 제한이 있습니다.

### 할당량 계산
- 검색 1회: 100 units
- 영상 조회 1회: 1 unit
- 댓글 조회 1회: 1 unit

### 일일 수집 가능량
- 50개 키워드 검색: 5,000 units
- 2,500개 영상 상세: 2,500 units
- 500개 영상 댓글: 500 units
- **총계**: 8,000 units (여유 2,000)

### 최적화 팁
- 자막은 youtube-transcript-api 사용 (할당량 0)
- 채널 정보는 캐싱
- 중복 검사로 불필요한 조회 방지

## 🔧 환경 설정 예시

### config.py
```python
# YouTube Data API v3
YOUTUBE_API_KEY = "your_api_key_here"

# 선택 사항
GOOGLE_VISION_API_KEY = "your_vision_api_key"  # 썸네일 OCR용
```

### .env (또는 환경변수)
```bash
YOUTUBE_API_KEY=your_api_key_here
```

## 📈 예상 결과

### 수집량
- 목표: 500~2,000개 영상
- 기간: 1-2일 (API 할당량 내)

### 데이터 품질
- 영상 콘텐츠의 특성상 블로그보다 정보 밀도 높음
- 추천인 정보 포함률 예상: 60-80%
- 멀티미디어 데이터 풍부 (자막, 음성, 썸네일)

## ⚠️ 주의사항

### 법적 준수
- YouTube 이용약관 준수
- API 할당량 초과 금지
- 개인정보 처리 주의 (전화번호 마스킹 등)

### 기술적 제한
- 자막 없는 영상은 Whisper 필요 (비용 발생 가능)
- 썸네일 OCR은 Google Vision API 권장 (무료 할당량 있음)
- API 키 노출 주의 (.gitignore에 config.py 추가)

## 🤝 도움말

### 문제 해결
1. API 할당량 초과: 다음날 재시도 또는 유료 플랜
2. API 키 오류: Google Cloud Console에서 API 활성화 확인
3. 자막 없음: Whisper 사용 또는 해당 영상 스킵

### 추가 기능 구현 시
- `YOUTUBE_DATA_COLLECTION_GUIDE.md`의 Phase 2-4 참고
- 네이버 블로그 코드의 CrawlStats, KeywordStats 클래스 재사용 권장
- 멀티미디어 분석은 Google Colab 기존 노트북 활용

## 📚 참고 자료

- [YouTube Data API v3 공식 문서](https://developers.google.com/youtube/v3)
- [youtube-transcript-api GitHub](https://github.com/jdepoix/youtube-transcript-api)
- [Google Cloud Console](https://console.cloud.google.com/)

## 📝 버전 히스토리

- **v1.0** (2025-11-11): 초기 설계 및 샘플 코드 작성

---

**프로젝트**: PMIK SNS 분석  
**작성자**: PMIK 데이터 분석팀  
**최종 업데이트**: 2025-11-11
