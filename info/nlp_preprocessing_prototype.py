import pandas as pd
import re
from konlpy.tag import Okt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import numpy as np

def preprocess_text(text):
    """
    기본적인 텍스트 전처리 함수
    1. 특수문자 제거
    2. 형태소 분석 및 명사 추출 (KoNLPy Okt 사용)
    """
    if pd.isna(text):
        return ""
    
    # 1. 특수문자, URL 등 제거 (간단한 예시)
    text = re.sub(r'http\S+', '', str(text)) # URL 제거
    text = re.sub(r'[^\w\s가-힣]', '', text) # 한글, 영문, 숫자, 공백 외 제거
    
    # 2. 형태소 분석기 초기화 (Okt)
    # 실무에서는 Mecab을 추천하지만, 설치 편의성을 위해 Okt 사용
    okt = Okt()
    
    # 명사만 추출 (홍보글 특성상 명사가 핵심 키워드일 확률 높음)
    # 필요에 따라 adjectives=True 등으로 형용사도 포함 가능
    nouns = okt.nouns(text)
    
    # 불용어 처리 (예시)
    stopwords = ['것', '수', '나', '저', '이', '그', '저', '위해', '문의']
    nouns = [n for n in nouns if n not in stopwords and len(n) > 1]
    
    return ' '.join(nouns)

def run_topic_modeling(documents, n_topics=5):
    """
    LDA 토픽 모델링 실행 함수
    """
    print(f"총 {len(documents)}개의 문서로 토픽 모델링을 시작합니다.")
    
    # 1. 벡터화 (CountVectorizer)
    # LDA는 TF-IDF보다 단순히 단어 빈도(Count)를 사용하는 것이 일반적입니다.
    vectorizer = CountVectorizer(max_features=1000, min_df=2)
    X = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    
    # 2. LDA 모델링
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)
    
    # 3. 결과 출력
    print("\n[토픽 모델링 결과]")
    for topic_idx, topic in enumerate(lda.components_):
        top_features_ind = topic.argsort()[:-11:-1] # 상위 10개 단어 인덱스
        top_features = [feature_names[i] for i in top_features_ind]
        print(f"Topic #{topic_idx+1}: {', '.join(top_features)}")
        
    return lda, vectorizer

if __name__ == "__main__":
    # 예시 데이터 (실제 사용 시에는 pd.read_csv('posts.csv') 등으로 로드)
    sample_data = [
        "피엠인터내셔널의 액티바이즈는 정말 에너지가 넘쳐요. 비타민 B군이 풍부해서 피로회복에 좋습니다.",
        "독일 프리미엄 건강기능식품, 피엠 쥬스 마시고 건강 챙기세요. 아침에 한잔!",
        "다이어트 챌린지 모집합니다. 30일 동안 함께 살 빼실 분 구해요. 보상 플랜도 있습니다.",
        "사업 문의 환영합니다. 투잡으로도 좋고 전업으로도 추천드려요. 수익 구조 설명해드립니다.",
        "오늘도 액티바이즈 한잔으로 하루를 시작합니다. 활력이 생기네요. #피엠 #건강",
        "부업 찾으시는 분들 연락주세요. 초기 비용 없이 시작할 수 있는 기회입니다."
    ]
    
    print("1. 데이터 전처리 중...")
    processed_docs = [preprocess_text(doc) for doc in sample_data]
    print(f"전처리 예시: {processed_docs[0]}")
    
    print("\n2. 토픽 모델링 수행 중...")
    run_topic_modeling(processed_docs, n_topics=3)
    
    print("\n[가이드]")
    print("이 코드는 프로토타입입니다. 실제 데이터에 적용하려면:")
    print("1. pd.read_csv()로 크롤링 데이터를 로드하세요.")
    print("2. 'content' 컬럼에 preprocess_text 함수를 적용하세요.")
    print("3. 불용어(stopwords) 리스트를 도메인에 맞게 확장하세요.")
