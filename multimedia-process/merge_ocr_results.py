#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 결과를 원본 네이버 블로그 CSV에 병합

입력:
- naver_blog_pm_v8_3_20251109_211033.csv (원본)
- pmi_ocr_results/naver_image_ocr_results.csv
- pmi_ocr_results/naver_video_frame_ocr_results.csv
- pmi_ocr_results/naver_whisper_transcript_results.csv
- pmi_ocr_results/naver_youtube_transcript_results.csv

출력:
- naver_blog_pm_v8_3_with_ocr.csv (병합 결과)
"""

import pandas as pd
import json
from pathlib import Path

# 파일 경로
BASE_DIR = Path("/Users/kimble/Documents/IT/PMIK-sns-analysis")
ORIGINAL_CSV = BASE_DIR / "multimedia-process" / "naver_blog_pm_v8_3_20251109_211033.csv"
OCR_DIR = BASE_DIR / "pmi_ocr_results"
OUTPUT_CSV = BASE_DIR / "multimedia-process" / "naver_blog_pm_v8_3_with_ocr.csv"

# OCR 결과 파일들
IMAGE_OCR = OCR_DIR / "naver_image_ocr_results.csv"
VIDEO_FRAME_OCR = OCR_DIR / "naver_video_frame_ocr_results.csv"
WHISPER_TRANSCRIPT = OCR_DIR / "naver_whisper_transcript_results.csv"
YOUTUBE_TRANSCRIPT = OCR_DIR / "naver_youtube_transcript_results.csv"

def main():
    print("=" * 80)
    print("OCR 결과 병합 시작")
    print("=" * 80)
    
    # 1. 원본 CSV 로드
    print("\n[1/5] 원본 CSV 로드 중...")
    df_original = pd.read_csv(ORIGINAL_CSV, encoding='utf-8-sig')
    print(f"   원본 데이터: {len(df_original):,}개 게시물")
    print(f"   컬럼: {list(df_original.columns)}")
    
    # 2. 이미지 OCR 결과 로드 및 집계
    print("\n[2/5] 이미지 OCR 결과 처리 중...")
    df_image_ocr = pd.read_csv(IMAGE_OCR, encoding='utf-8-sig')
    print(f"   이미지 OCR: {len(df_image_ocr):,}개 이미지")
    
    # post_id별로 OCR 텍스트 집계
    image_ocr_grouped = df_image_ocr.groupby('post_id').agg({
        'ocr_text': lambda x: ' | '.join([str(text) for text in x if pd.notna(text) and str(text).strip()]),
        'confidence': 'mean',
        'status': lambda x: 'success' if all(x == 'success') else 'partial'
    }).reset_index()
    
    image_ocr_grouped.columns = ['post_id', 'image_ocr_text', 'image_ocr_confidence', 'image_ocr_status']
    print(f"   집계 완료: {len(image_ocr_grouped):,}개 게시물")
    
    # 3. 비디오 프레임 OCR 결과 로드 및 집계
    print("\n[3/5] 비디오 프레임 OCR 결과 처리 중...")
    df_video_ocr = pd.read_csv(VIDEO_FRAME_OCR, encoding='utf-8-sig')
    print(f"   비디오 프레임 OCR: {len(df_video_ocr):,}개 비디오")
    
    video_ocr_grouped = df_video_ocr.groupby('post_id').agg({
        'frame_ocr_text': lambda x: ' | '.join([str(text) for text in x if pd.notna(text) and str(text).strip()]),
        'confidence': 'mean',
        'status': lambda x: 'success' if all(x == 'success') else 'partial'
    }).reset_index()
    
    video_ocr_grouped.columns = ['post_id', 'video_frame_ocr_text', 'video_frame_ocr_confidence', 'video_frame_ocr_status']
    print(f"   집계 완료: {len(video_ocr_grouped):,}개 게시물")
    
    # 4. Whisper 자막 결과 로드 및 집계
    print("\n[4/5] Whisper 자막 결과 처리 중...")
    df_whisper = pd.read_csv(WHISPER_TRANSCRIPT, encoding='utf-8-sig')
    print(f"   Whisper 자막: {len(df_whisper):,}개 비디오")
    
    # video_id를 기준으로 post_id 매핑 (whisper는 post_id가 없을 수 있음)
    whisper_grouped = df_whisper.groupby('video_id').agg({
        'transcript': 'first',
        'status': 'first',
        'post_id': 'first'
    }).reset_index()
    
    # post_id가 있는 것만 필터링
    whisper_grouped = whisper_grouped[whisper_grouped['post_id'].notna()]
    whisper_grouped.columns = ['video_id', 'whisper_transcript', 'whisper_status', 'post_id']
    print(f"   집계 완료: {len(whisper_grouped):,}개 게시물")
    
    # 5. YouTube 자막 결과 로드 및 집계
    print("\n[5/5] YouTube 자막 결과 처리 중...")
    df_youtube = pd.read_csv(YOUTUBE_TRANSCRIPT, encoding='utf-8-sig')
    print(f"   YouTube 자막: {len(df_youtube):,}개 비디오")
    
    youtube_grouped = df_youtube.groupby('post_id').agg({
        'transcript': lambda x: ' | '.join([str(text) for text in x if pd.notna(text) and str(text).strip()]),
        'status': lambda x: 'success' if all(x == 'success') else 'error'
    }).reset_index()
    
    youtube_grouped.columns = ['post_id', 'youtube_transcript', 'youtube_status']
    print(f"   집계 완료: {len(youtube_grouped):,}개 게시물")
    
    # 6. 병합
    print("\n[병합] OCR 결과를 원본에 병합 중...")
    
    # post_id를 정수형으로 변환
    df_original['post_id'] = df_original['post_id'].astype(str).astype(int)
    image_ocr_grouped['post_id'] = image_ocr_grouped['post_id'].astype(int)
    video_ocr_grouped['post_id'] = video_ocr_grouped['post_id'].astype(int)
    whisper_grouped['post_id'] = whisper_grouped['post_id'].astype(int)
    youtube_grouped['post_id'] = youtube_grouped['post_id'].astype(int)
    
    # 순차적으로 병합 (left join)
    df_merged = df_original.copy()
    
    # 이미지 OCR 병합
    df_merged = df_merged.merge(image_ocr_grouped, on='post_id', how='left')
    print(f"   이미지 OCR 병합: {df_merged['image_ocr_text'].notna().sum():,}개 게시물에 데이터 추가")
    
    # 비디오 프레임 OCR 병합
    df_merged = df_merged.merge(video_ocr_grouped, on='post_id', how='left')
    print(f"   비디오 프레임 OCR 병합: {df_merged['video_frame_ocr_text'].notna().sum():,}개 게시물에 데이터 추가")
    
    # Whisper 자막 병합
    df_merged = df_merged.merge(whisper_grouped[['post_id', 'whisper_transcript', 'whisper_status']], 
                                 on='post_id', how='left')
    print(f"   Whisper 자막 병합: {df_merged['whisper_transcript'].notna().sum():,}개 게시물에 데이터 추가")
    
    # YouTube 자막 병합
    df_merged = df_merged.merge(youtube_grouped, on='post_id', how='left')
    print(f"   YouTube 자막 병합: {df_merged['youtube_transcript'].notna().sum():,}개 게시물에 데이터 추가")
    
    # 7. 통합 OCR 텍스트 컬럼 생성 (모든 OCR 결과 통합)
    print("\n[통합] 통합 OCR 텍스트 컬럼 생성 중...")
    
    def combine_ocr_texts(row):
        """모든 OCR 텍스트를 하나로 통합"""
        texts = []
        
        if pd.notna(row.get('image_ocr_text')) and str(row['image_ocr_text']).strip():
            texts.append(f"[이미지] {row['image_ocr_text']}")
        
        if pd.notna(row.get('video_frame_ocr_text')) and str(row['video_frame_ocr_text']).strip():
            texts.append(f"[비디오프레임] {row['video_frame_ocr_text']}")
        
        if pd.notna(row.get('whisper_transcript')) and str(row['whisper_transcript']).strip():
            texts.append(f"[Whisper음성] {row['whisper_transcript']}")
        
        if pd.notna(row.get('youtube_transcript')) and str(row['youtube_transcript']).strip():
            texts.append(f"[YouTube자막] {row['youtube_transcript']}")
        
        return ' || '.join(texts) if texts else ''
    
    df_merged['ocr_combined_text'] = df_merged.apply(combine_ocr_texts, axis=1)
    print(f"   통합 OCR 텍스트: {df_merged['ocr_combined_text'].str.len().gt(0).sum():,}개 게시물")
    
    # 8. 저장
    print("\n[저장] 병합 결과 저장 중...")
    df_merged.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"   저장 완료: {OUTPUT_CSV}")
    
    # 9. 통계 출력
    print("\n" + "=" * 80)
    print("병합 완료 통계")
    print("=" * 80)
    print(f"총 게시물 수: {len(df_merged):,}개")
    print(f"\n[OCR 데이터 보유 현황]")
    print(f"  - 이미지 OCR: {df_merged['image_ocr_text'].notna().sum():,}개 ({df_merged['image_ocr_text'].notna().sum()/len(df_merged)*100:.1f}%)")
    print(f"  - 비디오 프레임 OCR: {df_merged['video_frame_ocr_text'].notna().sum():,}개 ({df_merged['video_frame_ocr_text'].notna().sum()/len(df_merged)*100:.1f}%)")
    print(f"  - Whisper 음성 자막: {df_merged['whisper_transcript'].notna().sum():,}개 ({df_merged['whisper_transcript'].notna().sum()/len(df_merged)*100:.1f}%)")
    print(f"  - YouTube 자막: {df_merged['youtube_transcript'].notna().sum():,}개 ({df_merged['youtube_transcript'].notna().sum()/len(df_merged)*100:.1f}%)")
    print(f"  - 통합 OCR 텍스트: {df_merged['ocr_combined_text'].str.len().gt(0).sum():,}개 ({df_merged['ocr_combined_text'].str.len().gt(0).sum()/len(df_merged)*100:.1f}%)")
    
    print(f"\n[컬럼 목록]")
    print(f"  원본 컬럼: {len(df_original.columns)}개")
    print(f"  병합 후 컬럼: {len(df_merged.columns)}개")
    print(f"  추가된 컬럼: {len(df_merged.columns) - len(df_original.columns)}개")
    print(f"\n  새로 추가된 컬럼:")
    new_columns = [col for col in df_merged.columns if col not in df_original.columns]
    for col in new_columns:
        print(f"    - {col}")
    
    print("\n" + "=" * 80)
    print("✅ 병합 완료!")
    print("=" * 80)

if __name__ == "__main__":
    main()
