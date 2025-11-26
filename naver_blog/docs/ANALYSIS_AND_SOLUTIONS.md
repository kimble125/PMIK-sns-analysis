# PM 크롤러 v10.1 문제 분석 및 해결 방안

## 📊 현상 분석

### 실행 결과
- **실행 시간**: 2시간 (정상)
- **수집 게시물**: 3개 (심각한 문제)
- **필터링된 게시물**: 717개

### 핵심 문제
**필터링이 너무 엄격해서 대부분의 게시물이 제외됨**

---

## 🔍 상세 원인 분석

### 1. 키워드 문제
```
검색 키워드: "PM 2023", "PM 2024", "PM 2025"
→ "PM"만으로는 다른 의미의 PM도 검색됨
→ Project Manager, Prime Minister, 파워메탈, PM코리아(매트리스) 등
```

### 2. 필터링 로직 문제
```python
# 현재 로직: 제외 키워드 2개 이상이면 무조건 제외
exclude_count = sum(1 for keyword in EXCLUDE_KEYWORDS if keyword in full_text)
if exclude_count >= 2:
    return False
```

**문제:**
- PM-International 게시물도 "뉴스", "기사" 같은 일반 단어 포함 시 제외됨
- 제외 키워드 55개가 너무 많음

### 3. 프로필 수집 실패
- CSS 선택자 불일치로 profile_intro 수집 실패
- 추천인 정보가 프로필에 있어도 추출 못함

### 4. OCR 미작동
- EasyOCR 미설치
- 이미지 로딩 비활성화 (`--disable-images`)

---

## 💡 해결 방안

### [우선순위 1] 필터링 완화 (즉시 적용 필요)

#### 방안 A: 제외 키워드 기준 완화
```yaml
# config.yaml 수정

# 현재: 2개 이상 → 너무 엄격
# 개선: 3~4개 이상으로 완화

# 또는 특정 키워드 조합으로 변경
```

```python
# pm_naver_blog_crawler_v10_1_test.py 수정
# 1460번째 줄

# 현재
if exclude_count >= 2:
    return False

# 개선 1: 기준 상향
if exclude_count >= 4:  # 4개 이상일 때만 제외
    return False

# 개선 2: 중요 키워드만 체크
critical_excludes = ["매트리스", "침대", "채용", "주가", "상장"]
if any(kw in full_text for kw in critical_excludes):
    return False
```

#### 방안 B: 키워드 개선
```python
# 너무 광범위한 "PM 2023"을 제거하고 구체적인 키워드만 사용

# 제거할 키워드:
- "PM 2023/2024/2025"  # 너무 광범위
- "PM인터내셔널 2023/2024/2025"  # 띄어쓰기 문제

# 유지할 키워드:
- "피엠인터내셔널 2023/2024/2025"  # 명확함
- "피트라인 2023/2024/2025"  # 제품명
- "독일피엠 2023/2024/2025"  # 구체적
```

#### 방안 C: 2단계 수집 전략
```
1단계: 관대한 필터링으로 많이 수집
2단계: 후처리로 정제

장점:
- 누락 최소화
- 분석 시 필터링 기준 조정 가능
```

---

### [우선순위 2] 프로필 수집 개선

#### CSS 선택자 업데이트
```python
# pm_naver_blog_crawler_v10_1_test.py 수정

def extract_profile_info(driver, soup, blog_id):
    # 기존
    intro_selectors = [
        '.blog_intro', '.profile_intro', '.introduce', 
        '.blog_description', '#blogIntro', '.profile_text'
    ]
    
    # 개선: 더 많은 선택자 추가
    intro_selectors = [
        '.blog_intro', '.profile_intro', '.introduce', 
        '.blog_description', '#blogIntro', '.profile_text',
        '.se_textarea',  # 신규
        '.blog_profile_txt',  # 신규
        '#content-area .profile',  # 신규
        '.nick_box .intro',  # 신규
    ]
    
    # 전체 프로필 영역도 확인
    profile_area = soup_profile.select_one('#content-area, .profile_area, .blog_1depth')
    if profile_area:
        full_text = clean_text(profile_area.get_text())
        # 여기서 전화번호, 회원번호 추출
```

---

### [우선순위 3] 키워드 연도 확장 재검토

#### 문제
```
"PM 2023" 같은 키워드는 너무 광범위
→ 다른 의미의 PM도 대량 검색
```

#### 해결
```python
# Option 1: 연도 제거
def expand_keywords_with_years(keywords, years=[]):  # 빈 리스트
    # 연도 붙이지 않음
    return keywords

# Option 2: 구체적인 키워드만 연도 추가
def expand_keywords_with_years(keywords, years=[2023, 2024, 2025]):
    expanded = []
    for kw_info in keywords:
        keyword = kw_info["keyword"]
        
        # "PM"만 있는 키워드는 연도 제외
        if keyword in ["PM", "PM International", "PM인터내셔널"]:
            # 연도 없이 추가
            expanded.append({
                "keyword": keyword,
                "target": 300
            })
        else:
            # 구체적인 키워드만 연도 추가
            for year in years:
                expanded.append({
                    "keyword": f"{keyword} {year}",
                    "target": 300
                })
    return expanded

# Option 3: 연도 범위 추가 (추천)
# "피엠인터내셔널 2023..2025" 형식으로 검색
```

---

### [우선순위 4] OCR 활성화

#### 방안 A: 크롤링 시 OCR (느림)
```bash
# VM에서
pip3 install --user easyocr Pillow

# 코드 수정
# chrome_options.add_argument('--disable-images')  # 주석 처리
```

#### 방안 B: 별도 OCR (권장)
```python
# 1단계: 이미지 URL만 수집 (빠름)
# 2단계: 별도 스크립트로 OCR 실행
# → 기존 step2_colab_processing.ipynb 활용
```

---

## 🎯 권장 실행 계획

### 즉시 실행 (테스트)
1. ✅ 필터링 기준 완화: 2개 → 4개
2. ✅ "PM 2023/2024/2025" 키워드 제거
3. ✅ 30분 테스트 실행

### 단기 (이번 주)
1. ✅ 프로필 CSS 선택자 개선
2. ✅ 필터링 로직 재설계
3. ✅ 2시간 전체 실행

### 중기 (다음 주)
1. ✅ 2단계 수집 전략 구현
2. ✅ 별도 OCR 파이프라인 구축
3. ✅ 프로필 정보 별도 테이블 분리

---

## 📋 수정 체크리스트

### config.yaml
- [ ] exclude_keywords 축소 (55개 → 20개 핵심만)
- [ ] "PM 2023" 등 광범위 키워드 제거

### pm_naver_blog_crawler_v10_1_test.py
- [ ] 필터링 기준: `>= 2` → `>= 4`
- [ ] 프로필 CSS 선택자 추가
- [ ] 키워드 확장 로직 개선
- [ ] 에러 로깅 강화

### 테스트
- [ ] 30분 테스트 실행
- [ ] 필터링 통계 확인
- [ ] 수집 게시물 품질 검증

---

## 💬 컬럼 관련 종합 의견

### profile_nickname
- **유지 필요**: blog_id보다 사람이 읽기 쉬움
- **활용**: 동일 판매원의 여러 블로그 연결

### profile_intro vs profile_description
- **profile_intro**: 짧은 소개글
- **profile_description**: 전체 프로필 내용 (추가 필요)
- **중복 문제**: 블로거별 1회만 수집 (별도 테이블 권장)

### profile_member_id
- **매우 중요**: PM 판매원 식별자
- **blog_id와 별개**: PM 시스템 연동 가능

### profile_url
- **필요**: 추천인 링크 파악
- **활용**: 마케팅 채널 분석

### sponsor_phone, sponsor_partner_id
- **현재 문제**: 프로필 추출 실패
- **해결**: CSS 선택자 개선

### 파생 컬럼
- **현재 방식 유지 OK**: 간단한 계산은 수집 시
- **복잡한 분석은 후처리**: content_type, sentiment 등

### image_ocr_text
- **문제**: OCR 미설치 + 이미지 로딩 비활성화
- **해결**: 별도 OCR 파이프라인 (권장)

---

## 🚨 가장 시급한 문제

**1. 필터링 완화** (최우선)
- 717건 필터링 → 3건 수집은 비정상
- 제외 키워드 기준을 2개 → 4개로 완화
- 또는 핵심 키워드만 체크

**2. 키워드 개선**
- "PM 2023" 같은 광범위 키워드 제거
- 구체적인 키워드만 사용

**3. 프로필 수집**
- CSS 선택자 업데이트
- 추천인 정보 추출 개선

---

**작성일**: 2025-11-20
**버전**: v10.1 문제 분석
**다음 액션**: 필터링 완화 후 테스트 실행
