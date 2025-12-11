# VM 로그 관리 시스템 구축 가이드

## 🎯 목표

Analyst VM과 Crawler VM에서 실행되는 모든 작업의 **시작/종료 시간, 종료 원인, 실행 상태**를 체계적으로 로그로 남기는 시스템 구축

---

## 📋 로그 요구사항

### 필수 기록 항목
1. **시작 시간**: 프로세스 시작 타임스탬프
2. **종료 시간**: 프로세스 종료 타임스탬프
3. **실행 시간**: 총 소요 시간
4. **종료 원인**: 정상 종료 / 에러 / 강제 종료 / 시스템 재부팅
5. **실행 상태**: 성공 / 실패 / 부분 성공
6. **수집 통계**: 처리된 데이터 수, 에러 수 등
7. **시스템 정보**: CPU, 메모리 사용량
8. **에러 메시지**: 발생한 에러의 상세 내용

---

## 🛠️ 방법 1: PM2 프로세스 매니저 (권장)

### 설치 및 설정

```bash
# SSH로 VM 접속
ssh crawler  # 또는 ssh analyst

# PM2 설치 (Node.js 필요)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g pm2

# PM2 설정 확인
pm2 --version
```

### PM2 설정 파일 생성

```bash
cd ~/PMIK-sns-analysis/naver_blog
nano ecosystem.config.js
```

**ecosystem.config.js 내용**:
```javascript
module.exports = {
  apps: [{
    name: 'naver-blog-crawler',
    script: 'pm_naver_blog_crawler_v9_1_final.py',
    interpreter: 'python3',
    cwd: '/home/pmi/PMIK-sns-analysis/naver_blog',
    
    // 로그 설정
    error_file: './logs/error.log',
    out_file: './logs/output.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    
    // 자동 재시작 설정
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
    max_memory_restart: '2G',
    
    // 환경 변수
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },
    
    // 크론 재시작 (선택사항)
    cron_restart: '0 6 * * *',  // 매일 오전 6시 재시작
    
    // 인스턴스 설정
    instances: 1,
    exec_mode: 'fork'
  }]
};
```

### PM2 실행 및 관리

```bash
# 로그 디렉토리 생성
mkdir -p ~/PMIK-sns-analysis/naver_blog/logs

# PM2로 크롤러 시작
pm2 start ecosystem.config.js

# 상태 확인
pm2 status

# 로그 실시간 확인
pm2 logs naver-blog-crawler

# 특정 줄 수만큼 로그 확인
pm2 logs naver-blog-crawler --lines 100

# 로그 파일 직접 확인
tail -f ~/PMIK-sns-analysis/naver_blog/logs/output.log

# 프로세스 정보 상세 확인
pm2 show naver-blog-crawler

# 모니터링 대시보드
pm2 monit

# 서버 재부팅 시 자동 시작 설정
pm2 startup
pm2 save
```

### PM2 로그 로테이션

```bash
# PM2 로그 로테이션 모듈 설치
pm2 install pm2-logrotate

# 로그 로테이션 설정
pm2 set pm2-logrotate:max_size 10M        # 최대 10MB
pm2 set pm2-logrotate:retain 30           # 30개 파일 보관
pm2 set pm2-logrotate:compress true       # 압축 활성화
pm2 set pm2-logrotate:dateFormat YYYY-MM-DD_HH-mm-ss
pm2 set pm2-logrotate:rotateModule true
```

---

## 🛠️ 방법 2: Systemd 서비스 (대안)

### Systemd 서비스 파일 생성

```bash
sudo nano /etc/systemd/system/naver-blog-crawler.service
```

**서비스 파일 내용**:
```ini
[Unit]
Description=Naver Blog Crawler Service
After=network.target

[Service]
Type=simple
User=pmi
WorkingDirectory=/home/pmi/PMIK-sns-analysis/naver_blog
ExecStart=/usr/bin/python3 /home/pmi/PMIK-sns-analysis/naver_blog/pm_naver_blog_crawler_v9_1_final.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/pmi/PMIK-sns-analysis/naver_blog/logs/service.log
StandardError=append:/home/pmi/PMIK-sns-analysis/naver_blog/logs/service_error.log

# 환경 변수
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

### Systemd 서비스 관리

```bash
# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable naver-blog-crawler.service

# 서비스 시작
sudo systemctl start naver-blog-crawler.service

# 상태 확인
sudo systemctl status naver-blog-crawler.service

# 로그 확인
sudo journalctl -u naver-blog-crawler.service -f

# 특정 기간 로그 확인
sudo journalctl -u naver-blog-crawler.service --since "2025-11-17" --until "2025-11-18"

# 서비스 중지
sudo systemctl stop naver-blog-crawler.service

# 서비스 재시작
sudo systemctl restart naver-blog-crawler.service
```

---

## 🛠️ 방법 3: 커스텀 로깅 래퍼 스크립트

### 로깅 래퍼 스크립트 생성

```bash
nano ~/PMIK-sns-analysis/naver_blog/run_with_logging.sh
```

**run_with_logging.sh 내용**:
```bash
#!/bin/bash

# 설정
SCRIPT_NAME="pm_naver_blog_crawler_v9_1_final.py"
LOG_DIR="$HOME/PMIK-sns-analysis/naver_blog/logs"
LOG_FILE="$LOG_DIR/execution_$(date +%Y%m%d_%H%M%S).log"
STATUS_FILE="$LOG_DIR/status.json"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

# 시작 시간 기록
START_TIME=$(date +%s)
START_DATETIME=$(date '+%Y-%m-%d %H:%M:%S')

echo "========================================" | tee -a "$LOG_FILE"
echo "🚀 크롤러 시작" | tee -a "$LOG_FILE"
echo "시작 시간: $START_DATETIME" | tee -a "$LOG_FILE"
echo "스크립트: $SCRIPT_NAME" | tee -a "$LOG_FILE"
echo "호스트: $(hostname)" | tee -a "$LOG_FILE"
echo "사용자: $(whoami)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 시스템 정보 기록
echo "" | tee -a "$LOG_FILE"
echo "📊 시스템 정보:" | tee -a "$LOG_FILE"
echo "CPU: $(nproc) cores" | tee -a "$LOG_FILE"
echo "메모리: $(free -h | awk '/^Mem:/ {print $2}')" | tee -a "$LOG_FILE"
echo "디스크: $(df -h / | awk 'NR==2 {print $4 " 사용 가능"}')" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Python 스크립트 실행
python3 "$SCRIPT_NAME" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

# 종료 시간 기록
END_TIME=$(date +%s)
END_DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

# 종료 원인 판단
if [ $EXIT_CODE -eq 0 ]; then
    STATUS="✅ 정상 종료"
    REASON="성공적으로 완료됨"
elif [ $EXIT_CODE -eq 130 ]; then
    STATUS="⚠️ 사용자 중단"
    REASON="Ctrl+C로 중단됨"
elif [ $EXIT_CODE -eq 137 ]; then
    STATUS="❌ 메모리 부족"
    REASON="OOM Killer에 의해 종료됨"
elif [ $EXIT_CODE -eq 143 ]; then
    STATUS="⚠️ SIGTERM"
    REASON="시스템 종료 신호 수신"
else
    STATUS="❌ 에러 종료"
    REASON="Exit code: $EXIT_CODE"
fi

# 종료 정보 기록
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "🏁 크롤러 종료" | tee -a "$LOG_FILE"
echo "종료 시간: $END_DATETIME" | tee -a "$LOG_FILE"
echo "실행 시간: ${DURATION_MIN}분 ${DURATION_SEC}초" | tee -a "$LOG_FILE"
echo "종료 상태: $STATUS" | tee -a "$LOG_FILE"
echo "종료 원인: $REASON" | tee -a "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# JSON 형식으로 상태 저장
cat > "$STATUS_FILE" << EOF
{
  "script": "$SCRIPT_NAME",
  "start_time": "$START_DATETIME",
  "end_time": "$END_DATETIME",
  "duration_seconds": $DURATION,
  "exit_code": $EXIT_CODE,
  "status": "$STATUS",
  "reason": "$REASON",
  "log_file": "$LOG_FILE",
  "hostname": "$(hostname)",
  "user": "$(whoami)"
}
EOF

echo "" | tee -a "$LOG_FILE"
echo "📝 상태 파일 저장: $STATUS_FILE" | tee -a "$LOG_FILE"

# 이메일 알림 (선택사항)
# echo "크롤러 종료: $STATUS" | mail -s "VM Crawler Alert" your-email@example.com

exit $EXIT_CODE
```

### 실행 권한 부여 및 사용

```bash
# 실행 권한 부여
chmod +x ~/PMIK-sns-analysis/naver_blog/run_with_logging.sh

# 실행
cd ~/PMIK-sns-analysis/naver_blog
./run_with_logging.sh

# 백그라운드 실행
nohup ./run_with_logging.sh > /dev/null 2>&1 &

# 로그 확인
tail -f logs/execution_*.log

# 상태 확인
cat logs/status.json | jq .
```

---

## 📊 로그 분석 스크립트

### 로그 요약 스크립트 생성

```bash
nano ~/PMIK-sns-analysis/naver_blog/analyze_logs.sh
```

**analyze_logs.sh 내용**:
```bash
#!/bin/bash

LOG_DIR="$HOME/PMIK-sns-analysis/naver_blog/logs"

echo "========================================="
echo "📊 VM 크롤러 실행 이력 분석"
echo "========================================="
echo ""

# 최근 10개 실행 이력
echo "📋 최근 실행 이력 (최근 10개):"
echo ""
for status_file in $(ls -t "$LOG_DIR"/status.json 2>/dev/null | head -10); do
    if [ -f "$status_file" ]; then
        echo "---"
        cat "$status_file" | jq -r '"시작: \(.start_time) | 종료: \(.end_time) | 실행시간: \(.duration_seconds)초 | 상태: \(.status)"'
    fi
done

echo ""
echo "========================================="
echo "📈 통계 요약:"
echo ""

# 총 실행 횟수
TOTAL_RUNS=$(ls "$LOG_DIR"/execution_*.log 2>/dev/null | wc -l)
echo "총 실행 횟수: $TOTAL_RUNS"

# 최근 7일 실행 횟수
RECENT_RUNS=$(find "$LOG_DIR" -name "execution_*.log" -mtime -7 2>/dev/null | wc -l)
echo "최근 7일 실행: $RECENT_RUNS"

# 디스크 사용량
LOG_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
echo "로그 디스크 사용: $LOG_SIZE"

echo ""
echo "========================================="
```

```bash
# 실행 권한 부여
chmod +x ~/PMIK-sns-analysis/naver_blog/analyze_logs.sh

# 실행
./analyze_logs.sh
```

---

## 🔔 알림 시스템 구축 (선택사항)

### Slack 알림 설정

```bash
# Slack Webhook URL 설정
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# 알림 함수 추가 (run_with_logging.sh에)
send_slack_notification() {
    local message="$1"
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$message\"}" \
        "$SLACK_WEBHOOK_URL"
}

# 종료 시 알림 전송
send_slack_notification "🤖 VM Crawler 종료\n상태: $STATUS\n실행시간: ${DURATION_MIN}분\n호스트: $(hostname)"
```

---

## 📋 체크리스트

### Crawler VM 설정
- [ ] PM2 설치 및 설정
- [ ] ecosystem.config.js 파일 생성
- [ ] 로그 디렉토리 생성
- [ ] PM2 로그 로테이션 설정
- [ ] 자동 시작 설정 (pm2 startup)
- [ ] 테스트 실행 및 로그 확인

### Analyst VM 설정
- [ ] PM2 설치 및 설정
- [ ] 분석 스크립트용 ecosystem.config.js 생성
- [ ] 로그 디렉토리 생성
- [ ] 자동 시작 설정

### 모니터링 설정
- [ ] 로그 분석 스크립트 작성
- [ ] 크론잡 설정 (일일 로그 요약)
- [ ] 알림 시스템 구축 (선택)
- [ ] 대시보드 구축 (선택)

---

## 🎯 권장 설정

### 최소 설정 (필수)
1. **PM2 설치 및 기본 설정**
2. **로그 로테이션 활성화**
3. **자동 재시작 설정**

### 권장 설정
1. 최소 설정 +
2. **커스텀 로깅 래퍼 스크립트**
3. **로그 분석 스크립트**
4. **일일 로그 요약 크론잡**

### 최적 설정
1. 권장 설정 +
2. **Slack/이메일 알림**
3. **모니터링 대시보드**
4. **자동 백업 시스템**

---

## 📞 문의

**작성자**: PMI Korea 데이터 분석팀  
**작성일**: 2025년 11월 18일  
**업데이트**: 필요 시 수시 업데이트
