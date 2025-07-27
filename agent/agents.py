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
        tradingview_html = None
        agent_type = None
        # 에이전트 선택 및 TradingView 위젯 생성
        if re.search(r"(주가|가격)", user_input):
            context = self.sa.run(user_input, user_stocks, db_params) or ""
            agent_type = "정형(Structured) 에이전트"
            mapping = {"애플":"AAPL","엔비디아":"NVDA","마이크로소프트":"MSFT","아마존":"AMZN","알파벳":"GOOGL"}
            symbol = next((sym for kor,sym in mapping.items() if kor in user_input), None)
            if symbol:
                tradingview_html = f'''
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
                '''
        elif re.search(r"(검색|뉴스|기사|웹)", user_input):
            context = self.wa.run(user_input, user_stocks, db_params)
            agent_type = "웹(Web) 에이전트"
        else:
            context = self.ua.run(user_input, user_stocks, db_params)
            agent_type = "비정형(Unstructured) 에이전트"

        system_msg = f"오늘 날짜는 {today}입니다. 아래 정보를 참고하여 **한국어**로만 답변해 주세요."
        human_msg  = f"[컨텍스트]\n{context}\n\n[질문]\n{user_input}"

        ai_msg = self.llm.invoke([
            ("system", system_msg),
            ("human", human_msg)
        ])
        return ai_msg.content, tradingview_html, agent_type