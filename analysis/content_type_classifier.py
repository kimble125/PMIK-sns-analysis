#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM-International 콘텐츠 타입 분류기 (분석용)

이 모듈은 크롤러에서 분리된 분석용 모듈입니다.
수집된 원시 데이터에 콘텐츠 타입을 분류하여 파생 컬럼을 추가합니다.

사용법:
    python content_type_classifier.py --input posts.csv --output posts_classified.csv

작성자: PMI Korea 데이터 분석팀
버전: 1.0.0
최종 수정일: 2025-11-26
"""

import re
import pandas as pd
import argparse
from typing import List, Dict
from pathlib import Path


class ContentTypeClassifier:
    """게시물 콘텐츠 타입 자동 분류기 (19가지 타입)
    
    분석 단계에서 사용하며, 크롤러에서는 원시 데이터만 수집합니다.
    """
    
    PRIORITY = {
        'Undisclosed_Ad': 100,
        'Official_Announcement': 90,
        'News_Media': 85,
        'Video_Content': 80,
        'Image_Carousel': 75,
        'QA_Format': 70,
        'User_Review_Experience': 65,
        'Before_After': 60,
        'Text_Testimonial': 55,
        'Product_Recommendation': 50,
        'Price_Promotion': 45,
        'Comparison': 40,
        'Lifestyle_Daily': 35,
        'Storytelling': 30,
        'Business_Opportunity': 25,
        'Team_Group_Activity': 20,
        'Event_Challenge': 15,
        'Celebrity_Influencer': 10,
    }
    
    KEYWORDS = {
        'Undisclosed_Ad': [],  # 로직으로 처리
        'Official_Announcement': ['공지', '알림', '안내', '발표', '새소식', '업데이트'],
        'News_Media': ['뉴스', '기사', '보도', '취재', '인터뷰', '미디어', '언론'],
        'Video_Content': [],  # 로직으로 처리
        'Image_Carousel': [],  # 로직으로 처리
        'QA_Format': ['Q&A', 'Q.', 'A.', '질문', '답변', '자주', 'FAQ', '궁금', '?', '안전한가요'],
        'User_Review_Experience': ['후기', '체험', '사용해보니', '먹어보니', '경험', '느낀점', '솔직', '리얼', '개인적'],
        'Before_After': ['비포', '애프터', 'before', 'after', 'B&A', '전후', '변화', '달라진', '개선'],
        'Text_Testimonial': ['강력추천', '진짜좋아', '최고', '꼭', '완전', '대박', '인정', '믿어도', '강추'],
        'Product_Recommendation': ['추천', '강추', '추천인', '코드', '번호', '문의', '연락', '가입'],
        'Price_Promotion': ['가격', '할인', '이벤트', '프로모션', '특가', '세일', '%', '혜택', '구매', '정가'],
        'Comparison': ['비교', 'vs', 'VS', '차이', '다른점', '같은점', '어떤게', '선택'],
        'Lifestyle_Daily': ['일상', '라이프', '루틴', '하루', '웰니스', '건강한', '활력', '매일'],
        'Storytelling': ['스토리', '이야기', '계기', '시작', '여정', '변화', '인생', '과정'],
        'Business_Opportunity': ['사업', '부업', '수익', '벌다', '돈', '파트너', '가입', '모집', '기회', '비즈니스'],
        'Team_Group_Activity': ['콩그레스', '나셔널', '미팅', '세미나', '행사', '교육', '팀', '모임'],
        'Event_Challenge': ['챌린지', '이벤트', '체험단', '참여', '모집', '30일', '일주', '도전'],
        'Celebrity_Influencer': ['연예인', '유명인', '인플루언서', '선수', '국가대표', '스타', '운동선수'],
    }
    
    def __init__(self):
        """분류기 초기화"""
        pass
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화 (띄어쓰기 제거)"""
        if not text:
            return ""
        return re.sub(r'\s+', '', str(text).lower())
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """키워드 출현 횟수 계산"""
        text_normalized = self._normalize_text(text)
        count = 0
        for keyword in keywords:
            keyword_normalized = self._normalize_text(keyword)
            count += text_normalized.count(keyword_normalized)
        return count
    
    def classify(self, post_data: Dict) -> Dict:
        """게시물 분류 (다중 분류 지원, 최대 3개)"""
        title = str(post_data.get('title', ''))
        content = str(post_data.get('content', ''))
        full_text = f"{title} {content}"
        
        scores = {}
        
        # 키워드 기반 점수
        for content_type, keywords in self.KEYWORDS.items():
            score = self._count_keywords(full_text, keywords)
            if score > 0:
                scores[content_type] = score
        
        # 특수 조건 기반 점수
        has_sponsor = bool(post_data.get('sponsor_phone') or post_data.get('content_sponsor_id'))
        has_ad_disclosure = bool(re.search(r'#광고|#ad|광고\s*포함', full_text, re.IGNORECASE))
        if has_sponsor and not has_ad_disclosure:
            scores['Undisclosed_Ad'] = 50
        
        if post_data.get('video_urls'):
            scores['Video_Content'] = 20
        
        # 이미지 개수 계산
        image_urls = post_data.get('image_urls', '')
        if isinstance(image_urls, str) and image_urls:
            image_count = len(image_urls.split(','))
        else:
            image_count = 0
            
        if image_count >= 5:
            scores['Image_Carousel'] = 10
        
        sorted_types = sorted(
            scores.items(),
            key=lambda x: (self.PRIORITY.get(x[0], 0), x[1]),
            reverse=True
        )
        
        top_types = sorted_types[:3]
        
        if not top_types:
            return {
                'content_type': '',
                'content_type_primary': '',
                'content_type_count': 0
            }
        
        return {
            'content_type': ', '.join([t[0] for t in top_types]),
            'content_type_primary': top_types[0][0],
            'content_type_count': len(top_types)
        }
    
    def classify_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame 전체에 콘텐츠 타입 분류 적용"""
        results = []
        for idx, row in df.iterrows():
            classification = self.classify(row.to_dict())
            results.append(classification)
        
        result_df = pd.DataFrame(results)
        return pd.concat([df, result_df], axis=1)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='PM-International 콘텐츠 타입 분류기')
    parser.add_argument('--input', '-i', required=True, help='입력 CSV 파일 경로')
    parser.add_argument('--output', '-o', help='출력 CSV 파일 경로 (기본: input_classified.csv)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
        return
    
    output_path = args.output or input_path.stem + '_classified.csv'
    
    print(f"📖 파일 로드 중: {input_path}")
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    print(f"   {len(df)}개 게시물 로드됨")
    
    print("🔍 콘텐츠 타입 분류 중...")
    classifier = ContentTypeClassifier()
    result_df = classifier.classify_dataframe(df)
    
    print(f"💾 결과 저장 중: {output_path}")
    result_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # 통계 출력
    print("\n📊 분류 결과 통계:")
    if 'content_type_primary' in result_df.columns:
        type_counts = result_df['content_type_primary'].value_counts()
        for content_type, count in type_counts.head(10).items():
            print(f"   {content_type}: {count}개 ({count/len(result_df)*100:.1f}%)")
    
    print(f"\n✅ 완료! {len(result_df)}개 게시물 분류됨")


if __name__ == "__main__":
    main()
