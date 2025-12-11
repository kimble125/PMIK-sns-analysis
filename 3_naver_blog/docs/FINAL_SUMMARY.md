# PM 네이버 블로그 크롤러 v9.1 Final 완성! 🎉

## 📊 1. 테스트 결과 분석

### ✅ 수집 데이터 품질
- **총 수집**: 138개 (20분 테스트)
- **데이터 품질**: 우수 ⭐⭐⭐⭐⭐
- **잘못된 데이터**: 없음
- **후원번호 추출**: 정상 작동

### 📋 수집된 정보
- 제목, 본문, 날짜, URL ✅
- 후원번호 (7-8자리) ✅
- 해시태그, 이미지 URL ✅
- 좋아요, 댓글 수 ✅

---

## 🎯 2. Final 버전 변경사항

### 주요 수정 (config.yaml)

| 항목 | Test 버전 | Final 버전 |
|------|-----------|------------|
| **테스트 모드** | enabled: true | enabled: false |
| **시간 제한** | 20분 | 무제한 |
| **키워드** | "피엠인터내셔널 2025" | "피엠인터내셔널" |
| **키워드당 목표** | 800개 | 1000개 |
| **총 키워드 수** | 33개 (연도 포함) | 11개 (연도 제거) |

### 키워드 목록 (11개)

**Primary (4개):**
1. 피엠인터내셔널
2. 독일피엠
3. PM인터내셔널
4. 피엠코리아

**Secondary (7개):**
5. 피트라인
6. 탑쉐이프
7. 프로쉐이프
8. 디드링크
9. 뮤노겐
10. 엑티바이즈
11. 파워칵테일

### 연도 제거 이유
- ✅ 오래된 데이터도 수집 가능
- ✅ 키워드 수 감소 (33개 → 11개)
- ✅ 실행 시간 단축 (예상: 22-33시간)

---

## 🚀 3. VM 실행 방법

### Step 1: 파일 전송

**Git 사용 (추천):**
```bash
# 로컬 Mac
cd ~/Documents/IT/PMIK-sns-analysis
git add naver_blog/pm_naver_blog_crawler_v9_1_final.py
git add naver_blog/config.yaml
git commit -m "Add v9.1 final version"
git push origin main

# VM
cd ~/PMIK-sns-analysis
git pull origin main
```

**SCP 사용:**
```bash
# 로컬 Mac
cd ~/Documents/IT/PMIK-sns-analysis/naver_blog
scp pm_naver_blog_crawler_v9_1_final.py config.yaml pmi@PMIKR-DATA-CRAWLER:~/PMIK-sns-analysis/naver_blog/
```

### Step 2: VM에서 실행

```bash
# SSH 접속
ssh pmi@PMIKR-DATA-CRAWLER

# 디렉토리 이동
cd ~/PMIK-sns-analysis/naver_blog
source ../.venv/bin/activate

# PyYAML 설치
pip install pyyaml

# 백그라운드 실행 (로컬 종료해도 계속 실행)
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &

# 프로세스 ID 저장
echo $!

# 로그 확인
tail -f crawler.log
```

### Step 3: 로컬 컴퓨터 종료해도 OK!

**nohup 사용 시:**
- ✅ SSH 연결 끊어도 계속 실행
- ✅ 로컬 Mac 종료해도 계속 실행
- ✅ VM만 켜져 있으면 OK

**진행 상황 확인:**
```bash
# 다시 SSH 접속
ssh pmi@PMIKR-DATA-CRAWLER

# 로그 확인
cd ~/PMIK-sns-analysis/naver_blog
tail -f crawler.log

# 수집 개수 확인
ls -lht naver_blog_pm_v9_1_final_*.csv
wc -l naver_blog_pm_v9_1_final_*.csv
```

---

## 💾 4. 데이터 안전성

### ✅ VM 종료 시 유지되는 것
1. **수집된 CSV 파일** - 디스크에 저장
2. **체크포인트 파일** - `checkpoints/` 디렉토리
3. **실패 URL 로그** - `failed_urls.json`
4. **로그 파일** - `crawler.log`

### ❌ VM 종료 시 사라지는 것
1. **실행 중인 프로세스** - 재시작 필요
2. **메모리 상의 데이터** - 체크포인트 저장 전 데이터

### 🔄 체크포인트 시스템
- **1시간마다 자동 저장**
- CSV + 메타데이터(JSON)
- 중단 후 재시작 시 자동 로드

### 재시작 방법
```bash
# VM 재시작 후
cd ~/PMIK-sns-analysis/naver_blog
source ../.venv/bin/activate
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &

# 이전 데이터 자동 로드 확인
tail -f crawler.log
# "📂 이전 데이터 로드: XXX개" 메시지 확인
```

---

## ⏱️ 5. 예상 실행 시간

### 키워드별 예상
- **키워드당 1000개**: 2-3시간
- **총 11개 키워드**: 22-33시간
- **체크포인트**: 1시간마다 자동 저장

### 실행 시간표
| 시간 | 예상 수집량 | 체크포인트 |
|------|------------|-----------|
| 1시간 | ~300개 | ✅ 저장 |
| 3시간 | ~1,000개 | ✅ 저장 |
| 6시간 | ~2,000개 | ✅ 저장 |
| 12시간 | ~4,000개 | ✅ 저장 |
| 24시간 | ~8,000개 | ✅ 저장 |
| 30시간 | ~11,000개 | ✅ 완료 |

---

## 📊 6. 모니터링 방법

### 실시간 로그 확인
```bash
# SSH 접속
ssh pmi@PMIKR-DATA-CRAWLER

# 로그 확인
tail -f ~/PMIK-sns-analysis/naver_blog/crawler.log

# 특정 키워드 검색
grep "수집 완료" crawler.log | wc -l
grep "체크포인트 저장" crawler.log
```

### 수집 파일 확인
```bash
# CSV 파일 목록
ls -lht ~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v9_1_final_*.csv

# 체크포인트 파일
ls -lht ~/PMIK-sns-analysis/naver_blog/checkpoints/

# 수집 개수
wc -l ~/PMIK-sns-analysis/naver_blog/naver_blog_pm_v9_1_final_*.csv
```

### 프로세스 확인
```bash
# 실행 중인지 확인
ps aux | grep pm_naver_blog_crawler_v9_1_final

# CPU/메모리 사용량
top -p $(pgrep -f pm_naver_blog_crawler_v9_1_final)
```

---

## 🛑 7. 중단 및 재시작

### 안전한 중단
```bash
# 프로세스 ID 확인
ps aux | grep pm_naver_blog_crawler_v9_1_final

# 정상 종료 (SIGTERM)
kill <PID>

# 강제 종료는 피하기!
# kill -9 <PID>  # 데이터 손실 가능
```

### 재시작
```bash
# 백그라운드 실행
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &

# 로그 확인 (이전 데이터 자동 로드)
tail -f crawler.log
```

---

## 📁 8. 생성되는 파일

### 주요 파일
1. **naver_blog_pm_v9_1_final_YYYYMMDD_HHMMSS.csv** - 최종 수집 데이터
2. **checkpoints/checkpoint_YYYYMMDD_HHMMSS.csv** - 1시간마다 저장
3. **checkpoints/checkpoint_YYYYMMDD_HHMMSS_meta.json** - 메타데이터
4. **failed_urls.json** - 실패 URL 목록
5. **crawler.log** - 실행 로그

### 파일 크기 예상
- CSV 파일: ~50MB (11,000개 기준)
- 체크포인트: ~5MB (1,000개 기준)
- 로그 파일: ~10MB

---

## 🔧 9. 문제 해결

### 자주 발생하는 문제

**1. "설정 파일을 찾을 수 없습니다"**
```bash
ls -l config.yaml
pwd  # 현재 디렉토리 확인
```

**2. "No module named 'yaml'"**
```bash
pip install pyyaml
```

**3. Chrome/Selenium 오류**
```bash
google-chrome --version
pip install webdriver-manager
```

**4. 메모리 부족**
```bash
free -h
pkill -f pm_naver_blog_crawler_v9_1_final
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &
```

**5. 디스크 공간 부족**
```bash
df -h
rm -rf checkpoints/checkpoint_202511*.csv  # 오래된 체크포인트 삭제
```

---

## ✅ 10. 체크리스트

### 실행 전
- [ ] config.yaml 확인 (test_mode: false)
- [ ] 파일 VM에 전송 완료
- [ ] 가상환경 활성화
- [ ] PyYAML 설치
- [ ] 디스크 공간 확인 (최소 10GB)

### 실행 중
- [ ] nohup으로 백그라운드 실행
- [ ] 프로세스 ID 저장
- [ ] 로그 파일 확인 (정상 실행)
- [ ] 체크포인트 파일 생성 확인 (1시간 후)

### 실행 후
- [ ] CSV 파일 다운로드
- [ ] 데이터 품질 확인
- [ ] 후원번호 패턴 분석 확인
- [ ] 중복 데이터 확인

---

## 📞 11. 요약

### 핵심 명령어 (복사해서 사용)

**VM 실행:**
```bash
ssh pmi@PMIKR-DATA-CRAWLER
cd ~/PMIK-sns-analysis/naver_blog
source ../.venv/bin/activate
pip install pyyaml
nohup python pm_naver_blog_crawler_v9_1_final.py > crawler.log 2>&1 &
echo $!
tail -f crawler.log
```

**진행 확인:**
```bash
ssh pmi@PMIKR-DATA-CRAWLER
cd ~/PMIK-sns-analysis/naver_blog
tail -f crawler.log
ls -lht naver_blog_pm_v9_1_final_*.csv
```

**중단:**
```bash
ps aux | grep pm_naver_blog_crawler_v9_1_final
kill <PID>
```

---

## 🎉 완료!

모든 준비가 완료되었습니다!

**다음 단계:**
1. ✅ 파일을 VM에 전송
2. ✅ VM에서 백그라운드 실행
3. ✅ 로컬 컴퓨터 종료 가능
4. ✅ 22-33시간 후 완료 예상
5. ✅ 체크포인트로 안전하게 저장

**작성자**: PMI Korea 데이터 분석팀  
**버전**: 9.1.0 Final  
**날짜**: 2025-11-17

---

**📚 추가 문서:**
- `README_V9_1.md` - 사용 가이드
- `V9_1_CHANGES.md` - 상세 변경사항
- `VM_DEPLOYMENT_GUIDE.md` - VM 배포 가이드 (상세)
