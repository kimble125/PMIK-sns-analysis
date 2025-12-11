# Git 빠른 시작 가이드

> Windows PC에서 GitHub로 프로젝트 업로드하기

## 🎯 목표

현재 프로젝트를 GitHub에 업로드하여:
1. MacBook에서 작업 계속하기
2. 버전 관리 및 백업
3. 포트폴리오로 활용
4. 팀원과 공유

---

## 📝 사전 준비

### 1. Git 설치 확인

PowerShell에서 실행:

```powershell
git --version
```

**설치되지 않았다면:**
- https://git-scm.com/download/win 에서 다운로드
- 설치 시 모든 옵션 기본값으로 진행

### 2. GitHub 계정 준비

- https://github.com 에서 계정 생성 (무료)
- 이메일 인증 완료

---

## 🚀 Step-by-Step 가이드

### Step 1: 프로젝트 정리 (5분)

```powershell
# 프로젝트 폴더로 이동
cd C:\Users\PC\Desktop\IT

# 정리 스크립트 실행
python cleanup_for_git.py
# 프롬프트에서 'y' 입력
```

**이 스크립트가 하는 일:**
- ✅ 불필요한 파일 삭제 (캐시, 로그 등)
- ✅ 중복 문서 제거
- ✅ 테스트 스크립트 정리
- ✅ API 키 보호 (.gitignore 적용)

### Step 2: Git 초기 설정 (3분)

```powershell
# 사용자 정보 설정 (한 번만 실행)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 설정 확인
git config --list
```

### Step 3: Git 저장소 초기화 (2분)

```powershell
# Git 저장소 초기화
git init

# 상태 확인
git status
```

**예상 출력:**
```
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .gitignore
        README.md
        naver_blog/
        ...
```

### Step 4: 파일 추가 및 커밋 (2분)

```powershell
# 모든 파일 추가 (.gitignore 규칙 자동 적용)
git add .

# 상태 확인
git status

# 커밋 (첫 번째 저장 지점)
git commit -m "Initial commit: PM Korea SNS Analysis v6.0"

# 커밋 확인
git log --oneline
```

### Step 5: GitHub 저장소 생성 (3분)

**브라우저에서:**

1. https://github.com 로그인
2. 우측 상단 `+` 버튼 → `New repository` 클릭
3. 저장소 설정:
   ```
   Repository name: pm-korea-sns-analysis
   Description: PM-International Korea SNS 데이터 수집 및 분석
   
   ⚪ Public  (포트폴리오용)
   🔘 Private (회사 내부용 - 권장)
   
   ☐ Add a README file (체크 안 함)
   ☐ Add .gitignore (체크 안 함)
   ☐ Choose a license (체크 안 함)
   ```
4. `Create repository` 클릭

### Step 6: GitHub에 업로드 (2분)

**GitHub 페이지에 표시된 명령어 복사:**

```powershell
# 원격 저장소 추가 (YOUR_USERNAME을 본인 것으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/pm-korea-sns-analysis.git

# 브랜치 이름 변경
git branch -M main

# 업로드
git push -u origin main
```

**GitHub 인증:**
- Username: GitHub 사용자명 입력
- Password: **Personal Access Token** 입력 (비밀번호 아님!)

**Personal Access Token 생성 방법:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. `Generate new token` → `Generate new token (classic)`
3. Note: `pm-korea-crawler`
4. Expiration: `90 days` 또는 `No expiration`
5. Scopes: `repo` 체크
6. `Generate token` 클릭
7. **토큰 복사** (다시 볼 수 없으니 안전한 곳에 저장!)

### Step 7: 업로드 확인 (1분)

브라우저에서 GitHub 저장소 페이지 새로고침:
- ✅ README.md 표시됨
- ✅ naver_blog/ 폴더 있음
- ✅ 파일 개수 확인

---

## 📊 최종 구조 확인

GitHub에 업로드된 구조:

```
pm-korea-sns-analysis/
├── .gitignore
├── README.md
├── MACBOOK_SETUP_GUIDE.md
├── GIT_QUICK_GUIDE.md
├── PM_SNS_Intern_Work_Plan_v2.2.md
├── PM_SNS_Theoretical_Background_v2_4.md
│
├── naver_blog/
│   ├── naver_blog_crawler_v5.py
│   ├── naver_blog_crawler_v6.py  ⭐ 병렬 처리 버전
│   ├── requirements_v5.txt
│   ├── config.example.py
│   ├── .env.example
│   ├── .gitignore
│   │
│   ├── output/
│   │   └── .gitkeep
│   │
│   └── (핵심 문서들)
│       ├── README.md
│       ├── FINAL_SUMMARY.md
│       ├── NAVER_API_FIELDS.md
│       └── ...
│
└── instagram/
    └── (인스타그램 크롤러)
```

**✅ 포함된 것:**
- 크롤러 코드 (v5.0, v6.0)
- 문서 및 가이드
- 설정 예시 파일
- 프로젝트 계획서

**❌ 제외된 것:**
- API 키 (config.py, .env)
- 크롤링 결과 (output/*.csv, *.json)
- 캐시 및 임시 파일
- 가상 환경

---

## 🔄 일상적인 Git 사용법

### 코드 수정 후 업로드

```powershell
# 변경사항 확인
git status

# 변경된 파일 추가
git add .

# 커밋 (변경 내용 설명)
git commit -m "Update: 크롤링 속도 개선"

# GitHub에 업로드
git push origin main
```

### MacBook에서 최신 코드 받기

```bash
# 최신 코드 다운로드
git pull origin main
```

### 변경 이력 확인

```powershell
# 커밋 로그 보기
git log --oneline --graph

# 특정 파일 변경 이력
git log --follow naver_blog/naver_blog_crawler_v6.py
```

---

## 🎓 유용한 Git 명령어

### 상태 확인

```powershell
# 현재 상태
git status

# 변경사항 비교
git diff

# 커밋 이력
git log --oneline -10
```

### 실수 복구

```powershell
# 마지막 커밋 취소 (파일은 유지)
git reset --soft HEAD~1

# 특정 파일 복원
git checkout -- filename.py

# 모든 변경사항 취소 (주의!)
git reset --hard HEAD
```

### 브랜치 사용

```powershell
# 새 브랜치 생성
git checkout -b feature/new-feature

# 브랜치 목록
git branch

# 브랜치 전환
git checkout main

# 브랜치 병합
git merge feature/new-feature
```

---

## ⚠️ 주의사항

### 절대 업로드하면 안 되는 것

- ❌ API 키 (config.py, .env)
- ❌ 비밀번호
- ❌ 개인정보가 포함된 데이터
- ❌ 대용량 파일 (100MB 이상)

### .gitignore가 보호하는 파일

```
config.py          # API 키
.env               # 환경 변수
output/*.csv       # 크롤링 결과
output/*.json      # 통계 데이터
__pycache__/       # Python 캐시
.venv/             # 가상 환경
```

---

## 🆘 문제 해결

### 문제 1: git push 실패

```
error: failed to push some refs
```

**해결:**
```powershell
# 최신 코드 먼저 받기
git pull origin main --rebase

# 다시 푸시
git push origin main
```

### 문제 2: 인증 실패

```
remote: Support for password authentication was removed
```

**해결:**
- Personal Access Token 사용 (위 Step 6 참조)
- 비밀번호 대신 토큰 입력

### 문제 3: 파일이 너무 큼

```
error: file is too large
```

**해결:**
```powershell
# .gitignore에 추가
echo "large_file.csv" >> .gitignore

# 캐시에서 제거
git rm --cached large_file.csv

# 다시 커밋
git commit -m "Remove large file"
```

---

## 📞 추가 도움

### 공식 문서
- Git: https://git-scm.com/doc
- GitHub: https://docs.github.com

### 학습 자료
- GitHub Skills: https://skills.github.com
- Git 시각화: https://git-school.github.io/visualizing-git

### 빠른 참조
```powershell
# 도움말
git --help
git commit --help

# 설정 확인
git config --list
```

---

## ✅ 완료 체크리스트

- [ ] Git 설치 및 설정
- [ ] 프로젝트 정리 (cleanup_for_git.py)
- [ ] Git 저장소 초기화
- [ ] 파일 추가 및 커밋
- [ ] GitHub 저장소 생성
- [ ] GitHub에 업로드
- [ ] 업로드 확인
- [ ] MacBook에서 클론 (MACBOOK_SETUP_GUIDE.md 참조)

---

**작성일**: 2025-11-02  
**소요 시간**: 약 20분  
**난이도**: ⭐⭐☆☆☆ (초급)
