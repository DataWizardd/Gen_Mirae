import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("PG_NAME"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT")
)
cursor = conn.cursor()

dummy_reports = [
    {
        "symbol": "AAPL",
        "report": {
            "title": "Apple Q2 Earnings: Solid Growth",
            "analyst": "John Kim",
            "firm": "KB Securities",
            "date": "2025-07-10",
            "content": "Apple’s service revenue continues to grow steadily. We maintain a buy rating with a target price of $210."
        }
    },
    {
        "symbol": "NVDA",
        "report": {
            "title": "NVIDIA: Leading the AI Chip Market",
            "analyst": "Emily Lee",
            "firm": "Mirae Asset",
            "date": "2025-07-15",
            "content": "With increasing demand for AI infrastructure, NVIDIA is set to outperform. Short-term volatility expected."
        }
    }
]

for doc in dummy_reports:
    cursor.execute(
        "INSERT INTO analyst_reports (symbol, report) VALUES (%s, %s)",
        (doc["symbol"], json.dumps(doc["report"]))
    )

conn.commit()
cursor.close()
conn.close()
print("✅ Dummy reports inserted.")
