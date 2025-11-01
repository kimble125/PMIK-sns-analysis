# PM-International Korea SNS 분석 프로젝트

> 네이버 블로그 크롤링 및 SNS 데이터 분석 자동화 시스템

## 📋 프로젝트 개요

PM-International Korea의 SNS 마케팅 효과 분석을 위한 데이터 수집 및 분석 시스템입니다.
네이버 블로그에서 PM 관련 해시태그를 자동으로 수집하고, 추천인 정보를 추출하여 마케팅 성과를 분석합니다.

### 주요 기능

- ✅ **해시태그 기반 자동 크롤링**: 17개 주요 해시태그 모니터링
- ✅ **추천인 정보 자동 추출**: 이름, 전화번호, 파트너 번호, 카카오톡 ID
- ✅ **병렬 처리 최적화**: MacBook M2 기준 6-8시간 (v6.0)
- ✅ **진행 상황 자동 저장**: 중단 시 재개 가능
- ✅ **CSV 출력**: 17개 컬럼, Excel 호환

### 수집 데이터

| 카테고리 | 항목 |
|---------|------|
| **기본 정보** | 플랫폼, 제목, 설명, 블로거 프로필, URL, 작성자 ID |
| **콘텐츠** | 본문, 해시태그, 작성일 |
| **미디어** | 이미지 개수/URL, 동영상 개수/URL |
| **참여 지표** | 조회수, 좋아요, 댓글 수 |
| **추천인 정보** | 이름, 전화번호, 파트너 번호, 카카오톡 ID |

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# Python 3.11 이상 필요
python --version

# 의존성 설치
pip install -r naver_blog/requirements_v5.txt
```

### 2. API 키 설정

`naver_blog/config.py` 파일 생성:

```python
NAVER_CLIENT_ID = 'your_client_id'
NAVER_CLIENT_SECRET = 'your_client_secret'
```

또는 `.env` 파일 사용:

```bash
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
```

### 3. 크롤링 실행

```bash
cd naver_blog

# v6.0 (병렬 처리 - 권장)
python naver_blog_crawler_v6.py

# v5.0 (단일 스레드)
python naver_blog_crawler_v5.py
```

## 📊 버전 비교

| 버전 | 처리 방식 | 예상 시간 (13,741개) | 권장 환경 |
|------|----------|---------------------|----------|
| **v5.0** | 단일 스레드 | 22-31시간 | Windows PC |
| **v6.0** | 병렬 처리 (4 워커) | 6-8시간 | MacBook M2 |

### v6.0 주요 개선사항

- 🚀 **4배 속도 향상**: 멀티프로세싱 적용
- 🛡️ **Alert 자동 처리**: 비공개 글 자동 스킵
- ⚡ **메모리 최적화**: 16GB 환경 최적화
- 💾 **진행 상황 저장**: 중단 시 재개 가능

## 📁 프로젝트 구조

```
IT/
├── naver_blog/                 # 네이버 블로그 크롤러
│   ├── naver_blog_crawler_v6.py  # v6.0 (병렬 처리)
│   ├── naver_blog_crawler_v5.py  # v5.0 (단일 스레드)
│   ├── requirements_v5.txt       # 필수 라이브러리
│   ├── config.example.py         # API 키 설정 예시
│   └── output/                   # 크롤링 결과 (gitignore)
│
├── instagram/                  # 인스타그램 크롤러 (개발 중)
│
├── PM_SNS_Intern_Work_Plan_v2.2.md      # 업무 계획서
├── PM_SNS_Theoretical_Background_v2_4.md # 이론적 배경
└── README.md                   # 이 파일
```

## 🎯 타겟 해시태그

### 브랜드명 (4개)
- #피엠인터내셔널, #피엠코리아, #독일피엠, #PM인터내셔널

### 제품 라인 (2개)
- #핏라인, #피트라인

### 개별 제품 (11개)
- #베이식스, #베이직스, #베이식
- #프로셰이프, #프로쉐이프
- #엑티바이즈, #파워칵테일, #리스토레이트
- #뮤니티, #옵티멀셋, #셀플러스

## 💻 시스템 요구사항

### 최소 사양
- **CPU**: 2코어 이상
- **RAM**: 8GB 이상
- **저장공간**: 10GB 이상
- **OS**: Windows 10/11, macOS 12+, Linux

### 권장 사양 (v6.0)
- **CPU**: 4코어 이상 (Apple M2 최적화)
- **RAM**: 16GB 이상
- **저장공간**: 20GB 이상
- **OS**: macOS 12+ (Apple Silicon)

## 📖 사용 가이드

### MacBook으로 작업 이전

1. **Git 클론**
   ```bash
   git clone <repository-url>
   cd IT/naver_blog
   ```

2. **환경 설정**
   ```bash
   # Python 3.11 설치 (Homebrew)
   brew install python@3.11
   
   # Chrome 설치
   brew install --cask google-chrome
   
   # ChromeDriver 설치
   brew install chromedriver
   
   # 의존성 설치
   pip3 install -r requirements_v5.txt
   ```

3. **API 키 설정**
   ```bash
   cp config.example.py config.py
   # config.py 파일 편집하여 API 키 입력
   ```

4. **크롤링 실행**
   ```bash
   python3 naver_blog_crawler_v6.py
   ```

### 출력 파일

```
output/
├── naver_blog_crawl_YYYYMMDD_HHMMSS.csv  # 크롤링 결과
└── crawl_stats_YYYYMMDD_HHMMSS.json      # 통계 정보
```

## 🔧 트러블슈팅

### Chrome 관련 오류
```bash
# ChromeDriver 권한 오류 (macOS)
xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

### API 키 오류
- `config.py` 파일이 올바른 위치에 있는지 확인
- API 키가 정확한지 Naver Developers에서 확인

### 메모리 부족
- v6.0의 `NUM_WORKERS` 값을 2로 줄이기
- 다른 프로그램 종료

## 📈 성능 벤치마크

| 환경 | CPU | RAM | 처리 속도 | 총 시간 (13,741개) |
|------|-----|-----|----------|-------------------|
| Windows PC | i3-1115G4 | 8GB | 6.15초/개 | 22-31시간 |
| MacBook M2 (v5.0) | M2 8코어 | 16GB | 4.10초/개 | 15-17시간 |
| MacBook M2 (v6.0) | M2 8코어 | 16GB | 1.54초/개 | **6-8시간** |

## 📝 다음 단계

1. **이미지 OCR**: Google Colab에서 EasyOCR 처리
2. **동영상 분석**: Whisper로 음성 텍스트 추출
3. **데이터 분석**: 추천인 네트워크 분석
4. **시각화**: 대시보드 구축

## 👥 기여자

- **데이터 팀**: 크롤링 시스템 개발
- **인턴**: SNS 데이터 수집 및 분석

## 📄 라이선스

이 프로젝트는 PM-International Korea의 내부 프로젝트입니다.

## 📞 문의

프로젝트 관련 문의사항은 데이터 팀으로 연락 바랍니다.

---

**Last Updated**: 2025-11-02  
**Version**: 6.0  
**Status**: Production Ready
