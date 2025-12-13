"""輔助腳本：在有設定 DATABASE_URL 時建立資料表。

用法：
    set DATABASE_URL=postgres://...   # Windows PowerShell
    python init_db.py
"""
import os
import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime


DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not set. Set it to your Postgres connection string and rerun.")
    raise SystemExit(1)

engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

posts_table = Table(
    "posts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nickname", String(100), nullable=False),
    Column("content", Text, nullable=False),
    Column("created_at", DateTime, default=datetime.datetime.utcnow),
)

if __name__ == "__main__":
    metadata.create_all(engine)
    print("Tables created (if not existed)")
