import os
import time
import base64
import io
import pickle
import subprocess
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
import whisper

# .env 파일에서 로그인 정보 불러오기
load_dotenv()
USERNAME = os.getenv("IG_USERNAME")
PASSWORD = os.getenv("IG_PASSWORD")

# 쿠키 파일 경로
# 파일 경로 (현재 파일 위치 기준)
BASE_DIR = Path(__file__).parent
COOKIE_PATH = BASE_DIR / "instagram_cookies.pkl"


def setup_driver():
    """Selenium WebDriver 설정"""
    options = Options()
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
    # 자동 재생 정책 우회
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    # Performance logging 활성화 (네트워크 요청 모니터링용)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    # Network domain 활성화 (CDP 사용)
    options.set_capability('goog:chromeOptions', {
        'perfLoggingPrefs': {
            'enableNetwork': True,
            'enablePage': True
        }
    })
    # Chrome DevTools Protocol을 통한 자동 재생 허용
    prefs = {
        "profile.default_content_setting_values.media_stream": 1,
        "profile.default_content_setting_values.notifications": 1
    }
    options.add_experimental_option("prefs", prefs)
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    # 스크립트 타임아웃을 5분으로 설정 (비디오 재생 시간 고려)
    driver.set_script_timeout(300)  # 5분
    return driver


def login_instagram(driver):
    """Instagram 로그인 (쿠키 사용 또는 새로 로그인)"""
    logged_in = False
    
    # 쿠키 로드 시도
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
            
            driver.refresh()
            time.sleep(3)
            
            current_url = driver.current_url
            if "accounts/login" not in current_url:
                print("✅ 쿠키로 로그인 성공!")
                logged_in = True
            else:
                print("⚠️ 쿠키가 만료되었습니다. 새로 로그인합니다.")
        except Exception as e:
            print(f"⚠️ 쿠키 로드 실패: {e}")
    
    # 쿠키가 없거나 만료된 경우 로그인
    if not logged_in:
        print("🔐 인스타그램 로그인 중...")
        driver.get("https://www.instagram.com")
        time.sleep(3)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            ).send_keys(USERNAME)
            driver.find_element(By.NAME, "password").send_keys(PASSWORD)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            print("✅ 로그인 버튼 클릭")
            
            time.sleep(5)
            
            # 팝업 닫기 시도
            try:
                not_now_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '나중에 하기') or contains(text(), 'Not Now')]"))
                )
                not_now_button.click()
                time.sleep(2)
            except:
                pass
            
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


def find_and_click_audio_button_in_li(driver, li_element):
    """
    li 요소 내에서 비디오를 찾고, 비디오가 있으면 해당 li 요소 내에서만 오디오 버튼을 찾아서 클릭
    사용자가 정한 기준으로 면밀하게 찾기
    
    Args:
        driver: Selenium WebDriver
        li_element: li 요소 (WebElement)
    
    Returns:
        bool: 오디오 버튼을 찾아서 클릭했는지 여부
    """
    try:
        print("   🔍 li 요소 내에서 비디오 및 오디오 버튼 분석 중...")
        
        # JavaScript로 li 요소 내에서 비디오와 오디오 버튼 찾기
        result = driver.execute_script("""
            var li = arguments[0];
            if (!li) return {videoFound: false, audioButtonClicked: false};
            
            // 1. li 요소 내에서 비디오 찾기
            var video = li.querySelector('video');
            if (!video) {
                console.log('❌ li 요소 내에 비디오가 없습니다.');
                return {videoFound: false, audioButtonClicked: false};
            }
            
            var videoSrc = video.getAttribute('src') || video.getAttribute('data-src');
            if (!videoSrc) {
                console.log('❌ 비디오에 src 속성이 없습니다.');
                return {videoFound: false, audioButtonClicked: false};
            }
            
            console.log('✅ li 요소 내에서 비디오 발견');
            
            // 2. li 요소 내에서 <title>오디오 소리 꺼짐</title>이 있는 div 요소 찾기
            // 구조: <div aria-label="볼륨 조정"><div><div role="button"><svg><title>오디오 소리 꺼짐</title></svg></div></div></div>
            var foundDiv = null;
            var divInfo = null;
            
            // li 요소 내의 모든 div 요소 찾기
            var allDivs = li.querySelectorAll('div[role="button"]');
            console.log('🔍 li 요소 내 div[role="button"] 개수:', allDivs.length);
            
            // <title>오디오 소리 꺼짐</title>이 있는 div 찾기
            for (var i = 0; i < allDivs.length; i++) {
                var div = allDivs[i];
                var svg = div.querySelector('svg');
                
                if (svg) {
                    var title = svg.querySelector('title');
                    if (title) {
                        var titleText = (title.textContent || title.innerText || '').trim();
                        console.log('div #' + i + ' 검사 중...');
                        console.log('  title 텍스트:', titleText);
                        
                        // <title>오디오 소리 꺼짐</title> 확인
                        if (titleText === '오디오 소리 꺼짐' || titleText === '오디오 소리') {
                            var visible = div.offsetParent !== null;
                            console.log('  ✅ <title>오디오 소리 꺼짐</title> 발견!');
                            console.log('  div 표시됨:', visible);
                            
                            if (visible) {
                                foundDiv = div;
                                divInfo = {
                                    method: 'title_audio_sound_off',
                                    titleText: titleText,
                                    index: i
                                };
                                console.log('✅ <title>오디오 소리 꺼짐</title>이 있는 div 발견 (인덱스: ' + i + ')');
                                break;  // 첫 번째로 발견한 div만 사용
                            }
                        }
                    }
                }
            }
            
            // fallback: SVG의 aria-label로 찾기
            if (!foundDiv) {
                for (var i = 0; i < allDivs.length; i++) {
                    var div = allDivs[i];
                    var svg = div.querySelector('svg');
                    
                    if (svg) {
                        var svgAriaLabel = (svg.getAttribute('aria-label') || '').trim();
                        console.log('div #' + i + ' 검사 중 (aria-label)...');
                        console.log('  SVG aria-label:', svgAriaLabel);
                        
                        if (svgAriaLabel === '오디오 소리 꺼짐' || svgAriaLabel === '오디오 소리') {
                            var visible = div.offsetParent !== null;
                            console.log('  ✅ SVG aria-label에서 오디오 소리 꺼짐 발견!');
                            console.log('  div 표시됨:', visible);
                            
                            if (visible) {
                                foundDiv = div;
                                divInfo = {
                                    method: 'svg_aria_label_audio_off',
                                    svgAriaLabel: svgAriaLabel,
                                    index: i
                                };
                                console.log('✅ SVG aria-label로 div 발견 (인덱스: ' + i + ')');
                                break;
                            }
                        }
                    }
                }
            }
            
            var foundButton = foundDiv;  // 호환성을 위해 foundButton 변수 사용
            var buttonInfo = divInfo;
            
            // 버튼을 찾았으면 클릭 시도
            if (foundButton) {
                var clickSuccess = false;
                try {
                    foundButton.click();
                    console.log('✅ 오디오 버튼 클릭 성공 (방법: ' + buttonInfo.method + ')');
                    clickSuccess = true;
                } catch (e) {
                    console.log('⚠️ 버튼 클릭 실패:', e);
                    try {
                        foundButton.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        console.log('✅ JavaScript로 오디오 버튼 클릭 성공');
                        clickSuccess = true;
                    } catch (e2) {
                        console.log('⚠️ JavaScript 클릭도 실패:', e2);
                    }
                }
                
                // 클릭 후 검증
                if (clickSuccess) {
                    // 약간 대기 후 비디오 muted 상태 확인
                    var start = Date.now();
                    while (Date.now() - start < 1000) {}
                    
                    var videoMuted = video.muted;
                    var newAriaLabel = foundButton.getAttribute('aria-label') || '';
                    console.log('클릭 후 검증:');
                    console.log('  video.muted:', videoMuted);
                    console.log('  aria-label:', newAriaLabel);
                    
                    return {
                        videoFound: true,
                        audioButtonClicked: true,
                        method: buttonInfo.method,
                        videoMuted: videoMuted,
                        ariaLabel: newAriaLabel
                    };
                }
            }
            
            console.log('⚠️ li 요소 내에서 오디오 버튼을 찾지 못했습니다.');
            return {videoFound: true, audioButtonClicked: false};
            
        """, li_element)
        
        if result and result.get('videoFound'):
            if result.get('audioButtonClicked'):
                method = result.get('method', 'unknown')
                print(f"   ✅ li 요소 내에서 비디오 발견 및 오디오 버튼 클릭 완료 (방법: {method})")
                time.sleep(1)  # 클릭 후 대기
                return True
            else:
                print("   ⚠️ li 요소 내에 비디오는 있지만 오디오 버튼을 찾지 못했습니다.")
                return False
        else:
            print("   ℹ️ li 요소 내에 비디오가 없습니다.")
            return False
            
    except Exception as e:
        print(f"   ⚠️ li 요소 내 오디오 버튼 찾기 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def extract_video_blob_to_base64(driver, video_element):
    """
    JavaScript를 사용하여 video 요소의 blob URL을 가져와서 Base64로 변환
    
    Args:
        driver: Selenium WebDriver
        video_element: video WebElement
    
    Returns:
        str: Base64 인코딩된 비디오 데이터 (없으면 None)
    """
    try:
        # 비디오 상태 및 실제 URL 확인
        print("   🔍 비디오 상태 및 실제 URL 확인 중...")
        video_info = driver.execute_script("""
            var video = arguments[0];
            var info = {
                readyState: video.readyState,
                networkState: video.networkState,
                src: video.src,
                currentSrc: video.currentSrc,
                duration: video.duration,
                videoWidth: video.videoWidth,
                videoHeight: video.videoHeight,
                sources: [],
                parentAttributes: {},
                dataAttributes: {}
            };
            
            // source 태그들 확인
            var sources = video.querySelectorAll('source');
            for (var i = 0; i < sources.length; i++) {
                info.sources.push({
                    src: sources[i].src,
                    type: sources[i].type
                });
            }
            
            // 부모 요소의 속성 확인 (Instagram은 종종 여기에 URL을 숨김)
            var parent = video.parentElement;
            if (parent) {
                for (var attr of parent.attributes) {
                    if (attr.name.includes('src') || attr.name.includes('url') || attr.name.includes('video')) {
                        info.parentAttributes[attr.name] = attr.value;
                    }
                }
            }
            
            // video 요소의 data 속성 확인
            for (var attr of video.attributes) {
                if (attr.name.startsWith('data-')) {
                    info.dataAttributes[attr.name] = attr.value;
                }
            }
            
            return info;
        """, video_element)
        
        print(f"   📊 비디오 상태: readyState={video_info['readyState']}, duration={video_info.get('duration', 'N/A')}")
        print(f"   📹 video.src: {video_info['src'][:80] if video_info['src'] else 'None'}...")
        print(f"   📹 video.currentSrc: {video_info['currentSrc'][:80] if video_info['currentSrc'] else 'None'}...")
        
        # 실제 비디오 URL 찾기 (blob이 아닌 경우)
        actual_video_url = None
        
        # 1. currentSrc 확인
        if video_info['currentSrc'] and not video_info['currentSrc'].startswith('blob:'):
            actual_video_url = video_info['currentSrc']
            print(f"   ✅ 실제 비디오 URL 발견 (currentSrc): {actual_video_url[:80]}...")
        # 2. src 확인
        elif video_info['src'] and not video_info['src'].startswith('blob:'):
            actual_video_url = video_info['src']
            print(f"   ✅ 실제 비디오 URL 발견 (src): {actual_video_url[:80]}...")
        # 3. source 태그 확인
        elif video_info['sources']:
            for source in video_info['sources']:
                if source['src'] and not source['src'].startswith('blob:'):
                    actual_video_url = source['src']
                    print(f"   ✅ source 태그에서 실제 비디오 URL 발견: {actual_video_url[:80]}...")
                    break
        
        # 4. 부모 요소의 속성에서 URL 찾기
        if not actual_video_url and video_info.get('parentAttributes'):
            for attr_name, attr_value in video_info['parentAttributes'].items():
                if attr_value and isinstance(attr_value, str):
                    # URL 패턴 확인 (http:// 또는 https://로 시작)
                    if (attr_value.startswith('http://') or attr_value.startswith('https://')) and \
                       ('.mp4' in attr_value or '.webm' in attr_value or 'video' in attr_value.lower()):
                        actual_video_url = attr_value
                        print(f"   ✅ 부모 요소 속성에서 실제 비디오 URL 발견 ({attr_name}): {actual_video_url[:80]}...")
                        break
        
        # 5. 페이지의 JavaScript 변수에서 비디오 URL 찾기
        if not actual_video_url:
            print("   🔍 페이지 JavaScript 변수에서 비디오 URL 검색 중...")
            try:
                js_video_url = driver.execute_script("""
                    // Instagram의 React/GraphQL 데이터에서 비디오 URL 찾기
                    var videoUrl = null;
                    
                    // window 객체에서 찾기
                    if (window.__initialDataLoaded || window._sharedData) {
                        try {
                            var data = window.__initialDataLoaded || window._sharedData;
                            var jsonStr = JSON.stringify(data);
                            // video URL 패턴 찾기
                            var match = jsonStr.match(/https?:\/\/[^"\\s]+\\.(mp4|webm|m3u8)/i);
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
                                var match = jsonStr.match(/https?:\/\/[^"\\s]+\\.(mp4|webm|m3u8)/i);
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
                    print(f"   ✅ JavaScript 변수에서 실제 비디오 URL 발견: {actual_video_url[:80]}...")
            except Exception as e:
                print(f"   ℹ️ JavaScript 변수 검색 실패: {e}")
        
        # 6. 네트워크 로그에서 비디오 URL 찾기 시도
        if not actual_video_url:
            print("   🔍 네트워크 로그에서 비디오 URL 검색 중...")
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
                            
                            if url and ('.mp4' in url or '.webm' in url or 'video' in url.lower() or 'cdninstagram' in url):
                                if not url.startswith('blob:') and url not in video_urls:
                                    video_urls.append(url)
                    except:
                        continue
                
                if video_urls:
                    # 가장 최근 URL 사용
                    actual_video_url = video_urls[-1]
                    print(f"   ✅ 네트워크 로그에서 실제 비디오 URL 발견: {actual_video_url[:80]}...")
            except Exception as e:
                print(f"   ℹ️ 네트워크 로그 확인 실패: {e}")
        
        # 실제 URL이 있으면 requests로 다운로드
        download_failed_403 = False
        if actual_video_url:
            print("   🔄 실제 비디오 URL에서 다운로드 중...")
            try:
                import requests
                
                # Selenium의 쿠키를 requests 세션에 전달
                selenium_cookies = driver.get_cookies()
                session = requests.Session()
                
                # 쿠키 추가
                for cookie in selenium_cookies:
                    session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', ''))
                
                # 더 많은 헤더 추가 (Instagram이 요구하는 헤더)
                user_agent = driver.execute_script("return navigator.userAgent;")
                headers = {
                    'User-Agent': user_agent,
                    'Referer': driver.current_url,
                    'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'identity',  # gzip 압축 해제 문제 방지
                    'Range': 'bytes=0-',  # 전체 다운로드
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'video',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Site': 'cross-site',
                }
                
                print(f"   📥 다운로드 시도 중... (쿠키 {len(selenium_cookies)}개 사용)")
                response = session.get(actual_video_url, headers=headers, timeout=60, stream=True)
                
                if response.status_code == 200 or response.status_code == 206:  # 206은 Partial Content (Range 요청)
                    # 스트림으로 다운로드 (메모리 효율적)
                    video_bytes = b''
                    total_size = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            video_bytes += chunk
                            total_size += len(chunk)
                            if total_size % (1024 * 1024) == 0:  # 1MB마다 로그
                                print(f"   📥 다운로드 중... {total_size / (1024 * 1024):.1f} MB")
                    
                    print(f"   ✅ 다운로드 완료 (크기: {len(video_bytes)} bytes)")
                    
                    # base64로 인코딩
                    import base64
                    base64_data = base64.b64encode(video_bytes).decode('utf-8')
                    print(f"   ✅ base64 변환 완료 (크기: {len(base64_data)} bytes)")
                    return base64_data
                else:
                    print(f"   ⚠️ 다운로드 실패: HTTP {response.status_code}")
                    print(f"   📋 응답 헤더: {dict(response.headers)}")
                    # 403인 경우 다른 방법 시도
                    if response.status_code == 403:
                        download_failed_403 = True
                        print("   💡 403 오류: Instagram이 요청을 차단했습니다. JavaScript로 직접 추출을 시도합니다...")
            except Exception as e:
                print(f"   ⚠️ 다운로드 중 오류: {e}")
                import traceback
                print(traceback.format_exc())
        
        # 403 오류 또는 blob URL인 경우 - JavaScript로 직접 추출 시도
        result = None
        if download_failed_403 or (video_info['src'] and video_info['src'].startswith('blob:')):
            print("   🔄 JavaScript로 비디오 데이터 직접 추출 중...")
            
            # 사용자 상호작용 시뮬레이션 (자동 재생 정책 우회)
            # stale element 오류 방지를 위해 JavaScript로 직접 처리
            print("   👆 사용자 상호작용 시뮬레이션 중...")
            try:
                # JavaScript로 비디오 요소를 찾아서 클릭 (stale element 오류 방지)
                driver.execute_script("""
                    var videos = document.querySelectorAll('video');
                    if (videos.length > 0) {
                        var video = videos[0];
                        // 마우스 이벤트로 클릭 시뮬레이션
                        var clickEvent = new MouseEvent('click', {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        video.dispatchEvent(clickEvent);
                        return true;
                    }
                    return false;
                """)
                time.sleep(1)
                print("   ✅ 비디오 요소 클릭 완료 (JavaScript)")
            except Exception as e:
                print(f"   ⚠️ 비디오 클릭 실패: {e}, 다른 방법 시도...")
                # 대체 방법: 페이지 클릭
                try:
                    actions = ActionChains(driver)
                    actions.move_by_offset(100, 100)  # 페이지 중앙으로 이동
                    actions.click()
                    actions.perform()
                    time.sleep(1)
                except:
                    pass
            
            # 비디오 길이 확인하여 타임아웃 설정
            video_duration = video_info.get('duration', 0)
            if video_duration > 0:
                # 비디오 길이 + 여유 시간(10초)으로 타임아웃 설정
                script_timeout = int(video_duration) + 10
                if script_timeout > 300:  # 최대 5분
                    script_timeout = 300
                elif script_timeout < 60:  # 최소 1분
                    script_timeout = 60
                driver.set_script_timeout(script_timeout)
                print(f"   ⏱️ 스크립트 타임아웃 설정: {script_timeout}초 (비디오 길이: {video_duration:.1f}초)")
            
            # stale element 오류 방지를 위해 video 요소를 JavaScript에서 다시 찾기
            # arguments를 전달하지 않고 JavaScript 내에서 직접 찾기
            result = driver.execute_async_script("""
                // stale element 오류 방지: video 요소를 JavaScript에서 직접 찾기
                var callback = arguments[arguments.length - 1];
                
                var video = null;
                var videoElements = document.querySelectorAll('video');
                if (videoElements.length > 0) {
                    video = videoElements[0];  // 첫 번째 video 요소 사용
                }
                
                if (!video) {
                    callback({success: false, error: '비디오 요소를 찾을 수 없습니다'});
                    return;
                }
                
                try {
                    // 방법 1: 비디오 요소에서 직접 데이터 가져오기 (가장 안정적)
                    // 비디오가 이미 로드되어 있으므로, 캔버스를 통해 프레임을 추출하거나
                    // MediaRecorder API를 사용하여 오디오만 추출
                    
                    console.log('Video readyState:', video.readyState);
                    console.log('Video duration:', video.duration);
                    
                    // 비디오가 로드되지 않았으면 로드 대기
                    if (video.readyState < 2) {
                        video.load();
                        var loadPromise = new Promise(function(resolve) {
                            video.addEventListener('loadeddata', resolve, { once: true });
                            setTimeout(resolve, 5000); // 타임아웃
                        });
                        loadPromise.then(function() {
                            extractVideoData();
                        });
                    } else {
                        extractVideoData();
                    }
                    
                    function extractVideoData() {
                        // 방법 1: XMLHttpRequest로 blob URL 접근 시도
                        var blobUrl = video.src;
                        if (blobUrl && blobUrl.startsWith('blob:')) {
                            console.log('Blob URL:', blobUrl);
                            
                            var xhr = new XMLHttpRequest();
                            xhr.open('GET', blobUrl, true);
                            xhr.responseType = 'blob';
                            
                            xhr.onload = function() {
                                if (xhr.status === 200 || xhr.status === 0) { // 0은 blob URL의 경우 정상
                                    var blob = xhr.response;
                                    console.log('Blob size:', blob.size);
                                    
                                    if (blob.size === 0) {
                                        // 방법 2: MediaRecorder API로 오디오만 추출
                                        tryMediaRecorder();
                                        return;
                                    }
                                    
                                    // Blob을 ArrayBuffer로 변환
                                    var reader = new FileReader();
                                    reader.onloadend = function() {
                                        var arrayBuffer = reader.result;
                                        convertToBase64(arrayBuffer);
                                    };
                                    reader.onerror = function(e) {
                                        console.error('FileReader error:', e);
                                        tryMediaRecorder();
                                    };
                                    reader.readAsArrayBuffer(blob);
                                } else {
                                    console.error('XHR failed:', xhr.status);
                                    tryMediaRecorder();
                                }
                            };
                            
                            xhr.onerror = function() {
                                console.error('XHR network error');
                                tryMediaRecorder();
                            };
                            
                            xhr.send();
                        } else {
                            tryMediaRecorder();
                        }
                    }
                    
                    function tryMediaRecorder() {
                        // 방법 2: Web Audio API로 오디오 직접 추출
                        console.log('Web Audio API 시도...');
                        try {
                            var audioContext = new (window.AudioContext || window.webkitAudioContext)();
                            
                            // 비디오에 오디오 트랙이 있는지 확인
                            if (video.muted) {
                                video.muted = false;
                                console.log('비디오 음소거 해제');
                            }
                            
                            var source = audioContext.createMediaElementSource(video);
                            
                            // 오디오를 분석하기 위한 노드 생성
                            var processor = audioContext.createScriptProcessor(4096, 1, 1);
                            var audioData = [];
                            var sampleCount = 0;
                            
                            processor.onaudioprocess = function(e) {
                                var inputData = e.inputBuffer.getChannelData(0);
                                var hasAudio = false;
                                
                                for (var i = 0; i < inputData.length; i++) {
                                    if (Math.abs(inputData[i]) > 0.001) {  // 무음이 아닌지 확인
                                        hasAudio = true;
                                    }
                                    audioData.push(inputData[i]);
                                }
                                
                                sampleCount++;
                                if (sampleCount % 10 === 0) {  // 10번마다 로그
                                    console.log('오디오 샘플 수집 중...', audioData.length, 'samples, hasAudio:', hasAudio);
                                }
                                
                                // 출력도 연결 (필요한 경우)
                                var outputData = e.outputBuffer.getChannelData(0);
                                for (var i = 0; i < inputData.length; i++) {
                                    outputData[i] = inputData[i];
                                }
                            };
                            
                            source.connect(processor);
                            processor.connect(audioContext.destination);
                            
                            console.log('AudioContext 생성 완료, 비디오 재생 준비...');
                            
                            var checkInterval = null;
                            var endedHandler = null;
                            
                            function startAudioCapture() {
                                // 비디오 재생 시작
                                video.currentTime = 0;
                                
                                // 자동 재생 정책 우회를 위해 사용자 상호작용 확인
                                var playPromise = null;
                                try {
                                    playPromise = video.play();
                                } catch (e) {
                                    console.error('play() 호출 실패:', e);
                                    // 재시도: 사용자 상호작용 시뮬레이션
                                    var clickEvent = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    video.dispatchEvent(clickEvent);
                                    
                                    setTimeout(function() {
                                        try {
                                            playPromise = video.play();
                                        } catch (e2) {
                                            callback({success: false, error: '비디오 재생 불가: ' + e2.toString()});
                                            return;
                                        }
                                        if (playPromise) {
                                            handlePlayPromise(playPromise);
                                        }
                                    }, 100);
                                    return;
                                }
                                
                                if (playPromise !== undefined && playPromise !== null) {
                                    handlePlayPromise(playPromise);
                                } else {
                                    // play()가 Promise를 반환하지 않는 경우
                                    startCapture();
                                }
                            }
                            
                            function handlePlayPromise(playPromise) {
                                playPromise.then(function() {
                                    startCapture();
                                }).catch(function(e) {
                                    console.error('비디오 재생 실패:', e);
                                    // 재시도: 사용자 상호작용 시뮬레이션 후 재생
                                    console.log('사용자 상호작용 시뮬레이션 후 재시도...');
                                    var clickEvent = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    video.dispatchEvent(clickEvent);
                                    
                                    setTimeout(function() {
                                        try {
                                            var retryPromise = video.play();
                                            if (retryPromise) {
                                                retryPromise.then(function() {
                                                    startCapture();
                                                }).catch(function(e2) {
                                                    processor.disconnect();
                                                    source.disconnect();
                                                    callback({success: false, error: '비디오 재생 실패: ' + e2.toString()});
                                                });
                                            } else {
                                                startCapture();
                                            }
                                        } catch (e3) {
                                            processor.disconnect();
                                            source.disconnect();
                                            callback({success: false, error: '비디오 재생 불가: ' + e3.toString()});
                                        }
                                    }, 200);
                                });
                            }
                            
                            function startCapture() {
                                console.log('비디오 재생 시작, 오디오 캡처 중...');
                                console.log('비디오 duration:', video.duration);
                                console.log('비디오 muted:', video.muted);
                                console.log('비디오 volume:', video.volume);
                                
                                checkInterval = setInterval(function() {
                                    console.log('진행 상황 - currentTime:', video.currentTime, '/', video.duration, ', audioData:', audioData.length);
                                }, 5000);  // 5초마다 진행 상황 로그
                                
                                // 비디오가 끝날 때까지 대기
                                endedHandler = function() {
                                    if (checkInterval) {
                                        clearInterval(checkInterval);
                                        checkInterval = null;
                                    }
                                    processor.disconnect();
                                    source.disconnect();
                                    
                                    console.log('오디오 데이터 수집 완료, 크기:', audioData.length);
                                    
                                    if (audioData.length === 0) {
                                        callback({success: false, error: '오디오 데이터가 없습니다 (비디오가 무음일 수 있습니다)'});
                                        return;
                                    }
                                    
                                    // Float32Array를 Int16Array로 변환 (WAV 형식)
                                    var int16Data = new Int16Array(audioData.length);
                                    for (var i = 0; i < audioData.length; i++) {
                                        var s = Math.max(-1, Math.min(1, audioData[i]));
                                        int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                                    }
                                    
                                    // WAV 헤더 생성
                                    var sampleRate = audioContext.sampleRate;
                                    var numChannels = 1;
                                    var numSamples = int16Data.length;
                                    var byteRate = sampleRate * numChannels * 2;
                                    var blockAlign = numChannels * 2;
                                    var dataSize = numSamples * 2;
                                    var fileSize = 36 + dataSize;
                                    
                                    var buffer = new ArrayBuffer(44 + dataSize);
                                    var view = new DataView(buffer);
                                    
                                    // WAV 헤더 작성
                                    function writeString(offset, string) {
                                        for (var i = 0; i < string.length; i++) {
                                            view.setUint8(offset + i, string.charCodeAt(i));
                                        }
                                    }
                                    
                                    writeString(0, 'RIFF');
                                    view.setUint32(4, fileSize, true);
                                    writeString(8, 'WAVE');
                                    writeString(12, 'fmt ');
                                    view.setUint32(16, 16, true);
                                    view.setUint16(20, 1, true);
                                    view.setUint16(22, numChannels, true);
                                    view.setUint32(24, sampleRate, true);
                                    view.setUint32(28, byteRate, true);
                                    view.setUint16(32, blockAlign, true);
                                    view.setUint16(34, 16, true);
                                    writeString(36, 'data');
                                    view.setUint32(40, dataSize, true);
                                    
                                    // 오디오 데이터 복사
                                    var int16View = new Int16Array(buffer, 44);
                                    int16View.set(int16Data);
                                    
                                    convertToBase64(buffer);
                                };
                                
                                video.addEventListener('ended', endedHandler, { once: true });
                                
                                // 타임아웃 설정 (최대 비디오 길이 + 5초)
                                var duration = video.duration || 10;
                                setTimeout(function() {
                                    if (!video.ended && endedHandler) {
                                        console.log('타임아웃 발생, 강제 종료...');
                                        if (checkInterval) {
                                            clearInterval(checkInterval);
                                            checkInterval = null;
                                        }
                                        video.removeEventListener('ended', endedHandler);
                                        endedHandler();
                                    }
                                }, (duration + 5) * 1000);
                            }
                            
                            // 오디오 캡처 시작
                            startAudioCapture();
                            
                        } catch (e) {
                            console.error('Web Audio API error:', e);
                            callback({success: false, error: 'Web Audio API 실패: ' + e.toString()});
                        }
                    }
                    
                    function convertToBase64(arrayBuffer) {
                        try {
                            var bytes = new Uint8Array(arrayBuffer);
                            var binary = '';
                            var chunkSize = 8192;
                            
                            for (var i = 0; i < bytes.byteLength; i += chunkSize) {
                                var chunk = bytes.subarray(i, Math.min(i + chunkSize, bytes.byteLength));
                                binary += String.fromCharCode.apply(null, chunk);
                            }
                            
                            var base64 = btoa(binary);
                            callback({success: true, data: base64, size: base64.length});
                        } catch (e) {
                            callback({success: false, error: 'Base64 변환 실패: ' + e.toString()});
                        }
                    }
                } catch (e) {
                    console.error('Exception:', e);
                    callback({success: false, error: e.toString()});
                }
            """, video_element)
        
        # 결과 확인 (blob URL 처리 결과)
        if result is not None:
            if isinstance(result, dict):
                if result.get('success'):
                    base64_data = result.get('data')
                    data_size = result.get('size', 0)
                    print(f"   ✅ base64 변환 성공 (크기: {data_size} bytes)")
                    return base64_data
                else:
                    error_msg = result.get('error', '알 수 없는 오류')
                    print(f"   ⚠️ JavaScript 오류: {error_msg}")
                    return None
            else:
                # 이전 형식 호환성 (문자열로 직접 반환된 경우)
                print(f"   ✅ base64 변환 완료 (크기: {len(result)} bytes)")
                return result
        else:
            # 실제 URL도 없고 blob 처리도 안 된 경우
            if not actual_video_url and (not video_info['src'] or not video_info['src'].startswith('blob:')):
                print(f"   ⚠️ 비디오 URL을 찾을 수 없습니다.")
            return None
        
    except Exception as e:
        print(f"   ⚠️ blob → base64 변환 실패: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def find_ffmpeg():
    """
    ffmpeg 실행 파일 경로 찾기
    
    Returns:
        str: ffmpeg 실행 파일 경로 (없으면 None)
    """
    ffmpeg_exe = 'ffmpeg'
    ffmpeg_found = False
    
    # 방법 1: shutil.which() 사용 (가장 신뢰성 높음)
    try:
        import shutil
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            ffmpeg_exe = ffmpeg_path
            ffmpeg_found = True
            print(f"   ✅ shutil.which()로 ffmpeg 발견: {ffmpeg_exe}")
    except Exception as e:
        print(f"   ℹ️ shutil.which() 실패: {e}")
    
    # 방법 2: PATH 환경 변수에서 직접 찾기
    if not ffmpeg_found:
        try:
            path_env = os.environ.get('PATH', '')
            path_dirs = path_env.split(os.pathsep)
            print(f"   🔍 PATH 환경 변수 확인 중... (경로 {len(path_dirs)}개)")
            
            for path_dir in path_dirs:
                if not path_dir:
                    continue
                ffmpeg_candidate = os.path.join(path_dir, 'ffmpeg.exe')
                if os.path.exists(ffmpeg_candidate):
                    ffmpeg_exe = ffmpeg_candidate
                    ffmpeg_found = True
                    print(f"   ✅ PATH에서 ffmpeg 발견: {ffmpeg_exe}")
                    break
        except Exception as e:
            print(f"   ℹ️ PATH 확인 실패: {e}")
    
    # 방법 3: subprocess로 직접 실행 시도
    if not ffmpeg_found:
        try:
            result_check = subprocess.run(['ffmpeg', '-version'], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE, 
                                        timeout=5,
                                        shell=True)
            if result_check.returncode == 0:
                ffmpeg_found = True
                print(f"   ✅ subprocess로 ffmpeg 실행 성공")
        except Exception as e:
            print(f"   ℹ️ subprocess 확인 실패: {e}")
    
    # 방법 4: 일반적인 설치 경로 확인
    if not ffmpeg_found:
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
            r'C:\tools\ffmpeg\bin\ffmpeg.exe',
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
        ]
        for path in common_paths:
            if os.path.exists(path):
                ffmpeg_exe = path
                ffmpeg_found = True
                print(f"   📍 일반 경로에서 ffmpeg 발견: {ffmpeg_exe}")
                break
    
    if not ffmpeg_found:
        print(f"   ⚠️ ffmpeg를 찾을 수 없습니다.")
        print(f"   📋 현재 PATH 환경 변수:")
        path_env = os.environ.get('PATH', '')
        path_dirs = [d for d in path_env.split(os.pathsep) if d and 'ffmpeg' in d.lower()]
        if path_dirs:
            print(f"      ffmpeg 관련 경로: {path_dirs}")
        else:
            print(f"      (ffmpeg 관련 경로 없음)")
        print(f"   💡 해결 방법:")
        print(f"      1. 새 터미널을 열어서 'ffmpeg -version' 명령어가 작동하는지 확인")
        print(f"      2. Python을 재시작 (환경 변수 변경 후)")
        print(f"      3. 코드에서 ffmpeg 경로를 직접 지정")
        return None
    
    return ffmpeg_exe


def process_video_with_ffmpeg_whisper(video_bytes):
    """
    비디오 바이트 데이터를 ffmpeg/Whisper로 처리
    
    Args:
        video_bytes: bytes - 비디오 바이트 데이터
    
    Returns:
        str: 추출된 음성 텍스트 (없으면 None)
    """
    print(f"📹 비디오 데이터 크기: {len(video_bytes)} bytes")
    
    # 임시 파일로 비디오 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as video_file:
        video_path = video_file.name
        video_file.write(video_bytes)
    
    try:
        # ffmpeg 경로 찾기
        ffmpeg_exe = find_ffmpeg()
        if not ffmpeg_exe:
            return None
        
        # ffmpeg로 비디오에서 오디오 추출
        print("🔄 ffmpeg로 오디오 추출 중...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as audio_file:
            audio_path = audio_file.name
        
        # ffmpeg 명령어 실행
        ffmpeg_cmd = [
            ffmpeg_exe,
            '-i', video_path,
            '-vn',  # 비디오 스트림 제거
            '-acodec', 'pcm_s16le',  # PCM 16-bit
            '-ar', '16000',  # 샘플링 레이트 16kHz (Whisper 권장)
            '-ac', '1',  # 모노
            '-y',  # 덮어쓰기
            audio_path
        ]
        
        print(f"   🔧 ffmpeg 명령어 실행 중...")
        # Windows에서는 shell=True를 사용하여 PATH 확인
        use_shell = os.name == 'nt'  # Windows인 경우
        result = subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=use_shell
        )
        
        if result.returncode != 0:
            print(f"⚠️ ffmpeg 오류: {result.stderr}")
            return None
        
        print(f"✅ 오디오 추출 완료: {audio_path}")
        
        # 무음 여부 확인
        print("🔍 무음 여부 확인 중...")
        volume_check_cmd = [
            ffmpeg_exe,  # 찾은 ffmpeg 경로 사용
            '-i', audio_path,
            '-af', 'volumedetect',
            '-f', 'null',
            '-'
        ]
        
        # Windows에서는 shell=True를 사용하여 PATH 확인
        use_shell = os.name == 'nt'  # Windows인 경우
        volume_result = subprocess.run(
            volume_check_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=use_shell
        )
        
        # 볼륨 레벨 파싱
        is_silent = False
        if volume_result.returncode == 0:
            stderr_output = volume_result.stderr
            # mean_volume과 max_volume 추출
            mean_volume = None
            max_volume = None
            
            for line in stderr_output.split('\n'):
                if 'mean_volume:' in line:
                    try:
                        # mean_volume: -XX.X dB 형식에서 숫자 추출
                        mean_volume = float(line.split('mean_volume:')[1].split('dB')[0].strip())
                    except:
                        pass
                if 'max_volume:' in line:
                    try:
                        # max_volume: -XX.X dB 형식에서 숫자 추출
                        max_volume = float(line.split('max_volume:')[1].split('dB')[0].strip())
                    except:
                        pass
            
            # 볼륨 레벨 분석
            # 무음 판단 기준:
            # 1. 평균 볼륨이 -60dB 이하이고, 최대 볼륨도 -50dB 이하인 경우
            # 2. 또는 평균 볼륨과 최대 볼륨 모두 매우 낮은 경우
            # (보컬이 있는 음악은 최대 볼륨이 보통 -20 ~ -10 dB 정도이므로, 
            #  최대 볼륨만으로 무음을 판단하면 안 됨)
            
            if mean_volume is not None and max_volume is not None:
                # 평균과 최대 모두 확인 가능한 경우
                if mean_volume < -60 and max_volume < -50:
                    is_silent = True
                    print(f"🔇 무음 비디오로 판단됨 (평균: {mean_volume:.2f} dB, 최대: {max_volume:.2f} dB)")
                else:
                    print(f"🔊 음성이 있는 비디오 (평균: {mean_volume:.2f} dB, 최대: {max_volume:.2f} dB)")
            elif mean_volume is not None:
                # 평균 볼륨만 확인 가능한 경우
                if mean_volume < -60:
                    is_silent = True
                    print(f"🔇 무음 비디오로 판단됨 (평균 볼륨: {mean_volume:.2f} dB)")
                else:
                    print(f"🔊 음성이 있는 비디오 (평균 볼륨: {mean_volume:.2f} dB)")
            elif max_volume is not None:
                # 최대 볼륨만 확인 가능한 경우
                # 최대 볼륨이 -40dB보다 낮으면 의심스럽지만, 
                # 최대 볼륨만으로는 무음을 확정할 수 없으므로 계속 진행
                if max_volume < -40:
                    print(f"⚠️ 최대 볼륨이 낮습니다 ({max_volume:.2f} dB). 계속 진행합니다.")
                else:
                    print(f"🔊 음성이 있는 비디오 (최대 볼륨: {max_volume:.2f} dB)")
            else:
                print(f"ℹ️ 볼륨 레벨을 확인할 수 없습니다. 계속 진행합니다.")
        else:
            print(f"⚠️ 볼륨 확인 실패, 계속 진행합니다.")
        
        # 무음이면 Whisper 처리 생략
        if is_silent:
            print("⏭️ 무음 비디오이므로 Whisper 처리를 건너뜁니다.")
            return None
        
        # Whisper로 오디오를 텍스트로 변환
        print("🔄 Whisper로 음성 인식 중...")
        try:
            # 오디오 파일 존재 여부 및 경로 확인
            if not os.path.exists(audio_path):
                print(f"⚠️ 오디오 파일을 찾을 수 없습니다: {audio_path}")
                return None
            
            # 절대 경로로 변환 (Whisper가 상대 경로를 제대로 처리하지 못할 수 있음)
            audio_path_abs = os.path.abspath(audio_path)
            print(f"   📁 오디오 파일 경로: {audio_path_abs}")
            
            # Whisper가 내부적으로 사용하는 ffmpeg 경로 설정
            # Whisper는 subprocess로 ffmpeg를 호출하므로, PATH에 ffmpeg가 있어야 함
            ffmpeg_path = find_ffmpeg()
            if ffmpeg_path:
                # ffmpeg 실행 파일의 디렉토리 찾기
                if os.path.isfile(ffmpeg_path):
                    # 실행 파일인 경우 (예: C:\ffmpeg\bin\ffmpeg.exe)
                    ffmpeg_dir = os.path.dirname(ffmpeg_path)
                else:
                    # 디렉토리인 경우 (예: C:\ffmpeg\bin)
                    ffmpeg_dir = ffmpeg_path
                
                # PATH에 ffmpeg 디렉토리가 없으면 추가
                current_path = os.environ.get('PATH', '')
                if ffmpeg_dir not in current_path.split(os.pathsep):
                    os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
                    print(f"   🔧 PATH에 ffmpeg 디렉토리 추가: {ffmpeg_dir}")
                else:
                    print(f"   ✅ PATH에 이미 ffmpeg 디렉토리 포함됨: {ffmpeg_dir}")
            else:
                print(f"   ⚠️ ffmpeg를 찾을 수 없어 Whisper가 실패할 수 있습니다.")
            
            # Whisper 모델 로드 (base 모델 사용, 필요시 변경 가능)
            model = whisper.load_model("base")
            
            # 오디오 파일에서 텍스트 추출
            # Whisper는 내부적으로 ffmpeg를 사용하여 오디오를 로드함
            result = model.transcribe(audio_path_abs, language="ko")  # 한국어 지정
            
            transcribed_text = result["text"].strip()
            print(f"✅ 음성 인식 완료: {len(transcribed_text)}자")
            
            return transcribed_text if transcribed_text else None
            
        except Exception as e:
            print(f"⚠️ Whisper 처리 실패: {e}")
            import traceback
            print(f"   상세 오류:")
            traceback.print_exc()
            return None
    
    finally:
        # 임시 파일 삭제
        try:
            if os.path.exists(video_path):
                os.unlink(video_path)
            if os.path.exists(audio_path):
                os.unlink(audio_path)
        except Exception as e:
            print(f"⚠️ 임시 파일 삭제 실패: {e}")


def extract_voice_from_instagram_post(driver, post_url, is_carousel=False):
    """
    Instagram 게시글에서 비디오를 찾아 음성을 추출
    "다음" 버튼을 클릭하면서 모든 페이지의 비디오를 확인
    
    Args:
        driver: Selenium WebDriver
        post_url: str - Instagram 게시글 URL
        is_carousel: bool - 캐러셀 앨범인지 여부 (True면 li 요소를 찾음, False면 단일 비디오로 처리)
    
    Returns:
        list: 추출 결과 리스트
    """
    print(f"\n📱 Instagram 게시글 로딩 중: {post_url}")
    driver.get(post_url)
    
    # 페이지 로드 대기
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )
        print("✅ 게시글 페이지 로드 완료")
    except TimeoutException:
        print("⚠️ 게시글 페이지 로드 타임아웃, 계속 진행...")
    
    # 캐러셀 앨범의 경우 비디오를 찾은 후에 오디오 버튼을 찾아야 하므로
    # 여기서는 단일 비디오 포스트인 경우에만 오디오 버튼을 찾음
    # 캐러셀은 비디오를 찾은 후에 각 비디오마다 오디오 버튼을 찾음
    print("🔍 오디오 켜기 버튼 찾는 중... (단일 비디오 포스트인 경우)")
    audio_button_found = False
    
    # 버튼이 로드될 때까지 대기
    time.sleep(3)
    
    # 방법 1: 정확한 aria-label로 찾기 (최우선)
    # 버튼: <button aria-label="오디오 켜기/끄기" class="_aswp _aswq _aswu _asw_ _asx2" type="button">
    try:
        # 버튼이 클릭 가능할 때까지 대기
        print("   ⏳ 버튼이 나타날 때까지 대기 중...")
        exact_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="오디오 켜기/끄기"]'))
        )
        print("   ✅ 정확한 aria-label로 버튼 발견: '오디오 켜기/끄기'")
        
        # 버튼 정보 확인
        aria_label = exact_button.get_attribute("aria-label")
        is_displayed = exact_button.is_displayed()
        is_enabled = exact_button.is_enabled()
        print(f"   📋 버튼 정보: aria-label={aria_label}, displayed={is_displayed}, enabled={is_enabled}")
        
        # 스크롤하여 버튼이 보이도록
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", exact_button)
        time.sleep(0.5)
        
        # 여러 방법으로 클릭 시도
        click_success = False
        try:
            # 방법 1: ActionChains로 클릭 (가장 안정적)
            ActionChains(driver).move_to_element(exact_button).pause(0.3).click().perform()
            print("   ✅ ActionChains로 클릭 완료")
            click_success = True
            audio_button_found = True
        except Exception as e1:
            print(f"   ℹ️ ActionChains 클릭 실패: {e1}")
            try:
                # 방법 2: JavaScript로 직접 클릭
                driver.execute_script("arguments[0].click();", exact_button)
                print("   ✅ JavaScript로 클릭 완료")
                click_success = True
                audio_button_found = True
            except Exception as e2:
                print(f"   ℹ️ JavaScript 클릭 실패: {e2}")
                try:
                    # 방법 3: 일반 click() 시도
                    exact_button.click()
                    print("   ✅ 일반 click()으로 클릭 완료")
                    click_success = True
                    audio_button_found = True
                except Exception as e3:
                    print(f"   ⚠️ 모든 클릭 방법 실패: {e3}")
        
        # 클릭 후 확인: 버튼의 aria-label이 변경되었는지 확인 (켜기 -> 끄기)
        if click_success:
            time.sleep(1)  # 클릭 후 대기
            try:
                # 클릭 후 버튼 상태 확인
                new_aria_label = exact_button.get_attribute("aria-label")
                print(f"   🔍 클릭 후 aria-label: {new_aria_label}")
                if "끄기" in new_aria_label or "Mute" in new_aria_label:
                    print("   ✅ 오디오가 켜진 것으로 확인됨 (aria-label 변경됨)")
                else:
                    print("   ⚠️ aria-label이 변경되지 않았습니다. 클릭이 제대로 되지 않았을 수 있습니다.")
            except Exception as e:
                print(f"   ℹ️ 클릭 후 상태 확인 실패: {e}")
                
    except TimeoutException:
        print("   ⚠️ 버튼이 10초 내에 나타나지 않았습니다.")
    except Exception as e:
        print(f"   ℹ️ 정확한 aria-label로 찾기 실패: {e}")
    
    # 방법 2: CSS 셀렉터로 찾기 (더 많은 패턴 추가)
    if not audio_button_found:
        audio_button_selectors = [
            'button[aria-label*="오디오 켜기/끄기"]',
            'button[aria-label*="오디오 켜기"]',
            'button[aria-label*="오디오"]',
            'button[aria-label*="켜기"]',
            'button[aria-label*="Audio"]',
            'button[aria-label*="audio"]',
            'button[aria-label*="Unmute"]',
            'button[aria-label*="unmute"]',
            'button[aria-label*="Mute"]',
            'button[aria-label*="mute"]',
            'button[role="button"][aria-label*="오디오"]',
            'button[role="button"][aria-label*="Audio"]',
            '[role="button"][aria-label*="오디오"]',
            '[role="button"][aria-label*="Audio"]',
            'div[role="button"][aria-label*="오디오"]',
            'div[role="button"][aria-label*="Audio"]',
        ]
    
    for selector in audio_button_selectors:
        try:
            audio_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            if audio_buttons:
                print(f"   🔍 셀렉터 '{selector}'로 {len(audio_buttons)}개 버튼 발견")
                for btn in audio_buttons:
                    try:
                        # 버튼이 보이는지 확인
                        if btn.is_displayed():
                            # ActionChains를 사용하여 클릭
                            ActionChains(driver).move_to_element(btn).click().perform()
                            print(f"   ✅ 오디오 켜기 버튼 클릭 완료 (CSS 셀렉터: {selector})")
                            audio_button_found = True
                            time.sleep(1)  # 클릭 후 대기
                            break
                    except Exception as e:
                        print(f"   ℹ️ 버튼 클릭 시도 실패: {e}")
                        continue
                if audio_button_found:
                    break
        except Exception as e:
            continue
    
    # 방법 2: XPath로 찾기
    if not audio_button_found:
        xpath_selectors = [
            "//button[contains(@aria-label, '오디오')]",
            "//button[contains(@aria-label, '켜기')]",
            "//button[contains(@aria-label, 'Audio')]",
            "//button[contains(@aria-label, 'Unmute')]",
            "//*[@role='button' and contains(@aria-label, '오디오')]",
            "//*[@role='button' and contains(@aria-label, 'Audio')]",
            "//div[contains(@aria-label, '오디오')]",
            "//div[contains(@aria-label, 'Audio')]",
        ]
        
        for xpath in xpath_selectors:
            try:
                audio_buttons = driver.find_elements(By.XPATH, xpath)
                if audio_buttons:
                    print(f"   🔍 XPath '{xpath}'로 {len(audio_buttons)}개 버튼 발견")
                    for btn in audio_buttons:
                        try:
                            if btn.is_displayed():
                                ActionChains(driver).move_to_element(btn).click().perform()
                                print(f"   ✅ 오디오 켜기 버튼 클릭 완료 (XPath: {xpath})")
                                audio_button_found = True
                                time.sleep(1)
                                break
                        except Exception as e:
                            continue
                    if audio_button_found:
                        break
            except Exception as e:
                continue
    
    # 방법 3: 모든 button 요소를 찾아서 aria-label 확인
    if not audio_button_found:
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"   🔍 전체 버튼 개수: {len(all_buttons)}")
            for btn in all_buttons:
                try:
                    aria_label = btn.get_attribute("aria-label")
                    if aria_label and ("오디오" in aria_label or "Audio" in aria_label or "Unmute" in aria_label or "켜기" in aria_label):
                        if btn.is_displayed():
                            print(f"   🔍 aria-label 발견: {aria_label}")
                            ActionChains(driver).move_to_element(btn).click().perform()
                            print(f"   ✅ 오디오 켜기 버튼 클릭 완료 (aria-label: {aria_label})")
                            audio_button_found = True
                            time.sleep(1)
                            break
                except Exception:
                    continue
        except Exception as e:
            print(f"   ℹ️ 전체 버튼 검색 실패: {e}")
    
    # 방법 4: JavaScript로 직접 찾기 및 검증
    if not audio_button_found:
        try:
            print("   🔍 JavaScript로 버튼 찾기 및 클릭 시도...")
            
            # JavaScript 콘솔 로그를 캡처하기 위한 설정
            # (Selenium은 기본적으로 console.log를 캡처하지 않으므로, 
            #  JavaScript에서 직접 Python으로 로그를 전달하도록 수정)
            
            button_info = driver.execute_script("""
                // 모든 button 요소 찾기
                var buttons = document.querySelectorAll('button, [role="button"]');
                var foundButton = null;
                var buttonInfo = null;
                
                console.log('전체 버튼 개수:', buttons.length);
                
                // 모든 버튼 정보 디버깅 출력
                for (var j = 0; j < buttons.length; j++) {
                    var debugBtn = buttons[j];
                    var debugAriaLabel = debugBtn.getAttribute('aria-label') || '';
                    var debugClassName = debugBtn.className || '';
                    var debugSvg = debugBtn.querySelector('svg');
                    var debugSvgTitle = '';
                    var debugSvgAriaLabel = '';
                    if (debugSvg) {
                        var debugTitle = debugSvg.querySelector('title');
                        if (debugTitle) {
                            debugSvgTitle = (debugTitle.textContent || debugTitle.innerText || '').trim();
                        }
                        debugSvgAriaLabel = (debugSvg.getAttribute('aria-label') || '').trim();
                    }
                    console.log('버튼 #' + j + ':', {
                        ariaLabel: debugAriaLabel,
                        className: debugClassName.substring(0, 100),
                        hasSvg: !!debugSvg,
                        svgTitle: debugSvgTitle,
                        svgAriaLabel: debugSvgAriaLabel,
                        visible: debugBtn.offsetParent !== null
                    });
                }
                
                // 방법 1: 정확한 aria-label + 정확한 클래스명 + SVG 확인 (가장 엄격)
                // 첫 번째로 발견한 버튼만 선택
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var ariaLabel = btn.getAttribute('aria-label') || '';
                    var className = btn.className || '';
                    
                    console.log('버튼 #' + i + ' 검사 중...');
                    console.log('  aria-label:', ariaLabel);
                    console.log('  className:', className.substring(0, 100));
                    
                    // 버튼 내부에 SVG가 있는지 확인 (오디오 소리 관련 SVG)
                    // SVG 내부의 title 요소에 "오디오" 키워드가 포함되어 있어야 함
                    var svg = btn.querySelector('svg');
                    var hasAudioSvg = false;
                    if (svg) {
                        var svgTitle = svg.querySelector('title');
                        if (svgTitle) {
                            var svgTitleText = (svgTitle.textContent || svgTitle.innerText || '').trim();
                            console.log('  SVG title:', svgTitleText);
                            // title 텍스트에 "오디오" 키워드가 정확히 포함되어 있는지 확인 (가장 중요)
                            // "오디오 소리", "오디오 켜기" 등이 포함되어야 함
                            if (svgTitleText.indexOf('오디오') !== -1 || svgTitleText.indexOf('Audio') !== -1) {
                                hasAudioSvg = true;
                                console.log('  ✅ SVG title에서 오디오 키워드 발견:', svgTitleText);
                            } else {
                                console.log('  ❌ SVG title에 오디오 키워드 없음:', svgTitleText);
                            }
                        } else {
                            console.log('  ❌ SVG에 title 요소 없음');
                        }
                        // title이 없으면 aria-label 확인 (fallback)
                        if (!hasAudioSvg) {
                            var svgAriaLabel = (svg.getAttribute('aria-label') || '').trim();
                            console.log('  SVG aria-label:', svgAriaLabel);
                            if (svgAriaLabel.indexOf('오디오') !== -1 || svgAriaLabel.indexOf('Audio') !== -1 || 
                                svgAriaLabel.indexOf('소리') !== -1) {
                                hasAudioSvg = true;
                                console.log('  ✅ SVG aria-label에서 오디오 키워드 발견:', svgAriaLabel);
                            }
                        }
                    } else {
                        console.log('  ❌ 버튼에 SVG 요소 없음');
                    }
                    
                    // 조건 확인
                    var ariaLabelMatch = ariaLabel === '오디오 켜기/끄기';
                    var classMatch = className.includes('_aswp') && className.includes('_aswq') && 
                                     className.includes('_aswu') && className.includes('_asw_') && 
                                     className.includes('_asx2');
                    var visible = btn.offsetParent !== null;
                    
                    console.log('  조건 확인:');
                    console.log('    aria-label === "오디오 켜기/끄기":', ariaLabelMatch);
                    console.log('    클래스명 매칭:', classMatch);
                    console.log('    SVG 오디오 확인:', hasAudioSvg);
                    console.log('    버튼 표시됨:', visible);
                    
                    // 정확한 aria-label과 정확한 클래스명 모두 확인
                    // SVG도 확인 (오디오 관련 SVG가 있어야 함)
                    if (ariaLabelMatch && classMatch && hasAudioSvg && visible) {
                        foundButton = btn;
                        buttonInfo = {
                            method: 'exact_aria_label_and_class_with_svg',
                            ariaLabel: ariaLabel,
                            className: className,
                            type: btn.type || '',
                            index: i
                        };
                        console.log('✅ 정확한 aria-label + 클래스명 + SVG로 버튼 발견 (첫 번째 버튼, 인덱스: ' + i + ')');
                        console.log('✅ 선택된 버튼 정보:', {
                            ariaLabel: ariaLabel,
                            className: className,
                            svgTitle: svgTitle ? (svgTitle.textContent || svgTitle.innerText || '').trim() : 'N/A'
                        });
                        break;  // 첫 번째로 발견한 버튼만 사용
                    } else {
                        console.log('  ❌ 조건 불일치 - 다음 버튼 검사');
                    }
                }
                
                // 방법 2: 정확한 aria-label + 정확한 클래스명 (SVG 없어도)
                if (!foundButton) {
                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        var ariaLabel = btn.getAttribute('aria-label') || '';
                        var className = btn.className || '';
                        
                        // 정확한 aria-label과 정확한 클래스명 모두 확인
                        if (ariaLabel === '오디오 켜기/끄기' && 
                            className.includes('_aswp') && className.includes('_aswq') && 
                            className.includes('_aswu') && className.includes('_asw_') && 
                            className.includes('_asx2')) {
                            if (btn.offsetParent !== null) {
                                foundButton = btn;
                                buttonInfo = {
                                    method: 'exact_aria_label_and_class',
                                    ariaLabel: ariaLabel,
                                    className: className,
                                    type: btn.type || '',
                                    index: i
                                };
                                console.log('정확한 aria-label + 클래스명으로 버튼 발견 (첫 번째 버튼, 인덱스: ' + i + ')');
                                break;  // 첫 번째로 발견한 버튼만 사용
                            }
                        }
                    }
                }
                
                // 방법 2: 정확한 aria-label로만 찾기 (첫 번째만)
                if (!foundButton) {
                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        var ariaLabel = btn.getAttribute('aria-label') || '';
                        
                        // 정확한 aria-label 확인: "오디오 켜기/끄기"
                        if (ariaLabel === '오디오 켜기/끄기') {
                            if (btn.offsetParent !== null) {
                                foundButton = btn;
                                buttonInfo = {
                                    method: 'exact_aria_label',
                                    ariaLabel: ariaLabel,
                                    className: btn.className || '',
                                    type: btn.type || '',
                                    index: i
                                };
                                console.log('정확한 aria-label로 버튼 발견 (첫 번째 버튼, 인덱스: ' + i + ')');
                                break;  // 첫 번째로 발견한 버튼만 사용
                            }
                        }
                    }
                }
                
                // 방법 3: 정확한 클래스명으로만 찾기 (_aswp _aswq _aswu _asw_ _asx2)
                // 단, aria-label이 비어있거나 "오디오" 관련이어야 함 (첫 번째만)
                if (!foundButton) {
                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        var className = btn.className || '';
                        var ariaLabel = btn.getAttribute('aria-label') || '';
                        
                        // 정확한 클래스명 패턴 확인 + aria-label이 비어있거나 오디오 관련이어야 함
                        if (className.includes('_aswp') && className.includes('_aswq') && 
                            className.includes('_aswu') && className.includes('_asw_') && 
                            className.includes('_asx2') &&
                            (ariaLabel === '' || ariaLabel.includes('오디오') || ariaLabel.includes('Audio'))) {
                            if (btn.offsetParent !== null) {
                                foundButton = btn;
                                buttonInfo = {
                                    method: 'exact_class_name',
                                    ariaLabel: ariaLabel,
                                    className: className,
                                    type: btn.type || '',
                                    index: i
                                };
                                console.log('정확한 클래스명으로 버튼 발견 (첫 번째 버튼, 인덱스: ' + i + ')');
                                break;  // 첫 번째로 발견한 버튼만 사용
                            }
                        }
                    }
                }
                
                // 방법 4: aria-label 부분 매칭으로 찾기 (하지만 클래스명도 확인, 첫 번째만)
                if (!foundButton) {
                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        var ariaLabel = btn.getAttribute('aria-label') || '';
                        var className = btn.className || '';
                        
                        // 오디오 관련 키워드 확인 + 클래스명에 _asw가 포함되어 있어야 함
                        if ((ariaLabel.includes('오디오') || ariaLabel.includes('Audio') || 
                            ariaLabel.includes('Unmute') || ariaLabel.includes('켜기')) &&
                            (className.includes('_asw'))) {
                            if (btn.offsetParent !== null) {
                                foundButton = btn;
                                buttonInfo = {
                                    method: 'partial_aria_label_with_class',
                                    ariaLabel: ariaLabel,
                                    className: className,
                                    type: btn.type || '',
                                    index: i
                                };
                                console.log('부분 aria-label + 클래스명으로 버튼 발견 (첫 번째 버튼, 인덱스: ' + i + ')');
                                break;  // 첫 번째로 발견한 버튼만 사용
                            }
                        }
                    }
                }
                
                // 버튼을 찾았으면 클릭
                if (foundButton) {
                    console.log('🎯 클릭할 버튼 선택됨!');
                    console.log('  버튼 인덱스:', buttonInfo ? buttonInfo.index : 'N/A');
                    console.log('  aria-label:', foundButton.getAttribute('aria-label') || '');
                    console.log('  className:', foundButton.className || '');
                    var finalSvg = foundButton.querySelector('svg');
                    if (finalSvg) {
                        var finalSvgTitle = finalSvg.querySelector('title');
                        if (finalSvgTitle) {
                            console.log('  SVG title:', (finalSvgTitle.textContent || finalSvgTitle.innerText || '').trim());
                        }
                        console.log('  SVG aria-label:', (finalSvg.getAttribute('aria-label') || '').trim());
                    }
                    
                    var beforeLabel = foundButton.getAttribute('aria-label') || '';
                    
                    // 비디오 요소의 muted 상태도 확인
                    var video = document.querySelector('video');
                    var videoMutedBefore = video ? video.muted : null;
                    
                    console.log('🖱️ 버튼 클릭 시작...');
                    // 첫 번째 클릭 방법만 시도하고 즉시 중단
                    var clickMethods = [];
                    var clickSuccess = false;
                    
                    // 방법 1: 일반 click() - stopPropagation으로 버블링 방지
                    if (!clickSuccess) {
                        try {
                            console.log('  방법 1: click() 시도...');
                            // 클릭 이벤트 리스너를 추가하여 버블링 방지
                            var clickHandler = function(e) {
                                console.log('  ⚠️ 클릭 이벤트 발생 - 버블링 방지:', e.target);
                                e.stopPropagation();
                                e.stopImmediatePropagation();
                            };
                            foundButton.addEventListener('click', clickHandler, true);
                            foundButton.click();
                            foundButton.removeEventListener('click', clickHandler, true);
                            clickMethods.push('click()');
                            clickSuccess = true;
                            console.log('  ✅ click() 완료 - 클릭 중단');
                        } catch (e) {
                            console.log('  ❌ 일반 click() 실패:', e);
                        }
                    }
                    
                    // 방법 2: dispatchEvent로 클릭 이벤트 발생 - 버블링 방지 (방법 1 실패 시에만)
                    if (!clickSuccess) {
                        try {
                            console.log('  방법 2: dispatchEvent 시도...');
                            var clickEvent = new MouseEvent('click', {
                                bubbles: false,  // 버블링 방지
                                cancelable: true,
                                view: window
                            });
                            foundButton.dispatchEvent(clickEvent);
                            clickMethods.push('dispatchEvent');
                            clickSuccess = true;
                            console.log('  ✅ dispatchEvent 완료 - 클릭 중단');
                        } catch (e) {
                            console.log('  ❌ dispatchEvent 실패:', e);
                        }
                    }
                    
                    // 방법 3: 직접 muted 속성 변경 시도 (방법 1, 2 실패 시에만)
                    if (!clickSuccess) {
                        try {
                            console.log('  방법 3: 직접 muted 속성 변경 시도...');
                            var video = document.querySelector('video');
                            if (video && video.muted) {
                                video.muted = false;
                                clickMethods.push('direct_muted_change');
                                clickSuccess = true;
                                console.log('  ✅ 직접 muted 속성 변경 완료 - 클릭 중단');
                            }
                        } catch (e) {
                            console.log('  ❌ direct muted change 실패:', e);
                        }
                    }
                    
                    // 클릭 후 충분한 대기 (상태 변경 시간)
                    if (clickSuccess) {
                        console.log('  ⏳ 클릭 후 상태 변경 대기 중...');
                        var start = Date.now();
                        while (Date.now() - start < 2000) {
                            // 대기
                        }
                        console.log('  ✅ 대기 완료');
                    }
                    
                    // 클릭 후 상태 확인 (버튼을 다시 찾아서 확인)
                    var afterLabel = '';
                    var videoMutedAfter = null;
                    
                    // 버튼을 다시 찾기 (DOM이 변경되었을 수 있음)
                    var buttonsAfter = document.querySelectorAll('button, [role="button"]');
                    var foundButtonAfter = null;
                    
                    for (var i = 0; i < buttonsAfter.length; i++) {
                        var btn = buttonsAfter[i];
                        var className = btn.className || '';
                        if (className.includes('_aswp') && className.includes('_aswq') && 
                            className.includes('_aswu') && className.includes('_asw_') && 
                            className.includes('_asx2')) {
                            foundButtonAfter = btn;
                            afterLabel = btn.getAttribute('aria-label') || '';
                            break;
                        }
                    }
                    
                    // 비디오 상태 재확인
                    video = document.querySelector('video');
                    videoMutedAfter = video ? video.muted : null;
                    
                    // 오디오가 활성화되었는지 확인
                    var audioActivated = false;
                    if (afterLabel.includes('끄기') || afterLabel.includes('Mute') || afterLabel.includes('mute')) {
                        audioActivated = true;
                    } else if (video && videoMutedBefore === true && videoMutedAfter === false) {
                        audioActivated = true;
                    } else if (video && videoMutedAfter === false) {
                        audioActivated = true;
                    }
                    
                    return {
                        clicked: true,
                        clickSuccess: clickMethods.length > 0,
                        clickMethods: clickMethods,
                        beforeLabel: beforeLabel,
                        afterLabel: afterLabel,
                        changed: beforeLabel !== afterLabel,
                        audioActivated: audioActivated,
                        videoMutedBefore: videoMutedBefore,
                        videoMutedAfter: videoMutedAfter,
                        videoFound: video !== null,
                        buttonInfo: buttonInfo
                    };
                }
                
                return {clicked: false, buttonsFound: buttons.length};
            """)
            
            if button_info:
                if button_info.get('clicked'):
                    btn_info = button_info.get('buttonInfo', {})
                    click_methods = button_info.get('clickMethods', [])
                    
                    # 버튼 선택 정보 출력
                    print(f"   📋 찾기 방법: {btn_info.get('method', 'N/A')}")
                    print(f"   📋 선택된 버튼 인덱스: {btn_info.get('index', 'N/A')}")
                    print(f"   📋 클릭 전 aria-label: '{button_info.get('beforeLabel', 'N/A')}'")
                    print(f"   📋 클릭 후 aria-label: '{button_info.get('afterLabel', 'N/A')}'")
                    if btn_info.get('className'):
                        print(f"   📋 버튼 클래스: {btn_info.get('className', 'N/A')[:80]}...")
                    
                    if click_methods:
                        print(f"   ✅ JavaScript로 버튼 클릭 완료 (사용된 방법: {', '.join(click_methods)})")
                    else:
                        print(f"   ⚠️ JavaScript로 버튼 클릭 시도했지만 성공 여부 불확실")
                    
                    # 브라우저 콘솔 로그 확인 (가능한 경우)
                    try:
                        logs = driver.get_log('browser')
                        if logs:
                            print("   📝 브라우저 콘솔 로그 (최근 20개):")
                            for log in logs[-20:]:  # 최근 20개만
                                msg = log.get('message', '')
                                if any(keyword in msg for keyword in ['버튼', 'SVG', '클릭', '오디오', 'Audio', 'title', '조건']):
                                    # 콘솔 로그 메시지에서 실제 내용만 추출
                                    if 'console-api' in msg:
                                        import json
                                        try:
                                            log_data = json.loads(msg.split('console-api: ')[-1] if 'console-api: ' in msg else msg)
                                            print(f"      {log_data}")
                                        except:
                                            print(f"      {msg[:200]}")
                                    else:
                                        print(f"      {msg[:200]}")
                    except Exception as e:
                        # 로그를 가져올 수 없는 경우 무시
                        pass
                    
                    # 비디오 muted 상태 정보
                    if button_info.get('videoFound'):
                        print(f"   📹 비디오 muted 상태: {button_info.get('videoMutedBefore')} → {button_info.get('videoMutedAfter')}")
                    
                    # 오디오 활성화 여부 확인
                    if button_info.get('audioActivated'):
                        print("   ✅ 오디오가 실제로 활성화되었습니다!")
                        audio_button_found = True
                    else:
                        print("   ⚠️ 오디오가 활성화되지 않았을 수 있습니다.")
                        # aria-label이 변경되었는지 확인
                        if button_info.get('changed'):
                            print("   ℹ️ aria-label은 변경되었지만 오디오 활성화 확인 실패")
                        else:
                            print("   ⚠️ aria-label도 변경되지 않았습니다.")
                            # 비디오 muted 상태가 변경되지 않았는지 확인
                            if button_info.get('videoMutedBefore') == button_info.get('videoMutedAfter'):
                                print("   ⚠️ 비디오 muted 상태도 변경되지 않았습니다.")
                                print("   🔄 버튼을 다시 클릭 시도합니다...")
                                
                                # 재시도: 버튼을 다시 찾아서 클릭
                                try:
                                    retry_result = driver.execute_script("""
                                        var buttons = document.querySelectorAll('button, [role="button"]');
                                        var foundBtn = null;
                                        
                                        // 첫 번째로 발견한 버튼만 찾기 (SVG도 확인)
                                        for (var i = 0; i < buttons.length; i++) {
                                            var btn = buttons[i];
                                            var className = btn.className || '';
                                            var ariaLabel = btn.getAttribute('aria-label') || '';
                                            
                                            // 버튼 내부에 오디오 관련 SVG가 있는지 확인
                                            // SVG 내부의 title 요소에 "오디오" 키워드가 포함되어 있어야 함
                                            var svg = btn.querySelector('svg');
                                            var hasAudioSvg = false;
                                            if (svg) {
                                                var svgTitle = svg.querySelector('title');
                                                if (svgTitle) {
                                                    var svgTitleText = svgTitle.textContent || svgTitle.innerText || '';
                                                    // title 텍스트에 "오디오" 키워드가 포함되어 있는지 확인 (가장 중요)
                                                    if (svgTitleText.includes('오디오') || svgTitleText.includes('Audio')) {
                                                        hasAudioSvg = true;
                                                    }
                                                }
                                                // title이 없으면 aria-label 확인 (fallback)
                                                if (!hasAudioSvg) {
                                                    var svgAriaLabel = svg.getAttribute('aria-label') || '';
                                                    if (svgAriaLabel.includes('오디오') || svgAriaLabel.includes('Audio') || 
                                                        svgAriaLabel.includes('소리')) {
                                                        hasAudioSvg = true;
                                                    }
                                                }
                                            }
                                            
                                            // 정확한 조건: aria-label과 클래스명 모두 확인
                                            // aria-label이 "오디오 켜기/끄기"이거나 비어있고, 정확한 클래스명이 있어야 함
                                            // 그리고 오디오 관련 SVG가 있어야 함
                                            if ((ariaLabel === '오디오 켜기/끄기' || ariaLabel === '') &&
                                                className.includes('_aswp') && className.includes('_aswq') && 
                                                className.includes('_aswu') && className.includes('_asw_') && 
                                                className.includes('_asx2') &&
                                                hasAudioSvg) {
                                                if (btn.offsetParent !== null) {
                                                    foundBtn = btn;
                                                    break;  // 첫 번째로 발견한 버튼만 사용
                                                }
                                            }
                                        }
                                        
                                        // SVG가 없는 경우도 시도 (하지만 더 엄격한 조건)
                                        if (!foundBtn) {
                                            for (var i = 0; i < buttons.length; i++) {
                                                var btn = buttons[i];
                                                var className = btn.className || '';
                                                var ariaLabel = btn.getAttribute('aria-label') || '';
                                                
                                                if ((ariaLabel === '오디오 켜기/끄기' || ariaLabel === '') &&
                                                    className.includes('_aswp') && className.includes('_aswq') && 
                                                    className.includes('_aswu') && className.includes('_asw_') && 
                                                    className.includes('_asx2')) {
                                                    if (btn.offsetParent !== null) {
                                                        foundBtn = btn;
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                        
                                        if (foundBtn) {
                                            // 여러 방법으로 클릭 시도 - 버블링 방지
                                            try {
                                                // 클릭 이벤트 리스너를 추가하여 버블링 방지
                                                var clickHandler = function(e) {
                                                    e.stopPropagation();
                                                    e.stopImmediatePropagation();
                                                };
                                                foundBtn.addEventListener('click', clickHandler, true);
                                                foundBtn.click();
                                                foundBtn.removeEventListener('click', clickHandler, true);
                                            } catch(e) {
                                                var clickEvent = new MouseEvent('click', {
                                                    bubbles: false,  // 버블링 방지
                                                    cancelable: true,
                                                    view: window
                                                });
                                                foundBtn.dispatchEvent(clickEvent);
                                            }
                                            
                                            // 대기
                                            var start = Date.now();
                                            while (Date.now() - start < 1500) {}
                                            
                                            // 상태 확인
                                            var video = document.querySelector('video');
                                            var afterLabel = foundBtn.getAttribute('aria-label') || '';
                                            var videoMuted = video ? video.muted : null;
                                            
                                            return {
                                                clicked: true,
                                                afterLabel: afterLabel,
                                                videoMuted: videoMuted,
                                                audioActivated: afterLabel.includes('끄기') || afterLabel.includes('Mute') || (video && !videoMuted)
                                            };
                                        }
                                        
                                        return {clicked: false};
                                    """)
                                    
                                    if retry_result and retry_result.get('clicked'):
                                        if retry_result.get('audioActivated'):
                                            print("   ✅ 재시도 성공! 오디오가 활성화되었습니다!")
                                            audio_button_found = True
                                        else:
                                            print(f"   ⚠️ 재시도했지만 여전히 활성화되지 않았습니다.")
                                            print(f"      aria-label: '{retry_result.get('afterLabel', 'N/A')}'")
                                            print(f"      video muted: {retry_result.get('videoMuted', 'N/A')}")
                                            
                                            # 최종 시도: 비디오의 muted 속성을 직접 변경
                                            print("   🔄 최종 시도: 비디오 muted 속성을 직접 변경합니다...")
                                            final_attempt = driver.execute_script("""
                                                var video = document.querySelector('video');
                                                if (video && video.muted) {
                                                    video.muted = false;
                                                    // 약간 대기
                                                    var start = Date.now();
                                                    while (Date.now() - start < 1000) {}
                                                    return !video.muted;
                                                }
                                                return video ? !video.muted : false;
                                            """)
                                            if final_attempt:
                                                print("   ✅ 비디오 muted 속성 직접 변경 성공! 오디오가 활성화되었습니다!")
                                                audio_button_found = True
                                            else:
                                                print("   ⚠️ 모든 자동 시도가 실패했습니다.")
                                                print("   💡 비디오에 오디오가 포함되어 있을 수 있으므로 계속 진행합니다...")
                                                print("   💡 (나중에 무음 감지로 필터링됩니다)")
                                                # 오디오가 없어도 계속 진행 (나중에 무음 감지로 필터링)
                                                audio_button_found = False
                                except Exception as e:
                                    print(f"   ⚠️ 재시도 실패: {e}")
                                    # 최종 시도: 비디오의 muted 속성을 직접 변경
                                    print("   🔄 최종 시도: 비디오 muted 속성을 직접 변경합니다...")
                                    try:
                                        final_attempt = driver.execute_script("""
                                            var video = document.querySelector('video');
                                            if (video && video.muted) {
                                                video.muted = false;
                                                var start = Date.now();
                                                while (Date.now() - start < 1000) {}
                                                return !video.muted;
                                            }
                                            return video ? !video.muted : false;
                                        """)
                                        if final_attempt:
                                            print("   ✅ 비디오 muted 속성 직접 변경 성공! 오디오가 활성화되었습니다!")
                                            audio_button_found = True
                                        else:
                                            print("   💡 비디오에 오디오가 포함되어 있을 수 있으므로 계속 진행합니다...")
                                            audio_button_found = False
                                    except Exception as e2:
                                        print(f"   ⚠️ 최종 시도도 실패: {e2}")
                                        print("   💡 비디오에 오디오가 포함되어 있을 수 있으므로 계속 진행합니다...")
                                        audio_button_found = False
                else:
                    buttons_found = button_info.get('buttonsFound', 0)
                    print(f"   ⚠️ 오디오 버튼을 찾지 못했습니다. (전체 버튼 개수: {buttons_found})")
        except Exception as e:
            print(f"   ℹ️ JavaScript 검색 실패: {e}")
            import traceback
            traceback.print_exc()
    
    if not audio_button_found:
        print("   ⚠️ 오디오 켜기 버튼을 찾을 수 없거나 클릭이 실패했습니다. 계속 진행합니다.")
    else:
        print("   ✅ 오디오 활성화 완료 (검증됨)")
    
    # 추가 대기 및 스크롤 (비디오 로드를 위해)
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    results = []
    video_count = 0
    
    # 캐러셀 앨범인 경우에만 li 요소를 찾고, 단일 비디오인 경우 바로 비디오를 찾음
    if not is_carousel:
        # 단일 비디오 포스트 처리
        print("ℹ️ 단일 비디오 포스트로 처리합니다.")
        try:
            article = None
            try:
                article = driver.find_element(By.TAG_NAME, "article")
                print(f"🔍 article 요소 발견")
            except NoSuchElementException:
                print(f"⚠️ article 요소를 찾을 수 없습니다. 전체 페이지에서 검색합니다.")
            
            # 비디오 찾기 (article이 있으면 article 내에서, 없으면 전체 페이지에서)
            if article:
                video_elements = article.find_elements(By.CSS_SELECTOR, "video")
                if not video_elements:
                    video_elements = driver.find_elements(By.CSS_SELECTOR, "video")
            else:
                video_elements = driver.find_elements(By.CSS_SELECTOR, "video")
            
            print(f"🔍 video 요소 개수: {len(video_elements)}")
            
            for video in video_elements:
                video_src = video.get_attribute("src")
                if not video_src:
                    video_src = video.get_attribute("data-src")
                
                if video_src:
                    video_count += 1
                    print(f"✅ 비디오 태그 발견! (#{video_count})")
                    print(f"   📹 video.src: {video_src[:80]}...")
                    
                    # 단일 비디오 포스트는 이미 페이지 로드 시 오디오 버튼을 찾았으므로
                    # 여기서는 추가로 찾을 필요 없음
                    
                    # blob URL인 경우 처리
                    if video_src.startswith('blob:'):
                        print(f"   🔄 blob URL 확인됨, 처리 시작...")
                        
                        # blob → base64 변환
                        print(f"   🔄 blob → base64 변환 중...")
                        base64_data = extract_video_blob_to_base64(driver, video)
                        
                        if not base64_data:
                            print(f"   ⚠️ base64 변환 실패")
                            continue
                        
                        print(f"   ✅ base64 변환 완료 (길이: {len(base64_data)})")
                        
                        # Python에서 base64 디코딩
                        print(f"   🔄 base64 디코딩 중...")
                        try:
                            video_bytes = base64.b64decode(base64_data)
                            print(f"   ✅ 디코딩 완료 (크기: {len(video_bytes)} bytes)")
                        except Exception as e:
                            print(f"   ⚠️ base64 디코딩 실패: {e}")
                            continue
                        
                        # BytesIO로 변환
                        video_io = io.BytesIO(video_bytes)
                        
                        # ffmpeg/Whisper 처리
                        print(f"   🔄 ffmpeg/Whisper 처리 중...")
                        voice_text = process_video_with_ffmpeg_whisper(video_bytes)
                        
                        if voice_text:
                            print(f"   ✅ 음성 텍스트 추출 완료: {voice_text[:100]}...")
                            results.append({
                                "video_index": video_count,
                                "video_src": video_src,
                                "video_size": len(video_bytes),
                                "voice_text": voice_text
                            })
                        else:
                            print(f"   ⚠️ 음성 텍스트 추출 실패")
                    else:
                        print(f"   ℹ️ blob URL이 아닙니다. (일반 URL)")
            
        except Exception as e:
            print(f"⚠️ 단일 비디오 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n📊 총 {video_count}개의 비디오 태그를 발견했습니다.")
        return results
    
    # 캐러셀 앨범인 경우: "다음" 버튼이 없을 때까지 반복
    print("ℹ️ 캐러셀 앨범으로 처리합니다.")
    while True:
        # 현재 페이지의 모든 <li class="_acaz"> 요소 찾기 (여러 셀렉터 시도)
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
                    print(f"🔍 셀렉터 '{selector}'로 발견된 li 요소 개수: {len(li_elements)}")
                    break
            except Exception:
                continue
        
        # li 요소가 없을 때 = 캐러셀에서도 li를 찾지 못한 경우
        if not li_elements:
            print("⚠️ li 요소를 찾을 수 없습니다. 대체 방법 시도...")
            try:
                article = None
                try:
                    article = driver.find_element(By.TAG_NAME, "article")
                    print(f"🔍 article 요소 발견")
                except NoSuchElementException:
                    print(f"⚠️ article 요소를 찾을 수 없습니다. 전체 페이지에서 검색합니다.")
                
                # 비디오 찾기 (article이 있으면 article 내에서, 없으면 전체 페이지에서)
                if article:
                    video_elements = article.find_elements(By.CSS_SELECTOR, "video")
                    if not video_elements:
                        video_elements = driver.find_elements(By.CSS_SELECTOR, "video")
                else:
                    video_elements = driver.find_elements(By.CSS_SELECTOR, "video")
                
                print(f"🔍 video 요소 개수: {len(video_elements)}")
                
                for video in video_elements:
                    video_src = video.get_attribute("src")
                    if not video_src:
                        video_src = video.get_attribute("data-src")
                    
                    if video_src:
                        video_count += 1
                        print(f"✅ 비디오 태그 발견! (#{video_count})")
                        
                        # 비디오를 찾은 후에 해당 비디오의 오디오 버튼 찾기
                        find_and_click_audio_button_near_video(driver, video)
                        
                        print(f"   📹 video.src: {video_src[:80]}...")
                        
                        # blob URL인 경우 처리
                        if video_src.startswith('blob:'):
                            print(f"   🔄 blob URL 확인됨, 처리 시작...")
                            
                            # blob → base64 변환
                            print(f"   🔄 blob → base64 변환 중...")
                            base64_data = extract_video_blob_to_base64(driver, video)
                            
                            if not base64_data:
                                print(f"   ⚠️ base64 변환 실패")
                                continue
                            
                            print(f"   ✅ base64 변환 완료 (길이: {len(base64_data)})")
                            
                            # Python에서 base64 디코딩
                            print(f"   🔄 base64 디코딩 중...")
                            try:
                                video_bytes = base64.b64decode(base64_data)
                                print(f"   ✅ 디코딩 완료 (크기: {len(video_bytes)} bytes)")
                            except Exception as e:
                                print(f"   ⚠️ base64 디코딩 실패: {e}")
                                continue
                            
                            # BytesIO로 변환
                            video_io = io.BytesIO(video_bytes)
                            
                            # ffmpeg/Whisper 처리
                            print(f"   🔄 ffmpeg/Whisper 처리 중...")
                            voice_text = process_video_with_ffmpeg_whisper(video_bytes)
                            
                            if voice_text:
                                print(f"   ✅ 음성 텍스트 추출 완료: {voice_text[:100]}...")
                                results.append({
                                    "video_index": video_count,
                                    "video_src": video_src,
                                    "video_size": len(video_bytes),
                                    "voice_text": voice_text
                                })
                            else:
                                print(f"   ⚠️ 음성 텍스트 추출 실패")
                        else:
                            print(f"   ℹ️ blob URL이 아닙니다. (일반 URL)")
                
            except Exception as e:
                print(f"⚠️ 대체 방법도 실패: {e}")
            
            # "다음" 버튼 찾기
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="다음"]')
                if next_button.is_displayed() and next_button.is_enabled():
                    print("➡️ '다음' 버튼 클릭 중...")
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(3)
                    continue
            except NoSuchElementException:
                pass
            
            break
        
        # 각 li 요소 내에서 video 태그 찾기
        for li in li_elements:
            try:
                # 비디오 찾기 (여러 셀렉터 시도)
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
                
                # 비디오가 있는지 확인하고 is_video 정보 저장
                has_video = video is not None
                if has_video:
                    # li 요소 내에서 비디오와 오디오 버튼을 함께 찾기
                    # 비디오가 있으면 해당 li 요소 내에서만 오디오 버튼을 찾음
                    audio_button_clicked = find_and_click_audio_button_in_li(driver, li)
                
                if video:
                    video_count += 1
                    print(f"✅ 비디오 태그 발견! (#{video_count})")
                    
                    # video 태그의 src 속성 확인
                    video_src = video.get_attribute("src")
                    if not video_src:
                        video_src = video.get_attribute("data-src")
                    
                    if video_src:
                        print(f"   📹 video.src: {video_src[:80]}...")
                        
                        # blob URL인 경우 처리
                        if video_src.startswith('blob:'):
                            print(f"   🔄 blob URL 확인됨, 처리 시작...")
                            
                            # blob → base64 변환
                            print(f"   🔄 blob → base64 변환 중...")
                            base64_data = extract_video_blob_to_base64(driver, video)
                            
                            if not base64_data:
                                print(f"   ⚠️ base64 변환 실패")
                                continue
                            
                            print(f"   ✅ base64 변환 완료 (길이: {len(base64_data)})")
                            
                            # Python에서 base64 디코딩
                            print(f"   🔄 base64 디코딩 중...")
                            try:
                                video_bytes = base64.b64decode(base64_data)
                                print(f"   ✅ 디코딩 완료 (크기: {len(video_bytes)} bytes)")
                            except Exception as e:
                                print(f"   ⚠️ base64 디코딩 실패: {e}")
                                continue
                            
                            # BytesIO로 변환
                            video_io = io.BytesIO(video_bytes)
                            
                            # ffmpeg/Whisper 처리
                            print(f"   🔄 ffmpeg/Whisper 처리 중...")
                            voice_text = process_video_with_ffmpeg_whisper(video_bytes)
                            
                            if voice_text:
                                print(f"   ✅ 음성 텍스트 추출 완료: {voice_text[:100]}...")
                                results.append({
                                    "is_video": "Y",
                                    "video_index": video_count,
                                    "video_src": video_src,
                                    "video_size": len(video_bytes),
                                    "voice_text": voice_text
                                })
                            else:
                                print(f"   ⚠️ 음성 텍스트 추출 실패")
                                results.append({
                                    "is_video": "Y",
                                    "video_index": video_count,
                                    "video_src": video_src,
                                    "video_size": len(video_bytes),
                                    "voice_text": None
                                })
                        else:
                            print(f"   ℹ️ blob URL이 아닙니다. (일반 URL)")
                    else:
                        # source 태그 확인
                        try:
                            source = video.find_element(By.CSS_SELECTOR, "source")
                            source_src = source.get_attribute("src")
                            if source_src:
                                print(f"   📹 source.src: {source_src[:80]}...")
                        except NoSuchElementException:
                            pass
                else:
                    # 비디오가 없는 경우 is_video="N" 정보 저장
                    print(f"   ℹ️ 이 li 요소에는 비디오가 없습니다. (이미지 슬라이드)")
                    results.append({
                        "is_video": "N",
                        "video_index": None,
                        "voice_text": None
                    })
                
            except NoSuchElementException:
                # 비디오를 찾지 못한 경우
                print(f"   ℹ️ 이 li 요소에는 비디오를 찾을 수 없습니다.")
                results.append({
                    "is_video": "N",
                    "video_index": None,
                    "voice_text": None
                })
                continue
            except Exception as e:
                print(f"⚠️ 비디오 추출 중 오류: {e}")
                # 오류 발생 시에도 is_video 정보 저장
                results.append({
                    "is_video": "N",
                    "video_index": None,
                    "voice_text": None
                })
                continue
        
        # "다음" 버튼 찾기 (여러 셀렉터 시도)
        next_button = None
        next_selectors = [
            'button[aria-label="다음"]._afxw._al46._al47',
            'button[aria-label="다음"]',
            'button[aria-label*="다음"]',
        ]
        
        for next_selector in next_selectors:
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, next_selector)
                break
            except NoSuchElementException:
                continue
        
        if next_button:
            # 버튼이 보이고 클릭 가능한지 확인
            if next_button.is_displayed() and next_button.is_enabled():
                print("➡️ '다음' 버튼 클릭 중...")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)  # 비디오 로드 대기 시간
            else:
                print("ℹ️ '다음' 버튼이 비활성화되어 있습니다.")
                break
        else:
            print("ℹ️ '다음' 버튼을 찾을 수 없습니다. 모든 비디오를 확인했습니다.")
            break
    
    print(f"\n📊 총 {video_count}개의 비디오 태그를 발견했습니다.")
    return results


def main():
    """메인 함수"""
    driver = None
    
    try:
        # WebDriver 설정
        print("🚀 WebDriver 초기화 중...")
        driver = setup_driver()
        
        # Instagram 로그인
        login_instagram(driver)
        
        # ============================================
        # 테스트용 URL 설정 (여기에 Instagram 게시글 URL을 입력하세요)
        # ============================================
        test_url = "https://www.instagram.com/yeonjuleee/reel/DRL9pRWkRgo/"  # 실제 URL로 변경 필요
        # ============================================
        
        # 음성 추출
        results = extract_voice_from_instagram_post(driver, test_url)
        
        if results:
            print("\n" + "="*60)
            print("📊 추출 결과")
            print("="*60)
            for result in results:
                print(f"비디오 #{result['video_index']}:")
                print(f"  크기: {result['video_size']} bytes")
                print(f"  음성 텍스트: {result['voice_text']}")
            print("="*60)
        else:
            print("⚠️ 추출된 결과가 없습니다.")
    
    except Exception as e:
        print(f"⚠️ 오류 발생: {e}")
        import traceback
        print(traceback.format_exc())
    
    finally:
        if driver:
            driver.quit()
            print("✅ WebDriver 종료")


if __name__ == "__main__":
    main()

