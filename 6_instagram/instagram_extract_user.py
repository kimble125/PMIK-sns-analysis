import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
import os
import shutil

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# JSON 파일 경로
INPUT_JSON = Path("instagram_media.json")
OUTPUT_JSON = Path("instagram_user.json")
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

# 테스트 모드: 이 변수에 URL을 설정하면 해당 URL만 테스트합니다
# 예: TEST_URL = "https://www.instagram.com/reel/DQ7AdRnAcSa/"
TEST_URL = None  # None이면 전체 실행, URL이 있으면 테스트 모드

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
    for chrome_path in chrome_path_candidates:
        chrome_binary_location = chrome_path.as_posix()
        logging.info(f"Chrome 경로 시도: {chrome_binary_location}")
        
        chrome_options = Options()
        chrome_options.binary_location = chrome_binary_location
        
        chrome_options.add_argument("--headless")  # 브라우저 창 숨기기
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
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

def extract_user_handle(driver, permalink):
    """permalink에서 사용자 핸들 추출"""
    try:
        print(f"  🔍 접속 중: {permalink}")
        driver.get(permalink)
        
        # 페이지 로드 대기 (더 긴 대기 시간)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            print(f"  ✅ article 태그 로드 완료")
        except TimeoutException:
            print(f"  ⚠️ article 태그 로드 타임아웃, 계속 진행...")
        
        time.sleep(3)  # 추가 대기
        
        # 사용자 핸들을 찾기 위한 여러 시도
        user_handle = None
        
        # 방법 1: article 내에서 a 태그의 href에서 추출 (가장 안정적)
        try:
            wait = WebDriverWait(driver, 10)
            article = wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
            
            # article 내의 모든 a 태그 찾기
            links = article.find_elements(By.CSS_SELECTOR, "a[href*='/']")
            for link in links:
                href = link.get_attribute("href")
                if href and "/" in href:
                    # Instagram 사용자 프로필 URL 패턴: https://www.instagram.com/username/
                    parts = href.split("/")
                    if len(parts) >= 4 and parts[2] == "www.instagram.com" and parts[3] and parts[3] != "":
                        potential_handle = parts[3]
                        # 사용자 핸들 형식 검증 (알파벳, 숫자, 언더스코어, 점만 포함)
                        if potential_handle.replace("_", "").replace(".", "").isalnum() and len(potential_handle) > 0:
                            user_handle = potential_handle
                            print(f"  ✅ 사용자 핸들 발견 (href 추출): {user_handle}")
                            return user_handle
        except (TimeoutException, NoSuchElementException) as e:
            print(f"  ⚠️ 방법 1 실패: {e}")
        
        # 방법 2: JavaScript로 article 내에서 사용자 링크 찾기
        try:
            script = """
            var article = document.querySelector('article');
            if (!article) return null;
            
            // article 내의 모든 a 태그 찾기
            var links = article.querySelectorAll('a[href*="/"]');
            for (var i = 0; i < links.length; i++) {
                var href = links[i].getAttribute('href');
                if (href && href.includes('instagram.com/')) {
                    var parts = href.split('/');
                    if (parts.length >= 4 && parts[2] === 'www.instagram.com' && parts[3] && parts[3] !== '') {
                        var handle = parts[3];
                        // 사용자 핸들 형식 검증
                        if (/^[a-zA-Z0-9._]+$/.test(handle) && handle.length > 0 && handle !== 'p' && handle !== 'reel' && handle !== 'stories') {
                            return handle;
                        }
                    }
                }
            }
            return null;
            """
            user_handle = driver.execute_script(script)
            if user_handle:
                print(f"  ✅ 사용자 핸들 발견 (JavaScript href): {user_handle}")
                return user_handle
        except Exception as e:
            print(f"  ⚠️ JavaScript 실행 실패: {e}")
        
        # 방법 3: 지정된 클래스로 찾기 (기존 방법)
        try:
            wait = WebDriverWait(driver, 5)
            element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span._ap3a._aaco._aacw._aacx._aad7._aade"))
            )
            user_handle = element.text.strip()
            if user_handle:
                print(f"  ✅ 사용자 핸들 발견 (클래스): {user_handle}")
                return user_handle
        except (TimeoutException, NoSuchElementException):
            pass
        
        # 방법 4: 더 넓은 범위의 클래스 패턴으로 찾기
        try:
            # article 내에서 span 요소들 중 사용자 핸들 같은 텍스트 찾기
            article = driver.find_element(By.TAG_NAME, "article")
            spans = article.find_elements(By.CSS_SELECTOR, "span")
            for span in spans:
                text = span.text.strip()
                # 사용자 핸들 형식 검증 (알파벳, 숫자, 언더스코어, 점만 포함, 길이 제한)
                if text and len(text) > 0 and len(text) < 50:
                    if text.replace("_", "").replace(".", "").isalnum() and not text.startswith("http"):
                        # 링크가 있는지 확인
                        try:
                            parent_link = span.find_element(By.XPATH, "./ancestor::a[1]")
                            href = parent_link.get_attribute("href")
                            if href and "/" in href and "instagram.com" in href:
                                parts = href.split("/")
                                if len(parts) >= 4 and parts[2] == "www.instagram.com" and parts[3] == text:
                                    user_handle = text
                                    print(f"  ✅ 사용자 핸들 발견 (span 텍스트): {user_handle}")
                                    return user_handle
                        except NoSuchElementException:
                            pass
        except Exception as e:
            print(f"  ⚠️ 방법 4 실패: {e}")
        
        # 방법 5: 전체 HTML에서 검색 (BeautifulSoup 사용)
        if HAS_BS4:
            try:
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # article 태그 찾기
                article = soup.find('article')
                if article:
                    # article 내의 모든 a 태그 찾기
                    links = article.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if href and 'instagram.com/' in href:
                            parts = href.split('/')
                            if len(parts) >= 4 and parts[2] == 'www.instagram.com' and parts[3] and parts[3] != '':
                                potential_handle = parts[3]
                                if potential_handle.replace("_", "").replace(".", "").isalnum() and len(potential_handle) > 0:
                                    if potential_handle not in ['p', 'reel', 'stories', 'explore', 'accounts']:
                                        user_handle = potential_handle
                                        print(f"  ✅ 사용자 핸들 발견 (BeautifulSoup): {user_handle}")
                                        return user_handle
            except Exception as e:
                print(f"  ⚠️ BeautifulSoup 파싱 실패: {e}")
        
        # 방법 6: JavaScript로 더 광범위하게 검색
        try:
            script = """
            var article = document.querySelector('article');
            if (!article) {
                // article이 없으면 전체 페이지에서 검색
                article = document.body;
            }
            
            // 모든 span 요소 검색
            var spans = article.querySelectorAll('span');
            for (var i = 0; i < spans.length; i++) {
                var text = spans[i].textContent.trim();
                if (text && /^[a-zA-Z0-9._]+$/.test(text) && text.length > 0 && text.length < 50) {
                    // 부모 또는 조상 요소 중 a 태그 찾기
                    var parent = spans[i];
                    for (var j = 0; j < 5; j++) {
                        if (parent.tagName === 'A') {
                            var href = parent.getAttribute('href');
                            if (href && href.includes('instagram.com/')) {
                                var parts = href.split('/');
                                if (parts.length >= 4 && parts[2] === 'www.instagram.com' && parts[3] === text) {
                                    if (parts[3] !== 'p' && parts[3] !== 'reel' && parts[3] !== 'stories') {
                                        return text;
                                    }
                                }
                            }
                        }
                        parent = parent.parentElement;
                        if (!parent) break;
                    }
                }
            }
            return null;
            """
            user_handle = driver.execute_script(script)
            if user_handle:
                print(f"  ✅ 사용자 핸들 발견 (JavaScript 광범위 검색): {user_handle}")
                return user_handle
        except Exception as e:
            print(f"  ⚠️ JavaScript 광범위 검색 실패: {e}")
        
        print(f"  ❌ 사용자 핸들을 찾을 수 없습니다")
        return None
        
    except Exception as e:
        print(f"  ❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_existing_data():
    """기존 결과 파일 로드 (모든 필드 보존)"""
    if OUTPUT_JSON.exists():
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                # 기존 데이터의 모든 필드를 보존 (user_name, introduce, linked_page, followers 등)
                # instagram_save_userinfo.py에서 추가한 필드도 보존
                converted_data = []
                for item in existing_data:
                    # user_handle이 있고 id가 있는 경우만 포함
                    if item.get("user_handle") and item.get("id"):
                        # 기존 항목의 모든 필드를 보존 (followers 포함)
                        converted_data.append(item.copy())
                print(f"📂 기존 데이터 {len(converted_data)}개 로드됨 (모든 필드 보존, followers 포함)")
                return converted_data
        except (json.JSONDecodeError, FileNotFoundError):
            print("📂 기존 데이터 파일이 없거나 손상됨. 새로 시작합니다.")
            return []
    return []

def main():
    """메인 함수"""
    # 기존 결과 파일 로드
    existing_results = load_existing_data()
    
    # 기존 데이터를 딕셔너리로 변환 (id를 키로 사용)
    existing_by_id = {r.get("id"): r for r in existing_results if r.get("id")}
    
    # 이미 존재하는 user_handle 집합 (중복 체크용)
    existing_user_handles = {r.get("user_handle") for r in existing_results if r.get("user_handle")}
    
    print(f"📊 기존에 저장된 항목: {len(existing_results)}개")
    print(f"📊 기존에 저장된 user_handle: {len(existing_user_handles)}개\n")
    
    # JSON 파일 로드
    print(f"📂 {INPUT_JSON} 파일 로딩 중...")
    try:
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            media_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {INPUT_JSON} 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print(f"❌ {INPUT_JSON} 파일의 JSON 형식이 올바르지 않습니다.")
        return
    
    print(f"✅ {len(media_data)}개의 항목 발견\n")
    
    # 결과 저장용 리스트 (기존 데이터로 시작)
    results = existing_results.copy()
    
    # 새로 처리할 항목들
    new_items_count = 0
    skipped_count = 0
    duplicate_handle_count = 0
    null_handle_count = 0
    
    # Selenium WebDriver 초기화
    driver = setup_driver()
    
    try:
        # 각 항목의 permalink 처리
        for idx, item in enumerate(media_data, 1):
            media_id = item.get("id")
            permalink = item.get("permalink")
            
            if not media_id:
                skipped_count += 1
                print(f"[{idx}/{len(media_data)}] ⚠️ id가 없습니다. 건너뜁니다.")
                continue
            
            if not permalink:
                skipped_count += 1
                print(f"[{idx}/{len(media_data)}] ⚠️ permalink가 없습니다. 건너뜁니다.")
                continue
            
            # 이미 처리된 id인지 확인
            if media_id in existing_by_id:
                skipped_count += 1
                print(f"[{idx}/{len(media_data)}] ⏭️ 이미 처리된 id입니다. 건너뜁니다.")
                continue
            
            print(f"[{idx}/{len(media_data)}] 처리 중... (id: {media_id})")
            user_handle = extract_user_handle(driver, permalink)
            
            # user_handle이 None이면 저장하지 않음
            if not user_handle:
                null_handle_count += 1
                print(f"  ⚠️ user_handle이 없어 저장하지 않습니다.")
                continue
            
            # 중복된 user_handle인지 확인
            if user_handle in existing_user_handles:
                duplicate_handle_count += 1
                print(f"  ⚠️ 중복된 user_handle '{user_handle}' 발견. 저장하지 않습니다.")
                continue
            
            # 새로운 user_handle이면 저장
            existing_user_handles.add(user_handle)
            
            # 기존 항목이 있으면 기존 필드 보존 (user_name, introduce, linked_page, followers 등)
            if media_id in existing_by_id:
                # 기존 항목 업데이트 (id와 user_handle만 업데이트, 나머지 필드는 보존)
                # followers 필드도 자동으로 보존됨
                existing_item = existing_by_id[media_id]
                existing_item["id"] = media_id
                existing_item["user_handle"] = user_handle
                # results에 이미 있으므로 추가하지 않음
            else:
                # 새 항목 추가
                new_item = {
                    "id": media_id,
                    "user_handle": user_handle
                }
                results.append(new_item)
                existing_by_id[media_id] = new_item
                new_items_count += 1
            
            # 요청 간 딜레이 (Instagram 차단 방지)
            time.sleep(2)
            
    finally:
        driver.quit()
        print("\n🔒 브라우저 종료")
    
    # id 순서로 정렬 (문자열이지만 숫자로 변환 가능하면 숫자로 정렬)
    def sort_key(x):
        id_val = x.get("id", "")
        try:
            return int(id_val)
        except (ValueError, TypeError):
            return id_val
    
    results.sort(key=sort_key)
    
    # 결과를 JSON 파일로 저장
    print(f"\n💾 결과를 {OUTPUT_JSON}에 저장 중...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    success_count = sum(1 for r in results if r.get("user_handle"))
    print(f"\n✅ 완료!")
    print(f"   총 항목: {len(results)}")
    print(f"   성공 (user_handle 있음): {success_count}")
    print(f"   새로 처리된 항목: {new_items_count}")
    print(f"   건너뛴 항목 (이미 처리됨): {skipped_count}")
    print(f"   중복 user_handle로 인해 저장하지 않은 항목: {duplicate_handle_count}")
    print(f"   user_handle이 없어 저장하지 않은 항목: {null_handle_count}")

def test_single_url(test_url):
    """단일 URL 테스트 함수"""
    print(f"🧪 테스트 모드: 단일 URL 테스트\n")
    print(f"📋 테스트 URL: {test_url}\n")
    
    # Selenium WebDriver 초기화
    driver = setup_driver()
    
    try:
        user_handle = extract_user_handle(driver, test_url)
        print(f"\n{'='*50}")
        print(f"📊 테스트 결과:")
        print(f"   URL: {test_url}")
        print(f"   User Handle: {user_handle if user_handle else '❌ 찾을 수 없음'}")
        print(f"{'='*50}")
        return user_handle
    finally:
        driver.quit()
        print("\n🔒 브라우저 종료")

if __name__ == "__main__":
    import sys
    
    # 로깅 초기화
    setup_logging(str(LOG_PATH))
    logging.info("=" * 80)
    logging.info("프로그램 시작 - instagram_extract_user.py")
    logging.info("=" * 80)
    
    # 우선순위: 1) 코드 상단 TEST_URL 변수, 2) 명령줄 인자, 3) 전체 실행
    if TEST_URL:
        test_single_url(TEST_URL)
    elif len(sys.argv) > 1:
        test_url = sys.argv[1]
        test_single_url(test_url)
    else:
        main()

