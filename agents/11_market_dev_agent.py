"""
市場開發 Agent
File: C:/Users/user/claude AI_Agent/agents/11_market_dev_agent.py
Function: 陌生名單評分 → 生成開場話術 → 追蹤接觸狀態
Data:  output/csv_data/market_list.csv（本地 CSV，不需 Google Cloud）
Trigger:
  - 每日 09:00 自動掃描（由 10_orchestrator.py 呼叫）
  - LINE 輸入「小幫手 新增潛在家人 姓名|職業|接觸管道|備註」
CSV 欄位:
  姓名|電話|職業|接觸管道|備註|AI評分|需求標籤|話術_健康型|話術_收入型|話術_好奇型|接觸狀態|最後更新|下次跟進日
"""

import csv
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

try:
    from common_runtime import BASE_DIR, run_codex_cli, push_line_message
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR, run_codex_cli, push_line_message

CSV_DIR    = BASE_DIR / "output" / "csv_data"
MARKET_CSV = CSV_DIR / "market_list.csv"
LOG_FILE   = BASE_DIR / "logs" / "market_dev_log.txt"

load_dotenv(dotenv_path=BASE_DIR / ".env")

LINE_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_USER  = os.getenv("LINE_USER_ID", "")
LINE_PUSH  = "https://api.line.me/v2/bot/message/push"

FIELDNAMES = [
    "姓名", "電話", "職業", "接觸管道", "備註",
    "AI評分", "需求標籤", "話術_健康型", "話術_收入型", "話術_好奇型",
    "接觸狀態", "最後更新", "下次跟進日",
    # 擴充欄位
    "地區", "地址",
    "使用產品",
    "淨水器型號", "濾心上次換", "濾心下次換",
    "體驗記錄",
]


# ============================================================
# CSV 讀寫工具
# ============================================================

def read_csv() -> list[dict]:
    """讀取市場名單 CSV，回傳 list[dict]"""
    if not MARKET_CSV.exists():
        return []
    with open(MARKET_CSV, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict]):
    """將 list[dict] 覆蓋寫入 CSV"""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(MARKET_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_row(row: dict):
    """新增一列（若 CSV 不存在則建立含 header）"""
    need_header = not MARKET_CSV.exists()
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    with open(MARKET_CSV, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        if need_header:
            writer.writeheader()
        writer.writerow(row)


# ============================================================
# 工具函式
# ============================================================

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [MARKET_DEV] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp950", errors="replace").decode("cp950"))
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_claude(prompt: str, timeout: int = 60) -> str:
    return run_codex_cli(prompt, timeout=timeout)


def extract_json(text: str) -> dict:
    cleaned = re.sub(r"```json|```", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"找不到 JSON：{cleaned[:100]}")
    return json.loads(match.group())


def push_line(message: str):
    status = push_line_message(LINE_TOKEN, LINE_USER, LINE_PUSH, message)
    if status is None:
        log("  ⚠️ LINE 未設定，跳過推播")
        return
    if status != 200:
        log(f"  ⚠️ LINE 推播失敗：{status}")


# ============================================================
# AI 評分與話術生成
# ============================================================

def score_prospect(row: dict) -> dict:
    prompt = f"""你是 Amway 市場開發顧問。請評估以下潛在家人，給出 JSON 格式回應。

潛在家人資料：
姓名：{row.get('姓名', '')}
職業：{row.get('職業', '')}
接觸管道：{row.get('接觸管道', '')}
備註：{row.get('備註', '')}

請評估並回傳 JSON（只回傳 JSON，不要其他文字）：
{{
  "評分": <1-5整數，5最高>,
  "需求標籤": "<健康需求型 / 收入需求型 / 好奇型>",
  "評分理由": "<一句話說明>"
}}

評分標準：
5分：職業符合（護士/業務/媽媽/老師）+ 明確需求訊號
4分：有需求訊號但職業普通
3分：職業符合但無明確需求
2分：普通接觸，需進一步了解
1分：不適合或資料不足"""

    return extract_json(run_claude(prompt))


def generate_scripts(row: dict, need_tag: str) -> dict:
    prompt = f"""你是 Amway 市場開發顧問。請為以下潛在家人生成三版開場話術。

潛在家人：
姓名：{row.get('姓名', '')}
職業：{row.get('職業', '')}
需求標籤：{need_tag}
備註：{row.get('備註', '')}

生成三版話術，每版控制在 80 字以內，自然口語，不誇大，回傳 JSON：
{{
  "健康型": "<關注健康需求的開場>",
  "收入型": "<關注副業收入的開場>",
  "好奇型": "<引起好奇、輕鬆開場>"
}}

只回傳 JSON，不要其他說明。"""

    return extract_json(run_claude(prompt))


# ============================================================
# 主要 Agent 類別
# ============================================================

class MarketDevAgent:

    def run(self):
        """掃描並評分所有未評分潛在家人"""
        log("=== 市場開發 Agent 啟動 ===")
        rows = read_csv()

        if not rows:
            log(f"  名單為空（{MARKET_CSV}）")
            log("  可手動新增：小幫手 新增潛在家人 姓名|職業|接觸管道|備註")
            return

        scored_count = 0
        results = []
        changed = False

        for row in rows:
            if row.get("AI評分", "").strip():
                continue
            if not row.get("姓名", "").strip():
                continue

            name = row["姓名"]
            log(f"  處理：{name} ({row.get('職業', '')})")
            try:
                score_result = score_prospect(row)
                score  = str(score_result.get("評分", ""))
                tag    = score_result.get("需求標籤", "")
                log(f"    評分：{score}分 / {tag}")

                scripts = generate_scripts(row, tag)
                today   = datetime.now().strftime("%Y-%m-%d")
                next_f  = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

                row["AI評分"]     = score
                row["需求標籤"]   = tag
                row["話術_健康型"] = scripts.get("健康型", "")
                row["話術_收入型"] = scripts.get("收入型", "")
                row["話術_好奇型"] = scripts.get("好奇型", "")
                row["接觸狀態"]   = row.get("接觸狀態") or "待接觸"
                row["最後更新"]   = today
                row["下次跟進日"] = next_f

                scored_count += 1
                changed = True
                results.append({"姓名": name, "評分": score, "標籤": tag})
                log(f"    ✓ 評分完成")

            except Exception as e:
                log(f"    ✗ 失敗：{e}")

        if changed:
            write_csv(rows)
            log(f"  ✓ CSV 已更新：{MARKET_CSV}")

        if scored_count > 0:
            self._send_summary(scored_count, results)
        else:
            log("  今日無新潛在家人需評分")

        log(f"=== 市場開發完成，共評分 {scored_count} 筆 ===")

    def _send_summary(self, count: int, results: list):
        lines = [f"🎯 今日市場開發摘要\n共評分 {count} 位潛在家人\n"]
        for r in results:
            star = "⭐" * int(r["評分"]) if r["評分"].isdigit() else ""
            lines.append(f"• {r['姓名']} — {r['評分']}分 {star}\n  標籤：{r['標籤']}")
        lines.append(f"\n📂 查看完整話術：{MARKET_CSV}")
        push_line("\n".join(lines))

    def handle_add_prospect(self, msg: str) -> str:
        """LINE 指令：新增潛在家人 姓名|職業|接觸管道|備註"""
        content = msg.replace("新增潛在家人", "", 1).strip()
        parts = [p.strip() for p in content.split("|")]
        while len(parts) < 4:
            parts.append("")
        name, job, channel, note = parts[0], parts[1], parts[2], parts[3]

        if not name:
            return "⚠️ 格式：新增潛在家人 姓名|職業|接觸管道|備註"

        today = datetime.now().strftime("%Y-%m-%d")
        new_row = {f: "" for f in FIELDNAMES}
        new_row.update({
            "姓名": name, "職業": job, "接觸管道": channel, "備註": note,
            "接觸狀態": "新增", "最後更新": today,
        })
        append_row(new_row)

        # 立即評分
        try:
            score_result = score_prospect(new_row)
            score   = str(score_result.get("評分", ""))
            tag     = score_result.get("需求標籤", "")
            scripts = generate_scripts(new_row, tag)

            # 更新剛新增的那列
            rows = read_csv()
            for r in rows:
                if r["姓名"] == name and not r.get("AI評分", "").strip():
                    r["AI評分"]     = score
                    r["需求標籤"]   = tag
                    r["話術_健康型"] = scripts.get("健康型", "")
                    r["話術_收入型"] = scripts.get("收入型", "")
                    r["話術_好奇型"] = scripts.get("好奇型", "")
                    r["接觸狀態"]   = "待接觸"
                    r["下次跟進日"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                    break
            write_csv(rows)

            star = "⭐" * int(score) if score.isdigit() else ""
            h = scripts.get("健康型", "")[:60]
            i = scripts.get("收入型", "")[:60]
            c = scripts.get("好奇型", "")[:60]
            return (
                f"✅ 潛在家人已新增並評分\n\n"
                f"姓名：{name}\n職業：{job}\n"
                f"AI評分：{score}分 {star}\n需求標籤：{tag}\n\n"
                f"📝 健康型：{h}{'...' if len(scripts.get('健康型',''))>60 else ''}\n"
                f"💰 收入型：{i}{'...' if len(scripts.get('收入型',''))>60 else ''}\n"
                f"🤔 好奇型：{c}{'...' if len(scripts.get('好奇型',''))>60 else ''}"
            )
        except Exception as e:
            log(f"  評分失敗：{e}")
            return f"✅ {name} 已新增至名單（評分稍後自動執行）"

    def list_prospects(self, keyword: str = "") -> list[dict]:
        """回傳所有（或關鍵字篩選）潛在家人 row list"""
        rows = read_csv()
        if keyword:
            rows = [r for r in rows if keyword in r.get("姓名", "")]
        return rows

    def get_prospect_by_name(self, name: str) -> dict | None:
        """依姓名取得潛在家人完整資料"""
        for row in read_csv():
            if row.get("姓名", "") == name:
                return row
        return None

    def update_prospect_fields(self, name: str, fields: dict) -> str:
        """更新潛在家人的指定欄位（不覆蓋 AI 評分與話術）"""
        _readonly = {"AI評分", "需求標籤", "話術_健康型", "話術_收入型", "話術_好奇型"}
        rows = read_csv()
        for row in rows:
            if row.get("姓名", "") == name:
                changed = []
                for k, v in fields.items():
                    if k in FIELDNAMES and k not in _readonly:
                        row[k] = v
                        changed.append(f"{k}：{v}")
                row["最後更新"] = datetime.now().strftime("%Y-%m-%d")
                write_csv(rows)
                return "✅ " + name + " 資料已更新\n" + "\n".join(changed)
        return f"⚠️ 找不到「{name}」"

    def add_experience(self, name: str, product: str, note: str = "",
                       filter_last: str = "", filter_next: str = "") -> str:
        """新增產品體驗記錄，並更新淨水器濾心日期"""
        rows = read_csv()
        for row in rows:
            if row.get("姓名", "") == name:
                today = datetime.now().strftime("%Y-%m-%d")
                existing = row.get("體驗記錄", "")
                try:
                    records = json.loads(existing) if existing else []
                except Exception:
                    records = []
                entry = {"日期": today, "產品": product}
                if note:
                    entry["備註"] = note
                records.append(entry)
                row["體驗記錄"] = json.dumps(records, ensure_ascii=False)
                # 更新使用產品彙總
                all_prods = list(dict.fromkeys(r["產品"] for r in records if r.get("產品")))
                row["使用產品"] = "、".join(all_prods)
                if filter_last:
                    row["濾心上次換"] = filter_last
                if filter_next:
                    row["濾心下次換"] = filter_next
                row["最後更新"] = today
                write_csv(rows)
                msg = f"✅ 已為 {name} 新增體驗記錄：{product}"
                if note:
                    msg += f"\n備註：{note}"
                if filter_last:
                    msg += f"\n💧 上次換濾心：{filter_last}"
                if filter_next:
                    msg += f"\n💧 下次換濾心：{filter_next}"
                return msg
        return f"⚠️ 找不到「{name}」"

    def handle_query_prospect(self, msg: str) -> str:
        """LINE 指令：查詢潛在家人 [姓名（可省略）]"""
        keyword = msg.replace("查詢潛在家人", "", 1).strip()
        rows = read_csv()
        if not rows:
            return "📋 目前名單是空的。\n新增：小幫手 新增潛在家人 姓名|職業|管道|備註"

        if keyword:
            rows = [r for r in rows if keyword in r.get("姓名", "")]
            if not rows:
                return f"🔍 找不到「{keyword}」"

        lines = [f"📋 潛在家人名單（共 {len(rows)} 筆）\n"]
        for r in rows:
            star = "⭐" * int(r["AI評分"]) if r.get("AI評分", "").isdigit() else ""
            lines.append(
                f"👤 {r['姓名']}　{r.get('職業','')}　{star}\n"
                f"   管道：{r.get('接觸管道','')}　狀態：{r.get('接觸狀態','')}\n"
                f"   備註：{r.get('備註','')[:30]}"
            )
        return "\n".join(lines)


if __name__ == "__main__":
    MarketDevAgent().run()
