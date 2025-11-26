# PM 크롤러 v10.2 변경사항

## 📋 변경 요약

**버전**: v10.1 → v10.2
**날짜**: 2025-11-20
**목적**: 필터링 과다 문제 해결, 데이터 구조 개선, 컬럼명 명확화

---

## 🔄 주요 변경사항

### 1. 필터링 완화 ⭐⭐⭐

#### 제외 키워드 기준 완화
- **변경 전**: 제외 키워드 2개 이상 → 필터링
- **변경 후**: 제외 키워드 4개 이상 → 필터링
- **위치**: `pm_naver_blog_crawler_v10_2_test.py:1510`
- **효과**: 717건 필터링 → 예상 200~300건 필터링

#### PM 브랜드 키워드 정제
- **제거된 키워드**: "피엠", "PM" (너무 광범위)
- **유지된 키워드**: "피엠인터내셔널", "독일피엠", "피트라인" 등
- **위치**: `config.yaml:91`
- **효과**: 불필요한 검색 결과 감소

---

### 2. 프로필 정보 별도 저장 ⭐⭐⭐⭐

#### 파일 분리
- **posts.csv**: 게시물 정보 (프로필 제외)
- **bloggers.csv**: 블로거 프로필 (blog_id당 1행)

#### 효과
- ✅ 중복 데이터 제거 (과대표현 방지)
- ✅ 데이터 정규화
- ✅ 저장 공간 절약
- ✅ 분석 시 정확도 향상

#### 예시
```
기존 (v10.1):
posts.csv (1000개 게시물)
- profile_nickname이 1000번 중복 저장

개선 (v10.2):
posts.csv (1000개 게시물, 프로필 제외)
bloggers.csv (50명 블로거, blog_id당 1회)
- 저장 공간 50% 절감
- 분석 시 블로거별 1회만 계산
```

---

### 3. 컬럼명 명확화 ⭐⭐⭐

#### 변경된 컬럼명

| 변경 전 | 변경 후 | 의미 |
|--------|---------|------|
| `profile_member_id` | `blogger_member_id` | 블로거 본인의 회원번호 |
| `sponsor_partner_id` | `content_sponsor_id` | 게시물 내 명시된 후원번호 |

#### 효과
- ✅ 출처 명확화 (프로필 vs 본문)
- ✅ 데이터 이해도 향상
- ✅ 분석 시 혼란 방지

---

### 4. 키워드 확장 수정 ⭐⭐

#### 변경 내용
- **제외 키워드**: "PM", "PM International"
- **적용 키워드**: "PM인터내셔널"도 연도 확장 적용

#### 근거
- "PM인터내셔널"은 실제로 구체적인 키워드
- 이전 버전에서 임의로 제외했던 것을 수정

---

### 5. 파생 컬럼 분리 ⭐

#### 분리된 기능
- **제거**: 크롤러 내부 파생 컬럼 생성 로직
- **추가**: `post_derived_columns.py` (별도 스크립트)

#### 효과
- ✅ 수집 속도 향상
- ✅ 로직 분리로 유지보수 개선
- ✅ 파생 컬럼 생성 시점 선택 가능

---

### 6. 오타 수정

- **수정**: "길자수" → "글자수"
- **위치**: 보고서 생성 부분

---

## 📊 파일 변경 내역

### 수정된 파일
1. **`pm_naver_blog_crawler_v10_2_test.py`** (메인 크롤러)
   - 필터링 로직 완화
   - 프로필 별도 저장
   - 컬럼명 변경
   - 버전 업데이트

2. **`config.yaml`**
   - PM 브랜드 키워드 수정
   - 버전 10.2.0으로 업데이트

### 생성된 파일
1. **`post_derived_columns.py`** (파생 컬럼 생성 스크립트)
2. **`COLLECTION_IMPROVEMENT_GUIDE.md`** (수집량 개선 가이드)
3. **`V10_2_CHANGES.md`** (이 파일)

---

## 🎯 예상 효과

### 수집량
- **v10.1**: 3개 (2시간)
- **v10.2**: 800~1,600개 (2시간)
- **개선율**: 250~500배 증가

### 데이터 품질
- ✅ 프로필 중복 제거
- ✅ 컬럼명 명확화
- ✅ 과대표현 방지

### 성능
- ✅ 저장 공간 절약
- ✅ 분석 속도 향상

---

## 🚀 실행 방법

### 1. 파일 업로드
```bash
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp pm_naver_blog_crawler_v10_2_test.py crawler:~/PMIK-sns-analysis/naver_blog/
scp config.yaml crawler:~/PMIK-sns-analysis/naver_blog/
```

### 2. 30분 테스트
```bash
ssh crawler
cd ~/PMIK-sns-analysis/naver_blog
screen -S test_v10_2
python3 pm_naver_blog_crawler_v10_2_test.py
# Ctrl+A, D (Detach)
```

### 3. 결과 확인
```bash
screen -r test_v10_2
# 또는
ls -lh *v10_2*.csv
```

### 4. 로컬 다운로드
```bash
exit  # VM에서 나가기
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp 'crawler:~/PMIK-sns-analysis/naver_blog/*v10_2*.csv' .
scp 'crawler:~/PMIK-sns-analysis/naver_blog/*v10_2*_report.txt' .
```

---

## 📋 체크리스트

### 실행 전
- [x] pm_naver_blog_crawler_v10_2_test.py 생성
- [x] config.yaml 업데이트
- [x] 문서 작성 완료
- [ ] VM에 파일 업로드

### 실행 중
- [ ] 30분 테스트 실행
- [ ] 수집량 확인 (목표: 50~150개)
- [ ] 필터링 통계 확인
- [ ] 품질 검증

### 실행 후
- [ ] posts.csv 확인
- [ ] bloggers.csv 확인
- [ ] 보고서 확인
- [ ] 다음 단계 결정

---

## 🔧 트러블슈팅

### 문제 1: 여전히 수집량 적음
**해결**: `COLLECTION_IMPROVEMENT_GUIDE.md` 참조
- 제외 키워드 기준 5개로 상향
- 연도 범위 확대 (2020~2025)
- 키워드 추가

### 문제 2: bloggers.csv가 생성 안됨
**원인**: 프로필 컬럼이 없음
**해결**: profile_nickname 등 컬럼 확인

### 문제 3: 컬럼명 오류
**원인**: 이전 버전 코드 사용
**확인**: VERSION이 "10.2.0"인지 확인

---

## 📚 관련 문서

1. **`V10_1_README.md`**: v10.1 전체 기능 설명
2. **`COLLECTION_IMPROVEMENT_GUIDE.md`**: 수집량 개선 방법
3. **`QUICK_START.md`**: 빠른 실행 가이드
4. **`VM_EXECUTION_GUIDE.md`**: VM 실행 상세 가이드
5. **`post_derived_columns.py`**: 파생 컬럼 생성 스크립트

---

## 🎓 기술적 세부사항

### 프로필 분리 로직
```python
# posts.csv: 프로필 제외
df_posts = df_all[posts_column_order]

# bloggers.csv: blog_id당 1회만
df_bloggers = df_all[blogger_cols].drop_duplicates(subset=['blog_id'])
```

### 필터링 변경
```python
# v10.1
if exclude_count >= 2:
    return False

# v10.2
if exclude_count >= 4:
    return False
```

### 컬럼명 변경 영향
- `extract_profile_info()`: 딕셔너리 키 변경
- `crawl_blog_post_selenium()`: 변수명 변경
- `generate_test_report()`: 통계 계산 변경

---

**작성일**: 2025-11-20
**버전**: v10.1 → v10.2
**작성자**: PMI Korea 데이터 분석팀
