# 판매원 정보 연결 가이드

## 개요

수집한 블로그 게시물 데이터와 사내 판매원 정보를 연결하여 게시물 형태와 수익의 연관성을 분석하기 위한 가이드입니다.

---

## 1. 추가된 데이터 컬럼

크롤러에 다음 3개의 컬럼이 추가되었습니다:

| 컬럼명 | 설명 | 데이터 타입 | 예시 |
|--------|------|-------------|------|
| `referrer_name` | 추천인(판매원) 이름 | 문자열 | "김민수" |
| `referrer_phone` | 추천인 전화번호 | 문자열 | "010-1234-5678" |
| `partner_number` | 파트너 번호 (사내 고유 ID) | 문자열 | "P2024-1234" |

### 위치
- 파일: `naver_blog_crawler.py`
- 함수: `save_to_csv()`
- CSV 출력: 모든 수집 데이터에 자동 포함 (초기값: 빈 문자열)

---

## 2. 판매원 식별 방법

### 2.1 기본 식별자: `author_id` (블로그 ID)

**자동 수집되는 정보:**
```python
author_id = "fldpffm0614"  # blog.naver.com/fldpffm0614 에서 추출
```

**활용 방법:**
1. 블로그 ID를 기준으로 판매원 매칭
2. 사내 판매원 DB에 블로그 ID 컬럼 추가
3. `author_id`를 키로 사용하여 조인(JOIN)

**장점:**
- ✅ 자동 수집됨
- ✅ 고유값 (중복 없음)
- ✅ 변경되지 않음

**단점:**
- ⚠️ 사전에 판매원의 블로그 ID를 수집해야 함

---

### 2.2 추가 식별자

#### A. 블로그 프로필 URL (`blogger_profile`)

**자동 수집되는 정보:**
```python
blogger_profile = "blog.naver.com/fldpffm0614"
```

**활용 방법:**
- `author_id`와 동일하게 사용 가능
- URL 전체를 키로 사용

---

#### B. 게시물 내용 분석

**본문/해시태그에서 연락처 추출:**

```python
# 전화번호 패턴
phone_pattern = r'010[-\s]?\d{4}[-\s]?\d{4}'

# 카카오톡 ID 패턴
kakao_pattern = r'카카오톡?\s*[:：]?\s*([a-zA-Z0-9_]+)'

# 이메일 패턴
email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
```

**예시 코드:**
```python
import re
import pandas as pd

def extract_contact_info(text):
    """게시물 본문에서 연락처 정보 추출"""
    phone = re.search(r'010[-\s]?\d{4}[-\s]?\d{4}', text)
    kakao = re.search(r'카카오톡?\s*[:：]?\s*([a-zA-Z0-9_]+)', text)
    
    return {
        'phone': phone.group(0) if phone else '',
        'kakao': kakao.group(1) if kakao else ''
    }

# CSV 파일 로드
df = pd.read_csv('output/naver_blog_crawl_20251101.csv')

# 연락처 추출
df['extracted_phone'] = df['content_text'].apply(
    lambda x: extract_contact_info(str(x))['phone']
)
df['extracted_kakao'] = df['content_text'].apply(
    lambda x: extract_contact_info(str(x))['kakao']
)
```

---

#### C. 이미지 OCR 텍스트 분석

**OCR로 추출된 텍스트에서 연락처 찾기:**

```python
# OCR 텍스트에서 연락처 추출
df['ocr_phone'] = df['image_text'].apply(
    lambda x: extract_contact_info(str(x))['phone']
)
```

**활용 사례:**
- 이미지에 포함된 명함 정보
- 제품 홍보 이미지의 연락처
- 프로필 이미지의 텍스트

---

### 2.3 판매원 매칭 워크플로우

```
[1단계] 자동 수집
    ↓
author_id, blogger_profile, content_text, image_text 수집
    ↓
[2단계] 연락처 추출 (선택)
    ↓
본문/OCR 텍스트에서 전화번호, 카카오톡 ID 추출
    ↓
[3단계] 사내 DB 매칭
    ↓
author_id 또는 추출된 연락처로 판매원 DB와 조인
    ↓
[4단계] 수동 입력
    ↓
매칭되지 않은 경우 referrer_name, referrer_phone, partner_number 수동 입력
    ↓
[5단계] 최종 데이터셋
    ↓
게시물 + 판매원 정보 완성
```

---

## 3. 사내 데이터 연결 방법

### 3.1 방법 1: author_id 기반 매칭 (권장)

**사전 준비:**
1. 판매원 DB에 `blog_id` 컬럼 추가
2. 각 판매원의 네이버 블로그 ID 수집

**매칭 코드:**
```python
import pandas as pd

# 크롤링 데이터
crawl_df = pd.read_csv('output/naver_blog_crawl_20251101.csv')

# 사내 판매원 DB
partner_df = pd.read_csv('internal/partners.csv')
# 컬럼: partner_number, name, phone, blog_id

# 매칭
merged_df = crawl_df.merge(
    partner_df,
    left_on='author_id',
    right_on='blog_id',
    how='left'
)

# 판매원 정보 채우기
merged_df['referrer_name'] = merged_df['name']
merged_df['referrer_phone'] = merged_df['phone']
merged_df['partner_number'] = merged_df['partner_number']

# 저장
merged_df.to_csv('output/matched_posts.csv', index=False, encoding='utf-8-sig')
```

---

### 3.2 방법 2: 전화번호 기반 매칭

**매칭 코드:**
```python
# 본문에서 전화번호 추출
def extract_phone(text):
    match = re.search(r'010[-\s]?\d{4}[-\s]?\d{4}', str(text))
    return match.group(0).replace('-', '').replace(' ', '') if match else ''

crawl_df['extracted_phone'] = crawl_df['content_text'].apply(extract_phone)

# 전화번호로 매칭
merged_df = crawl_df.merge(
    partner_df,
    left_on='extracted_phone',
    right_on='phone',
    how='left'
)
```

---

### 3.3 방법 3: 수동 매칭 (소규모)

**Excel 활용:**
1. CSV 파일을 Excel로 열기
2. `author_id` 확인
3. 판매원 DB에서 해당 ID 검색
4. `referrer_name`, `referrer_phone`, `partner_number` 수동 입력
5. CSV로 다시 저장

---

## 4. 판매원 DB 구조 제안

### 4.1 최소 필수 컬럼

```sql
CREATE TABLE partners (
    partner_number VARCHAR(50) PRIMARY KEY,  -- 파트너 번호 (고유 ID)
    name VARCHAR(100),                       -- 이름
    phone VARCHAR(20),                       -- 전화번호
    blog_id VARCHAR(100),                    -- 네이버 블로그 ID
    join_date DATE,                          -- 가입일
    team VARCHAR(100),                       -- 소속 팀
    rank VARCHAR(50)                         -- 직급/등급
);
```

### 4.2 확장 컬럼 (선택)

```sql
ALTER TABLE partners ADD COLUMN instagram_id VARCHAR(100);
ALTER TABLE partners ADD COLUMN youtube_channel VARCHAR(200);
ALTER TABLE partners ADD COLUMN kakao_id VARCHAR(100);
ALTER TABLE partners ADD COLUMN email VARCHAR(200);
```

---

## 5. 데이터 분석 예시

### 5.1 판매원별 게시물 수 집계

```python
# 판매원별 게시물 수
partner_stats = merged_df.groupby('partner_number').agg({
    'post_url': 'count',
    'view_count': 'sum',
    'like_count': 'sum',
    'comment_count': 'sum'
}).rename(columns={'post_url': 'post_count'})

print(partner_stats.sort_values('post_count', ascending=False))
```

### 5.2 게시물 형태와 수익 연관성 분석

```python
# 수익 데이터 추가 (예시)
# revenue_df: partner_number, monthly_revenue

analysis_df = partner_stats.merge(revenue_df, on='partner_number')

# 상관관계 분석
correlation = analysis_df[['post_count', 'view_count', 'like_count', 
                           'comment_count', 'monthly_revenue']].corr()

print(correlation['monthly_revenue'].sort_values(ascending=False))
```

### 5.3 인기 게시물 형태 분석

```python
# 인기도 점수 상위 20% 게시물
top_20_pct = merged_df.nlargest(int(len(merged_df) * 0.2), 'popularity_score')

# 해시태그 분석
top_hashtags = top_20_pct['hashtags'].str.split(', ').explode().value_counts()

# 이미지/동영상 사용 비율
media_usage = {
    'avg_images': top_20_pct['image_count'].mean(),
    'avg_videos': top_20_pct['video_count'].mean(),
    'has_video_pct': (top_20_pct['video_count'] > 0).mean() * 100
}

print("인기 게시물 특징:")
print(f"평균 이미지 수: {media_usage['avg_images']:.1f}")
print(f"평균 동영상 수: {media_usage['avg_videos']:.1f}")
print(f"동영상 포함 비율: {media_usage['has_video_pct']:.1f}%")
```

---

## 6. 추가 식별 방법

### 6.1 프로필 정보 크롤링 (고급)

**네이버 블로그 프로필 페이지에서 추가 정보 수집:**

```python
def crawl_profile_info(blog_id):
    """블로그 프로필 정보 크롤링"""
    url = f"https://blog.naver.com/prologue/PrologueList.naver?blogId={blog_id}"
    
    # Selenium으로 프로필 페이지 접근
    # 닉네임, 소개글, 프로필 이미지 등 수집
    
    return {
        'nickname': '...',
        'introduction': '...',
        'profile_image': '...'
    }
```

### 6.2 게시물 패턴 분석

**동일 판매원 식별:**
- 유사한 해시태그 사용 패턴
- 동일한 제품 언급 빈도
- 글쓰기 스타일 분석 (NLP)

---

## 7. 주의사항

### 7.1 개인정보 보호

⚠️ **중요:**
- 전화번호, 이름 등 개인정보는 사내 보안 규정 준수
- 외부 공유 시 개인정보 마스킹 필수
- GDPR/개인정보보호법 준수

### 7.2 데이터 품질

- `author_id`는 신뢰도 높음 (자동 수집)
- 본문 추출 연락처는 검증 필요 (오탐 가능)
- 수동 입력 시 오타 주의

### 7.3 업데이트 주기

- 판매원 DB는 정기적으로 업데이트
- 신규 판매원 블로그 ID 수집 프로세스 구축

---

## 8. 체크리스트

### 데이터 수집 전
- [ ] 판매원 DB 준비 (partner_number, name, phone, blog_id)
- [ ] 판매원들에게 블로그 ID 수집 요청
- [ ] 개인정보 처리 방침 확인

### 데이터 수집 후
- [ ] `author_id` 기반 자동 매칭 실행
- [ ] 매칭 실패 건 확인
- [ ] 본문/OCR 텍스트에서 연락처 추출 시도
- [ ] 수동 매칭 필요 건 처리
- [ ] 최종 데이터 검증

### 분석 단계
- [ ] 판매원별 게시물 통계 생성
- [ ] 게시물 형태 vs 수익 상관관계 분석
- [ ] 인기 게시물 패턴 분석
- [ ] 리포트 작성

---

## 9. 문의

데이터 연결 관련 문의사항은 데이터 팀으로 연락 바랍니다.
