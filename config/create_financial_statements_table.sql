-- 종목별 연간/분기 재무제표 데이터를 저장하는 테이블
CREATE TABLE IF NOT EXISTS financial_statements (
    id SERIAL,
    ticker VARCHAR(10) NOT NULL,
    statement_type VARCHAR(50) NOT NULL,  -- e.g., 'annual_income_statement', 'quarterly_balance_sheet'
    period DATE NOT NULL,                 -- 재무제표 기준일 (타입 변경: TIMESTAMPTZ -> DATE)
    data JSONB NOT NULL,                  -- 재무제표 상세 데이터 (JSONB 타입)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (ticker, statement_type, period) -- 중복 데이터 방지 및 기본키 설정
);

-- financial_statements 테이블을 TimescaleDB 하이퍼테이블로 전환합니다.
-- (period 컬럼을 기준으로 자동 파티셔닝)
SELECT create_hypertable('financial_statements', 'period', if_not_exists => TRUE);

-- 검색 성능 향상을 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_fs_ticker_type_period 
ON financial_statements (ticker, statement_type, period DESC); 