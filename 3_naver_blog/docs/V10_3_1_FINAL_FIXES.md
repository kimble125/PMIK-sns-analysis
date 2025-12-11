# v10.3.1 최종 수정사항 (2025-11-21)

## 🐛 수정된 버그

### 1. NameError: logger 정의 순서 오류

**에러 메시지**:
```
NameError: name 'logger' is not defined
```

**원인**:
- API 키 로드 코드(line 146)에서 `logger.info()` 사용
- logger 정의는 line 207에서 이루어짐
- logger가 정의되기 전에 사용하여 오류 발생

**수정**:
```python
# 수정 전 (line 146)
logger.info("✅ config.py에서 Naver API 키 로드 완료")

# 수정 후 (line 146)
print("✅ config.py에서 Naver API 키 로드 완료")

# logger 정의 후 다시 로깅 (line 210-213)
logger = logging.getLogger(__name__)
if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
    logger.info(f"✅ Naver API 키 로드 완료 (Client ID: {NAVER_CLIENT_ID[:10]}...)")
else:
    logger.warning("⚠️  Naver API 키가 설정되지 않았습니다.")
```

---

## ⏱️ 시간 제한 변경

### 요청사항
- 1시간 → 40분으로 변경
- 종료 시간에 작업 중이던 작업까지만 완료

### 수정 파일

#### 1. `pm_naver_blog_crawler_v10_3_test.py` (line 126)
```python
# 수정 전
MAX_DURATION_SECONDS = 60 * 60  # 1시간 = 3600초

# 수정 후
MAX_DURATION_SECONDS = 40 * 60  # 40분 = 2400초
```

#### 2. `config.yaml` (line 19)
```yaml
# 수정 전
test_mode:
  enabled: true
  max_duration_minutes: 210  # 3시간 30분 테스트

# 수정 후
test_mode:
  enabled: true
  max_duration_minutes: 40  # v10.3.1: 40분 테스트 (작업 중인 게시물까지만 완료 후 종료)
```

### 동작 방식

```python
def check_time_limit():
    """시간 제한 확인"""
    elapsed = time.time() - START_TIME
    if elapsed >= MAX_DURATION_SECONDS:
        return True
    return False

# 메인 루프에서 사용
for keyword_idx, keyword in enumerate(all_keywords, 1):
    # 키워드 검색 전 시간 확인
    if check_time_limit():
        logger.info("⏰ 시간 제한 도달, 크롤링 중단")
        break
    
    for idx, result in enumerate(search_results, 1):
        # 각 게시물 크롤링 전 시간 확인
        if check_time_limit():
            logger.info("⏰ 시간 제한 도달, 현재 키워드 처리 완료 후 종료")
            break
```

**특징**:
- 40분 경과 시 새로운 키워드 검색 중단
- 현재 크롤링 중인 게시물은 완료
- 데이터 손실 없이 안전하게 종료
- 수집된 데이터는 자동 저장

---

## 📋 전체 수정 요약

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| **logger 오류** | NameError 발생 | print 사용 후 logger 재로깅 |
| **실행 시간** | 1시간 (3600초) | 40분 (2400초) |
| **config.yaml** | 210분 | 40분 |
| **종료 방식** | 시간 제한 도달 시 즉시 종료 | 작업 중인 게시물까지 완료 후 종료 |

---

## 🚀 VM에서 실행 방법

### 1. 파일 업로드
로컬에서 수정된 파일을 VM으로 업로드:

```bash
# 로컬 맥북에서 실행
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog

# VM으로 업로드
scp pm_naver_blog_crawler_v10_3_test.py pmi@your_vm_ip:~/PMIK-sns-analysis/naver_blog/
scp config.yaml pmi@your_vm_ip:~/PMIK-sns-analysis/naver_blog/
```

### 2. config.py 확인
VM에서 API 키 설정 확인:

```bash
# VM에서 실행
cd ~/PMIK-sns-analysis/naver_blog

# config.py 존재 확인
ls -la config.py

# API 키 확인
python3 -c "
try:
    import config
    print(f'Client ID: {config.NAVER_CLIENT_ID[:10]}...')
    print('✅ config.py 정상')
except Exception as e:
    print(f'❌ config.py 오류: {e}')
"
```

### 3. 크롤러 실행

```bash
cd ~/PMIK-sns-analysis/naver_blog
python3 pm_naver_blog_crawler_v10_3_test.py
```

### 4. 예상 출력

**성공 시**:
```
⚠️  EasyOCR 또는 PIL을 설치하지 않았습니다. OCR 기능이 비활성화됩니다.
설치: pip install easyocr pillow
✅ config.py에서 Naver API 키 로드 완료
2025-11-21 00:20:00 [INFO] ✅ Naver API 키 로드 완료 (Client ID: abcdefghij...)
2025-11-21 00:20:00 [INFO] ================================================================================
2025-11-21 00:20:00 [INFO] 📊 PM-International Korea 네이버 블로그 크롤러 v10.3.1 시작
2025-11-21 00:20:00 [INFO] ================================================================================
2025-11-21 00:20:00 [INFO] ⏰ 시작 시간: 2025-11-21 00:20:00
2025-11-21 00:20:00 [INFO] ⏱️  최대 실행 시간: 40분 (작업 중인 게시물까지만 완료 후 종료)
2025-11-21 00:20:05 [INFO] 🔧 Selenium 드라이버 초기화 중...
2025-11-21 00:20:10 [INFO] ✅ Selenium 드라이버 준비 완료
2025-11-21 00:20:10 [INFO] 🔍 총 44개 키워드로 검색 시작
2025-11-21 00:20:10 [INFO]
[1/44] 키워드: '피엠인터내셔널' 검색 중...
2025-11-21 00:20:11 [INFO] 📝 '피엠인터내셔널' 검색 결과: 100개
```

---

## ⚠️ 주의사항

### 1. OCR 기능 비활성화
```
⚠️  EasyOCR 또는 PIL을 설치하지 않았습니다. OCR 기능이 비활성화됩니다.
```

**해결** (선택사항):
```bash
# VM에서 실행
pip3 install easyocr pillow
```

**참고**: OCR 없이도 크롤링은 정상 작동하며, `image_ocr_text` 컬럼만 비어있습니다.

### 2. urllib3 경고
```
RequestsDependencyWarning: urllib3 (2.5.0) or chardet (4.0.0) doesn't match a supported version!
```

**영향**: 경고일 뿐 크롤링에는 영향 없음. 무시해도 됩니다.

**해결** (선택사항):
```bash
pip3 install --upgrade requests urllib3
```

### 3. 40분 후 자동 종료
- 40분 경과 시 새로운 키워드 검색 중단
- 현재 크롤링 중인 게시물은 완료
- 로그에 "⏰ 시간 제한 도달" 메시지 출력

---

## 📊 예상 결과

### 40분 실행 시 예상 수집량

**가정**:
- 게시물당 평균 소요 시간: 25초
- 40분 = 2400초
- 예상 수집량: 2400 / 25 = **약 96개**

**실제 수집량**:
- API 검색 시간, 필터링, 중복 제거 등을 고려하면
- **60-80개** 정도 예상

### 출력 파일
- `naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS.csv` - 게시물 데이터
- `naver_blog_pm_v10_3_bloggers_YYYYMMDD_HHMMSS.csv` - 블로거 프로필
- `naver_blog_pm_v10_3_posts_YYYYMMDD_HHMMSS_report.txt` - 실행 리포트

---

## ✅ 체크리스트

- [x] logger 정의 순서 오류 수정
- [x] 시간 제한 40분으로 변경
- [x] config.yaml 업데이트
- [x] 작업 중인 게시물까지만 완료 로직 확인
- [x] 문서 업데이트
- [ ] VM에 파일 업로드
- [ ] VM에서 config.py 확인
- [ ] 크롤러 실행 테스트
- [ ] 40분 후 정상 종료 확인

---

## 🔍 문제 발생 시

### Q1: 여전히 logger 오류가 나요
```bash
# 파일이 제대로 업로드되었는지 확인
cd ~/PMIK-sns-analysis/naver_blog
head -150 pm_naver_blog_crawler_v10_3_test.py | tail -10
```

### Q2: API 키를 못 찾아요
```bash
# config.py 확인
ls -la config.py
cat config.py
```

### Q3: 40분이 아니라 다른 시간으로 변경하고 싶어요
```python
# pm_naver_blog_crawler_v10_3_test.py (line 126)
MAX_DURATION_SECONDS = 30 * 60  # 30분으로 변경
```

---

**최종 수정 일시**: 2025-11-21 00:20
**버전**: v10.3.1
**작성자**: PMI Korea 데이터 분석팀
