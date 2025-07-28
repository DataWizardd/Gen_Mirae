import os
import time
import pandas as pd
import yfinance as yf
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# .env 파일 로드
load_dotenv(dotenv_path='.env')  

# 환경변수 불러오기
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT')
PG_NAME = os.getenv('PG_NAME')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=PG_NAME,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def fetch_and_store_realtime(symbol, conn):
    print(f"Fetching 1-minute data for {symbol}...")
    try:
        # yfinance에서 데이터 가져오기 (progress=False로 출력 억제)
        data = yf.download(symbol, period="2d", interval="1m", progress=False)
        
        if data.empty:
            print(f"❌ No data found for {symbol}")
            return
            
        print(f"📊 {symbol}: {len(data)} records fetched from yfinance")
        
        cursor = conn.cursor()
        successful_inserts = 0
        batch_data = []
        
        # 배치로 데이터 준비
        for ts, row in data.iterrows():
            if row.isnull().any():
                continue
            
            try:
                batch_data.append((
                    ts.to_pydatetime(),
                    symbol,
                    float(row['Open']),
                    float(row['High']),
                    float(row['Low']),
                    float(row['Close']),
                    int(row['Volume'])
                ))
            except (ValueError, TypeError) as e:
                print(f"⚠️ Data conversion error for {symbol} at {ts}: {e}")
                continue
        
        # 배치 삽입
        if batch_data:
            try:
                cursor.executemany("""
                    INSERT INTO stock_price (time, symbol, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (time, symbol) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume;
                """, batch_data)
                
                successful_inserts = len(batch_data)
                conn.commit()
                print(f"✅ {symbol}: {successful_inserts} records processed successfully")
                
            except Exception as e:
                print(f"❌ Batch insert error for {symbol}: {e}")
                conn.rollback()
        else:
            print(f"⚠️ {symbol}: No valid data to insert")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        try:
            conn.rollback()
        except:
            pass

if __name__ == '__main__':
    # PoC 용 종목 
    symbols = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOGL', 'AVGO', 'META', 'NFLX', 'TSLA']
    
    print("Starting real-time data collection loop (every 5 minutes)...")
    
    while True:
        conn = get_db_connection()
        if conn:
            print(f"\n--- New cycle started at {datetime.now()} ---")
            for symbol in symbols:
                fetch_and_store_realtime(symbol, conn)
            
            conn.close()
            print("--- Cycle finished, waiting for the next one ---")
        else:
            print("Could not connect to database, will retry in 1 minute...")

        time.sleep(300)