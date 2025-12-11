# PM-International Korea 네이버 블로그 크롤러 v10.3 - 사용 설명서

## 📋 개요

PM-International Korea 팀파트너의 네이버 블로그 게시물을 자동으로 수집하는 크롤러 v10.3입니다.

### 주요 개선사항 (v10.2 → v10.3)

1. **🖼️ OCR 처리 개선**
   - 이미지 다운로드 타임아웃 증가 (10초 → 15초)
   - GPU 사용 시도 후 CPU로 자동 폴백
   - 이미지 전처리 추가 (대비 향상)
   - 상세 로깅 및 에러 처리 강화

2. **📝 프로필 소개글 수집 강화**
   - 프로필 페이지 로딩 대기 시간 증가
   - 더 많은 CSS 선택자 추가
   - JavaScript 실행 대기 및 스크롤 재시도

3. **🔧 파생 컬럼 분리**
   - 크롤러는 원시 데이터만 수집
   - 파생 컬럼은 별도 스크립트(`create_derived_columns.py`)로 처리
   - 수집 속도 향상

4. **⏱️ 실행 시간 제한**
   - 1시간 실행 후 자동 종료
   - 작업 중이던 게시물까지만 완료

5. **🔍 키워드 설정 개선**
   - API 요청 개수: 키워드당 100개로 제한
   - 연도 제외 키워드 추가

---

## 📦 필요한 패키지 설치

```bash
# 기본 패키지
pip install requests beautifulsoup4 selenium pandas numpy pyyaml webdriver-manager

# OCR 관련 (선택사항, 하지만 강력 권장)
pip install easyocr pillow

# 설치 완료 확인
python -c "import easyocr; print('✅ EasyOCR 설치 완료')"
```

---

## 🔑 Naver API 키 설정

환경 변수로 Naver Open API 키를 설정해야 합니다:

```bash
# Linux/Mac
export NAVER_CLIENT_ID="your_client_id"
export NAVER_CLIENT_SECRET="your_client_secret"

# Windows (PowerShell)
$env:NAVER_CLIENT_ID="your_client_id"
$env:NAVER_CLIENT_SECRET="your_client_secret"

# Windows (CMD)
set NAVER_CLIENT_ID=your_client_id
set NAVER_CLIENT_SECRET=your_client_secret
```

### Naver API 키 발급 방법

1. [Naver Developers](https://developers.naver.com/) 접속
2. 애플리케이션 등록
3. 검색 > 블로그 API 사용 설정
4. Client ID와 Client Secret 확인

---

## 🚀 사용 방법

### 1단계: 크롤러 실행

```bash
python pm_naver_blog_crawler_v10_3_test.py
```

**실행 시 생성되는 파일들:**
- `naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS.csv` - 수집된 게시물 데이터 (원시)
- `naver_blog_pm_v10_3_bloggers_YYYYMMDD_HHMMSS.csv` - 블로거 프로필 정보
- `naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS_report.txt` - 실행 리포트
- `checkpoint_posts_YYYYMMDD_HHMMSS.csv` - 체크포인트 (100개마다 자동 저장)
- `failed_urls.json` - 실패한 URL 목록
- `vm_logs/session_YYYYMMDD_HHMMSS.log` - 세션 로그

**실행 시간:**
- 자동으로 1시간 후 종료됩니다
- 작업 중이던 게시물까지는 완료합니다
- Ctrl+C로 중단할 수 있습니다

### 2단계: 파생 컬럼 추가

크롤링이 완료된 후, 파생 컬럼을 추가합니다:

```bash
python create_derived_columns.py naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS.csv
```

이 명령은 다음 파일을 생성합니다:
- `naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS_with_derived.csv`

**추가되는 파생 컬럼:**
1. `image_count` - 이미지 개수
2. `video_count` - 비디오 개수
3. `word_count` - 단어 수
4. `char_count` - 글자 수
5. `has_sponsor_info` - 추천인 정보 유무 (0/1)
6. `engagement_rate` - 참여율 (%)
7. `hashtag_count` - 해시태그 개수
8. `days_since_publish` - 발행 후 경과 일수
9. `is_recent` - 최근 게시물 여부 (30일 이내: 1, 아니면: 0)
10. `content_length_category` - 콘텐츠 길이 카테고리 (짧음/보통/길음/매우 길음)

**커스텀 출력 파일명 지정:**
```bash
python create_derived_columns.py input.csv output_custom_name.csv
```

---

## ⚙️ 설정 파일 (config.yaml)

`config.yaml` 파일에서 다양한 설정을 변경할 수 있습니다:

```yaml
# 타겟 키워드 설정
targets:
  max_search_results: 100  # 키워드당 최대 검색 결과 수
  primary_keywords:
    - '피엠인터내셔널'
    - '독일피엠'
    # ... 추가 키워드

# 크롤링 설정
crawling:
  page_load_timeout: 10  # 페이지 로딩 타임아웃 (초)
  request_delay_min: 1.5  # 최소 요청 딜레이 (초)
  request_delay_max: 2.5  # 최대 요청 딜레이 (초)
  
  # OCR 설정
  ocr_enabled: true
  ocr_max_images: 3  # 게시물당 최대 OCR 처리 이미지 수
  ocr_timeout: 15  # 이미지 다운로드 타임아웃 (초)

# 필터링 설정
filters:
  pm_brand_keywords:  # 최소 1개 이상 포함 필요
    - '피엠인터내셔널'
    - 'PM인터내셔널'
    # ...
  
  exclude_keywords:  # 4개 이상 포함 시 필터링
    - '뉴스'
    - '기사'
    # ...
```

---

## 📊 수집되는 데이터 필드

### 기본 정보
- `platform` - 플랫폼명 (naver_blog)
- `post_id` - 게시물 ID
- `blog_id` - 블로그 ID
- `url` - 게시물 URL
- `title` - 제목
- `content` - 본문 전체 텍스트
- `published_datetime` - 발행 날짜/시간
- `collected_date` - 수집 날짜/시간

### 프로필 정보
- `profile_nickname` - 블로거 닉네임
- `profile_intro` - 블로거 소개글
- `blogger_member_id` - 블로거 회원번호 (pm1234567 형식)
- `profile_url` - 프로필 URL

### 추천인 정보
- `sponsor_phone` - 추천인 전화번호 (010-XXXX-XXXX 형식)
- `content_sponsor_id` - 추천인 파트너 ID (7-8자리 숫자)

### 참여 지표
- `like_count` - 좋아요 수
- `comment_count` - 댓글 수

### 콘텐츠 메타데이터
- `hashtags` - 해시태그 목록 (쉼표 구분)
- `image_urls` - 이미지 URL 목록 (쉼표 구분)
- `video_urls` - 비디오 URL 목록 (쉼표 구분)
- `image_ocr_text` - 이미지 OCR 결과 텍스트

### 콘텐츠 타입 분류
- `content_type` - 콘텐츠 타입 (쉼표 구분, 최대 3개)
- `content_type_primary` - 주요 콘텐츠 타입
- `content_type_count` - 분류된 타입 개수

**콘텐츠 타입 종류 (19가지):**
1. `Undisclosed_Ad` - 미공개 광고
2. `Official_Announcement` - 공식 공지
3. `News_Media` - 뉴스/언론
4. `Video_Content` - 비디오 콘텐츠
5. `Image_Carousel` - 이미지 캐러셀 (5개 이상)
6. `QA_Format` - Q&A 형식
7. `User_Review_Experience` - 사용자 후기/체험
8. `Before_After` - 비포/애프터
9. `Text_Testimonial` - 텍스트 추천
10. `Product_Recommendation` - 제품 추천
11. `Price_Promotion` - 가격/프로모션
12. `Comparison` - 비교
13. `Lifestyle_Daily` - 라이프스타일/일상
14. `Storytelling` - 스토리텔링
15. `Business_Opportunity` - 비즈니스 기회
16. `Team_Group_Activity` - 팀/그룹 활동
17. `Event_Challenge` - 이벤트/챌린지
18. `Celebrity_Influencer` - 유명인/인플루언서

---

## 🔍 데이터 품질 확인

크롤링 완료 후 리포트 파일(`*_report.txt`)에서 다음 지표를 확인하세요:

### 중요 지표
- **수집 성공률**: 전체 시도 대비 성공률 (목표: 70% 이상)
- **OCR 처리 성공률**: 이미지가 있는 게시물 중 OCR 성공률 (목표: 60% 이상)
- **프로필 소개글 수집률**: 블로거 프로필 소개글 수집률 (목표: 50% 이상)
- **추천인 정보 수집률**: 전화번호 또는 파트너 ID 수집률 (목표: 40% 이상)

### 필터링 현황
- **필터링률**: PM 브랜드 키워드 미포함, 언론 스타일 등으로 필터링된 비율
- **중복률**: 이전에 수집된 중복 게시물 비율

---

## 🐛 문제 해결

### OCR이 작동하지 않는 경우

```bash
# EasyOCR 재설치
pip uninstall easyocr
pip install easyocr

# 한국어 모델 다운로드 확인
python -c "import easyocr; reader = easyocr.Reader(['ko', 'en']); print('✅ 모델 로드 성공')"
```

### 프로필 소개글이 수집되지 않는 경우

- 네이버 블로그 구조가 변경되었을 수 있습니다
- 크롤러는 여러 CSS 선택자를 시도하지만, 모든 경우를 커버하지 못할 수 있습니다
- `pm_naver_blog_crawler_v10_3_test.py`의 `extract_profile_info()` 함수를 확인하세요

### Selenium 드라이버 오류

```bash
# Chrome/Chromium 버전 확인
google-chrome --version
chromium --version

# webdriver-manager로 자동 설치
pip install --upgrade webdriver-manager
```

### 메모리 부족 오류

- 한 번에 너무 많은 게시물을 수집하는 경우 발생할 수 있습니다
- `config.yaml`에서 `max_search_results`를 50 정도로 낮추세요
- 체크포인트 파일(`checkpoint_posts_*.csv`)에서 중간 결과를 확인할 수 있습니다

---

## 📝 라이선스 및 주의사항

### 법적 고려사항
- 공개 게시물만 수집합니다
- 개인 식별 정보는 해시 처리됩니다
- 네이버 이용약관 및 로봇 배제 표준(robots.txt)을 준수합니다

### 윤리적 사용
- 수집한 데이터는 PM-International Korea 내부 분석 목적으로만 사용하세요
- 무단 재배포 금지
- 크롤링 속도 제한을 준수하세요 (딜레이 설정 유지)

---

## 💡 팁

1. **정기 실행 자동화**
   ```bash
   # Linux/Mac crontab 예시 (매일 새벽 2시 실행)
   0 2 * * * cd /path/to/project && python pm_naver_blog_crawler_v10_3_test.py
   ```

2. **GPU 가속 활용**
   - CUDA가 설치된 환경에서는 OCR 속도가 10배 이상 빨라집니다
   - NVIDIA GPU + CUDA Toolkit 설치 권장

3. **데이터 병합**
   ```python
   import pandas as pd
   
   # 여러 날짜에 수집한 CSV 병합
   df1 = pd.read_csv('naver_blog_pm_v10_3_posts_20251120_193725.csv')
   df2 = pd.read_csv('naver_blog_pm_v10_3_posts_20251121_143020.csv')
   
   df_merged = pd.concat([df1, df2], ignore_index=True)
   df_merged.drop_duplicates(subset=['post_id'], inplace=True)
   df_merged.to_csv('merged_posts.csv', index=False, encoding='utf-8-sig')
   ```

---

## 📞 문의

문제가 발생하거나 개선 사항이 있으면 PM-International Korea 데이터 분석팀에 문의하세요.

**작성자**: PMI Korea 데이터 분석팀  
**버전**: 10.3.0  
**최종 수정일**: 2025-11-20
