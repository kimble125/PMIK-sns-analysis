import json
import time
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
import pickle
import shutil
import logging

# .env 파일에서 로그인 정보 불러오기
load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

# JSON 파일 경로
USER_JSON = Path("instagram_user.json")
MEDIA_JSON = Path("instagram_media.json")
PERMALINK_TXT = Path("permalink.txt")
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
    """Selenium WebDriver 설정 (리눅스 환경 대응)"""
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
                        print(f"우선 경로로 Chrome 경로 발견: {resolved_str}")
    
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
                print(f"which 명령어로 Chrome 경로 발견: {resolved_str}")
    
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
                    print(f"Chrome 브라우저 경로 발견 (실행 가능): {resolved_str}")
    
    if not chrome_path_candidates:
        error_msg = "실행 가능한 Chrome 브라우저를 찾을 수 없습니다."
        print(f"❌ {error_msg}")
        print("💡 해결 방법:")
        print("   1. Chrome 브라우저가 설치되어 있는지 확인하세요")
        print("   2. 다음 명령어로 Chrome을 설치할 수 있습니다:")
        print("      sudo apt-get update && sudo apt-get install -y google-chrome-stable")
        print("   3. 또는 Chromium을 설치할 수 있습니다:")
        print("      sudo apt-get install -y chromium-browser")
        raise RuntimeError(error_msg)
    
    # 경로 시도 순서 로그 출력
    print(f"Chrome 경로 시도 순서 (총 {len(chrome_path_candidates)}개):")
    for i, path in enumerate(chrome_path_candidates[:5], 1):  # 처음 5개만 출력
        print(f"  {i}. {path.as_posix()}")
    
    # 각 경로를 시도하여 실제로 작동하는지 확인
    last_error = None
    for chrome_path in chrome_path_candidates:
        chrome_binary_location = chrome_path.as_posix()
        print(f"Chrome 경로 시도: {chrome_binary_location}")
        
        chrome_options = Options()
        chrome_options.binary_location = chrome_binary_location
        
        # Headless 모드 설정 (리눅스 환경 대응)
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Performance 로그 활성화 (네트워크 로그에서 비디오 URL 찾기 위해)
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_window_size(1920, 1080)  # 창 크기 설정
            
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
            
            print(f"Chrome WebDriver 초기화 성공: {chrome_binary_location}")
            return driver
        except Exception as e:
            last_error = e
            print(f"Chrome 경로 실패 ({chrome_binary_location}): {str(e)}")
            continue
    
    # 모든 경로가 실패한 경우
    error_msg = f"모든 Chrome 경로 시도 실패. 마지막 오류: {str(last_error)}"
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

def login_instagram(driver):
    """Instagram 로그인 (쿠키가 없을 경우)"""
    if COOKIE_PATH.exists():
        try:
            print("🍪 저장된 쿠키 로드 중...")
            driver.get("https://www.instagram.com")
            time.sleep(2)
            
            cookies = pickle.load(open(COOKIE_PATH, "rb"))
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"  ⚠️ 쿠키 추가 실패: {e}")
            
            driver.refresh()
            time.sleep(3)
            
            # 로그인 확인
            if "login" not in driver.current_url.lower():
                print("✅ 쿠키로 로그인 성공")
                return True
        except Exception as e:
            print(f"⚠️ 쿠키 로드 실패: {e}")
    
    # 쿠키가 없거나 실패한 경우 수동 로그인
    if USERNAME and PASSWORD:
        print("🔐 수동 로그인 시도 중...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        
        try:
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_input = driver.find_element(By.NAME, "password")
            
            username_input.send_keys(USERNAME)
            password_input.send_keys(PASSWORD)
            
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            # 쿠키 저장
            pickle.dump(driver.get_cookies(), open(COOKIE_PATH, "wb"))
            print("✅ 로그인 성공 및 쿠키 저장")
            return True
        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
            return False
    else:
        print("⚠️ 로그인 정보가 없습니다. 수동으로 로그인해주세요.")
        input("로그인 후 Enter를 눌러주세요...")
        pickle.dump(driver.get_cookies(), open(COOKIE_PATH, "wb"))
        return True

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

def load_existing_permalinks():
    """기존 permalink.txt 파일에서 permalink 로드 (중복 체크용)"""
    existing_permalinks_set = set()  # 빠른 비교를 위한 set
    existing_permalinks_map = {}  # {shortcode: original_permalink} 디버깅용
    
    if PERMALINK_TXT.exists():
        try:
            with open(PERMALINK_TXT, "r", encoding="utf-8") as f:
                for line in f:
                    permalink = line.strip()
                    if permalink:
                        shortcode = normalize_permalink(permalink)
                        if shortcode:
                            existing_permalinks_set.add(shortcode)
                            existing_permalinks_map[shortcode] = permalink
            print(f"✅ 기존 permalink {len(existing_permalinks_set)}개 로드됨 (shortcode 기준)")
            # 디버깅: 처음 5개 샘플 출력
            if existing_permalinks_map:
                sample_items = list(existing_permalinks_map.items())[:5]
                print(f"   샘플 (처음 5개):")
                for shortcode, orig_url in sample_items:
                    print(f"     - shortcode: {shortcode} | 원본: {orig_url}")
        except Exception as e:
            print(f"⚠️ {PERMALINK_TXT} 파일 로드 중 오류: {e}")
            print("  중복 체크 없이 진행합니다.")
    else:
        print(f"⚠️ {PERMALINK_TXT} 파일이 없습니다. 중복 체크 없이 진행합니다.")
    
    return existing_permalinks_set, existing_permalinks_map

def save_permalinks_to_file(new_permalinks):
    """
    새로운 permalink들을 permalink.txt 파일에 추가 (append 모드)
    기존 파일 내용을 유지하고 새 permalink를 이어서 추가합니다 (덮어쓰기 아님)
    """
    if not new_permalinks:
        return
    
    try:
        # "a" 모드: append 모드 - 파일이 없으면 생성, 있으면 기존 내용 뒤에 추가
        with open(PERMALINK_TXT, "a", encoding="utf-8") as f:
            for permalink in new_permalinks:
                f.write(permalink + "\n")
        print(f"✅ {len(new_permalinks)}개의 permalink을 {PERMALINK_TXT}에 추가 저장했습니다. (기존 내용 유지)")
    except Exception as e:
        print(f"⚠️ {PERMALINK_TXT} 파일 저장 중 오류: {e}")

# ============================================
# 스텝1: 사용자 프로필에서 게시물 permalink 수집
# ============================================
# test_mode에서 True: 상위 1개의 데이터 테스트, False: 전체 데이터 테스트
def step1_collect_post_permalinks(test_mode=True):
    """
    스텝1: instagram_user.json에서 handle 정보를 가져와서
    각 사용자 프로필 페이지에 접속하여 스크롤하며
    게시물의 href를 수집하여 permalink.txt 파일에 저장
    
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
    logging.info("프로그램 시작 - instagram_crawling_postpermalink.py (스텝1)")
    if test_mode:
        logging.info("테스트 모드: 첫 번째 handle만 처리")
    logging.info("=" * 80)
    
    print("=" * 60)
    print("스텝1: 사용자 프로필에서 게시물 permalink 수집 및 중복 제거")
    if test_mode:
        print(f"🧪 테스트 모드: 첫 번째 handle만 처리")
    print("=" * 60)
    
    # permalink.txt에서 기존 permalink 로드 (중복 체크용)
    print(f"\n📂 {PERMALINK_TXT} 파일 로딩 중 (기존 permalink 확인용)...")
    existing_permalinks_set, existing_permalinks_map = load_existing_permalinks()
    
    # instagram_media.json에서도 기존 permalink 로드 (추가 중복 체크용)
    print(f"\n📂 {MEDIA_JSON} 파일 로딩 중 (추가 중복 체크용)...")
    try:
        if MEDIA_JSON.exists():
            with open(MEDIA_JSON, "r", encoding="utf-8") as f:
                media_data = json.load(f)
            for item in media_data:
                permalink = item.get("permalink")
                if permalink:
                    shortcode = normalize_permalink(permalink)
                    if shortcode:
                        existing_permalinks_set.add(shortcode)
                        if shortcode not in existing_permalinks_map:
                            existing_permalinks_map[shortcode] = permalink
            print(f"✅ {MEDIA_JSON}에서 추가로 {len(existing_permalinks_set)}개 (전체) 로드됨")
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
        return
    except json.JSONDecodeError:
        print(f"❌ {USER_JSON} 파일의 JSON 형식이 올바르지 않습니다.")
        return
    
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
            return
        
        # permalink 저장용 리스트 (파일에 저장할 permalink URL만)
        new_permalinks_to_save = []
        
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
                # 프로필 페이지 접속
                driver.get(profile_url)
                time.sleep(3)
                
                # 프로필 페이지 로드 대기
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "article"))
                    )
                    print("  ✅ 프로필 페이지 로드 완료")
                except TimeoutException:
                    print("  ⚠️ 프로필 페이지 로드 타임아웃, 계속 진행...")
                
                # 게시물 href 수집 (원본 URL과 shortcode 매핑 저장)
                collected_hrefs_map = {}  # {shortcode: original_url} - 원본 URL 보존
                collected_shortcodes = set()  # 중복 체크용 shortcode set
                previous_div_count = 0
                previous_href_count = 0
                no_new_content_count = 0
                max_no_new_content = 5  # 연속으로 새 콘텐츠(div 또는 href)가 생성되지 않으면 종료
                scroll_count = 0
                
                print("  📜 스크롤하며 href 수집 시작...")
                print("  📊 초기 상태 확인 중...")
                
                while True:
                    scroll_count += 1
                    
                    # 현재 페이지에서 div 개수와 href 수집
                    try:
                        # div._ac7v.x1ty9z65.xzboxd6 개수 확인 (스크롤 시 생성되는 div)
                        post_divs = driver.find_elements(
                            By.CSS_SELECTOR,
                            "div._ac7v.x1ty9z65.xzboxd6"
                        )
                        current_div_count = len(post_divs)
                        
                        # 특정 구조 내의 a 태그 찾기
                        # <div class="_ac7v x1ty9z65 xzboxd6"> 내부의
                        # <div class="x1lliihq x1n2onr6 xh8yej3 x4gyw5p x14z9mp xhe4ym4 xaudc5v x1j53mea"> 내부의
                        # <a> 태그의 href 수집
                        
                        # 방법 1: CSS 선택자로 직접 찾기
                        post_links = driver.find_elements(
                            By.CSS_SELECTOR,
                            "div._ac7v.x1ty9z65.xzboxd6 div.x1lliihq.x1n2onr6.xh8yej3.x4gyw5p.x14z9mp.xhe4ym4.xaudc5v.x1j53mea a[href*='/p/'], "
                            "div._ac7v.x1ty9z65.xzboxd6 div.x1lliihq.x1n2onr6.xh8yej3.x4gyw5p.x14z9mp.xhe4ym4.xaudc5v.x1j53mea a[href*='/reel/']"
                        )
                        
                        # 방법 2: 더 넓은 범위로 찾기 (방법 1이 실패할 경우)
                        if not post_links:
                            post_links = driver.find_elements(
                                By.CSS_SELECTOR,
                                "div._ac7v a[href*='/p/'], div._ac7v a[href*='/reel/']"
                            )
                        
                        # href 수집
                        new_hrefs_count = 0
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
                    
                    # 스크롤 다운 (스크롤 이벤트) - 점진적 스크롤로 변경
                    try:
                        # 점진적으로 스크롤 (로딩 시간 확보)
                        current_scroll = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
                        scroll_height = driver.execute_script("return document.body.scrollHeight;")
                        
                        # 여러 단계로 나누어 스크롤 (더 많은 단계로)
                        scroll_steps = 5
                        scroll_increment = (scroll_height - current_scroll) / scroll_steps
                        
                        for step in range(scroll_steps):
                            scroll_position = current_scroll + scroll_increment * (step + 1)
                            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                            time.sleep(2)  # 각 단계마다 대기 시간
                        
                        # 최종적으로 페이지 끝까지 스크롤
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(4)  # 스크롤 후 콘텐츠 로드 대기 시간
                        
                        # 추가로 약간 더 스크롤 (lazy loading 트리거)
                        driver.execute_script("window.scrollBy(0, 500);")
                        time.sleep(2.5)
                        
                        # 한 번 더 위로 스크롤 후 아래로 (로딩 트리거)
                        driver.execute_script("window.scrollBy(0, -200);")
                        time.sleep(1)
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
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
                        new_permalinks.append(original_url)
                        # 기존 set에도 추가 (같은 사용자 내에서 중복 방지)
                        existing_permalinks_set.add(shortcode)
                    else:
                        # 중복 permalink
                        duplicate_count += 1
                        # 디버깅: 처음 5개 중복 샘플 저장
                        if len(duplicate_samples) < 5:
                            existing_orig = existing_permalinks_map.get(shortcode, "알 수 없음")
                            duplicate_samples.append(f"shortcode: {shortcode} | 수집한: {original_url} | 기존: {existing_orig}")
                
                # 수집된 permalink를 리스트에 추가 (중복 제거된 것만)
                new_permalinks_to_save.extend(new_permalinks)
                
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
                
                # 요청 간 딜레이 (Instagram 차단 방지)
                time.sleep(2)
            
            except Exception as e:
                print(f"  ❌ 프로필 페이지 처리 중 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 수집한 permalink를 파일에 저장
        if new_permalinks_to_save:
            save_permalinks_to_file(new_permalinks_to_save)
        
        # handle별 통계 계산
        handle_stats = {}
        # permalink에서 user_handle 추출 (정확하지 않지만 대략적인 통계용)
        for permalink in new_permalinks_to_save:
            # permalink에서 handle 추출 시도 (예: https://www.instagram.com/username/p/...)
            parts = permalink.split("/")
            if len(parts) >= 4 and parts[2] == "www.instagram.com":
                handle = parts[3]
                if handle not in ['p', 'reel', 'stories', 'explore', 'accounts']:
                    if handle not in handle_stats:
                        handle_stats[handle] = 0
                    handle_stats[handle] += 1
        
        print(f"\n{'='*60}")
        print(f"✅ 스텝1 완료!")
        print(f"   총 수집된 신규 permalink: {len(new_permalinks_to_save)}개")
        print(f"\n📊 handle별 신규 permalink 개수 (대략적):")
        for handle, count in sorted(handle_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   - @{handle}: {count}개")
        print(f"{'='*60}")
        
        return new_permalinks_to_save
        
    finally:
        driver.quit()
        print("\n🔒 브라우저 종료")

if __name__ == "__main__":
    # 스텝1 실행 (전체 모드: 모든 handle 처리)
    permalinks = step1_collect_post_permalinks(test_mode=False)
    
    # 결과 출력
    if permalinks:
        print(f"\n📋 수집된 permalink 목록 (처음 20개):")
        for idx, permalink in enumerate(permalinks[:20], 1):
            print(f"  {idx}. {permalink}")
        if len(permalinks) > 20:
            print(f"  ... 외 {len(permalinks) - 20}개")
        print(f"\n✅ 총 {len(permalinks)}개의 permalink 수집됨")
        print(f"✅ 모든 permalink이 {PERMALINK_TXT} 파일에 저장되었습니다.")
    else:
        print("\n⚠️ 수집된 permalink가 없습니다.")

