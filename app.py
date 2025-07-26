# app.py
# -*- coding: utf-8 -*-

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
    st.error("❗ .env에 필요한 환경변수를 모두 설정해주세요.")
    st.stop()

os.environ["OPENAI_API_KEY"]  = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

st.set_page_config(page_title="나만의 AI 애널리스트", layout="wide")
st.markdown(
    """
    <style>
      /* 전체 배경 및 텍스트 다크 모드 */
      body, .stApp, .block-container {
        background-color: #121212 !important;
        color: #e0e0e0 !important;
      }
      /* TradingView 컨테이너 덮어쓰기 */
      .tradingview-widget-container {
        background-color: #121212 !important;
        border: none !important;
      }
      /* 사이드바 배경 */
      [data-testid="stSidebar"] {
        background-color: #1e1e1e !important;
      }
      /* 채팅 박스 배경 */
      .stChatMessage {
        background-color: #1e1e1e !important;
      }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 나만의 맞춤형 AI 애널리스트 에이전트")

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

# ------------------------------------------------------------------------------
# 에이전트 정의 (생략된 부분은 이전 예시와 동일)
# ------------------------------------------------------------------------------

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
# 사이드바: 보유 주식 최신가
# ------------------------------------------------------------------------------
with st.sidebar:
    st.header("📈 보유 주식 현황")
    if "user_stocks" not in st.session_state:
        # 5개 종목 모두 추가
        st.session_state["user_stocks"] = [
            {"종목명":"Apple Inc.","티커":"AAPL","수량":5,"평균단가":150},
            {"종목명":"Nvidia Corp.","티커":"NVDA","수량":3,"평균단가":200},
            {"종목명":"Microsoft Corp.","티커":"MSFT","수량":10,"평균단가":300},
            {"종목명":"Amazon.com, Inc.","티커":"AMZN","수량":2,"평균단가":100},
            {"종목명":"Alphabet Inc.","티커":"GOOGL","수량":4,"평균단가":140},
        ]
    stocks = st.session_state["user_stocks"]

    # 매번 DB에서 조회
    conn = psycopg2.connect(**db_params)
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    sidebar_data = []
    for s in stocks:
        cur.execute(
            "SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1",
            (s["티커"],)
        )
        row   = cur.fetchone()
        price = row["close"] if row else None
        sidebar_data.append({
            "종목명":   s["종목명"],
            "티커":     s["티커"],
            "수량":     s["수량"],
            "평균단가": f"{s['평균단가']:,}",
            "현재가":   f"{price:,.2f}" if price is not None else "-",
            "평가액":   f"{price * s['수량']:,.2f}" if price is not None else "-",
            "수익률":   f"{(price - s['평균단가'])/s['평균단가']*100:.2f}%" if price is not None else "-",
        })
    conn.close()

    st.table(pd.DataFrame(sidebar_data))

# ------------------------------------------------------------------------------
# 메인: 채팅 + 차트 + LLM 답변
# ------------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 이전 메시지 렌더링
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# 사용자 입력
if user_input := st.chat_input("메시지를 입력하세요..."):
    with st.spinner("답변 생성 중..."):
        answer, tradingview_html, agent_type = orchestrator.route(user_input, st.session_state["user_stocks"], db_params)
    if tradingview_html:
        components.html(tradingview_html, height=450)
    with st.expander("🤔 사용된 에이전트 유형/경로", expanded=False):
        st.markdown(f"**선택된 에이전트:** {agent_type}")
    st.chat_message("assistant").write(answer)
    st.session_state["messages"].append({"role":"assistant","content":answer})
