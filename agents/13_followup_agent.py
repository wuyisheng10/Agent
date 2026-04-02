"""
夥伴跟進 Agent
File: C:/Users/user/claude AI_Agent/agents/13_followup_agent.py
Function: 每日掃描夥伴狀態，風險分層，生成跟進報告與關懷草稿
Data:  output/csv_data/partners.csv（本地 CSV，不需 Google Cloud）
Trigger:
  - 每日 17:00 自動執行（由 10_orchestrator.py 呼叫）
  - LINE 輸入「小幫手 跟進報告」→ 立即執行
Risk:
  🔴 高風險：days_silent >= 3 AND 本週動作數 == 0
  🟡 中風險：days_silent >= 5
  🟢 正常  ：days_silent < 3
"""

import csv
import os
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv

try:
    from common_runtime import BASE_DIR, load_json_config, push_line_message, run_codex_cli
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR, load_json_config, push_line_message, run_codex_cli

CSV_DIR      = BASE_DIR / "output" / "csv_data"
PARTNERS_CSV = CSV_DIR / "partners.csv"
PARTNERS_JSON = BASE_DIR / "output" / "partners" / "partners.json"
LOG_FILE     = BASE_DIR / "logs" / "followup_agent_log.txt"
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


# ============================================================
# CSV 讀寫工具
# ============================================================

def read_csv() -> list[dict]:
    if not PARTNERS_CSV.exists():
        return _read_partners_json()
    with open(PARTNERS_CSV, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _read_partners_json() -> list[dict]:
    import json as _json

    if not PARTNERS_JSON.exists():
        return []
    with open(PARTNERS_JSON, encoding="utf-8") as f:
        raw = _json.load(f)

    rows = []
    for p in raw:
        updated = (p.get("updated_at") or "")[:10]
        next_followup = p.get("next_followup", "") or ""
        records = p.get("records") or []
        weekly_actions = sum(
            1
            for r in records
            if (r.get("time") or "")[:10] >= (date.today().replace(day=max(1, date.today().day - 6)).isoformat())
        )
        rows.append({
            "憪?": p.get("name", ""),
            "LINE_UID": "",
            "?餉店": "",
            "??交?": (p.get("created_at") or "")[:10],
            "撌脣??閮予": "",
            "?敺閮?剜": next_followup or updated,
            "?敺蝯⊥": updated,
            "?祇勗?雿": str(weekly_actions),
            "憸券蝑?": p.get("stage", ""),
            "??蝣?": p.get("recent_title", "") or p.get("goal", ""),
            "?酉": p.get("note", ""),
        })
    return rows


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
    line = f"[{ts}] [FOLLOWUP] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp950", errors="replace").decode("cp950"))
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_config() -> dict:
    return load_json_config(CONFIG)


def run_claude(prompt: str, timeout: int = 60) -> str:
    return run_codex_cli(prompt, timeout=timeout)


def push_line(message: str):
    status = push_line_message(LINE_TOKEN, LINE_USER, LINE_PUSH, message)
    if status is None:
        log("  ⚠️ LINE 未設定，跳過推播")
        return
    if status != 200:
        log(f"  ⚠️ LINE 推播失敗：{status}")


def days_silent(date_str: str) -> int:
    if not date_str or not date_str.strip():
        return 999
    try:
        last = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        return (date.today() - last).days
    except Exception:
        return 999


def classify_risk(partner: dict, red_days: int, yellow_days: int) -> str:
    d      = days_silent(partner.get("最後聯絡日", ""))
    try:
        weekly = int((partner.get("本週動作數", "0") or "0").strip())
    except (ValueError, AttributeError):
        weekly = 0
    if d >= red_days and weekly == 0:
        return "red"
    if d >= yellow_days:
        return "yellow"
    return "green"


# ============================================================
# 關懷草稿生成
# ============================================================

def generate_followup_draft(partner: dict, days: int) -> str:
    prompt = f"""你是一位溫暖、真誠的 Amway 夥伴。請幫我寫一則關懷訊息草稿，傳給久未聯絡的夥伴。

夥伴資訊：
姓名：{partner.get('姓名', '')}
已 {days} 天未聯絡
備註：{partner.get('備註', '')}
已達里程碑：{partner.get('里程碑', '') or '尚無'}

要求：
- 語氣輕鬆自然，像老朋友傳訊息
- 不要說教，不要直接問「你在做事業嗎？」
- 先關心對方最近狀況
- 可以提到一個輕鬆的話題引起回應
- 控制在 60 字以內
- 不要提到「幾天沒聯絡了」這種話"""

    return run_claude(prompt)


# ============================================================
# 主要 Agent 類別
# ============================================================

class FollowupAgent:
    def __init__(self):
        cfg = load_config()
        na = cfg.get("new_agents", {})
        self.red_days    = na.get("followup_red_days", 3)
        self.yellow_days = na.get("followup_yellow_days", 5)

    def run(self):
        """執行並推播每日跟進報告"""
        log("=== 夥伴跟進 Agent 啟動 ===")
        report = self.generate_report_text()
        push_line(report)
        log("=== 跟進報告已推播 ===")

    def generate_report_text(self) -> str:
        """建立報告文字（供 run() 和 Webhook 共用）"""
        rows = read_csv()
        if not rows:
            return f"📋 夥伴名冊為空\n請先在 {PARTNERS_CSV.name} 新增夥伴資料"

        red_list    = []
        yellow_list = []
        green_list  = []
        red_drafts  = {}
        changed     = False

        for row in rows:
            name = row.get("姓名", "").strip()
            if not name:
                continue

            d    = days_silent(row.get("最後聯絡日", ""))
            risk = classify_risk(row, self.red_days, self.yellow_days)

            risk_label = {"red": "🔴高風險", "yellow": "🟡中風險", "green": "🟢正常"}[risk]
            if row.get("風險等級") != risk_label:
                row["風險等級"] = risk_label
                changed = True

            note = row.get("備註", "").strip()

            if risk == "red":
                red_list.append({"name": name, "days": d, "note": note[:20] if note else ""})
                try:
                    draft = generate_followup_draft(row, d)
                    red_drafts[name] = draft
                    log(f"  ✓ {name} 草稿生成完成")
                except Exception as e:
                    log(f"  ✗ {name} 草稿失敗：{e}")
                    red_drafts[name] = "（草稿生成失敗，請手動撰寫）"
            elif risk == "yellow":
                yellow_list.append({"name": name, "days": d})
            else:
                green_list.append(name)

        if changed:
            write_csv(rows)

        # 組裝報告
        now_str = datetime.now().strftime("%H:%M")
        lines = [f"📋 今日夥伴狀況報告 {now_str}\n"]

        lines.append(f"🔴 必跟進（{len(red_list)}人）")
        if red_list:
            for r in red_list:
                suffix = f"，{r['note']}" if r["note"] else ""
                days_label = f"{r['days']}天未回報" if r["days"] < 999 else "從未聯絡"
                lines.append(f"  • {r['name']} — {days_label}{suffix}")
        else:
            lines.append("  無")

        lines.append(f"\n🟡 建議跟進（{len(yellow_list)}人）")
        if yellow_list:
            for y in yellow_list:
                lines.append(f"  • {y['name']} — 距上次聯絡{y['days']}天")
        else:
            lines.append("  無")

        lines.append(f"\n🟢 正常（{len(green_list)}人）")
        lines.append(f"  {' / '.join(green_list)}" if green_list else "  無")

        if red_drafts:
            lines.append("\n" + "─" * 20)
            lines.append("💬 已生成關懷草稿：")
            for name, draft in red_drafts.items():
                lines.append(f"\n【{name}】\n{draft}")

        return "\n".join(lines)


if __name__ == "__main__":
    FollowupAgent().run()
