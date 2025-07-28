import psycopg2
from psycopg2.extras import RealDictCursor
import re
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import pandas as pd
# from phoenix.trace import instrument

# @instrument
def get_tradingview_widget(symbol: str) -> str:
    """TradingView 위젯 HTML을 생성합니다."""
    sanitized_symbol = re.sub(r'[^a-zA-Z0-9]', '', symbol)
    return f"""
    <div class="tradingview-widget-container" style="height:350px;width:100%">
      <div id="tradingview_widget_{sanitized_symbol}" style="height:calc(100% - 32px);width:100%"></div>
      <div class="tradingview-widget-copyright" style="height:32px;width:100%">
        <a href="https://kr.tradingview.com/" rel="noopener nofollow" target="_blank">
          <span class="blue-text">TradingView에서 모든 시장 추적</span>
        </a>
      </div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
        "autosize": true,
        "symbol": "{sanitized_symbol}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "kr",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "tradingview_widget_{sanitized_symbol}"
      }}
      );
      </script>
    </div>
    """

class StructuredAgent:
    def __init__(self, llm, db_params):
        self.llm = llm
        self.db_params = db_params

    # @instrument
    def get_portfolio_performance(self, user_stocks: list) -> (str, None):
        """사용자의 포트폴리오 수익률을 계산하고 요약합니다."""
        if not user_stocks:
            return "보유하신 종목 정보가 없습니다. 포트폴리오를 먼저 구성해주세요.", None

        try:
            total_investment = 0
            current_total_value = 0
            
            summary_list = []

            for stock in user_stocks:
                symbol = stock.get("티커")
                quantity = stock.get("수량", 0)
                avg_price = stock.get("평균단가", 0)
                current_price = stock.get("현재가") # 프론트에서 받은 실시간 현재가 사용

                # 현재가가 없는 경우 DB에서 조회 (폴백)
                if current_price is None:
                    conn = psycopg2.connect(**self.db_params)
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        "SELECT close FROM stock_price WHERE symbol = %s ORDER BY time DESC LIMIT 1",
                        (symbol,)
                    )
                    result = cursor.fetchone()
                    current_price = result['close'] if result else float(avg_price)
                    cursor.close()
                    conn.close()
                
                if not symbol: continue

                investment = quantity * float(avg_price)
                current_value = quantity * float(current_price)
                profit_loss = current_value - investment
                return_rate = (profit_loss / investment) * 100 if investment > 0 else 0

                total_investment += investment
                current_total_value += current_value
                
                summary_list.append(
                    f"- {stock.get('종목명')} ({symbol}): "
                    f"수익률 {return_rate:.2f}% (손익: ${profit_loss:,.2f})"
                )
            
            total_profit_loss = current_total_value - total_investment
            total_return_rate = (total_profit_loss / total_investment) * 100 if total_investment > 0 else 0

            performance_summary = (
                f"총 수익률: {total_return_rate:.2f}%\n"
                f"총 투자금: ${total_investment:,.2f}\n"
                f"현재 평가금액: ${current_total_value:,.2f}\n"
                f"총 손익: ${total_profit_loss:,.2f}\n\n"
                "종목별 현황:\n" + "\n".join(summary_list)
            )
            
            return performance_summary, None
        except Exception as e:
            return f"포트폴리오 수익률을 계산하는 중 오류가 발생했습니다: {e}", None

    # @instrument
    def get_financial_metric(self, user_query: str, symbol: str) -> (str, None):
        """특정 주식의 재무 지표(PER, PBR 등)를 조회합니다."""
        metric_mapping = {
            "PER": "pe_ratio", "주가수익비율": "pe_ratio",
            "PBR": "pb_ratio", "주가순자산비율": "pb_ratio",
            "총매출": "total_revenue", "매출": "total_revenue",
            "순이익": "net_income",
            "시가총액": "market_cap", "시총": "market_cap"
        }

        found_metric_korean = None
        found_metric_db_col = None
        for term, col_name in metric_mapping.items():
            if term.lower() in user_query.lower():
                found_metric_korean = term
                found_metric_db_col = col_name
                break
        
        if not found_metric_db_col:
            return "어떤 재무 지표를 찾으시나요? (예: PER, PBR, 시가총액)", None
            
        if not symbol:
            return "어떤 종목의 재무 지표를 찾으시나요?", None

        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = f"SELECT {found_metric_db_col} FROM financial_metrics WHERE symbol = %s"
            cur.execute(query, (symbol,))
            
            row = cur.fetchone()
            conn.close()
            
            if row and row[found_metric_db_col] is not None:
                value = row[found_metric_db_col]
                # 숫자형 데이터는 포맷팅, 그 외는 그대로 출력
                if isinstance(value, (int, float)):
                    return f"{symbol}의 {found_metric_korean}({found_metric_db_col.replace('_', ' ').title()})는 {value:,.2f}입니다.", None
                else:
                    return f"{symbol}의 {found_metric_korean}({found_metric_db_col.replace('_', ' ').title()})는 {value}입니다.", None
            else:
                return f"{symbol}의 {found_metric_korean} 정보를 찾을 수 없습니다.", None
                
        except Exception as e:
            return f"재무 정보를 가져오는데 실패했습니다: {e}", None

    def run(self, user_query: str, user_stocks: list):

        if re.search(r"(수익률|포트폴리오|계좌)", user_query):
            return "get_portfolio_performance"
        if re.search(r"(주가|가격)", user_query):
            return "get_stock_price"
        return "get_stock_price" # 기본값

    # @instrument
    def get_stock_price(self, symbol: str) -> (str, str):
        """특정 주식의 현재 가격을 조회하고 TradingView 위젯을 반환합니다."""
        try:
            conn = psycopg2.connect(**self.db_params)
            cur  = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT close FROM stock_price WHERE symbol=%s ORDER BY time DESC LIMIT 1",
                (symbol,)
            )
            row = cur.fetchone()
            conn.close()
            latest_price = row if row else None
            if latest_price:
                answer = f"{symbol}의 현재 주가는 약 ${latest_price['close']:.2f} 입니다."
                tradingview_html = get_tradingview_widget(symbol)
                return answer, tradingview_html
            else:
                return f"{symbol}의 주가 정보를 찾을 수 없습니다.", None
        except Exception as e:
            return f"주가 정보를 가져오는데 실패했습니다: {e}", None

class PortfolioAnalysisAgent:
    def __init__(self, llm):
        self.llm = llm

    # @instrument
    def run(self, user_stocks: list) -> (str, None):
        """사용자의 보유 종목을 기반으로 포트폴리오를 분석합니다."""
        if not user_stocks:
            return "분석할 보유 종목 정보가 없습니다.", None

        # 프롬프트 생성
        prompt = self._create_prompt(user_stocks)
        
        # LLM을 사용하여 페르소나 분석
        response = self.llm.invoke(prompt)
        
        return response.content, None

    def _create_prompt(self, user_stocks: list) -> str:
        holdings_summary = "없음"
        if user_stocks:
            holdings_summary = ", ".join(
                [f"{s.get('종목명', '')}({s.get('티커', '')})" for s in user_stocks]
            )

        prompt_template = f"""
        당신은 전문 포트폴리오 분석가입니다. 사용자의 보유 종목을 바탕으로 포트폴리오의 특징과 투자 성향을 분석해주세요. 분석 결과는 친절하고 상세한 설명 형식으로 최대 3~4문장으로 요약해주세요.

        ### 사용자 보유 종목:
        - {holdings_summary}

        ### 분석 예시:
        - (보유: 애플, 엔비디아, 마이크로소프트) -> "고객님의 포트폴리오는 주로 대형 기술주에 집중되어 있습니다. 이는 기술 분야의 성장에 대한 높은 확신을 바탕으로 한 '성장주 중심의 투자 전략'을 추구하시는 것으로 보입니다."
        - (보유: 코카콜라, 존슨앤드존슨, P&G) -> "고객님의 포트폴리오는 안정적인 현금 흐름과 배당을 제공하는 필수소비재 및 헬스케어 기업들로 구성되어 있습니다. 이는 '안정 추구형 가치 투자' 성향을 명확히 보여줍니다."

        ### 분석 시작:
        """
        return prompt_template.strip()


class UnstructuredAgent:
    """DB에서 최신 리포트 3개를 가져오는 역할을 합니다."""
    # @instrument
    def run(self, db_params: dict) -> str:
        try:
            conn = psycopg2.connect(**db_params)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT metadata->>'source' AS source, document AS summary
                FROM company_reports
                ORDER BY created_at DESC LIMIT 3
            """)
            rows = cur.fetchall()
            conn.close()
            if not rows:
                return "현재 데이터베이스에 저장된 최신 리포트가 없습니다."
            return "\n".join(f"- {r['source']}: {r['summary']}" for r in rows)
        except Exception as e:
            return f"리포트 정보를 가져오는 중 오류가 발생했습니다: {e}"


class WatchlistAnalysisAgent:
    def __init__(self, llm, db_params, search_tool):
        self.llm = llm
        self.db_params = db_params
        self.search_tool = search_tool

    # @instrument
    def run(self, watchlist: list) -> (str, None):
        """사용자의 관심 종목을 기반으로 특징을 분석합니다."""
        if not watchlist:
            return "분석할 관심 종목 정보가 없습니다.", None

        stock_names = [item['name'] for item in watchlist]
        prompt = self._create_prompt(stock_names)
        response = self.llm.invoke(prompt)
        return response.content, None

    # @instrument
    def rank_stocks(self, watchlist: list) -> (str, None):
        """관심 종목의 매력도를 DB 리포트 또는 웹 검색을 통해 분석하고 추천합니다."""
        if not watchlist:
            return "분석할 관심 종목 정보가 없습니다.", None

        symbols = [item['symbol'] for item in watchlist]
        stock_names_map = {item['symbol']: item['name'] for item in watchlist}
        
        # 1. DB에서 리포트 검색
        report_summaries = self._get_report_summaries_from_db(symbols)
        
        # 2. DB에 정보가 없는 종목에 대해 웹 검색 수행
        missing_symbols = [s for s in symbols if s not in report_summaries]
        if missing_symbols:
            web_summaries = self._get_summaries_from_web(missing_symbols, stock_names_map)
            report_summaries.update(web_summaries)
        
        if not report_summaries:
            return "관심 종목에 대한 최신 정보를 찾을 수 없어 매력도를 분석하기 어렵습니다.", None

        prompt = self._create_ranking_prompt(report_summaries, stock_names_map)
        response = self.llm.invoke(prompt)
        return response.content, None

    def _get_report_summaries_from_db(self, symbols: list) -> dict:
        summaries = {}
        try:
            conn = psycopg2.connect(**self.db_params)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            for symbol in symbols:
                cur.execute("""
                    SELECT document FROM company_reports
                    WHERE metadata->>'source' ILIKE %s
                    ORDER BY created_at DESC LIMIT 1
                """, (f'%{symbol}%',))
                result = cur.fetchone()
                if result: summaries[symbol] = result['document']
            cur.close()
            conn.close()
        except Exception: return {}
        return summaries

    def _get_summaries_from_web(self, symbols: list, stock_names_map: dict) -> dict:
        """Tavily 웹 검색을 통해 종목 정보를 수집합니다."""
        summaries = {}
        for symbol in symbols:
            stock_name = stock_names_map.get(symbol, symbol)
            query = f"{stock_name} ({symbol}) 주가 전망 및 최신 뉴스 분석"
            search_results = self.search_tool.run(query)
            if search_results:
                summary_text = "\n".join([f"- {res.get('title', '')}: {res.get('content', '')}" for res in search_results])
                summaries[symbol] = f"웹 검색 결과 요약:\n{summary_text}"
        return summaries

    def _create_ranking_prompt(self, summaries: dict, stock_names_map: dict) -> str:
        context = ""
        for symbol, summary in summaries.items():
            stock_name = stock_names_map.get(symbol, symbol)
            context += f"### {stock_name}({symbol}) 분석:\n{summary}\n\n"

        prompt_template = f"""
        당신은 최고의 투자 전략가입니다. 제공된 각 주식에 대한 최신 분석 리포트를 바탕으로, 현재 시점에서 가장 매력적인 종목을 하나만 선택하고 그 이유를 설명해주세요.

        ### 분석 대상 종목 리포트 요약:
        {context}

        ### 지시사항:
        1.  모든 종목의 긍정적인 점과 부정적인 점을 비교 분석하세요.
        2.  그 분석을 바탕으로, 가장 투자 매력도가 높다고 판단되는 종목을 **단 하나만** 선택하세요.
        3.  왜 그 종목을 선택했는지 명확하고 논리적인 이유를 2~3문장으로 설명해주세요.
        4.  "가장 매력적인 종목은 [종목명]입니다." 로 답변을 시작하세요.

        ### 분석 시작:
        """
        return prompt_template.strip()

    def _create_prompt(self, watchlist: list) -> str:
        watchlist_summary = ", ".join(watchlist)
        prompt_template = f"""
        당신은 전문 주식 분석가입니다. 사용자의 관심 종목 목록을 바탕으로, 해당 종목들이 공통적으로 속한 산업, 기술, 또는 투자 테마를 분석해주세요. 분석 결과는 친절하고 상세한 설명 형식으로 최대 3~4문장으로 요약해주세요.

        ### 사용자 관심 종목:
        - {watchlist_summary}

        ### 분석 예시:
        - (관심 종목: 브로드컴, 메타, 넷플릭스, 테슬라) -> "고객님의 관심 종목들은 주로 AI, 클라우드 컴퓨팅, 전기차 등 미래 성장성이 높은 기술 분야를 선도하는 기업들입니다. 이는 혁신 기술을 통해 시장을 주도하는 기업에 대한 높은 관심도를 보여줍니다."
        
        ### 분석 시작:
        """
        return prompt_template.strip()


class WebAgent:
    def __init__(self, llm, search_tool):
        self.llm = llm
        self.search_tool = search_tool
    
    # @instrument
    def run(self, user_input, *_):
        results = self.search_tool.run(user_input)
        return "\n".join(
            f"- {item.get('title','')} : {item.get('content','')[:100]}… ({item.get('url','')})"
            for item in results
        )

class Orchestrator:
    def __init__(self, llm, search_tool, db_params):
        self.llm = llm
        self.structured_agent = StructuredAgent(llm, db_params)
        self.portfolio_analysis_agent = PortfolioAnalysisAgent(llm)
        self.watchlist_analysis_agent = WatchlistAnalysisAgent(llm, db_params, search_tool)
        self.unstructured_agent = UnstructuredAgent()
        self.web_agent = WebAgent(llm, search_tool)

    # @instrument
    def _augment_and_classify_query(self, user_query: str) -> str:
        """사용자의 질문을 분석하여 명확한 의도(intent)로 분류합니다."""
        
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "당신은 사용자의 질문 의도를 정확하게 분석하고 분류하는 전문가입니다. "
                    "사용자의 질문을 아래에 정의된 '카테고리' 중 가장 적절한 하나로 분류해주세요. "
                    "다른 설명 없이 오직 카테고리 이름 하나만 응답해야 합니다."
                ),
                (
                    "user",
                    "### 사용자 질문:\n{query}\n\n"
                    "### 카테고리:\n"
                    "- GET_PORTFOLIO_PERFORMANCE: '수익률', '계좌 현황', '보유 종목' 등 포트폴리오의 수치적 실적을 묻는 질문\n"
                    "- ANALYZE_PORTFOLIO_COMPOSITION: '포트폴리오 평가', '분석', '진단', '어때' 등 보유 종목 구성에 대한 질적 분석을 요청하는 질문\n"
                    "- RANK_WATCHLIST_STOCKS: '관심 종목' 중에서 '추천', '매력', '골라줘' 등 순위나 우열을 가려달라는 질문\n"
                    "- ANALYZE_WATCHLIST_STOCKS: '관심 종목'의 특징이나 공통점을 '분석'해달라는 질문\n"
                    "- GET_UNSTRUCTURED_REPORTS: '최신 리포트', '최근 증권사 리포트', '리포트 알려줘' 등 DB의 비정형 리포트 요약을 요청하는 질문\n"
                    "- GET_STOCK_PRICE: 특정 종목의 '주가'나 '가격'을 묻는 질문\n"
                    "- GET_FINANCIAL_METRIC: 'PER', 'PBR', '매출' 등 특정 종목의 재무 지표를 묻는 질문\n"
                    "- WEB_SEARCH: '뉴스', '기사', '최신 정보' 등 웹 검색이 필요한 질문\n"
                    "- GENERAL_CONVERSATION: 위의 어느 카테고리에도 속하지 않는 일반 대화나 정보 요청\n\n"
                    "### 분류 결과 (카테고리 이름만 출력):"
                ),
            ]
        )
        
        chain = prompt | self.llm
        response = chain.invoke({"query": user_query})
        
        # LLM 응답에서 카테고리 이름만 추출
        intent = response.content.strip()
        return intent

    # @instrument
    def route(self, user_query: str, user_stocks: list, watchlist: list, db_params: dict) -> (str, str, str):
        """쿼리 증강을 통해 사용자의 의도를 명확히 파악하고, 그에 따라 적절한 에이전트로 라우팅합니다."""
        
        # 1. 쿼리 증강 및 의도 분류
        intent = self._augment_and_classify_query(user_query)

        # 2. 분류된 의도에 따라 에이전트 실행
        
        # 포트폴리오 수익률 조회
        if intent == "GET_PORTFOLIO_PERFORMANCE":
            context, tradingview_html = self.structured_agent.get_portfolio_performance(user_stocks)
            if "보유하신" in context or "오류가 발생했습니다" in context: return context, tradingview_html, "structured (portfolio)"
            prompt = ChatPromptTemplate.from_messages([("system", "당신은 '미래에셋 AI 애널리스트'입니다. 주어진 포트폴리오 실적 데이터를 바탕으로 사용자의 질문에 친절하고 대화적인 톤으로 답변해주세요. 먼저 총 수익률을 언급하며 전체적인 요약을 한 문장으로 시작하고, 그 다음에 상세 내역(총 투자금, 평가금액, 총 손익)을 명확히 전달합니다. 마지막으로 종목별 현황을 목록으로 제시합니다. 개인적인 의견이나 투자 조언은 절대 추가하지 마세요. 답변은 항상 한국어로 해야 합니다."),("user", "포트폴리오 데이터:\n{context}\n\n사용자 질문:\n{question}")])
            chain = RunnablePassthrough.assign(context=lambda x: context) | prompt | self.llm
            return chain.invoke({"question": user_query}).content, tradingview_html, "structured (portfolio)"

        # 포트폴리오 구성 분석
        elif intent == "ANALYZE_PORTFOLIO_COMPOSITION":
            answer, tradingview_html = self.portfolio_analysis_agent.run(user_stocks)
            return answer, tradingview_html, "persona"

        # 관심 종목 순위 추천
        elif intent == "RANK_WATCHLIST_STOCKS":
            answer, tradingview_html = self.watchlist_analysis_agent.rank_stocks(watchlist)
            return answer, tradingview_html, "persona"

        # 관심 종목 특징 분석
        elif intent == "ANALYZE_WATCHLIST_STOCKS":
            answer, tradingview_html = self.watchlist_analysis_agent.run(watchlist)
            return answer, tradingview_html, "persona"

        # 비정형 리포트 조회
        elif intent == "GET_UNSTRUCTURED_REPORTS":
            context = self.unstructured_agent.run(db_params)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "당신은 '미래에셋 AI 애널리스트'입니다. 주어진 최신 리포트 요약 목록을 바탕으로 사용자의 질문에 답변해주세요. 각 리포트를 명확하게 구분하여 전달해야 합니다. 답변은 항상 한국어로 해야 합니다."),
                ("user", "최신 리포트 목록:\n{context}\n\n질문:\n{question}")
            ])
            chain = prompt | self.llm
            return chain.invoke({"context": context, "question": user_query}).content, None, "unstructured"

        # 특정 종목 주가 조회
        elif intent == "GET_STOCK_PRICE":
            mapping = {"애플":"AAPL","엔비디아":"NVDA","마이크로소프트":"MSFT","아마존":"AMZN","알파벳":"GOOGL"}
            symbol = next((sym for kor, sym in mapping.items() if kor in user_query), None)
            answer, tradingview_html = self.structured_agent.get_stock_price(symbol)
            return answer, tradingview_html, "structured (price)"

        # 재무 지표 조회
        elif intent == "GET_FINANCIAL_METRIC":
            mapping = {"애플":"AAPL","엔비디아":"NVDA","마이크로소프트":"MSFT","아마존":"AMZN","알파벳":"GOOGL"}
            symbol = next((sym for kor, sym in mapping.items() if kor in user_query), None)
            context, _ = self.structured_agent.get_financial_metric(user_query, symbol)
            if "어떤" in context or "찾을 수 없습니다" in context or "실패했습니다" in context: return context, None, "structured (metric)"
            prompt = ChatPromptTemplate.from_messages([("system", "당신은 '미래에셋 AI 애널리스트'입니다. 주어진 재무 데이터를 바탕으로 사용자의 질문에 답변해주세요. 데이터를 간결하고 명확하게 전달해야 합니다. 답변은 항상 한국어로 해야 합니다."),("user", "재무 데이터:\n{context}\n\n사용자 질문:\n{question}")])
            chain = RunnablePassthrough.assign(context=lambda x: context) | prompt | self.llm
            return chain.invoke({"question": user_query}).content, None, "structured (metric)"
        
        # 웹 검색 또는 일반 대화
        else: # GENERAL_CONVERSATION 또는 WEB_SEARCH
            context = ""
            if user_stocks:
                stocks_summary = ", ".join([f"{s.get('종목명', '')}({s.get('티커', '')})" for s in user_stocks])
                context += f"사용자 보유 종목: {stocks_summary}\n\n"

            if intent == "WEB_SEARCH":
                agent_type = "web"
                search_results = self.web_agent.run(user_query)
                context += search_results
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", "당신은 '증권사 AI 애널리스트'입니다. 주어진 웹 검색 결과를 바탕으로 사용자의 질문에 대해 친절하게 답변해주세요. 투자 조언은 하지 않으며, 검색된 정보를 요약하여 전달합니다. 답변은 항상 한국어로 해야 합니다."),
                    ("user", "웹 검색 결과:\n{context}\n\n사용자 질문:\n{question}")
                ])
                chain = prompt_template | self.llm
                return chain.invoke({"context": context, "question": user_query}).content, None, agent_type
            
            else: # GENERAL_CONVERSATION
                # 범용 대화는 특별한 컨텍스트 없이 바로 LLM에 전달 (UnstructuredAgent 사용 안함)
                prompt_template = ChatPromptTemplate.from_messages([("system", "당신은 '증권사 AI 애널리스트'입니다. 사용자의 일반적인 질문에 대해 친절하게 대화해주세요. 투자 조언은 하지 않습니다. 답변은 항상 한국어로 해야 합니다."),("user", "질문:\n{question}")])
                chain = prompt_template | self.llm
                return chain.invoke({"question": user_query}).content, None, "unstructured"
            
            # 웹 검색 결과가 있는 경우
            