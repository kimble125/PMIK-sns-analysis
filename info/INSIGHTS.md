# 프로젝트 인사이트 (Project Insights)

AI 코딩 도구 활용 및 크롤러 개발에서 얻은 핵심 인사이트를 정리합니다.

---

## 🧠 AI 코딩 도구 활용 인사이트

### 1. AI 코드 재작성 문제 해결법

**문제**: AI가 요청한 부분 외의 코드도 함께 수정하여 이전 버그 재발

**해결책**:
```markdown
❌ 잘못된 요청:
"네이버 블로그 크롤러를 개선해줘"

✅ 올바른 요청:
"pm_naver_blog_crawler_v10_3_test.py의 619번 라인 profile_url 변수만 수정해줘.
다른 코드는 절대 건드리지 마."
```

**핵심 원칙**:
- **수정 범위를 명시적으로 지정** (파일명, 함수명, 라인 번호)
- **"다른 부분은 수정하지 마"라고 명시**
- **한 번에 하나의 수정만 요청**

---

### 2. 모듈화의 적정 수준

**문제**: 과도한 모듈화는 오히려 복잡도 증가

**인사이트**:
```
1개 플랫폼 크롤러의 적정 파일 수:
- ❌ 7개 이상: 과잉 (파일 간 의존성 복잡)
- ✅ 3-4개: 적정 (메인/OCR/검증/유틸)
- ⚠️ 1개: 위험 (1500줄 이상 시)
```

**권장 구조**:
```
platform_crawler/
├── main_crawler.py      # 800줄 이하
├── ocr_processor.py     # 300줄 이하
├── data_validator.py    # 200줄 이하
└── tests/
    └── test_core.py     # 핵심 함수 테스트
```

---

### 3. AI 도구 선택 가이드

| 작업 유형 | 추천 도구 | 이유 |
|-----------|----------|------|
| 작은 버그 수정 | Windsurf Cascade | 빠른 응답, GUI 편리 |
| 대규모 리팩토링 | Google Antigravity | 멀티 에이전트, 무료 |
| 전체 프로젝트 분석 | Claude Code | 큰 컨텍스트, Opus 모델 |
| 새 기능 개발 | Antigravity | Artifacts 검증 |

---

## 🕷️ 크롤러 개발 인사이트

### 4. 네이버 블로그 크롤링 핵심 포인트

**URL 패턴**:
```python
# 게시물 URL
f"https://blog.naver.com/{blog_id}/{post_id}"

# 프로필 URL (정확한 형태!)
f"https://blog.naver.com/ProlieOf.nhn?blogId={blog_id}"
# ⚠️ 주의: ProileOf (X), ProlieOf (O)
# ⚠️ 주의: .naver (X), .nhn (O)
```

**연도 키워드 검색의 함정**:
```
"독일피엠 2018" 검색 → 제목/본문에 "2018"이 명시된 게시물만
→ 2018년에 작성되었어도 제목에 연도 없으면 검색 안 됨

해결: 연도 없는 키워드를 먼저 검색하여 더 넓은 범위 수집
```

---

### 5. OCR 처리 핵심 설정

```python
# Selenium 이미지 로딩 설정
# ❌ OCR 불가 (이미지 비활성화)
chrome_options.add_argument('--disable-images')

# ✅ OCR 가능 (이미지 활성화)
# 위 옵션을 제거하거나 주석 처리
```

**EasyOCR 최적화**:
```python
# GPU 사용 시도 후 CPU 폴백
try:
    reader = easyocr.Reader(['ko', 'en'], gpu=True)
except:
    reader = easyocr.Reader(['ko', 'en'], gpu=False)
```

---

### 6. 멀티미디어 처리 우선순위

```
1순위: YouTube 자막 API (95% 정확도, 무료)
2순위: Whisper Local (85% 정확도, 무료, 느림)
3순위: AssemblyAI/Azure Speech (95% 정확도, 유료)
4순위: 썸네일 OCR (50% 정확도, 대체 수단)
5순위: 메타데이터만 저장 (fallback)
```

---

## 💡 프로젝트 관리 인사이트

### 7. Git 커밋 메시지 규칙

```bash
# 형식: type: description

feat: 프로필 소개글 수집 기능 추가
fix: profile_url 오타 수정 (ProileOf → ProlieOf)
refactor: OCR 처리 로직 별도 파일로 분리
test: extract_post_id 단위 테스트 추가
docs: README 업데이트
```

---

### 8. 테스트 우선 개발 (TDD Lite)

```python
# 핵심 함수만 테스트 (5-10개)
def test_extract_post_id():
    url = "https://blog.naver.com/abc123/224082772826"
    assert extract_post_id(url) == "224082772826"

def test_extract_phone_number():
    content = "연락주세요 010-1234-5678"
    assert extract_phone_number(content) == "010-1234-5678"

# 실행
# pytest tests/test_core.py -v
```

---

## 📅 업데이트 이력

- **2025-11-25**: 초기 작성 (AI 도구 비교, 크롤러 인사이트)

---

## 📌 참고 자료

- [Claude Code 공식 문서](https://docs.claude.com/en/docs/claude-code/setup)
- [Google Antigravity 다운로드](https://antigravity.google/download)
- [EasyOCR 공식 문서](https://github.com/JaidedAI/EasyOCR)
