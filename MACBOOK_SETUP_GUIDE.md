# MacBook 이전 및 설정 가이드

> Windows PC에서 MacBook M2로 크롤링 작업을 이전하는 완벽 가이드

## 📋 개요

이 가이드는 현재 Windows PC에서 실행 중인 네이버 블로그 크롤링 작업을 MacBook M2로 이전하는 방법을 설명합니다.

### 예상 성능 향상

| 항목 | Windows PC | MacBook M2 (v6.0) | 개선율 |
|------|------------|-------------------|--------|
| **처리 시간** | 22-31시간 | 6-8시간 | **70-75% 단축** |
| **처리 속도** | 6.15초/개 | 1.54초/개 | 4배 향상 |
| **발열** | 높음 | 거의 없음 | 팬리스 |
| **전력 소비** | 중간 | 매우 낮음 | 배터리 작업 가능 |

---

## 🚀 Step 1: Windows PC에서 Git 저장소 생성

### 1-1. Git 설치 확인

PowerShell에서 실행:

```powershell
git --version
```

설치되지 않았다면:
- [Git for Windows](https://git-scm.com/download/win) 다운로드 및 설치

### 1-2. Git 초기 설정

```powershell
# 사용자 정보 설정
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 기본 브랜치 이름 설정
git config --global init.defaultBranch main
```

### 1-3. 프로젝트 폴더로 이동

```powershell
cd C:\Users\PC\Desktop\IT
```

### 1-4. Git 저장소 초기화

```powershell
# Git 저장소 초기화
git init

# 현재 상태 확인
git status
```

### 1-5. 불필요한 파일 정리

다음 파일/폴더는 Git에 포함하지 않습니다 (`.gitignore`에 자동 추가됨):

```
✅ 포함할 파일:
- *.py (크롤러 코드)
- *.md (문서)
- requirements*.txt
- config.example.py
- .env.example

❌ 제외할 파일:
- config.py (API 키 포함)
- .env (API 키 포함)
- output/*.csv, *.json (크롤링 결과)
- __pycache__/
- .venv/
```

### 1-6. 파일 추가 및 커밋

```powershell
# 모든 파일 추가 (.gitignore 규칙 적용)
git add .

# 커밋
git commit -m "Initial commit: Naver Blog Crawler v6.0"

# 커밋 확인
git log --oneline
```

---

## 🌐 Step 2: GitHub에 업로드

### 2-1. GitHub 저장소 생성

1. [GitHub](https://github.com) 로그인
2. 우측 상단 `+` → `New repository` 클릭
3. 저장소 설정:
   - **Repository name**: `pm-korea-sns-analysis` (또는 원하는 이름)
   - **Description**: `PM-International Korea SNS 데이터 수집 및 분석`
   - **Visibility**: 
     - `Private` (회사 내부용 - 권장)
     - `Public` (포트폴리오용)
   - **Initialize**: 체크 안 함 (이미 로컬에 있음)
4. `Create repository` 클릭

### 2-2. 로컬 저장소와 연결

GitHub에서 제공하는 명령어 복사 후 실행:

```powershell
# 원격 저장소 추가
git remote add origin https://github.com/YOUR_USERNAME/pm-korea-sns-analysis.git

# 원격 저장소 확인
git remote -v

# 푸시
git branch -M main
git push -u origin main
```

### 2-3. 업로드 확인

브라우저에서 GitHub 저장소 페이지 새로고침하여 파일 업로드 확인

---

## 💻 Step 3: MacBook에서 설정

### 3-1. Homebrew 설치

터미널 열기 (`Command + Space` → "Terminal" 입력):

```bash
# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 설치 확인
brew --version
```

### 3-2. 필수 프로그램 설치

```bash
# Python 3.11 설치
brew install python@3.11

# Python 버전 확인
python3 --version

# Google Chrome 설치
brew install --cask google-chrome

# ChromeDriver 설치
brew install chromedriver

# ChromeDriver 권한 설정 (중요!)
xattr -d com.apple.quarantine $(which chromedriver)
```

### 3-3. Git 설정

```bash
# Git 설치 확인 (macOS에 기본 설치됨)
git --version

# 사용자 정보 설정 (Windows와 동일하게)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3-4. 프로젝트 클론

```bash
# 작업 디렉토리로 이동
cd ~/Desktop

# GitHub에서 클론
git clone https://github.com/YOUR_USERNAME/pm-korea-sns-analysis.git

# 프로젝트 폴더로 이동
cd pm-korea-sns-analysis/naver_blog
```

### 3-5. Python 의존성 설치

```bash
# 의존성 설치
pip3 install -r requirements_v5.txt

# 설치 확인
pip3 list | grep selenium
pip3 list | grep pandas
```

### 3-6. API 키 설정

```bash
# config.py 파일 생성
cp config.example.py config.py

# 파일 편집 (nano 또는 원하는 에디터 사용)
nano config.py
```

`config.py` 내용:
```python
NAVER_CLIENT_ID = 'your_actual_client_id'
NAVER_CLIENT_SECRET = 'your_actual_client_secret'
```

저장: `Control + O` → `Enter` → `Control + X`

---

## 🎯 Step 4: 크롤링 실행

### 4-1. 테스트 실행

```bash
# v6.0 실행 (병렬 처리)
python3 naver_blog_crawler_v6.py
```

### 4-2. 백그라운드 실행 (장시간 작업)

```bash
# nohup으로 백그라운드 실행
nohup python3 naver_blog_crawler_v6.py > crawler.log 2>&1 &

# 프로세스 ID 확인
echo $!

# 실시간 로그 확인
tail -f crawler.log

# 로그 확인 중단: Control + C
```

### 4-3. 진행 상황 모니터링

```bash
# 로그 파일 확인
tail -n 50 crawler.log

# 프로세스 확인
ps aux | grep python

# 시스템 리소스 확인
top
# 종료: q
```

### 4-4. 완료 후 결과 확인

```bash
# 출력 파일 확인
ls -lh output/

# CSV 파일 미리보기
head -n 5 output/naver_blog_crawl_*.csv
```

---

## 📊 성능 최적화 팁

### MacBook M2 최적화 설정

`naver_blog_crawler_v6.py` 파일에서 워커 수 조정:

```python
# 기본값 (권장)
NUM_WORKERS = 4

# 더 빠르게 (메모리 여유 있을 때)
NUM_WORKERS = 6

# 안정적으로 (메모리 부족 시)
NUM_WORKERS = 2
```

### 메모리 사용량 확인

```bash
# 활동 모니터 실행
open -a "Activity Monitor"

# 또는 터미널에서
vm_stat | head -n 10
```

---

## 🔧 트러블슈팅

### 문제 1: ChromeDriver 권한 오류

```
Error: "chromedriver" cannot be opened because the developer cannot be verified
```

**해결:**
```bash
xattr -d com.apple.quarantine $(which chromedriver)
```

### 문제 2: SSL 인증서 오류

```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**해결:**
```bash
# Python 인증서 설치
/Applications/Python\ 3.11/Install\ Certificates.command
```

### 문제 3: 메모리 부족

```
Error: MemoryError
```

**해결:**
```python
# v6.0 파일에서 워커 수 줄이기
NUM_WORKERS = 2
```

### 문제 4: API 키 오류

```
Error: ❌ Naver API 키를 찾을 수 없습니다!
```

**해결:**
```bash
# config.py 파일 확인
cat config.py

# 파일이 없으면 생성
cp config.example.py config.py
nano config.py
```

---

## 📈 예상 타임라인

| 단계 | 예상 시간 |
|------|----------|
| Git 저장소 생성 및 업로드 | 10-15분 |
| MacBook 환경 설정 | 20-30분 |
| 프로젝트 클론 및 의존성 설치 | 10-15분 |
| **총 준비 시간** | **40-60분** |
| **크롤링 실행 시간 (v6.0)** | **6-8시간** |

---

## ✅ 체크리스트

### Windows PC (출발지)
- [ ] Git 설치 및 설정
- [ ] 불필요한 파일 정리
- [ ] Git 저장소 초기화
- [ ] GitHub에 업로드
- [ ] 업로드 확인

### MacBook (목적지)
- [ ] Homebrew 설치
- [ ] Python 3.11 설치
- [ ] Chrome & ChromeDriver 설치
- [ ] Git 클론
- [ ] 의존성 설치
- [ ] API 키 설정
- [ ] 테스트 실행

### 크롤링 실행
- [ ] v6.0 코드 실행
- [ ] 진행 상황 모니터링
- [ ] 결과 파일 확인
- [ ] GitHub에 결과 업로드 (선택)

---

## 🎓 추가 학습 자료

### Git 기본 명령어

```bash
# 상태 확인
git status

# 변경사항 확인
git diff

# 로그 확인
git log --oneline --graph

# 브랜치 생성
git checkout -b feature/new-feature

# 변경사항 푸시
git add .
git commit -m "Update: description"
git push origin main
```

### 유용한 macOS 단축키

- `Command + Space`: Spotlight (프로그램 실행)
- `Command + Tab`: 앱 전환
- `Command + Q`: 앱 종료
- `Control + C`: 터미널 명령 중단

---

## 📞 도움이 필요하신가요?

### 일반적인 질문
- README.md 참조
- GitHub Issues 활용

### 긴급 문의
- 데이터 팀 연락

---

**작성일**: 2025-11-02  
**버전**: 1.0  
**대상**: MacBook M2 사용자
