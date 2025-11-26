#!/bin/bash

echo "=================================="
echo "🚀 YouTube Crawler v3.1 로컬 실행"
echo "=================================="
echo ""
echo "⏰ 실행시간: 10분"
echo "🎯 목표: 100개 비디오"
echo "💾 체크포인트: 2분마다"
echo ""

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo "⚠️ 가상환경이 없습니다. 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# 필수 라이브러리 설치
echo "📦 라이브러리 확인 중..."
pip install -q python-dotenv yt-dlp openai-whisper easyocr opencv-python \
    youtube-transcript-api google-api-python-client pandas tqdm pillow requests

echo ""
echo "🎬 크롤러 시작..."
echo "=================================="
echo ""

# 크롤러 실행
python3 youtube_crawler_v3_1_test.py

echo ""
echo "=================================="
echo "✅ 크롤러 종료"
echo "=================================="
echo ""
echo "📁 결과 확인:"
echo "   - CSV: ./output/"
echo "   - 로그: ./logs/crawler.log"
echo "   - 체크포인트: ./checkpoints/"
