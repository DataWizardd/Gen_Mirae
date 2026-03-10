# 📊 Mirae Asset 나만의 AI 애널리스트

<!-- <img width="400" alt="Mirae 투자 포트폴리오 AI 애널리스트" src="https://github.com/user-attachments/assets/735dd787-bae7-4094-adc1-445fa7981080" /> -->

### 📱 주요 화면들
<div align="center">
  <img width="250" alt="대시보드" src="https://github.com/user-attachments/assets/27bb3926-92eb-40f7-bc0f-87771511d2ed" />
  <br><br>
  <img width="250" alt="인사이트" src="https://github.com/user-attachments/assets/d741ba0d-1407-4f99-b9c9-2efe4d85ba22" />
  <img width="250" alt="리포트" src="https://github.com/user-attachments/assets/600abb12-7bb1-4eef-9f8d-7b36ba0a9ea3" />
  <br><br>
  <img width="250" alt="종목 발굴" src="https://github.com/user-attachments/assets/ea58d32d-bd6a-4e90-ab91-605327646dff" />
  <img width="250" alt="ChatBot" src="https://github.com/user-attachments/assets/6c35253e-483c-441c-9847-eecab0fa0575" />
</div>

## 🎯 프로젝트 개요

프로젝트 Gen_Mirae는 개인 투자자를 위한 AI 기반 투자 포트폴리오 분석 및 관리 시스템입니다. 다양한 데이터 소스에서 정보를 수집하고 AI를 활용하여 개인화된 투자 인사이트를 제공합니다.

## 🏗️ 프로젝트 구조

```
Gen_Mirae/
├── 📁 agent/                    # AI 멀티에이전트 시스템
│   ├── base.py                # BaseAgent 추상 클래스 및 데이터 모델
│   ├── tools.py               # 에이전트 도구(Tool) 레지스트리
│   ├── orchestrator.py        # 오케스트레이터 (쿼리 분석 → 디스패치 → 종합)
│   ├── specialists.py         # 전문 에이전트 (Price/News/Financial/Event)
│   ├── report_agent.py        # 리포트 생성 에이전트
│   ├── data_retrieval.py      # 데이터 조회 로직
│   └── pdf_generator.py       # PDF 리포트 생성
├── 📁 collectors/              # 데이터 수집기들
│   ├── edgar_collector.py      # SEC EDGAR 공시자료
│   ├── news_collector.py       # 뉴스 데이터
│   ├── reddit_collector.py     # Reddit 투자 커뮤니티
│   ├── gdelt_collector.py      # GDELT 글로벌 이벤트
│   ├── stock_collector*.py     # 주식 데이터 (실시간/일별)
│   ├── valuation_collector.py  # 기업 밸류에이션
│   └── run_collectors.py       # 수집기 통합 실행
├── 📁 config/                  # 설정 파일들
│   ├── clova_config.py         # Clova AI 설정
│   ├── *.sql                   # 데이터베이스 스키마
│   └── install_database.sh     # DB 설치 스크립트
├── 📁 deployment/              # 배포 관련 파일들
│   ├── deploy.py              # Python 배포 스크립트
│   ├── deploy_improved.sh     # 개선된 배포 스크립트
│   ├── ecosystem.config.js    # PM2 설정
│   ├── mirae-api.service      # systemd 서비스
│   ├── mirae.nginx.conf       # Nginx 설정
│   ├── DEPLOYMENT_GUIDE.md    # 배포 가이드
│   └── DATABASE_SETUP.md      # DB 설치 가이드
├── 📁 tests/                   # 테스트 파일들
│   ├── test_connection.py     # 데이터베이스 연결 테스트
│   ├── test_single_collection.py
│   └── test_concurrent_reports.py
├── 📁 frontend/                # React 프론트엔드 (레거시)
├── 📁 src/                     # 메인 React 프론트엔드
├── 📁 notebook/                # 데이터 수집 test 
├── 📁 report/                  # 생성된 리포트들
├── 📁 archive/                 # 압축 파일 보관소
├── api.py                      # FastAPI 백엔드
└── README.md                   # 이 파일
```

## 🚀 주요 기능

### 📈 데이터 수집
- **주식 데이터**: 실시간 및 일별 주가 정보
- **뉴스 분석**: 주식 관련 뉴스 수집 및 감정 분석
- **SEC 공시**: 기업 공시자료 자동 수집
- **소셜 미디어**: Reddit 투자 커뮤니티 분석
- **글로벌 이벤트**: GDELT 데이터를 통한 글로벌 이벤트 모니터링

### 🤖 AI 멀티에이전트 분석
- **OrchestratorAgent**: 사용자 쿼리를 LLM으로 분석하고, 전문 에이전트에게 작업 위임 후 결과 종합
- **PriceAnalystAgent**: 주가 시계열 및 밸류에이션 전문 분석
- **NewsAnalystAgent**: 뉴스 흐름 및 시장 여론 분석
- **FinancialAnalystAgent**: 재무제표 및 SEC 공시 심층 분석
- **EventAnalystAgent**: GDELT 기반 거시경제·지정학적 리스크 분석
- **ReportAgent**: 전문 에이전트 협업 기반 종합 리포트 생성

### 💻 사용자 인터페이스
- **React 대시보드**: 모던한 웹 인터페이스
- **모바일 반응형**: 모든 디바이스에서 접근 가능

## 🛠️ 설치 및 실행

### 요구사항
- Python 3.8+
- Node.js 16+
- PostgreSQL 15+
- Redis (선택사항)

### 1. 환경 설정
```bash
# 저장소 클론
git clone <repository-url>
cd Gen_Mirae

# Python 의존성 설치
pip install -r requirements.txt

# Node.js 의존성 설치
npm install
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 변수들을 설정:
```env
# 데이터베이스
PG_HOST=localhost
PG_PORT=5432
PG_NAME=mirae_db
PG_USER=mirae_user
PG_PASSWORD=your_password

# API 키들
TAVILY_API_KEY=your_tavily_key
CLOVA_API_KEY=your_clova_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
```

### 3. 데이터베이스 설정
```bash
# 데이터베이스 설치 (Ubuntu/Debian)
cd config
./install_database.sh

# 테이블 생성
psql -U mirae_user -d mirae_db -f create_stock_news_table.sql
psql -U mirae_user -d mirae_db -f create_reddit_posts_table.sql
# 다른 테이블들도 동일하게 생성
```

### 4. 애플리케이션 실행

#### 백엔드 (FastAPI)
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

#### 프론트엔드 (React)
```bash
npm start
```

#### Streamlit 앱
```bash
cd notebook
streamlit run app.py
```

#### 데이터 수집기
```bash
cd collectors
python run_collectors.py
```

## 📊 사용법

1. **대시보드 접속**: `http://175.106.97.51/`  (서버 중지 2025-08-28)
2. **AI 분석 요청**: 챗봇을 통한 대화형 분석
3. **리포트 확인**: 자동 생성된 투자 리포트 검토

## 🚀 배포

### 서버 배포
```bash
# 개선된 배포 스크립트 사용
cd deployment
./deploy_improved.sh

# 또는 Python 스크립트 사용
python deploy.py --server-ip YOUR_SERVER_IP --server-user root
```

자세한 배포 가이드는 [`deployment/DEPLOYMENT_GUIDE.md`](deployment/DEPLOYMENT_GUIDE.md)를 참조하세요.

