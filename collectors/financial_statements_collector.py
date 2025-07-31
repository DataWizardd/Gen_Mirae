import os
import logging
import json
import pandas as pd
import psycopg2
import yfinance as yf
from dotenv import load_dotenv
from psycopg2.extras import execute_values
import numpy as np

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """데이터베이스 연결을 생성합니다."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            database=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            port=os.getenv("PG_PORT")
        )
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"데이터베이스 연결에 실패했습니다: {e}")
        return None

def fetch_financial_statements(ticker_symbol):
    """yfinance를 사용하여 특정 종목의 연간/분기 재무제표를 가져옵니다."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        statements = {
            "annual_income_statement": ticker.financials,
            "annual_balance_sheet": ticker.balance_sheet,
            "annual_cash_flow": ticker.cashflow,
            "quarterly_income_statement": ticker.quarterly_financials,
            "quarterly_balance_sheet": ticker.quarterly_balance_sheet,
            "quarterly_cash_flow": ticker.quarterly_cashflow
        }
        logging.info(f"✅ {ticker_symbol}: 재무제표 데이터 수집 성공")
        return statements
    except Exception as e:
        logging.error(f"❌ {ticker_symbol} 재무제표 수집 중 오류 발생: {e}")
        return {}

def process_and_prepare_data(ticker, statements):
    """수집한 재무제표 데이터를 DB에 삽입할 형태로 가공합니다."""
    records = []
    for stmt_type, df in statements.items():
        if df.empty:
            continue
        
        # DataFrame을 JSON 친화적인 포맷으로 변환
        df_reset = df.reset_index().rename(columns={'index': 'item'})
        
        # 'item' 컬럼을 제외한 나머지 기간(Timestamp) 컬럼들을 순회
        period_columns = [col for col in df_reset.columns if col != 'item']
        
        for period_col in period_columns:
            # period_col은 Timestamp 객체입니다. DB 저장을 위해 문자열로 변환합니다.
            period_str = period_col.strftime('%Y-%m-%d')
            
            # 해당 기간의 데이터만 추출합니다. ('item' 컬럼과 현재 기간 컬럼)
            # .copy()를 사용하여 SettingWithCopyWarning을 방지합니다.
            period_df = df_reset[['item', period_col]].copy()
            
            # JSON으로 변환하기 쉽도록 기간 컬럼명을 'value'로 일괄 변경합니다.
            period_df.rename(columns={period_col: 'value'}, inplace=True)
            
            # 숫자가 아닌 값(NaN, None)을 Python의 None(JSON의 null)으로 변환 후 dict 리스트로 만듭니다.
            # [FIX] NaN 값을 Python의 None으로 명시적으로 변환합니다.
            # json.dumps는 None을 null로 올바르게 변환합니다.
            period_df['value'] = period_df['value'].replace({np.nan: None})
            
            period_data = period_df.to_dict('records')
            
            records.append((
                ticker,
                stmt_type,
                period_str,
                json.dumps(period_data, ensure_ascii=False) # JSON 문자열로 변환
            ))
    return records
    
def upsert_financial_data(conn, all_records):
    """가공된 재무제표 데이터를 DB에 삽입 또는 업데이트합니다."""
    if not all_records:
        logging.info("업데이트할 재무제표 데이터가 없습니다.")
        return

    query = """
        INSERT INTO financial_statements (ticker, statement_type, period, data)
        VALUES %s
        ON CONFLICT (ticker, statement_type, period) DO UPDATE SET
            data = EXCLUDED.data;
    """
    with conn.cursor() as cursor:
        try:
            execute_values(cursor, query, all_records)
            conn.commit()
            logging.info(f"{cursor.rowcount}개의 재무제표 데이터를 성공적으로 삽입/업데이트했습니다.")
        except psycopg2.Error as e:
            logging.error(f"데이터 삽입/업데이트 중 오류 발생: {e}")
            conn.rollback()

def main():
    """메인 실행 함수"""
    load_dotenv()
    
    TICKERS = ["AAPL", "AMZN", "NVDA", "MSFT", "GOOGL"]
    all_financial_records = []
    
    logging.info("재무제표 데이터 수집을 시작합니다.")
    for ticker in TICKERS:
        statements = fetch_financial_statements(ticker)
        if statements:
            records = process_and_prepare_data(ticker, statements)
            all_financial_records.extend(records)
    
    if all_financial_records:
        conn = get_db_connection()
        if conn:
            upsert_financial_data(conn, all_financial_records)
            conn.close()
            logging.info("데이터베이스 연결을 종료합니다.")

if __name__ == "__main__":
    main() 