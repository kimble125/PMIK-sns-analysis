# Cron 자동화 가이드

## 📖 Cron이란?

**Cron**은 리눅스/유닉스에서 **정해진 시간에 자동으로 명령어나 스크립트를 실행**하는 스케줄러입니다.

### 사용 예시
- 매일 새벽 2시에 크롤러 자동 실행
- 매주 월요일 오전 9시에 데이터 분석
- 매시간 로그 파일 백업
- 매일 자정에 데이터베이스 정리

---

## 🚀 빠른 시작

### 1. Cron 작업 목록 확인
```bash
crontab -l
```

### 2. Cron 작업 편집
```bash
crontab -e
```

### 3. Cron 작업 추가 예시
```bash
# 매일 새벽 2시에 크롤러 실행
0 2 * * * cd ~/PMIK-sns-analysis/naver_blog && source ../.venv/bin/activate && python pm_naver_blog_crawler_v8_4_final.py >> ~/logs/crawler.log 2>&1
```

---

## ⏰ Cron 시간 형식

```
* * * * * 실행할_명령어
│ │ │ │ │
│ │ │ │ └─ 요일 (0-7, 0과 7은 일요일)
│ │ │ └─── 월 (1-12)
│ │ └───── 일 (1-31)
│ └─────── 시 (0-23)
└───────── 분 (0-59)
```

### 예시

| Cron 표현식 | 의미 |
|------------|------|
| `0 2 * * *` | 매일 새벽 2시 |
| `30 9 * * 1` | 매주 월요일 오전 9시 30분 |
| `0 */6 * * *` | 6시간마다 (0시, 6시, 12시, 18시) |
| `0 0 1 * *` | 매월 1일 자정 |
| `*/15 * * * *` | 15분마다 |
| `0 9-17 * * 1-5` | 평일(월-금) 오전 9시~오후 5시 매시 정각 |

---

## 📝 실전 예시

### 예시 1: 네이버 블로그 크롤러 자동 실행

```bash
# 매일 새벽 2시에 실행
0 2 * * * cd ~/PMIK-sns-analysis/naver_blog && source ../.venv/bin/activate && python pm_naver_blog_crawler_v8_4_final.py >> ~/logs/crawler_$(date +\%Y\%m\%d).log 2>&1
```

**설명:**
- `0 2 * * *`: 매일 새벽 2시
- `cd ~/PMIK-sns-analysis/naver_blog`: 작업 디렉토리로 이동
- `source ../.venv/bin/activate`: 가상환경 활성화
- `python pm_naver_blog_crawler_v8_4_final.py`: 크롤러 실행
- `>> ~/logs/crawler_$(date +\%Y\%m\%d).log`: 로그 파일에 출력 저장
- `2>&1`: 에러도 로그 파일에 저장

### 예시 2: 데이터 분석 자동 실행

```bash
# 매주 월요일 오전 9시에 실행
0 9 * * 1 cd ~/PMIK-sns-analysis/analysis && source ../.venv/bin/activate && python analyze_weekly_data.py >> ~/logs/analysis_weekly.log 2>&1
```

### 예시 3: 로그 파일 정리

```bash
# 매일 자정에 30일 이상 된 로그 파일 삭제
0 0 * * * find ~/logs -name "*.log" -mtime +30 -delete
```

### 예시 4: 디스크 사용량 모니터링

```bash
# 매일 오전 8시에 디스크 사용량 체크
0 8 * * * df -h > ~/logs/disk_usage_$(date +\%Y\%m\%d).txt
```

---

## 🛠️ Cron 작업 설정 단계별 가이드

### Step 1: 로그 디렉토리 생성
```bash
mkdir -p ~/logs
```

### Step 2: 테스트 스크립트 작성
```bash
# 간단한 테스트 스크립트
cat > ~/test_cron.sh << 'EOF'
#!/bin/bash
echo "Cron test at $(date)" >> ~/logs/cron_test.log
EOF

chmod +x ~/test_cron.sh
```

### Step 3: Cron 편집기 열기
```bash
crontab -e
```

### Step 4: 테스트 작업 추가 (1분마다 실행)
```bash
* * * * * ~/test_cron.sh
```

### Step 5: 저장 후 확인
```bash
# Cron 목록 확인
crontab -l

# 1-2분 후 로그 확인
cat ~/logs/cron_test.log
```

### Step 6: 테스트 작업 제거
```bash
crontab -e
# 테스트 라인 삭제 후 저장
```

---

## 🔧 크롤러 자동화 설정 (실전)

### 1. 크롤러 래퍼 스크립트 생성

VM에서 실행:
```bash
cat > ~/run_crawler.sh << 'EOF'
#!/bin/bash

# 로그 디렉토리 생성
mkdir -p ~/logs

# 날짜 기반 로그 파일명
LOG_FILE=~/logs/crawler_$(date +%Y%m%d_%H%M%S).log

# 크롤러 실행
cd ~/PMIK-sns-analysis/naver_blog
source ../.venv/bin/activate

echo "========================================" >> $LOG_FILE
echo "크롤러 시작: $(date)" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

python pm_naver_blog_crawler_v8_4_final.py >> $LOG_FILE 2>&1

echo "========================================" >> $LOG_FILE
echo "크롤러 종료: $(date)" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

# 완료 알림 (선택사항)
echo "크롤러 완료: $(date)" | mail -s "Crawler Completed" your_email@example.com
EOF

chmod +x ~/run_crawler.sh
```

### 2. Cron 등록
```bash
crontab -e

# 매일 새벽 2시에 실행
0 2 * * * ~/run_crawler.sh
```

### 3. 수동 테스트
```bash
~/run_crawler.sh
```

---

## ⚠️ 주의사항

### 1. 환경변수 문제
Cron은 제한된 환경변수로 실행되므로 **절대 경로** 사용 권장:

```bash
# ❌ 나쁜 예
0 2 * * * python crawler.py

# ✅ 좋은 예
0 2 * * * /home/pmi/PMIK-sns-analysis/.venv/bin/python /home/pmi/PMIK-sns-analysis/naver_blog/pm_naver_blog_crawler_v8_4_final.py
```

### 2. 가상환경 활성화
```bash
# 가상환경 활성화 필수
source /home/pmi/PMIK-sns-analysis/.venv/bin/activate
```

### 3. 로그 파일 관리
```bash
# 로그가 계속 쌓이므로 정기적으로 정리
0 0 * * 0 find ~/logs -name "*.log" -mtime +30 -delete
```

### 4. 중복 실행 방지
```bash
# 락 파일을 사용한 중복 실행 방지
#!/bin/bash
LOCKFILE=/tmp/crawler.lock

if [ -e $LOCKFILE ]; then
    echo "이미 실행 중입니다."
    exit 1
fi

touch $LOCKFILE
# 크롤러 실행
python crawler.py
rm $LOCKFILE
```

---

## 🐛 트러블슈팅

### Cron이 실행되지 않을 때

1. **Cron 서비스 상태 확인**
```bash
sudo service cron status
```

2. **Cron 로그 확인**
```bash
grep CRON /var/log/syslog
```

3. **권한 확인**
```bash
ls -l ~/run_crawler.sh
# 실행 권한이 있어야 함: -rwxr-xr-x
```

4. **경로 확인**
```bash
# 스크립트 내에서 절대 경로 사용
which python  # Cron 환경에서는 작동 안 할 수 있음
/home/pmi/PMIK-sns-analysis/.venv/bin/python  # 절대 경로 사용
```

### 로그가 생성되지 않을 때

```bash
# 로그 디렉토리 권한 확인
ls -ld ~/logs

# 수동으로 스크립트 실행해서 에러 확인
bash -x ~/run_crawler.sh
```

---

## 📊 동료와 Cron 작업 조율

### 1. 현재 등록된 Cron 작업 공유
```bash
# 각자 자신의 cron 작업 목록 공유
crontab -l > ~/my_cron_jobs.txt
```

### 2. 시간대 분리 예시

**김블:**
```bash
# 매일 새벽 2시: 네이버 블로그 크롤링
0 2 * * * ~/run_naver_crawler.sh

# 매일 새벽 4시: 유튜브 크롤링
0 4 * * * ~/run_youtube_crawler.sh
```

**동료:**
```bash
# 매일 오전 9시: 데이터 분석
0 9 * * * ~/run_analysis.sh

# 매주 월요일 오후 2시: 주간 리포트 생성
0 14 * * 1 ~/run_weekly_report.sh
```

### 3. 충돌 방지 체크리스트
- [ ] 같은 시간대에 리소스 집약적 작업 없음
- [ ] 같은 파일/데이터베이스 동시 접근 없음
- [ ] 로그 파일명 중복 없음
- [ ] Screen 세션명 중복 없음

---

## 🎯 권장 Cron 스케줄 (공유 VM)

| 시간대 | 권장 작업 | 리소스 사용 |
|--------|----------|------------|
| 새벽 1-6시 | 대용량 크롤링, 데이터 처리 | 높음 |
| 오전 7-9시 | 가벼운 작업, 리포트 생성 | 낮음 |
| 오전 9-12시 | 데이터 분석 | 중간 |
| 오후 1-6시 | 수동 작업 시간 (Cron 피하기) | - |
| 저녁 7-11시 | 가벼운 자동화 작업 | 낮음 |
| 자정-새벽 1시 | 로그 정리, 백업 | 낮음 |

---

## 📧 알림 설정 (선택사항)

### 이메일 알림
```bash
# 크롤러 완료 시 이메일 발송
0 2 * * * ~/run_crawler.sh && echo "Crawler completed" | mail -s "Crawler Done" your@email.com
```

### Slack 알림
```bash
# Slack webhook 사용
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"크롤러 완료!"}' \
  YOUR_SLACK_WEBHOOK_URL
```

---

## 🔍 유용한 Cron 관련 명령어

```bash
# Cron 작업 목록 보기
crontab -l

# Cron 작업 편집
crontab -e

# Cron 작업 모두 삭제
crontab -r

# 다른 사용자의 Cron (root만 가능)
sudo crontab -u username -l

# Cron 로그 실시간 확인
tail -f /var/log/syslog | grep CRON

# 최근 Cron 실행 기록
grep CRON /var/log/syslog | tail -20
```

---

## 📚 추가 자료

- [Crontab Guru](https://crontab.guru/) - Cron 표현식 생성 도구
- [Cron 공식 문서](https://man7.org/linux/man-pages/man5/crontab.5.html)
