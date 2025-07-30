CREATE TABLE IF NOT EXISTS reddit_posts (
    id VARCHAR(20) PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    title TEXT,
    selftext TEXT,
    author VARCHAR(255),
    created_utc TIMESTAMP,
    score INTEGER,
    num_comments INTEGER,
    url TEXT,
    embedding VECTOR(1024),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HNSW 인덱스 생성 (유사도 검색 성능 향상)
-- lists는 데이터 크기에 따라 조정 (일반적으로 N/1000 ~ N/500, N은 총 데이터 수)
-- m은 16, ef_construction은 64로 시작하는 것이 일반적
CREATE INDEX IF NOT EXISTS reddit_posts_embedding_idx ON reddit_posts USING hnsw (embedding vector_l2_ops) WITH (m = 16, ef_construction = 64);
