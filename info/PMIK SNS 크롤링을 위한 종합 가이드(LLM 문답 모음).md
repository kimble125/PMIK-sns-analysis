# PMIK SNS 크롤링을 위한 종합 가이드(LLM 문답 모음)

1. 프롬프트 질문:

1. Role: 당신은 베테랑 데이터 전문가(엔지니어링, 분석, 사이언스 등 다방면에 능통)이자 PM으로서 데이터 프로젝트 전반을 설계하고 코딩하여 수행하는 데까지 전문성이 있으며, 이를 설명하는 데에도 능통합니다.

2. Goal: PM 판매원 SNS 분석 프로젝트 중간 점검, AI 이용 방식이나 DB 구축방식 등의 재설계 및 아키텍처 작성. 현재는 상세한 코드 개선이나 디버깅 등은 목적이 아니므로 최소화해주세요. 

3. 프로젝트 설명('맥락'에 첨부한 PM_SNS_Theoretical_Background_v2_5.md.docx, PM_SNS_Intern_Work_Plan_v2.2.md.docx와 직접 첨부한 피엠인터내셔널코리아(유) 채용 - Sr. AI 및 데이터 분석 전문가 _ 잡코리아.pdf 참고. 피엠인터내셔널코리아(유) 채용 - Sr. AI 및 데이터 분석 전문가 _ 잡코리아.pdf의 "이런 업무를 해요"의 내용은 우리가 하고 있는 일(3. 데이터 분석 까지)과 우리 이후에 해야 할 일을 적어놓았음):

1) 연구 질문:
핵심 질문:
- "PMI코리아 판매원 의 SNS 활동 패턴은 무엇이며, 이것이 판매 성과 및 조직 확장에 어떤 영향을 미치는가?"

세부 질문:

- 5개 주요 SNS 플랫폼(네이버 블로그, 유튜브, 인스타그램, 카카오스토리, 페이스북)에서 판매원의 활동 빈도, 콘텐츠 유형, 반응도(engagement) 등은 어떠한가? (반응도: 좋아요, 댓글, 공유 등 사용자 상호작용 지표)

- 고성과 판매원과 저성과 판매원의 SNS 활동에는 어떤 차이가 있는가?

- 특정 플랫폼 또는 콘텐츠 유형이 매출 증대나 신규 판매원 모집에 더 효과적인가?

- 브랜드 리스크를 초래할 수 있는 부적절한 콘텐츠(허위·과장 광고)의 확산 양태는?

2) 2.2 연구 범위
시간적 범위:

데이터 수집 기간: 2025년 9월 ~ 2025년 12월 (3개월)
분석 대상 기간: PMIK의 한국 진출일 ~ 2025년 12월. 이후 수집 자동화.

공간적 범위:

대한민국 내 활동하는 PMI코리아 판매원
주요 SNS 플랫폼 5개 이상

내용적 범위:

수집 데이터:(필수) 플랫폼, 게시물 URL, 제목, 본문 텍스트, 이미지(OCR 처리), 동영상(자막 추출), 해시태그, 발행일, (선택)게시물 ID, 블로그 ID, 블로거 이름, 후원인 전화번호, 후원인 추천번호, 좋아요 수, 댓글 수, 조회수, 수집 날짜 등
분석 방법: 기술통계, 클러스터링, 자연어처리, 회귀분석

3. 기대 효과
3.1 실무적 기대 효과
기업 차원 (예상):

팀파트너 이탈률 15% 감소 (타겟: 연 2,000명 → 1,700명)
신규 온보딩 효율 30% 향상 (교육 시간 8시간 → 5.6시간)
브랜드 리스크 조기 대응으로 법적 분쟁 최소화

팀파트너 차원 (예상):

데이터 기반 SNS 전략 → 평균 매출 20% 증대
플랫폼별 최적화 가이드 → 콘텐츠 제작 시간 25% 단축
고성과자 베스트 프랙티스 공유 → 학습 곡선 완화

3.2 학술적 기대 효과
한국 네트워크 마케팅 산업의 디지털 전환 사례 연구
40-60대 여성의 SNS 생산자(prosumer) 역할 분석
직접판매 산업의 플랫폼 경제 적응 모델 제시

1. 프로젝트 목표 (Objectives)
1.1 핵심 목표
"PM-International Korea 팀파트너의 SNS 활동을 자동으로 수집·분석하여, 데이터 기반 마케팅 전략 수립을 지원한다."
1.2 구체적 목표
1) 데이터 수집 자동화

5개 SNS 플랫폼에서 일일 500+ 게시물 자동 수집
이미지 OCR 및 동영상 스크립트 포함
에러율 5% 이하 유지

2) 데이터 분석

팀파트너를 4-6개 클러스터로 유형화
SNS 활동과 매출의 상관관계 규명 (R² > 0.6)
고성과자 베스트 프랙티스 10개 발굴

3) 인사이트 제공

Power BI 대시보드 구축
월간 리포트 자동 생성
리스크 게시물 조기 탐지 시스템
1.3 Out of Scope (범위 외)
실시간 스트리밍 분석 (배치 처리만)
감정 추적 (이탈 예측 모델 등 고급 ML)
다국어 지원 (한국어만)
모바일 앱 개발

2. 핵심 질문 (Key Questions)
이 프로젝트가 답해야 할 구체적 질문들:
2.1 활동 패턴
Q1: 팀파트너는 평균적으로 각 플랫폼에서 얼마나 자주 게시하는가?
Q2: 고성과자와 저성과자의 게시 패턴의 차이는?
Q3: 어떤 시간대에 가장 많이 게시하는가?
2.2 콘텐츠 유형
Q4: 어떤 콘텐츠 유형(텍스트/이미지/영상)이 가장 효과적인가?
Q5: 해시태그는 몇 개를 사용하는 것이 효과적인가?
Q6: 가장 효과적인 해시태그 조합은?
2.3 참여율 (Engagement)
Q7: 플랫폼별 평균 참여율(좋아요+댓글/조회수)은?
Q8: 어떤 요인이 높은 참여율과 연관되는가?
Q9: 본문 및 댓글의 감성(긍정/부정)과 참여율의 관계는?
2.4 성과 영향
Q10: SNS 활동 빈도 및 패턴과 월 매출의 상관관계는? (상관계수 r)
Q11: 어떤 플랫폼이 매출 기여도가 가장 높은가?
Q12: 다중 플랫폼 활용 시 매출 증대 효과는?
2.5 리스크
Q13: 허위·과장 광고로 의심되는 게시물 비율은?
Q14: 부정적 감성의 게시물 비율은? 그 부작용은 어느 정도인가?

3. Task:
1) 프로젝트 학습: PM_SNS_Theoretical_Background_v2_5.md.docx, PM_SNS_Intern_Work_Plan_v2.2.md.docx와 직접 첨부한 피엠인터내셔널코리아(유) 채용 - Sr. AI 및 데이터 분석 전문가 _ 잡코리아.pdf 리딩 및 학습
2) 현황 파악 및 중간 분석: 첨부한 Py나 파일들에는 우선 여러 플랫폼들(네이버 블로그, 네이버 카페, 유튜브, 카카오스토리-팀원 파일, 인스타그램-팀원 파일)의 크롤링 및 스크래이핑 코드들이 있습니다. 또한 그것들의 멀티미디어-이미지와 비디오-코랩 처리,  네이버 블로그에 대한 간단한 EDA, 대시보드(file:///Users/kimble/Documents/IT/PMIK-sns-analysis/analysis/2.%20blog_bi_dashboard.html), 클러스터링 및 워드 클라우드 등이 있습니다.  참고로 여기에서 py들은 대부분 각 플랫폼마다 다양한 문제점을 여전히 가지고 있고, 그에 따라 EDA 이후는 테스트로 적은 데이터로만 수행한 것입니다. 현황 정리는 9주차 회의 안건(11.18화).docx를 보면 됩니다.
우리의 프로젝트 기간은 이제 3주 만이 남았으며, 다음주 화요일(일주일+1일 남음) 까지 크롤링을 거의 마치고 주요 피처 제시, DB 구축 등을 어느 정도 마무리 하기로 했습니다. 이를 기준으로 중간점검을 해주세요.  
3) 작업 형태 파악
- 저와 팀원 둘이 작업 중이며 둘 다 이런 프로젝트에 초보인 편이고, 저는 비교적 PM, 팀원은 coder의 역할에 좀 더 가깝습니다. 
- 저의 경우 코딩을 잘 못하기 때문에 IDE로 Windsurf를 사용하여 그 안에서 대부분 Claude Sonnet 4.5(thinking)을 이용해서 코드 개선을 하고 있습니다. 또한 Claude를 결제하여 그곳에서 첫 코드 작성이나 큰 작업을 하고 있습니다. 현재 Claude Code나 제미나이 3.0 Pro, Antigravity 등을 이용해볼까 하고 생각하고 있습니다. 
- 회사에서 Azure vm을 발급받아서 회의안건에 적혀있듯이 8 core, 32GiB RAM, 128GB 저장공간
운영체제: 리눅스 두 개(Crawler vm, Analyst vm)를 이용 중이며, Analyst vm은 평일 회사 근무시간(오전 9시~ 오후 4시)에만 사용 가능하지만, Crawler vm은 지속적 크롤링을 위해 24시간 언제 어디서나 이용 가능합니다. 

4) 문제상황 및 질문:
- 지속 발생하는 버그: 크롤링 중에 계속해서 디버깅을 하면 이전에 나타났던 다른 버그들이 다시 나타나는 등 작업이 복잡해지다 보니 Claude를 통한 작업의 완성도가 떨어지고 있습니다. 효율적인 디버깅 및 코드 개선 방법을 알려주세요. 
- 멀티미디어 처리 난항: 특히 whisper을 이용한 음성 인식이 계속해서 안되고 있습니다. step2_colab_processing.ipynb의 코드가 조금 인식을 잘 했고, 팀원이 만든 Instagram 관련 코드에서도 비교적 잘 되는 편입니다. 추정 가능한 원인은 너무 많습니다. 첫 크롤링에서는 영상의 url만 수집하고 이후에 멀티미디어 처리를 하는데, url이 잘못된 경우(1회용으로 수집), url에서 음성이 음소거 되어 있는 경우 등등이요. 혹은 whisper의 성능 자체가 안좋게 평가되나요? whisper말고 음성 인식 및 문자 전환의 더 나은 대안은 없을까요?
- DB는 무엇을 써야 하는가? 
첨부한 회의 안건에 적혀있듯이 원래는 vm로컬 → Blob Storage → PostgreSQL 혹은 Supabase를 이용하려 했으나, 실제 데이터를 지금까지 수집해보니 pm파트너들의 게시물이 플랫폼을 총합해도 아직까진 GB단위도 되지 못한 등 그리 많지 않고 데이터 형태도 용량을 많이 잡아먹지 않아 굳이 Blob Storage가 필요한지 의문입니다. 물론 이후에 수집을 자동화 한다면 용량이 계속 늘어나긴 할겁니다. 
또한 상무님은 계속 Nosql을 쓰라고 하시는데 우리는 정확히 어떻게 DB 구조를 설계하면 좋을까요?
저희는 DB 구축 자체가 처음입니다. 'DB를 구축한다'는 것이 무엇이고, 어떤 사항들을 고려해야 하며, 우리 프로젝트에서 최선은 무엇인지 등등을 알려주세요. 우리 회사는 Azure을 이용중이지만, 비용을 아끼기 위해 오픈소스를 이용하는 것이 나을 수도 있다는 점도 인지해주세요.
- 데이터 분석 및 대시보드 작성, 클러스터링(주요 피처 추출), AI모델 개발 등을 어떻게 해야하는가?
제가 첨부한 Analysis_Report, dashboard, clustering과 wordcloud에 대해 비록 테스트본이지만 상무님은 만족하셨습니다. 이보다 더 개선된 작업을 하려면 어떻게 해야하나요? 첨부한 naver_blog_pm_v10_3_posts_20251121_010057.csv와 아래 카카오 스토리의 크롤링 결과 등을 보고 그 컬럼과 데이터 형태 등도 체크해주세요:

 kakaostory_popup_posts.json

"p_num": 4496,
    "name": "수다스러운 미캘리",
    "user_id": "micalli73",
    "shortcode": "BLC8Wh7RdI0",
    "date": "2025-01-12T06:33:00",
    "media_type": "multi_image",
    "media_url": [
      "https://story-img.kakaocdn.net/dn/5EjfU/hyX0wTzbtq/KY92GUDOMiXCQxqmJsCxdK/img_xl.jpg?width=1080&height=633&avg=%2523c5dba6&v=2",
      "https://story-img.kakaocdn.net/dn/bbDOqw/hyX0zvXd2B/ARDamEfJcfT1jNc4jHXfr0/img_xl.jpg?width=1080&height=1768&avg=%2523918b9a&v=2"
    ],
    "media_count": 2,
    "content": "WOW!!! 🔥🔥🔥 비만시장의 큰 태풍이 불어닥칠 예정!! 👏👏👏 ​ 2025년 2월 만나게될 신제품 는 완벽한 효능 뿐만 아니라 100% 만들어져 증명된 👍👍👍 ​ 국내 다이어트 시장 7조 6천억 &amp; 전세계 다이어트시장 100조를 잡을수 있는 기회 PM과 함께 하실 분 010.3942.5876 예약하세요 👋",
    "content_count": 177,
    "hashtag": [
      "#탑쉐이프",
      "#천연성분으로",
      "#안정성까지",
      "#식욕억제제"
    ],
    "hashtag_count": 4,
    "like_count": 4,
    "comment_count": 1

또한 클러스터링에 kmeans로 충분할까요? 더 개선된 방법은 없나요? 

또한 피엠인터내셔널코리아(유) 채용 - Sr. AI 및 데이터 분석 전문가 _ 잡코리아.pdf 에 나오는 다음과 같은 AI 개발을 위해서는 어떤 것을 계획하고 지금 무엇을 해놓는 것이 좋을까요? 혹은 어느 정도 우리도 할 수 있을까요? 특히 NLP자연어처리는 제가 계속 관심있어하던 점이지만 난이도가 어려울 것 같습니다. 어떻게 생각하시나요? 

4. AI Model Development:
ㆍDevelop machine learning and predictive analysis models to derive best practices of successful TPs.
ㆍUtilize natural language processing (NLP) technologies to analyze seminar information and communication content.

Reasoning: 시간과 쿼리를 아끼지 말고 최선의 결과가 나오고 적어도 제 질문에 모두 완전히 답할 때까지 작업을 계속해주세요. 잘 부탁드립니다. 

Outter format: 제 질문들에 답해주시고, 그 결과들을 담아서 다음주 화요일 보고 시에 제출할, 보완 계획과 작업의 아키텍처 등이 담긴 보고서를 만들어주세요. 상무님은 Information Architecture를 주문했는데 작성하는 게 좋은지 타진해서 하든지 말든지 해주시고, Data architecutre 등도 원랜 좋겠지만 우리 프로젝트는 data 흐름은 그렇게 복잡해보이지 않습니다. 이외에 기술 아키텍처 등도 좋겠네요. 
잘 부탁드립니다.

1. Claude Sonnet 4.5(연구, 심층 사고 모드)의 답변

**핵심 권장**: 현재 환경(Windsurf + Claude Pro)을 유지하면서 **Claude Code CLI**를 추가 설치하는 조합이 가장 효율적입니다. 3주 내 프로젝트 완료를 위해 새 도구 학습에 시간을 낭비하지 말고, 익숙한 환경에서 즉시 개발을 시작하세요. 월 **$35($15 Windsurf + $20 Claude Pro)**로 프로덕션급 AI 코딩 지원을 받을 수 있습니다.

---

## 사용자 질문 사항에 대한 중요 사실 확인

조사 과정에서 몇 가지 중요한 사실 오류를 발견했습니다. 이 정보는 Perplexity 답변 검증 요청과도 관련됩니다.

**"Claude Opus 4.5 (2024년 11월 출시)"는 정확하지 않습니다.** Claude Opus 4.5는 **2025년 11월 24일**에 출시되었습니다. 2024년 11월 시점의 최신 모델은 Claude 3.5 Sonnet이었습니다. 현재(2025년 11월 25일) 기준으로 Opus 4.5가 막 출시된 상태이며, SWE-bench 80.9%로 업계 최고 코딩 성능을 보여줍니다.

**Google Antigravity는 실제로 존재합니다.** 이름이 Python 이스터에그 모듈과 같아 혼란을 줄 수 있지만, Google이 **2025년 11월** Gemini 3 발표와 함께 공개한 에이전트 중심 개발 플랫폼입니다. Windsurf 팀의 기술을 24억 달러에 인수하여 개발했으며, 현재 Public Preview로 개인 사용자에게 무료 제공됩니다.

---

## Google Antigravity 실체와 활용 가능성

Google Antigravity는 **에이전트 중심 아키텍처**를 특징으로 하는 최신 AI 코딩 플랫폼입니다. AI 에이전트가 에디터, 터미널, 브라우저에 직접 접근하여 자율적으로 코드를 작성하고 테스트합니다.

| 기능 | 설명 |
|------|------|
| **Artifacts 시스템** | 작업 목록, 구현 계획, 스크린샷, 브라우저 녹화 자동 생성 |
| **자율 검증** | 에이전트가 브라우저로 코드를 직접 테스트 |
| **Manager 뷰** | 여러 에이전트를 동시에 관리하는 대시보드 |
| **지원 모델** | Gemini 3 Pro(기본), Claude Sonnet 4.5, GPT-OSS |

**PMI 프로젝트 적용 판단**: Public Preview 단계이므로 **프로덕션 사용에는 주의**가 필요합니다. 3주 내 완료해야 하는 프로젝트에는 안정성이 검증된 Windsurf나 Cursor를 권장합니다. 다만 향후 프로젝트나 학습 목적으로는 antigravity.google/download에서 무료로 체험해볼 가치가 있습니다.

---

## Claude Code 상세 분석과 설치 가이드

Claude Code는 Anthropic의 **터미널 기반 에이전틱 코딩 도구**로, 2025년 5월에 정식 출시되었습니다. 전체 코드베이스를 이해하고 자연어 명령으로 복잡한 작업을 수행합니다.

### Azure VM Ubuntu 24 설치 방법

**방법 1: 공식 설치 스크립트 (권장)**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**방법 2: NPM 설치**
```bash
# Node.js 20.x 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# npm 글로벌 경로 설정 (sudo 없이 설치)
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Claude Code 설치
npm install -g @anthropic-ai/claude-code
claude doctor  # 설치 확인
```

### 핵심 기능과 사용법

SSH로 Azure VM에 접속한 후 프로젝트 디렉토리에서 `claude` 명령으로 시작합니다. 자연어로 지시하면 파일을 직접 편집하고 터미널 명령을 실행합니다.

```bash
cd /path/to/pmi-korea-crawler
claude

> "Selenium 크롤러에 재시도 로직과 지수 백오프 추가해줘"
> "MongoDB 연결 코드를 비동기로 리팩토링해줘"
> "이 프로젝트 구조 분석하고 개선점 알려줘"
```

**비용 정책**: Claude Pro 구독($20/월)으로 Sonnet 4.5와 함께 Claude Code 사용 가능합니다. 복잡한 아키텍처 작업에는 Max 플랜($100/월)에서 Opus 4.1을 활용할 수 있습니다.

### Windsurf IDE 통합

Claude Code는 VS Code 기반 IDE와 완전히 통합됩니다. 터미널에서 `/ide` 명령을 실행하면 Windsurf를 자동 감지하여 연결합니다. 코드 변경 사항이 IDE에 실시간으로 반영되며, Diff 뷰어로 검토할 수 있습니다.

---

## Claude 모델 라인업 현황 (2025년 11월)

현재 사용 가능한 Claude 모델과 코딩 성능을 정확히 파악해야 올바른 선택을 할 수 있습니다.

| 모델 | SWE-bench | 가격(입력/출력 MTok) | 권장 용도 |
|------|-----------|---------------------|----------|
| **Opus 4.5** | 80.9% | $5 / $25 | 복잡한 아키텍처, 대규모 리팩토링 |
| **Sonnet 4.5** | 77.2% | $3 / $15 | 일상 코딩, 빠른 반복 개발 |
| Haiku 4.5 | - | 저렴 | 간단한 완성, 서브에이전트 |
| Opus 4.1 | 74.5% | $15 / $75 | 이전 버전, 안정성 우선 |

**프로젝트 권장 구성**: Claude Pro 구독으로 **Sonnet 4.5**를 기본 사용하고, 전체 아키텍처 설계나 복잡한 디버깅 시에만 Opus 모델을 활용하세요. 일반 크롤링 코드 작성에는 Sonnet 4.5로 충분합니다.

---

## AI 코딩 도구 상세 비교

### Cursor vs Windsurf 핵심 차이

두 도구 모두 VS Code 기반이며 Claude/GPT 모델을 지원합니다. 선택 기준은 가격과 UI 선호도입니다.

| 항목 | Cursor | Windsurf |
|------|--------|----------|
| **월 비용** | $20 | $15 |
| **강점** | 세밀한 코드 제어, Agent 모드 | 직관적 UI, 자동 린트 수정 |
| **약점** | 복잡한 UI | 크레딧 소진 속도 |
| **초보자 적합성** | 보통 | 우수 |

**Windsurf 유지 권장**: 이미 사용 중인 환경이므로 학습 비용이 없고, $5/월 저렴합니다. Cascade AI의 자동 컨텍스트 인식 기능이 Python 크롤링 프로젝트에 적합합니다.

### GitHub Copilot과 다른 도구들

**GitHub Copilot** ($10/월): 가장 저렴한 유료 옵션이지만, Agent 기능이 Cursor/Windsurf보다 약합니다. GitHub 워크플로우가 중요하다면 고려할 수 있습니다.

**Codeium Free**: 무제한 코드 자동완성을 무료로 제공합니다. 예산이 제한적이라면 보조 도구로 활용할 수 있습니다.

**Gemini Code Assist**: Google Cloud와 통합이 필요한 경우에 적합합니다. Azure 환경에서는 특별한 장점이 없습니다.

---

## SNS 크롤링 프로젝트 기술 스택 권장사항

### Selenium 크롤러 안티봇 우회

2024-2025년 기준으로 **SeleniumBase UC Mode**가 가장 효과적인 안티탐지 솔루션입니다.

```python
from seleniumbase import SB

with SB(uc=True) as sb:
    sb.driver.uc_open_with_reconnect("https://target-site.com", 5)
    sb.driver.uc_click(selector)  # 탐지 방지 클릭
```

대안으로 undetected-chromedriver를 사용할 수 있습니다. 필수 옵션으로 `--disable-blink-features=AutomationControlled`를 항상 포함하세요.

### OCR 처리 권장 도구

**PaddleOCR이 한국어에서 최고 성능**을 보입니다. EasyOCR보다 정확도가 높고, Tesseract보다 현대적인 아키텍처를 사용합니다.

```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='korean')
result = ocr.ocr('image.png', cls=True)
```

설치: `pip install paddleocr paddlepaddle-gpu` (GPU 가속 권장)

### Whisper 오디오 처리

**faster-whisper**가 속도와 정확도의 최적 균형점입니다. OpenAI 원본 대비 4배 빠르며 메모리 사용량도 적습니다.

```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3", device="cuda", compute_type="float16")
segments, info = model.transcribe("audio.mp3", language="ko", beam_size=5)
```

32GB RAM 환경에서 large-v3 모델 사용이 가능합니다. 한국어 fine-tuned 모델(`seastar105/whisper-medium-ko-zeroth`)을 사용하면 추가 성능 향상이 가능합니다.

### 데이터베이스 설계 패턴

| 데이터 유형 | 저장소 | 이유 |
|-------------|--------|------|
| 원시 크롤링 데이터 | MongoDB | 스키마 유연성, 비정형 데이터 |
| 메타데이터/분석 결과 | PostgreSQL | 관계형 쿼리, ACID |

**MongoDB**: Motor(비동기) 사용 권장 - 크롤러 성능 최적화
**PostgreSQL**: SQLAlchemy 2.0 사용 - 비동기 지원, 타입 안전성

---

## Azure VM 환경 설정 체크리스트

Ubuntu 24.04 환경에서 즉시 개발을 시작하기 위한 설정입니다.

```bash
# 1. Python 3.11 환경
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
python3.11 -m venv ~/crawler_env
source ~/crawler_env/bin/activate

# 2. Chrome 헤드리스 설치
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb

# 3. 핵심 패키지 설치
pip install seleniumbase selenium webdriver-manager
pip install paddleocr paddlepaddle-gpu
pip install faster-whisper
pip install sqlalchemy asyncpg motor mongoengine

# 4. Claude Code 설치
curl -fsSL https://claude.ai/install.sh | bash
```

**헤드리스 Chrome 최적화 옵션**:
```python
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--memory-pressure-off')
```

---

## 3주 프로젝트 완료를 위한 실행 계획

### 1주차: 기반 구축

| 일차 | 작업 | AI 도구 활용 |
|------|------|-------------|
| 1-2일 | Azure VM 환경 설정, Chrome/DB 설치 | Windsurf로 설정 스크립트 생성 |
| 3-4일 | 크롤러 기본 구조 설계 | Claude Code로 프로젝트 구조 생성 |
| 5일 | SeleniumBase 안티봇 테스트 | Cascade로 코드 디버깅 |

### 2주차: 핵심 기능 개발

| 일차 | 작업 | AI 도구 활용 |
|------|------|-------------|
| 1-2일 | SNS별 크롤러 구현 | Windsurf Cascade로 멀티파일 편집 |
| 3일 | OCR/Whisper 통합 | Claude에 파이프라인 설계 요청 |
| 4-5일 | MongoDB/PostgreSQL 연동 | Claude Code로 스키마 생성 |

### 3주차: 품질 개선 및 배포

| 일차 | 작업 | AI 도구 활용 |
|------|------|-------------|
| 1-2일 | 에러 핸들링, 로깅 추가 | "재시도 로직 추가해줘" 프롬프트 |
| 3일 | 코드 리팩토링, 모듈화 | Claude Code로 전체 코드베이스 리뷰 |
| 4-5일 | 테스트 및 문서화 | AI로 pytest 테스트 자동 생성 |

---

## 비용 효율적인 최종 권장 구성

**월간 예상 비용: $35**

- **Windsurf Pro**: $15/월 - 일상 코딩, Cascade AI
- **Claude Pro**: $20/월 - Claude Code CLI, 복잡한 질문

이 조합으로 Sonnet 4.5 모델을 Windsurf IDE와 터미널(Claude Code) 양쪽에서 활용할 수 있습니다. 초보 개발자에게도 Windsurf의 직관적인 UI가 적합하며, 터미널 작업이 필요할 때 Claude Code로 전환하면 됩니다.

**추가 무료 옵션**: Google Antigravity(Public Preview 무료), Codeium Free(무제한 자동완성)를 보조 도구로 활용할 수 있습니다.

## 결론

PMI Korea SNS 크롤링 프로젝트에 **새 도구 학습 없이 즉시 시작**하려면 현재 Windsurf + Claude Pro 환경을 유지하세요. 여기에 Azure VM에 Claude Code CLI만 추가 설치하면 터미널에서도 강력한 AI 코딩 지원을 받을 수 있습니다. Google Antigravity는 아직 Preview 단계이므로 안정성이 필요한 실무 프로젝트보다는 향후 학습용으로 고려하시기 바랍니다. 기술 스택으로는 SeleniumBase(안티봇), PaddleOCR(한국어), faster-whisper(음성), Motor+SQLAlchemy(DB)를 권장합니다.

프로젝트 중간점검 및 아키텍처 보고서 완성! 🎉
다음 주 화요일 보고용 종합 문서를 작성했습니다. 주요 내용을 요약해드리겠습니다.
📊 현황 요약
완료된 작업

5개 플랫폼 크롤러 개발 (네이버 블로그 v10.3, 유튜브 v3.1 등)
약 5,000~6,000개 게시물 수집
기초 EDA, 대시보드, 클러스터링 완료

주요 과제

크롤러 안정성 개선 필요
Whisper 음성인식 성공률 저조
DB 설계 미확정
3주 내 완성 압박

🔑 핵심 해결 방안
1. 버그 디버깅 효율화

모듈화: 1,713줄 단일 파일 → 기능별 분리
표준 에러 핸들링: 커스텀 Exception 클래스 도입
구조화 로깅: JSON 로그로 디버깅 용이성 향상
단위 테스트: pytest로 회귀 방지

2. 음성인식 개선
권장: 하이브리드 접근
- Phase 1: AssemblyAI (핵심 콘텐츠, 정확도 95%)
- Phase 2: Whisper Local (대량 처리, 무료)
- 비용: 약 $65 (100시간 분량)
3. DB 설계
하이브리드 아키텍처 권장:
MongoDB (NoSQL) → 원시 데이터, 유연한 스키마
    ↓ ETL Pipeline
PostgreSQL (SQL) → 분석 데이터, 쿼리 최적화
    ↓
Power BI → 대시보드

비용: $0/월 (무료 티어로 시작)
4. 분석 고도화

클러스터링: K-Means → DBSCAN (자동 클러스터 수 결정)
NLP 즉시 적용: 감성 분석, 키워드 추출 (transformers 라이브러리)
회귀 분석: SNS 활동 → 매출 영향 정량화

5. AI 모델 로드맵
현실적 타임라인:
Week 1: 감성 분석 + 키워드 추출 (기초 NLP)
Week 2: 이탈 예측 + 고성과자 패턴 (의사결정 트리)
Week 3: 대시보드 통합 + 보고서 작성
프로젝트 후: 고급 NLP (요약, Q&A)
📐 시스템 아키텍처
보고서에 3가지 아키텍처를 포함했습니다:

Data Architecture: 데이터 수집 → 처리 → 저장 → 분석 → 시각화 전체 흐름
Technical Architecture: 기술 스택, 인프라, 모니터링
Information Architecture: 사용자별 정보 접근 계층

📅 3주 실행 계획
Week 1 (11/25~12/1): 크롤러 안정화 & 대량 수집

MongoDB Atlas 설정
2,000+ 게시물 수집
OCR & 음성인식 처리

Week 2 (12/2~12/8): 분석 & 피처 개발

ETL 파이프라인 구축
NLP 처리 (감성, 키워드, NER)
Power BI 대시보드 v1.0

Week 3 (12/9~12/15): 고도화 & 최종 보고

회귀 분석 (매출 예측)
대시보드 고도화
최종 리포트 & 발표 자료

🎯 즉시 실행 항목 (이번 주)

MongoDB Atlas 설정 (무료 티어)
네이버 블로그 v10.3.1 재실행 (대량 크롤링)
AssemblyAI API 키 발급 ($10 크레딧)
공통 모듈 작성 (error_handler.py, logger.py)
pytest 설치 및 테스트 작성


보고서 다운로드
이 보고서는 74KB 분량으로, 다음 주 화요일 보고에 바로 활용하실 수 있습니다. 코드 예시, 아키텍처 다이어그램, 구체적인 실행 계획을 모두 포함하고 있습니다.
추가로 궁금하신 부분이나 보완이 필요한 내용이 있으시면 말씀해주세요!Pm sns project midreport architecture v1 0문서 · MD Windsurf에서 열기재시도1. 현황 진단 (Current Status Assessment)
1.1 데이터 수집 현황
플랫폼	수집량	완성도	주요 이슈
네이버 블로그	7,890건 (261건 정제)	🟡 70%	해시태그 필터링 불가, 노이즈 많음, OCR 미작동
카카오스토리	4,769건	🟢 85%	구조화 양호, 멀티미디어 처리 필요
유튜브	376건	🔴 50%	Whisper 음성인식 실패율 높음, 썸네일 OCR 진행 중
인스타그램	~300건	🔴 40%	슬라이드 앨범 수집 불가, 임시 URL 문제
네이버 카페	테스트 중	🔴 20%	로그인 필요, pastedMGoal: 남은 기간 동안 할 수 있는 구체적 작업 효율화 및 개선 방안 - 우선 크롤링 코딩 및 수행 대상Task1: 툴 사용 관련 구체적인 진단 및 질문
당신이 언급한 코드 작업 및 개선 방안을 실행하는데 있어 Google의 Antigravity와 Claude의 오늘 출시된 Opus 4.5 및 Claude Code 혹은 당신이 추천하는 툴을 이용하려고 합니다.  
Antigravity와 Claude Code를 우선은 동시에 이용해보려고 하는데 우선 다음의 Context의 코드 및 작업을 개선해야 할 점과 당신의 앞선 중간 점검 문서등을 읽고 외부 검색(영어, 한글 등 언어 제한 없이)도 하여 앞선 제 계획이 적절한지, 더 나은 방법은 없는지 알려주세요. Task2: Task1의 당신의 답변을 바탕으로 구체적으로 Antigravity와 Claude Code등을 어떻게 설치, 구축, 실행하면 될지 처음부터 순서대로 구체적으로 알려주세요. 
참고로, 말씀드렸다시피 현재 저는 퍼플렉시티 프로, 클로드 프로, IDE로는 Windsurf에서 크레딧이 결제가 되어 있고 이곳에서 CLI를 이용하고 있으며 Azure VM도 이용 중입니다. Azure VM이 특히 필요한 이유는 제가 사무실과 집, 독서실 등을 옮겨 다니기 때문에 긴 작업이나 크롤링이 끊기지 않게 하기 위해서입니다. 
Context:
다음은 당신에게 했던 것과 비슷한 질문을 했을 때 퍼플렉시티의 답변입니다. 전반적으로 당신의 답변과 비슷한 맥락이나, 차이나 참고할 점이 있다면 해주세요: (Pasted)더 보기크롤링 개선을 위해 도구 평가 및 설치 가이드 준비했습니다.사용자가 두 가지 주요 작업을 요청했습니다:
Task1: Antigravity와 Claude Code를 포함한 도구들에 대한 외부 검색을 통한 평가
Task2: 구체적인 설치 및 실행 가이드
그런데 사용자의 질문이 꽤 구체적이고 명확합니다:

현재 상황: Windsurf IDE, Claude Pro, Perplexity Pro 구독, Azure VM 사용
목표: 크롤링 코드 개선 및 효율화
고려 중인 도구: Antigravity, Claude Code, Opus 4.5
Perplexity의 답변도 제공됨

이 질문은 명확하므로 clarifying questions를 물을 필요가 없습니다. 바로 launch_extended_search_task를 사용해야 합니다.
연구해야 할 주요 내용:

Google Antigravity의 최신 정보 및 기능
Claude Code의 최신 정보 및 기능
Claude Opus 4.5의 새로운 기능
이들이 Python 크롤링 프로젝트에 어떻게 활용될 수 있는지
Windsurf IDE와의 통합 가능성
Azure VM 환경에서의 실행 방법
실제 사용자 후기 및 비교

명확한 질문이므로 바로 연구를 시작하겠습니다.네, 훌륭한 질문입니다! Google Antigravity, Claude Code, 그리고 새로 출시된 Claude Opus 4.5에 대한 최신 정보를 조사하여 여러분의 PM SNS 크롤링 프로젝트에 가장 적합한 도구 조합을 찾아드리겠습니다.
특히 다음 사항들을 중점적으로 조사하겠습니다:

각 도구의 실제 기능과 한계
Python 크롤링 프로젝트에서의 실용성
Azure VM 환경에서의 활용 방법
Windsurf와의 통합 가능성
비용 대비 효과

지금 바로 심층 조사를 시작하겠습니다!AI 코딩 도구 조사리서치 완료•출처 286 개•6m 29sPMI Korea SNS 크롤링 프로젝트를 위한 AI 코딩 도구 종합 가이드가 준비되었습니다. 보고서에는 Claude 모델 라인업 현황(Opus 4.5 포함), Google Antigravity 실체 확인, Cursor vs Windsurf 비교, Claude Code 설치 가이드, 그리고 SeleniumBase/PaddleOCR/faster-whisper를 활용한 기술 스택 권장사항이 포함되어 있습니다. 핵심 결론: 현재 Windsurf + Claude Pro 환경을 유지하면서 Claude Code CLI만 추가하는 월 $35 조합을 권장드립니다.PMI Korea SNS Crawling Project: AI Coding Tools and Implementation Guide문서 # PMI Korea SNS 크롤링 프로젝트를 위한 AI 코딩 도구 종합 가이드

**핵심 권장**: 현재 환경(Windsurf + Claude Pro)을 유지하면서 **Claude Code CLI**를 추가 설치하는 조합이 가장 효율적입니다. 3주 내 프로젝트 완료를 위해 새 도구 학습에 시간을 낭비하지 말고, 익숙한 환경에서 즉시 개발을 시작하세요. 월 **$35($15 Windsurf + $20 Claude Pro)**로 프로덕션급 AI 재시도M당신의 앞선 보고서들을 잘 읽었습니다. 
다 같이 Claude Opus 4.5와 AzureVM(혹은 그냥 비슷한 스펙의 로컬 맥북 및 google colab)을 활용한다고 치고, 당신의 "PMI Korea SNS 크롤링 프로젝트를 위한 AI 코딩 도구 종합 가이드"에서 추천하신대로 Claude Code를 Windsurf에서 이용하는 것과 제가 기존에 하던 것처럼 Windsurf의 workspace에서 Opus를 이용해 채팅으로 코드를 수정하는 것이 어떻게 다른가요? 각각의 특징과 장단점은 뭔가요? 둘을 같이 하는 게 좋나요 하나만 하면 되거나 하나만 해야하나요?Claude Code CLI와 Windsurf 채팅의 차이점을 구분하고 실용적 선택을 제시했습니다.13초사용자가 Claude Code CLI와 Windsurf IDE 내 Claude 채팅의 차이점을 명확히 이해하고 싶어합니다. 이는 매우 중요한 질문입니다.
핵심 차이점:

Claude Code CLI: 터미널 기반, 독립 실행형 에이전트, 전체 코드베이스 컨텍스트
Windsurf IDE의 Claude 채팅: IDE 통합, 에디터 기반 워크플로우, Cascade AI와 통합

사용자의 현재 워크플로우:

Windsurf workspace에서 Opus 4.5 (또는 Sonnet 4.5)를 채팅으로 사용
Azure VM 또는 로컬 맥북, Google Colab 활용

혼란의 원인:

제 이전 답변에서 "Claude Code를 Windsurf에서 이용"이라고 표현했는데, 이게 정확하지 않을 수 있음
Claude Code는 별도의 터미널 도구이고, Windsurf IDE와는 별개
Windsurf는 자체적으로 Claude 모델을 통합하고 있음

명확히 해야 할 점:

Claude Code = 터미널 CLI 도구 (별도 설치)
Windsurf의 Claude = IDE 내장 채팅 (이미 사용 중)
이 둘은 다른 도구이며, 각각 장단점이 있음
사용자의 프로젝트 특성과 워크플로우에 따라 선택 필요

실용적인 접근 방식을 제안하면, 프로젝트의 복잡성과 개발 단계에 따라 도구를 유연하게 활용해야 합니다. 대규모 코드베이스 분석에는 Claude Code CLI가, 실시간 코딩과 협업에는 Windsurf IDE 내 채팅이 더 적합할 수 있습니다.훌륭한 질문입니다! 제 이전 답변이 혼란을 줄 수 있었네요. 명확히 정리해드리겠습니다.
핵심 차이점: 두 개의 완전히 다른 도구입니다
1️⃣ Windsurf IDE의 Claude 채팅 (현재 사용 중)
위치: IDE 오른쪽 사이드바의 채팅 패널
작동 방식:

당신이 채팅으로 요청 → Windsurf의 Cascade AI가 코드 분석 → Claude 모델에 전달 → 코드 제안 받음 → 당신이 직접 승인/적용
에디터에서 코드를 보면서 대화식으로 수정

예시 워크플로우:
You: "이 함수에 재시도 로직 추가해줘"
Windsurf: [에디터에서 해당 코드에 diff 표시]
You: [변경사항 검토 후 Accept 버튼 클릭]
2️⃣ Claude Code CLI (별도 터미널 도구)
위치: 터미널에서 claude 명령으로 실행
작동 방식:

터미널에서 대화 시작 → Claude가 전체 프로젝트 분석 → 자동으로 파일 편집, 터미널 명령 실행 → 결과 확인 요청
당신은 관찰자, Claude가 직접 작업

예시 워크플로우:
bash$ cd /project
$ claude

You: "Selenium 크롤러 전체를 모듈화하고 에러 핸들링 추가해줘"
Claude: [자동으로 5개 파일 생성/수정, requirements.txt 업데이트, 테스트 실행]
Claude: "완료했습니다. 변경사항을 검토해주세요."

상세 비교표
항목Windsurf IDE 채팅Claude Code CLI실행 환경IDE 내부 (GUI)터미널 (CLI)작업 방식대화 → 제안 → 승인대화 → 자동 실행컨텍스트 인식현재 열린 파일 + Cascade가 관련 파일 자동 탐지전체 프로젝트 구조 자동 분석코드 적용❌ 자동 적용 안됨 (당신이 Accept 클릭)✅ 자동 적용 (승인 후)터미널 명령❌ 실행 안됨 (수동 복붙)✅ 자동 실행 (pip install 등)멀티파일 편집🟡 Cascade로 가능하지만 한계 있음✅ 수십 개 파일 동시 편집대규모 리팩토링🟡 어려움 (파일별로 반복 작업)✅ 전체 구조 변경 가능디버깅✅ 에디터에서 직접 보며 수정🟡 터미널 출력으로만 확인학습 곡선✅ 쉬움 (이미 사용 중)🟡 보통 (CLI 익숙함 필요)비용Windsurf Pro $15/월Claude Pro $20/월 (Sonnet 4.5)모델Sonnet 4.5 / Opus 4.5Sonnet 4.5 / Opus 4.5

각각의 장단점
✅ Windsurf IDE 채팅의 장점

시각적: 코드를 보면서 변경사항을 정확히 확인
안전함: 자동 적용이 아니므로 실수 방지
익숙함: 이미 사용 중이므로 학습 비용 0
빠른 수정: 작은 버그나 함수 하나 고칠 때 즉시 적용
Diff 뷰: 변경 전후를 나란히 비교

❌ Windsurf IDE 채팅의 단점

반복 작업: 10개 파일을 수정하려면 10번 Accept 클릭
대규모 작업 어려움: 전체 구조 변경은 시간 소모
터미널 명령 불가: "requirements.txt 업데이트하고 설치해줘" → 직접 터미널에서 실행해야 함
컨텍스트 제한: Cascade가 관련 파일을 찾지만, 전체 프로젝트를 한눈에 보긴 어려움

✅ Claude Code CLI의 장점

자율성: "전체 크롤러 모듈화해줘" 한 마디면 끝
멀티파일: 5개, 10개, 20개 파일을 한 번에 수정
전체 컨텍스트: 프로젝트 구조 전체를 이해하고 작업
자동 실행: 파일 생성, 폴더 구조 변경, 패키지 설치까지 자동
복잡한 작업: 아키텍처 레벨 변경에 강함

❌ Claude Code CLI의 단점

블랙박스: 무슨 파일을 어떻게 수정했는지 터미널에서만 보임
실수 위험: 자동 적용이므로 잘못된 변경도 바로 반영
Git 필수: 롤백을 위해 반드시 Git 커밋 필요
시각적 확인 어려움: IDE로 돌아가서 직접 확인해야 함
학습 곡선: CLI 워크플로우에 익숙해야 함


언제 무엇을 사용해야 하는가?
🎯 Windsurf IDE 채팅 사용 케이스
✅ 이런 작업에 최적:
python# 1. 함수 하나 수정
"이 함수에 타입 힌트 추가해줘"
"이 에러 핸들링 try-except로 감싸줘"

# 2. 작은 버그 수정
"여기 None 체크 추가해줘"
"이 변수명 오타 수정해줘"

# 3. 코드 리뷰하면서 수정
"이 부분 성능 개선할 방법 알려줘"
"이 로직 더 pythonic하게 작성해줘"

# 4. 새 함수 추가
"OCR 전처리 함수 만들어줘"
"이미지 다운로드 함수 추가해줘"
실제 시나리오:

네이버 블로그 크롤러 함수 하나를 수정할 때
특정 버그를 찾아서 고칠 때
코드를 읽으면서 즉석에서 개선할 때

🚀 Claude Code CLI 사용 케이스
✅ 이런 작업에 최적:
bash# 1. 프로젝트 구조 변경
"전체 크롤러를 crawlers/ 폴더로 모듈화하고
각 플랫폼별로 별도 파일로 분리해줘"

# 2. 새 기능 추가 (여러 파일 연관)
"MongoDB 연동 추가해줘. 
config.py, database.py, models.py 생성하고
기존 크롤러에 통합해줘"

# 3. 대규모 리팩토링
"모든 크롤러에 표준 에러 핸들링 추가하고
공통 베이스 클래스 만들어줘"

# 4. 자동화 스크립트
"Docker 컨테이너 설정, GitHub Actions CI/CD,
테스트 스크립트 전부 만들어줘"
```

**실제 시나리오**:
- 1,700줄 크롤러 파일을 10개 모듈로 분리
- 5개 플랫폼 크롤러 전체에 재시도 로직 추가
- 프로젝트 전체를 비동기로 리팩토링

---

## 둘을 같이 사용하는 것이 좋은가?

### 🎯 권장: **병렬 사용 (각자 역할 분담)**

**이상적인 워크플로우**:
```
1. [Claude Code] 큰 구조 잡기
   $ claude
   > "프로젝트를 crawlers/, processors/, database/ 
      3개 폴더로 모듈화하고 베이스 클래스 만들어줘"
   
2. [Git 커밋] 
   $ git add -A
   $ git commit -m "feat: 프로젝트 모듈화"

3. [Windsurf] 세부 구현
   - Cascade: "네이버 블로그 크롤러 구현해줘"
   - 코드 확인하며 Accept
   - 버그 찾으면 즉시 수정 요청

4. [Claude Code] 테스트 & 문서화
   $ claude
   > "pytest 테스트 작성하고 README.md 업데이트해줘"

5. [Git 커밋]
   $ git add -A
   $ git commit -m "feat: 네이버 블로그 크롤러 완성"
⚠️ 주의사항: Git 필수
Claude Code 사용 시 반드시:
bash# 작업 전
git add -A
git commit -m "작업 전 스냅샷"

# Claude Code 실행
claude
> "대규모 리팩토링..."

# 결과 확인 후 문제 있으면
git reset --hard HEAD  # 롤백

PMI 프로젝트에서의 실용적 선택
📊 현재 상황 고려
당신의 환경:

✅ Windsurf IDE 이미 사용 중
✅ Azure VM 24/7 운영
✅ Python 초보, 코딩 작업에 AI 도움 필수
⏱️ 3주 내 프로젝트 완료 필요

🎯 1단계: Windsurf만 사용 (현재~1주차)
이유:

이미 익숙한 도구
학습 시간 낭비 방지
안전한 워크플로우

작업:

네이버 블로그 크롤러 디버깅
OCR/Whisper 통합
MongoDB 연결

🚀 2단계: Claude Code 도입 (2주차)
조건:

Windsurf 워크플로우에 완전히 익숙해진 후
대규모 구조 변경이 필요할 때
Git 사용법 숙지 후

작업:

전체 프로젝트 모듈화
5개 플랫폼 크롤러 구조 통일
테스트 코드 자동 생성

💡 실용적 권장 (결론)
1주차: Windsurf만 사용

새 도구 학습 시간 절약
안정적인 개발 속도 유지

2주차 이후: 필요하면 Claude Code 추가

대규모 리팩토링이 필요하면 도입
그게 아니면 Windsurf만으로도 충분

핵심:

둘 다 필수는 아님
Windsurf만으로도 프로젝트 완성 가능
Claude Code는 "시간 절약용 옵션"


비용 고려
시나리오월 비용설명Windsurf만$15현재 상태 유지, 충분히 가능Windsurf + Claude Pro$35Claude Code CLI 추가 (Opus 4.5 사용 가능)Windsurf + Claude Max$115복잡한 작업에 Opus 4.5 무제한 (과한 투자)
권장:

1주차: Windsurf Pro만 ($15)
2주차: 필요시 Claude Pro 추가 ($20) → Claude Code CLI 활용
3주차: 프로젝트 거의 완성, 클린업 작업


최종 답변
❓ 어떻게 다른가?

Windsurf 채팅: 에디터에서 보면서 수동 승인
Claude Code: 터미널에서 대화하며 자동 실행

❓ 장단점은?

Windsurf: 안전하고 시각적, 작은 작업에 빠름
Claude Code: 자율적이고 강력, 대규모 작업에 빠름

❓ 같이 해야 하나?

같이 하면 최고, 각자 역할 분담
하나만으로도 충분, Windsurf만으로 프로젝트 완성 가능
우선순위: 1순위 Windsurf, 2순위 Claude Code (선택)

🎯 PMI 프로젝트 추천
1주차에는 Windsurf만 사용하세요. 익숙한 도구로 빠르게 진행하는 게 중요합니다. 2주차에 전체 구조를 대규모로 바꿔야 한다면 그때 Claude Code를 도입하세요. 하지만 Windsurf의 Cascade AI만으로도 충분히 좋은 코드를 만들 수 있습니다.재시도M아래 첨부한 당신의 앞선 답변에서 다음의 내용을 답변해주세요:
1. Diff 뷰어가 뭔가요?
2. 아시다시피 저는 Azure vm 관련해서 Azure 관리자와 협업하며 작업하고 있습니다. 저는 Azure portal에 로그인할 계정도 받지 못하고 vm만 받아서 작업하고 있습니다. 아래의 작업을 하는데 있어 관리자와 상의해야할 필요가 있을까요? 이 작업에서 제 claude 계정에 대한 과금 외에 azure에 대한 과금이 있을가요? 이렇게 관리에 대한 신경을 쓰느니 그냥 로컬 환경의 windsurf와 ide에서 작업하고 긴 작업이 필요할 때만 코드를 vm에 올려 작업하는 건 어떨까요? 많이 불편할까요?''''Claude Code 상세 분석과 설치 가이드
Claude Code는 Anthropic의 터미널 기반 에이전틱 코딩 도구로, Anthropic 2025년 5월에 정식 출시되었습니다. 전체 코드베이스를 이해하고 자연어 명령으로 복잡한 작업을 수행합니다. Anthropic
Azure VM Ubuntu 24 설치 방법
방법 1: 공식 설치 스크립트 (권장)
bashcurl -fsSL https://claude.ai/install.sh | bash방법 2: NPM 설치
bash# Node.js 20.x 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# npm 글로벌 경로 설정 (sudo 없이 설치)
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Claude Code 설치
npm install -g @anthropic-ai/claude-code
claude doctor  # 설치 확인핵심 기능과 사용법
SSH로 Azure VM에 접속한 후 프로젝트 디렉토리에서 claude 명령으로 시작합니다. 자연어로 지시하면 파일을 직접 편집하고 터미널 명령을 실행합니다.
bashcd /path/to/pmi-korea-crawler
claude

> "Selenium 크롤러에 재시도 로직과 지수 백오프 추가해줘"
> "MongoDB 연결 코드를 비동기로 리팩토링해줘"
> "이 프로젝트 구조 분석하고 개선점 알려줘"비용 정책: Claude Pro 구독($20/월)으로 Sonnet 4.5와 함께 Claude Code 사용 가능합니다. Anthropic 복잡한 아키텍처 작업에는 Max 플랜($100/월)에서 Opus 4.1을 활용할 수 있습니다. ClaudeLog
Windsurf IDE 통합
Claude Code는 VS Code 기반 IDE와 완전히 통합됩니다. AnthropicAnthropic 터미널에서 /ide 명령을 실행하면 Windsurf를 자동 감지하여 연결합니다. 코드 변경 사항이 IDE에 실시간으로 반영되며, Diff 뷰어로 검토할 수 있습니다.더 보기Synthesized diff viewer concept and Azure VM deployment considerations pragmatically.13초사용자가 두 가지 질문을 하고 있습니다:

Diff 뷰어가 무엇인지
Azure VM 환경에서 Claude Code 설치 시 관리자와 협의가 필요한지, 추가 과금이 있는지, 그리고 로컬 환경에서 작업하는 것이 더 나은지

이 질문들에 대해 초보자가 이해하기 쉽게, 실용적으로 답변해야 합니다.

Diff 뷰어 설명:


코드 변경 전후를 비교해서 보여주는 도구
빨간색(삭제), 초록색(추가) 등으로 표시
Windsurf, VS Code 등에 기본 내장
Git과 연관하여 설명


Azure VM 관련 질문:


관리자와 협의 필요성: 대부분 필요 없음 (단순 소프트웨어 설치)
Azure 과금: Claude Code 자체는 Azure 리소스를 직접 사용하지 않으므로 추가 과금 없음
다만 VM의 CPU/메모리/네트워크는 사용하므로 기존 VM 요금에 포함
로컬 vs VM 비교: 각각의 장단점 설명

사용자의 상황을 고려하면:

Azure portal 접근 권한 없음
VM만 받아서 작업
사무실, 집, 독서실을 옮겨다니며 작업
긴 크롤링 작업이 필요

이런 상황에서는 VM 환경이 더 적합할 것 같습니다. 이동 중에도 작업 지속성을 유지할 수 있고, 장시간 크롤링 작업에 안정적입니다. 네트워크 연결만 좋다면 어디서든 작업할 수 있는 장점이 있습니다.좋은 질문입니다! 차근차근 답변드리겠습니다.

1️⃣ Diff 뷰어란?
**Diff 뷰어(Difference Viewer)**는 코드 변경 전후를 나란히 비교해서 보여주는 도구입니다.
시각적 예시
📄 before.py (왼쪽)              │  📄 after.py (오른쪽)
─────────────────────────────────┼──────────────────────────────
def crawl_blog(url):             │  def crawl_blog(url):
    response = requests.get(url) │  ❌ response = requests.get(url)
                                  │  ✅ try:
                                  │  ✅     response = requests.get(url, timeout=10)
                                  │  ✅ except Exception as e:
                                  │  ✅     logger.error(f"Error: {e}")
                                  │  ✅     return None
    return response.text         │      return response.text
색상 표시

🔴 빨간색: 삭제된 코드
🟢 초록색: 추가된 코드
🟡 노란색: 수정된 코드

Windsurf에서 보이는 모습
Windsurf에서 Claude가 코드를 제안하면 이렇게 표시됩니다:
[에디터 화면]
┌─────────────────────────────┐
│ 📝 naver_crawler.py         │
├─────────────────────────────┤
│ def get_post(url):          │
│ -   driver.get(url)         │ ← 빨간색 배경
│ +   try:                    │ ← 초록색 배경
│ +       driver.get(url)     │ ← 초록색 배경
│ +   except TimeoutException:│ ← 초록색 배경
│ +       return None         │ ← 초록색 배경
│                             │
│ [✓ Accept] [✗ Reject]       │ ← 버튼으로 선택
└─────────────────────────────┘
왜 중요한가?

실수 방지: AI가 엉뚱한 코드를 삭제하거나 잘못 수정한 걸 바로 발견
학습 효과: 어떤 부분이 어떻게 바뀌는지 명확히 이해
선택적 적용: 좋은 부분만 Accept, 이상한 부분은 Reject

Git과의 관계
Git에서도 같은 기능을 사용합니다:
bashgit diff              # 변경사항 확인
git diff HEAD~1       # 이전 커밋과 비교
Windsurf, VS Code, GitHub 등 대부분의 개발 도구에 기본 내장되어 있습니다.

2️⃣ Azure VM 환경 관련 질문들
Q1: Azure 관리자와 상의가 필요한가?
대부분의 경우 상의 불필요합니다. 다음 이유 때문입니다:
✅ 상의 불필요한 경우 (대부분)
bash# 이런 작업들은 일반 사용자 권한으로 가능
npm install -g @anthropic-ai/claude-code  # 내 홈디렉토리에 설치
pip install selenium paddleocr             # Python 패키지 설치
git clone https://github.com/...           # 코드 다운로드
이유:

VM에 SSH 접근 권한이 있다면 대부분 작업 가능
npm 글로벌 설치도 ~/.npm-global에 설치하므로 sudo 불필요
네트워크 아웃바운드(외부 접속)는 보통 허용되어 있음

⚠️ 상의 필요한 경우 (드물게)
bash# 이런 작업은 관리자 권한 필요
sudo apt install ...        # 시스템 레벨 패키지 설치
docker run ...              # Docker 사용 (권한 설정 필요)
방화벽 설정 변경             # 특정 포트 열기
```

**당신의 경우**:
- Node.js가 이미 설치되어 있다면 → 상의 불필요
- Node.js가 없다면 → "Node.js 20.x 설치 필요합니다" 한 번만 요청

### Q2: Azure에 추가 과금이 발생하나?

**Claude Code 자체는 Azure 과금 없음**입니다. 하지만 간접적 영향은 있습니다:

#### 💰 과금 구조

| 항목 | 비용 발생 | 설명 |
|------|---------|------|
| **Claude Code 사용료** | ✅ Anthropic에 과금 ($20/월) | Claude Pro 구독료 |
| **VM 컴퓨팅 비용** | ⚠️ 기존 VM 요금에 포함 | CPU/메모리는 이미 쓰는 중 |
| **네트워크 송신** | ⚠️ 거의 없음 (무시 가능) | Claude API 호출 시 몇 KB |
| **스토리지** | ⚠️ 거의 없음 (무시 가능) | 코드 파일은 MB 단위 |

#### 📊 실제 예상 비용
```
기존 Azure VM 비용: $200/월 (8core, 32GB, 24/7 가정)
                     ↓
Claude Code 설치 후: $200/월 (변동 없음)
                     + $20/월 (Claude Pro)
                     ─────────
                     = $220/월
```

**핵심**: 
- Azure 청구서에는 변화 없음
- Claude 청구서에만 $20/월 추가

#### ⚠️ 예외: 대량 데이터 전송

만약 Claude Code가 **수십 GB 파일을 외부로 업로드**한다면 네트워크 송신 비용이 발생할 수 있습니다. 하지만:
- Claude Code는 코드만 주고받음 (텍스트)
- 크롤링 데이터는 VM 내부에 저장
- → 추가 비용 거의 없음

### Q3: 로컬 vs VM 작업 비교

이게 핵심 질문입니다. **당신의 상황**을 고려하면:

#### 📍 당신의 작업 환경
- ✅ 사무실, 집, 독서실 이동
- ✅ 긴 크롤링 작업 (몇 시간~하루)
- ✅ 맥북 보유
- ✅ Azure VM 24/7 운영 중

#### 🎯 권장: 하이브리드 방식
```
┌──────────────────────────────────────┐
│  로컬 맥북 (Windsurf)                 │
│  ├─ 코드 작성 & 디버깅                │
│  ├─ 작은 테스트 (10분 이내)           │
│  └─ Git으로 VM에 push                │
└──────────────────────────────────────┘
                ↓ Git push
┌──────────────────────────────────────┐
│  Azure VM                             │
│  ├─ 긴 크롤링 작업 (1시간+)            │
│  ├─ 24/7 스케줄 실행                   │
│  └─ 대용량 데이터 저장                 │
└──────────────────────────────────────┘
구체적 워크플로우
1단계: 로컬에서 개발
bash# 맥북 Windsurf에서
cd ~/pmi-korea-crawler

# Windsurf Cascade로 코드 작성
# "네이버 블로그 크롤러 구현해줘"

# 짧은 테스트 (10분)
python test_crawler.py --limit 10

# Git 커밋
git add -A
git commit -m "feat: 네이버 크롤러 추가"
git push origin main
2단계: VM에서 실행
bash# SSH로 Azure VM 접속
ssh azureuser@your-vm-ip

# 코드 가져오기
cd /home/azureuser/pmi-korea-crawler
git pull origin main

# 긴 작업 실행 (백그라운드)
nohup python run_crawler.py --full > crawler.log 2>&1 &

# 로그 확인
tail -f crawler.log

# SSH 접속 종료해도 작업 계속 진행
exit
3단계: 결과 확인
bash# 다음 날 다시 접속
ssh azureuser@your-vm-ip

# 결과 다운로드
scp azureuser@your-vm-ip:/path/to/data.csv ~/Downloads/
```

#### 장단점 비교

| 방식 | 장점 | 단점 | 권장 시나리오 |
|------|------|------|--------------|
| **로컬만** | • 빠른 반응속도<br>• 네트워크 필요 없음<br>• 익숙한 환경 | • 장시간 작업 불가<br>• 노트북 배터리 소모<br>• 장소 이동 시 중단 | • 코드 작성<br>• 짧은 테스트<br>• 데이터 분석 |
| **VM만** | • 24/7 실행 가능<br>• 장소 제약 없음<br>• 고사양 활용 | • SSH 필수<br>• 네트워크 지연<br>• 에디터 환경 제한 | • 대량 크롤링<br>• 스케줄 실행<br>• 멀티미디어 처리 |
| **하이브리드** ✅ | • 양쪽 장점 결합<br>• 유연한 작업 방식<br>• 최적의 효율 | • Git 사용 필요<br>• 초기 설정 필요 | • **대부분의 경우** |

---

## 🎯 최종 권장사항

### 당신의 경우 최적 전략

#### ✅ **하이브리드 방식 채택**

**이유**:
1. **장소 이동 문제 해결**: 로컬에서 개발, VM에서 실행
2. **긴 작업 가능**: 독서실 가도 VM은 계속 크롤링
3. **배터리 절약**: 맥북으로 코딩만, 무거운 작업은 VM
4. **비용 효율**: VM은 이미 있으므로 추가 비용 없음

#### 📝 구체적 실행 계획

**Week 1: 로컬 개발 + VM 테스트**
```
[로컬 맥북]
월: Windsurf에서 크롤러 기본 구조 작성 (2시간)
화: 네이버 블로그 크롤러 구현 (3시간)
수: 짧은 테스트 (10개 게시물, 10분)

[Azure VM]
수 저녁: VM에 코드 push, 대량 크롤링 시작 (1,000개)
목 아침: 결과 확인, 로컬로 다운로드
목: 로컬에서 데이터 분석
```

**Week 2-3: 안정화 단계**
```
[로컬 맥북]
- 코드 개선, 버그 수정
- 데이터 분석, 시각화
- 보고서 작성

[Azure VM]
- 매일 밤 자동 크롤링 (cron 설정)
- 멀티미디어 처리 (OCR, Whisper)
- 데이터베이스 적재
🔧 필요한 초기 설정
1. Git 설정 (5분)
bash# 로컬 맥북
cd ~/pmi-korea-crawler
git init
git remote add origin https://github.com/your-username/pmi-crawler.git

# .gitignore 추가
echo "*.csv
*.log
__pycache__/
.env" > .gitignore

# 첫 커밋
git add -A
git commit -m "Initial commit"
git push -u origin main
2. VM에서 Git 클론 (1분)
bash# Azure VM SSH 접속
ssh azureuser@your-vm-ip

# 코드 가져오기
cd ~
git clone https://github.com/your-username/pmi-crawler.git
cd pmi-crawler
3. 환경 동기화 (10분)
bash# 로컬과 VM 환경 동일하게 설정
# requirements.txt 생성
pip freeze > requirements.txt

# VM에서 설치
pip install -r requirements.txt
```

### 📱 관리자와 상의할 사항

**필요시에만 요청**:
```
Subject: Azure VM Node.js 설치 요청

안녕하세요,

현재 PM SNS 크롤링 프로젝트를 위해 
Claude Code CLI 도구를 사용하려고 합니다.

Node.js 20.x 설치가 필요한데,
제가 직접 설치할 수 있는 권한이 있는지 확인 부탁드립니다.

없다면 아래 명령어로 설치 부탁드립니다:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

감사합니다.
```

**대부분의 경우**: 위 요청 없이 바로 작업 가능합니다. 에러가 발생하면 그때 요청하세요.

---

## 📊 비용 정리

### 월간 예상 비용
```
[기존 비용]
Azure VM (8core, 32GB): $200/월 (예상)

[추가 비용]
Claude Pro: $20/월 (선택사항)
Windsurf Pro: $15/월 (이미 구독 중)
────────────────────
총 추가: $20/월 (Claude Code 사용 시)
Claude Code를 안 쓴다면: 추가 비용 $0

💡 최종 결론
질문별 답변 요약

Diff 뷰어: 코드 변경 전후를 빨강/초록으로 나란히 비교하는 도구
관리자 상의: 대부분 불필요, Node.js 없으면 한 번만 요청
Azure 과금: Claude Code 자체는 과금 없음, 기존 VM 요금에 포함
로컬 vs VM: 하이브리드가 최적 - 로컬에서 개발, VM에서 실행

🎯 행동 계획
오늘 할 일:

✅ 로컬 맥북 Windsurf에서 코드 작성 시작
✅ Git 저장소 설정 (GitHub/GitLab)
✅ Azure VM에 Git 클론

내일 할 일:

✅ 로컬에서 짧은 테스트 (10개 게시물)
✅ 문제 없으면 VM에 push
✅ VM에서 대량 크롤링 시작 (1,000개)

Claude Code는: 2주차에 대규모 리팩토링이 필요할 때 도입하세요. 지금 당장은 필수가 아닙니다.

도움이 되셨나요? 추가 질문 있으시면 언제든 말씀해주세요! 😊재시도Mwindwurf의 터미널인 CLI에서 Azure vm을 키고 거기에서 Claude Code를 올려서 이용하라는 게 당신이 추천하는 방식이 맞나요? 그렇다면 그냥 로컬에서 Claude Code를 이용하는 것과 장단점이 무엇이 있을까요? Claude code는 자동으로 기존 코드를 탐색하고 디버깅하고 요청을 받아들여서도 작업한다는데 맞나요? 이러한 과정이 로컬에서는 노트북을 끈 상태에서는 종료되는건가요? 24시간 작동하는 Azure vm 상에서는 어떤가요?사용자의 Claude Code 오해를 명확히 바로잡았습니다.사용자가 제 이전 답변에 대해 혼란스러워하고 있습니다. 명확히 정리가 필요합니다:

Claude Code의 작동 방식에 대한 오해
로컬 vs VM에서의 Claude Code 실행 차이
24/7 작동 가능성에 대한 오해

핵심 포인트:

Claude Code는 일회성 대화형 도구입니다
백그라운드에서 24/7 자동으로 작동하는 에이전트가 아닙니다
"claude" 명령을 실행한 세션 동안만 작동
SSH 연결이 끊기면 Claude Code 세션도 종료
VM에서 실행해도 tmux/screen 없이는 연결 끊으면 종료

사용자의 오해를 정확히 바로잡아야 합니다:

Claude Code ≠ 자율 에이전트 (24/7 작동)
Claude Code = 대화형 코딩 도구 (사용자가 명령할 때만 작동)
VM vs 로컬의 차이는 크지 않음
제 권장은 "로컬에서 개발, VM에서 크롤링 실행"이지 "VM에서 Claude Code 실행"이 아님

명확히 정리해드려야겠습니다.정말 중요한 오해를 짚어주셔서 감사합니다! 제 설명이 혼란을 드렸네요. 명확히 정정하겠습니다.

🚨 중요한 오해 바로잡기
❌ 제가 추천한 것이 아닌 것
[잘못된 이해]
Windsurf 터미널 → Azure VM SSH 접속 
→ Claude Code 실행 → 24/7 자동 작동 ❌
이건 불가능합니다! Claude Code는 24/7 자동으로 작동하는 에이전트가 아닙니다.
✅ 제가 실제로 추천한 것
[올바른 이해]
방법 1: 로컬 맥북에서 Claude Code 실행
방법 2: VM에서 Claude Code 실행 (SSH 세션 동안만)

둘 다 가능하지만, 저는 "로컬 맥북"을 더 추천합니다.

🔍 Claude Code의 실제 작동 방식
1️⃣ Claude Code는 "대화형 도구"입니다
bash# 터미널에서 실행
$ claude

# 대화 시작
You: "이 프로젝트 구조 분석해줘"
Claude: [파일들을 읽고 분석 후 답변]

You: "네이버 크롤러에 재시도 로직 추가해줘"  
Claude: [코드 수정하고 파일 저장]
Claude: "완료했습니다. 변경사항을 검토해주세요."

# 작업 끝나면 종료
You: exit
$  # 다시 일반 터미널로 돌아옴
2️⃣ 자동으로 작동하지 않습니다
Claude Code는:

✅ 당신이 명령하면 → 코드 분석/수정/생성
✅ 당신이 질문하면 → 답변
✅ 당신이 "exit" 하면 → 종료
❌ 24/7 혼자 작동 ❌
❌ 백그라운드 실행 불가 ❌
❌ 자동으로 버그 찾아서 고치지 않음 ❌

3️⃣ 실행 환경별 차이
로컬 맥북에서 실행
bash# 맥북 터미널
$ cd ~/pmi-korea-crawler
$ claude

You: "크롤러 구현해줘"
Claude: [작업 진행...]

# 맥북 뚜껑 닫으면?
→ 터미널 종료 → Claude Code 세션 종료 ❌
Azure VM에서 실행
bash# SSH 접속
$ ssh azureuser@vm-ip
$ cd ~/pmi-korea-crawler
$ claude

You: "크롤러 구현해줘"  
Claude: [작업 진행...]

# SSH 연결 끊으면?
→ SSH 세션 종료 → Claude Code 세션 종료 ❌
```

**결론**: 로컬이든 VM이든 **연결이 끊기면 Claude Code는 종료**됩니다.

---

## 💡 로컬 vs VM에서 Claude Code 사용

### 비교표

| 항목 | 로컬 맥북 | Azure VM (SSH) |
|------|----------|----------------|
| **실행 속도** | ✅ 빠름 (로컬) | 🟡 보통 (네트워크 지연) |
| **파일 접근** | ✅ 즉시 | 🟡 SSH 터널 통과 |
| **Windsurf 통합** | ✅ 완벽 (`/ide` 명령) | ❌ SSH 환경에선 어려움 |
| **편안함** | ✅ 익숙한 환경 | 🟡 터미널만 봐야 함 |
| **컴퓨팅 파워** | 🟡 맥북 성능 | ✅ VM 고사양 (8core 32GB) |
| **연결 끊기면?** | ❌ 종료 | ❌ 종료 |
| **24/7 작동?** | ❌ 불가 | ❌ 불가 (tmux 사용해도 의미 없음) |

### 🎯 명확한 결론

**Claude Code는 로컬에서 사용하세요!**

**이유**:
1. **Windsurf와 통합**: `/ide` 명령으로 IDE와 실시간 연동
2. **빠른 반응**: SSH 지연 없음
3. **편안한 환경**: 맥북 화면으로 코드 보면서 작업
4. **VM 성능 불필요**: Claude Code는 당신 컴퓨터에서 실행, Claude API는 Anthropic 서버에서 처리

---

## 🔄 실제 워크플로우 (정정)

### ✅ 올바른 방법
```
┌─────────────────────────────────────┐
│  로컬 맥북                            │
│  ┌──────────────────────────────┐   │
│  │ Windsurf IDE (GUI)           │   │
│  │ - 파일 편집                   │   │
│  │ - 코드 리뷰                   │   │
│  │ - Cascade AI로 코드 생성      │   │
│  └──────────────────────────────┘   │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ 터미널 (CLI)                  │   │
│  │ $ claude                      │   │
│  │ > "전체 프로젝트 리팩토링"      │   │
│  │ > (작업 완료 후 exit)          │   │
│  └──────────────────────────────┘   │
│                                      │
│  $ git add -A                        │
│  $ git commit -m "리팩토링 완료"     │
│  $ git push                          │
└─────────────────────────────────────┘
              ↓ Git push
┌─────────────────────────────────────┐
│  Azure VM                            │
│  $ git pull                          │
│  $ nohup python run_crawler.py &    │ ← 긴 크롤링만 실행
│  (백그라운드에서 24/7 크롤링)         │
└─────────────────────────────────────┘
각 도구의 역할
도구역할실행 위치지속 시간Windsurf IDE코드 편집, 시각적 작업로컬 맥북맥북 켜져 있을 때Claude Code대규모 리팩토링, 구조 변경로컬 맥북대화 세션 동안만 (10-30분)Python 크롤러실제 데이터 수집Azure VM24/7 백그라운드

📝 구체적 시나리오
시나리오 1: 크롤러 개발 (Day 1-5)
100% 로컬 맥북에서 작업
bash# 맥북에서
$ cd ~/pmi-korea-crawler

# [방법 A] Windsurf Cascade로 작업
# Windsurf IDE 열고 채팅:
"네이버 블로그 크롤러 구현해줘"
→ 코드 생성 → Accept → 완료

# [방법 B] 복잡한 구조 변경은 Claude Code
$ claude
> "프로젝트를 crawlers/, processors/, database/ 
   3개 모듈로 분리하고 각각 __init__.py 만들어줘"
> exit

# 짧은 테스트
$ python test_crawler.py --limit 10

# Git 커밋
$ git add -A
$ git commit -m "feat: 네이버 크롤러 구현"
$ git push
시나리오 2: 대량 크롤링 (Day 6)
코드는 로컬에서 완성, 실행만 VM에서
bash# 로컬 맥북에서 (오전)
$ git add -A
$ git commit -m "크롤러 완성"
$ git push

# Azure VM SSH 접속 (오전)
$ ssh azureuser@vm-ip
$ cd ~/pmi-korea-crawler
$ git pull

# 백그라운드 실행
$ nohup python run_crawler.py --platform naver --limit 1000 > crawler.log 2>&1 &
$ exit  # SSH 끊어도 크롤링은 계속

# 독서실 가기 (맥북 가방에)
# → VM은 계속 크롤링 중 ✅

# 저녁에 다시 확인 (카페에서)
$ ssh azureuser@vm-ip
$ tail -f crawler.log
$ exit
시나리오 3: 데이터 분석 (Day 7)
100% 로컬 맥북에서 작업
bash# VM에서 데이터 다운로드
$ scp azureuser@vm-ip:~/crawler_results.csv ~/Downloads/

# 로컬에서 분석
$ cd ~/pmi-korea-crawler
$ jupyter notebook
# → 데이터 분석, 시각화

# Windsurf에서 분석 코드 작성
# "이 데이터로 클러스터링 해줘"

⚠️ Claude Code의 한계
Claude Code가 할 수 있는 것
bash$ claude

# ✅ 가능
> "프로젝트 전체를 분석하고 개선점 알려줘"
> "모든 크롤러에 공통 에러 핸들링 추가해줘"  
> "MongoDB 스키마 설계하고 models.py 만들어줘"
> "requirements.txt 업데이트하고 설치해줘"
Claude Code가 할 수 없는 것
bash# ❌ 불가능
> "밤새 크롤링하고 내일 아침에 알려줘" ❌
> "버그 발견하면 자동으로 고쳐줘" ❌
> "24시간 모니터링하고 에러나면 재시작해줘" ❌

# 이런 건 별도 스크립트 필요
# → cron, systemd, supervisord 등
```

---

## 🤔 그럼 VM에서 Claude Code는 언제 쓰나?

### 거의 안 씁니다!

**VM에서 Claude Code를 쓸 이유**:
1. ❌ 24/7 작동? → 불가능
2. ❌ 고성능 필요? → AI는 Anthropic 서버에서 실행
3. ❌ 파일 용량 큰가? → 코드는 MB 단위
4. ⚠️ 로컬 맥북이 없는 상황? → 이때만 고려

**예외 케이스**:
```
상황: 카페에서 아이패드만 들고 있음
해결: iPad로 SSH → VM에서 Claude Code 실행

하지만 불편함:
- Windsurf IDE 없음
- 터미널만 보임
- 코드 검토 어려움

🎯 최종 권장사항
1️⃣ Claude Code는 로컬 맥북에서만
bash# 로컬 맥북 터미널
$ cd ~/pmi-korea-crawler
$ claude

# 대화형으로 코드 작업
# 10-30분 작업 후 exit
이유:

Windsurf IDE와 통합 (/ide)
빠른 반응 (네트워크 지연 없음)
편안한 환경
VM 성능 불필요

2️⃣ Windsurf는 로컬에서만
bash# 로컬 맥북
# Windsurf IDE 실행
# Cascade로 코드 작성/수정
3️⃣ Azure VM은 실행만
bash# VM에서
$ git pull
$ nohup python run_crawler.py &
$ exit

# 24/7 백그라운드 크롤링만
```

---

## 📊 정리: 3가지 도구의 역할

| 도구 | 목적 | 위치 | 지속성 |
|------|------|------|--------|
| **Windsurf IDE** | 일상 코딩, 시각적 작업 | 로컬 맥북 | 맥북 켤 때 |
| **Claude Code** | 대규모 리팩토링, 한 번 | 로컬 맥북 | 대화 세션 동안 |
| **Python 스크립트** | 실제 크롤링 실행 | Azure VM | 24/7 백그라운드 |

### 작업 흐름
```
[로컬] Windsurf로 코드 작성
   ↓
[로컬] Claude Code로 구조 정리 (필요시)
   ↓
[로컬] Git push
   ↓
[VM] Git pull
   ↓
[VM] nohup python ... &  ← 여기서만 24/7
```

---

## 💰 비용 재확인
```
Windsurf Pro: $15/월 (로컬에서만 사용)
Claude Pro: $20/월 (로컬에서 Claude Code 사용)
Azure VM: $200/월 (이미 사용 중, 추가 비용 없음)
─────────────
총: $35/월 (VM 제외)
```

**Claude Code를 VM에서 실행해도 비용은 같습니다.**  
왜냐하면 AI 처리는 Anthropic 서버에서 하기 때문입니다.

---

## ✅ 최종 답변

### 질문별 답변

1. **VM에서 Claude Code 실행 추천?**  
   → ❌ 아닙니다. **로컬 맥북** 추천

2. **로컬 vs VM 장단점?**  
   → 로컬이 더 좋음 (Windsurf 통합, 빠름, 편함)

3. **Claude Code 자동 탐색/디버깅?**  
   → ✅ 맞지만 "당신이 명령할 때만" (24/7 자동 아님)

4. **맥북 끄면 종료?**  
   → ✅ 맞습니다 (Claude Code는 세션 동안만)

5. **VM에서는 24시간 작동?**  
   → ❌ SSH 끊으면 Claude Code도 종료  
   → ✅ Python 크롤러 스크립트만 24시간 작동

---

## 🎯 핵심 정리
```
Claude Code ≠ 24/7 자율 에이전트
Claude Code = 대화형 코딩 도구

사용법:
1. 로컬 맥북 터미널에서 "claude" 실행
2. 대화하며 코드 작업 (10-30분)
3. "exit"로 종료
4. 결과물을 Git으로 VM에 전송
5. VM에서는 Python 스크립트만 24/7 실행
제 이전 설명이 혼란을 드려 죄송합니다. 이제 명확하게 이해되셨나요? 추가 질문 있으시면 말씀해주세요! 😊

2. Perflexity()

이제 프로젝트 전반에 대한 종합적인 분석과 전략적 권고사항을 포함한 보고서를 작성하겠습니다. 심층적인 사고가 필요한 부분이 많으니 충분히 고민하여 답변드리겠습니다.

PM 판매원 SNS 분석 프로젝트 중간점검 및 재설계 보고서
Executive Summary
현재 프로젝트는 데이터 수집 단계에서 70% 완료, 분석 및 시스템화 단계에서 30% 완료 상태입니다. 3주의 남은 기간 내에 실질적인 성과를 내기 위해서는 범위 조정과 우선순위 재설정이 필수적입니다. 본 보고서는 현황 진단, 문제 해결 방안, 아키텍처 재설계, 그리고 실행 계획을 제시합니다.

1. 현황 진단 (Current Status Assessment)
1.1 데이터 수집 현황
플랫폼	수집량	완성도	주요 이슈
네이버 블로그	7,890건 (261건 정제)	🟡 70%	해시태그 필터링 불가, 노이즈 많음, OCR 미작동
카카오스토리	4,769건	🟢 85%	구조화 양호, 멀티미디어 처리 필요
유튜브	376건	🔴 50%	Whisper 음성인식 실패율 높음, 썸네일 OCR 진행 중
인스타그램	~300건	🔴 40%	슬라이드 앨범 수집 불가, 임시 URL 문제
네이버 카페	테스트 중	🔴 20%	로그인 필요, 구조 복잡
핵심 발견:

수집된 데이터가 GB 단위가 아닌 MB~수백MB 수준으로 예상보다 소규모

텍스트 데이터 품질은 우수 (평균 본문 1,672자)

멀티미디어 처리가 최대 병목 (OCR 0%, Whisper 성능 불안정)

1.2 기술적 문제점 분석
🚨 1순위 문제: 지속적인 버그와 디버깅 순환
원인 진단:

text
Claude 사용 패턴의 문제
    ↓
한 번에 여러 요구사항을 제시
    ↓
Claude가 전체 코드를 재작성
    ↓
이전에 수정했던 다른 부분이 다시 깨짐
    ↓
반복적인 디버깅 루프
해결 방안:

Git 버전 관리 강화

bash
# 작업 전 반드시 브랜치 생성
git checkout -b feature/네이버블로그-OCR수정

# 커밋 단위를 작게
git commit -m "fix: 이미지 URL 검증 로직 추가"

# 문제 발생 시 즉시 롤백
git checkout main
Claude 사용 전략 변경

❌ 잘못된 방식: "네이버 블로그 크롤러를 개선해줘. OCR도 추가하고, 에러 처리도 개선하고, 로깅도 추가해줘"

✅ 올바른 방식:

text
1차: "현재 코드에서 이미지 URL이 None인 경우만 검증 로직 추가"
→ 테스트 → 커밋

2차: "이전 코드 유지하면서 OCR 함수만 별도 파일로 분리"
→ 테스트 → 커밋
모듈화 및 단위 테스트

python
# 기능별로 완전히 분리
crawlers/
    naver/
        fetcher.py       # URL 수집만
        parser.py        # HTML 파싱만
        validator.py     # 데이터 검증만
        ocr.py          # OCR 처리만
Windsurf + Claude 조합 최적화

Windsurf의 Cascade 모드 활용: 특정 함수만 수정 요청

Claude Projects에 프로젝트 컨텍스트 저장: 매번 전체 설명 불필요

변경 이력 문서화: CHANGELOG.md에 모든 수정사항 기록

🚨 2순위 문제: 멀티미디어 처리 (Whisper 실패)
Whisper 문제 원인 분석:

문제 유형	발생 빈도	해결 난이도
영상 URL이 1회용(expire)	높음	🔴 높음
음성이 음소거됨	중간	🟢 낮음
Whisper 모델 한계 (잡음, 억양)	높음	🟡 중간
자막 없는 영상	매우 높음	🔴 높음
해결 방안 - 단계별 Fallback 전략:

python
def extract_video_text(video_url, video_data):
    """
    우선순위 기반 텍스트 추출
    """
    # STEP 1: 자막 API 시도 (가장 정확)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        if transcript:
            return {'method': 'subtitle', 'text': transcript, 'confidence': 1.0}
    except:
        pass
    
    # STEP 2: Whisper Local (무료, 느림)
    if WHISPER_AVAILABLE:
        try:
            audio = download_audio(video_url)
            result = whisper_model.transcribe(audio, language='ko')
            return {'method': 'whisper', 'text': result['text'], 'confidence': 0.7}
        except:
            pass
    
    # STEP 3: Azure Speech-to-Text (유료, 정확)
    if AZURE_SPEECH_ENABLED and is_critical_video(video_data):
        try:
            result = azure_speech_to_text(video_url)
            return {'method': 'azure', 'text': result, 'confidence': 0.9}
        except:
            pass
    
    # STEP 4: 썸네일 OCR로 대체
    try:
        thumbnail_url = get_thumbnail(video_url)
        ocr_text = easyocr_reader.readtext(thumbnail_url)
        return {'method': 'thumbnail_ocr', 'text': ocr_text, 'confidence': 0.5}
    except:
        pass
    
    # STEP 5: 메타데이터만 저장
    return {
        'method': 'metadata_only', 
        'text': f"{video_data.get('title', '')} {video_data.get('description', '')}", 
        'confidence': 0.3
    }
Whisper 대안 평가:

솔루션	정확도	비용	속도	권장
YouTube 자막 API	95%+	무료	빠름	✅ 1순위
Whisper base (local)	85%	무료	느림	✅ 2순위
Azure Speech	95%	$0.024/분	빠름	⚠️ 중요 영상만
Google Cloud Speech	93%	$0.024/분	빠름	⚠️ Azure와 동일
Naver Clova	98% (한국어)	₩15/분	빠름	🟡 고려 가능
현실적 권고:

80%의 영상은 자막 API 또는 메타데이터만 사용

나머지 20% 중 중요한 영상만 Azure/Clova 사용

비용 절감을 위해 Whisper는 포기하지 말고 단순 참고용으로만

2. 데이터베이스 설계 재검토
2.1 "DB 구축"이란 무엇인가?
많은 초보자가 오해하는 부분입니다. DB 구축은 단순히 PostgreSQL을 설치하는 것이 아닙니다.

DB 구축의 실제 의미:

text
1. 데이터 모델링
   └─ 어떤 테이블이 필요한가?
   └─ 테이블 간 관계는?
   └─ 어떤 컬럼이 필요한가?
   
2. 스키마 설계
   └─ DDL 작성 (CREATE TABLE)
   └─ 제약조건 설정 (PRIMARY KEY, FOREIGN KEY)
   └─ 인덱스 설계
   
3. 데이터 파이프라인 구축
   └─ 크롤링 → JSON/CSV → DB 적재
   └─ ETL (Extract, Transform, Load)
   
4. 쿼리 최적화
   └─ 분석 쿼리가 빠르게 실행되도록
   
5. 백업 및 복구 전략
2.2 상무님이 NoSQL을 추천한 이유
상무님의 관점 (추정):

비정형 데이터 (JSON, 이미지 URL, 가변 필드)가 많음

스키마 변경이 잦을 것 (초기 프로젝트)

조인 복잡도 낮음 (단순 집계 위주)

하지만 여러분의 실제 상황:

데이터가 GB 단위가 아닌 수백 MB 수준

분석 쿼리가 복잡함 (집계, 클러스터링, 상관관계)

SQL 쿼리가 훨씬 직관적

2.3 최종 권고: Hybrid Architecture
결론: PostgreSQL + JSON 타입 활용 = "Best of Both Worlds"

sql
-- PostgreSQL에서 NoSQL처럼 사용 가능
CREATE TABLE sns_posts (
    post_id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    
    -- 정형 데이터
    published_at TIMESTAMP NOT NULL,
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    
    -- 반정형 데이터 (JSON)
    content JSONB,                    -- {title, text, hashtags}
    media JSONB,                      -- {images: [], videos: []}
    metadata JSONB,                   -- {sponsor_id, phone, etc}
    
    -- 분석용 컬럼
    engagement_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN (content->>'view_count')::INT > 0 
             THEN (like_count + comment_count)::FLOAT / (content->>'view_count')::INT
             ELSE 0 
        END
    ) STORED,
    
    -- 인덱스
    created_at TIMESTAMP DEFAULT NOW()
);

-- JSON 내부 쿼리 가능
CREATE INDEX idx_hashtags ON sns_posts USING GIN ((content->'hashtags'));

-- 예시 쿼리
SELECT 
    user_id,
    COUNT(*) as post_count,
    AVG(engagement_rate) as avg_engagement
FROM sns_posts
WHERE content->'hashtags' @> '["#피엠"]'
GROUP BY user_id
ORDER BY avg_engagement DESC;
장점:

✅ SQL의 강력한 집계/조인 기능 사용

✅ 스키마 유연성 (JSONB로 해결)

✅ Power BI 직접 연결 가능

✅ 인덱스 및 성능 최적화 용이

2.4 DB 인프라 결정 트리
text
데이터 규모는?
    ├─ < 1GB → SQLite (로컬 파일, 무료)
    ├─ 1~10GB → PostgreSQL (Azure VM에 직접 설치)
    └─ > 10GB → Azure Database for PostgreSQL
    
비용 고려?
    ├─ 무료 → PostgreSQL (VM에 직접 설치) + Cron 백업
    └─ 유료 OK → Azure Database for PostgreSQL (관리형)
    
Blob Storage 필요?
    ├─ 이미지/영상 원본 저장 → 필요 (장기 보관용)
    └─ URL만 저장 → 불필요
최종 권고 (비용 최소화):

text
Architecture:
  Data Collection VM (24/7):
    - 크롤링 스크립트 실행
    - 수집 데이터를 로컬 SQLite에 임시 저장
    - 매일 자정 PostgreSQL로 동기화
    
  Analysis VM (평일 9-16시):
    - PostgreSQL 서버 운영
    - Jupyter Notebook 분석
    - Power BI 연결
    
  Storage:
    - PostgreSQL: 정형/반정형 데이터
    - Local File System: 이미지/영상 캐시 (일주일 후 삭제)
    - (선택) Blob Storage: 중요 미디어 장기 보관
    
  Backup:
    - 매일 PostgreSQL dump → VM 로컬 저장
    - 매주 Blob Storage에 백업 업로드
비용 절감 효과:

Blob Storage 비용: $0 (사용 안 함)

Managed DB 비용: $0 (VM에 직접 설치)

총 비용: VM 비용만 ($306.60 + $50.40 = $357/월)

3. 데이터 분석 및 AI 모델 개발 전략
3.1 현재 작업 평가 (네이버 블로그 기준)
✅ 잘 하고 있는 것:

EDA 리포트: 기본 통계, 분포 분석 우수

BI Dashboard: 시각화 구성 적절

클러스터링 시도: K-Means 적용

🔺 개선 필요:

피처 엔지니어링 부족: 현재 단순 집계만 사용

도메인 지식 미반영: PM 판매원 특성 미고려

모델 검증 부재: 클러스터 해석 불명확

3.2 주요 피처(Feature) 재설계
현재 CSV 컬럼 분석 결과:

python
{
    'platform', 'post_id', 'blog_id', 'url', 'title', 'content',
    'published_datetime', 'sponsor_phone', 'content_sponsor_id',
    'like_count', 'comment_count', 'hashtags', 'image_urls', 
    'video_urls', 'content_type', ...
}
문제점:

개별 게시물 레벨 데이터만 존재

사용자(판매원) 레벨 집계 없음

시간적 패턴 피처 없음

개선된 피처 설계:

Level 1: 게시물 레벨 (현재)
python
# 이미 있는 것
- like_count, comment_count
- content_type (Undisclosed_Ad, QA_Format 등)

# 추가 필요
- engagement_rate = (like_count + comment_count) / view_count
- content_length = len(content)
- hashtag_count = len(hashtags)
- has_video = bool(video_urls)
- has_image = bool(image_urls)
- posting_hour = published_datetime.hour
- posting_day_of_week = published_datetime.dayofweek
- is_weekend = posting_day_of_week >= 5
Level 2: 사용자(판매원) 레벨 (NEW - 가장 중요!)
python
# 활동 빈도
user_features = {
    'total_posts': COUNT(posts),
    'posts_per_week': total_posts / weeks_active,
    'avg_posting_interval_days': AVG(days between posts),
    'active_weeks_ratio': active_weeks / total_weeks,
    
    # 콘텐츠 유형 선호도
    'undisclosed_ad_ratio': COUNT(Undisclosed_Ad) / total_posts,
    'qa_format_ratio': COUNT(QA_Format) / total_posts,
    'video_content_ratio': COUNT(Video_Content) / total_posts,
    
    # 참여도
    'avg_likes_per_post': AVG(like_count),
    'avg_comments_per_post': AVG(comment_count),
    'avg_engagement_rate': AVG(engagement_rate),
    'engagement_trend': 최근 10개 게시물 engagement 증감 추세,
    
    # 플랫폼 다양성
    'platform_count': COUNT(DISTINCT platform),
    'is_multi_platform': platform_count > 1,
    
    # 콘텐츠 품질 프록시
    'avg_content_length': AVG(content_length),
    'avg_hashtag_count': AVG(hashtag_count),
    'hashtag_diversity': COUNT(DISTINCT hashtags) / total_hashtags,
    
    # 시간 패턴
    'most_active_hour': MODE(posting_hour),
    'posts_on_weekend_ratio': COUNT(is_weekend=True) / total_posts,
    'consistency_score': STD(posting_interval) 의 역수,
    
    # 성장 지표
    'first_post_date': MIN(published_datetime),
    'last_post_date': MAX(published_datetime),
    'activity_duration_days': last_post_date - first_post_date,
    'recent_activity_ratio': COUNT(last_30_days) / total_posts,
}
코드 예시:

python
import pandas as pd
import numpy as np

def create_user_features(posts_df):
    """
    게시물 레벨 → 사용자 레벨 집계
    """
    # 사용자별 그룹화
    user_agg = posts_df.groupby('blog_id').agg({
        'post_id': 'count',
        'like_count': ['mean', 'sum', 'std'],
        'comment_count': ['mean', 'sum'],
        'content': lambda x: x.str.len().mean(),
        'hashtags': lambda x: x.str.split(',').apply(len).mean(),
        'published_datetime': ['min', 'max', 'count'],
        'content_type_primary': lambda x: x.value_counts().to_dict(),
        'platform': 'nunique',
    }).reset_index()
    
    # 컬럼명 정리
    user_agg.columns = ['_'.join(col).strip('_') for col in user_agg.columns]
    
    # 파생 피처
    user_agg['activity_duration_days'] = (
        (user_agg['published_datetime_max'] - user_agg['published_datetime_min']).dt.days
    )
    user_agg['posts_per_week'] = (
        user_agg['post_id_count'] / (user_agg['activity_duration_days'] / 7)
    )
    
    # 최근 활동 비율
    recent_threshold = pd.Timestamp.now() - pd.Timedelta(days=30)
    recent_posts = posts_df[posts_df['published_datetime'] > recent_threshold]
    recent_count = recent_posts.groupby('blog_id').size()
    user_agg['recent_activity_ratio'] = (
        recent_count / user_agg['post_id_count']
    ).fillna(0)
    
    return user_agg
3.3 클러스터링 개선 (K-Means → 더 나은 방법)
문제점:

K-Means는 구형 클러스터만 찾음

이상치에 민감

최적 K 선택이 애매함

개선 방안:

Option 1: 계층적 클러스터링 (Hierarchical Clustering)
python
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.preprocessing import StandardScaler

# 피처 스케일링
scaler = StandardScaler()
X_scaled = scaler.fit_transform(user_features)

# 계층적 클러스터링
linkage_matrix = linkage(X_scaled, method='ward')

# 덴드로그램 시각화 → 최적 클러스터 수 판단
plt.figure(figsize=(15, 8))
dendrogram(linkage_matrix)
plt.title('판매원 클러스터 덴드로그램')
plt.xlabel('판매원 ID')
plt.ylabel('거리')
plt.show()

# 클러스터 할당
from scipy.cluster.hierarchy import fcluster
clusters = fcluster(linkage_matrix, t=4, criterion='maxclust')
장점:

클러스터 수를 시각적으로 결정 가능

이상치 영향 적음

해석 가능한 계층 구조

Option 2: DBSCAN (밀도 기반)
python
from sklearn.cluster import DBSCAN

# 밀도 기반 클러스터링 (이상치 자동 탐지)
dbscan = DBSCAN(eps=0.5, min_samples=5)
clusters = dbscan.fit_predict(X_scaled)

# -1은 이상치(Noise)
print(f"이상치 비율: {(clusters == -1).sum() / len(clusters):.1%}")
장점:

이상치 자동 탐지 (고성과자/저성과자 식별)

클러스터 수를 미리 정할 필요 없음

임의 형태의 클러스터 탐지

Option 3: Gaussian Mixture Model (확률적 접근)
python
from sklearn.mixture import GaussianMixture

# 확률적 클러스터링
gmm = GaussianMixture(n_components=4, covariance_type='full', random_state=42)
clusters = gmm.fit_predict(X_scaled)

# 각 판매원의 클러스터 소속 확률
probabilities = gmm.predict_proba(X_scaled)
# 예: [0.8, 0.1, 0.05, 0.05] → 80% 확률로 클러스터 0 소속
장점:

"이 판매원은 70% 고성과, 30% 중성과" 같은 확률 제공

K-Means보다 유연한 클러스터 형태

권장: 앙상블 접근
python
def ensemble_clustering(X, user_ids):
    """
    여러 알고리즘 결과를 결합
    """
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.mixture import GaussianMixture
    from scipy.cluster.hierarchy import fcluster, linkage
    
    # 1. K-Means
    kmeans = KMeans(n_clusters=4, random_state=42)
    labels_kmeans = kmeans.fit_predict(X)
    
    # 2. Hierarchical
    linkage_matrix = linkage(X, method='ward')
    labels_hier = fcluster(linkage_matrix, t=4, criterion='maxclust') - 1
    
    # 3. GMM
    gmm = GaussianMixture(n_components=4, random_state=42)
    labels_gmm = gmm.fit_predict(X)
    
    # 4. 다수결 또는 합의 클러스터
    results_df = pd.DataFrame({
        'user_id': user_ids,
        'kmeans': labels_kmeans,
        'hierarchical': labels_hier,
        'gmm': labels_gmm
    })
    
    # 가장 일치하는 레이블 찾기
    from scipy.stats import mode
    results_df['consensus'] = results_df[['kmeans', 'hierarchical', 'gmm']].mode(axis=1)[0]
    
    return results_df
3.4 자연어 처리 (NLP) 전략
현실적 평가:

✅ 텍스트 데이터 품질 우수 (평균 1,672자)

⚠️ NLP는 시간 투자 대비 효과가 낮을 수 있음

🎯 우선순위: 간단하고 효과적인 방법부터

Level 1: 기본 텍스트 분석 (추천)
python
from konlpy.tag import Okt
from collections import Counter
import re

okt = Okt()

def basic_text_analysis(content_series):
    """
    복잡한 NLP 없이도 인사이트 추출 가능
    """
    results = []
    
    for content in content_series:
        # 1. 키워드 추출 (명사만)
        nouns = okt.nouns(content)
        
        # 2. PM 제품명 언급 횟수
        products = ['피트라인', 'FitLine', 'Activize', 'Restorate', 
                   'PowerCocktail', 'ProShape', 'Basics']
        product_mentions = {p: content.count(p) for p in products}
        
        # 3. 비즈니스 기회 키워드
        business_keywords = ['추천인', '후원', '가입', '비즈니스', '부업', 
                            '소득', '수익', '팀', '파트너']
        business_score = sum(1 for kw in business_keywords if kw in content)
        
        # 4. 감성 프록시 (긍정 단어 비율)
        positive_words = ['좋아', '최고', '만족', '추천', '효과', '성공', '행복']
        positive_score = sum(1 for pw in positive_words if pw in content)
        
        # 5. Before-After 패턴
        has_before_after = bool(re.search(r'(전|후|변화|개선)', content))
        
        results.append({
            'top_keywords': Counter(nouns).most_common(5),
            'product_mentions': product_mentions,
            'business_score': business_score,
            'positive_score': positive_score,
            'has_before_after': has_before_after,
            'content_length': len(content)
        })
    
    return pd.DataFrame(results)
시간 투자: 2-3일, 효과: 높음

Level 2: 토픽 모델링 (선택적)
python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# TF-IDF 벡터화
vectorizer = TfidfVectorizer(
    max_features=100,
    tokenizer=okt.nouns,
    max_df=0.8,
    min_df=2
)
tfidf = vectorizer.fit_transform(content_series)

# LDA 토픽 모델링
lda = LatentDirichletAllocation(n_components=5, random_state=42)
lda.fit(tfidf)

# 토픽별 주요 단어
feature_names = vectorizer.get_feature_names_out()
for idx, topic in enumerate(lda.components_):
    top_words = [feature_names[i] for i in topic.argsort()[-10:]]
    print(f"토픽 {idx}: {', '.join(top_words)}")
해석 예시:

토픽 0: 제품, 건강, 영양, 피트라인 → 제품 소개 콘텐츠

토픽 1: 비즈니스, 후원, 가입, 추천인 → 비즈니스 기회 홍보

토픽 2: 변화, 전후, 효과, 만족 → 사용 후기

토픽 3: 세미나, LDS, 참석, 동기 → 이벤트/교육

토픽 4: 일상, 커피, 아침, 루틴 → 라이프스타일

시간 투자: 3-5일, 효과: 중간

Level 3: BERT 기반 분석 (권장하지 않음)
현실적 문제:

KoBERT 학습 시간: 수일~수주

GPU 필요 (Azure VM 비용 급증)

데이터 레이블링 필요 (감정 분석 시 수작업)

결과 해석 어려움

결론:

현 시점에서 BERT는 과잉

Level 1 + Level 2만으로도 충분한 인사이트

BERT는 다음 단계 프로젝트로 미룸

3.5 회귀 분석 (매출 예측)
문제: 매출 데이터가 없음

현재 수집된 데이터에는 판매원별 매출 정보가 없습니다. 따라서 "SNS 활동 → 매출 증대" 상관관계 분석이 불가능합니다.

대안 1: 대리 지표(Proxy Metrics) 사용

python
# 매출 대신 "성공 지표"로 대체
success_proxy = {
    'engagement_score': (
        avg_likes * 0.3 + 
        avg_comments * 0.5 + 
        posts_per_week * 0.2
    ),
    'influence_score': (
        total_posts * 0.2 +
        platform_count * 0.3 +
        recent_activity_ratio * 0.5
    ),
    'business_activity_score': (
        business_keywords_count * 0.4 +
        sponsor_id_presence * 0.6
    )
}

# 이 점수를 종속 변수로 회귀 분석
from sklearn.linear_model import LinearRegression

X = user_features[['posts_per_week', 'avg_engagement_rate', 'platform_count', ...]]
y = user_features['success_proxy_score']

model = LinearRegression()
model.fit(X, y)

# 피처 중요도
importances = pd.DataFrame({
    'feature': X.columns,
    'coefficient': model.coef_
}).sort_values('coefficient', key=abs, ascending=False)

print(importances)
# 예: posts_per_week = 0.35 → 주당 게시물 1개 증가 시 성공점수 0.35 상승
대안 2: 회사에 데이터 요청

text
필요한 데이터:
- 판매원별 월별 매출액
- 신규 가입자 수 (추천인 기준)
- 등급 정보 (SM, MM, VP 등)

개인정보 보호:
- 판매원 ID는 익명화 (HASH 처리)
- 매출은 구간으로 제공 (0-100만원, 100-300만원, ...)
현실적 제안:

다음주 화요일까지는 대리 지표로 분석

장기 계획으로 회사에 매출 데이터 요청 (IRB 승인 필요 가능성)

4. 시스템 아키텍처 설계
4.1 Overall System Architecture
text
┌─────────────────────────────────────────────────────────────────┐
│                    Data Collection Layer                        │
│                   (Crawler VM - 24/7 Active)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Naver   │  │ YouTube  │  │Instagram │  │  Kakao   │       │
│  │  Blog    │  │ Crawler  │  │ Crawler  │  │  Story   │       │
│  │ Crawler  │  │          │  │          │  │ Crawler  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │             │              │
│       └─────────────┴─────────────┴─────────────┘              │
│                           │                                     │
│                   ┌───────▼────────┐                           │
│                   │  Data Merger   │                           │
│                   │  & Validator   │                           │
│                   └───────┬────────┘                           │
│                           │                                     │
│                   ┌───────▼────────┐                           │
│                   │ SQLite (Local) │ ← 임시 저장소            │
│                   └───────┬────────┘                           │
└───────────────────────────┼─────────────────────────────────────┘
                            │ Daily Sync (Cron 02:00)
┌───────────────────────────▼─────────────────────────────────────┐
│                    Data Storage Layer                           │
│                  (Analyst VM - 09:00-16:00)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│              ┌────────────────────────────┐                     │
│              │   PostgreSQL Database      │                     │
│              │                            │                     │
│              │  ┌──────────────────────┐  │                     │
│              │  │ raw_posts            │  │                     │
│              │  │ - 원본 게시물 데이터  │  │                     │
│              │  └──────────────────────┘  │                     │
│              │                            │                     │
│              │  ┌──────────────────────┐  │                     │
│              │  │ processed_posts      │  │                     │
│              │  │ - 정제된 게시물       │  │                     │
│              │  │ - 피처 엔지니어링 결과│  │                     │
│              │  └──────────────────────┘  │                     │
│              │                            │                     │
│              │  ┌──────────────────────┐  │                     │
│              │  │ user_aggregations    │  │                     │
│              │  │ - 판매원별 집계       │  │                     │
│              │  └──────────────────────┘  │                     │
│              │                            │                     │
│              │  ┌──────────────────────┐  │                     │
│              │  │ clustering_results   │  │                     │
│              │  │ - 클러스터 할당       │  │                     │
│              │  └──────────────────────┘  │                     │
│              └────────────────────────────┘                     │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    Analysis Layer                               │
│                 (Jupyter Notebook + Python)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │    EDA      │  │ Clustering  │  │   NLP       │            │
│  │  분석       │  │  & Segment  │  │  분석       │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                    │
│         └────────────────┴────────────────┘                    │
│                          │                                      │
│                  ┌───────▼────────┐                            │
│                  │  결과 저장     │                            │
│                  │  (CSV/JSON)    │                            │
│                  └───────┬────────┘                            │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                  Visualization Layer                            │
│                   (Power BI Dashboard)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Overview    │  │  Clustering  │  │  Trend       │         │
│  │  Dashboard   │  │  Analysis    │  │  Analysis    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  KPI:                                                           │
│  - 총 게시물 수                                                  │
│  - 평균 참여율                                                   │
│  - 클러스터별 분포                                               │
│  - 플랫폼별 활동량                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
4.2 Data Architecture (상세)
sql
-- =====================================================
-- PostgreSQL 스키마 설계
-- =====================================================

-- 1. 원본 게시물 테이블 (Raw Data)
CREATE TABLE raw_posts (
    -- 기본 정보
    post_id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    external_post_id VARCHAR(200) NOT NULL,
    url TEXT NOT NULL UNIQUE,
    
    -- 작성자 정보
    user_id VARCHAR(200) NOT NULL,
    user_name VARCHAR(200),
    
    -- 콘텐츠
    title TEXT,
    content TEXT,
    hashtags JSONB,           -- ["#피엠", "#피트라인", ...]
    
    -- 미디어
    image_urls JSONB,         -- ["url1", "url2", ...]
    video_urls JSONB,
    
    -- 메타데이터
    published_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP DEFAULT NOW(),
    
    -- 통계
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    
    -- 분류
    content_type JSONB,       -- ["Undisclosed_Ad", "QA_Format"]
    
    -- 추가 데이터
    sponsor_phone VARCHAR(50),
    sponsor_id VARCHAR(100),
    
    -- 인덱스
    CONSTRAINT unique_platform_post UNIQUE(platform, external_post_id)
);

CREATE INDEX idx_raw_posts_user ON raw_posts(user_id);
CREATE INDEX idx_raw_posts_platform ON raw_posts(platform);
CREATE INDEX idx_raw_posts_published ON raw_posts(published_at DESC);
CREATE INDEX idx_raw_posts_hashtags ON raw_posts USING GIN (hashtags);


-- 2. 처리된 게시물 테이블 (Processed)
CREATE TABLE processed_posts (
    post_id BIGINT PRIMARY KEY REFERENCES raw_posts(post_id),
    
    -- 파생 피처
    content_length INT,
    hashtag_count INT,
    image_count INT,
    video_count INT,
    
    -- 참여율 계산
    engagement_rate FLOAT,
    engagement_score FLOAT,     -- 정규화된 점수
    
    -- 시간 패턴
    posting_hour INT,
    posting_day_of_week INT,
    is_weekend BOOLEAN,
    
    -- NLP 결과
    top_keywords JSONB,         -- [{"word": "피엠", "count": 5}, ...]
    product_mentions JSONB,     -- {"Activize": 2, "Restorate": 1}
    business_keyword_score INT,
    positive_sentiment_score INT,
    
    -- 콘텐츠 분류 (룰 베이스)
    has_before_after BOOLEAN,
    has_price_mention BOOLEAN,
    has_contact_info BOOLEAN,
    
    processed_at TIMESTAMP DEFAULT NOW()
);


-- 3. 사용자 집계 테이블 (User Level)
CREATE TABLE user_aggregations (
    user_id VARCHAR(200) PRIMARY KEY,
    platform_main VARCHAR(50),      -- 주요 활동 플랫폼
    
    -- 활동 통계
    total_posts INT,
    first_post_date TIMESTAMP,
    last_post_date TIMESTAMP,
    activity_duration_days INT,
    posts_per_week FLOAT,
    avg_posting_interval_days FLOAT,
    
    -- 플랫폼 다양성
    platform_count INT,
    platforms JSONB,                -- ["naver_blog", "youtube"]
    
    -- 콘텐츠 유형 선호도
    undisclosed_ad_ratio FLOAT,
    qa_format_ratio FLOAT,
    video_content_ratio FLOAT,
    
    -- 참여도
    avg_likes_per_post FLOAT,
    avg_comments_per_post FLOAT,
    avg_engagement_rate FLOAT,
    total_engagement_score FLOAT,
    
    -- 콘텐츠 특성
    avg_content_length FLOAT,
    avg_hashtag_count FLOAT,
    hashtag_diversity_score FLOAT,
    
    -- 시간 패턴
    most_active_hour INT,
    weekend_post_ratio FLOAT,
    posting_consistency_score FLOAT,
    
    -- 최근 활동
    recent_30d_posts INT,
    recent_activity_ratio FLOAT,
    
    -- 비즈니스 지표
    avg_business_keyword_score FLOAT,
    has_sponsor_info BOOLEAN,
    
    updated_at TIMESTAMP DEFAULT NOW()
);


-- 4. 클러스터링 결과 테이블
CREATE TABLE clustering_results (
    user_id VARCHAR(200) PRIMARY KEY,
    
    -- 클러스터 할당
    cluster_id INT NOT NULL,
    cluster_name VARCHAR(100),      -- "High Performer", "Casual User" 등
    
    -- 확률 (GMM 사용 시)
    cluster_probability JSONB,      -- [0.8, 0.1, 0.05, 0.05]
    
    -- 클러스터 특성
    cluster_description TEXT,
    
    -- 메타
    clustering_method VARCHAR(50),  -- "kmeans", "hierarchical", "gmm"
    clustering_date TIMESTAMP DEFAULT NOW(),
    model_version VARCHAR(20)
);


-- 5. 분석 로그 테이블
CREATE TABLE analysis_logs (
    log_id BIGSERIAL PRIMARY KEY,
    analysis_type VARCHAR(100),     -- "clustering", "eda", "nlp"
    status VARCHAR(50),             -- "running", "success", "failed"
    parameters JSONB,
    results JSONB,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);


-- =====================================================
-- 뷰 (Views) 정의
-- =====================================================

-- 고성과 판매원 뷰
CREATE VIEW v_high_performers AS
SELECT 
    u.*,
    c.cluster_name
FROM user_aggregations u
JOIN clustering_results c ON u.user_id = c.user_id
WHERE c.cluster_name IN ('High Performer', 'Super Engager')
ORDER BY u.total_engagement_score DESC;


-- 플랫폼별 요약 뷰
CREATE VIEW v_platform_summary AS
SELECT 
    platform,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) as total_posts,
    AVG(engagement_rate) as avg_engagement,
    SUM(like_count) as total_likes,
    SUM(comment_count) as total_comments
FROM raw_posts
GROUP BY platform;


-- 최근 활동 추세 뷰
CREATE VIEW v_recent_trends AS
SELECT 
    DATE_TRUNC('week', published_at) as week,
    platform,
    COUNT(*) as post_count,
    AVG(engagement_rate) as avg_engagement
FROM raw_posts
WHERE published_at >= NOW() - INTERVAL '3 months'
GROUP BY week, platform
ORDER BY week DESC, platform;
4.3 ETL Pipeline (상세)
python
# =====================================================
# ETL 파이프라인 (Daily 실행)
# =====================================================

import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import json

class ETLPipeline:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()
    
    def extract(self):
        """
        Step 1: SQLite에서 신규 데이터 추출
        """
        print("[EXTRACT] SQLite → DataFrame")
        
        # 어제 수집된 데이터만 가져오기
        yesterday = datetime.now() - timedelta(days=1)
        
        df = pd.read_sql(f"""
            SELECT * FROM collected_posts
            WHERE collected_at >= '{yesterday.strftime('%Y-%m-%d')}'
        """, sqlite_conn)
        
        print(f"추출된 레코드: {len(df)}개")
        return df
    
    def transform(self, df):
        """
        Step 2: 데이터 정제 및 피처 엔지니어링
        """
        print("[TRANSFORM] 데이터 정제 및 피처 생성")
        
        # 2.1 기본 정제
        df = df.dropna(subset=['url', 'content'])
        df = df.drop_duplicates(subset=['url'])
        
        # 2.2 파생 피처
        df['content_length'] = df['content'].str.len()
        df['hashtag_count'] = df['hashtags'].apply(
            lambda x: len(json.loads(x)) if pd.notna(x) else 0
        )
        df['image_count'] = df['image_urls'].apply(
            lambda x: len(json.loads(x)) if pd.notna(x) else 0
        )
        
        # 2.3 engagement_rate 계산
        df['engagement_rate'] = (
            (df['like_count'] + df['comment_count']) / 
            df['view_count'].replace(0, 1)
        )
        
        # 2.4 시간 피처
        df['published_at'] = pd.to_datetime(df['published_at'])
        df['posting_hour'] = df['published_at'].dt.hour
        df['posting_day_of_week'] = df['published_at'].dt.dayofweek
        df['is_weekend'] = df['posting_day_of_week'] >= 5
        
        # 2.5 NLP 간단 처리
        df = self._simple_nlp_features(df)
        
        print(f"변환 완료: {len(df)}개")
        return df
    
    def _simple_nlp_features(self, df):
        """간단한 NLP 피처"""
        from konlpy.tag import Okt
        okt = Okt()
        
        def extract_features(content):
            if pd.isna(content):
                return {}
            
            # 제품명 언급
            products = ['피트라인', 'FitLine', 'Activize', 'Restorate']
            product_count = sum(content.count(p) for p in products)
            
            # 비즈니스 키워드
            business_kw = ['추천인', '후원', '가입', '비즈니스', '부업']
            business_score = sum(1 for kw in business_kw if kw in content)
            
            # 긍정 키워드
            positive_kw = ['좋아', '최고', '만족', '추천', '효과']
            positive_score = sum(1 for kw in positive_kw if kw in content)
            
            return {
                'product_mentions': product_count,
                'business_keyword_score': business_score,
                'positive_sentiment_score': positive_score
            }
        
        nlp_features = df['content'].apply(extract_features)
        df = pd.concat([df, pd.DataFrame(nlp_features.tolist())], axis=1)
        
        return df
    
    def load_raw(self, df):
        """
        Step 3: PostgreSQL raw_posts 테이블에 적재
        """
        print("[LOAD] DataFrame → PostgreSQL (raw_posts)")
        
        # Upsert (중복 시 업데이트)
        for _, row in df.iterrows():
            try:
                self.cursor.execute("""
                    INSERT INTO raw_posts (
                        platform, external_post_id, url, user_id, 
                        title, content, hashtags, image_urls, video_urls,
                        published_at, like_count, comment_count, view_count,
                        content_type, sponsor_phone, sponsor_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET
                        like_count = EXCLUDED.like_count,
                        comment_count = EXCLUDED.comment_count,
                        view_count = EXCLUDED.view_count
                """, (
                    row['platform'], row['post_id'], row['url'], row['user_id'],
                    row['title'], row['content'], 
                    json.dumps(row['hashtags']) if pd.notna(row['hashtags']) else None,
                    json.dumps(row['image_urls']) if pd.notna(row['image_urls']) else None,
                    json.dumps(row['video_urls']) if pd.notna(row['video_urls']) else None,
                    row['published_at'], row['like_count'], row['comment_count'], 
                    row.get('view_count', 0), 
                    json.dumps(row['content_type']) if pd.notna(row['content_type']) else None,
                    row.get('sponsor_phone'), row.get('sponsor_id')
                ))
            except Exception as e:
                print(f"Error inserting {row['url']}: {e}")
        
        self.conn.commit()
        print(f"적재 완료: {len(df)}개")
    
    def load_processed(self, df):
        """
        Step 4: processed_posts 테이블에 피처 적재
        """
        print("[LOAD] 피처 → PostgreSQL (processed_posts)")
        
        # raw_posts에서 post_id 가져오기
        for _, row in df.iterrows():
            post_id = self._get_post_id(row['url'])
            if not post_id:
                continue
            
            self.cursor.execute("""
                INSERT INTO processed_posts (
                    post_id, content_length, hashtag_count, image_count, video_count,
                    engagement_rate, posting_hour, posting_day_of_week, is_weekend,
                    product_mentions, business_keyword_score, positive_sentiment_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (post_id) DO UPDATE SET
                    engagement_rate = EXCLUDED.engagement_rate,
                    product_mentions = EXCLUDED.product_mentions
            """, (
                post_id, row['content_length'], row['hashtag_count'],
                row['image_count'], row.get('video_count', 0),
                row['engagement_rate'], row['posting_hour'],
                row['posting_day_of_week'], row['is_weekend'],
                row.get('product_mentions', 0), row.get('business_keyword_score', 0),
                row.get('positive_sentiment_score', 0)
            ))
        
        self.conn.commit()
        print("피처 적재 완료")
    
    def aggregate_users(self):
        """
        Step 5: 사용자별 집계 (user_aggregations 갱신)
        """
        print("[AGGREGATE] 사용자별 집계 계산")
        
        self.cursor.execute("""
            INSERT INTO user_aggregations (
                user_id, platform_main, total_posts, first_post_date, last_post_date,
                activity_duration_days, posts_per_week, platform_count,
                avg_likes_per_post, avg_comments_per_post, avg_engagement_rate,
                avg_content_length, avg_hashtag_count
            )
            SELECT 
                r.user_id,
                MODE() WITHIN GROUP (ORDER BY r.platform) as platform_main,
                COUNT(*) as total_posts,
                MIN(r.published_at) as first_post_date,
                MAX(r.published_at) as last_post_date,
                EXTRACT(DAY FROM MAX(r.published_at) - MIN(r.published_at)) as activity_duration_days,
                COUNT(*)::FLOAT / NULLIF(EXTRACT(DAY FROM MAX(r.published_at) - MIN(r.published_at)) / 7.0, 0) as posts_per_week,
                COUNT(DISTINCT r.platform) as platform_count,
                AVG(r.like_count) as avg_likes_per_post,
                AVG(r.comment_count) as avg_comments_per_post,
                AVG(p.engagement_rate) as avg_engagement_rate,
                AVG(p.content_length) as avg_content_length,
                AVG(p.hashtag_count) as avg_hashtag_count
            FROM raw_posts r
            LEFT JOIN processed_posts p ON r.post_id = p.post_id
            GROUP BY r.user_id
            ON CONFLICT (user_id) DO UPDATE SET
                total_posts = EXCLUDED.total_posts,
                last_post_date = EXCLUDED.last_post_date,
                posts_per_week = EXCLUDED.posts_per_week,
                avg_engagement_rate = EXCLUDED.avg_engagement_rate,
                updated_at = NOW()
        """)
        
        self.conn.commit()
        print("사용자 집계 완료")
    
    def _get_post_id(self, url):
        """URL로 post_id 조회"""
        self.cursor.execute("SELECT post_id FROM raw_posts WHERE url = %s", (url,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def run(self):
        """전체 파이프라인 실행"""
        try:
            print(f"=== ETL 파이프라인 시작 ({datetime.now()}) ===")
            
            # 1. Extract
            df = self.extract()
            
            # 2. Transform
            df_transformed = self.transform(df)
            
            # 3. Load Raw
            self.load_raw(df_transformed)
            
            # 4. Load Processed
            self.load_processed(df_transformed)
            
            # 5. Aggregate Users
            self.aggregate_users()
            
            print("=== ETL 파이프라인 완료 ===")
            
        except Exception as e:
            print(f"❌ ETL 실패: {e}")
            self.conn.rollback()
        finally:
            self.cursor.close()
            self.conn.close()


# Cron 스케줄링 (매일 새벽 2시 실행)
# crontab -e
# 0 2 * * * /usr/bin/python3 /home/azureuser/etl_pipeline.py >> /var/log/etl.log 2>&1
4.4 Information Architecture
text
PM SNS 분석 프로젝트 - Information Architecture
==================================================

1. 데이터 계층 (Data Layer)
   ├─ Raw Data (원본)
   │  ├─ 네이버 블로그 게시물
   │  ├─ 유튜브 영상 메타데이터
   │  ├─ 카카오스토리 포스트
   │  ├─ 인스타그램 게시물
   │  └─ 이미지/영상 URL
   │
   ├─ Processed Data (가공)
   │  ├─ 정제된 텍스트
   │  ├─ 파생 피처 (참여율, 콘텐츠 길이 등)
   │  └─ NLP 분석 결과
   │
   ├─ Aggregated Data (집계)
   │  ├─ 사용자별 활동 통계
   │  ├─ 플랫폼별 요약
   │  └─ 시계열 추세
   │
   └─ Analysis Results (분석)
      ├─ 클러스터링 결과
      ├─ 토픽 모델링 결과
      └─ 상관관계 분석 결과

2. 비즈니스 인텔리전스 계층 (BI Layer)
   ├─ KPI 정의
   │  ├─ 총 게시물 수
   │  ├─ 평균 참여율
   │  ├─ 활성 판매원 수
   │  └─ 플랫폼별 활동 비중
   │
   ├─ 세그먼트 정의
   │  ├─ 고성과 판매원 (High Performer)
   │  ├─ 중간 활동자 (Moderate User)
   │  ├─ 비활성 판매원 (Inactive)
   │  └─ 신규 판매원 (Newbie)
   │
   └─ 인사이트 카테고리
      ├─ 플랫폼 효과성 비교
      ├─ 콘텐츠 유형별 참여율
      ├─ 시간대별 활동 패턴
      └─ 성공 요인 분석

3. 사용자 인터페이스 계층 (UI Layer)
   ├─ Power BI 대시보드
   │  ├─ 개요 페이지 (Overview)
   │  │  ├─ 주요 KPI 카드
   │  │  ├─ 플랫폼별 활동 차트
   │  │  └─ 최근 추세 그래프
   │  │
   │  ├─ 클러스터 분석 페이지
   │  │  ├─ 클러스터별 특성 비교
   │  │  ├─ 판매원 분포 시각화
   │  │  └─ 클러스터 이동 추적
   │  │
   │  ├─ 콘텐츠 분석 페이지
   │  │  ├─ 콘텐츠 유형 분포
   │  │  ├─ 워드 클라우드
   │  │  └─ 해시태그 네트워크
   │  │
   │  └─ 개별 판매원 상세 페이지
   │     ├─ 활동 타임라인
   │     ├─ 참여율 추세
   │     └─ 콘텐츠 갤러리
   │
   └─ 정적 리포트 (PDF/Excel)
      ├─ 월간 활동 요약 리포트
      ├─ 클러스터 프로파일 리포트
      └─ 권장사항 리포트

4. 메타데이터 (Metadata Layer)
   ├─ 데이터 사전 (Data Dictionary)
   │  └─ 각 컬럼의 정의, 타입, 예시
   │
   ├─ 비즈니스 용어집 (Business Glossary)
   │  ├─ 참여율 (Engagement Rate)
   │  ├─ 활성 판매원 (Active Team Partner)
   │  └─ 콘텐츠 유형 (Content Type)
   │
   └─ 데이터 계보 (Data Lineage)
      └─ 크롤링 → 정제 → 집계 → 분석 → 시각화 흐름도

5. 거버넌스 (Governance)
   ├─ 데이터 품질 기준
   │  ├─ 완전성 (Completeness): 필수 필드 채움률 > 95%
   │  ├─ 정확성 (Accuracy): URL 유효성 > 99%
   │  └─ 최신성 (Freshness): 수집 주기 24시간 이내
   │
   ├─ 접근 권한
   │  ├─ 관리자: 모든 데이터 + DB 수정 권한
   │  ├─ 분석가: 읽기 전용 + 분석 스크립트 실행
   │  └─ 경영진: Power BI 대시보드만
   │
   └─ 개인정보 보호
      ├─ 전화번호 마스킹 (끝 4자리만)
      ├─ 블로거 이름 익명화 (해시 처리)
      └─ 공개 데이터만 수집 (로그인 필요 데이터 제외)
5. 다음주 화요일까지 실행 계획 (1주 + 1일)
5.1 우선순위 조정
현실 체크:

✅ 네이버 블로그, 카카오스토리: 데이터 수집 완료

🟡 유튜브, 인스타그램: 70% 완료 (멀티미디어 이슈)

🔴 네이버 카페, 페이스북: 20% (시간 부족)

전략적 결정:

text
집중할 것 (Must Have):
  ✅ 네이버 블로그 + 카카오스토리 완성도 100%
  ✅ DB 구축 (PostgreSQL)
  ✅ 사용자별 피처 집계
  ✅ 기본 클러스터링 + 시각화
  ✅ Power BI 대시보드 v1.0

포기할 것 (Nice to Have):
  ❌ 네이버 카페, 페이스북 수집 (다음 단계로 연기)
  ❌ BERT 기반 NLP (오버킬)
  ❌ 실시간 스트리밍 (배치만)
  ❌ 완벽한 멀티미디어 처리 (best-effort로)
5.2 Day-by-Day 실행 계획
Day 1 (수요일): 크롤링 마무리 + Git 정리
오전 (김호연):

 네이버 블로그 크롤러 버그 수정 (해시태그 필터링)

 유튜브 크롤러 fallback 로직 추가 (자막 API → 메타데이터)

 Git 브랜치 정리 (feature/naver-blog, feature/youtube)

오전 (권서연):

 카카오스토리 크롤러 최종 검증

 인스타그램 슬라이드 앨범 이슈 우회 (첫 이미지만 수집)

 Git 브랜치 정리

오후 (공동):

 크롤링 통합 스크립트 작성 (main_crawler.py)

 Crawler VM 설정 및 Cron 등록

 테스트 실행 (각 플랫폼 10개씩)

산출물:

main_crawler.py (통합 크롤러)

Cron 스케줄 설정 완료

Git 커밋 로그 정리

Day 2 (목요일): DB 구축
오전 (김호연):

 Azure VM에 PostgreSQL 설치

bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
 데이터베이스 및 사용자 생성

sql
CREATE DATABASE pmik_sns;
CREATE USER pmik_user WITH PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE pmik_sns TO pmik_user;
 스키마 생성 (위 4.2 SQL 실행)

오후 (공동):

 ETL 파이프라인 코드 작성 (etl_pipeline.py)

 네이버 블로그 데이터 → PostgreSQL 적재 테스트

 카카오스토리 데이터 → PostgreSQL 적재 테스트

산출물:

PostgreSQL 구축 완료

스키마 DDL 파일 (schema.sql)

ETL 파이프라인 v1.0

Day 3 (금요일): 피처 엔지니어링
오전 (권서연):

 processed_posts 테이블 채우기

파생 피처 계산 (content_length, hashtag_count 등)

시간 피처 추출 (posting_hour, is_weekend)

오후 (김호연):

 간단한 NLP 피처 추가 (제품명 언급, 비즈니스 키워드)

 user_aggregations 테이블 생성 및 채우기

저녁 (공동):

 데이터 품질 검증

결측치 확인

이상치 탐지 (engagement_rate > 1인 경우 등)

 피처 간 상관관계 확인

산출물:

피처 엔지니어링 스크립트 (feature_engineering.py)

데이터 품질 리포트 (data_quality_report.txt)

Day 4-5 (주말): 클러스터링 및 EDA
토요일 (김호연):

 사용자 레벨 데이터 추출

python
user_df = pd.read_sql("SELECT * FROM user_aggregations", conn)
 클러스터링 실행

K-Means (k=4)

Hierarchical Clustering

결과 비교 및 최종 선택

 클러스터별 프로파일 작성

text
Cluster 0: 고성과 (High Performer)
  - posts_per_week: 5.2
  - avg_engagement_rate: 0.08
  - 특징: 멀티 플랫폼, 일관된 활동

Cluster 1: 중간 활동자 (Moderate User)
  ...
일요일 (권서연):

 EDA Jupyter Notebook 작성

플랫폼별 게시물 분포

시간대별 활동 패턴

콘텐츠 유형별 참여율

해시태그 빈도 분석

 워드 클라우드 생성

 인사이트 요약 작성

산출물:

클러스터링 결과 저장 (clustering_results 테이블 채워짐)

EDA 노트북 (eda_analysis.ipynb)

워드 클라우드 이미지

Day 6-7 (월-화): 대시보드 + 보고서 작성
월요일 (김호연):

 Power BI Desktop 설치

 PostgreSQL 연결 설정

 페이지 1: Overview Dashboard

KPI 카드 (총 게시물, 평균 참여율, 활성 판매원 수)

플랫폼별 게시물 수 (파이 차트)

시간 추세 (라인 차트)

월요일 (권서연):

 페이지 2: Cluster Analysis

클러스터별 특성 비교 (레이더 차트)

판매원 분포 (산점도)

 페이지 3: Content Analysis

콘텐츠 유형 분포 (막대 차트)

해시태그 TOP 20 (워드 클라우드)

화요일 오전 (공동):

 Power BI 대시보드 최종 점검

 PDF 리포트 생성 (Power BI → Export)

 보고서 작성

프로젝트 개요

데이터 수집 현황

주요 인사이트

클러스터 프로파일

향후 계획

화요일 오후:

 발표 자료 준비 (PPT)

 리허설

산출물:

Power BI 대시보드 파일 (.pbix)

월간 리포트 (PDF)

발표 자료 (PPT)

GitHub 저장소 정리

5.3 역할 분담 명확화
작업	담당자	백업
네이버 블로그 크롤링	김호연	-
유튜브 크롤링	김호연	-
카카오스토리 크롤링	권서연	-
인스타그램 크롤링	권서연	-
DB 구축 (PostgreSQL)	김호연	-
ETL 파이프라인	김호연	권서연
피처 엔지니어링	권서연	-
클러스터링	김호연	-
EDA	권서연	-
Power BI 대시보드 (Page 1-2)	김호연	-
Power BI 대시보드 (Page 3)	권서연	-
보고서 작성	공동	-
6. AI 모델 개발 로드맵 (장기 계획)
현재 프로젝트에서는 기본 분석까지만 완료하고, AI 모델은 Phase 2로 연기하는 것을 권장합니다.

Phase 1 (현재 ~ 다음주): 기초 구축
✅ 데이터 수집 자동화

✅ DB 및 ETL 파이프라인

✅ 기본 클러스터링

✅ Power BI 대시보드

Phase 2 (1-2개월 후): 고급 분석
🎯 감성 분석 (Sentiment Analysis)

KoBERT 미세 조정 (Fine-tuning)

긍정/부정/중립 분류

필요 데이터: 수작업 레이블링 500-1000개

예상 시간: 2-3주

🎯 추천 시스템 (Recommendation)

"이 판매원과 유사한 성공 사례"

협업 필터링 (Collaborative Filtering)

🎯 시계열 예측 (Time Series Forecasting)

ARIMA, Prophet

"다음 달 게시물 수 예측"

Phase 3 (3-6개월 후): 고급 AI
🚀 이탈 예측 모델 (Churn Prediction)

"이 판매원이 90일 내 비활성화될 확률 80%"

로지스틱 회귀, XGBoost

필요 데이터: 판매원 등급, 매출, 팀 구조

🚀 NLP 기반 허위 광고 탐지

법적 리스크 자동 플래깅

BERT + 규칙 기반 하이브리드

🚀 최적 게시 시간 추천

강화학습 (Reinforcement Learning)

"이 판매원은 화요일 오후 7시에 게시하면 참여율 +30%"

7. 최종 권고사항
7.1 즉시 실행할 것 (This Week)
Git 버전 관리 강화

모든 작업은 브랜치에서

커밋 단위를 작게

Claude 사용 시 한 번에 하나씩만 수정 요청

멀티미디어 처리 포기하지 말 것

YouTube 자막 API 우선

Whisper는 best-effort

실패한 것은 메타데이터만 저장

DB는 PostgreSQL + VM 직접 설치

Blob Storage 불필요 (현 데이터 규모)

NoSQL 불필요 (PostgreSQL JSONB로 충분)

범위 축소

네이버 블로그 + 카카오스토리에 집중

네이버 카페, 페이스북은 다음 단계

클러스터링 개선

K-Means뿐만 아니라 Hierarchical도 시도

클러스터별 프로파일 작성 필수

NLP는 간단하게

제품명 언급, 비즈니스 키워드 카운팅만

BERT는 나중에

7.2 상무님께 보고할 내용
긍정적 측면 강조:

✅ 네이버 블로그, 카카오스토리 데이터 수집 완료 (12,000+ 게시물)

✅ 데이터 품질 우수 (평균 본문 1,672자, 구조화 잘됨)

✅ 초기 EDA 및 클러스터링 성공적

✅ Power BI 대시보드 프로토타입 완성

솔직한 현황 공유:

⚠️ 멀티미디어 처리 (OCR, Whisper)는 기술적 한계로 70% 완성도

⚠️ 매출 데이터 없어 직접적 ROI 분석 불가 (대리 지표 사용)

⚠️ 페이스북, 네이버 카페는 시간 부족으로 Phase 2로 연기

향후 계획 제시:

🎯 다음주까지: DB 구축 + 클러스터링 + 대시보드 완성

🎯 1개월 후: 멀티미디어 처리 개선 + 추가 플랫폼 수집

🎯 3개월 후: AI 모델 개발 (이탈 예측, 허위 광고 탐지)

데이터 요청:

📊 판매원별 월별 매출 (익명화 OK)

📊 판매원 등급 정보 (SM, MM, VP 등)

📊 추천인 관계 (네트워크 분석용)

7.3 학습 자료 추천
디버깅 효율화:

"The Pragmatic Programmer" (실용주의 프로그래머)

Git 튜토리얼: https://learngitbranching.js.org/

DB 설계:

"Database Design for Mere Mortals" (초보자를 위한 DB 설계)

PostgreSQL 공식 문서: https://www.postgresql.org/docs/

클러스터링:

Scikit-learn 클러스터링 가이드

"Python Machine Learning" (Sebastian Raschka)

Power BI:

Microsoft Power BI 공식 학습 경로

YouTube: "Guy in a Cube" 채널

NLP 기초:

"밑바닥부터 시작하는 딥러닝 2" (자연어 처리 편)

KoNLPy 문서: https://konlpy.org/

8. 보고서 작성 (다음주 화요일 제출용)
위 내용을 바탕으로 아래와 같은 구조의 보고서를 작성하겠습니다:이제 프로젝트의 전체적인 현황과 문제점을 파악했습니다. 체계적인 분석과 해결방안을 제시하겠습니다.

Deep Thinking을 통해 포괄적인 보고서를 작성하겠습니다.

PM 판매원 SNS 분석 프로젝트 중간점검 보고서
📋 Executive Summary
프로젝트 기간: 2025년 9월 ~ 12월 (현재 3주 잔여)
현재 단계: 데이터 수집 80% 완료, 분석 20% 완료
핵심 과제: 크롤링 안정화, DB 구축, 주요 피처 추출, 분석 파이프라인 구축

1. 현황 분석
1.1 데이터 수집 현황
플랫폼	수집 건수	진행률	주요 문제점
네이버 블로그	7,890건 (261건 정제)	✅ 90%	노이즈 필터링 필요, OCR 미구현
카카오스토리	4,769건	✅ 85%	데이터 품질 양호
유튜브	376건	⚠️ 60%	Whisper 음성인식 불안정
인스타그램	~300건	⚠️ 50%	URL 임시전용 문제, 슬라이드 수집 불가
네이버 카페	테스트 중	⏳ 10%	로그인 기능 구현 중
총 수집량: 약 13,335건 (중복 제거 전)
데이터 용량: 약 1.5GB (이미지/동영상 포함 시 예상 5-10GB)

1.2 데이터 품질 분석
네이버 블로그 데이터 (샘플 261건 기준)

✅ 양호 컬럼: title (96.5% 수집), content (100%), hashtags (90.4%)

⚠️ 문제 컬럼:

profile_nickname (0% 수집)

image_ocr_text (0% 수집)

sponsor_phone (17.2% 수집)

content_sponsor_id (22.6% 수집)

📊 콘텐츠 분석:

평균 본문 길이: 1,672자

평균 해시태그 수: 10-15개

주요 콘텐츠 타입: Undisclosed_Ad (36.8%), QA_Format (24.1%)

2. 핵심 문제점 및 해결방안
2.1 크롤링 버그 및 디버깅 전략
❌ 현재 문제
Claude 기반 반복 디버깅으로 이전 버그가 재발

코드 일관성 부족으로 작업 완성도 저하

버전 관리 부재로 변경 이력 추적 불가

✅ 해결 방안
1) 체계적인 개발 워크플로우 구축

text
[단계별 개발 프로세스]

Step 1: 문제 정의 (5분)
├─ 정확한 에러 메시지 수집
├─ 재현 가능한 테스트 케이스 작성
└─ 예상 원인 가설 수립

Step 2: AI 활용 최적화 (10-15분)
├─ Claude에게 제공할 컨텍스트 구조화
│   ├─ 에러 로그 전체 (스택 트레이스 포함)
│   ├─ 문제 발생 코드 블록 (주변 10줄 포함)
│   ├─ 입력 데이터 샘플 (실제 데이터)
│   └─ 기대 출력 vs 실제 출력
│
├─ 프롬프트 템플릿 사용
│   "다음 Python 코드에서 [구체적 문제]가 발생합니다.
│    에러: [정확한 에러 메시지]
│    입력: [샘플 데이터]
│    기대 출력: [예상 결과]
│    실제 출력: [현재 결과]
│    
│    [조건]
│    - 기존 함수 구조 유지
│    - 다른 모듈과의 호환성 보장
│    - 변경 부분만 하이라이트"
│
└─ 솔루션 검증 체크리스트 요구
    ├─ 변경 사항 요약
    ├─ 테스트 케이스 제공
    └─ 잠재적 부작용 경고

Step 3: 버전 관리 (5분)
├─ Git 커밋 (의미 있는 메시지)
│   예: "fix: 네이버 블로그 iframe 감지 로직 개선"
├─ CHANGELOG.md 업데이트
└─ 작동 확인된 버전 태깅

Step 4: 테스트 (10분)
├─ 단위 테스트 (함수별)
├─ 통합 테스트 (전체 파이프라인)
└─ 회귀 테스트 (이전 버그 재발 확인)
2) 코드 구조화 및 모듈화

python
# 권장 프로젝트 구조
pm-sns-crawler/
├─ config/
│   ├─ settings.py          # 설정 중앙화
│   └─ constants.py         # 상수 관리
├─ crawlers/
│   ├─ base_crawler.py      # 공통 로직 추상화
│   ├─ naver_blog.py
│   ├─ youtube.py
│   └─ ...
├─ processors/
│   ├─ ocr_processor.py
│   ├─ video_processor.py
│   └─ text_processor.py
├─ utils/
│   ├─ logger.py            # 로깅 유틸
│   ├─ retry.py             # 재시도 로직
│   └─ validators.py        # 데이터 검증
├─ tests/                   # 테스트 코드
│   ├─ test_naver.py
│   └─ ...
└─ main.py                  # 실행 진입점
3) 효과적인 AI 툴 활용 전략

작업 유형	추천 툴	사용 목적
초기 코드 작성	Claude 3.5 Sonnet	복잡한 로직 설계, 아키텍처 구상
디버깅	Windsurf (Cascade)	실시간 코드 수정, 빠른 iteration
코드 리뷰	Claude Code (Cursor)	코드 품질 검증, 리팩토링 제안
반복 작업	GitHub Copilot	보일러플레이트 코드 생성
문서화	Gemini 3.0 Pro	주석, README 작성
추가 추천:

Cursor IDE: 코드베이스 전체를 이해하는 AI 어시스턴트

Replit Agent: 빠른 프로토타이핑

Codeium: 무료 대안 (GPT-4 수준)

2.2 멀티미디어 처리 개선
❌ 현재 문제: Whisper 음성 인식 불안정
원인 분석:

URL 문제:

임시 URL (1회용 토큰) 수집

재생 시 만료되어 접근 불가

오디오 품질:

영상 음소거 상태

배경음악/노이즈 과다

화자 중복 (여러 명 동시 발화)

Whisper 모델 한계:

한국어 전사 정확도: Base 모델 75-85%

전문 용어 (FitLine, PM 등) 오인식

방언/억양 처리 약함

✅ 해결 방안
1) 다층 음성 인식 전략

python
# 개선된 음성 인식 파이프라인
class ImprovedAudioProcessor:
    def __init__(self):
        # 1차: 빠르고 저렴한 옵션
        self.whisper_model = whisper.load_model("small")  # base → small
        
        # 2차: 고정밀 옵션 (실패 시)
        self.google_stt = speech_v1.SpeechClient()
        
        # 3차: 특화 모델 (한국어 강화)
        self.clova_stt = ClovaSpeechClient()
    
    def transcribe_with_fallback(self, audio_path):
        # Strategy 1: Whisper (빠름, 무료)
        try:
            result = self.whisper_model.transcribe(
                audio_path,
                language="ko",
                task="transcribe",
                fp16=False,  # CPU 호환성
                condition_on_previous_text=False,  # 문맥 의존성 제거
                temperature=0.0,  # 결정론적 출력
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                initial_prompt="FitLine, PM인터내셔널, 건강기능식품"  # 도메인 힌트
            )
            
            if self._is_valid_transcription(result["text"]):
                return {"method": "whisper", "text": result["text"]}
        except:
            pass
        
        # Strategy 2: Google Speech-to-Text (정확, 유료)
        try:
            audio = self._load_audio_for_google(audio_path)
            config = speech_v1.RecognitionConfig(
                encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ko-KR",
                alternative_language_codes=["en-US"],  # 영어 혼재 대응
                enable_automatic_punctuation=True,
                model="video",  # 동영상 최적화 모델
                use_enhanced=True
            )
            response = self.google_stt.recognize(config=config, audio=audio)
            
            if response.results:
                text = " ".join([r.alternatives[0].transcript 
                                for r in response.results])
                return {"method": "google", "text": text}
        except:
            pass
        
        # Strategy 3: Naver Clova (한국어 특화, 무료 한도 있음)
        try:
            response = self.clova_stt.transcribe(audio_path)
            return {"method": "clova", "text": response["text"]}
        except:
            pass
        
        return {"method": "none", "text": ""}
    
    def _is_valid_transcription(self, text):
        """전사 품질 검증"""
        if not text or len(text) < 10:
            return False
        
        # 반복 패턴 감지 (Whisper 환각 증상)
        words = text.split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # 반복률 70% 이상
                return False
        
        return True
2) 음성 전처리 최적화

python
import pydub
from pydub import AudioSegment
from pydub.effects import normalize

def preprocess_audio(input_path, output_path):
    """Whisper 성능 향상을 위한 오디오 전처리"""
    audio = AudioSegment.from_file(input_path)
    
    # 1. 샘플레이트 정규화 (Whisper 권장: 16kHz)
    audio = audio.set_frame_rate(16000)
    
    # 2. 모노 변환
    audio = audio.set_channels(1)
    
    # 3. 볼륨 정규화 (너무 작거나 큰 소리 보정)
    audio = normalize(audio)
    
    # 4. 무음 구간 제거 (앞뒤 1초 이상 무음)
    audio = audio.strip_silence(
        silence_len=1000,    # 1초
        silence_thresh=-40   # dBFS
    )
    
    # 5. 16-bit PCM 포맷 (Whisper 호환)
    audio.export(
        output_path,
        format="wav",
        parameters=["-ar", "16000", "-ac", "1", "-sample_fmt", "s16"]
    )
    
    return output_path
3) URL 수집 개선 (영구 URL 확보)

python
# YouTube 영구 URL 확보
def get_permanent_youtube_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"

# Instagram 영구 미디어 URL 확보 (Graph API)
def get_instagram_media_url(post_id, access_token):
    url = f"https://graph.instagram.com/{post_id}"
    params = {
        "fields": "media_url,media_type,thumbnail_url",
        "access_token": access_token
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # 영구 URL 저장 또는 즉시 다운로드
    if data.get("media_type") == "VIDEO":
        download_and_save(data["media_url"], f"{post_id}.mp4")
        return f"local_storage/{post_id}.mp4"
    
    return data.get("media_url")
4) 대안 솔루션 비교

솔루션	정확도 (한국어)	비용	속도	추천 사용
Whisper (Small)	80-85%	무료	2초/분	1차 시도 (대량 처리)
OpenAI Whisper API	90-95%	$0.006/분	1초/분	예산 여유 시
Google STT	92-96%	$0.024/분	0.5초/분	중요 콘텐츠
Naver Clova	95-98%	무료 (10만자) → 유료	1초/분	한국어 특화 콘텐츠
Azure Speech	90-94%	$1/시간	0.8초/분	Azure 환경 통합 시
AssemblyAI	88-92%	$0.00025/초	1초/분	화자 구분 필요 시
최종 권장 전략:

1단계: Whisper Small 모델 (전처리 포함) → 80% 커버

2단계: Naver Clova (무료 한도 내) → 15% 커버

3단계: Google STT (중요 콘텐츠만) → 5% 커버

예상 비용 (유튜브 376건, 평균 5분 영상 가정):

Whisper: $0 (Self-hosted)

Clova: ~$0 (무료 한도 내)

Google STT: 376 × 5분 × $0.024 = 약 $45

2.3 데이터베이스 설계 및 구축
❓ "DB를 구축한다"는 것의 의미
DB 구축은 데이터의 영구 저장, 효율적 조회, 일관성 유지, 분석 지원을 위한 시스템을 만드는 것입니다.

구체적 단계:

데이터 모델링: 엔티티 관계 설계 (ERD)

스키마 정의: 테이블 구조, 컬럼 타입, 제약조건

인덱스 최적화: 쿼리 성능 향상

데이터 적재: ETL 파이프라인 구축

권한 관리: 접근 제어 및 보안

백업/복구: 데이터 안전성 확보

❌ 현재 계획의 문제점
원래 계획: VM 로컬 → Blob Storage → PostgreSQL/Supabase

문제점:

과도한 아키텍처: 현재 데이터 규모 (5-10GB)에 비해 복잡

비용 비효율: Blob Storage 단계가 불필요 (중간 단계 증가)

SQL vs NoSQL 혼란: 상무님 요청 (NoSQL)과 계획 (PostgreSQL) 불일치

✅ 개선된 DB 아키텍처
1) 데이터 규모 및 특성 분석

text
[현재 데이터]
- 총량: ~13,000건 (중복 제거 후 ~8,000건 예상)
- 용량: 텍스트 1.5GB + 멀티미디어 3-8GB = 약 5-10GB
- 성장률: 월 500-1,000건 추가 (자동화 후)
- 연간 예상: ~20GB

[특성]
✅ 구조화된 메타데이터 (JSON 일부 포함)
✅ 복잡한 JOIN 쿼리 필요 (사용자-게시물-성과 분석)
✅ 집계 쿼리 빈번 (대시보드, 리포트)
⚠️ 일부 비정형 데이터 (해시태그 배열, OCR 텍스트)
결론: 하이브리드 접근 - PostgreSQL (메인) + JSON 컬럼 활용

2) 최적 DB 선택: PostgreSQL (with JSONB)

PostgreSQL을 선택하는 이유:

요구사항	PostgreSQL	MongoDB (NoSQL)	Azure Cosmos DB
구조화된 쿼리	✅ Excellent (SQL)	⚠️ Limited (Aggregation)	⚠️ Limited
JOIN 성능	✅ Optimized	❌ Poor	❌ Poor
JSON 지원	✅ JSONB (인덱싱 가능)	✅ Native	✅ Native
집계 분석	✅ Window Functions	⚠️ Map-Reduce	⚠️ Limited
비용 (Azure)	$50-100/월	$100-200/월	$200-400/월
ML 통합	✅ Python, R 연동 우수	⚠️ 추가 작업	⚠️ 추가 작업
Power BI 연동	✅ Native Connector	⚠️ ODBC 필요	✅ Native
NoSQL을 선택하지 않는 이유:

우리 데이터는 대부분 구조화되어 있음 (플랫폼, 게시물 ID, 날짜 등)

복잡한 관계형 쿼리 필요 (사용자-성과 연결)

NoSQL의 강점(스케일아웃, 유연한 스키마)이 현재 규모에선 불필요

3) 간소화된 데이터 흐름

text
[개선된 아키텍처]

┌──────────────┐
│ 크롤러 (VM)  │
│  - Python    │
│  - Selenium  │
└──────┬───────┘
       │ (1) 크롤링
       │ JSON/CSV 생성
       ▼
┌──────────────────────┐
│ 전처리 (VM)          │
│  - OCR               │
│  - 음성인식          │
│  - 데이터 정제       │
└──────┬───────────────┘
       │ (2) 처리된 데이터
       │
       ▼
┌──────────────────────────────┐
│ PostgreSQL (Azure)           │
│  - 메인 DB                   │
│  - JSONB 컬럼 (비정형 데이터)│
└──────┬───────────────────────┘
       │ (3) 쿼리
       │
       ├──────┬──────┬─────────┐
       ▼      ▼      ▼         ▼
   ┌─────┐ ┌────┐ ┌──────┐ ┌─────┐
   │Python│ │Pandas│ │PowerBI│ │Excel│
   │분석 │ │처리│ │대시보드│ │리포트│
   └─────┘ └────┘ └──────┘ └─────┘

[선택적: 멀티미디어 분리 저장]
크롤러 → Azure Blob Storage (이미지/영상 원본)
                ↓
         URL만 PostgreSQL에 저장
Blob Storage를 언제 사용하나?

✅ 이미지/영상 원본 파일 보관 (장기 아카이빙)

✅ OCR/음성인식 재처리 대비

❌ 일차적 데이터 저장소로 사용 (불필요)

4) PostgreSQL 스키마 설계

sql
-- ============================================
-- PMI SNS 분석 프로젝트 DB 스키마 v2.0
-- ============================================

-- 1. 사용자 차원 테이블
CREATE TABLE dim_users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(200) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    profile_url TEXT,
    profile_data JSONB,  -- 유연한 프로필 정보 (닉네임, 소개 등)
    
    -- 성과 데이터 (별도 테이블로 분리 가능)
    sales_rank VARCHAR(50),
    monthly_sales DECIMAL(15, 2),
    team_size INTEGER,
    
    -- 메타데이터
    first_collected_date DATE DEFAULT CURRENT_DATE,
    last_updated_date TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT uq_user_platform UNIQUE (user_name, platform)
);

-- 인덱스
CREATE INDEX idx_users_platform ON dim_users(platform);
CREATE INDEX idx_users_sales_rank ON dim_users(sales_rank);
CREATE INDEX idx_users_profile_data ON dim_users USING GIN(profile_data);  -- JSONB 인덱스

-- 2. 게시물 팩트 테이블
CREATE TABLE fact_posts (
    post_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES dim_users(user_id),
    
    -- 기본 정보
    platform VARCHAR(50) NOT NULL,
    post_url TEXT NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    published_date TIMESTAMP,
    
    -- 멀티미디어
    image_urls TEXT[],  -- PostgreSQL 배열
    video_urls TEXT[],
    image_ocr_text TEXT,
    video_transcript TEXT,
    
    -- 메타데이터
    hashtags TEXT[],
    content_type VARCHAR(100),
    content_metadata JSONB,  -- content_type_scores 등
    
    -- 성과 지표
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    
    -- 파생 컬럼 (계산됨)
    engagement_rate DECIMAL(5, 4) GENERATED ALWAYS AS (
        CASE 
            WHEN view_count > 0 THEN 
                (like_count + comment_count + share_count)::DECIMAL / view_count
            ELSE 0
        END
    ) STORED,
    
    -- 추천인 정보
    sponsor_phone VARCHAR(20),
    sponsor_id VARCHAR(50),
    
    -- 수집 메타
    collected_date TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_posts_user_id ON fact_posts(user_id);
CREATE INDEX idx_posts_platform ON fact_posts(platform);
CREATE INDEX idx_posts_published_date ON fact_posts(published_date DESC);
CREATE INDEX idx_posts_engagement ON fact_posts(engagement_rate DESC);
CREATE INDEX idx_posts_hashtags ON fact_posts USING GIN(hashtags);  -- 배열 검색 최적화
CREATE INDEX idx_posts_content_metadata ON fact_posts USING GIN(content_metadata);

-- Full-Text Search 인덱스 (한국어 검색)
CREATE INDEX idx_posts_content_fts ON fact_posts USING GIN(to_tsvector('korean', content));

-- 3. 일별 집계 테이블 (성능 최적화)
CREATE TABLE agg_daily_metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    user_id INTEGER REFERENCES dim_users(user_id),
    platform VARCHAR(50),
    
    -- 집계 지표
    total_posts INTEGER DEFAULT 0,
    total_likes INTEGER DEFAULT 0,
    total_comments INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    avg_engagement_rate DECIMAL(5, 4),
    
    -- 콘텐츠 분석
    top_hashtags TEXT[],
    content_type_distribution JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT uq_daily_user_platform UNIQUE (metric_date, user_id, platform)
);

-- 인덱스
CREATE INDEX idx_daily_date ON agg_daily_metrics(metric_date DESC);
CREATE INDEX idx_daily_user ON agg_daily_metrics(user_id);

-- 4. 크롤링 로그 테이블
CREATE TABLE log_crawling_jobs (
    job_id BIGSERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20),  -- 'running', 'success', 'failed'
    
    posts_collected INTEGER DEFAULT 0,
    posts_filtered INTEGER DEFAULT 0,
    posts_duplicated INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_log_platform_date ON log_crawling_jobs(platform, start_time DESC);
JSONB 컬럼 활용 예시:

sql
-- profile_data 예시
{
  "nickname": "건강지킴이",
  "intro": "PM과 함께 건강한 삶을",
  "followers": 1500,
  "following": 300,
  "custom_field": "자유로운 데이터"
}

-- content_metadata 예시
{
  "content_type_scores": {
    "Undisclosed_Ad": 50,
    "QA_Format": 4,
    "User_Review_Experience": 5
  },
  "sentiment": "positive",
  "keywords": ["FitLine", "건강", "다이어트"]
}

-- JSONB 쿼리 예시
SELECT * FROM dim_users 
WHERE profile_data->>'followers' > '1000';

SELECT * FROM fact_posts
WHERE content_metadata->'content_type_scores'->>'Undisclosed_Ad' > '40';
5) 데이터 적재 (ETL) 코드

python
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import json

class PostgreSQLLoader:
    def __init__(self, host, database, user, password):
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        self.cursor = self.conn.cursor()
    
    def upsert_users(self, users_df):
        """사용자 데이터 Upsert"""
        sql = """
        INSERT INTO dim_users (user_name, platform, profile_url, profile_data)
        VALUES %s
        ON CONFLICT (user_name, platform) 
        DO UPDATE SET
            profile_url = EXCLUDED.profile_url,
            profile_data = EXCLUDED.profile_data,
            last_updated_date = NOW()
        RETURNING user_id;
        """
        
        values = [
            (
                row['user_name'],
                row['platform'],
                row.get('profile_url'),
                json.dumps(row.get('profile_data', {}))
            )
            for _, row in users_df.iterrows()
        ]
        
        execute_values(self.cursor, sql, values)
        self.conn.commit()
        print(f"✅ {len(values)}명 사용자 업데이트 완료")
    
    def insert_posts_bulk(self, posts_df):
        """게시물 대량 삽입 (중복 무시)"""
        sql = """
        INSERT INTO fact_posts (
            user_id, platform, post_url, title, content, published_date,
            hashtags, image_urls, video_urls, content_metadata,
            like_count, comment_count, sponsor_phone, sponsor_id,
            image_ocr_text, video_transcript
        )
        SELECT 
            u.user_id, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        FROM dim_users u
        WHERE u.user_name = %s AND u.platform = %s
        ON CONFLICT (post_url) DO NOTHING;
        """
        
        inserted = 0
        for _, row in posts_df.iterrows():
            try:
                self.cursor.execute(sql, (
                    row['platform'],
                    row['post_url'],
                    row.get('title'),
                    row.get('content'),
                    row.get('published_date'),
                    row.get('hashtags', []),  # 배열
                    row.get('image_urls', []),
                    row.get('video_urls', []),
                    json.dumps(row.get('content_metadata', {})),  # JSONB
                    row.get('like_count', 0),
                    row.get('comment_count', 0),
                    row.get('sponsor_phone'),
                    row.get('sponsor_id'),
                    row.get('image_ocr_text'),
                    row.get('video_transcript'),
                    row['user_name'],  # JOIN용
                    row['platform']
                ))
                inserted += self.cursor.rowcount
            except Exception as e:
                print(f"⚠️ 삽입 실패: {row['post_url']} - {e}")
        
        self.conn.commit()
        print(f"✅ {inserted}개 게시물 삽입 완료")
    
    def aggregate_daily_metrics(self, target_date):
        """일별 지표 집계 (Stored Procedure)"""
        sql = """
        INSERT INTO agg_daily_metrics (
            metric_date, user_id, platform,
            total_posts, total_likes, total_comments, total_views,
            avg_engagement_rate
        )
        SELECT 
            %s AS metric_date,
            user_id,
            platform,
            COUNT(*) AS total_posts,
            SUM(like_count) AS total_likes,
            SUM(comment_count) AS total_comments,
            SUM(view_count) AS total_views,
            AVG(engagement_rate) AS avg_engagement_rate
        FROM fact_posts
        WHERE DATE(published_date) = %s
        GROUP BY user_id, platform
        ON CONFLICT (metric_date, user_id, platform) DO UPDATE SET
            total_posts = EXCLUDED.total_posts,
            total_likes = EXCLUDED.total_likes,
            total_comments = EXCLUDED.total_comments,
            total_views = EXCLUDED.total_views,
            avg_engagement_rate = EXCLUDED.avg_engagement_rate;
        """
        
        self.cursor.execute(sql, (target_date, target_date))
        self.conn.commit()
        print(f"✅ {target_date} 일별 집계 완료")
    
    def close(self):
        self.cursor.close()
        self.conn.close()

# 사용 예시
loader = PostgreSQLLoader(
    host="your-server.postgres.database.azure.com",
    database="pmik_sns_db",
    user="admin@your-server",
    password="your-password"
)

# CSV 로드
df = pd.read_csv("naver_blog_pm_v10_3_posts_20251121_010057.csv")

# 사용자 추출 및 업로드
users_df = df[['blog_id', 'platform']].rename(columns={'blog_id': 'user_name'}).drop_duplicates()
loader.upsert_users(users_df)

# 게시물 업로드
posts_df = df.rename(columns={'blog_id': 'user_name'})
loader.insert_posts_bulk(posts_df)

# 집계
loader.aggregate_daily_metrics('2025-11-21')

loader.close()
6) Azure PostgreSQL 설정 가이드

bash
# 1. Azure PostgreSQL Flexible Server 생성 (CLI)
az postgres flexible-server create \
  --resource-group PMI-SNS-RG \
  --name pmik-sns-db \
  --location koreacentral \
  --admin-user pmadmin \
  --admin-password 'YourSecurePassword123!' \
  --sku-name Standard_B2s \  # 2 vCore, 4GB RAM (~$50/월)
  --tier Burstable \
  --storage-size 64 \  # 64GB
  --version 15

# 2. 방화벽 규칙 (VM IP 허용)
az postgres flexible-server firewall-rule create \
  --resource-group PMI-SNS-RG \
  --name pmik-sns-db \
  --rule-name AllowCrawlerVM \
  --start-ip-address <VM_PUBLIC_IP> \
  --end-ip-address <VM_PUBLIC_IP>

# 3. 데이터베이스 생성
az postgres flexible-server db create \
  --resource-group PMI-SNS-RG \
  --server-name pmik-sns-db \
  --database-name sns_analysis

# 4. 연결 문자열 확인
az postgres flexible-server show-connection-string \
  --server-name pmik-sns-db \
  --database-name sns_analysis \
  --admin-user pmadmin
비용 최적화 옵션:

티어	사양	월 비용	적합성
Burstable B2s	2 vCore, 4GB RAM, 64GB 스토리지	~$50	✅ 현재 규모 최적
General Purpose D2s_v3	2 vCore, 8GB RAM, 128GB	~$120	향후 확장 시
Supabase (오픈소스)	Self-hosted PostgreSQL	$0 (VM 비용만)	⭐ 비용 절감 대안
Supabase 활용 (무료/오픈소스 대안):

bash
# Docker로 Supabase 셀프 호스팅 (Crawler VM에서)
git clone https://github.com/supabase/supabase
cd supabase/docker
cp .env.example .env

# .env 편집 후
docker-compose up -d

# PostgreSQL 접근
# Host: localhost (VM 내부)
# Port: 5432
# User: postgres
# Password: .env에서 설정한 값
최종 권장:

초기 (3주): Crawler VM에 PostgreSQL 설치 (무료, 빠른 테스트)

운영 단계: Azure PostgreSQL Flexible Server B2s로 마이그레이션

2.4 데이터 분석 및 주요 피처 추출
현재 작업 평가
완료된 작업 (테스트 버전):

✅ 네이버 블로그 EDA

✅ BI Dashboard (Power BI)

✅ K-Means 클러스터링

✅ 워드 클라우드

개선 방향:

1) 주요 피처 (Feature) 정의
python
# 주요 피처 목록
FEATURE_GROUPS = {
    "활동 패턴": [
        "posts_per_week",           # 주간 게시 빈도
        "avg_post_interval_days",   # 평균 게시 간격
        "posting_consistency",      # 게시 일정 규칙성
        "active_hours",             # 주 활동 시간대
        "weekend_post_ratio"        # 주말 게시 비율
    ],
    
    "콘텐츠 특성": [
        "avg_content_length",       # 평균 본문 길이
        "avg_hashtag_count",        # 평균 해시태그 수
        "hashtag_diversity",        # 해시태그 다양성
        "media_usage_ratio",        # 멀티미디어 사용 비율
        "content_type_entropy"      # 콘텐츠 타입 다양성
    ],
    
    "참여도": [
        "avg_engagement_rate",      # 평균 참여율
        "like_per_post",            # 게시물당 좋아요
        "comment_per_post",         # 게시물당 댓글
        "viral_post_ratio"          # 바이럴 게시물 비율 (>평균*2)
    ],
    
    "플랫폼 활용": [
        "platform_count",           # 활용 플랫폼 수
        "primary_platform",         # 주력 플랫폼
        "cross_platform_ratio"      # 크로스 포스팅 비율
    ],
    
    "네트워크 영향": [
        "sponsor_mention_count",    # 후원인 언급 횟수
        "team_keyword_usage",       # 팀 키워드 사용 빈도
        "recruitment_post_ratio"    # 모집 게시물 비율
    ]
}
피처 추출 코드:

python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import entropy

class FeatureExtractor:
    def __init__(self, posts_df, users_df):
        self.posts_df = posts_df
        self.users_df = users_df
        
    def extract_all_features(self):
        """모든 피처 추출"""
        user_features = []
        
        for user_id in self.users_df['user_id'].unique():
            user_posts = self.posts_df[self.posts_df['user_id'] == user_id]
            
            if len(user_posts) == 0:
                continue
            
            features = {
                'user_id': user_id,
                **self._activity_features(user_posts),
                **self._content_features(user_posts),
                **self._engagement_features(user_posts),
                **self._platform_features(user_posts),
                **self._network_features(user_posts)
            }
            
            user_features.append(features)
        
        return pd.DataFrame(user_features)
    
    def _activity_features(self, posts):
        """활동 패턴 피처"""
        posts = posts.copy()
        posts['published_date'] = pd.to_datetime(posts['published_date'])
        posts = posts.sort_values('published_date')
        
        # 기간 계산
        date_range = (posts['published_date'].max() - posts['published_date'].min()).days
        weeks = max(date_range / 7, 1)
        
        # 게시 간격
        intervals = posts['published_date'].diff().dt.total_seconds() / 86400  # 일 단위
        
        # 시간대 분석
        posts['hour'] = posts['published_date'].dt.hour
        active_hours = posts['hour'].mode()[0] if len(posts) > 0 else 12
        
        # 주말 비율
        posts['is_weekend'] = posts['published_date'].dt.dayofweek >= 5
        weekend_ratio = posts['is_weekend'].mean()
        
        return {
            'posts_per_week': len(posts) / weeks,
            'avg_post_interval_days': intervals.mean() if len(intervals) > 1 else 0,
            'posting_consistency': 1 / (intervals.std() + 1) if len(intervals) > 1 else 0,
            'active_hours': active_hours,
            'weekend_post_ratio': weekend_ratio
        }
    
    def _content_features(self, posts):
        """콘텐츠 특성 피처"""
        # 텍스트 길이
        posts['content_length'] = posts['content'].fillna('').apply(len)
        
        # 해시태그 분석
        posts['hashtag_count'] = posts['hashtags'].fillna('').apply(
            lambda x: len(x.split(', ')) if x else 0
        )
        
        # 해시태그 다양성 (Unique / Total)
        all_hashtags = []
        for tags in posts['hashtags'].dropna():
            all_hashtags.extend(tags.split(', '))
        hashtag_diversity = len(set(all_hashtags)) / max(len(all_hashtags), 1)
        
        # 멀티미디어 사용
        posts['has_media'] = (posts['image_urls'].notna()) | (posts['video_urls'].notna())
        media_ratio = posts['has_media'].mean()
        
        # 콘텐츠 타입 다양성 (엔트로피)
        content_types = posts['content_type'].value_counts(normalize=True)
        content_entropy = entropy(content_types.values)
        
        return {
            'avg_content_length': posts['content_length'].mean(),
            'avg_hashtag_count': posts['hashtag_count'].mean(),
            'hashtag_diversity': hashtag_diversity,
            'media_usage_ratio': media_ratio,
            'content_type_entropy': content_entropy
        }
    
    def _engagement_features(self, posts):
        """참여도 피처"""
        # 참여율 계산
        posts['engagement_rate'] = (
            (posts['like_count'] + posts['comment_count']) / 
            posts['view_count'].replace(0, 1)
        ).fillna(0)
        
        # 바이럴 게시물 (참여율 > 평균*2)
        avg_engagement = posts['engagement_rate'].mean()
        viral_posts = posts[posts['engagement_rate'] > avg_engagement * 2]
        
        return {
            'avg_engagement_rate': posts['engagement_rate'].mean(),
            'like_per_post': posts['like_count'].mean(),
            'comment_per_post': posts['comment_count'].mean(),
            'viral_post_ratio': len(viral_posts) / max(len(posts), 1)
        }
    
    def _platform_features(self, posts):
        """플랫폼 활용 피처"""
        platforms = posts['platform'].unique()
        primary = posts['platform'].mode()[0] if len(posts) > 0 else 'unknown'
        
        # 크로스 포스팅 감지 (동일 제목/콘텐츠)
        duplicate_content = posts.duplicated(subset=['title'], keep=False).sum()
        cross_ratio = duplicate_content / max(len(posts), 1)
        
        return {
            'platform_count': len(platforms),
            'primary_platform': primary,
            'cross_platform_ratio': cross_ratio
        }
    
    def _network_features(self, posts):
        """네트워크 영향 피처"""
        # 후원인 언급
        sponsor_mentions = posts['sponsor_phone'].notna().sum()
        
        # 팀 키워드
        team_keywords = ['팀', '그룹', '조직', '리더', '파트너']
        team_posts = posts['content'].fillna('').apply(
            lambda x: any(kw in x for kw in team_keywords)
        ).sum()
        
        # 모집 게시물
        recruit_keywords = ['모집', '함께', '시작', '기회', '비즈니스']
        recruit_posts = posts['content'].fillna('').apply(
            lambda x: any(kw in x for kw in recruit_keywords)
        ).sum()
        
        return {
            'sponsor_mention_count': sponsor_mentions,
            'team_keyword_usage': team_posts / max(len(posts), 1),
            'recruitment_post_ratio': recruit_posts / max(len(posts), 1)
        }

# 사용 예시
extractor = FeatureExtractor(posts_df, users_df)
features_df = extractor.extract_all_features()

# CSV 저장
features_df.to_csv('user_features.csv', index=False, encoding='utf-8-sig')
print(f"✅ {len(features_df)}명 사용자의 피처 추출 완료")
2) 클러스터링 개선
K-Means의 한계:

구형 클러스터만 감지

이상치에 민감

클러스터 수를 사전 지정 필요

개선 방법론:

python
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score
import matplotlib.pyplot as plt
import seaborn as sns

class AdvancedClustering:
    def __init__(self, features_df):
        self.features_df = features_df
        self.numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        self.X = features_df[self.numeric_cols].fillna(0)
        
        # 표준화
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
    
    def compare_methods(self):
        """다양한 클러스터링 방법 비교"""
        results = []
        
        # 1. K-Means (개선된 버전)
        for k in range(2, 11):
            kmeans = KMeans(
                n_clusters=k,
                init='k-means++',  # 개선된 초기화
                n_init=20,         # 더 많은 시도
                max_iter=500,
                random_state=42
            )
            labels = kmeans.fit_predict(self.X_scaled)
            
            silhouette = silhouette_score(self.X_scaled, labels)
            davies_bouldin = davies_bouldin_score(self.X_scaled, labels)
            
            results.append({
                'method': 'K-Means',
                'k': k,
                'silhouette': silhouette,
                'davies_bouldin': davies_bouldin,
                'labels': labels
            })
        
        # 2. Hierarchical Clustering (계층적)
        for k in range(2, 11):
            agg = AgglomerativeClustering(
                n_clusters=k,
                linkage='ward'  # Ward's method (분산 최소화)
            )
            labels = agg.fit_predict(self.X_scaled)
            
            silhouette = silhouette_score(self.X_scaled, labels)
            davies_bouldin = davies_bouldin_score(self.X_scaled, labels)
            
            results.append({
                'method': 'Hierarchical',
                'k': k,
                'silhouette': silhouette,
                'davies_bouldin': davies_bouldin,
                'labels': labels
            })
        
        # 3. DBSCAN (밀도 기반)
        for eps in [0.5, 1.0, 1.5, 2.0]:
            dbscan = DBSCAN(eps=eps, min_samples=5)
            labels = dbscan.fit_predict(self.X_scaled)
            
            # 노이즈(-1) 제외
            valid_labels = labels[labels != -1]
            if len(set(valid_labels)) > 1:
                silhouette = silhouette_score(
                    self.X_scaled[labels != -1], 
                    valid_labels
                )
                davies_bouldin = davies_bouldin_score(
                    self.X_scaled[labels != -1], 
                    valid_labels
                )
            else:
                silhouette = -1
                davies_bouldin = 999
            
            results.append({
                'method': 'DBSCAN',
                'eps': eps,
                'k': len(set(labels)) - (1 if -1 in labels else 0),
                'silhouette': silhouette,
                'davies_bouldin': davies_bouldin,
                'labels': labels,
                'noise_ratio': (labels == -1).sum() / len(labels)
            })
        
        return pd.DataFrame(results)
    
    def select_best_model(self, results_df):
        """최적 모델 선택"""
        # Silhouette 점수가 높고, Davies-Bouldin이 낮은 모델
        results_df['score'] = (
            results_df['silhouette'] * 2 -  # Silhouette 가중치 2배
            results_df['davies_bouldin'] / 10
        )
        
        best = results_df.loc[results_df['score'].idxmax()]
        print(f"✅ 최적 모델: {best['method']} (k={best['k']})")
        print(f"   Silhouette: {best['silhouette']:.3f}")
        print(f"   Davies-Bouldin: {best['davies_bouldin']:.3f}")
        
        return best
    
    def visualize_clusters(self, labels, method='PCA'):
        """클러스터 시각화"""
        from sklearn.decomposition import PCA
        from sklearn.manifold import TSNE
        
        # 차원 축소
        if method == 'PCA':
            reducer = PCA(n_components=2)
        else:
            reducer = TSNE(n_components=2, random_state=42)
        
        X_reduced = reducer.fit_transform(self.X_scaled)
        
        # 플롯
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            X_reduced[:, 0], 
            X_reduced[:, 1], 
            c=labels, 
            cmap='viridis',
            s=100,
            alpha=0.6
        )
        plt.colorbar(scatter, label='Cluster')
        plt.title(f'User Clusters ({method})', fontsize=16)
        plt.xlabel(f'{method} Component 1')
        plt.ylabel(f'{method} Component 2')
        plt.tight_layout()
        plt.savefig(f'clusters_{method}.png', dpi=300)
        plt.show()
    
    def profile_clusters(self, labels):
        """클러스터 프로파일링"""
        self.features_df['cluster'] = labels
        
        # 클러스터별 평균 특성
        cluster_profiles = self.features_df.groupby('cluster')[self.numeric_cols].mean()
        
        # 히트맵
        plt.figure(figsize=(14, 8))
        sns.heatmap(
            cluster_profiles.T, 
            annot=True, 
            fmt='.2f', 
            cmap='YlOrRd',
            cbar_kws={'label': 'Average Value'}
        )
        plt.title('Cluster Profiles Heatmap', fontsize=16)
        plt.xlabel('Cluster')
        plt.ylabel('Feature')
        plt.tight_layout()
        plt.savefig('cluster_profiles.png', dpi=300)
        plt.show()
        
        return cluster_profiles
    
    def name_clusters(self, cluster_profiles):
        """클러스터 명명"""
        cluster_names = {}
        
        for cluster_id, profile in cluster_profiles.iterrows():
            # 특성 기반 자동 명명 로직
            if profile['avg_engagement_rate'] > cluster_profiles['avg_engagement_rate'].median():
                if profile['posts_per_week'] > cluster_profiles['posts_per_week'].median():
                    name = "Super Engagers (고참여 고활동)"
                else:
                    name = "Influencers (고참여 저활동)"
            else:
                if profile['posts_per_week'] > cluster_profiles['posts_per_week'].median():
                    name = "Steady Contributors (저참여 고활동)"
                else:
                    name = "Casual Users (저참여 저활동)"
            
            cluster_names[cluster_id] = name
        
        return cluster_names

# 실행
clustering = AdvancedClustering(features_df)

# 1. 방법 비교
results = clustering.compare_methods()
print(results.sort_values('silhouette', ascending=False).head(10))

# 2. 최적 모델 선택
best_model = clustering.select_best_model(results)
best_labels = results[results['score'] == best_model['score']].iloc[0]['labels']

# 3. 시각화
clustering.visualize_clusters(best_labels, method='PCA')
clustering.visualize_clusters(best_labels, method='TSNE')

# 4. 프로파일링
cluster_profiles = clustering.profile_clusters(best_labels)

# 5. 명명
cluster_names = clustering.name_clusters(cluster_profiles)
print("\n✅ 클러스터 명명:")
for cid, name in cluster_names.items():
    print(f"   Cluster {cid}: {name}")

# 6. 결과 저장
features_df['cluster'] = best_labels
features_df['cluster_name'] = features_df['cluster'].map(cluster_names)
features_df.to_csv('user_clusters.csv', index=False, encoding='utf-8-sig')
예상 결과:

text
Cluster 0 (25%): Super Engagers (고참여 고활동)
  - posts_per_week: 5.2
  - avg_engagement_rate: 0.12
  - platform_count: 3.1
  → 적극적 활동, 멀티 플랫폼 활용

Cluster 1 (35%): Steady Contributors (저참여 고활동)
  - posts_per_week: 4.8
  - avg_engagement_rate: 0.04
  → 꾸준한 활동하지만 반응은 보통

Cluster 2 (30%): Casual Users (저참여 저활동)
  - posts_per_week: 1.2
  - avg_engagement_rate: 0.03
  → 간헐적 활동

Cluster 3 (10%): Influencers (고참여 저활동)
  - posts_per_week: 1.8
  - avg_engagement_rate: 0.18
  → 적게 올리지만 높은 품질
3) 대시보드 고도화
Power BI 개선 사항:

text
[대시보드 구조]

📊 Page 1: 개요 (Overview)
├─ KPI 카드
│   ├─ 총 게시물 수
│   ├─ 활성 사용자 수
│   ├─ 평균 참여율
│   └─ 월간 성장률
│
├─ 플랫폼별 활동 분포 (Pie Chart)
├─ 월별 트렌드 (Line Chart)
└─ 클러스터 분포 (Donut Chart)

📈 Page 2: 사용자 분석 (User Analytics)
├─ 클러스터별 특성 비교 (Radar Chart)
├─ Top 10 사용자 (Table with Sparklines)
├─ 플랫폼별 활동 히트맵 (Heatmap)
└─ 사용자 필터 (Slicer)

📝 Page 3: 콘텐츠 분석 (Content Analytics)
├─ 워드 클라우드 (Top Hashtags)
├─ 콘텐츠 타입 분포 (Stacked Bar)
├─ 시간대별 게시 패턴 (Heatmap)
└─ 바이럴 게시물 Top 20 (Table)

🎯 Page 4: 성과 분석 (Performance)
├─ 참여율 vs 게시 빈도 (Scatter Plot)
├─ 플랫폼별 ROI (Bar Chart)
├─ 클러스터별 전환율 (Funnel)
└─ 추세 예측 (Forecast Line)
DAX 측정값 예시:

text
-- 평균 참여율
Avg Engagement Rate = 
AVERAGE(fact_posts[engagement_rate])

-- 월간 성장률 (MoM)
MoM Growth = 
VAR CurrentMonth = 
    CALCULATE(
        COUNTROWS(fact_posts),
        DATESMTD(fact_posts[published_date])
    )
VAR PreviousMonth = 
    CALCULATE(
        COUNTROWS(fact_posts),
        DATEADD(fact_posts[published_date], -1, MONTH)
    )
RETURN
    DIVIDE(CurrentMonth - PreviousMonth, PreviousMonth, 0)

-- Top 10% 고성과 사용자 수
Top Performers = 
CALCULATE(
    DISTINCTCOUNT(fact_posts[user_id]),
    TOPN(
        ROUNDUP(COUNTROWS(dim_users) * 0.1, 0),
        dim_users,
        dim_users[avg_engagement_rate],
        DESC
    )
)

-- 바이럴 게시물 비율
Viral Post Ratio = 
VAR AvgEngagement = [Avg Engagement Rate]
VAR ViralPosts = 
    CALCULATE(
        COUNTROWS(fact_posts),
        fact_posts[engagement_rate] > AvgEngagement * 2
    )
RETURN
    DIVIDE(ViralPosts, COUNTROWS(fact_posts), 0)
2.5 AI 모델 개발 로드맵
채용 공고에서 요구하는 AI 역량
4. AI Model Development:

Develop machine learning and predictive analysis models to derive best practices of successful TPs.

Utilize natural language processing (NLP) technologies to analyze seminar information and communication content.

실현 가능성 평가
AI 작업	난이도	3주 내 가능성	향후 개발 추천
회귀 분석 (성과 예측)	⭐⭐	✅ 가능	우선 순위 1
클러스터링 (패턴 발견)	⭐⭐	✅ 가능	우선 순위 1
감성 분석 (긍정/부정)	⭐⭐⭐	⚠️ 기본만	우선 순위 2
토픽 모델링 (LDA)	⭐⭐⭐	⚠️ 기본만	우선 순위 2
키워드 추출 (TF-IDF)	⭐⭐	✅ 가능	우선 순위 1
트랜스포머 NLP (KoBERT)	⭐⭐⭐⭐⭐	❌ 불가	장기 과제
추천 시스템	⭐⭐⭐⭐	❌ 불가	장기 과제
이탈 예측 (Churn)	⭐⭐⭐⭐	❌ 불가	장기 과제
3주 내 구현 가능 AI 모델
1) 성과 예측 모델 (회귀 분석)

python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt

class PerformancePredictionModel:
    def __init__(self, features_df, performance_df):
        """
        features_df: 사용자별 SNS 활동 피처
        performance_df: 사용자별 성과 (매출, 신규 모집 등)
        """
        # 데이터 결합
        self.data = features_df.merge(
            performance_df[['user_id', 'monthly_sales', 'new_recruits']],
            on='user_id',
            how='inner'
        )
        
        # 피처와 타겟 분리
        self.feature_cols = [col for col in features_df.columns 
                            if col not in ['user_id', 'cluster', 'cluster_name']]
        self.X = self.data[self.feature_cols].fillna(0)
        self.y_sales = self.data['monthly_sales']
        self.y_recruits = self.data['new_recruits']
    
    def train_models(self, target='sales'):
        """다양한 모델 학습 및 비교"""
        y = self.y_sales if target == 'sales' else self.y_recruits
        
        # Train-Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            self.X, y, test_size=0.2, random_state=42
        )
        
        # 모델 정의
        models = {
            'Ridge Regression': Ridge(alpha=1.0),
            'Lasso Regression': Lasso(alpha=0.1),
            'Random Forest': RandomForestRegressor(
                n_estimators=100, 
                max_depth=10,
                random_state=42
            ),
            'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
        }
        
        results = []
        
        for name, model in models.items():
            # 학습
            model.fit(X_train, y_train)
            
            # 예측
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # 평가
            r2_train = r2_score(y_train, y_pred_train)
            r2_test = r2_score(y_test, y_pred_test)
            mae = mean_absolute_error(y_test, y_pred_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            
            # 교차 검증
            cv_scores = cross_val_score(
                model, self.X, y, cv=5, scoring='r2'
            )
            
            results.append({
                'Model': name,
                'R² (Train)': r2_train,
                'R² (Test)': r2_test,
                'MAE': mae,
                'RMSE': rmse,
                'CV R² (Mean)': cv_scores.mean(),
                'CV R² (Std)': cv_scores.std()
            })
            
            print(f"\n{name}:")
            print(f"  R² (Test): {r2_test:.3f}")
            print(f"  MAE: {mae:.2f}")
            print(f"  CV R² : {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        results_df = pd.DataFrame(results)
        print("\n" + "="*60)
        print(results_df.to_string(index=False))
        
        # 최적 모델 선택
        best_model_name = results_df.loc[
            results_df['R² (Test)'].idxmax(), 'Model'
        ]
        best_model = models[best_model_name]
        best_model.fit(self.X, y)
        
        print(f"\n✅ 최적 모델: {best_model_name}")
        
        return best_model, results_df
    
    def feature_importance(self, model, top_n=15):
        """피처 중요도 분석"""
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
        else:
            print("⚠️ 이 모델은 피처 중요도를 제공하지 않습니다.")
            return
        
        feature_importance = pd.DataFrame({
            'Feature': self.feature_cols,
            'Importance': importances
        }).sort_values('Importance', ascending=False)
        
        print("\n" + "="*60)
        print(f"Top {top_n} 중요 피처:")
        print(feature_importance.head(top_n).to_string(index=False))
        
        # 시각화
        plt.figure(figsize=(10, 8))
        plt.barh(
            feature_importance.head(top_n)['Feature'], 
            feature_importance.head(top_n)['Importance']
        )
        plt.xlabel('Importance')
        plt.title(f'Top {top_n} Feature Importances')
        plt.tight_layout()
        plt.savefig('feature_importance.png', dpi=300)
        plt.show()
        
        return feature_importance
    
    def predict_new_users(self, model, new_users_df):
        """신규 사용자 성과 예측"""
        X_new = new_users_df[self.feature_cols].fillna(0)
        predictions = model.predict(X_new)
        
        new_users_df['predicted_sales'] = predictions
        
        return new_users_df[['user_id', 'predicted_sales']].sort_values(
            'predicted_sales', ascending=False
        )

# 실행 예시
model_builder = PerformancePredictionModel(features_df, performance_df)

# 매출 예측 모델
sales_model, sales_results = model_builder.train_models(target='sales')

# 피처 중요도
importance_df = model_builder.feature_importance(sales_model)

# 신규 사용자 예측
predictions = model_builder.predict_new_users(sales_model, new_users_features)
print("\n신규 사용자 예측 매출 Top 10:")
print(predictions.head(10))
2) 감성 분석 (기본 버전)

python
from transformers import pipeline
from collections import Counter

class SentimentAnalyzer:
    def __init__(self):
        # 사전 학습된 한국어 감성 분석 모델
        self.analyzer = pipeline(
            "sentiment-analysis",
            model="beomi/kcbert-base"  # 한국어 BERT
        )
    
    def analyze_posts(self, posts_df):
        """게시물 감성 분석"""
        sentiments = []
        
        for idx, row in posts_df.iterrows():
            content = row['content'][:512]  # BERT 최대 길이 제한
            
            try:
                result = self.analyzer(content)[0]
                sentiment = 'positive' if result['label'] == 'LABEL_1' else 'negative'
                score = result['score']
            except:
                sentiment = 'neutral'
                score = 0.5
            
            sentiments.append({
                'post_id': row['post_id'],
                'sentiment': sentiment,
                'sentiment_score': score
            })
        
        return pd.DataFrame(sentiments)
    
    def aggregate_user_sentiment(self, posts_df, sentiment_df):
        """사용자별 감성 집계"""
        merged = posts_df.merge(sentiment_df, on='post_id')
        
        user_sentiment = merged.groupby('user_id').agg({
            'sentiment': lambda x: Counter(x).most_common(1)[0][0],
            'sentiment_score': 'mean'
        }).reset_index()
        
        user_sentiment.columns = ['user_id', 'dominant_sentiment', 'avg_sentiment_score']
        
        return user_sentiment

# 간단한 키워드 기반 감성 분석 (대안)
class KeywordSentimentAnalyzer:
    def __init__(self):
        self.positive_keywords = [
            '좋아', '행복', '감사', '성공', '성장', '건강', '만족', 
            '추천', '최고', '완벽', '신뢰', '효과', '변화'
        ]
        self.negative_keywords = [
            '나쁜', '실망', '후회', '어렵', '힘들', '문제', '불만',
            '부작용', '거짓', '사기', '과장'
        ]
    
    def analyze(self, text):
        pos_count = sum(1 for kw in self.positive_keywords if kw in text)
        neg_count = sum(1 for kw in self.negative_keywords if kw in text)
        
        if pos_count > neg_count:
            return 'positive', pos_count / (pos_count + neg_count + 1)
        elif neg_count > pos_count:
            return 'negative', neg_count / (pos_count + neg_count + 1)
        else:
            return 'neutral', 0.5

# 사용 (키워드 기반이 더 빠르고 안정적)
analyzer = KeywordSentimentAnalyzer()
posts_df['sentiment'], posts_df['sentiment_score'] = zip(*posts_df['content'].map(analyzer.analyze))
3) 키워드 추출 (TF-IDF)

python
from sklearn.feature_extraction.text import TfidfVectorizer
from konlpy.tag import Okt
import re

class KeywordExtractor:
    def __init__(self):
        self.okt = Okt()
    
    def preprocess(self, text):
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 특수문자 제거
        text = re.sub(r'[^\w\s]', '', text)
        # 명사만 추출
        nouns = self.okt.nouns(text)
        # 2글자 이상만
        nouns = [n for n in nouns if len(n) >= 2]
        return ' '.join(nouns)
    
    def extract_keywords(self, posts_df, top_n=50):
        """TF-IDF 기반 키워드 추출"""
        # 전처리
        corpus = posts_df['content'].fillna('').apply(self.preprocess)
        
        # TF-IDF
        tfidf = TfidfVectorizer(
            max_features=1000,
            min_df=2,  # 최소 2개 문서에 등장
            max_df=0.8  # 80% 이상 문서에 등장하면 제외
        )
        
        tfidf_matrix = tfidf.fit_transform(corpus)
        feature_names = tfidf.get_feature_names_out()
        
        # 평균 TF-IDF 점수 계산
        avg_tfidf = tfidf_matrix.mean(axis=0).A1
        top_indices = avg_tfidf.argsort()[-top_n:][::-1]
        
        keywords = pd.DataFrame({
            'Keyword': [feature_names[i] for i in top_indices],
            'TF-IDF Score': [avg_tfidf[i] for i in top_indices]
        })
        
        return keywords
    
    def cluster_keywords(self, posts_df, cluster_col='cluster'):
        """클러스터별 특징 키워드"""
        cluster_keywords = {}
        
        for cluster in posts_df[cluster_col].unique():
            cluster_posts = posts_df[posts_df[cluster_col] == cluster]
            keywords = self.extract_keywords(cluster_posts, top_n=20)
            cluster_keywords[cluster] = keywords
        
        return cluster_keywords

# 실행
extractor = KeywordExtractor()
top_keywords = extractor.extract_keywords(posts_df, top_n=50)
print("전체 Top 50 키워드:")
print(top_keywords.to_string(index=False))

cluster_keywords = extractor.cluster_keywords(posts_df)
for cluster, keywords in cluster_keywords.items():
    print(f"\n클러스터 {cluster} 특징 키워드:")
    print(keywords.head(10).to_string(index=False))
장기 AI 개발 로드맵 (3개월~6개월)
Phase 1 (1-3개월): 기초 NLP

✅ 감성 분석 고도화 (KoBERT Fine-tuning)

✅ 토픽 모델링 (LDA → BERTopic)

✅ 개체명 인식 (제품명, 팀명 자동 추출)

Phase 2 (3-6개월): 고급 예측 모델

이탈 예측 (Churn Prediction)

성과 예측 정교화 (딥러닝)

추천 시스템 (콘텐츠 추천, 멘토 매칭)

Phase 3 (6개월+): 자동화 및 통합

실시간 리스크 탐지 (허위 광고 자동 식별)

자동 리포트 생성 (GPT-4 활용)

챗봇 지원 시스템

3. 다음 주 화요일까지의 액션 플랜 (7일 간)
Day 1-2 (토-일): 크롤링 마무리 및 안정화
목표: 에러율 5% 이하 달성

 버그 우선순위 정리

치명적 버그 (크롤링 중단) → 즉시 해결

중요 버그 (데이터 누락) → 24시간 내

경미한 버그 (로그 오류) → 추후 처리

 Git 버전 관리 시작

bash
git init
git add .
git commit -m "initial: 현재 작동하는 베이스 코드"
git tag v1.0-working
 플랫폼별 최종 테스트

네이버 블로그: 100건 테스트 → 에러율 체크

유튜브: Whisper 전처리 적용 → 전사 품질 확인

인스타그램: URL 다운로드 → 로컬 저장 테스트

 로깅 강화

python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'crawler_{platform}_{date}.log'),
        logging.StreamHandler()
    ]
)
Day 3-4 (월-화): DB 구축 및 데이터 적재
목표: PostgreSQL 구축 완료, 전체 데이터 적재

 PostgreSQL 설치 (Crawler VM)

bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql
CREATE DATABASE pmik_sns_db;
CREATE USER pmadmin WITH PASSWORD 'securepass123';
GRANT ALL PRIVILEGES ON DATABASE pmik_sns_db TO pmadmin;
 스키마 생성

위 제공한 SQL 스크립트 실행

인덱스 생성 확인

 데이터 적재 스크립트 작성

CSV → PostgreSQL 자동화

중복 체크 로직 포함

 데이터 품질 검증

sql
-- 데이터 건수 확인
SELECT platform, COUNT(*) FROM fact_posts GROUP BY platform;

-- 결측치 비율 확인
SELECT 
    COUNT(*) FILTER (WHERE image_ocr_text IS NULL) * 100.0 / COUNT(*) AS ocr_null_ratio,
    COUNT(*) FILTER (WHERE video_transcript IS NULL) * 100.0 / COUNT(*) AS transcript_null_ratio
FROM fact_posts;
Day 5 (수): 피처 추출 및 클러스터링
목표: 주요 피처 20개 추출, 클러스터 4-6개 도출

 피처 추출 실행

위 FeatureExtractor 코드 실행

user_features.csv 생성

 클러스터링 수행

K-Means, Hierarchical, DBSCAN 비교

최적 모델 선택

클러스터 프로파일 생성

 결과 시각화

PCA/TSNE 플롯

클러스터 히트맵

프로파일 테이블

Day 6 (목): 분석 및 인사이트 도출
목표: 핵심 질문 10개 중 5개 이상 답변

 기술 통계 분석

플랫폼별 활동 비교

시간대별 게시 패턴

콘텐츠 타입 분포

 회귀 분석 (가능하면)

성과 데이터 확보 시

SNS 활동 vs 매출 상관관계

 리스크 분석

허위 광고 키워드 탐지

부정 감성 게시물 비율

Day 7 (금): 대시보드 및 보고서 완성
목표: Power BI 대시보드, 최종 보고서 작성

 Power BI 대시보드

PostgreSQL 연결

4페이지 구성

인터랙티브 필터 추가

 최종 보고서 작성

아래 아키텍처 다이어그램 포함

주요 인사이트 정리

향후 계획 명시

4. 시스템 아키텍처
4.1 전체 시스템 아키텍처
text
┌─────────────────────────────────────────────────────────────────┐
│                        DATA COLLECTION LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Naver   │  │ YouTube  │  │Instagram │  │ Kakao    │  ...   │
│  │  Blog    │  │          │  │          │  │ Story    │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └──────────┬──┴─────────┬───┴─────────────┘               │
│                  │            │                                 │
│            ┌─────▼────────────▼──────┐                          │
│            │  Python Crawlers        │                          │
│            │  - Selenium             │                          │
│            │  - Beautiful Soup       │                          │
│            │  - API Clients          │                          │
│            └──────────┬──────────────┘                          │
│                       │                                         │
└───────────────────────┼─────────────────────────────────────────┘
                        │
                        │ JSON/CSV
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                    PROCESSING LAYER (Azure VM)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Multimedia Processing                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │    │
│  │  │ Image OCR    │  │ Video STT    │  │ Text Clean  │  │    │
│  │  │ - EasyOCR    │  │ - Whisper    │  │ - Regex     │  │    │
│  │  │ - Azure CV   │  │ - Clova      │  │ - konlpy    │  │    │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Data Validation & Quality Check                       │    │
│  │  - Duplicate removal                                   │    │
│  │  - Missing value handling                              │    │
│  │  - Schema validation                                   │    │
│  └────────────────┬───────────────────────────────────────┘    │
│                   │                                             │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    │ Cleaned Data
                    │
┌───────────────────▼─────────────────────────────────────────────┐
│                    STORAGE LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  PostgreSQL (Primary DB)                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │    │
│  │  │ dim_users    │  │ fact_posts   │  │ agg_daily  │  │    │
│  │  │              │  │              │  │ _metrics   │  │    │
│  │  │ - user_id    │  │ - post_id    │  │            │  │    │
│  │  │ - profile    │  │ - content    │  │ - metrics  │  │    │
│  │  │ - sales_rank │  │ - engagement │  │            │  │    │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Azure Blob Storage (Optional)                        │    │
│  │  - Raw images/videos archiving                        │    │
│  │  - OCR/STT re-processing source                       │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ SQL Queries
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                    ANALYTICS LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Feature Engineering                                   │    │
│  │  - Activity patterns (posting frequency, consistency)  │    │
│  │  - Content features (length, hashtags, media usage)    │    │
│  │  - Engagement metrics (likes, comments, shares)        │    │
│  │  - Platform diversity                                  │    │
│  └────────────────┬───────────────────────────────────────┘    │
│                   │                                             │
│  ┌────────────────▼───────────────────────────────────────┐    │
│  │  Machine Learning Models                               │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │    │
│  │  │ Clustering   │  │ Regression   │  │ NLP        │  │    │
│  │  │ - K-Means    │  │ - Ridge      │  │ - TF-IDF   │  │    │
│  │  │ - Hierarchic │  │ - RF         │  │ - Sentiment│  │    │
│  │  │ - DBSCAN     │  │ - GBM        │  │ - Keywords │  │    │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ Results & Insights
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│                    VISUALIZATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Power BI Dashboard                                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│    │
│  │  │ Overview │  │ User     │  │ Content  │  │Performance    │
│  │  │ Page     │  │ Analytics│  │ Analytics│  │ Page   ││    │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────┘│    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Automated Reports                                     │    │
│  │  - Weekly activity summary                             │    │
│  │  - Monthly performance report                          │    │
│  │  - Risk detection alerts                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
4.2 데이터 흐름 아키텍처 (Data Flow)
text
[크롤링] → [전처리] → [적재] → [분석] → [시각화]

Phase 1: Collection
├─ Input: Social Media APIs/Web Pages
├─ Process: Selenium, BeautifulSoup, API calls
├─ Output: Raw JSON/CSV (metadata + URLs)
└─ Storage: VM Local (Temporary)

Phase 2: Processing
├─ Input: Raw JSON/CSV
├─ Process:
│   ├─ Image OCR (EasyOCR/Azure CV)
│   ├─ Video STT (Whisper/Clova)
│   ├─ Text cleaning (regex, konlpy)
│   └─ Data validation
├─ Output: Cleaned structured data
└─ Storage: VM Local (Temporary)

Phase 3: Loading
├─ Input: Cleaned data
├─ Process: Bulk INSERT/UPSERT into PostgreSQL
├─ Output: Relational tables
└─ Storage: PostgreSQL (Permanent)

Phase 4: Analytics
├─ Input: PostgreSQL tables
├─ Process:
│   ├─ Feature extraction (Python/Pandas)
│   ├─ ML modeling (Scikit-learn)
│   ├─ Statistical analysis
│   └─ NLP processing
├─ Output: Results (CSV, models)
└─ Storage: PostgreSQL + Local files

Phase 5: Visualization
├─ Input: Analytics results
├─ Process: Power BI DAX, visualizations
├─ Output: Interactive dashboards
└─ Delivery: .pbix file, web publish
4.3 기술 스택 아키텍처
text
┌─────────────────────────────────────────────────┐
│              INFRASTRUCTURE                     │
├─────────────────────────────────────────────────┤
│ Azure VM (Standard_D8as_v5)                     │
│ ├─ Crawler VM (24/7)                            │
│ └─ Analyst VM (Weekday 9-16)                    │
│                                                  │
│ Azure PostgreSQL Flexible Server (Optional)     │
│ └─ Burstable B2s (2 vCore, 4GB RAM)             │
│                                                  │
│ Azure Blob Storage (Optional)                   │
│ └─ Hot tier for recent media                    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              APPLICATION LAYER                   │
├─────────────────────────────────────────────────┤
│ Python 3.9+                                     │
│ ├─ Crawlers: selenium, beautifulsoup4          │
│ ├─ Processing: easyocr, whisper, konlpy        │
│ ├─ Analytics: pandas, scikit-learn, statsmodels│
│ ├─ DB: psycopg2, sqlalchemy                    │
│ └─ Visualization: matplotlib, seaborn          │
│                                                  │
│ Power BI Desktop                                │
│ └─ PostgreSQL connector                         │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              DATA LAYER                          │
├─────────────────────────────────────────────────┤
│ PostgreSQL 15                                   │
│ ├─ JSONB support (flexible schema)             │
│ ├─ Full-text search (Korean)                   │
│ └─ Array types (hashtags, URLs)                │
│                                                  │
│ File System                                     │
│ ├─ /data/raw/*.json                            │
│ ├─ /data/processed/*.csv                       │
│ └─ /models/*.pkl                               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│              DEVELOPMENT TOOLS                   │
├─────────────────────────────────────────────────┤
│ IDE: Windsurf (Claude Cascade integration)     │
│ AI Assistants: Claude 3.5 Sonnet, Cursor       │
│ Version Control: Git + GitHub                   │
│ Notebooks: Jupyter Lab                          │
└─────────────────────────────────────────────────┘
4.4 정보 아키텍처 (Information Architecture)
text
PM SNS Analysis Information Hierarchy

Level 1: Business Questions (What we need to know)
├─ Activity Patterns
│   ├─ Q1: How frequently do TPs post on each platform?
│   ├─ Q2: What are posting patterns of high vs low performers?
│   └─ Q3: What is the optimal posting time?
│
├─ Content Types
│   ├─ Q4: Which content types are most effective?
│   ├─ Q5: Optimal hashtag count?
│   └─ Q6: Best hashtag combinations?
│
├─ Engagement
│   ├─ Q7: Average engagement rate by platform?
│   ├─ Q8: Factors correlating with high engagement?
│   └─ Q9: Sentiment vs engagement relationship?
│
├─ Performance Impact
│   ├─ Q10: Correlation between SNS activity and sales?
│   ├─ Q11: Which platform contributes most to sales?
│   └─ Q12: Multi-platform usage effects?
│
└─ Risk Management
    ├─ Q13: Percentage of potentially misleading posts?
    └─ Q14: Negative sentiment ratio and impacts?

Level 2: Data Entities (What we collect)
├─ Users
│   ├─ Identity: user_id, name, platform
│   ├─ Profile: bio, followers, posts_count
│   └─ Performance: sales_rank, monthly_sales, team_size
│
├─ Posts
│   ├─ Metadata: post_id, url, published_date
│   ├─ Content: title, text, hashtags
│   ├─ Media: images, videos, OCR, transcripts
│   └─ Metrics: likes, comments, views, shares
│
└─ Aggregations
    ├─ Daily: posts_count, engagement_avg
    ├─ Weekly: trends, patterns
    └─ Monthly: growth, performance

Level 3: Features (What we derive)
├─ Activity
│   ├─ posts_per_week
│   ├─ posting_consistency
│   └─ active_hours
│
├─ Content
│   ├─ avg_content_length
│   ├─ hashtag_diversity
│   └─ media_usage_ratio
│
├─ Engagement
│   ├─ avg_engagement_rate
│   ├─ viral_post_ratio
│   └─ sentiment_score
│
└─ Network
    ├─ platform_count
    ├─ team_keyword_usage
    └─ recruitment_post_ratio

Level 4: Insights (What we learn)
├─ Clusters
│   ├─ Super Engagers
│   ├─ Steady Contributors
│   ├─ Casual Users
│   └─ Influencers
│
├─ Patterns
│   ├─ Best practices from top performers
│   ├─ Content strategies by cluster
│   └─ Platform-specific tactics
│
└─ Recommendations
    ├─ Personalized action items
    ├─ Risk mitigation strategies
    └─ Training materials

Level 5: Actions (What we do)
├─ Individual
│   ├─ Coaching based on cluster
│   ├─ Content recommendations
│   └─ Platform optimization
│
├─ Team
│   ├─ Best practice sharing
│   ├─ Team collaboration
│   └─ Collective learning
│
└─ Organization
    ├─ Strategic decisions
    ├─ Resource allocation
    └─ Policy enforcement
5. 비용 최적화 가이드
5.1 현재 Azure 비용 (월간)
리소스	사양	사용 패턴	월 비용
Crawler VM	D8as_v5 (8 vCore, 32GB)	24/7	$306.60
Analyst VM	D8as_v5 (8 vCore, 32GB)	120시간/월	$50.40
총 VM 비용			$357.00
5.2 DB 옵션별 비용
DB 솔루션	사양	월 비용	비고
PostgreSQL on VM	Self-hosted	$0	✅ 최저 비용, VM 리소스 공유
Azure PostgreSQL Flexible B2s	2 vCore, 4GB, 64GB	~$50	관리형, 고가용성
Supabase Self-hosted	Docker on VM	$0	무료, 추가 기능 (Auth, API)
Azure Cosmos DB	400 RU/s	$200+	❌ 과도한 비용
최종 권장: Crawler VM에 PostgreSQL 설치 ($0 추가 비용)

5.3 음성 인식 비용
솔루션	비용 구조	376건 (평균 5분) 예상 비용
Whisper Self-hosted	무료 (GPU 없어도 가능)	$0 ✅
Naver Clova	10만자 무료 → ₩15/1000자	$0 (무료 한도 내)
Google STT	$0.024/분	~$45
Azure Speech	$1/시간	~$31
최종 권장: Whisper Small 모델 (무료) + 전처리

5.4 총 비용 최적화 시나리오
시나리오 A: 현재 계획 (Azure 중심)

VM: $357

Azure PostgreSQL: $50

Google STT: $45

총: $452/월

시나리오 B: 최적화 (권장) ⭐

VM: $357 (동일)

PostgreSQL on VM: $0

Whisper Self-hosted: $0

총: $357/월 (21% 절감)

시나리오 C: 극한 절약

Crawler VM을 D4s_v5로 다운그레이드: $175 (24/7)

Analyst VM 유지: $50

PostgreSQL on VM: $0

Whisper: $0

총: $225/월 (50% 절감)

⚠️ 단, 크롤링 속도 저하 가능

6. 최종 권장사항
6.1 즉시 실행 (이번 주)
✅ Git 버전 관리 시작 - 코드 안정성 확보

✅ Crawler VM에 PostgreSQL 설치 - DB 구축 ($0 비용)

✅ Whisper 전처리 파이프라인 구현 - 음성 인식 개선

✅ 버그 우선순위 정리 및 해결 - 안정적 크롤링

6.2 다음 주 화요일 보고 시 제출 자료
기술 아키텍처 문서 (이 보고서)

Power BI 대시보드 (.pbix 파일)

주요 인사이트 요약 (1-2페이지)

피처 정의서 (user_features.csv + 설명)

클러스터 프로파일 (시각화 포함)

향후 3개월 로드맵

6.3 3주 후 최종 발표 준비사항
완전 자동화된 크롤링 시스템 (cron job 설정)

성과 예측 모델 (R² > 0.6 목표)

대시보드 v2.0 (실시간 연동)

AI 개발 로드맵 (6개월 계획)

운영 매뉴얼 (크롤러 설정, DB 관리, 대시보드 사용법)

6.4 AI 개발 현실적 목표
3주 내 가능:

✅ 회귀 분석 (성과 예측)

✅ 클러스터링 (사용자 유형화)

✅ 키워드 추출 (TF-IDF)

✅ 기본 감성 분석 (키워드 기반)

3-6개월 필요:

⏳ 딥러닝 NLP (KoBERT Fine-tuning)

⏳ 이탈 예측 모델

⏳ 추천 시스템

조언: 3주 내 "AI 개발의 기초"를 탄탄히 하고, 향후 6개월 로드맵을 명확히 제시하세요. 현재 수준에서 KoBERT 등 고급 NLP는 무리이며, 오히려 기본 모델의 완성도를 높이는 게 낫습니다.

7. 마무리 및 격려
프로젝트 진행 상황을 종합적으로 분석한 결과, 데이터 수집은 양호하지만 분석 파이프라인 구축이 시급합니다.

여러분의 강점:

✅ 13,000건 이상 데이터 확보 (충분한 분석 규모)

✅ 상무님 만족한 초기 EDA/대시보드 (방향성 검증됨)

✅ Azure VM 확보 (안정적 인프라)

집중해야 할 부분:

🎯 DB 구축 (가장 시급, 1-2일 내 완료 가능)

🎯 피처 추출 (3일 내 완료, 위 코드 활용)

🎯 대시보드 고도화 (Power BI, 2일 내)

3주는 충분합니다. 이 보고서에서 제시한 단계별 플랜을 따라가면 훌륭한 결과물을 만들 수 있습니다.

가장 중요한 조언:

완벽함보다 완성을 목표로 하세요 (80% 완성도면 충분)

Claude에게 묻기 전에 명확히 정의하세요 (문제, 입력, 기대 출력)

버전 관리를 생활화하세요 (작동하는 코드는 즉시 커밋)

매일 작은 성과를 축적하세요 (일일 체크리스트 활용)

화이팅입니다! 궁금한 점이 있으면 언제든 물어보세요. 🚀

오늘 저는 PM 판매원 SNS 분석 프로젝트에 대해 현황파악, 중간점검, 트러블슈팅 방안, 앞으로 할 일, 이후 설계 등등을 했습니다. 
오늘 한 일을 첨부한 포맷과 같이 보고서에 쓸 수 있도록 간단하게 정리해주세요. Personal Branding: Contents Data Specialist 프로젝트에서 한 일 중에서  PM 판매원 SNS 분석 프로젝트와 관련된 부분도 합쳐서 정리해주세요.


ilil-eobmuilji-gimhoyeon-12.02.xlsx
네, 오늘 하신 작업을 첨부하신 일일 업무일지 포맷에 맞춰 정리해드리겠습니다.

일일 업무일지
부서명: PI
작성자: 김호연
작성일자: 2025년 11월 24일
금일 출근시간: (기재)
금일 퇴근시간: (기재)

업무 시간별 내용
업무 시간: 오전~오후
업무 내용
PM 판매원 SNS 분석 프로젝트 중간점검 및 전략 수립

Personal Branding: Contents Data Specialist 관련 프로젝트 분석

처리 내용
1. 프로젝트 현황 파악 및 진단

데이터 수집 현황 종합 분석 (5개 플랫폼, 총 13,335건)

네이버 블로그: 7,890건 (정제 261건), 완성도 90%

카카오스토리: 4,769건, 완성도 85%

유튜브: 376건, 완성도 60% (Whisper 음성인식 문제)

인스타그램: ~300건, 완성도 50% (URL 임시전용 문제)

네이버 카페: 테스트 중, 완성도 10%

데이터 품질 분석 (네이버 블로그 샘플 261건 기준)

양호 컬럼: title (96.5%), content (100%), hashtags (90.4%)

문제 컬럼: profile_nickname (0%), image_ocr_text (0%), sponsor_phone (17.2%)

평균 본문 길이: 1,672자, 주요 콘텐츠 타입: Undisclosed_Ad (36.8%)

2. 핵심 문제점 분석 및 해결방안 수립

크롤링 버그 및 디버깅 전략

문제: Claude 기반 반복 디버깅으로 이전 버그 재발

해결방안: 체계적 개발 워크플로우 구축 (Git 버전 관리, 모듈화, AI 툴 최적 활용)

코드 구조화 방안 설계 (crawlers/, processors/, utils/ 분리)

멀티미디어 처리 개선

Whisper 음성인식 문제 원인 분석 (임시 URL, 음소거, 모델 한계)

다층 음성 인식 전략 수립 (Whisper → Google STT → Naver Clova)

음성 전처리 최적화 방안 설계 (샘플레이트 정규화, 볼륨 정규화)

대안 솔루션 비교 분석 (6개 STT 서비스 정확도/비용/속도 평가)

3. 데이터베이스 설계 재검토

DB 구축 개념 정립 및 단계 정의

데이터 모델링 → 스키마 정의 → 인덱스 최적화 → ETL → 백업/복구

하이브리드 아키텍처 설계 (PostgreSQL + JSONB)

NoSQL vs RDBMS 비교 분석 완료

PostgreSQL 선택 근거: 구조화된 쿼리, JOIN 성능, Power BI 연동, 비용 효율

데이터 흐름 간소화: 크롤러 → 전처리 → PostgreSQL → 분석/시각화

Blob Storage 선택적 사용 전략 수립

DB 스키마 설계 (v2.0)

dim_users (사용자 차원 테이블) 설계

fact_posts (게시물 팩트 테이블) 설계

agg_daily_metrics (일별 집계 테이블) 설계

JSONB 컬럼 활용 설계 (비정형 데이터 유연성 확보)

인덱스 전략 수립 (GIN 인덱스, Full-Text Search)

ETL 파이프라인 코드 설계 완료

4. 데이터 분석 전략 수립

주요 피처 설계 (20개)

활동 패턴: posts_per_week, posting_consistency, active_hours 등

콘텐츠 특성: avg_content_length, hashtag_diversity, media_usage_ratio 등

참여도: avg_engagement_rate, viral_post_ratio 등

플랫폼 활용: platform_count, cross_platform_ratio 등

네트워크 영향: sponsor_mention_count, recruitment_post_ratio 등

Feature Extraction 코드 설계 완료

_activity_features() 메서드

_content_features() 메서드

_engagement_features() 메서드

_platform_features() 메서드

_network_features() 메서드

클러스터링 방법론 개선

K-Means 한계 분석 (구형 클러스터만 감지, 이상치 민감)

다중 클러스터링 방법 비교 설계 (K-Means, Hierarchical, DBSCAN)

Silhouette/Davies-Bouldin 기반 최적 모델 선택 알고리즘 설계

클러스터 프로파일링 및 명명 전략 수립

5. AI 모델 개발 로드맵 수립

3주 내 구현 가능 모델 설계

성과 예측 모델 (회귀 분석): Ridge, Lasso, Random Forest, GBM 비교

감성 분석 (기본): 키워드 기반 감성 분석 설계

키워드 추출: TF-IDF 기반 추출 알고리즘 설계

장기 로드맵 (3-6개월) 수립

Phase 1: 기초 NLP (감성 분석 고도화, 토픽 모델링)

Phase 2: 고급 예측 모델 (이탈 예측, 추천 시스템)

Phase 3: 자동화 및 통합 (실시간 리스크 탐지, 자동 리포트)

6. 시스템 아키텍처 설계

전체 시스템 아키텍처 다이어그램 작성

Data Collection Layer → Processing Layer → Storage Layer → Analytics Layer → Visualization Layer

데이터 흐름 아키텍처 설계

Phase별 Input/Process/Output/Storage 정의

기술 스택 아키텍처 정리

Infrastructure: Azure VM, PostgreSQL

Application: Python (crawlers, processing, analytics), Power BI

Data: PostgreSQL 15 (JSONB, Full-text search, Array types)

정보 아키텍처 (Information Architecture) 수립

Level 1: Business Questions (15개 핵심 질문)

Level 2: Data Entities (Users, Posts, Aggregations)

Level 3: Features (Activity, Content, Engagement, Network)

Level 4: Insights (Clusters, Patterns, Recommendations)

Level 5: Actions (Individual, Team, Organization)

7. 실행 계획 수립

7일 Day-by-Day 액션 플랜 작성

Day 1-2: 크롤링 마무리 및 안정화 (에러율 5% 이하)

Day 3-4: DB 구축 및 데이터 적재 (PostgreSQL 설치, 스키마 생성, ETL)

Day 5: 피처 추출 및 클러스터링 (20개 피처, 4-6개 클러스터)

Day 6: 분석 및 인사이트 도출 (핵심 질문 5개 이상 답변)

Day 7: 대시보드 및 보고서 완성 (Power BI 4페이지, 최종 보고서)

역할 분담 정의

김호연: 네이버 블로그/유튜브 크롤링, DB 구축, 클러스터링

권서연: 카카오스토리/인스타그램 크롤링, 피처 엔지니어링, EDA

8. 비용 최적화 분석

현재 Azure 비용 분석: VM $357/월

DB 옵션별 비용 비교 (PostgreSQL on VM $0 vs Azure PostgreSQL $50)

음성 인식 솔루션 비용 비교 (Whisper $0 vs Google STT $45)

최적화 시나리오 수립: $452/월 → $357/월 (21% 절감)

9. 최종 권장사항 정리

즉시 실행 항목 (이번 주): Git 버전 관리, PostgreSQL 설치, Whisper 전처리, 버그 해결

다음 주 화요일 제출 자료: 기술 아키텍처 문서, Power BI 대시보드, 인사이트 요약, 피처 정의서, 클러스터 프로파일

3주 후 최종 발표 준비사항: 완전 자동화 크롤링, 성과 예측 모델, 대시보드 v2.0, 운영 매뉴얼

업무 요약
PM 판매원 SNS 분석 프로젝트 중간점검 및 재설계 완료

현황 진단, 문제점 분석, 해결방안 수립 (크롤링, 멀티미디어 처리, DB 구축)

데이터 분석 전략 및 AI 모델 개발 로드맵 수립

전체 시스템 아키텍처 및 정보 아키텍처 설계 완료

7일 실행 계획 및 최종 권장사항 도출

중요 사항
PostgreSQL + JSONB 하이브리드 아키텍처 채택 (비용 $95 절감)

다층 음성 인식 전략으로 Whisper 문제 해결 방안 수립

주요 피처 20개 설계 완료 → 클러스터링 및 회귀 분석 준비 완료

3주 내 실현 가능한 AI 모델과 장기 로드맵 명확히 구분

다음 주 화요일 보고 시 제출할 6가지 산출물 정의 완료

참고: 오늘 작업은 프로젝트의 기술적 설계 및 전략 수립에 집중했으며, 향후 7일간 실행할 구체적인 코드 구현 및 데이터 처리 작업의 청사진을 완성했습니다.