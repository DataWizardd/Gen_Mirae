# document_dummy_debug.py

import os
import json
import traceback
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

def main():
    try:
        # 1) .env 로드
        load_dotenv()
        PG_NAME     = os.getenv("PG_NAME")
        PG_USER     = os.getenv("PG_USER")
        PG_PASSWORD = os.getenv("PG_PASSWORD")
        PG_HOST     = os.getenv("PG_HOST")
        PG_PORT     = os.getenv("PG_PORT")
        print("📌 Loaded env variables:",
              f"DB={PG_NAME}@{PG_HOST}:{PG_PORT}, USER={PG_USER}")

        # 2) DB 연결
        print("🔌 Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            dbname=PG_NAME,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT
        )
        cur = conn.cursor()
        print("✅ DB connection successful")

        # 3) vector 확장 설치 & 테이블 생성
        print("⚙️  Creating extension/table if not exists...")
        cur.execute("""
            CREATE EXTENSION IF NOT EXISTS vector;
            CREATE TABLE IF NOT EXISTS company_reports (
              id          SERIAL PRIMARY KEY,
              embedding   VECTOR(1024)        NOT NULL,
              document    TEXT                NOT NULL,
              metadata    JSONB,
              namespace   TEXT,
              created_at  TIMESTAMPTZ         NOT NULL DEFAULT NOW()
            );
        """)
        conn.commit()
        print("✅ Table ready")

        # 4) 임베딩 모델 로드
        print("📦 Loading embedding model...")
        model = SentenceTransformer("BAAI/bge-m3", device="cpu")
        print("✅ Model loaded")

        # 5) 삽입할 문서 리스트
        docs = [
            {
                "source": "Amazon",
                "content": """
제목: 20241204_아마존 (AMZN US_매수)
- 자체 파운데이션 모델 및 반도체, 슈퍼컴 공개
- 인프라 최적화 통한 가성비 강조
- 오픈AI, 엔비디아와 경쟁 중
- 생성 AI 비용 하락으로 전체 시장 확대 기대
""".strip()
            },
            {
                "source": "Microsoft",
                "content": """
제목: 20250718_마이크로소프트 (MSFT US_매수_신규)
- FY27 EPS 기준 목표주가 $663, 매수 의견
- AI 에이전트 도입 → 수익화 잠재력 높음
- M365, Copilot 등 AI 기능 통합으로 실적 가속화
""".strip()
            },
            {
                "source": "Nvidia",
                "content": """
제목: 20250530_엔비디아 (NVDA US_매수)
- 목표주가 $174 상향
- Blackwell 제품 본격 출하
- H20 관련 손실에도 FY26 GPM 16.6% 전망
""".strip()
            },
            {
                "source": "Alphabet",
                "content": """
제목: 20250724_알파벳 (GOOGL US_매수)
- 목표주가 $241로 상향
- 검색광고, 클라우드 고성장
- AI 투자 증대, 수익화는 과제로 남음
""".strip()
            },
            {
                "source": "Apple",
                "content": """
제목: 20250502_애플 (AAPL US_Not Rated)
- 매출·이익 모두 예상치 부합
- Mac/서비스 매출 호조
- 탄소 배출 절감, 고객 충성도 강조
""".strip()
            },
        ]

        # 6) 삽입 루프
        print("✏️  Inserting documents...")
        for i, doc in enumerate(docs, start=1):
            emb = model.encode(doc["content"], normalize_embeddings=True)
            metadata  = {"source": doc["source"]}
            namespace = "company_reports"
            cur.execute(
                """
                INSERT INTO company_reports
                    (embedding, document, metadata, namespace)
                VALUES
                    (%s,         %s,       %s,       %s)
                """,
                (
                    emb.tolist(),            # VECTOR(1024)
                    doc["content"],         # TEXT
                    json.dumps(metadata),   # JSONB
                    namespace               # TEXT
                )
            )
            print(f"  · Inserted {i}/{len(docs)}: {doc['source']}")
        conn.commit()

        # 7) 삽입 확인
        cur.execute("SELECT COUNT(*) FROM company_reports;")
        total = cur.fetchone()[0]
        print(f"✅ 총 삽입된 문서 수: {total}")

    except Exception:
        print("❌ 오류 발생:\n", traceback.format_exc())
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main()
