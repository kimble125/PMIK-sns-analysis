# 🚀 v10.2 VM 실행 가이드 (2시간 테스트)

## 📋 실행 개요

**목표**: 2시간 동안 크롤링, 노트북 종료해도 계속 실행, 로컬 다운로드
**예상 수집량**: 800~2,000개
**설정**:
- 키워드당 500건 수집
- 연도: 2018-2025 (8년)
- 제품 테스트: 레스토레이트 (1000건)
- 필터링: 제외 키워드 4개 이상

---

## 🔧 1단계: 로컬에서 VM으로 파일 업로드

### 파일 업로드
```bash
# 로컬 터미널에서
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog

# 크롤러와 설정 파일 업로드
scp pm_naver_blog_crawler_v10_2_test.py crawler:~/PMIK-sns-analysis/naver_blog/
scp config.yaml crawler:~/PMIK-sns-analysis/naver_blog/
```

**확인 메시지:**
```
pm_naver_blog_crawler_v10_2_test.py    100%  xxx KB   x.xMB/s   00:0x
config.yaml                             100%  xxx KB   x.xMB/s   00:00
```

---

## 🖥️ 2단계: VM 접속 및 screen 세션 시작

### VM 접속
```bash
ssh crawler
```

### 작업 디렉토리로 이동
```bash
cd ~/PMIK-sns-analysis/naver_blog
```

### 파일 확인
```bash
ls -lh pm_naver_blog_crawler_v10_2_test.py config.yaml
```

**예상 출력:**
```
-rw-r--r-- 1 user user  xxx pm_naver_blog_crawler_v10_2_test.py
-rw-r--r-- 1 user user  xxx config.yaml
```

### screen 세션 시작
```bash
screen -S crawl_v10_2
```

**설명:**
- `screen`: 가상 터미널 (노트북 종료해도 계속 실행)
- `-S crawl_v10_2`: 세션 이름

---

## ▶️ 3단계: 크롤러 실행

### 실행 명령
```bash
python3 pm_naver_blog_crawler_v10_2_test.py
```

### 실행 확인
**초기 로그:**
```
======================================================================
🚀 PM International 네이버 블로그 크롤러 v10.2.0 시작
🔄 v10.2 주요 수정: 필터링 완화, 프로필 분리, 컬럼명 명확화
🆕 v10.1 신기능:
   - 프로필 정보 수집
   - 이미지 OCR 처리 (EasyOCR)
   - 19가지 콘텐츠 타입 자동 분류
📅 v10.2: 키워드 연도 확장 완료 (2018-2025)
   원본 키워드: 12개
   확장 후: 96개 (8년치)
🎯 목표: 10,000~15,000개 (품질 우선)
🧪 테스트 모드: 120분 제한
======================================================================
```

**크롤링 진행 중:**
```
[피엠인터내셔널 2024: 1/500] 크롤링 중...
✅ 수집 완료: PM인터내셔널 제품 리뷰 - 피트라인으로 건강...
[피엠인터내셔널 2024: 2/500] 크롤링 중...
```

---

## 🔌 4단계: screen Detach (노트북 종료 가능)

### Detach 방법
**키 조합:** `Ctrl + A`, 그 다음 `D`

1. `Ctrl`과 `A`를 동시에 누름
2. 손을 뗌
3. `D`를 누름

**메시지:**
```
[detached from xxxxx.crawl_v10_2]
```

### VM에서 로그아웃
```bash
exit
```

**이제 노트북을 종료해도 크롤러는 계속 실행됩니다!** ✅

---

## 🔍 5단계: 진행 상황 확인 (중간 체크)

### VM 재접속
```bash
ssh crawler
```

### screen 세션 재접속
```bash
screen -r crawl_v10_2
```

**다시 크롤러 화면이 보입니다!**

### 확인 후 다시 Detach
`Ctrl + A`, `D`

---

## ⏰ 6단계: 2시간 후 결과 확인

### VM 접속
```bash
ssh crawler
cd ~/PMIK-sns-analysis/naver_blog
```

### 실행 상태 확인
```bash
screen -r crawl_v10_2
```

**완료 메시지 확인:**
```
======================================================================
📊 PM-International 네이버 블로그 크롤러 v10.2 테스트 결과 보고서
======================================================================

⏱️  실행 시간
────────────────────────────────────────────────────────────────────────────────
• 총 실행 시간: 120.0분 (7200초)
• 시작 시간: 2025-11-20 15:00:00
• 종료 시간: 2025-11-20 17:00:00

📈 수집 성과
────────────────────────────────────────────────────────────────────────────────
• ✅ 최종 수집: 1,234개
• 📊 시도: 5,678회
• ✅ 성공률: 21.7%
• 🔍 필터링: 3,456개 (60.9%)
• 🔄 중복: 987개 (17.4%)
• ❌ 에러: 1회 (0.0%)
...
```

### 생성된 파일 확인
```bash
ls -lh *v10_2*.csv *v10_2*_report.txt
```

**예상 출력:**
```
-rw-r--r-- 1 user user 15M naver_blog_pm_v10_2_posts_20251120_170000.csv
-rw-r--r-- 1 user user 1.2M naver_blog_pm_v10_2_bloggers_20251120_170000.csv
-rw-r--r-- 1 user user 25K naver_blog_pm_v10_2_posts_20251120_170000_report.txt
```

### screen 세션 종료
```bash
exit  # screen 세션에서 나가기 (Ctrl+D)
```

---

## 💾 7단계: 로컬로 다운로드

### VM에서 로그아웃
```bash
exit  # VM에서 나가기
```

### 로컬 터미널에서 다운로드
```bash
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog

# 모든 v10.2 결과 파일 다운로드
scp 'crawler:~/PMIK-sns-analysis/naver_blog/*v10_2*.csv' .
scp 'crawler:~/PMIK-sns-analysis/naver_blog/*v10_2*_report.txt' .
```

**진행 표시:**
```
naver_blog_pm_v10_2_posts_xxx.csv        100%   15MB  xx.xMB/s   00:0x
naver_blog_pm_v10_2_bloggers_xxx.csv     100%  1.2MB  xx.xMB/s   00:00
naver_blog_pm_v10_2_posts_xxx_report.txt 100%   25KB  xx.xKB/s   00:00
```

### 로컬에서 파일 확인
```bash
ls -lh *v10_2*
```

**완료!** 🎉

---

## 📊 8단계: 결과 분석

### 보고서 확인
```bash
cat naver_blog_pm_v10_2_posts_*_report.txt
```

### CSV 파일 확인
```bash
# 게시물 수 확인
wc -l naver_blog_pm_v10_2_posts_*.csv

# 블로거 수 확인
wc -l naver_blog_pm_v10_2_bloggers_*.csv

# 첫 5줄 확인
head -n 5 naver_blog_pm_v10_2_posts_*.csv
```

---

## 🔧 트러블슈팅

### 문제 1: screen 세션을 찾을 수 없음
```bash
screen -ls
```

**해결:**
- 세션 목록 확인
- 다른 이름으로 실행되었을 수 있음

### 문제 2: 크롤러가 중단됨
```bash
screen -r crawl_v10_2
# 에러 메시지 확인
```

**해결:**
- 로그 확인: `tail -n 50 crawler.log`
- 재실행

### 문제 3: 파일 다운로드 실패
```bash
# VM에서 파일 존재 확인
ssh crawler "ls -lh ~/PMIK-sns-analysis/naver_blog/*v10_2*"
```

**해결:**
- 경로 확인
- 파일명 정확히 입력

### 문제 4: 수집량이 너무 적음 (< 100개)
**원인**: 필터링 과다
**해결**: `COLLECTION_IMPROVEMENT_GUIDE.md` 참조
- 제외 키워드 기준 5개로 상향
- 로그 확인하여 원인 파악

---

## ⚡ 빠른 명령어 모음

### 업로드
```bash
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp pm_naver_blog_crawler_v10_2_test.py config.yaml crawler:~/PMIK-sns-analysis/naver_blog/
```

### 실행
```bash
ssh crawler
cd ~/PMIK-sns-analysis/naver_blog
screen -S crawl_v10_2
python3 pm_naver_blog_crawler_v10_2_test.py
# Ctrl+A, D (Detach)
exit
```

### 확인
```bash
ssh crawler
screen -r crawl_v10_2
# Ctrl+A, D (Detach)
exit
```

### 다운로드
```bash
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog
scp 'crawler:~/PMIK-sns-analysis/naver_blog/*v10_2*.csv' .
scp 'crawler:~/PMIK-sns-analysis/naver_blog/*v10_2*_report.txt' .
```

---

## 📝 체크리스트

### 실행 전
- [ ] 로컬 파일 백업 완료
- [ ] VM에 파일 업로드 완료
- [ ] config.yaml 설정 확인 (2시간, 500건)

### 실행 중
- [ ] screen 세션 Detach 완료
- [ ] 노트북 종료 가능 확인

### 실행 후
- [ ] 2시간 후 결과 확인
- [ ] 파일 다운로드 완료
- [ ] 로컬에서 파일 확인

### 분석
- [ ] 보고서 확인
- [ ] 수집량 확인 (목표: 800~2,000개)
- [ ] 연도별/키워드별 통계 확인
- [ ] 레스토레이트 효과 확인

---

## 🎯 예상 결과

### 수집량
- **기존 (v10.1)**: 3개 (2시간)
- **v10.2 목표**: 800~2,000개 (2시간)
- **실제 결과**: 보고서 확인

### 파일
1. **posts.csv**: 게시물 정보 (프로필 제외)
2. **bloggers.csv**: 블로거 프로필 (중복 제거)
3. **report.txt**: 상세 보고서

### 보고서 내용
- 실행 시간
- 수집 성과
- 키워드별 통계 (Primary, Secondary, Product Test)
- 연도별 통계 (2018-2025)
- 필터링 통계
- 레스토레이트 영향 분석

---

**작성일**: 2025-11-20
**버전**: v10.2
**실행 시간**: 2시간
**예상 수집**: 800~2,000개
