#!/bin/bash

# PostgreSQL, pgvector, TimescaleDB 설치 스크립트
# Ubuntu/Debian 기반 서버용

set -e

echo "🚀 PostgreSQL, pgvector, TimescaleDB 설치를 시작합니다..."

# 1. 시스템 업데이트
echo "📦 시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y

# 2. PostgreSQL 설치
echo "🐘 PostgreSQL 설치 중..."
sudo apt install -y postgresql postgresql-contrib

# 3. PostgreSQL 서비스 시작 및 활성화
echo "🔄 PostgreSQL 서비스 시작 중..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 4. PostgreSQL 버전 확인
echo "📋 PostgreSQL 버전 확인:"
psql --version

# 5. TimescaleDB 저장소 추가 및 설치
echo "⏰ TimescaleDB 설치 중..."
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update
sudo apt install -y timescaledb-postgresql-15

# 6. pgvector 설치
echo "🔢 pgvector 설치 중..."
sudo apt install -y postgresql-15-pgvector

# 7. PostgreSQL 설정 최적화
echo "⚙️ PostgreSQL 설정 최적화 중..."
sudo timescaledb-tune --quiet --yes

# 8. PostgreSQL 재시작
echo "🔄 PostgreSQL 재시작 중..."
sudo systemctl restart postgresql

# 9. 데이터베이스 및 사용자 생성
echo "👤 데이터베이스 사용자 및 데이터베이스 생성 중..."
sudo -u postgres psql << EOF
-- 사용자 생성 (비밀번호는 나중에 .env 파일에서 설정)
CREATE USER mirae_user WITH PASSWORD 'mirae_password';
CREATE DATABASE mirae_db OWNER mirae_user;
GRANT ALL PRIVILEGES ON DATABASE mirae_db TO mirae_user;

-- mirae_db에 연결
\c mirae_db

-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- TimescaleDB 확장 설치
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 사용자에게 확장 권한 부여
GRANT ALL ON SCHEMA public TO mirae_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mirae_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mirae_user;

-- 기본 테이블 생성
CREATE TABLE IF NOT EXISTS stock_price (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    PRIMARY KEY (time, symbol)
);

-- TimescaleDB 하이퍼테이블로 변환
SELECT create_hypertable('stock_price', 'time', if_not_exists => TRUE);

-- 벡터 저장용 테이블 생성
CREATE TABLE IF NOT EXISTS company_reports (
    id SERIAL PRIMARY KEY,
    embedding VECTOR(1024) NOT NULL,
    document TEXT NOT NULL,
    metadata JSONB,
    namespace TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 애널리스트 리포트 테이블 생성
CREATE TABLE IF NOT EXISTS analyst_reports (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    report JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_stock_price_symbol_time ON stock_price (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_company_reports_namespace ON company_reports (namespace);
CREATE INDEX IF NOT EXISTS idx_analyst_reports_symbol ON analyst_reports (symbol);

-- 사용자에게 테이블 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mirae_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mirae_user;
EOF

# 10. PostgreSQL 설정 파일 수정 (원격 접속 허용)
echo "🌐 원격 접속 설정 중..."
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/15/main/postgresql.conf
sudo sed -i "s/#port = 5432/port = 5432/" /etc/postgresql/15/main/postgresql.conf

# pg_hba.conf 파일에 원격 접속 허용 규칙 추가
echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a /etc/postgresql/15/main/pg_hba.conf

# 11. 방화벽 설정 (Ubuntu UFW 사용)
echo "🔥 방화벽 설정 중..."
sudo ufw allow 5432/tcp
sudo ufw reload

# 12. PostgreSQL 재시작
echo "🔄 PostgreSQL 재시작 중..."
sudo systemctl restart postgresql

# 13. 설치 확인
echo "✅ 설치 확인 중..."
sudo -u postgres psql -d mirae_db -c "SELECT version();"
sudo -u postgres psql -d mirae_db -c "SELECT * FROM pg_extension WHERE extname IN ('vector', 'timescaledb');"

echo ""
echo "🎉 설치가 완료되었습니다!"
echo ""
echo "📋 데이터베이스 정보:"
echo "   - 호스트: $(hostname -I | awk '{print $1}')"
echo "   - 포트: 5432"
echo "   - 데이터베이스: mirae_db"
echo "   - 사용자: mirae_user"
echo "   - 비밀번호: mirae_password"
echo ""
echo "🔧 다음 단계:"
echo "   1. .env 파일에서 PG_HOST를 서버 IP로 변경"
echo "   2. 애플리케이션 재시작"
echo ""
echo "📝 연결 테스트:"
echo "   psql -h $(hostname -I | awk '{print $1}') -p 5432 -U mirae_user -d mirae_db" 