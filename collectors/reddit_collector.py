import os
import praw
import pandas as pd
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from pgvector.psycopg2 import register_vector

# .env 파일에서 환경 변수 로드
load_dotenv()

# Reddit API 자격 증명 (환경 변수에서 가져오기)
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# 데이터베이스 연결 정보 (환경 변수에서 가져오기)
PG_HOST = os.getenv("PG_HOST")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_NAME = os.getenv("PG_NAME")
PG_PORT = os.getenv("PG_PORT")

# 임베딩 모델 설정
EMBEDDING_MODEL = 'BAAI/bge-m3'
# GPU 사용 가능 여부 확인 및 장치 설정
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"임베딩을 위해 사용하는 장치: {DEVICE}")
model = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

def get_reddit_data(tickers, limit_per_ticker):
    """지정된 티커 목록에 대한 Reddit 게시물을 수집하고 중복을 제거합니다."""
    if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT]):
        print("Reddit API 자격 증명이 환경 변수에 설정되지 않았습니다.")
        return pd.DataFrame()

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    rows = []
    subreddit = reddit.subreddit("investing")
    print(f"'{subreddit.display_name}' 서브레딧에서 데이터 수집을 시작합니다.")

    for ticker in tickers:
        print(f"'{ticker}'에 대한 게시물을 검색 중...")
        try:
            for post in subreddit.search(ticker, sort="new", limit=limit_per_ticker):
                text_to_embed = f"{post.title}\n\n{post.selftext}"
                rows.append({
                    "id": post.id,
                    "ticker": ticker,
                    "title": post.title,
                    "selftext": post.selftext,
                    "author": str(post.author),
                    "created_utc": datetime.fromtimestamp(post.created_utc),
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "text_to_embed": text_to_embed
                })
        except Exception as e:
            print(f"'{ticker}' 검색 중 오류 발생: {e}")
    
    print(f"총 {len(rows)}개의 게시물(중복 포함)을 수집했습니다.")
    df = pd.DataFrame(rows)
    
    if not df.empty:
        initial_count = len(df)
        df.drop_duplicates(subset=['id'], keep='first', inplace=True)
        final_count = len(df)
        if initial_count > final_count:
            print(f"중복 게시물 {initial_count - final_count}개를 제거했습니다. 최종 {final_count}개.")

    return df

def create_embeddings(df):
    """DataFrame의 텍스트 데이터에 대한 임베딩을 생성합니다."""
    if df.empty or "text_to_embed" not in df.columns:
        print("임베딩을 생성할 데이터가 없습니다.")
        return df

    print("임베딩 생성을 시작합니다...")
    embeddings = model.encode(df["text_to_embed"].tolist(), show_progress_bar=True)
    df['embedding'] = list(embeddings)
    print("임베딩 생성이 완료되었습니다.")
    return df

def insert_data_to_db(df):
    """수집 및 임베딩된 데이터를 데이터베이스에 삽입합니다."""
    if df.empty or 'embedding' not in df.columns:
        print("데이터베이스에 삽입할 데이터가 없습니다.")
        return

    conn = None
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_NAME,
            port=PG_PORT,
        )
        register_vector(conn)
        cursor = conn.cursor()
        print("데이터베이스에 연결되었습니다.")

        cols = ["id", "ticker", "title", "selftext", "author", "created_utc", "score", "num_comments", "url", "embedding"]
        df_to_insert = df[cols]

        insert_query = f"""
            INSERT INTO reddit_posts ({', '.join(cols)})
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                ticker = EXCLUDED.ticker,
                title = EXCLUDED.title,
                selftext = EXCLUDED.selftext,
                author = EXCLUDED.author,
                created_utc = EXCLUDED.created_utc,
                score = EXCLUDED.score,
                num_comments = EXCLUDED.num_comments,
                url = EXCLUDED.url,
                embedding = EXCLUDED.embedding;
        """
        
        data_tuples = [tuple(x) for x in df_to_insert.to_numpy()]

        execute_values(cursor, insert_query, data_tuples)
        conn.commit()
        print(f"{len(df)}개의 행이 'reddit_posts' 테이블에 성공적으로 삽입/업데이트되었습니다.")

    except psycopg2.Error as e:
        print(f"데이터베이스 오류: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("데이터베이스 연결이 종료되었습니다.")

if __name__ == "__main__":
    target_tickers = ["NVIDIA", "Apple", "Alphabet", "Amazon", "Microsoft"]
    limit_per_ticker = 50

    reddit_df = get_reddit_data(target_tickers, limit_per_ticker)
    
    if not reddit_df.empty:
        reddit_df = create_embeddings(reddit_df)

    if not reddit_df.empty:
        insert_data_to_db(reddit_df)
    else:
        print("수집된 데이터가 없어 데이터베이스 작업을 수행하지 않습니다.")
