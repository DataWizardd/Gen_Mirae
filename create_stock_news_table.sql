-- 종목별 뉴스 데이터를 저장하기 위한 테이블
CREATE TABLE IF NOT EXISTS stock_news (
    id SERIAL PRIMARY KEY,                          -- 고유 식별자
    ticker VARCHAR(10) NOT NULL,                    -- 종목 티커 (e.g., AAPL)
    published_at TIMESTAMPTZ NOT NULL,              -- 기사 발행 시각 (타임존 포함)
    source_name VARCHAR(255),                       -- 뉴스 출처 (e.g., Reuters)
    title TEXT NOT NULL,                            -- 기사 제목
    description TEXT,                               -- 기사 요약
    content TEXT,                                   -- 기사 내용 일부
    url TEXT NOT NULL UNIQUE,                       -- 기사 원문 URL (중복 방지를 위해 UNIQUE 설정)
    embedding VECTOR(1024),                         -- BGE-M3 임베딩 벡터
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()   -- 데이터 적재 시각
);

-- 검색 성능 향상을 위해 ticker와 published_at 컬럼에 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_stock_news_ticker_published_at ON stock_news (ticker, published_at DESC);

-- HNSW 인덱스 생성 (유사도 검색 성능 향상)
CREATE INDEX IF NOT EXISTS stock_news_embedding_idx ON stock_news USING hnsw (embedding vector_l2_ops) WITH (m = 16, ef_construction = 64);
