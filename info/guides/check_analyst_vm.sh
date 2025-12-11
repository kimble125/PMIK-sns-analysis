#!/bin/bash
# Analyst VM 리소스 및 작업 확인 스크립트
# 프로젝트 디렉토리 없이도 실행 가능
# 작성자: PMI Korea 데이터 분석팀
# 날짜: 2025-11-17

echo "=========================================="
echo "Analyst VM 상태 확인"
echo "생성 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

ssh analyst "
echo '📊 1. 시스템 정보'
echo '----------------------------------------'
echo '호스트명: '\$(hostname)
echo 'OS: '\$(lsb_release -d | cut -f2)
echo '커널: '\$(uname -r)
echo '가동 시간: '\$(uptime -p)
echo '현재 시간: '\$(date '+%Y-%m-%d %H:%M:%S')
echo ''

echo '💾 2. 메모리 사용량'
echo '----------------------------------------'
free -h
echo ''

echo '💿 3. 디스크 사용량'
echo '----------------------------------------'
df -h
echo ''

echo '🔥 4. CPU 부하'
echo '----------------------------------------'
uptime
echo 'CPU 코어 수: '\$(nproc)
echo ''

echo '🐍 5. 실행 중인 Python 프로세스'
echo '----------------------------------------'
ps aux | grep python | grep -v grep || echo '실행 중인 Python 프로세스 없음'
echo ''

echo '📓 6. Jupyter Notebook 확인'
echo '----------------------------------------'
ps aux | grep jupyter | grep -v grep || echo 'Jupyter Notebook 실행 중 아님'
echo ''

echo '👥 7. 현재 로그인 사용자'
echo '----------------------------------------'
who
echo ''

echo '📁 8. 홈 디렉토리 용량'
echo '----------------------------------------'
echo '본인 홈 디렉토리: '\$(du -sh ~ 2>/dev/null | cut -f1)
echo ''

echo '📂 9. 주요 디렉토리 확인'
echo '----------------------------------------'
ls -lh ~ | head -15
echo ''

echo '🕐 10. 최근 로그인 기록 (최근 10개)'
echo '----------------------------------------'
last | head -10
echo ''

echo '⚡ 11. 상위 CPU 사용 프로세스 (Top 5)'
echo '----------------------------------------'
ps aux --sort=-%cpu | head -6
echo ''

echo '💾 12. 상위 메모리 사용 프로세스 (Top 5)'
echo '----------------------------------------'
ps aux --sort=-%mem | head -6
echo ''
"

echo "=========================================="
echo "확인 완료"
echo "=========================================="
