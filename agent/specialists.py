"""
전문 분석 에이전트 모듈.
각 에이전트는 특정 도메인의 데이터를 수집·분석하여 독립적인 인사이트를 제공합니다.
"""

import logging
from typing import Dict, List

from langchain_core.prompts import ChatPromptTemplate

from agent.base import AgentContext, AgentResult, BaseAgent
from agent.tools import ToolRegistry

logger = logging.getLogger(__name__)


class PriceAnalystAgent(BaseAgent):
    """주가 및 밸류에이션 전문 분석 에이전트"""

    def __init__(self, tool_registry: ToolRegistry, **kwargs):
        super().__init__(**kwargs)
        self.price_tool = tool_registry.get("get_stock_price")
        self.valuation_tool = tool_registry.get("get_valuation_data")

    def execute(self, context: AgentContext) -> AgentResult:
        if not context.tickers:
            return AgentResult(agent_name=self.name, analysis="", source="price")

        logger.info(f"[{self.name}] {context.tickers} 주가·밸류에이션 분석 시작")

        price_data = self.price_tool(tickers=context.tickers, time_range=context.time_range)
        valuation_data = self.valuation_tool(tickers=context.tickers)

        raw_data = {"price": price_data, "valuation": valuation_data}
        data_summary = self._summarize(price_data, valuation_data)

        if not data_summary:
            return AgentResult(agent_name=self.name, analysis="", raw_data=raw_data, source="price")

        prompt = ChatPromptTemplate.from_template(
            "당신은 주가 및 밸류에이션 전문 애널리스트입니다.\n\n"
            "분석 대상 종목: {tickers}\n"
            "수집된 데이터:\n{data_summary}\n\n"
            "위 데이터를 기반으로 간결하고 전문적인 주가·밸류에이션 분석을 한국어로 작성하세요.\n"
            "핵심 수치를 **굵은 글씨**로 강조하고, 불릿 포인트(- )로 구조화하세요."
        )
        analysis = self._invoke_llm(prompt, {
            "tickers": ", ".join(context.tickers),
            "data_summary": data_summary,
        })
        return AgentResult(
            agent_name=self.name, analysis=analysis,
            raw_data=raw_data, confidence=0.9, source="price"
        )

    def _summarize(self, price_data: Dict, valuation_data: Dict) -> str:
        parts = []
        for ticker, data in price_data.items():
            if isinstance(data, list) and data:
                latest = data[0]
                parts.append(f"{ticker} 현재가: ${latest.get('close', 'N/A')}")
        for ticker, data in valuation_data.items():
            if isinstance(data, dict) and data:
                pe = data.get('trailing_pe', 'N/A')
                pb = data.get('price_to_book', 'N/A')
                cap = data.get('market_cap', 'N/A')
                parts.append(f"{ticker} P/E: {pe}, PBR: {pb}, 시가총액: {cap}")
        return "; ".join(parts)


class NewsAnalystAgent(BaseAgent):
    """뉴스 및 여론 분석 에이전트"""

    def __init__(self, tool_registry: ToolRegistry, **kwargs):
        super().__init__(**kwargs)
        self.news_tool = tool_registry.get("get_stock_news")
        self.web_tool = tool_registry.get("tavily_search")

    def execute(self, context: AgentContext) -> AgentResult:
        if not context.tickers:
            return AgentResult(agent_name=self.name, analysis="", source="news")

        logger.info(f"[{self.name}] {context.tickers} 뉴스·여론 분석 시작")

        news_data = self.news_tool(tickers=context.tickers, time_range=context.time_range)
        web_data = self.web_tool(query=context.query, keywords=context.keywords)

        raw_data = {"news": news_data, "web": web_data}
        data_summary = self._summarize(news_data, web_data)

        if not data_summary:
            return AgentResult(agent_name=self.name, analysis="", raw_data=raw_data, source="news")

        prompt = ChatPromptTemplate.from_template(
            "당신은 금융 뉴스 및 시장 여론 분석 전문가입니다.\n\n"
            "분석 대상: {tickers}\n"
            "수집된 뉴스 및 웹 데이터:\n{data_summary}\n\n"
            "뉴스 흐름과 시장 심리를 분석하여 한국어로 간결하게 작성하세요.\n"
            "중요 이벤트를 **굵은 글씨**로 강조하세요."
        )
        analysis = self._invoke_llm(prompt, {
            "tickers": ", ".join(context.tickers),
            "data_summary": data_summary,
        })
        return AgentResult(
            agent_name=self.name, analysis=analysis,
            raw_data=raw_data, confidence=0.85, source="news"
        )

    def _summarize(self, news_data: Dict, web_data: Dict) -> str:
        parts = []
        for ticker, articles in news_data.items():
            if isinstance(articles, list):
                for a in articles[:3]:
                    parts.append(f"[{ticker}] {a.get('title', '')}")
        web_results = web_data.get("web_results", [])
        if isinstance(web_results, list):
            for r in web_results[:3]:
                if isinstance(r, dict):
                    parts.append(f"[웹] {r.get('content', r.get('title', ''))[:120]}")
        return "\n".join(parts)


class FinancialAnalystAgent(BaseAgent):
    """재무제표 및 SEC 공시 분석 에이전트"""

    def __init__(self, tool_registry: ToolRegistry, **kwargs):
        super().__init__(**kwargs)
        self.financial_tool = tool_registry.get("get_financial_statements")
        self.sec_tool = tool_registry.get("search_sec_filings")

    def execute(self, context: AgentContext) -> AgentResult:
        if not context.tickers:
            return AgentResult(agent_name=self.name, analysis="", source="financial")

        logger.info(f"[{self.name}] {context.tickers} 재무·공시 분석 시작")

        financial_data = self.financial_tool(tickers=context.tickers)
        sec_data = self.sec_tool(tickers=context.tickers)

        raw_data = {"financials": financial_data, "sec_filings": sec_data}
        data_summary = self._summarize(financial_data, sec_data)

        if not data_summary:
            return AgentResult(agent_name=self.name, analysis="", raw_data=raw_data, source="financial")

        prompt = ChatPromptTemplate.from_template(
            "당신은 기업 재무제표 및 SEC 공시 분석 전문가입니다.\n\n"
            "분석 대상: {tickers}\n"
            "수집된 재무 데이터:\n{data_summary}\n\n"
            "재무 건전성, 수익성, 성장성을 중심으로 전문적인 분석을 한국어로 작성하세요.\n"
            "핵심 재무 지표를 **굵은 글씨**로 강조하세요."
        )
        analysis = self._invoke_llm(prompt, {
            "tickers": ", ".join(context.tickers),
            "data_summary": data_summary,
        })
        return AgentResult(
            agent_name=self.name, analysis=analysis,
            raw_data=raw_data, confidence=0.85, source="financial"
        )

    def _summarize(self, financial_data: Dict, sec_data: Dict) -> str:
        parts = []
        for ticker, statements in financial_data.items():
            if isinstance(statements, list) and statements:
                parts.append(f"[{ticker}] 재무제표 {len(statements)}분기 데이터 확보")
                for s in statements[:2]:
                    parts.append(f"  - {s.get('statement_type', '')} / {s.get('period', '')}")
        for ticker, filings in sec_data.items():
            if isinstance(filings, list) and filings:
                parts.append(f"[{ticker}] SEC 공시 {len(filings)}건 확보")
                for f in filings[:2]:
                    meta = f.get('metadata', {})
                    if isinstance(meta, dict):
                        parts.append(f"  - {meta.get('form_type', 'N/A')}")
        return "\n".join(parts)


class EventAnalystAgent(BaseAgent):
    """거시경제 및 지정학적 이벤트 분석 에이전트"""

    def __init__(self, tool_registry: ToolRegistry, **kwargs):
        super().__init__(**kwargs)
        self.gdelt_tool = tool_registry.get("get_gdelt_events")

    def execute(self, context: AgentContext) -> AgentResult:
        search_keywords = context.keywords or context.tickers
        if not search_keywords:
            return AgentResult(agent_name=self.name, analysis="", source="event")

        logger.info(f"[{self.name}] 지정학적 이벤트 분석 시작 (키워드: {search_keywords})")

        gdelt_data = self.gdelt_tool(keywords=search_keywords, time_range=context.time_range)

        raw_data = {"gdelt": gdelt_data}
        events = gdelt_data.get("events", [])

        if not events:
            return AgentResult(agent_name=self.name, analysis="", raw_data=raw_data, source="event")

        data_summary = self._summarize(events)

        prompt = ChatPromptTemplate.from_template(
            "당신은 거시경제 및 지정학적 리스크 분석 전문가입니다.\n\n"
            "관련 키워드: {keywords}\n"
            "수집된 GDELT 이벤트 데이터:\n{data_summary}\n\n"
            "지정학적 리스크와 투자 영향을 분석하여 한국어로 작성하세요.\n"
            "리스크 수준과 핵심 이벤트를 **굵은 글씨**로 강조하세요."
        )
        analysis = self._invoke_llm(prompt, {
            "keywords": ", ".join(search_keywords),
            "data_summary": data_summary,
        })
        return AgentResult(
            agent_name=self.name, analysis=analysis,
            raw_data=raw_data, confidence=0.8, source="event"
        )

    def _summarize(self, events: List[Dict]) -> str:
        parts = []
        for e in events[:7]:
            actor1 = e.get('actor1_name', 'N/A')
            actor2 = e.get('actor2_name', 'N/A')
            tone = e.get('avg_tone', 0)
            goldstein = e.get('goldstein_scale', 0)
            date = e.get('event_date', 'N/A')
            parts.append(f"[{date}] {actor1} ↔ {actor2} | 톤: {tone:.1f}, 골드스타인: {goldstein}")
        return "\n".join(parts)
