"""
夥伴跟進報告 Agent
File: C:/Users/user/claude AI_Agent/agents/13_followup_agent.py
Function:
  - 依夥伴互動頻率計算風險等級
  - 產生每日跟進報告
  - 為高風險夥伴生成跟進草稿
Data:
  - output/csv_data/partners.csv
  - 若 CSV 不存在，退回讀取 output/partners/partners.json
Trigger:
  - 排程每日執行
  - LINE / Web 手動觸發「跟進報告」
"""

import csv
import os
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

try:
    from common_runtime import BASE_DIR, load_json_config, push_line_message, run_codex_cli
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR, load_json_config, push_line_message, run_codex_cli

CSV_DIR = BASE_DIR / "output" / "csv_data"
PARTNERS_CSV = CSV_DIR / "partners.csv"
PARTNERS_JSON = BASE_DIR / "output" / "partners" / "partners.json"
LOG_FILE = BASE_DIR / "logs" / "followup_agent_log.txt"
CONFIG = BASE_DIR / "config" / "settings.json"

load_dotenv(dotenv_path=BASE_DIR / ".env")

LINE_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_USER = os.getenv("LINE_USER_ID", "")
LINE_PUSH = "https://api.line.me/v2/bot/message/push"

FIELD_NAME = "姓名"
FIELD_LINE_UID = "LINE_UID"
FIELD_PHONE = "電話"
FIELD_JOINED = "加入日期"
FIELD_TRAINING_DAYS = "已完成培訓天"
FIELD_LAST_TRAINING_PUSH = "最後培訓推播日"
FIELD_LAST_CONTACT = "最後聯絡日"
FIELD_WEEKLY_ACTIONS = "本週動作數"
FIELD_RISK = "風險等級"
FIELD_MILESTONE = "里程碑"
FIELD_NOTE = "備註"

FIELDNAMES = [
    FIELD_NAME,
    FIELD_LINE_UID,
    FIELD_PHONE,
    FIELD_JOINED,
    FIELD_TRAINING_DAYS,
    FIELD_LAST_TRAINING_PUSH,
    FIELD_LAST_CONTACT,
    FIELD_WEEKLY_ACTIONS,
    FIELD_RISK,
    FIELD_MILESTONE,
    FIELD_NOTE,
]


def _legacy_row_to_clean(row: dict) -> dict:
    values = list(row.values())
    padded = values + [""] * max(0, len(FIELDNAMES) - len(values))
    return dict(zip(FIELDNAMES, padded[: len(FIELDNAMES)]))


def _normalize_partner_row(row: dict) -> dict:
    if FIELD_NAME in row:
        return {field: row.get(field, "") for field in FIELDNAMES}
    return _legacy_row_to_clean(row)


def read_csv() -> list[dict]:
    if not PARTNERS_CSV.exists():
        return _read_partners_json()
    with open(PARTNERS_CSV, encoding="utf-8-sig", newline="") as f:
        return [_normalize_partner_row(row) for row in csv.DictReader(f)]


def _read_partners_json() -> list[dict]:
    import json as _json

    if not PARTNERS_JSON.exists():
        return []
    with open(PARTNERS_JSON, encoding="utf-8") as f:
        raw = _json.load(f)

    rows = []
    for partner in raw:
        updated = (partner.get("updated_at") or "")[:10]
        next_followup = partner.get("next_followup", "") or ""
        records = partner.get("records") or []
        weekly_actions = sum(
            1
            for record in records
            if (record.get("time") or "")[:10]
            >= date.today().replace(day=max(1, date.today().day - 6)).isoformat()
        )
        rows.append(
            {
                FIELD_NAME: partner.get("name", ""),
                FIELD_LINE_UID: "",
                FIELD_PHONE: "",
                FIELD_JOINED: (partner.get("created_at") or "")[:10],
                FIELD_TRAINING_DAYS: "",
                FIELD_LAST_TRAINING_PUSH: next_followup or updated,
                FIELD_LAST_CONTACT: updated,
                FIELD_WEEKLY_ACTIONS: str(weekly_actions),
                FIELD_RISK: partner.get("stage", ""),
                FIELD_MILESTONE: partner.get("recent_title", "") or partner.get("goal", ""),
                FIELD_NOTE: partner.get("note", ""),
            }
        )
    return rows


def write_csv(rows: list[dict]):
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(PARTNERS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in FIELDNAMES} for row in rows])


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
        log("  ⚠️ LINE 推播失敗：缺少必要設定")
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
    days = days_silent(partner.get(FIELD_LAST_CONTACT, ""))
    try:
        weekly = int((partner.get(FIELD_WEEKLY_ACTIONS, "0") or "0").strip())
    except (ValueError, AttributeError):
        weekly = 0
    if days >= red_days and weekly == 0:
        return "red"
    if days >= yellow_days:
        return "yellow"
    return "green"


def generate_followup_draft(partner: dict, days: int) -> str:
    name = partner.get(FIELD_NAME, "")
    milestone = partner.get(FIELD_MILESTONE, "") or "尚無紀錄"
    note = partner.get(FIELD_NOTE, "") or "無"
    
    prompt = f"""你是一位擁有 20 年經驗、語氣溫暖且充滿智慧的事業導師（Mentor）。
請針對以下這位已經有段時間未深入互動的夥伴，產出精確的「跟進策略分析」與「溫暖低壓的訊息草稿」。

### 夥伴背景資料
- 姓名：{name}
- 沉默天數：{days} 天
- 目前里程碑/獎銜：{milestone}
- 備註資訊：{note}

### 要求
1. 觀察分析：根據沉默天數與備註，判斷該夥伴目前的狀態。
2. 跟進策略：給出具體的切入點建議。
3. 建議訊息：產出一段約 60-120 字的 LINE 訊息草稿。語氣要像老朋友，帶一點 Emoji，絕對不要催促業績或提到產品，要專注於「人」的關懷。

請使用繁體中文回傳結果，直接顯示內容，不需開場白。"""

    try:
        return run_codex_cli(prompt, timeout=90)
    except Exception as e:
        log(f"  AI 生成失敗: {e}")
        return "（建議先以輕鬆的語氣關心近況，避開事業話題，重建互動溫度。）"


def _load_prompt_manager():
    import importlib.util
    from pathlib import Path
    
    # 處理數字開頭的模組載入
    mod_name = "ai_prompt_manager"
    path = Path(__file__).parent / "20_ai_prompt_manager.py"
    if not path.exists():
        path = Path(r"C:\Users\user\claude AI_Agent\agents\20_ai_prompt_manager.py")
        
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.AIPromptManager()


class FollowupAgent:
    def __init__(self):
        cfg = load_config()
        new_agents = cfg.get("new_agents", {})
        self.red_days = new_agents.get("followup_red_days", 3)
        self.yellow_days = new_agents.get("followup_yellow_days", 5)

    def run(self):
        log("=== 夥伴跟進報告 Agent 啟動 ===")
        report = self.generate_report_text()
        push_line(report)
        log("=== 跟進報告推播完成 ===")

    def generate_report_text(self, target_name: str = None) -> str:
        rows = read_csv()
        if not rows:
            return f"📭 夥伴跟進報告\n找不到 {PARTNERS_CSV.name} 或夥伴主資料。"

        if target_name:
            target_name = target_name.strip()
            row = next((r for r in rows if r.get(FIELD_NAME, "").strip() == target_name), None)
            if not row:
                return f"🔍 找不到夥伴「{target_name}」的跟進資料。"
            
            days = days_silent(row.get(FIELD_LAST_CONTACT, ""))
            
            pm = _load_prompt_manager()
            prompt = pm.render_prompt(
                "followup_individual_report",
                target_name=target_name,
                last_contact=row.get(FIELD_LAST_CONTACT, '無記錄'),
                days=days,
                weekly_actions=row.get(FIELD_WEEKLY_ACTIONS, '0'),
                milestone=row.get(FIELD_MILESTONE, '尚無紀錄'),
                note=row.get(FIELD_NOTE, '無')
            )

            try:
                log(f"  🚀 正在為 {target_name} 生成 Codex 深度報告...")
                return run_codex_cli(prompt, timeout=90)
            except Exception as e:
                log(f"  AI 生成失敗: {e}")
                return f"📈 夥伴跟進報告：{target_name}\n（AI 生成暫時無法使用，請根據備註內容進行基礎關懷。）"

        red_list = []
        yellow_list = []
        green_list = []
        red_drafts = {}
        changed = False

        for row in rows:
            name = row.get(FIELD_NAME, "").strip()
            if not name:
                continue

            days = days_silent(row.get(FIELD_LAST_CONTACT, ""))
            risk = classify_risk(row, self.red_days, self.yellow_days)
            risk_label = {"red": "🔴高風險", "yellow": "🟡中風險", "green": "🟢正常"}[risk]
            if row.get(FIELD_RISK) != risk_label:
                row[FIELD_RISK] = risk_label
                changed = True

            note = row.get(FIELD_NOTE, "").strip()

            if risk == "red":
                red_list.append({"name": name, "days": days, "note": note[:20] if note else ""})
                try:
                    draft = generate_followup_draft(row, days)
                    red_drafts[name] = draft
                    log(f"  ✓ {name} 草稿生成完成")
                except Exception as e:
                    log(f"  ⚠️ {name} 草稿生成失敗：{e}")
                    red_drafts[name] = "請先以關心近況為主，避免直接推銷，先建立互動。"
            elif risk == "yellow":
                yellow_list.append({"name": name, "days": days})
            else:
                green_list.append(name)

        if changed:
            write_csv(rows)

        now_str = datetime.now().strftime("%H:%M")
        lines = [f"📋 今日夥伴跟進報告 {now_str}\n"]

        lines.append(f"🔴 高風險：{len(red_list)} 位")
        if red_list:
            for item in red_list:
                suffix = f"｜{item['note']}" if item["note"] else ""
                days_label = f"{item['days']} 天未互動" if item["days"] < 999 else "未記錄互動"
                lines.append(f"  - {item['name']}｜{days_label}{suffix}")
        else:
            lines.append("  - 無")

        lines.append(f"\n🟡 中風險：{len(yellow_list)} 位")
        if yellow_list:
            for item in yellow_list:
                lines.append(f"  - {item['name']}｜已 {item['days']} 天未聯絡")
        else:
            lines.append("  - 無")

        lines.append(f"\n🟢 正常：{len(green_list)} 位")
        lines.append(f"  {' / '.join(green_list)}" if green_list else "  - 無")

        if red_drafts:
            lines.append("\n" + "—" * 20)
            lines.append("📝 高風險夥伴跟進草稿")
            for name, draft in red_drafts.items():
                lines.append(f"\n【{name}】\n{draft}")

        return "\n".join(lines)


if __name__ == "__main__":
    FollowupAgent().run()
