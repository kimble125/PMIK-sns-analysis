# 📝 .env 파일 생성 가이드

## 🔑 .env 파일이란?

**.env 파일**은 YouTube API 키를 안전하게 저장하는 설정 파일입니다.
- 코드에 직접 API 키를 넣지 않고 별도 파일로 관리
- Git에 업로드되지 않아 보안 유지

---

## 📋 .env 파일 생성 방법

### 방법 1: 텍스트 에디터로 생성 (권장)

1. **메모장** 또는 **VS Code** 열기
2. 다음 내용 입력:
   ```
   YOUTUBE_API_KEY=실제_유튜브_API_키
   ```
3. 파일명: `.env` (확장자 없음!)
4. 저장 위치: `/Users/kimble/Documents/IT/PMIK-sns-analysis/youtube/.env`

### 방법 2: 터미널로 생성

```bash
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/youtube
echo "YOUTUBE_API_KEY=실제_유튜브_API_키" > .env
```

---

## 🎯 .env 파일 예시

```
YOUTUBE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**주의사항:**
- ✅ `=` 앞뒤 공백 없음
- ✅ 따옴표 없음
- ✅ 한 줄로 작성
- ❌ `YOUTUBE_API_KEY = "키값"` (잘못된 예시)

---

## 🔐 YouTube API 키 발급 방법

1. https://console.cloud.google.com/ 접속
2. **새 프로젝트 생성**
3. **API 및 서비스** > **라이브러리** 클릭
4. **YouTube Data API v3** 검색 후 **활성화**
5. **사용자 인증 정보** > **API 키 만들기**
6. 생성된 API 키 복사
7. `.env` 파일에 붙여넣기

---

## ✅ .env 파일 확인

파일이 제대로 생성되었는지 확인:

```bash
cat /Users/kimble/Documents/IT/PMIK-sns-analysis/youtube/.env
```

출력 예시:
```
YOUTUBE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🚀 Google Colab에서 사용

1. `.env` 파일을 로컬에 저장
2. Colab 셀 2에서 파일 업로드
3. 자동으로 API 키 적용

---

## ⚠️ 주의사항

- **절대 Git에 업로드하지 마세요!** (이미 .gitignore에 포함됨)
- **API 키를 공유하지 마세요!**
- **API 키가 노출되면 즉시 재발급하세요!**

---

## 📁 현재 위치

`.env` 파일 위치:
```
/Users/kimble/Documents/IT/PMIK-sns-analysis/youtube/.env
```

`.env.example` 파일 (템플릿):
```
/Users/kimble/Documents/IT/PMIK-sns-analysis/youtube/.env.example
```

---

## 🎉 완료!

이제 Google Colab 셀 2에서 `.env` 파일을 업로드하면 자동으로 API 키가 설정됩니다!
