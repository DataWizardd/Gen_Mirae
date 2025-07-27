# api.py
# -*- coding: utf-8 -*-

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_naver import ChatClovaX
from langchain_community.tools.tavily_search import TavilySearchResults
from clova_config import MODEL_PARAMS
from agent.agents import Orchestrator, StructuredAgent, UnstructuredAgent, WebAgent

# ------------------------------------------------------------------------------
# 환경설정
# ------------------------------------------------------------------------------
load_dotenv()

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

db_params = {
    "dbname": PG_NAME, "user": PG_USER, "password": PG_PASSWORD,
    "host": PG_HOST,   "port": PG_PORT
}
sa = StructuredAgent()
ua = UnstructuredAgent()
wa = WebAgent(search_tool)
orchestrator = Orchestrator(sa, ua, wa, llm)

user_stocks = [
    {"종목명":"Apple Inc.","티커":"AAPL","수량":5,"평균단가":150},
    {"종목명":"Nvidia Corp.","티커":"NVDA","수량":3,"평균단가":200},
    {"종목명":"Microsoft Corp.","티커":"MSFT","수량":10,"평균단가":300},
    {"종목명":"Amazon.com, Inc.","티커":"AMZN","수량":2,"평균단가":100},
    {"종목명":"Alphabet Inc.","티커":"GOOGL","수량":4,"평균단가":140},
]

class ChatRequest(BaseModel):
    message: str

# ------------------------------------------------------------------------------
# API 엔드포인트
# ------------------------------------------------------------------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    answer, tradingview_html, agent_type = orchestrator.route(request.message, user_stocks, db_params)
    return {"answer": answer, "tradingview_html": tradingview_html, "agent_type": agent_type} 

# React 앱 서빙 (가장 마지막에 위치해야 함)
app.mount("/", StaticFiles(directory="build", html=True), name="static") 