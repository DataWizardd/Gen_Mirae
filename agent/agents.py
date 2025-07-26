import psycopg2
from psycopg2.extras import RealDictCursor
import re
from datetime import datetime

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