#!/bin/bash

# Analyst VM 상세 확인 스크립트
# 작성일: 2025-11-21

echo "========================================="
echo "📊 ANALYST VM 상세 현황"
echo "========================================="
echo ""

echo "📁 전체 디렉토리 트리:"
echo ""
ssh analyst "find ~/venvs -maxdepth 3 -type d | sort"
echo ""

echo "========================================="
echo "📊 python_code 폴더 상세"
echo "========================================="
echo ""
ssh analyst "ls -lh ~/venvs/python_code/ 2>/dev/null || echo '폴더 없음'"
echo ""

echo "========================================="
echo "🐍 Python 파일 목록"
echo "========================================="
echo ""
ssh analyst "find ~/venvs/python_code -name '*.py' -type f -exec ls -lh {} \; 2>/dev/null | awk '{print \$5, \$9}'"
echo ""

echo "========================================="
echo "📄 데이터 파일 목록"
echo "========================================="
echo ""
echo "JSON 파일:"
ssh analyst "find ~/venvs/python_code -name '*.json' -type f -exec ls -lh {} \; 2>/dev/null | awk '{print \$5, \$9}'"
echo ""
echo "CSV 파일:"
ssh analyst "find ~/venvs/python_code -name '*.csv' -type f -exec ls -lh {} \; 2>/dev/null | awk '{print \$5, \$9}'"
echo ""
echo "로그 파일:"
ssh analyst "find ~/venvs/python_code -name '*.log' -type f -exec ls -lh {} \; 2>/dev/null | awk '{print \$5, \$9}'"
echo ""

echo "========================================="
echo "💾 용량 정보"
echo "========================================="
echo ""
ssh analyst "du -sh ~/venvs/* 2>/dev/null | sort -h"
echo ""

echo "========================================="
echo "📝 최근 수정 파일 (7일 이내)"
echo "========================================="
echo ""
ssh analyst "find ~/venvs/python_code -type f -mtime -7 -exec ls -lh {} \; 2>/dev/null | awk '{print \$6, \$7, \$8, \$9}' | sort -r | head -20"
echo ""

echo "✅ 완료"
