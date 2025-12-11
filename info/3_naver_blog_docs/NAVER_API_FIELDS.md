# Naver Blog Search API - 수집 가능한 필드 분석

## 📊 Naver API에서 제공하는 필드

### ✅ 현재 수집 중인 필드

| 필드명 | 타입 | 설명 | 예시 |
|--------|------|------|------|
| `title` | String | 블로그 포스트 제목 (HTML 태그 포함) | `"명예훼손 없이 <b>리뷰</b>쓰기"` |
| `link` | String | 블로그 포스트 URL | `"http://blog.naver.com/user/123"` |
| `description` | String | 블로그 포스트 요약 (HTML 태그 포함, 최대 160자) | `"명예훼손 없이 <b>리뷰</b>쓰기..."` |
| `bloggername` | String | 블로그 이름 | `"건짱의 Best Drawing World2"` |
| `bloggerlink` | String | 블로거 프로필 URL | `"http://blog.naver.com/yoonbitgaram"` |
| `postdate` | String | 작성 날짜 (YYYYMMDD 형식) | `"20161208"` |

### 🔍 Naver API 응답 구조

```json
{
  "lastBuildDate": "Mon, 26 Sep 2016 10:39:37 +0900",
  "total": 8714891,
  "start": 1,
  "display": 10,
  "items": [
    {
      "title": "명예훼손 없이 <b>리뷰</b>쓰기",
      "link": "http://openapi.naver.com/l?AAABW...",
      "description": "명예훼손 없이 <b>리뷰</b>쓰기 우리 블로그하시는 분들께는...",
      "bloggername": "건짱의 Best Drawing World2",
      "bloggerlink": "http://blog.naver.com/yoonbitgaram",
      "postdate": "20161208"
    }
  ]
}
```

**API 제공 필드는 6개가 전부입니다.**

---

## 🌐 Selenium 크롤링으로 추가 수집 가능한 필드

### ✅ 현재 Selenium으로 수집 중인 필드

| 필드명 | 설명 | 수집 방법 |
|--------|------|-----------|
| `content_text` | 본문 전체 텍스트 | `soup.get_text()` |
| `hashtags` | 해시태그 리스트 | 정규식 `#[가-힣a-zA-Z0-9_]+` |
| `images` | 이미지 URL 리스트 | `img.se-image-resource` 선택자 |
| `videos` | 동영상 URL 리스트 | `iframe[src*="youtube"]` 선택자 |
| `author_id` | 작성자 ID | URL에서 추출 |

### 🆕 추가 수집 가능한 필드

| 필드명 | 설명 | CSS 선택자 예시 | 난이도 |
|--------|------|------------------|--------|
| `view_count` | 조회수 | `.se_publishDate .se_viewCount` | 중 |
| `comment_count` | 댓글 수 | `.se_commentCount` | 중 |
| `like_count` | 공감 수 | `.se_likeCount` | 중 |
| `category` | 카테고리 | `.blog_category` | 쉬움 |
| `tags` | 태그 (해시태그와 별개) | `.tag_list a` | 쉬움 |
| `neighbor_count` | 이웃 수 | `.neighbor_count` | 어려움 |
| `post_time` | 작성 시간 (HH:MM) | `.se_publishDate` | 쉬움 |
| `is_ad` | 광고 여부 | `[data-ad]` 속성 | 쉬움 |
| `thumbnail_url` | 썸네일 이미지 URL | `.thumb_area img` | 쉬움 |

**주의사항:**
- 네이버 블로그 레이아웃은 자주 변경되므로 선택자가 작동하지 않을 수 있음
- 일부 필드는 JavaScript 렌더링 후에만 나타남
- 조회수, 댓글 수 등은 동적으로 로드되어 추가 대기 시간 필요

---

## 📝 추천 추가 필드

### 우선순위 1 (쉽고 유용함)
1. **`category`** - 블로그 카테고리 (예: "건강", "리뷰")
2. **`tags`** - 태그 리스트
3. **`post_time`** - 작성 시간

### 우선순위 2 (중요하지만 수집 어려움)
4. **`view_count`** - 조회수 (인기도 측정)
5. **`comment_count`** - 댓글 수 (참여도 측정)
6. **`like_count`** - 공감 수 (호감도 측정)

### 우선순위 3 (선택사항)
7. **`thumbnail_url`** - 썸네일 이미지
8. **`is_ad`** - 광고 여부

---

## 🔧 구현 예시

```python
# 조회수 추출
view_count_elem = soup.select_one('.se_publishDate .se_viewCount')
view_count = view_count_elem.get_text(strip=True) if view_count_elem else "0"

# 댓글 수 추출
comment_count_elem = soup.select_one('.se_commentCount')
comment_count = comment_count_elem.get_text(strip=True) if comment_count_elem else "0"

# 카테고리 추출
category_elem = soup.select_one('.blog_category')
category = category_elem.get_text(strip=True) if category_elem else ""

# 태그 추출
tags = [tag.get_text(strip=True) for tag in soup.select('.tag_list a')]
```

---

## ⚠️ 제한 사항

1. **Naver API 제한**
   - API는 6개 필드만 제공
   - 추가 정보는 Selenium 크롤링 필요

2. **크롤링 제한**
   - 네이버 블로그 레이아웃은 버전별로 다름 (구버전/신버전)
   - 일부 블로그는 비공개 설정으로 접근 불가
   - 동적 콘텐츠는 JavaScript 실행 필요

3. **성능 영향**
   - 추가 필드 수집 시 크롤링 시간 증가
   - 조회수/댓글 수는 별도 API 호출 필요할 수 있음

---

## 📌 결론

**Naver API 필드**: 6개 (모두 수집 중)  
**Selenium 추가 가능 필드**: 9개 (5개 수집 중, 4개 추가 가능)

추가하고 싶은 필드를 알려주시면 코드에 구현하겠습니다!
