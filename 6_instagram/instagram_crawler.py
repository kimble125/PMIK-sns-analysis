import json
import logging
import time
import re
import random
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
import os
import pickle

# .env 파일에서 로그인 정보 불러오기
load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

# JSON 파일 경로
USER_JSON = Path("instagram_user.json")
MEDIA_JSON = Path("instagram_media.json")
COLLECTED_PERMALINKS_JSON = Path("instagram_collected_permalinks.json")  # 스텝1에서 수집한 permalink 저장
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

# Selenium WebDriver 설정
def setup_driver():
    """Selenium WebDriver 설정"""
    import shutil
    
    # Chrome 브라우저 경로 후보 리스트 (우선순위 순)
    chrome_path_candidates = []
    
    # 1. which 명령어로 PATH에서 찾기 (가장 신뢰할 수 있음)
    for cmd in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
        chrome_cmd = shutil.which(cmd)
        if chrome_cmd:
            chrome_path_candidates.append(Path(chrome_cmd))
            logging.info(f"which 명령어로 Chrome 경로 발견: {chrome_cmd}")
    
    # 2. 일반적인 설치 경로 확인
    for chrome_path in (
        Path("/opt/google/chrome/chrome"),
        Path("/opt/google/chrome/google-chrome"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/google-chrome-stable"),
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
    ):
        if chrome_path.exists() and os.access(chrome_path, os.X_OK):
            if chrome_path not in chrome_path_candidates:
                chrome_path_candidates.append(chrome_path)
                logging.info(f"Chrome 브라우저 경로 발견 (실행 가능): {chrome_path}")
    
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
    
    # 각 경로를 시도하여 실제로 작동하는지 확인
    last_error = None
    for chrome_path in chrome_path_candidates:
        chrome_binary_location = chrome_path.as_posix()
        logging.info(f"Chrome 경로 시도: {chrome_binary_location}")
        
    chrome_options = Options()
        chrome_options.binary_location = chrome_binary_location
        
        # Windows와 동일하게 headless 비활성화 (Instagram이 headless를 감지하여 차단함)
        # Linux에서는 Xvfb를 사용하여 가상 디스플레이에서 실행
        chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--display=:99")  # Xvfb 디스플레이 사용
        
        # WebDriver 감지 방지 (Windows와 동일하게)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 현실적인 User-Agent 설정 (Windows Chrome과 유사하게)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Performance 로그 활성화 (네트워크 로그에서 비디오 URL 찾기 위해)
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
        try:
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_window_size(1920, 1080)  # 카카오스토리처럼 창 크기 설정
            
            # WebDriver 속성 숨기기 (초기화 시점에)
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.navigator.chrome = {
                        runtime: {}
                    };
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['ko-KR', 'ko', 'en-US', 'en']
                    });
                '''
            })
            
            logging.info(f"Chrome WebDriver 초기화 성공: {chrome_binary_location}")
    return driver
        except Exception as e:
            last_error = e
            logging.warning(f"Chrome 경로 실패 ({chrome_binary_location}): {str(e)}")
            continue
    
    # 모든 경로가 실패한 경우
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

def simulate_human_behavior(driver):
    """실제 브라우저처럼 보이는 행동 패턴 시뮬레이션"""
    try:
        # 랜덤한 마우스 움직임
        actions = ActionChains(driver)
        # 현재 페이지에서 랜덤한 위치로 마우스 이동
        for _ in range(random.randint(1, 3)):
            x_offset = random.randint(-100, 100)
            y_offset = random.randint(-100, 100)
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                actions.move_to_element_with_offset(body, x_offset, y_offset)
                actions.perform()
                time.sleep(random.uniform(0.1, 0.3))
            except:
                pass
        
        # 자연스러운 대기 시간
        time.sleep(random.uniform(0.5, 1.5))
        
        # 약간의 스크롤 (자연스러운 행동)
        scroll_amount = random.randint(50, 200)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(0.3, 0.8))
                except Exception as e:
        logging.debug(f"인간 행동 시뮬레이션 중 오류: {e}")

def regenerate_cookies(driver):
    """쿠키 재생성 (기존 쿠키 삭제 후 새로 생성)"""
    print("🔄 쿠키 재생성 시작...")
    logging.info("쿠키 재생성 시작")
    
    # 기존 쿠키 파일 삭제
    if COOKIE_PATH.exists():
        try:
            COOKIE_PATH.unlink()
            print("  ✅ 기존 쿠키 파일 삭제됨")
            logging.info("기존 쿠키 파일 삭제됨")
        except Exception as e:
            logging.warning(f"쿠키 파일 삭제 실패: {e}")
            print(f"  ⚠️ 쿠키 파일 삭제 실패: {e}")
    
    # 새 쿠키 생성 (수동 로그인)
    if USERNAME and PASSWORD:
        print("🔐 새 쿠키 생성 중 (자동 로그인)...")
        logging.info("자동 로그인으로 새 쿠키 생성")
        
        try:
        driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(random.uniform(3, 5))
            
            # 페이지 로드 확인
            print("  ⏳ 로그인 페이지 로드 대기 중...")
            try:
                # 다양한 선택자로 username 필드 찾기
                username_input = None
                username_selectors = [
                    (By.NAME, "username"),
                    (By.CSS_SELECTOR, "input[name='username']"),
                    (By.CSS_SELECTOR, "input[type='text']"),
                    (By.CSS_SELECTOR, "input[aria-label*='전화번호']"),
                    (By.CSS_SELECTOR, "input[aria-label*='사용자 이름']"),
                ]
                
                for selector_type, selector_value in username_selectors:
                    try:
                        username_input = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        print(f"  ✅ Username 필드 발견: {selector_value}")
                        break
                    except TimeoutException:
                        continue
                
                if not username_input:
                    print("  ⚠️ Username 필드를 찾을 수 없습니다.")
                    print("  현재 페이지 URL:", driver.current_url)
                    print("  페이지 제목:", driver.title)
                    logging.warning(f"Username 필드를 찾을 수 없음. URL: {driver.current_url}, Title: {driver.title}")
                    # 수동 로그인으로 전환
                    print("  수동 로그인으로 전환합니다...")
                    return regenerate_cookies_manual(driver)
                
                # Password 필드 찾기
                password_input = None
                password_selectors = [
                    (By.NAME, "password"),
                    (By.CSS_SELECTOR, "input[name='password']"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                ]
                
                for selector_type, selector_value in password_selectors:
                    try:
                        password_input = driver.find_element(selector_type, selector_value)
                        print(f"  ✅ Password 필드 발견: {selector_value}")
                        break
                    except NoSuchElementException:
                        continue
                
                if not password_input:
                    print("  ⚠️ Password 필드를 찾을 수 없습니다.")
                    logging.warning("Password 필드를 찾을 수 없음")
                    return regenerate_cookies_manual(driver)
                
                # 실제 사용자처럼 타이핑 (느리게)
                print("  ⌨️ 사용자 이름 입력 중...")
                username_input.clear()
                for char in USERNAME:
                    username_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                time.sleep(random.uniform(0.5, 1.0))
                
                print("  ⌨️ 비밀번호 입력 중...")
                password_input.clear()
                for char in PASSWORD:
                    password_input.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                time.sleep(random.uniform(0.5, 1.0))
                
                # 실제 사용자처럼 행동
                simulate_human_behavior(driver)
                
                # 로그인 버튼 찾기
                login_button = None
                login_selectors = [
                    "button[type='submit']",
                    "button._acan._acap._acas._aj1-",
                    "button:contains('로그인')",
                    "button:contains('Log in')",
                ]
                
                for selector in login_selectors:
                    try:
                        login_button = driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"  ✅ 로그인 버튼 발견: {selector}")
                        break
                    except NoSuchElementException:
                        continue
                
                if not login_button:
                    # JavaScript로 버튼 찾기
                    try:
                        login_button = driver.execute_script("""
                            var buttons = document.querySelectorAll('button[type="submit"]');
                            return buttons.length > 0 ? buttons[0] : null;
                        """)
                        if login_button:
                            print("  ✅ 로그인 버튼 발견 (JavaScript)")
                    except:
                        pass
                
                if not login_button:
                    print("  ⚠️ 로그인 버튼을 찾을 수 없습니다.")
                    logging.warning("로그인 버튼을 찾을 수 없음")
                    return regenerate_cookies_manual(driver)
                
                # 로그인 버튼 클릭
                print("  🔘 로그인 버튼 클릭...")
                try:
            login_button.click()
                except:
                    # JavaScript로 클릭 시도
                    driver.execute_script("arguments[0].click();", login_button)
                
                # 로그인 완료 대기
                print("  ⏳ 로그인 완료 대기 중...")
                time.sleep(random.uniform(5, 8))
                
                # 실제 사용자처럼 행동
                simulate_human_behavior(driver)
                
                # 로그인 확인
                current_url = driver.current_url.lower()
                print(f"  🔍 현재 URL: {driver.current_url}")
                
                # Challenge 페이지 감지
                if "/challenge/" in current_url:
                    print("  ⚠️ Instagram 보안 검증 페이지(challenge)로 리다이렉트됨")
                    print("  💡 Instagram이 봇을 감지했습니다.")
                    print(f"  📋 Challenge 페이지 URL: {driver.current_url}")
                    logging.warning(f"Challenge 페이지 감지: {driver.current_url}")
                    print("\n" + "="*60)
                    print("🔐 Challenge 페이지 처리 방법:")
                    print("  1. 위의 URL을 복사하여 일반 브라우저에서 열어주세요")
                    print("  2. Challenge 검증을 완료해주세요")
                    print("  3. 검증 완료 후 이 스크립트를 다시 실행하거나")
                    print("  4. 아래에서 수동 로그인을 진행해주세요")
                    print("="*60 + "\n")
                    # Challenge 페이지에서 일정 시간 대기 (자동으로 완료될 수도 있음)
                    print("  ⏳ Challenge 페이지에서 30초 대기 중... (자동 완료 대기)")
                    for wait_sec in range(30, 0, -5):
            time.sleep(5)
                        current_url_check = driver.current_url.lower()
                        if "/challenge/" not in current_url_check:
                            print(f"  ✅ Challenge가 자동으로 완료된 것 같습니다!")
                            break
                        print(f"  ⏳ {wait_sec}초 남음...")
                    
                    # 다시 확인
                    final_url = driver.current_url.lower()
                    if "/challenge/" not in final_url and "login" not in final_url and "accounts/login" not in final_url:
                        print("  ✅ Challenge 완료! 쿠키 저장 중...")
                        try:
                            cookies = driver.get_cookies()
                            pickle.dump(cookies, open(COOKIE_PATH, "wb"))
                            print(f"✅ 쿠키 저장 완료 ({len(cookies)}개 쿠키)")
                            logging.info(f"Challenge 완료 후 쿠키 저장: {len(cookies)}개 쿠키")
                            return True
                        except Exception as e:
                            logging.error(f"쿠키 저장 실패: {e}")
                    
                    # 여전히 challenge 페이지면 수동 로그인으로 전환
                    print("  ⚠️ Challenge가 자동으로 완료되지 않았습니다.")
                    print("  수동 로그인으로 전환합니다...")
                    return regenerate_cookies_manual(driver)
                
                if "login" not in current_url and "accounts/login" not in current_url:
            # 쿠키 저장
                    try:
                        cookies = driver.get_cookies()
                        pickle.dump(cookies, open(COOKIE_PATH, "wb"))
                        print(f"✅ 새 쿠키 생성 및 저장 완료 ({len(cookies)}개 쿠키)")
                        logging.info(f"새 쿠키 생성 및 저장 완료 ({len(cookies)}개 쿠키)")
            return True
        except Exception as e:
                        logging.error(f"쿠키 저장 실패: {e}", exc_info=True)
                        print(f"  ⚠️ 쿠키 저장 실패: {e}")
            return False
    else:
                    print("  ⚠️ 로그인 실패 (로그인 페이지에 머물러 있음)")
                    print(f"  현재 URL: {driver.current_url}")
                    logging.warning(f"자동 로그인 실패. URL: {driver.current_url}")
                    # 수동 로그인으로 전환
                    print("  수동 로그인으로 전환합니다...")
                    return regenerate_cookies_manual(driver)
                    
            except TimeoutException as e:
                logging.error(f"로그인 페이지 로드 타임아웃: {e}", exc_info=True)
                print(f"❌ 로그인 페이지 로드 타임아웃: {e}")
                print("  수동 로그인으로 전환합니다...")
                return regenerate_cookies_manual(driver)
        except Exception as e:
            logging.error(f"자동 로그인 실패: {e}", exc_info=True)
            print(f"❌ 자동 로그인 실패: {e}")
            import traceback
            traceback.print_exc()
            print("  수동 로그인으로 전환합니다...")
            return regenerate_cookies_manual(driver)
    else:
        # 수동 로그인
        return regenerate_cookies_manual(driver)

def regenerate_cookies_manual(driver):
    """수동 로그인으로 쿠키 재생성"""
    print("\n" + "="*70)
    print("🔐 수동 로그인 모드")
    print("="*70)
    logging.info("수동 로그인으로 쿠키 재생성 시작")
    
    try:
        current_url = driver.current_url
        print(f"\n📋 현재 페이지 URL:")
        print(f"   {current_url}\n")
        
        # Challenge 페이지인 경우
        if "/challenge/" in current_url.lower():
            print("⚠️ Challenge 페이지가 감지되었습니다.\n")
            print("💡 Challenge URL이 만료되었거나 작동하지 않을 수 있습니다.")
            print("   다음 방법 중 하나를 선택하세요:\n")
            print("   [방법 1] 일반 브라우저에서 직접 로그인 후 쿠키 추출 (권장)")
            print("   1. 일반 브라우저(Chrome, Firefox 등)에서 https://www.instagram.com 접속")
            print("   2. Instagram에 로그인 (필요시 Challenge 완료)")
            print("   3. 로그인 완료 후 Instagram 메인 페이지로 이동 확인")
            print("   4. 개발자 도구(F12) → Application → Cookies → instagram.com")
            print("   5. 쿠키를 추출하여 저장 (아래 Python 스크립트 사용)\n")
            print("   [방법 2] 스크립트 브라우저에서 Challenge 페이지 새로고침 후 대기")
            print("   1. 아래에서 'r'을 입력하여 Challenge 페이지 새로고침")
            print("   2. 또는 'w'를 입력하여 자동 완료 대기 (최대 5분)\n")
            
            choice = input("선택하세요 (1=일반 브라우저 사용, r=새로고침, w=대기, n=취소): ").lower()
            
            if choice == '1':
                print("\n" + "="*70)
                print("📋 일반 브라우저에서 로그인 후 쿠키 추출 방법:")
                print("="*70)
                print("\n[단계별 안내]")
                print("1. 일반 브라우저(Chrome/Firefox)에서 https://www.instagram.com 접속")
                print("2. Instagram에 로그인 (필요시 Challenge 검증 완료)")
                print("3. 로그인 완료 후 Instagram 메인 페이지로 이동 확인")
                print("4. 브라우저 개발자 도구 열기 (F12)")
                print("5. Application 탭 → Cookies → https://www.instagram.com 선택")
                print("6. 쿠키를 추출하여 저장\n")
                print("[Python 스크립트로 쿠키 추출]")
                print("별도의 Python 스크립트를 사용하여 쿠키를 추출할 수 있습니다:")
                print("-"*70)
                print("다음 명령어로 쿠키 추출 스크립트를 실행하세요:")
                print("  python extract_instagram_cookies.py")
                print("")
                print("또는 수동으로:")
                print("  1. 일반 브라우저에서 https://www.instagram.com 접속")
                print("  2. 로그인/Challenge 완료")
                print("  3. 개발자 도구(F12) → Application → Cookies → instagram.com")
                print("  4. 쿠키를 JSON 형식으로 내보내기")
                print("-"*70)
                print("\n⚠️ 쿠키를 저장한 후 이 스크립트를 다시 실행해주세요.")
                print("="*70 + "\n")
                return False
            elif choice == 'r':
                print("\n🔄 Challenge 페이지 새로고침 중...")
                try:
                    driver.refresh()
                    time.sleep(5)
                    current_url_refresh = driver.current_url.lower()
                    print(f"  현재 URL: {driver.current_url[:80]}...")
                    
                    if "/challenge/" not in current_url_refresh:
                        print("  ✅ Challenge가 완료된 것 같습니다! 쿠키 저장 중...")
                        cookies = driver.get_cookies()
                        if cookies:
                            pickle.dump(cookies, open(COOKIE_PATH, "wb"))
                            print(f"✅ 쿠키 저장 완료 ({len(cookies)}개 쿠키)")
                            logging.info(f"Challenge 완료 후 쿠키 저장: {len(cookies)}개 쿠키")
                            return True
                        else:
                            print("  ⚠️ 쿠키를 찾을 수 없습니다.")
                            return False
                    else:
                        print("  ⚠️ 여전히 Challenge 페이지에 있습니다.")
                        print("  💡 일반 브라우저에서 직접 로그인하는 방법(방법 1)을 권장합니다.")
                        return False
                except Exception as e:
                    logging.error(f"Challenge 페이지 새로고침 중 오류: {e}", exc_info=True)
                    print(f"  ❌ 오류 발생: {e}")
                    return False
            elif choice == 'w':
                print("\n⏳ Challenge 페이지에서 자동 완료 대기 중...")
                print("💡 Challenge를 완료하려면:")
                print("   1. 위의 URL을 복사하여 일반 브라우저에서 열기")
                print("   2. Challenge 검증 완료")
                print("   3. 일반 브라우저에서 쿠키를 추출하여 저장 (아래 방법 참고)")
                print("   4. 또는 스크립트 브라우저에서 자동 완료 대기 (최대 5분)\n")
                
                print("📋 일반 브라우저에서 쿠키 추출 방법:")
                print("   Chrome: F12 → Application → Cookies → instagram.com")
                print("   Firefox: F12 → Storage → Cookies → instagram.com")
                print("   쿠키를 JSON 형식으로 내보내거나, 아래 Python 코드로 추출:\n")
                print("   import json")
                print("   from selenium import webdriver")
                print("   driver = webdriver.Chrome()  # 일반 브라우저")
                print("   driver.get('https://www.instagram.com')")
                print("   # 로그인/Challenge 완료 후")
                print("   cookies = driver.get_cookies()")
                print("   import pickle")
                print("   pickle.dump(cookies, open('instagram_cookies.pkl', 'wb'))\n")
                
                print("  💡 'c'를 입력하면 Challenge 완료 확인, 'q'를 입력하면 취소")
                print("  ⏳ 자동 감지 대기 중... (최대 5분, 10초마다 URL 확인)\n")
                
                start_time = time.time()
                timeout = 300  # 5분
                check_interval = 10  # 10초마다 확인
                last_url = driver.current_url
                
                while time.time() - start_time < timeout:
                    elapsed = int(time.time() - start_time)
                    
                    # URL 변경 확인
                    try:
                        current_url_check = driver.current_url.lower()
                        if "/challenge/" not in current_url_check:
                            if current_url_check != last_url.lower():
                                print(f"  ✅ URL 변경 감지! Challenge 완료로 보입니다. (경과: {elapsed}초)")
                                break
                        last_url = driver.current_url
                    except:
                        pass
                    
                    # 진행 상황 출력 (30초마다)
                    if elapsed > 0 and elapsed % 30 == 0:
                        print(f"  ⏳ {elapsed}초 경과... (현재 URL: {driver.current_url[:60]}...)")
                        print("     💡 'c' 입력 시 즉시 확인, 'q' 입력 시 취소")
                    
                    # 사용자 입력 확인 (비차단 방식 - 간단하게)
                    try:
                        import sys
                        import select
                        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                            user_input = input().strip().lower()
                            if user_input == 'c':
                                print("  ✅ Challenge 완료 확인됨. 쿠키 저장 중...")
                                break
                            elif user_input == 'q':
                                print("  ❌ 취소되었습니다.")
                                return False
                    except:
                        # select가 작동하지 않는 환경에서는 무시
                        pass
                    
                    time.sleep(check_interval)
                
                # 최종 확인
                try:
                    final_url = driver.current_url.lower()
                    if "/challenge/" not in final_url and "login" not in final_url and "accounts/login" not in final_url:
                        print("  ✅ Challenge 완료 확인! 쿠키 저장 중...")
                        time.sleep(2)  # 쿠키가 저장될 시간 확보
                        cookies = driver.get_cookies()
                        if cookies:
                            pickle.dump(cookies, open(COOKIE_PATH, "wb"))
                            print(f"✅ 쿠키 저장 완료 ({len(cookies)}개 쿠키)")
                            logging.info(f"Challenge 완료 후 쿠키 저장: {len(cookies)}개 쿠키")
                            return True
                        else:
                            print("  ⚠️ 쿠키를 찾을 수 없습니다.")
                            print("  💡 일반 브라우저에서 쿠키를 수동으로 저장해주세요.")
                            return False
                    else:
                        print("  ⚠️ Challenge가 완료되지 않았습니다.")
                        print(f"  현재 URL: {driver.current_url}")
                        print("\n  💡 해결 방법:")
                        print("     1. 일반 브라우저에서 Challenge를 완료")
                        print("     2. 일반 브라우저에서 쿠키를 추출하여 저장")
                        print("     3. 또는 스크립트를 다시 실행하여 재시도")
                        return False
                except Exception as e:
                    logging.error(f"Challenge 대기 중 오류: {e}", exc_info=True)
                    print(f"  ❌ 오류 발생: {e}")
                    return False
            else:
                print("  ❌ 취소되었습니다.")
                return False
        else:
            # 로그인 페이지인 경우
            print("💡 Instagram 로그인이 필요합니다.\n")
            print("   다음 단계를 따라주세요:")
            print("   1. 위의 URL을 복사하여 일반 브라우저에서 열기")
            print("   2. Instagram에 로그인")
            print("   3. 로그인 완료 후 Instagram 메인 페이지로 이동 확인")
            print("   4. 아래에서 'y'를 입력하여 계속 진행\n")
            
            user_input = input("로그인 완료 후 계속하시겠습니까? (y/n): ")
            if user_input.lower() != 'y':
                print("  ❌ 취소되었습니다.")
                return False
            
            # 현재 페이지에서 쿠키 확인
            print("\n  🔍 현재 페이지 상태 확인 중...")
            time.sleep(2)
            try:
                current_url_check = driver.current_url.lower()
                
                # Challenge 페이지인 경우
                if "/challenge/" in current_url_check:
                    print("  ⚠️ Challenge 페이지로 리다이렉트되었습니다.")
                    print("  Challenge 처리로 전환합니다...")
                    return regenerate_cookies_manual(driver)
                
                # 로그인 페이지인 경우
                if "login" in current_url_check or "accounts/login" in current_url_check:
                    print("  ⚠️ 여전히 로그인 페이지에 있습니다.")
                    print("  💡 일반 브라우저에서 로그인하셨다면,")
                    print("     이 스크립트의 브라우저는 여전히 로그인 페이지에 있을 수 있습니다.")
                    retry = input("  다시 시도하시겠습니까? (y/n): ")
                    if retry.lower() == 'y':
                        return regenerate_cookies_manual(driver)
                    else:
                        return False
                
                # 로그인 성공한 경우 쿠키 저장
                print("  ✅ 로그인 완료로 보입니다. 쿠키 저장 중...")
                cookies = driver.get_cookies()
                if not cookies:
                    print("  ⚠️ 쿠키를 찾을 수 없습니다.")
                    return False
                
                pickle.dump(cookies, open(COOKIE_PATH, "wb"))
                print(f"✅ 새 쿠키 저장 완료 ({len(cookies)}개 쿠키)")
                logging.info(f"수동 로그인으로 새 쿠키 저장 완료 ({len(cookies)}개 쿠키)")
                return True
            except Exception as e:
                logging.error(f"쿠키 확인 중 오류: {e}", exc_info=True)
                print(f"  ❌ 오류 발생: {e}")
                return False
    except Exception as e:
        logging.error(f"수동 로그인 중 오류: {e}", exc_info=True)
        print(f"❌ 수동 로그인 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def login_instagram(driver, force_regenerate=False):
    """Instagram 로그인 (쿠키가 없을 경우)
    
    Args:
        driver: Selenium WebDriver
        force_regenerate: True면 기존 쿠키를 무시하고 재생성
    """
    # 강제 재생성 요청이 있으면 재생성
    if force_regenerate:
        return regenerate_cookies(driver)
    
    if COOKIE_PATH.exists():
        try:
            print("🍪 저장된 쿠키 로드 중...")
            logging.info("저장된 쿠키 로드 시도")
            
            # 먼저 메인 페이지로 이동
            driver.get("https://www.instagram.com")
            time.sleep(3)  # 페이지 로드 대기
            
            # 쿠키 로드
            cookies = pickle.load(open(COOKIE_PATH, "rb"))
            cookies_added = 0
            for cookie in cookies:
                try:
                    # 쿠키 도메인 확인 및 수정
                    if 'domain' in cookie:
                        # Instagram 도메인 정규화
                        if cookie['domain'].startswith('.'):
                            cookie['domain'] = cookie['domain'][1:]
                        if cookie['domain'] not in ['instagram.com', 'www.instagram.com']:
                            cookie['domain'] = 'instagram.com'
                    driver.add_cookie(cookie)
                    cookies_added += 1
                except Exception as e:
                    logging.warning(f"쿠키 추가 실패: {e}")
                    print(f"  ⚠️ 쿠키 추가 실패: {e}")
            
            print(f"  ✅ {cookies_added}개 쿠키 추가됨")
            logging.info(f"{cookies_added}개 쿠키 추가됨")
            
            # 쿠키를 추가한 후 메인 페이지로 다시 이동 (refresh 대신)
            # Instagram이 쿠키를 제대로 인식하도록 새로 페이지를 로드
            driver.get("https://www.instagram.com")
            time.sleep(random.uniform(4, 6))  # 충분한 대기 시간
            
            # 실제 사용자처럼 행동 (마우스 움직임, 스크롤)
            simulate_human_behavior(driver)
            
            # 로그인 확인 (여러 번 확인)
            for check_attempt in range(3):
                current_url = driver.current_url.lower()
                
                # Challenge 페이지 감지
                if "/challenge/" in current_url:
                    print("  ⚠️ Instagram 보안 검증 페이지(challenge) 감지됨")
                    print("  💡 Instagram이 봇을 감지했습니다. 쿠키가 만료되었거나 차단되었을 수 있습니다.")
                    logging.warning(f"Challenge 페이지 감지: {driver.current_url}")
                    # 쿠키 재생성 시도
                    return regenerate_cookies(driver)
                
                if "login" not in current_url and "accounts/login" not in current_url:
                    print("✅ 쿠키로 로그인 성공")
                    logging.info("쿠키로 로그인 성공")
                    # 쿠키 업데이트 (세션 유지)
                    try:
        pickle.dump(driver.get_cookies(), open(COOKIE_PATH, "wb"))
                        logging.info("쿠키 업데이트 완료")
                    except Exception as e:
                        logging.warning(f"쿠키 업데이트 실패: {e}")
                    # 로그인 성공 후 실제 사용자처럼 행동
                    simulate_human_behavior(driver)
        return True
                else:
                    if check_attempt < 2:
                        print(f"  ⏳ 로그인 확인 중... (시도 {check_attempt + 1}/3)")
                        time.sleep(random.uniform(2, 3))
                        # refresh 대신 다시 메인 페이지로 이동
                        driver.get("https://www.instagram.com")
                        time.sleep(random.uniform(3, 5))
                        simulate_human_behavior(driver)
                    else:
                        logging.warning("쿠키로 로그인 실패 (로그인 페이지로 리다이렉트됨)")
                        print("  ⚠️ 쿠키로 로그인 실패, 쿠키 재생성 시도...")
                        # 쿠키 재생성 시도
                        return regenerate_cookies(driver)
        except Exception as e:
            logging.error(f"쿠키 로드 실패: {e}", exc_info=True)
            print(f"⚠️ 쿠키 로드 실패: {e}")
            print("  쿠키 재생성 시도...")
            # 쿠키 재생성 시도
            return regenerate_cookies(driver)
    
    # 쿠키가 없거나 실패한 경우 새 쿠키 생성
    return regenerate_cookies(driver)

def login_instagram_legacy(driver):
    """Instagram 로그인 (레거시 - 호환성 유지용)"""
    return login_instagram(driver, force_regenerate=False)

# permalink 정규화 함수
def normalize_permalink(url):
    """
    permalink를 정규화하여 shortcode만 추출
    - instagram_media.json 형식: "https://www.instagram.com/reel/DQ5hGrqE6SP/"
    - 수집한 형식: "https://www.instagram.com/pmi_min/reel/DD4hDgTy82T/"
    → 둘 다 shortcode만 추출하여 비교: "DQ5hGrqE6SP", "DD4hDgTy82T"
    """
    if not url:
        return None
    # 쿼리 파라미터 제거
    url = url.split("?")[0]
    # 끝에 슬래시 제거
    url = url.rstrip("/")
    
    # shortcode 추출
    # 형식 1: /reel/SHORTCODE 또는 /p/SHORTCODE
    # 형식 2: /USERNAME/reel/SHORTCODE 또는 /USERNAME/p/SHORTCODE
    if "/reel/" in url:
        parts = url.split("/reel/")
        if len(parts) > 1:
            shortcode = parts[-1].split("/")[0].split("?")[0]
            return shortcode
    elif "/p/" in url:
        parts = url.split("/p/")
        if len(parts) > 1:
            shortcode = parts[-1].split("/")[0].split("?")[0]
            return shortcode
    
    return None

# ============================================
# 스텝1: 사용자 프로필에서 게시물 permalink 수집
# ============================================
# test_mode에서 True: 상위 1개의 데이터 테스트, False: 전체 데이터 테스트
def step1_collect_post_permalinks(test_mode=False):
    """
    스텝1: instagram_user.json에서 handle 정보를 가져와서
    각 사용자 프로필 페이지에 접속하여 스크롤하며
    게시물의 href를 수집하여 리스트에 저장
    
    구조:
    - <div class="xg7h5cd x1n2onr6">...<div class="x1i5p2am x1whfx0g x16uus16 xbiv7yw x6ikm8r x10wlt62 x17h65es x117kv93 x18tieia x1xwj7al"><div><div>
      - 여러 <div class="_ac7v x1ty9z65 xzboxd6"> (스크롤 시 계속 생성됨)
        - 3개의 <div class="x1lliihq x1n2onr6 xh8yej3 x4gyw5p x14z9mp xhe4ym4 xaudc5v x1j53mea">
          - <a> 태그의 href 수집
    
    Args:
        test_mode: 테스트 모드 (True면 첫 번째 handle만 처리)
    """
    # 로깅 초기화
    setup_logging(str(LOG_PATH))
    logging.info("=" * 80)
    logging.info("프로그램 시작 - instagram_crawling_userposts.py (스텝1)")
    if test_mode:
        logging.info("테스트 모드: 첫 번째 handle만 처리")
    logging.info("=" * 80)
    
    print("=" * 60)
    print("스텝1: 사용자 프로필에서 게시물 permalink 수집 및 중복 제거")
    if test_mode:
        print(f"🧪 테스트 모드: 첫 번째 handle만 처리")
    print("=" * 60)
    
    # instagram_media.json에서 기존 permalink 로드 (리스트로 저장)
    print(f"\n📂 {MEDIA_JSON} 파일 로딩 중 (기존 permalink 확인용)...")
    existing_permalinks_list = []  # 리스트로 저장
    existing_permalinks_set = set()  # 빠른 비교를 위한 set
    existing_permalinks_map = {}  # {shortcode: original_permalink} 디버깅용
    try:
        if MEDIA_JSON.exists():
            with open(MEDIA_JSON, "r", encoding="utf-8") as f:
                media_data = json.load(f)
            for item in media_data:
                permalink = item.get("permalink")
                if permalink:
                    # instagram_media.json의 permalink는 이미 "https://www.instagram.com/reel/DQ7AdRnAcSa/" 형식
                    # shortcode만 추출하여 저장
                    shortcode = normalize_permalink(permalink)
                    if shortcode:
                        existing_permalinks_list.append(shortcode)
                        existing_permalinks_set.add(shortcode)
                        existing_permalinks_map[shortcode] = permalink
            print(f"✅ 기존 permalink {len(existing_permalinks_set)}개 로드됨 (shortcode 기준)")
            # 디버깅: 처음 5개 샘플 출력
            if existing_permalinks_list:
                sample_items = list(existing_permalinks_map.items())[:5]
                print(f"   샘플 (처음 5개):")
                for shortcode, orig_url in sample_items:
                    print(f"     - shortcode: {shortcode} | 원본: {orig_url}")
        else:
            print(f"⚠️ {MEDIA_JSON} 파일이 없습니다. 중복 체크 없이 진행합니다.")
    except Exception as e:
        print(f"⚠️ {MEDIA_JSON} 파일 로드 중 오류: {e}")
        print("  중복 체크 없이 진행합니다.")
    
    # instagram_user.json 파일 로드
    print(f"\n📂 {USER_JSON} 파일 로딩 중...")
    try:
        with open(USER_JSON, "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {USER_JSON} 파일을 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        print(f"❌ {USER_JSON} 파일의 JSON 형식이 올바르지 않습니다.")
        return []
    
    print(f"✅ {len(user_data)}개의 사용자 데이터 발견\n")
    
    # user_handle이 있는 사용자만 필터링
    users_with_handle = [user for user in user_data if user.get("user_handle")]
    print(f"📊 user_handle이 있는 사용자: {len(users_with_handle)}명\n")
    
    # 테스트 모드면 첫 번째 사용자만 처리
    if test_mode:
        users_with_handle = users_with_handle[:1]
        print(f"🧪 테스트 모드: {len(users_with_handle)}명만 처리\n")
    
    # Selenium WebDriver 초기화
    driver = setup_driver()
    
    try:
        # Instagram 로그인
        if not login_instagram(driver):
            print("❌ 로그인 실패. 스텝1을 종료합니다.")
            return []
        
        # permalink 저장용 리스트
        collected_permalinks = []
        
        # 각 사용자에 대해 반복
        for idx, user in enumerate(users_with_handle, 1):
            user_handle = user.get("user_handle")
            if not user_handle:
                continue
            
            user_id = user.get("id", "unknown")
            profile_url = f"https://www.instagram.com/{user_handle}/"
            
            print(f"\n[{idx}/{len(users_with_handle)}] 처리 중: @{user_handle} (id: {user_id})")
            print(f"  🔍 프로필 페이지 접속: {profile_url}")
            
            try:
                # 프로필 페이지 접속 전 세션 확인 및 실제 사용자처럼 행동
                print("  🔍 세션 확인 중...")
                try:
                    # 메인 페이지로 먼저 이동하여 세션 확인
                    driver.get("https://www.instagram.com")
                    time.sleep(random.uniform(2, 4))  # 랜덤 대기
                    
                    # 실제 사용자처럼 행동 (마우스 움직임, 스크롤)
                    simulate_human_behavior(driver)
                    
                    # 로그인 상태 확인
                    current_url = driver.current_url.lower()
                    if "login" in current_url or "accounts/login" in current_url:
                        print("  ⚠️ 세션이 만료되었습니다. 재로그인 시도...")
                        logging.warning(f"세션 만료 감지: {current_url}")
                        # 다시 로그인 시도
                        if not login_instagram(driver):
                            print("  ❌ 로그인 실패. 이 사용자 건너뜁니다.")
                            continue
                        # 재로그인 후 메인 페이지로 이동
                        driver.get("https://www.instagram.com")
                        time.sleep(random.uniform(2, 4))
                        # 실제 사용자처럼 행동
                        simulate_human_behavior(driver)
                except Exception as e:
                    logging.debug(f"세션 확인 중 오류: {e}")
                
                # 프로필 페이지 접속 전 자연스러운 대기
                time.sleep(random.uniform(1, 3))
                
                # 프로필 페이지 접속
                print(f"  🔍 프로필 페이지 접속: {profile_url}")
                driver.get(profile_url)
                time.sleep(random.uniform(3, 6))  # 랜덤 대기 시간
                
                # 프로필 페이지 로드 후 실제 사용자처럼 행동
                simulate_human_behavior(driver)
                
                # WebDriver 속성 숨기기 (페이지 로드 전)
                try:
                    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                        'source': '''
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                            window.navigator.chrome = {
                                runtime: {}
                            };
                            Object.defineProperty(navigator, 'plugins', {
                                get: () => [1, 2, 3, 4, 5]
                            });
                            Object.defineProperty(navigator, 'languages', {
                                get: () => ['ko-KR', 'ko', 'en-US', 'en']
                            });
                        '''
                    })
                except Exception as e:
                    logging.debug(f"WebDriver 속성 숨기기 실패: {e}")
                
                # 로그인 상태 확인 (프로필 페이지 접속 후) - 여러 번 확인
                print("  🔍 로그인 상태 확인 중...")
                max_redirect_retries = 3
                redirect_retry_count = 0
                profile_loaded = False
                
                while redirect_retry_count < max_redirect_retries:
                    try:
                        current_url = driver.current_url
                        current_url_lower = current_url.lower()
                        
                        # Challenge 페이지 감지 (가장 먼저 확인)
                        if "/challenge/" in current_url_lower:
                            print(f"  ⚠️ Instagram 보안 검증 페이지(challenge) 감지됨 ({redirect_retry_count + 1}/{max_redirect_retries})")
                            print("  💡 Instagram이 봇을 감지했습니다. 쿠키 재생성이 필요합니다.")
                            logging.warning(f"Challenge 페이지 감지: {current_url}")
                            redirect_retry_count += 1
                            
                            # 쿠키 재생성 시도
                            if not login_instagram(driver, force_regenerate=True):
                                print("  ❌ 쿠키 재생성 실패. 이 사용자 건너뜁니다.")
                                profile_loaded = False
                                break
                            
                            # 재로그인 후 메인 페이지에서 잠시 대기 (세션 안정화)
                            driver.get("https://www.instagram.com")
                            time.sleep(random.uniform(3, 5))
                            simulate_human_behavior(driver)
                            
                            # 프로필 페이지 재접속
                            driver.get(profile_url)
                            time.sleep(random.uniform(5, 7))
                            simulate_human_behavior(driver)
                            continue
                        
                        # 로그인 페이지로 리다이렉트된 경우
                        if "login" in current_url_lower or "accounts/login" in current_url:
                            redirect_retry_count += 1
                            print(f"  ⚠️ 로그인 페이지로 리다이렉트됨 ({redirect_retry_count}/{max_redirect_retries}). 재로그인 시도...")
                            logging.warning(f"프로필 페이지 접속 후 로그인 페이지로 리다이렉트됨 (시도 {redirect_retry_count}): {current_url}")
                            
                            # 다시 로그인 시도 (강제 재생성)
                            if not login_instagram(driver, force_regenerate=(redirect_retry_count >= 2)):
                                print("  ❌ 로그인 실패. 이 사용자 건너뜁니다.")
                                profile_loaded = False
                                break
                            
                            # 재로그인 후 메인 페이지에서 잠시 대기 (세션 안정화)
                            driver.get("https://www.instagram.com")
                            time.sleep(random.uniform(3, 5))
                            simulate_human_behavior(driver)
                            
                            # 프로필 페이지 재접속
                            driver.get(profile_url)
                            time.sleep(random.uniform(5, 7))  # 충분한 대기 시간
                            simulate_human_behavior(driver)
                            
                            # 재접속 후 다시 확인
                            time.sleep(2)
                            current_url_retry = driver.current_url
                            if "login" not in current_url_retry.lower() and "accounts/login" not in current_url_retry and "/challenge/" not in current_url_retry.lower():
                                print("  ✅ 프로필 페이지 접속 성공")
                                profile_loaded = True
                                break
                            else:
                                # 여전히 로그인 페이지나 challenge 페이지면 한 번 더 대기
                time.sleep(3)
                                current_url_retry = driver.current_url
                                if "login" not in current_url_retry.lower() and "accounts/login" not in current_url_retry and "/challenge/" not in current_url_retry.lower():
                                    print("  ✅ 프로필 페이지 접속 성공 (재확인)")
                                    profile_loaded = True
                                    break
                        else:
                            # 로그인 페이지도 challenge 페이지도 아니면 성공
                            profile_loaded = True
                            break
                    except Exception as e:
                        logging.debug(f"로그인 상태 확인 중 오류: {e}")
                        break
                
                if not profile_loaded:
                    print(f"  ❌ {max_redirect_retries}번 재시도 후에도 프로필 페이지 접속 실패. 이 사용자 건너뜁니다.")
                    logging.warning(f"{max_redirect_retries}번 재시도 후에도 프로필 페이지 접속 실패: {profile_url}")
                    continue
                
                # 프로필 페이지 로드 대기 (더 긴 대기 시간과 다양한 선택자 시도)
                print("  ⏳ 프로필 페이지 로드 대기 중...")
                page_loaded = False
                wait_selectors = [
                    (By.TAG_NAME, "article"),
                    (By.CSS_SELECTOR, "div[role='main']"),
                    (By.CSS_SELECTOR, "main"),
                    (By.CSS_SELECTOR, "section"),
                ]
                
                for selector_type, selector_value in wait_selectors:
                    try:
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((selector_type, selector_value))
                        )
                        print(f"  ✅ 프로필 페이지 로드 완료 ({selector_value})")
                        page_loaded = True
                        break
                except TimeoutException:
                        continue
                
                if not page_loaded:
                    print("  ⚠️ 프로필 페이지 로드 타임아웃, 계속 진행...")
                    logging.warning(f"프로필 페이지 로드 타임아웃: {profile_url}")
                
                # 추가 대기 시간 (JavaScript 렌더링 완료 대기)
                time.sleep(5)
                
                # JavaScript가 완전히 로드될 때까지 대기 (리눅스 환경 대응)
                print("  ⏳ JavaScript 렌더링 대기 중...")
                max_wait_attempts = 30  # 30초까지 대기
                content_loaded = False
                try:
                    # document.readyState가 'complete'가 될 때까지 대기
                    WebDriverWait(driver, 30).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    
                    # 추가로 React/Instagram이 로드될 때까지 대기 (최대 30초)
                    for wait_attempt in range(max_wait_attempts):
                        try:
                            # Instagram의 게시물 그리드가 로드되었는지 확인
                            has_content = driver.execute_script("""
                                // 게시물 링크가 있는지 확인
                                var links = document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]');
                                // 또는 게시물 컨테이너가 있는지 확인
                                var containers = document.querySelectorAll('article, div[role="main"] section, div._ac7v');
                                return links.length > 0 || containers.length > 0;
                            """)
                            if has_content:
                                print(f"  ✅ JavaScript 콘텐츠 로드 완료 (시도 {wait_attempt + 1}/{max_wait_attempts})")
                                content_loaded = True
                                logging.info(f"JavaScript 콘텐츠 로드 완료: {wait_attempt + 1}번째 시도")
                                break
                        except Exception as e:
                            logging.debug(f"콘텐츠 확인 중 오류 (시도 {wait_attempt + 1}): {e}")
                        time.sleep(1)
                    
                    if not content_loaded:
                        print(f"  ⚠️ {max_wait_attempts}초 동안 콘텐츠를 찾지 못했습니다.")
                        logging.warning(f"{max_wait_attempts}초 동안 콘텐츠를 찾지 못함: {profile_url}")
                except TimeoutException:
                    print("  ⚠️ JavaScript 로드 타임아웃, 계속 진행...")
                    logging.warning(f"JavaScript 로드 타임아웃: {profile_url}")
                
                # 초기 스크롤로 콘텐츠 로드 트리거 (리눅스 환경에서 중요) - 실제 사용자처럼
                print("  📜 초기 스크롤로 콘텐츠 로드 트리거...")
                for scroll_attempt in range(3):  # 3번 반복
                    try:
                        # 실제 사용자처럼 자연스러운 스크롤
                        # 페이지 하단으로 부드럽게 스크롤
                        driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                        time.sleep(random.uniform(3, 5))  # 랜덤 대기 시간
                        
                        # 마우스 움직임 시뮬레이션
                        simulate_human_behavior(driver)
                        
                        # 다시 상단으로 부드럽게 스크롤
                        driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
                        time.sleep(random.uniform(1.5, 2.5))
                        
                        # 다시 하단으로 부드럽게 스크롤
                        driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                        time.sleep(random.uniform(3, 5))
                        
                        # 마우스 움직임 시뮬레이션
                        simulate_human_behavior(driver)
                        
                        # 스크롤 후 콘텐츠 확인
                        has_content_after_scroll = driver.execute_script("""
                            var links = document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]');
                            return links.length > 0;
                        """)
                        if has_content_after_scroll:
                            print(f"  ✅ 스크롤 후 콘텐츠 발견! (시도 {scroll_attempt + 1})")
                            logging.info(f"스크롤 후 콘텐츠 발견: {scroll_attempt + 1}번째 시도")
                            break
                    except Exception as e:
                        logging.debug(f"초기 스크롤 중 오류 (시도 {scroll_attempt + 1}): {e}")
                
                # 디버깅: 페이지 구조 확인
                try:
                    # 다양한 선택자로 게시물 링크 찾기 시도
                    debug_selectors = [
                        "a[href*='/p/']",
                        "a[href*='/reel/']",
                        "article a[href*='/p/']",
                        "article a[href*='/reel/']",
                        "main a[href*='/p/']",
                        "main a[href*='/reel/']",
                        "section a[href*='/p/']",
                        "section a[href*='/reel/']",
                    ]
                    
                    print("  🔍 페이지 구조 디버깅 중...")
                    for debug_selector in debug_selectors:
                        debug_links = driver.find_elements(By.CSS_SELECTOR, debug_selector)
                        if debug_links:
                            print(f"     발견: {debug_selector} → {len(debug_links)}개 링크")
                            logging.info(f"디버깅 - {debug_selector}: {len(debug_links)}개 링크 발견")
                except Exception as e:
                    logging.debug(f"디버깅 중 오류: {e}")
                
                # 게시물 href 수집 (원본 URL과 shortcode 매핑 저장)
                collected_hrefs_map = {}  # {shortcode: original_url} - 원본 URL 보존
                collected_shortcodes = set()  # 중복 체크용 shortcode set
                previous_div_count = 0
                previous_href_count = 0
                no_new_content_count = 0
                max_no_new_content = 5  # 연속으로 새 콘텐츠(div 또는 href)가 생성되지 않으면 종료 (3 -> 5로 증가)
                scroll_count = 0
                
                print("  📜 스크롤하며 href 수집 시작...")
                print("  📊 초기 상태 확인 중...")
                
                while True:
                    scroll_count += 1
                    
                    # 스크롤 루프 시작 전 로그인 상태 확인 (매번 확인)
                    try:
                        current_url = driver.current_url.lower()
                        if "login" in current_url or "accounts/login" in current_url:
                            print(f"  ⚠️ 스크롤 중 로그인 페이지로 리다이렉트됨. 재로그인 시도...")
                            logging.warning(f"스크롤 중 로그인 페이지로 리다이렉트됨: {driver.current_url}")
                            # 다시 로그인 시도
                            if not login_instagram(driver):
                                print("  ❌ 로그인 실패. 이 사용자 건너뜁니다.")
                                break
                            # 재로그인 후 프로필 페이지 재접속
                            driver.get(profile_url)
                            time.sleep(5)
                            # 페이지 로드 대기
                            WebDriverWait(driver, 20).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "main"))
                            )
                            time.sleep(3)
                    except Exception as e:
                        logging.debug(f"스크롤 중 로그인 상태 확인 오류: {e}")
                    
                    # 현재 페이지에서 div 개수와 href 수집
                    try:
                        # 다양한 선택자로 게시물 링크 찾기 (우선순위 순)
                        post_links = []
                        
                        # 방법 1: 가장 구체적인 선택자
                        selectors = [
                            "div._ac7v.x1ty9z65.xzboxd6 div.x1lliihq.x1n2onr6.xh8yej3.x4gyw5p.x14z9mp.xhe4ym4.xaudc5v.x1j53mea a[href*='/p/']",
                            "div._ac7v.x1ty9z65.xzboxd6 div.x1lliihq.x1n2onr6.xh8yej3.x4gyw5p.x14z9mp.xhe4ym4.xaudc5v.x1j53mea a[href*='/reel/']",
                            "div._ac7v a[href*='/p/']",
                            "div._ac7v a[href*='/reel/']",
                            "article a[href*='/p/']",
                            "article a[href*='/reel/']",
                            "main a[href*='/p/']",
                            "main a[href*='/reel/']",
                            "section a[href*='/p/']",
                            "section a[href*='/reel/']",
                            "a[href*='/p/']",
                            "a[href*='/reel/']",
                        ]
                        
                        for selector in selectors:
                            try:
                                found_links = driver.find_elements(By.CSS_SELECTOR, selector)
                                if found_links:
                                    post_links = found_links
                                    if scroll_count == 1:  # 첫 번째 스크롤에서만 로그
                                        print(f"  ✅ 선택자 성공: {selector[:50]}... → {len(found_links)}개 링크")
                                        logging.info(f"작동하는 선택자 발견: {selector} → {len(found_links)}개")
                                    break
                            except Exception:
                                continue
                        
                        # div 개수 확인 (다양한 선택자 시도)
                        post_divs = []
                        div_selectors = [
                            "div._ac7v.x1ty9z65.xzboxd6",
                            "div._ac7v",
                            "article > div > div",
                            "main > section > div",
                        ]
                        
                        for div_selector in div_selectors:
                            try:
                                found_divs = driver.find_elements(By.CSS_SELECTOR, div_selector)
                                if found_divs:
                                    post_divs = found_divs
                                    break
                            except Exception:
                                continue
                        
                        current_div_count = len(post_divs)
                        
                        # href 수집
                        new_hrefs_count = 0
                        
                        # 첫 번째 스크롤에서 링크를 찾지 못한 경우 디버깅 정보 출력 및 JavaScript로 시도
                        if scroll_count == 1 and not post_links:
                            print("  ⚠️ 첫 번째 스크롤에서 게시물 링크를 찾지 못했습니다.")
                            logging.warning(f"프로필 페이지에서 게시물 링크를 찾지 못함: {profile_url}")
                            
                            # 페이지 소스 일부 확인
                            try:
                                page_source = driver.page_source
                                has_p_links = '/p/' in page_source or '/reel/' in page_source
                                has_article = '<article' in page_source
                                has_main = '<main' in page_source
                                
                                # 추가 디버깅: Instagram GraphQL 데이터 확인
                                has_graphql_data = False
                                try:
                                    graphql_data = driver.execute_script("""
                                        // Instagram의 GraphQL 데이터 확인
                                        var scripts = document.querySelectorAll('script[type="application/json"]');
                                        for (var i = 0; i < scripts.length; i++) {
                                            try {
                                                var data = JSON.parse(scripts[i].textContent);
                                                var jsonStr = JSON.stringify(data);
                                                if (jsonStr.includes('"shortcode"') || jsonStr.includes('/p/') || jsonStr.includes('/reel/')) {
                                                    return true;
                                                }
                                            } catch(e) {}
                                        }
                                        return false;
                                    """)
                                    has_graphql_data = graphql_data
                                except:
                                    pass
                                
                                print(f"  🔍 페이지 소스 확인:")
                                print(f"     - /p/ 또는 /reel/ 포함: {has_p_links}")
                                print(f"     - article 태그: {has_article}")
                                print(f"     - main 태그: {has_main}")
                                print(f"     - GraphQL 데이터: {has_graphql_data}")
                                print(f"     - 현재 URL: {driver.current_url}")
                                logging.info(f"페이지 소스 확인 - /p/ 또는 /reel/: {has_p_links}, article: {has_article}, main: {has_main}, GraphQL: {has_graphql_data}, URL: {driver.current_url}")
                                
                                # JavaScript로 직접 링크 찾기 시도 (페이지 소스에 없어도 DOM에는 있을 수 있음)
                                js_links = driver.execute_script("""
                                    var links = document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]');
                                    var result = [];
                                    for (var i = 0; i < links.length; i++) {
                                        var href = links[i].href || links[i].getAttribute('href');
                                        if (href && (href.includes('/p/') || href.includes('/reel/'))) {
                                            // 상대 경로를 절대 경로로 변환
                                            if (href.startsWith('/')) {
                                                href = 'https://www.instagram.com' + href;
                                            }
                                            result.push(href);
                                        }
                                    }
                                    return result;
                                """)
                                
                                if js_links and len(js_links) > 0:
                                    print(f"  ✅ JavaScript로 {len(js_links)}개 링크 발견!")
                                    logging.info(f"JavaScript로 {len(js_links)}개 링크 발견")
                                    # JavaScript로 찾은 링크를 직접 처리
                                    for js_link in js_links:
                                        if not js_link or not isinstance(js_link, str):
                                            continue
                                        if js_link.startswith("/"):
                                            js_link = "https://www.instagram.com" + js_link
                                        elif not js_link.startswith("http"):
                                            continue
                                        
                                        if "/p/" in js_link or "/reel/" in js_link:
                                            shortcode = normalize_permalink(js_link)
                                            if shortcode and shortcode not in collected_shortcodes:
                                                collected_shortcodes.add(shortcode)
                                                collected_hrefs_map[shortcode] = js_link
                                                new_hrefs_count += 1
                                elif has_p_links:
                                    # 페이지 소스에는 있지만 DOM에는 없는 경우 (아직 렌더링 안 됨)
                                    print(f"  ⏳ 페이지 소스에는 링크가 있지만 DOM에는 없습니다. 추가 대기 중...")
                                    time.sleep(5)
                                    # 다시 시도
                                    js_links_retry = driver.execute_script("""
                                        var links = document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]');
                                        var result = [];
                                        for (var i = 0; i < links.length; i++) {
                                            var href = links[i].href || links[i].getAttribute('href');
                                            if (href && (href.includes('/p/') || href.includes('/reel/'))) {
                                                if (href.startsWith('/')) {
                                                    href = 'https://www.instagram.com' + href;
                                                }
                                                result.push(href);
                                            }
                                        }
                                        return result;
                                    """)
                                    if js_links_retry and len(js_links_retry) > 0:
                                        print(f"  ✅ 재시도 후 {len(js_links_retry)}개 링크 발견!")
                                        for js_link in js_links_retry:
                                            if not js_link or not isinstance(js_link, str):
                                                continue
                                            if js_link.startswith("/"):
                                                js_link = "https://www.instagram.com" + js_link
                                            elif not js_link.startswith("http"):
                                                continue
                                            
                                            if "/p/" in js_link or "/reel/" in js_link:
                                                shortcode = normalize_permalink(js_link)
                                                if shortcode and shortcode not in collected_shortcodes:
                                                    collected_shortcodes.add(shortcode)
                                                    collected_hrefs_map[shortcode] = js_link
                                                    new_hrefs_count += 1
                            except Exception as debug_e:
                                logging.debug(f"디버깅 정보 수집 실패: {debug_e}", exc_info=True)
                        for link in post_links:
                            href = link.get_attribute("href")
                            if href:
                                # href가 상대 경로일 수 있으므로 절대 URL로 변환
                                if href.startswith("/"):
                                    href = "https://www.instagram.com" + href
                                elif not href.startswith("http"):
                                    # shortcode만 있는 경우는 건너뜀
                                    continue
                                
                                if "/p/" in href or "/reel/" in href:
                                    # shortcode 추출
                                    shortcode = normalize_permalink(href)
                                    if shortcode:
                                        if shortcode not in collected_shortcodes:
                                            collected_shortcodes.add(shortcode)
                                            collected_hrefs_map[shortcode] = href
                                            new_hrefs_count += 1
                                    else:
                                        # 파싱 실패한 경우 원본 href 출력 (디버깅용)
                                        if new_hrefs_count == 0:  # 첫 번째 실패만 출력
                                            print(f"     ⚠️ shortcode 파싱 실패 - 원본 href: {href}")
                        
                        current_href_count = len(collected_shortcodes)
                        
                        # 터미널 로그 출력
                        print(f"  📊 스크롤 #{scroll_count} | div: {current_div_count}개 | href: {current_href_count}개 (새로 추가: {new_hrefs_count}개)")
                        
                        # div와 href 둘 다 변하지 않았는지 확인 (더 정확한 종료 조건)
                        div_changed = current_div_count != previous_div_count
                        href_changed = current_href_count != previous_href_count
                        
                        if not div_changed and not href_changed:
                            # div와 href 둘 다 변하지 않음
                            no_new_content_count += 1
                            print(f"  ⏸️ 새 콘텐츠 없음 (연속 {no_new_content_count}회)")
                            
                            if no_new_content_count >= max_no_new_content:
                                print(f"  ✅ 더 이상 새 콘텐츠가 없습니다. (연속 {max_no_new_content}회 동일)")
                                print(f"  ✅ 최종 수집 완료: {current_href_count}개의 href 수집됨")
                                break
                        else:
                            # div 또는 href가 변했으면 카운터 리셋
                            no_new_content_count = 0
                            if div_changed:
                                print(f"  📈 div 개수 증가: {previous_div_count} -> {current_div_count}")
                            if href_changed:
                                print(f"  📈 href 개수 증가: {previous_href_count} -> {current_href_count}")
                        
                        previous_div_count = current_div_count
                        previous_href_count = current_href_count
                        
                    except Exception as e:
                        print(f"  ⚠️ href 수집 중 오류: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # 스크롤 다운 (스크롤 이벤트) - 실제 사용자처럼 자연스러운 스크롤
                    try:
                        # 점진적으로 스크롤 (로딩 시간 확보)
                        current_scroll = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
                        scroll_height = driver.execute_script("return document.body.scrollHeight;")
                        
                        # 여러 단계로 나누어 스크롤 (더 많은 단계로)
                        scroll_steps = random.randint(4, 7)  # 랜덤한 스크롤 단계
                        scroll_increment = (scroll_height - current_scroll) / scroll_steps
                        
                        for step in range(scroll_steps):
                            scroll_position = current_scroll + scroll_increment * (step + 1)
                            # 자연스러운 스크롤 (부드러운 애니메이션)
                            driver.execute_script(f"""
                                window.scrollTo({{
                                    top: {scroll_position},
                                    behavior: 'smooth'
                                }});
                            """)
                            # 랜덤한 대기 시간 (실제 사용자처럼)
                            time.sleep(random.uniform(1.5, 3.0))
                            
                            # 가끔 마우스 움직임 시뮬레이션
                            if random.random() < 0.3:  # 30% 확률
                                simulate_human_behavior(driver)
                        
                        # 최종적으로 페이지 끝까지 스크롤
                        driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                        time.sleep(random.uniform(3, 5))  # 랜덤 대기 시간
                        
                        # 실제 사용자처럼 가끔 위로 스크롤
                        if random.random() < 0.4:  # 40% 확률
                            scroll_back = random.randint(100, 300)
                            driver.execute_script(f"window.scrollBy({{top: -{scroll_back}, behavior: 'smooth'}});")
                            time.sleep(random.uniform(1, 2))
                            driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                            time.sleep(random.uniform(2, 4))
                    except Exception as e:
                        print(f"  ⚠️ 스크롤 중 오류: {e}")
                        break
                
                # 기존 permalink 리스트와 비교하여 중복 제거
                new_permalinks = []
                duplicate_count = 0
                duplicate_samples = []  # 디버깅용
                collected_samples = []  # 디버깅용: 수집한 permalink 샘플
                
                # collected_hrefs_map에는 이미 {shortcode: original_url} 형태로 저장되어 있음
                # 디버깅: 처음 5개 샘플 저장
                for idx, (shortcode, original_url) in enumerate(list(collected_hrefs_map.items())[:5]):
                    collected_samples.append(f"shortcode: {shortcode} | 원본: {original_url}")
                
                # 기존 permalink 리스트와 비교 (shortcode 기준)
                for shortcode, original_url in collected_hrefs_map.items():
                    if shortcode not in existing_permalinks_set:
                        # 신규 permalink (원본 URL 저장)
                        new_permalinks.append({
                            "user_id": user_id,
                            "user_handle": user_handle,
                            "permalink": original_url
                        })
                    else:
                        # 중복 permalink
                        duplicate_count += 1
                        # 디버깅: 처음 5개 중복 샘플 저장
                        if len(duplicate_samples) < 5:
                            existing_orig = existing_permalinks_map.get(shortcode, "알 수 없음")
                            duplicate_samples.append(f"shortcode: {shortcode} | 수집한: {original_url} | 기존: {existing_orig}")
                
                # 수집된 href를 리스트에 추가 (중복 제거된 것만)
                collected_permalinks.extend(new_permalinks)
                
                # 터미널 로그 출력
                print(f"  ✅ @{user_handle}:")
                print(f"     - 총 수집: {len(collected_shortcodes)}개")
                if collected_samples:
                    print(f"     - 수집한 permalink 샘플 (처음 5개):")
                    for sample in collected_samples:
                        print(f"       {sample}")
                print(f"     - 중복 제거: {duplicate_count}개")
                if duplicate_samples:
                    print(f"     - 중복 permalink 샘플 (처음 5개):")
                    for sample in duplicate_samples:
                        print(f"       {sample}")
                print(f"     - 신규 permalink: {len(new_permalinks)}개")
                
                # 테스트 모드면 첫 번째 사용자만 처리하고 종료
                if test_mode:
                    break
                
                # 요청 간 딜레이 (Instagram 차단 방지) - 실제 사용자처럼 랜덤 대기
                wait_time = random.uniform(3, 7)  # 3-7초 랜덤 대기
                print(f"  ⏳ 다음 사용자 처리 전 대기 중... ({wait_time:.1f}초)")
                time.sleep(wait_time)
                
                # 대기 중에도 실제 사용자처럼 행동 (메인 페이지로 이동 후 행동)
                try:
                    driver.get("https://www.instagram.com")
                    time.sleep(random.uniform(1, 2))
                    simulate_human_behavior(driver)
                except Exception as e:
                    logging.debug(f"대기 중 행동 시뮬레이션 오류: {e}")
                
            except Exception as e:
                print(f"  ❌ 프로필 페이지 처리 중 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # handle별 통계 계산
        handle_stats = {}
        for item in collected_permalinks:
            handle = item['user_handle']
            if handle not in handle_stats:
                handle_stats[handle] = 0
            handle_stats[handle] += 1
        
        print(f"\n{'='*60}")
        print(f"✅ 스텝1 완료!")
        print(f"   총 수집된 신규 permalink: {len(collected_permalinks)}개")
        print(f"\n📊 handle별 신규 permalink 개수:")
        for handle, count in sorted(handle_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   - @{handle}: {count}개")
        print(f"{'='*60}")
        
        # 로그에도 통계 기록
        logging.info("=" * 80)
        logging.info("스텝1 완료 - instagram_crawling_userposts.py")
        logging.info(f"총 수집된 신규 permalink: {len(collected_permalinks)}개")
        for handle, count in sorted(handle_stats.items(), key=lambda x: x[1], reverse=True):
            logging.info(f"handle별 신규 permalink - @{handle}: {count}개")
        logging.info("=" * 80)
        
        return collected_permalinks
        
    finally:
        driver.quit()
        print("\n🔒 브라우저 종료")

# ============================================
# 스텝2: 수집한 permalink 처리
# ============================================
def step2_process_permalinks(permalinks, test_mode=False):
    """
    스텝2: step1에서 수집한 permalink를 하나씩 방문하여 처리
    - 각 permalink에 접속
    - 본문에서 특정 단어 리스트 확인
    - 단어가 없으면 스킵, 있으면 데이터 수집
    
    Args:
        permalinks: step1에서 반환한 permalink 리스트
                   [{"user_id": "...", "user_handle": "...", "permalink": "..."}, ...]
        test_mode: 테스트 모드 (True면 상위 3개만 처리)
    """
    # 로깅 초기화 (스텝1에서 이미 설정되었을 수 있지만, 다시 설정하여 확실히 함)
    setup_logging(str(LOG_PATH))
    logging.info("=" * 80)
    logging.info("프로그램 시작 - instagram_crawling_userposts.py (스텝2)")
    if test_mode:
        logging.info("테스트 모드: 상위 3개만 처리")
    logging.info(f"처리할 permalink 개수: {len(permalinks)}")
    logging.info("=" * 80)
    
    print("=" * 60)
    print("스텝2: 수집한 permalink 처리 시작")
    if test_mode:
        print("🧪 테스트 모드: 상위 3개만 처리합니다")
    print("=" * 60)
    
    if not permalinks:
        print("⚠️ 처리할 permalink가 없습니다.")
        return
    
    # 테스트 모드면 상위 3개만 처리
    if test_mode:
        permalinks = permalinks[:3]
        print(f"\n🧪 테스트 모드: 상위 3개만 처리합니다")
    
    print(f"\n📊 {len(permalinks)}개의 permalink 처리 시작...")
    
    # ============================================
    # ============================================
    # 필터링할 단어 리스트 (해시태그에 이 단어들이 없으면 스킵)
    # ============================================
    # ⬇️ 여기에 필터 단어를 추가/수정하세요 ⬇️
    filter_words = [
        "#독일피엠",
        "#독일PM",
        "#독일 PM",
        "#PM",
        "#피엠",
        "#피엠코리아",
        "#피트라인",
        "Fitline",
        "#액티바이즈",
        "#부산피엠",
        "#파워칵테일",
        "#리스토레이트",
        "#탑쉐이프",
    ]
    # ⬆️ 필터 단어 리스트 끝 ⬆️
    
    print(f"📝 필터 단어 리스트: {filter_words}")
    print(f"   (해시태그에 이 단어들이 없으면 스킵합니다)\n")
    
    # Selenium WebDriver 초기화
    driver = setup_driver()
    
    try:
        # Instagram 로그인
        if not login_instagram(driver):
            print("❌ 로그인 실패. 스텝2를 종료합니다.")
            return
        
        # 처리 통계
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        # 각 permalink에 대해 반복문 처리
        for idx, item in enumerate(permalinks, 1):
            user_id = item.get("user_id")
            user_handle = item.get("user_handle")
            permalink = item.get("permalink")
            
            if not permalink:
                skipped_count += 1
                print(f"[{idx}/{len(permalinks)}] ⚠️ permalink가 없습니다. 건너뜁니다.")
                continue
            
            print(f"\n[{idx}/{len(permalinks)}] 처리 중: @{user_handle}")
            print(f"  🔍 접속 중: {permalink}")
            logging.info(f"[{idx}/{len(permalinks)}] 처리 중: @{user_handle}, permalink: {permalink}")
            
            try:
                # permalink 페이지 접속
                driver.get(permalink)
                time.sleep(3)
                
                # 페이지 로드 대기
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "article"))
                    )
                    print("  ✅ 페이지 로드 완료")
                except TimeoutException:
                    print("  ⚠️ 페이지 로드 타임아웃, 계속 진행...")
                
                # 추가 대기 및 스크롤 (콘텐츠 로드를 위해)
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 비디오 로드를 위해 대기 시간 증가
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)  # 비디오 로드를 위해 대기 시간 증가
                
                # 1. handle 추출
                handle = ""
                try:
                    handle_element = driver.find_element(By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade")
                    handle = handle_element.text.strip()
                    print(f"  👤 handle: {handle}")
                except NoSuchElementException:
                    print(f"  ⚠️ handle을 찾을 수 없습니다.")
                
                # 2. content와 hashtags 추출
                content = ""
                hashtags = []
                try:
                    # content와 hashtags가 있는 div 찾기
                    content_div = driver.find_element(By.CSS_SELECTOR, "div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x9f619.xjbqb8w.x78zum5.x15mokao.x1ga7v0g.x16uus16.xbiv7yw.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1")
                    
                    # 전체 텍스트 가져오기
                    full_text = content_div.text
                    
                    # hashtags 추출 (<a> 태그에서)
                    hashtag_links = content_div.find_elements(By.CSS_SELECTOR, "a")
                    for link in hashtag_links:
                        href = link.get_attribute("href")
                        if href and "/explore/tags/" in href:
                            hashtag_text = link.text.strip()
                            if hashtag_text and hashtag_text.startswith("#"):
                                hashtags.append(hashtag_text)
                    
                    # content 추출: hashtag를 제외한 본문 텍스트
                    # HTML에서 직접 추출하여 <br>과 &nbsp; 제거
                    try:
                        # innerHTML 가져오기
                        inner_html = driver.execute_script("""
                            var div = arguments[0];
                            return div.innerHTML;
                        """, content_div)
                        
                        # BeautifulSoup 없이 간단한 정규식으로 처리
                        # <br> 태그를 공백으로 변환
                        inner_html = re.sub(r'<br\s*/?>', ' ', inner_html, flags=re.IGNORECASE)
                        # &nbsp;를 공백으로 변환
                        inner_html = inner_html.replace('&nbsp;', ' ')
                        # HTML 태그 제거
                        inner_html = re.sub(r'<[^>]+>', '', inner_html)
                        # 여러 공백을 하나로
                        inner_html = re.sub(r'\s+', ' ', inner_html)
                        # 앞뒤 공백 제거
                        content = inner_html.strip()
                        
                        # hashtag 제거 (content에서)
                        for tag in hashtags:
                            content = content.replace(tag, '').strip()
                        content = re.sub(r'\s+', ' ', content).strip()
                        
                    except Exception as e:
                        print(f"  ⚠️ HTML 파싱 실패, 텍스트로 대체: {e}")
                        # 대체 방법: 텍스트에서 hashtag 제거
                        content = full_text
                        for tag in hashtags:
                            content = content.replace(tag, '').strip()
                    
                    print(f"  📝 content: {content[:100]}...")
                    print(f"  🏷️ hashtags: {len(hashtags)}개")
                    
                except NoSuchElementException:
                    print(f"  ⚠️ content div를 찾을 수 없습니다.")
                
                # 3. content_count와 hashtag_count 계산
                content_count = len(content) if content else 0
                hashtag_count = len(hashtags)
                print(f"  📊 content_count: {content_count}, hashtag_count: {hashtag_count}")
                
                # 필터 단어 확인 (hashtags에서)
                # hashtags 리스트를 문자열로 변환하여 확인
                hashtags_text = " ".join(hashtags) if hashtags else ""
                has_filter_word = any(word in hashtags_text for word in filter_words) if hashtags_text else False
                
                if not has_filter_word:
                    # 필터 단어가 하나도 없으면 스킵
                    skipped_count += 1
                    print(f"  ⏭️ 해시태그에 필터 단어가 하나도 없어 스킵합니다.")
                    print(f"     (해시태그: {hashtags if hashtags else '(없음)'})")
                    continue
                
                # 필터 단어가 하나라도 있으면 데이터 수집 진행
                print(f"  ✅ 필터 단어 발견! (해시태그에 하나라도 있음) 데이터 수집 진행...")
                
                # 4. media_type 판단
                media_type = "IMAGE"
                if "reel" in permalink.lower():
                    media_type = "VIDEO"
                    print(f"  🎬 media_type: VIDEO (reel 감지)")
                    # VIDEO 타입인 경우 비디오가 로드될 때까지 추가 대기
                    print("  ⏳ 비디오 로딩 대기 중...")
                    try:
                        # video 요소가 나타날 때까지 대기
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "video"))
                        )
                        print("  ✅ 비디오 요소 발견")
                        # 비디오가 실제로 로드될 때까지 추가 대기
                        time.sleep(3)
                    except TimeoutException:
                        print("  ⚠️ 비디오 요소를 찾을 수 없습니다. 계속 진행...")
                else:
                    # li 태그 확인 (CAROUSEL_ALBUM 판단)
                    try:
                        li_elements = driver.find_elements(By.CSS_SELECTOR, "li._acaz, li[class*='_acaz']")
                        if li_elements:
                            media_type = "CAROUSEL_ALBUM"
                            print(f"  🖼️ media_type: CAROUSEL_ALBUM (li 태그 {len(li_elements)}개 발견)")
                        else:
                            print(f"  🖼️ media_type: IMAGE")
                    except Exception:
                        print(f"  🖼️ media_type: IMAGE (기본값)")
                
                # 5. media_url 추출 (instagram_extract_imgurl.py 로직 참고)
                media_urls = []
                seen_urls = set()
                
                print(f"  🔍 media_url 추출 시작 (media_type: {media_type})")
                
                try:
                    # CAROUSEL_ALBUM인 경우 li 요소에서 찾기
                    if media_type == "CAROUSEL_ALBUM":
                        print(f"  🔍 CAROUSEL_ALBUM: li 요소 검색 중...")
                        # li._acaz 요소 찾기 (여러 셀렉터 시도)
                        li_elements = []
                        selectors = [
                            "li._acaz",
                            "li[class*='_acaz']",
                            "article li",
                            "div[role='dialog'] li",
                            "ul li",
                            "div[class*='carousel'] li",
                        ]
                        
                        for selector in selectors:
                            try:
                                li_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if li_elements:
                                    print(f"  🔍 셀렉터 '{selector}'로 발견된 li 요소 개수: {len(li_elements)}")
                                    break
                            except Exception as e:
                                print(f"  ⚠️ 셀렉터 '{selector}' 시도 실패: {e}")
                                continue
                        
                        if not li_elements:
                            print(f"  ⚠️ li 요소를 찾을 수 없습니다.")
                        
                        if li_elements:
                            # 각 li 요소 내에서 img src와 video src 찾기 (첫 번째만)
                            for li in li_elements[:1]:  # 첫 번째만
                                try:
                                    # 이미지 찾기 (여러 셀렉터 시도)
                                    img = None
                                    img_selectors = [
                                        "div._aagu div._aagv img",
                                        "div._aagu img",
                                        "div[class*='_aagu'] img",
                                        "img",
                                    ]
                                    
                                    for img_selector in img_selectors:
                                        try:
                                            img = li.find_element(By.CSS_SELECTOR, img_selector)
                                            break
                                        except NoSuchElementException:
                                            continue
                                    
                                    if img:
                                        img_src = img.get_attribute("src")
                                        if not img_src:
                                            img_src = img.get_attribute("data-src")
                                        
                                        if img_src and ("scontent" in img_src or "cdninstagram" in img_src) and img_src not in seen_urls:
                                            seen_urls.add(img_src)
                                            media_urls.append(img_src)
                                            print(f"  ✅ 이미지 URL 추가: {img_src[:80]}...")
                                            break  # 첫 번째만 수집
                                    
                                    # 비디오 찾기 (이미지가 없는 경우)
                                    if not media_urls:
                                        video = None
                                        video_selectors = [
                                            "video",
                                            "div._aagu video",
                                            "div[class*='_aagu'] video",
                                            "div._aagu div._aagv video",
                                        ]
                                        
                                        for video_selector in video_selectors:
                                            try:
                                                video = li.find_element(By.CSS_SELECTOR, video_selector)
                                                break
                                            except NoSuchElementException:
                                                continue
                                        
                                        if video:
                                            actual_video_url = None
                                            
                                            # 1. currentSrc 확인 (실제 재생 중인 비디오 URL, 우선순위 높음)
                                            try:
                                                current_src = driver.execute_script("return arguments[0].currentSrc;", video)
                                                if current_src and not current_src.startswith('blob:') and current_src not in seen_urls:
                                                    actual_video_url = current_src
                                                    print(f"  ✅ 비디오 URL 발견 (currentSrc): {actual_video_url[:80]}...")
                                            except Exception:
                                                pass
                                            
                                            # 2. src 확인
                                            if not actual_video_url:
                                                video_src = video.get_attribute("src")
                                                if video_src and not video_src.startswith('blob:') and video_src not in seen_urls:
                                                    actual_video_url = video_src
                                                    print(f"  ✅ 비디오 URL 발견 (src): {actual_video_url[:80]}...")
                                            
                                            # 3. data-src 확인
                                            if not actual_video_url:
                                                video_data_src = video.get_attribute("data-src")
                                                if video_data_src and not video_data_src.startswith('blob:') and video_data_src not in seen_urls:
                                                    actual_video_url = video_data_src
                                                    print(f"  ✅ 비디오 URL 발견 (data-src): {actual_video_url[:80]}...")
                                            
                                            # 4. source 태그 확인
                                            if not actual_video_url:
                                                try:
                                                    sources = video.find_elements(By.CSS_SELECTOR, "source")
                                                    for source in sources:
                                                        source_src = source.get_attribute("src")
                                                        if source_src and not source_src.startswith('blob:') and source_src not in seen_urls:
                                                            actual_video_url = source_src
                                                            print(f"  ✅ 비디오 URL 발견 (source): {actual_video_url[:80]}...")
                                                            break
                                                except NoSuchElementException:
                                                    pass
                                            
                                            # URL이 발견되면 추가
                                            if actual_video_url:
                                                seen_urls.add(actual_video_url)
                                                media_urls.append(actual_video_url)
                                                print(f"  ✅ 비디오 URL 추가: {actual_video_url[:80]}...")
                                                break  # 첫 번째만 수집
                                    
                                except Exception as e:
                                    print(f"  ⚠️ li 요소 처리 중 오류: {e}")
                                    continue
                    
                    # IMAGE나 VIDEO 타입이거나 li 요소를 찾지 못한 경우
                    if not media_urls:
                        print(f"  🔍 article 또는 전체 페이지에서 검색 중...")
                        # article 내에서 또는 전체 페이지에서 찾기
                        article = None
                        try:
                            article = driver.find_element(By.TAG_NAME, "article")
                            print(f"  🔍 article 요소 발견")
                        except NoSuchElementException:
                            print(f"  ⚠️ article 요소를 찾을 수 없습니다. 전체 페이지에서 검색합니다.")
                        
                        # 이미지 찾기 (VIDEO 타입이 아닌 경우만)
                        if media_type != "VIDEO":
                            if article:
                                img_elements = article.find_elements(By.CSS_SELECTOR, "img")
                                print(f"  🔍 article 내 img 요소 개수: {len(img_elements)}")
                            else:
                                img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
                                print(f"  🔍 전체 페이지 img 요소 개수: {len(img_elements)}")
                            
                            if not img_elements:
                                print(f"  ⚠️ img 요소를 찾을 수 없습니다.")
                            
                            for img in img_elements:
                                img_src = img.get_attribute("src")
                                if not img_src:
                                    img_src = img.get_attribute("data-src")
                                
                                # scontent나 cdninstagram이 포함된 URL만 (인스타그램 CDN 이미지)
                                if img_src and ("scontent" in img_src or "cdninstagram" in img_src) and img_src not in seen_urls:
                                    seen_urls.add(img_src)
                                    media_urls.append(img_src)
                                    print(f"  ✅ 이미지 URL 추가: {img_src[:80]}...")
                                    # IMAGE 타입이면 첫 번째만 수집
                                    if media_type == "IMAGE":
                                        break
                        
                        # 비디오 찾기 (VIDEO 타입이거나 이미지가 없는 경우)
                        # instagram_extract_voice.py의 로직 참고: currentSrc, src, source 태그 순서로 확인
                        if media_type == "VIDEO" or not media_urls:
                            if article:
                                video_elements = article.find_elements(By.CSS_SELECTOR, "video")
                                print(f"  🔍 article 내 video 요소 개수: {len(video_elements)}")
                            else:
                                video_elements = driver.find_elements(By.CSS_SELECTOR, "video")
                                print(f"  🔍 전체 페이지 video 요소 개수: {len(video_elements)}")
                            
                            if not video_elements:
                                print(f"  ⚠️ video 요소를 찾을 수 없습니다.")
                            
                            for video_idx, video in enumerate(video_elements, 1):
                                print(f"  🔍 video 요소 #{video_idx} 분석 중...")
                                actual_video_url = None
                                
                                # 1. currentSrc 확인 (실제 재생 중인 비디오 URL, 우선순위 높음)
                                try:
                                    current_src = driver.execute_script("return arguments[0].currentSrc;", video)
                                    print(f"    currentSrc: {current_src[:100] if current_src else 'None'}...")
                                    if current_src:
                                        if current_src.startswith('blob:'):
                                            print(f"    ⚠️ currentSrc는 blob URL입니다.")
                                        elif current_src in seen_urls:
                                            print(f"    ⚠️ currentSrc는 이미 수집된 URL입니다.")
                                        else:
                                            actual_video_url = current_src
                                            print(f"  ✅ 비디오 URL 발견 (currentSrc): {actual_video_url[:80]}...")
                                except Exception as e:
                                    print(f"    ⚠️ currentSrc 확인 중 오류: {e}")
                                
                                # 2. src 확인
                                if not actual_video_url:
                                    video_src = video.get_attribute("src")
                                    print(f"    src: {video_src[:100] if video_src else 'None'}...")
                                    if video_src:
                                        if video_src.startswith('blob:'):
                                            print(f"    ⚠️ src는 blob URL입니다.")
                                        elif video_src in seen_urls:
                                            print(f"    ⚠️ src는 이미 수집된 URL입니다.")
                                        else:
                                            actual_video_url = video_src
                                            print(f"  ✅ 비디오 URL 발견 (src): {actual_video_url[:80]}...")
                                
                                # 3. data-src 확인
                                if not actual_video_url:
                                    video_data_src = video.get_attribute("data-src")
                                    print(f"    data-src: {video_data_src[:100] if video_data_src else 'None'}...")
                                    if video_data_src:
                                        if video_data_src.startswith('blob:'):
                                            print(f"    ⚠️ data-src는 blob URL입니다.")
                                        elif video_data_src in seen_urls:
                                            print(f"    ⚠️ data-src는 이미 수집된 URL입니다.")
                                        else:
                                            actual_video_url = video_data_src
                                            print(f"  ✅ 비디오 URL 발견 (data-src): {actual_video_url[:80]}...")
                                
                                # 4. source 태그 확인
                                if not actual_video_url:
                                    try:
                                        sources = video.find_elements(By.CSS_SELECTOR, "source")
                                        print(f"    source 태그 개수: {len(sources)}")
                                        for source_idx, source in enumerate(sources, 1):
                                            source_src = source.get_attribute("src")
                                            print(f"      source #{source_idx} src: {source_src[:100] if source_src else 'None'}...")
                                            if source_src:
                                                if source_src.startswith('blob:'):
                                                    print(f"        ⚠️ source src는 blob URL입니다.")
                                                elif source_src in seen_urls:
                                                    print(f"        ⚠️ source src는 이미 수집된 URL입니다.")
                                                else:
                                                    actual_video_url = source_src
                                                    print(f"  ✅ 비디오 URL 발견 (source): {actual_video_url[:80]}...")
                                                    break
                                    except NoSuchElementException:
                                        print(f"    ⚠️ source 태그를 찾을 수 없습니다.")
                                    except Exception as e:
                                        print(f"    ⚠️ source 태그 확인 중 오류: {e}")
                                
                                # 5. blob URL인 경우 JavaScript 변수에서 실제 비디오 URL 찾기 (instagram_extract_voice.py 참고)
                                if not actual_video_url:
                                    print(f"    🔍 blob URL이므로 JavaScript 변수에서 실제 비디오 URL 검색 중...")
                                    try:
                                        js_video_url = driver.execute_script("""
                                            // Instagram의 React/GraphQL 데이터에서 비디오 URL 찾기
                                            var videoUrl = null;
                                            
                                            // window 객체에서 찾기
                                            if (window.__initialDataLoaded || window._sharedData) {
                                                try {
                                                    var data = window.__initialDataLoaded || window._sharedData;
                                                    var jsonStr = JSON.stringify(data);
                                                    // video URL 패턴 찾기 (scontent 또는 cdninstagram 포함)
                                                    var match = jsonStr.match(/https?:\/\/[^"\\s]*(?:scontent|cdninstagram)[^"\\s]*\\.(mp4|webm|m3u8)/i);
                                                    if (match) {
                                                        videoUrl = match[0];
                                                    }
                                                } catch(e) {}
                                            }
                                            
                                            // document에서 script 태그의 JSON 데이터 찾기
                                            if (!videoUrl) {
                                                var scripts = document.querySelectorAll('script[type="application/json"]');
                                                for (var i = 0; i < scripts.length; i++) {
                                                    try {
                                                        var data = JSON.parse(scripts[i].textContent);
                                                        var jsonStr = JSON.stringify(data);
                                                        var match = jsonStr.match(/https?:\/\/[^"\\s]*(?:scontent|cdninstagram)[^"\\s]*\\.(mp4|webm|m3u8)/i);
                                                        if (match && !match[0].includes('blob:')) {
                                                            videoUrl = match[0];
                                                            break;
                                                        }
                                                    } catch(e) {}
                                                }
                                            }
                                            
                                            return videoUrl;
                                        """)
                                        
                                        if js_video_url:
                                            actual_video_url = js_video_url
                                            print(f"  ✅ JavaScript 변수에서 실제 비디오 URL 발견: {actual_video_url[:80]}...")
                                        else:
                                            print(f"    ⚠️ JavaScript 변수에서 비디오 URL을 찾을 수 없습니다.")
                                    except Exception as e:
                                        print(f"    ⚠️ JavaScript 변수 검색 중 오류: {e}")
                                
                                # 6. 네트워크 로그에서 비디오 URL 찾기 (instagram_extract_voice.py 참고)
                                if not actual_video_url:
                                    print(f"    🔍 네트워크 로그에서 비디오 URL 검색 중...")
                                    try:
                                        # Performance log 확인
                                        logs = driver.get_log('performance')
                                        video_urls = []
                                        for log in logs:
                                            try:
                                                import json
                                                log_data = json.loads(log.get('message', '{}'))
                                                message = log_data.get('message', {})
                                                method = message.get('method', '')
                                                
                                                # Network.responseReceived 또는 Network.requestWillBeSent 이벤트 확인
                                                if method in ['Network.responseReceived', 'Network.requestWillBeSent']:
                                                    params = message.get('params', {})
                                                    request = params.get('request', {})
                                                    response = params.get('response', {})
                                                    url = request.get('url') or response.get('url', '')
                                                    
                                                    if url and ('.mp4' in url or '.webm' in url or 'video' in url.lower() or 'cdninstagram' in url or 'scontent' in url):
                                                        if not url.startswith('blob:') and url not in video_urls:
                                                            video_urls.append(url)
                                            except:
                                                continue
                                        
                                        if video_urls:
                                            # 가장 최근 URL 사용
                                            actual_video_url = video_urls[-1]
                                            print(f"  ✅ 네트워크 로그에서 실제 비디오 URL 발견: {actual_video_url[:80]}...")
                                        else:
                                            print(f"    ⚠️ 네트워크 로그에서 비디오 URL을 찾을 수 없습니다.")
                                    except Exception as e:
                                        print(f"    ⚠️ 네트워크 로그 확인 중 오류: {e}")
                                
                                # URL이 발견되면 추가
                                if actual_video_url:
                                    seen_urls.add(actual_video_url)
                                    media_urls.append(actual_video_url)
                                    print(f"  ✅ 비디오 URL 추가 완료!")
                                    # VIDEO 타입이면 첫 번째만 수집
                                    if media_type == "VIDEO":
                                        break
                                else:
                                    print(f"  ⚠️ video 요소 #{video_idx}에서 URL을 찾을 수 없습니다.")
                    
                    print(f"  📎 media_url: {len(media_urls)}개")
                    if media_urls:
                        print(f"  ✅ 수집된 media_url (첫 3개):")
                        for idx, url in enumerate(media_urls[:3], 1):
                            print(f"     {idx}. {url[:100]}...")
                    else:
                        print(f"  ❌ media_url을 찾지 못했습니다!")
                        # 디버깅: 페이지 소스 일부 확인
                        try:
                            page_source_length = len(driver.page_source)
                            print(f"  🔍 페이지 소스 길이: {page_source_length}자")
                            # img와 video 태그가 있는지 확인
                            img_count = driver.page_source.count('<img')
                            video_count = driver.page_source.count('<video')
                            print(f"  🔍 페이지 소스 내 <img> 태그 개수: {img_count}, <video> 태그 개수: {video_count}")
                        except Exception as debug_e:
                            print(f"  ⚠️ 디버깅 정보 수집 실패: {debug_e}")
                    
                    if media_type == "CAROUSEL_ALBUM":
                        print(f"  ℹ️ CAROUSEL_ALBUM이므로 첫 번째 media_url만 수집했습니다.")
                except Exception as e:
                    print(f"  ⚠️ media_url 추출 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 6. media_count 계산
                media_count = len(media_urls)
                
                # 7. timestamp 추출
                timestamp_str = None
                try:
                    time_element = driver.find_element(By.CSS_SELECTOR, "time.xdwrcjd")
                    datetime_attr = time_element.get_attribute("datetime")
                    if datetime_attr:
                        # ISO 형식을 datetime으로 변환
                        try:
                            # ISO 형식 파싱 (예: "2025-10-03T13:31:22.000Z")
                            dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                            timestamp_str = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
                            print(f"  🕐 timestamp: {timestamp_str}")
                        except Exception as e:
                            print(f"  ⚠️ timestamp 파싱 실패: {e}")
                except NoSuchElementException:
                    print(f"  ⚠️ timestamp를 찾을 수 없습니다.")
                
                # 8. like_count와 comments_count 추출
                like_count = None
                comments_count = None
                
                print(f"  🔍 like_count와 comments_count 추출 시작...")
                
                # 좋아요 수 추출
                # <section class="x12nagc"><div><div><span><a><span><span class="html-span xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x1hl2dhg x16tdsg8 x1vvkbs">
                try:
                    # section.x12nagc 찾기
                    section = driver.find_element(By.CSS_SELECTOR, "section.x12nagc")
                    # 하위 요소로 이동: div > div > span > a > span > span.html-span.xdj266r...
                    like_span = section.find_element(By.CSS_SELECTOR, "div > div > span > a > span > span.html-span.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x1hl2dhg.x16tdsg8.x1vvkbs")
                    like_text = like_span.text.strip()
                    print(f"  🔍 좋아요 span 텍스트: '{like_text}'")
                    # 숫자만 추출 (예: "1,234" -> 1234)
                    like_numbers = re.findall(r'\d+', like_text.replace(',', ''))
                    if like_numbers:
                        like_count = int(''.join(like_numbers))
                        print(f"  ❤️ like_count: {like_count}")
                except NoSuchElementException:
                    # 부분 매칭 시도
                    try:
                        section = driver.find_element(By.CSS_SELECTOR, "section[class*='x12nagc']")
                        like_span = section.find_element(By.CSS_SELECTOR, "span.html-span.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x1hl2dhg.x16tdsg8.x1vvkbs")
                        like_text = like_span.text.strip()
                        print(f"  🔍 좋아요 span 텍스트 (부분 매칭): '{like_text}'")
                        like_numbers = re.findall(r'\d+', like_text.replace(',', ''))
                        if like_numbers:
                            like_count = int(''.join(like_numbers))
                            print(f"  ❤️ like_count: {like_count}")
                    except Exception as e:
                        print(f"  ⚠️ like_count 추출 실패: {e}")
                except Exception as e:
                    print(f"  ⚠️ like_count 추출 중 오류: {e}")
                
                # 댓글 수 추출
                # <div class="x9f619 x78zum5 xdt5ytf x5yr21d xexx8yu xv54qhq x1l90r2v xf7dkkf x10l6tqk xh8yej3">
                #   안에 있는 <div class="x78zum5 xdt5ytf x1iyjqo2">
                #     안에 있는 <div class="html-div xdj266r x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x9f619 xjbqb8w x78zum5 x15mokao x1ga7v0g x16uus16 xbiv7yw x1uhb9sk x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1qjc9v5 x1oa3qoh x1nhvcw1">의 개수
                # 각 div마다 하위 요소 <div><div><div><span>으로 감싸진 "답글 X개 모두 보기"에서 X를 찾아서 더하기
                try:
                    # 최상위 컨테이너 <div class="x9f619 x78zum5 xdt5ytf x5yr21d xexx8yu xv54qhq x1l90r2v xf7dkkf x10l6tqk xh8yej3"> 찾기
                    top_containers = driver.find_elements(By.CSS_SELECTOR, "div.x9f619.x78zum5.xdt5ytf.x5yr21d.xexx8yu.xv54qhq.x1l90r2v.xf7dkkf.x10l6tqk.xh8yej3")
                    print(f"  🔍 최상위 댓글 컨테이너 개수: {len(top_containers)}")
                    
                    total_comments = 0
                    reply_count = 0
                    seen_comments = set()  # 중복 제거를 위한 set
                    
                    for top_container in top_containers:
                        # 각 최상위 컨테이너 안의 <div class="x78zum5 xdt5ytf x1iyjqo2"> 찾기
                        middle_containers = top_container.find_elements(By.CSS_SELECTOR, "div.x78zum5.xdt5ytf.x1iyjqo2")
                        print(f"    최상위 컨테이너 내 중간 컨테이너 개수: {len(middle_containers)}")
                        
                        for middle_container in middle_containers:
                            # 각 중간 컨테이너 안의 실제 댓글 span 찾기
                            # 구조: <div class="html-div xdj266r...x1qjc9v5 x1oa3qoh x1nhvcw1">
                            #   > <div class="html-div xdj266r...x1cy8zhl x1oa3qoh x1nhvcw1">
                            #     > <span class="x1lliihq x1plvlek xryxfnj x1n2onr6 xyejjpt x15dsfln x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye xvs91rp xo1l8bm x5n08af x10wh9bi xpm28yp x8viiok x1o7cslx">
                            
                            # 첫 번째 div (외부)
                            outer_divs = middle_container.find_elements(By.CSS_SELECTOR, "div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x9f619.xjbqb8w.x78zum5.x15mokao.x1ga7v0g.x16uus16.xbiv7yw.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1")
                            print(f"      중간 컨테이너 내 외부 div 개수: {len(outer_divs)}")
                            
                            for outer_div in outer_divs:
                                # 두 번째 div (내부, x1cy8zhl 포함)
                                inner_divs = outer_div.find_elements(By.CSS_SELECTOR, "div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x9f619.xjbqb8w.x78zum5.x15mokao.x1ga7v0g.x16uus16.xbiv7yw.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1cy8zhl.x1oa3qoh.x1nhvcw1")
                                
                                for inner_div in inner_divs:
                                    # 실제 댓글 span 찾기
                                    comment_spans = inner_div.find_elements(By.CSS_SELECTOR, "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.xyejjpt.x15dsfln.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.xpm28yp.x8viiok.x1o7cslx")
                                    
                                    if comment_spans:
                                        print(f"        댓글 span 발견: {len(comment_spans)}개")
                                        
                                        # 각 댓글 span의 내용 확인
                                        for idx, comment_span in enumerate(comment_spans, 1):
                                            span_text = comment_span.text.strip()
                                            print(f"          span #{idx} 내용: '{span_text[:100] if span_text else '(빈 텍스트)'}...'")
                                            
                                            # 빈 텍스트이거나 특정 패턴이 아닌 경우만 댓글로 카운트
                                            # "답글 X개 모두 보기" 같은 패턴은 제외
                                            if span_text and "답글" not in span_text and "모두 보기" not in span_text:
                                                # 중복 체크 (텍스트로 비교)
                                                if span_text not in seen_comments:
                                                    seen_comments.add(span_text)
                                                    total_comments += 1
                                                    print(f"            → 유효한 댓글로 카운트 (중복 아님)")
                                                else:
                                                    print(f"            → 중복 댓글, 스킵")
                                            
                                            # 답글 수 찾기 (새로운 셀렉터 사용)
                                            try:
                                                # 답글 구조: <div class="html-div xdj266r...x11hdunq">
                                                #   > <div class="x1i10hfl xjbqb8w...">
                                                #     > <div class="html-div xdj266r...x6s0dn4 x1oa3qoh x1nhvcw1">
                                                #       > <span class="x1lliihq...x1fhwpqd x1s688f x1roi4f4 x1s3etm8 x676frb...">에 "답글 X개 모두 보기"
                                                
                                                # outer_div에서 답글 div 찾기
                                                reply_container = outer_div.find_element(By.CSS_SELECTOR, "div.html-div.xdj266r.x14z9mp.xat24cr.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x9f619.xjbqb8w.x78zum5.x15mokao.x1ga7v0g.x16uus16.xbiv7yw.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1.x11hdunq")
                                                
                                                # 답글 span 찾기
                                                reply_spans = reply_container.find_elements(By.CSS_SELECTOR, "div.x1i10hfl.xjbqb8w.x1ejq31n.x18oe1m7.x1sy0etr.xstzfhl.x972fbf.x10w94by.x1qhh985.x14e42zd.x9f619.x1ypdohk.xt0psk2.x3ct3a4.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x16tdsg8.x1hl2dhg.xggy1nq.x1a2a7pz.x87ps6o.x1d5wrs8 > div.html-div.xdj266r.x14z9mp.xat24cr.x1lziwak.xyri2b.x1c1uobl.x9f619.xjbqb8w.x78zum5.x15mokao.x1ga7v0g.x16uus16.xbiv7yw.xwib8y2.x1y1aw1k.x1uhb9sk.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.x1q0g3np.xqjyukv.x6s0dn4.x1oa3qoh.x1nhvcw1 > span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.xyejjpt.x15dsfln.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.x1fhwpqd.x1s688f.x1roi4f4.x1s3etm8.x676frb.x10wh9bi.xpm28yp.x8viiok.x1o7cslx")
                                                
                                                for reply_span in reply_spans:
                                                    reply_text = reply_span.text.strip()
                                                    # "답글 X개 모두 보기" 패턴 찾기
                                                    if "답글" in reply_text and "모두 보기" in reply_text:
                                                        # 숫자 추출
                                                        reply_numbers = re.findall(r'\d+', reply_text)
                                                        if reply_numbers:
                                                            reply_num = int(''.join(reply_numbers))
                                                            reply_count += reply_num
                                                            print(f"            답글 수 발견: {reply_num}개 (텍스트: '{reply_text}')")
                                            except NoSuchElementException:
                                                # 답글이 없는 경우
                                                pass
                                            except Exception as e:
                                                print(f"            답글 찾기 중 오류: {e}")
                                        
                                        print(f"        현재까지 총 댓글 수: {total_comments}개, 답글 수: {reply_count}개")
                    
                    # 댓글 수 = 댓글 div 개수 + 답글 수
                    comments_count = total_comments + reply_count
                    print(f"  💬 comments_count: {comments_count} (댓글 div: {total_comments}개, 답글: {reply_count}개)")
                    
                except NoSuchElementException:
                    # 부분 매칭 시도
                    try:
                        top_containers = driver.find_elements(By.CSS_SELECTOR, "div[class*='x9f619'][class*='x78zum5'][class*='xdt5ytf'][class*='x5yr21d']")
                        print(f"  🔍 최상위 댓글 컨테이너 개수 (부분 매칭): {len(top_containers)}")
                        
                        total_comments = 0
                        reply_count = 0
                        seen_comments = set()  # 중복 제거를 위한 set
                        
                        for top_container in top_containers:
                            middle_containers = top_container.find_elements(By.CSS_SELECTOR, "div[class*='x78zum5'][class*='xdt5ytf'][class*='x1iyjqo2']")
                            print(f"    최상위 컨테이너 내 중간 컨테이너 개수: {len(middle_containers)}")
                            
                            for middle_container in middle_containers:
                                # 부분 매칭으로 외부 div 찾기
                                outer_divs = middle_container.find_elements(By.CSS_SELECTOR, "div[class*='html-div'][class*='xdj266r'][class*='x1qjc9v5']")
                                print(f"      중간 컨테이너 내 외부 div 개수: {len(outer_divs)}")
                                
                                for outer_div in outer_divs:
                                    # 내부 div 찾기 (x1cy8zhl 포함)
                                    inner_divs = outer_div.find_elements(By.CSS_SELECTOR, "div[class*='html-div'][class*='xdj266r'][class*='x1cy8zhl']")
                                    
                                    for inner_div in inner_divs:
                                        # 댓글 span 찾기
                                        comment_spans = inner_div.find_elements(By.CSS_SELECTOR, "span[class*='x1lliihq'][class*='x1plvlek'][class*='xryxfnj']")
                                        
                                        if comment_spans:
                                            print(f"        댓글 span 발견: {len(comment_spans)}개")
                                            
                                            for idx, comment_span in enumerate(comment_spans, 1):
                                                span_text = comment_span.text.strip()
                                                print(f"          span #{idx} 내용: '{span_text[:100] if span_text else '(빈 텍스트)'}...'")
                                                
                                                # 빈 텍스트이거나 특정 패턴이 아닌 경우만 댓글로 카운트
                                                if span_text and "답글" not in span_text and "모두 보기" not in span_text:
                                                    # 중복 체크 (텍스트로 비교)
                                                    if span_text not in seen_comments:
                                                        seen_comments.add(span_text)
                                                        total_comments += 1
                                                        print(f"            → 유효한 댓글로 카운트 (중복 아님)")
                                                    else:
                                                        print(f"            → 중복 댓글, 스킵")
                                                
                                                # 답글 수 찾기 (부분 매칭)
                                                try:
                                                    reply_container = outer_div.find_element(By.CSS_SELECTOR, "div[class*='html-div'][class*='xdj266r'][class*='x11hdunq']")
                                                    reply_spans = reply_container.find_elements(By.CSS_SELECTOR, "span[class*='x1lliihq'][class*='x1fhwpqd'][class*='x1s688f']")
                                                    
                                                    for reply_span in reply_spans:
                                                        reply_text = reply_span.text.strip()
                                                        if "답글" in reply_text and "모두 보기" in reply_text:
                                                            reply_numbers = re.findall(r'\d+', reply_text)
                                                            if reply_numbers:
                                                                reply_num = int(''.join(reply_numbers))
                                                                reply_count += reply_num
                                                                print(f"            답글 수 발견: {reply_num}개 (텍스트: '{reply_text}')")
                                                except NoSuchElementException:
                                                    pass
                                                except Exception as e:
                                                    print(f"            답글 찾기 중 오류: {e}")
                                            
                                            print(f"        현재까지 총 댓글 수: {total_comments}개, 답글 수: {reply_count}개")
                        
                        comments_count = total_comments + reply_count
                        print(f"  💬 comments_count (부분 매칭): {comments_count} (댓글 div: {total_comments}개, 답글: {reply_count}개)")
                    except Exception as e:
                        print(f"  ⚠️ comments_count 추출 실패: {e}")
                except Exception as e:
                    print(f"  ⚠️ comments_count 추출 중 오류: {e}")
                
                if like_count is None:
                    print(f"  ⚠️ like_count를 찾을 수 없습니다.")
                if comments_count is None:
                    print(f"  ⚠️ comments_count를 찾을 수 없습니다.")
                
                # 9. 데이터 수집 완료 및 출력/저장
                # 새 데이터 항목 생성
                new_item = {
                    "id": user_id if user_id else f"collected_{int(time.time())}",
                    "media_type": media_type,
                    "media_url": media_urls,
                    "media_count": media_count,
                    "content": content,
                    "hashtags": hashtags,
                    "content_count": content_count,
                    "hashtag_count": hashtag_count,
                    "permalink": permalink,
                    "timestamp": timestamp_str,
                    "like_count": like_count,
                    "comments_count": comments_count,
                    "handle": handle
                }
                
                # 테스트 모드면 터미널에만 출력
                if test_mode:
                    print(f"\n  📋 수집된 데이터 (테스트 모드 - JSON 저장 안 함):")
                    print(f"     id: {new_item['id']}")
                    print(f"     handle: {new_item['handle']}")
                    print(f"     media_type: {new_item['media_type']}")
                    print(f"     media_count: {new_item['media_count']}")
                    print(f"     content: {new_item['content'][:100] if new_item['content'] else '(없음)'}...")
                    print(f"     content_count: {new_item['content_count']}")
                    print(f"     hashtags: {new_item['hashtags']}")
                    print(f"     hashtag_count: {new_item['hashtag_count']}")
                    print(f"     timestamp: {new_item['timestamp']}")
                    print(f"     like_count: {new_item['like_count']}")
                    print(f"     comments_count: {new_item['comments_count']}")
                    print(f"     permalink: {new_item['permalink']}")
                    print(f"     media_url (첫 3개): {new_item['media_url'][:3]}")
                    processed_count += 1
                else:
                    # 실제 모드면 JSON에 저장
                    # instagram_media.json 로드
                    try:
                        with open(MEDIA_JSON, "r", encoding="utf-8") as f:
                            media_data = json.load(f)
                    except FileNotFoundError:
                        media_data = []
                        print(f"  ⚠️ {MEDIA_JSON} 파일이 없어 새로 생성합니다.")
                    
                    # 중복 확인 (permalink 기준)
                    existing_permalinks = {item.get("permalink") for item in media_data if item.get("permalink")}
                    if permalink in existing_permalinks:
                        print(f"  ⚠️ 이미 존재하는 permalink입니다. 건너뜁니다.")
                        skipped_count += 1
                    else:
                        media_data.append(new_item)
                        
                        # JSON 파일에 저장
                        try:
                            with open(MEDIA_JSON, "w", encoding="utf-8") as f:
                                json.dump(media_data, f, ensure_ascii=False, indent=2)
                            print(f"  💾 JSON 저장 완료!")
                        except Exception as e:
                            print(f"  ⚠️ JSON 저장 실패: {e}")
                        
                        processed_count += 1
                
                # 요청 간 딜레이 (Instagram 차단 방지)
                time.sleep(2)
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ 처리 중 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 최종 통계 출력
        print(f"\n{'='*60}")
        print(f"✅ 스텝2 완료!")
        print(f"   총 permalink: {len(permalinks)}개")
        print(f"   처리 완료: {processed_count}개")
        print(f"   스킵됨 (필터 단어 없음): {skipped_count}개")
        print(f"   오류 발생: {error_count}개")
        print(f"{'='*60}")
        
        # 로그에도 통계 기록
        logging.info("=" * 80)
        logging.info("스텝2 완료 - instagram_crawling_userposts.py")
        logging.info(f"총 permalink: {len(permalinks)}개")
        logging.info(f"처리 완료: {processed_count}개")
        logging.info(f"스킵됨 (필터 단어 없음): {skipped_count}개")
        logging.info(f"오류 발생: {error_count}개")
        logging.info("=" * 80)
        
    finally:
        driver.quit()
        print("\n🔒 브라우저 종료")

if __name__ == "__main__":
    # 쿠키 재생성 옵션 확인
    import sys
    regenerate_cookie = False
    if len(sys.argv) > 1 and sys.argv[1] in ['--regenerate-cookie', '-r']:
        regenerate_cookie = True
        print("🔄 쿠키 재생성 모드로 실행합니다.")
        print("=" * 60)
    
    # 쿠키 재생성이 필요한 경우 먼저 실행
    if regenerate_cookie:
        driver = setup_driver()
        try:
            if regenerate_cookies(driver):
                print("\n✅ 쿠키 재생성 완료!")
                print("=" * 60)
            else:
                print("\n❌ 쿠키 재생성 실패. 프로그램을 종료합니다.")
                sys.exit(1)
        finally:
            driver.quit()
        print()
    
    # 스텝1 실행 (test_mode=False: 모든 사용자 처리)
    permalinks = step1_collect_post_permalinks(test_mode=False)
    
    # 결과 출력
    if permalinks:
        print(f"\n📋 수집된 permalink 목록 (처음 20개):")
        for idx, item in enumerate(permalinks[:20], 1):
            print(f"  {idx}. @{item['user_handle']}: {item['permalink']}")
        if len(permalinks) > 20:
            print(f"  ... 외 {len(permalinks) - 20}개")
        print(f"\n✅ 총 {len(permalinks)}개의 permalink 수집됨")
        
        # 스텝2 실행 (수집한 permalink 리스트를 바로 전달, test_mode=False: 전체 처리)
        print(f"\n{'='*60}")
        step2_process_permalinks(permalinks, test_mode=False)
    else:
        print("\n⚠️ 수집된 permalink가 없습니다.")

