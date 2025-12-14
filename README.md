# 部署到 Render 並使用 Render Managed Postgres

這個專案是靜態前端搭配一個小型 Flask 後端（`proxy.py`）。目前專案已改為完全使用 Render 的 Managed Postgres：當你在環境變數設定 `DATABASE_URL` 時，`/proxy` 會把收到的貼文寫入 Postgres 的 `posts` 表，並提供一個 `GET /posts` 端點讀取最新貼文。

快速步驟（Render）：

1. 建立 GitHub repo，將此專案 push 上去（請先把 `venv/` 加入 `.gitignore`，不要將虛擬環境上傳）。
2. 在 Render 建立一個 Web Service（Connect to GitHub → 選 repo）
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn proxy:app
3. 建立 Managed Postgres：在 Render 控制台新增 Database，建立後在 Database 的設定中會有一個連線字串（形式類似 postgres://... 或 postgresql://...）。
4. 在 Web Service 的 Environment 下新增 `DATABASE_URL` 環境變數，值設定為 Render 提供的 DB 連線字串。
5. 到 Web Service 的 Shell 或在本機，執行 `python init_db.py`（或在啟動時 `proxy.py` 會自動建立 table）。

本機測試：

Windows PowerShell 範例：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = 'sqlite:///local.db'  # 本機可以用 sqlite 測試
python init_db.py
python proxy.py
```

安全與注意事項：
- 不要把真實密碼或私密金鑰放在程式碼裡。使用 Render 的 Secrets/Environment 來儲存 `DATABASE_URL` 或其他機敏資訊。
- Windows 本機若要安裝 `psycopg2-binary` 可能需要 PostgreSQL dev headers，開發階段可以用 SQLite 測試；在 Render（Linux）上通常能正常安裝 `psycopg2-binary`。
 - Windows 本機若要安裝 `psycopg2-binary` 可能需要 PostgreSQL dev headers，開發階段可以用 SQLite 測試；在 Render（Linux）上通常能正常安裝 `psycopg2-binary`。
 - 已改用 psycopg v3（`psycopg[binary]`）以支援較新的 Python 版本。若你的 `DATABASE_URL` 使用 `postgres://` 開頭，程式會自動在啟動時把它轉成 `postgresql+psycopg://` 以符合 SQLAlchemy 的 psycopg v3 dialect。
 - 已改用 psycopg v3（`psycopg[binary]`）以支援較新的 Python 版本。若你的 `DATABASE_URL` 使用 `postgres://` 或 `postgresql://` 開頭，程式會在啟動時自動嘗試把它轉成合適的 SQLAlchemy dialect 前綴：
    - 如果安裝了 psycopg v3，會轉為 `postgresql+psycopg://`
    - 如果只有 psycopg2（較舊），會轉為 `postgresql+psycopg2://`
 - 如果在 Render 上出現啟動時找不到 psycopg 的錯誤（例如 ModuleNotFoundError: No module named 'psycopg2' 或 undefined symbol errors），請：
    1. 在 Render 的 Web Service Build logs 查看 pip 安裝階段是否成功安裝 `psycopg[binary]`。若安裝失敗，檢查 Python runtime 與 wheel 相容性。
    2. 在 Render Dashboard 的 Service 設定中將 Runtime 設為 `python3.11`（或使用 repo 中的 `render.yaml` 指定 runtime），然後重新部署。
    3. 若你想使用較新 Python（3.13+），可以改用 psycopg v3（已在 requirements 中設定為 `psycopg[binary]`），但仍需確認該 Python 版本有可用的 psycopg wheel。
