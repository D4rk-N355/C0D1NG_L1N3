import os
import datetime
import importlib.util
import sys
import platform
from flask import Flask, request, Response, jsonify

from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Text, DateTime
)
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# 支援 DATABASE_URL（Render 管理 Postgres） — 在 Render 上必須設定此 env var
DATABASE_URL = os.environ.get("DATABASE_URL")

# Detect available Postgres DB API package: prefer psycopg (v3), fall back to psycopg2
HAS_PSYCOPG = False
HAS_PSYCOPG2 = False
try:
    import psycopg as _psycopg  # type: ignore
    HAS_PSYCOPG = True
except Exception:
    HAS_PSYCOPG = False

try:
    import psycopg2 as _psycopg2  # type: ignore
    HAS_PSYCOPG2 = True
except Exception:
    HAS_PSYCOPG2 = False

# Check whether SQLAlchemy has a dialect plugin for psycopg (v3)
PSYCOPG_DIALECT_AVAILABLE = importlib.util.find_spec("sqlalchemy.dialects.postgresql.psycopg") is not None

engine = None
Session = None
posts_table = None

# Normalize DATABASE_URL based on installed driver and provider-provided schemes.
if DATABASE_URL:
    # provider might give postgres:// or postgresql://. Normalize to include
    # the SQLAlchemy dialect prefix when possible so SQLAlchemy imports the
    # correct DBAPI (psycopg for v3 or psycopg2 for v2).
    if DATABASE_URL.startswith("postgres://"):
        # Prefer psycopg v3 only if SQLAlchemy provides the dialect plugin.
        if HAS_PSYCOPG and PSYCOPG_DIALECT_AVAILABLE:
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
        elif HAS_PSYCOPG2:
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        elif HAS_PSYCOPG:
            # psycopg v3 is installed but SQLAlchemy lacks the dialect plugin
            # (older SQLAlchemy). Fall back to psycopg2 dialect if possible.
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        else:
            raise RuntimeError(
                "No Postgres DB driver found: install psycopg[binary] or psycopg2-binary, "
                "or set Render runtime to a Python version compatible with your driver."
            )

    elif DATABASE_URL.startswith("postgresql://"):
        # If psycopg v3 is available prefer explicit dialect prefix
        if HAS_PSYCOPG and not DATABASE_URL.startswith("postgresql+psycopg://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

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


# Log environment and DB driver availability at startup so we can debug without shell access
def _startup_diag():
    try:
        psycopg_version = None
        psycopg2_version = None
        try:
            import psycopg as _p
            psycopg_version = getattr(_p, "__version__", None)
        except Exception:
            psycopg_version = None
        try:
            import psycopg2 as _p2
            psycopg2_version = getattr(_p2, "__version__", None)
        except Exception:
            psycopg2_version = None

        diag = {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "has_psycopg_v3": HAS_PSYCOPG,
            "psycopg_version": psycopg_version,
            "has_psycopg2": HAS_PSYCOPG2,
            "psycopg2_version": psycopg2_version,
            "psycopg_dialect_available": PSYCOPG_DIALECT_AVAILABLE,
        }
        app.logger.info("startup diag: %s", diag)
        return diag
    except Exception as e:
        app.logger.exception("startup diag failed: %s", e)
        return {"error": str(e)}


_startup_diag()


@app.route("/_diag", methods=["GET"])
def diag_endpoint():
    """Return non-sensitive runtime diagnostics when ENABLE_DIAG=1 is set.

    This endpoint is intended for temporary debugging in environments where
    shell access is not available (e.g., Render free tier). It does NOT return
    database credentials or sensitive information.
    """
    if os.environ.get("ENABLE_DIAG", "0").lower() not in ("1", "true", "yes"):
        return jsonify({"error": "diagnostics disabled"}), 403

    diag = _startup_diag()
    return jsonify(diag)


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