import os
import re
import logging
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_naver import ChatClovaX
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta


## AI Analyst Chatbot을 위한 코드
## 향후 고도화 시 Orchestrator 및 다중 Agent 호출 구조로 변경 예정

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

class QueryExpander:
    """사용자 질문을 확장하고 관련 키워드를 추출하는 클래스"""
    
    def __init__(self, llm):
        self.llm = llm
        
    def expand_query(self, query: str) -> Dict[str, Any]:
        """쿼리를 분석하고 관련 정보를 추출"""
        expansion_prompt = ChatPromptTemplate.from_template("""
사용자 질문을 분석하여 다음 정보를 JSON 형태로 추출해주세요:

사용자 질문: {query}

추출할 정보:
1. intent: 질문의 의도
   - price_check: 주가, 가격, 시세 관련 질문
   - news_search: 뉴스, 기사 관련 질문
   - valuation_analysis: 밸류에이션, P/E, PBR 등 지표 관련 질문
   - financial_analysis: 재무제표, 손익계산서, 대차대조표 관련 질문
   - sec_filing_search: SEC 공시, 10-K, 10-Q 등 관련 질문
   - market_sentiment: 시장 감정, 이벤트, 트렌드 관련 질문
   - portfolio_analysis: 포트폴리오, 보유종목, 관심종목 관련 질문
   - general_search: 위에 해당하지 않는 일반적인 질문

2. tickers: 언급된 종목 티커들 (예: ["AAPL", "NVDA"])
3. time_range: 시간 범위 (recent, 1week, 1month, 1quarter, 1year, all)
4. keywords: 핵심 키워드들 (리스트)
5. needs_chart: 주가나 차트 관련 질문인지 여부 (boolean)

주가, 가격, 시세 등의 키워드가 포함된 경우 intent는 "price_check"이고 needs_chart는 true로 설정하세요.

JSON 형태로만 응답하세요.
""")
        
        try:
            chain = expansion_prompt | self.llm
            response = chain.invoke({"query": query})
            content = response.content if hasattr(response, 'content') else str(response)
            
            # JSON 파싱 시도
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
                
            return json.loads(content.strip())
        except Exception as e:
            logging.error(f"Query expansion error: {e}")
            
            # 기본 의도 결정 (간단한 키워드 매칭)
            intent = "general_search"
            needs_chart = False
            
            if any(keyword in query for keyword in ["주가", "가격", "시세", "현재가"]):
                intent = "price_check"
                needs_chart = True
            elif any(keyword in query for keyword in ["뉴스", "기사"]):
                intent = "news_search"
            elif any(keyword in query for keyword in ["보유", "포트폴리오", "관심"]):
                intent = "portfolio_analysis"
            elif any(keyword in query for keyword in ["밸류에이션", "P/E", "PBR", "지표"]):
                intent = "valuation_analysis"    
                
            return {
                "intent": intent,
                "tickers": [],
                "time_range": "recent",
                "keywords": [query],
                "needs_chart": needs_chart
            }


class DataSourceRouter:
    """적절한 데이터 소스를 선택하는 라우터"""
    
    @staticmethod
    def route(expanded_query: Dict[str, Any]) -> List[str]:
        """확장된 쿼리를 기반으로 필요한 데이터 소스들을 반환"""
        intent = expanded_query.get("intent", "general_search")
        data_sources = []
        
        if intent == "price_check":
            data_sources.extend(["stock_price", "stock_valuation"])
        elif intent == "news_search":
            data_sources.extend(["stock_news", "tavily_search"])
        elif intent == "valuation_analysis":
            data_sources.extend(["stock_valuation", "financial_statements"])
        elif intent == "financial_analysis":
            data_sources.extend(["financial_statements", "sec_filings"])
        elif intent == "sec_filing_search":
            data_sources.extend(["sec_filings"])
        elif intent == "market_sentiment":
            data_sources.extend(["gdelt_events", "stock_news", "tavily_search"])
        elif intent == "portfolio_analysis":
            data_sources.extend(["stock_price", "stock_valuation"])
        else:
            data_sources.extend(["tavily_search"])
            
        return data_sources
    
    @staticmethod
    def should_show_chart(expanded_query: Dict[str, Any]) -> bool:
        """차트 표시 여부를 결정 - 단순 주가 질문에만 표시"""
        intent = expanded_query.get("intent", "")
        needs_chart = expanded_query.get("needs_chart", False)
        
        # 오직 price_check 의도일 때만 차트 표시
        return intent == "price_check" and needs_chart


class AdvancedDataRetriever:
    """다양한 데이터 소스에서 정보를 가져오는 클래스"""
    
    def __init__(self, search_tool: TavilySearchResults):
        self.search_tool = search_tool
        self.stock_map = {
            "애플": "AAPL", "엔비디아": "NVDA", "마이크로소프트": "MSFT", 
            "아마존": "AMZN", "알파벳": "GOOGL", "테슬라": "TSLA"
        }
        self.ticker_map = {v: k for k, v in self.stock_map.items()}
    
    def get_stock_price(self, tickers: List[str], time_range: str = "recent") -> Dict[str, Any]:
        """주가 정보 조회"""
        if not tickers:
            return {"error": "티커가 지정되지 않았습니다."}
            
        results = {}
        for ticker in tickers:
            # 한글 종목명을 티커로 변환
            symbol = self.stock_map.get(ticker, ticker.upper())
            
            if time_range == "recent":
                query = "SELECT close, time FROM stock_price WHERE symbol = %s ORDER BY time DESC LIMIT 1"
            else:
                days_map = {"1week": 7, "1month": 30, "1quarter": 90, "1year": 365}
                days = days_map.get(time_range, 1)
                cutoff_date = datetime.now() - timedelta(days=days)
                query = "SELECT close, time FROM stock_price WHERE symbol = %s AND time >= %s ORDER BY time DESC"
                
            result = execute_query(query, (symbol, cutoff_date) if time_range != "recent" else (symbol,))
            
            if result and not result[0].get('error'):
                results[symbol] = result
            else:
                results[symbol] = {"error": f"{symbol} 주가 정보를 찾을 수 없습니다."}
                
        return results
    
    def get_stock_news(self, tickers: List[str], keywords: List[str], time_range: str = "recent") -> Dict[str, Any]:
        """뉴스 정보 조회"""
        results = {}
        
        for ticker in tickers:
            symbol = self.stock_map.get(ticker, ticker.upper())
            
            if time_range == "recent":
                query = "SELECT title, description, url, published_at FROM stock_news WHERE ticker = %s ORDER BY published_at DESC LIMIT 5"
                params = (symbol,)
            else:
                days_map = {"1week": 7, "1month": 30, "1quarter": 90, "1year": 365}
                days = days_map.get(time_range, 7)
                cutoff_date = datetime.now() - timedelta(days=days)
                query = "SELECT title, description, url, published_at FROM stock_news WHERE ticker = %s AND published_at >= %s ORDER BY published_at DESC"
                params = (symbol, cutoff_date)
                
            result = execute_query(query, params)
            
            if result and not result[0].get('error'):
                results[symbol] = result
            else:
                results[symbol] = {"error": f"{symbol} 뉴스를 찾을 수 없습니다."}
                
        return results
    
    def get_valuation_data(self, tickers: List[str]) -> Dict[str, Any]:
        """밸류에이션 데이터 조회"""
        results = {}
        
        for ticker in tickers:
            symbol = self.stock_map.get(ticker, ticker.upper())
            query = """
            SELECT trailing_pe, forward_pe, price_to_book, price_to_sales, 
                   market_cap, enterprise_value, updated_at 
            FROM stock_valuation 
            WHERE ticker = %s 
            ORDER BY updated_at DESC LIMIT 1
            """
            
            result = execute_query(query, (symbol,))
            
            if result and not result[0].get('error'):
                results[symbol] = result[0]
            else:
                results[symbol] = {"error": f"{symbol} 밸류에이션 데이터를 찾을 수 없습니다."}
                
        return results
    
    def get_financial_statements(self, tickers: List[str]) -> Dict[str, Any]:
        """재무제표 데이터 조회"""
        results = {}
        
        for ticker in tickers:
            symbol = self.stock_map.get(ticker, ticker.upper())
            query = """
            SELECT statement_type, period, data 
            FROM financial_statements 
            WHERE ticker = %s 
            ORDER BY period DESC 
            LIMIT 5
            """
            
            result = execute_query(query, (symbol,))
            
            if result and not result[0].get('error'):
                results[symbol] = result
            else:
                results[symbol] = {"error": f"{symbol} 재무제표 데이터를 찾을 수 없습니다."}
                
        return results
    
    def search_sec_filings(self, tickers: List[str], keywords: List[str]) -> Dict[str, Any]:
        """SEC 공시 문서 검색"""
        results = {}
        
        for ticker in tickers:
            symbol = self.stock_map.get(ticker, ticker.upper())
            
            # 메타데이터 기반 검색
            query = """
            SELECT document, metadata, created_at
            FROM sec_filings 
            WHERE metadata->>'symbol' = %s
            ORDER BY created_at DESC 
            LIMIT 3
            """
            
            result = execute_query(query, (symbol,))
            
            if result and not result[0].get('error'):
                results[symbol] = result
            else:
                results[symbol] = {"error": f"{symbol} SEC 공시 문서를 찾을 수 없습니다."}
                
        return results
    
    def get_gdelt_events(self, keywords: List[str], time_range: str = "1week") -> Dict[str, Any]:
        """GDELT 이벤트 데이터 조회"""
        if not keywords:
            return {"error": "검색할 키워드가 지정되지 않았습니다."}
            
        days_map = {"1week": 7, "1month": 30, "1quarter": 90}
        days = days_map.get(time_range, 7)
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 키워드와 관련된 이벤트 검색
        keyword_conditions = " OR ".join([f"actor1_name ILIKE %s OR actor2_name ILIKE %s" for _ in keywords])
        query = f"""
        SELECT actor1_name, actor2_name, event_code, goldstein_scale, avg_tone, 
               event_date, source_url
        FROM gdelt_events 
        WHERE event_date >= %s AND ({keyword_conditions})
        ORDER BY event_date DESC 
        LIMIT 10
        """
        
        # 키워드 파라미터 준비 (각 키워드마다 2개씩)
        params = [cutoff_date]
        for keyword in keywords:
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            
        result = execute_query(query, tuple(params))
        
        if result and not result[0].get('error'):
            return {"events": result}
        else:
            return {"error": "관련 GDELT 이벤트를 찾을 수 없습니다."}
    
    def tavily_search(self, query: str, keywords: List[str]) -> Dict[str, Any]:
        """Tavily 웹 검색"""
        try:
            search_query = f"{query} {' '.join(keywords)}"
            results = self.search_tool.invoke(search_query)
            return {"web_results": results}
        except Exception as e:
            logging.error(f"Tavily search error: {e}")
            return {"error": "웹 검색 중 오류가 발생했습니다."}


class Chatbot:
    def __init__(self, user_stocks: List[Dict] = None, watchlist: List[Dict] = None):
        self.llm = ChatClovaX(model="HCX-005", temperature=0.1)
        self.search_tool = TavilySearchResults(max_results=5)
        self.user_stocks = user_stocks or []
        self.watchlist = watchlist or []
        
        # 새로운 컴포넌트들
        self.query_expander = QueryExpander(self.llm)
        self.data_retriever = AdvancedDataRetriever(self.search_tool)
        
        self.stock_map = {
            "애플": "AAPL", "엔비디아": "NVDA", "마이크로소프트": "MSFT", 
            "아마존": "AMZN", "알파벳": "GOOGL", "테슬라": "TSLA"
        }
        self.ticker_map = {v: k for k, v in self.stock_map.items()}
        
        # 현재 시간 정보
        self.current_date = datetime.now().strftime("%Y년 %m월 %d일")
        self.current_year = datetime.now().year

    def _extract_tickers_from_query(self, query: str, expanded_query: Dict) -> List[str]:
        """쿼리에서 티커 추출"""
        tickers = []
        
        # 확장된 쿼리에서 티커 추출
        if expanded_query.get("tickers"):
            tickers.extend(expanded_query["tickers"])
            
        # 직접 한글 종목명 매칭
        for name, ticker in self.stock_map.items():
            if name in query:
                tickers.append(ticker)

        
        # 보유 종목만 질문하는 경우
        portfolio_phrases = ["내 보유", "내 종목", "보유 종목", "내 포트폴리오", "투자한 종목", "산 종목"]
        if any(phrase in query for phrase in portfolio_phrases):
            for stock in self.user_stocks:
                symbol = stock.get('symbol', '').upper()
                if symbol and symbol not in tickers:
                    tickers.append(symbol)
        
        # 관심 종목만 질문하는 경우        
        watchlist_phrases = ["관심 종목", "지켜보는 종목", "관찰하는 종목", "팔로우하는 종목"]
        if any(phrase in query for phrase in watchlist_phrases):
            # 실제 관심 종목이 있는지 확인
            if not self.watchlist:
                logging.warning("사용자의 관심 종목 데이터가 비어있습니다.")
                # 관심 종목이 없는 경우 빈 리스트 반환하여 명확한 안내 제공
                return []
            else:
                logging.info(f"사용자 관심 종목: {[item.get('name', item.get('symbol', '')) for item in self.watchlist]}")
                
            for item in self.watchlist:
                symbol = item.get('symbol', '').upper()
                if symbol and symbol not in tickers:
                    tickers.append(symbol)
                    
        # "전체", "모든" 종목 질문인 경우에만 보유+관심 모두 포함
        all_phrases = ["모든 종목", "전체 종목", "전부 종목", "모든 주식", "전체 주식"]
        if any(phrase in query for phrase in all_phrases):
            for stock in self.user_stocks:
                symbol = stock.get('symbol', '').upper()
                if symbol and symbol not in tickers:
                    tickers.append(symbol)
            for item in self.watchlist:
                symbol = item.get('symbol', '').upper()
                if symbol and symbol not in tickers:
                    tickers.append(symbol)
                
        # 중복 제거
        return list(set(tickers))

    def _should_include_portfolio_context(self, query: str, expanded_query: Dict, tickers: List[str]) -> bool:
        """포트폴리오 컨텍스트를 포함할지 여부를 결정"""
        intent = expanded_query.get("intent", "")
        
        # 포트폴리오 관련 질문인 경우 항상 포함
        if intent == "portfolio_analysis":
            return True
            
        # 특정 종목에 대한 일반적인 질문인 경우 포함하지 않음
        specific_stock_patterns = [
            # "테슬라 전망", "애플 어때", "엔비디아 상승 가능성" 등
            r'[가-힣a-zA-Z]+ (전망|어때|상승|하락|투자|분석|가격|주가|어떨까|괜찮|좋|나쁨)',
            r'(전망|어때|상승|하락|투자|분석|가격|주가) [가-힣a-zA-Z]+',
            r'[가-힣a-zA-Z]+ 관련',
            r'[가-힣a-zA-Z]+에 대한',
        ]
        
        for pattern in specific_stock_patterns:
            if re.search(pattern, query):
                return False
        
        # 보유/관심 종목 관련 키워드가 포함된 경우만 포함
        portfolio_related = ["내 보유", "내 종목", "보유 종목", "관심 종목", "내 포트폴리오"]
        return any(phrase in query for phrase in portfolio_related)

    def _synthesize_response(self, expanded_query: Dict, data_results: Dict) -> str:
        """수집된 데이터를 바탕으로 종합적인 답변 생성"""
        
        # 포트폴리오 컨텍스트 포함 여부 결정
        query = expanded_query.get("original_query", "")
        tickers = expanded_query.get("tickers", [])
        include_portfolio = self._should_include_portfolio_context(query, expanded_query, tickers)
        
        if include_portfolio:
            synthesis_prompt = ChatPromptTemplate.from_template("""
사용자 질문: {query}
질문 의도: {intent}

중요한 정보:
{portfolio_context}

수집된 데이터:
{data_summary}

답변 작성 가이드라인:
1. 현재 날짜를 정확히 인지하고 답변하세요 (현재: {current_date})
2. 보유 종목(실제 투자중)과 관심 종목(관찰중)을 명확히 구분해서 언급하세요
3. 보유 종목의 경우 "투자하고 계신", "보유하고 계신" 등의 표현 사용
4. 관심 종목의 경우 "관심을 두고 계신", "지켜보고 계신" 등의 표현 사용
5. "관심 종목"에 대한 질문이라면 관심 종목에만 집중하고 보유 종목은 언급하지 마세요
6. 구체적인 데이터와 수치를 포함해서 친근하고 이해하기 쉽게 작성
7. 종목명이나 중요한 정보는 **굵은 글씨**로 강조하고, 여러 항목이 있을 때는 불릿 포인트(- )를 사용하세요
8. 절대로 임의의 종목명을 만들어내지 마세요. 제공된 데이터에 없는 종목은 언급하지 마세요

위 정보를 바탕으로 사용자 질문에 대한 정확하고 유용한 답변을 한국어로 작성해주세요.
""")
        else:
            synthesis_prompt = ChatPromptTemplate.from_template("""
사용자 질문: {query}
질문 의도: {intent}

수집된 데이터:
{data_summary}

답변 작성 가이드라인:
1. 현재 날짜를 정확히 인지하고 답변하세요 (현재: {current_date})
2. 구체적인 데이터와 수치를 포함해서 친근하고 이해하기 쉽게 작성
3. 질문한 종목에 대해서만 집중해서 답변하세요
4. "관심 종목"에 대한 질문이라면 관심 종목에만 집중하고 보유 종목은 언급하지 마세요
5. 종목명이나 중요한 정보는 **굵은 글씨**로 강조하고, 여러 항목이 있을 때는 불릿 포인트(- )를 사용하세요
6. 절대로 임의의 종목명을 만들어내지 마세요. 제공된 데이터에 없는 종목은 언급하지 마세요

위 정보를 바탕으로 사용자 질문에 대한 정확하고 유용한 답변을 한국어로 작성해주세요.
""")
        
        try:
            # 데이터 요약 생성
            data_summary = self._create_data_summary(data_results)
            
            chain = synthesis_prompt | self.llm
            
            if include_portfolio:
                # 포트폴리오 컨텍스트 생성
                portfolio_context = self._create_portfolio_context()
                response = chain.invoke({
                    "query": expanded_query.get("original_query", ""),
                    "intent": expanded_query.get("intent", ""),
                    "portfolio_context": portfolio_context,
                    "data_summary": data_summary,
                    "current_date": self.current_date
                })
            else:
                response = chain.invoke({
                    "query": expanded_query.get("original_query", ""),
                    "intent": expanded_query.get("intent", ""),
                    "data_summary": data_summary,
                    "current_date": self.current_date
                })
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logging.error(f"Response synthesis error: {e}")
            return "죄송합니다. 답변 생성 중 오류가 발생했습니다."

    def _create_portfolio_context(self) -> str:
        """사용자 포트폴리오 정보를 문자열로 생성"""
        context_parts = []
        
        # 현재 날짜 정보 추가
        current_date = datetime.now().strftime("%Y년 %m월 %d일")
        context_parts.append(f"현재 날짜: {current_date}")
        
        # 보유 종목 정보 (실제 투자한 종목)
        if self.user_stocks:
            stock_info = []
            for stock in self.user_stocks:
                name = stock.get('name', stock.get('symbol', 'N/A'))
                quantity = stock.get('quantity', 0)
                avg_price = stock.get('avgPrice', 0)
                if quantity and avg_price:
                    stock_info.append(f"{name}({quantity}주, 평균단가 ${avg_price:.2f})")
                else:
                    stock_info.append(name)
            context_parts.append(f"실제 보유 종목(투자중): {', '.join(stock_info)}")
            
        # 관심 종목 정보 (관찰만 하는 종목)    
        if self.watchlist:
            watchlist_names = [item.get('name', item.get('symbol', 'N/A')) for item in self.watchlist]
            context_parts.append(f"관심 종목(관찰중): {', '.join(watchlist_names)}")
            
        return "; ".join(context_parts) if context_parts else f"현재 날짜: {current_date}; 포트폴리오 정보 없음"

    def _create_data_summary(self, data_results: Dict) -> str:
        """데이터 결과를 요약 문자열로 변환"""
        summary_parts = []
        
        for source, data in data_results.items():
            if source == "stock_price" and data:
                for ticker, price_data in data.items():
                    if isinstance(price_data, list) and price_data:
                        latest = price_data[0]
                        summary_parts.append(f"{ticker} 현재가: ${latest.get('close', 'N/A')}")
                        
            elif source == "stock_news" and data:
                for ticker, news_data in data.items():
                    if isinstance(news_data, list) and news_data:
                        summary_parts.append(f"{ticker} 최신 뉴스 {len(news_data)}건")
                        
            elif source == "valuation" and data:
                for ticker, val_data in data.items():
                    if not val_data.get('error'):
                        pe = val_data.get('trailing_pe', 'N/A')
                        summary_parts.append(f"{ticker} P/E: {pe}")
                        
            elif source == "web_results" and data.get("web_results"):
                summary_parts.append(f"웹 검색 결과 {len(data['web_results'])}건")
                
        return "; ".join(summary_parts) if summary_parts else "관련 데이터 없음"

    def run(self, query: str) -> Dict:
        """챗봇의 메인 실행 로직"""
        logging.info(f"Processing query: {query}")
        
        # 1. 쿼리 확장
        expanded_query = self.query_expander.expand_query(query)
        expanded_query["original_query"] = query
        logging.info(f"Expanded query: {expanded_query}")
        
        # 2. 티커 추출
        tickers = self._extract_tickers_from_query(query, expanded_query)
        logging.info(f"Extracted tickers: {tickers}")
        
        # 3. 데이터 소스 라우팅
        data_sources = DataSourceRouter.route(expanded_query)
        logging.info(f"Selected data sources: {data_sources}")
        
        # 4. 데이터 수집
        data_results = {}
        
        # 관심 종목 질문인데 티커가 없는 경우 (관심 종목이 등록되지 않음)
        if "관심 종목" in query and not tickers:
            return {
                "answer": "등록된 관심 종목이 없습니다. 먼저 관심 종목을 추가해주세요.",
                "tradingview_symbol": None
            }
        
        if "stock_price" in data_sources and tickers:
            data_results["stock_price"] = self.data_retriever.get_stock_price(
                tickers, expanded_query.get("time_range", "recent")
            )
            
        if "stock_news" in data_sources and tickers:
            data_results["stock_news"] = self.data_retriever.get_stock_news(
                tickers, expanded_query.get("keywords", []), expanded_query.get("time_range", "recent")
            )
            
        if "stock_valuation" in data_sources and tickers:
            data_results["valuation"] = self.data_retriever.get_valuation_data(tickers)
            
        if "financial_statements" in data_sources and tickers:
            data_results["financial_statements"] = self.data_retriever.get_financial_statements(tickers)
            
        if "sec_filings" in data_sources and tickers:
            data_results["sec_filings"] = self.data_retriever.search_sec_filings(
                tickers, expanded_query.get("keywords", [])
            )
            
        if "gdelt_events" in data_sources:
            data_results["gdelt_events"] = self.data_retriever.get_gdelt_events(
                expanded_query.get("keywords", []), expanded_query.get("time_range", "1week")
            )
            
        if "tavily_search" in data_sources:
            data_results["web_results"] = self.data_retriever.tavily_search(
                query, expanded_query.get("keywords", [])
            )
        
        # 5. 포트폴리오 관련 처리
        if expanded_query.get("intent") == "portfolio_analysis":
            if self.user_stocks:
                portfolio_info = f"보유 종목: {', '.join([s.get('name', 'N/A') for s in self.user_stocks])}"
                data_results["portfolio"] = {"info": portfolio_info}
            if self.watchlist:
                watchlist_info = f"관심 종목: {', '.join([w.get('name', 'N/A') for w in self.watchlist])}"
                data_results["watchlist"] = {"info": watchlist_info}
        
        # 6. 응답 생성
        answer = self._synthesize_response(expanded_query, data_results)
        
        # 데이터가 부족한 경우 기본 답변 제공
        if not data_results or all(not data or data.get('error') for data in data_results.values()):
            current_date = datetime.now().strftime("%Y년 %m월 %d일")
            
            # fallback에서도 포트폴리오 컨텍스트 포함 여부 결정
            include_portfolio_fallback = self._should_include_portfolio_context(query, expanded_query, tickers)
            
            try:
                if include_portfolio_fallback:
                    portfolio_context = self._create_portfolio_context()
                    fallback_prompt = ChatPromptTemplate.from_template("""
현재 날짜: {current_date}
사용자 질문: {query}

사용자 포트폴리오 정보:
{portfolio_context}

위 질문에 대해 일반적인 투자 지식을 바탕으로 도움이 되는 답변을 작성해주세요.
현재가 {current_date}임을 정확히 인지하고 답변하세요.
사용자의 보유 종목이나 관심 종목과 관련이 있다면 이를 구분해서 언급해주세요.
종목명이나 중요한 정보는 **굵은 글씨**로 강조하고, 여러 항목이 있을 때는 불릿 포인트(- )를 사용하세요.
절대로 임의의 종목명을 만들어내지 마세요. 제공된 데이터에 없는 종목은 언급하지 마세요.
구체적인 데이터가 없더라도 유용한 정보를 제공해주세요.
""")
                    chain = fallback_prompt | self.llm
                    fallback_response = chain.invoke({
                        "current_date": current_date, 
                        "query": query,
                        "portfolio_context": portfolio_context
                    })
                else:
                    fallback_prompt = ChatPromptTemplate.from_template("""
현재 날짜: {current_date}
사용자 질문: {query}

위 질문에 대해 일반적인 투자 지식을 바탕으로 도움이 되는 답변을 작성해주세요.
현재가 {current_date}임을 정확히 인지하고 답변하세요.
질문한 종목에 대해서만 집중해서 답변하세요.
만약 "관심 종목"에 대한 질문이라면 관심 종목에만 집중하고 보유 종목은 언급하지 마세요.
종목명이나 중요한 정보는 **굵은 글씨**로 강조하고, 여러 항목이 있을 때는 불릿 포인트(- )를 사용하세요.
절대로 임의의 종목명을 만들어내지 마세요. 제공된 데이터에 없는 종목은 언급하지 마세요.
구체적인 데이터가 없더라도 유용한 정보를 제공해주세요.
""")
                    chain = fallback_prompt | self.llm
                    fallback_response = chain.invoke({
                        "current_date": current_date, 
                        "query": query
                    })
                
                answer = fallback_response.content if hasattr(fallback_response, 'content') else str(fallback_response)
            except Exception as e:
                logging.error(f"Fallback response error: {e}")
                answer = "죄송합니다. 현재 해당 정보를 조회할 수 없습니다."
        
        # 7. TradingView 차트 필요 여부 결정
        tradingview_symbol = None
        if DataSourceRouter.should_show_chart(expanded_query) and tickers:
            tradingview_symbol = tickers[0]  # 첫 번째 티커로 차트 표시
            
        logging.info(f"Generated answer length: {len(answer)}")
        
        return {
            "answer": answer,
            "tradingview_symbol": tradingview_symbol
        }
