#!/bin/bash

# 🚀 Mirae 애플리케이션 개선된 서버 배포 스크립트
# 로컬에서 서버로 전체 파일 전송 및 설치 자동화

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 서버 정보 (사용자가 수정해야 함)
SERVER_IP="175.106.97.51"
SERVER_USER="root"
SERVER_PATH="/root/mirae-app"
BACKUP_PATH="/root/mirae-app-backup-$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}🚀 Mirae 애플리케이션 서버 배포를 시작합니다...${NC}"

# 1. 서버 정보 확인
if [ "$SERVER_IP" = "your-server-ip" ]; then
    echo -e "${RED}❌ SERVER_IP를 실제 서버 IP로 수정해주세요.${NC}"
    exit 1
fi

echo -e "${BLUE}📋 서버 정보:${NC}"
echo "   IP: $SERVER_IP"
echo "   사용자: $SERVER_USER"
echo "   경로: $SERVER_PATH"
echo "   백업 경로: $BACKUP_PATH"

# 2. 서버 연결 테스트
echo -e "${YELLOW}🔌 서버 연결 테스트 중...${NC}"
if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo '연결 성공'" 2>/dev/null; then
    echo -e "${RED}❌ 서버에 연결할 수 없습니다. IP와 SSH 키를 확인해주세요.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 서버 연결 성공${NC}"

# 3. 기존 애플리케이션 백업 (있는 경우)
echo -e "${YELLOW}💾 기존 애플리케이션 백업 중...${NC}"
ssh $SERVER_USER@$SERVER_IP "
    if [ -d '$SERVER_PATH' ]; then
        cp -r '$SERVER_PATH' '$BACKUP_PATH'
        echo '기존 애플리케이션을 $BACKUP_PATH로 백업했습니다.'
    else
        echo '새로운 설치입니다. 백업할 내용이 없습니다.'
    fi
"

# 4. 서버에 디렉토리 생성
echo -e "${YELLOW}📁 서버 디렉토리 생성 중...${NC}"
ssh $SERVER_USER@$SERVER_IP "
    mkdir -p $SERVER_PATH
    mkdir -p $SERVER_PATH/agent
    mkdir -p $SERVER_PATH/src
    mkdir -p $SERVER_PATH/public
    mkdir -p $SERVER_PATH/sql
    mkdir -p $SERVER_PATH/report
"

# 5. 로컬 파일들 압축
echo -e "${YELLOW}📦 로컬 파일들 압축 중...${NC}"
TEMP_TAR="/tmp/mirae-app-$(date +%Y%m%d_%H%M%S).tar.gz"

# 제외할 파일/디렉토리 목록
cat > /tmp/exclude_list.txt << EOF
.git/
node_modules/
__pycache__/
*.pyc
.env
.DS_Store
*.log
.pytest_cache/
build/
dist/
EOF

# 압축 생성
tar --exclude-from=/tmp/exclude_list.txt -czf $TEMP_TAR .
echo -e "${GREEN}✅ 압축 파일 생성 완료: $TEMP_TAR${NC}"

# 6. 압축 파일 전송
echo -e "${YELLOW}📤 압축 파일 전송 중...${NC}"
scp $TEMP_TAR $SERVER_USER@$SERVER_IP:/tmp/

# 7. 서버에서 압축 해제 및 설치
echo -e "${YELLOW}⚙️ 서버에서 압축 해제 및 설치를 시작합니다...${NC}"
ssh $SERVER_USER@$SERVER_IP "
    set -e
    cd $SERVER_PATH
    
    echo '📦 압축 파일 해제 중...'
    tar -xzf /tmp/$(basename $TEMP_TAR) -C .
    rm /tmp/$(basename $TEMP_TAR)
    
    echo '🐍 Python 환경 설정 중...'
    python3 -m pip install --upgrade pip
    pip3 install -r requirements.txt
    
    echo '📊 데이터베이스 설정 확인 중...'
    if [ ! -f .env ]; then
        echo '⚠️ .env 파일이 없습니다. 샘플 .env 파일을 생성합니다.'
        cat > .env << 'ENV_EOF'
# 데이터베이스 설정
PG_HOST=localhost
PG_PORT=5432
PG_NAME=mirae_db
PG_USER=mirae_user
PG_PASSWORD=mirae_password

# API 키들 (실제 값으로 수정 필요)
TAVILY_API_KEY=your_tavily_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent

# Clova API 설정
CLOVA_API_KEY=your_clova_api_key
CLOVA_API_KEY_PRIMARY_VAL=your_clova_primary_key
CLOVA_REQUEST_ID=your_clova_request_id
ENV_EOF
        echo '📝 .env 파일을 수정하여 실제 API 키와 DB 정보를 입력해주세요.'
    fi
    
    # 실행 권한 부여
    chmod +x install_database.sh
    find . -name '*.sh' -exec chmod +x {} \;
    
    echo '🧪 연결 테스트 실행 중...'
    if [ -f test_connection.py ]; then
        python3 test_connection.py || echo '⚠️ DB 연결 실패. .env 파일을 확인해주세요.'
    fi
    
    echo '🎉 배포 완료!'
"

# 8. 로컬 임시 파일 정리
rm $TEMP_TAR
rm /tmp/exclude_list.txt

echo ""
echo -e "${GREEN}🎉 배포가 완료되었습니다!${NC}"
echo ""
echo -e "${BLUE}📝 다음 단계:${NC}"
echo "1. 서버에 접속하여 .env 파일을 수정하세요:"
echo "   ssh $SERVER_USER@$SERVER_IP"
echo "   cd $SERVER_PATH"
echo "   nano .env"
echo ""
echo "2. 데이터베이스 설치 (필요한 경우):"
echo "   ./install_database.sh"
echo ""
echo "3. 애플리케이션 실행:"
echo "   # 백엔드 API 서버"
echo "   python3 api.py"
echo ""
echo "   # 또는 백그라운드 실행"
echo "   nohup python3 api.py > api.log 2>&1 &"
echo ""
echo "4. 프론트엔드 빌드 및 실행 (필요한 경우):"
echo "   npm install"
echo "   npm run build"
echo "   npm start"
echo ""
echo "5. Nginx 설정 (있는 경우):"
echo "   sudo cp mirae.nginx.conf /etc/nginx/sites-available/mirae"
echo "   sudo ln -s /etc/nginx/sites-available/mirae /etc/nginx/sites-enabled/"
echo "   sudo nginx -t && sudo systemctl reload nginx"
echo ""
echo -e "${YELLOW}💡 복원이 필요한 경우:${NC}"
echo "   cp -r $BACKUP_PATH/* $SERVER_PATH/"
echo ""
echo -e "${GREEN}✅ Happy coding! 🚀${NC}"