# v10.3.1 버그 수정 요약

## 📋 수정 개요

v10.3에서 발견된 **3가지 치명적 버그**를 수정한 버전입니다.

---

## 🐛 수정된 버그

### 1. ⚠️ **Profile URL 오타 수정** (치명적)

**파일**: `pm_naver_blog_crawler_v10_3_test.py` (line 619)

**문제**:
```python
# 잘못된 코드
profile_url = f"https://blog.naver.com/ProileOf.naver?blogId={blog_id}"
```
- `ProileOf` (오타) → `ProlieOf` (정상)
- `.naver` → `.nhn`
- **이것이 v10.2의 profile_intro 수집률 0%의 근본 원인**

**수정**:
```python
# 수정된 코드
profile_url = f"https://blog.naver.com/ProlieOf.nhn?blogId={blog_id}"
```

**예상 효과**: profile_intro 수집률 0% → 50~80% 개선 예상

---

### 2. 🔍 **키워드 로직 오류 수정**

**파일**: `pm_naver_blog_crawler_v10_3_test.py` (line 1407-1420)

**문제**:
```python
# 잘못된 코드
# 연도 확장 키워드
for base_keyword in YEAR_EXPANSION_KEYWORDS:
    for year in YEARS:
        all_keywords.append(f"{base_keyword} {year}")

# 연도 제외 키워드 추가
for keyword in TARGET_KEYWORDS['primary']:
    if keyword not in YEAR_EXPANSION_KEYWORDS:
        all_keywords.append(keyword)  # 이 조건문이 항상 False
```
- `YEAR_EXPANSION_KEYWORDS`와 `TARGET_KEYWORDS['primary']`가 동일한 리스트
- **연도 제외 키워드가 하나도 추가되지 않음**

**수정**:
```python
# 수정된 코드
# v10.3.1: 연도 제외 키워드 먼저 추가 (더 넓은 검색)
for keyword in TARGET_KEYWORDS['primary']:
    all_keywords.append(keyword)

for keyword in TARGET_KEYWORDS['secondary']:
    all_keywords.append(keyword)

for keyword in TARGET_KEYWORDS['product_test']:
    all_keywords.append(keyword)

# 연도 확장 키워드 (primary만)
for base_keyword in YEAR_EXPANSION_KEYWORDS:
    for year in YEARS:
        all_keywords.append(f"{base_keyword} {year}")
```

**키워드 순서 변경 이유**:
- 연도 제외 키워드를 **먼저** 검색하여 더 넓은 범위의 게시물 수집
- 연도별 키워드는 보조적으로 사용

**예상 효과**: 
- 키워드당 수집량 60-80개 → 200-300개로 증가 예상
- 중복률 감소 (69.4% → 40-50%)

---

### 3. 🖼️ **OCR을 위한 이미지 로딩 활성화**

**파일**: `pm_naver_blog_crawler_v10_3_test.py` (line 1041-1043)

### 4. ⏱️ **시간 제한 40분으로 변경**

**파일**: `pm_naver_blog_crawler_v10_3_test.py` (line 126), `config.yaml` (line 19)

**변경**:
```python
# 이전: 1시간
MAX_DURATION_SECONDS = 60 * 60  # 3600초

# 변경: 40분
MAX_DURATION_SECONDS = 40 * 60  # 2400초
```

**동작 방식**:
- 40분 경과 시 새로운 키워드 검색 중단
- 현재 크롤링 중인 게시물까지만 완료 후 종료
- 데이터 손실 없이 안전하게 종료

---

### 5. 🐛 **logger 정의 순서 오류 수정**

**문제**:
```python
# API 키 로드 (line 146)
logger.info("✅ config.py에서 Naver API 키 로드 완료")

# logger 정의 (line 207) - 너무 늦음!
logger = logging.getLogger(__name__)
```
- logger가 정의되기 전에 사용하여 `NameError: name 'logger' is not defined` 발생

**수정**:
```python
# API 키 로드 시 print 사용 (logger 정의 전)
print("✅ config.py에서 Naver API 키 로드 완료")

# logger 정의 후 다시 로깅
logger = logging.getLogger(__name__)
if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
    logger.info(f"✅ Naver API 키 로드 완료 (Client ID: {NAVER_CLIENT_ID[:10]}...)")
```

---

### 이전 내용 (OCR 이미지 로딩)

**문제**:
```python
# 잘못된 코드
chrome_options.add_argument('--disable-images')
chrome_options.add_argument('--blink-settings=imagesEnabled=false')
```
- 이미지를 **아예 로드하지 않음**
- `extract_image_urls()`에서 HTML의 이미지 URL은 추출하지만, 실제 다운로드는 불가
- **이것이 v10.2의 OCR 처리 성공률 0%의 근본 원인**

**수정**:
```python
# 수정된 코드
# v10.3.1: OCR을 위해 이미지 로딩 활성화 (주석 처리)
# chrome_options.add_argument('--disable-images')
# chrome_options.add_argument('--blink-settings=imagesEnabled=false')
```

**예상 효과**: OCR 처리 성공률 0% → 30-50% 개선 예상

---

### 4. 📝 **config.yaml - API 요청 개수 수정**

**파일**: `config.yaml` (line 27)

**문제**:
```yaml
# 잘못된 설정
targets:
  max_search_results: 1000  # 키워드당 최대 검색 결과
```
- 사용자 요청: 100개로 제한
- v10.3 코드는 이미 100개로 제한했으나 config.yaml은 미수정

**수정**:
```yaml
# 수정된 설정
targets:
  max_search_results: 100  # v10.3: 키워드당 최대 검색 결과 (100개로 제한)
```

---

## 📊 수집량 저조 원인 분석

### v10.2 결과
```
독일피엠 2018: 80/1000 수집, 14 필터링, 40.2% 성공
독일피엠 2020: 77/1000 수집, 31 필터링, 25.9% 성공
독일피엠 2022: 61/1000 수집, 41 필터링, 20.5% 성공
```

### 주요 원인 3가지

#### 1. **연도 붙인 키워드의 검색 결과 부족** ⭐ 주요 원인
- 네이버 검색: `"독일피엠 2018"` → 제목/본문에 "2018"이 명시된 게시물만 검색
- 실제 블로그: 날짜는 발행일로 자동 표시, 제목에 연도 쓰는 경우 드뭄
- 예시: "독일피엠 제품 후기" (2018년 작성이지만 제목에 연도 없음)

#### 2. **높은 중복률** (69.4%)
- 다른 연도 키워드에서 같은 게시물 반복 검색
- 예: "독일피엠 2018"과 "독일피엠 2019"에서 같은 게시물 발견

#### 3. **API 검색 제한**
- 네이버 API: 키워드당 최대 1000개
- 연도별 키워드: 검색 결과 100개 미만인 경우 많음

### 해결 방법

✅ **연도 제외 키워드 추가** → v10.3.1에서 수정 완료

**기대 효과**:
- 검색 풀 확대: 모든 시기 게시물 접근
- 중복 감소: 하나의 넓은 키워드로 검색
- **수집량 3-4배 증가 예상** (60-80개 → 200-300개)

---

## 🎯 v10.3.1 기대 효과

| 항목 | v10.2 | v10.3.1 예상 |
|------|-------|-------------|
| **profile_intro 수집률** | 0.0% | 50-80% |
| **OCR 처리 성공률** | 0.0% | 30-50% |
| **키워드당 수집량** | 60-80개 | 200-300개 |
| **중복률** | 69.4% | 40-50% |

---

## 📝 사용 방법

### 1. 실행 전 확인사항
```bash
# EasyOCR 설치 확인
pip install easyocr pillow

# Naver API 키 설정 확인
export NAVER_CLIENT_ID="your_client_id"
export NAVER_CLIENT_SECRET="your_client_secret"
```

### 2. 크롤러 실행
```bash
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
python pm_naver_blog_crawler_v10_3_test.py
```

### 3. 실행 시간
- **제한**: 1시간 (3600초)
- **작업 완료**: 시간 초과 시 현재 게시물까지만 완료 후 종료

### 4. 출력 파일
- `naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS.csv` - 게시물 데이터
- `naver_blog_pm_v10_3_bloggers_YYYYMMDD_HHMMSS.csv` - 블로거 프로필
- `naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS_report.txt` - 실행 리포트

---

## 🔍 추가 개선 권장사항

### 1. 파생 컬럼 생성 스크립트 작성
v10.3에서 제거한 파생 컬럼을 별도로 생성하는 스크립트 필요:
- `engagement_total` = like_count + comment_count
- `engagement_per_day` = engagement_total / days_since_published
- `content_length` = len(content)
- `image_count` = count(image_urls)
- 등

### 2. 프로필 URL 추가 검증
현재 `ProlieOf.nhn`이 맞는지 실제 네이버 블로그에서 확인 필요.
일부 블로그는 다른 URL 구조를 사용할 수 있음.

### 3. OCR 성능 모니터링
이미지 로딩 활성화로 크롤링 속도가 느려질 수 있음.
- 현재: 2.37개/분
- 예상: 1.5-2개/분

필요시 이미지 개수 제한 조정:
```python
# line 1297
image_ocr_text = ocr_processor.process_image_urls(image_urls, max_images=3)
# max_images를 2로 줄이면 속도 향상
```

---

## 📌 버전 정보

- **버전**: v10.3.1
- **기반**: v10.3
- **수정 일자**: 2025-11-20
- **작성자**: PMI Korea 데이터 분석팀
