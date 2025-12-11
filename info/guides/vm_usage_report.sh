#!/bin/bash
# VM 리소스 사용량 리포트 생성 스크립트
# 작성자: PMI Korea 데이터 분석팀
# 날짜: 2025-11-17

echo "=========================================="
echo "VM 리소스 사용량 리포트"
echo "생성 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 1. 시스템 정보
echo "📊 1. 시스템 정보"
echo "----------------------------------------"
echo "호스트명: $(hostname)"
echo "OS: $(lsb_release -d | cut -f2)"
echo "커널: $(uname -r)"
echo "가동 시간: $(uptime -p)"
echo ""

# 2. CPU 정보
echo "🖥️  2. CPU 정보"
echo "----------------------------------------"
echo "CPU 코어 수: $(nproc)"
echo "CPU 모델: $(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)"
echo "부하 평균 (1분/5분/15분): $(uptime | awk -F'load average:' '{print $2}')"
echo ""

# 3. 메모리 사용량
echo "💾 3. 메모리 사용량"
echo "----------------------------------------"
free -h
echo ""

# 4. 디스크 사용량
echo "💿 4. 디스크 사용량"
echo "----------------------------------------"
df -h | grep -E '^/dev/'
echo ""

# 5. 실행 중인 Python 프로세스
echo "🐍 5. 실행 중인 Python 프로세스"
echo "----------------------------------------"
ps aux | grep python | grep -v grep | awk '{printf "%-10s %-8s %5s %5s %10s %s\n", $1, $2, $3"%", $4"%", $10, $11" "$12" "$13}'
echo ""

# 6. 크롤러 프로세스 상세
echo "🕷️  6. 크롤러 프로세스 상세"
echo "----------------------------------------"
if pgrep -f "pm_naver_blog_crawler" > /dev/null; then
    CRAWLER_PID=$(pgrep -f "pm_naver_blog_crawler")
    echo "프로세스 ID: $CRAWLER_PID"
    ps -p $CRAWLER_PID -o pid,ppid,%cpu,%mem,vsz,rss,etime,cmd --no-headers
    echo ""
    echo "실행 시간: $(ps -p $CRAWLER_PID -o etime --no-headers)"
    echo "CPU 사용률: $(ps -p $CRAWLER_PID -o %cpu --no-headers)%"
    echo "메모리 사용률: $(ps -p $CRAWLER_PID -o %mem --no-headers)%"
    echo "메모리 사용량: $(ps -p $CRAWLER_PID -o rss --no-headers | awk '{printf "%.2f MB", $1/1024}')"
else
    echo "크롤러 프로세스가 실행 중이지 않습니다."
fi
echo ""

# 7. 프로젝트 디스크 사용량
echo "📁 7. 프로젝트 디스크 사용량"
echo "----------------------------------------"
if [ -d ~/PMIK-sns-analysis ]; then
    echo "전체 프로젝트: $(du -sh ~/PMIK-sns-analysis 2>/dev/null | cut -f1)"
    echo "naver_blog: $(du -sh ~/PMIK-sns-analysis/naver_blog 2>/dev/null | cut -f1)"
    echo "CSV 파일: $(find ~/PMIK-sns-analysis/naver_blog -name "*.csv" -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)"
    echo "체크포인트: $(du -sh ~/PMIK-sns-analysis/naver_blog/checkpoints 2>/dev/null | cut -f1)"
else
    echo "프로젝트 디렉토리를 찾을 수 없습니다."
fi
echo ""

# 8. 네트워크 통계
echo "🌐 8. 네트워크 통계"
echo "----------------------------------------"
netstat -i | grep -v Kernel | grep -v Iface
echo ""

# 9. 최근 로그 (크롤러)
echo "📝 9. 크롤러 최근 로그 (마지막 10줄)"
echo "----------------------------------------"
if [ -f ~/PMIK-sns-analysis/naver_blog/crawler.log ]; then
    tail -10 ~/PMIK-sns-analysis/naver_blog/crawler.log
else
    echo "로그 파일을 찾을 수 없습니다."
fi
echo ""

# 10. 수집 통계
echo "📊 10. 데이터 수집 통계"
echo "----------------------------------------"
if [ -f ~/PMIK-sns-analysis/naver_blog/crawler.log ]; then
    echo "수집 완료 건수: $(grep -c '✅ 수집 완료' ~/PMIK-sns-analysis/naver_blog/crawler.log)"
    echo "체크포인트 저장: $(grep -c '체크포인트 저장' ~/PMIK-sns-analysis/naver_blog/crawler.log)"
    echo "에러 발생: $(grep -c 'ERROR' ~/PMIK-sns-analysis/naver_blog/crawler.log)"
fi

# CSV 파일 확인
CSV_FILES=$(find ~/PMIK-sns-analysis/naver_blog -name "naver_blog_pm_v9_1_final_*.csv" 2>/dev/null)
if [ -n "$CSV_FILES" ]; then
    echo ""
    echo "CSV 파일:"
    for file in $CSV_FILES; do
        LINE_COUNT=$(($(wc -l < "$file") - 1))  # 헤더 제외
        FILE_SIZE=$(du -h "$file" | cut -f1)
        echo "  - $(basename $file): ${LINE_COUNT}개, ${FILE_SIZE}"
    done
fi
echo ""

echo "=========================================="
echo "리포트 생성 완료"
echo "=========================================="
