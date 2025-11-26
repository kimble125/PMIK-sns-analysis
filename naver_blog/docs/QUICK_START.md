# 🚀 VM 크롤러 실행 빠른 가이드

## 한눈에 보는 실행 순서

```
로컬 맥북 → 파일 업로드 → VM 접속 → Screen 시작 → 크롤러 실행 → Detach → 종료
```

---

## 📝 복사해서 붙여넣기 (Copy & Paste)

### 1️⃣ 로컬 맥북에서 (터미널)

```bash
# 파일 업로드
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp pm_naver_blog_crawler_v10_1_test.py crawler:~/PMIK-sns-analysis/naver_blog/
scp config.yaml crawler:~/PMIK-sns-analysis/naver_blog/

# VM 접속
ssh crawler
```

---

### 2️⃣ VM에서

```bash
# 디렉토리 이동
cd ~/PMIK-sns-analysis/naver_blog

# Screen 세션 시작
screen -S crawler_v10

# 크롤러 실행
python3 pm_naver_blog_crawler_v10_1_test.py
```

**크롤러가 시작되면:**
- 로그가 출력되는 것 확인
- `Ctrl + A`, 그 다음 `D` (Detach)
- `exit` (SSH 종료)
- **노트북 종료 OK!** ✅

---

### 3️⃣ 2시간 후 결과 확인

```bash
# VM 재접속
ssh crawler

# Screen 세션 확인
screen -ls

# 세션에 다시 접속 (선택)
screen -r crawler_v10

# 또는 바로 파일 확인
cd ~/PMIK-sns-analysis/naver_blog
ls -lh *.csv *.txt

# 로컬로 다운로드
exit  # VM에서 나가기

# 로컬 터미널에서
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp 'crawler:~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v10_1_test_*.csv' .
scp 'crawler:~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v10_1_test_*_report.txt' .
```

---

## 🎯 핵심 명령어 3가지

### Screen 시작
```bash
screen -S crawler_v10
```

### Screen에서 나오기 (Detach)
```
Ctrl + A, 그 다음 D
```

### Screen 다시 접속 (Reattach)
```bash
screen -r crawler_v10
```

---

## ⚡ 긴급 상황

### 크롤러 중단하기
```bash
ssh crawler
screen -r crawler_v10
# Ctrl + C (크롤러 중단)
exit  # Screen 종료
```

### Screen 세션 강제 종료
```bash
screen -X -S crawler_v10 quit
```

---

## 📊 현재 설정

- **실행 시간**: 2시간 (120분)
- **키워드당 목표**: 300개
- **예상 수집량**: 500~1,500개
- **출력 파일**: CSV + 보고서 + VM 로그

---

## ✅ 체크리스트

- [ ] 파일 업로드 완료
- [ ] VM 접속 완료
- [ ] Screen 세션 시작
- [ ] 크롤러 실행 확인
- [ ] Detach 완료 (`Ctrl+A, D`)
- [ ] SSH 종료
- [ ] 노트북 종료 (선택)

---

**상세 가이드**: `VM_EXECUTION_GUIDE.md` 참조
