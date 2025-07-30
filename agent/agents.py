import os
import re
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_naver import ChatClovaX
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# --- 도구(Tools) 및 헬퍼 함수 ---
db_params = {
    "dbname": os.getenv("PG_NAME"), "user": os.getenv("PG_USER"), 
    "password": os.getenv("PG_PASSWORD"), "host": os.getenv("PG_HOST"), "port": os.getenv("PG_PORT")
}

def get_tradingview_widget(symbol: str) -> str:
    """TradingView 위젯 HTML을 생성합니다."""
    sanitized_symbol = re.sub(r'[^a-zA-Z0-9]', '', symbol)
    return f"""<div class="tradingview-widget-container" style="height:350px;width:100%"><div id="tv_widget_{sanitized_symbol}"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script type="text/javascript">new TradingView.widget({{"autosize": true,"symbol": "{sanitized_symbol}","interval": "D","timezone": "Etc/UTC","theme": "dark","style": "1","locale": "kr","enable_publishing": false,"allow_symbol_change": true,"container_id": "tv_widget_{sanitized_symbol}"}});</script></div>"""

def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """DB 쿼리를 안전하게 실행하고 결과를 반환합니다."""
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall() if cur.description else []
    except Exception as e:
        print(f"[DB ERROR] {e}") # 서버 로그에 에러 기록
        return [{"error": "데이터베이스 조회 중 오류가 발생했습니다."}]

# --- 에이전트 클래스 ---

class Chatbot:
    def __init__(self):
        self.llm = ChatClovaX(model="HCX-005", temperature=0.1)
        self.search_tool = TavilySearchResults(max_results=3)

    def _get_symbol_from_query(self, query: str) -> str:
        """쿼리에서 종목명을 찾아 티커로 변환합니다."""
        stock_map = { "애플": "AAPL", "엔비디아": "NVDA", "마이크로소프트": "MSFT", "아마존": "AMZN", "알파벳": "GOOGL", "테슬라": "TSLA" }
        return next((ticker for name, ticker in stock_map.items() if name.lower() in query.lower()), None)

    def run(self, query: str, user_info: Dict, chat_history: List[Dict]) -> Dict:
        """챗봇의 메인 실행 로직 (안정화 버전)"""
        symbol = self._get_symbol_from_query(query)
        answer, tradingview_html = "", None

        # 1. 키워드 기반으로 명확한 의도 먼저 처리
        if any(keyword in query for keyword in ["주가", "가격"]):
            if symbol:
                result = execute_query("SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1", (symbol,))
                if result and 'close' in result[0]:
                    price = result[0]['close']
                    answer = f"{symbol}의 현재 주가는 약 ${price:,.2f} 입니다."
                    tradingview_html = get_tradingview_widget(symbol)
                else:
                    answer = f"{symbol}의 주가 정보를 찾을 수 없습니다."
            else:
                answer = "어떤 종목의 주가가 궁금하신가요?"
        
        elif any(keyword in query for keyword in ["뉴스", "기사"]):
            if symbol:
                results = execute_query("SELECT title, url, published_at FROM stock_news WHERE symbol = %s ORDER BY published_at DESC LIMIT 3", (symbol,))
                if results and 'error' not in results[0]:
                    answer = f"{symbol} 관련 최신 뉴스:\n" + "\n".join([f"- {row['title']} ({row['published_at']:%Y-%m-%d})" for row in results])
                else:
                    answer = f"{symbol}에 대한 최신 뉴스를 찾을 수 없습니다."
            else:
                answer = "어떤 종목의 뉴스가 궁금하신가요?"
        
        elif any(keyword in query for keyword in ["보유 종목", "내 종목", "내 주식"]):
            holdings = user_info.get('user_stocks', [])
            answer = "고객님의 보유 종목은 다음과 같습니다:\n" + (", ".join([s['종목명'] for s in holdings]) if holdings else '보유 종목 정보가 없습니다.')

        elif "관심 종목" in query:
            watchlist = user_info.get('watchlist', [])
            answer = "고객님의 관심 종목은 다음과 같습니다:\n" + (", ".join([w['name'] for w in watchlist]) if watchlist else '관심 종목 정보가 없습니다.')

        elif any(keyword in query for keyword in ["리포트", "전망", "분석"]):
             search_results = self.search_tool.invoke(query)
             answer = "웹 검색 결과 요약:\n" + "\n".join([f"- {res['title']}: {res['snippet']}" for res in search_results])

        # 2. 위 키워드에 해당하지 않으면 일반 대화로 처리
        else:
            prompt = ChatPromptTemplate.from_template("다음 사용자의 질문에 대해 친절하고 간결하게 답변해줘: {query}")
            chain = prompt | self.llm
            llm_response = chain.invoke({"query": query})
            answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

        # 3. 항상 올바른 형식으로 응답 반환 보장
        return {"answer": answer, "tradingview_html": tradingview_html}
