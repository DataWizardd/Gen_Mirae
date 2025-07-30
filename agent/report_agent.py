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
        self._generate_perspectives()
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

    def _generate_perspectives(self):
        """각 질문에 대해 데이터가 있을 경우에만 LLM 답변을 생성합니다."""
        logging.info("다각도 질문 및 답변 생성 단계 시작...")
        
        question_context_map = {
            "이 종목의 주요 재무 강점과 약점은 무엇인가?": ['financials', 'valuation'],
            "최근 뉴스·공시·커뮤니티 이슈 중 투자에 긍정적·부정적 영향을 준 이벤트는?": ['documents'],
            "주가 모멘텀(가격 추세·거래량 변화)은 어떤가?": ['prices'],
            "GDELT 이벤트 지표를 고려했을 때, 글로벌 환경 변화가 이 종목에 미칠 영향은?": ['gdelt']
        }
        
        prompt_template = PromptTemplate.from_template(
            "You are a financial analyst summarizing information for a report on {ticker}.\n"
            "Answer the following question in Korean, using only the provided context. "
            "Do not use any external knowledge. If the context is somehow insufficient despite being provided, be concise.\n"
            "Structure your answer in concise bullet points.\n\n"
            "--- CONTEXT ---\n"
            "{context_str}\n\n"
            "--- QUESTION ---\n"
            "{question}\n\n"
            "--- ANSWER (in Korean) ---\n"
        )
        
        chain = prompt_template | self.llm | StrOutputParser()
        
        for question, data_keys in question_context_map.items():
            context_str = self._format_context_for_llm(data_keys)
            
            # 데이터가 존재할 때만 LLM 호출
            if "No relevant data available" not in context_str:
                logging.info(f"LLM 호출: '{question}' (데이터 존재)")
                answer = chain.invoke({
                    "ticker": self.ticker,
                    "context_str": context_str,
                    "question": question
                })
                self.sections.append({"question": question, "answer": answer})
            else:
                logging.warning(f"LLM 호출 건너뜀: '{question}' (관련 데이터 없음)")

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
        """5 & 6단계: 답변들을 종합하여 최종 리포트를 구조화합니다."""
        logging.info("리포트 종합 및 구조화 단계 시작...")
        
        section_mapping = {
            "이 종목의 주요 재무 강점과 약점은 무엇인가?": "재무 분석",
            "최근 뉴스·공시·커뮤니티 이슈 중 투자에 긍정적·부정적 영향을 준 이벤트는?": "최신 이벤트 및 여론 분석",
            "주가 모멘텀(가격 추세·거래량 변화)은 어떤가?": "기술적 분석 및 주가 모멘텀",
            "GDELT 이벤트 지표를 고려했을 때, 글로벌 환경 변화가 이 종목에 미칠 영향은?": "거시 경제 및 지정학적 리스크"
        }
        
        # self.sections에 있는 내용만으로 리포트 구성
        self.report = {
            "title": f"{self.ticker} 종목 분석 리포트",
            "sections": [
                {"heading": section_mapping.get(s["question"]), "content": s["answer"]}
                for s in self.sections if section_mapping.get(s["question"])
            ]
        }

    def _generate_and_set_pdf_url(self):
        """PDF를 생성하고 다운로드 가능한 API 경로를 설정합니다."""
        logging.info("PDF 생성 및 URL 설정 단계 시작...")
        import os
        from urllib.parse import quote
        
        # 생성할 섹션이 있을 경우에만 PDF 생성
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
