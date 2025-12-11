#!/bin/bash
# 두 VM 리소스 사용량 동시 확인 스크립트
# 작성자: PMI Korea 데이터 분석팀
# 날짜: 2025-11-17

echo "=========================================="
echo "VM 리소스 사용량 통합 리포트"
echo "생성 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

echo "=== CRAWLER VM ==="
ssh crawler "cd ~/PMIK-sns-analysis && ./vm_usage_report.sh"
echo ""
echo ""

echo "=== ANALYST VM ==="
echo "📊 기본 리소스 사용량"
echo "----------------------------------------"
ssh analyst "echo '호스트명: '\$(hostname) && \
echo 'OS: '\$(lsb_release -d | cut -f2) && \
echo '가동 시간: '\$(uptime -p) && \
echo '' && \
echo '💾 메모리:' && free -h && \
echo '' && \
echo '💿 디스크:' && df -h | grep -E '^/dev/' && \
echo '' && \
echo '🐍 Python 프로세스:' && ps aux | grep python | grep -v grep || echo '실행 중인 Python 프로세스 없음'"
echo ""

echo "=========================================="
echo "통합 리포트 생성 완료"
echo "=========================================="
