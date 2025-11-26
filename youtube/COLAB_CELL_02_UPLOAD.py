"""
Google Colab - 셀 2: 파일 업로드 및 API 키 설정
"""

from google.colab import files
import os

print("="*60)
print("📤 파일 업로드")
print("="*60)

# 1. .env 파일 업로드
print("\n1️⃣ .env 파일을 업로드하세요 (YouTube API 키 포함)")
print("   형식: YOUTUBE_API_KEY=실제_API_키")
env_uploaded = files.upload()

# 2. youtube_crawler_v3_1_test.py 업로드
print("\n2️⃣ youtube_crawler_v3_1_test.py 파일을 업로드하세요")
crawler_uploaded = files.upload()

print("\n✅ 파일 업로드 완료!")

# .env에서 API 키 읽기
print("\n" + "="*60)
print("🔑 API 키 설정")
print("="*60)

def read_api_key_from_env():
    """
    .env 파일에서 YouTube API 키를 읽어옵니다.
    """
    if '.env' not in env_uploaded:
        raise ValueError("❌ .env 파일을 찾을 수 없습니다!")
    
    env_content = env_uploaded['.env'].decode('utf-8')
    
    for line in env_content.split('\n'):
        line = line.strip()
        if line.startswith('YOUTUBE_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            # 따옴표 제거
            api_key = api_key.strip('"').strip("'")
            
            if api_key and api_key != 'your_youtube_api_key_here':
                return api_key
            else:
                raise ValueError("❌ .env 파일에 유효한 API 키가 없습니다!")
    
    raise ValueError("❌ .env 파일에서 YOUTUBE_API_KEY를 찾을 수 없습니다!")

try:
    # API 키 읽기
    api_key = read_api_key_from_env()
    print(f"✅ API 키 로드 성공: {api_key[:10]}...")
    
    # 크롤러 파일에 API 키 적용
    print("\n🔧 크롤러 파일에 API 키 설정 중...")
    
    with open('youtube_crawler_v3_1_test.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # API 키 교체
    content = content.replace('YOUR_YOUTUBE_API_KEY_HERE', api_key)
    
    # 수정된 파일 저장
    with open('youtube_crawler_v3_1_test.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ API 키 설정 완료!")
    
    print("\n" + "="*60)
    print("🎉 설정 완료!")
    print("="*60)
    print("\n다음 단계: 셀 3 실행 (크롤러 시작)")
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    print("\n📋 해결 방법:")
    print("1. .env 파일 형식 확인: YOUTUBE_API_KEY=실제_API_키")
    print("2. API 키에 따옴표가 없는지 확인")
    print("3. API 키가 유효한지 확인")
    raise
