"""
Google Colab - 셀 1: 환경 설정 및 GPU/RAM 확인
"""

# GPU 및 RAM 확인
print("="*60)
print("🔍 시스템 사양 확인")
print("="*60)

# GPU 확인
print("\n📊 GPU 정보:")
!nvidia-smi --query-gpu=name,memory.total --format=csv

# RAM 확인
print("\n💾 RAM 정보:")
!free -h | grep Mem

# 디스크 확인
print("\n💿 디스크 정보:")
!df -h | grep -E "Filesystem|/content"

print("\n" + "="*60)
print("✅ 시스템 확인 완료!")
print("="*60)

# 라이브러리 설치
print("\n📦 필수 라이브러리 설치 중...")
print("⏱️ 약 2-3분 소요됩니다.\n")

!pip install -q yt-dlp
!pip install -q openai-whisper
!pip install -q easyocr
!pip install -q opencv-python-headless
!pip install -q youtube-transcript-api
!pip install -q google-api-python-client
!pip install -q python-dotenv

print("\n✅ 라이브러리 설치 완료!")

# Google Drive 마운트
print("\n📁 Google Drive 마운트 중...")
print("⚠️ 팝업 창이 나타나면 Google 계정을 선택하고 권한을 허용하세요")

from google.colab import drive
import os

try:
    # 강제 재마운트 옵션 추가
    drive.mount('/content/drive', force_remount=True)
    
    # 작업 디렉토리 생성
    os.makedirs('/content/drive/MyDrive/youtube_crawl_results', exist_ok=True)
    
    print("\n✅ Google Drive 마운트 완료!")
    print("📂 결과 저장 위치: /content/drive/MyDrive/youtube_crawl_results")
    
except Exception as e:
    print(f"\n❌ Google Drive 마운트 실패: {e}")
    print("\n🔧 해결 방법:")
    print("1. 런타임 > 런타임 다시 시작")
    print("2. 브라우저 쿠키/캐시 삭제")
    print("3. 시크릿 모드에서 Colab 열기")
    print("4. 다른 Google 계정으로 시도")
    print("\n💡 또는 로컬 저장 모드로 계속하시겠습니까?")
    
    use_local = input("로컬 저장 모드 사용? (y/n): ").lower().strip()
    
    if use_local == 'y':
        print("\n📁 로컬 저장 모드로 전환")
        os.makedirs('/content/youtube_crawl_results', exist_ok=True)
        print("📂 결과 저장 위치: /content/youtube_crawl_results")
        print("⚠️ 주의: 런타임 종료시 데이터가 삭제됩니다!")
    else:
        raise

print("\n" + "="*60)
print("🎉 환경 설정 완료!")
print("="*60)
print("\n다음 단계: 셀 2 실행 (파일 업로드)")
