-- 종목별 벨류에이션 지표를 시계열로 저장하는 테이블
CREATE TABLE IF NOT EXISTS stock_valuation (
    ticker VARCHAR(10) NOT NULL,                       -- 종목 티커
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),     -- 데이터 수집 시각 (Time-series 키)
    trailing_pe FLOAT,                                 -- Trailing P/E
    forward_pe FLOAT,                                  -- Forward P/E
    price_to_book FLOAT,                               -- PBR
    price_to_sales FLOAT,                              -- PSR
    enterprise_to_revenue FLOAT,                       -- EV/Revenue
    enterprise_to_ebitda FLOAT,                        -- EV/EBITDA
    market_cap BIGINT,                                 -- 시가총액
    enterprise_value BIGINT,                           -- 기업가치(EV)
    total_revenue BIGINT,                              -- 총매출
    net_income_to_common BIGINT,                       -- 순이익
    PRIMARY KEY (ticker, updated_at)                   -- Ticker와 시간을 복합 기본 키로 설정
);

-- stock_valuation 테이블을 TimescaleDB 하이퍼테이블로 전환합니다.
-- (updated_at 컬럼을 기준으로 자동 파티셔닝)
SELECT create_hypertable('stock_valuation', 'updated_at', if_not_exists => TRUE); 