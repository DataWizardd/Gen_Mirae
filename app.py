# app.py
# -*- coding: utf-8 -*-

import os
import uuid
import json
import requests
import streamlit as st
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pandas as pd

from clova_config import MODEL_PARAMS, get_persona_agent, remove_duplicate_sentences

# TF import 차단
os.environ["TRANSFORMERS_NO_TF"] = "1"

# 환경변수 로드
load_dotenv()
CLOVA_API_KEY  = os.getenv("CLOVA_API_KEY")
CLOVA_API_URL  = os.getenv("CLOVA_API_URL")
PG_HOST        = os.getenv("PG_HOST")
PG_PORT        = os.getenv("PG_PORT")
PG_NAME        = os.getenv("PG_NAME")
PG_USER        = os.getenv("PG_USER")
PG_PASSWORD    = os.getenv("PG_PASSWORD")

if not all([CLOVA_API_KEY, CLOVA_API_URL, PG_HOST, PG_NAME, PG_USER, PG_PASSWORD]):
    st.error("❗ .env에 CLOVA_API_KEY, CLOVA_API_URL, PG_XXX 값을 모두 설정해주세요.")
    st.stop()

# Clova Streaming 호출기
class CompletionExecutor:
    def __init__(self, api_url, api_key, request_id):
        self._api_url     = api_url
        self._api_key     = api_key
        self._request_id  = request_id

    def execute(self, completion_request):
        headers = {
            "Authorization":             f"Bearer {self._api_key}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self._request_id,
            "Content-Type":              "application/json; charset=utf-8",
            "Accept":                    "text/event-stream",
        }
        answer = ""
        with requests.post(self._api_url, headers=headers, json=completion_request, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                text = line.decode("utf-8")
                if text.startswith("data:"):
                    try:
                        data = json.loads(text[5:])
                        chunk = data.get("message", {}).get("content", "")
                        answer += chunk
                    except json.JSONDecodeError:
                        continue
        return answer

st.set_page_config(page_title="재무+리포트 챗봇", layout="wide")
st.title("📊 재무 데이터 + 리포트 기반 챗봇")

# ──────────── 사이드바: 보유 주식 현황 ────────────
with st.sidebar:
    st.header("📈 보유 주식")
    if "user_stocks" not in st.session_state:
        st.session_state["user_stocks"] = [
            {"종목명": "Apple Inc.",      "종목번호": "AAPL", "보유수량":  5, "평균단가": 150},
            {"종목명": "Nvidia Corp.",    "종목번호": "NVDA", "보유수량":  3, "평균단가": 200},
            {"종목명": "Microsoft Corp.", "종목번호": "MSFT", "보유수량": 10, "평균단가": 300},
            {"종목명": "Amazon.com, Inc.","종목번호": "AMZN", "보유수량":  2, "평균단가": 100},
            {"종목명": "Alphabet Inc.",   "종목번호": "GOOGL","보유수량":  4, "평균단가": 140},
        ]
    user_stocks = st.session_state["user_stocks"]

    # DB에서 최신 종가 가져오기
    conn = psycopg2.connect(
        dbname=PG_NAME, user=PG_USER, password=PG_PASSWORD,
        host=PG_HOST, port=PG_PORT
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    sidebar_rows = []
    for stk in user_stocks:
        code = stk["종목번호"]
        cur.execute(
            "SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1",
            (code,)
        )
        row       = cur.fetchone()
        current   = row["close"] if row else None
        buy_amt   = stk["보유수량"] * stk["평균단가"]
        eval_amt  = stk["보유수량"] * current if current else None
        profit    = (current - stk["평균단가"]) * stk["보유수량"] if current else None
        profit_rt = (profit / buy_amt * 100) if profit else None

        sidebar_rows.append({
            "종목명":   stk["종목명"],
            "코드":     code,
            "수량":     stk["보유수량"],
            "평균단가": f"{stk['평균단가']:,}",
            "현재가":   f"{current:,}" if current else "-",
            "평가액":   f"{eval_amt:,}" if eval_amt else "-",
            "수익률":   f"{profit_rt:.2f}%" if profit_rt is not None else "-",
        })

    cur.close()
    conn.close()

    st.dataframe(pd.DataFrame(sidebar_rows), hide_index=True)

# ──────────── 메인: 채팅 인터페이스 ────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 과거 메시지 출력
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# 사용자 입력
if prompt := st.chat_input("메시지를 입력하세요…"):
    # 1) 시스템 프롬프트 구성
    today    = datetime.now().strftime("%Y-%m-%d")
    persona  = get_persona_agent(sidebar_rows)
    sys_msg  = {
        "role":    "system",
        "content": f"오늘 날짜는 {today}입니다.\n당신은 재무 분석 어시스턴트입니다.\n{persona}"
    }

    # 2) 메시지 히스토리 업데이트
    if not any(m["role"] == "system" for m in st.session_state["messages"]):
        st.session_state["messages"].append(sys_msg)
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 3) RAG 컨텍스트 조회 (TimescaleDB + pgvector)
    conn = psycopg2.connect(
        dbname=PG_NAME, user=PG_USER, password=PG_PASSWORD,
        host=PG_HOST, port=PG_PORT
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 3‑1) 정형: stock_price 테이블에서 AAPL, NVDA 최근 5건
    symbols = [stk["종목번호"] for stk in user_stocks]
    cur.execute(
        """
        SELECT time, symbol, close
          FROM stock_price
         WHERE symbol = ANY(%s)
      ORDER BY time DESC
         LIMIT 10
        """,
        (symbols,)
    )
    stock_ctx_rows = cur.fetchall()

    # 3‑2) 비정형: company_reports에서 최근 3건
    cur.execute(
        """
        SELECT metadata->>'source' AS source,
               document            AS summary
          FROM company_reports
      ORDER BY id DESC
         LIMIT 3
        """
    )
    report_ctx_rows = cur.fetchall()

    cur.close()
    conn.close()

    # 4) 시스템 프롬프트에 추가
    stock_ctx = "\n".join(
        f"{r['time']:%Y-%m-%d %H:%M}: {r['symbol']} close={r['close']}"
        for r in stock_ctx_rows
    )
    report_ctx = "\n".join(
        f"{r['source']}: {r['summary']}"
        for r in report_ctx_rows
    )
    # append to existing system content
    st.session_state["messages"][0]["content"] += f"\n\n[주가 데이터]\n{stock_ctx}\n\n[분석 리포트]\n{report_ctx}"

    # 5) Clova 호출
    request_id = str(uuid.uuid4())
    executor   = CompletionExecutor(CLOVA_API_URL, CLOVA_API_KEY, request_id)
    payload    = {
        "messages": st.session_state["messages"],
        **MODEL_PARAMS
    }
    with st.spinner("응답 생성 중…"):
        raw = executor.execute(payload)

    # 6) 중복 문장 제거 및 출력
    answer = remove_duplicate_sentences(raw)
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)
