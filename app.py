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

st.title("📊 나만의 맞춤형 AI 애널리스트 에이전트 (다크 모드)")

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
class StructuredAgent:
    def run(self, user_input, user_stocks, db_params):
        mapping = {"애플":"AAPL","엔비디아":"NVDA","마이크로소프트":"MSFT",
                   "아마존":"AMZN","알파벳":"GOOGL"}
        symbol = next((sym for kor,sym in mapping.items() if kor in user_input), None)
        if symbol:
            conn = psycopg2.connect(**db_params)
            cur  = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1",
                (symbol,)
            )
            row = cur.fetchone()
            conn.close()
            price = row["close"] if row else None
            return f"{symbol} 현재가: {price}"
        return None

class UnstructuredAgent:
    def run(self, user_input, user_stocks, db_params):
        conn = psycopg2.connect(**db_params)
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT metadata->>'source' AS source, document AS summary
              FROM company_reports
          ORDER BY id DESC LIMIT 3
        """)
        rows = cur.fetchall()
        conn.close()
        return "\n".join(f"{r['source']}: {r['summary']}" for r in rows)

class WebAgent:
    def __init__(self, search_tool):
        self.search_tool = search_tool
    def run(self, user_input, *_):
        results = self.search_tool.run(user_input)
        return "\n".join(
            f"- {item.get('title','')} : {item.get('content','')[:100]}… ({item.get('url','')})"
            for item in results
        )

class Orchestrator:
    def __init__(self, sa, ua, wa, llm):
        self.sa   = sa
        self.ua   = ua
        self.wa   = wa
        self.llm  = llm

    def route(self, user_input, user_stocks, db_params):
        today = datetime.now().strftime("%Y-%m-%d")
        # 에이전트 선택
        if re.search(r"(주가|가격)", user_input):
            context = self.sa.run(user_input, user_stocks, db_params) or ""
        elif re.search(r"(검색|뉴스|기사|웹)", user_input):
            context = self.wa.run(user_input, user_stocks, db_params)
        else:
            context = self.ua.run(user_input, user_stocks, db_params)

        system_msg = f"오늘 날짜는 {today}입니다. 아래 정보를 참고하여 **한국어**로만 답변해 주세요."
        human_msg  = f"[컨텍스트]\n{context}\n\n[질문]\n{user_input}"

        ai_msg = self.llm.invoke([
            ("system", system_msg),
            ("human", human_msg)
        ])
        return ai_msg.content

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
        # 예시 종목
        st.session_state["user_stocks"] = [
            {"종목명":"Apple Inc.","티커":"AAPL","수량":5,"평균단가":150},
            {"종목명":"Nvidia Corp.","티커":"NVDA","수량":3,"평균단가":200},
        ]
    stocks = st.session_state["user_stocks"]

    conn = psycopg2.connect(**db_params)
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    sidebar_data = []
    for s in stocks:
        cur.execute(
            "SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1",
            (s["티커"],)
        )
        row = cur.fetchone()
        price = row["close"] if row else None
        sidebar_data.append({
            "종목명": s["종목명"],
            "티커":   s["티커"],
            "수량":   s["수량"],
            "현재가": f"{price:,}" if price else "-",
            "평균단가": f"{s['평균단가']:,}"
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

    # 1) 주가 질의 감지
    kor2sym = {"애플":"AAPL","엔비디아":"NVDA","마이크로소프트":"MSFT",
               "아마존":"AMZN","알파벳":"GOOGL"}
    symbol = next((v for k,v in kor2sym.items() if k in user_input), None)

    if symbol:
        # TradingView 다크 모드 위젯
        widget_html = f"""
        <div class="tradingview-widget-container">
          <div id="tv_{symbol}"></div>
          <script src="https://s3.tradingview.com/tv.js"></script>
          <script>
          new TradingView.widget({{
            "width": "100%",
            "height": 400,
            "symbol": "NASDAQ:{symbol}",
            "interval": "D",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "kr",
            "toolbar_bg": "#2b2b2b",
            "container_id": "tv_{symbol}"
          }});
          </script>
        </div>
        """
        components.html(widget_html, height=450)

        # DB에서 현재가 조회
        conn = psycopg2.connect(**db_params)
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1",
            (symbol,)
        )
        row = cur.fetchone()
        conn.close()
        current = row["close"] if row else None

        # 차트 하단에 현재가
        st.markdown(f"**현재 {symbol} 주가:** `{current:.2f}` USD")

        # 2) LLM 최종 답변 호출
        answer = orchestrator.route(user_input, st.session_state["user_stocks"], db_params)
        st.chat_message("assistant").write(answer)
        st.session_state["messages"].append({"role":"assistant","content":answer})

    else:
        # 일반 RAG 대화 흐름
        st.session_state["messages"].append({"role":"user","content":user_input})
        st.chat_message("user").write(user_input)
        with st.spinner("응답 생성 중…"):
            raw = orchestrator.route(user_input, st.session_state["user_stocks"], db_params)
        st.chat_message("assistant").write(raw)
        st.session_state["messages"].append({"role":"assistant","content":raw})
