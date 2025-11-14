# 크롤러 확실하게 실행하고 맥북 끄기 가이드

## 🎯 목표
맥북을 끄고 가도 CRAWLER VM에서 크롤러가 계속 실행되도록 설정

---

## 📋 사전 준비 체크리스트

### 1. 환경변수 파일 확인
```bash
ssh crawler
cd ~/PMIK-sns-analysis/naver_blog
cat .env

# 다음 항목이 있어야 함:
# NAVER_CLIENT_ID=your_client_id
# NAVER_CLIENT_SECRET=your_client_secret
```

### 2. 가상환경 확인
```bash
cd ~/PMIK-sns-analysis
source .venv/bin/activate
python --version  # Python 3.10 이상
pip list | grep selenium  # selenium 설치 확인
```

### 3. 크롤러 파일 확인
```bash
ls -lh ~/PMIK-sns-analysis/naver_blog/pm_naver_blog_crawler_v8_4_final.py
```

---

## 🚀 단계별 실행 가이드

### Step 1: 기존 Screen 세션 정리

```bash
# VM 접속
ssh crawler

# 기존 Screen 세션 확인
screen -ls

# 출력 예시:
# 196510.kimble_crawler   (Attached)
# 193920.kimble_crawler   (Detached)

# 오래된 세션 종료 (필요시)
screen -S 193920 -X quit  # 세션 ID로 종료
```

### Step 2: 새로운 Screen 세션 시작

```bash
# 타임스탬프 포함한 세션명으로 시작
screen -S kimble_crawler_$(date +%Y%m%d)

# 예: kimble_crawler_20251114
```

### Step 3: 크롤러 실행 (로그 포함)

```bash
# 프로젝트 디렉토리로 이동
cd ~/PMIK-sns-analysis/naver_blog

# 가상환경 활성화
source ../.venv/bin/activate

# 로그 디렉토리 생성
mkdir -p ~/logs

# 크롤러 실행 (로그 파일에 출력 저장)
python pm_naver_blog_crawler_v8_4_final.py 2>&1 | tee ~/logs/crawler_$(date +%Y%m%d_%H%M%S).log
```

**명령어 설명:**
- `2>&1`: 에러 메시지도 함께 출력
- `| tee`: 화면에도 보이고 파일에도 저장
- `~/logs/crawler_20251114_155630.log`: 로그 파일 경로

### Step 4: 크롤러 실행 확인

```bash
# 다른 터미널 창을 열어서 (맥북에서)
ssh crawler

# 실행 중인 프로세스 확인
ps aux | grep pm_naver_blog_crawler

# 출력 예시:
# pmi  12345  50.2  2.1  ... python pm_naver_blog_crawler_v8_4_final.py
```

### Step 5: Screen에서 나가기 (Detach)

```bash
# Screen 세션 내에서 (크롤러가 실행 중인 터미널)
Ctrl + A, D

# 메시지 확인:
# [detached from 196510.kimble_crawler_20251114]
```

### Step 6: 크롤러 계속 실행 확인

```bash
# Screen 세션 목록 확인
screen -ls

# 출력:
# 196510.kimble_crawler_20251114   (Detached)  ← Detached 상태!

# 프로세스 확인
ps aux | grep pm_naver_blog_crawler

# 로그 파일 확인 (실시간)
tail -f ~/logs/crawler_*.log
```

### Step 7: SSH 종료 및 맥북 끄기

```bash
# SSH 종료
exit

# 맥북 종료 가능! ✅
```

---

## 🔍 나중에 다시 확인하는 방법

### 1. VM 재접속
```bash
ssh crawler
```

### 2. Screen 세션 재접속
```bash
# Screen 목록 확인
screen -ls

# 재접속
screen -r kimble_crawler_20251114

# 또는 세션 ID로
screen -r 196510
```

### 3. 로그 파일 확인
```bash
# 최신 로그 파일 찾기
ls -lht ~/logs/crawler_*.log | head -5

# 로그 내용 확인
tail -100 ~/logs/crawler_20251114_155630.log

# 실시간 로그 확인
tail -f ~/logs/crawler_20251114_155630.log
```

### 4. 크롤링 결과 확인
```bash
# CSV 파일 찾기
find ~/PMIK-sns-analysis/naver_blog -name "*.csv" -mtime -1

# 또는
ls -lht ~/shared_data/raw_data/naver_blog/*.csv
```

---

## ⚠️ 문제 해결

### 문제 1: 크롤러가 바로 종료됨

**원인:** 환경변수 누락, 의존성 문제

**해결:**
```bash
# 환경변수 확인
cat ~/PMIK-sns-analysis/naver_blog/.env

# 의존성 재설치
cd ~/PMIK-sns-analysis
source .venv/bin/activate
pip install -r requirements.txt
```

### 문제 2: Screen 세션이 사라짐

**원인:** VM 재부팅, 수동 종료

**확인:**
```bash
# VM 가동 시간 확인
uptime

# Screen 세션 확인
screen -ls
```

### 문제 3: 로그 파일이 생성 안 됨

**원인:** 디렉토리 권한, 경로 오류

**해결:**
```bash
# 로그 디렉토리 생성 및 권한 확인
mkdir -p ~/logs
ls -ld ~/logs

# 수동으로 로그 파일 생성 테스트
echo "test" > ~/logs/test.log
cat ~/logs/test.log
```

### 문제 4: ChromeDriver 에러

**원인:** 이전에 수정한 코드가 반영 안 됨

**해결:**
```bash
# 최신 코드 받기
cd ~/PMIK-sns-analysis
git pull

# 크롤러 파일 확인
grep "remote-debugging-port" ~/PMIK-sns-analysis/naver_blog/pm_naver_blog_crawler_v8_4_final.py
```

---

## 📊 실행 상태 모니터링

### 실시간 모니터링 스크립트

```bash
# monitor_crawler.sh 생성
cat > ~/monitor_crawler.sh << 'EOF'
#!/bin/bash

echo "=== Screen 세션 ==="
screen -ls

echo ""
echo "=== 크롤러 프로세스 ==="
ps aux | grep pm_naver_blog_crawler | grep -v grep

echo ""
echo "=== 최신 로그 (마지막 10줄) ==="
tail -10 ~/logs/crawler_*.log 2>/dev/null | tail -10

echo ""
echo "=== CPU/메모리 사용량 ==="
top -b -n 1 | head -20
EOF

chmod +x ~/monitor_crawler.sh

# 실행
~/monitor_crawler.sh
```

### Cron으로 자동 모니터링

```bash
# 10분마다 상태 체크
crontab -e

# 추가:
*/10 * * * * ~/monitor_crawler.sh >> ~/logs/monitor.log 2>&1
```

---

## 🎯 완벽한 실행 체크리스트

실행 전 체크:
- [ ] `.env` 파일 확인
- [ ] 가상환경 활성화 확인
- [ ] 이전 Screen 세션 정리
- [ ] 로그 디렉토리 생성

실행 중 체크:
- [ ] Screen 세션 시작
- [ ] 크롤러 실행 (로그 포함)
- [ ] 프로세스 실행 확인
- [ ] 로그 파일 생성 확인

실행 후 체크:
- [ ] Screen Detach
- [ ] 프로세스 계속 실행 확인
- [ ] SSH 종료
- [ ] 맥북 종료 가능!

재접속 시 체크:
- [ ] Screen 세션 존재 확인
- [ ] 프로세스 실행 중 확인
- [ ] 로그 파일 확인
- [ ] 결과 파일 확인

---

## 💡 추가 팁

### 1. 여러 크롤러 동시 실행

```bash
# 네이버 블로그
screen -S kimble_naver
python pm_naver_blog_crawler_v8_4_final.py
Ctrl + A, D

# 유튜브
screen -S kimble_youtube
python youtube_crawler_v2.py
Ctrl + A, D

# 세션 목록
screen -ls
```

### 2. Screen 세션 간 전환

```bash
# 세션 목록
screen -ls

# 특정 세션으로 전환
screen -r kimble_naver

# Detach 후 다른 세션으로
Ctrl + A, D
screen -r kimble_youtube
```

### 3. 로그 파일 자동 정리

```bash
# 7일 이상된 로그 삭제
find ~/logs -name "*.log" -mtime +7 -delete

# Cron 등록
0 0 * * * find ~/logs -name "*.log" -mtime +7 -delete
```

---

## 📞 긴급 상황 대응

### 크롤러 강제 종료

```bash
# 프로세스 ID 확인
ps aux | grep pm_naver_blog_crawler

# 종료
kill -9 [PID]

# 또는 Screen 세션 종료
screen -S kimble_crawler_20251114 -X quit
```

### VM 재부팅 시

```bash
# Screen 세션은 사라짐!
# 다시 시작 필요

ssh crawler
screen -S kimble_crawler_new
cd ~/PMIK-sns-analysis/naver_blog
source ../.venv/bin/activate
python pm_naver_blog_crawler_v8_4_final.py 2>&1 | tee ~/logs/crawler_$(date +%Y%m%d_%H%M%S).log
```

---

## 🎓 Screen 단축키 모음

| 단축키 | 기능 |
|--------|------|
| `Ctrl + A, D` | Detach (나가기) |
| `Ctrl + A, K` | 세션 종료 |
| `Ctrl + A, C` | 새 창 생성 |
| `Ctrl + A, N` | 다음 창 |
| `Ctrl + A, P` | 이전 창 |
| `Ctrl + A, "` | 창 목록 |
| `Ctrl + A, ?` | 도움말 |

---

## ✅ 최종 확인

맥북을 끄기 전 마지막 확인:

```bash
# 1. Screen 세션 Detached 상태
screen -ls
# → kimble_crawler_20251114 (Detached)

# 2. 프로세스 실행 중
ps aux | grep pm_naver_blog_crawler
# → python pm_naver_blog_crawler_v8_4_final.py

# 3. 로그 파일 생성 중
ls -lh ~/logs/crawler_*.log
# → 파일 크기가 계속 증가

# 모두 확인되면 맥북 종료 OK! ✅
```
