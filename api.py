import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

from agent.report_agent import ReportAgent
from agent.agents import Chatbot # 수정된 Chatbot 클래스 임포트

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 환경 변수 로드 ---
load_dotenv()

# --- FastAPI 앱 초기화 ---
app = FastAPI()

# --- CORS 미들웨어 설정 ---
origins = [
    "http://localhost:3000",
    "http://175.106.97.51:3000",
    "http://www.gen-mirae.com",
    "http://gen-mirae.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DB 연결 정보 ---
db_params = {
    "dbname": os.getenv("PG_NAME"), "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"), "host": os.getenv("PG_HOST"), "port": os.getenv("PG_PORT")
}

# --- Pydantic 모델 정의 ---
class StockDetailsRequest(BaseModel):
    symbols: List[str]

class ReportRequest(BaseModel):
    ticker: str
    report_type: str

class ChatRequest(BaseModel):
    message: str
    user_stocks: List[Dict] = Field(default_factory=list)
    watchlist: List[Dict] = Field(default_factory=list)
    chat_history: Optional[List[Dict]] = Field(default_factory=list)


# --- 라우트 핸들러 ---

@app.get("/")
def read_root():
    return {"message": "Mirae-AI-Financial-Report-Service"}

@app.post("/stock-details")
async def get_stock_details(request: StockDetailsRequest):
    # ... (기존 코드와 동일) ...
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
    cur.close()
    conn.close()
    return details


@app.post("/generate_report")
async def generate_report_endpoint(request: ReportRequest):
    # ... (기존 코드와 동일) ...
    try:
        agent = ReportAgent(ticker=request.ticker)
        report_data = agent.run()
        if not report_data or not report_data.get('sections'):
            raise HTTPException(status_code=404, detail=f"{request.ticker}에 대한 리포트를 생성할 수 없습니다. 데이터가 부족합니다.")
        return JSONResponse(content=report_data)
    except Exception as e:
        logging.error(f"Report generation error for {request.ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/{file_name}")
async def get_report_file(file_name: str):
    # ... (기존 코드와 동일) ...
    file_path = os.path.join("/tmp", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', filename=file_name)
    raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

@app.post("/chat")
async def chat_with_ai_analyst(request: ChatRequest):
    try:
        # Chatbot 인스턴스 생성 시 사용자 정보 전달
        chatbot = Chatbot(
            user_stocks=request.user_stocks,
            watchlist=request.watchlist
        )
        # run 메소드에는 쿼리만 전달
        response_data = chatbot.run(query=request.message)
        return JSONResponse(content=response_data)
    except Exception as e:
        logging.error(f"Chat API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"챗봇 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)