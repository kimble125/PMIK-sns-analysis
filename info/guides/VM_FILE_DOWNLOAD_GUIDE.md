# VM 파일 다운로드 완전 가이드

## 📋 개요

팀원이 Analyst VM과 Crawler VM에서 작업한 코드와 데이터를 로컬로 다운로드하는 방법을 설명합니다.

---

## 📁 현재 VM 파일 구조

### Crawler VM
```
~/PMIK-sns-analysis/
├── instagram/
│   ├── insta_crawl.py (1.3KB)
│   └── insta_crawl_direct.py (1.5KB)
├── kakaostory/
│   └── kakaostory_posts.json (18MB)
├── naver_blog/
│   ├── pm_naver_blog_crawler_v9_1_final.py
│   ├── config.yaml
│   ├── naver_blog_pm_v9_1_final_20251117_124720.csv
│   └── logs/
└── youtube/
    └── (유튜브 크롤러 파일들)
```

### Analyst VM
```
~/ 
└── (분석 관련 파일들)
```

---

## 💾 다운로드 방법

### 방법 1: SCP (가장 간단) ⭐

#### 개별 파일 다운로드
```bash
# 기본 형식
scp [VM별칭]:[원격파일경로] [로컬저장경로]

# Instagram 크롤러 다운로드
scp crawler:~/PMIK-sns-analysis/instagram/insta_crawl.py ~/Documents/IT/PMIK-sns-analysis/instagram/

# Kakaostory 데이터 다운로드
scp crawler:~/PMIK-sns-analysis/kakaostory/kakaostory_posts.json ~/Documents/IT/PMIK-sns-analysis/kakaostory/
```

#### 폴더 전체 다운로드
```bash
# -r 옵션: 재귀적 복사 (폴더 전체)
scp -r crawler:~/PMIK-sns-analysis/instagram ~/Documents/IT/PMIK-sns-analysis/

# 여러 폴더 한번에
scp -r crawler:~/PMIK-sns-analysis/{instagram,kakaostory} ~/Documents/IT/PMIK-sns-analysis/
```

#### 장단점
✅ **장점**:
- 가장 간단하고 직관적
- SSH 설정만 되어있으면 바로 사용 가능
- 작은 파일에 적합

❌ **단점**:
- 대용량 파일 전송 시 중단되면 처음부터 다시
- 진행률 표시 없음
- 파일이 많으면 비효율적

---

### 방법 2: Rsync (대용량 권장) ⭐⭐

```bash
# 기본 형식
rsync -avz --progress [원격경로] [로컬경로]

# Instagram 폴더 동기화
rsync -avz --progress \
    crawler:~/PMIK-sns-analysis/instagram/ \
    ~/Documents/IT/PMIK-sns-analysis/instagram/

# Kakaostory 폴더 동기화
rsync -avz --progress \
    crawler:~/PMIK-sns-analysis/kakaostory/ \
    ~/Documents/IT/PMIK-sns-analysis/kakaostory/

# 전체 프로젝트 동기화
rsync -avz --progress \
    crawler:~/PMIK-sns-analysis/ \
    ~/Documents/IT/PMIK-sns-analysis/vm-backup/
```

#### 옵션 설명
```
-a: archive 모드 (권한, 타임스탬프 보존)
-v: verbose (상세 출력)
-z: compress (전송 시 압축)
--progress: 진행률 표시
--exclude: 특정 파일/폴더 제외
--dry-run: 실제 복사 없이 시뮬레이션
```

#### 고급 옵션
```bash
# CSV 파일만 동기화
rsync -avz --progress --include="*.csv" --exclude="*" \
    crawler:~/PMIK-sns-analysis/naver_blog/ \
    ~/Documents/IT/PMIK-sns-analysis/naver_blog/

# 로그 제외하고 동기화
rsync -avz --progress --exclude="*.log" --exclude="logs/" \
    crawler:~/PMIK-sns-analysis/naver_blog/ \
    ~/Documents/IT/PMIK-sns-analysis/naver_blog/

# 시뮬레이션 (실제 복사 안함)
rsync -avz --progress --dry-run \
    crawler:~/PMIK-sns-analysis/instagram/ \
    ~/Documents/IT/PMIK-sns-analysis/instagram/
```

#### 장단점
✅ **장점**:
- 중단된 전송 재개 가능
- 진행률 표시
- 변경된 파일만 전송 (효율적)
- 대용량 파일에 적합

❌ **단점**:
- SCP보다 약간 복잡한 문법

---

### 방법 3: 자동 동기화 스크립트 ⭐⭐⭐

**이미 생성한 스크립트 사용**:

```bash
# 스크립트 실행 (최초 1회)
cd ~/Documents/IT/PMIK-sns-analysis
chmod +x sync_from_vm.sh

# 동기화 실행
./sync_from_vm.sh
```

**스크립트 기능**:
- ✅ Instagram, Kakaostory, Naver Blog, YouTube 자동 동기화
- ✅ 진행률 표시
- ✅ 폴더 자동 생성
- ✅ 오류 처리
- ✅ 다운로드 파일 목록 출력

**스크립트 커스터마이징**:
```bash
# 스크립트 편집
nano ~/Documents/IT/PMIK-sns-analysis/sync_from_vm.sh

# FOLDERS 배열 수정
FOLDERS=("instagram" "kakaostory" "naver_blog" "youtube" "analysis")
```

---

### 방법 4: Git 버전 관리 (협업 최적) ⭐⭐⭐

#### 최초 설정 (VM에서)
```bash
# VM에 접속
ssh crawler

# Git 저장소 초기화
cd ~/PMIK-sns-analysis
git init

# .gitignore 생성 (대용량 파일 제외)
cat > .gitignore << 'EOF'
*.csv
*.json
*.log
*.xlsx
logs/
.venv/
__pycache__/
.DS_Store
EOF

# 파일 추가 및 커밋
git add .
git commit -m "Initial commit: Instagram and Kakaostory crawlers"

# 브랜치 생성 (선택)
git branch -M main
```

#### 로컬에서 Clone
```bash
# 방법 1: SSH를 통한 직접 clone
git clone crawler:~/PMIK-sns-analysis ~/Documents/IT/PMIK-sns-analysis/vm-repo

# 방법 2: GitHub/GitLab 사용 (권장)
# VM에서 GitHub에 push 후 로컬에서 clone
git clone https://github.com/your-org/PMIK-sns-analysis.git
```

#### 업데이트 받기
```bash
# 로컬에서
cd ~/Documents/IT/PMIK-sns-analysis/vm-repo
git pull

# 또는 특정 파일만
git checkout main -- instagram/insta_crawl.py
```

#### 장단점
✅ **장점**:
- 버전 관리 (변경 이력 추적)
- 협업 용이
- 코드 리뷰 가능
- 충돌 방지

❌ **단점**:
- 초기 설정 필요
- Git 사용법 학습 필요
- 대용량 파일 관리 어려움 (Git LFS 필요)

---

## 🎯 상황별 권장 방법

### 1회성 파일 다운로드
```bash
# SCP 사용
scp crawler:~/PMIK-sns-analysis/instagram/insta_crawl.py ./
```
**권장**: SCP

### 정기적 동기화
```bash
# Rsync 또는 자동화 스크립트
./sync_from_vm.sh
```
**권장**: Rsync 또는 스크립트

### 팀 협업
```bash
# Git 사용
git pull
```
**권장**: Git

### 대용량 데이터
```bash
# Rsync with progress
rsync -avz --progress crawler:~/large_file.csv ./
```
**권장**: Rsync

---

## 📊 실전 예제

### 예제 1: Instagram 크롤러만 다운로드

```bash
# SCP로 간단하게
scp -r crawler:~/PMIK-sns-analysis/instagram ~/Documents/IT/PMIK-sns-analysis/

# 또는 Rsync로
rsync -avz --progress \
    crawler:~/PMIK-sns-analysis/instagram/ \
    ~/Documents/IT/PMIK-sns-analysis/instagram/
```

### 예제 2: Kakaostory 데이터만 다운로드

```bash
# 18MB JSON 파일
rsync -avz --progress \
    crawler:~/PMIK-sns-analysis/kakaostory/kakaostory_posts.json \
    ~/Documents/IT/PMIK-sns-analysis/kakaostory/
```

### 예제 3: Python 파일만 선택적 다운로드

```bash
# Python 파일만
rsync -avz --progress \
    --include="*.py" \
    --exclude="*" \
    crawler:~/PMIK-sns-analysis/instagram/ \
    ~/Documents/IT/PMIK-sns-analysis/instagram/
```

### 예제 4: 최신 변경사항만 동기화

```bash
# 변경된 파일만 전송 (효율적)
rsync -avz --progress \
    --update \
    crawler:~/PMIK-sns-analysis/ \
    ~/Documents/IT/PMIK-sns-analysis/vm-backup/
```

---

## 🔄 역방향: 로컬 → VM 업로드

### 로컬에서 VM으로 파일 전송

```bash
# SCP로 업로드
scp local_file.py crawler:~/PMIK-sns-analysis/instagram/

# Rsync로 업로드
rsync -avz --progress \
    ~/Documents/IT/PMIK-sns-analysis/instagram/ \
    crawler:~/PMIK-sns-analysis/instagram/
```

---

## 🛠️ 트러블슈팅

### 문제 1: Permission Denied

```bash
# 원인: SSH 키 권한 문제
# 해결:
chmod 600 ~/.ssh/azure_vm_key
ssh-add ~/.ssh/azure_vm_key
```

### 문제 2: No such file or directory

```bash
# 원인: 원격 경로가 잘못됨
# 해결: SSH로 경로 확인
ssh crawler "ls -la ~/PMIK-sns-analysis/instagram/"
```

### 문제 3: Connection timeout

```bash
# 원인: ACL 제한 (회사 네트워크 외부)
# 해결: VPN 연결 후 재시도
```

### 문제 4: Transfer interrupted

```bash
# 원인: 네트워크 불안정
# 해결: Rsync 사용 (자동 재개)
rsync -avz --progress --partial \
    crawler:~/large_file.csv ./
```

---

## 📋 체크리스트

### 다운로드 전
- [ ] SSH 접속 가능 확인 (`ssh crawler`)
- [ ] 원격 파일 존재 확인 (`ssh crawler "ls -la ~/경로"`)
- [ ] 로컬 저장 공간 확인 (`df -h`)
- [ ] VPN 연결 확인 (필요시)

### 다운로드 후
- [ ] 파일 크기 확인 (`ls -lh`)
- [ ] 파일 내용 확인 (코드 열어보기)
- [ ] 의존성 확인 (requirements.txt 등)
- [ ] 실행 테스트

---

## 🎓 유용한 명령어 모음

### 파일 크기 확인
```bash
# VM에서 폴더 크기 확인
ssh crawler "du -sh ~/PMIK-sns-analysis/*"

# 용량이 큰 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -type f -size +10M"
```

### 최근 수정된 파일 찾기
```bash
# 최근 7일 이내 수정된 파일
ssh crawler "find ~/PMIK-sns-analysis -type f -mtime -7"

# 오늘 수정된 Python 파일
ssh crawler "find ~/PMIK-sns-analysis -name '*.py' -mtime 0"
```

### 파일 비교
```bash
# 로컬과 VM 파일 비교
diff <(cat local_file.py) <(ssh crawler "cat ~/PMIK-sns-analysis/instagram/insta_crawl.py")

# 또는 rsync dry-run으로 차이 확인
rsync -avz --progress --dry-run \
    crawler:~/PMIK-sns-analysis/instagram/ \
    ~/Documents/IT/PMIK-sns-analysis/instagram/
```

---

## 🚀 자동화 팁

### Cron으로 자동 동기화

```bash
# crontab 편집
crontab -e

# 매일 오후 6시에 자동 동기화
0 18 * * * /Users/kimble/Documents/IT/PMIK-sns-analysis/sync_from_vm.sh >> ~/vm_sync.log 2>&1

# 매시간 동기화
0 * * * * /Users/kimble/Documents/IT/PMIK-sns-analysis/sync_from_vm.sh >> ~/vm_sync.log 2>&1
```

### Automator로 GUI 버튼 만들기

1. Automator 실행
2. "Application" 선택
3. "Run Shell Script" 추가
4. 스크립트 입력: `/Users/kimble/Documents/IT/PMIK-sns-analysis/sync_from_vm.sh`
5. 저장: "VM Sync.app"
6. Dock에 추가하여 클릭만으로 동기화

---

## 📞 빠른 참조

### 가장 많이 쓰는 명령어

```bash
# 1. 파일 1개 다운로드
scp crawler:~/path/file.py ./

# 2. 폴더 전체 다운로드
scp -r crawler:~/folder ./

# 3. 동기화 (권장)
rsync -avz --progress crawler:~/folder/ ./folder/

# 4. 자동 스크립트
./sync_from_vm.sh

# 5. Git 업데이트
git pull
```

---

**작성일**: 2025년 11월 21일  
**작성자**: PMI Korea 데이터 분석팀  
**버전**: 1.0
