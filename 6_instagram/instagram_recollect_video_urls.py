"""
Instagram 비디오 URL 재수집 스크립트
instagram_media.json에서 media_type이 "VIDEO"이고 media_count가 0이거나 media_url이 비어있는 항목의 비디오 URL을 재수집합니다.

사용 방법:
    python instagram_recollect_video_urls.py [--test]
    
    옵션:
        --test, -t: 테스트 모드 (상위 10개만 처리)
"""

import json
import logging
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
import os

# instagram_filter_userposts.py에서 필요한 함수 import
import sys
sys.path.insert(0, str(Path(__file__).parent))
from instagram_filter_userposts import setup_driver, login_instagram, setup_logging

# .env 파일에서 로그인 정보 불러오기
load_dotenv()

# JSON 파일 경로
MEDIA_JSON = Path("instagram_media.json")
LOG_PATH = Path("instagram_recollect_video.log")


def extract_real_url(url: str) -> str:
    """blob: URL에서 실제 URL 추출"""
    if url and url.startswith('blob:'):
        # blob:https://... 형식에서 https://... 부분 추출
        if 'https://' in url:
            return url[url.find('https://'):]
        elif 'http://' in url:
            return url[url.find('http://'):]
    return url


def extract_video_urls(driver, permalink: str) -> list:
    """
    permalink 페이지에서 비디오 URL 추출
    
    Args:
        driver: Selenium WebDriver
        permalink: Instagram permalink URL
        
    Returns:
        비디오 URL 리스트
    """
    media_urls = []
    seen_urls = set()
    
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
        
        # 비디오 요소 찾기
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
                if media_urls:
                    break
                    
            except Exception as e:
                print(f"  ⚠️ 비디오 URL 추출 중 오류: {e}")
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
        
    except Exception as e:
        print(f"  ❌ 비디오 URL 추출 실패: {e}")
        import traceback
        traceback.print_exc()
    
    return media_urls


def main(test_mode=False):
    """메인 함수"""
    # 로깅 초기화
    setup_logging(str(LOG_PATH))
    logging.info("=" * 80)
    logging.info("프로그램 시작 - instagram_recollect_video_urls.py")
    if test_mode:
        logging.info("테스트 모드: 상위 10개만 처리")
    logging.info("=" * 80)
    
    print("=" * 60)
    print("Instagram 비디오 URL 재수집")
    if test_mode:
        print("🧪 테스트 모드: 상위 10개만 처리합니다")
    print("=" * 60)
    
    # instagram_media.json 로드
    if not MEDIA_JSON.exists():
        print(f"❌ {MEDIA_JSON} 파일을 찾을 수 없습니다.")
        return
    
    print(f"\n📂 {MEDIA_JSON} 파일 로드 중...")
    try:
        with open(MEDIA_JSON, "r", encoding="utf-8") as f:
            media_data = json.load(f)
        
        if not isinstance(media_data, list):
            print(f"❌ {MEDIA_JSON} 파일 형식이 올바르지 않습니다. (리스트가 아님)")
            return
        
        print(f"✅ 총 {len(media_data)}개 항목 로드됨")
    except Exception as e:
        print(f"❌ {MEDIA_JSON} 파일 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # media_type이 "VIDEO"이고 media_count가 0이거나 media_url이 비어있는 항목 필터링
    target_items = []
    for item in media_data:
        media_type = item.get("media_type", "").upper()
        media_count = item.get("media_count", 0)
        media_url = item.get("media_url", [])
        
        if media_type == "VIDEO":
            if media_count == 0 or not media_url or len(media_url) == 0:
                target_items.append(item)
    
    print(f"\n📊 재수집 대상: {len(target_items)}개")
    if len(target_items) == 0:
        print("✅ 재수집할 비디오가 없습니다.")
        return
    
    # 테스트 모드면 상위 10개만 처리
    if test_mode:
        target_items = target_items[:10]
        print(f"🧪 테스트 모드: 상위 {len(target_items)}개만 처리합니다")
    
    # 처음 10개 항목 정보 출력
    print(f"\n📋 재수집 대상 항목 (처음 10개):")
    for idx, item in enumerate(target_items[:10], 1):
        permalink = item.get("permalink", "N/A")
        handle = item.get("handle", "N/A")
        print(f"  {idx}. @{handle}: {permalink[:60]}...")
    if len(target_items) > 10:
        print(f"  ... 외 {len(target_items) - 10}개")
    
    # Selenium WebDriver 초기화
    print(f"\n🔧 WebDriver 초기화 중...")
    driver = None
    try:
        driver = setup_driver()
        
        # Instagram 로그인
        print(f"\n🔐 Instagram 로그인 중...")
        if not login_instagram(driver):
            print("❌ 로그인 실패. 프로그램을 종료합니다.")
            return
        
        # 통계
        success_count = 0
        fail_count = 0
        updated_count = 0
        
        # 각 항목 처리
        print(f"\n{'='*60}")
        print(f"비디오 URL 재수집 시작 ({len(target_items)}개)")
        print(f"{'='*60}\n")
        
        for idx, item in enumerate(target_items, 1):
            permalink = item.get("permalink")
            handle = item.get("handle", "N/A")
            
            if not permalink:
                print(f"\n[{idx}/{len(target_items)}] ⚠️ permalink가 없습니다. 건너뜁니다.")
                fail_count += 1
                continue
            
            print(f"\n[{idx}/{len(target_items)}] 처리 중: @{handle}")
            print(f"  🔍 permalink: {permalink}")
            logging.info(f"[{idx}/{len(target_items)}] 처리 중: @{handle}, permalink: {permalink}")
            
            # 비디오 URL 추출
            media_urls = extract_video_urls(driver, permalink)
            
            if media_urls:
                # media_url과 media_count 업데이트
                item["media_url"] = media_urls
                item["media_count"] = len(media_urls)
                updated_count += 1
                success_count += 1
                print(f"  ✅ 비디오 URL {len(media_urls)}개 수집 완료")
                logging.info(f"비디오 URL {len(media_urls)}개 수집 완료: {permalink}")
            else:
                fail_count += 1
                print(f"  ❌ 비디오 URL을 찾지 못했습니다.")
                logging.warning(f"비디오 URL을 찾지 못함: {permalink}")
            
            # 요청 간 딜레이 (Instagram 차단 방지)
            time.sleep(2)
        
        # JSON 파일 저장
        if updated_count > 0:
            print(f"\n💾 {MEDIA_JSON} 파일 저장 중...")
            try:
                with open(MEDIA_JSON, "w", encoding="utf-8") as f:
                    json.dump(media_data, f, ensure_ascii=False, indent=2)
                print(f"✅ {MEDIA_JSON} 파일 저장 완료!")
                logging.info(f"{MEDIA_JSON} 파일 저장 완료: {updated_count}개 항목 업데이트")
            except Exception as e:
                print(f"❌ {MEDIA_JSON} 파일 저장 실패: {e}")
                logging.error(f"{MEDIA_JSON} 파일 저장 실패: {e}", exc_info=True)
        
        # 최종 통계 출력
        print(f"\n{'='*60}")
        print(f"✅ 재수집 완료!")
        print(f"   총 처리: {len(target_items)}개")
        print(f"   성공: {success_count}개")
        print(f"   실패: {fail_count}개")
        print(f"   업데이트: {updated_count}개")
        print(f"{'='*60}")
        
        logging.info("=" * 80)
        logging.info("재수집 완료")
        logging.info(f"총 처리: {len(target_items)}개")
        logging.info(f"성공: {success_count}개")
        logging.info(f"실패: {fail_count}개")
        logging.info(f"업데이트: {updated_count}개")
        logging.info("=" * 80)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        logging.error(f"오류 발생: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
                print("\n🔒 브라우저 종료")
            except:
                pass


if __name__ == "__main__":
    import sys
    
    test_mode = False
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ['--test', '-t']:
                test_mode = True
    
    main(test_mode=test_mode)

