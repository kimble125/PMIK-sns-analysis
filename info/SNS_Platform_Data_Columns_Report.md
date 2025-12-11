# 📊 PM-International SNS 크롤러 데이터 컬럼 비교 보고서

> 작성일: 2025-12-03  
> 목적: 각 플랫폼별 수집 데이터 컬럼 현황 파악 및 비교

---

## 1. 플랫폼별 수집 컬럼 상세

### 📘 네이버 블로그 (naver_blog)
| 컬럼명 | 설명 |
|--------|------|
| platform | 플랫폼 구분 ("naver_blog") |
| post_id | 게시물 ID |
| blog_id | 블로그 ID |
| url | 게시물 URL |
| title | 제목 |
| content | 본문 내용 |
| published_datetime | 작성일시 |
| sponsor_phone | 추천인 전화번호 |
| sponsor_partner_id | 추천인 파트너 ID (7-8자리) |
| like_count | 좋아요 수 |
| comment_count | 댓글 수 |
| hashtags | 해시태그 |
| image_urls | 이미지 URL 목록 |
| video_urls | 비디오 URL 목록 |
| collected_date | 수집일 |

### ☕ 네이버 카페 (naver_cafe)
| 컬럼명 | 설명 |
|--------|------|
| platform | 플랫폼 구분 ("naver_cafe") |
| cafe_id | 카페 ID |
| cafe_name | 카페 이름 |
| article_id | 게시물 ID |
| url | 게시물 URL |
| title | 제목 |
| content | 본문 내용 |
| author_nickname | 작성자 닉네임 |
| published_datetime | 작성일시 |
| view_count | 조회수 |
| like_count | 좋아요 수 |
| comment_count | 댓글 수 |
| sponsor_phone | 추천인 전화번호 |
| sponsor_partner_id | 추천인 파트너 ID |
| hashtags | 해시태그 |
| image_urls | 이미지 URL 목록 |
| video_urls | 비디오 URL 목록 |
| collected_datetime | 수집일시 |
| is_public | 공개 여부 |
| cafe_type | 카페 유형 |
| is_pm_keyword | PM 키워드 포함 여부 |

### 🎵 밴드 (Band)
| 컬럼명 | 설명 |
|--------|------|
| platform | 플랫폼 구분 ("band") |
| entity_type | 엔티티 유형 (band/page) |
| entity_id | 밴드/페이지 ID |
| entity_name | 밴드/페이지 이름 |
| post_id | 게시물 ID |
| url | 게시물 URL |
| title | 제목 |
| content | 본문 내용 |
| author_nickname | 작성자 닉네임 |
| published_datetime | 작성일시 |
| like_count | 좋아요 수 |
| comment_count | 댓글 수 |
| view_count | 조회수 |
| sponsor_phone | 추천인 전화번호 |
| sponsor_partner_id | 추천인 파트너 ID |
| hashtags | 해시태그 |
| image_urls | 이미지 URL 목록 |
| video_urls | 비디오 URL 목록 |
| collected_datetime | 수집일시 |
| is_public | 공개 여부 |
| is_pm_keyword | PM 키워드 포함 여부 |
| search_keyword | 검색 키워드 |

### 📺 유튜브 (YouTube)
#### 비디오 (Videos)
| 컬럼명 | 설명 |
|--------|------|
| platform | 플랫폼 구분 ("youtube") |
| video_id | 비디오 ID |
| url | 비디오 URL |
| channel_id | 채널 ID (FK) |
| channel_name | 채널명 |
| title | 제목 |
| description | 설명 |
| published_datetime | 업로드일시 |
| duration | 영상 길이 |
| view_count | 조회수 |
| like_count | 좋아요 수 |
| comment_count | 댓글 수 |
| tags | 태그 |
| thumbnail_url | 썸네일 URL |
| collected_date | 수집일 |
| sponsor_phone | 추천인 전화번호 |
| sponsor_partner_id | 추천인 파트너 ID |
| hashtags | 해시태그 |
| thumbnail_text_ocr | 썸네일 OCR 텍스트 |
| thumbnail_phone_ocr | 썸네일 OCR 전화번호 |
| thumbnail_partner_ocr | 썸네일 OCR 파트너ID |
| video_start_frame_ocr | 시작 프레임 OCR |
| video_start_phone_ocr | 시작 프레임 전화번호 |
| video_start_partner_ocr | 시작 프레임 파트너ID |
| video_end_frame_ocr | 종료 프레임 OCR |
| video_end_phone_ocr | 종료 프레임 전화번호 |
| video_end_partner_ocr | 종료 프레임 파트너ID |

#### 채널 (Channels)
| 컬럼명 | 설명 |
|--------|------|
| channel_id | 채널 ID |
| channel_name | 채널명 |
| channel_url | 채널 URL |
| custom_url | 커스텀 URL |
| description | 채널 설명 |
| joined_date | 채널 개설일 |
| subscriber_count | 구독자 수 |
| video_count | 영상 수 |
| view_count | 총 조회수 |
| country | 국가 |
| thumbnail_url | 프로필 이미지 |
| banner_url | 배너 이미지 |
| collected_date | 수집일 |
| sponsor_phone | 추천인 전화번호 |
| sponsor_partner_id | 추천인 파트너 ID |

### 📷 인스타그램 (Instagram)
| 컬럼명 | 설명 |
|--------|------|
| id | 사용자 ID |
| handle | 사용자 핸들 (@username) |
| permalink | 게시물 고유 링크 |
| media_type | 미디어 유형 (IMAGE/VIDEO/CAROUSEL_ALBUM) |
| media_url | 미디어 URL 목록 |
| media_count | 미디어 개수 |
| content | 본문 내용 |
| content_count | 본문 글자 수 |
| hashtags | 해시태그 목록 |
| hashtag_count | 해시태그 개수 |
| timestamp | 작성일시 |
| like_count | 좋아요 수 |
| comments_count | 댓글 수 |

### 📘 페이스북 (Facebook)
| 컬럼명 | 설명 |
|--------|------|
| user_name | 사용자 이름 |
| user_num | 사용자 번호 |
| datetime | 작성일시 |
| content | 본문 내용 |
| content_count | 본문 글자 수 |
| hashtags | 해시태그 목록 |
| hashtag_count | 해시태그 개수 |
| like_count | 좋아요 수 |
| comments_count | 댓글 수 |
| share_count | 공유 수 |
| media_urls | 미디어 URL 목록 |
| media_count | 미디어 개수 |
| audio_caption | 음성 인식 결과 (선택) |
| media_caption | 이미지 OCR 결과 (선택) |

### 💛 카카오스토리 (KakaoStory)
| 컬럼명 | 설명 |
|--------|------|
| p_num | 게시물 순번 |
| name | 사용자 이름 |
| user_id | 사용자 ID |
| shortcode | 게시물 고유코드 |
| date | 작성일시 |
| media_type | 미디어 유형 (image/multi_image/video/none) |
| media_url | 미디어 URL 목록 |
| media_count | 미디어 개수 |
| content | 본문 내용 |
| content_count | 본문 글자 수 |
| hashtag | 해시태그 목록 |
| hashtag_count | 해시태그 개수 |
| like_count | 좋아요 수 |
| comment_count | 댓글 수 |
| media_caption | 이미지 OCR 결과 (선택) |

---

## 2. 공통 컬럼 vs 플랫폼 특화 컬럼

### ✅ 모든 플랫폼 공통 (7개 컬럼)
| 컬럼 | 네이버블로그 | 네이버카페 | 밴드 | 유튜브 | 인스타그램 | 페이스북 | 카카오스토리 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **본문/설명 (content/description)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **작성일시 (datetime/timestamp)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **좋아요 수 (like_count)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **댓글 수 (comment_count)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **해시태그 (hashtags/hashtag)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **미디어 URL** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **수집일 (collected_date)** | ✅ | ✅ | ✅ | ✅ | - | - | - |

### ✅ 대부분 플랫폼 공통 (4-6개 플랫폼)
| 컬럼 | 네이버블로그 | 네이버카페 | 밴드 | 유튜브 | 인스타그램 | 페이스북 | 카카오스토리 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **게시물 ID (post_id/article_id)** | ✅ | ✅ | ✅ | ✅ | - | - | ✅ |
| **URL** | ✅ | ✅ | ✅ | ✅ | ✅ | - | - |
| **제목 (title)** | ✅ | ✅ | ✅ | ✅ | - | - | - |
| **조회수 (view_count)** | - | ✅ | ✅ | ✅ | - | - | - |
| **추천인 전화번호** | ✅ | ✅ | ✅ | ✅ | - | - | - |
| **추천인 파트너ID** | ✅ | ✅ | ✅ | ✅ | - | - | - |
| **플랫폼 구분** | ✅ | ✅ | ✅ | ✅ | - | - | - |
| **미디어 개수** | - | - | - | - | ✅ | ✅ | ✅ |
| **콘텐츠 글자수** | - | - | - | - | ✅ | ✅ | ✅ |

### 🔹 플랫폼 특화 컬럼

#### 네이버 (블로그 + 카페)
- `blog_id` / `cafe_id`, `cafe_name` - 블로그/카페 식별자
- `cafe_type` - 카페 유형 분류
- `is_pm_keyword` - PM 키워드 포함 여부

#### 밴드
- `entity_type` - 밴드/페이지 구분
- `entity_id`, `entity_name` - 엔티티 식별 정보
- `search_keyword` - 발견 검색어

#### 유튜브
- `channel_id`, `channel_name` - 채널 연결 정보
- `duration` - 영상 길이
- `tags` - 유튜브 태그 (해시태그와 별도)
- `thumbnail_url` - 썸네일 이미지
- `subscriber_count`, `video_count` - 채널 통계
- **OCR 관련 9개 컬럼** - 썸네일/프레임 텍스트 인식

#### 인스타그램
- `handle` - @사용자명
- `permalink` - 게시물 고유 링크
- `media_type` - IMAGE/VIDEO/CAROUSEL_ALBUM

#### 페이스북
- `share_count` - 공유 수 (페이스북 특화)
- `user_num` - 사용자 번호
- `audio_caption` - 음성 인식 결과

#### 카카오스토리
- `shortcode` - 게시물 고유 코드
- `p_num` - 수집 순번
- `media_caption` - 이미지 OCR 결과

---

## 3. 시각화 요약

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        📊 SNS 플랫폼별 데이터 수집 컬럼 현황                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    🌐 전체 공통 (7개)                                │   │
│  │  본문 | 작성일시 | 좋아요 | 댓글 | 해시태그 | 미디어URL | 수집일      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                🇰🇷 국내 플랫폼 공통 (4개)                             │   │
│  │       제목 | URL | 게시물ID | 플랫폼구분                              │   │
│  │       (네이버블로그, 네이버카페, 밴드)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              💼 PM 비즈니스 특화 (2개)                                │   │
│  │          추천인 전화번호 | 추천인 파트너ID                             │   │
│  │       (네이버블로그, 네이버카페, 밴드, 유튜브)                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │  네이버   │ │   밴드    │ │  유튜브   │ │  해외SNS  │                       │
│  │ 블로그ID  │ │entity_   │ │channel_  │ │ handle   │                       │
│  │ 카페ID   │ │type/id   │ │id/name   │ │permalink │                       │
│  │ 카페이름  │ │search_   │ │duration  │ │share_cnt │                       │
│  │ is_pm_  │ │keyword   │ │OCR(9개)  │ │media_type│                       │
│  │ keyword │ │          │ │subscriber│ │shortcode │                       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                       │
│    (2개)       (3개)       (10개+)      (인스타/FB/카카오)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 컬럼 수 비교

| 플랫폼 | 컬럼 수 | 특징 |
|--------|:------:|------|
| 네이버 블로그 | **15** | 기본 구조, 블로거 정보 별도 CSV |
| 네이버 카페 | **21** | 카페 메타정보 추가 |
| 밴드 | **22** | 엔티티 유형 구분, 검색어 추적 |
| 유튜브 비디오 | **28** | OCR 관련 컬럼 다수 (9개) |
| 유튜브 채널 | **15** | 채널 통계 중심 |
| 인스타그램 | **13** | 미디어 타입 분류 |
| 페이스북 | **14** | 공유 수 추가, 음성인식 |
| 카카오스토리 | **15** | OCR 결과 포함 |

---

## 5. 권장 사항

### 데이터 통합 시 고려사항
1. **공통 컬럼 표준화**: 컬럼명 통일 필요 (예: `datetime` vs `timestamp` vs `published_datetime`)
2. **PM 비즈니스 컬럼**: `sponsor_phone`, `sponsor_partner_id`는 인스타/페이스북/카카오에도 추가 권장
3. **OCR 결과**: 유튜브 방식을 다른 플랫폼에도 확대 적용 고려

### 향후 추가 권장 컬럼
- 모든 플랫폼에 `is_pm_keyword` 플래그 추가
- 통합 분석을 위한 `unified_id` 생성 고려
- `sentiment_score` (감정 분석 결과) 추가 고려

---

*본 보고서는 2025년 12월 기준 크롤러 버전 기반으로 작성되었습니다.*
