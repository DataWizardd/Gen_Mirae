# api.py
# -*- coding: utf-8 -*-

import os
# import phoenix as px
# from phoenix.client import Client
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

from langchain_naver import ChatClovaX
from langchain_community.tools.tavily_search import TavilySearchResults
from clova_config import MODEL_PARAMS
from agent.agents import Orchestrator, StructuredAgent, UnstructuredAgent, WebAgent

# ------------------------------------------------------------------------------
# 환경설정
# ------------------------------------------------------------------------------
load_dotenv()

PHOENIX_URL      = os.getenv("PHOENIX_URL")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE  = os.getenv("OPENAI_API_BASE")
TAVILY_API_KEY   = os.getenv("TAVILY_API_KEY")
PG_HOST          = os.getenv("PG_HOST")
PG_PORT          = os.getenv("PG_PORT")
PG_NAME          = os.getenv("PG_NAME")
PG_USER          = os.getenv("PG_USER")
PG_PASSWORD      = os.getenv("PG_PASSWORD")

os.environ["OPENAI_API_KEY"]  = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

# 데이터베이스 파라미터 정의
db_params = {
    "dbname": PG_NAME, "user": PG_USER, "password": PG_PASSWORD,
    "host": PG_HOST,   "port": PG_PORT
}

# ------------------------------------------------------------------------------
# Phoenix Tracing 설정 (임시 비활성화)
# ------------------------------------------------------------------------------
# if PHOENIX_URL:
#     # Phoenix Client 초기화 (사용자 제안 적용)
#     client = Client(base_url=PHOENIX_URL)
#     # launch_app에 client를 전달하여 원격 서버에 연결
#     session = px.launch_app(client=client)

#     # OpenTelemetry 설정
#     tracer_provider = TracerProvider()
#     tracer_provider.add_span_processor(
#         BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{PHOENIX_URL}/v1/traces"))
#     )
#     trace.set_tracer_provider(tracer_provider)
#     tracer = trace.get_tracer("Mirae-RAG-App")
#     print(f"✅ Phoenix Tracing is enabled. View at: {session.url}")
# else:
#     print("⚠️ Phoenix Tracing is disabled. Set PHOENIX_URL environment variable to enable.")
tracer = trace.get_tracer("Mirae-RAG-App-no-tracing")


# ------------------------------------------------------------------------------
# FastAPI 앱 및 모델 초기화
# ------------------------------------------------------------------------------
app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용 (프로덕션용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

llm = ChatClovaX(
    model="HCX-005",
    max_tokens=MODEL_PARAMS["max_tokens"],
    temperature=MODEL_PARAMS["temperature"],
    top_p=MODEL_PARAMS["top_p"],
    stream=False,
)
search_tool = TavilySearchResults(api_key=TAVILY_API_KEY, max_results=5)
orchestrator = Orchestrator(llm, search_tool, db_params)

user_stocks = [
    {"종목명":"Apple Inc.","티커":"AAPL","수량":5,"평균단가":150},
    {"종목명":"Nvidia Corp.","티커":"NVDA","수량":3,"평균단가":200},
    {"종목명":"Microsoft Corp.","티커":"MSFT","수량":10,"평균단가":300},
    {"종목명":"Amazon.com, Inc.","티커":"AMZN","수량":2,"평균단가":100},
    {"종목명":"Alphabet Inc.","티커":"GOOGL","수량":4,"평균단가":140},
]

# ------------------------------------------------------------------------------
# Pydantic 모델 정의
# ------------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    user_stocks: Optional[List[Dict[str, Any]]] = None
    watchlist: Optional[List[Dict[str, str]]] = None

class StockDetailsRequest(BaseModel):
    symbols: List[str]

# ------------------------------------------------------------------------------
# API 엔드포인트
# ------------------------------------------------------------------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    user_stocks_data = request.user_stocks if request.user_stocks is not None else []
    watchlist_data = request.watchlist if request.watchlist is not None else []
    
    answer, tradingview_html, agent_type = orchestrator.route(request.message, user_stocks_data, watchlist_data, db_params)
    return {"answer": answer, "tradingview_html": tradingview_html, "agent_type": agent_type}

@app.post("/stock-details")
async def get_stock_details(request: StockDetailsRequest):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    details = {}
    for symbol in request.symbols:
        cur.execute("""
            SELECT time, close
            FROM stock_price
            WHERE symbol = %s
            ORDER BY time DESC
            LIMIT 2
        """, (symbol,))
        prices = cur.fetchall()
        
        if len(prices) >= 2:
            latest_price = prices[0]['close']
            previous_price = prices[1]['close']
            change = latest_price - previous_price
            change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
            details[symbol] = {
                "price": latest_price,
                "change": change,
                "changePercent": change_percent
            }
        elif len(prices) == 1:
            details[symbol] = {
                "price": prices[0]['close'],
                "change": 0,
                "changePercent": 0
            }
    
    cur.close()
    conn.close()
    return details

# React 앱 서빙 (가장 마지막에 위치해야 함)
app.mount("/", StaticFiles(directory="build", html=True), name="static") 