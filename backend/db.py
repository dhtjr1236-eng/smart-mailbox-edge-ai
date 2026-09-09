import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", 5432),
    "dbname": os.getenv("POSTGRES_DB", "mailbox"),
    "user": os.getenv("POSTGRES_USER", "admin"),
    "password": os.getenv("POSTGRES_PASSWORD", "password"),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id            SERIAL PRIMARY KEY,
            detected      BOOLEAN NOT NULL DEFAULT FALSE,
            confidence    FLOAT,
            label         VARCHAR(100),
            gemini_result TEXT,
            image_path    VARCHAR(500),
            telegram_sent BOOLEAN NOT NULL DEFAULT FALSE,
            created_at    TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[DB] 테이블 초기화 완료")
