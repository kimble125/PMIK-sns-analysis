"""
Google Colab - 셀 3: 백그라운드 크롤러 실행
"""

import subprocess
import time
import os

print("="*60)
print("🚀 YouTube 크롤러 백그라운드 실행")
print("="*60)

print("\n📋 실행 정보:")
print("   ⏰ 실행시간: 45분")
print("   🛡️ 안전 종료: 40분 후")
print("   🎯 목표: 최대 300개 비디오")
print("   💾 체크포인트: 5분마다")
print("   📁 결과 위치: /content/drive/MyDrive/youtube_crawl_results/")

# 백그라운드 실행
print("\n🔄 크롤러 시작 중...")

# nohup으로 백그라운드 실행
subprocess.Popen(
    ['nohup', 'python3', 'youtube_crawler_v3_1_test.py'],
    stdout=open('/content/drive/MyDrive/crawler.log', 'w'),
    stderr=subprocess.STDOUT
)

time.sleep(3)  # 시작 대기

# 프로세스 확인
result = subprocess.run(
    ['ps', 'aux'],
    capture_output=True,
    text=True
)

if 'youtube_crawler_v3_1_test.py' in result.stdout:
    print("✅ 크롤러 백그라운드 실행 시작!")
    print("\n📋 중요 사항:")
    print("   ✅ 노트북을 종료해도 계속 실행됩니다")
    print("   ✅ 45분 후 자동 종료됩니다")
    print("   ✅ 결과는 Google Drive에 자동 저장됩니다")
    print("\n📊 진행 상황 확인: 셀 4 실행")
else:
    print("❌ 크롤러 시작 실패")
    print("\n로그 확인:")
    if os.path.exists('/content/drive/MyDrive/crawler.log'):
        with open('/content/drive/MyDrive/crawler.log', 'r') as f:
            print(f.read())

print("\n" + "="*60)
print("다음 단계: 셀 4 실행 (모니터링)")
print("="*60)
