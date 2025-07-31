# 🗄️ 데이터베이스 설치 가이드

## 📋 개요
이 가이드는 서버에 PostgreSQL, pgvector, TimescaleDB를 설치하고 Mirae 투자 포트폴리오 애플리케이션과 연동하는 방법을 설명합니다.

## 🎯 설치할 구성요소
- **PostgreSQL 15**: 메인 데이터베이스
- **pgvector**: 벡터 임베딩 저장 및 검색
- **TimescaleDB**: 시계열 데이터 최적화

## 🚀 설치 방법

### 1. 서버에 접속
```bash
ssh root@your-server-ip
```

### 2. 설치 스크립트 실행
```bash
# 스크립트 다운로드 (로컬에서)
scp install_database.sh root@your-server-ip:/root/

# 서버에서 실행
chmod +x install_database.sh
./install_database.sh
```

### 3. 수동 설치 (스크립트가 실패할 경우)

#### 3.1 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

#### 3.2 PostgreSQL 설치
```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 3.3 TimescaleDB 설치
```bash
# 저장소 추가
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update

# 설치
sudo apt install -y timescaledb-postgresql-15
```

#### 3.4 pgvector 설치
```bash
sudo apt install -y postgresql-15-pgvector
```

#### 3.5 설정 최적화
```bash
sudo timescaledb-tune --quiet --yes
sudo systemctl restart postgresql
```

## 🗃️ 데이터베이스 설정

### 1. 데이터베이스 및 사용자 생성
```bash
sudo -u postgres psql
```

PostgreSQL 프롬프트에서:
```sql
-- 사용자 생성
CREATE USER mirae_user WITH PASSWORD 'mirae_password';

-- 데이터베이스 생성
CREATE DATABASE mirae_db OWNER mirae_user;
GRANT ALL PRIVILEGES ON DATABASE mirae_db TO mirae_user;

-- mirae_db에 연결
\c mirae_db

-- 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 권한 부여
GRANT ALL ON SCHEMA public TO mirae_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mirae_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mirae_user;

-- 테이블 생성
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

-- 벡터 테이블 생성
CREATE TABLE IF NOT EXISTS company_reports (
    id SERIAL PRIMARY KEY,
    embedding VECTOR(1024) NOT NULL,
    document TEXT NOT NULL,
    metadata JSONB,
    namespace TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 애널리스트 리포트 테이블
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

-- 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mirae_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mirae_user;

\q
```

### 2. 원격 접속 설정
```bash
# postgresql.conf 수정
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/15/main/postgresql.conf
sudo sed -i "s/#port = 5432/port = 5432/" /etc/postgresql/15/main/postgresql.conf

# pg_hba.conf에 원격 접속 허용 규칙 추가
echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a /etc/postgresql/15/main/pg_hba.conf

# 방화벽 설정
sudo ufw allow 5432/tcp
sudo ufw reload

# PostgreSQL 재시작
sudo systemctl restart postgresql
```

## 🔧 애플리케이션 설정

### 1. .env 파일 수정
로컬 프로젝트의 `.env` 파일을 다음과 같이 수정:

```env
# 기존 설정을 서버 정보로 변경
PG_HOST=your-server-ip
PG_PORT=5432
PG_NAME=mirae_db
PG_USER=mirae_user
PG_PASSWORD=mirae_password
```

### 2. 연결 테스트
```bash
# 로컬에서 서버 DB 연결 테스트
psql -h your-server-ip -p 5432 -U mirae_user -d mirae_db
```

## 📊 데이터베이스 구조

### stock_price 테이블
- **용도**: 주식 가격 시계열 데이터
- **특징**: TimescaleDB 하이퍼테이블로 최적화
- **컬럼**: time, symbol, open, high, low, close, volume

### company_reports 테이블
- **용도**: 회사 리포트 문서의 벡터 임베딩 저장
- **특징**: pgvector를 사용한 벡터 검색
- **컬럼**: id, embedding(VECTOR), document, metadata, namespace, created_at

### analyst_reports 테이블
- **용도**: 애널리스트 리포트 저장
- **특징**: JSONB 형태로 유연한 데이터 저장
- **컬럼**: id, symbol, report(JSONB), created_at

## 🔍 문제 해결

### 1. 연결 오류
```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 로그 확인
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 2. 권한 오류
```bash
# 사용자 권한 재설정
sudo -u postgres psql -d mirae_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mirae_user;"
```

### 3. 확장 설치 오류
```bash
# 확장 재설치
sudo -u postgres psql -d mirae_db -c "DROP EXTENSION IF EXISTS vector; CREATE EXTENSION vector;"
sudo -u postgres psql -d mirae_db -c "DROP EXTENSION IF EXISTS timescaledb; CREATE EXTENSION timescaledb;"
```

## 📈 성능 최적화

### 1. PostgreSQL 설정 최적화
```bash
# 메모리 설정 (서버 RAM의 25% 권장)
sudo sed -i "s/#shared_buffers = 128MB/shared_buffers = 1GB/" /etc/postgresql/15/main/postgresql.conf
sudo sed -i "s/#effective_cache_size = 4GB/effective_cache_size = 4GB/" /etc/postgresql/15/main/postgresql.conf
```

### 2. 인덱스 최적화
```sql
-- 벡터 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_company_reports_embedding 
ON company_reports USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

## 🔒 보안 고려사항

1. **강력한 비밀번호 사용**
2. **방화벽에서 특정 IP만 허용**
3. **SSL 연결 사용 권장**
4. **정기적인 백업 설정**

## 📞 지원

설치 과정에서 문제가 발생하면:
1. 로그 파일 확인
2. PostgreSQL 공식 문서 참조
3. TimescaleDB 커뮤니티 포럼 활용 