-- 1. pgvector 확장 활성화 (이미 설치되어 있다면 생략 가능)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. SEC 공시 정보를 저장할 테이블 생성
CREATE TABLE IF NOT EXISTS sec_filings (
    id SERIAL PRIMARY KEY,
    -- BAAI/bge-m3 모델은 1024 차원 벡터를 생성합니다.
    embedding VECTOR(1024) NOT NULL,
    document TEXT NOT NULL,
    metadata JSONB,
    -- 예: '10-K', 'AAPL', '2023-10-27'
    -- metadata 필드에 들어갈 주요 내용:
    -- 'symbol': 'AAPL'
    -- 'form_type': '10-K'
    -- 'filing_date': '2023-10-27'
    -- 'source_url': 'https://www.sec.gov/...'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. 벡터 검색 성능 향상을 위한 인덱스 생성
-- 코사인 유사도(cosine_ops)를 사용하여 IVFFlat 인덱스를 생성합니다.
-- 데이터가 1백만 건 미만일 경우 lists = 1000, 1백만 건 이상일 경우 lists = N/1000 (N=총 데이터 수)
-- 로 권장됩니다.
CREATE INDEX IF NOT EXISTS idx_sec_filings_embedding
ON sec_filings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. 메타데이터 검색을 위한 인덱스 생성 (선택 사항이지만 권장)
-- 특정 종목이나 양식 유형으로 문서를 필터링하는 속도를 높입니다.
CREATE INDEX IF NOT EXISTS idx_sec_filings_metadata 
ON sec_filings USING gin (metadata); 