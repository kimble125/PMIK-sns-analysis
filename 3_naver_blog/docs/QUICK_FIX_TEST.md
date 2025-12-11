# 🚀 긴급 수정 후 테스트 가이드

## ✅ 수정 완료 사항

### 1. 필터링 완화
```python
# 변경 전: 제외 키워드 2개 이상 시 필터링
if exclude_count >= 2:
    return False

# 변경 후: 4개 이상일 때만 필터링
if exclude_count >= 4:
    return False
```

**예상 효과:**
- 이전: 717개 필터링 → 3개 수집
- 예상: 200~300개 필터링 → 100~200개 수집

---

### 2. 광범위한 키워드 개선
```python
# 제외된 키워드 (연도 없이 사용):
- "PM"
- "PM International"  
- "PM인터내셔널"

# 유지된 키워드 (연도 추가):
- "피엠인터내셔널 2023/2024/2025"
- "독일피엠 2023/2024/2025"
- "피트라인 2023/2024/2025"
```

**예상 효과:**
- 불필요한 "PM 2023" 검색 제거
- 더 구체적인 키워드만 검색

---

### 3. 프로필 CSS 선택자 확장
```python
# 추가된 선택자:
'.se_textarea', '.blog_profile_txt', '.nick_box .intro',
'#content-area .profile', '.profile_area .intro'

# 폴백 로직:
전체 프로필 영역에서 텍스트 추출
```

**예상 효과:**
- profile_intro 수집률 증가
- sponsor_phone, sponsor_partner_id 추출 개선

---

## 🧪 30분 빠른 테스트

### Step 1: 파일 업로드
```bash
# 로컬 맥북에서
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp pm_naver_blog_crawler_v10_1_test.py crawler:~/PMIK-sns-analysis/naver_blog/
```

### Step 2: 테스트 모드 설정 (30분)
```bash
# 로컬에서 config.yaml 수정
# max_duration_minutes: 120 → 30

scp config.yaml crawler:~/PMIK-sns-analysis/naver_blog/
```

또는 VM에서 직접:
```bash
ssh crawler
cd ~/PMIK-sns-analysis/naver_blog
nano config.yaml
# max_duration_minutes를 30으로 수정
# Ctrl+O, Enter, Ctrl+X
```

### Step 3: 실행
```bash
# VM에서
cd ~/PMIK-sns-analysis/naver_blog
screen -S test_v10
python3 pm_naver_blog_crawler_v10_1_test.py
```

### Step 4: 30분 후 확인
```bash
# VM에서
screen -r test_v10
# 또는
ls -lh *.csv
tail -50 naver_blog_pm_v10_1_test_*_report.txt
```

---

## 📊 기대 결과 (30분 테스트)

### 이전 (2시간, 문제 있음)
- 수집: 3개
- 필터링: 717개
- 시간당 수집: 1.5개/시간

### 예상 (30분, 수정 후)
- 수집: 50~100개
- 필터링: 100~200개
- 시간당 수집: 100~200개/시간

**100배 이상 개선 예상!** 🎉

---

## 🔍 테스트 확인 포인트

### 1. 필터링 통계
```bash
cat vm_crawler_log.json | grep "필터링: 제외 키워드"
```

**확인사항:**
- "제외 키워드 2개 발견": 0건 (이제 통과함)
- "제외 키워드 3개 발견": 0건 (이제 통과함)
- "제외 키워드 4개 발견": 여전히 필터링

### 2. 수집 개수
```bash
wc -l naver_blog_pm_v10_1_test_*.csv
# 첫 줄 제외하고 50개 이상이면 성공
```

### 3. 프로필 정보
```bash
# CSV에서 profile_intro 컬럼 확인
head -1 naver_blog_pm_v10_1_test_*.csv | grep profile_intro
```

---

## 📥 결과 다운로드

```bash
# VM에서 나가기
exit

# 로컬에서
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp 'crawler:~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v10_1_test_*.csv' .
scp 'crawler:~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v10_1_test_*_report.txt' .
scp 'crawler:~/PMIK-sns-analysis/naver_blog/vm_crawler_log.json' .
```

---

## 🎯 성공 기준

### 최소 기준 (통과)
- ✅ 30분에 50개 이상 수집
- ✅ 필터링율 70% 이하

### 양호 기준
- ✅ 30분에 100개 이상 수집
- ✅ 필터링율 50% 이하

### 우수 기준
- ✅ 30분에 150개 이상 수집
- ✅ 필터링율 30% 이하

---

## 🔧 문제 발생 시

### Case 1: 여전히 3~10개만 수집
**원인:** 키워드가 여전히 문제
**해결:** 
```python
# 연도 확장 완전히 제거
years = []  # 빈 리스트
```

### Case 2: 필터링 여전히 많음
**원인:** 제외 키워드가 여전히 엄격
**해결:**
```python
# 5개 이상으로 더 완화
if exclude_count >= 5:
    return False
```

### Case 3: profile_intro 여전히 비어있음
**원인:** 네이버 블로그 구조 변경
**해결:** 
- 프로필 페이지 HTML 직접 확인 필요
- 별도 이슈로 처리

---

## 💬 다음 단계

### 테스트 성공 시
1. ✅ 2시간 전체 실행
2. ✅ 예상 수집: 400~800개
3. ✅ 데이터 품질 검증

### 테스트 실패 시
1. ❌ 로그 분석
2. ❌ 추가 수정
3. ❌ 재테스트

---

**작성일**: 2025-11-20
**버전**: v10.1 긴급 수정
**예상 소요 시간**: 30분
**목표**: 50개 이상 수집
