import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import re

from langchain_naver import ChatClovaX
from langchain_community.tools.tavily_search import TavilySearchResults
from clova_config import MODEL_PARAMS
from agent.agents import StructuredAgent, UnstructuredAgent, WebAgent, Orchestrator

# ------------------------------------------------------------------------------
# 환경설정
# ------------------------------------------------------------------------------
os.environ["TRANSFORMERS_NO_TF"] = "1"
load_dotenv()

OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE  = os.getenv("OPENAI_API_BASE")
TAVILY_API_KEY   = os.getenv("TAVILY_API_KEY")
PG_HOST          = os.getenv("PG_HOST")
PG_PORT          = os.getenv("PG_PORT")
PG_NAME          = os.getenv("PG_NAME")
PG_USER          = os.getenv("PG_USER")
PG_PASSWORD      = os.getenv("PG_PASSWORD")

if not all([OPENAI_API_KEY, OPENAI_API_BASE, TAVILY_API_KEY,
            PG_HOST, PG_PORT, PG_NAME, PG_USER, PG_PASSWORD]):
    st.error(".env에 필요한 환경변수를 모두 설정 바람")
    st.stop()

os.environ["OPENAI_API_KEY"]  = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

st.set_page_config(page_title="나만의 AI 애널리스트", layout="wide")

# CSS 스타일 
st.markdown("""
<style>
:root {
  --font-size: 14px;
  --background: #ffffff;
  --foreground: oklch(0.145 0 0);
  --card: #ffffff;
  --card-foreground: oklch(0.145 0 0);
  --primary: #030213;
  --primary-foreground: oklch(1 0 0);
  --secondary: oklch(0.95 0.0058 264.53);
  --secondary-foreground: #030213;
  --muted: #ececf0;
  --muted-foreground: #717182;
  --accent: #e9ebef;
  --accent-foreground: #030213;
  --destructive: #d4183d;
  --destructive-foreground: #ffffff;
  --border: rgba(0, 0, 0, 0.1);
  --input: transparent;
  --input-background: #f3f3f5;
  --radius: 0.625rem;
  --sidebar: oklch(0.985 0 0);
  --sidebar-foreground: oklch(0.145 0 0);
}

/* 다크모드 */
@media (prefers-color-scheme: dark) {
  :root {
    --background: oklch(0.145 0 0);
    --foreground: oklch(0.985 0 0);
    --card: oklch(0.145 0 0);
    --card-foreground: oklch(0.985 0 0);
    --primary: oklch(0.985 0 0);
    --primary-foreground: oklch(0.205 0 0);
    --secondary: oklch(0.269 0 0);
    --secondary-foreground: oklch(0.985 0 0);
    --muted: oklch(0.269 0 0);
    --muted-foreground: oklch(0.708 0 0);
    --accent: oklch(0.269 0 0);
    --accent-foreground: oklch(0.985 0 0);
    --border: oklch(0.269 0 0);
    --input: oklch(0.269 0 0);
    --sidebar: oklch(0.205 0 0);
    --sidebar-foreground: oklch(0.985 0 0);
  }
}

/* 전체 배경 및 텍스트 */
body, .stApp, .block-container {
  background-color: var(--background) !important;
  color: var(--foreground) !important;
}

/* 카드 스타일 */
.stCard {
  background-color: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: 1rem !important;
}

/* 채팅 메시지 스타일 */
.stChatMessage {
  background-color: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

/* 입력 필드 스타일 */
.stTextInput > div > div > input {
  background-color: var(--input-background) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
  background-color: var(--card) !important;
  border-bottom: 1px solid var(--border) !important;
}

.stTabs [data-baseweb="tab"] {
  color: var(--foreground) !important;
}

.stTabs [aria-selected="true"] {
  color: var(--primary) !important;
  border-bottom: 2px solid var(--primary) !important;
}

/* 사이드바 스타일 */
[data-testid="stSidebar"] {
  background-color: var(--sidebar) !important;
  color: var(--sidebar-foreground) !important;
}

/* TradingView 컨테이너 */
.tradingview-widget-container {
  background-color: var(--card) !important;
  border: none !important;
  border-radius: var(--radius) !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 나만의 맞춤형 AI 애널리스트")

# user_stocks 초기화
if "user_stocks" not in st.session_state:
    st.session_state["user_stocks"] = [
        {"종목명":"Apple Inc.","티커":"AAPL","수량":5,"평균단가":150},
        {"종목명":"Nvidia Corp.","티커":"NVDA","수량":3,"평균단가":200},
        {"종목명":"Microsoft Corp.","티커":"MSFT","수량":10,"평균단가":300},
        {"종목명":"Amazon.com, Inc.","티커":"AMZN","수량":2,"평균단가":100},
        {"종목명":"Alphabet Inc.","티커":"GOOGL","수량":4,"평균단가":140},
    ]

# ------------------------------------------------------------------------------
# LLM & Tool
# ------------------------------------------------------------------------------
llm = ChatClovaX(
    model="HCX-005",
    max_tokens=MODEL_PARAMS["max_tokens"],
    temperature=MODEL_PARAMS["temperature"],
    top_p=MODEL_PARAMS["top_p"],
    stream=False,
)
search_tool = TavilySearchResults(api_key=TAVILY_API_KEY, max_results=5)

# 인스턴스 생성
db_params = {
    "dbname": PG_NAME, "user": PG_USER, "password": PG_PASSWORD,
    "host": PG_HOST,   "port": PG_PORT
}
sa = StructuredAgent()
ua = UnstructuredAgent()
wa = WebAgent(search_tool)
orchestrator = Orchestrator(sa, ua, wa, llm)

# ------------------------------------------------------------------------------
# 탭 기반 레이아웃
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💼 Portfolio", "📈 Journey", "🤖 AI Chat"])

with tab1:
    st.header("대시보드")
    
    # AgentNotifications (알림 섹션)
    with st.container():
        st.subheader("🔔 오늘의 알림")
        st.info("엔비디아(NVDA)가 전일 대비 8.2% 상승했습니다. AI 칩 수요 증가로 긍정적인 전망이 나오고 있습니다.")
    
    # PerformanceSummary (성과 요약)
    with st.container():
        st.subheader("📈 포트폴리오 성과 요약")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 자산", "$12,450", "+6.07%")
        with col2:
            st.metric("일간 수익", "+$712", "+2.1%")
        with col3:
            st.metric("월간 수익", "+$1,234", "+4.3%")
        with col4:
            st.metric("연간 수익", "+$2,890", "+12.5%")

with tab2:
    st.header("포트폴리오")
    
    # PortfolioChart (포트폴리오 차트)
    with st.container():
        st.subheader("📊 포트폴리오 차트")
        # TradingView 차트 예시
        chart_html = """
        <div class="tradingview-widget-container">
          <div id="tv_portfolio"></div>
          <script src="https://s3.tradingview.com/tv.js"></script>
          <script>
          new TradingView.widget({
            "width": "100%",
            "height": 400,
            "symbol": "NASDAQ:AAPL",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "light",
            "style": "1",
            "locale": "kr",
            "toolbar_bg": "#f1f3f6",
            "container_id": "tv_portfolio"
          });
          </script>
        </div>
        """
        components.html(chart_html, height=450)
    
    # AssetSummaryCards (자산 요약 카드)
    with st.container():
        st.subheader("💼 자산 요약")
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container():
                st.markdown("""
                <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem;">
                    <h4>📈 해외 주식</h4>
                    <p style="font-size: 24px; font-weight: bold; color: #10b981;">$5,450</p>
                    <p style="color: var(--muted-foreground);">+6.71% (이번 달)</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            with st.container():
                st.markdown("""
                <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem;">
                    <h4>🇰🇷 국내 주식</h4>
                    <p style="font-size: 24px; font-weight: bold; color: #10b981;">$5,450</p>
                    <p style="color: var(--muted-foreground);">+5.43% (이번 달)</p>
                </div>
                """, unsafe_allow_html=True)
        
        col3, col4 = st.columns(2)
        with col3:
            with st.container():
                st.markdown("""
                <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem;">
                    <h4>💰 현금</h4>
                    <p style="font-size: 24px; font-weight: bold; color: var(--foreground);">$1,550</p>
                    <p style="color: var(--muted-foreground);">12.5% 비중</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            with st.container():
                st.markdown("""
                <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem;">
                    <h4>📊 전체</h4>
                    <p style="font-size: 24px; font-weight: bold; color: #10b981;">$12,450</p>
                    <p style="color: var(--muted-foreground);">+6.07% (총 수익률)</p>
                </div>
                """, unsafe_allow_html=True)

with tab3:
    st.header("투자 여정")
    
    # InvestmentJourney (투자 여정)
    with st.container():
        st.subheader("🚀 투자 여정")
        
        # 타임라인 형태로 투자 히스토리 표시
        timeline_data = [
            {"date": "2024-01-15", "action": "첫 투자 시작", "amount": "$5,000", "description": "애플, 엔비디아 첫 매수"},
            {"date": "2024-03-20", "action": "포트폴리오 확장", "amount": "$3,000", "description": "마이크로소프트, 아마존 추가"},
            {"date": "2024-06-10", "action": "리밸런싱", "amount": "$2,000", "description": "알파벳 추가, 비중 조정"},
            {"date": "2024-09-05", "action": "수익 실현", "amount": "$1,500", "description": "일부 수익 실현 및 현금 보유"},
        ]
        
        for i, item in enumerate(timeline_data):
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.5rem;">
                        <div style="width: 40px; height: 40px; border-radius: 50%; background-color: var(--primary); color: var(--primary-foreground); display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                            {i+1}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style="background-color: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; margin-bottom: 1rem;">
                        <h4>{item['action']}</h4>
                        <p style="color: var(--muted-foreground);">{item['date']} • {item['amount']}</p>
                        <p>{item['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)

with tab4:
    st.header("AI 애널리스트")
    # 기존 LLM 채팅 기능
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # 히스토리 먼저 렌더링
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        elif msg["role"] == "assistant":
            if msg.get("tradingview_html"):
                components.html(msg["tradingview_html"], height=450)
            st.chat_message("assistant").write(msg["content"])
            with st.expander("🤔 사용된 에이전트 유형", expanded=False):
                st.markdown(f"**선택된 에이전트:** {msg.get('agent_type','-')}")

    # 사용자 입력 처리 (입력 시에만 메시지 추가)
    if user_input := st.chat_input("메시지를 입력하세요..."):
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)  # 사용자 질문을 즉시 채팅창에 출력
        with st.spinner("답변 생성 중..."):
            answer, tradingview_html, agent_type = orchestrator.route(user_input, st.session_state["user_stocks"], db_params)
        st.session_state["messages"].append({"role": "assistant", "content": answer, "agent_type": agent_type, "tradingview_html": tradingview_html})
        st.experimental_rerun()