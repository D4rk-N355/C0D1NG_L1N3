import os
import datetime
from flask import Flask, request, Response, jsonify
import requests

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
)
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# 原來的 Google Apps Script URL（備援）
API_URL = os.environ.get(
    "GAS_API_URL",
    "https://script.google.com/macros/s/AKfycbx6UdvQqj0NABc2ngtTkyzk5dU9CwaMXOIbjUWmMab65A9HqoD387pXY49wHOpBsL-GEg/exec",
)

# 支援 DATABASE_URL（Render 管理 Postgres）
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = None
Session = None
posts_table = None

if DATABASE_URL:
    # 建立 SQLAlchemy engine 與 table metadata
    try:
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
    except Exception:
        # 若建立 DB 失敗，保留 engine 為 None，後續會使用 GAS 轉發
        engine = None


@app.route("/proxy", methods=["POST"])
def proxy_post():
    """接受前端 POST，若設定 DATABASE_URL 則寫入 Postgres，否則轉發到 Google Apps Script。

    行為：
    - 接收 JSON，欄位：nickname、content
    - 若可用，寫入資料庫後回傳簡單成功訊息
    - 若 DB 不可用，回退到舊的 GAS 轉發行為
    """
    try:
        json_data = request.get_json() or {}
        nickname = json_data.get("nickname", "匿名")
        content = json_data.get("content", "")

        # 優先嘗試寫入資料庫
        if engine and Session and posts_table is not None:
            try:
                with Session() as sess:
                    ins = posts_table.insert().values(
                        nickname=nickname, content=content, created_at=datetime.datetime.utcnow()
                    )
                    sess.execute(ins)
                    sess.commit()
                return jsonify({"status": "ok", "source": "db"}), 201
            except SQLAlchemyError as db_err:
                # 若 DB 發生錯誤，作為降級：嘗試轉發到 GAS
                app.logger.exception("DB write failed, falling back to GAS: %s", db_err)

        # 回退：轉發到 Google Apps Script（form-urlencoded）
        form_data = {"nickname": nickname, "content": content}
        r = requests.post(API_URL, data=form_data, timeout=10)
        return Response(r.text, status=r.status_code, mimetype="text/plain")
    except Exception as err:
        app.logger.exception("Unexpected error in /proxy: %s", err)
        return Response("error: " + str(err), status=500, mimetype="text/plain")


@app.route("/posts", methods=["GET"])
def list_posts():
    """簡單的讀取端點：若有 DB，從 posts table 讀取最新的 50 筆；否則回傳空陣列或錯誤訊息。"""
    if engine and Session and posts_table is not None:
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
    else:
        # 若沒有 DB，提示前端目前無儲存功能（仍可用 GAS）
        return jsonify({"message": "no database configured; proxy will forward to GAS"}), 200


if __name__ == "__main__":
    # 本機測試用（不要用在 production）
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)