# VM 디렉토리 현황 확인 가이드

## 📋 개요

Crawler VM과 Analyst VM의 디렉토리 구조와 파일 현황을 확인하는 방법을 설명합니다.

---

## 🚀 빠른 시작

### 생성된 스크립트 사용

```bash
# 두 VM 모두 확인 (요약)
./check_all_vms.sh

# Crawler VM 상세 확인
./check_crawler_vm.sh

# Analyst VM 상세 확인
./check_analyst_vm.sh
```

---

## 📊 현재 VM 현황 (2025-11-21 기준)

### 🔧 Crawler VM

#### 디렉토리 구조
```
~/
├── PMIK-sns-analysis/          # 메인 프로젝트 (81MB)
│   ├── instagram/              # Instagram 크롤러 (12KB)
│   ├── kakaostory/             # Kakaostory 크롤러 (18MB)
│   ├── naver_blog/             # 네이버 블로그 크롤러 (81MB)
│   ├── youtube/                # 유튜브 크롤러 (436KB)
│   ├── analysis/               # 분석 결과 (9.2MB)
│   └── multimedia-process/     # 멀티미디어 처리 (17MB)
├── venvs/                      # Python 가상환경
├── logs/                       # 로그 파일
├── shared_data/                # 공유 데이터
├── work_kimble/                # 개인 작업 공간
└── work_colleague/             # 팀원 작업 공간
```

#### 주요 파일
- **Instagram**: `insta_crawl.py`, `insta_crawl_direct.py`
- **Kakaostory**: `kakaostory_posts.json` (18MB)
- **Naver Blog**: 다수의 크롤러 버전 (v5, v6, v9 등)
- **YouTube**: 트랜스크립트 포함 크롤러

#### 디스크 사용량
- **총 용량**: 124GB
- **사용 중**: 35GB (28%)
- **여유 공간**: 89GB

---

### 📊 Analyst VM

#### 디렉토리 구조
```
~/
└── venvs/
    ├── py311/                  # Python 3.11 환경 (7.4GB)
    └── python_code/            # 분석 코드 (9.6MB)
        ├── kakaostory_popup_posts.json (9.5MB)
        ├── kakaostory_postprocess.py (19KB)
        └── kakaostory_postprocess.log (61KB)
```

#### 주요 파일
- **Kakaostory 후처리**: `kakaostory_postprocess.py`
- **처리된 데이터**: `kakaostory_popup_posts.json` (9.5MB)
- **로그**: `kakaostory_postprocess.log`

#### 디스크 사용량
- **총 용량**: 124GB
- **사용 중**: 16GB (13%)
- **여유 공간**: 108GB

---

## 🔍 수동 확인 방법

### 기본 명령어

#### 1. 홈 디렉토리 확인
```bash
# Crawler VM
ssh crawler "ls -lah ~/"

# Analyst VM
ssh analyst "ls -lah ~/"
```

#### 2. 특정 폴더 확인
```bash
# Crawler VM - PMIK-sns-analysis
ssh crawler "ls -lh ~/PMIK-sns-analysis/"

# Analyst VM - python_code
ssh analyst "ls -lh ~/venvs/python_code/"
```

#### 3. 디렉토리 트리 보기
```bash
# Crawler VM
ssh crawler "find ~/PMIK-sns-analysis -maxdepth 2 -type d"

# Analyst VM
ssh analyst "find ~/venvs -maxdepth 2 -type d"
```

#### 4. 용량 확인
```bash
# 폴더별 용량
ssh crawler "du -sh ~/PMIK-sns-analysis/*"

# 디스크 사용량
ssh crawler "df -h ~/"
```

---

## 📁 파일 검색

### 파일명으로 검색
```bash
# Instagram 관련 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*instagram*'"

# Python 파일만 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.py'"

# JSON 파일만 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.json'"
```

### 최근 수정된 파일 찾기
```bash
# 최근 7일 이내 수정된 파일
ssh crawler "find ~/PMIK-sns-analysis -type f -mtime -7"

# 오늘 수정된 파일
ssh crawler "find ~/PMIK-sns-analysis -type f -mtime 0"

# 최근 수정 순으로 정렬
ssh crawler "find ~/PMIK-sns-analysis -type f -printf '%T@ %p\n' | sort -rn | head -20"
```

### 크기로 검색
```bash
# 10MB 이상 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -type f -size +10M"

# 1MB 이상 파일 크기순 정렬
ssh crawler "find ~/PMIK-sns-analysis -type f -size +1M -exec ls -lh {} \; | sort -k5 -h"
```

---

## 📊 상세 분석 명령어

### 폴더별 용량 분석
```bash
# 크기순 정렬
ssh crawler "du -sh ~/PMIK-sns-analysis/* | sort -h"

# 상위 10개 폴더
ssh crawler "du -h ~/PMIK-sns-analysis | sort -rh | head -10"

# 특정 깊이까지만
ssh crawler "du -h --max-depth=2 ~/PMIK-sns-analysis | sort -rh"
```

### 파일 타입별 통계
```bash
# Python 파일 개수
ssh crawler "find ~/PMIK-sns-analysis -name '*.py' | wc -l"

# CSV 파일 총 용량
ssh crawler "find ~/PMIK-sns-analysis -name '*.csv' -exec du -ch {} + | tail -1"

# 파일 타입별 개수
ssh crawler "find ~/PMIK-sns-analysis -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn"
```

### 디렉토리 통계
```bash
# 총 파일 개수
ssh crawler "find ~/PMIK-sns-analysis -type f | wc -l"

# 총 디렉토리 개수
ssh crawler "find ~/PMIK-sns-analysis -type d | wc -l"

# 전체 용량
ssh crawler "du -sh ~/PMIK-sns-analysis"
```

---

## 🎯 실전 예제

### 예제 1: Instagram 크롤러 찾기
```bash
# 파일 위치 확인
ssh crawler "find ~/PMIK-sns-analysis -name '*insta*'"

# 파일 내용 미리보기
ssh crawler "head -20 ~/PMIK-sns-analysis/instagram/insta_crawl.py"

# 파일 크기 확인
ssh crawler "ls -lh ~/PMIK-sns-analysis/instagram/"
```

### 예제 2: 최신 크롤링 결과 확인
```bash
# 최근 CSV 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.csv' -mtime -7 -exec ls -lh {} \;"

# 최신 파일 5개
ssh crawler "ls -lt ~/PMIK-sns-analysis/naver_blog/*.csv | head -5"
```

### 예제 3: 로그 파일 확인
```bash
# 모든 로그 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.log'"

# 로그 파일 크기 확인
ssh crawler "find ~/PMIK-sns-analysis -name '*.log' -exec du -h {} \;"

# 최근 로그 내용 확인
ssh crawler "tail -50 ~/PMIK-sns-analysis/naver_blog/crawler.log"
```

### 예제 4: 팀원 작업 확인
```bash
# Analyst VM의 최근 작업
ssh analyst "ls -lt ~/venvs/python_code/ | head -10"

# 최근 수정된 Python 파일
ssh analyst "find ~/venvs/python_code -name '*.py' -mtime -7"
```

---

## 🔄 정기 모니터링

### 일일 체크리스트
```bash
# 1. 디스크 용량 확인
ssh crawler "df -h ~/"
ssh analyst "df -h ~/"

# 2. 최근 활동 확인
ssh crawler "find ~/PMIK-sns-analysis -type f -mtime 0"
ssh analyst "find ~/venvs/python_code -type f -mtime 0"

# 3. 로그 확인
ssh crawler "tail -20 ~/PMIK-sns-analysis/naver_blog/crawler.log"
```

### 주간 리포트 생성
```bash
# 스크립트 실행 후 저장
./check_all_vms.sh > vm_status_$(date +%Y%m%d).txt

# 또는 상세 리포트
{
    echo "=== Crawler VM ==="
    ./check_crawler_vm.sh
    echo ""
    echo "=== Analyst VM ==="
    ./check_analyst_vm.sh
} > vm_detailed_status_$(date +%Y%m%d).txt
```

---

## 🛠️ 유용한 별칭(Alias) 설정

로컬 `~/.zshrc` 또는 `~/.bashrc`에 추가:

```bash
# VM 디렉토리 확인 별칭
alias vm-status='~/Documents/IT/PMIK-sns-analysis/check_all_vms.sh'
alias vm-crawler='~/Documents/IT/PMIK-sns-analysis/check_crawler_vm.sh'
alias vm-analyst='~/Documents/IT/PMIK-sns-analysis/check_analyst_vm.sh'

# 빠른 디렉토리 확인
alias crawler-ls='ssh crawler "ls -lh ~/PMIK-sns-analysis/"'
alias analyst-ls='ssh analyst "ls -lh ~/venvs/python_code/"'

# 디스크 용량 확인
alias crawler-disk='ssh crawler "df -h ~/"'
alias analyst-disk='ssh analyst "df -h ~/"'

# 최근 파일 확인
alias crawler-recent='ssh crawler "find ~/PMIK-sns-analysis -type f -mtime -1"'
alias analyst-recent='ssh analyst "find ~/venvs/python_code -type f -mtime -1"'
```

설정 후:
```bash
source ~/.zshrc  # 또는 source ~/.bashrc
vm-status        # 바로 사용 가능
```

---

## 📋 트러블슈팅

### 문제 1: 디렉토리가 보이지 않음
```bash
# 숨김 파일 포함 확인
ssh crawler "ls -la ~/PMIK-sns-analysis/"

# 권한 확인
ssh crawler "ls -ld ~/PMIK-sns-analysis"
```

### 문제 2: 용량이 부족함
```bash
# 큰 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -type f -size +100M"

# 오래된 로그 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.log' -mtime +30"

# 임시 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.tmp' -o -name '*~'"
```

### 문제 3: 파일을 찾을 수 없음
```bash
# 대소문자 구분 없이 검색
ssh crawler "find ~/PMIK-sns-analysis -iname '*instagram*'"

# 전체 시스템 검색 (느림)
ssh crawler "find ~ -name 'insta_crawl.py' 2>/dev/null"
```

---

## 📞 빠른 참조

### 가장 많이 쓰는 명령어

```bash
# 1. 전체 현황 확인
./check_all_vms.sh

# 2. 특정 폴더 확인
ssh crawler "ls -lh ~/PMIK-sns-analysis/instagram/"

# 3. 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '파일명'"

# 4. 용량 확인
ssh crawler "du -sh ~/PMIK-sns-analysis/*"

# 5. 최근 파일
ssh crawler "find ~/PMIK-sns-analysis -type f -mtime -7"
```

---

## 📚 관련 문서

- `VM_FILE_DOWNLOAD_GUIDE.md` - VM 파일 다운로드 방법
- `VM_TIMEZONE_GUIDE.md` - VM 시간대 설정
- `VM_UBUNTU_ACCESS_GUIDE.md` - VM 접속 및 권한 관리

---

**작성일**: 2025년 11월 21일  
**작성자**: PMI Korea 데이터 분석팀  
**버전**: 1.0
