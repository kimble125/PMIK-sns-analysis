# 데이터베이스 선택 가이드

## 📊 현재 데이터 특성

### 데이터 유형
1. **네이버 블로그** - CSV (정형)
2. **카카오스토리** - JSON (반정형)  
3. **유튜브** - CSV (정형)

### 데이터 특징
- ✅ 대부분 **정형 데이터**
- ✅ **고정된 스키마**
- ✅ **문자 중심**
- ⚠️ 일부 JSON
- ⚠️ 긴 텍스트 (블로그 본문)

---

## 🎯 PostgreSQL 추천 (⭐⭐⭐⭐⭐)

### 추천 이유

#### 1. RDB + JSON 지원
```sql
CREATE TABLE naver_blog (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    url VARCHAR(500) UNIQUE,
    metadata JSONB  -- JSON 저장!
);

-- JSON 쿼리
SELECT * FROM naver_blog 
WHERE metadata->>'category' = 'PM제품';
```

#### 2. 한글 전문 검색
```sql
-- 전문 검색 인덱스
CREATE INDEX idx_content_fts ON naver_blog 
USING GIN (to_tsvector('korean', content));

-- 검색
SELECT * FROM naver_blog 
WHERE to_tsvector('korean', content) @@ 
      to_tsquery('korean', '피엠인터내셔널');
```

#### 3. 장점
- ✅ 정형 데이터에 최적
- ✅ 복잡한 쿼리 (JOIN, 집계)
- ✅ ACID 트랜잭션
- ✅ 무료 & 오픈소스
- ✅ Python 완벽 호환

---

## ⚖️ MongoDB vs PostgreSQL

| 요구사항 | PostgreSQL | MongoDB |
|---------|-----------|---------|
| 정형 데이터 | ✅ 완벽 | ⚠️ 가능 |
| JSON 지원 | ✅ JSONB | ✅ 네이티브 |
| 전문 검색 | ✅ 강력 (한글) | ⚠️ 보통 |
| 복잡한 쿼리 | ✅ SQL | ❌ 어려움 |
| 트랜잭션 | ✅ 강력 | ⚠️ 제한적 |
| 학습 곡선 | ⚠️ 보통 | ⚠️ 높음 |
| 현재 데이터 적합성 | ✅ 매우 높음 | ⚠️ 과한 스펙 |

### 결론
**현재 데이터는 정형이 대부분 → PostgreSQL이 최적**

MongoDB는:
- 스키마가 자주 변경될 때
- 중첩 JSON이 많을 때
- 초대규모 샤딩 필요할 때

---

## 🏗️ PostgreSQL 구축 옵션

### 옵션 A: ANALYST VM에 설치 (추천)
```bash
# 설치
sudo apt update
sudo apt install postgresql postgresql-contrib

# 설정
sudo -u postgres createdb pmik_sns_db
sudo -u postgres psql
```

**장점:**
- 무료
- 분석 작업과 함께 사용
- 크롤링과 분리

**단점:**
- ANALYST VM 활성화 필요

### 옵션 B: Supabase (무료 티어)
- **무료**: 500MB, 무제한 API 요청
- **관리형**: 백업, 스케일링 자동
- **REST API**: 자동 생성

**시작:**
https://supabase.com

### 옵션 C: Azure Database for PostgreSQL
- **관리형**: 완전 자동화
- **비용**: ~$100/월

---

## 📝 Python 연동 예시

```python
from sqlalchemy import create_engine
import pandas as pd

# 연결
engine = create_engine(
    'postgresql://user:pass@localhost:5432/pmik_sns_db'
)

# CSV → PostgreSQL
df = pd.read_csv('naver_blog_20251114.csv')
df.to_sql('naver_blog', engine, if_exists='append')

# 쿼리
df_result = pd.read_sql(
    "SELECT * FROM naver_blog WHERE created_at > '2025-01-01'",
    engine
)
```

---

## ❓ 선택 질문

1. **PostgreSQL 설치 위치**는?
   - [ ] A. ANALYST VM
   - [ ] B. Supabase 무료
   - [ ] C. CRAWLER VM
   
2. **데이터 백업** 주기는?
   - [ ] 매일
   - [ ] 매주
   - [ ] 수동

3. **외부 접근** 필요한가요?
   - [ ] Yes (REST API 필요)
   - [ ] No (VM 내부만)
