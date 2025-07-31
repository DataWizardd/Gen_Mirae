import os
import re
import logging
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_naver import ChatClovaX
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db_params = {
    "dbname": os.getenv("PG_NAME"), "user": os.getenv("PG_USER"), 
    "password": os.getenv("PG_PASSWORD"), "host": os.getenv("PG_HOST"), "port": os.getenv("PG_PORT")
}

def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """DB 쿼리를 안전하게 실행하고 결과를 반환합니다."""
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall() if cur.description else []
    except Exception as e:
        logging.error(f"[DB ERROR] 쿼리 실행 중 오류 발생: {e}", exc_info=True)
        return [{"error": "데이터베이스 조회 중 오류가 발생했습니다."}]

class Chatbot:
    def __init__(self, user_stocks: List[Dict] = None, watchlist: List[Dict] = None):
        self.llm = ChatClovaX(model="HCX-005", temperature=0.1)
        self.search_tool = TavilySearchResults(max_results=3)
        self.user_stocks = user_stocks or []
        self.watchlist = watchlist or []
        self.stock_map = { "애플": "AAPL", "엔비디아": "NVDA", "마이크로소프트": "MSFT", "아마존": "AMZN", "알파벳": "GOOGL", "테슬라": "TSLA" }
        self.ticker_map = {v: k for k, v in self.stock_map.items()}

    def _get_symbol_from_query(self, query: str) -> str:
        for name, ticker in self.stock_map.items():
            if name in query:
                return ticker
        return None

    def run(self, query: str) -> Dict:
        """챗봇의 메인 실행 로직"""
        symbol = self._get_symbol_from_query(query)
        answer, tradingview_symbol = "", None
        company_name = self.ticker_map.get(symbol, symbol)

        if any(keyword in query for keyword in ["주가", "가격"]):
            if symbol:
                logging.info(f"'{symbol}'의 주가 정보를 조회합니다.")
                result = execute_query("SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1", (symbol,))
                
                if result and not result[0].get('error'):
                    price = result[0]['close']
                    answer = f"{company_name}의 현재 주가는 약 ${price:,.2f} 입니다."
                    tradingview_symbol = symbol
                    logging.info(f"'{symbol}' 주가 조회 성공. TradingView 위젯 생성을 위해 심볼 반환.")
                else:
                    logging.warning(f"'{symbol}'의 주가 정보를 DB에서 찾을 수 없습니다. Result: {result}")
                    answer = f"{company_name}의 주가 정보를 찾을 수 없습니다."
            else:
                answer = "어떤 종목의 주가가 궁금하신가요? (예: 애플 주가)"
        
        elif any(keyword in query for keyword in ["뉴스", "기사"]):
            if symbol:
                results = execute_query("SELECT title, url, published_at FROM stock_news WHERE symbol = %s ORDER BY published_at DESC LIMIT 3", (symbol,))
                if results and not results[0].get('error'):
                    answer = f"{company_name} 관련 최신 뉴스:\n" + "\n".join([f"- {row['title']} ({row['published_at']:%Y-%m-%d})" for row in results])
                else:
                    answer = f"{company_name}에 대한 최신 뉴스를 찾을 수 없습니다."
            else:
                answer = "어떤 종목의 뉴스가 궁금하신가요?"
        
        elif any(keyword in query for keyword in ["보유 종목", "내 종목", "내 주식", "포트폴리오"]):
            if self.user_stocks:
                answer = "고객님의 보유 종목은 다음과 같습니다:\n" + ", ".join([s.get('종목명', 'N/A') for s in self.user_stocks])
            else:
                answer = "보유 종목 정보가 없습니다."

        elif "관심 종목" in query:
            if self.watchlist:
                answer = "고객님의 관심 종목은 다음과 같습니다:\n" + ", ".join([w.get('name', 'N/A') for w in self.watchlist])
            else:
                answer = '관심 종목 정보가 없습니다.'

        elif any(keyword in query for keyword in ["리포트", "전망", "분석"]):
             search_results = self.search_tool.invoke(f"{query}에 대한 최신 정보")
             answer = "웹 검색 결과 요약:\n" + "\n".join([f"- {res.get('title', 'N/A')}: {res.get('snippet', '내용 없음')}" for res in search_results])

        else:
            prompt = ChatPromptTemplate.from_template("다음 사용자의 질문에 대해 친절하고 간결하게 답변해줘: {query}")
            chain = prompt | self.llm
            llm_response = chain.invoke({"query": query})
            answer = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

        return {"answer": answer, "tradingview_symbol": tradingview_symbol}
