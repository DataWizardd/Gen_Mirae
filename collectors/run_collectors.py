#!/usr/bin/env python3
"""
📊 Mirae 데이터 수집기 통합 실행 스크립트
모든 데이터 소스에서 주기적으로 데이터를 수집합니다.
"""

import os
import sys
import time
import logging
import schedule
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/mirae/collectors.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataCollectorManager:
    def __init__(self):
        self.collectors = {
            'stock_price': {
                'script': 'stock_collector.py',
                'interval': 'realtime',  # 실시간
                'description': '주가 데이터 수집'
            },
            'stock_news': {
                'script': 'news_collector.py',
                'interval': 'hourly',
                'description': '뉴스 데이터 수집'
            },
            'reddit': {
                'script': 'reddit_collector.py',
                'interval': 'daily',
                'description': 'Reddit 투자 게시글 수집'
            },
            'valuation': {
                'script': 'valuation_collector.py',
                'interval': 'daily',
                'description': '밸류에이션 지표 수집'
            },
            'financial': {
                'script': 'financial_statements_collector.py',
                'interval': 'weekly',
                'description': '재무제표 데이터 수집'
            },
            'edgar': {
                'script': 'edgar_collector.py',
                'interval': 'weekly',
                'description': 'SEC 공시 문서 수집'
            },
            'gdelt': {
                'script': 'gdelt_collector.py',
                'interval': 'daily',
                'description': 'GDELT 이벤트 데이터 수집'
            }
        }
        
    def run_collector(self, name, config):
        """개별 수집기 실행"""
        script_path = config['script']
        if not os.path.exists(script_path):
            logger.warning(f"수집기 스크립트를 찾을 수 없습니다: {script_path}")
            return False
            
        try:
            logger.info(f"🚀 {config['description']} 시작...")
            start_time = time.time()
            
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=3600  # 1시간 타임아웃
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ {config['description']} 완료 ({duration:.1f}초)")
                return True
            else:
                logger.error(f"❌ {config['description']} 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {config['description']} 타임아웃")
            return False
        except Exception as e:
            logger.error(f"💥 {config['description']} 예외 발생: {e}")
            return False
    
    def run_realtime_collectors(self):
        """실시간 수집기 실행 (주가)"""
        logger.info("📈 실시간 데이터 수집 시작")
        for name, config in self.collectors.items():
            if config['interval'] == 'realtime':
                self.run_collector(name, config)
    
    def run_hourly_collectors(self):
        """시간별 수집기 실행"""
        logger.info("⏰ 시간별 데이터 수집 시작")
        for name, config in self.collectors.items():
            if config['interval'] == 'hourly':
                self.run_collector(name, config)
    
    def run_daily_collectors(self):
        """일별 수집기 실행"""
        logger.info("📅 일별 데이터 수집 시작")
        for name, config in self.collectors.items():
            if config['interval'] == 'daily':
                self.run_collector(name, config)
    
    def run_weekly_collectors(self):
        """주별 수집기 실행"""
        logger.info("📊 주별 데이터 수집 시작")
        for name, config in self.collectors.items():
            if config['interval'] == 'weekly':
                self.run_collector(name, config)
    
    def setup_schedule(self):
        """스케줄 설정"""
        logger.info("⚙️ 데이터 수집 스케줄 설정 중...")
        
        # 실시간 (주가): 5분마다 (시장 시간 중)
        schedule.every(5).minutes.do(self.run_realtime_collectors)
        
        # 시간별 (뉴스): 매시 정각
        schedule.every().hour.at(":00").do(self.run_hourly_collectors)
        
        # 일별 (Reddit, 밸류에이션, GDELT): 매일 오전 9시
        schedule.every().day.at("09:00").do(self.run_daily_collectors)
        
        # 주별 (재무제표, SEC): 매주 월요일 오전 10시
        schedule.every().monday.at("10:00").do(self.run_weekly_collectors)
        
        logger.info("✅ 스케줄 설정 완료")
        
        # 초기 데이터 수집 실행
        logger.info("🔄 초기 데이터 수집 실행...")
        self.run_daily_collectors()
        self.run_hourly_collectors()
    
    def run_forever(self):
        """무한 루프로 스케줄 실행"""
        logger.info("🚀 데이터 수집기 매니저 시작...")
        self.setup_schedule()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
                
        except KeyboardInterrupt:
            logger.info("⏹️ 사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"💥 예상치 못한 오류: {e}")
        finally:
            logger.info("🔚 데이터 수집기 매니저 종료")

def main():
    """메인 실행 함수"""
    # 로그 디렉토리 생성
    os.makedirs('/var/log/mirae', exist_ok=True)
    
    # 수집기 매니저 생성 및 실행
    manager = DataCollectorManager()
    
    # 명령행 인수 처리
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "once":
            logger.info("🔄 일회성 데이터 수집 실행")
            manager.run_daily_collectors()
            manager.run_hourly_collectors()
        elif command == "test":
            logger.info("🧪 테스트 모드 - 주가 데이터만 수집")
            manager.run_realtime_collectors()
        else:
            logger.error(f"❌ 알 수 없는 명령어: {command}")
            print("사용법: python3 run_collectors.py [once|test]")
            sys.exit(1)
    else:
        # 기본: 무한 루프 실행
        manager.run_forever()

if __name__ == "__main__":
    main()