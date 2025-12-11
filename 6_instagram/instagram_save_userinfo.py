import json
import time
import pickle
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
import os
import logging
import shutil

# .env 파일에서 로그인 정보 불러오기
load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

# JSON 파일 경로
USER_JSON = Path("instagram_user.json")
COOKIE_PATH = Path("instagram_cookies.pkl")
LOG_PATH = Path("instagram.log")

def setup_logging(log_file: str = "instagram.log") -> None:
    """로깅 설정: 파일과 콘솔 모두에 로그 출력"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 (추가 모드로 기존 로그 보존)
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logging.info(f"로깅이 시작되었습니다. 로그 파일: {log_file}")

# 로깅 초기화
setup_logging(str(LOG_PATH))
logging.info("=" * 80)
logging.info("프로그램 시작 - instagram_save_userinfo.py")
logging.info("=" * 80)

# 테스트 모드: 이 변수에 URL을 설정하면 해당 URL만 테스트합니다
# 예: TEST_URL = "https://www.instagram.com/username/"
TEST_URL = None  # None이면 전체 실행, URL이 있으면 테스트 모드

# 비가시 유니코드 제거 함수
def clean_text(text):
    """비가시 유니코드 문자 제거 (<br>, ZWJ, Zero-width space, NBSP, Tab 등)"""
    if not text:
        return ""
    
    # <br> 태그 제거
    text = re.sub(r'<br\s*/?>', ' ', text, flags=re.IGNORECASE)
    
    # Zero-width joiner (ZWJ): U+200D
    text = text.replace('\u200D', '')
    
    # Zero-width space: U+200B
    text = text.replace('\u200B', '')
    
    # Zero-width non-joiner: U+200C
    text = text.replace('\u200C', '')
    
    # Non-breaking space (NBSP): U+00A0
    text = text.replace('\u00A0', ' ')
    
    # Tab 문자 제거
    text = text.replace('\t', ' ')
    
    # 기타 제어 문자 제거 (U+0000 ~ U+001F, U+007F ~ U+009F)
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    return text

# JSON 파일 불러오기 (기존 데이터 보존)
# instagram_user.json의 구조: [{"id": "...", "user_handle": "...", "user_name": "...", "introduce": "...", "linked_page": [...]}, ...]
# instagram_extract_user.py는 id와 user_handle만 추가/수정
# instagram_save_userinfo.py는 user_name, introduce, linked_page만 추가/수정
print("📂 instagram_user.json 파일 로딩 중...")
try:
    if USER_JSON.exists():
        with open(USER_JSON, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        # 기존 데이터를 딕셔너리로 변환 (user_handle을 키로 사용, index 보존)
        existing_by_handle = {item.get("user_handle"): item for item in user_data if item.get("user_handle")}
        print(f"✅ 기존 데이터 {len(user_data)}개 로드됨")
    else:
        user_data = []
        existing_by_handle = {}
        print("📂 기존 데이터 파일이 없습니다. 새로 시작합니다.")
except json.JSONDecodeError:
    print(f"⚠️ {USER_JSON} 파일의 JSON 형식이 올바르지 않습니다. 새로 시작합니다.")
    user_data = []
    existing_by_handle = {}

print(f"✅ {len(user_data)}개의 사용자 핸들 발견\n")

# 크롬 설정 (리눅스 환경 대응)
# Chrome 브라우저 경로 후보 리스트 (우선순위 순)
chrome_path_candidates = []
seen_paths = set()  # 중복 제거용

# 1. 작동하는 경로를 우선 추가 (테스트로 확인됨)
priority_paths = [
    Path("/usr/bin/chromium-browser"),  # 우선 (테스트로 작동 확인됨)
]

for path in priority_paths:
    if path.exists():
        resolved = path.resolve()
        resolved_str = resolved.as_posix()
        # 심볼릭 링크인 경우 실제 파일 확인
        if resolved.exists():
            # 파일이거나 실행 가능한 심볼릭 링크인지 확인
            if (resolved.is_file() or (resolved.is_symlink() and resolved.readlink().exists())) and os.access(resolved, os.X_OK):
                if resolved_str not in seen_paths:
                    chrome_path_candidates.append(resolved)
                    seen_paths.add(resolved_str)
                    logging.info(f"우선 경로로 Chrome 경로 발견: {resolved_str}")

# 2. which 명령어로 PATH에서 찾기
for cmd in ["chromium-browser", "google-chrome", "google-chrome-stable", "chromium", "chrome"]:
    chrome_cmd = shutil.which(cmd)
    if chrome_cmd:
        path_obj = Path(chrome_cmd)
        resolved = path_obj.resolve()
        resolved_str = resolved.as_posix()
        if resolved_str not in seen_paths:
            chrome_path_candidates.append(resolved)
            seen_paths.add(resolved_str)
            logging.info(f"which 명령어로 Chrome 경로 발견: {resolved_str}")

# 3. 일반적인 설치 경로 확인
common_paths = [
    Path("/opt/google/chrome/google-chrome"),
    Path("/opt/google/chrome/chrome"),
    Path("/usr/bin/google-chrome-stable"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
]

for chrome_path in common_paths:
    if chrome_path.exists():
        resolved = chrome_path.resolve()
        if resolved.exists() and resolved.is_file() and os.access(resolved, os.X_OK):
            resolved_str = resolved.as_posix()
            if resolved_str not in seen_paths:
                chrome_path_candidates.append(resolved)
                seen_paths.add(resolved_str)
                logging.info(f"Chrome 브라우저 경로 발견 (실행 가능): {resolved_str}")

if not chrome_path_candidates:
    error_msg = "실행 가능한 Chrome 브라우저를 찾을 수 없습니다."
    logging.error(error_msg)
    print(f"❌ {error_msg}")
    print("💡 해결 방법:")
    print("   1. Chrome 브라우저가 설치되어 있는지 확인하세요")
    print("   2. 다음 명령어로 Chrome을 설치할 수 있습니다:")
    print("      sudo apt-get update && sudo apt-get install -y google-chrome-stable")
    print("   3. 또는 Chromium을 설치할 수 있습니다:")
    print("      sudo apt-get install -y chromium-browser")
    raise RuntimeError(error_msg)

# 경로 시도 순서 로그 출력
logging.info(f"Chrome 경로 시도 순서 (총 {len(chrome_path_candidates)}개):")
for i, path in enumerate(chrome_path_candidates[:5], 1):  # 처음 5개만 출력
    logging.info(f"  {i}. {path.as_posix()}")

# 각 경로를 시도하여 실제로 작동하는지 확인
last_error = None
driver = None
for chrome_path in chrome_path_candidates:
    chrome_binary_location = chrome_path.as_posix()
    logging.info(f"Chrome 경로 시도: {chrome_binary_location}")
    
    options = Options()
    options.binary_location = chrome_binary_location
    
    # Headless 모드 설정 (리눅스 환경 대응)
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        logging.info(f"Chrome WebDriver 초기화 성공: {chrome_binary_location}")
        break
    except Exception as e:
        last_error = e
        logging.warning(f"Chrome 경로 실패 ({chrome_binary_location}): {str(e)}")
        continue

# 모든 경로가 실패한 경우
if driver is None:
    error_msg = f"모든 Chrome 경로 시도 실패. 마지막 오류: {str(last_error)}"
    logging.error(error_msg, exc_info=True)
    print(f"❌ {error_msg}")
    print("💡 해결 방법:")
    print("   1. Chrome 브라우저가 올바르게 설치되어 있는지 확인하세요")
    print("   2. 다음 명령어로 Chrome을 설치할 수 있습니다:")
    print("      sudo apt-get update && sudo apt-get install -y google-chrome-stable")
    print("   3. 또는 Chromium을 설치할 수 있습니다:")
    print("      sudo apt-get install -y chromium-browser")
    print("   4. 설치 후 다음 명령어로 경로를 확인하세요:")
    print("      which google-chrome")
    raise RuntimeError(error_msg) from last_error

# 쿠키 로드 시도
logged_in = False
if COOKIE_PATH.exists():
    try:
        print("🍪 저장된 쿠키 로드 중...")
        driver.get("https://www.instagram.com")
        time.sleep(2)
        
        with open(COOKIE_PATH, "rb") as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"⚠️ 쿠키 추가 실패: {e}")
                continue
        
        # 쿠키 로드 후 페이지 새로고침하여 로그인 상태 확인
        driver.refresh()
        time.sleep(3)
        
        # 로그인 상태 확인 (로그인 페이지가 아니면 로그인 성공)
        current_url = driver.current_url
        if "accounts/login" not in current_url:
            print("✅ 쿠키로 로그인 성공!")
            logged_in = True
        else:
            print("⚠️ 쿠키가 만료되었습니다. 새로 로그인합니다.")
    except Exception as e:
        print(f"⚠️ 쿠키 로드 실패: {e}")
        print("⚠️ 새로 로그인합니다.")

# 쿠키가 없거나 만료된 경우 로그인
if not logged_in:
    print("🔐 인스타그램 로그인 중...")
    driver.get("https://www.instagram.com")
    time.sleep(3)

    try:
        # 로그인 과정
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("✅ 로그인 버튼 클릭")
        
        # 로그인 완료 대기
        time.sleep(5)
        
        # 로그인 성공 확인
        current_url = driver.current_url
        if "accounts/login" in current_url:
            print("⚠️ 로그인 실패로 보입니다. 계속 진행합니다...")
        else:
            print("✅ 로그인 성공!")
        
        # 팝업 닫기 시도
        try:
            not_now_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '나중에 하기') or contains(text(), '지금은 안함') or contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            print("✅ 팝업 닫기 성공")
            time.sleep(2)
        except:
            print("ℹ️ 팝업 없음 또는 이미 닫힘")
        
        # 알림 팝업 닫기
        try:
            not_now_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '나중에 하기') or contains(text(), '지금은 안함') or contains(text(), 'Not Now')]"))
            )
            not_now_button.click()
            print("✅ 알림 팝업 닫기 성공")
            time.sleep(2)
        except:
            print("ℹ️ 알림 팝업 없음")
        
        # 쿠키 저장
        try:
            cookies = driver.get_cookies()
            with open(COOKIE_PATH, "wb") as f:
                pickle.dump(cookies, f)
            print("✅ 쿠키 저장 완료!")
        except Exception as e:
            print(f"⚠️ 쿠키 저장 실패: {e}")
            
    except Exception as e:
        print(f"⚠️ 로그인 중 오류 발생: {e}")
        print("⚠️ 로그인 없이 진행합니다...")

# 테스트 모드 확인
try:
    if TEST_URL:
        # 테스트 모드: 단일 URL 테스트
        print("🧪 테스트 모드: 단일 URL 테스트\n")
        print(f"📋 테스트 URL: {TEST_URL}\n")
        
        # URL에서 handle 추출
        if "/" in TEST_URL:
            handle = TEST_URL.rstrip("/").split("/")[-1]
        else:
            handle = TEST_URL
        
        user_url = TEST_URL if TEST_URL.startswith("http") else f"https://www.instagram.com/{TEST_URL}/"
        
        print("="*60)
        print(f"👤 테스트 사용자 처리 중")
        print(f"   Handle: {handle}")
        print(f"   URL: {user_url}")
        print("="*60)
        
        # 페이지 접속
        print(f"📱 페이지 접속 중...")
        driver.get(user_url)
        
        # 페이지 로드 대기
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(f"✅ 페이지 로드 완료")
        except TimeoutException:
            print(f"⚠️ 페이지 로드 타임아웃, 계속 진행...")
        
        # 추가 대기 (동적 콘텐츠 로드를 위해)
        time.sleep(3)
        
        # 사용자 정보 수집
        user_name = None
        introduce = None
        linked_page = []
        
        try:
            # 1. user_name 수집
            try:
                # 여러 셀렉터 시도
                user_name_selectors = [
                    "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.xyejjpt.x15dsfln.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.xpm28yp.x8viiok.x1o7cslx",
                    "span[class*='x1lliihq'][class*='x1plvlek'][class*='xryxfnj']",
                ]
                
                for selector in user_name_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        user_name = element.text.strip()
                        if user_name:
                            user_name = clean_text(user_name)
                            print(f"   ✅ user_name 수집: {user_name[:50]}...")
                            break
                    except NoSuchElementException:
                        continue
                
                if not user_name:
                    print(f"   ⚠️ user_name을 찾을 수 없습니다.")
            except Exception as e:
                print(f"   ⚠️ user_name 수집 중 오류: {e}")
            
            # 2. introduce 수집
            try:
                # 여러 셀렉터 시도
                introduce_selectors = [
                    "span._ap3a._aaco._aacu._aacx._aad7._aade",
                    "span[class*='_ap3a'][class*='_aaco'][class*='_aacu']",
                ]
                
                introduce_element = None
                for selector in introduce_selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and len(text) > 0:
                                introduce = clean_text(text)
                                introduce_element = element  # 요소 저장 (나중에 "더 보기" 클릭용)
                                print(f"   ✅ introduce 수집: {introduce[:100]}...")
                                break
                        if introduce:
                            break
                    except NoSuchElementException:
                        continue
                
                # "더 보기" 텍스트가 있는지 확인
                if introduce and "더 보기" in introduce:
                    print(f"   🔍 '더 보기' 텍스트 발견! 전체 내용 가져오기 시도...")
                    try:
                        # introduce 요소의 부모나 형제 요소에서 "더 보기" 버튼 찾기
                        # <div role="button"> 요소 찾기
                        more_button = None
                        
                        # 방법 1: introduce 요소의 부모 요소에서 찾기
                        try:
                            parent = introduce_element.find_element(By.XPATH, "./..")
                            more_buttons = parent.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
                            for btn in more_buttons:
                                btn_text = btn.text.strip()
                                if "더 보기" in btn_text or "more" in btn_text.lower():
                                    more_button = btn
                                    print(f"   ✅ '더 보기' 버튼 발견 (부모 요소)")
                                    break
                        except:
                            pass
                        
                        # 방법 2: 전체 페이지에서 "더 보기" 텍스트가 있는 div[role="button"] 찾기
                        if not more_button:
                            try:
                                all_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
                                for btn in all_buttons:
                                    btn_text = btn.text.strip()
                                    if "더 보기" in btn_text or "more" in btn_text.lower():
                                        # introduce 요소와 가까운지 확인
                                        try:
                                            # introduce 요소와 같은 부모나 가까운 위치에 있는지 확인
                                            introduce_parent = introduce_element.find_element(By.XPATH, "./ancestor::*[position()<=3]")
                                            btn_parent = btn.find_element(By.XPATH, "./ancestor::*[position()<=3]")
                                            if introduce_parent == btn_parent or btn in introduce_parent.find_elements(By.CSS_SELECTOR, "*"):
                                                more_button = btn
                                                print(f"   ✅ '더 보기' 버튼 발견 (전체 검색)")
                                                break
                                        except:
                                            # 가까운 위치 확인 실패해도 일단 사용
                                            more_button = btn
                                            print(f"   ✅ '더 보기' 버튼 발견 (전체 검색, 위치 확인 실패)")
                                            break
                            except Exception as e:
                                print(f"   ⚠️ '더 보기' 버튼 검색 중 오류: {e}")
                        
                        # "더 보기" 버튼 클릭
                        if more_button:
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_button)
                                time.sleep(0.5)
                                driver.execute_script("arguments[0].click();", more_button)
                                print(f"   ✅ '더 보기' 버튼 클릭 완료")
                                time.sleep(2)  # 내용 로드 대기
                                
                                # 클릭 후 다시 introduce 수집
                                new_introduce = None
                                for selector in introduce_selectors:
                                    try:
                                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                        for element in elements:
                                            text = element.text.strip()
                                            if text and len(text) > 0:
                                                new_introduce = clean_text(text)
                                                if new_introduce and len(new_introduce) > len(introduce):
                                                    introduce = new_introduce
                                                    print(f"   ✅ 전체 introduce 수집 완료: {len(introduce)}자")
                                                    break
                                        if introduce and len(introduce) > 0:
                                            break
                                    except NoSuchElementException:
                                        continue
                                
                                if not new_introduce or len(new_introduce) <= len(introduce):
                                    print(f"   ⚠️ '더 보기' 클릭 후에도 내용이 변경되지 않았습니다.")
                            except Exception as e:
                                print(f"   ⚠️ '더 보기' 버튼 클릭 실패: {e}")
                        else:
                            print(f"   ⚠️ '더 보기' 버튼을 찾을 수 없습니다.")
                    except Exception as e:
                        print(f"   ⚠️ '더 보기' 처리 중 오류: {e}")
                        import traceback
                        traceback.print_exc()
                
                if not introduce:
                    print(f"   ⚠️ introduce를 찾을 수 없습니다.")
            except Exception as e:
                print(f"   ⚠️ introduce 수집 중 오류: {e}")
                import traceback
                traceback.print_exc()
            
            # 3. linked_page 수집
            try:
                # 1단계: 첫 번째 버튼 찾기 및 클릭 (모달 열기)
                # <div class="html-div xdj266r..."> 안에 있는 <button class=" _aswp _aswq _asws _aswu _asx0 _asx2">
                first_button_selectors = [
                    'div[class*="xdj266r"][class*="x14z9mp"][class*="xat24cr"] button[class*="_aswp"][class*="_aswq"][class*="_asws"][class*="_aswu"][class*="_asx0"][class*="_asx2"]',
                    'div[class*="xdj266r"] button[class*="_aswp"][class*="_aswq"][class*="_asws"]',
                    'button[class*="_aswp"][class*="_aswq"][class*="_asws"][class*="_aswu"][class*="_asx0"][class*="_asx2"]',
                ]
                
                first_button_clicked = False
                for selector in first_button_selectors:
                    try:
                        button = driver.find_element(By.CSS_SELECTOR, selector)
                        if button.is_displayed() and button.is_enabled():
                            driver.execute_script("arguments[0].click();", button)
                            print(f"   ✅ 첫 번째 linked_page 버튼 클릭 (모달 열기)")
                            first_button_clicked = True
                            time.sleep(2)  # 모달 생성 대기
                            break
                    except NoSuchElementException:
                        continue
                
                if first_button_clicked:
                    # 2단계: 생성된 모달 div에서 링크 찾기
                    # <div class="x1n2onr6 xzkaem6">가 생성됨
                    # 그 안의 <div x78zum5 xdt5ytf x1crbq5u xvrdyt3 x179zr98><div> 안의 <button> 안의 <a> 태그
                    try:
                        # 생성된 모달 div 대기
                        modal_selectors = [
                            'div[class*="x1n2onr6"][class*="xzkaem6"]',
                            'div[class*="x1n2onr6"]',
                        ]
                        
                        modal_div = None
                        for selector in modal_selectors:
                            try:
                                modal_div = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                )
                                print(f"   ✅ 모달 div 생성 확인")
                                break
                            except TimeoutException:
                                continue
                        
                        if modal_div:
                            # 모달 내에서 링크 찾기
                            link_container_selectors = [
                                'div[class*="x78zum5"][class*="xdt5ytf"][class*="x1crbq5u"] div button[class*="xjbqb8w"][class*="x1qhh985"] a',
                                'div[class*="x78zum5"][class*="xdt5ytf"] button[class*="xjbqb8w"] a',
                                'div[class*="x78zum5"] button[class*="xjbqb8w"] a',
                            ]
                            
                            for selector in link_container_selectors:
                                try:
                                    links = modal_div.find_elements(By.CSS_SELECTOR, selector)
                                    for link in links:
                                        href = link.get_attribute("href")
                                        if href and href not in linked_page:
                                            linked_page.append(href)
                                            print(f"   ✅ linked_page 추가: {href[:80]}...")
                                    if linked_page:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            if not linked_page:
                                print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다.")
                        else:
                            print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다.")
                    except Exception as e:
                        print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다. (오류: {e})")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다.")
            except Exception as e:
                print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다. (오류: {e})")
                import traceback
                traceback.print_exc()
            
            # linked_page가 비어있으면 null로 설정
            if not linked_page:
                linked_page = None
            
            # 4. followers 수집 (팔로워 페이지 접근) - 테스트 모드
            followers_count = None
            try:
                followers_url = f"https://www.instagram.com/{handle}/followers/"
                print(f"   👥 팔로워 페이지 접근 중: {followers_url}")
                driver.get(followers_url)
                time.sleep(3)
                
                # 디버깅: 모든 <a href="/~~/followers/"> 요소 찾기 및 출력
                print(f"\n   🔍 디버깅: <a href*='/followers/'> 요소 검색 중...")
                try:
                    # 모든 followers 링크 찾기
                    followers_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/followers/"]')
                    print(f"   📊 발견된 followers 링크 개수: {len(followers_links)}개")
                    
                    for idx, link in enumerate(followers_links[:10], 1):  # 처음 10개만 출력
                        try:
                            href = link.get_attribute("href")
                            text = link.text.strip()
                            inner_html = link.get_attribute("innerHTML")
                            
                            print(f"   [{idx}] href: {href}")
                            print(f"       text: {text}")
                            if inner_html and len(inner_html) < 200:
                                print(f"       innerHTML: {inner_html}")
                            
                            # span 요소 찾기
                            try:
                                spans = link.find_elements(By.CSS_SELECTOR, "span")
                                if spans:
                                    print(f"       span 개수: {len(spans)}개")
                                    for span_idx, span in enumerate(spans[:3], 1):  # 처음 3개만
                                        span_text = span.text.strip()
                                        if span_text:
                                            print(f"         span[{span_idx}]: {span_text}")
                            except:
                                pass
                            print()
                        except Exception as e:
                            print(f"   [{idx}] 요소 처리 중 오류: {e}")
                except Exception as e:
                    print(f"   ⚠️ 디버깅 중 오류: {e}")
                
                # JavaScript로 더 자세한 디버깅
                print(f"   🔍 JavaScript 디버깅 실행 중...")
                debug_info = driver.execute_script("""
                    var links = document.querySelectorAll('a[href*="/followers/"]');
                    var results = [];
                    for (var i = 0; i < Math.min(links.length, 10); i++) {
                        var link = links[i];
                        var href = link.getAttribute('href');
                        var text = link.textContent || link.innerText;
                        var innerHTML = link.innerHTML;
                        
                        // span 요소 찾기
                        var spans = link.querySelectorAll('span');
                        var spanTexts = [];
                        for (var j = 0; j < spans.length; j++) {
                            var spanText = spans[j].textContent || spans[j].innerText;
                            if (spanText && spanText.trim()) {
                                spanTexts.push(spanText.trim());
                            }
                        }
                        
                        results.push({
                            href: href,
                            text: text.trim(),
                            innerHTML: innerHTML.substring(0, 200),
                            spanTexts: spanTexts.slice(0, 5)
                        });
                    }
                    return results;
                """)
                
                print(f"   📊 JavaScript로 발견된 요소: {len(debug_info)}개")
                for idx, info in enumerate(debug_info, 1):
                    print(f"   [{idx}] href: {info.get('href', 'N/A')}")
                    print(f"       text: {info.get('text', 'N/A')}")
                    if info.get('spanTexts'):
                        print(f"       span texts: {info.get('spanTexts')}")
                    print()
                
                # 팔로워 수 추출
                print(f"   🔍 팔로워 수 추출 시도 중...")
                try:
                    followers_text = driver.execute_script("""
                        var links = document.querySelectorAll('a[href*="/followers/"]');
                        console.log('총 링크 개수:', links.length);
                        for (var i = 0; i < links.length; i++) {
                            var link = links[i];
                            var text = link.textContent || link.innerText;
                            console.log('링크[' + i + '] text:', text);
                            if (text && text.includes('팔로워')) {
                                var match = text.match(/[\\d,]+/);
                                if (match) {
                                    console.log('매칭된 숫자:', match[0]);
                                    return match[0].replace(/,/g, '');
                                }
                            }
                        }
                        return null;
                    """)
                    
                    print(f"   🔍 JavaScript 추출 결과: {followers_text}")
                    
                    if followers_text:
                        try:
                            followers_count = int(followers_text)
                            print(f"   ✅ followers 수집: {followers_count:,}명")
                        except ValueError:
                            print(f"   ⚠️ 숫자 변환 실패: {followers_text}")
                except Exception as e:
                    print(f"   ⚠️ followers 추출 실패: {e}")
                
                # 대체 방법
                if followers_count is None:
                    print(f"   🔍 대체 방법: 페이지 소스에서 검색 중...")
                    try:
                        page_source = driver.page_source
                        patterns = [
                            r'팔로워\s*([\d,]+)',
                            r'followers["\']?\s*:?\s*([\d,]+)',
                            r'([\d,]+)\s*팔로워',
                        ]
                        for pattern in patterns:
                            matches = re.findall(pattern, page_source, re.IGNORECASE)
                            print(f"   🔍 패턴 '{pattern}' 매칭 결과: {len(matches)}개")
                            if matches:
                                for match in matches[:5]:  # 처음 5개만 출력
                                    print(f"      매칭: {match}")
                                try:
                                    numbers = [int(m.replace(',', '')) for m in matches]
                                    if numbers:
                                        followers_count = max(numbers)
                                        print(f"   ✅ followers 수집 (대체 방법): {followers_count:,}명")
                                        break
                                except ValueError:
                                    continue
                    except Exception as e:
                        print(f"   ⚠️ followers 수집 실패 (대체 방법): {e}")
                
                if followers_count is None:
                    print(f"   ⚠️ followers를 찾을 수 없습니다.")
                    print(f"   💡 팔로워 페이지가 제대로 로드되었는지 확인하세요.")
            except Exception as e:
                print(f"   ⚠️ followers 수집 중 오류: {e}")
                import traceback
                traceback.print_exc()
            
            # 테스트 결과 출력
            print("\n" + "="*60)
            print("📊 테스트 결과:")
            print(f"   Handle: {handle}")
            print(f"   user_name: {user_name if user_name else '❌ 수집 실패'}")
            print(f"   introduce: {introduce[:100] + '...' if introduce and len(introduce) > 100 else (introduce if introduce else '❌ 수집 실패')}")
            print(f"   linked_page: {linked_page if linked_page else '❌ 수집 실패'}")
            print(f"   followers: {followers_count:,}명" if followers_count is not None else "   followers: ❌ 수집 실패")
            print("="*60)
            
        except Exception as e:
            print(f"   ❌ 정보 수집 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()

    else:
        # 일반 모드: 전체 실행
        try:
            # 각 사용자 핸들에 대해 반복문으로 처리
            for idx, user_item in enumerate(user_data, 1):
                handle = user_item.get("user_handle")
                
                if not handle:
                    print(f"[{idx}/{len(user_data)}] ⚠️ user_handle이 없어 스킵합니다.")
                    continue
                
                # 이미 user_name이나 introduce가 있으면 스킵 (기존 데이터는 재수집하지 않음)
                # 단, followers는 항상 업데이트 (변동 가능)
                existing_user_name = user_item.get("user_name")
                existing_introduce = user_item.get("introduce")
                existing_followers = user_item.get("followers")
                
                # user_name과 introduce가 모두 있고, introduce에 "더 보기"가 없으면 스킵 (followers는 별도로 처리)
                # introduce에 "더 보기"가 있으면 전체 내용을 가져오기 위해 재수집
                should_skip_introduce = existing_user_name and existing_introduce and ("더 보기" not in existing_introduce if existing_introduce else True)
                
                if should_skip_introduce:
                    # followers만 업데이트하기 위해 팔로워 페이지 접근
                    print(f"\n[{idx}/{len(user_data)}] 👥 팔로워 수만 업데이트: {handle}")
                    if existing_followers is not None:
                        print(f"   - 기존 followers: {existing_followers:,}명")
                    
                    try:
                        followers_url = f"https://www.instagram.com/{handle}/followers/"
                        print(f"   📱 팔로워 페이지 접근 중: {followers_url}")
                        driver.get(followers_url)
                        time.sleep(3)
                        
                        # 디버깅: 모든 <a href="/~~/followers/"> 요소 찾기 및 출력
                        print(f"\n   🔍 디버깅: <a href*='/followers/'> 요소 검색 중...")
                        try:
                            # 모든 followers 링크 찾기
                            followers_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/followers/"]')
                            print(f"   📊 발견된 followers 링크 개수: {len(followers_links)}개")
                            
                            for idx, link in enumerate(followers_links[:10], 1):  # 처음 10개만 출력
                                try:
                                    href = link.get_attribute("href")
                                    text = link.text.strip()
                                    inner_html = link.get_attribute("innerHTML")
                                    
                                    print(f"   [{idx}] href: {href}")
                                    print(f"       text: {text}")
                                    if inner_html and len(inner_html) < 200:
                                        print(f"       innerHTML: {inner_html}")
                                    
                                    # span 요소 찾기
                                    try:
                                        spans = link.find_elements(By.CSS_SELECTOR, "span")
                                        if spans:
                                            print(f"       span 개수: {len(spans)}개")
                                            for span_idx, span in enumerate(spans[:3], 1):  # 처음 3개만
                                                span_text = span.text.strip()
                                                if span_text:
                                                    print(f"         span[{span_idx}]: {span_text}")
                                    except:
                                        pass
                                    print()
                                except Exception as e:
                                    print(f"   [{idx}] 요소 처리 중 오류: {e}")
                        except Exception as e:
                            print(f"   ⚠️ 디버깅 중 오류: {e}")
                        
                        # JavaScript로 더 자세한 디버깅
                        print(f"   🔍 JavaScript 디버깅 실행 중...")
                        debug_info = driver.execute_script("""
                            var links = document.querySelectorAll('a[href*="/followers/"]');
                            var results = [];
                            for (var i = 0; i < Math.min(links.length, 10); i++) {
                                var link = links[i];
                                var href = link.getAttribute('href');
                                var text = link.textContent || link.innerText;
                                var innerHTML = link.innerHTML;
                                
                                // span 요소 찾기
                                var spans = link.querySelectorAll('span');
                                var spanTexts = [];
                                for (var j = 0; j < spans.length; j++) {
                                    var spanText = spans[j].textContent || spans[j].innerText;
                                    if (spanText && spanText.trim()) {
                                        spanTexts.push(spanText.trim());
                                    }
                                }
                                
                                results.push({
                                    href: href,
                                    text: text.trim(),
                                    innerHTML: innerHTML.substring(0, 200),
                                    spanTexts: spanTexts.slice(0, 5)
                                });
                            }
                            return results;
                        """)
                        
                        print(f"   📊 JavaScript로 발견된 요소: {len(debug_info)}개")
                        for idx, info in enumerate(debug_info, 1):
                            print(f"   [{idx}] href: {info.get('href', 'N/A')}")
                            print(f"       text: {info.get('text', 'N/A')}")
                            if info.get('spanTexts'):
                                print(f"       span texts: {info.get('spanTexts')}")
                            print()
                        
                        # 팔로워 수 추출
                        # 디버깅: 모든 <a href="/~~/followers/"> 요소 찾기 및 출력
                        print(f"\n   🔍 디버깅: <a href*='/followers/'> 요소 검색 중...")
                        try:
                            # 모든 followers 링크 찾기
                            followers_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/followers/"]')
                            print(f"   📊 발견된 followers 링크 개수: {len(followers_links)}개")
                            
                            for idx, link in enumerate(followers_links[:10], 1):  # 처음 10개만 출력
                                try:
                                    href = link.get_attribute("href")
                                    text = link.text.strip()
                                    inner_html = link.get_attribute("innerHTML")
                                    
                                    print(f"   [{idx}] href: {href}")
                                    print(f"       text: {text}")
                                    if inner_html and len(inner_html) < 200:
                                        print(f"       innerHTML: {inner_html}")
                                    
                                    # span 요소 찾기
                                    try:
                                        spans = link.find_elements(By.CSS_SELECTOR, "span")
                                        if spans:
                                            print(f"       span 개수: {len(spans)}개")
                                            for span_idx, span in enumerate(spans[:3], 1):  # 처음 3개만
                                                span_text = span.text.strip()
                                                if span_text:
                                                    print(f"         span[{span_idx}]: {span_text}")
                                    except:
                                        pass
                                    print()
                                except Exception as e:
                                    print(f"   [{idx}] 요소 처리 중 오류: {e}")
                        except Exception as e:
                            print(f"   ⚠️ 디버깅 중 오류: {e}")
                        
                        # JavaScript로 더 자세한 디버깅
                        print(f"   🔍 JavaScript 디버깅 실행 중...")
                        debug_info = driver.execute_script("""
                            var links = document.querySelectorAll('a[href*="/followers/"]');
                            var results = [];
                            for (var i = 0; i < Math.min(links.length, 10); i++) {
                                var link = links[i];
                                var href = link.getAttribute('href');
                                var text = link.textContent || link.innerText;
                                var innerHTML = link.innerHTML;
                                
                                // span 요소 찾기
                                var spans = link.querySelectorAll('span');
                                var spanTexts = [];
                                for (var j = 0; j < spans.length; j++) {
                                    var spanText = spans[j].textContent || spans[j].innerText;
                                    if (spanText && spanText.trim()) {
                                        spanTexts.push(spanText.trim());
                                    }
                                }
                                
                                results.push({
                                    href: href,
                                    text: text.trim(),
                                    innerHTML: innerHTML.substring(0, 200),
                                    spanTexts: spanTexts.slice(0, 5)
                                });
                            }
                            return results;
                        """)
                        
                        print(f"   📊 JavaScript로 발견된 요소: {len(debug_info)}개")
                        for idx, info in enumerate(debug_info, 1):
                            print(f"   [{idx}] href: {info.get('href', 'N/A')}")
                            print(f"       text: {info.get('text', 'N/A')}")
                            if info.get('spanTexts'):
                                print(f"       span texts: {info.get('spanTexts')}")
                            print()
                        
                        followers_count = None
                        print(f"   🔍 팔로워 수 추출 시도 중...")
                        try:
                            followers_text = driver.execute_script("""
                                var links = document.querySelectorAll('a[href*="/followers/"]');
                                console.log('총 링크 개수:', links.length);
                                for (var i = 0; i < links.length; i++) {
                                    var link = links[i];
                                    var text = link.textContent || link.innerText;
                                    console.log('링크[' + i + '] text:', text);
                                    if (text && text.includes('팔로워')) {
                                        var match = text.match(/[\\d,]+/);
                                        if (match) {
                                            console.log('매칭된 숫자:', match[0]);
                                            return match[0].replace(/,/g, '');
                                        }
                                    }
                                }
                                return null;
                            """)
                            
                            print(f"   🔍 JavaScript 추출 결과: {followers_text}")
                            
                            if followers_text:
                                try:
                                    followers_count = int(followers_text)
                                    print(f"   ✅ followers 수집: {followers_count:,}명")
                                except ValueError:
                                    print(f"   ⚠️ 숫자 변환 실패: {followers_text}")
                        except Exception as e:
                            print(f"   ⚠️ followers 추출 실패: {e}")
                        
                        # 대체 방법
                        if followers_count is None:
                            print(f"   🔍 대체 방법: 페이지 소스에서 검색 중...")
                            try:
                                page_source = driver.page_source
                                import re
                                patterns = [
                                    r'팔로워\s*([\d,]+)',
                                    r'followers["\']?\s*:?\s*([\d,]+)',
                                    r'([\d,]+)\s*팔로워',
                                ]
                                for pattern in patterns:
                                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                                    print(f"   🔍 패턴 '{pattern}' 매칭 결과: {len(matches)}개")
                                    if matches:
                                        for match in matches[:5]:  # 처음 5개만 출력
                                            print(f"      매칭: {match}")
                                        try:
                                            numbers = [int(m.replace(',', '')) for m in matches]
                                            if numbers:
                                                followers_count = max(numbers)
                                                print(f"   ✅ followers 수집 (대체 방법): {followers_count:,}명")
                                                break
                                        except ValueError:
                                            continue
                            except Exception as e:
                                print(f"   ⚠️ 대체 방법 실패: {e}")
                        
                        if followers_count is None:
                            print(f"   ⚠️ followers를 찾을 수 없습니다.")
                            print(f"   💡 팔로워 페이지가 제대로 로드되었는지 확인하세요.")
                        
                        # followers 업데이트
                        if followers_count is not None:
                            if existing_followers != followers_count:
                                user_item["followers"] = followers_count
                                print(f"   ✅ followers 업데이트: {existing_followers:,} → {followers_count:,}명")
                                
                                # JSON 파일 저장
                                try:
                                    with open(USER_JSON, "w", encoding="utf-8") as f:
                                        json.dump(user_data, f, ensure_ascii=False, indent=2)
                                    print(f"   💾 JSON 파일 저장 완료")
                                except Exception as e:
                                    print(f"   ⚠️ JSON 파일 저장 실패: {e}")
                            else:
                                print(f"   ℹ️ followers 변경 없음: {followers_count:,}명")
                        else:
                            print(f"   ⚠️ followers를 찾을 수 없습니다.")
                    except Exception as e:
                        print(f"   ⚠️ 팔로워 페이지 접근 실패: {e}")
                    
                    # 요청 간 딜레이
                    time.sleep(2)
                    continue
                
                # URL 생성
                user_url = f"https://www.instagram.com/{handle}/"
                
                print("\n" + "="*60)
                print(f"👤 사용자 #{idx}/{len(user_data)} 처리 중 (새 데이터 수집)")
                print(f"   Handle: {handle}")
                print(f"   URL: {user_url}")
                print("="*60)
                
                # 페이지 접속
                print(f"📱 페이지 접속 중...")
                driver.get(user_url)
                
                # 페이지 로드 대기
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    print(f"✅ 페이지 로드 완료")
                except TimeoutException:
                    print(f"⚠️ 페이지 로드 타임아웃, 계속 진행...")
                
                # 추가 대기 (동적 콘텐츠 로드를 위해)
                time.sleep(3)
                
                # 사용자 정보 수집
                user_name = None
                introduce = None
                linked_page = []
                
                try:
                    # 1. user_name 수집
                    try:
                        # 여러 셀렉터 시도
                        user_name_selectors = [
                            "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.xyejjpt.x15dsfln.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.xpm28yp.x8viiok.x1o7cslx",
                            "span[class*='x1lliihq'][class*='x1plvlek'][class*='xryxfnj']",
                        ]
                        
                        for selector in user_name_selectors:
                            try:
                                element = driver.find_element(By.CSS_SELECTOR, selector)
                                user_name = element.text.strip()
                                if user_name:
                                    user_name = clean_text(user_name)
                                    print(f"   ✅ user_name 수집: {user_name[:50]}...")
                                    break
                            except NoSuchElementException:
                                continue
                        
                        if not user_name:
                            print(f"   ⚠️ user_name을 찾을 수 없습니다.")
                    except Exception as e:
                        print(f"   ⚠️ user_name 수집 중 오류: {e}")
                    
                    # 2. introduce 수집
                    try:
                        # 여러 셀렉터 시도
                        introduce_selectors = [
                            "span._ap3a._aaco._aacu._aacx._aad7._aade",
                            "span[class*='_ap3a'][class*='_aaco'][class*='_aacu']",
                        ]
                        
                        introduce_element = None
                        for selector in introduce_selectors:
                            try:
                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                for element in elements:
                                    text = element.text.strip()
                                    if text and len(text) > 0:
                                        introduce = clean_text(text)
                                        introduce_element = element  # 요소 저장 (나중에 "더 보기" 클릭용)
                                        print(f"   ✅ introduce 수집: {introduce[:100]}...")
                                        break
                                if introduce:
                                    break
                            except NoSuchElementException:
                                continue
                        
                        # "더 보기" 텍스트가 있는지 확인
                        if introduce and "더 보기" in introduce:
                            print(f"   🔍 '더 보기' 텍스트 발견! 전체 내용 가져오기 시도...")
                            try:
                                # introduce 요소의 부모나 형제 요소에서 "더 보기" 버튼 찾기
                                # <div role="button"> 요소 찾기
                                more_button = None
                                
                                # 방법 1: introduce 요소의 부모 요소에서 찾기
                                try:
                                    parent = introduce_element.find_element(By.XPATH, "./..")
                                    more_buttons = parent.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
                                    for btn in more_buttons:
                                        btn_text = btn.text.strip()
                                        if "더 보기" in btn_text or "more" in btn_text.lower():
                                            more_button = btn
                                            print(f"   ✅ '더 보기' 버튼 발견 (부모 요소)")
                                            break
                                except:
                                    pass
                                
                                # 방법 2: 전체 페이지에서 "더 보기" 텍스트가 있는 div[role="button"] 찾기
                                if not more_button:
                                    try:
                                        all_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
                                        for btn in all_buttons:
                                            btn_text = btn.text.strip()
                                            if "더 보기" in btn_text or "more" in btn_text.lower():
                                                # introduce 요소와 가까운지 확인
                                                try:
                                                    # introduce 요소와 같은 부모나 가까운 위치에 있는지 확인
                                                    introduce_parent = introduce_element.find_element(By.XPATH, "./ancestor::*[position()<=3]")
                                                    btn_parent = btn.find_element(By.XPATH, "./ancestor::*[position()<=3]")
                                                    if introduce_parent == btn_parent or btn in introduce_parent.find_elements(By.CSS_SELECTOR, "*"):
                                                        more_button = btn
                                                        print(f"   ✅ '더 보기' 버튼 발견 (전체 검색)")
                                                        break
                                                except:
                                                    # 가까운 위치 확인 실패해도 일단 사용
                                                    more_button = btn
                                                    print(f"   ✅ '더 보기' 버튼 발견 (전체 검색, 위치 확인 실패)")
                                                    break
                                    except Exception as e:
                                        print(f"   ⚠️ '더 보기' 버튼 검색 중 오류: {e}")
                                
                                # "더 보기" 버튼 클릭
                                if more_button:
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more_button)
                                        time.sleep(0.5)
                                        driver.execute_script("arguments[0].click();", more_button)
                                        print(f"   ✅ '더 보기' 버튼 클릭 완료")
                                        time.sleep(2)  # 내용 로드 대기
                                        
                                        # 클릭 후 다시 introduce 수집
                                        new_introduce = None
                                        for selector in introduce_selectors:
                                            try:
                                                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                                for element in elements:
                                                    text = element.text.strip()
                                                    if text and len(text) > 0:
                                                        new_introduce = clean_text(text)
                                                        if new_introduce and len(new_introduce) > len(introduce):
                                                            introduce = new_introduce
                                                            print(f"   ✅ 전체 introduce 수집 완료: {len(introduce)}자")
                                                            break
                                                if introduce and len(introduce) > 0:
                                                    break
                                            except NoSuchElementException:
                                                continue
                                        
                                        if not new_introduce or len(new_introduce) <= len(introduce):
                                            print(f"   ⚠️ '더 보기' 클릭 후에도 내용이 변경되지 않았습니다.")
                                    except Exception as e:
                                        print(f"   ⚠️ '더 보기' 버튼 클릭 실패: {e}")
                                else:
                                    print(f"   ⚠️ '더 보기' 버튼을 찾을 수 없습니다.")
                            except Exception as e:
                                print(f"   ⚠️ '더 보기' 처리 중 오류: {e}")
                                import traceback
                                traceback.print_exc()
                        
                        if not introduce:
                            print(f"   ⚠️ introduce를 찾을 수 없습니다.")
                    except Exception as e:
                        print(f"   ⚠️ introduce 수집 중 오류: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # 3. linked_page 수집
                    try:
                        # 1단계: 첫 번째 버튼 찾기 및 클릭 (모달 열기)
                        # <div class="html-div xdj266r..."> 안에 있는 <button class=" _aswp _aswq _asws _aswu _asx0 _asx2">
                        first_button_selectors = [
                            'div[class*="xdj266r"][class*="x14z9mp"][class*="xat24cr"] button[class*="_aswp"][class*="_aswq"][class*="_asws"][class*="_aswu"][class*="_asx0"][class*="_asx2"]',
                            'div[class*="xdj266r"] button[class*="_aswp"][class*="_aswq"][class*="_asws"]',
                            'button[class*="_aswp"][class*="_aswq"][class*="_asws"][class*="_aswu"][class*="_asx0"][class*="_asx2"]',
                        ]
                        
                        first_button_clicked = False
                        for selector in first_button_selectors:
                            try:
                                button = driver.find_element(By.CSS_SELECTOR, selector)
                                if button.is_displayed() and button.is_enabled():
                                    driver.execute_script("arguments[0].click();", button)
                                    print(f"   ✅ 첫 번째 linked_page 버튼 클릭 (모달 열기)")
                                    first_button_clicked = True
                                    time.sleep(2)  # 모달 생성 대기
                                    break
                            except NoSuchElementException:
                                continue
                        
                        if first_button_clicked:
                            # 2단계: 생성된 모달 div에서 링크 찾기
                            # <div class="x1n2onr6 xzkaem6">가 생성됨
                            # 그 안의 <div x78zum5 xdt5ytf x1crbq5u xvrdyt3 x179zr98><div> 안의 <button> 안의 <a> 태그
                            try:
                                # 생성된 모달 div 대기
                                modal_selectors = [
                                    'div[class*="x1n2onr6"][class*="xzkaem6"]',
                                    'div[class*="x1n2onr6"]',
                                ]
                                
                                modal_div = None
                                for selector in modal_selectors:
                                    try:
                                        modal_div = WebDriverWait(driver, 5).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                        )
                                        print(f"   ✅ 모달 div 생성 확인")
                                        break
                                    except TimeoutException:
                                        continue
                                
                                if modal_div:
                                    # 모달 내에서 링크 찾기
                                    link_container_selectors = [
                                        'div[class*="x78zum5"][class*="xdt5ytf"][class*="x1crbq5u"] div button[class*="xjbqb8w"][class*="x1qhh985"] a',
                                        'div[class*="x78zum5"][class*="xdt5ytf"] button[class*="xjbqb8w"] a',
                                        'div[class*="x78zum5"] button[class*="xjbqb8w"] a',
                                    ]
                                    
                                    for selector in link_container_selectors:
                                        try:
                                            links = modal_div.find_elements(By.CSS_SELECTOR, selector)
                                            for link in links:
                                                href = link.get_attribute("href")
                                                if href and href not in linked_page:
                                                    linked_page.append(href)
                                                    print(f"   ✅ linked_page 추가: {href[:80]}...")
                                            if linked_page:
                                                break
                                        except NoSuchElementException:
                                            continue
                                    
                                    if not linked_page:
                                        print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다.")
                                else:
                                    print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다.")
                            except Exception as e:
                                print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다. (오류: {e})")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다.")
                    except Exception as e:
                        print(f"   ⚠️ 링크를 건 페이지를 찾을 수 없습니다. (오류: {e})")
                        import traceback
                        traceback.print_exc()
                    
                    # linked_page가 비어있으면 null로 설정
                    if not linked_page:
                        linked_page = None
                    
                    # 4. followers 수집 (팔로워 페이지 접근)
                    followers_count = None
                    try:
                        followers_url = f"https://www.instagram.com/{handle}/followers/"
                        print(f"   👥 팔로워 페이지 접근 중: {followers_url}")
                        driver.get(followers_url)
                        time.sleep(3)  # 페이지 로드 대기
                        
                        # 디버깅: 모든 <a href="/~~/followers/"> 요소 찾기 및 출력
                        print(f"\n   🔍 디버깅: <a href*='/followers/'> 요소 검색 중...")
                        try:
                            # 모든 followers 링크 찾기
                            followers_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/followers/"]')
                            print(f"   📊 발견된 followers 링크 개수: {len(followers_links)}개")
                            
                            for idx, link in enumerate(followers_links[:10], 1):  # 처음 10개만 출력
                                try:
                                    href = link.get_attribute("href")
                                    text = link.text.strip()
                                    inner_html = link.get_attribute("innerHTML")
                                    
                                    print(f"   [{idx}] href: {href}")
                                    print(f"       text: {text}")
                                    if inner_html and len(inner_html) < 200:
                                        print(f"       innerHTML: {inner_html}")
                                    
                                    # span 요소 찾기
                                    try:
                                        spans = link.find_elements(By.CSS_SELECTOR, "span")
                                        if spans:
                                            print(f"       span 개수: {len(spans)}개")
                                            for span_idx, span in enumerate(spans[:3], 1):  # 처음 3개만
                                                span_text = span.text.strip()
                                                if span_text:
                                                    print(f"         span[{span_idx}]: {span_text}")
                                    except:
                                        pass
                                    print()
                                except Exception as e:
                                    print(f"   [{idx}] 요소 처리 중 오류: {e}")
                        except Exception as e:
                            print(f"   ⚠️ 디버깅 중 오류: {e}")
                        
                        # JavaScript로 더 자세한 디버깅
                        print(f"   🔍 JavaScript 디버깅 실행 중...")
                        debug_info = driver.execute_script("""
                            var links = document.querySelectorAll('a[href*="/followers/"]');
                            var results = [];
                            for (var i = 0; i < Math.min(links.length, 10); i++) {
                                var link = links[i];
                                var href = link.getAttribute('href');
                                var text = link.textContent || link.innerText;
                                var innerHTML = link.innerHTML;
                                
                                // span 요소 찾기
                                var spans = link.querySelectorAll('span');
                                var spanTexts = [];
                                for (var j = 0; j < spans.length; j++) {
                                    var spanText = spans[j].textContent || spans[j].innerText;
                                    if (spanText && spanText.trim()) {
                                        spanTexts.push(spanText.trim());
                                    }
                                }
                                
                                results.push({
                                    href: href,
                                    text: text.trim(),
                                    innerHTML: innerHTML.substring(0, 200),
                                    spanTexts: spanTexts.slice(0, 5)
                                });
                            }
                            return results;
                        """)
                        
                        print(f"   📊 JavaScript로 발견된 요소: {len(debug_info)}개")
                        for idx, info in enumerate(debug_info, 1):
                            print(f"   [{idx}] href: {info.get('href', 'N/A')}")
                            print(f"       text: {info.get('text', 'N/A')}")
                            if info.get('spanTexts'):
                                print(f"       span texts: {info.get('spanTexts')}")
                            print()
                        
                        # 팔로워 수 추출 시도 (여러 셀렉터 시도)
                        print(f"   🔍 팔로워 수 추출 시도 중...")
                        followers_selectors = [
                            'a[href*="/followers/"] span',
                            'a[href*="/followers/"]',
                            'span:contains("팔로워")',
                            'a:contains("팔로워")',
                        ]
                        
                        for selector in followers_selectors:
                            try:
                                # JavaScript로 텍스트 검색
                                followers_text = driver.execute_script("""
                                    var links = document.querySelectorAll('a[href*="/followers/"]');
                                    console.log('총 링크 개수:', links.length);
                                    for (var i = 0; i < links.length; i++) {
                                        var link = links[i];
                                        var text = link.textContent || link.innerText;
                                        console.log('링크[' + i + '] text:', text);
                                        if (text && text.includes('팔로워')) {
                                            // 숫자 추출
                                            var match = text.match(/[\\d,]+/);
                                            if (match) {
                                                console.log('매칭된 숫자:', match[0]);
                                                return match[0].replace(/,/g, '');
                                            }
                                        }
                                    }
                                    return null;
                                """)
                                
                                print(f"   🔍 셀렉터 '{selector}' 결과: {followers_text}")
                                
                                if followers_text:
                                    try:
                                        followers_count = int(followers_text)
                                        print(f"   ✅ followers 수집: {followers_count:,}명")
                                        break
                                    except ValueError:
                                        print(f"   ⚠️ 숫자 변환 실패: {followers_text}")
                                        continue
                            except Exception as e:
                                print(f"   ⚠️ 셀렉터 '{selector}' 처리 중 오류: {e}")
                                continue
                        
                        # 대체 방법: 페이지 소스에서 검색
                        if followers_count is None:
                            print(f"   🔍 대체 방법: 페이지 소스에서 검색 중...")
                            try:
                                page_source = driver.page_source
                                import re
                                # "팔로워 OOO" 패턴 찾기
                                patterns = [
                                    r'팔로워\s*([\d,]+)',
                                    r'followers["\']?\s*:?\s*([\d,]+)',
                                    r'([\d,]+)\s*팔로워',
                                ]
                                for pattern in patterns:
                                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                                    print(f"   🔍 패턴 '{pattern}' 매칭 결과: {len(matches)}개")
                                    if matches:
                                        for match in matches[:5]:  # 처음 5개만 출력
                                            print(f"      매칭: {match}")
                                        try:
                                            # 가장 큰 숫자 선택 (보통 팔로워 수가 가장 큼)
                                            numbers = [int(m.replace(',', '')) for m in matches]
                                            if numbers:
                                                followers_count = max(numbers)
                                                print(f"   ✅ followers 수집 (대체 방법): {followers_count:,}명")
                                                break
                                        except ValueError:
                                            continue
                            except Exception as e:
                                print(f"   ⚠️ followers 수집 실패 (대체 방법): {e}")
                        
                        if followers_count is None:
                            print(f"   ⚠️ followers를 찾을 수 없습니다.")
                            print(f"   💡 팔로워 페이지가 제대로 로드되었는지 확인하세요.")
                    except Exception as e:
                        print(f"   ⚠️ followers 수집 중 오류: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # 기존 데이터 업데이트 (id와 user_handle은 보존)
                    if handle in existing_by_handle:
                        # 기존 항목 찾기 (id와 user_handle 보존)
                        for item in user_data:
                            if item.get("user_handle") == handle:
                                # id와 user_handle은 보존하고, user_name, introduce, linked_page, followers 업데이트
                                if user_name:
                                    item["user_name"] = user_name
                                
                                # introduce는 기존 값과 다르면 업데이트
                                if introduce:
                                    existing_introduce = item.get("introduce")
                                    if existing_introduce != introduce:
                                        item["introduce"] = introduce
                                        print(f"   ✅ introduce 업데이트: {len(existing_introduce) if existing_introduce else 0}자 → {len(introduce)}자")
                                    else:
                                        item["introduce"] = introduce  # 기존 값과 같아도 저장 (보존)
                                # introduce가 None이면 기존 값 보존
                                elif "introduce" in item:
                                    # 기존 introduce 값 유지
                                    pass
                                
                                # linked_page는 null이어도 저장
                                item["linked_page"] = linked_page
                                
                                # followers는 숫자가 있으면 업데이트 (기존 값과 다르면 업데이트)
                                if followers_count is not None:
                                    existing_followers = item.get("followers")
                                    if existing_followers != followers_count:
                                        item["followers"] = followers_count
                                        print(f"   ✅ followers 업데이트: {existing_followers} → {followers_count}")
                                    else:
                                        item["followers"] = followers_count  # 기존 값과 같아도 저장 (보존)
                                # followers가 None이면 기존 값 보존
                                elif "followers" in item:
                                    # 기존 followers 값 유지
                                    pass
                                print(f"   ✅ 기존 데이터 업데이트 완료")
                                break
                    else:
                        # 새 데이터 추가 (instagram_extract_user.py에서 생성되지 않은 경우)
                        # 하지만 일반적으로는 instagram_extract_user.py에서 먼저 user_handle을 생성하므로
                        # 이 경우는 발생하지 않아야 함
                        new_item = {
                            "user_handle": handle
                        }
                        if user_name:
                            new_item["user_name"] = user_name
                        if introduce:
                            new_item["introduce"] = introduce
                        # linked_page는 null이어도 저장
                        new_item["linked_page"] = linked_page
                        # followers는 숫자가 있으면 저장
                        if followers_count is not None:
                            new_item["followers"] = followers_count
                        user_data.append(new_item)
                        existing_by_handle[handle] = new_item
                        print(f"   ✅ 새 데이터 추가 완료 (주의: user_handle이 instagram_extract_user.py에 없음)")
                    
                    # JSON 파일 저장 (각 항목 처리 후 즉시 저장) - 테스트 모드가 아닐 때만
                    if TEST_URL is None:
                        try:
                            with open(USER_JSON, "w", encoding="utf-8") as f:
                                json.dump(user_data, f, ensure_ascii=False, indent=2)
                            print(f"   💾 JSON 파일 저장 완료")
                        except Exception as e:
                            print(f"   ⚠️ JSON 파일 저장 실패: {e}")
                    else:
                        print(f"   ℹ️ 테스트 모드: JSON 파일 저장하지 않음")
                        
                except Exception as e:
                    print(f"   ❌ 정보 수집 중 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 요청 간 딜레이 (Instagram 차단 방지)
                time.sleep(2)
        
        except Exception as e:
            print(f"❌ 일반 모드 실행 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"❌ 전체 실행 중 오류 발생: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    
    # 최종 JSON 파일 저장 (안전장치) - 테스트 모드가 아닐 때만
    if TEST_URL is None:
        try:
            print("\n📝 최종 JSON 파일 저장 중...")
            with open(USER_JSON, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            print("✅ 최종 JSON 파일 저장 완료")
        except Exception as e:
            print(f"⚠️ 최종 JSON 파일 저장 실패: {e}")
    else:
        print("\nℹ️ 테스트 모드: JSON 파일 저장하지 않음")
    
    print("\n🔒 브라우저 종료")
    
    # 386번째 줄: 모든 작업 완료 확인
    # 이 시점에서 JSON 저장이 완료되었는지 확인
    try:
        # JSON 파일이 존재하고 올바르게 저장되었는지 확인
        if USER_JSON.exists():
            with open(USER_JSON, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            print(f"✅ JSON 파일 저장 확인: {len(saved_data)}개 항목 저장됨")
        else:
            print("⚠️ JSON 파일이 존재하지 않습니다.")
    except Exception as e:
        print(f"⚠️ JSON 파일 확인 중 오류: {e}")
    
    print("✅ 모든 작업 완료")
    print("\n" + "="*60)
    print("📌 이 시점에서 instagram_user.json 저장이 완료되었습니다.")
    print("📌 이제 다른 반복문을 실행할 수 있습니다.")
    print("="*60)

# 새로운 반복문: instagram_media.json과 instagram_user.json에서 숫자 패턴 찾아 user_num 추가
# finally 블록 밖에서 실행 (브라우저 종료 후)
print("\n" + "="*60)
print("🔍 숫자 패턴 검색 및 user_num 필드 추가 시작")
print("="*60)

try:
    # JSON 파일 경로
    MEDIA_JSON = Path("instagram_media.json")
    USER_JSON_FOR_NUM = Path("instagram_user.json")
    
    # instagram_media.json 불러오기
    if not MEDIA_JSON.exists():
        print(f"⚠️ {MEDIA_JSON} 파일이 존재하지 않습니다.")
    elif not USER_JSON_FOR_NUM.exists():
        print(f"⚠️ {USER_JSON_FOR_NUM} 파일이 존재하지 않습니다.")
    else:
        with open(MEDIA_JSON, "r", encoding="utf-8") as f:
            media_data = json.load(f)
        
        print(f"✅ {MEDIA_JSON} 로드 완료: {len(media_data)}개 항목")
        
        # instagram_user.json 불러오기
        with open(USER_JSON_FOR_NUM, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        
        if not user_data:
            print(f"⚠️ {USER_JSON_FOR_NUM}에 데이터가 없습니다.")
        else:
            print(f"✅ {USER_JSON_FOR_NUM} 로드 완료: {len(user_data)}개 항목")
            
            # user_data를 id를 키로 하는 딕셔너리로 변환 (빠른 검색을 위해)
            user_by_id = {}
            for user in user_data:
                user_id = user.get("id")
                if user_id:
                    user_by_id[str(user_id)] = user
            
            print(f"✅ user_by_id 딕셔너리 생성 완료: {len(user_by_id)}개 항목")
            
            # user_data를 handle을 키로 하는 딕셔너리로 변환 (빠른 검색을 위해)
            user_by_handle = {}
            for user in user_data:
                user_handle = user.get("user_handle", "")
                if user_handle:
                    user_by_handle[user_handle] = user
            
            print(f"✅ user_by_handle 딕셔너리 생성 완료: {len(user_by_handle)}개 항목")
            
            # 숫자 패턴 정의
            # 앞자리가 7 또는 8로 시작하는 7자리 숫자열 (앞뒤에 숫자가 아닌 문자나 기호가 있어도 발견)
            pattern_7digit = re.compile(r'[78]\d{6}')
            # 앞자리가 1 또는 2 또는 4로 시작하는 8자리 숫자열 (앞뒤에 숫자가 아닌 문자나 기호가 있어도 발견)
            pattern_8digit = re.compile(r'[124]\d{7}')
            
            # instagram_media.json의 각 항목에서 숫자 패턴 찾기
            # 각 media_item의 id 또는 handle을 사용해서 instagram_user.json에서 매칭할 예정
            media_found_numbers_by_id = []  # (media_id, found_number) 튜플 리스트
            media_found_numbers_by_handle = []  # (media_handle, found_number) 튜플 리스트
            
            for media_item in media_data:
                media_id = media_item.get("id")
                media_handle = media_item.get("handle", "")  # handle 필드 확인
                
                found_numbers_in_item = set()
                
                # content 필드에서 찾기
                content = media_item.get("content", "")
                if content:
                    matches_7 = pattern_7digit.findall(content)
                    matches_8 = pattern_8digit.findall(content)
                    for match in matches_7 + matches_8:
                        found_numbers_in_item.add(match)
                
                # media_caption 필드에서 찾기 (리스트일 수 있음)
                media_caption = media_item.get("media_caption", [])
                if isinstance(media_caption, list):
                    for caption_item in media_caption:
                        if isinstance(caption_item, str):
                            matches_7 = pattern_7digit.findall(caption_item)
                            matches_8 = pattern_8digit.findall(caption_item)
                            for match in matches_7 + matches_8:
                                found_numbers_in_item.add(match)
                elif isinstance(media_caption, str):
                    matches_7 = pattern_7digit.findall(media_caption)
                    matches_8 = pattern_8digit.findall(media_caption)
                    for match in matches_7 + matches_8:
                        found_numbers_in_item.add(match)
                
                # audio_caption 필드에서 찾기
                audio_caption = media_item.get("audio_caption", "")
                if audio_caption:
                    matches_7 = pattern_7digit.findall(audio_caption)
                    matches_8 = pattern_8digit.findall(audio_caption)
                    for match in matches_7 + matches_8:
                        found_numbers_in_item.add(match)
                
                # 찾은 숫자를 media_id 또는 media_handle과 함께 저장
                if found_numbers_in_item:
                    if media_id:
                        # id가 있으면 id로 매칭
                        for num in found_numbers_in_item:
                            media_found_numbers_by_id.append((str(media_id), num))
                    elif media_handle:
                        # id가 없고 handle이 있으면 handle로 매칭
                        for num in found_numbers_in_item:
                            media_found_numbers_by_handle.append((media_handle, num))
            
            total_media_found = len(media_found_numbers_by_id) + len(media_found_numbers_by_handle)
            print(f"✅ instagram_media.json에서 발견된 숫자 패턴: {total_media_found}개")
            print(f"   - id로 매칭: {len(media_found_numbers_by_id)}개")
            print(f"   - handle로 매칭: {len(media_found_numbers_by_handle)}개")
            if media_found_numbers_by_id or media_found_numbers_by_handle:
                all_numbers = [num for _, num in media_found_numbers_by_id] + [num for _, num in media_found_numbers_by_handle]
                unique_numbers = set(all_numbers)
                print(f"   발견된 숫자: {sorted(unique_numbers)[:20]}...")  # 처음 20개만 출력
            
            # instagram_user.json의 각 항목에서 숫자 패턴 찾기
            for user_item in user_data:
                user_found_numbers = set()
                
                # user_name 필드에서 찾기
                user_name = user_item.get("user_name", "")
                if user_name:
                    matches_7 = pattern_7digit.findall(user_name)
                    matches_8 = pattern_8digit.findall(user_name)
                    for match in matches_7 + matches_8:
                        user_found_numbers.add(match)
                
                # handle 필드에서 찾기
                handle = user_item.get("user_handle", "")
                if handle:
                    matches_7 = pattern_7digit.findall(handle)
                    matches_8 = pattern_8digit.findall(handle)
                    for match in matches_7 + matches_8:
                        user_found_numbers.add(match)
                
                # introduce 필드에서 찾기
                introduce = user_item.get("introduce", "")
                if introduce:
                    matches_7 = pattern_7digit.findall(introduce)
                    matches_8 = pattern_8digit.findall(introduce)
                    for match in matches_7 + matches_8:
                        user_found_numbers.add(match)
                
                # 찾은 숫자를 해당 user_item의 user_num에 추가 (리스트가 아닌 단일 값으로 저장)
                if user_found_numbers:
                    # 여러 개 발견되면 첫 번째 값만 저장
                    num = sorted(user_found_numbers)[0]
                    user_item["user_num"] = num
                    print(f"   ✅ user_num 추가 (user.json에서 발견): user_id={user_item.get('id')}, user_handle={user_item.get('user_handle')}, user_num={num}")
            
            # instagram_media.json에서 찾은 숫자 처리 (id로 매칭)
            # media_item의 id를 사용해서 instagram_user.json에서 같은 id를 가진 항목 찾기
            for media_id, num in media_found_numbers_by_id:
                # media_id와 일치하는 user_item 찾기
                if media_id in user_by_id:
                    user_item = user_by_id[media_id]
                    # user_num이 이미 있으면 업데이트하지 않음 (기존 값 유지)
                    if "user_num" not in user_item:
                        user_item["user_num"] = num
                        print(f"   ✅ user_num 추가 (media에서 발견, id로 매칭): user_id={user_item.get('id')}, user_num={num}")
                else:
                    # media_id와 일치하는 user_item이 없으면 로그만 출력
                    print(f"   ⚠️ media_id={media_id}와 일치하는 user_item을 찾을 수 없습니다. (발견된 숫자: {num})")
            
            # instagram_media.json에서 찾은 숫자 처리 (handle로 매칭)
            # media_item의 handle을 사용해서 instagram_user.json에서 같은 user_handle을 가진 항목 찾기
            for media_handle, num in media_found_numbers_by_handle:
                # media_handle과 일치하는 user_item 찾기
                if media_handle in user_by_handle:
                    user_item = user_by_handle[media_handle]
                    # user_num이 이미 있으면 업데이트하지 않음 (기존 값 유지)
                    if "user_num" not in user_item:
                        user_item["user_num"] = num
                        print(f"   ✅ user_num 추가 (media에서 발견, handle로 매칭): user_handle={user_item.get('user_handle')}, user_id={user_item.get('id')}, user_num={num}")
                else:
                    # media_handle과 일치하는 user_item이 없으면 로그만 출력
                    print(f"   ⚠️ media_handle={media_handle}와 일치하는 user_item을 찾을 수 없습니다. (발견된 숫자: {num})")
            
            # instagram_user.json 저장
            with open(USER_JSON_FOR_NUM, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            
            # 통계 출력
            user_num_count = sum(1 for user in user_data if user.get("user_num"))
            print(f"\n✅ user_num 필드 추가 완료")
            print(f"   user_num이 추가된 항목: {user_num_count}개")
            print(f"   총 user_data 항목: {len(user_data)}개")

except Exception as e:
    print(f"❌ 숫자 패턴 검색 중 오류 발생: {e}")
    import traceback
    traceback.print_exc()
