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
import threading
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, abort, send_from_directory
from dotenv import load_dotenv
import importlib.util as _ilu
import sys as _sys

def _load_training():
    spec = _ilu.spec_from_file_location(
        "training_log",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "07_training_log.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_calendar():
    spec = _ilu.spec_from_file_location(
        "calendar_manager",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "08_calendar_manager.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

BASE_DIR      = Path(r"C:\Users\user\claude AI_Agent")
SENT_LOG      = BASE_DIR / "output" / "sent_log.json"
LOG_FILE      = BASE_DIR / "logs" / "webhook_log.txt"

LINE_TOKEN    = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_SECRET   = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_REPLY    = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH     = "https://api.line.me/v2/bot/message/push"
NGROK_URL     = os.getenv("NGROK_URL", "").rstrip("/")

# 觸發詞設定（訊息必須以此開頭才會被處理）
TRIGGER_WORDS = ["小幫手", "@Yisheng助理", "@Yisheng", "/yisheng"]

HELP_TEXT = """\
📋 Yisheng 助理 — 可用指令
觸發詞：小幫手 / @Yisheng / /yisheng
══════════════════════
📚 培訓記錄
  整理
    → 整理今天已歸檔的逐字稿
  整理 YYYYMMDD
    → 整理指定日期的逐字稿
  整理 [逐字稿內容]
    → 直接附上逐字稿一起整理
  再次整理
    → 強制覆蓋重新整理今天記錄
  再次整理 [逐字稿]
    → 強制覆蓋並重新整理

🔍 查詢記錄
  MTG-YYYYMMDD
    → 查詢指定日期的培訓總結
    範例：MTG-20260329

📷 傳送圖片
  → 自動歸檔至今日培訓資料夾

❓ 說明
  查詢 / 指令 / help / ?
    → 顯示此說明
══════════════════════
完整記錄網頁版：
""" + (NGROK_URL + "/summary/YYYYMMDD" if NGROK_URL else "（尚未設定 NGROK_URL）")

HELP_TEXT += """

🗓️ 行事曆
  查詢行事曆
  查詢過往行事曆
  查詢行事曆 YYYY-MM-DD
  查詢行事曆 YYYY-MM-DD 到 YYYY-MM-DD
  查詢全部行事曆
  新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註
  修改行事曆 EVT-xxxx YYYY-MM-DD [HH:MM] 標題 | 備註
  刪除行事曆 EVT-xxxx

📷 行事曆圖片
  若上傳的是行事曆，會自動整理今天之後的活動。
"""

app = Flask(__name__)

def extract_trigger(msg: str) -> str | None:
    """若訊息以觸發詞開頭，回傳去掉觸發詞後的內容；否則回傳 None"""
    for tw in TRIGGER_WORDS:
        if msg.startswith(tw):
            return msg[len(tw):].strip()
    return None

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
# 🤖 規則式意圖分析（零 API 消耗）
# ============================================================

INTENT_RULES = [
    {
        "意圖": "有興趣",
        "關鍵字": ["有興趣","想了解","想知道","告訴我","可以","好啊","好的","想試","報名","加入","怎麼做","如何"],
        "情緒": "正面",
        "建議回覆": "太好了！我這邊為你安排更多資訊，方便的話我們可以找個時間聊聊 😊",
        "建議行動": "安排會面"
    },
    {
        "意圖": "需要更多資訊",
        "關鍵字": ["什麼","詳細","介紹","說明","資料","多少錢","費用","怎樣","如何","哪裡"],
        "情緒": "中立",
        "建議回覆": "當然！我來為你說明，這個機會非常適合想要增加收入的朋友 💪",
        "建議行動": "發送資料"
    },
    {
        "意圖": "忙碌稍後",
        "關鍵字": ["忙","等等","待會","晚點","之後","改天","最近","稍後","下次"],
        "情緒": "中立",
        "建議回覆": "沒問題！等你方便的時候再聊，我隨時都在 😄",
        "建議行動": "繼續跟進"
    },
    {
        "意圖": "婉拒",
        "關鍵字": ["不用","不要","沒興趣","不需要","拒絕","算了","不了","謝謝但","不考慮"],
        "情緒": "負面",
        "建議回覆": "完全理解！如果未來有任何需要，歡迎隨時找我 😊",
        "建議行動": "暫停跟進"
    },
]

def analyze_intent(user_message: str) -> dict:
    """規則式意圖分析，零 API 消耗"""
    msg = user_message.lower()
    for rule in INTENT_RULES:
        if any(kw in msg for kw in rule["關鍵字"]):
            return {
                "意圖":    rule["意圖"],
                "情緒":    rule["情緒"],
                "建議回覆": rule["建議回覆"],
                "建議行動": rule["建議行動"],
            }
    return {
        "意圖": "其他",
        "情緒": "中立",
        "建議回覆": "謝謝你的訊息！我稍後再跟你聯繫 😊",
        "建議行動": "繼續跟進"
    }


# ============================================================
# 💬 回覆 LINE 訊息
# ============================================================

def reply_message(reply_token: str, message: str):
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    r = requests.post(LINE_REPLY, headers=headers, json=payload, timeout=5)
    if r.status_code != 200:
        log(f"  ⚠️ Reply 失敗：{r.status_code} {r.text[:80]}")

def push_message(user_id: str, message: str):
    """Push API：不受 reply token 限制，自動分割超過 4900 字的訊息"""
    MAX = 4900
    chunks = [message[i:i+MAX] for i in range(0, len(message), MAX)]
    messages = [{"type": "text", "text": c} for c in chunks[:5]]  # LINE 最多 5 則
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {"to": user_id, "messages": messages}
    r = requests.post(LINE_PUSH, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        log(f"  ⚠️ Push 失敗：{r.status_code} {r.text[:120]}")


# ============================================================
# 📡 Webhook 路由
# ============================================================

def handle_image_message(event: dict):
    """接收圖片 → 下載並歸檔"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    date_str    = datetime.now().strftime("%Y%m%d")

    url = f"https://api-data.line.me/v2/bot/message/{msg_id}/content"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        tl = _load_training()
        cal = _load_calendar()
        try:
            result = cal.process_calendar_image(r.content, msg_id)
        except Exception as e:
            log(f"  行事曆整理失敗：{repr(e)}")
            result = {"is_calendar": False}

        if result.get("is_calendar"):
            reply_message(reply_token, result["message"])
        else:
            filename = f"image_{msg_id}.jpg"
            tl.archive_image(r.content, filename, date_str)
            reply_message(reply_token, f"📸 圖片已歸檔（{date_str}）\n若這是行事曆，請上傳更清楚的整張截圖。")
    else:
        reply_message(reply_token, "⚠️ 圖片下載失敗，請重試")


def handle_training_command(user_msg: str, reply_token: str,
                            user_id: str = "", group_id: str = ""):
    """
    培訓記錄指令判斷：
      整理 / 整理YYYYMMDD → 產生當日或指定日期總結（背景執行，Push 到群組）
      再次整理            → 強制覆蓋重新整理
      MTG-YYYYMMDD        → 查詢已有總結（立即 Reply）
      [長文字 >100字]     → 視為逐字稿直接整理
    """
    tl = _load_training()
    cal = _load_calendar()
    msg = user_msg.strip()
    push_target = group_id or user_id   # 優先推送回群組

    cal_result = cal.handle_calendar_command(msg)
    if cal_result:
        reply_message(reply_token, cal_result)
        return True

    # 1. Key 查詢（立即回覆）
    if msg.upper().startswith("MTG-"):
        result = tl.get_summary_by_key(msg.upper())
        if result:
            reply_message(reply_token, result)
        else:
            reply_message(reply_token, f"❌ 找不到記錄：{msg}\n請確認 Key 是否正確")
        return True

    def _parse_cmd(prefix: str) -> tuple[str | None, str | None]:
        rest = msg[len(prefix):].strip()
        if not rest:
            return datetime.now().strftime("%Y%m%d"), None
        import re as _re
        if _re.fullmatch(r"\d{8}", rest):
            return rest, None
        return datetime.now().strftime("%Y%m%d"), rest

    def _bg_process(transcript: str, date_str: str, force: bool):
        """背景執行整理，完成後 Push 到群組（不使用 reply token）"""
        try:
            key, summary_msg = tl.process_transcript(transcript, date_str, force=force)
            url_prefix = f"🌐 {NGROK_URL}/summary/{date_str}\n{'─'*20}\n" if NGROK_URL else ""
            push_message(push_target, url_prefix + summary_msg)
        except Exception as e:
            log(f"背景整理失敗：{e}")
            push_message(push_target, f"❌ 整理失敗，請重試\n{str(e)[:80]}")

    # 2. 再次整理（強制覆蓋，背景執行）
    if msg.startswith("再次整理"):
        date_str, inline = _parse_cmd("再次整理")
        if inline:
            tl.archive_transcript(inline, date_str)
            transcript = inline
        else:
            transcript_path = tl.get_date_dir(date_str) / "transcript.txt"
            if not transcript_path.exists():
                reply_message(reply_token, f"⚠️ 找不到 {date_str} 的逐字稿")
                return True
            with open(transcript_path, encoding="utf-8") as f:
                transcript = f.read()
        threading.Thread(target=_bg_process, args=(transcript, date_str, True), daemon=True).start()
        return True

    # 3. 整理指令（背景執行）
    if msg.startswith("整理"):
        date_str, inline = _parse_cmd("整理")
        if inline:
            tl.archive_transcript(inline, date_str)
            transcript = inline
        else:
            transcript_path = tl.get_date_dir(date_str) / "transcript.txt"
            if not transcript_path.exists():
                reply_message(reply_token, f"⚠️ 找不到 {date_str} 的逐字稿")
                return True
            with open(transcript_path, encoding="utf-8") as f:
                transcript = f.read()
        threading.Thread(target=_bg_process, args=(transcript, date_str, False), daemon=True).start()
        return True

    # 4. 長文字視為逐字稿（>100字，背景執行）
    if len(msg) > 100:
        date_str = datetime.now().strftime("%Y%m%d")
        tl.archive_transcript(msg, date_str)
        threading.Thread(target=_bg_process, args=(msg, date_str, False), daemon=True).start()
        return True

    return False


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()

    if not verify_signature(body, signature):
        log("❌ 簽章驗證失敗")
        abort(400)

    data   = request.json
    events = data.get("events", [])

    for event in events:
        if event.get("type") != "message":
            continue

        msg_type    = event.get("message", {}).get("type", "")
        reply_token = event["replyToken"]

        # 圖片訊息
        if msg_type == "image":
            log("🖼️ 收到圖片")
            handle_image_message(event)
            continue

        if msg_type != "text":
            continue

        user_id  = event["source"]["userId"]
        user_msg = event["message"]["text"]
        log(f"📨 收到訊息 from {user_id[:8]}：{user_msg[:50]}")

        # 觸發詞檢查
        content = extract_trigger(user_msg)
        if content is None:
            log("  略過（無觸發詞）")
            continue

        log(f"  觸發詞符合，內容：{content[:40]}")

        # 查詢指令 — 回傳所有可用指令說明
        if content.strip() in ("查詢", "指令", "help", "?", "？"):
            reply_message(reply_token, HELP_TEXT)
            continue

        # 培訓記錄指令優先
        group_id = event.get("source", {}).get("groupId", "")
        if handle_training_command(content, reply_token, user_id, group_id):
            continue

        # 一般意圖回覆
        intent = analyze_intent(content)
        log(f"  意圖：{intent['意圖']} | 情緒：{intent['情緒']} | 行動：{intent['建議行動']}")
        update_status(user_id, intent)
        reply_message(reply_token, intent["建議回覆"])

    return "OK"


@app.route("/health", methods=["GET"])
def health():
    return {"status": "running", "time": datetime.now().isoformat()}


@app.route("/summary/<date_str>", methods=["GET"])
def view_summary(date_str):
    tl = _load_training()
    path = tl.get_date_dir(date_str) / "summary.html"
    if not path.exists():
        return f"<h2>找不到 {date_str} 的記錄</h2>", 404
    with open(path, encoding="utf-8") as f:
        content = f.read()
    return content, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/summary/<date_str>/images/<path:filename>", methods=["GET"])
def view_summary_image(date_str, filename):
    tl = _load_training()
    img_dir = tl.get_date_dir(date_str) / "images"
    if not img_dir.exists():
        return f"<h2>找不到 {date_str} 的圖片資料夾</h2>", 404
    return send_from_directory(str(img_dir), filename)


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
