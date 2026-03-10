"""
에이전트 시스템의 기본 인터페이스 및 데이터 모델을 정의합니다.
모든 에이전트는 BaseAgent를 상속하여 execute() 메서드를 구현합니다.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain_naver import ChatClovaX


logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """에이전트 실행에 필요한 컨텍스트"""
    query: str
    tickers: List[str] = field(default_factory=list)
    intent: str = "general_search"
    time_range: str = "recent"
    keywords: List[str] = field(default_factory=list)
    needs_chart: bool = False
    user_stocks: List[Dict] = field(default_factory=list)
    watchlist: List[Dict] = field(default_factory=list)


@dataclass
class AgentResult:
    """에이전트 실행 결과"""
    agent_name: str
    analysis: str
    raw_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    source: str = ""

    @property
    def has_data(self) -> bool:
        return bool(self.analysis and self.analysis.strip())


class BaseAgent(ABC):
    """모든 에이전트의 기본 추상 클래스"""

    def __init__(self, llm: ChatClovaX = None):
        self.llm = llm or ChatClovaX(model="HCX-005", temperature=0.1)
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """에이전트의 핵심 로직을 실행합니다."""
        ...

    def _invoke_llm(self, prompt_template, variables: Dict[str, Any]) -> str:
        """LLM을 호출하고 텍스트 응답을 반환합니다."""
        try:
            chain = prompt_template | self.llm
            response = chain.invoke(variables)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"[{self.name}] LLM 호출 실패: {e}", exc_info=True)
            return ""

    def __repr__(self):
        return f"<{self.name}>"
