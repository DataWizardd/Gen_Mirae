"""
리포트 생성 에이전트.
전문 에이전트들을 활용하여 종합 투자 리포트를 생성합니다.
"""

import logging
import os
from typing import Dict, List
from urllib.parse import quote

import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser

from agent.base import AgentContext, AgentResult, BaseAgent
from agent.tools import ToolRegistry
from agent.specialists import (
    PriceAnalystAgent,
    NewsAnalystAgent,
    FinancialAnalystAgent,
    EventAnalystAgent,
)
from agent import data_retrieval, pdf_generator
from config.clova_config import MODEL_PARAMS
from langchain_naver import ChatClovaX

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """
    STORM 기반 리포트 생성 에이전트.

    1단계: 데이터 수집 (data_retrieval 모듈)
    2단계: 전문 에이전트별 섹션 분석
    3단계: 최종 리포트 구조화 및 PDF 생성
    """

    SECTION_CONFIG = [
        {
            "heading": "재무 분석",
            "agent": "FinancialAnalystAgent",
            "data_keys": ["financials", "valuation"],
        },
        {
            "heading": "최신 이벤트 및 여론 분석",
            "agent": "NewsAnalystAgent",
            "data_keys": ["documents"],
        },
        {
            "heading": "기술적 분석 및 주가 모멘텀",
            "agent": "PriceAnalystAgent",
            "data_keys": ["prices"],
        },
        {
            "heading": "거시 경제 및 지정학적 리스크",
            "agent": "EventAnalystAgent",
            "data_keys": ["gdelt"],
        },
    ]

    def __init__(self, ticker: str, report_type: str = "summary"):
        llm = ChatClovaX(
            model="HCX-005",
            max_tokens=MODEL_PARAMS.get("max_tokens", 4096),
            temperature=MODEL_PARAMS.get("temperature", 0.1),
            top_p=MODEL_PARAMS.get("top_p", 0.8),
            stream=False,
        )
        super().__init__(llm=llm)
        self.ticker = ticker
        self.report_type = report_type
        self.retrieved_data: Dict[str, pd.DataFrame] = {}
        self.report: Dict = {}
        self.sections: List[Dict] = []

        # 전문 에이전트 초기화
        tool_registry = ToolRegistry()
        self.specialist_agents = {
            "FinancialAnalystAgent": FinancialAnalystAgent(tool_registry, llm=self.llm),
            "NewsAnalystAgent": NewsAnalystAgent(tool_registry, llm=self.llm),
            "PriceAnalystAgent": PriceAnalystAgent(tool_registry, llm=self.llm),
            "EventAnalystAgent": EventAnalystAgent(tool_registry, llm=self.llm),
        }

    def execute(self, context: AgentContext) -> AgentResult:
        """BaseAgent 인터페이스 구현"""
        report = self.run()
        return AgentResult(
            agent_name=self.name,
            analysis=str(report),
            raw_data=report,
        )

    def run(self) -> Dict:
        """리포트 생성 파이프라인을 실행합니다."""
        logger.info(f"[{self.ticker}] 리포트 생성 시작 (타입: {self.report_type})")

        self._retrieve_data()
        self._generate_sections()
        self._synthesize_report()

        if self.report_type == "full":
            self._generate_pdf()

        logger.info(f"[{self.ticker}] 리포트 생성 완료")
        return self.report

    # ------------------------------------------------------------------
    # 1단계: 데이터 수집
    # ------------------------------------------------------------------

    def _retrieve_data(self):
        """모든 데이터 소스에서 원시 데이터를 수집합니다."""
        logger.info(f"[{self.ticker}] 데이터 수집 단계")
        self.retrieved_data["documents"] = data_retrieval.get_combined_documents(self.ticker)
        self.retrieved_data["financials"] = data_retrieval.get_financial_statements(self.ticker)
        self.retrieved_data["valuation"] = data_retrieval.get_valuation_metrics(self.ticker)
        self.retrieved_data["prices"] = data_retrieval.get_stock_prices(self.ticker)
        self.retrieved_data["gdelt"] = data_retrieval.get_gdelt_events(self.ticker)

    # ------------------------------------------------------------------
    # 2단계: 전문 에이전트별 섹션 생성
    # ------------------------------------------------------------------

    def _generate_sections(self):
        """각 섹션을 담당 전문 에이전트가 생성합니다."""
        logger.info(f"[{self.ticker}] 섹션 생성 단계")

        section_prompt = PromptTemplate.from_template(
            "당신은 {ticker}에 대한 금융 분석 보고서를 작성하는 AI 애널리스트입니다.\n"
            "아래 '주제'에 대해 '제공된 컨텍스트'의 데이터를 **분석하고 해석하여** "
            "보고서의 본문 섹션을 한국어로 작성해 주십시오.\n\n"
            "**지침:**\n"
            "1. 데이터를 그대로 나열하지 말고 통찰력 있는 분석을 제공하세요.\n"
            "2. 답변에 제목을 반복하지 마세요.\n"
            "3. 전문적이고 분석적인 톤으로 간결하게 작성하세요.\n"
            "4. 제공된 데이터 외의 정보는 사용하지 마세요.\n"
            "5. 핵심 내용을 불릿 포인트(`-`)나 굵은 글씨(`**`)로 강조하세요.\n\n"
            "--- 제공된 컨텍스트 ---\n{context_str}\n\n"
            "--- 주제 ---\n{topic}\n\n"
            "--- 보고서 본문 (한국어, Markdown) ---\n"
        )
        chain = section_prompt | self.llm | StrOutputParser()

        for config in self.SECTION_CONFIG:
            heading = config["heading"]
            agent_name = config["agent"]
            data_keys = config["data_keys"]

            context_str = self._format_context(data_keys)
            if "No relevant data available" in context_str:
                logger.warning(f"[{self.ticker}] '{heading}' 데이터 없음 → 건너뜀")
                continue

            logger.info(f"[{self.ticker}] [{agent_name}] '{heading}' 섹션 생성")
            content = chain.invoke({
                "ticker": self.ticker,
                "context_str": context_str,
                "topic": heading,
            })
            self.sections.append({"heading": heading, "content": content})

    def _format_context(self, data_keys: List[str]) -> str:
        """지정된 키의 데이터를 LLM 입력용 문자열로 변환합니다."""
        parts = []
        has_data = False
        for key in data_keys:
            df = self.retrieved_data.get(key)
            if df is not None and not df.empty:
                has_data = True
                parts.append(f"--- {key.upper()} DATA ---\n{df.head(15).to_string(index=False)}\n")
        return "\n".join(parts) if has_data else "No relevant data available in the context."

    # ------------------------------------------------------------------
    # 3단계: 리포트 종합 & PDF
    # ------------------------------------------------------------------

    def _synthesize_report(self):
        """섹션들을 최종 리포트로 구조화합니다."""
        logger.info(f"[{self.ticker}] 리포트 구조화")
        self.report = {
            "title": f"{self.ticker} 종목 분석 리포트",
            "sections": self.sections,
        }

    def _generate_pdf(self):
        """PDF를 생성하고 다운로드 URL을 설정합니다."""
        logger.info(f"[{self.ticker}] PDF 생성")
        if self.report.get("sections"):
            local_path = pdf_generator.generate_pdf_report(self.report)
            file_name = os.path.basename(local_path)
            self.report["pdf_url"] = f"/reports/{quote(file_name)}"
        else:
            self.report["pdf_url"] = None
            logger.warning(f"[{self.ticker}] 섹션이 없어 PDF 생성 건너뜀")


if __name__ == "__main__":
    pass
