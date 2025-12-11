#!/bin/bash

# Crawler VM 상세 확인 스크립트
# 작성일: 2025-11-21

echo "========================================="
echo "🔧 CRAWLER VM 상세 현황"
echo "========================================="
echo ""

echo "📁 전체 디렉토리 트리:"
echo ""
ssh crawler "find ~/PMIK-sns-analysis -maxdepth 3 -type d | sort"
echo ""

echo "========================================="
echo "📊 폴더별 파일 목록"
echo "========================================="
echo ""

# Instagram
echo "━━━ Instagram ━━━"
ssh crawler "ls -lh ~/PMIK-sns-analysis/instagram/ 2>/dev/null || echo '폴더 없음'"
echo ""

# Kakaostory
echo "━━━ Kakaostory ━━━"
ssh crawler "ls -lh ~/PMIK-sns-analysis/kakaostory/ 2>/dev/null || echo '폴더 없음'"
echo ""

# Naver Blog
echo "━━━ Naver Blog ━━━"
ssh crawler "ls -lh ~/PMIK-sns-analysis/naver_blog/*.{py,yaml,txt} 2>/dev/null | head -20"
echo ""

# YouTube
echo "━━━ YouTube ━━━"
ssh crawler "ls -lh ~/PMIK-sns-analysis/youtube/*.py 2>/dev/null | head -20"
echo ""

# Analysis
echo "━━━ Analysis ━━━"
ssh crawler "ls -lh ~/PMIK-sns-analysis/analysis/ 2>/dev/null || echo '폴더 없음'"
echo ""

# Multimedia Process
echo "━━━ Multimedia Process ━━━"
ssh crawler "ls -lh ~/PMIK-sns-analysis/multimedia-process/ 2>/dev/null || echo '폴더 없음'"
echo ""

echo "========================================="
echo "💾 용량 정보"
echo "========================================="
echo ""
ssh crawler "du -sh ~/PMIK-sns-analysis/* 2>/dev/null | sort -h"
echo ""

echo "========================================="
echo "📝 최근 수정 파일 (7일 이내)"
echo "========================================="
echo ""
ssh crawler "find ~/PMIK-sns-analysis -type f -mtime -7 -not -path '*/.*' -not -path '*/__pycache__/*' -exec ls -lh {} \; | awk '{print \$6, \$7, \$8, \$9}' | sort -r | head -20"
echo ""

echo "✅ 완료"
