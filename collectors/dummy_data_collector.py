#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import psycopg2.extras # Json 사용을 위해 import

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

if __name__ == '__main__':
    # 5) 삽입할 문서 리스트 (document_dummy.py 참고)
    docs = [
        {
            "namespace": "AMZN",
            "content": """
제목: 20241204_아마존 (AMZN US_매수)
- 자체 파운데이션 모델 및 반도체, 슈퍼컴 공개
- 인프라 최적화 통한 가성비 강조
- 오픈AI, 엔비디아와 경쟁 중
- 생성 AI 비용 하락으로 전체 시장 확대 기대
""".strip()
        },
        {
            "namespace": "MSFT",
            "content": """
제목: 20250718_마이크로소프트 (MSFT US_매수_신규)
- FY27 EPS 기준 목표주가 $663, 매수 의견
- AI 에이전트 도입 → 수익화 잠재력 높음
- M365, Copilot 등 AI 기능 통합으로 실적 가속화
""".strip()
        },
        {
            "namespace": "NVDA",
            "content": """
제목: 20250530_엔비디아 (NVDA US_매수)
- 목표주가 $174 상향
- Blackwell 제품 본격 출하
- H20 관련 손실에도 FY26 GPM 16.6% 전망
""".strip()
        },
        {
            "namespace": "GOOGL",
            "content": """
제목: 20250724_알파벳 (GOOGL US_매수)
- 목표주가 $241로 상향
- 검색광고, 클라우드 고성장
- AI 투자 증대, 수익화는 과제로 남음
""".strip()
        },
        {
            "namespace": "AAPL",
            "content": """
제목: 20250502_애플 (AAPL US_Not Rated)
- 매출·이익 모두 예상치 부합
- Mac/서비스 매출 호조
- 탄소 배출 절감, 고객 충성도 강조
""".strip()
        }
    ]

    # 임베딩 모델 로드
    print("Loading embedding model (BAAI/bge-m3)...")
    model = SentenceTransformer("BAAI/bge-m3", device="cpu")
    print("Model loaded.")

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            print(f"Processing {len(docs)} documents...")
            
            # 기존 데이터 삭제 (새로운 데이터로 채우기 위함)
            print("Deleting existing data from company_reports...")
            cursor.execute("DELETE FROM company_reports;")
            
            for doc in docs:
                content = doc['content']
                namespace = doc['namespace']
                
                # 문서 전체를 하나의 임베딩으로 생성
                embedding = model.encode(content)
                
                metadata = {
                    "source": "dummy_data",
                    "document_length": len(content)
                }

                cursor.execute("""
                    INSERT INTO company_reports (embedding, document, metadata, namespace)
                    VALUES (%s, %s, %s, %s)
                """, (embedding.tolist(), content, psycopg2.extras.Json(metadata), namespace))
                print(f"Inserted document for {namespace}")

            conn.commit()
            cursor.close()
        finally:
            conn.close()
            print("Dummy data collection completed!")
    else:
        print("Could not connect to the database. Aborting.")