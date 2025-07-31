# 🚀 Mirae 애플리케이션 배포 가이드

이 가이드는 로컬에서 서버로 Mirae 애플리케이션을 배포하는 방법을 설명합니다.

## 📋 준비사항

### 1. 서버 준비
- Ubuntu 20.04+ 또는 CentOS 7+ 서버
- SSH 접근 권한 (키 기반 인증 권장)
- Python 3.8+ 설치
- PostgreSQL 15+ 설치 (선택사항 - 스크립트로 자동 설치 가능)

### 2. 로컬 준비
- SSH 클라이언트 (Windows의 경우 Git Bash 권장)
- Python 3.8+ (배포 스크립트 실행용)

## 🔧 배포 방법

### 방법 1: 개선된 Bash 스크립트 (권장)

1. **스크립트 실행 권한 부여**
```bash
chmod +x deploy_improved.sh
```

2. **서버 IP 수정**
```bash
nano deploy_improved.sh
# SERVER_IP="your-server-ip" 를 실제 IP로 변경
```

3. **배포 실행**
```bash
./deploy_improved.sh
```

### 방법 2: Python 배포 스크립트

1. **Python 스크립트 실행**
```bash
python3 deploy.py --server-ip 175.106.97.51 --server-user root
```

2. **다른 옵션들**
```bash
# 사용자 지정 경로
python3 deploy.py --server-ip 175.106.97.51 --server-path /home/ubuntu/mirae

# 도움말 확인
python3 deploy.py --help
```

## ⚙️ 서버 설정

### 1. 환경 변수 설정

배포 후 서버에 접속하여 `.env` 파일을 수정합니다:

```bash
ssh root@your-server-ip
cd /root/mirae-app
nano .env
```

`.env` 파일 내용:
```env
# 데이터베이스 설정
PG_HOST=localhost
PG_PORT=5432
PG_NAME=mirae_db
PG_USER=mirae_user
PG_PASSWORD=your_secure_password

# API 키들
TAVILY_API_KEY=your_tavily_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=Mirae:1.0 (by /u/yourusername)

# Clova API 설정
CLOVA_API_KEY=your_clova_api_key
CLOVA_API_KEY_PRIMARY_VAL=your_clova_primary_key
CLOVA_REQUEST_ID=your_clova_request_id
```

### 2. 데이터베이스 설치 (필요한 경우)

```bash
# 자동 설치 스크립트 실행
./install_database.sh

# 또는 수동 설치
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

### 3. 연결 테스트

```bash
python3 test_connection.py
```

## 🎯 서비스 실행 방법

### 방법 1: 직접 실행 (개발/테스트용)

```bash
# API 서버 실행
python3 api.py

# 백그라운드 실행
nohup python3 api.py > api.log 2>&1 &

# 데이터 수집기 실행
python3 run_collectors.py
```

### 방법 2: Systemd 서비스 (권장)

1. **서비스 파일 복사**
```bash
sudo cp mirae-api.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. **서비스 시작 및 자동 시작 설정**
```bash
sudo systemctl start mirae-api
sudo systemctl enable mirae-api
```

3. **서비스 상태 확인**
```bash
sudo systemctl status mirae-api
sudo journalctl -u mirae-api -f  # 로그 실시간 보기
```

### 방법 3: PM2 (Node.js 환경)

1. **PM2 설치**
```bash
npm install -g pm2
```

2. **로그 디렉토리 생성**
```bash
sudo mkdir -p /var/log/mirae
sudo chown $USER:$USER /var/log/mirae
```

3. **PM2로 애플리케이션 시작**
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

4. **PM2 상태 확인**
```bash
pm2 status
pm2 logs mirae-api
```

## 🔄 지속적 배포 (CI/CD) 설정

### GitHub Actions 예제

`.github/workflows/deploy.yml` 파일 생성:

```yaml
name: Deploy to Server

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup SSH
      uses: webfactory/ssh-agent@v0.7.0
      with:
        ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
    
    - name: Deploy to server
      run: |
        python3 deploy.py --server-ip ${{ secrets.SERVER_IP }}
```

## 🌐 Nginx 설정 (선택사항)

### 1. Nginx 설치
```bash
sudo apt install -y nginx
```

### 2. 설정 파일 복사
```bash
sudo cp mirae.nginx.conf /etc/nginx/sites-available/mirae
sudo ln -s /etc/nginx/sites-available/mirae /etc/nginx/sites-enabled/
```

### 3. Nginx 재시작
```bash
sudo nginx -t  # 설정 테스트
sudo systemctl reload nginx
```

## 🔍 문제 해결

### 1. 배포 실패 시

```bash
# 로그 확인
tail -f /var/log/mirae/*.log

# 서비스 상태 확인
sudo systemctl status mirae-api

# 포트 사용 확인
sudo netstat -tlnp | grep :8000
```

### 2. 데이터베이스 연결 오류

```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 연결 테스트
psql -h localhost -U mirae_user -d mirae_db
```

### 3. 메모리/CPU 사용량 확인

```bash
# 시스템 리소스 모니터링
htop
free -h
df -h

# PM2 모니터링 (PM2 사용 시)
pm2 monit
```

## 📊 모니터링 및 로그

### 로그 위치
- API 서버: `/var/log/mirae/api-combined.log`
- 데이터 수집: `/var/log/mirae/collectors.log`
- Nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`

### 성능 모니터링
```bash
# API 응답 시간 테스트
curl -w "%{time_total}" http://localhost:8000/

# 데이터베이스 성능
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## 🔄 업데이트 및 롤백

### 업데이트
```bash
# 새 코드 배포
./deploy_improved.sh

# 서비스 재시작
sudo systemctl restart mirae-api
```

### 롤백 (필요시)
```bash
# 백업에서 복원
cp -r /root/mirae-app-backup-YYYYMMDD_HHMMSS/* /root/mirae-app/
sudo systemctl restart mirae-api
```

## 🚨 백업 전략

### 1. 자동 백업 스크립트
```bash
#!/bin/bash
# daily_backup.sh
BACKUP_DIR="/backup/mirae-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 애플리케이션 백업
cp -r /root/mirae-app $BACKUP_DIR/

# 데이터베이스 백업
sudo -u postgres pg_dump mirae_db > $BACKUP_DIR/mirae_db.sql

# 7일 이전 백업 삭제
find /backup -name "mirae-*" -mtime +7 -exec rm -rf {} \;
```

### 2. Crontab 설정
```bash
crontab -e
# 매일 새벽 2시 백업
0 2 * * * /root/daily_backup.sh
```

---

## 🎉 완료!

이제 Mirae 애플리케이션이 서버에서 실행됩니다.

- **API 접근**: `http://your-server-ip:8000`
- **헬스체크**: `http://your-server-ip:8000/`
- **리포트 생성**: `http://your-server-ip:8000/generate_report`

문제가 발생하면 로그를 확인하고, 필요시 백업에서 롤백하세요! 🚀