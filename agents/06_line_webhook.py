"""
LINE Bot Webhook Server
File: C:/Users/user/claude AI_Agent/agents/06_line_webhook.py
Function: Receive user replies, AI intent detection, update follow-up status
Run: python 06_line_webhook.py (keep running)
External access: use ngrok (free) to expose Webhook URL
"""

import os
import json
import hmac
import hashlib
import base64
from datetime import datetime
from pathlib import Path
from flask import Flask, request, abort
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

BASE_DIR      = Path(r"C:\Users\user\claude AI_Agent")
SENT_LOG      = BASE_DIR / "output" / "sent_log.json"
LOG_FILE      = BASE_DIR / "logs" / "webhook_log.txt"

LINE_TOKEN    = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_SECRET   = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_REPLY    = "https://api.line.me/v2/bot/message/reply"

client = Anthropic()
app    = Flask(__name__)

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [WEBHOOK] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 🔐 LINE 簽章驗證
# ============================================================

def verify_signature(body: bytes, signature: str) -> bool:
    if not LINE_SECRET:
        return True  # 開發模式跳過驗證
    hash_val = hmac.new(
        LINE_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    return base64.b64encode(hash_val).decode() == signature


# ============================================================
# 🤖 AI 意圖分析
# ============================================================

def analyze_intent(user_message: str) -> dict:
    """分析用戶回覆的意圖"""
    prompt = f"""
分析以下訊息的意圖，以純JSON回覆：

訊息：「{user_message}」

{{
  "意圖": "有興趣 | 需要更多資訊 | 婉拒 | 忙碌稍後 | 其他",
  "情緒": "正面 | 中立 | 負面",
  "建議回覆": "一句繁體中文的建議回覆（50字內）",
  "建議行動": "安排會面 | 發送資料 | 暫停跟進 | 繼續跟進 | 移除名單"
}}
"""
    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        import re
        text = re.sub(r"```json|```", "", r.content[0].text).strip()
        return json.loads(text)
    except:
        return {
            "意圖": "其他",
            "情緒": "中立",
            "建議回覆": "謝謝你的回覆！我稍後再跟你聯繫 😊",
            "建議行動": "繼續跟進"
        }


# ============================================================
# 💬 回覆 LINE 訊息
# ============================================================

def reply_message(reply_token: str, message: str):
    import requests
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(LINE_REPLY, headers=headers, json=payload, timeout=5)


# ============================================================
# 📡 Webhook 路由
# ============================================================

@app.route("/webhook", methods=["POST"])
def webhook():
    # 驗證簽章
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()

    if not verify_signature(body, signature):
        log("❌ 簽章驗證失敗")
        abort(400)

    data = request.json
    events = data.get("events", [])

    for event in events:
        if event.get("type") != "message":
            continue
        if event.get("message", {}).get("type") != "text":
            continue

        user_id     = event["source"]["userId"]
        reply_token = event["replyToken"]
        user_msg    = event["message"]["text"]

        log(f"📨 收到回覆 from {user_id[:8]}：{user_msg[:50]}")

        # AI 分析意圖
        intent = analyze_intent(user_msg)
        log(f"  意圖：{intent['意圖']} | 情緒：{intent['情緒']} | 行動：{intent['建議行動']}")

        # 根據行動更新狀態
        update_status(user_id, intent)

        # 自動回覆
        reply_message(reply_token, intent["建議回覆"])

    return "OK"


@app.route("/health", methods=["GET"])
def health():
    return {"status": "running", "time": datetime.now().isoformat()}


# ============================================================
# 📝 更新跟進狀態
# ============================================================

def update_status(user_id: str, intent: dict):
    """根據 AI 分析結果更新追蹤紀錄"""
    try:
        if SENT_LOG.exists():
            with open(SENT_LOG, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        data[f"reply_{user_id}"] = {
            "時間":    datetime.now().isoformat(),
            "意圖":    intent["意圖"],
            "情緒":    intent["情緒"],
            "建議行動": intent["建議行動"],
        }

        with open(SENT_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"  ⚠️ 狀態更新失敗：{e}")


# ============================================================
# 🚀 啟動伺服器
# ============================================================

if __name__ == "__main__":
    log("🚀 LINE Webhook 伺服器啟動")
    log("📡 本地地址：http://localhost:5000/webhook")
    log("💡 對外存取：請執行 ngrok http 5000")
    log("   複製 ngrok URL 設定到 LINE Console → Webhook URL")
    app.run(host="0.0.0.0", port=5000, debug=False)
