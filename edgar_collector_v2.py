import os
import json
import psycopg2
from dotenv import load_dotenv
from sec_edgar_downloader import Downloader
from langchain_community.document_loaders import BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# .env 파일에서 환경 변수 로드
load_dotenv()

# ------------------------------------------------------------------------------
# 설정
# ------------------------------------------------------------------------------
# SEC Downloader 설정
DOWNLOAD_DIR = "sec_filings"
EMAIL_ADDRESS = os.getenv("SEC_EMAIL_ADDRESS", "james4327@gmail.com")
# 분석 대상 기업 티커
TICKERS = ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL"]
# 다운로드할 공시 유형 (10-K만 활성화)
FORM_TYPES = [
    # "10-K",
    "10-Q",
    "8-K",
    "S-1",
    "DEF 14A",
    "SC 13D",
    "SC 13G"
]
# 임베딩 모델
EMBEDDING_MODEL = 'BAAI/bge-m3'

# 데이터베이스 연결 정보
DB_HOST = os.getenv("PG_HOST")
DB_PORT = os.getenv("PG_PORT")
DB_NAME = os.getenv("PG_NAME")
DB_USER = os.getenv("PG_USER")
DB_PASSWORD = os.getenv("PG_PASSWORD")

# ------------------------------------------------------------------------------
# SEC 공시 자료 다운로드
# ------------------------------------------------------------------------------
def download_filings():
    print("SEC 공시 자료 다운로드를 시작합니다...")
    dl = Downloader("MiraeAsset", EMAIL_ADDRESS, DOWNLOAD_DIR)
    
    for ticker in TICKERS:
        for form_type in FORM_TYPES:
            try:
                # 최근 1개만 다운로드 (인자 이름 수정: amount -> limit)
                dl.get(form_type, ticker, limit=1, download_details=True)
                print(f"[{ticker}] {form_type} 다운로드 성공")
            except Exception as e:
                print(f"[{ticker}] {form_type} 다운로드 실패: {e}")
    print("다운로드 완료.")

# ------------------------------------------------------------------------------
# 파일 처리 및 데이터베이스 저장
# ------------------------------------------------------------------------------
def process_and_store_files():
    print("\n 파일 처리 및 데이터베이스 저장을 시작합니다...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    except psycopg2.OperationalError as e:
        print(f"데이터베이스 연결 실패: {e}")
        return

    # 텍스트 분할기 설정
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # 다운로드된 파일 순회
    filings_path = os.path.join(DOWNLOAD_DIR, "sec-edgar-filings")
    for ticker in os.listdir(filings_path):
        ticker_path = os.path.join(filings_path, ticker)
        for form_type in os.listdir(ticker_path):
            form_path = os.path.join(ticker_path, form_type)
            for filing_dir in os.listdir(form_path):
                filing_path = os.path.join(form_path, filing_dir)
                
                filing_html_path = None
                
                # 1. 메타데이터 파일에서 정확한 문서명 찾기 (가장 신뢰도 높은 방법)
                details_json_path = os.path.join(filing_path, "filing-details.json")
                if os.path.exists(details_json_path):
                    try:
                        with open(details_json_path, 'r') as f:
                            details = json.load(f)
                        html_filename = details.get("document")
                        if html_filename:
                            filing_html_path = os.path.join(filing_path, html_filename)
                    except Exception as e:
                        print(f"메타데이터 파일 읽기 오류: {e}")

                # 2. 메타데이터가 없으면, 폴더 내에서 가장 큰 HTML 파일 찾기 (대체 방법)
                if not filing_html_path or not os.path.exists(filing_html_path):
                    try:
                        html_files = [f for f in os.listdir(filing_path) if f.lower().endswith((".htm", ".html"))]
                        if html_files:
                            # 가장 용량이 큰 파일을 메인 문서로 간주
                            main_doc_filename = max(html_files, key=lambda f: os.path.getsize(os.path.join(filing_path, f)))
                            filing_html_path = os.path.join(filing_path, main_doc_filename)
                    except Exception as e:
                        print(f"폴더 내 HTML 파일 검색 오류: {e}")

                # 3. 최종적으로 처리할 파일이 없으면 건너뛰기
                if not filing_html_path or not os.path.exists(filing_html_path):
                    print(f"처리할 공시 문서를 찾을 수 없어 건너뜁니다: {filing_path}")
                    continue

                try:
                    # HTML에서 텍스트 추출 (lxml의 XML 파서를 사용하도록 BSHTMLLoader 수정)
                    loader = BSHTMLLoader(
                        filing_html_path, 
                        open_encoding='utf-8',
                        bs_kwargs={'features': 'xml'}
                    )
                    documents = loader.load()

                    if not documents: 
                        print(f"문서 내용을 읽을 수 없어 건너뜁니다: {filing_path}")
                        continue

                    # 텍스트 분할
                    chunks = text_splitter.split_documents(documents)

                    # 파일 경로에서 기본 메타데이터 생성
                    metadata = {
                        "symbol": ticker,
                        "form_type": form_type,
                        "filing_dir": filing_dir,
                        "source_path": filing_html_path
                    }

                    # 각 청크를 임베딩하고 DB에 저장
                    for chunk in chunks:
                        text_content = chunk.page_content
                        embedding = model.encode(text_content).tolist()
                        
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO sec_filings (embedding, document, metadata)
                                VALUES (%s, %s, %s)
                                """,
                                (embedding, text_content, json.dumps(metadata))
                            )
                    conn.commit()
                    print(f"[{ticker}] {form_type} ({filing_dir}) 처리 및 저장 완료")

                except Exception as e:
                    print(f"파일 처리 중 오류 발생 ({filing_path}): {e}")
                    conn.rollback()

    conn.close()
    print("✨ 모든 파일 처리 및 저장이 완료되었습니다.")


if __name__ == "__main__":
    print("EDGAR 데이터 수집 스크립트 실행 시작...")
    # 1. 데이터 다운로드 실행
    download_filings()
    
    # 2. 다운로드된 파일 처리 및 DB 저장 실행
    process_and_store_files() 