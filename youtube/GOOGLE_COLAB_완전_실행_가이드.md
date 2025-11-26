# 🚀 Google Colab YouTube 크롤러 완전 실행 가이드

## 📋 목차
1. [RAM/GPU 설정](#ramgpu-설정)
2. [파일 준비](#파일-준비)
3. [실행 순서](#실행-순서)
4. [문제 해결](#문제-해결)

---

## 🎛️ RAM/GPU 설정

### 1단계: 런타임 설정 (필수!)

Google Colab 상단 메뉴에서:
```
런타임 > 런타임 유형 변경
```

### 2단계: 권장 설정

**무료 사용자:**
- **하드웨어 가속기**: `GPU` (T4)
- **런타임 모양**: `고용량 RAM`

**Colab Pro 사용자:**
- **하드웨어 가속기**: `GPU` (A100 또는 V100)
- **런타임 모양**: `고용량 RAM` 또는 `프리미엄`

### 3단계: RAM/GPU 옵션 설명

| 옵션 | RAM | 설명 |
|------|-----|------|
| **표준** | 12.7GB | 기본 (작동 가능하나 불안정) |
| **고용량 RAM** | 25.5GB | ✅ **권장** (안정적) |
| **프리미엄** | 51GB | 대용량 처리용 |

| GPU | 속도 | 설명 |
|-----|------|------|
| **없음** | 1x | ❌ 45분 내 완료 불가능 |
| **T4** | 5x | ✅ **권장** (무료) |
| **V100** | 10x | Pro 전용 |
| **A100** | 15x | Pro+ 전용 |

### 왜 GPU가 필요한가?

- **Whisper AI**: GPU 사용시 5-10배 빠름
- **EasyOCR**: GPU 사용시 3-5배 빠름
- **45분 제한**: GPU 없으면 시간 내 완료 불가

---

## 📁 파일 준비

### 필요한 파일 (2개)

1. **`.env`** - YouTube API 키 포함
   ```
   YOUTUBE_API_KEY=실제_유튜브_API_키
   ```

2. **`youtube_crawler_v3_1_test.py`** - 크롤러 메인 파일

### API 키 발급 방법

1. https://console.cloud.google.com/ 접속
2. 새 프로젝트 생성
3. "API 및 서비스" > "라이브러리" 클릭
4. "YouTube Data API v3" 검색 후 활성화
5. "사용자 인증 정보" > "API 키" 생성
6. `.env` 파일에 저장

---

## 🎯 실행 순서

### 셀 1: 환경 설정 및 GPU/RAM 확인

```python
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
from google.colab import drive
drive.mount('/content/drive')

# 작업 디렉토리 생성
import os
os.makedirs('/content/drive/MyDrive/youtube_crawl_results', exist_ok=True)

print("\n✅ Google Drive 마운트 완료!")
print("📂 결과 저장 위치: /content/drive/MyDrive/youtube_crawl_results")

print("\n" + "="*60)
print("🎉 환경 설정 완료!")
print("="*60)
print("\n다음 단계: 셀 2 실행 (파일 업로드)")
```

**예상 소요시간**: 2-3분

---

### 셀 2: 파일 업로드 및 API 키 설정

```python
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
    if '.env' not in env_uploaded:
        raise ValueError("❌ .env 파일을 찾을 수 없습니다!")
    
    env_content = env_uploaded['.env'].decode('utf-8')
    
    for line in env_content.split('\n'):
        line = line.strip()
        if line.startswith('YOUTUBE_API_KEY='):
            api_key = line.split('=', 1)[1].strip()
            api_key = api_key.strip('"').strip("'")
            
            if api_key and api_key != 'your_youtube_api_key_here':
                return api_key
            else:
                raise ValueError("❌ .env 파일에 유효한 API 키가 없습니다!")
    
    raise ValueError("❌ .env 파일에서 YOUTUBE_API_KEY를 찾을 수 없습니다!")

try:
    api_key = read_api_key_from_env()
    print(f"✅ API 키 로드 성공: {api_key[:10]}...")
    
    print("\n🔧 크롤러 파일에 API 키 설정 중...")
    
    with open('youtube_crawler_v3_1_test.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace('YOUR_YOUTUBE_API_KEY_HERE', api_key)
    
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
```

**예상 소요시간**: 1분

---

### 셀 3: 백그라운드 크롤러 실행

```python
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

print("\n🔄 크롤러 시작 중...")

subprocess.Popen(
    ['nohup', 'python3', 'youtube_crawler_v3_1_test.py'],
    stdout=open('/content/drive/MyDrive/crawler.log', 'w'),
    stderr=subprocess.STDOUT
)

time.sleep(3)

result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)

if 'youtube_crawler_v3_1_test.py' in result.stdout:
    print("✅ 크롤러 백그라운드 실행 시작!")
    print("\n📋 중요 사항:")
    print("   ✅ 노트북을 종료해도 계속 실행됩니다")
    print("   ✅ 45분 후 자동 종료됩니다")
    print("   ✅ 결과는 Google Drive에 자동 저장됩니다")
    print("\n📊 진행 상황 확인: 셀 4 실행")
else:
    print("❌ 크롤러 시작 실패")

print("\n" + "="*60)
print("다음 단계: 셀 4 실행 (모니터링)")
print("="*60)
```

**예상 소요시간**: 즉시 (백그라운드 실행)

---

### 셀 4: 실시간 모니터링 (선택사항)

```python
import time
import os
import subprocess

print("="*60)
print("📊 크롤러 실시간 모니터링")
print("="*60)
print("\n⚠️ 이 셀을 중단해도 크롤러는 계속 실행됩니다")
print("⏱️ 1분마다 상태를 확인합니다\n")

def check_process():
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    return 'youtube_crawler_v3_1_test.py' in result.stdout

def show_log(lines=20):
    log_path = '/content/drive/MyDrive/crawler.log'
    if os.path.exists(log_path):
        result = subprocess.run(['tail', f'-{lines}', log_path], capture_output=True, text=True)
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
        
        print("\n📋 최신 로그 (최근 15줄):")
        print("-" * 60)
        print(show_log(15))
        print("-" * 60)
        
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
except Exception as e:
    print(f"\n❌ 모니터링 오류: {e}")
```

**참고**: 이 셀은 선택사항입니다. 중단해도 크롤러는 계속 실행됩니다.

---

### 셀 5: 결과 확인 및 다운로드

```python
import pandas as pd
import glob
import os
from google.colab import files

print("="*60)
print("📊 크롤링 결과 확인")
print("="*60)

result_dir = '/content/drive/MyDrive/youtube_crawl_results'
csv_files = glob.glob(f'{result_dir}/*.csv')
csv_files = [f for f in csv_files if 'youtube_pm_v3_1_colab' in f]
csv_files = sorted(csv_files, key=os.path.getmtime, reverse=True)

if not csv_files:
    print("\n❌ 결과 파일을 찾을 수 없습니다.")
    log_path = '/content/drive/MyDrive/crawler.log'
    if os.path.exists(log_path):
        print("\n📋 로그 내용 (마지막 30줄):")
        with open(log_path, 'r') as f:
            lines = f.readlines()
            print(''.join(lines[-30:]))
else:
    latest_file = csv_files[0]
    file_name = os.path.basename(latest_file)
    file_size = os.path.getsize(latest_file) / 1024 / 1024
    
    print(f"\n✅ 최신 결과 파일 발견!")
    print(f"📁 파일명: {file_name}")
    print(f"💾 크기: {file_size:.2f} MB")
    
    df = pd.read_csv(latest_file)
    
    print("\n" + "="*60)
    print("📈 수집 통계")
    print("="*60)
    
    total_videos = len(df)
    print(f"\n🎬 총 비디오: {total_videos}개")
    
    if 'transcript_text' in df.columns:
        with_transcript = (df['transcript_text'].notna() & (df['transcript_text'] != '')).sum()
        print(f"🎤 음성인식 성공: {with_transcript}개 ({with_transcript/total_videos*100:.1f}%)")
    
    if 'thumbnail_text_ocr' in df.columns:
        with_ocr = (df['thumbnail_text_ocr'].notna() & (df['thumbnail_text_ocr'] != '')).sum()
        print(f"👁️ 썸네일 OCR 성공: {with_ocr}개 ({with_ocr/total_videos*100:.1f}%)")
    
    download = input("\n결과 파일을 다운로드하시겠습니까? (y/n): ").lower().strip()
    
    if download == 'y':
        print("\n📥 다운로드 중...")
        files.download(latest_file)
        print("✅ 다운로드 완료!")
    else:
        print(f"\n📁 파일 위치: {latest_file}")

print("\n" + "="*60)
print("🎉 모든 작업 완료!")
print("="*60)
```

---

## 🔧 문제 해결

### Q1: GPU가 할당되지 않았습니다

**해결**: 런타임 > 런타임 유형 변경 > GPU 선택

### Q2: RAM 부족 오류

**해결**: 런타임 > 런타임 유형 변경 > 고용량 RAM 선택

### Q3: API 키 오류

**해결**: 
- .env 파일 형식 확인: `YOUTUBE_API_KEY=키값`
- 따옴표 제거
- API 키 활성화 확인

### Q4: 45분 내 완료되지 않음

**해결**:
- GPU 사용 확인
- 고용량 RAM 사용
- 목표 개수 줄이기 (300 → 200)

### Q5: 크롤러가 중단됨

**해결**:
- 로그 파일 확인: `/content/drive/MyDrive/crawler.log`
- 체크포인트에서 재시작 가능

---

## 📊 예상 결과 (45분 기준)

- **수집량**: 100-200개 비디오
- **음성인식**: 70-80% 성공률
- **썸네일 OCR**: 85-90% 성공률
- **전화번호 추출**: 실제 작동
- **후원번호 추출**: 실제 작동

---

## ✅ 체크리스트

- [ ] GPU 설정 완료 (T4 이상)
- [ ] 고용량 RAM 설정 완료
- [ ] .env 파일 준비 (API 키 포함)
- [ ] youtube_crawler_v3_1_test.py 파일 준비
- [ ] 셀 1 실행 (환경 설정)
- [ ] 셀 2 실행 (파일 업로드)
- [ ] 셀 3 실행 (크롤러 시작)
- [ ] 45분 대기
- [ ] 셀 5 실행 (결과 확인)

---

**🎉 성공적인 크롤링을 기원합니다!**
