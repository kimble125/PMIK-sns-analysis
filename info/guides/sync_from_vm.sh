#!/bin/bash

# VM 코드 동기화 스크립트
# 작성일: 2025-11-21

echo "========================================="
echo "🔄 VM에서 로컬로 파일 동기화 시작"
echo "========================================="
echo ""

# 설정
LOCAL_DIR="$HOME/Documents/IT/PMIK-sns-analysis"
REMOTE_USER="pmi"
REMOTE_HOST="crawler"
REMOTE_DIR="~/PMIK-sns-analysis"

# 동기화할 폴더 목록
FOLDERS=("instagram" "kakaostory" "naver_blog" "youtube")

# 각 폴더 동기화
for folder in "${FOLDERS[@]}"; do
    echo "📁 $folder 동기화 중..."
    
    # 로컬 폴더가 없으면 생성
    mkdir -p "$LOCAL_DIR/$folder"
    
    # rsync로 동기화
    rsync -avz --progress \
        "$REMOTE_HOST:$REMOTE_DIR/$folder/" \
        "$LOCAL_DIR/$folder/" \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ $folder 동기화 완료"
    else
        echo "⚠️  $folder 동기화 실패 (폴더가 없을 수 있음)"
    fi
    echo ""
done

echo "========================================="
echo "🎉 동기화 완료!"
echo "========================================="

# 파일 목록 출력
echo ""
echo "📊 다운로드된 파일:"
for folder in "${FOLDERS[@]}"; do
    if [ -d "$LOCAL_DIR/$folder" ]; then
        echo ""
        echo "[$folder]"
        ls -lh "$LOCAL_DIR/$folder" | tail -n +2
    fi
done
