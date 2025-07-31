-- GDELT 이벤트 데이터를 저장하기 위한 시계열 테이블
CREATE TABLE IF NOT EXISTS gdelt_events (
    global_event_id BIGINT PRIMARY KEY,              -- GDELT의 고유 이벤트 ID
    event_date TIMESTAMPTZ NOT NULL,                  -- 이벤트 발생 시각 (파티션 키)
    date_added TIMESTAMPTZ,                            -- GDELT에 추가된 시각
    source_url TEXT,                                   -- 원문 기사 URL

    -- 행위자 정보
    actor1_name TEXT,
    actor2_name TEXT,
    actor1_country_code VARCHAR(3),
    actor2_country_code VARCHAR(3),
    actor1_type1_code VARCHAR(3),
    actor2_type1_code VARCHAR(3),

    -- 이벤트 정보
    event_code VARCHAR(4),
    event_base_code VARCHAR(4),
    event_root_code VARCHAR(2),
    quad_class SMALLINT,
    goldstein_scale REAL,
    avg_tone REAL,

    -- 위치 정보
    action_geo_country_code VARCHAR(2),
    action_geo_lat REAL,
    action_geo_long REAL
);

-- gdelt_events 테이블을 TimescaleDB 하이퍼테이블로 전환합니다.
SELECT create_hypertable('gdelt_events', 'event_date', if_not_exists => TRUE);

-- 검색 성능 향상을 위한 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_gdelt_actor1_name ON gdelt_events (actor1_name);
CREATE INDEX IF NOT EXISTS idx_gdelt_actor2_name ON gdelt_events (actor2_name);
CREATE INDEX IF NOT EXISTS idx_gdelt_event_codes ON gdelt_events (event_code, event_base_code, event_root_code); 