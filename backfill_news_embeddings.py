import os
import logging
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
from pgvector.psycopg2 import register_vector
import numpy as np

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 임베딩 모델 설정
EMBEDDING_MODEL = 'BAAI/bge-m3'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
logging.info(f"임베딩을 위해 사용하는 장치: {DEVICE}")
model = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

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
        logging.info("PostgreSQL 데이터베이스에 성공적으로 연결되었습니다.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"데이터베이스 연결에 실패했습니다: {e}")
        return None

def fetch_news_without_embeddings(conn):
    """embedding 컬럼이 NULL인 뉴스 데이터를 가져옵니다."""
    query = "SELECT id, title, description FROM stock_news WHERE embedding IS NULL;"
    try:
        df = pd.read_sql_query(query, conn)
        logging.info(f"임베딩이 필요한 {len(df)}개의 뉴스를 찾았습니다.")
        return df
    except psycopg2.Error as e:
        logging.error(f"데이터 조회 중 오류 발생: {e}")
        return pd.DataFrame()

def backfill_embeddings(conn, df_to_update):
    """가져온 데이터에 대해 임베딩을 생성하고 DB를 업데이트합니다."""
    if df_to_update.empty:
        logging.info("업데이트할 뉴스가 없습니다.")
        return

    # 텍스트 조합 및 임베딩 생성
    df_to_update['text_to_embed'] = df_to_update['title'].fillna('') + "\n\n" + df_to_update['description'].fillna('')
    logging.info("기존 뉴스 데이터 임베딩 생성을 시작합니다...")
    embeddings = model.encode(df_to_update["text_to_embed"].tolist(), show_progress_bar=True)
    df_to_update['embedding'] = list(embeddings)
    logging.info("임베딩 생성이 완료되었습니다.")

    # 데이터베이스 업데이트
    update_query = "UPDATE stock_news SET embedding = %s WHERE id = %s;"
    
    # 튜플 리스트로 변환 (embedding, id 순서)
    update_data = [(np.array(row['embedding']), row['id']) for index, row in df_to_update.iterrows()]

    with conn.cursor() as cursor:
        try:
            # executemany를 사용하여 여러 행을 한 번에 업데이트
            cursor.executemany(update_query, update_data)
            conn.commit()
            logging.info(f"{cursor.rowcount}개의 뉴스에 대한 임베딩을 성공적으로 업데이트했습니다.")
        except psycopg2.Error as e:
            logging.error(f"데이터 업데이트 중 오류 발생: {e}")
            conn.rollback()

def main():
    """메인 실행 함수"""
    load_dotenv()
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        # 1. 임베딩 없는 뉴스 데이터 가져오기
        df_news_to_backfill = fetch_news_without_embeddings(conn)
        
        # 2. 임베딩 생성 및 DB 업데이트
        backfill_embeddings(conn, df_news_to_backfill)
    finally:
        if conn:
            conn.close()
            logging.info("데이터베이스 연결을 종료합니다.")

if __name__ == "__main__":
    main()
