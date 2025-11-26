# VM에서 크롤러 실행 가이드

## 📋 준비사항

### 1. 로컬에서 파일 전송

**방법 1: Git 사용 (추천)**
```bash
# 로컬 Mac에서
cd ~/Documents/IT/PMIK-sns-analysis
git add naver_blog/pm_naver_blog_crawler_v9_1_final.py
git add naver_blog/config.yaml
git commit -m "Add v9.1 final version for full crawling"
git push origin main

# VM에서
cd ~/PMIK-sns-analysis
git pull origin main
```

**방법 2: SCP 직접 전송**
```bash
# 로컬 Mac에서
cd ~/Documents/IT/PMIK-sns-analysis/naver_blog
scp pm_naver_blog_crawler_v9_1_final.py config.yaml pmi@PMIKR-DATA-CRAWLER:~/PMIK-sns-analysis/naver_blog/
```

---

## 🚀 VM에서 실행

### 1. SSH 접속
```bash
ssh pmi@PMIKR-DATA-CRAWLER
```

### 2. 디렉토리 이동 및 가상환경 활성화
```bash
cd ~/PMIK-sns-analysis/naver_blog
source ../.venv/bin/activate
```

### 3. 필요한 패키지 설치
```bash
pip install pyyaml
```

### 4. 파일 확인
```bash
ls -lh pm_naver_blog_crawler_v9_1_final.py config.yaml
head -20 config.yaml
```

---

## 🔄 백그라운드 실행 (로컬 컴퓨터 종료해도 계속 실행)

### 방법 1: nohup 사용 (추천 ⭐⭐⭐⭐⭐)

```bash
# 백그라운드 실행
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &

# 프로세스 ID 확인
echo $!

# 실시간 로그 확인
tail -f crawler.log

# Ctrl+C로 로그 보기 중단 (크롤러는 계속 실행됨)
```

**장점:**
- 간단하고 빠름
- SSH 연결 끊어도 계속 실행
- 로그 파일로 진행 상황 확인 가능

**프로세스 확인:**
```bash
# 실행 중인지 확인
ps aux | grep pm_naver_blog_crawler_v9_1_final

# CPU/메모리 사용량 확인
top -p $(pgrep -f pm_naver_blog_crawler_v9_1_final)
```

**프로세스 종료:**
```bash
# 프로세스 ID로 종료
kill <PID>

# 또는 이름으로 종료
pkill -f pm_naver_blog_crawler_v9_1_final
```

---

### 방법 2: screen 사용 (고급)

```bash
# screen 설치 (없는 경우)
sudo apt-get install screen

# screen 세션 시작
screen -S crawler

# 크롤러 실행
python pm_naver_blog_crawler_v9_1_final.py

# Ctrl+A, D 로 세션에서 빠져나오기 (크롤러는 계속 실행)

# 세션 목록 확인
screen -ls

# 세션 다시 접속
screen -r crawler

# 세션 종료 (크롤러도 종료)
# 세션 안에서: Ctrl+D 또는 exit
```

**장점:**
- 실시간 출력 확인 가능
- 언제든 다시 접속 가능
- 여러 세션 관리 가능

---

### 방법 3: tmux 사용 (최신)

```bash
# tmux 설치 (없는 경우)
sudo apt-get install tmux

# tmux 세션 시작
tmux new -s crawler

# 크롤러 실행
python pm_naver_blog_crawler_v9_1_final.py

# Ctrl+B, D 로 세션에서 빠져나오기

# 세션 목록 확인
tmux ls

# 세션 다시 접속
tmux attach -t crawler

# 세션 종료
# 세션 안에서: Ctrl+D 또는 exit
```

---

## 📊 진행 상황 확인

### 1. 로그 파일 확인
```bash
# 실시간 로그 (nohup 사용 시)
tail -f crawler.log

# 마지막 100줄
tail -100 crawler.log

# 특정 키워드 검색
grep "수집 완료" crawler.log | wc -l
grep "체크포인트 저장" crawler.log
```

### 2. 수집된 파일 확인
```bash
# CSV 파일 목록
ls -lht naver_blog_pm_v9_1_final_*.csv

# 체크포인트 파일
ls -lht checkpoints/

# 파일 크기 확인
du -h naver_blog_pm_v9_1_final_*.csv
```

### 3. 수집 개수 확인
```bash
# CSV 파일 라인 수 (헤더 제외)
wc -l naver_blog_pm_v9_1_final_*.csv

# 또는
tail -1 naver_blog_pm_v9_1_final_*.csv | wc -l
```

---

## 💾 데이터 안전성

### VM 종료 시 데이터 유지 여부

**✅ 유지되는 것:**
1. **수집된 CSV 파일** - 디스크에 저장됨
2. **체크포인트 파일** - `checkpoints/` 디렉토리에 저장
3. **실패 URL 로그** - `failed_urls.json`에 저장
4. **로그 파일** - `crawler.log`에 저장

**❌ 유지되지 않는 것:**
1. **메모리 상의 데이터** - 체크포인트 저장 전 데이터
2. **실행 중인 프로세스** - VM 재시작 시 자동 재시작 안 됨

### 안전한 중단 방법

```bash
# 1. 현재 진행 상황 확인
tail -50 crawler.log

# 2. 프로세스 정상 종료 (SIGTERM)
kill <PID>

# 3. 강제 종료는 피하기 (데이터 손실 가능)
# kill -9 <PID>  # 사용 금지!

# 4. 종료 확인
ps aux | grep pm_naver_blog_crawler_v9_1_final
```

### 재시작 방법

```bash
# 1. 이전 체크포인트 확인
ls -lht checkpoints/

# 2. 크롤러 재시작 (자동으로 이전 데이터 로드)
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &

# 3. 로그 확인
tail -f crawler.log
# "📂 이전 데이터 로드: XXX개" 메시지 확인
```

---

## ⏱️ 예상 실행 시간

### 키워드별 예상 시간
- **키워드당 1000개 수집**: 약 2-3시간
- **총 11개 키워드**: 약 22-33시간
- **체크포인트 저장**: 1시간마다 자동

### 실행 시간 단축 팁
1. **VM 성능 확인**: CPU/메모리 충분한지 확인
2. **네트워크 안정성**: 안정적인 네트워크 환경
3. **시간대 선택**: 트래픽 적은 시간대 (새벽)

---

## 🔧 문제 해결

### 1. "설정 파일을 찾을 수 없습니다"
```bash
# config.yaml 확인
ls -l config.yaml
pwd  # 현재 디렉토리 확인
```

### 2. "No module named 'yaml'"
```bash
pip install pyyaml
```

### 3. Chrome/Selenium 오류
```bash
# Chrome 설치 확인
google-chrome --version

# ChromeDriver 자동 설치 (webdriver-manager)
pip install webdriver-manager
```

### 4. 메모리 부족
```bash
# 메모리 사용량 확인
free -h

# 스왑 메모리 확인
swapon --show

# 크롤러 재시작 (메모리 정리)
pkill -f pm_naver_blog_crawler_v9_1_final
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &
```

### 5. 디스크 공간 부족
```bash
# 디스크 사용량 확인
df -h

# 불필요한 파일 삭제
rm -rf checkpoints/checkpoint_202511*.csv  # 오래된 체크포인트
```

---

## 📱 원격 모니터링

### 1. SSH 접속 유지
```bash
# 로컬 Mac에서 주기적으로 확인
ssh pmi@PMIKR-DATA-CRAWLER "tail -20 ~/PMIK-sns-analysis/naver_blog/crawler.log"
```

### 2. 이메일 알림 (선택)
```bash
# 크롤링 완료 시 이메일 발송
python pm_naver_blog_crawler_v9_1_final.py && echo "크롤링 완료" | mail -s "PM 크롤러 완료" your@email.com
```

### 3. 슬랙/텔레그램 알림 (고급)
- 별도 스크립트 작성 필요

---

## ✅ 체크리스트

**실행 전:**
- [ ] config.yaml 파일 확인 (test_mode: false)
- [ ] 가상환경 활성화
- [ ] PyYAML 설치
- [ ] 디스크 공간 확인 (최소 10GB)

**실행 중:**
- [ ] nohup 또는 screen으로 백그라운드 실행
- [ ] 로그 파일 주기적 확인
- [ ] 체크포인트 파일 생성 확인 (1시간마다)

**실행 후:**
- [ ] CSV 파일 다운로드
- [ ] 데이터 품질 확인
- [ ] 후원번호 패턴 분석 확인

---

## 📞 문의

문제 발생 시:
1. 로그 파일 확인: `tail -100 crawler.log`
2. 에러 메시지 복사
3. 팀에 공유

**작성자**: PMI Korea 데이터 분석팀  
**버전**: 9.1.0 Final  
**날짜**: 2025-11-17
