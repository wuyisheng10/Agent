"""
培訓 Agent
File: C:/Users/user/claude AI_Agent/agents/12_training_agent.py
Function: 依夥伴加入天數自動推播七天法則培訓內容
Data:  output/csv_data/partners.csv（本地 CSV，不需 Google Cloud）
Trigger:
  - 每日 09:00 自動執行（由 10_orchestrator.py 呼叫）
  - LINE 輸入「小幫手 培訓 夥伴名」→ 查詢進度
CSV 欄位:
  姓名|LINE_UID|電話|加入日期|已完成培訓天|最後培訓推播日|最後聯絡日|本週動作數|風險等級|里程碑|備註
"""

import csv
import json
import os
import subprocess
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR     = Path(r"C:\Users\user\claude AI_Agent")
CSV_DIR      = BASE_DIR / "output" / "csv_data"
PARTNERS_CSV = CSV_DIR / "partners.csv"
LOG_FILE     = BASE_DIR / "logs" / "training_agent_log.txt"
CONFIG       = BASE_DIR / "config" / "settings.json"

load_dotenv(dotenv_path=BASE_DIR / ".env")

LINE_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_USER  = os.getenv("LINE_USER_ID", "")
LINE_PUSH  = "https://api.line.me/v2/bot/message/push"

FIELDNAMES = [
    "姓名", "LINE_UID", "電話", "加入日期",
    "已完成培訓天", "最後培訓推播日", "最後聯絡日",
    "本週動作數", "風險等級", "里程碑", "備註",
]

CURRICULUM = {
    1: {
        "主題": "歡迎加入 + 七天法則說明",
        "要點": [
            "恭喜你開始這段旅程",
            "七天法則：每天一個小行動，累積改變",
            "今天的功課：告訴一個人你開始了新事業",
        ],
        "功課": "今天告訴一個親友你開始了新事業",
    },
    3: {
        "主題": "OPP觀念複習 + 打好預防針",
        "要點": [
            "家人問「安利飽和了吧？」→ 用數據說話",
            "朋友潑冷水時的心態：他們在保護你",
            "重溫 OPP 的核心：產品好 + 制度公平",
        ],
        "功課": "重溫 OPP 一次，用自己的話說給鏡子前的自己聽",
    },
    5: {
        "主題": "產品知識測試",
        "要點": [
            "你最熟悉哪一款產品？",
            "如何用一句話介紹它的核心功效？",
            "客戶最常問的三個問題是什麼？",
        ],
        "功課": "準備一款產品的 30 秒介紹詞",
    },
    7: {
        "主題": "第一週總結 + 目標設定",
        "要點": [
            "回顧這週：有哪些進展？",
            "遇到什麼困難？怎麼應對？",
            "設定下個月的一個具體目標",
        ],
        "功課": "寫下這週三件讓你有進展的事，以及下個月想達成的一個目標",
    },
    14: {
        "主題": "2689 帶線觀念",
        "要點": [
            "2689 是什麼：每週帶2人看OPP",
            "6個月後，你的線的力量",
            "帶人的心態：幫助，不是招募",
        ],
        "功課": "列出 3 位你認為適合分享事業的朋友",
    },
    30: {
        "主題": "進階：四個勇於深度分享",
        "要點": [
            "勇於分享產品體驗",
            "勇於分享事業機會",
            "勇於邀約對方去看 OPP",
            "勇於跟進，不怕被拒絕",
        ],
        "功課": "本月嘗試一次深度分享，記錄下來",
    },
}


# ============================================================
# CSV 讀寫工具
# ============================================================

def read_csv() -> list[dict]:
    if not PARTNERS_CSV.exists():
        return []
    with open(PARTNERS_CSV, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict]):
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(PARTNERS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# 工具函式
# ============================================================

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [TRAINING] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp950", errors="replace").decode("cp950"))
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config() -> dict:
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def run_claude(prompt: str, timeout: int = 90) -> str:
    result = subprocess.run(
        ["cmd", "/c", "claude", "-p", "--output-format", "text"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "claude CLI 回傳非零")
    out = result.stdout.strip()
    if not out:
        raise RuntimeError("claude CLI 未回傳內容")
    return out


def push_line(user_id: str, message: str):
    if not LINE_TOKEN or not user_id:
        log("  ⚠️ LINE 未設定或無 UID，跳過推播")
        return
    import requests
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    chunks = [message[i:i+4900] for i in range(0, len(message), 4900)]
    payload = {"to": user_id, "messages": [{"type": "text", "text": c} for c in chunks[:5]]}
    r = requests.post(LINE_PUSH, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        log(f"  ⚠️ LINE 推播失敗：{r.status_code}")


def days_since(date_str: str) -> int:
    try:
        join = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        return (date.today() - join).days
    except Exception:
        return -1


# ============================================================
# 培訓訊息生成
# ============================================================

def generate_training_message(partner: dict, day: int) -> str:
    curriculum = CURRICULUM[day]
    prompt = f"""你是一位溫暖、鼓勵型的 Amway 培訓助理。請為以下夥伴生成第 {day} 天的培訓訊息。

夥伴資訊：
姓名：{partner.get('姓名', '')}
加入天數：第 {day} 天
備註/特色：{partner.get('備註', '')}
已達里程碑：{partner.get('里程碑', '')}

今日培訓主題：{curriculum['主題']}
要點：
{chr(10).join('- ' + p for p in curriculum['要點'])}
今日功課：{curriculum['功課']}

要求：
- 開頭打招呼，語氣溫暖自然，像朋友傳訊息
- 呈現今日主題與3個要點（可用emoji輕鬆標記）
- 結尾給出今日功課，鼓勵他/她完成
- 全文控制在 200 字以內
- 不要說教，要像夥伴聊天的語氣
- 結尾一句：「有問題直接回覆這裡，助理隨時在！」"""

    return run_claude(prompt)


# ============================================================
# 主要 Agent 類別
# ============================================================

class TrainingAgent:
    def __init__(self):
        cfg = load_config()
        self.training_days = cfg.get("new_agents", {}).get(
            "training_days", [1, 3, 5, 7, 14, 30]
        )

    def run(self):
        log("=== 培訓 Agent 啟動 ===")
        rows = read_csv()

        if not rows:
            log(f"  夥伴名冊為空（{PARTNERS_CSV}）")
            return

        today_str = date.today().isoformat()
        pushed_count = 0
        changed = False

        for row in rows:
            name      = row.get("姓名", "").strip()
            join_date = row.get("加入日期", "").strip()
            line_uid  = row.get("LINE_UID", "").strip()
            last_push = row.get("最後培訓推播日", "").strip()

            if not name or not join_date:
                continue

            n_days = days_since(join_date)
            if n_days < 0:
                log(f"  ⚠️ {name} 加入日期格式錯誤：{join_date}")
                continue

            if n_days not in self.training_days:
                continue

            if last_push == today_str:
                log(f"  {name} 第{n_days}天 — 今日已推播，跳過")
                continue

            log(f"  {name} 加入第 {n_days} 天 → 推播培訓")
            try:
                msg = generate_training_message(row, n_days)
                target = line_uid if line_uid else LINE_USER
                push_line(target, msg)
                row["最後培訓推播日"] = today_str
                changed = True
                pushed_count += 1
                log(f"    ✓ 已推播{'（至夥伴）' if line_uid else '（至老闆）'}")
            except Exception as e:
                log(f"    ✗ {name} 培訓訊息失敗：{e}")

        if changed:
            write_csv(rows)

        log(f"=== 培訓完成，今日推播 {pushed_count} 位夥伴 ===")

    def handle_query(self, msg: str) -> str:
        """LINE 指令：培訓 夥伴名"""
        name = msg.replace("培訓", "", 1).strip()
        if not name:
            return "⚠️ 格式：培訓 夥伴名"

        rows = read_csv()
        for row in rows:
            if row.get("姓名", "").strip() == name:
                join_date = row.get("加入日期", "")
                n_days    = days_since(join_date)
                last_push = row.get("最後培訓推播日", "") or "尚無記錄"
                next_days = [d for d in self.training_days if d > n_days]
                next_info = f"第 {next_days[0]} 天（還有 {next_days[0]-n_days} 天）" if next_days else "已完成全部培訓"
                return (
                    f"📚 {name} 的培訓進度\n\n"
                    f"加入日期：{join_date}\n"
                    f"加入天數：第 {n_days} 天\n"
                    f"最後推播：{last_push}\n"
                    f"下一個培訓：{next_info}\n\n"
                    f"培訓節奏：Day 1 / 3 / 5 / 7 / 14 / 30"
                )

        return f"⚠️ 找不到夥伴「{name}」\n請確認姓名，或先至 {PARTNERS_CSV.name} 新增夥伴資料"


if __name__ == "__main__":
    TrainingAgent().run()
