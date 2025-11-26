#!/bin/bash

# VM 디렉토리 현황 확인 스크립트
# 작성일: 2025-11-21

echo "========================================="
echo "🖥️  VM 디렉토리 현황 확인"
echo "========================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Crawler VM 확인
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🔧 CRAWLER VM${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}📁 홈 디렉토리 구조:${NC}"
ssh crawler "ls -lh ~/ | grep '^d' | awk '{print \$9, \"(\"\$5\")\"}'"
echo ""

echo -e "${BLUE}📂 PMIK-sns-analysis 프로젝트:${NC}"
ssh crawler "du -sh ~/PMIK-sns-analysis/* 2>/dev/null | sort -h"
echo ""

echo -e "${BLUE}📊 주요 폴더 상세:${NC}"
echo ""
echo "  [Instagram]"
ssh crawler "ls -lh ~/PMIK-sns-analysis/instagram/ 2>/dev/null | tail -n +2 | awk '{print \"    \"\$9, \"(\"\$5\")\"}' || echo '    (폴더 없음)'"
echo ""
echo "  [Kakaostory]"
ssh crawler "ls -lh ~/PMIK-sns-analysis/kakaostory/ 2>/dev/null | tail -n +2 | awk '{print \"    \"\$9, \"(\"\$5\")\"}' || echo '    (폴더 없음)'"
echo ""
echo "  [Naver Blog]"
ssh crawler "ls -lh ~/PMIK-sns-analysis/naver_blog/*.py 2>/dev/null | awk '{print \"    \"\$9, \"(\"\$5\")\"}' | head -5 || echo '    (파일 없음)'"
echo ""
echo "  [YouTube]"
ssh crawler "ls -lh ~/PMIK-sns-analysis/youtube/*.py 2>/dev/null | awk '{print \"    \"\$9, \"(\"\$5\")\"}' | head -5 || echo '    (파일 없음)'"
echo ""

echo -e "${BLUE}💾 디스크 사용량:${NC}"
ssh crawler "df -h ~/ | tail -1 | awk '{print \"  사용: \"\$3\" / \"\$2\" (\"\$5\" 사용 중)\"}'"
echo ""

# Analyst VM 확인
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 ANALYST VM${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${BLUE}📁 홈 디렉토리 구조:${NC}"
ssh analyst "ls -lh ~/ | grep '^d' | awk '{print \$9, \"(\"\$5\")\"}'"
echo ""

echo -e "${BLUE}📂 venvs 폴더:${NC}"
ssh analyst "du -sh ~/venvs/* 2>/dev/null | sort -h"
echo ""

echo -e "${BLUE}📊 python_code 폴더 상세:${NC}"
ssh analyst "ls -lh ~/venvs/python_code/ 2>/dev/null | tail -n +2 | awk '{print \"  \"\$9, \"(\"\$5\")\"}' | head -20 || echo '  (폴더 없음)'"
echo ""

echo -e "${BLUE}💾 디스크 사용량:${NC}"
ssh analyst "df -h ~/ | tail -1 | awk '{print \"  사용: \"\$3\" / \"\$2\" (\"\$5\" 사용 중)\"}'"
echo ""

echo "========================================="
echo "✅ 확인 완료"
echo "========================================="
