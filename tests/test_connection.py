#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
데이터베이스 연결 테스트 스크립트
PostgreSQL, pgvector, TimescaleDB 연결 및 기능 테스트
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

def test_connection():
    """데이터베이스 연결 테스트"""
    print("🔌 데이터베이스 연결 테스트 중...")
    
    try:
        # 환경변수 로드
        load_dotenv()
        
        # 연결 정보
        db_params = {
            "dbname": os.getenv("PG_NAME"),
            "user": os.getenv("PG_USER"),
            "password": os.getenv("PG_PASSWORD"),
            "host": os.getenv("PG_HOST"),
            "port": os.getenv("PG_PORT")
        }
        
        print(f"📋 연결 정보:")
        print(f"   호스트: {db_params['host']}")
        print(f"   포트: {db_params['port']}")
        print(f"   데이터베이스: {db_params['dbname']}")
        print(f"   사용자: {db_params['user']}")
        
        # 연결 시도
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✅ 데이터베이스 연결 성공!")
        
        # PostgreSQL 버전 확인
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"📋 PostgreSQL 버전: {version['version']}")
        
        # 확장 확인
        cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'timescaledb');")
        extensions = cur.fetchall()
        print("🔧 설치된 확장:")
        for ext in extensions:
            print(f"   - {ext['extname']}")
        
        # 테이블 확인
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        print("📊 테이블 목록:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # TimescaleDB 하이퍼테이블 확인
        cur.execute("""
            SELECT hypertable_name 
            FROM timescaledb_information.hypertables;
        """)
        hypertables = cur.fetchall()
        if hypertables:
            print("⏰ TimescaleDB 하이퍼테이블:")
            for ht in hypertables:
                print(f"   - {ht['hypertable_name']}")
        
        # 샘플 데이터 삽입 테스트
        print("\n🧪 샘플 데이터 삽입 테스트...")
        
        # stock_price 테이블 테스트
        cur.execute("""
            INSERT INTO stock_price (time, symbol, open, high, low, close, volume)
            VALUES (NOW(), 'TEST', 100.0, 105.0, 95.0, 102.0, 1000)
            ON CONFLICT (time, symbol) DO NOTHING;
        """)
        
        # company_reports 테이블 테스트 (벡터)
        cur.execute("""
            INSERT INTO company_reports (embedding, document, metadata, namespace)
            VALUES (
                '[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]'::vector,
                '테스트 문서입니다.',
                '{"source": "test", "type": "sample"}',
                'test_namespace'
            );
        """)
        
        # analyst_reports 테이블 테스트
        cur.execute("""
            INSERT INTO analyst_reports (symbol, report)
            VALUES (
                'TEST',
                '{"title": "테스트 리포트", "analyst": "테스트 애널리스트", "rating": "매수"}'
            );
        """)
        
        conn.commit()
        print("✅ 샘플 데이터 삽입 성공!")
        
        # 데이터 조회 테스트
        print("\n📖 데이터 조회 테스트...")
        
        # stock_price 조회
        cur.execute("SELECT COUNT(*) as count FROM stock_price WHERE symbol = 'TEST';")
        stock_count = cur.fetchone()
        print(f"   stock_price 레코드 수: {stock_count['count']}")
        
        # company_reports 조회
        cur.execute("SELECT COUNT(*) as count FROM company_reports WHERE namespace = 'test_namespace';")
        report_count = cur.fetchone()
        print(f"   company_reports 레코드 수: {report_count['count']}")
        
        # analyst_reports 조회
        cur.execute("SELECT COUNT(*) as count FROM analyst_reports WHERE symbol = 'TEST';")
        analyst_count = cur.fetchone()
        print(f"   analyst_reports 레코드 수: {analyst_count['count']}")
        
        # 벡터 검색 테스트
        print("\n🔍 벡터 검색 테스트...")
        cur.execute("""
            SELECT document, 
                   embedding <=> '[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]'::vector as distance
            FROM company_reports 
            WHERE namespace = 'test_namespace'
            ORDER BY embedding <=> '[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]'::vector
            LIMIT 1;
        """)
        vector_result = cur.fetchone()
        if vector_result:
            print(f"   벡터 검색 결과: {vector_result['document']} (거리: {vector_result['distance']})")
        
        # 테스트 데이터 정리
        print("\n🧹 테스트 데이터 정리...")
        cur.execute("DELETE FROM stock_price WHERE symbol = 'TEST';")
        cur.execute("DELETE FROM company_reports WHERE namespace = 'test_namespace';")
        cur.execute("DELETE FROM analyst_reports WHERE symbol = 'TEST';")
        conn.commit()
        print("✅ 테스트 데이터 정리 완료!")
        
        cur.close()
        conn.close()
        
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ PostgreSQL, pgvector, TimescaleDB가 정상적으로 작동합니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n🔧 문제 해결 방법:")
        print("1. .env 파일의 데이터베이스 설정을 확인하세요")
        print("2. 서버의 PostgreSQL이 실행 중인지 확인하세요")
        print("3. 방화벽 설정을 확인하세요")
        print("4. 데이터베이스 사용자 권한을 확인하세요")
        sys.exit(1)

if __name__ == "__main__":
    test_connection() 