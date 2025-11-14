# 앞으로 고민해야 할 사항들

## 📋 목차
1. [크롤링 결과 확인 방법](#1-크롤링-결과-확인-방법)
2. [데이터 관련 고민사항](#2-데이터-관련-고민사항)
3. [인프라 관련 고민사항](#3-인프라-관련-고민사항)
4. [프로세스 관련 고민사항](#4-프로세스-관련-고민사항)
5. [선택해야 할 사항들](#5-선택해야-할-사항들)

---

## 1. 크롤링 결과 확인 방법

### A. Screen 세션 확인
```bash
# VM 접속
ssh crawler

# Screen 세션 목록
screen -ls

# 재접속
screen -r kimble_crawler
```

### B. 파일 확인
```bash
# 최근 생성된 파일 찾기
ssh crawler "find ~/PMIK-sns-analysis -name '*.csv' -mtime -1"
ssh crawler "find ~/shared_data -name '*.csv'"

# 파일 다운로드
scp crawler:~/PMIK-sns-analysis/naver_blog/*.csv ~/Downloads/
```

### C. 로그 확인
```bash
# 크롤러 로그
ssh crawler "ls -lht ~/logs/*.log"
ssh crawler "tail -100 ~/logs/crawler_20251114.log"
```

---

## 2. 데이터 관련 고민사항

### A. 데이터 품질 관리

#### 1) 중복 제거 전략
**현재 문제:**
- 같은 블로그 글이 여러 키워드로 중복 수집
- 수정된 글 재수집 시 중복

**해결 방안:**
```python
# URL 기준 중복 제거
df = df.drop_duplicates(subset=['url'], keep='last')

# PostgreSQL에서 UNIQUE 제약조건
CREATE TABLE naver_blog (
    url VARCHAR(500) UNIQUE NOT NULL
);

# 또는 UPSERT
INSERT INTO naver_blog (...) 
VALUES (...) 
ON CONFLICT (url) DO UPDATE SET ...;
```

**질문:**
- 수정된 글을 어떻게 처리? 
  - [ ] 최신 버전만 유지
  - [ ] 버전 히스토리 저장

#### 2) 데이터 검증
```python
def validate_blog_data(df):
    """데이터 검증"""
    issues = []
    
    # URL 형식 체크
    invalid_urls = df[~df['url'].str.startswith('http')]
    if len(invalid_urls) > 0:
        issues.append(f"잘못된 URL: {len(invalid_urls)}개")
    
    # 필수 필드 체크
    null_titles = df['title'].isna().sum()
    if null_titles > 0:
        issues.append(f"제목 없음: {null_titles}개")
    
    # 날짜 범위 체크
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    future_dates = df[df['created_at'] > datetime.now()]
    if len(future_dates) > 0:
        issues.append(f"미래 날짜: {len(future_dates)}개")
    
    return issues
```

#### 3) 데이터 정제
- **HTML 태그** 제거
- **특수문자** 처리
- **이모지** 처리
- **공백** 정규화

### B. 데이터 저장 전략

#### 1) 원본 데이터 보관
```
Azure Blob Storage (Cold Tier)
├── 2025/
│   ├── 11/
│   │   ├── 14/
│   │   │   ├── naver_blog_20251114_100530.csv
│   │   │   └── naver_blog_20251114_143022.csv
│   │   └── 15/
│   └── 12/
```

**보관 정책:**
- 원본 CSV/JSON 영구 보관
- 압축 후 저장 (gzip)
- 90일 후 Cold Tier 이동

#### 2) 데이터베이스 저장
```sql
-- 테이블 설계
CREATE TABLE naver_blog (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    url VARCHAR(500) UNIQUE NOT NULL,
    author VARCHAR(100),
    blog_url VARCHAR(500),
    created_at TIMESTAMP,
    
    -- 인기도 지표
    view_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    
    -- OCR 결과
    ocr_text TEXT,
    has_image BOOLEAN DEFAULT FALSE,
    
    -- 메타데이터 (JSON)
    metadata JSONB,
    
    -- 시스템 필드
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_created_at ON naver_blog(created_at);
CREATE INDEX idx_author ON naver_blog(author);
CREATE INDEX idx_collected_at ON naver_blog(collected_at);

-- 전문 검색
CREATE INDEX idx_content_fts ON naver_blog 
    USING GIN (to_tsvector('korean', content));
```

### C. 이미지/비디오 처리

**현재:** URL만 저장

**고민 사항:**
1. **다운로드 여부**
   - [ ] URL만 저장 (현재)
   - [ ] 이미지 다운로드 후 Blob 저장
   - [ ] 썸네일만 저장

2. **저장 위치**
   - [ ] Azure Blob Storage
   - [ ] CDN
   - [ ] 별도 미디어 서버

3. **비용**
   - Blob Storage: ~$0.02/GB/월
   - 예상 이미지: 10GB/월 → $0.20/월

---

## 3. 인프라 관련 고민사항

### A. VM 리소스 분배

#### 현재 VM 스펙
```
CRAWLER VM:
- CPU: 8 코어
- 메모리: 31GB
- 디스크: 124GB

ANALYST VM:
- 상태: 중지됨
- 용도: 미정
```

#### 역할 분리 전략

**옵션 1: 기능별 분리**
```
CRAWLER VM:
- 크롤링 전용
- 임시 데이터 저장
- 전처리

ANALYST VM:
- PostgreSQL 설치
- 데이터 분석
- Jupyter Notebook
```

**옵션 2: 시간대별 사용**
```
CRAWLER VM:
- 새벽 1-6시: 크롤링
- 오전 9시-오후 6시: 분석

ANALYST VM:
- 예비용
```

**질문:**
- ANALYST VM을 활성화할까요?
  - [ ] Yes - PostgreSQL 전용
  - [ ] No - CRAWLER VM에서 모두 처리
  - [ ] 필요시에만 켜기

### B. 비용 최적화

#### VM 비용 절감
```python
# VM 자동 시작/종료 스크립트
from azure.mgmt.compute import ComputeManagementClient

def stop_vm_if_idle():
    """유휴 상태 시 VM 자동 중지"""
    cpu_usage = get_cpu_usage()
    
    if cpu_usage < 5:  # 5% 미만
        if is_idle_for_hours(1):  # 1시간 이상 유휴
            stop_vm('PMIKR-DATA-ANALYST')
            send_notification("ANALYST VM 자동 중지")
```

#### 스케줄링
```
월-금:
- 06:00: CRAWLER VM 크롤링 시작
- 09:00: ANALYST VM 자동 시작
- 18:00: ANALYST VM 자동 중지

주말:
- 크롤링만 실행 (Cron)
```

### C. 데이터베이스 위치

**질문: PostgreSQL을 어디에 설치?**

| 옵션 | 비용 | 장점 | 단점 |
|------|------|------|------|
| **A. ANALYST VM** | 무료 | 분석 최적 | VM 활성화 필요 |
| **B. CRAWLER VM** | 무료 | 간단함 | 리소스 공유 |
| **C. Supabase** | 무료~$25 | 관리 불필요 | 데이터 제한 |
| **D. Azure DB** | ~$100 | 완전 관리 | 비용 높음 |

**추천:** **A (ANALYST VM)** 또는 **C (Supabase 무료로 시작)**

---

## 4. 프로세스 관련 고민사항

### A. 크롤링 빈도

**현재:** 수동 실행

**옵션:**
1. **정기 Cron**
   ```bash
   # 매일 새벽 2시
   0 2 * * * ~/run_naver_crawler.sh
   
   # 주 1회 (월요일)
   0 2 * * 1 ~/run_naver_crawler.sh
   ```

2. **증분 크롤링**
   - 신규 데이터만 수집
   - 마지막 수집 날짜 이후

**질문:**
- 크롤링 주기는?
  - [ ] 매일
  - [ ] 주 1회
  - [ ] 월 1회
  - [ ] 수동

### B. 데이터 파이프라인 자동화

```python
# 전체 파이프라인
def daily_pipeline():
    """
    1. 크롤링
    2. Blob 백업
    3. 전처리
    4. PostgreSQL 저장
    5. 분석
    6. 리포트 생성
    """
    
    # 1. 크롤링
    run_crawler()
    
    # 2. 백업
    backup_to_blob()
    
    # 3. 전처리
    df = preprocess_data()
    
    # 4. DB 저장
    save_to_postgresql(df)
    
    # 5. 분석
    generate_insights()
    
    # 6. 리포트
    send_daily_report()
```

### C. 에러 처리 및 알림

```python
# Slack 알림
def send_slack_notification(message):
    """크롤링 완료/실패 시 알림"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    requests.post(webhook_url, json={
        "text": f"🤖 {message}",
        "username": "Crawler Bot"
    })

# 사용 예시
try:
    run_crawler()
    send_slack_notification("✅ 크롤링 완료: 1,234개 수집")
except Exception as e:
    send_slack_notification(f"❌ 크롤링 실패: {str(e)}")
```

### D. 데이터 품질 모니터링

```python
# 대시보드 메트릭
metrics = {
    "today_collected": 1234,  # 오늘 수집 건수
    "duplicates_removed": 56,  # 중복 제거 건수
    "failed_urls": 12,          # 실패한 URL
    "avg_processing_time": 2.5, # 평균 처리 시간 (초)
    "database_size": "15.2 GB"  # DB 크기
}
```

---

## 5. 선택해야 할 사항들

### 🎯 우선순위 1: 즉시 결정

#### Q1. PostgreSQL 설치 위치
- [ ] **A. ANALYST VM** (추천)
  - 장점: 분석과 분리, 무료
  - 단점: VM 활성화 필요
  
- [ ] **B. Supabase 무료 티어**
  - 장점: 관리 불필요, 쉬운 시작
  - 단점: 500MB 제한
  
- [ ] **C. CRAWLER VM**
  - 장점: 간단함
  - 단점: 리소스 경쟁

**추천:** **A** (데이터 작으면 B로 시작)

#### Q2. 크롤링 결과 어디 저장?
- [ ] **A. 계층형 저장** (추천)
  ```
  VM 임시 → Blob 백업 → PostgreSQL
  ```
  
- [ ] **B. 직접 DB 저장**
  ```
  크롤링 → PostgreSQL
  ```

**추천:** **A** (안전성)

#### Q3. ANALYST VM 활성화?
- [ ] **Yes** - PostgreSQL 전용으로 사용
- [ ] **No** - CRAWLER VM에서 모두 처리
- [ ] **나중에** - 일단 Supabase로 시작

### 🎯 우선순위 2: 단계적 결정

#### Q4. 중복 데이터 처리
- [ ] 최신 버전만 유지
- [ ] 버전 히스토리 저장
- [ ] 수동 확인 후 처리

#### Q5. 이미지/비디오
- [ ] URL만 저장 (현재)
- [ ] 썸네일만 다운로드
- [ ] 전체 다운로드

#### Q6. 크롤링 빈도
- [ ] 매일 자동
- [ ] 주 1회 자동
- [ ] 수동

#### Q7. 데이터 백업
- [ ] 매일
- [ ] 매주
- [ ] 수동

### 🎯 우선순위 3: 장기 계획

#### Q8. 스케일링 전략
- 데이터가 1억 건 이상이 되면?
- 동시 사용자가 많아지면?

#### Q9. 외부 공개 여부
- 데이터 API 제공?
- 웹 대시보드 공개?

---

## 📝 다음 단계 권장사항

### 이번 주 (11/14 - 11/18)
1. ✅ VM 디렉토리 구조 정리
2. ⬜ PostgreSQL 설치 위치 결정
3. ⬜ 크롤링 결과 확인 및 분석
4. ⬜ Blob Storage 연동 테스트

### 다음 주 (11/21 -)
1. ⬜ PostgreSQL 설치 및 테이블 설계
2. ⬜ 데이터 파이프라인 구축
3. ⬜ Cron 자동화 설정
4. ⬜ 모니터링 대시보드 구축

### 월말까지 (11/30)
1. ⬜ 전체 워크플로우 문서화
2. ⬜ 백업 전략 수립
3. ⬜ 팀원과 사용 가이드 공유
4. ⬜ 상무님께 보고서 작성

---

## 💬 질문 리스트 (의사결정 필요)

**당장 답변이 필요한 질문:**

1. **PostgreSQL을 어디에 설치하시겠습니까?**
   - A. ANALYST VM (추천)
   - B. Supabase 무료
   - C. CRAWLER VM

2. **ANALYST VM을 지금 활성화하시겠습니까?**
   - Yes / No / 나중에

3. **크롤링을 얼마나 자주 실행하시겠습니까?**
   - 매일 / 주 1회 / 수동

4. **이미지/비디오 파일은 어떻게 처리하시겠습니까?**
   - URL만 / 썸네일 다운 / 전체 다운

5. **팀원과 동시 작업 시 어떻게 조율하시겠습니까?**
   - 시간대 분리 / 디렉토리 분리 / 둘 다

**답변을 주시면 구체적인 구현 계획을 작성해드리겠습니다!**
