#!/bin/bash

# 서버 배포 스크립트
# 로컬에서 서버로 파일 전송 및 설치 자동화

set -e

# 서버 정보 (사용자가 수정해야 함)
SERVER_IP="175.106.97.51"
SERVER_USER="root"
SERVER_PATH="/root/mirae-app"

echo "🚀 Mirae 애플리케이션 서버 배포를 시작합니다..."

# 1. 서버 정보 확인
if [ "$SERVER_IP" = "your-server-ip" ]; then
    echo "❌ SERVER_IP를 실제 서버 IP로 수정해주세요."
    exit 1
fi

echo "📋 서버 정보:"
echo "   IP: $SERVER_IP"
echo "   사용자: $SERVER_USER"
echo "   경로: $SERVER_PATH"

# 2. 서버 연결 테스트
echo "🔌 서버 연결 테스트 중..."
if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo '연결 성공'" 2>/dev/null; then
    echo "❌ 서버에 연결할 수 없습니다. IP와 SSH 키를 확인해주세요."
    exit 1
fi

# 3. 서버에 디렉토리 생성
echo "📁 서버 디렉토리 생성 중..."
ssh $SERVER_USER@$SERVER_IP "mkdir -p $SERVER_PATH"

# 4. 필요한 파일들 전송
echo "📤 파일 전송 중..."

# 설치 스크립트 전송
scp install_database.sh $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# SQL 파일 전송
scp create_reddit_posts_table.sql $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# Python 파일들 전송
scp *.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp requirements.txt $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# 프론트엔드 파일들 전송 (필요한 경우)
if [ -d "src" ]; then
    scp -r src $SERVER_USER@$SERVER_IP:$SERVER_PATH/
fi

if [ -d "public" ]; then
    scp -r public $SERVER_USER@$SERVER_IP:$SERVER_PATH/
fi

# 설정 파일들 전송
scp package.json $SERVER_USER@$SERVER_IP:$SERVER_PATH/ 2>/dev/null || echo "package.json 없음"
scp Procfile $SERVER_USER@$SERVER_IP:$SERVER_PATH/ 2>/dev/null || echo "Procfile 없음"

echo "✅ 파일 전송 완료!"

# 5. 서버에서 원격으로 스크립트 실행
echo "⚙️ 서버에서 설치 및 데이터 수집을 시작합니다..."
ssh $SERVER_USER@$SERVER_IP "
    set -e
    cd $SERVER_PATH

    echo '🗄️ 데이터베이스 설치 및 테이블 생성 중...'
    chmod +x install_database.sh
    ./install_database.sh

    # .env 파일 로드
    if [ -f .env ]; then
        export \$(grep -v '^#' .env | xargs)
    else
        echo '⚠️ .env 파일이 없습니다. DB 연결 정보를 수동으로 설정해야 합니다.'
    fi
    
    psql \"postgresql://\$PG_USER:\$PG_PASSWORD@\$PG_HOST:\$PG_PORT/\$PG_NAME\" -f create_reddit_posts_table.sql

    echo '🐍 Python 환경 설정 중...'
    python3 -m pip install --upgrade pip
    pip3 install -r requirements.txt

    echo '📰 Reddit 데이터 수집 중...'
    python3 reddit_collector.py

    echo '🎉 모든 작업 완료!'
"

echo ""
echo "📝 다음 단계:"
echo "1. 서버에서 .env 파일을 생성하거나 업데이트하세요:"
echo "   ssh $SERVER_USER@$SERVER_IP"
echo "   cd $SERVER_PATH"
echo "   nano .env"
echo ""
echo "2. .env 파일에 다음 내용이 포함되어 있는지 확인하세요:"
echo "   PG_HOST=localhost"
echo "   PG_PORT=5432"
echo "   PG_NAME=mirae_db"
echo "   PG_USER=mirae_user"
echo "   PG_PASSWORD=mirae_password"
echo "   REDDIT_CLIENT_ID=your_reddit_client_id"
echo "   REDDIT_CLIENT_SECRET=your_reddit_client_secret"
echo "   REDDIT_USER_AGENT=your_reddit_user_agent"
echo ""
echo "3. 연결 테스트를 실행하세요:"
echo "   python3 test_connection.py"
echo ""
echo "4. 애플리케이션을 실행하세요:"
echo "   python3 api.py"
echo ""
echo "✅ 배포가 완료되었습니다!"
