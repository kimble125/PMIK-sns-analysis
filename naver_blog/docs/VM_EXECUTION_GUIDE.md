# VM에서 크롤러 백그라운드 실행 가이드

## 🎯 목표
crawler VM에서 크롤러를 실행하고, 로컬 노트북을 꺼도 계속 작동하도록 설정합니다.

---

## 📋 사전 준비

### 1. 필요한 정보
- **VM 접속 명령어**: `ssh crawler`
- **크롤러 경로**: `/home/사용자명/PMIK-sns-analysis/naver_blog/`
- **Python 환경**: Python 3.8 이상

### 2. 로컬에서 파일 업로드 준비
```bash
# 로컬 터미널에서 (맥북)
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
```

---

## 🚀 단계별 실행 가이드

### Step 1: VM에 파일 업로드

#### 방법 A: SCP로 파일 전송 (권장)
```bash
# 로컬 터미널에서 실행
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog

# 크롤러 파일 업로드
scp pm_naver_blog_crawler_v10_1_test.py crawler:~/PMIK-sns-analysis/naver_blog/

# 설정 파일 업로드
scp config.yaml crawler:~/PMIK-sns-analysis/naver_blog/

# 비디오 프로세서 업로드 (선택)
scp pm_video_processor_v1.py crawler:~/PMIK-sns-analysis/naver_blog/

# 문서 파일들 업로드 (선택)
scp V10_1_README.md crawler:~/PMIK-sns-analysis/naver_blog/
scp CONTENT_TYPE_CLASSIFICATION.md crawler:~/PMIK-sns-analysis/naver_blog/
scp TEST_RUN_GUIDE.md crawler:~/PMIK-sns-analysis/naver_blog/
```

#### 방법 B: Git 사용 (이미 Git 저장소인 경우)
```bash
# 로컬에서 커밋 & 푸시
cd /Users/kimble/Documents/IT/PMIK-sns-analysis
git add .
git commit -m "v10.1 크롤러 업데이트"
git push

# VM에서 풀
ssh crawler
cd ~/PMIK-sns-analysis
git pull
```

---

### Step 2: VM에 접속

```bash
# 로컬 터미널에서
ssh crawler
```

접속 성공 시:
```
Welcome to Ubuntu 20.04.x LTS
...
user@crawler:~$
```

---

### Step 3: 작업 디렉토리로 이동

```bash
cd ~/PMIK-sns-analysis/naver_blog
ls -la
```

다음 파일들이 있는지 확인:
- `pm_naver_blog_crawler_v10_1_test.py`
- `config.yaml`
- `config.py` (Naver API 키)

---

### Step 4: Python 환경 확인

```bash
# Python 버전 확인
python3 --version
# Python 3.8 이상이어야 함

# 필수 라이브러리 확인
python3 -c "import selenium, requests, pandas, yaml, bs4; print('✅ 기본 라이브러리 OK')"

# OCR 라이브러리 확인 (선택)
python3 -c "import easyocr, PIL; print('✅ OCR 라이브러리 OK')"
```

**라이브러리 없으면 설치**:
```bash
pip3 install selenium requests pandas pyyaml beautifulsoup4 webdriver-manager

# OCR 사용 시 (선택)
pip3 install easyocr Pillow
```

---

### Step 5: Screen 세션 시작

**Screen이란?**  
터미널 세션을 백그라운드로 유지하는 도구. SSH 연결이 끊겨도 프로세스가 계속 실행됩니다.

#### Screen 설치 확인
```bash
screen --version
```

없으면 설치:
```bash
sudo apt-get update
sudo apt-get install screen
```

#### Screen 세션 생성
```bash
# "crawler_v10" 이름으로 세션 생성
screen -S crawler_v10
```

새로운 화면이 나타나면 성공!

---

### Step 6: 크롤러 실행

Screen 세션 안에서:

```bash
# 작업 디렉토리 확인
pwd
# /home/사용자명/PMIK-sns-analysis/naver_blog

# 크롤러 실행
python3 pm_naver_blog_crawler_v10_1_test.py
```

**실행 확인**:
```
======================================================================
🚀 PM International 네이버 블로그 크롤러 v10.1 시작
🆕 v10.1 신기능:
   - 프로필 정보 수집
   - 이미지 OCR 처리 (EasyOCR)
   ...
🧪 테스트 모드: 120분 제한
======================================================================
📅 키워드 연도 확장 완료: 10개 → 30개
```

---

### Step 7: Screen 세션에서 나오기 (Detach)

크롤러가 실행 중인 상태에서:

**키보드 단축키**: `Ctrl + A`, 그 다음 `D`

1. `Ctrl` 키를 누른 채로 `A` 키 누르기
2. 손을 떼고 `D` 키 누르기

**성공 메시지**:
```
[detached from 12345.crawler_v10]
```

이제 원래 터미널로 돌아왔고, 크롤러는 백그라운드에서 계속 실행 중입니다!

---

### Step 8: SSH 연결 종료 (노트북 꺼도 OK)

```bash
exit
```

또는 터미널 창을 그냥 닫아도 됩니다.  
**크롤러는 VM에서 계속 실행됩니다!** ✅

---

## 🔍 실행 중 확인 방법

### 다시 VM에 접속
```bash
ssh crawler
```

### Screen 세션 목록 확인
```bash
screen -ls
```

출력 예시:
```
There is a screen on:
    12345.crawler_v10    (Detached)
1 Socket in /run/screen/S-user.
```

### Screen 세션에 다시 접속 (Reattach)
```bash
screen -r crawler_v10
```

크롤러 실행 화면이 다시 나타납니다!

### 로그 실시간 확인
```bash
# Screen 세션 안에서
# 로그가 계속 출력되는 것을 볼 수 있음
```

### 다시 나오기
`Ctrl + A`, 그 다음 `D`

---

## 📊 결과 파일 확인

### VM에서 파일 확인
```bash
cd ~/PMIK-sns-analysis/naver_blog
ls -lh *.csv *.txt *.json
```

생성된 파일:
- `naver_blog_pm_v10_1_test_YYYYMMDD_HHMMSS.csv` (데이터)
- `naver_blog_pm_v10_1_test_YYYYMMDD_HHMMSS_report.txt` (보고서)
- `vm_crawler_log.json` (VM 로그)
- `failed_urls.json` (실패 URL)

### 로컬로 다운로드
```bash
# 로컬 터미널에서
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog

# CSV 다운로드
scp 'crawler:~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v10_1_test_*.csv' .

# 보고서 다운로드
scp 'crawler:~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v10_1_test_*_report.txt' .

# 로그 다운로드
scp crawler:~/PMIK-sns-analysis/naver_blog/vm_crawler_log.json .
```

---

## ⚠️  중요 사항

### 1. Screen 세션 종료 방법

**크롤러를 중단하고 싶을 때**:
```bash
# Screen 세션에 접속
screen -r crawler_v10

# 크롤러 중단
Ctrl + C

# Screen 세션 종료
exit
```

### 2. 여러 Screen 세션 관리

```bash
# 모든 세션 보기
screen -ls

# 특정 세션에 접속
screen -r crawler_v10

# 세션이 여러 개일 때 ID로 접속
screen -r 12345
```

### 3. Screen 세션 강제 종료

```bash
# 세션 ID 확인
screen -ls

# 강제 종료
screen -X -S crawler_v10 quit
```

### 4. 디스크 공간 확인

```bash
# 디스크 사용량 확인
df -h

# 현재 디렉토리 크기
du -sh ~/PMIK-sns-analysis/naver_blog
```

---

## 🐛 트러블슈팅

### 문제 1: Screen 세션이 안 보임
```bash
screen -ls
# No Sockets found

# 해결: 새로 생성
screen -S crawler_v10
```

### 문제 2: "There is no screen to be resumed"
```bash
# 세션 이름 확인
screen -ls

# 정확한 이름으로 접속
screen -r [정확한_세션_이름]
```

### 문제 3: Python 라이브러리 없음
```bash
# 가상환경 사용 중이라면
source ~/venv/bin/activate

# 또는 전역 설치
pip3 install --user [라이브러리명]
```

### 문제 4: ChromeDriver 오류
```bash
# ChromeDriver 자동 설치 확인
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

### 문제 5: 메모리 부족
```bash
# 메모리 확인
free -h

# 크롤러 중단 후 재시작
screen -r crawler_v10
Ctrl + C
python3 pm_naver_blog_crawler_v10_1_test.py
```

---

## 📝 완전한 실행 체크리스트

### 로컬 (맥북)에서
- [ ] 1. 파일 수정 완료 확인
- [ ] 2. `scp`로 VM에 파일 업로드
- [ ] 3. `ssh crawler`로 VM 접속

### VM에서
- [ ] 4. 작업 디렉토리로 이동
- [ ] 5. Python 환경 확인
- [ ] 6. `screen -S crawler_v10` 실행
- [ ] 7. `python3 pm_naver_blog_crawler_v10_1_test.py` 실행
- [ ] 8. 크롤러 시작 확인
- [ ] 9. `Ctrl + A`, `D`로 Detach
- [ ] 10. `exit`로 SSH 종료

### 노트북
- [ ] 11. 노트북 종료해도 OK! ✅

### 2시간 후
- [ ] 12. `ssh crawler`로 재접속
- [ ] 13. 결과 파일 확인
- [ ] 14. `scp`로 로컬에 다운로드

---

## 🎯 예상 결과 (2시간 실행)

### 수집 예상치
- **키워드**: 30개 (10개 × 3년)
- **키워드당 목표**: 300개
- **이론적 최대**: 9,000개
- **현실적 예상**: 500~1,500개
  - 중복 제거
  - 필터링
  - 시간 제한

### 파일 크기
- **CSV**: 5~20MB
- **보고서**: 10~20KB
- **로그**: 5~10KB

---

## 💡 추가 팁

### tmux 사용 (Screen 대안)
```bash
# tmux 설치
sudo apt-get install tmux

# 세션 생성
tmux new -s crawler_v10

# Detach: Ctrl + B, 그 다음 D
# Reattach: tmux attach -t crawler_v10
```

### 로그 파일로 저장
```bash
# Screen 세션 안에서
python3 pm_naver_blog_crawler_v10_1_test.py 2>&1 | tee crawler_log.txt
```

### 자동 재시작 스크립트
```bash
# run_crawler.sh 생성
cat > run_crawler.sh << 'EOF'
#!/bin/bash
cd ~/PMIK-sns-analysis/naver_blog
python3 pm_naver_blog_crawler_v10_1_test.py
EOF

chmod +x run_crawler.sh

# Screen에서 실행
screen -S crawler_v10
./run_crawler.sh
```

---

**작성일**: 2025-11-19  
**버전**: v10.1  
**대상 VM**: crawler  
**실행 시간**: 2시간 (120분)  
**키워드당 목표**: 300개
