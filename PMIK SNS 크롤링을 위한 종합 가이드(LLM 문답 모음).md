# PMI Korea SNS 크롤링 프로젝트를 위한 AI 코딩 도구 종합 가이드

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