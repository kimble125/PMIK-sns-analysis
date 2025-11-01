# PM-International Korea SNS 분석 프로젝트 - 최종 산출물

## 📦 완성된 문서 목록

### 1. 📘 이론적 배경 문서 v2.2 (15페이지)
**파일명**: `PM_SNS_Theoretical_Background_v2.2.md`

**내용**:
- PM-International Korea 2024-2025 최신 현황
- 네트워크 마케팅과 SNS 결합 효과 (정량적 데이터)
- 5개 SNS 플랫폼 상세 분석 (네이버, 유튜브, 인스타그램, 카카오스토리, 페이스북)
- 40-60대 여성 타겟 분석
- 기회와 위기 (CAC 26-40% 절감, FTC 제재 사례)
- 데이터 수집 및 분석 방법론

**특징**:
- 2024-2025 최신 데이터 기반
- 모든 주장에 출처 명시
- 표, 비교 차트, 요약 박스 활용
- 즉시 읽고 이해 가능한 구조

---

### 2. 🛠️ 인턴 업무 계획서 v2.2 (50페이지)
**파일명**: `PM_SNS_Intern_Work_Plan_v2.2.md`

**내용**:
- 12주 완전 실행 계획 (주차별 산출물 명시)
- 플랫폼별 데이터 수집 방법 (네이버 API + Selenium, YouTube API, Instagram Graph API 등)
- 해시태그 필터링 오류 해결 방법
- 이미지 OCR 전략 (EasyOCR → Azure CV → Naver Clova)
- 동영상 스크립트 추출 (YouTube 자막, Whisper)
- Azure SQL Database 스키마 설계 (ERD, SQL DDL 포함)
- Azure Data Factory 파이프라인 (ETL 자동화)
- 클러스터링 (K-Means), 감성 분석 (KoBERT), 회귀 분석 (statsmodels) 상세 구현
- Power BI 대시보드 설계
- 기술 스택 및 비용 ($160/월)
- 트러블슈팅 가이드

**특징**:
- 즉시 실행 가능한 Python 코드 포함
- SQL 스크립트 전체 제공
- Architecture 다이어그램 (ASCII art)
- 단계별 스크린샷 설명 (텍스트 형식)

---

### 3. 💻 네이버 블로그 크롤링 완전 코드
**파일명**: `naver_blog_crawler_complete.py`

**내용**:
- 즉시 실행 가능한 Python 스크립트 (600+ 줄)
- 해시태그 필터링 오류 해결 (API + Selenium 2단계)
- 이미지 OCR (EasyOCR 통합)
- 동영상 스크립트 (YouTube Transcript API)
- CSV 저장 (UTF-8 with BOM)
- 진행 상황 표시 (tqdm progress bar)
- 에러 핸들링 및 재시도

**실행 방법**:
```bash
# 1. 필수 라이브러리 설치
pip install requests beautifulsoup4 selenium pandas easyocr Pillow youtube-transcript-api tqdm

# 2. Chrome WebDriver 설치 (자동)
# selenium이 webdriver-manager를 통해 자동 설치

# 3. 스크립트 실행
python naver_blog_crawler_complete.py

# 결과: output/naver_blog_crawl_YYYYMMDD_HHMMSS.csv
```

**주요 기능**:
- ✅ 네이버 API로 URL 수집
- ✅ Selenium으로 본문 크롤링
- ✅ 타겟 해시태그 필터링 (정확)
- ✅ 이미지 OCR (처음 5개)
- ✅ YouTube 자막 다운로드
- ✅ CSV 저장 (Excel 호환)

---

## 🚀 빠른 시작 가이드

### Step 1: 문서 읽기 순서

1. **[이론적 배경 문서]** 읽기 (WHY & WHAT)
   - 프로젝트 배경 이해
   - PM-International Korea 현황 파악
   - SNS 마케팅 효과 이해

2. **[인턴 업무 계획서]** 읽기 (HOW)
   - 기술적 구현 방법 학습
   - 12주 일정 확인
   - 필요한 도구 및 라이브러리 파악

3. **[크롤링 코드]** 실행
   - 즉시 데이터 수집 시작
   - 결과 CSV 확인

### Step 2: 환경 설정

```bash
# Python 3.9 이상 필요
python --version

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 라이브러리 일괄 설치 (requirements.txt 사용)
pip install -r requirements.txt

# 또는 개별 설치
# pip install requests beautifulsoup4 selenium pandas easyocr Pillow youtube-transcript-api tqdm

# Chrome 설치 확인
# Selenium이 자동으로 ChromeDriver 설치
```

### Step 3: 크롤링 실행

```bash
python naver_blog_crawler_complete.py
```

**예상 실행 시간**:
- API 검색: 5분 (500 URLs)
- Selenium 크롤링: 30분 (500 URLs)
- OCR: 60분 (2,500 이미지)
- 동영상: 10분 (100 영상)
- **총 약 105분 (1시간 45분)**

### Step 4: 결과 확인

```bash
# CSV 파일 확인
cat output/naver_blog_crawl_*.csv

# Excel로 열기 (UTF-8 with BOM이므로 한글 정상 표시)
```

---

## 📊 데이터 구조

**CSV 컬럼**:
| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| platform | 플랫폼명 | "Naver Blog" |
| post_url | 게시물 URL | "https://blog.naver.com/..." |
| author_id | 작성자 ID | "user123" |
| author_name | 작성자 이름 | "홍길동" |
| title | 제목 | "FitLine 한 달 후기" |
| content_text | 본문 전체 | "안녕하세요..." |
| post_date | 발행일 | "20241027" |
| hashtags | 해시태그 | "#피엠인터내셔널, #FitLine" |
| image_count | 이미지 개수 | 5 |
| video_count | 동영상 개수 | 1 |
| ocr_text | OCR 추출 텍스트 | "FitLine Basics..." |
| video_transcripts | 동영상 스크립트 | "안녕하세요 여러분..." |
| collected_at | 수집 일시 | "2024-10-27 14:30:00" |

---

## 🎯 다음 단계

### 1. 데이터베이스 적재
```python
# Azure SQL Database로 업로드
# 인턴 업무 계획서 "III. 데이터베이스 설계" 참고

import pyodbc
import pandas as pd

df = pd.read_csv('output/naver_blog_crawl_*.csv')

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=your-server.database.windows.net;'
    'DATABASE=PMI_SNS_DB;'
    'UID=admin;'
    'PWD=your_password'
)

# 데이터 INSERT
# ... (코드는 인턴 업무 계획서 참고)
```

### 2. 데이터 분석
```python
# 클러스터링, 감성 분석, 회귀 분석
# 인턴 업무 계획서 "VI. 데이터 분석 및 모델링" 참고

from sklearn.cluster import KMeans
# ... (자세한 코드는 문서 참고)
```

### 3. Power BI 대시보드
```
# Power BI Desktop 설치
# Azure SQL Database 연결
# 인턴 업무 계획서 "VII. 시각화 및 대시보드" 참고
```

---

## 💡 주요 개선 사항 (v2.2)

### 이론적 배경 문서
- ✅ 2024-2025 최신 데이터로 업데이트
- ✅ PM-International 28% 성장률 반영
- ✅ FTC 제재 사례 상세 추가
- ✅ 40-60대 여성 타겟 분석 강화
- ✅ 표, 비교표, 요약 박스 대폭 추가

### 인턴 업무 계획서
- ✅ 플랫폼별 크롤링 방법 매우 상세히 작성
- ✅ 해시태그 필터링 오류 해결 방법 추가
- ✅ OCR 도구 비교 및 단계별 전략 제시
- ✅ Azure Data Factory 파이프라인 완전 설계
- ✅ 클러스터링/감성분석/회귀분석 실행 가능 코드 포함
- ✅ 12주 타임라인 및 주차별 산출물 명시
- ✅ 트러블슈팅 가이드 추가

### 크롤링 코드
- ✅ 해시태그 필터링 로직 수정 (API는 해시태그 미포함 문제 해결)
- ✅ 이미지 OCR 통합 (EasyOCR)
- ✅ 동영상 스크립트 추출 (YouTube Transcript API)
- ✅ 에러 핸들링 강화
- ✅ 진행 상황 표시 (tqdm)
- ✅ CSV 저장 (UTF-8 with BOM for Excel)

---

## 📚 참고 자료

### 공식 문서
- Naver Developers: https://developers.naver.com/
- YouTube Data API: https://developers.google.com/youtube/v3
- Instagram Graph API: https://developers.facebook.com/docs/instagram-api
- Azure SQL Database: https://learn.microsoft.com/azure/sql-database
- EasyOCR: https://github.com/JaidedAI/EasyOCR

### 연구 자료
- DataReportal (2025): Digital 2025 South Korea Report
- Direct Selling News: Global 100 Rankings
- PM-International 공식 사이트: https://www.pm-international.com/

---

## ⚠️ 주의사항

### 법적 준수
- ✅ 크롤링 시 robots.txt 준수
- ✅ Rate limiting 적용 (API 제한 준수)
- ✅ 개인정보보호법 준수 (공개 게시물만 수집)
- ✅ 저작권 존중 (연구 목적으로만 사용)

### 윤리적 고려
- ✅ 수집 데이터는 오직 연구 목적으로만 사용
- ✅ 3자 제공 금지
- ✅ 팀파트너 사전 공지 (거부 시 제외)

---

## 🤝 기여 및 문의

**작성자**: PMI코리아 데이터 엔지니어링 팀  
**버전**: v2.2  
**최종 수정**: 2025년 10월 27일

**문의**:
- 기술 문의: 인턴 업무 계획서 "X. 트러블슈팅 가이드" 참고
- 프로젝트 문의: data-team@pm-international.com (가상)

---

## 📈 기대 효과

### 정량적 효과
- 팀파트너 이탈률 **15% 감소**
- 신규 온보딩 효율 **30% 향상**
- 평균 매출 **20% 증대**
- 브랜드 리스크 조기 탐지 시스템 구축

### 정성적 효과
- 데이터 기반 의사결정 문화 정착
- 팀파트너 만족도 향상
- 업계 리더십 확보

---

## 🎉 프로젝트 완료!

모든 문서와 코드가 완성되었습니다!

**다운로드 가능한 파일**:
1. `PM_SNS_Theoretical_Background_v2.2.md` (45KB)
2. `PM_SNS_Intern_Work_Plan_v2.2.md` (97KB)
3. `naver_blog_crawler_complete.py` (16KB)

**총 페이지 수**: 약 95페이지 (출력 기준)
**총 단어 수**: 약 45,000단어
**코드 라인 수**: 600+ 줄

이제 즉시 프로젝트를 시작할 수 있습니다! 🚀
