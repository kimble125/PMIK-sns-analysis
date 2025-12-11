# PM-International Korea 네이버 카페 크롤러 v1.0

## 📝 개요

네이버 카페에서 PMIK(PM-International Korea) 판매원 관련 게시물을 효율적으로 수집하는 크롤러입니다.

## 🎯 주요 특징

### ✨ 핵심 기능
- **iframe 기반 크롤링**: 네이버 카페의 iframe 구조 완벽 지원
- **키워드 검색 기반**: 효율적인 타겟 게시물 수집
- **PMIK 특화 데이터**: 추천인 정보, 파트너 ID 등 자동 추출
- **중복 제거**: 동일 게시물 중복 수집 방지
- **실시간 모니터링**: 진행률 및 통계 실시간 확인

### 🛡️ 안정성 기능
- **에러 복구**: 네트워크 오류 시 자동 재시도
- **체크포인트**: 중간 결과 자동 저장
- **테스트 모드**: 안전한 테스트 실행

## 📊 수집 데이터

### 기본 컬럼 (9개)
- `platform`: 플랫폼 (naver_cafe)
- `cafe_name`: 카페명
- `post_id`: 게시글 고유 ID
- `article_id`: 게시글 번호
- `url`: 게시글 URL
- `title`: 제목
- `content`: 본문 내용
- `author_nickname`: 작성자 닉네임
- `published_date`: 작성일시

### PMIK 특화 컬럼 (4개)
- `sponsor_phone`: 추천인 전화번호 (010-xxxx-xxxx)
- `sponsor_partner_id`: 파트너 ID (7-8자리)
- `pm_keywords_found`: 발견된 PM 키워드
- `sales_keywords_found`: 판매원 관련 키워드

### 참여도 컬럼 (4개)
- `view_count`: 조회수
- `comment_count`: 댓글 수
- `like_count`: 좋아요 수
- `reply_list`: 댓글 내용

### 콘텐츠 컬럼 (3개)
- `image_urls`: 이미지 URL 목록
- `hashtags`: 해시태그
- `collected_date`: 수집일시

## 🚀 사용 방법

### 1. 환경 설정
```bash
cd naver_cafe
pip install -r requirements.txt
```

### 2. 설정 파일 수정
`config.yaml` 파일에서 대상 카페와 키워드를 설정하세요.

```yaml
target_cafes:
  - name: "your_cafe_name"
    cafe_id: "your_cafe_id"
    cafe_url: "https://cafe.naver.com/your_cafe"
```

### 3. 실행
```bash
python pm_naver_cafe_crawler_v1_0.py
```

### 4. 테스트 모드 실행
안전한 테스트를 위해 설정 파일에서 `test_mode.enabled: true`로 설정하세요.

## ⚙️ 설정 옵션

### 크롤링 설정
- `page_load_timeout`: 페이지 로드 대기 시간
- `request_delay_min/max`: 요청 간 대기 시간 범위
- `max_pages_per_keyword`: 키워드당 최대 페이지 수
- `max_posts_per_page`: 페이지당 최대 게시물 수

### 키워드 설정
- `primary`: 주요 키워드 (PM, FitLine 등)
- `secondary`: 보조 키워드 (판매원, 추천인 등)

### 필터링 설정
- `pm_brand_keywords`: PM 브랜드 관련 키워드
- `pm_sales_keywords`: 판매원 관련 키워드  
- `exclude_keywords`: 제외할 키워드

## 📈 우선순위별 수집 전략

### 1순위: Selenium + iframe 방식 (가장 정확)
- 네이버 카페의 iframe 구조 완벽 지원
- 동적 콘텐츠 로딩 대응
- 가장 안정적이고 정확한 데이터 수집

### 2순위: 키워드 검색 기반 (효율적)
- 특정 키워드 관련 게시물만 타겟 수집
- 불필요한 데이터 수집 최소화
- 빠른 수집 속도

### 3순위: 게시판별 순차 크롤링
- 전체 데이터 수집 가능
- 시간 소요가 크지만 누락 없는 수집

## 🔧 네이버 카페 크롤링 핵심 기술

### iframe 처리
```python
# iframe으로 전환 (필수)
driver.switch_to.frame('cafe_main')

# 작업 수행
# ...

# 기본 프레임으로 복귀
driver.switch_to.default_content()
```

### 키워드 검색
```python
# 검색창에 키워드 입력
search_input = driver.find_element(By.NAME, 'query')
search_input.send_keys(keyword)
search_input.send_keys(Keys.ENTER)
```

### 게시글 링크 수집
```python
# 게시글 링크 추출
articles = driver.find_elements(By.CSS_SELECTOR, 'td.td_article a')
post_links = [article.get_attribute('href') for article in articles]
```

## ⚠️ 주의사항

1. **로그인 필요**: 일부 카페는 회원 가입 및 로그인이 필요합니다.
2. **등급 제한**: 등급 제한이 있는 게시물은 수집이 제한될 수 있습니다.
3. **속도 조절**: 과도한 요청으로 인한 차단 방지를 위해 적절한 지연 시간을 설정하세요.
4. **법적 준수**: 저작권 및 개인정보보호법을 준수하여 사용하세요.

## 📁 출력 파일

- `naver_cafe_pm_YYYYMMDD_HHMMSS.csv`: 수집된 데이터
- `checkpoints/`: 중간 저장 파일들
- `logs/`: 실행 로그 파일들

## 🛠️ 문제 해결

### 일반적인 문제
- **ChromeDriver 오류**: `webdriver-manager`가 자동으로 최신 버전을 다운로드합니다.
- **로그인 문제**: 수동으로 로그인 후 세션을 유지하세요.
- **iframe 오류**: `switch_to.frame('cafe_main')`을 확인하세요.

### 성능 최적화
- `headless` 모드 활성화로 리소스 절약
- 적절한 `request_delay` 설정으로 안정성 확보
- `test_mode`로 먼저 테스트 후 본격 실행

## 📞 지원

문제가 발생하면 다음 사항을 확인하세요:
1. 설정 파일 (`config.yaml`) 검토
2. 로그 파일 확인
3. 네트워크 연결 상태
4. Chrome 브라우저 버전

---

**작성자**: PMI Korea 데이터 분석팀  
**버전**: 1.0.0  
**최종 수정일**: 2024-11-18
