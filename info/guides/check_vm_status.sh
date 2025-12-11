#!/bin/bash
# VM 상태 자동 체크 스크립트

VM_IP="20.214.48.112"
VM_NAME="CRAWLER VM"

echo "🔍 $VM_NAME 상태 확인 중..."
echo "================================"
echo ""

# 1. Ping 테스트
echo "📡 [1/3] Ping 테스트..."
if ping -c 2 -W 2 $VM_IP > /dev/null 2>&1; then
    echo "✅ Ping 응답 있음"
    PING_OK=true
else
    echo "❌ Ping 응답 없음 (방화벽 차단일 수 있음)"
    PING_OK=false
fi

echo ""

# 2. SSH 포트 확인
echo "🔌 [2/3] SSH 포트(22) 확인..."
if nc -z -w 3 $VM_IP 22 > /dev/null 2>&1; then
    echo "✅ SSH 포트 열림 - VM 실행 중!"
    PORT_OK=true
else
    echo "❌ SSH 포트 닫힘 - VM 중지됨"
    PORT_OK=false
fi

echo ""

# 3. SSH 접속 테스트
echo "🔐 [3/3] SSH 접속 테스트..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes crawler "echo 'connected'" > /dev/null 2>&1; then
    echo "✅ SSH 접속 성공!"
    SSH_OK=true
else
    echo "❌ SSH 접속 실패"
    SSH_OK=false
fi

echo ""
echo "================================"
echo "📊 최종 결과:"
echo ""

if [ "$PORT_OK" = true ] && [ "$SSH_OK" = true ]; then
    echo "✅ VM 정상 작동 중"
    echo ""
    echo "🎯 다음 단계:"
    echo "   ssh crawler"
    exit 0
elif [ "$PORT_OK" = true ] && [ "$SSH_OK" = false ]; then
    echo "⚠️  VM은 켜져있지만 SSH 접속 불가"
    echo ""
    echo "🔧 가능한 원인:"
    echo "   - SSH 키 문제"
    echo "   - 방화벽 규칙 변경"
    echo "   - 사용자 권한 문제"
    echo ""
    echo "🎯 조치:"
    echo "   1. SSH 키 확인: ls -la ~/.ssh/"
    echo "   2. 회사 관리자에게 문의"
    exit 1
else
    echo "❌ VM 중지됨 또는 네트워크 문제"
    echo ""
    echo "🔧 가능한 원인:"
    echo "   - VM이 자동 중지됨"
    echo "   - VM이 수동으로 중지됨"
    echo "   - 네트워크 문제"
    echo ""
    echo "🎯 조치:"
    echo "   1. 회사 관리자에게 VM 시작 요청"
    echo "   2. Azure Portal 접근 권한 요청"
    echo "   3. 또는 Azure CLI 권한 요청"
    exit 1
fi
