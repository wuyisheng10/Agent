"""
夥伴激勵 Agent
File: C:/Users/user/claude AI_Agent/agents/14_motivation_agent.py
Function: 偵測情緒低落 / 里程碑達成，自動生成個人化激勵內容
Data:
  讀取：output/csv_data/partners.csv
  寫入：output/csv_data/motivation_log.csv（本地 CSV，不需 Google Cloud）
Trigger:
  - LINE 即時：「小幫手 激勵 夥伴名 [情境]」
  - LINE 即時：「小幫手 里程碑 夥伴名 [成就]」
  - 排程：每日 09:00 隨 morning 執行，掃描沉默 5+ 天的夥伴
"""

import argparse
import csv
import json
import os
from datetime import datetime, date
from pathlib import Path
import sys

from dotenv import load_dotenv

AGENTS_DIR = Path(__file__).resolve().parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))
from common_runtime import load_json_config, push_line_message, run_codex_cli

BASE_DIR         = Path(r"C:\Users\user\claude AI_Agent")
CSV_DIR          = BASE_DIR / "output" / "csv_data"
PARTNERS_CSV     = CSV_DIR / "partners.csv"
MOTIVATION_LOG   = CSV_DIR / "motivation_log.csv"
LOG_FILE         = BASE_DIR / "logs" / "motivation_agent_log.txt"
CONFIG           = BASE_DIR / "config" / "settings.json"

load_dotenv(dotenv_path=BASE_DIR / ".env")

LINE_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_USER  = os.getenv("LINE_USER_ID", "")
LINE_PUSH  = "https://api.line.me/v2/bot/message/push"

PARTNER_FIELDNAMES = [
    "姓名", "LINE_UID", "電話", "加入日期",
    "已完成培訓天", "最後培訓推播日", "最後聯絡日",
    "本週動作數", "風險等級", "里程碑", "備註",
]
LOG_FIELDNAMES = ["日期時間", "夥伴姓名", "觸發類型", "觸發內容", "AI回應摘要"]

EMOTION_KEYWORDS = [
    "好難", "好累", "沒有人", "放棄", "沒動力", "好沮喪",
    "不想做", "好辛苦", "沒結果", "挫折", "灰心", "想放棄",
    "沒用", "失敗了", "做不到", "沒有進展", "撐不住",
]
MILESTONE_KEYWORDS = [
    "第一單", "首次成交", "上聘", "上獎銜", "達標", "晉升",
    "旅遊資格", "第一個客戶", "突破", "首單", "拿獎",
]


# ============================================================
# CSV 讀寫工具
# ============================================================

def read_partners() -> list[dict]:
    if not PARTNERS_CSV.exists():
        return []
    with open(PARTNERS_CSV, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_partners(rows: list[dict]):
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(PARTNERS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PARTNER_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_motivation_log(name: str, trigger_type: str, context: str, summary: str):
    need_header = not MOTIVATION_LOG.exists()
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(MOTIVATION_LOG, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDNAMES, extrasaction="ignore")
        if need_header:
            writer.writeheader()
        writer.writerow({
            "日期時間":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "夥伴姓名":  name,
            "觸發類型":  trigger_type,
            "觸發內容":  context[:100],
            "AI回應摘要": summary[:100],
        })


# ============================================================
# 工具函式
# ============================================================

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [MOTIVATION] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp950", errors="replace").decode("cp950"))
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config() -> dict:
    return load_json_config(CONFIG)


def run_claude(prompt: str, timeout: int = 90) -> str:
    return run_codex_cli(prompt, timeout=timeout)


def push_line_to_owner(message: str):
    status = push_line_message(LINE_TOKEN, LINE_USER, LINE_PUSH, message)
    if status is None:
        log("  ⚠️ LINE 未設定，跳過推播")
        return
    if status != 200:
        log(f"  ⚠️ LINE 推播失敗：{status}")


def days_since(date_str: str) -> int:
    if not date_str or not date_str.strip():
        return 999
    try:
        last = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        return (date.today() - last).days
    except Exception:
        return 999


def get_partner(name: str) -> dict:
    """從 CSV 查詢夥伴，找不到回傳只含姓名的 dict"""
    for row in read_partners():
        if row.get("姓名", "").strip() == name:
            return row
    return {"姓名": name}


# ============================================================
# 激勵訊息生成
# ============================================================

def generate_emotion_support(partner: dict, context: str) -> str:
    prompt = f"""你是一位溫暖、有經驗的 Amway 夥伴兼導師。請為情緒低落的夥伴生成一則鼓勵訊息。

夥伴資訊：
姓名：{partner.get('姓名', '夥伴')}
備註：{partner.get('備註', '') or '無'}
已達里程碑：{partner.get('里程碑', '') or '尚無'}

情境：{context or '夥伴表示感到辛苦、疲憊'}

請生成：
1. 一段個人化鼓勵文（3-4句，真誠、不說教）
2. 一個相似案例（不具名，說明類似困難如何度過）
3. 一個今日小目標（具體、容易達成、30分鐘內可完成）

格式：
🤗 [鼓勵文]

💪 有位夥伴也曾[相似案例...]，後來...

🎯 今日小目標：[具體行動]"""

    return run_claude(prompt)


def generate_milestone_celebration(partner: dict, achievement: str) -> str:
    prompt = f"""你是一位充滿熱情的 Amway 導師。夥伴剛達成了一個重要里程碑，請為他/她生成慶賀訊息。

夥伴資訊：
姓名：{partner.get('姓名', '夥伴')}
備註：{partner.get('備註', '') or '無'}

達成成就：{achievement}

請生成：
1. 熱情的慶賀語（2-3句，真誠有力）
2. 肯定這個成就的意義
3. 提示下一個目標（具體、有激勵性）
4. 一句收尾勉勵語

控制在 120 字以內，語氣要讓人讀了想截圖分享！"""

    return run_claude(prompt)


def generate_silent_checkin(partner: dict, days: int) -> str:
    prompt = f"""你是一位關心朋友的人。請為久未聯絡的夥伴生成一則輕鬆的開場訊息。

夥伴資訊：
姓名：{partner.get('姓名', '夥伴')}
沉默天數：{days} 天
備註：{partner.get('備註', '') or '無'}

要求：
- 輕鬆日常的語氣，像老朋友傳訊
- 完全不提事業、產品
- 自然帶出一個讓對方容易回應的問題
- 40字以內
- 不要用「好久不見」這種開場"""

    return run_claude(prompt, timeout=45)


# ============================================================
# 主要 Agent 類別
# ============================================================

class MotivationAgent:
    def __init__(self):
        cfg = load_config()
        self.silent_days = cfg.get("new_agents", {}).get("motivation_silent_days", 5)

    def handle_realtime(self, msg: str) -> str:
        """Webhook 即時指令：激勵 / 里程碑"""
        msg = msg.strip()

        if msg.startswith("里程碑"):
            content = msg[3:].strip()
            parts = content.split(" ", 1)
            name        = parts[0].strip() if parts else ""
            achievement = parts[1].strip() if len(parts) > 1 else "達成里程碑"
            return self._handle_milestone(name, achievement)

        if msg.startswith("激勵"):
            content = msg[2:].strip()
            parts = content.split(" ", 1)
            name    = parts[0].strip() if parts else ""
            context = parts[1].strip() if len(parts) > 1 else ""
            return self._handle_emotion(name, context)

        return "⚠️ 格式：激勵 夥伴名 [情境] 或 里程碑 夥伴名 [成就]"

    def _handle_emotion(self, name: str, context: str) -> str:
        if not name:
            return "⚠️ 格式：激勵 夥伴名 [情境說明]"

        log(f"  生成情緒激勵：{name}")
        partner = get_partner(name)
        try:
            result = generate_emotion_support(partner, context)
            append_motivation_log(name, "emotion", context or "情緒低落", result[:80])
            return (
                f"💙 {name} 的激勵訊息（請確認後轉發）\n"
                f"─────────────────\n"
                f"{result}"
            )
        except Exception as e:
            log(f"  ✗ 失敗：{e}")
            return f"✗ 激勵訊息生成失敗：{e}"

    def _handle_milestone(self, name: str, achievement: str) -> str:
        if not name:
            return "⚠️ 格式：里程碑 夥伴名 [成就描述]"

        log(f"  生成里程碑慶賀：{name} — {achievement}")
        partner = get_partner(name)
        try:
            result = generate_milestone_celebration(partner, achievement)

            # 更新 partners.csv 的里程碑欄位
            rows = read_partners()
            changed = False
            for row in rows:
                if row.get("姓名", "").strip() == name:
                    existing = row.get("里程碑", "") or ""
                    row["里程碑"] = f"{existing} / {achievement}".strip(" /")
                    changed = True
                    break
            if changed:
                write_partners(rows)

            append_motivation_log(name, "milestone", achievement, result[:80])
            return (
                f"🎉 {name} 的里程碑慶賀（請確認後轉發 / 推播群組）\n"
                f"─────────────────\n"
                f"{result}"
            )
        except Exception as e:
            log(f"  ✗ 失敗：{e}")
            return f"✗ 慶賀訊息生成失敗：{e}"

    def run_scheduled(self):
        """排程：掃描沉默 5+ 天的夥伴，生成開場話推播給老闆"""
        log("=== 激勵 Agent 排程啟動 ===")
        rows = read_partners()

        silent_partners = [
            (row, days_since(row.get("最後聯絡日", "")))
            for row in rows
            if row.get("姓名", "").strip()
            and days_since(row.get("最後聯絡日", "")) >= self.silent_days
        ]

        if not silent_partners:
            log("  無沉默夥伴，結束")
            return

        log(f"  沉默夥伴：{len(silent_partners)} 位")
        lines = [f"💤 沉默夥伴開場話參考（{len(silent_partners)}人）\n"]

        for partner, d in silent_partners:
            name = partner["姓名"]
            try:
                checkin = generate_silent_checkin(partner, d)
                append_motivation_log(name, "silent_checkin", f"沉默{d}天", checkin[:80])
                lines.append(f"【{name}，{d}天未聯絡】\n{checkin}\n")
                log(f"  ✓ {name} 開場話完成")
            except Exception as e:
                log(f"  ✗ {name} 失敗：{e}")
                lines.append(f"【{name}】（生成失敗）\n")

        push_line_to_owner("\n".join(lines))
        log("=== 激勵排程完成 ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["scheduled", "emotion", "milestone"], default="scheduled")
    parser.add_argument("--name", default="")
    parser.add_argument("--context", default="")
    args = parser.parse_args()

    agent = MotivationAgent()
    if args.mode == "scheduled":
        agent.run_scheduled()
    elif args.mode == "emotion":
        print(agent._handle_emotion(args.name, args.context))
    elif args.mode == "milestone":
        print(agent._handle_milestone(args.name, args.context))
