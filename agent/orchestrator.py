"""
오케스트레이터 에이전트.
사용자 질의를 분석하고, 전문 에이전트들에게 작업을 위임한 뒤,
결과를 종합하여 최종 응답을 생성합니다.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_naver import ChatClovaX

from agent.base import AgentContext, AgentResult, BaseAgent
from agent.tools import ToolRegistry, STOCK_MAP
from agent.specialists import (
    PriceAnalystAgent,
    NewsAnalystAgent,
    FinancialAnalystAgent,
    EventAnalystAgent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Intent → Specialist 매핑
# ---------------------------------------------------------------------------
INTENT_AGENT_MAP = {
    "price_check":        ["PriceAnalystAgent"],
    "news_search":        ["NewsAnalystAgent"],
    "valuation_analysis": ["PriceAnalystAgent", "FinancialAnalystAgent"],
    "financial_analysis": ["FinancialAnalystAgent"],
    "sec_filing_search":  ["FinancialAnalystAgent"],
    "market_sentiment":   ["NewsAnalystAgent", "EventAnalystAgent"],
    "portfolio_analysis": ["PriceAnalystAgent", "NewsAnalystAgent"],
    "general_search":     ["PriceAnalystAgent", "NewsAnalystAgent"],
}


class OrchestratorAgent(BaseAgent):
    """
    다중 에이전트 오케스트레이터.

    1. 쿼리 분석 (의도·티커·키워드 추출)
    2. 전문 에이전트 디스패치
    3. 결과 종합 및 최종 응답 생성
    """

    def __init__(
        self,
        user_stocks: List[Dict] = None,
        watchlist: List[Dict] = None,
    ):
        super().__init__()
        self.user_stocks = user_stocks or []
        self.watchlist = watchlist or []
        self.current_date = datetime.now().strftime("%Y년 %m월 %d일")

        # 도구 레지스트리 & 전문 에이전트 초기화
        self.tool_registry = ToolRegistry()
        self.specialists: Dict[str, BaseAgent] = {
            "PriceAnalystAgent": PriceAnalystAgent(self.tool_registry, llm=self.llm),
            "NewsAnalystAgent": NewsAnalystAgent(self.tool_registry, llm=self.llm),
            "FinancialAnalystAgent": FinancialAnalystAgent(self.tool_registry, llm=self.llm),
            "EventAnalystAgent": EventAnalystAgent(self.tool_registry, llm=self.llm),
        }

    # ------------------------------------------------------------------
    # 1단계: 쿼리 분석
    # ------------------------------------------------------------------

    def _analyze_query(self, query: str) -> AgentContext:
        """LLM을 사용하여 사용자 쿼리를 분석합니다."""
        analysis_prompt = ChatPromptTemplate.from_template("""
사용자 질문을 분석하여 다음 정보를 JSON 형태로 추출해주세요:

사용자 질문: {query}

추출할 정보:
1. intent: 질문의 의도
   - price_check: 주가, 가격, 시세 관련
   - news_search: 뉴스, 기사 관련
   - valuation_analysis: 밸류에이션, P/E, PBR 등 지표 관련
   - financial_analysis: 재무제표, 손익계산서 관련
   - sec_filing_search: SEC 공시 관련
   - market_sentiment: 시장 감정, 이벤트, 트렌드 관련
   - portfolio_analysis: 포트폴리오, 보유종목 관련
   - general_search: 그 외 일반

2. tickers: 언급된 종목 티커 (예: ["AAPL", "NVDA"])
3. time_range: 시간 범위 (recent, 1week, 1month, 1quarter, 1year)
4. keywords: 핵심 키워드 리스트
5. needs_chart: 차트 필요 여부 (boolean)

JSON 형태로만 응답하세요.
""")
        try:
            content = self._invoke_llm(analysis_prompt, {"query": query})
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
            parsed = json.loads(content.strip())
        except Exception as e:
            logger.warning(f"[{self.name}] LLM 쿼리 분석 실패, 규칙 기반으로 전환: {e}")
            parsed = self._rule_based_analysis(query)

        # 포트폴리오 기반 티커 보강
        tickers = self._enrich_tickers(query, parsed.get("tickers", []))

        return AgentContext(
            query=query,
            tickers=tickers,
            intent=parsed.get("intent", "general_search"),
            time_range=parsed.get("time_range", "recent"),
            keywords=parsed.get("keywords", [query]),
            needs_chart=parsed.get("needs_chart", False),
            user_stocks=self.user_stocks,
            watchlist=self.watchlist,
        )

    def _rule_based_analysis(self, query: str) -> Dict:
        """LLM 분석 실패 시 규칙 기반 폴백"""
        intent = "general_search"
        needs_chart = False
        if any(kw in query for kw in ["주가", "가격", "시세", "현재가"]):
            intent, needs_chart = "price_check", True
        elif any(kw in query for kw in ["뉴스", "기사"]):
            intent = "news_search"
        elif any(kw in query for kw in ["보유", "포트폴리오", "관심"]):
            intent = "portfolio_analysis"
        elif any(kw in query for kw in ["밸류에이션", "P/E", "PBR", "지표"]):
            intent = "valuation_analysis"
        elif any(kw in query for kw in ["재무", "실적", "매출", "영업이익"]):
            intent = "financial_analysis"
        elif any(kw in query for kw in ["이벤트", "지정학", "리스크", "트렌드"]):
            intent = "market_sentiment"
        return {"intent": intent, "tickers": [], "time_range": "recent",
                "keywords": [query], "needs_chart": needs_chart}

    def _enrich_tickers(self, query: str, tickers: List[str]) -> List[str]:
        """한글 종목명·포트폴리오에서 티커를 추가로 추출합니다."""
        for name, ticker in STOCK_MAP.items():
            if name in query and ticker not in tickers:
                tickers.append(ticker)

        portfolio_phrases = ["내 보유", "내 종목", "보유 종목", "내 포트폴리오"]
        if any(p in query for p in portfolio_phrases):
            for s in self.user_stocks:
                sym = s.get("symbol", "").upper()
                if sym and sym not in tickers:
                    tickers.append(sym)

        watchlist_phrases = ["관심 종목", "지켜보는 종목"]
        if any(p in query for p in watchlist_phrases):
            for w in self.watchlist:
                sym = w.get("symbol", "").upper()
                if sym and sym not in tickers:
                    tickers.append(sym)

        all_phrases = ["모든 종목", "전체 종목"]
        if any(p in query for p in all_phrases):
            for s in self.user_stocks + self.watchlist:
                sym = s.get("symbol", "").upper()
                if sym and sym not in tickers:
                    tickers.append(sym)

        return list(set(tickers))

    # ------------------------------------------------------------------
    # 2단계: 전문 에이전트 디스패치
    # ------------------------------------------------------------------

    def _dispatch(self, context: AgentContext) -> List[AgentResult]:
        """의도에 맞는 전문 에이전트들을 호출합니다."""
        agent_names = INTENT_AGENT_MAP.get(context.intent, ["PriceAnalystAgent", "NewsAnalystAgent"])

        logger.info(f"[{self.name}] 디스패치: intent={context.intent} → {agent_names}")

        results = []
        for name in agent_names:
            agent = self.specialists.get(name)
            if agent:
                try:
                    result = agent.execute(context)
                    results.append(result)
                    logger.info(f"[{self.name}] {name} 완료 (데이터: {result.has_data})")
                except Exception as e:
                    logger.error(f"[{self.name}] {name} 실행 실패: {e}", exc_info=True)
        return results

    # ------------------------------------------------------------------
    # 3단계: 응답 종합
    # ------------------------------------------------------------------

    def _synthesize(self, context: AgentContext, agent_results: List[AgentResult]) -> str:
        """전문 에이전트 결과들을 종합하여 최종 답변을 생성합니다."""
        analyses = [r for r in agent_results if r.has_data]

        if not analyses:
            return self._generate_fallback(context)

        agent_reports = "\n\n".join([
            f"--- {r.agent_name} 분석 ---\n{r.analysis}" for r in analyses
        ])

        include_portfolio = self._should_include_portfolio(context)
        portfolio_section = ""
        if include_portfolio:
            portfolio_section = f"\n\n사용자 포트폴리오 정보:\n{self._format_portfolio()}"

        synthesis_prompt = ChatPromptTemplate.from_template(
            "당신은 투자 자문 AI 오케스트레이터입니다.\n"
            "아래는 전문 에이전트들의 분석 결과입니다.\n\n"
            "사용자 질문: {query}\n"
            "현재 날짜: {current_date}\n"
            "{portfolio_section}\n\n"
            "전문 에이전트 분석 결과:\n{agent_reports}\n\n"
            "위 분석들을 종합하여 사용자 질문에 대한 최종 답변을 한국어로 작성하세요.\n"
            "가이드라인:\n"
            "- 각 에이전트의 분석을 자연스럽게 통합하세요\n"
            "- 종목명이나 중요 수치는 **굵은 글씨**로 강조하세요\n"
            "- 여러 항목은 불릿 포인트(- )로 구조화하세요\n"
            "- 제공된 데이터에 없는 종목이나 수치를 임의로 만들지 마세요\n"
        )
        return self._invoke_llm(synthesis_prompt, {
            "query": context.query,
            "current_date": self.current_date,
            "portfolio_section": portfolio_section,
            "agent_reports": agent_reports,
        })

    def _generate_fallback(self, context: AgentContext) -> str:
        """데이터가 부족할 때 일반 지식 기반 응답을 생성합니다."""
        fallback_prompt = ChatPromptTemplate.from_template(
            "현재 날짜: {current_date}\n"
            "사용자 질문: {query}\n\n"
            "데이터베이스에서 관련 데이터를 찾지 못했습니다.\n"
            "일반적인 투자 지식을 바탕으로 도움이 되는 답변을 한국어로 작성하세요.\n"
            "절대로 임의의 수치나 종목명을 만들지 마세요."
        )
        return self._invoke_llm(fallback_prompt, {
            "current_date": self.current_date,
            "query": context.query,
        })

    def _should_include_portfolio(self, context: AgentContext) -> bool:
        if context.intent == "portfolio_analysis":
            return True
        portfolio_phrases = ["내 보유", "내 종목", "보유 종목", "관심 종목", "내 포트폴리오"]
        return any(p in context.query for p in portfolio_phrases)

    def _format_portfolio(self) -> str:
        parts = [f"현재 날짜: {self.current_date}"]
        if self.user_stocks:
            items = []
            for s in self.user_stocks:
                name = s.get("name", s.get("symbol", "N/A"))
                qty = s.get("quantity", 0)
                avg = s.get("avgPrice", 0)
                items.append(f"{name}({qty}주, 평균단가 ${avg:.2f})" if qty and avg else name)
            parts.append(f"보유 종목(투자중): {', '.join(items)}")
        if self.watchlist:
            names = [w.get("name", w.get("symbol", "N/A")) for w in self.watchlist]
            parts.append(f"관심 종목(관찰중): {', '.join(names)}")
        return "; ".join(parts)

    # ------------------------------------------------------------------
    # 메인 실행
    # ------------------------------------------------------------------

    def execute(self, context: AgentContext) -> AgentResult:
        """BaseAgent 인터페이스 구현 (내부용)"""
        results = self._dispatch(context)
        answer = self._synthesize(context, results)
        return AgentResult(agent_name=self.name, analysis=answer, confidence=0.9)

    def run(self, query: str) -> Dict:
        """
        외부 API에서 호출하는 메인 엔트리포인트.
        기존 Chatbot.run()과 동일한 응답 형식을 반환합니다.
        """
        logger.info(f"[{self.name}] 쿼리 수신: {query}")

        # 1. 쿼리 분석
        context = self._analyze_query(query)
        logger.info(f"[{self.name}] 분석 결과: intent={context.intent}, tickers={context.tickers}")

        # 관심 종목 질문인데 등록된 종목이 없는 경우
        if "관심 종목" in query and not context.tickers:
            return {
                "answer": "등록된 관심 종목이 없습니다. 먼저 관심 종목을 추가해주세요.",
                "tradingview_symbol": None
            }

        # 2. 전문 에이전트 디스패치 & 응답 종합
        result = self.execute(context)

        if not result.analysis:
            result = AgentResult(
                agent_name=self.name,
                analysis="죄송합니다. 현재 해당 정보를 조회할 수 없습니다."
            )

        # 3. TradingView 차트 심볼 결정
        tradingview_symbol = None
        if context.intent == "price_check" and context.needs_chart and context.tickers:
            tradingview_symbol = context.tickers[0]

        logger.info(f"[{self.name}] 응답 생성 완료 (길이: {len(result.analysis)})")

        return {
            "answer": result.analysis,
            "tradingview_symbol": tradingview_symbol
        }
