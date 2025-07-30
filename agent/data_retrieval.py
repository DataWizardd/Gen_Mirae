import os
import logging
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """데이터베이스 연결을 생성하고 pgvector를 등록합니다."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            database=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            port=os.getenv("PG_PORT")
        )
        register_vector(conn)
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"데이터베이스 연결 실패: {e}")
        raise

def get_combined_documents(ticker: str, limit: int = 50) -> pd.DataFrame:
    """주어진 티커에 대해 뉴스, 레딧, SEC 공시 문서를 최신순으로 가져옵니다."""
    # 각 소스에서 가져올 데이터 수를 분배합니다.
    limit_per_source = limit // 3

    query = f"""
    (
        SELECT 'news' as source, published_at as "timestamp", title, description as text, embedding
        FROM stock_news
        WHERE ticker = %(ticker)s AND embedding IS NOT NULL
        ORDER BY published_at DESC
        LIMIT {limit_per_source}
    )
    UNION ALL
    (
        SELECT 'reddit' as source, created_utc as "timestamp", title, selftext as text, embedding
        FROM reddit_posts
        WHERE ticker = %(ticker)s AND embedding IS NOT NULL
        ORDER BY created_utc DESC
        LIMIT {limit_per_source}
    )
    UNION ALL
    (
        SELECT 
            'sec_filing' as source, 
            (metadata->>'filing_date')::TIMESTAMPTZ as "timestamp",
            'SEC Filing: ' || (metadata->>'form_type') as title,
            document as text,
            embedding
        FROM sec_filings
        WHERE metadata->>'symbol' = %(ticker)s AND embedding IS NOT NULL
        ORDER BY "timestamp" DESC
        LIMIT {limit_per_source}
    )
    ORDER BY "timestamp" DESC;
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params={'ticker': ticker})
        logging.info(f"[{ticker}] 뉴스, 레딧, 공시 문서 {len(df)}개 조회 완료.")
        return df

def get_financial_statements(ticker: str, quarters: int = 4) -> pd.DataFrame:
    """최근 분기 재무제표 데이터를 가져옵니다."""
    query = """
    SELECT * FROM financial_statements
    WHERE ticker = %(ticker)s
    ORDER BY "period" DESC
    LIMIT %(limit)s;
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params={'ticker': ticker, 'limit': quarters})
        logging.info(f"[{ticker}] 재무제표 {len(df)}개 분기 조회 완료.")
        return df

def get_valuation_metrics(ticker: str) -> pd.DataFrame:
    """최신 밸류에이션 지표를 가져옵니다."""
    query = """
    SELECT * FROM stock_valuation
    WHERE ticker = %(ticker)s
    ORDER BY "updated_at" DESC
    LIMIT 1;
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params={'ticker': ticker})
        logging.info(f"[{ticker}] 밸류에이션 지표 조회 완료.")
        return df
        
def get_stock_prices(ticker: str, days: int = 90) -> pd.DataFrame:
    """최근 주가 시계열 데이터를 가져옵니다."""
    query = """
    SELECT "time", "open", "high", "low", "close", "volume"
    FROM stock_price
    WHERE symbol = %(ticker)s AND "time" >= NOW() - INTERVAL '90 days'
    ORDER BY "time" DESC;
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params={'ticker': ticker})
        logging.info(f"[{ticker}] 주가 데이터 {len(df)}일치 조회 완료.")
        return df

def get_gdelt_events(ticker: str, days: int = 30) -> pd.DataFrame:
    """최근 GDELT 이벤트 데이터를 가져옵니다."""
    company_name_map = {"AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "NVDA": "Nvidia"}
    actor_name = company_name_map.get(ticker, ticker)

    query = """
    SELECT "event_date", "source_url", "avg_tone", "goldstein_scale"
    FROM gdelt_events
    WHERE (actor1_name ILIKE %(actor_name)s OR actor2_name ILIKE %(actor_name)s)
    AND event_date >= NOW() - INTERVAL '30 days'
    ORDER BY event_date DESC;
    """
    with get_db_connection() as conn:
        # actor_name에 와일드카드 추가
        df = pd.read_sql_query(query, conn, params={'actor_name': f'%{actor_name}%'})
        logging.info(f"[{ticker}] GDELT 이벤트 {len(df)}개 조회 완료.")
        return df

if __name__ == '__main__':
    # 테스트용 코드
    ticker_to_test = "NVDA"
    docs = get_combined_documents(ticker_to_test)
    print("\n--- Combined Documents ---")
    print(docs.head())

    fs = get_financial_statements(ticker_to_test)
    print("\n--- Financial Statements ---")
    print(fs.head())

    val = get_valuation_metrics(ticker_to_test)
    print("\n--- Valuation Metrics ---")
    print(val.head())
    
    prices = get_stock_prices(ticker_to_test)
    print("\n--- Stock Prices ---")
    print(prices.head())

    gdelt = get_gdelt_events(ticker_to_test)
    print("\n--- GDELT Events ---")
    print(gdelt.head())
