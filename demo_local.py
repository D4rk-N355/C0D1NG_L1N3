"""在同一個進程中啟動 app 的測試 client，使用 SQLite 做本機 demo。

執行方式（在已安裝依賴的 venv 中）:
    python demo_local.py
"""
import os
import json

# 使用本機 sqlite 檔案
os.environ.setdefault("DATABASE_URL", "sqlite:///local.db")

import proxy

app = proxy.app

def run_demo():
    # 建立 table（proxy 模組在 import 時已建立，但再呼叫一次沒問題）
    if hasattr(proxy, 'engine') and proxy.engine is not None:
        # call init via proxy module state
        pass

    client = app.test_client()

    payload = {"nickname": "demo_user", "content": "Hello from local demo"}
    resp = client.post('/proxy', json=payload)
    print('POST /proxy -> status:', resp.status_code)
    try:
        print('POST response:', resp.get_json())
    except Exception:
        print('POST response text:', resp.get_data(as_text=True))

    resp2 = client.get('/posts')
    print('\nGET /posts -> status:', resp2.status_code)
    print('GET response:', json.dumps(resp2.get_json(), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    run_demo()
