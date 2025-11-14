# PMIKR-DATA-CRAWLER VM 공유 사용 가이드

## 👥 현재 사용자
- **김블** (kimble)
- **동료** (colleague_name)

---

## 📋 작업 현황 (실시간 업데이트)

### 김블 작업
- **Screen 세션**: `kimble_crawler`
- **실행 중인 스크립트**: `pm_naver_blog_crawler_v8_4_final.py`
- **작업 디렉토리**: `~/PMIK-sns-analysis/naver_blog`
- **예상 종료 시간**: TBD
- **리소스 사용**: CPU 중간, 메모리 중간

### 동료 작업
- **Screen 세션**: `colleague_xxx`
- **실행 중인 스크립트**: TBD
- **작업 디렉토리**: TBD
- **예상 종료 시간**: TBD
- **리소스 사용**: TBD

---

## 🕐 Cron 스케줄 조율

### 현재 등록된 Cron 작업

#### 김블
```bash
# 아직 등록 안 함
```

#### 동료
```bash
# TBD
```

### 권장 시간대 분리
- **새벽 1-6시**: 대용량 크롤링 작업
- **오전 9-12시**: 데이터 분석/처리
- **오후 2-5시**: 수동 작업 (충돌 가능성 있음)
- **저녁 8-11시**: 가벼운 작업

---

## 📁 디렉토리 구조

```
/home/pmi/
├── PMIK-sns-analysis/          # Git 저장소 (공유)
│   ├── naver_blog/
│   ├── youtube/
│   └── analysis/
├── work_kimble/                # 김블 개인 작업 공간
├── work_colleague/             # 동료 개인 작업 공간
└── shared_data/                # 공유 데이터
    ├── raw_data/
    ├── processed_data/
    └── results/
```

---

## ⚠️ 충돌 방지 규칙

### 1. Screen 세션 명명 규칙
```bash
# ✅ 좋은 예
screen -S kimble_crawler
screen -S colleague_analysis

# ❌ 나쁜 예
screen -S crawler  # 누구 것인지 모름
```

### 2. 로그 파일 명명 규칙
```bash
# 사용자 이름 포함
crawler_kimble_20251114.log
analysis_colleague_20251114.log
```

### 3. 같은 스크립트 동시 실행 금지
- 같은 크롤러를 동시에 실행하면 중복 데이터 수집
- 실행 전 `ps aux | grep python` 으로 확인

### 4. 리소스 집약적 작업 전 알림
- Slack/카톡으로 "지금부터 크롤러 돌립니다" 공지
- `htop` 으로 현재 리소스 사용량 확인

---

## 🔍 현재 작업 확인 명령어

```bash
# 실행 중인 Python 프로세스
ps aux | grep python

# Screen 세션 목록
screen -ls

# CPU/메모리 사용량
htop

# 디스크 사용량
df -h

# 특정 사용자의 프로세스
ps -u pmi

# 네트워크 사용량
iftop  # 설치 필요: sudo apt install iftop
```

---

## 📝 Cron 작업 등록 예시

### Cron 편집
```bash
crontab -e
```

### 예시 1: 매일 새벽 2시 크롤러 실행
```bash
0 2 * * * cd ~/PMIK-sns-analysis/naver_blog && source ../.venv/bin/activate && python pm_naver_blog_crawler_v8_4_final.py >> ~/logs/crawler_$(date +\%Y\%m\%d).log 2>&1
```

### 예시 2: 매주 월요일 오전 9시 분석 실행
```bash
0 9 * * 1 cd ~/PMIK-sns-analysis/analysis && source ../.venv/bin/activate && python analyze_data.py >> ~/logs/analysis_$(date +\%Y\%m\%d).log 2>&1
```

### Cron 시간 형식
```
* * * * * 명령어
│ │ │ │ │
│ │ │ │ └─ 요일 (0-7, 0과 7은 일요일)
│ │ │ └─── 월 (1-12)
│ │ └───── 일 (1-31)
│ └─────── 시 (0-23)
└───────── 분 (0-59)
```

---

## 🚨 긴급 상황 대처

### 프로세스가 멈추지 않을 때
```bash
# 프로세스 ID 확인
ps aux | grep python

# 강제 종료
kill -9 [PID]

# Screen 세션 강제 종료
screen -X -S 세션명 quit
```

### VM 리소스 부족
```bash
# 메모리 정리
sudo sync && sudo sysctl -w vm.drop_caches=3

# 디스크 정리
sudo apt clean
sudo apt autoremove
```

---

## 📞 커뮤니케이션 체크리스트

작업 시작 전:
- [ ] 동료에게 작업 시작 알림
- [ ] 예상 종료 시간 공유
- [ ] 리소스 사용량 확인 (`htop`)
- [ ] 충돌 가능성 확인

작업 종료 후:
- [ ] 동료에게 작업 완료 알림
- [ ] Screen 세션 정리
- [ ] 로그 파일 정리 (필요시)
- [ ] 이 문서 업데이트

---

## 📊 리소스 사용 가이드라인

| 작업 유형 | CPU 사용률 | 메모리 사용량 | 권장 시간대 |
|-----------|-----------|--------------|------------|
| 크롤링 (대용량) | 50-80% | 2-4GB | 새벽 1-6시 |
| 데이터 분석 | 30-60% | 1-3GB | 오전 9-12시 |
| OCR 처리 | 70-90% | 4-8GB | 새벽 2-5시 |
| 가벼운 작업 | <30% | <1GB | 언제든지 |

---

## 🔄 업데이트 로그

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2025-11-14 | 김블 | 초기 문서 작성 |
| TBD | 동료 | TBD |
