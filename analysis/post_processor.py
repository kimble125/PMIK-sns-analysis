#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International 수집 데이터 후처리기

이 모듈은 크롤러에서 분리된 분석용 모듈입니다.
수집된 원시 데이터에 파생 컬럼을 추가하고 분석을 위한 전처리를 수행합니다.

포함 기능:
1. 콘텐츠 타입 분류 (ContentTypeClassifier 활용)
2. 텍스트 길이 계산
3. 해시태그 개수 계산
4. 이미지/비디오 개수 계산
5. 연도/월 추출

사용법:
    python post_processor.py --input posts.csv --output posts_processed.csv

작성자: PMI Korea 데이터 분석팀
버전: 1.0.0
최종 수정일: 2025-11-26
"""

import re
import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime
from content_type_classifier import ContentTypeClassifier


def calculate_text_length(text: str) -> int:
    """텍스트 길이 계산 (공백 제외)"""
    if pd.isna(text) or not text:
        return 0
    return len(str(text).replace(' ', ''))


def count_hashtags(hashtags: str) -> int:
    """해시태그 개수 계산"""
    if pd.isna(hashtags) or not hashtags:
        return 0
    return len(str(hashtags).split(','))


def count_urls(urls: str) -> int:
    """URL 개수 계산 (이미지/비디오)"""
    if pd.isna(urls) or not urls:
        return 0
    return len(str(urls).split(','))


def extract_year_month(date_str: str) -> tuple:
    """날짜에서 연도/월 추출"""
    if pd.isna(date_str) or not date_str:
        return '', ''
    
    try:
        # YYYY-MM-DD 형식
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', str(date_str))
        if match:
            return match.group(1), match.group(2)
        
        # YYYY. MM. DD. 형식
        match = re.search(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})', str(date_str))
        if match:
            return match.group(1), f"{int(match.group(2)):02d}"
        
        return '', ''
    except:
        return '', ''


def has_sponsor_info(row: pd.Series) -> bool:
    """추천인 정보 유무 확인"""
    phone = row.get('sponsor_phone', '')
    sponsor_id = row.get('content_sponsor_id', '')
    
    has_phone = pd.notna(phone) and str(phone).strip() != ''
    has_id = pd.notna(sponsor_id) and str(sponsor_id).strip() != ''
    
    return has_phone or has_id


def process_dataframe(df: pd.DataFrame, add_content_type: bool = True) -> pd.DataFrame:
    """DataFrame에 파생 컬럼 추가"""
    result_df = df.copy()
    
    print("   ├─ 텍스트 길이 계산...")
    result_df['content_length'] = result_df['content'].apply(calculate_text_length)
    result_df['title_length'] = result_df['title'].apply(calculate_text_length)
    
    print("   ├─ 해시태그 개수 계산...")
    result_df['hashtag_count'] = result_df['hashtags'].apply(count_hashtags)
    
    print("   ├─ 이미지/비디오 개수 계산...")
    result_df['image_count'] = result_df['image_urls'].apply(count_urls)
    result_df['video_count'] = result_df['video_urls'].apply(count_urls)
    
    print("   ├─ 연도/월 추출...")
    year_month = result_df['published_datetime'].apply(extract_year_month)
    result_df['published_year'] = year_month.apply(lambda x: x[0])
    result_df['published_month'] = year_month.apply(lambda x: x[1])
    
    print("   ├─ 추천인 정보 유무 확인...")
    result_df['has_sponsor'] = result_df.apply(has_sponsor_info, axis=1)
    
    if add_content_type:
        print("   ├─ 콘텐츠 타입 분류...")
        classifier = ContentTypeClassifier()
        
        # 이미 분류된 경우 스킵
        if 'content_type' not in result_df.columns or result_df['content_type'].isna().all():
            result_df = classifier.classify_dataframe(result_df)
        else:
            print("      (이미 분류됨, 스킵)")
    
    print("   └─ 완료!")
    return result_df


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='PM-International 수집 데이터 후처리기')
    parser.add_argument('--input', '-i', required=True, help='입력 CSV 파일 경로')
    parser.add_argument('--output', '-o', help='출력 CSV 파일 경로 (기본: input_processed.csv)')
    parser.add_argument('--no-content-type', action='store_true', help='콘텐츠 타입 분류 생략')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
        return
    
    output_path = args.output or str(input_path.parent / (input_path.stem + '_processed.csv'))
    
    print(f"📖 파일 로드 중: {input_path}")
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    print(f"   {len(df)}개 게시물 로드됨")
    
    print("🔧 후처리 진행 중...")
    result_df = process_dataframe(df, add_content_type=not args.no_content_type)
    
    print(f"💾 결과 저장 중: {output_path}")
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # 통계 출력
    print("\n📊 후처리 결과 통계:")
    print(f"   총 게시물: {len(result_df)}개")
    print(f"   평균 본문 길이: {result_df['content_length'].mean():.0f}자")
    print(f"   평균 해시태그 수: {result_df['hashtag_count'].mean():.1f}개")
    print(f"   평균 이미지 수: {result_df['image_count'].mean():.1f}개")
    print(f"   추천인 정보 포함: {result_df['has_sponsor'].sum()}개 ({result_df['has_sponsor'].mean()*100:.1f}%)")
    
    if 'content_type_primary' in result_df.columns:
        print("\n   콘텐츠 타입 분포:")
        type_counts = result_df['content_type_primary'].value_counts().head(5)
        for content_type, count in type_counts.items():
            print(f"      {content_type}: {count}개")
    
    print(f"\n✅ 완료! {output_path}")


if __name__ == "__main__":
    main()
