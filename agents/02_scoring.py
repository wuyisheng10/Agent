"""
Agent 2: AI Scoring Agent
File: C:/Users/user/claude AI_Agent/agents/02_scoring.py
Input: C:/Users/user/claude AI_Agent/output/prospects_raw/*.json
Output: C:/Users/user/claude AI_Agent/output/prospects_scored/YYYYMMDD_HHMM.json
"""

import os
import json
import glob
import re
import subprocess
import tempfile
import psutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# ============================================================
# ⚙️ 路徑設定
# ============================================================

BASE_DIR      = Path(r"C:\Users\user\claude AI_Agent")
INPUT_DIR     = BASE_DIR / "output" / "prospects_raw"
OUTPUT_DIR    = BASE_DIR / "output" / "prospects_scored"
LOG_FILE      = BASE_DIR / "logs" / "agent_log.txt"
CONFIG        = BASE_DIR / "config" / "settings.json"
CODEX_FALLBACK_LIMIT = 2
codex_fallback_count = 0

def load_bypass_config() -> tuple[set, set]:
    """回傳 (bypass_urls, bypass_domains)"""
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
        return set(cfg.get("bypass_urls", [])), set(cfg.get("bypass_domains", []))
    except:
        return set(), set()

def is_bypassed(url: str, bypass_urls: set, bypass_domains: set) -> bool:
    if url in bypass_urls:
        return True
    try:
        host = urlparse(url).hostname or ""
        return any(host == d or host.endswith("." + d) for d in bypass_domains)
    except:
        return False

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [SCORING] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        safe_line = line.encode("cp950", errors="replace").decode("cp950")
        print(safe_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 📐 規則式評分（快速，不消耗 API）
# ============================================================

CRITERIA = {
    "有副業需求":       {"分數": 30, "kw": ["副業","兼職","想賺","被動收入","斜槓","創業"]},
    "對健康產品有興趣":  {"分數": 25, "kw": ["健康","保健","養生","減肥","瘦身","保養","營養"]},
    "社群互動活躍":     {"分數": 25, "kw": []},   # 由留言數/收藏數判斷
    "地區符合":         {"分數": 20, "kw": ["台灣","台北","台中","高雄","新北","桃園","台南"]},
}

def rule_score(p: dict) -> tuple[int, dict]:
    text = f"{p.get('標題','')} {p.get('摘要','')}".lower()
    score = 0
    detail = {}
    for name, cfg in CRITERIA.items():
        kws = cfg["kw"]
        pts = cfg["分數"]
        if name == "社群互動活躍":
            # 留言 > 20 或 收藏 > 50 視為活躍
            active = p.get("留言數", 0) > 20 or p.get("收藏數", 0) > 50
            earned = pts if active else 0
        else:
            earned = pts if (kws and any(k in text for k in kws)) else 0
        score += earned
        detail[name] = earned
    return score, detail


# ============================================================
# 🤖 Claude AI 深度分析
# ============================================================

def build_ai_prompt(p: dict) -> str:
    return (
        "你是安麗事業的資深業務顧問，請分析這位潛在客戶並以純JSON回覆（不加說明或markdown）：\n\n"
        f"資料：\n"
        f"- 標題：{p.get('標題','')}\n"
        f"- 摘要：{p.get('摘要','')}\n"
        f"- 留言數：{p.get('留言數',0)}\n"
        f"- 收藏數：{p.get('收藏數',0)}\n\n"
        "回覆格式：\n"
        '{"需求分析":"50字內說明此人的核心需求",'
        '"推薦話術類型":"上班族副業 | 全職媽媽 | 健康意識族群 | 社群達人 | 創業斜槓族",'
        '"最佳接觸時機":"立即 | 觀察1週 | 觀察1個月",'
        '"注意事項":"30字內",'
        '"AI加分":0到20的整數}'
    )

def check_cpu(cli_name: str):
    """CPU > 60% 拋出例外；50~60% 僅警告 log。"""
    cpu = psutil.cpu_percent(interval=1)
    if cpu > 60:
        msg = f"  [{cli_name}] CPU {cpu:.0f}% > 60%，略過本次呼叫"
        log(msg)
        raise RuntimeError(msg)
    if cpu > 50:
        log(f"  [{cli_name}] ⚠️ CPU {cpu:.0f}% > 50%，繼續執行但請注意負載")

def extract_json_payload(text: str) -> dict:
    cleaned = re.sub(r"```json|```", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found: {cleaned[:120]}")
    return json.loads(match.group())

def run_gemini_cli(prompt_text: str) -> dict:
    check_cpu("Gemini")
    log("  [Gemini] 開始呼叫 Gemini CLI")
    log(f"  [Gemini] 指令：cmd /c gemini --prompt <prompt>")
    log(f"  [Gemini] Prompt 前80字：{prompt_text[:80].replace(chr(10), ' ')}")

    result = subprocess.run(
        ["cmd", "/c", "gemini", "--prompt", prompt_text],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30
    )

    log(f"  [Gemini] returncode：{result.returncode}")

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if stdout:
        log(f"  [Gemini] stdout（前200字）：{stdout[:200]}")
    else:
        log("  [Gemini] stdout：（空）")

    if stderr:
        log(f"  [Gemini] stderr（前200字）：{stderr[:200]}")
    else:
        log("  [Gemini] stderr：（空）")

    if result.returncode != 0:
        err = stderr or stdout or "gemini CLI 回傳非零"
        log(f"  [Gemini] 失敗，錯誤：{err[:200]}")
        raise RuntimeError(err)

    log("  [Gemini] 分析完成，解析 JSON")
    return extract_json_payload(stdout)

def run_claude_cli(prompt_text: str) -> dict:
    check_cpu("Claude")
    log("  使用 Claude CLI 進行分析")
    result = subprocess.run(
        ["cmd", "/c", "claude", "-p", "--output-format", "text"],
        input=prompt_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "claude CLI 回傳非零"
        raise RuntimeError(err)
    log("  Claude CLI 分析完成")
    return extract_json_payload(result.stdout)

def run_codex_cli(prompt_text: str) -> dict:
    check_cpu("Codex")
    response_path = None
    try:
        log("  使用 Codex CLI 進行分析")
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt",
            delete=False, dir=str(BASE_DIR / "logs")
        ) as f:
            response_path = f.name

        result = subprocess.run(
            [
                "cmd", "/c", "codex", "exec",
                "--skip-git-repo-check",
                "--sandbox", "read-only",
                "--color", "never",
                "-C", str(BASE_DIR),
                "-o", response_path,
                "-"
            ],
            input=prompt_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90
        )
        if result.returncode != 0:
            err = result.stderr.strip() or result.stdout.strip() or "codex CLI 回傳非零"
            raise RuntimeError(err)

        output_text = ""
        if response_path and os.path.exists(response_path):
            with open(response_path, "r", encoding="utf-8") as f:
                output_text = f.read().strip()
        if not output_text:
            output_text = result.stdout.strip()
        log("  Codex CLI 分析完成")
        return extract_json_payload(output_text)
    finally:
        if response_path and os.path.exists(response_path):
            try:
                os.unlink(response_path)
            except:
                pass

def default_ai_result(reason: str) -> dict:
    return {
        "需求分析": reason,
        "推薦話術類型": "上班族副業",
        "最佳接觸時機": "觀察1週",
        "注意事項": "請人工確認",
        "AI加分": 0
    }

def ai_analyze(p: dict) -> dict:
    global codex_fallback_count
    prompt_text = build_ai_prompt(p)

    try:
        return run_gemini_cli(prompt_text)
    except Exception as gemini_error:
        log(f"  Gemini CLI分析失敗：{gemini_error}")

    try:
        return run_claude_cli(prompt_text)
    except Exception as claude_error:
        log(f"  Claude AI分析失敗：{claude_error}")

    if codex_fallback_count >= CODEX_FALLBACK_LIMIT:
        log(f"  Codex CLI 備援已達上限 {CODEX_FALLBACK_LIMIT} 筆，後續改用預設結果")
        return default_ai_result("Gemini 與 Claude 失敗，Codex 備援已達上限")

    codex_fallback_count += 1
    try:
        log(f"  Gemini 與 Claude 失敗，改用 Codex CLI 備援分析（第 {codex_fallback_count}/{CODEX_FALLBACK_LIMIT} 筆）")
        return run_codex_cli(prompt_text)
    except Exception as codex_error:
        log(f"  Codex CLI分析失敗：{codex_error}")
        return default_ai_result("AI分析失敗，請人工確認")


# ============================================================
# 🏆 完整評分流程
# ============================================================

def score_all(prospects: list) -> dict:
    high, mid, low = [], [], []
    bypass_urls, bypass_domains = load_bypass_config()

    for i, p in enumerate(prospects, 1):
        url = p.get("連結", "")
        if is_bypassed(url, bypass_urls, bypass_domains):
            log(f"  [{i}/{len(prospects)}] ⏭️ 已略過（bypass）：{url}")
            continue
        log(f"  [{i}/{len(prospects)}] {p.get('標題','')[:40]}")

        rule, detail = rule_score(p)

        # 只有規則分 >= 40 才呼叫 AI（省費用）
        ai = ai_analyze(p) if rule >= 40 else {
            "需求分析": "規則分過低，跳過AI分析",
            "推薦話術類型": "上班族副業",
            "最佳接觸時機": "觀察1個月",
            "注意事項": "",
            "AI加分": 0
        }

        total = rule + ai.get("AI加分", 0)
        record = {
            **p,
            "規則分": rule,
            "規則明細": detail,
            "AI分析": ai,
            "最終分數": total,
            "話術類型": ai.get("推薦話術類型", "上班族副業"),
            "需求分析": ai.get("需求分析", ""),
            "注意事項": ai.get("注意事項", ""),
            "最佳接觸時機": ai.get("最佳接觸時機", "觀察1個月"),
            "潛力等級": "高" if total >= 60 else ("中" if total >= 40 else "低"),
        }

        if total >= 60:
            high.append(record)
        elif total >= 40:
            mid.append(record)
        else:
            low.append(record)

    log(f"  高潛力：{len(high)} 人 / 中潛力：{len(mid)} 人 / 低潛力：{len(low)} 人")
    return {"高潛力名單": high, "中潛力名單": mid, "低潛力名單": low}


# ============================================================
# 💾 儲存
# ============================================================

def load_latest_raw() -> list:
    files = sorted(INPUT_DIR.glob("prospects_raw_*.json"))
    if not files:
        log("⚠️ 找不到原始資料，請先執行 01_scraper.py")
        return []
    latest = files[-1]
    with open(latest, encoding="utf-8") as f:
        data = json.load(f).get("data", [])
    log(f"📂 讀取原始資料：{latest.name}（{len(data)} 筆）")
    return data


def save_json(result: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = OUTPUT_DIR / f"prospects_scored_{ts}.json"
    payload = {
        "generated_at": datetime.now().isoformat(),
        "status": "scored",
        "next_step": "messaging",
        "統計": {
            "總計": sum(len(v) for v in result.values()),
            "高潛力": len(result["高潛力名單"]),
            "中潛力": len(result["中潛力名單"]),
            "低潛力": len(result["低潛力名單"]),
        },
        **result,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    log(f"✅ 評分結果 → {path}")
    return path


# ============================================================
# 🚀 主程式
# ============================================================

def main():
    log("=" * 50)
    log("🚀 評分Agent 啟動")

    prospects = load_latest_raw()
    if not prospects:
        return

    log(f"📋 開始評分：{len(prospects)} 筆")
    result = score_all(prospects)
    path = save_json(result)

    log(f"🏁 評分完成 → {path}")
    log("=" * 50)
    return str(path)


if __name__ == "__main__":
    main()
