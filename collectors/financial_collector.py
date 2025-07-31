#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yfinance as yf
import psycopg2
from dotenv import load_dotenv
from datetime import date
import numpy as np # NumPy import 추가

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

def convert_to_native_type(value):
    """NumPy 타입을 Python 기본 타입으로 변환"""
    if isinstance(value, (np.integer, np.int64)):
        return int(value)
    if isinstance(value, (np.floating, np.float64)):
        return float(value)
    if value is None or np.isnan(value):
        return None
    return value

def get_and_store_metrics(symbol, conn):
    print(f"Fetching financial metrics for {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # yfinance에서 데이터 가져오기 및 타입 변환
        pe_ratio = convert_to_native_type(info.get('trailingPE'))
        pb_ratio = convert_to_native_type(info.get('priceToBook'))
        market_cap = convert_to_native_type(info.get('marketCap'))

        # 최신 재무 데이터 가져오기 (연간)
        financials = ticker.financials
        total_revenue = None
        net_income = None
        if not financials.empty:
            latest_financials = financials.iloc[:, 0]
            total_revenue = convert_to_native_type(latest_financials.get('Total Revenue'))
            net_income = convert_to_native_type(latest_financials.get('Net Income'))

        # 데이터베이스에 삽입 또는 업데이트
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO financial_metrics (date, symbol, pe_ratio, pb_ratio, total_revenue, net_income, market_cap)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date, symbol) DO UPDATE SET
                pe_ratio = EXCLUDED.pe_ratio,
                pb_ratio = EXCLUDED.pb_ratio,
                total_revenue = EXCLUDED.total_revenue,
                net_income = EXCLUDED.net_income,
                market_cap = EXCLUDED.market_cap;
        """, (
            date.today(),
            symbol,
            pe_ratio,
            pb_ratio,
            total_revenue,
            net_income,
            market_cap
        ))
        conn.commit()
        cursor.close()
        print(f"Successfully stored metrics for {symbol}")

    except Exception as e:
        print(f"Failed to process {symbol}: {e}")
        conn.rollback()

if __name__ == '__main__':
    symbols = ['AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOGL']
    
    print(f"Starting financial metrics collection for {date.today()}...")
    
    conn = get_db_connection()
    if conn:
        for symbol in symbols:
            get_and_store_metrics(symbol, conn)
        conn.close()
        print("Financial metrics collection completed!")
    else:
        print("Could not connect to the database. Aborting.")