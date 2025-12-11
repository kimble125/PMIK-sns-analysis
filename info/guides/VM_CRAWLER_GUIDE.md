# VM에서 크롤러 실행 가이드

## 🚀 빠른 시작

### 1. VM 접속
```bash
ssh crawler
```

### 2. Screen 세션으로 크롤러 실행 (권장)

```bash
# Screen 세션 생성 (본인 이름으로)
screen -S kimble_crawler

# 프로젝트 디렉토리로 이동
cd ~/PMIK-sns-analysis/naver_blog

# 가상환경 활성화
source ../.venv/bin/activate

# 크롤러 실행
python pm_naver_blog_crawler_v8_4_final.py

# Screen에서 나가기 (크롤러는 백그라운드에서 계속 실행)
# Ctrl + A, 그 다음 D 키 누르기
```

### 3. 로컬 컴퓨터 종료
✅ **이제 로컬 Mac을 종료해도 크롤러가 계속 실행됩니다!**

### 4. 나중에 크롤러 상태 확인

```bash
# VM 재접속
ssh crawler

# Screen 세션 목록 확인
screen -ls

# Screen 세션에 재접속
screen -r kimble_crawler

# Screen에서 다시 나가기
# Ctrl + A, D
```

---

## 📋 Screen 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `screen -S 세션명` | 새 Screen 세션 생성 |
| `screen -ls` | Screen 세션 목록 보기 |
| `screen -r 세션명` | Screen 세션에 재접속 |
| `Ctrl + A, D` | Screen에서 나가기 (detach) |
| `Ctrl + A, K` | Screen 세션 종료 |
| `Ctrl + C` | 실행 중인 프로그램 종료 |

---

## 🔄 코드 업데이트 방법

로컬에서 코드를 수정한 후:

```bash
# 로컬에서
git add .
git commit -m "수정 내용"
git push origin main

# VM에서
ssh crawler
cd ~/PMIK-sns-analysis
git pull
```

---

## 📊 크롤러 로그 확인

```bash
# 실시간 로그 확인 (크롤러가 로그 파일을 생성하는 경우)
ssh crawler
cd ~/PMIK-sns-analysis/naver_blog
tail -f *.log

# 또는 Screen 세션에 접속해서 직접 확인
screen -r kimble_crawler
```

---

## ⚠️ 주의사항

### 동료와 함께 사용할 때

1. **Screen 세션 이름에 본인 이름 포함**
   ```bash
   screen -S kimble_crawler  # ✅ 좋음
   screen -S crawler         # ❌ 누구 것인지 모름
   ```

2. **실행 중인 프로세스 확인**
   ```bash
   ps aux | grep python
   screen -ls
   ```

3. **같은 크롤러를 동시에 실행하지 않기**
   - 같은 데이터를 중복 수집할 수 있음
   - 동료와 커뮤니케이션 필수

4. **리소스 사용량 확인**
   ```bash
   htop  # CPU/메모리 사용량 확인
   ```

---

## 🛠️ 문제 해결

### Chrome/Chromium 관련 오류
```bash
# Chromium 설치 확인
which chromium-browser

# 재설치가 필요한 경우
sudo apt update
sudo apt install -y chromium-browser chromium-chromedriver
```

### 패키지 누락 오류
```bash
cd ~/PMIK-sns-analysis
source .venv/bin/activate
pip install -r requirements.txt
```

### Screen 세션이 응답하지 않을 때
```bash
# 강제 종료
screen -X -S 세션명 quit

# 또는 프로세스 직접 종료
ps aux | grep python
kill -9 [PID]
```

---

## 💡 유용한 팁

### 백그라운드 실행 (nohup 방식)
Screen 대신 간단하게 실행하려면:
```bash
cd ~/PMIK-sns-analysis/naver_blog
source ../.venv/bin/activate
nohup python pm_naver_blog_crawler_v8_4_final.py > crawler_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# 프로세스 확인
ps aux | grep python

# 종료
kill [PID]
```

### 여러 크롤러 동시 실행
```bash
# 각각 다른 Screen 세션에서
screen -S kimble_naver
screen -S kimble_youtube
screen -S kimble_instagram

# 세션 전환
screen -ls  # 목록 확인
screen -r kimble_naver  # 특정 세션 접속
```
