# api.py
# -*- coding: utf-8 -*-

import os
import re
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# 에이전트 임포트
from agent.agents import Chatbot
from agent.report_agent import ReportAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic 모델 정의 ---
class ChatMessage(BaseModel):
    type: str
    content: str

class ChatRequest(BaseModel):
    message: str
    user_stocks: Optional[List[Dict[str, Any]]] = None
    watchlist: Optional[List[Dict[str, str]]] = None
    chat_history: Optional[List[ChatMessage]] = []

class StockDetailsRequest(BaseModel):
    symbols: List[str]

class ReportRequest(BaseModel):
    ticker: str
    report_type: str = "full"

# --- API 엔드포인트 ---

@app.post("/stock-details")
async def get_stock_details(request: StockDetailsRequest):
    """홈 화면의 보유/관심 종목 가격 정보를 반환하는 엔드포인트"""
    db_params = {
        "dbname": os.getenv("PG_NAME"), "user": os.getenv("PG_USER"),
        "password": os.getenv("PG_PASSWORD"), "host": os.getenv("PG_HOST"),
        "port": os.getenv("PG_PORT")
    }
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        details = {}
        for symbol in request.symbols:
            cur.execute("SELECT time, close FROM stock_price WHERE symbol = %s ORDER BY time DESC LIMIT 1", (symbol,))
            latest_price_row = cur.fetchone()

            if latest_price_row:
                latest_price = latest_price_row['close']
                cur.execute("SELECT close FROM stock_price WHERE symbol = %s AND time < %s::date ORDER BY time DESC LIMIT 1", (symbol, latest_price_row['time']))
                previous_price_row = cur.fetchone()
                previous_price = previous_price_row['close'] if previous_price_row else latest_price
                change = latest_price - previous_price
                change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
                details[symbol] = {"price": latest_price, "change": change, "changePercent": change_percent}
            else:
                details[symbol] = {"price": 0, "change": 0, "changePercent": 0}
        return details
    except psycopg2.Error as e:
        logging.error(f"DB 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터베이스 오류가 발생했습니다.")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.post("/generate_report")
async def generate_report_endpoint(request: ReportRequest):
    """AI 리포트를 생성하는 엔드포인트"""
    try:
        agent = ReportAgent(request.ticker, request.report_type)
        report_data = agent.run()
        return report_data
    except Exception as e:
        logging.exception("리포트 생성 중 오류 발생")
        raise HTTPException(status_code=500, detail=f"리포트 생성 중 오류 발생: {str(e)}")

@app.get("/reports/{file_name}")
async def get_report_file(file_name: str):
    file_path = os.path.join("/tmp", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', filename=file_name)
    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

# 전역 Chatbot 인스턴스 (메모리 효율을 위해 한번만 생성)
chatbot_agent = Chatbot()

@app.post("/chat")
async def chat(request: ChatRequest):
    """챗봇 응답을 처리하는 엔드포인트"""
    try:
        user_info = {"user_stocks": request.user_stocks, "watchlist": request.watchlist}
        
        lc_chat_history = []
        for msg in request.chat_history:
            if msg.type == 'human':
                lc_chat_history.append({"role": "user", "content": msg.content})
            elif msg.type == 'ai':
                lc_chat_history.append({"role": "assistant", "content": msg.content})

        result = chatbot_agent.run(
            query=request.message,
            user_info=user_info,
            chat_history=lc_chat_history
        )
        return result
    except Exception as e:
        logging.error(f"Chat API 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="챗봇 응답 생성 중 오류가 발생했습니다.")

# React 앱 서빙 (가장 마지막에 위치해야 함)
app.mount("/", StaticFiles(directory="build", html=True), name="static")

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return FileResponse("build/index.html")
