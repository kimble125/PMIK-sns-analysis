"""
Google Colab - 셀 5: 결과 확인 및 다운로드
"""

import pandas as pd
import glob
import os
from google.colab import files

print("="*60)
print("📊 크롤링 결과 확인")
print("="*60)

# 결과 파일 검색
result_dir = '/content/drive/MyDrive/youtube_crawl_results'
csv_files = glob.glob(f'{result_dir}/*.csv')
csv_files = [f for f in csv_files if 'youtube_pm_v3_1_colab' in f]
csv_files = sorted(csv_files, key=os.path.getmtime, reverse=True)

if not csv_files:
    print("\n❌ 결과 파일을 찾을 수 없습니다.")
    print("\n📋 확인사항:")
    print("   1. 크롤러가 실행되었는지 확인")
    print("   2. 로그 파일 확인:")
    
    log_path = '/content/drive/MyDrive/crawler.log'
    if os.path.exists(log_path):
        print("\n📋 로그 내용 (마지막 30줄):")
        with open(log_path, 'r') as f:
            lines = f.readlines()
            print(''.join(lines[-30:]))
    else:
        print("   ❌ 로그 파일도 없습니다")
else:
    latest_file = csv_files[0]
    file_name = os.path.basename(latest_file)
    file_size = os.path.getsize(latest_file) / 1024 / 1024  # MB
    
    print(f"\n✅ 최신 결과 파일 발견!")
    print(f"📁 파일명: {file_name}")
    print(f"💾 크기: {file_size:.2f} MB")
    print(f"📍 위치: {latest_file}")
    
    # CSV 읽기
    print("\n📊 데이터 분석 중...")
    df = pd.read_csv(latest_file)
    
    print("\n" + "="*60)
    print("📈 수집 통계")
    print("="*60)
    
    # 기본 통계
    total_videos = len(df)
    print(f"\n🎬 총 비디오: {total_videos}개")
    
    # 멀티미디어 처리 통계
    if 'transcript_text' in df.columns:
        with_transcript = (df['transcript_text'].notna() & (df['transcript_text'] != '')).sum()
        transcript_rate = with_transcript / total_videos * 100
        print(f"🎤 음성인식 성공: {with_transcript}개 ({transcript_rate:.1f}%)")
        
        # 소스별 통계
        if 'transcript_source' in df.columns:
            source_counts = df['transcript_source'].value_counts()
            print(f"\n   📋 소스별:")
            for source, count in source_counts.items():
                if source != 'none':
                    print(f"      - {source}: {count}개")
    
    if 'thumbnail_text_ocr' in df.columns:
        with_ocr = (df['thumbnail_text_ocr'].notna() & (df['thumbnail_text_ocr'] != '')).sum()
        ocr_rate = with_ocr / total_videos * 100
        print(f"👁️ 썸네일 OCR 성공: {with_ocr}개 ({ocr_rate:.1f}%)")
    
    # 전화번호/후원번호 통계
    if 'sponsor_phone' in df.columns:
        with_phone = (df['sponsor_phone'].notna() & (df['sponsor_phone'] != '')).sum()
        print(f"📞 전화번호 추출: {with_phone}개")
    
    if 'sponsor_partner_id' in df.columns:
        with_partner = (df['sponsor_partner_id'].notna() & (df['sponsor_partner_id'] != '')).sum()
        print(f"🏷️ 후원번호 추출: {with_partner}개")
    
    # 조회수 통계
    if 'view_count' in df.columns:
        total_views = df['view_count'].sum()
        avg_views = df['view_count'].mean()
        print(f"\n👀 총 조회수: {total_views:,}회")
        print(f"📊 평균 조회수: {avg_views:,.0f}회")
    
    # 샘플 데이터 표시
    print("\n" + "="*60)
    print("📋 샘플 데이터 (상위 5개)")
    print("="*60)
    
    display_columns = ['title', 'channel_name', 'view_count', 'transcript_source']
    available_columns = [col for col in display_columns if col in df.columns]
    
    if available_columns:
        sample_df = df[available_columns].head(5)
        # 제목 길이 제한
        if 'title' in sample_df.columns:
            sample_df['title'] = sample_df['title'].str[:40] + '...'
        print(sample_df.to_string(index=False))
    
    # 다운로드 옵션
    print("\n" + "="*60)
    print("💾 결과 다운로드")
    print("="*60)
    
    download = input("\n결과 파일을 다운로드하시겠습니까? (y/n): ").lower().strip()
    
    if download == 'y':
        print("\n📥 다운로드 중...")
        files.download(latest_file)
        print("✅ 다운로드 완료!")
    else:
        print(f"\n📁 파일 위치: {latest_file}")
        print("💡 Google Drive에서 직접 다운로드할 수 있습니다.")
    
    # 추가 파일 확인
    print("\n" + "="*60)
    print("📂 기타 파일")
    print("="*60)
    
    # 체크포인트 파일
    checkpoint_files = glob.glob(f'{result_dir}/checkpoint*.json')
    if checkpoint_files:
        print(f"\n💾 체크포인트 파일: {len(checkpoint_files)}개")
    
    # 로그 파일
    log_path = '/content/drive/MyDrive/crawler.log'
    if os.path.exists(log_path):
        log_size = os.path.getsize(log_path) / 1024
        print(f"📋 로그 파일: {log_size:.1f} KB")
        
        view_log = input("\n로그 파일을 확인하시겠습니까? (y/n): ").lower().strip()
        if view_log == 'y':
            print("\n📋 로그 내용 (마지막 50줄):")
            print("="*60)
            with open(log_path, 'r') as f:
                lines = f.readlines()
                print(''.join(lines[-50:]))

print("\n" + "="*60)
print("🎉 모든 작업 완료!")
print("="*60)
