# PM 네이버 블로그 크롤러 v10.1 사용 가이드

## 🆕 v10.1 주요 개선사항

### 1. 키워드 연도 확장 (2023~2025) 🆕
- **모든 키워드에 연도 자동 추가**: "피엠인터내셔널" → "피엠인터내셔널 2023", "피엠인터내셔널 2024", "피엠인터내셔널 2025"
- **키워드 3배 확장**: 원본 키워드 × 3년 = 총 키워드 수
- **키워드당 50개 수집**: 연도별로 최신 데이터 확보
- **자동 처리**: config.yaml 수정 없이 자동 확장

### 2. 프로필 정보 수집
- `profile_nickname`: 블로그 닉네임
- `profile_intro`: 프로필 소개글
- `profile_member_id`: PM 회원번호 (pm8073590 형식)
- `profile_url`: 프로필에 포함된 URL

### 3. 이미지 OCR 처리
- **크롤러 내부에서 실시간 OCR 처리**
- EasyOCR 사용 (한국어 + 영어)
- 최대 3개 이미지 처리 (성능 최적화)
- OCR 결과에서 추천인 정보 추가 추출

### 4. 19가지 콘텐츠 타입 자동 분류
- 다중 분류 지원 (최대 3개)
- 우선순위 기반 정렬
- 상세 분류 기준은 `CONTENT_TYPE_CLASSIFICATION.md` 참조

### 5. 20개 추가 분석 컬럼
**콘텐츠 분석:**
- `content_length`: 본문 글자수
- `image_count`, `video_count`, `media_total_count`: 미디어 개수
- `hashtag_count`: 해시태그 개수
- `pm_brand_mention_count`: PM 브랜드 키워드 언급 횟수
- `product_mention_count`: 제품명 언급 횟수

**참여 지표:**
- `engagement_total`: 총 참여 수 (좋아요 + 댓글)
- `engagement_per_day`: 일평균 참여 수

**콘텐츠 분류:**
- `content_type`: 콘텐츠 유형 (다중, 쉼표로 구분)
- `content_type_primary`: 주요 콘텐츠 유형
- `content_type_count`: 분류된 유형 개수

**날짜 파생:**
- `posting_day_of_week`: 게시 요일 (월~일)
- `published_year`: 게시 연도
- `published_month`: 게시 월

**기타:**
- `has_sponsor_info`: 추천인 정보 포함 여부 (Yes/No)
- `image_ocr_text`: 이미지 OCR 결과

### 6. 향상된 추천인 정보 추출
**우선순위:**
1. 본문에서 추출
2. 프로필에서 추출
3. 이미지 OCR 결과에서 추출

### 7. VM 작업 로그 시스템
- `vm_crawler_log.json` 파일 생성
- 시작/종료 시간, 총 수집 개수 기록
- 실패 원인 및 통계 자동 기록
- 시스템 중단 시에도 로그 저장

---

## 📋 최종 컬럼 구성 (35개)

### 핵심 정보 (7개)
```
platform, post_id, blog_id, url, title, content, published_datetime
```

### 프로필 정보 (4개) 🆕
```
profile_nickname, profile_intro, profile_member_id, profile_url
```

### 추천인 정보 (3개)
```
sponsor_phone, sponsor_partner_id, has_sponsor_info
```

### 참여 지표 (4개)
```
like_count, comment_count, engagement_total, engagement_per_day
```

### 콘텐츠 분석 (7개) 🆕
```
content_length, image_count, video_count, media_total_count,
hashtag_count, pm_brand_mention_count, product_mention_count
```

### 미디어 (4개)
```
hashtags, image_urls, video_urls, image_ocr_text
```

### 콘텐츠 분류 (3개) 🆕
```
content_type, content_type_primary, content_type_count
```

### 날짜 파생 (3개) 🆕
```
posting_day_of_week, published_year, published_month
```

### 메타 (1개)
```
collected_date
```

---

## 🚀 실행 방법

### 1. 필수 라이브러리 설치

#### 기본 설치
```bash
pip install -r requirements.txt
```

#### OCR 사용 시 추가 설치 (권장)
```bash
pip install easyocr Pillow
```

### 2. 크롤러 실행

#### 🧪 20분 테스트 실행 (권장)
v10.1 기능을 먼저 테스트하세요!

```bash
# 1. config.yaml에서 테스트 모드 활성화 확인
# test_mode:
#   enabled: true
#   max_duration_minutes: 20

# 2. 실행
python pm_naver_blog_crawler_v10_1_test.py
```

**20분 테스트 특징**:
- ⏰ 정확히 20분 후 자동 종료 (진행 중인 수집 완료 후)
- 📊 상세 결과 보고서 자동 생성
- ✅ 수집 한 건당 소요 시간, 성공/실패율 분석
- 🆕 v10.1 신규 기능 성과 측정

#### 📘 전체 실행
```bash
# config.yaml에서 테스트 모드 비활성화
# test_mode:
#   enabled: false

python pm_naver_blog_crawler_v10_1_test.py
```

### 3. 출력 파일
- **메인 CSV**: `naver_blog_pm_v10_1_test_YYYYMMDD_HHMMSS.csv`
- **📊 결과 보고서**: `naver_blog_pm_v10_1_test_YYYYMMDD_HHMMSS_report.txt` 🆕
- **VM 로그**: `vm_crawler_log.json`
- **실패 URL**: `failed_urls.json`
- **체크포인트**: `checkpoints/checkpoint_*.csv` (1시간마다)

---

## 📊 결과 보고서 (v10.1 신규)

### 자동 생성되는 상세 보고서

크롤링 완료 시 `_report.txt` 파일이 자동 생성됩니다.

**보고서 내용**:

#### ⏱️ 실행 시간
- 총 실행 시간 (분, 초)
- 시작/종료 시간

#### 📈 수집 성과
- **총 수집 게시물 수**
- **수집 속도** (개/분)
- **게시물당 평균 소요 시간** ⭐

#### ✅ 성공률 분석
- **총 시도 횟수**
- **성공률** (수집 성공 비율)
- **필터링률** (제외 키워드로 필터링된 비율)
- **중복률** (이미 수집된 게시물)
- **에러율** (크롤링 실패)

#### 🆕 v10.1 신규 기능 성과
- **프로필 정보 수집률**: 닉네임, 소개글
- **추천인 정보 수집률**: 전화번호, 파트너 ID (7자리/8자리)
- **이미지 OCR 성공률**
- **콘텐츠 타입 분류율**: Top 5 유형 분포

#### 📊 콘텐츠 분석
- 평균 본문 글자수
- 평균 이미지/동영상/해시태그 개수
- 평균 PM 브랜드/제품명 언급 횟수
- 평균 참여 지표 (좋아요, 댓글)

#### 🔍 키워드별 수집 현황
- 상위 5개 키워드별 수집 개수 및 성공률

### 보고서 예시

```
================================================================================
📊 PM-International 네이버 블로그 크롤러 v10.1 테스트 결과 보고서
================================================================================

⏱️  실행 시간
────────────────────────────────────────────────────────────────────────────────
• 총 실행 시간: 20.0분 (1200초)
• 시작 시간: 2025-11-19 15:00:00
• 종료 시간: 2025-11-19 15:20:00

📈 수집 성과
────────────────────────────────────────────────────────────────────────────────
• 총 수집 게시물: 45개
• 수집 속도: 2.25개/분
• 게시물당 평균 소요 시간: 26.7초

✅ 성공률 분석
────────────────────────────────────────────────────────────────────────────────
• 총 시도: 78회
• ✅ 성공: 45회 (57.7%)
• 🔍 필터링: 20회 (25.6%)
• 🔄 중복: 8회 (10.3%)
• ❌ 에러: 5회 (6.4%)

🆕 v10.1 신규 기능 성과
────────────────────────────────────────────────────────────────────────────────
[프로필 정보 수집]
• 닉네임 수집률: 82.2%
• 소개글 수집률: 71.1%

[추천인 정보 추출 (통합)]
• 전화번호 수집률: 64.4%
• 파트너 ID 수집률: 53.3%
• 7자리 파트너 ID: 18개
• 8자리 파트너 ID: 6개

[이미지 OCR 처리]
• OCR 처리 성공률: 68.9%

[콘텐츠 타입 자동 분류]
• 분류 성공률: 97.8%

• Top 5 콘텐츠 유형:
  1. Product_Education: 15개 (33.3%)
  2. User_Review_Experience: 12개 (26.7%)
  3. Product_Recommendation: 8개 (17.8%)
  4. Lifestyle_Daily: 6개 (13.3%)
  5. Before_After: 4개 (8.9%)
```

---

## 🎬 비디오 처리 (별도 실행)

### 1. 준비사항
```bash
# FFmpeg 설치 (필수)
# Ubuntu/VM:
sudo apt-get update
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Python 라이브러리
pip install openai-whisper youtube-transcript-api yt-dlp
```

### 2. 실행 방법
```bash
# 기본 실행 (base 모델)
python pm_video_processor_v1.py naver_blog_pm_v10_1_test_20251119_150000.csv

# 작은 모델 사용 (빠름, 정확도 낮음)
python pm_video_processor_v1.py your_file.csv --model tiny

# 큰 모델 사용 (느림, 정확도 높음)
python pm_video_processor_v1.py your_file.csv --model medium

# 출력 경로 지정
python pm_video_processor_v1.py your_file.csv -o output_with_video.csv
```

### 3. 추가되는 컬럼
- `youtube_transcript`: YouTube 자막 텍스트
- `youtube_transcript_lang`: 자막 언어 (ko/en/auto)
- `whisper_transcript`: Whisper 음성인식 결과
- `whisper_confidence`: Whisper 신뢰도
- `video_processing_status`: 처리 상태

### 4. 처리 순서
1. YouTube 자막 우선 시도 (빠름)
2. 자막 없으면 Whisper AI 사용 (느림, GPU 권장)
3. 10개마다 중간 저장

---

## ⚙️ 설정 파일 (config.yaml)

### v10.1에서 추가된 설정

```yaml
filters:
  # PM 브랜드 키워드 (확장)
  pm_brand_keywords:
    - "피엠"
    - "피엠인터내셔널"
    - "PMIK"
    - "독일PM"
    - "독일피엠"
    # ...
  
  # 제품명 키워드 (띄어쓰기 무시 매칭)
  product_keywords:
    - "FitLine"
    - "파워칵테일"
    - "액티바이즈"
    - "리스토레이트"
    # ... (총 50개 이상)
  
  # 제외 블로그 ID
  excluded_blog_ids:
    - "kimnkimmarketing"  # v10.1 추가
    # ...
```

---

## 📊 Content Type 분류 기준

### 19가지 콘텐츠 유형

#### 교육/정보 제공형
- `Product_Education`: 제품 정보/교육
- `Scientific_Health_Info`: 과학적 근거/건강 정보
- `QA_Format`: Q&A 형식

#### 후기/증언형
- `User_Review_Experience`: 사용 후기/체험담
- `Before_After`: 비포앤애프터
- `Text_Testimonial`: 증언/추천글

#### 추천/판매 촉진형
- `Product_Recommendation`: 제품 추천
- `Price_Promotion`: 가격/할인/프로모션
- `Comparison`: 비교 콘텐츠

#### 라이프스타일/영감형
- `Lifestyle_Daily`: 라이프스타일/일상
- `Storytelling`: 스토리텔링

#### 사업/기회 강조형
- `Business_Opportunity`: 사업 기회/수익 강조
- `Team_Group_Activity`: 팀 활동/그룹 사진

#### 미디어/시각 콘텐츠형
- `Video_Content`: 동영상 콘텐츠
- `Image_Carousel`: 이미지 갤러리/캐러셀

#### 참여/이벤트형
- `Event_Challenge`: 이벤트/챌린지
- `Celebrity_Influencer`: 연예인/인플루언서 활용

#### 주의: 규제 대상
- `Undisclosed_Ad`: 뒷광고/기만광고

**상세 분류 기준**: `CONTENT_TYPE_CLASSIFICATION.md` 참조

---

## 🔧 트러블슈팅

### OCR 관련 문제

**문제**: `EasyOCR 미설치` 경고
```bash
# 해결:
pip install easyocr
```

**문제**: OCR 처리가 너무 느림
```python
# pm_naver_blog_crawler_v10_1_test.py의 OCRProcessor 수정:
# max_images=3 → max_images=1  (1개만 처리)
```

### Whisper 관련 문제

**문제**: FFmpeg 미설치
```bash
# Ubuntu/VM:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg
```

**문제**: Whisper가 너무 느림
```bash
# 작은 모델 사용:
python pm_video_processor_v1.py your_file.csv --model tiny
```

**문제**: GPU 메모리 부족
```python
# pm_video_processor_v1.py 수정:
# whisper.load_model("base") 대신
whisper.load_model("tiny")  # 가장 작은 모델
```

### 프로필 추출 실패

**원인**: 네이버 블로그 구조 변경
**해결**: `extract_profile_info()` 함수의 selector 업데이트 필요

---

## 💡 성능 최적화 팁

### 1. OCR 처리 최적화
- 이미지 개수가 많은 게시물은 처리 시간이 길어짐
- `max_images=3` 설정으로 제한 (필요시 조정)
- GPU가 없는 VM에서는 OCR 비활성화 고려

### 2. 비디오 처리 최적화
- YouTube 자막이 있으면 Whisper 스킵 (빠름)
- `--model tiny` 사용 시 처리 속도 10배 향상
- GPU가 있으면 Whisper 속도 5-10배 향상

### 3. VM 실행 최적화
- Screen 또는 tmux 사용하여 백그라운드 실행
- 체크포인트 기능으로 중단 시에도 안전
- 크롤러와 비디오 처리를 분리하여 안정성 확보

---

## 📝 체크리스트

### 실행 전
- [ ] config.yaml 확인 (키워드, 목표 개수)
- [ ] Naver API 키 설정 (config.py 또는 환경변수)
- [ ] OCR 라이브러리 설치 (easyocr, Pillow)
- [ ] 디스크 공간 확인 (10GB 이상 권장)
- [ ] 전원 연결 및 절전 모드 해제

### 크롤러 실행 중
- [ ] 주기적으로 로그 확인
- [ ] 체크포인트 파일 생성 확인 (1시간마다)
- [ ] VM 상태 모니터링 (메모리, CPU)

### 실행 후
- [ ] CSV 파일 확인 (컬럼 개수 35개)
- [ ] vm_crawler_log.json 확인
- [ ] 비디오 처리 스크립트 실행 (선택)
- [ ] 데이터 백업

---

## 📚 참고 문서

- `CONTENT_TYPE_CLASSIFICATION.md`: 콘텐츠 분류 상세 기준
- `config.yaml`: 전체 설정 파일
- `failed_urls.json`: 실패한 URL 목록
- `vm_crawler_log.json`: VM 실행 로그

---

**작성자**: PMI Korea 데이터 분석팀  
**버전**: 10.1.0  
**최종 수정일**: 2025-11-19
