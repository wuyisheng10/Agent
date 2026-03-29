"""
LINE Bot Module
File: C:/Users/user/claude AI_Agent/agents/05_line_bot.py
Function: Read messages JSON and send LINE messages based on follow-up schedule
Requires: LINE Messaging API (free plan)
"""

import os
import json
import requests
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# ⚙️ 設定
# ============================================================

BASE_DIR      = Path(r"C:\Users\user\claude AI_Agent")
MESSAGES_DIR  = BASE_DIR / "output" / "messages"
SENT_LOG      = BASE_DIR / "output" / "sent_log.json"   # 發送紀錄（避免重複發送）
LOG_FILE      = BASE_DIR / "logs" / "agent_log.txt"

# LINE Messaging API
LINE_TOKEN    = os.getenv("LINE_CHANNEL_TOKEN", "")     # Channel Access Token
LINE_API      = "https://api.line.me/v2/bot/message/push"
LINE_REPLY    = "https://api.line.me/v2/bot/message/reply"

# LINE Bot 群組/好友設定（依你的實際帳號填入）
# 取得方式：讓用戶加 Bot 好友後，從 webhook 取得 userId
DEFAULT_USER_ID = os.getenv("LINE_USER_ID", "")

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [LINE_BOT] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 📬 LINE 訊息發送功能
# ============================================================

class LineBotSender:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {token}"
        }

    def send_text(self, user_id: str, message: str) -> bool:
        """發送純文字訊息"""
        payload = {
            "to": user_id,
            "messages": [{"type": "text", "text": message}]
        }
        try:
            r = requests.post(LINE_API, headers=self.headers,
                              json=payload, timeout=10)
            if r.status_code == 200:
                log(f"  ✅ 發送成功 → {user_id[:8]}...")
                return True
            else:
                log(f"  ❌ 發送失敗：{r.status_code} {r.text[:100]}")
                return False
        except Exception as e:
            log(f"  ❌ 例外錯誤：{e}")
            return False

    def send_flex(self, user_id: str, prospect: dict, message: str) -> bool:
        """發送 Flex Message（卡片樣式，視覺更好看）"""
        flex_content = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [{
                    "type": "text",
                    "text": "🌟 安麗 AI 邀約系統",
                    "weight": "bold",
                    "color": "#1a73e8",
                    "size": "md"
                }],
                "backgroundColor": "#f0f7ff"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"話術類型：{prospect.get('話術類型', '')}",
                        "size": "sm",
                        "color": "#666666"
                    },
                    {"type": "separator", "margin": "sm"},
                    {
                        "type": "text",
                        "text": message,
                        "wrap": True,
                        "size": "sm",
                        "margin": "md"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "message",
                            "label": "✅ 已發送",
                            "text": f"已發送訊息給：{prospect.get('標題','')[:20]}"
                        },
                        "height": "sm",
                        "color": "#1a73e8"
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "message",
                            "label": "⏭ 跳過",
                            "text": f"跳過：{prospect.get('標題','')[:20]}"
                        },
                        "height": "sm",
                        "margin": "sm"
                    }
                ]
            }
        }

        payload = {
            "to": user_id,
            "messages": [{
                "type": "flex",
                "altText": "安麗 AI 邀約通知",
                "contents": flex_content
            }]
        }

        try:
            r = requests.post(LINE_API, headers=self.headers,
                              json=payload, timeout=10)
            return r.status_code == 200
        except:
            # Flex 失敗就 fallback 純文字
            return self.send_text(user_id, message)

    def send_summary(self, user_id: str, stats: dict):
        """發送每日摘要通知給業主"""
        msg = (
            f"📊 安麗 AI Agent 每日報告\n"
            f"{'─'*25}\n"
            f"📅 日期：{date.today()}\n"
            f"✉️  今日發送：{stats.get('sent', 0)} 則\n"
            f"⏭  跳過：{stats.get('skipped', 0)} 則\n"
            f"❌  失敗：{stats.get('failed', 0)} 則\n"
            f"{'─'*25}\n"
            f"🔔 下次跟進：明日 Day3 名單"
        )
        self.send_text(user_id, msg)


# ============================================================
# 📅 發送紀錄管理（防止重複發送）
# ============================================================

def load_sent_log() -> dict:
    if SENT_LOG.exists():
        with open(SENT_LOG, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_sent_log(log_data: dict):
    SENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_LOG, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def already_sent(sent_log: dict, prospect_id: int, day: str) -> bool:
    key = f"{prospect_id}_{day}"
    return key in sent_log

def mark_sent(sent_log: dict, prospect_id: int, day: str):
    key = f"{prospect_id}_{day}"
    sent_log[key] = datetime.now().isoformat()


# ============================================================
# 🎯 核心：依跟進時程發送訊息
# ============================================================

def process_messages(sender: LineBotSender, user_id: str) -> dict:
    """讀取最新訊息檔案，依今天的日期決定發送哪些"""

    files = sorted(MESSAGES_DIR.glob("messages_*.json"))
    if not files:
        log("⚠️ 找不到訊息檔案，請先執行 03_templates.py")
        return {"sent": 0, "skipped": 0, "failed": 0}

    today = date.today().strftime("%Y-%m-%d")
    sent_log = load_sent_log()
    stats = {"sent": 0, "skipped": 0, "failed": 0}

    # 讀取所有訊息檔（可能有多天的累積）
    for msg_file in files:
        with open(msg_file, encoding="utf-8") as f:
            data = json.load(f)

        for p in data.get("messages", []):
            pid      = p.get("id", 0)
            schedule = p.get("跟進時程", {})
            messages = p.get("訊息", {})

            # 檢查今天應該發哪個 Day
            for day, send_date in schedule.items():
                if send_date != today:
                    continue
                if day not in messages:
                    continue
                if already_sent(sent_log, pid, day):
                    log(f"  ⏭ 已發送過（跳過）：#{pid} {day}")
                    stats["skipped"] += 1
                    continue

                msg_text = messages[day]
                log(f"  📤 發送 {day}：#{pid} {p.get('標題','')[:25]}")

                # 發送（Flex 卡片模式）
                ok = sender.send_flex(user_id, p, msg_text)

                if ok:
                    mark_sent(sent_log, pid, day)
                    stats["sent"] += 1
                else:
                    stats["failed"] += 1

    save_sent_log(sent_log)
    return stats


# ============================================================
# 🚀 主程式
# ============================================================

def main():
    log("=" * 55)
    log("🚀 LINE Bot 發送Agent 啟動")

    if not LINE_TOKEN:
        log("⚠️ 未設定 LINE_CHANNEL_TOKEN，進入模擬模式")
        log("   請在 .env 檔案設定：")
        log("   LINE_CHANNEL_TOKEN=你的Token")
        log("   LINE_USER_ID=你的UserId")
        log("=" * 55)
        return

    if not DEFAULT_USER_ID:
        log("⚠️ 未設定 LINE_USER_ID")
        return

    sender = LineBotSender(LINE_TOKEN)
    stats  = process_messages(sender, DEFAULT_USER_ID)

    # 發送每日摘要給業主
    sender.send_summary(DEFAULT_USER_ID, stats)

    log(f"📊 發送完成：成功 {stats['sent']} | 跳過 {stats['skipped']} | 失敗 {stats['failed']}")
    log("=" * 55)


if __name__ == "__main__":
    main()
