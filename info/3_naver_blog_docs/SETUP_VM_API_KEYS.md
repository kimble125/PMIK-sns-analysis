# VM에서 Naver API 키 설정 가이드

## 🔍 문제 원인

v10.3에서 `config.py` 로드 로직이 누락되어 API 키를 찾지 못했습니다.
v10.3.1에서 수정 완료했습니다.

---

## ✅ 해결 방법

### 방법 1: config.py 파일 생성 (권장)

VM의 naver_blog 디렉토리에서 실행:

```bash
cd ~/naver_blog

# config.py 파일 생성
cat > config.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Naver API 설정 파일
주의: 이 파일은 .gitignore에 포함되어 있어 Git에 커밋되지 않습니다.
"""

# Naver Open API 인증 정보
NAVER_CLIENT_ID = "your_actual_client_id_here"
NAVER_CLIENT_SECRET = "your_actual_client_secret_here"
EOF

# 보안을 위해 권한 제한
chmod 600 config.py

echo "✅ config.py 파일 생성 완료"
```

**중요**: `your_actual_client_id_here`와 `your_actual_client_secret_here`를 실제 API 키로 교체하세요.

---

### 방법 2: 로컬에서 VM으로 복사

로컬 맥북에 `config.py`가 있다면:

```bash
# 로컬 맥북에서 실행
cd /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog

# VM으로 복사 (VM 정보에 맞게 수정)
scp config.py your_vm_user@your_vm_ip:~/naver_blog/

# 예시:
# scp config.py azureuser@20.196.xxx.xxx:~/naver_blog/
```

---

### 방법 3: 환경 변수 설정 (임시)

config.py 없이 환경 변수만 사용:

```bash
# VM에서 실행
export NAVER_CLIENT_ID="your_actual_client_id_here"
export NAVER_CLIENT_SECRET="your_actual_client_secret_here"

# 크롤러 실행
python pm_naver_blog_crawler_v10_3_test.py
```

**단점**: 세션이 종료되면 다시 설정해야 함.

---

## 🔑 API 키 확인 방법

### 로컬에 config.py가 있는지 확인

```bash
# 로컬 맥북에서
ls -la /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog/config.py

# 있다면 내용 확인 (민감 정보 주의)
head -20 /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog/config.py
```

### VM에 config.py가 있는지 확인

```bash
# VM에서
cd ~/naver_blog
ls -la config.py

# 있다면 API 키 설정 확인 (실제 키는 보이지 않게)
python -c "
try:
    import config
    print(f'Client ID: {config.NAVER_CLIENT_ID[:10]}...')
    print(f'Client Secret: {config.NAVER_CLIENT_SECRET[:10]}...')
    print('✅ config.py 정상')
except Exception as e:
    print(f'❌ config.py 오류: {e}')
"
```

---

## 🚀 v10.3.1 실행 테스트

API 키 설정 후 테스트:

```bash
cd ~/naver_blog

# v10.3.1 실행
python pm_naver_blog_crawler_v10_3_test.py
```

**성공 로그 확인**:
```
✅ config.py에서 Naver API 키 로드 완료
📊 PM-International Korea 네이버 블로그 크롤러 v10.3.1 시작
```

**실패 로그** (API 키 없음):
```
⚠️  Naver API 키가 설정되지 않았습니다.
⚠️  Naver API 키가 없습니다.
```

---

## 📋 v10.2 vs v10.3.1 비교

### v10.2 (정상 작동)
```python
try:
    import config
    NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
    NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET
except ImportError:
    NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')
    NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')
```

### v10.3 (버그)
```python
# config.py 로드 로직 누락!
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')
```

### v10.3.1 (수정 완료)
```python
try:
    import config
    NAVER_CLIENT_ID = config.NAVER_CLIENT_ID
    NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET
    logger.info("✅ config.py에서 Naver API 키 로드 완료")
except (ImportError, AttributeError) as e:
    NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')
    NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')
    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        logger.info("✅ 환경 변수에서 Naver API 키 로드 완료")
    else:
        logger.warning("⚠️  Naver API 키가 설정되지 않았습니다.")
```

---

## 🔒 보안 주의사항

1. **config.py는 절대 Git에 커밋하지 마세요**
   - 이미 `.gitignore`에 포함되어 있음
   - 실수로 커밋하면 API 키가 노출됨

2. **파일 권한 제한**
   ```bash
   chmod 600 config.py  # 본인만 읽기/쓰기 가능
   ```

3. **API 키 공유 금지**
   - 팀원과 공유 시 안전한 방법 사용 (암호화된 채널)
   - 공개 채널에 절대 올리지 말 것

---

## 📞 문제 해결

### Q1: config.py를 만들었는데도 API 키를 못 찾아요
```bash
# Python 경로 확인
python -c "import sys; print('\n'.join(sys.path))"

# config.py가 현재 디렉토리에 있는지 확인
ls -la config.py

# 크롤러를 config.py와 같은 디렉토리에서 실행
cd ~/naver_blog
python pm_naver_blog_crawler_v10_3_test.py
```

### Q2: 로컬에는 config.py가 있는데 VM에는 없어요
```bash
# 로컬에서 VM으로 복사
scp /Users/kimble/Documents/IT/PMIK-sns-analysis/naver_blog/config.py \
    your_vm_user@your_vm_ip:~/naver_blog/
```

### Q3: API 키를 어디서 발급받나요?
1. https://developers.naver.com/apps/#/myapps 접속
2. 애플리케이션 등록
3. 검색 API 사용 설정
4. Client ID와 Client Secret 복사

---

## ✅ 체크리스트

- [ ] VM에 `config.py` 파일 생성 또는 복사
- [ ] API 키가 올바르게 설정되었는지 확인
- [ ] 파일 권한 설정 (`chmod 600 config.py`)
- [ ] v10.3.1 크롤러 실행 테스트
- [ ] 로그에서 "✅ config.py에서 Naver API 키 로드 완료" 확인
