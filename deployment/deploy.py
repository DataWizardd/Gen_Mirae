#!/usr/bin/env python3
"""
🚀 Mirae 애플리케이션 Python 배포 스크립트
더 세밀한 제어와 오류 처리를 위한 Python 버전
"""

import os
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
import argparse

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class ServerDeployment:
    def __init__(self, server_ip, server_user="root", server_path="/root/mirae-app"):
        self.server_ip = server_ip
        self.server_user = server_user
        self.server_path = server_path
        self.backup_path = f"/root/mirae-app-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def log(self, message, color=Colors.NC):
        print(f"{color}{message}{Colors.NC}")
        
    def run_command(self, command, check=True):
        """로컬 명령어 실행"""
        try:
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
            
    def ssh_command(self, command, check=True):
        """SSH를 통한 원격 명령어 실행"""
        ssh_cmd = f"ssh -o ConnectTimeout=10 {self.server_user}@{self.server_ip} '{command}'"
        return self.run_command(ssh_cmd, check)
        
    def scp_file(self, local_path, remote_path):
        """SCP를 통한 파일 전송"""
        scp_cmd = f"scp {local_path} {self.server_user}@{self.server_ip}:{remote_path}"
        return self.run_command(scp_cmd)
        
    def test_connection(self):
        """서버 연결 테스트"""
        self.log("🔌 서버 연결 테스트 중...", Colors.YELLOW)
        success, stdout, stderr = self.ssh_command("echo '연결 성공'", check=False)
        if success:
            self.log("✅ 서버 연결 성공", Colors.GREEN)
            return True
        else:
            self.log("❌ 서버에 연결할 수 없습니다. IP와 SSH 키를 확인해주세요.", Colors.RED)
            self.log(f"오류: {stderr}", Colors.RED)
            return False
            
    def create_backup(self):
        """기존 애플리케이션 백업"""
        self.log("💾 기존 애플리케이션 백업 중...", Colors.YELLOW)
        backup_cmd = f"""
        if [ -d '{self.server_path}' ]; then
            cp -r '{self.server_path}' '{self.backup_path}'
            echo '기존 애플리케이션을 {self.backup_path}로 백업했습니다.'
        else
            echo '새로운 설치입니다. 백업할 내용이 없습니다.'
        fi
        """
        success, stdout, stderr = self.ssh_command(backup_cmd)
        if success:
            self.log("✅ 백업 완료", Colors.GREEN)
        return success
        
    def create_directories(self):
        """서버 디렉토리 생성"""
        self.log("📁 서버 디렉토리 생성 중...", Colors.YELLOW)
        dirs_cmd = f"""
        mkdir -p {self.server_path}
        mkdir -p {self.server_path}/agent
        mkdir -p {self.server_path}/src
        mkdir -p {self.server_path}/public
        mkdir -p {self.server_path}/sql
        mkdir -p {self.server_path}/report
        mkdir -p {self.server_path}/notebook
        """
        success, stdout, stderr = self.ssh_command(dirs_cmd)
        if success:
            self.log("✅ 디렉토리 생성 완료", Colors.GREEN)
        return success
        
    def create_archive(self):
        """로컬 파일들 압축"""
        self.log("📦 로컬 파일들 압축 중...", Colors.YELLOW)
        
        # 제외할 파일/디렉토리 목록
        exclude_patterns = [
            '.git', '__pycache__', '*.pyc', '.DS_Store', '*.log',
            '.pytest_cache', 'build', 'dist', 'node_modules',
            '.env', '*.tar.gz'
        ]
        
        # 임시 압축 파일 생성
        temp_tar = tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False)
        temp_tar.close()
        
        try:
            with tarfile.open(temp_tar.name, 'w:gz') as tar:
                for item in Path('.').iterdir():
                    # 제외할 패턴 체크
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern.startswith('*'):
                            if item.name.endswith(pattern[1:]):
                                should_exclude = True
                                break
                        elif item.name == pattern:
                            should_exclude = True
                            break
                            
                    if not should_exclude:
                        self.log(f"  추가: {item.name}")
                        tar.add(item.name)
                        
            self.log(f"✅ 압축 파일 생성 완료: {temp_tar.name}", Colors.GREEN)
            return temp_tar.name
            
        except Exception as e:
            self.log(f"❌ 압축 생성 실패: {e}", Colors.RED)
            os.unlink(temp_tar.name)
            return None
            
    def upload_and_extract(self, archive_path):
        """압축 파일 업로드 및 해제"""
        self.log("📤 압축 파일 전송 중...", Colors.YELLOW)
        
        # 파일 업로드
        remote_temp = f"/tmp/{os.path.basename(archive_path)}"
        success, stdout, stderr = self.scp_file(archive_path, remote_temp)
        
        if not success:
            self.log(f"❌ 파일 전송 실패: {stderr}", Colors.RED)
            return False
            
        self.log("✅ 파일 전송 완료", Colors.GREEN)
        
        # 서버에서 압축 해제
        self.log("📦 서버에서 압축 해제 중...", Colors.YELLOW)
        extract_cmd = f"""
        cd {self.server_path}
        tar -xzf {remote_temp} -C .
        rm {remote_temp}
        """
        
        success, stdout, stderr = self.ssh_command(extract_cmd)
        if success:
            self.log("✅ 압축 해제 완료", Colors.GREEN)
        else:
            self.log(f"❌ 압축 해제 실패: {stderr}", Colors.RED)
            
        return success
        
    def setup_environment(self):
        """서버 환경 설정"""
        self.log("⚙️ 서버 환경 설정 중...", Colors.YELLOW)
        
        setup_cmd = f"""
        cd {self.server_path}
        
        echo '🐍 Python 환경 설정 중...'
        python3 -m pip install --upgrade pip
        pip3 install -r requirements.txt
        
        echo '📊 .env 파일 확인 중...'
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
        find . -name '*.sh' -exec chmod +x {{}} \;
        
        echo '🧪 연결 테스트 실행 중...'
        if [ -f test_connection.py ]; then
            python3 test_connection.py || echo '⚠️ DB 연결 실패. .env 파일을 확인해주세요.'
        fi
        """
        
        success, stdout, stderr = self.ssh_command(setup_cmd)
        if success:
            self.log("✅ 환경 설정 완료", Colors.GREEN)
            self.log(stdout)
        else:
            self.log(f"❌ 환경 설정 실패: {stderr}", Colors.RED)
            
        return success
        
    def deploy(self):
        """전체 배포 프로세스 실행"""
        self.log("🚀 Mirae 애플리케이션 서버 배포를 시작합니다...", Colors.GREEN)
        
        # 서버 정보 출력
        self.log("📋 서버 정보:", Colors.BLUE)
        print(f"   IP: {self.server_ip}")
        print(f"   사용자: {self.server_user}")
        print(f"   경로: {self.server_path}")
        print(f"   백업 경로: {self.backup_path}")
        
        # 단계별 실행
        if not self.test_connection():
            return False
            
        if not self.create_backup():
            return False
            
        if not self.create_directories():
            return False
            
        archive_path = self.create_archive()
        if not archive_path:
            return False
            
        try:
            if not self.upload_and_extract(archive_path):
                return False
                
            if not self.setup_environment():
                return False
                
            self.log("🎉 배포가 완료되었습니다!", Colors.GREEN)
            self.print_next_steps()
            return True
            
        finally:
            # 임시 파일 정리
            if archive_path and os.path.exists(archive_path):
                os.unlink(archive_path)
                
    def print_next_steps(self):
        """다음 단계 안내"""
        print()
        self.log("📝 다음 단계:", Colors.BLUE)
        print("1. 서버에 접속하여 .env 파일을 수정하세요:")
        print(f"   ssh {self.server_user}@{self.server_ip}")
        print(f"   cd {self.server_path}")
        print("   nano .env")
        print()
        print("2. 데이터베이스 설치 (필요한 경우):")
        print("   ./install_database.sh")
        print()
        print("3. 애플리케이션 실행:")
        print("   # 포그라운드 실행")
        print("   python3 api.py")
        print()
        print("   # 백그라운드 실행")
        print("   nohup python3 api.py > api.log 2>&1 &")
        print()
        print("4. 서비스 상태 확인:")
        print("   curl http://localhost:8000")
        print()
        self.log("💡 복원이 필요한 경우:", Colors.YELLOW)
        print(f"   cp -r {self.backup_path}/* {self.server_path}/")

def main():
    parser = argparse.ArgumentParser(description='Mirae 애플리케이션 서버 배포')
    parser.add_argument('--server-ip', default='175.106.97.51', help='서버 IP 주소')
    parser.add_argument('--server-user', default='root', help='서버 사용자명')
    parser.add_argument('--server-path', default='/root/mirae-app', help='서버 경로')
    
    args = parser.parse_args()
    
    if args.server_ip == 'your-server-ip':
        print(f"{Colors.RED}❌ --server-ip를 실제 서버 IP로 지정해주세요.{Colors.NC}")
        sys.exit(1)
    
    deployment = ServerDeployment(args.server_ip, args.server_user, args.server_path)
    success = deployment.deploy()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()