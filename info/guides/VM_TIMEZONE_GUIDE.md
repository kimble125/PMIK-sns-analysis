# VM 시간대(Timezone) 가이드

## 📅 현재 상황

### 로컬 맥북
```bash
$ date
Tue Nov 18 15:49:56 KST 2025
# KST = Korea Standard Time (한국 표준시)
# UTC+9 (UTC보다 9시간 빠름)
```

### VM (Crawler & Analyst)
```bash
$ date
Tue Nov 18 06:49:56 UTC 2025
# UTC = Coordinated Universal Time (협정 세계시)
# UTC+0 (기준 시간)
```

### 시간 차이
- **한국시간 15:49** = **UTC 06:49**
- **차이: 9시간** (한국이 9시간 빠름)

---

## 🌍 왜 VM은 UTC를 사용하나?

### 1. Azure 기본 설정
- **Azure VM의 기본 시간대: UTC**
- 전 세계 어디서나 동일한 기준 시간 사용
- 글로벌 서비스 운영에 적합

### 2. 서버 운영 표준
대부분의 클라우드 서버는 UTC를 사용합니다:

| 클라우드 | 기본 시간대 |
|---------|-----------|
| AWS EC2 | UTC |
| Azure VM | UTC |
| Google Cloud | UTC |
| DigitalOcean | UTC |

### 3. UTC 사용의 장점

#### ✅ 장점
1. **일관성**: 전 세계 어디서나 동일한 시간
2. **DST 없음**: 서머타임(일광절약시간) 문제 없음
3. **로그 분석**: 여러 서버 로그 비교 용이
4. **협업**: 다국적 팀 협업 시 혼란 방지
5. **데이터베이스**: 타임스탬프 저장 시 표준

#### ❌ 단점
1. **가독성**: 한국 시간으로 변환 필요
2. **혼란**: 처음 사용 시 헷갈림

---

## 📊 파일명 시간 비교

### 로컬 파일 (한국시간)
```
youtube_pm_v3_test_20251118_084908.csv
                    ^^^^^^^^^^^^^^
                    2025-11-18 08:49:08 KST
```

### VM 파일 (UTC)
```
naver_blog_pm_v9_1_final_20251117_124720.csv
                         ^^^^^^^^^^^^^^
                         2025-11-17 12:47:20 UTC
                         = 2025-11-17 21:47:20 KST
```

### 시간 변환 예시

| UTC 시간 | 한국 시간 (UTC+9) | 설명 |
|---------|------------------|------|
| 2025-11-17 06:04:29 | 2025-11-17 15:04:29 | 크롤러 시작 |
| 2025-11-17 12:47:20 | 2025-11-17 21:47:20 | 크롤러 종료 |
| 2025-11-18 00:00:00 | 2025-11-18 09:00:00 | 자정 |

---

## 🔧 시간대 변경 방법

### 방법 1: VM 시간대를 한국시간으로 변경 (권장하지 않음)

```bash
# VM에 접속
ssh crawler

# 현재 시간대 확인
timedatectl

# 사용 가능한 시간대 목록
timedatectl list-timezones | grep Seoul

# 한국 시간대로 변경
sudo timedatectl set-timezone Asia/Seoul

# 확인
date
# Tue Nov 18 15:49:56 KST 2025
```

**⚠️ 주의사항**:
- 서버는 UTC 유지가 표준
- 변경 시 다른 시스템과 혼란 가능
- 로그 분석 시 문제 발생 가능

### 방법 2: 코드에서 시간대 변환 (권장)

#### Python 코드 예시

```python
from datetime import datetime
import pytz

# UTC 시간 생성
utc_time = datetime.now(pytz.UTC)
print(f"UTC: {utc_time}")

# 한국 시간으로 변환
kst = pytz.timezone('Asia/Seoul')
kst_time = utc_time.astimezone(kst)
print(f"KST: {kst_time}")

# 파일명에 한국 시간 사용
filename = f"data_{kst_time.strftime('%Y%m%d_%H%M%S')}.csv"
print(f"파일명: {filename}")
```

#### 크롤러 코드 수정 예시

```python
# 기존 코드 (UTC)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"naver_blog_pm_{timestamp}.csv"
# 결과: naver_blog_pm_20251117_124720.csv (UTC)

# 수정 코드 (KST)
from datetime import datetime
import pytz

kst = pytz.timezone('Asia/Seoul')
timestamp = datetime.now(kst).strftime('%Y%m%d_%H%M%S')
filename = f"naver_blog_pm_{timestamp}.csv"
# 결과: naver_blog_pm_20251117_214720.csv (KST)
```

---

## 📋 실전 가이드

### 1. 파일명으로 실제 시간 알기

#### UTC 파일명 → 한국시간 변환
```bash
# 파일명: naver_blog_pm_v9_1_final_20251117_124720.csv
# UTC: 2025-11-17 12:47:20
# KST: 2025-11-17 21:47:20 (UTC + 9시간)
```

**간단 계산법**:
- UTC 시간 + 9시간 = 한국시간
- 단, 24시를 넘으면 날짜도 +1

**예시**:
```
UTC 12:47 → KST 21:47 (같은 날)
UTC 18:00 → KST 03:00 (다음 날)
UTC 23:00 → KST 08:00 (다음 날)
```

### 2. 로그 시간 해석

#### VM 로그 (UTC)
```
2025-11-17 06:04:29 [INFO] 🚀 크롤러 시작
2025-11-17 12:47:20 [INFO] 🏁 크롤링 완료
```

#### 한국시간으로 해석
```
2025-11-17 15:04:29 (오후 3시) - 크롤러 시작
2025-11-17 21:47:20 (오후 9시) - 크롤링 완료
```

### 3. 크론잡 설정 시 주의

#### VM에서 크론잡 설정 (UTC 기준)
```bash
# 한국시간 오전 6시에 실행하려면?
# UTC로는 전날 21시 (6시 - 9시간)
0 21 * * * /path/to/script.sh

# 한국시간 자정에 실행하려면?
# UTC로는 전날 15시
0 15 * * * /path/to/script.sh
```

---

## 🛠️ 유틸리티 함수

### Bash 스크립트

```bash
#!/bin/bash

# UTC를 KST로 변환
utc_to_kst() {
    local utc_time="$1"
    TZ='Asia/Seoul' date -d "$utc_time" '+%Y-%m-%d %H:%M:%S'
}

# 사용 예시
utc_to_kst "2025-11-17 12:47:20"
# 출력: 2025-11-17 21:47:20
```

### Python 함수

```python
from datetime import datetime
import pytz

def utc_to_kst(utc_time_str):
    """UTC 시간 문자열을 KST로 변환"""
    utc = pytz.UTC
    kst = pytz.timezone('Asia/Seoul')
    
    # UTC 시간 파싱
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_time = utc.localize(utc_time)
    
    # KST로 변환
    kst_time = utc_time.astimezone(kst)
    return kst_time.strftime('%Y-%m-%d %H:%M:%S')

# 사용 예시
print(utc_to_kst("2025-11-17 12:47:20"))
# 출력: 2025-11-17 21:47:20
```

---

## 📊 권장 사항

### 1. VM 시간대 설정
**권장**: UTC 유지 ✅
- 서버 운영 표준
- 글로벌 협업 용이
- 로그 분석 일관성

**비권장**: 한국시간으로 변경 ❌
- 표준에서 벗어남
- 다른 시스템과 혼란
- DST 문제 가능성

### 2. 코드 작성 시
```python
# ✅ 권장: 명시적 시간대 사용
from datetime import datetime
import pytz

kst = pytz.timezone('Asia/Seoul')
now_kst = datetime.now(kst)

# ❌ 비권장: 시스템 시간 의존
now = datetime.now()  # 시스템 시간대에 따라 다름
```

### 3. 파일명 규칙
```python
# 옵션 1: UTC 사용 + 명시
filename = f"data_{utc_time.strftime('%Y%m%d_%H%M%S')}_UTC.csv"

# 옵션 2: KST 사용 + 명시
filename = f"data_{kst_time.strftime('%Y%m%d_%H%M%S')}_KST.csv"

# 옵션 3: ISO 8601 형식 (타임존 포함)
filename = f"data_{kst_time.isoformat()}.csv"
# 예: data_2025-11-17T21:47:20+09:00.csv
```

---

## 🎯 실전 체크리스트

### VM 파일 다운로드 시
- [ ] 파일명의 시간이 UTC임을 인지
- [ ] 필요 시 한국시간으로 변환
- [ ] 로그 시간도 UTC임을 확인

### 크론잡 설정 시
- [ ] 원하는 실행 시간이 한국시간인지 확인
- [ ] UTC로 9시간 빼서 설정
- [ ] 날짜 변경 여부 확인

### 코드 작성 시
- [ ] 명시적으로 시간대 지정
- [ ] pytz 라이브러리 사용
- [ ] 파일명에 시간대 표시 (선택)

---

## 📞 빠른 참조

### 시간 변환 공식
```
KST = UTC + 9시간
UTC = KST - 9시간
```

### 주요 시간대
```
UTC+0  : 런던 (겨울), 리스본
UTC+1  : 파리, 베를린, 로마
UTC+5  : 파키스탄
UTC+8  : 중국, 싱가포르, 홍콩
UTC+9  : 한국, 일본, 인도네시아 (동부)
UTC-5  : 뉴욕 (겨울)
UTC-8  : 로스앤젤레스 (겨울)
```

### 온라인 도구
- https://www.timeanddate.com/worldclock/converter.html
- https://www.worldtimebuddy.com/

---

**작성일**: 2025년 11월 18일  
**작성자**: PMI Korea 데이터 분석팀
