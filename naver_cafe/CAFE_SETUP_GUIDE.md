# 네이버 카페 크롤러 설정 가이드

## ⚠️ 현재 상황

네이버 카페 크롤링을 시도했으나 다음과 같은 문제가 발생했습니다:

1. **iframe 전환 실패**: `cafe_main` iframe을 찾을 수 없음
2. **검색창 접근 불가**: 카페 검색 기능에 접근할 수 없음
3. **로그인 필요**: 대부분의 네이버 카페는 로그인이 필요함

## 🔍 문제 원인

### 1. 네이버 카페 접근 제한
- 대부분의 네이버 카페는 **회원 가입 및 로그인**이 필수
- 비회원은 게시글 목록조차 볼 수 없는 경우가 많음
- 등급 제한이 있는 게시판은 일정 활동 후에만 접근 가능

### 2. 네이버 보안 정책
- 자동화 도구 감지 시 접근 차단
- CAPTCHA 인증 요구
- IP 기반 속도 제한

### 3. 카페 구조 변경
- 네이버 카페의 HTML 구조가 자주 변경됨
- iframe 구조가 다를 수 있음
- 검색창 위치 및 선택자가 다를 수 있음

## 💡 해결 방법

### 방법 1: 수동 로그인 후 세션 유지 (권장)

```python
# 1. 브라우저를 headless 모드 OFF로 실행
# config.yaml에서 test_mode: enabled: true 설정

# 2. 크롤러 실행 후 수동으로 로그인
# 3. 로그인 완료 후 크롤러가 자동으로 진행
```

### 방법 2: 쿠키 저장 및 재사용

```python
# 1. 첫 실행 시 수동 로그인
# 2. 쿠키를 파일로 저장
# 3. 다음 실행 시 저장된 쿠키 로드
```

### 방법 3: 네이버 API 사용 (제한적)

- 네이버 검색 API를 통해 카페 게시글 검색
- 제한: 상세 내용 접근 불가, 검색 결과만 가능

### 방법 4: 특정 카페 URL 직접 수집

```python
# 카페 게시판 URL을 직접 지정
# 예: https://cafe.naver.com/카페명/게시판번호
```

## 🎯 PMIK 카페 크롤링을 위한 권장 방법

### 단계 1: 실제 PMIK 관련 카페 찾기

1. 네이버에서 "PM International", "FitLine" 등으로 검색
2. 활성화된 카페 찾기
3. 카페 가입 및 등급 확인

### 단계 2: 카페 정보 수집

```yaml
target_cafes:
  - name: "실제카페명"
    cafe_id: "실제카페ID"
    cafe_url: "https://cafe.naver.com/실제카페ID"
    description: "카페 설명"
```

### 단계 3: 로그인 기능 추가

크롤러에 네이버 로그인 기능을 추가해야 합니다:

```python
def naver_login(driver, user_id, user_pw):
    """네이버 로그인"""
    driver.get('https://nid.naver.com/nidlogin.login')
    time.sleep(2)
    
    # ID 입력
    driver.find_element(By.ID, 'id').send_keys(user_id)
    # PW 입력
    driver.find_element(By.ID, 'pw').send_keys(user_pw)
    # 로그인 버튼 클릭
    driver.find_element(By.ID, 'log.login').click()
    time.sleep(3)
```

### 단계 4: 게시판별 직접 접근

```python
# 검색 대신 게시판 URL로 직접 접근
board_url = f"https://cafe.naver.com/{cafe_id}/ArticleList.nhn?search.clubid={club_id}&search.menuid={menu_id}"
```

## 📋 다음 단계

### 즉시 실행 가능한 방법

1. **config.yaml 수정**
   - 실제 존재하고 접근 가능한 카페 URL 입력
   - 테스트 모드 활성화

2. **수동 로그인 테스트**
   - headless 모드 OFF
   - 브라우저 창에서 수동 로그인
   - 로그인 상태에서 크롤링 진행

3. **특정 게시판 타겟팅**
   - 전체 카페 검색 대신
   - 특정 게시판 URL로 직접 접근

### 장기적 개선 방안

1. **로그인 자동화**
   - 환경변수로 계정 정보 관리
   - 쿠키 저장/로드 기능 추가

2. **에러 처리 강화**
   - CAPTCHA 감지 및 대응
   - 접근 제한 시 대체 방법 시도

3. **카페 구조 분석**
   - 각 카페별 HTML 구조 파악
   - 동적 선택자 사용

## 🚨 중요 주의사항

1. **법적 준수**
   - 카페 운영 정책 확인
   - 저작권 및 개인정보 보호
   - 과도한 크롤링 자제

2. **윤리적 사용**
   - 카페 서버에 부담 주지 않기
   - 적절한 지연 시간 설정
   - 로봇 배제 표준 준수

3. **계정 보안**
   - 크롤링 전용 계정 사용 권장
   - 비밀번호 하드코딩 금지
   - 환경변수 또는 암호화된 설정 파일 사용

## 📞 문의

PMIK 관련 카페를 찾으셨다면:
1. 카페 URL 확인
2. 가입 및 등급 요구사항 확인
3. config.yaml 업데이트
4. 로그인 기능 추가 여부 결정

---

**작성일**: 2024-11-18  
**작성자**: PMI Korea 데이터 분석팀
