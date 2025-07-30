import os
import logging
import pandas as pd
import psycopg2
import yfinance as yf
from dotenv import load_dotenv
from psycopg2.extras import execute_values

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

def fetch_valuation_data(tickers):
    """yfinance를 사용하여 벨류에이션 지표를 가져옵니다."""
    metrics = [
        "trailingPE", "forwardPE", "priceToBook", "priceToSalesTrailing12Months",
        "enterpriseToRevenue", "enterpriseToEbitda", "marketCap", "enterpriseValue",
        "totalRevenue", "netIncomeToCommon"
    ]
    
    rows = []
    logging.info(f"{tickers}에 대한 벨류에이션 데이터 수집을 시작합니다.")
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            row = {"ticker": ticker}
            for m in metrics:
                row[m] = info.get(m)
            rows.append(row)
            logging.info(f"✅ {ticker}: 데이터 수집 성공")
        except Exception as e:
            logging.error(f"❌ {ticker} 데이터 수집 중 오류 발생: {e}")
    
    logging.info("벨류에이션 데이터 수집이 완료되었습니다.")
    return pd.DataFrame(rows)

def insert_valuation_data(conn, df_valuation):
    """수집한 벨류에이션 데이터를 DB에 단순 삽입합니다 (INSERT)."""
    if df_valuation.empty:
        logging.info("삽입할 벨류에이션 데이터가 없습니다.")
        return
        
    df_processed = df_valuation.where(pd.notnull(df_valuation), None)
    data_tuples = [tuple(x) for x in df_processed.to_numpy()]
    
    # 시계열 데이터이므로 단순 INSERT
    query = """
        INSERT INTO stock_valuation (ticker, trailing_pe, forward_pe, price_to_book, price_to_sales, 
                                     enterprise_to_revenue, enterprise_to_ebitda, market_cap, 
                                     enterprise_value, total_revenue, net_income_to_common)
        VALUES %s;
    """
    
    with conn.cursor() as cursor:
        try:
            execute_values(cursor, query, data_tuples)
            conn.commit()
            logging.info(f"{cursor.rowcount}개의 새로운 벨류에이션 데이터를 성공적으로 삽입했습니다.")
        except psycopg2.Error as e:
            logging.error(f"데이터 삽입 중 오류 발생: {e}")
            conn.rollback()

def main():
    """메인 실행 함수"""
    load_dotenv()
    
    TICKERS = ["AAPL", "AMZN", "NVDA", "MSFT", "GOOGL"]
    
    # 1. 벨류에이션 데이터 가져오기
    df_valuation = fetch_valuation_data(TICKERS)
    
    if not df_valuation.empty:
        # 2. 데이터베이스 연결
        conn = get_db_connection()
        if conn:
            # 3. 데이터베이스에 삽입
            insert_valuation_data(conn, df_valuation)
            # 4. 연결 종료
            conn.close()
            logging.info("데이터베이스 연결을 종료합니다.")

if __name__ == "__main__":
    main() 