"""
에이전트가 사용할 수 있는 도구(Tool) 레지스트리.
데이터 조회 함수들을 에이전트 호출 가능한 도구로 래핑합니다.
"""

import os
import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

db_params = {
    "dbname": os.getenv("PG_NAME"), "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"), "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT")
}


@dataclass
class Tool:
    """에이전트가 호출할 수 있는 단일 도구"""
    name: str
    description: str
    func: Callable
    category: str  # price, news, financial, event, search

    def __call__(self, **kwargs) -> Any:
        logger.info(f"[Tool:{self.name}] 실행 - params: {list(kwargs.keys())}")
        return self.func(**kwargs)


def _execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """DB 쿼리를 안전하게 실행합니다."""
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall() if cur.description else []
    except Exception as e:
        logger.error(f"[DB] 쿼리 실행 중 오류: {e}", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# 도구 함수 정의
# ---------------------------------------------------------------------------

STOCK_MAP = {
    "애플": "AAPL", "엔비디아": "NVDA", "마이크로소프트": "MSFT",
    "아마존": "AMZN", "알파벳": "GOOGL", "테슬라": "TSLA"
}


def _resolve_ticker(ticker: str) -> str:
    return STOCK_MAP.get(ticker, ticker.upper())


def get_stock_price(tickers: List[str], time_range: str = "recent") -> Dict[str, Any]:
    """주가 시계열 데이터를 조회합니다."""
    results = {}
    for ticker in tickers:
        symbol = _resolve_ticker(ticker)
        if time_range == "recent":
            query = "SELECT close, time FROM stock_price WHERE symbol = %s ORDER BY time DESC LIMIT 1"
            params = (symbol,)
        else:
            days_map = {"1week": 7, "1month": 30, "1quarter": 90, "1year": 365}
            days = days_map.get(time_range, 1)
            cutoff = datetime.now() - timedelta(days=days)
            query = "SELECT close, time FROM stock_price WHERE symbol = %s AND time >= %s ORDER BY time DESC"
            params = (symbol, cutoff)
        result = _execute_query(query, params)
        results[symbol] = result if result else []
    return results


def get_stock_news(tickers: List[str], time_range: str = "recent") -> Dict[str, Any]:
    """종목 관련 뉴스를 조회합니다."""
    results = {}
    for ticker in tickers:
        symbol = _resolve_ticker(ticker)
        if time_range == "recent":
            query = "SELECT title, description, url, published_at FROM stock_news WHERE ticker = %s ORDER BY published_at DESC LIMIT 5"
            params = (symbol,)
        else:
            days_map = {"1week": 7, "1month": 30, "1quarter": 90, "1year": 365}
            days = days_map.get(time_range, 7)
            cutoff = datetime.now() - timedelta(days=days)
            query = "SELECT title, description, url, published_at FROM stock_news WHERE ticker = %s AND published_at >= %s ORDER BY published_at DESC"
            params = (symbol, cutoff)
        result = _execute_query(query, params)
        results[symbol] = result if result else []
    return results


def get_valuation_data(tickers: List[str]) -> Dict[str, Any]:
    """밸류에이션 지표를 조회합니다."""
    results = {}
    for ticker in tickers:
        symbol = _resolve_ticker(ticker)
        query = """
        SELECT trailing_pe, forward_pe, price_to_book, price_to_sales,
               market_cap, enterprise_value, updated_at
        FROM stock_valuation WHERE ticker = %s
        ORDER BY updated_at DESC LIMIT 1
        """
        result = _execute_query(query, (symbol,))
        results[symbol] = result[0] if result else {}
    return results


def get_financial_statements(tickers: List[str]) -> Dict[str, Any]:
    """재무제표 데이터를 조회합니다."""
    results = {}
    for ticker in tickers:
        symbol = _resolve_ticker(ticker)
        query = """
        SELECT statement_type, period, data
        FROM financial_statements WHERE ticker = %s
        ORDER BY period DESC LIMIT 5
        """
        result = _execute_query(query, (symbol,))
        results[symbol] = result if result else []
    return results


def search_sec_filings(tickers: List[str]) -> Dict[str, Any]:
    """SEC 공시 문서를 검색합니다."""
    results = {}
    for ticker in tickers:
        symbol = _resolve_ticker(ticker)
        query = """
        SELECT document, metadata, created_at
        FROM sec_filings
        WHERE metadata->>'symbol' = %s
        ORDER BY created_at DESC LIMIT 3
        """
        result = _execute_query(query, (symbol,))
        results[symbol] = result if result else []
    return results


def get_gdelt_events(keywords: List[str], time_range: str = "1week") -> Dict[str, Any]:
    """GDELT 지정학적 이벤트 데이터를 조회합니다."""
    if not keywords:
        return {"events": []}
    days_map = {"1week": 7, "1month": 30, "1quarter": 90}
    days = days_map.get(time_range, 7)
    cutoff = datetime.now() - timedelta(days=days)

    keyword_conditions = " OR ".join(
        ["actor1_name ILIKE %s OR actor2_name ILIKE %s" for _ in keywords]
    )
    query = f"""
    SELECT actor1_name, actor2_name, event_code, goldstein_scale, avg_tone,
           event_date, source_url
    FROM gdelt_events
    WHERE event_date >= %s AND ({keyword_conditions})
    ORDER BY event_date DESC LIMIT 10
    """
    params = [cutoff]
    for kw in keywords:
        params.extend([f"%{kw}%", f"%{kw}%"])
    result = _execute_query(query, tuple(params))
    return {"events": result if result else []}


def tavily_search(query: str, keywords: List[str]) -> Dict[str, Any]:
    """Tavily 웹 검색을 수행합니다."""
    try:
        search_tool = TavilySearchResults(max_results=5)
        search_query = f"{query} {' '.join(keywords)}"
        results = search_tool.invoke(search_query)
        return {"web_results": results}
    except Exception as e:
        logger.error(f"[Tavily] 검색 오류: {e}")
        return {"web_results": []}


# ---------------------------------------------------------------------------
# 도구 레지스트리
# ---------------------------------------------------------------------------

class ToolRegistry:
    """에이전트가 사용 가능한 전체 도구 목록을 관리합니다."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_defaults()

    def _register_defaults(self):
        defaults = [
            Tool("get_stock_price", "주가 시계열 데이터를 조회합니다.", get_stock_price, "price"),
            Tool("get_stock_news", "종목 관련 뉴스를 조회합니다.", get_stock_news, "news"),
            Tool("get_valuation_data", "밸류에이션 지표(P/E, PBR 등)를 조회합니다.", get_valuation_data, "price"),
            Tool("get_financial_statements", "재무제표 데이터를 조회합니다.", get_financial_statements, "financial"),
            Tool("search_sec_filings", "SEC 공시 문서를 검색합니다.", search_sec_filings, "financial"),
            Tool("get_gdelt_events", "지정학적 이벤트 데이터를 조회합니다.", get_gdelt_events, "event"),
            Tool("tavily_search", "웹 검색을 수행합니다.", tavily_search, "search"),
        ]
        for tool in defaults:
            self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_by_category(self, category: str) -> List[Tool]:
        return [t for t in self._tools.values() if t.category == category]

    def list_tools(self) -> List[str]:
        return [f"{t.name}: {t.description}" for t in self._tools.values()]
