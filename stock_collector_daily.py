#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
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

# PostgreSQL 연결
try:
    conn = psycopg2.connect(
        dbname=PG_NAME,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )
    cursor = conn.cursor()
except Exception as e:
    print(f"Database connection failed: {e}")
    exit()

def fetch_and_store_daily(symbol, start_date, end_date):
    print(f"Fetching daily data for {symbol} from {start_date} to {end_date}...")
    try:
        data = yf.download(symbol, start=start_date, end=end_date, interval='1d')
        
        if data.empty:
            print(f"No data found for {symbol}")
            return
            
        inserted_count = 0
        for ts, row in data.iterrows():
            try:
                # 행 전체에 NaN 값이 있는지 확인하고, 있으면 해당 행을 건너뜁니다.
                if row.isnull().any():
                    # print(f"NaN value found for {symbol} at {ts}, skipping row.")
                    continue

                # 모든 값이 유효할 때만 데이터베이스에 삽입합니다.
                open_val = float(row['Open'])
                high_val = float(row['High'])
                low_val = float(row['Low'])
                close_val = float(row['Close'])
                volume_val = int(row['Volume'])
                
                cursor.execute("""
                    INSERT INTO stock_price (time, symbol, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (time, symbol) DO NOTHING;
                """, (
                    ts.to_pydatetime(),
                    symbol,
                    open_val,
                    high_val,
                    low_val,
                    close_val,
                    volume_val
                ))
                inserted_count += 1
            except Exception as e:
                print(f"Error inserting {ts} for {symbol} - {e}")
                # 문제가 발생한 데이터 행을 출력합니다.
                print(f"Problematic row data:\n{row}")
                conn.rollback()
            else:
                conn.commit()
        
        print(f"{symbol}: {inserted_count} records inserted")
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        conn.rollback()

if __name__ == '__main__':
    # 5개 종목
    symbols = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOGL']
    
    # 기간 설정: 2020년 1월 1일 ~ 2025년 7월 27일
    start_date = '2020-01-01'
    end_date = '2025-07-27'
    
    print(f"Starting data collection for {len(symbols)} symbols from {start_date} to {end_date}")
    
    for symbol in symbols:
        fetch_and_store_daily(symbol, start_date, end_date)
        print(f"{symbol} completed")

    cursor.close()
    conn.close()
    print("All data collection completed!")