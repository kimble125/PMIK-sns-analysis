# PM-International Korea SNS 분석 프로젝트 구조

## 📁 디렉토리 구조

```
naver_blog/
├── 📄 README.md                          # 프로젝트 개요 및 시작 가이드
├── 📄 requirements.txt                   # Python 패키지 의존성
├── 📄 .gitignore                         # Git 제외 파일 목록
│
├── 📂 core/                              # 핵심 스크립트
│   ├── naver_blog_crawler.py            # 메인 크롤러 (추천인 정보 자동 추출)
│   ├── popularity_analyzer.py           # 인기도 분석 엔진
│   └── comprehensive_analysis.py        # 종합 분석 및 시각화
│
├── 📂 utils/                             # 유틸리티 스크립트
│   ├── hashtag_direct_search.py         # 해시태그 직접 검색
│   ├── analyze_hashtags.py              # 해시태그 분석
│   └── video_processor.py               # 동영상 처리 (Whisper)
│
├── 📂 docs/                              # 문서
│   ├── USAGE_GUIDE.md                   # 사용 가이드
│   ├── INSTALL_GUIDE.md                 # 설치 가이드
│   ├── PARTNER_IDENTIFICATION_GUIDE.md  # 판매원 식별 가이드
│   ├── POPULARITY_METRICS_GUIDE.md      # 인기도 평가 기준
│   └── IMPLEMENTATION_SUMMARY.md        # 구현 요약
│
├── 📂 output/                            # 크롤링 결과 (Git 제외)
│   ├── naver_blog_crawl_*.csv           # 수집 데이터
│   └── *.json                            # 통계 파일
│
├── 📂 reports/                           # 분석 리포트 (Git 제외)
│   ├── *.png                             # 시각화 이미지
│   └── analysis_summary_*.json          # 분석 요약
│
└── 📂 archive/                           # 구버전 파일 (참고용)
    ├── test_*.py                         # 테스트 스크립트
    └── check_*.py                        # 검증 스크립트
```

---

## 🔧 핵심 스크립트

### 1. `naver_blog_crawler.py`
**목적**: 네이버 블로그 데이터 수집 및 추천인 정보 자동 추출

**주요 기능**:
- Naver Search API로 블로그 URL 수집
- Selenium으로 본문 크롤링
- 해시태그 필터링
- EasyOCR로 이미지 텍스트 추출
- YouTube 자막 추출
- **추천인 정보 자동 추출** (이름, 전화번호, 파트너번호)

**실행**:
```bash
python naver_blog_crawler.py
```

**출력**:
- `output/naver_blog_crawl_YYYYMMDD_HHMMSS.csv`

---

### 2. `popularity_analyzer.py`
**목적**: 가중치 기반 인기도 분석

**주요 기능**:
- 인기도 점수 계산 (조회수 1.0, 공감 5.0, 댓글 10.0)
- 참여율, 댓글률, 공감률 계산
- 상위 인기 게시물 추출
- 다양한 가중치 프리셋 제공

**실행**:
```bash
python popularity_analyzer.py
```

**출력**:
- `output/naver_blog_popularity_analysis_*.csv`
- `output/naver_blog_top_posts_*.csv`
- `output/naver_blog_popularity_report_*.txt`

---

### 3. `comprehensive_analysis.py`
**목적**: 종합 데이터 분석 및 시각화

**주요 기능**:
- 6가지 시각화 그래프 생성
- 통계 요약
- HTML/PDF 리포트 생성 (선택)

**실행**:
```bash
python comprehensive_analysis.py
```

**출력**:
- `reports/01_popularity_distribution.png`
- `reports/02_top_posts.png`
- `reports/03_correlation_matrix.png`
- `reports/04_time_series.png`
- `reports/05_media_analysis.png`
- `reports/06_hashtag_analysis.png`
- `reports/analysis_summary_*.json`

---

## 📊 데이터 흐름

```
[1] 데이터 수집
    ↓
naver_blog_crawler.py
    ↓
output/naver_blog_crawl_*.csv
(추천인 정보 자동 추출 포함)

[2] 인기도 분석
    ↓
popularity_analyzer.py
    ↓
output/naver_blog_popularity_analysis_*.csv
(인기도 점수, 참여율 등 계산)

[3] 종합 분석 & 시각화
    ↓
comprehensive_analysis.py
    ↓
reports/*.png
(6가지 시각화 그래프)
```

---

## 📝 문서 가이드

### 필수 문서
1. **README.md**: 프로젝트 개요, 빠른 시작
2. **USAGE_GUIDE.md**: 상세 사용법
3. **INSTALL_GUIDE.md**: 설치 및 환경 설정

### 참고 문서
4. **PARTNER_IDENTIFICATION_GUIDE.md**: 판매원 식별 방법
5. **POPULARITY_METRICS_GUIDE.md**: 인기도 평가 기준
6. **IMPLEMENTATION_SUMMARY.md**: 구현 요약

---

## 🗂️ 파일 정리 규칙

### Git에 포함
- ✅ 모든 `.py` 스크립트
- ✅ 모든 `.md` 문서
- ✅ `requirements.txt`
- ✅ `.gitignore`

### Git에서 제외
- ❌ `output/*.csv` (데이터 파일)
- ❌ `reports/*.png` (시각화 이미지)
- ❌ `.venv/` (가상환경)
- ❌ `__pycache__/` (Python 캐시)

---

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터 수집
```bash
python naver_blog_crawler.py
```

### 3. 분석 실행
```bash
# 인기도 분석
python popularity_analyzer.py

# 종합 분석 및 시각화
python comprehensive_analysis.py
```

---

## 📦 주요 패키지

```
requests          # API 호출
beautifulsoup4    # HTML 파싱
selenium          # 웹 크롤링
pandas            # 데이터 처리
easyocr           # 이미지 텍스트 추출
matplotlib        # 시각화
seaborn           # 고급 시각화
numpy             # 수치 계산
```

---

## 🎯 프로젝트 목표

1. **데이터 수집**: 네이버 블로그에서 PM-International 관련 게시물 수집
2. **추천인 식별**: 본문/이미지에서 판매원 정보 자동 추출
3. **인기도 분석**: 가중치 기반 인기도 점수로 우수 게시물 식별
4. **인사이트 도출**: 시각화를 통한 콘텐츠 전략 수립

---

## 👥 팀원 온보딩

### 신규 팀원을 위한 체크리스트

- [ ] README.md 읽기
- [ ] INSTALL_GUIDE.md 따라 환경 설정
- [ ] USAGE_GUIDE.md로 기본 사용법 학습
- [ ] 샘플 데이터로 분석 실습
- [ ] 코드 리뷰 및 이해

---

## 📞 문의

프로젝트 관련 문의: PMI코리아 데이터 팀

---

**최종 업데이트**: 2025-11-01  
**버전**: 2.0  
**작성자**: PMI코리아 데이터 팀
