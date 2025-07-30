import os
import io
import zipfile
import logging
import requests
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
from psycopg2.extras import execute_values

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """데이터베이스 연결을 생성합니다."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            database=os.getenv("PG_NAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            port=os.getenv("PG_PORT")
        )
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"데이터베이스 연결에 실패했습니다: {e}")
        return None

def download_and_extract_gdelt_data(target_date_str):
    """지정된 날짜의 GDELT 데이터를 다운로드하고 DataFrame으로 반환합니다."""
    url = f"http://data.gdeltproject.org/events/{target_date_str}.export.CSV.zip"
    logging.info(f"GDELT 데이터 다운로드를 시작합니다: {url}")
    
    try:
        response = requests.get(url, timeout=300) # 5분 타임아웃
        response.raise_for_status() # 200 OK가 아니면 예외 발생
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as f:
                df = pd.read_csv(f, sep='\t', header=None, low_memory=False)
                logging.info(f"데이터 로드 완료. 총 {len(df)}개의 이벤트.")
                return df
    except requests.exceptions.RequestException as e:
        logging.error(f"다운로드 실패: {e}")
    except Exception as e:
        logging.error(f"데이터 처리 중 오류 발생: {e}")
        
    return pd.DataFrame()

def filter_and_process_data(df):
    """기업 관련 데이터를 필터링하고 DB 스키마에 맞게 가공합니다."""
    # GDELT 2.0 컬럼명
    cols = [
        "GLOBALEVENTID", "SQLDATE", "MonthYear", "Year", "FractionDate", "Actor1Code", "Actor1Name", 
        "Actor1CountryCode", "Actor1KnownGroupCode", "Actor1EthnicCode", "Actor1Religion1Code", 
        "Actor1Religion2Code", "Actor1Type1Code", "Actor1Type2Code", "Actor1Type3Code", "Actor2Code", 
        "Actor2Name", "Actor2CountryCode", "Actor2KnownGroupCode", "Actor2EthnicCode", "Actor2Religion1Code", 
        "Actor2Religion2Code", "Actor2Type1Code", "Actor2Type2Code", "Actor2Type3Code", "IsRootEvent", 
        "EventCode", "EventBaseCode", "EventRootCode", "QuadClass", "GoldsteinScale", "NumMentions", 
        "NumSources", "NumArticles", "AvgTone", "Actor1Geo_Type", "Actor1Geo_FullName", 
        "Actor1Geo_CountryCode", "Actor1Geo_ADM1Code", "Actor1Geo_Lat", "Actor1Geo_Long", 
        "Actor1Geo_FeatureID", "Actor2Geo_Type", "Actor2Geo_FullName", "Actor2Geo_CountryCode", 
        "Actor2Geo_ADM1Code", "Actor2Geo_Lat", "Actor2Geo_Long", "Actor2Geo_FeatureID", 
        "ActionGeo_Type", "ActionGeo_FullName", "ActionGeo_CountryCode", "ActionGeo_ADM1Code", 
        "ActionGeo_Lat", "ActionGeo_Long", "ActionGeo_FeatureID", "DATEADDED", "SOURCEURL"
    ]
    df.columns = cols
    
    # 필터링 키워드
    keywords = ['nvidia', 'apple', 'amazon', 'microsoft', 'google', 'alphabet', 'tesla']
    
    df_filtered = df[
        df['Actor1Name'].fillna('').str.lower().str.contains('|'.join(keywords)) |
        df['Actor2Name'].fillna('').str.lower().str.contains('|'.join(keywords))
    ]
    logging.info(f"필터링 후 {len(df_filtered)}개의 기업 관련 이벤트를 찾았습니다.")

    if df_filtered.empty:
        return pd.DataFrame()

    # DB 스키마에 맞게 컬럼 선택 및 이름 변경
    schema_cols = {
        "GLOBALEVENTID": "global_event_id", "SQLDATE": "event_date", "DATEADDED": "date_added",
        "SOURCEURL": "source_url", "Actor1Name": "actor1_name", "Actor2Name": "actor2_name",
        "Actor1CountryCode": "actor1_country_code", "Actor2CountryCode": "actor2_country_code",
        "Actor1Type1Code": "actor1_type1_code", "Actor2Type1Code": "actor2_type1_code",
        "EventCode": "event_code", "EventBaseCode": "event_base_code", "EventRootCode": "event_root_code",
        "QuadClass": "quad_class", "GoldsteinScale": "goldstein_scale", "AvgTone": "avg_tone",
        "ActionGeo_CountryCode": "action_geo_country_code", "ActionGeo_Lat": "action_geo_lat",
        "ActionGeo_Long": "action_geo_long"
    }
    df_processed = df_filtered[schema_cols.keys()].rename(columns=schema_cols)

    # 데이터 타입 변환 (문자열 -> 타임스탬프)
    df_processed['event_date'] = pd.to_datetime(df_processed['event_date'], format='%Y%m%d', errors='coerce')
    df_processed['date_added'] = pd.to_datetime(df_processed['date_added'], format='%Y%m%d%H%M%S', errors='coerce')
    
    # 유효하지 않은 날짜 데이터 제거
    df_processed.dropna(subset=['global_event_id', 'event_date'], inplace=True)
    
    return df_processed

def insert_data_to_db(conn, df):
    """가공된 데이터를 DB에 삽입합니다."""
    if df.empty:
        logging.info("삽입할 데이터가 없습니다.")
        return

    # [FIX] NaT(Not a Time) 값을 DB가 인식하는 None(null)으로 명시적으로 변환
    df_clean = df.replace({pd.NaT: None})
    # 다른 NaN 값들도 None으로 변환
    df_clean = df_clean.where(pd.notnull(df_clean), None)
    
    data_tuples = [tuple(x) for x in df_clean.to_numpy()]
    
    query = """
        INSERT INTO gdelt_events (
            global_event_id, event_date, date_added, source_url, actor1_name, actor2_name,
            actor1_country_code, actor2_country_code, actor1_type1_code, actor2_type1_code,
            event_code, event_base_code, event_root_code, quad_class, goldstein_scale,
            avg_tone, action_geo_country_code, action_geo_lat, action_geo_long
        ) VALUES %s ON CONFLICT (global_event_id) DO NOTHING;
    """
    
    with conn.cursor() as cursor:
        try:
            execute_values(cursor, query, data_tuples)
            conn.commit()
            logging.info(f"{cursor.rowcount}개의 새로운 GDELT 이벤트를 성공적으로 삽입했습니다.")
        except psycopg2.Error as e:
            logging.error(f"데이터 삽입 중 오류 발생: {e}")
            conn.rollback()

def main():
    """메인 실행 함수"""
    load_dotenv()
    
    # 기본값: 어제 날짜
    target_date = datetime.utcnow() - timedelta(days=1)
    date_str = target_date.strftime('%Y%m%d')
    
    df_raw = download_and_extract_gdelt_data(date_str)
    
    if not df_raw.empty:
        df_processed = filter_and_process_data(df_raw)
        
        if not df_processed.empty:
            conn = get_db_connection()
            if conn:
                insert_data_to_db(conn, df_processed)
                conn.close()
                logging.info("데이터베이스 연결을 종료합니다.")

if __name__ == "__main__":
    main() 