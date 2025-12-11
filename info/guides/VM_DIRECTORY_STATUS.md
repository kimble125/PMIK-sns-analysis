# VM 디렉토리 현황 (2025-11-14 업데이트)

## 📊 PMIKR-DATA-CRAWLER VM

### 홈 디렉토리 구조 (`/home/pmi/`)

```
/home/pmi/
├── PMIK-sns-analysis/          # 🔄 Git 저장소 (공유 프로젝트)
│   ├── .venv/                  # Python 가상환경
│   ├── naver_blog/             # 네이버 블로그 크롤러
│   ├── youtube/                # 유튜브 크롤러
│   ├── analysis/               # 데이터 분석
│   ├── multimedia-process/     # 멀티미디어 처리
│   ├── instagram/              # 인스타그램 (미사용)
│   ├── kakaostory/             # 카카오스토리 (미사용)
│   └── *.md                    # 문서 파일들
│
├── work_kimble/                # 📁 김블 개인 작업 공간 (비어있음)
├── work_colleague/             # 📁 동료 개인 작업 공간 (비어있음)
├── shared_data/                # 📁 공유 데이터 (비어있음)
│
├── venvs/                      # 추가 가상환경들
│   ├── py311/
│   └── source_code/
│
├── CascadeProjects/            # Cascade 프로젝트
├── snap/                       # Snap 패키지 (chromium 등)
│   └── chromium/
│
└── *.sh                        # 유틸리티 스크립트들
    ├── check_resources.sh
    ├── check_vm_info.sh
    └── stop_vm.sh
```

### 현재 실행 중인 작업

#### Screen 세션
```
1. kimble_crawler (196510) - Attached (현재 접속 중)
   - 시작: 2025-11-13 07:14:01
   
2. kimble_crawler (193920) - Detached (백그라운드 실행)
   - 시작: 2025-11-13 07:05:29
```

#### Python 프로세스
- 시스템 프로세스만 실행 중 (크롤러는 Screen 내부에서 실행 중일 가능성)

---

## 📊 PMIKR-DATA-ANALYST VM

### 상태
❌ **현재 접속 불가** (VM이 중지되어 있거나 방화벽 설정 필요)
- IP: 20.214.24.3
- 포트: 22
- 상태: Connection timeout

### 확인 필요 사항
1. Azure Portal에서 VM 상태 확인
2. 네트워크 보안 그룹(NSG) SSH 포트 허용 확인
3. VM 시작 필요 시 Azure Portal에서 시작

---

## 🔍 디렉토리 확인 명령어

### CRAWLER VM 전체 구조 보기
```bash
ssh crawler
tree -L 2 -d ~/  # tree 설치 필요: sudo apt install tree

# 또는
find ~ -maxdepth 2 -type d ! -path '*/.*' | sort
```

### 특정 디렉토리 확인
```bash
# PMIK-sns-analysis 프로젝트
ssh crawler "ls -la ~/PMIK-sns-analysis"

# 개인 작업 공간
ssh crawler "ls -la ~/work_kimble"
ssh crawler "ls -la ~/work_colleague"

# 공유 데이터
ssh crawler "ls -la ~/shared_data"
```

### 디렉토리 크기 확인
```bash
ssh crawler "du -sh ~/PMIK-sns-analysis"
ssh crawler "du -sh ~/work_*"
ssh crawler "du -sh ~/shared_data"
```

### 실행 중인 작업 확인
```bash
# Screen 세션
ssh crawler "screen -ls"

# Python 프로세스
ssh crawler "ps aux | grep python | grep -v grep"

# 전체 프로세스 (pmi 사용자)
ssh crawler "ps -u pmi"
```

---

## 📁 권장 디렉토리 사용 방법

### 1. **PMIK-sns-analysis/** (공유 Git 저장소)
**용도:** 코드 공유, 버전 관리
**사용자:** 김블, 동료 모두

```bash
# 최신 코드 받기
cd ~/PMIK-sns-analysis
git pull

# 작업 후 푸시
git add .
git commit -m "작업 내용"
git push
```

**주의사항:**
- ✅ 코드 파일만 커밋
- ❌ 데이터 파일(.csv, .json 등)은 .gitignore에 포함
- ❌ 로그 파일은 커밋하지 않기

### 2. **work_kimble/** (김블 개인 작업)
**용도:** 개인 실험, 임시 작업, 테스트

```bash
cd ~/work_kimble

# 예시: 테스트 스크립트
python test_new_feature.py

# 예시: 임시 데이터 처리
python process_temp_data.py
```

**장점:**
- 동료 작업과 완전히 분리
- Git 관리 불필요
- 자유롭게 실험 가능

### 3. **work_colleague/** (동료 개인 작업)
**용도:** 동료의 개인 작업 공간

### 4. **shared_data/** (공유 데이터)
**용도:** 크롤링 결과, 분석 결과 공유

```bash
# 권장 구조
~/shared_data/
├── raw_data/           # 원본 크롤링 데이터
│   ├── naver_blog/
│   └── youtube/
├── processed_data/     # 전처리된 데이터
└── results/            # 최종 분석 결과
```

**사용 예시:**
```bash
# 크롤링 결과 저장
python crawler.py --output ~/shared_data/raw_data/naver_blog/

# 동료가 데이터 사용
python analyze.py --input ~/shared_data/raw_data/naver_blog/
```

---

## 🔄 작업 흐름 예시

### 김블의 작업 흐름
```bash
# 1. 개인 공간에서 테스트
cd ~/work_kimble
python test_new_crawler.py

# 2. 테스트 성공 시 Git 저장소로 이동
cp test_new_crawler.py ~/PMIK-sns-analysis/naver_blog/

# 3. Git 커밋
cd ~/PMIK-sns-analysis
git add naver_blog/test_new_crawler.py
git commit -m "Add new crawler feature"
git push

# 4. 크롤링 실행 (결과는 shared_data에)
cd ~/PMIK-sns-analysis/naver_blog
python crawler.py --output ~/shared_data/raw_data/
```

### 동료의 작업 흐름
```bash
# 1. 최신 코드 받기
cd ~/PMIK-sns-analysis
git pull

# 2. 공유 데이터로 분석
cd ~/work_colleague
python analyze.py --input ~/shared_data/raw_data/

# 3. 분석 결과 저장
python analyze.py --output ~/shared_data/results/
```

---

## 📋 현재 상태 체크리스트

### CRAWLER VM
- ✅ PMIK-sns-analysis 프로젝트 설치됨
- ✅ 가상환경 설정 완료
- ✅ work_kimble 디렉토리 생성됨
- ✅ work_colleague 디렉토리 생성됨
- ✅ shared_data 디렉토리 생성됨
- ⚠️ Screen 세션 2개 실행 중 (정리 필요할 수 있음)

### ANALYST VM
- ❌ 현재 접속 불가
- ❓ 디렉토리 구조 미확인
- ❓ 프로젝트 설치 여부 미확인

---

## 🛠️ 유용한 명령어 모음

### 디렉토리 생성
```bash
# 개인 작업 공간에 하위 디렉토리 생성
ssh crawler "mkdir -p ~/work_kimble/{tests,experiments,temp}"
ssh crawler "mkdir -p ~/shared_data/{raw_data,processed_data,results}"
```

### 디스크 사용량 확인
```bash
# 전체 디스크
ssh crawler "df -h"

# 홈 디렉토리 크기
ssh crawler "du -sh ~/*" | sort -h

# 큰 파일 찾기 (100MB 이상)
ssh crawler "find ~ -type f -size +100M -exec ls -lh {} \;"
```

### 파일 검색
```bash
# CSV 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.csv'"

# 최근 수정된 파일 (24시간 이내)
ssh crawler "find ~/PMIK-sns-analysis -type f -mtime -1"

# 로그 파일 찾기
ssh crawler "find ~ -name '*.log' -type f"
```

---

## 📞 동료와 공유할 정보

동료에게 다음 정보를 공유하세요:

1. **디렉토리 구조**
   - `~/PMIK-sns-analysis`: Git 저장소 (코드 공유)
   - `~/work_colleague`: 개인 작업 공간
   - `~/shared_data`: 데이터 공유

2. **Git 저장소 클론** (아직 안 했다면)
   ```bash
   cd ~
   git clone https://github.com/kimble125/PMIK-sns-analysis.git
   cd PMIK-sns-analysis
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Screen 세션 확인**
   ```bash
   screen -ls  # 실행 중인 세션 확인
   ```

4. **리소스 확인**
   ```bash
   htop  # CPU/메모리 사용량
   ```

---

## 🔄 정기 업데이트

이 문서는 VM 사용 현황이 변경될 때마다 업데이트하세요.

**마지막 업데이트:** 2025-11-14 10:23 (김블)
**다음 업데이트:** 동료 작업 시작 시
