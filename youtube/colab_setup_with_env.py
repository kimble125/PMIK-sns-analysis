#!/usr/bin/env python3
"""
Google Colab용 .env 파일을 이용한 API 키 자동 설정
"""

COLAB_ENV_SETUP = '''
# [셀 1] 환경 설정 및 라이브러리 설치
!pip install -q yt-dlp openai-whisper easyocr opencv-python-headless 
!pip install -q youtube-transcript-api google-api-python-client tqdm python-dotenv

# Google Drive 마운트
from google.colab import drive
drive.mount('/content/drive')

print("✅ 환경 설정 완료!")
'''

COLAB_ENV_READER = '''
# [셀 2] .env 파일 업로드 및 API 키 자동 설정
import os
import re
from google.colab import files

# .env 파일 업로드
print("📤 .env 파일을 업로드하세요...")
uploaded = files.upload()

# .env 파일에서 API 키 읽기
def read_env_file(env_filename):
    """
    .env 파일에서 YouTube API 키를 읽어옵니다.
    """
    if env_filename not in uploaded:
        raise ValueError("❌ .env 파일을 찾을 수 없습니다!")
    
    # .env 파일 내용 읽기
    env_content = uploaded[env_filename].decode('utf-8')
    
    # YOUTUBE_API_KEY 값 추출
    for line in env_content.split('\\n'):
        if line.strip().startswith('YOUTUBE_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            # 따옴표 제거
            api_key = api_key.strip('"').strip("'")
            
            if api_key and api_key != 'your_youtube_api_key_here':
                return api_key
            else:
                raise ValueError("❌ .env 파일에 유효한 API 키가 설정되지 않았습니다!")
    
    raise ValueError("❌ .env 파일에서 YOUTUBE_API_KEY를 찾을 수 없습니다!")

# API 키 읽기
try:
    api_key = read_env_file('.env')
    print(f"✅ API 키 로드 성공: {api_key[:8]}...")
    
    # 크롤러 파일에 API 키 설정
    print("🔧 크롤러 파일에 API 키 설정 중...")
    
    # youtube_crawler_v3_1_test.py 읽기
    with open('youtube_crawler_v3_1_test.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # API 키 교체
    content = content.replace('YOUR_YOUTUBE_API_KEY_HERE', api_key)
    
    # 수정된 파일 저장
    with open('youtube_crawler_v3_1_test.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ API 키 설정 완료!")
    print("🚀 이제 크롤러를 실행할 준비가 되었습니다.")
    
except Exception as e:
    print(f"❌ 오류: {e}")
    print("\\n📋 해결 방법:")
    print("1. .env 파일에 올바른 YouTube API 키가 설정되어 있는지 확인")
    print("2. 파일 형식: YOUTUBE_API_KEY=실제_API_키")
    print("3. API 키에 따옴표가 없는지 확인")
'''

COLAB_RUNNER = '''
# [셀 3] 백그라운드 크롤러 실행
!nohup python3 youtube_crawler_v3_1_test.py > /content/drive/MyDrive/crawler.log 2>&1 &

print("🚀 YouTube 크롤러 백그라운드 실행 시작!")
print("⏰ 45분 동안 실행됩니다.")
print("📋 노트북을 종료해도 계속 실행됩니다.")
print("📁 결과는 Google Drive에 자동 저장됩니다.")
'''

COLAB_MONITOR = '''
# [셀 4] 실시간 진행 상황 모니터링
import time
import os

def monitor_crawler():
    """크롤러 진행 상황을 실시간으로 모니터링합니다."""
    print("📊 크롤러 모니터링 시작")
    print("=" * 60)
    
    while True:
        try:
            # 로그 파일 확인
            if os.path.exists('/content/drive/MyDrive/crawler.log'):
                print(f"\\n🕒 {time.strftime('%H:%M:%S')} - 최신 로그:")
                !tail -15 /content/drive/MyDrive/crawler.log
            else:
                print(f"🕒 {time.strftime('%H:%M:%S')} - 로그 파일 대기 중...")
            
            # 프로세스 확인
            result = !ps aux | grep "youtube_crawler_v3_1_test.py" | grep -v grep
            if result:
                print("✅ 크롤러 실행 중")
            else:
                print("❌ 크롤러 종료됨")
                break
                
            print("-" * 60)
            time.sleep(60)  # 1분마다 체크
            
        except KeyboardInterrupt:
            print("\\n🛑 모니터링 중단")
            break
        except Exception as e:
            print(f"⚠️ 모니터링 오류: {e}")
            time.sleep(30)

# 모니터링 실행
monitor_crawler()
'''

COLAB_RESULTS = '''
# [셀 5] 결과 확인 및 다운로드
import pandas as pd
import glob
import os
from google.colab import files

# 결과 파일 검색
result_files = glob.glob('/content/drive/MyDrive/youtube_crawl_results/*.csv')
result_files = sorted(result_files, key=os.path.getmtime, reverse=True)

if result_files:
    latest_file = result_files[0]
    print(f"📁 최신 결과 파일: {os.path.basename(latest_file)}")
    
    # 결과 미리보기
    df = pd.read_csv(latest_file)
    print(f"\\n📊 수집 결과:")
    print(f"   - 총 비디오: {len(df)}개")
    
    # 멀티미디어 처리 통계
    with_transcript = (df['transcript_text'].notna() & (df['transcript_text'] != '')).sum()
    with_thumbnail_ocr = (df['thumbnail_text_ocr'].notna() & (df['thumbnail_text_ocr'] != '')).sum()
    
    print(f"   - 음성인식 성공: {with_transcript}개 ({with_transcript/len(df)*100:.1f}%)")
    print(f"   - 썸네일 OCR 성공: {with_thumbnail_ocr}개 ({with_thumbnail_ocr/len(df)*100:.1f}%)")
    
    # 샘플 데이터 표시
    print(f"\\n📋 샘플 데이터 (상위 3개):")
    display_columns = ['title', 'channel_name', 'view_count', 'transcript_source']
    if all(col in df.columns for col in display_columns):
        print(df[display_columns].head(3).to_string(index=False))
    
    # 파일 다운로드 옵션
    print(f"\\n💾 결과 다운로드:")
    download_choice = input("다운로드하시겠습니까? (y/n): ").lower()
    
    if download_choice == 'y':
        files.download(latest_file)
        print("✅ 다운로드 완료!")
    else:
        print("📁 파일 위치:", latest_file)
        
else:
    print("❌ 결과 파일을 찾을 수 없습니다.")
    print("📋 확인사항:")
    print("   1. 크롤러가 정상 실행되었는지 확인")
    print("   2. 로그 파일 확인: /content/drive/MyDrive/crawler.log")
'''

print("📝 Google Colab 실행 가이드:")
print("=" * 60)
print()
print("1️⃣ 환경 설정:")
print(COLAB_ENV_SETUP)
print()
print("2️⃣ .env 파일로 API 키 자동 설정:")
print(COLAB_ENV_READER)
print()
print("3️⃣ 백그라운드 실행:")
print(COLAB_RUNNER)
print()
print("4️⃣ 진행 상황 모니터링:")
print(COLAB_MONITOR)
print()
print("5️⃣ 결과 확인:")
print(COLAB_RESULTS)
