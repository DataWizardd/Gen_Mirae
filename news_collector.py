import os
import logging
import pandas as pd
import psycopg2
from newsapi import NewsApiClient
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
        logging.info("PostgreSQL 데이터베이스에 성공적으로 연결되었습니다.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"데이터베이스 연결에 실패했습니다: {e}")
        return None

def fetch_news_from_api(tickers, api_key):
    """News API로부터 종목별 뉴스를 가져옵니다."""
    if not api_key:
        logging.error("NEWSAPI_API_KEY 환경변수가 설정되지 않았습니다.")
        return pd.DataFrame()

    newsapi = NewsApiClient(api_key=api_key)
    records = []
    
    logging.info(f"{tickers}에 대한 뉴스 수집을 시작합니다.")
    for ticker in tickers:
        try:
            articles = newsapi.get_everything(
                q=ticker,
                language='en',
                sort_by='publishedAt',
                page_size=50  # 한 번에 더 많은 기사를 가져옵니다.
            )["articles"]
            
            for art in articles:
                if art.get("description") and art.get("content"): # 설명과 내용이 있는 기사만 포함
                    records.append({
                        "ticker":      ticker,
                        "published_at": art["publishedAt"],
                        "source_name": art["source"]["name"],
                        "title":       art["title"],
                        "description": art.get("description"),
                        "content":     art.get("content"),
                        "url":         art["url"]
                    })
            logging.info(f"✅ {ticker}: {len(articles)}개의 기사를 찾았습니다.")
        except Exception as e:
            logging.error(f"❌ {ticker} 뉴스 수집 중 오류 발생: {e}")
            
    logging.info("뉴스 수집이 완료되었습니다.")
    return pd.DataFrame(records)

def insert_news_to_db(conn, df_news):
    """수집한 뉴스 데이터를 데이터베이스에 삽입합니다."""
    if df_news.empty:
        logging.info("삽입할 새로운 뉴스가 없습니다.")
        return

    # DataFrame을 튜플 리스트로 변환
    data_tuples = [tuple(x) for x in df_news.to_numpy()]
    
    # SQL 쿼리 (ON CONFLICT를 사용하여 URL 중복 시 삽입하지 않음)
    query = """
        INSERT INTO stock_news (ticker, published_at, source_name, title, description, content, url)
        VALUES %s
        ON CONFLICT (url) DO NOTHING;
    """
    
    with conn.cursor() as cursor:
        try:
            execute_values(cursor, query, data_tuples)
            conn.commit()
            logging.info(f"{cursor.rowcount}개의 새로운 뉴스를 데이터베이스에 성공적으로 삽입했습니다.")
        except psycopg2.Error as e:
            logging.error(f"데이터 삽입 중 오류 발생: {e}")
            conn.rollback()

def main():
    """메인 실행 함수"""
    load_dotenv()
    
    TICKERS = ["AAPL", "AMZN", "NVDA", "MSFT", "GOOGL"]
    NEWSAPI_KEY = os.getenv("NEWSAPI_API_KEY")
    
    # 1. 뉴스 데이터 가져오기
    df_news = fetch_news_from_api(TICKERS, NEWSAPI_KEY)
    
    if not df_news.empty:
        # 2. 데이터베이스 연결
        conn = get_db_connection()
        if conn:
            # 3. 데이터베이스에 삽입
            insert_news_to_db(conn, df_news)
            # 4. 연결 종료
            conn.close()
            logging.info("데이터베이스 연결을 종료합니다.")

if __name__ == "__main__":
    main() 