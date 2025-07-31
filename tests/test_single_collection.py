#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import yfinance as yf
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

def get_db_connection():
    try:
        load_dotenv()
        conn = psycopg2.connect(
            dbname=os.getenv('PG_NAME'),
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT')
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_single_symbol(symbol='AAPL'):
    """단일 종목에 대해 실시간 데이터 수집 테스트"""
    print(f"🧪 {symbol} 단일 종목 테스트 시작...")
    
    # 1. yfinance API 테스트
    print(f"📡 {symbol} 데이터 요청 중...")
    try:
        data = yf.download(symbol, period="1d", interval="1m", progress=False)
        if data.empty:
            print(f"❌ {symbol}: yfinance에서 데이터를 가져올 수 없음")
            return False
        
        print(f"✅ {symbol}: {len(data)}개 레코드 수신")
        print(f"📊 데이터 범위: {data.index[0]} ~ {data.index[-1]}")
        print(f"💰 최신 가격: ${data['Close'].iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"❌ yfinance API 오류: {e}")
        return False
    
    # 2. 데이터베이스 연결 테스트
    conn = get_db_connection()
    if not conn:
        return False
    
    # 3. 기존 데이터 확인
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stock_price WHERE symbol = %s", (symbol,))
        before_count = cur.fetchone()[0]
        print(f"📋 기존 {symbol} 레코드 수: {before_count}")
        
        # 4. 새 데이터 삽입 테스트
        print(f"💾 {symbol} 데이터 삽입 중...")
        batch_data = []
        
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
                print(f"⚠️ 데이터 변환 오류 at {ts}: {e}")
                continue
        
        if batch_data:
            cur.executemany("""
                INSERT INTO stock_price (time, symbol, open, high, low, close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (time, symbol) DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    volume = EXCLUDED.volume;
            """, batch_data)
            
            conn.commit()
            
            # 5. 결과 확인
            cur.execute("SELECT COUNT(*) FROM stock_price WHERE symbol = %s", (symbol,))
            after_count = cur.fetchone()[0]
            new_records = after_count - before_count
            
            print(f"✅ 처리 완료: {len(batch_data)}개 레코드 처리")
            print(f"📈 현재 총 {symbol} 레코드 수: {after_count} (+{new_records})")
            
            # 최신 3개 레코드 표시
            cur.execute("""
                SELECT time, close, volume 
                FROM stock_price 
                WHERE symbol = %s 
                ORDER BY time DESC 
                LIMIT 3
            """, (symbol,))
            
            recent_records = cur.fetchall()
            print(f"🕐 최신 3개 레코드:")
            for i, (time, close, volume) in enumerate(recent_records, 1):
                print(f"   {i}. {time}: ${close:.2f} (거래량: {volume:,})")
            
        else:
            print(f"⚠️ 삽입할 유효한 데이터가 없음")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 작업 오류: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    print("🔬 단일 종목 실시간 데이터 수집 테스트\n")
    
    # 테스트할 종목들
    test_symbols = ['AAPL', 'NVDA', 'META', 'AVGO']
    
    for symbol in test_symbols:
        print(f"\n{'='*50}")
        success = test_single_symbol(symbol)
        if success:
            print(f"✅ {symbol} 테스트 성공!")
        else:
            print(f"❌ {symbol} 테스트 실패!")
        print('='*50)
        
        # 다음 종목 테스트 전 잠시 대기
        if symbol != test_symbols[-1]:
            print("⏳ 다음 종목 테스트를 위해 2초 대기...")
            time.sleep(2)
    
    print(f"\n🏁 모든 테스트 완료!")
    print(f"\n💡 다음 단계:")
    print(f"1. 모든 테스트가 성공했다면 stock_collector_realtime.py를 실행하세요")
    print(f"2. 실패한 테스트가 있다면 debug_stock_data.py를 실행하여 문제를 진단하세요") 