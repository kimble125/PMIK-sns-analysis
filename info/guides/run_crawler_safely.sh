#!/bin/bash
# 크롤러 안전 실행 스크립트

echo "🚀 크롤러 안전 실행 스크립트"
echo "================================"
echo ""

# 1. 환경 확인
echo "📋 [1/6] 환경 확인 중..."
if [ ! -f ~/PMIK-sns-analysis/naver_blog/.env ]; then
    echo "❌ .env 파일이 없습니다!"
    echo "   ~/PMIK-sns-analysis/naver_blog/.env 파일을 생성하세요."
    exit 1
fi
echo "✅ .env 파일 확인"

# 2. 가상환경 확인
echo ""
echo "📋 [2/6] 가상환경 확인 중..."
if [ ! -d ~/PMIK-sns-analysis/.venv ]; then
    echo "❌ 가상환경이 없습니다!"
    echo "   python3 -m venv ~/PMIK-sns-analysis/.venv"
    exit 1
fi
echo "✅ 가상환경 확인"

# 3. 로그 디렉토리 생성
echo ""
echo "📋 [3/6] 로그 디렉토리 생성..."
mkdir -p ~/logs
mkdir -p ~/shared_data/raw_data/naver_blog
echo "✅ 디렉토리 생성 완료"

# 4. 기존 Screen 세션 확인
echo ""
echo "📋 [4/6] 기존 Screen 세션 확인..."
screen -ls | grep kimble_crawler
if [ $? -eq 0 ]; then
    echo "⚠️  기존 kimble_crawler 세션이 있습니다."
    echo "   계속하려면 Enter, 취소하려면 Ctrl+C"
    read
fi

# 5. 타임스탬프 생성
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SESSION_NAME="kimble_crawler_${TIMESTAMP}"
LOG_FILE="$HOME/logs/crawler_${TIMESTAMP}.log"

echo ""
echo "📋 [5/6] Screen 세션 시작..."
echo "   세션명: $SESSION_NAME"
echo "   로그파일: $LOG_FILE"
echo ""

# 6. Screen 세션 시작 및 크롤러 실행
echo "📋 [6/6] 크롤러 실행 중..."
echo ""
echo "⚠️  주의사항:"
echo "   1. 크롤러가 시작되면 화면에 로그가 출력됩니다"
echo "   2. 'Ctrl + A, D'를 눌러 Screen에서 나가세요"
echo "   3. 그 후 'exit'로 SSH를 종료하면 맥북을 끌 수 있습니다"
echo ""
echo "계속하려면 Enter를 누르세요..."
read

# Screen 세션 시작
screen -dmS "$SESSION_NAME" bash -c "
    cd ~/PMIK-sns-analysis/naver_blog && \
    source ../.venv/bin/activate && \
    echo '🚀 크롤러 시작: $(date)' | tee -a $LOG_FILE && \
    echo '================================' | tee -a $LOG_FILE && \
    python pm_naver_blog_crawler_v8_4_final.py 2>&1 | tee -a $LOG_FILE
"

echo ""
echo "✅ Screen 세션 시작 완료!"
echo ""
echo "📊 상태 확인:"
echo "   screen -r $SESSION_NAME  # 세션 재접속"
echo "   tail -f $LOG_FILE        # 로그 실시간 확인"
echo ""
echo "🎯 다음 단계:"
echo "   1. 잠시 후 'screen -r $SESSION_NAME'로 접속해서 크롤러 실행 확인"
echo "   2. 정상 실행 중이면 'Ctrl + A, D'로 나가기"
echo "   3. 'exit'로 SSH 종료"
echo "   4. 맥북 종료 가능!"
echo ""
