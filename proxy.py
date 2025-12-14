import os
import datetime
from flask import Flask, request, Response, jsonify

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
)
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# 支援 DATABASE_URL（Render 管理 Postgres） — 在 Render 上必須設定此 env var
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = None
Session = None
posts_table = None

# If using psycopg v3 (psycopg[binary]) SQLAlchemy prefers the dialect
# prefix postgresql+psycopg://. Normalize common connection strings
# (many providers give postgres://) to the correct form.
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)

if DATABASE_URL:
    # 建立 SQLAlchemy engine 與 table metadata
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
    metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=engine, future=True)


@app.route("/proxy", methods=["POST"])
def proxy_post():
    """接受前端 POST，直接寫入 Postgres 並回傳新建立的貼文（JSON）。"""
    try:
        json_data = request.get_json() or {}
        nickname = json_data.get("nickname", "匿名")
        content = json_data.get("content", "")

        if not (engine and Session and posts_table is not None):
            return jsonify({"error": "database not configured"}), 500

        with Session() as sess:
            ins = posts_table.insert().values(
                nickname=nickname, content=content, created_at=datetime.datetime.utcnow()
            )
            result = sess.execute(ins)
            sess.commit()
            # 取得插入的 id（SQLAlchemy Core insert() result支持 inserted_primary_key 在某情況）
            inserted_id = None
            try:
                inserted_id = result.inserted_primary_key[0]
            except Exception:
                # 如果不可用，嘗試用最後一筆查詢（保守策略）
                row = sess.execute(posts_table.select().order_by(posts_table.c.id.desc()).limit(1)).first()
                if row:
                    inserted_id = row.id

        return jsonify({"status": "ok", "id": inserted_id}), 201
    except Exception as err:
        app.logger.exception("Unexpected error in /proxy: %s", err)
        return jsonify({"error": str(err)}), 500


@app.route("/posts", methods=["GET"])
def list_posts():
    """從 posts table 讀取最新的 50 筆並回傳 JSON。"""
    if not (engine and posts_table is not None):
        return jsonify({"error": "database not configured"}), 500

    try:
        with engine.connect() as conn:
            q = posts_table.select().order_by(posts_table.c.id.desc()).limit(50)
            result = conn.execute(q)
            items = [
                {
                    "id": row.id,
                    "nickname": row.nickname,
                    "content": row.content,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in result.fetchall()
            ]
        return jsonify(items)
    except Exception as err:
        app.logger.exception("Error reading posts: %s", err)
        return jsonify([]), 500


if __name__ == "__main__":
    # 本機測試用（不要用在 production）
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)