import os
import yfinance as yf
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta

# ✅ .env 파일 로드
load_dotenv(dotenv_path='.env')  

# ✅ 환경변수 불러오기
PG_HOST = os.getenv('PG_HOST')
PG_PORT = os.getenv('PG_PORT')
PG_NAME = os.getenv('PG_NAME')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')

# ✅ PostgreSQL 연결
conn = psycopg2.connect(
    dbname=PG_NAME,
    user=PG_USER,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT
)
cursor = conn.cursor()

def safe_item(val):
    if hasattr(val, 'item'):
        return val.item()
    return val

def fetch_and_store_daily(symbol, start_date, end_date):
    print(f"📥 Fetching daily data for {symbol} from {start_date} to {end_date}...")
    data = yf.download(symbol, start=start_date, end=end_date, interval='1d')

    for ts, row in data.iterrows():
        try:
            cursor.execute("""
                INSERT INTO stock_price (time, symbol, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (time, symbol) DO NOTHING;
            """, (
                ts.to_pydatetime(),
                symbol,
                float(safe_item(row['Open'])),
                float(safe_item(row['High'])),
                float(safe_item(row['Low'])),
                float(safe_item(row['Close'])),
                int(safe_item(row['Volume'])) if not (row['Volume'] is None or str(row['Volume']) == 'nan') else 0
            ))
        except Exception as e:
            print(f"❌ Error inserting {ts} - {e}")
            conn.rollback()
        else:
            conn.commit()

    print(f"✅ {symbol} done.\n")

if __name__ == '__main__':
    symbols = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOGL']
    start_date = '2025-01-01'
    end_date = '2025-07-26'  # 7월 25일까지 포함되도록 하루 뒤 날짜로 설정

    for symbol in symbols:
        fetch_and_store_daily(symbol, start_date, end_date)

    cursor.close()
    conn.close()
