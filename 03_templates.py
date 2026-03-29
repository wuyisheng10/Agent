"""
Agent 3: Message Template Generator
File: C:/Users/user/claude AI_Agent/agents/03_templates.py
Input: C:/Users/user/claude AI_Agent/output/prospects_scored/*.json
Output: C:/Users/user/claude AI_Agent/output/messages/YYYYMMDD_HHMM.json
"""

import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
INPUT_DIR = BASE_DIR / "output" / "prospects_scored"
OUTPUT_DIR = BASE_DIR / "output" / "messages"
LOG_FILE = BASE_DIR / "logs" / "agent_log.txt"

client = Anthropic()


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [TEMPLATE] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        safe_line = line.encode("cp950", errors="replace").decode("cp950")
        print(safe_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 📱 話術模板庫（Day1 / Day3 / Day7）
# ============================================================

TEMPLATES = {
    "上班族副業": {
        "Day1": "嗨 {姓名}！\n\n看到你分享的內容，感覺你最近也在找好副業 😊\n我自己做了一年多，利用下班時間，上個月額外多了 8,000-15,000 的收入。\n不是要你馬上決定什麼，就想聊聊我的方式，你這週有空10分鐘嗎？☕",
        "Day3": "嗨 {姓名}，再打擾一下！\n\n我們團隊一個夥伴本來跟你一樣在找副業，做了3個月後完全不一樣了。\n我可以把他的經驗分享傳給你參考嗎？😊",
        "Day7": "{姓名} 你好，最後一次打擾 🙏\n\n我們下週有個線上分享會，30分鐘，不喜歡沒關係。\n你有興趣來聽聽嗎？",
    },
    "全職媽媽": {
        "Day1": "嗨 {姓名}！\n\n我看到你最近分享家庭與生活的內容，感覺你很重視時間自由。\n我接觸的一個方式滿適合想兼顧家庭又想增加收入的人，如果你願意，我可以簡單跟你分享看看。",
        "Day3": "嗨 {姓名}！\n\n想到你之前提過生活安排很滿，我很能理解 😊\n我認識一位媽媽也是從每天利用2小時開始，慢慢做出穩定收入。\n如果你想，我可以把她的故事整理給你參考。",
        "Day7": "{姓名} 你好！\n\n如果你最近還在找能兼顧家庭的方式，我這邊剛好有一場很適合新手的線上分享。\n要不要我把資訊傳給你看看？",
    },
    "健康意識族群": {
        "Day1": "嗨 {姓名}！\n\n看到你平常很關注健康和生活品質，我覺得你對這類主題應該會有興趣。\n我最近接觸到一個結合健康分享和收入機會的模式，很多人都是先從了解開始。\n如果你願意，我可以跟你分享3分鐘重點，不會有壓力。",
        "Day3": "{姓名} 你好！\n\n前幾天有想到你，因為最近看到不少原本重視健康的人，也開始把這件事變成額外收入來源。\n如果你想知道怎麼開始，我可以簡單整理給你。",
        "Day7": "嗨 {姓名}！\n\n如果你對健康主題本來就有興趣，或許你也會想了解這個能分享給身邊朋友的方式。\n有空我可以傳你一份簡單介紹，讓你自己看看是否適合。",
    },
    "社群達人": {
        "Day1": "嗨 {姓名}！\n\n看得出來你平常很會經營內容，也很懂得和人互動。\n我最近接觸的一個機會，滿適合本來就喜歡分享、經營社群的人。\n不是要你立刻做決定，我只是覺得你可能會有興趣了解一下。",
        "Day3": "{姓名} 你好！\n\n想到你之前分享的內容，我覺得你的影響力其實很有價值。\n如果能把這份能力轉成另一種收入來源，也許會是個不錯的方向。",
        "Day7": "嗨 {姓名}！\n\n如果你還願意看看不同的可能性，我可以傳一個很短的介紹給你。\n看完再決定有沒有興趣就好，不會有壓力 🙂",
    },
    "創業斜槓族": {
        "Day1": "{姓名} 你好！\n\n我看到你最近也在思考多元收入的可能，感覺你很有行動力。\n我想跟你分享一個我自己正在做的模式，很多人都是先當作副業開始。\n如果你有興趣，我可以用最簡單的方式說明，不會耽誤你太多時間。",
        "Day3": "嗨 {姓名}！\n\n想到你前幾天說對新機會有興趣，我就想起一個很適合斜槓發展的模式。\n如果你願意，我可以整理成一頁重點給你，不會太複雜。",
        "Day7": "{姓名} 最後跟你打個招呼。\n\n如果你最近還在看新的收入機會，這個方式也許值得你花幾分鐘了解一下。\n如果想看，我再把資訊傳給你。",
    },
}


# ============================================================
# 🤖 AI 個人化生成
# ============================================================

def build_personalize_prompt(prospect: dict, template: str, day: str) -> str:
    return f"""
請根據這位潛在客戶的資料，微調以下邀約訊息，讓它更個人化、自然。
只輸出最終訊息，不要加任何說明。

客戶資料：
- 需求分析：{prospect.get('需求分析', '')}
- 注意事項：{prospect.get('注意事項', '')}
- 來源平台：{prospect.get('來源', '')}

原始模板（{day}）：
{template}

要求：
1. 保持輕鬆親切的語氣
2. 不要直接提安麗、直銷、傳銷
3. 長度維持在100-150字
4. 保留原本的 emoji 風格
"""


def run_gemini_cli(prompt_text: str) -> str:
    log("  使用 Gemini CLI 個人化訊息")
    result = subprocess.run(
        ["cmd", "/c", "gemini", "--prompt", prompt_text],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "gemini CLI 回傳非零"
        raise RuntimeError(err)
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("gemini CLI 未回傳內容")
    log("  Gemini CLI 個人化完成")
    return text


def run_claude_cli(prompt_text: str) -> str:
    log("  使用 Claude CLI 個人化訊息")
    result = subprocess.run(
        ["cmd", "/c", "claude", "-p", "--output-format", "text"],
        input=prompt_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "claude CLI 回傳非零"
        raise RuntimeError(err)
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("claude CLI 未回傳內容")
    log("  Claude CLI 個人化完成")
    return text


def run_claude_sdk(prompt_text: str) -> str:
    log("  使用 Claude SDK 個人化訊息")
    r = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt_text}],
    )
    text = r.content[0].text.strip()
    if not text:
        raise RuntimeError("Claude SDK 未回傳內容")
    log("  Claude SDK 個人化完成")
    return text


def run_codex_cli(prompt_text: str) -> str:
    response_path = None
    try:
        log("  使用 Codex CLI 個人化訊息")
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".txt",
            delete=False,
            dir=str(BASE_DIR / "logs"),
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
                "-",
            ],
            input=prompt_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=90,
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
        if not output_text:
            raise RuntimeError("codex CLI 未回傳內容")
        log("  Codex CLI 個人化完成")
        return output_text
    finally:
        if response_path and os.path.exists(response_path):
            try:
                os.unlink(response_path)
            except:
                pass


def fallback_template(prospect: dict, template: str) -> str:
    return template.replace("{姓名}", prospect.get("姓名", "您好"))


def ai_personalize(prospect: dict, template: str, day: str) -> str:
    prompt_text = build_personalize_prompt(prospect, template, day)

    try:
        return run_gemini_cli(prompt_text)
    except Exception as gemini_error:
        log(f"  Gemini CLI 個人化失敗：{gemini_error}")

    try:
        return run_claude_cli(prompt_text)
    except Exception as claude_cli_error:
        log(f"  Claude CLI 個人化失敗：{claude_cli_error}")

    try:
        return run_claude_sdk(prompt_text)
    except Exception as claude_sdk_error:
        log(f"  Claude SDK 個人化失敗：{claude_sdk_error}")

    try:
        log("  Gemini / Claude 不可用，改用 Codex CLI 個人化")
        return run_codex_cli(prompt_text)
    except Exception as codex_error:
        log(f"  Codex CLI 個人化失敗：{codex_error}")
        return fallback_template(prospect, template)


# ============================================================
# 📅 跟進時程計算
# ============================================================

def calc_schedule(base_date: datetime = None) -> dict:
    if not base_date:
        base_date = datetime.now()
    return {
        "Day1": base_date.strftime("%Y-%m-%d"),
        "Day3": (base_date + timedelta(days=3)).strftime("%Y-%m-%d"),
        "Day7": (base_date + timedelta(days=7)).strftime("%Y-%m-%d"),
        "Day14": (base_date + timedelta(days=14)).strftime("%Y-%m-%d"),
    }


# ============================================================
# ✉️ 生成訊息
# ============================================================

def generate_messages(high_prospects: list) -> list:
    results = []
    for i, p in enumerate(high_prospects, 1):
        log(f"  [{i}/{len(high_prospects)}] 生成訊息：{p.get('標題', '')[:30]}")

        talk_type = p.get("話術類型", "上班族副業")
        tpls = TEMPLATES.get(talk_type, TEMPLATES["上班族副業"])

        messages = {}
        for day, raw_tpl in tpls.items():
            personalized = ai_personalize(p, raw_tpl, day)
            messages[day] = personalized

        results.append(
            {
                "id": i,
                "來源": p.get("來源", ""),
                "標題": p.get("標題", ""),
                "連結": p.get("連結", ""),
                "最終分數": p.get("最終分數", 0),
                "話術類型": talk_type,
                "需求分析": p.get("需求分析", ""),
                "跟進時程": calc_schedule(),
                "訊息": messages,
                "狀態": "待發送",
                "已發送日期": None,
                "回覆狀態": "未回覆",
            }
        )

    return results


# ============================================================
# 💾 儲存
# ============================================================

def load_latest_scored() -> list:
    files = sorted(INPUT_DIR.glob("prospects_scored_*.json"))
    if not files:
        log("⚠️ 找不到評分結果，請先執行 02_scoring.py")
        return []
    latest = files[-1]
    with open(latest, encoding="utf-8") as f:
        high_list = json.load(f).get("高潛力名單", [])
    log(f"📂 讀取評分結果：{latest.name}")
    if not high_list:
        log("⚠️ 高潛力名單為 0 人，本次不產生 messages JSON")
    return high_list


def save_json(data: list) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = OUTPUT_DIR / f"messages_{ts}.json"
    payload = {
        "generated_at": datetime.now().isoformat(),
        "status": "ready",
        "next_step": "line_bot",
        "total": len(data),
        "messages": data,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    log(f"✅ 訊息結果 → {path}")
    return path


# ============================================================
# 🚀 主程式
# ============================================================

def main():
    log("=" * 50)
    log("🚀 邀約訊息Agent 啟動")

    high_list = load_latest_scored()
    if not high_list:
        return

    log(f"📋 高潛力名單：{len(high_list)} 人")
    messages = generate_messages(high_list)
    path = save_json(messages)

    log(f"🏁 訊息生成完成 → {path}")
    log("=" * 50)
    return str(path)


if __name__ == "__main__":
    main()
