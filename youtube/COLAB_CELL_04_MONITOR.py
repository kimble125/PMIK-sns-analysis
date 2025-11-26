"""
Google Colab - 셀 4: 실시간 모니터링
"""

import time
import os
import subprocess

print("="*60)
print("📊 크롤러 실시간 모니터링")
print("="*60)
print("\n⚠️ 이 셀을 중단해도 크롤러는 계속 실행됩니다")
print("⏱️ 1분마다 상태를 확인합니다\n")

def check_process():
    """크롤러 프로세스 확인"""
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True,
        text=True
    )
    return 'youtube_crawler_v3_1_test.py' in result.stdout

def show_log(lines=20):
    """로그 파일 표시"""
    log_path = '/content/drive/MyDrive/crawler.log'
    if os.path.exists(log_path):
        result = subprocess.run(
            ['tail', f'-{lines}', log_path],
            capture_output=True,
            text=True
        )
        return result.stdout
    return "로그 파일 없음"

try:
    iteration = 0
    while True:
        iteration += 1
        current_time = time.strftime('%H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"🕒 {current_time} - 체크 #{iteration}")
        print(f"{'='*60}")
        
        # 프로세스 확인
        is_running = check_process()
        if is_running:
            print("✅ 크롤러 실행 중")
        else:
            print("❌ 크롤러 종료됨")
            print("\n📋 최종 로그:")
            print(show_log(30))
            print("\n🏁 크롤러가 종료되었습니다.")
            print("📁 결과 확인: 셀 5 실행")
            break
        
        # 로그 표시
        print("\n📋 최신 로그 (최근 15줄):")
        print("-" * 60)
        print(show_log(15))
        print("-" * 60)
        
        # 체크포인트 파일 확인
        checkpoint_dir = '/content/drive/MyDrive/youtube_crawl_results'
        if os.path.exists(checkpoint_dir):
            checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint')]
            if checkpoint_files:
                latest_checkpoint = sorted(checkpoint_files)[-1]
                print(f"\n💾 최신 체크포인트: {latest_checkpoint}")
        
        print(f"\n⏳ 다음 체크: 60초 후...")
        time.sleep(60)
        
except KeyboardInterrupt:
    print("\n\n🛑 모니터링 중단")
    print("⚠️ 크롤러는 백그라운드에서 계속 실행됩니다")
    print("📋 재확인: 이 셀을 다시 실행하세요")
except Exception as e:
    print(f"\n❌ 모니터링 오류: {e}")
