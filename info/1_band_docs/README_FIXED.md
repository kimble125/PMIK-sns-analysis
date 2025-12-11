# Band 크롤러 v1.0 수정본 - 실행 가이드

## 📋 문제점 및 해결방법

### 🔴 원본 문제
```
발견된 밴드/페이지: 0개
```

실제 Band 검색 페이지에서 밴드가 1431개 검색되지만, 크롤러가 HTML을 파싱하지 못했습니다.

### ✅ 해결 방법
**CSS 셀렉터를 실제 HTML 구조에 맞게 수정**

#### 변경 전 (❌ 작동 안 함)
```python
band_items = soup.select('div.searchResultItem, li.searchBandItem, div.bandItem')
```

#### 변경 후 (✅ 작동함)
```python
# Band intro 페이지로 이동하는 모든 링크 선택
band_links = soup.select('a[href*="/band/"][href*="/intro"]')

# 페이지 링크 선택
page_links = soup.select('a[href*="/page/"]')
```

## 🚀 실행 방법

### 1단계: 파일 교체
```bash
# 수정된 파일들로 교체
cp band_crawler_v1_0_test_fixed.py band_crawler_v1_0_test.py
cp config_band_fixed.yaml config_band.yaml
```

### 2단계: 디버깅 모드로 실행 (브라우저 창 보기)
```bash
# headless: false로 설정되어 브라우저 창이 열립니다
python band_crawler_v1_0_test.py --config config_band.yaml
```

### 3단계: 실행 결과 확인
- **브라우저 창**: 실제 Band 검색 페이지가 표시됩니다
- **터미널**: 로그 메시지로 진행상황 확인
- **로그 파일**: `logs/band_crawler_YYYYMMDD_HHMMSS.log`

### 4단계: 데이터 확인
```bash
# 수집된 데이터 확인
ls -lh data_band/

# CSV 파일 미리보기
head -n 5 data_band/band_info_v1_0_*.csv
head -n 5 data_band/band_posts_v1_0_*.csv
```

## 🔧 설정 옵션

### config_band.yaml 주요 설정

```yaml
crawling:
  headless: false    # ⭐ false: 브라우저 창 표시 (디버깅용)
                     #    true: 백그라운드 실행 (운영용)

execution_mode:
  test_mode: true    # 테스트 모드
  max_duration_minutes: 10  # 10분간 실행
```

### 명령줄 옵션

```bash
# 기본 실행
python band_crawler_v1_0_test.py

# 설정 파일 지정
python band_crawler_v1_0_test.py --config config_band.yaml

# 실행 시간 지정 (분)
python band_crawler_v1_0_test.py --duration 15

# 밴드당 최대 게시물 수 지정
python band_crawler_v1_0_test.py --max-posts 100

# 브라우저 창 표시 (headless 무시)
python band_crawler_v1_0_test.py --no-headless
```

## 📊 예상 결과

### 정상 작동시
```
🔍 밴드 검색: 피엠인터내셔널
  → 밴드 링크 15개 발견
🔍 페이지 검색: 피엠인터내셔널
  → 페이지 링크 3개 발견

📊 크롤링 통계
===========================================
🏠 발견된 밴드: 15
📄 발견된 페이지: 3
 ✅ 접근 가능: 12
 🔒 비공개: 3
📝 수집된 게시물: 234
```

## 🐛 문제 해결

### 여전히 0개 발견되는 경우

#### 방법 1: 브라우저 창으로 확인
```bash
# headless: false로 실행하여 브라우저 창 확인
python band_crawler_v1_0_test.py --no-headless
```

실제 페이지를 보면서:
1. 검색 결과가 로드되는지 확인
2. 개발자 도구(F12)로 HTML 구조 확인
3. 필요시 CSS 셀렉터 재수정

#### 방법 2: 스크롤 대기 시간 증가
```yaml
crawling:
  scroll_wait_seconds: 5  # 3 → 5초로 증가
```

#### 방법 3: 페이지 로드 타임아웃 증가
```yaml
crawling:
  page_load_timeout: 30  # 20 → 30초로 증가
```

## 📁 출력 파일

### 1. 밴드/페이지 정보
```
data_band/band_info_v1_0_test_YYMMDD_HHMMSS.csv
```

컬럼:
- entity_type: 'band' 또는 'page'
- entity_id: 밴드/페이지 ID
- entity_name: 이름
- description: 소개글
- member_count: 멤버수
- tags: 태그
- is_pm_keyword: PM 키워드 포함 여부

### 2. 게시물 정보
```
data_band/band_posts_v1_0_test_YYMMDD_HHMMSS.csv
```

컬럼:
- post_id: 게시물 ID
- content: 내용
- author_nickname: 작성자
- published_datetime: 작성일시
- like_count: 좋아요 수
- comment_count: 댓글 수

## 🎯 다음 단계

### 테스트 성공 후
1. `headless: true`로 변경 (백그라운드 실행)
2. `max_duration_minutes` 증가 (더 많은 데이터 수집)
3. 키워드 추가 (config_band.yaml의 keywords 섹션)

### 운영 모드 실행
```bash
# config에서 headless: true로 변경 후
python band_crawler_v1_0_test.py --duration 60
```

## 📞 문의

크롤러 작동에 문제가 있거나 추가 개선이 필요한 경우:
- 로그 파일 확인: `logs/band_crawler_*.log`
- 에러 메시지와 함께 문의

---
**버전**: 1.0.1 (Fixed - 2025-12-02)
**수정 내용**: CSS 셀렉터 개선, 실제 HTML 구조 반영
