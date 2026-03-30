"""
市場開發 Agent
File: C:/Users/user/claude AI_Agent/agents/11_market_dev_agent.py
Function: 陌生名單評分 → 生成開場話術 → 追蹤接觸狀態
Data:  output/csv_data/market_list.csv（本地 CSV，不需 Google Cloud）
Trigger:
  - 每日 09:00 自動掃描（由 10_orchestrator.py 呼叫）
  - LINE 輸入「小幫手 新增潛在客戶 姓名|職業|接觸管道|備註」
CSV 欄位:
  姓名|電話|職業|接觸管道|備註|AI評分|需求標籤|話術_健康型|話術_收入型|話術_好奇型|接觸狀態|最後更新|下次跟進日
"""

import csv
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR   = Path(r"C:\Users\user\claude AI_Agent")
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
    # 優先：Codex CLI
    response_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt",
            delete=False, dir=str(BASE_DIR / "logs")
        ) as f:
            response_path = f.name
        result = subprocess.run(
            ["cmd", "/c", "codex", "exec",
             "--skip-git-repo-check", "--sandbox", "read-only",
             "--color", "never", "-C", str(BASE_DIR),
             "-o", response_path, "-"],
            input=prompt, capture_output=True, text=True,
            encoding="utf-8", timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "codex CLI 回傳非零")
        out = ""
        if response_path and os.path.exists(response_path):
            with open(response_path, "r", encoding="utf-8") as f:
                out = f.read().strip()
        if not out:
            out = result.stdout.strip()
        if out:
            return out
        raise RuntimeError("codex CLI 未回傳內容")
    except Exception:
        raise
    finally:
        if response_path and os.path.exists(response_path):
            try:
                os.unlink(response_path)
            except Exception:
                pass


def extract_json(text: str) -> dict:
    cleaned = re.sub(r"```json|```", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"找不到 JSON：{cleaned[:100]}")
    return json.loads(match.group())


def push_line(message: str):
    if not LINE_TOKEN or not LINE_USER:
        log("  ⚠️ LINE 未設定，跳過推播")
        return
    import requests
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_TOKEN}"}
    chunks = [message[i:i+4900] for i in range(0, len(message), 4900)]
    payload = {"to": LINE_USER, "messages": [{"type": "text", "text": c} for c in chunks[:5]]}
    r = requests.post(LINE_PUSH, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        log(f"  ⚠️ LINE 推播失敗：{r.status_code}")


# ============================================================
# AI 評分與話術生成
# ============================================================

def score_prospect(row: dict) -> dict:
    prompt = f"""你是 Amway 市場開發顧問。請評估以下潛在客戶，給出 JSON 格式回應。

潛在客戶資料：
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
    prompt = f"""你是 Amway 市場開發顧問。請為以下潛在客戶生成三版開場話術。

潛在客戶：
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
        """掃描並評分所有未評分潛在客戶"""
        log("=== 市場開發 Agent 啟動 ===")
        rows = read_csv()

        if not rows:
            log(f"  名單為空（{MARKET_CSV}）")
            log("  可手動新增：小幫手 新增潛在客戶 姓名|職業|接觸管道|備註")
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
            log("  今日無新潛在客戶需評分")

        log(f"=== 市場開發完成，共評分 {scored_count} 筆 ===")

    def _send_summary(self, count: int, results: list):
        lines = [f"🎯 今日市場開發摘要\n共評分 {count} 位潛在客戶\n"]
        for r in results:
            star = "⭐" * int(r["評分"]) if r["評分"].isdigit() else ""
            lines.append(f"• {r['姓名']} — {r['評分']}分 {star}\n  標籤：{r['標籤']}")
        lines.append(f"\n📂 查看完整話術：{MARKET_CSV}")
        push_line("\n".join(lines))

    def handle_add_prospect(self, msg: str) -> str:
        """LINE 指令：新增潛在客戶 姓名|職業|接觸管道|備註"""
        content = msg.replace("新增潛在客戶", "", 1).strip()
        parts = [p.strip() for p in content.split("|")]
        while len(parts) < 4:
            parts.append("")
        name, job, channel, note = parts[0], parts[1], parts[2], parts[3]

        if not name:
            return "⚠️ 格式：新增潛在客戶 姓名|職業|接觸管道|備註"

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
                f"✅ 潛在客戶已新增並評分\n\n"
                f"姓名：{name}\n職業：{job}\n"
                f"AI評分：{score}分 {star}\n需求標籤：{tag}\n\n"
                f"📝 健康型：{h}{'...' if len(scripts.get('健康型',''))>60 else ''}\n"
                f"💰 收入型：{i}{'...' if len(scripts.get('收入型',''))>60 else ''}\n"
                f"🤔 好奇型：{c}{'...' if len(scripts.get('好奇型',''))>60 else ''}"
            )
        except Exception as e:
            log(f"  評分失敗：{e}")
            return f"✅ {name} 已新增至名單（評分稍後自動執行）"


if __name__ == "__main__":
    MarketDevAgent().run()
