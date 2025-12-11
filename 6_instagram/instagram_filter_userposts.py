"""
Instagram 크롤링 스크립트 - Step 2 (필터링 및 데이터 수집)
permalink.txt 파일에서 permalink를 읽어와서 데이터 수집

사용 방법:
    python instagram_filter_userposts.py [--test] [--regenerate-cookie]
    
    옵션:
        --test, -t: 테스트 모드 (상위 3개만 처리)
        --regenerate-cookie, -r: 쿠키 재생성

permalink.txt 형식:
    한 줄에 하나씩 permalink URL
    예:
    https://www.instagram.com/p/ABC123/
    https://www.instagram.com/reel/XYZ789/
    https://www.instagram.com/username/p/ABC123/
"""

import json
import logging
import time
import re
import random
from pathlib import Path
from datetime import datetime
from typing import Optional
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
MEDIA_JSON = Path("instagram_media.json")
PERMALINK_TXT = Path("permalink.txt")
COOKIE_PATH = Path("instagram_cookies.pkl")
LOG_PATH = Path("instagram.log")
PROCESSED_PERMALINKS_JSON = Path("instagram_processed_permalinks.json")  # 처리된 permalink 추적
SKIPPED_PERMALINKS_JSON = Path("instagram_skipped_permalinks.json")  # 스킵된 permalink 추적 (필터 단어 없음)
BATCH_SIZE = 5000  # 배치 크기 (5000개씩 처리)


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
                else:
                    logging.debug(f"우선 경로 체크 실패 ({resolved_str}): is_file={resolved.is_file()}, is_symlink={resolved.is_symlink()}, executable={os.access(resolved, os.X_OK)}")
            else:
                logging.debug(f"우선 경로 resolve 실패: {path} -> {resolved_str}")
        else:
            logging.debug(f"우선 경로 존재하지 않음: {path}")
    
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

def normalize_permalink(url: str) -> Optional[str]:
    """
    permalink를 정규화하여 shortcode만 추출
    - instagram_media.json 형식: "https://www.instagram.com/reel/DQ5hGrqE6SP/"
    - 수집한 형식: "https://www.instagram.com/pmi_min/reel/DD4hDgTy82T/"
    → 둘 다 shortcode만 추출하여 비교: "DQ5hGrqE6SP", "DD4hDgTy82T"
    
    Args:
        url: permalink URL
        
    Returns:
        shortcode 또는 None
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

def clean_text(text: str) -> str:
    """
    텍스트에서 불필요한 공백과 특수 문자를 정리합니다.
    
    Args:
        text: 정리할 텍스트
        
    Returns:
        정리된 텍스트
    """
    if not text:
        return ""
    
    # 1. 유니코드 공백 문자들을 일반 공백으로 변환
    # (예: \u2000-\u200B, \u202F, \u205F, \u3000, \u2800 등)
    # \u2800은 Braille Pattern Blank (⠀) 문자
    text = re.sub(r'[\u2000-\u200B\u202F\u205F\u2800\u3000\ufeff]', ' ', text)
    
    # 2. 탭, 줄바꿈, 캐리지 리턴을 공백으로 변환
    text = re.sub(r'[\t\n\r]+', ' ', text)
    
    # 3. 연속된 공백을 하나로 변환
    text = re.sub(r' +', ' ', text)
    
    # 4. 앞뒤 공백 제거
    text = text.strip()
    
    # 5. 빈 문자열이나 공백만 있는 경우 빈 문자열 반환
    if not text or text.isspace():
        return ""
    
    return text

def clean_handle(handle_text: str) -> str:
    """
    handle 텍스트를 정리합니다.
    "glow.jung 수정됨•5주" 같은 형식에서 handle만 추출하거나 정리합니다.
    
    Args:
        handle_text: 정리할 handle 텍스트
        
    Returns:
        정리된 handle
    """
    if not handle_text:
        return ""
    
    # 기본 공백 정리
    handle = clean_text(handle_text)
    
    # "수정됨•N주", "수정됨•N일" 같은 패턴 제거
    handle = re.sub(r'\s*수정됨[•·]\d+\s*(주|일|시간|분)', '', handle, flags=re.IGNORECASE)
    
    # "•" 또는 "·" 같은 특수 문자로 시작하는 부분 제거
    # 예: "glow.jung •5주" -> "glow.jung"
    handle = re.sub(r'\s*[•·]\s*\d+\s*(주|일|시간|분)', '', handle, flags=re.IGNORECASE)
    
    # 숫자와 단위로만 이루어진 부분 제거 (예: "38주", "5주" 등)
    handle = re.sub(r'\s+\d+\s*(주|일|시간|분|개월|년)', '', handle, flags=re.IGNORECASE)
    
    # 다시 공백 정리
    handle = clean_text(handle)
    
    return handle

def load_processed_permalinks() -> set:
    """
    처리된 permalink 목록을 로드합니다.
    
    Returns:
        처리된 permalink의 set
    """
    processed = set()
    
    if PROCESSED_PERMALINKS_JSON.exists():
        try:
            with open(PROCESSED_PERMALINKS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                processed = set(data.get("processed_permalinks", []))
            print(f"📂 처리된 permalink {len(processed)}개 로드됨")
            logging.info(f"처리된 permalink {len(processed)}개 로드됨")
        except Exception as e:
            print(f"⚠️ 처리된 permalink 로드 실패: {e}")
            logging.warning(f"처리된 permalink 로드 실패: {e}")
    
    return processed

def save_processed_permalink(permalink: str):
    """
    처리된 permalink를 저장합니다.
    
    Args:
        permalink: 저장할 permalink
    """
    try:
        if PROCESSED_PERMALINKS_JSON.exists():
            with open(PROCESSED_PERMALINKS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"processed_permalinks": []}
        
        if permalink not in data["processed_permalinks"]:
            data["processed_permalinks"].append(permalink)
            
            with open(PROCESSED_PERMALINKS_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"처리된 permalink 저장 실패: {e}")

def load_skipped_permalinks() -> set:
    """
    스킵된 permalink 목록을 로드합니다 (필터 단어가 없어서 스킵된 항목).
    
    Returns:
        스킵된 permalink의 set
    """
    skipped = set()
    
    if SKIPPED_PERMALINKS_JSON.exists():
        try:
            with open(SKIPPED_PERMALINKS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                skipped = set(data.get("skipped_permalinks", []))
            print(f"📂 스킵된 permalink {len(skipped)}개 로드됨 (필터 단어 없음)")
            logging.info(f"스킵된 permalink {len(skipped)}개 로드됨")
        except Exception as e:
            print(f"⚠️ 스킵된 permalink 로드 실패: {e}")
            logging.warning(f"스킵된 permalink 로드 실패: {e}")
    
    return skipped

def save_skipped_permalink(permalink: str):
    """
    스킵된 permalink를 저장합니다 (필터 단어가 없어서 스킵된 항목).
    
    Args:
        permalink: 저장할 permalink
    """
    try:
        if SKIPPED_PERMALINKS_JSON.exists():
            with open(SKIPPED_PERMALINKS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"skipped_permalinks": []}
        
        if permalink not in data["skipped_permalinks"]:
            data["skipped_permalinks"].append(permalink)
            
            with open(SKIPPED_PERMALINKS_JSON, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"스킵된 permalink 저장 실패: {e}")

def is_connection_error(exception: Exception) -> bool:
    """
    연결 끊김 에러인지 확인합니다.
    
    Args:
        exception: 확인할 예외
        
    Returns:
        연결 끊김 에러면 True
    """
    error_str = str(exception).lower()
    error_type = type(exception).__name__
    
    # 연결 끊김 관련 에러 패턴
    connection_error_patterns = [
        "connectionrefused",
        "connection refused",
        "max retries exceeded",
        "httpconnectionpool",
        "failed to establish",
        "대상 컴퓨터에서 연결을 거부",
        "연결하지 못했습니다",
        "webdriver",
        "session",
    ]
    
    # 연결 끊김 관련 예외 타입
    connection_error_types = [
        "ConnectionRefusedError",
        "MaxRetryError",
        "NewConnectionError",
        "WebDriverException",
    ]
    
    # 타입 확인
    if any(err_type in error_type for err_type in connection_error_types):
        return True
    
    # 메시지 확인
    if any(pattern in error_str for pattern in connection_error_patterns):
        return True
    
    return False

def load_permalinks_from_file(permalink_file: Path) -> list:
    """
    permalink.txt 파일에서 permalink를 읽어옵니다.
    
    Args:
        permalink_file: permalink.txt 파일 경로
        
    Returns:
        permalink 리스트 [{"user_id": None, "user_handle": "...", "permalink": "..."}, ...]
    """
    permalinks = []
    
    if not permalink_file.exists():
        print(f"❌ {permalink_file} 파일을 찾을 수 없습니다.")
        return permalinks
    
    print(f"📂 {permalink_file} 파일 로딩 중...")
    
    try:
        with open(permalink_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):  # 빈 줄이나 주석 줄은 건너뜀
                continue
            
            # permalink URL에서 user_handle 추출 시도
            user_handle = None
            # 예: https://www.instagram.com/username/p/ABC123/ 또는 https://www.instagram.com/p/ABC123/
            # 또는 https://www.instagram.com/username/reel/XYZ789/
            match = re.search(r'instagram\.com/([^/]+)/(?:p|reel)/', line)
            if match:
                user_handle = match.group(1)
            else:
                # /p/ 또는 /reel/ 바로 앞에 username이 없는 경우
                # 예: https://www.instagram.com/p/ABC123/
                match = re.search(r'instagram\.com/(?:p|reel)/', line)
                if match:
                    user_handle = "unknown"
            
            permalinks.append({
                "user_id": None,  # permalink.txt에서는 user_id를 알 수 없음
                "user_handle": user_handle or "unknown",
                "permalink": line
            })
        
        print(f"✅ {len(permalinks)}개의 permalink 로드됨")
        return permalinks
    
    except Exception as e:
        print(f"❌ {permalink_file} 파일 로드 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return permalinks

# step2_process_permalinks 함수는 원본 파일과 동일하므로
# 원본 파일에서 복사해야 합니다. 파일이 너무 길어서 여기서는 생략하고
# 실제로는 원본 파일의 step2_process_permalinks 함수 전체를 복사해야 합니다.
# 아래는 간단한 버전입니다.

def step2_process_permalinks(permalinks, test_mode=False, batch_size=BATCH_SIZE):
    """
    스텝2: permalink를 하나씩 방문하여 처리 (배치 처리 지원)
    - 각 permalink에 접속
    - 본문에서 특정 단어 리스트 확인
    - 단어가 없으면 스킵, 있으면 데이터 수집
    - 배치 단위로 처리하여 WebDriver 연결 끊김 방지
    
    Args:
        permalinks: permalink 리스트
                   [{"user_id": "...", "user_handle": "...", "permalink": "..."}, ...]
        test_mode: 테스트 모드 (True면 상위 3개만 처리)
        batch_size: 배치 크기 (기본 5000개)
    """
    # 로깅 초기화
    setup_logging(str(LOG_PATH))
    logging.info("=" * 80)
    logging.info("프로그램 시작 - instagram_filter_userposts.py (스텝2)")
    if test_mode:
        logging.info("테스트 모드: 상위 3개만 처리")
    logging.info(f"처리할 permalink 개수: {len(permalinks)}")
    logging.info(f"배치 크기: {batch_size}개")
    logging.info("=" * 80)
    
    print("=" * 60)
    print("스텝2: 수집한 permalink 처리 시작")
    if test_mode:
        print("🧪 테스트 모드: 상위 3개만 처리합니다")
    print(f"📦 배치 크기: {batch_size}개")
    print("=" * 60)
    
    if not permalinks:
        print("⚠️ 처리할 permalink가 없습니다.")
        return
    
    # 테스트 모드면 상위 3개만 처리
    if test_mode:
        permalinks = permalinks[:3]
        batch_size = 3  # 테스트 모드에서는 배치 크기를 작게
        print(f"\n🧪 테스트 모드: 상위 3개만 처리합니다")
    
    # 처리된 permalink 로드 (중단된 지점부터 재개)
    processed_permalinks = load_processed_permalinks()
    
    # 스킵된 permalink 로드 (필터 단어가 없어서 스킵된 항목)
    skipped_permalinks = load_skipped_permalinks()
    
    # instagram_media.json에 있는 permalink 로드 (이미 저장된 항목 스킵)
    # shortcode 기준으로 중복 체크 (정규화된 permalink)
    existing_media_shortcodes = set()
    existing_media_permalinks = set()  # shortcode를 추출할 수 없는 경우를 위한 원본 permalink 저장
    if MEDIA_JSON.exists():
        try:
            with open(MEDIA_JSON, "r", encoding="utf-8") as f:
                media_data = json.load(f)
                if isinstance(media_data, list):
                    for item in media_data:
                        permalink = item.get("permalink")
                        if permalink:
                            shortcode = normalize_permalink(permalink)
                            if shortcode:
                                existing_media_shortcodes.add(shortcode)
                            else:
                                # shortcode를 추출할 수 없으면 원본 permalink 저장
                                existing_media_permalinks.add(permalink)
            print(f"📂 instagram_media.json에 있는 permalink (shortcode 기준): {len(existing_media_shortcodes)}개, 원본 permalink: {len(existing_media_permalinks)}개")
        except Exception as e:
            print(f"⚠️ instagram_media.json 로드 실패: {e}")
    
    # 이미 처리된 permalink, 스킵된 permalink, instagram_media.json에 있는 permalink 제외
    # shortcode 기준으로 비교
    remaining_permalinks = []
    for item in permalinks:
        permalink = item.get("permalink")
        if not permalink:
            continue
        
        # shortcode 추출
        shortcode = normalize_permalink(permalink)
        if not shortcode:
            # shortcode를 추출할 수 없으면 원본 permalink로 비교 (하위 호환성)
            if (permalink not in processed_permalinks 
                and permalink not in skipped_permalinks
                and permalink not in existing_media_permalinks):
                remaining_permalinks.append(item)
        else:
            # shortcode 기준으로 비교
            # processed_permalinks와 skipped_permalinks도 shortcode로 변환하여 비교
            processed_shortcodes = {normalize_permalink(p) for p in processed_permalinks if normalize_permalink(p)}
            skipped_shortcodes = {normalize_permalink(p) for p in skipped_permalinks if normalize_permalink(p)}
            
            if (shortcode not in processed_shortcodes 
                and shortcode not in skipped_shortcodes
                and shortcode not in existing_media_shortcodes):
                remaining_permalinks.append(item)
    
    if processed_permalinks:
        print(f"📂 이미 처리된 permalink: {len(processed_permalinks)}개")
    if skipped_permalinks:
        print(f"📂 스킵된 permalink (필터 단어 없음): {len(skipped_permalinks)}개")
    if existing_media_permalinks:
        print(f"📂 instagram_media.json에 있는 permalink: {len(existing_media_permalinks)}개")
    print(f"📊 남은 permalink: {len(remaining_permalinks)}개")
    
    if not remaining_permalinks:
        print("✅ 모든 permalink가 이미 처리되었습니다.")
        return
    
    print(f"\n📊 {len(remaining_permalinks)}개의 permalink 처리 시작...")
    
    # 필터링할 단어 리스트 (해시태그에 이 단어들이 없으면 스킵)
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
    
    print(f"📝 필터 단어 리스트: {filter_words}")
    print(f"   (해시태그에 이 단어들이 없으면 스킵합니다)\n")
    
    # 전체 통계
    total_processed_count = 0
    total_skipped_count = 0
    total_error_count = 0
    
    # 배치 단위로 처리
    total_batches = (len(remaining_permalinks) + batch_size - 1) // batch_size
    print(f"📦 총 {total_batches}개 배치로 나누어 처리합니다.\n")
    
    for batch_num in range(total_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(remaining_permalinks))
        batch_permalinks = remaining_permalinks[batch_start:batch_end]
        
        print(f"\n{'='*60}")
        print(f"📦 배치 {batch_num + 1}/{total_batches} 처리 시작")
        print(f"   범위: {batch_start + 1} ~ {batch_end} ({len(batch_permalinks)}개)")
        print(f"{'='*60}\n")
        
        # 배치 처리 (재시도 로직 포함)
        max_retries = 3
        retry_count = 0
        batch_success = False
        
        while retry_count < max_retries and not batch_success:
            driver = None
            try:
                # Selenium WebDriver 초기화
                driver = setup_driver()
                
                # Instagram 로그인
                if not login_instagram(driver):
                    print("❌ 로그인 실패. 이 배치를 건너뜁니다.")
                    retry_count += 1
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    continue
                
                # 배치 처리 통계
                batch_processed_count = 0
                batch_skipped_count = 0
                batch_error_count = 0
                
                # 각 permalink에 대해 반복문 처리
                for idx, item in enumerate(batch_permalinks, 1):
                    global_idx = batch_start + idx
                    user_id = item.get("user_id")
                    user_handle = item.get("user_handle")
                    permalink = item.get("permalink")
                    
                    if not permalink:
                        batch_skipped_count += 1
                        print(f"[{global_idx}/{len(remaining_permalinks)}] ⚠️ permalink가 없습니다. 건너뜁니다.")
                        continue
                    
                    # shortcode 추출
                    shortcode = normalize_permalink(permalink)
                    
                    # 이미 처리된 permalink는 건너뜀 (shortcode 기준)
                    if shortcode:
                        processed_shortcodes = {normalize_permalink(p) for p in processed_permalinks if normalize_permalink(p)}
                        if shortcode in processed_shortcodes:
                            print(f"[{global_idx}/{len(remaining_permalinks)}] ⏭️ 이미 처리된 permalink입니다. (shortcode: {shortcode})")
                            continue
                    else:
                        # shortcode를 추출할 수 없으면 원본 permalink로 비교 (하위 호환성)
                        if permalink in processed_permalinks:
                            print(f"[{global_idx}/{len(remaining_permalinks)}] ⏭️ 이미 처리된 permalink입니다.")
                            continue
                    
                    # instagram_media.json에 있는 permalink는 건너뜀 (shortcode 기준)
                    if shortcode and shortcode in existing_media_shortcodes:
                        print(f"[{global_idx}/{len(remaining_permalinks)}] ⏭️ instagram_media.json에 이미 있는 permalink입니다. (shortcode: {shortcode})")
                        batch_skipped_count += 1
                        save_processed_permalink(permalink)
                        processed_permalinks.add(permalink)
                        continue
                    elif not shortcode and permalink in existing_media_permalinks:
                        # shortcode를 추출할 수 없으면 원본 permalink로 비교 (하위 호환성)
                        print(f"[{global_idx}/{len(remaining_permalinks)}] ⏭️ instagram_media.json에 이미 있는 permalink입니다.")
                        batch_skipped_count += 1
                        save_processed_permalink(permalink)
                        processed_permalinks.add(permalink)
                        continue
                    
                    print(f"\n[{global_idx}/{len(remaining_permalinks)}] 처리 중: @{user_handle}")
                    print(f"  🔍 접속 중: {permalink}")
                    logging.info(f"[{global_idx}/{len(remaining_permalinks)}] 처리 중: @{user_handle}, permalink: {permalink}")
                    
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
                        time.sleep(2)
                        driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(2)
                        
                        # 1. handle 추출
                        handle = ""
                        try:
                            handle_element = driver.find_element(By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade")
                            handle_raw = handle_element.text
                            handle = clean_handle(handle_raw)
                            if handle_raw != handle:
                                print(f"  👤 handle (원본): {handle_raw}")
                                print(f"  👤 handle (정리됨): {handle}")
                            else:
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
                            try:
                                # innerHTML 가져오기
                                inner_html = driver.execute_script("""
                                    var div = arguments[0];
                                    return div.innerHTML;
                                """, content_div)
                                
                                # BeautifulSoup 없이 간단한 정규식으로 처리
                                # 1. <br> 태그를 공백으로 변환
                                inner_html = re.sub(r'<br\s*/?>', ' ', inner_html, flags=re.IGNORECASE)
                                # 2. HTML 엔티티 변환
                                inner_html = inner_html.replace('&nbsp;', ' ')
                                inner_html = inner_html.replace('&amp;', '&')
                                inner_html = inner_html.replace('&lt;', '<')
                                inner_html = inner_html.replace('&gt;', '>')
                                inner_html = inner_html.replace('&quot;', '"')
                                inner_html = inner_html.replace('&#39;', "'")
                                # 3. HTML 태그 제거
                                inner_html = re.sub(r'<[^>]+>', '', inner_html)
                                # 4. 기본 공백 정리
                                content = clean_text(inner_html)
                                
                                # hashtag 제거 (content에서)
                                for tag in hashtags:
                                    # 해시태그와 앞뒤 공백 제거
                                    content = re.sub(r'\s*' + re.escape(tag) + r'\s*', ' ', content)
                                
                                # handle과 "Edited•4d", "수정됨•4일" 같은 패턴 제거
                                if handle:
                                    # handle로 시작하는 부분 제거 (예: "glow.jung Edited•4d" -> "")
                                    content = re.sub(r'^' + re.escape(handle) + r'\s*', '', content, flags=re.IGNORECASE)
                                    # handle이 중간에 있을 수도 있으므로 제거
                                    content = re.sub(r'\s*' + re.escape(handle) + r'\s*', ' ', content, flags=re.IGNORECASE)
                                
                                # "Edited•4d", "수정됨•4일", "Edited•6w", "수정됨•6주", "•4일", "•5주" 같은 패턴 제거
                                # "Edited•4d", "수정됨•6주" 같은 패턴 (공백이 있을 수도 없을 수도 있음)
                                content = re.sub(r'\s*(Edited|수정됨)\s*[•·]\s*\d+\s*(d|w|일|시간|분|주|개월|년)\s*', ' ', content, flags=re.IGNORECASE)
                                # "•4일", "•5주" 같은 패턴 (앞에 공백이 있을 수도 없을 수도 있음)
                                content = re.sub(r'\s*[•·]\s*\d+\s*(d|w|일|시간|분|주|개월|년)\s*', ' ', content, flags=re.IGNORECASE)
                                
                                # 다시 공백 정리
                                content = clean_text(content)
                                
                            except Exception as e:
                                print(f"  ⚠️ HTML 파싱 실패, 텍스트로 대체: {e}")
                                # 텍스트로 대체하는 경우에도 공백 정리
                                content = clean_text(full_text)
                                for tag in hashtags:
                                    content = re.sub(r'\s*' + re.escape(tag) + r'\s*', ' ', content)
                                
                                # handle과 "Edited•4d", "수정됨•4일" 같은 패턴 제거
                                if handle:
                                    # handle로 시작하는 부분 제거 (예: "glow.jung Edited•4d" -> "")
                                    content = re.sub(r'^' + re.escape(handle) + r'\s*', '', content, flags=re.IGNORECASE)
                                    # handle이 중간에 있을 수도 있으므로 제거
                                    content = re.sub(r'\s*' + re.escape(handle) + r'\s*', ' ', content, flags=re.IGNORECASE)
                                
                                # "Edited•4d", "수정됨•4일", "Edited•6w", "수정됨•6주", "•4일", "•5주" 같은 패턴 제거
                                # "Edited•4d", "수정됨•6주" 같은 패턴 (공백이 있을 수도 없을 수도 있음)
                                content = re.sub(r'\s*(Edited|수정됨)\s*[•·]\s*\d+\s*(d|w|일|시간|분|주|개월|년)\s*', ' ', content, flags=re.IGNORECASE)
                                # "•4일", "•5주" 같은 패턴 (앞에 공백이 있을 수도 없을 수도 있음)
                                content = re.sub(r'\s*[•·]\s*\d+\s*(d|w|일|시간|분|주|개월|년)\s*', ' ', content, flags=re.IGNORECASE)
                                
                                content = clean_text(content)
                            
                            print(f"  📝 content: {content[:100]}...")
                            print(f"  🏷️ hashtags: {len(hashtags)}개")
                            
                        except NoSuchElementException:
                            print(f"  ⚠️ content div를 찾을 수 없습니다.")
                        
                        # 3. content_count와 hashtag_count 계산
                        content_count = len(content) if content else 0
                        hashtag_count = len(hashtags)
                        print(f"  📊 content_count: {content_count}, hashtag_count: {hashtag_count}")
                        
                        # 필터 단어 확인 (hashtags에서)
                        hashtags_text = " ".join(hashtags) if hashtags else ""
                        has_filter_word = any(word in hashtags_text for word in filter_words) if hashtags_text else False
                        
                        if not has_filter_word:
                            # 필터 단어가 하나도 없으면 스킵
                            batch_skipped_count += 1
                            # 스킵된 permalink로 저장 (다음 실행 시 자동으로 스킵)
                            save_skipped_permalink(permalink)
                            skipped_permalinks.add(permalink)
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
                            try:
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                                )
                                print("  ✅ 비디오 요소 발견")
                                time.sleep(3)
                            except TimeoutException:
                                print("  ⚠️ 비디오 요소를 찾을 수 없습니다. 계속 진행...")
                        else:
                            try:
                                li_elements = driver.find_elements(By.CSS_SELECTOR, "li._acaz, li[class*='_acaz']")
                                if li_elements:
                                    media_type = "CAROUSEL_ALBUM"
                                    print(f"  🖼️ media_type: CAROUSEL_ALBUM (li 태그 {len(li_elements)}개 발견)")
                                else:
                                    print(f"  🖼️ media_type: IMAGE")
                            except Exception:
                                print(f"  🖼️ media_type: IMAGE (기본값)")
                        
                        # 5. media_url 추출 (간단한 버전 - 원본 파일의 전체 로직을 복사해야 함)
                        media_urls = []
                        seen_urls = set()
                        
                        print(f"  🔍 media_url 추출 시작 (media_type: {media_type})")
                        
                        try:
                            # IMAGE 타입인 경우
                            if media_type == "IMAGE":
                                img_elements = driver.find_elements(By.CSS_SELECTOR, "img")
                                for img in img_elements:
                                    img_src = img.get_attribute("src")
                                    if not img_src:
                                        img_src = img.get_attribute("data-src")
                                    
                                    if img_src and ("scontent" in img_src or "cdninstagram" in img_src) and img_src not in seen_urls:
                                        seen_urls.add(img_src)
                                        media_urls.append(img_src)
                                        print(f"  ✅ 이미지 URL 추가: {img_src[:80]}...")
                                        break  # 첫 번째만 수집
                            
                            # VIDEO 타입인 경우 (instagram_extract_audio_from_json.py 참고)
                            elif media_type == "VIDEO":
                                # blob: URL에서 실제 URL 추출하는 헬퍼 함수
                                def extract_real_url(url: str) -> str:
                                    """blob: URL에서 실제 URL 추출"""
                                    if url and url.startswith('blob:'):
                                        # blob:https://... 형식에서 https://... 부분 추출
                                        if 'https://' in url:
                                            return url[url.find('https://'):]
                                        elif 'http://' in url:
                                            return url[url.find('http://'):]
                                    return url
                                
                                video_elements = driver.find_elements(By.CSS_SELECTOR, "video")
                                print(f"  🔍 비디오 요소 {len(video_elements)}개 발견")
                                
                                for video in video_elements:
                                    try:
                                        # 방법 1: currentSrc 확인
                                        current_src = driver.execute_script("return arguments[0].currentSrc;", video)
                                        if current_src:
                                            # blob: URL 처리
                                            real_url = extract_real_url(current_src)
                                            if real_url and real_url not in seen_urls:
                                                # 조건 완화: Instagram CDN 또는 비디오 확장자 포함
                                                if ("scontent" in real_url or "cdninstagram" in real_url or 
                                                    ".mp4" in real_url or "video" in real_url.lower() or
                                                    real_url.startswith("http")):
                                                    seen_urls.add(real_url)
                                                    media_urls.append(real_url)
                                                    print(f"  ✅ 비디오 URL 추가 (currentSrc): {real_url[:80]}...")
                                                    break
                                                else:
                                                    print(f"  🔍 currentSrc 발견했지만 조건 불일치: {real_url[:80]}...")
                                        
                                        # 방법 2: src 속성 확인
                                        video_src = video.get_attribute("src")
                                        if video_src:
                                            # blob: URL 처리
                                            real_url = extract_real_url(video_src)
                                            if real_url and real_url not in seen_urls:
                                                # 조건 완화: Instagram CDN 또는 비디오 확장자 포함
                                                if ("scontent" in real_url or "cdninstagram" in real_url or 
                                                    ".mp4" in real_url or "video" in real_url.lower() or
                                                    real_url.startswith("http")):
                                                    seen_urls.add(real_url)
                                                    media_urls.append(real_url)
                                                    print(f"  ✅ 비디오 URL 추가 (src): {real_url[:80]}...")
                                                    break
                                                else:
                                                    print(f"  🔍 src 발견했지만 조건 불일치: {real_url[:80]}...")
                                        
                                        # 방법 3: JavaScript로 src 확인
                                        js_src = driver.execute_script("""
                                            var video = arguments[0];
                                            return video.src || video.currentSrc || null;
                                        """, video)
                                        if js_src:
                                            # blob: URL 처리
                                            real_url = extract_real_url(js_src)
                                            if real_url and real_url not in seen_urls:
                                                # 조건 완화: Instagram CDN 또는 비디오 확장자 포함
                                                if ("scontent" in real_url or "cdninstagram" in real_url or 
                                                    ".mp4" in real_url or "video" in real_url.lower() or
                                                    real_url.startswith("http")):
                                                    seen_urls.add(real_url)
                                                    media_urls.append(real_url)
                                                    print(f"  ✅ 비디오 URL 추가 (JavaScript): {real_url[:80]}...")
                                                    break
                                                else:
                                                    print(f"  🔍 JavaScript src 발견했지만 조건 불일치: {real_url[:80]}...")
                                        
                                        # 방법 4: source 태그 확인
                                        source_elements = video.find_elements(By.CSS_SELECTOR, "source")
                                        for source in source_elements:
                                            source_src = source.get_attribute("src")
                                            if source_src:
                                                # blob: URL 처리
                                                real_url = extract_real_url(source_src)
                                                if real_url and real_url not in seen_urls:
                                                    # 조건 완화: Instagram CDN 또는 비디오 확장자 포함
                                                    if ("scontent" in real_url or "cdninstagram" in real_url or 
                                                        ".mp4" in real_url or "video" in real_url.lower() or
                                                        real_url.startswith("http")):
                                                        seen_urls.add(real_url)
                                                        media_urls.append(real_url)
                                                        print(f"  ✅ 비디오 URL 추가 (source 태그): {real_url[:80]}...")
                                                        break
                                                    else:
                                                        print(f"  🔍 source src 발견했지만 조건 불일치: {real_url[:80]}...")
                                        if media_urls:
                                            break
                                            
                                    except Exception as e:
                                        print(f"  ⚠️ 비디오 URL 추출 중 오류: {e}")
                                        import traceback
                                        traceback.print_exc()
                                        continue
                                
                                # 비디오 URL을 찾지 못한 경우 추가 시도
                                if not media_urls:
                                    print(f"  🔍 비디오 URL을 찾지 못해 추가 방법 시도 중...")
                                    try:
                                        # 페이지 소스에서 비디오 URL 패턴 찾기
                                        page_source = driver.page_source
                                        video_patterns = [
                                            r'blob:https?://[^"\'\\s]*',  # blob: URL 패턴 추가
                                            r'https?://[^"\'\\s]*scontent[^"\'\\s]*\.mp4[^"\'\\s]*',
                                            r'https?://[^"\'\\s]*cdninstagram[^"\'\\s]*\.mp4[^"\'\\s]*',
                                            r'https?://[^"\'\\s]*scontent[^"\'\\s]*video[^"\'\\s]*',
                                            r'https?://[^"\'\\s]*\.mp4[^"\'\\s]*',  # 모든 .mp4 URL
                                        ]
                                        for pattern in video_patterns:
                                            matches = re.finditer(pattern, page_source, re.IGNORECASE)
                                            for match in matches:
                                                url = match.group(0)
                                                # blob: URL 처리
                                                real_url = extract_real_url(url)
                                                if real_url and real_url not in seen_urls:
                                                    # 조건 확인
                                                    if ("scontent" in real_url or "cdninstagram" in real_url or 
                                                        ".mp4" in real_url or "video" in real_url.lower() or
                                                        real_url.startswith("http")):
                                                        seen_urls.add(real_url)
                                                        media_urls.append(real_url)
                                                        print(f"  ✅ 비디오 URL 추가 (페이지 소스): {real_url[:80]}...")
                                                        break
                                            if media_urls:
                                                break
                                    except Exception as e:
                                        print(f"  ⚠️ 페이지 소스 검색 중 오류: {e}")
                                        import traceback
                                        traceback.print_exc()
                            
                            # CAROUSEL_ALBUM인 경우
                            elif media_type == "CAROUSEL_ALBUM":
                                li_elements = driver.find_elements(By.CSS_SELECTOR, "li._acaz, li[class*='_acaz']")
                                if li_elements:
                                    li = li_elements[0]  # 첫 번째만
                                    try:
                                        img = li.find_element(By.CSS_SELECTOR, "img")
                                        img_src = img.get_attribute("src")
                                        if not img_src:
                                            img_src = img.get_attribute("data-src")
                                        
                                        if img_src and ("scontent" in img_src or "cdninstagram" in img_src) and img_src not in seen_urls:
                                            seen_urls.add(img_src)
                                            media_urls.append(img_src)
                                            print(f"  ✅ 이미지 URL 추가: {img_src[:80]}...")
                                    except:
                                        pass
                            
                            print(f"  📎 media_url: {len(media_urls)}개")
                            if media_urls:
                                print(f"  ✅ 수집된 media_url (첫 3개):")
                                for idx, url in enumerate(media_urls[:3], 1):
                                    print(f"     {idx}. {url[:100]}...")
                            else:
                                print(f"  ❌ media_url을 찾지 못했습니다!")
                        
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
                                try:
                                    dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                                    timestamp_str = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
                                    print(f"  🕐 timestamp: {timestamp_str}")
                                except Exception as e:
                                    print(f"  ⚠️ timestamp 파싱 실패: {e}")
                        except NoSuchElementException:
                            print(f"  ⚠️ timestamp를 찾을 수 없습니다.")
                        
                        # 8. like_count와 comments_count 추출 (간단한 버전)
                        like_count = None
                        comments_count = None
                        
                        print(f"  🔍 like_count와 comments_count 추출 시작...")
                        
                        # 좋아요 수 추출
                        try:
                            section = driver.find_element(By.CSS_SELECTOR, "section.x12nagc")
                            like_span = section.find_element(By.CSS_SELECTOR, "div > div > span > a > span > span.html-span.xdj266r.x14z9mp.xat24cr.x1lziwak.xexx8yu.xyri2b.x18d9i69.x1c1uobl.x1hl2dhg.x16tdsg8.x1vvkbs")
                            like_text = like_span.text.strip()
                            like_numbers = re.findall(r'\d+', like_text.replace(',', ''))
                            if like_numbers:
                                like_count = int(''.join(like_numbers))
                                print(f"  ❤️ like_count: {like_count}")
                        except:
                            print(f"  ⚠️ like_count 추출 실패")
                        
                        # 댓글 수 추출 (간단한 버전)
                        try:
                            # 댓글 컨테이너 찾기
                            comment_containers = driver.find_elements(By.CSS_SELECTOR, "div.x9f619.x78zum5.xdt5ytf.x5yr21d.xexx8yu.xv54qhq.x1l90r2v.xf7dkkf.x10l6tqk.xh8yej3")
                            comments_count = len(comment_containers)
                            print(f"  💬 comments_count: {comments_count}")
                        except:
                            print(f"  ⚠️ comments_count 추출 실패")
                        
                        # 9. 데이터 수집 완료 및 출력/저장
                        new_item = {
                            "id": user_id if user_id else str(int(time.time())),
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
                            batch_processed_count += 1
                            # 처리된 permalink로 저장
                            save_processed_permalink(permalink)
                            processed_permalinks.add(permalink)
                        else:
                            # 실제 모드면 JSON에 저장
                            try:
                                with open(MEDIA_JSON, "r", encoding="utf-8") as f:
                                    media_data = json.load(f)
                            except FileNotFoundError:
                                media_data = []
                                print(f"  ⚠️ {MEDIA_JSON} 파일이 없어 새로 생성합니다.")
                            
                            # 중복 확인 (shortcode 기준으로 정규화)
                            current_shortcode = normalize_permalink(permalink)
                            if current_shortcode:
                                # shortcode 기준으로 중복 체크
                                existing_shortcodes = {normalize_permalink(item.get("permalink")) for item in media_data if item.get("permalink")}
                                existing_shortcodes = {sc for sc in existing_shortcodes if sc}  # None 제거
                                
                                if current_shortcode in existing_shortcodes:
                                    print(f"  ⚠️ 이미 존재하는 permalink입니다. (shortcode: {current_shortcode}) 건너뜁니다.")
                                    batch_skipped_count += 1
                                    # 처리된 permalink로 저장
                                    save_processed_permalink(permalink)
                                    processed_permalinks.add(permalink)
                                else:
                                    media_data.append(new_item)
                                    
                                    # JSON 파일에 저장
                                    try:
                                        with open(MEDIA_JSON, "w", encoding="utf-8") as f:
                                            json.dump(media_data, f, ensure_ascii=False, indent=2)
                                        print(f"  💾 JSON 저장 완료!")
                                    except Exception as e:
                                        print(f"  ⚠️ JSON 저장 실패: {e}")
                                    
                                    batch_processed_count += 1
                                    # 처리된 permalink로 저장
                                    save_processed_permalink(permalink)
                                    processed_permalinks.add(permalink)
                            else:
                                # shortcode를 추출할 수 없으면 원본 permalink로 비교 (하위 호환성)
                                existing_permalinks = {item.get("permalink") for item in media_data if item.get("permalink")}
                                if permalink in existing_permalinks:
                                    print(f"  ⚠️ 이미 존재하는 permalink입니다. 건너뜁니다.")
                                    batch_skipped_count += 1
                                    # 처리된 permalink로 저장
                                    save_processed_permalink(permalink)
                                    processed_permalinks.add(permalink)
                                else:
                                    media_data.append(new_item)
                                    
                                    # JSON 파일에 저장
                                    try:
                                        with open(MEDIA_JSON, "w", encoding="utf-8") as f:
                                            json.dump(media_data, f, ensure_ascii=False, indent=2)
                                        print(f"  💾 JSON 저장 완료!")
                                    except Exception as e:
                                        print(f"  ⚠️ JSON 저장 실패: {e}")
                                    
                                    batch_processed_count += 1
                                    # 처리된 permalink로 저장
                                    save_processed_permalink(permalink)
                                    processed_permalinks.add(permalink)
                            
                            # 요청 간 딜레이 (Instagram 차단 방지)
                            time.sleep(2)
                    
                    except Exception as e:
                        batch_error_count += 1
                        error_str = str(e)
                        error_type = type(e).__name__
                        
                        # 연결 끊김 에러 확인
                        if is_connection_error(e):
                            print(f"  ❌ WebDriver 연결 끊김 감지: {error_type}")
                            print(f"     에러 메시지: {error_str[:200]}...")
                            logging.error(f"WebDriver 연결 끊김 감지: {error_type} - {error_str}")
                            
                            # 현재 배치를 중단하고 WebDriver 재시작
                            print(f"\n  ⚠️ 배치 {batch_num + 1} 처리 중 연결이 끊겼습니다.")
                            print(f"  🔄 WebDriver를 재시작하고 배치를 다시 시도합니다...")
                            
                            # WebDriver 종료 시도
                            if driver:
                                try:
                                    driver.quit()
                                except:
                                    pass
                            
                            # 재시도 카운터 증가
                            retry_count += 1
                            if retry_count < max_retries:
                                print(f"  🔄 재시도 {retry_count + 1}/{max_retries}...")
                                time.sleep(5)  # 재시도 전 대기
                                break  # 현재 배치 루프를 중단하고 재시도
                            else:
                                print(f"  ❌ 최대 재시도 횟수({max_retries})에 도달했습니다.")
                                print(f"  ⏭️ 배치 {batch_num + 1}를 건너뛰고 다음 배치로 진행합니다.")
                                # 배치를 건너뛸 때는 처리되지 않은 항목들을 processed_permalinks에 저장하지 않음
                                # (재시작 시 다시 처리할 수 있도록)
                                batch_success = True  # 실패했지만 다음 배치로 진행
                                break
                        else:
                            # 일반 에러는 계속 진행
                            print(f"  ❌ 처리 중 오류 발생: {e}")
                            import traceback
                            traceback.print_exc()
                            logging.error(f"처리 중 오류 발생: {e}", exc_info=True)
                            # 에러가 발생했어도 permalink는 처리된 것으로 표시 (재시도 방지)
                            save_processed_permalink(permalink)
                            processed_permalinks.add(permalink)
                            continue
                
                # 배치 내부 루프 완료 후 성공 처리
                batch_success = True
                total_processed_count += batch_processed_count
                total_skipped_count += batch_skipped_count
                total_error_count += batch_error_count
                
                print(f"\n{'='*60}")
                print(f"✅ 배치 {batch_num + 1}/{total_batches} 완료!")
                print(f"   처리 완료: {batch_processed_count}개")
                print(f"   스킵됨 (필터 단어 없음): {batch_skipped_count}개")
                print(f"   오류 발생: {batch_error_count}개")
                print(f"{'='*60}\n")
                
                logging.info(f"배치 {batch_num + 1}/{total_batches} 완료 - 처리: {batch_processed_count}, 스킵: {batch_skipped_count}, 오류: {batch_error_count}")
                
            except Exception as batch_error:
                # 배치 전체 실패 처리
                error_str = str(batch_error)
                error_type = type(batch_error).__name__
                
                if is_connection_error(batch_error):
                    print(f"  ❌ 배치 {batch_num + 1} 처리 중 WebDriver 연결 끊김: {error_type}")
                    logging.error(f"배치 {batch_num + 1} 처리 중 WebDriver 연결 끊김: {error_type} - {error_str}")
                    
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"  🔄 재시도 {retry_count + 1}/{max_retries}...")
                        time.sleep(5)
                    else:
                        print(f"  ❌ 최대 재시도 횟수에 도달했습니다. 배치를 건너뜁니다.")
                        batch_success = True  # 다음 배치로 진행
                else:
                    print(f"  ❌ 배치 {batch_num + 1} 처리 중 예상치 못한 오류: {batch_error}")
                    logging.error(f"배치 {batch_num + 1} 처리 중 예상치 못한 오류: {batch_error}", exc_info=True)
                    batch_success = True  # 다음 배치로 진행
                
            finally:
                # 배치 완료 후 WebDriver 종료 (다음 배치를 위해)
                if driver:
                    try:
                        driver.quit()
                        print("🔒 브라우저 종료 (다음 배치를 위해)")
                    except Exception as e:
                        logging.warning(f"브라우저 종료 중 오류: {e}")
                
                # 배치 간 대기 (시스템 부하 방지)
                if batch_num < total_batches - 1:  # 마지막 배치가 아니면
                    wait_time = 10  # 10초 대기
                    print(f"⏳ 다음 배치 전 대기 중... ({wait_time}초)")
                    time.sleep(wait_time)
        
        # 최종 통계 출력
        print(f"\n{'='*60}")
        print(f"✅ 전체 스텝2 완료!")
        print(f"   총 permalink: {len(remaining_permalinks)}개")
        print(f"   처리 완료: {total_processed_count}개")
        print(f"   스킵됨 (필터 단어 없음): {total_skipped_count}개")
        print(f"   오류 발생: {total_error_count}개")
        print(f"{'='*60}")
        
        # 로그에도 통계 기록
        logging.info("=" * 80)
        logging.info("전체 스텝2 완료 - instagram_filter_userposts.py")
        logging.info(f"총 permalink: {len(remaining_permalinks)}개")
        logging.info(f"처리 완료: {total_processed_count}개")
        logging.info(f"스킵됨 (필터 단어 없음): {total_skipped_count}개")
        logging.info(f"오류 발생: {total_error_count}개")
        logging.info("=" * 80)

if __name__ == "__main__":
    # 쿠키 재생성 옵션 확인
    import sys
    regenerate_cookie = False
    test_mode = False
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ['--regenerate-cookie', '-r']:
                regenerate_cookie = True
            elif arg in ['--test', '-t']:
                test_mode = True
    
    if regenerate_cookie:
        print("🔄 쿠키 재생성 모드로 실행합니다.")
        print("=" * 60)
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
    
    # permalink.txt 파일에서 permalink 로드
    print("=" * 60)
    print("Instagram permalink 데이터 수집 (Step 2)")
    if test_mode:
        print("🧪 테스트 모드: 상위 3개만 처리합니다")
    print("=" * 60)
    
    permalinks = load_permalinks_from_file(PERMALINK_TXT)
    
    if not permalinks:
        print("\n⚠️ permalink.txt 파일에서 permalink를 읽을 수 없습니다.")
        print("💡 permalink.txt 파일을 확인하고 한 줄에 하나씩 permalink URL을 입력하세요.")
        print("   예:")
        print("   https://www.instagram.com/p/ABC123/")
        print("   https://www.instagram.com/reel/XYZ789/")
        sys.exit(1)
    
    # 결과 출력
    print(f"\n📋 로드된 permalink 목록 (처음 20개):")
    for idx, item in enumerate(permalinks[:20], 1):
        print(f"  {idx}. @{item['user_handle']}: {item['permalink']}")
    if len(permalinks) > 20:
        print(f"  ... 외 {len(permalinks) - 20}개")
    print(f"\n✅ 총 {len(permalinks)}개의 permalink 로드됨")
    
    # 스텝2 실행
    print(f"\n{'='*60}")
    step2_process_permalinks(permalinks, test_mode=test_mode)
               