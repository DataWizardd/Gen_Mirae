import os
import logging
import pandas as pd
from typing import Dict, List, Any

from langchain_naver import ChatClovaX
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from clova_config import MODEL_PARAMS

from agent import data_retrieval, pdf_generator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReportAgent:
    def __init__(self, ticker: str, report_type: str = "summary"):
        self.ticker = ticker
        self.report_type = report_type
        self.llm = ChatClovaX(
            model="HCX-005",
            max_tokens=MODEL_PARAMS.get("max_tokens", 4096),
            temperature=MODEL_PARAMS.get("temperature", 0.1),
            top_p=MODEL_PARAMS.get("top_p", 0.8),
            stream=False,
        )
        self.retrieved_data = {}
        self.report = {}
        self.sections = []

    def run(self) -> Dict:
        """STORM 프로세스를 실행하여 리포트를 생성합니다."""
        logging.info(f"[{self.ticker}] 리포트 생성을 시작합니다 (타입: {self.report_type})...")
        
        self._retrieve_data()
        self._generate_report_sections()
        self._synthesize_report()
        
        if self.report_type == "full":
            self._generate_and_set_pdf_url()
            
        logging.info(f"[{self.ticker}] 리포트 생성이 완료되었습니다.")
        return self.report

    def _retrieve_data(self):
        """1단계: 모든 필요한 데이터를 조회합니다."""
        logging.info("데이터 조회 단계 시작...")
        self.retrieved_data['documents'] = data_retrieval.get_combined_documents(self.ticker)
        self.retrieved_data['financials'] = data_retrieval.get_financial_statements(self.ticker)
        self.retrieved_data['valuation'] = data_retrieval.get_valuation_metrics(self.ticker)
        self.retrieved_data['prices'] = data_retrieval.get_stock_prices(self.ticker)
        self.retrieved_data['gdelt'] = data_retrieval.get_gdelt_events(self.ticker)

    def _generate_report_sections(self):
        """각 주제에 대해 보고서 섹션을 생성합니다."""
        logging.info("보고서 섹션 생성 단계 시작...")
        
        section_topic_map = {
            "재무 분석": ['financials', 'valuation'],
            "최신 이벤트 및 여론 분석": ['documents'],
            "기술적 분석 및 주가 모멘텀": ['prices'],
            "거시 경제 및 지정학적 리스크": ['gdelt']
        }
        
        prompt_template = PromptTemplate.from_template(
            "당신은 {ticker}에 대한 금융 분석 보고서를 작성하는 AI 애널리스트입니다.\n"
            "아래 '주제'에 대해 '제공된 컨텍스트'의 데이터를 **분석하고 해석하여** 보고서의 본문 섹션을 한국어로 작성해 주십시오.\n\n"
            "**매우 중요한 지침:**\n"
            "1.  **통찰력 있는 분석 제공:** 절대 데이터를 그대로 나열하지 마십시오. 데이터가 의미하는 바(예: 재무 건전성, 수익성, 성장 추세, 시장 리스크 등)에 대한 전문적인 분석과 통찰을 제공해야 합니다.\n"
            "2.  **제목 반복 금지:** 생성하는 내용은 '주제'에 대한 본문이어야 합니다. **답변에 '주제'나 제목을 절대로 다시 쓰지 마세요.**\n"
            "3.  **객관적인 보고서 형식:** 대화체가 아닌, 전문가적이고 분석적인 톤으로 간결하게 작성하세요.\n"
            "4.  **컨텍스트 기반 작성:** 제공된 데이터 외의 정보는 절대 사용하지 마세요.\n"
            "5.  **구조화된 내용:** 가독성을 위해 핵심 내용을 불릿 포인트(`-`)나 굵은 글씨(`**`)로 강조하여 구조화하세요.\n\n"
            "--- 제공된 컨텍스트 ---\n"
            "{context_str}\n\n"
            "--- 주제 ---\n"
            "{topic}\n\n"
            "--- 보고서 본문 (제목을 절대 포함하지 말 것. 한국어, Markdown 형식) ---\n"
        )
        
        chain = prompt_template | self.llm | StrOutputParser()
        
        for topic, data_keys in section_topic_map.items():
            context_str = self._format_context_for_llm(data_keys)
            
            if "No relevant data available" not in context_str:
                logging.info(f"LLM 호출: '{topic}' 섹션 생성")
                content = chain.invoke({
                    "ticker": self.ticker,
                    "context_str": context_str,
                    "topic": topic
                })
                self.sections.append({"heading": topic, "content": content})
            else:
                logging.warning(f"LLM 호출 건너뜀: '{topic}' (관련 데이터 없음)")

    def _format_context_for_llm(self, data_keys: List[str]) -> str:
        """지정된 키에 해당하는 데이터만 단일 문자열로 포맷팅합니다."""
        parts = []
        has_data = False
        for key in data_keys:
            df = self.retrieved_data.get(key)
            if df is not None and not df.empty:
                has_data = True
                df_str = df.head(15).to_string(index=False)
                parts.append(f"--- {key.upper()} DATA ---\n{df_str}\n")
        
        return "\n".join(parts) if has_data else "No relevant data available in the context."

    def _synthesize_report(self):
        """생성된 섹션들을 종합하여 최종 리포트를 구조화합니다."""
        logging.info("리포트 종합 및 구조화 단계 시작...")
        
        self.report = {
            "title": f"{self.ticker} 종목 분석 리포트",
            "sections": self.sections
        }

    def _generate_and_set_pdf_url(self):
        """PDF를 생성하고 다운로드 가능한 API 경로를 설정합니다."""
        logging.info("PDF 생성 및 URL 설정 단계 시작...")
        import os
        from urllib.parse import quote
        
        if self.report.get("sections"):
            local_pdf_path = pdf_generator.generate_pdf_report(self.report)
            file_name = os.path.basename(local_pdf_path)
            encoded_file_name = quote(file_name)
            self.report["pdf_url"] = f"/reports/{encoded_file_name}"
        else:
            self.report["pdf_url"] = None
            logging.warning("PDF 생성을 건너뜁니다. 리포트에 포함할 섹션이 없습니다.")

if __name__ == '__main__':
    # ... (테스트 코드는 동일) ...
    pass
