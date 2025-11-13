#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 1: 크롤링 데이터에서 이미지/비디오 URL 추출 및 전처리
- 중복 제거, 유효성 검사, CSV 저장
"""

import pandas as pd
import re
from urllib.parse import urlparse
from typing import List, Set
import json

def parse_url_string(url_string: str) -> List[str]:
    """
    쉼표로 구분된 URL 문자열을 리스트로 변환
    """
    if pd.isna(url_string) or url_string == '':
        return []
    
    # 쉼표로 분리하고 공백 제거
    urls = [url.strip() for url in str(url_string).split(',')]
    return [url for url in urls if url and url.startswith('http')]

def is_valid_image_url(url: str) -> bool:
    """
    유효한 이미지 URL인지 확인
    - GIF 애니메이션 제외 (아이콘, 버튼 등)
    - 로그 URL 제외
    """
    exclude_patterns = [
        'btn_',           # 버튼 이미지
        'img_ani_',       # 애니메이션 아이콘
        'icon_',          # 아이콘
        '/imgs/btn_',     # 버튼 경로
        'spacer.gif',     # 스페이서
    ]
    
    url_lower = url.lower()
    return not any(pattern in url_lower for pattern in exclude_patterns)

def categorize_video_url(url: str) -> str:
    """
    비디오 URL 유형 구분
    """
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'mblogvideo' in url:
        return 'naver_blog'
    else:
        return 'other'

def extract_youtube_video_id(url: str) -> str:
    """
    유튜브 URL에서 비디오 ID 추출
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ''

def main():
    print("="*70)
    print("STEP 1: URL 추출 및 전처리 시작")
    print("="*70)
    
    # CSV 파일 읽기
    input_file = 'naver_blog_pm_v8_3_20251109_211033.csv'  # 파일명 수정 필요 시 여기 변경
    print(f"\n📂 입력 파일: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"✅ 전체 포스트 수: {len(df)}")
    except FileNotFoundError:
        print(f"❌ 오류: {input_file} 파일을 찾을 수 없습니다.")
        print("   현재 디렉토리에 CSV 파일이 있는지 확인하세요.")
        return
    
    # 1. 이미지 URL 추출
    print("\n" + "="*70)
    print("📸 이미지 URL 처리 중...")
    print("="*70)
    
    all_image_urls: Set[str] = set()
    image_data = []
    
    for idx, row in df.iterrows():
        post_id = row['post_id']
        urls = parse_url_string(row['image_urls'])
        
        # 유효한 이미지만 필터링
        valid_urls = [url for url in urls if is_valid_image_url(url)]
        
        for url in valid_urls:
            if url not in all_image_urls:
                all_image_urls.add(url)
                image_data.append({
                    'post_id': post_id,
                    'url': url,
                    'type': 'image'
                })
    
    print(f"✅ 고유 이미지 URL: {len(all_image_urls)}개")
    print(f"   (중복 제거 및 버튼/아이콘 필터링 완료)")
    
    # 2. 비디오 URL 추출
    print("\n" + "="*70)
    print("🎬 비디오 URL 처리 중...")
    print("="*70)
    
    video_data = []
    youtube_count = 0
    naver_count = 0
    
    for idx, row in df.iterrows():
        post_id = row['post_id']
        urls = parse_url_string(row['video_urls'])
        
        for url in urls:
            video_type = categorize_video_url(url)
            
            video_info = {
                'post_id': post_id,
                'url': url,
                'type': video_type
            }
            
            # 유튜브인 경우 video_id 추출
            if video_type == 'youtube':
                video_id = extract_youtube_video_id(url)
                video_info['youtube_video_id'] = video_id
                youtube_count += 1
            elif video_type == 'naver_blog':
                naver_count += 1
            
            video_data.append(video_info)
    
    print(f"✅ 전체 비디오 URL: {len(video_data)}개")
    print(f"   - 유튜브: {youtube_count}개")
    print(f"   - 네이버 블로그: {naver_count}개")
    
    # 3. CSV 파일로 저장
    print("\n" + "="*70)
    print("💾 결과 파일 저장 중...")
    print("="*70)
    
    # 이미지 URL 저장
    if image_data:
        image_df = pd.DataFrame(image_data)
        image_output = 'extracted_image_urls.csv'
        image_df.to_csv(image_output, index=False, encoding='utf-8-sig')
        print(f"✅ {image_output} 저장 완료 ({len(image_df)}개)")
    
    # 비디오 URL 저장
    if video_data:
        video_df = pd.DataFrame(video_data)
        video_output = 'extracted_video_urls.csv'
        video_df.to_csv(video_output, index=False, encoding='utf-8-sig')
        print(f"✅ {video_output} 저장 완료 ({len(video_df)}개)")
    
    # 4. 통계 요약 저장
    summary = {
        'total_posts': len(df),
        'total_images': len(all_image_urls),
        'total_videos': len(video_data),
        'youtube_videos': youtube_count,
        'naver_blog_videos': naver_count,
        'extraction_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open('extraction_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ extraction_summary.json 저장 완료")
    
    # 5. 최종 요약
    print("\n" + "="*70)
    print("🎉 URL 추출 완료!")
    print("="*70)
    print(f"""
📊 최종 통계:
   - 전체 포스트: {len(df)}개
   - 이미지 URL: {len(all_image_urls)}개
   - 비디오 URL: {len(video_data)}개
     ├─ 유튜브: {youtube_count}개
     └─ 네이버: {naver_count}개

📁 생성된 파일:
   1. extracted_image_urls.csv (Google Colab 업로드용)
   2. extracted_video_urls.csv (Google Colab 업로드용)
   3. extraction_summary.json (통계 정보)

🚀 다음 단계:
   STEP 2의 Google Colab 노트북으로 이동하여
   위 2개 CSV 파일을 업로드하세요!
    """)

if __name__ == "__main__":
    main()
