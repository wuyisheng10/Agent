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


def _load_partner():
    spec = _ilu.spec_from_file_location(
        "partner_engagement",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "09_partner_engagement.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_market_dev():
    spec = _ilu.spec_from_file_location(
        "market_dev_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "11_market_dev_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_training_agent():
    spec = _ilu.spec_from_file_location(
        "training_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "12_training_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_followup():
    spec = _ilu.spec_from_file_location(
        "followup_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "13_followup_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_motivation():
    spec = _ilu.spec_from_file_location(
        "motivation_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "14_motivation_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_classifier():
    spec = _ilu.spec_from_file_location(
        "classifier_agent",
        str(Path(r"C:\Users\user\claude AI_Agent") / "agents" / "15_classifier_agent.py")
    )
    m = _ilu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

BASE_DIR        = Path(r"C:\Users\user\claude AI_Agent")
SENT_LOG        = BASE_DIR / "output" / "sent_log.json"
LOG_FILE        = BASE_DIR / "logs" / "webhook_log.txt"
CLASSIFIED_DIR  = BASE_DIR / "output" / "classified"

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
  上傳圖片/檔案後會先進待歸檔目錄，再回傳數字選單
  回覆「13」可執行行事曆圖檔整理
"""

HELP_TEXT += """

📂 歸類模式（Content Router）
  上傳圖片 / 音檔 / 影片 / 檔案
    → 先進待歸檔目錄，系統回傳數字選單
    → 直接回數字即可執行，例如回 7 = 第 7 個歸檔項目
  待歸檔 / 查詢待歸檔
    → 重新查看目前待歸檔選單
  歸類模式
    → 查詢目前模式與可用模式清單
  歸類模式 [模式名稱]
    → 設定歸類模式（設定後傳任何內容都自動歸檔）
    可用：會議記錄 / 行事曆 / 夥伴跟進 / 市場開發 / 培訓資料 / 一般歸檔
  歸類模式 [人員名稱] [模式名稱]
    → 設定人員專屬歸類（如：歸類模式 建德 會議記錄）
  關閉歸類模式
    → 回到自動模式
  查詢歸檔
    → 列出所有人員的歸檔記錄（含網頁瀏覽連結）
  查詢歸檔 [人員名稱]
    → 查詢指定人員的所有歸檔（含網頁連結可查看圖片/檔案）

  在歸類模式下，不需觸發詞，直接傳：
    🖼️ 圖片 / 🎤 音檔 / 🎬 影片 / 📄 檔案 → 先暫存並回傳歸檔選單
    💬 文字 → 記入今日備註（行事曆/夥伴跟進模式會嘗試解析）
"""

HELP_TEXT += """

🎯 市場開發（新系統）
  新增潛在客戶 姓名|職業|接觸管道|備註
    → 新增至 Google Sheets 並立即 AI 評分 + 生成話術

📚 培訓系統（新系統）
  培訓 夥伴名
    → 查詢該夥伴培訓進度（Day 1/3/5/7/14/30）

📋 夥伴跟進（新系統）
  跟進報告
    → 即時生成🔴🟡🟢風險報告 + 關懷草稿

💪 夥伴激勵（新系統）
  激勵 夥伴名 [情境說明]
    → 生成個人化鼓勵文 + 今日小目標
  里程碑 夥伴名 [成就描述]
    → 生成慶賀訊息 + 更新里程碑紀錄
"""

HELP_TEXT += """

🤝 夥伴經營
  新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註
  更新夥伴 姓名 | 層級 | 近況 | 下次跟進日期 | 聯絡資訊 | 備註 | 類型 | 編號 | 合夥人 | 推薦人 | 到期日 | 年月 | 一年內新上獎銜 | 首次獎金% | 現金抵用券 | 購物積點 | 優惠券 | 本月購貨 | 上月購貨 | 前2月購貨 | 前3月購貨
  邀約夥伴 姓名 | 活動名稱 | 下次跟進日期 | 備註
  跟進夥伴 姓名 | 狀態 | 下次跟進日期 | 備註
  激勵夥伴 姓名
  查詢夥伴
  查詢待跟進夥伴
  查詢夥伴 姓名
  刪除夥伴 姓名
  匯入夥伴名單
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

def _download_line_content(msg_id: str, timeout: int = 30) -> bytes | None:
    """從 LINE Content API 下載媒體（圖片/音檔/影片/檔案）"""
    url = f"https://api-data.line.me/v2/bot/message/{msg_id}/content"
    r = requests.get(url, headers={"Authorization": f"Bearer {LINE_TOKEN}"}, timeout=timeout)
    return r.content if r.status_code == 200 else None


def handle_image_message(event: dict, mode_info: dict = None, clf=None):
    """接收圖片 → 先暫存至待歸檔，再由使用者回覆數字執行歸類"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id

    img_bytes = _download_line_content(msg_id)
    if img_bytes is None:
        reply_message(reply_token, "⚠️ 圖片下載失敗，請重試")
        return

    if clf is not None:
        menu = clf.stage_file(
            img_bytes,
            f"image_{msg_id}.jpg",
            "image",
            scope_id,
            content_type="image/jpeg",
            source_name=event.get("message", {}).get("type", "image"),
        )
        reply_message(reply_token, menu)
        return

    date_str = datetime.now().strftime("%Y%m%d")
    tl  = _load_training()
    filename = f"image_{msg_id}.jpg"
    tl.archive_image(img_bytes, filename, date_str)
    reply_message(reply_token, f"📸 圖片已歸檔（{date_str}）")


def handle_audio_message(event: dict, mode_info: dict, clf):
    """接收音檔 → 先暫存至待歸檔"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id

    data = _download_line_content(msg_id, timeout=60)
    if data is None:
        reply_message(reply_token, "⚠️ 音檔下載失敗，請重試")
        return

    menu = clf.stage_file(
        data,
        f"audio_{msg_id}.m4a",
        "audio",
        scope_id,
        content_type="audio/m4a",
        source_name=event.get("message", {}).get("type", "audio"),
    )
    reply_message(reply_token, menu)


def handle_video_message(event: dict, mode_info: dict, clf):
    """接收影片 → 先暫存至待歸檔"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id

    data = _download_line_content(msg_id, timeout=120)
    if data is None:
        reply_message(reply_token, "⚠️ 影片下載失敗，請重試")
        return

    menu = clf.stage_file(
        data,
        f"video_{msg_id}.mp4",
        "video",
        scope_id,
        content_type="video/mp4",
        source_name=event.get("message", {}).get("type", "video"),
    )
    reply_message(reply_token, menu)


def handle_file_message(event: dict, mode_info: dict, clf):
    """接收檔案（PDF/PPTX/XLSX/其他）→ 先暫存至待歸檔"""
    msg_id      = event["message"]["id"]
    reply_token = event["replyToken"]
    user_id     = event.get("source", {}).get("userId", "")
    group_id    = event.get("source", {}).get("groupId", "")
    scope_id    = group_id or user_id

    orig_name = event["message"].get("fileName", "")
    # 安全化檔名
    safe = "".join(c for c in orig_name if c.isalnum() or c in "._- ()[]") or f"file_{msg_id}"

    data = _download_line_content(msg_id, timeout=60)
    if data is None:
        reply_message(reply_token, "⚠️ 檔案下載失敗，請重試")
        return

    menu = clf.stage_file(
        data,
        safe,
        "file",
        scope_id,
        content_type=event.get("message", {}).get("fileName", ""),
        source_name=orig_name,
    )
    reply_message(reply_token, menu)


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
    partner = _load_partner()
    msg = user_msg.strip()
    push_target = group_id or user_id   # 優先推送回群組

    # ── 歸類模式指令（優先處理）──────────────────────────────
    if msg.startswith("歸類模式") or msg == "關閉歸類模式":
        try:
            clf_mod = _load_classifier()
            result = clf_mod.ClassifierAgent().handle_command(msg)
            if result:
                reply_message(reply_token, result)
                return True
        except Exception as e:
            reply_message(reply_token, f"✗ 歸類模式設定失敗：{e}")
            return True

    if msg.startswith("查詢歸檔"):
        try:
            clf_mod = _load_classifier()
            person = msg.replace("查詢歸檔", "").strip()
            result = clf_mod.ClassifierAgent().query_archive(person)
            # 附上網頁瀏覽連結
            if NGROK_URL:
                if person:
                    # 嘗試找實際資料夾名稱（支援模糊）
                    from pathlib import Path as _P
                    _classified = BASE_DIR / "output" / "classified"
                    matched_name = person
                    if _classified.exists():
                        for _d in _classified.iterdir():
                            if _d.is_dir() and (person in _d.name or _d.name in person):
                                matched_name = _d.name
                                break
                    import urllib.parse
                    url_path = urllib.parse.quote(matched_name, safe="")
                    result += f"\n\n🌐 網頁查看：{NGROK_URL}/archive/{url_path}"
                else:
                    result += f"\n\n🌐 網頁查看：{NGROK_URL}/archive"
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 查詢歸檔失敗：{e}")
        return True

    cal_result = cal.handle_calendar_command(msg)
    if cal_result:
        reply_message(reply_token, cal_result)
        return True

    partner_result = partner.handle_partner_command(msg)
    if partner_result:
        reply_message(reply_token, partner_result)
        return True

    # === 新系統：市場開發 / 培訓 / 跟進 / 激勵 ===

    if msg.startswith("新增潛在客戶"):
        def _run_market():
            try:
                market = _load_market_dev()
                result = market.MarketDevAgent().handle_add_prospect(msg)
                push_message(push_target, result)
            except Exception as e:
                push_message(push_target, f"✗ 新增潛在客戶失敗：{e}")
        reply_message(reply_token, "⏳ 正在新增並 AI 評分，請稍候...")
        threading.Thread(target=_run_market, daemon=True).start()
        return True

    if msg.startswith("培訓"):
        try:
            training = _load_training_agent()
            result = training.TrainingAgent().handle_query(msg)
            reply_message(reply_token, result)
        except Exception as e:
            reply_message(reply_token, f"✗ 培訓查詢失敗：{e}")
        return True

    if msg.strip() == "跟進報告":
        def _run_followup():
            try:
                followup = _load_followup()
                result = followup.FollowupAgent().generate_report_text()
                push_message(push_target, result)
            except Exception as e:
                push_message(push_target, f"✗ 跟進報告失敗：{e}")
        reply_message(reply_token, "⏳ 正在生成跟進報告，請稍候...")
        threading.Thread(target=_run_followup, daemon=True).start()
        return True

    if msg.startswith("激勵") or msg.startswith("里程碑"):
        def _run_motivation():
            try:
                motivation = _load_motivation()
                result = motivation.MotivationAgent().handle_realtime(msg)
                push_message(push_target, result)
            except Exception as e:
                push_message(push_target, f"✗ 激勵訊息失敗：{e}")
        reply_message(reply_token, "⏳ 正在生成激勵訊息，請稍候...")
        threading.Thread(target=_run_motivation, daemon=True).start()
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

    # 載入歸類模式（一次，供所有 event 共用）
    try:
        _clf_mod   = _load_classifier()
        _clf_agent = _clf_mod.ClassifierAgent()
        _mode_info = _clf_agent.get_mode()
    except Exception as _e:
        log(f"  ⚠️ ClassifierAgent 載入失敗：{_e}")
        _clf_agent = None
        _mode_info = {"mode": "auto", "set_at": ""}

    for event in events:
        if event.get("type") != "message":
            continue

        msg_type    = event.get("message", {}).get("type", "")
        reply_token = event.get("replyToken", "")
        user_id     = event.get("source", {}).get("userId", "")
        group_id    = event.get("source", {}).get("groupId", "")
        push_target = group_id or user_id

        # ── 圖片 ───────────────────────────────────────────────
        if msg_type == "image":
            log(f"🖼️ 收到圖片（模式：{_mode_info['mode']}）")
            handle_image_message(event, _mode_info, _clf_agent)
            continue

        # ── 音檔 ───────────────────────────────────────────────
        if msg_type == "audio":
            log(f"🎤 收到音檔（模式：{_mode_info['mode']}）")
            if _clf_agent:
                handle_audio_message(event, _mode_info, _clf_agent)
            else:
                reply_message(reply_token, "⚠️ 音檔功能暫時無法使用")
            continue

        # ── 影片 ───────────────────────────────────────────────
        if msg_type == "video":
            log(f"🎬 收到影片（模式：{_mode_info['mode']}）")
            if _clf_agent:
                handle_video_message(event, _mode_info, _clf_agent)
            else:
                reply_message(reply_token, "⚠️ 影片功能暫時無法使用")
            continue

        # ── 檔案（PDF/PPTX/XLSX 等）────────────────────────────
        if msg_type == "file":
            fname = event.get("message", {}).get("fileName", "")
            log(f"📄 收到檔案：{fname}（模式：{_mode_info['mode']}）")
            if _clf_agent:
                handle_file_message(event, _mode_info, _clf_agent)
            else:
                reply_message(reply_token, "⚠️ 檔案功能暫時無法使用")
            continue

        if msg_type != "text":
            continue

        user_msg = event["message"]["text"]
        log(f"📨 收到訊息 from {user_id[:8]}：{user_msg[:50]}")

        if _clf_agent:
            pending_scope = group_id or user_id
            pending = _clf_agent.get_pending(pending_scope)
            if pending and user_msg.strip().isdigit():
                choice = int(user_msg.strip())
                log(f"  待歸檔選擇：{choice}")
                reply_message(reply_token, _clf_agent.execute_pending_option(pending_scope, choice))
                continue
            if pending and user_msg.strip() in {"待歸檔", "查詢待歸檔"}:
                reply_message(reply_token, _clf_agent.format_pending_menu(pending_scope))
                continue

        # ── 觸發詞檢查 ─────────────────────────────────────────
        content = extract_trigger(user_msg)
        if content is None:
            # 歸類模式：無觸發詞的文字也要處理
            if _mode_info["mode"] != "auto" and _clf_agent:
                log(f"  歸類模式({_mode_info['mode']})：路由文字")
                _clf_agent.route_text(
                    user_msg, _mode_info["mode"], _mode_info.get("person", ""),
                    reply_message, push_message, reply_token, push_target
                )
            else:
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
# 📂 歸檔瀏覽器（HTML）
# ============================================================

_ARCHIVE_MODE_ICON = {
    "會議記錄": "📝", "行事曆": "🗓️", "夥伴跟進": "🤝",
    "市場開發": "🎯", "培訓資料": "📚", "一般歸檔": "📁",
}
_ARCHIVE_EXT_ICON = {
    ".pdf": "📄", ".pptx": "📊", ".xlsx": "📊", ".docx": "📝",
    ".mp4": "🎬", ".m4a": "🎤", ".mov": "🎬",
}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _render_archive_html(current_dir: Path, url_parts: list) -> str:
    """產生歸檔瀏覽器 HTML 頁面"""

    # ── 麵包屑 ──────────────────────────────────────────────
    crumbs = ['<a href="/archive">歸檔總覽</a>']
    for i, part in enumerate(url_parts):
        href = "/archive/" + "/".join(url_parts[:i + 1])
        crumbs.append(f'<a href="{href}">{part}</a>')
    breadcrumb = " &rsaquo; ".join(crumbs)

    # ── 分類子項 ────────────────────────────────────────────
    subdirs, images, other_files, notes_text = [], [], [], ""

    if current_dir.exists():
        for item in sorted(current_dir.iterdir()):
            if item.is_dir():
                subdirs.append(item)
            elif item.is_file():
                if item.name == "notes.txt":
                    try:
                        notes_text = item.read_text(encoding="utf-8")
                    except Exception:
                        notes_text = "(讀取失敗)"
                elif item.suffix.lower() in _IMAGE_EXTS:
                    images.append(item)
                else:
                    other_files.append(item)

    # ── 資料夾卡片 ──────────────────────────────────────────
    dir_cards_html = ""
    for d in subdirs:
        href = "/archive/" + "/".join(url_parts + [d.name])
        icon = _ARCHIVE_MODE_ICON.get(d.name, "📁")
        try:
            dt = datetime.strptime(d.name, "%Y%m%d")
            label = dt.strftime("%Y/%m/%d")
            icon = "📅"
        except ValueError:
            label = d.name
        file_count = sum(1 for _ in d.rglob("*") if _.is_file())
        dir_cards_html += f'''
        <a href="{href}" class="card">
          <span class="icon">{icon}</span>
          <div>
            <div class="card-name">{label}</div>
            <div class="card-meta">{file_count} 個檔案</div>
          </div>
        </a>'''

    # ── 圖片格子 ────────────────────────────────────────────
    images_html = ""
    for img in images:
        href = "/archive/" + "/".join(url_parts + [img.name])
        images_html += f'''
        <a href="{href}" target="_blank" class="img-thumb">
          <img src="{href}" alt="{img.name}" loading="lazy">
          <div class="img-name">{img.name}</div>
        </a>'''

    # ── 一般檔案列表 ────────────────────────────────────────
    files_html = ""
    for f in other_files:
        href = "/archive/" + "/".join(url_parts + [f.name])
        ext = f.suffix.lower()
        icon = _ARCHIVE_EXT_ICON.get(ext, "📎")
        size = f.stat().st_size
        size_str = f"{size // 1024}KB" if size >= 1024 else f"{size}B"
        files_html += f'''
        <div class="file-row">
          <a href="{href}" download="{f.name}">{icon} {f.name}</a>
          <span class="file-size">{size_str}</span>
        </div>'''

    # ── notes.txt 預覽 ──────────────────────────────────────
    notes_html = ""
    if notes_text:
        safe = notes_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        notes_html = f'''
        <div class="section-title">📋 備註記錄</div>
        <div class="notes-box"><pre>{safe}</pre></div>'''

    # ── 各區塊組合 ──────────────────────────────────────────
    body_parts = []
    if dir_cards_html:
        body_parts.append(
            f'<div class="section-title">資料夾</div>'
            f'<div class="cards">{dir_cards_html}</div>'
        )
    body_parts.append(notes_html)
    if images_html:
        body_parts.append(
            f'<div class="section-title">圖片（{len(images)} 張）</div>'
            f'<div class="img-grid">{images_html}</div>'
        )
    if files_html:
        body_parts.append(
            f'<div class="section-title">檔案（{len(other_files)} 個）</div>'
            f'<div class="file-list">{files_html}</div>'
        )
    if not dir_cards_html and not images_html and not files_html and not notes_text:
        body_parts.append('<div class="empty">此資料夾目前沒有內容</div>')

    body = "\n".join(body_parts)
    title = url_parts[-1] if url_parts else "歸檔總覽"

    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — 歸檔瀏覽器</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
     background:#f5f5f7;color:#1d1d1f;}}
.header{{background:#fff;padding:14px 20px;border-bottom:1px solid #e5e5ea;
         position:sticky;top:0;z-index:10;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.header h1{{font-size:18px;margin-bottom:4px}}
.breadcrumb{{font-size:13px;color:#888}}
.breadcrumb a{{color:#007aff;text-decoration:none}}
.breadcrumb a:hover{{text-decoration:underline}}
.container{{max-width:900px;margin:0 auto;padding:16px 20px}}
.section-title{{font-size:11px;font-weight:700;color:#888;text-transform:uppercase;
                letter-spacing:.5px;margin:20px 0 8px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}
.card{{background:#fff;border-radius:12px;padding:12px 14px;text-decoration:none;
       color:#1d1d1f;display:flex;align-items:center;gap:10px;
       box-shadow:0 1px 3px rgba(0,0,0,.08);transition:box-shadow .15s}}
.card:hover{{box-shadow:0 4px 12px rgba(0,0,0,.14)}}
.icon{{font-size:26px;line-height:1;flex-shrink:0}}
.card-name{{font-size:13px;font-weight:600;word-break:break-word}}
.card-meta{{font-size:11px;color:#aaa;margin-top:2px}}
.img-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px}}
.img-thumb{{display:block;text-decoration:none;color:#555}}
.img-thumb img{{width:100%;height:110px;object-fit:cover;border-radius:8px;
                border:1px solid #e5e5ea;display:block}}
.img-name{{font-size:10px;margin-top:3px;text-align:center;
           overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.file-list{{background:#fff;border-radius:12px;overflow:hidden;
            box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.file-row{{display:flex;justify-content:space-between;align-items:center;
           padding:11px 16px;border-bottom:1px solid #f2f2f7}}
.file-row:last-child{{border-bottom:none}}
.file-row a{{text-decoration:none;color:#007aff;font-size:13px}}
.file-row a:hover{{text-decoration:underline}}
.file-size{{font-size:11px;color:#aaa;margin-left:8px;white-space:nowrap}}
.notes-box{{background:#fffde7;border:1px solid #ffe082;border-radius:12px;padding:14px 16px}}
.notes-box pre{{white-space:pre-wrap;font-size:13px;line-height:1.65;font-family:inherit}}
.empty{{text-align:center;color:#bbb;padding:48px 0;font-size:14px}}
</style>
</head>
<body>
<div class="header">
  <h1>📂 歸檔瀏覽器</h1>
  <div class="breadcrumb">{breadcrumb}</div>
</div>
<div class="container">
{body}
</div>
</body>
</html>'''


@app.route("/archive")
@app.route("/archive/")
def archive_index():
    return _render_archive_html(CLASSIFIED_DIR, []), 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/archive/<path:subpath>")
def archive_browse(subpath):
    target = CLASSIFIED_DIR / subpath
    if not target.exists():
        return "<h2 style='font-family:sans-serif;padding:20px'>找不到此路徑</h2>", 404
    if target.is_file():
        return send_from_directory(str(target.parent), target.name)
    parts = list(Path(subpath).parts)
    return _render_archive_html(target, parts), 200, {"Content-Type": "text/html; charset=utf-8"}


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
