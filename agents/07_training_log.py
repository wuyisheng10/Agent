"""
Agent 7: 培訓課程學習記錄管理
File: C:/Users/user/claude AI_Agent/agents/07_training_log.py
功能：
  1. 接收圖片 + 逐字稿 → 以日期歸檔
  2. 同一天已整理過則略過
  3. 整理逐字稿為五部分總結（感恩/悟到/學到/做到/目標）
  4. 儲存並回傳 Key（格式：MTG-YYYYMMDD）
  5. 輸入 Key → 取出總結回傳
"""

import os
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

BASE_DIR      = Path(r"C:\Users\user\claude AI_Agent")
TRAINING_DIR  = BASE_DIR / "output" / "training"
INDEX_FILE    = TRAINING_DIR / "training_index.json"
LOG_FILE      = BASE_DIR / "logs" / "agent_log.txt"

# ============================================================
# 📁 目錄與索引管理
# ============================================================

def ensure_dirs():
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

def load_index() -> dict:
    """key → 日期資料夾對應"""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_index(index: dict):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

def get_today_key() -> str:
    return f"MTG-{datetime.now().strftime('%Y%m%d')}"

def get_date_dir(date_str: str) -> Path:
    """date_str: YYYYMMDD"""
    return TRAINING_DIR / date_str

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [TRAINING] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# 📅 日期重複檢查
# ============================================================

def already_processed(date_str: str) -> bool:
    """當天是否已整理過"""
    key = f"MTG-{date_str}"
    index = load_index()
    if key not in index:
        return False
    summary_path = get_date_dir(date_str) / "summary.json"
    return summary_path.exists()


# ============================================================
# 💾 歸檔原始資料
# ============================================================

def archive_transcript(transcript: str, date_str: str = None) -> Path:
    """儲存逐字稿到日期資料夾"""
    ensure_dirs()
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")
    date_dir = get_date_dir(date_str)
    date_dir.mkdir(parents=True, exist_ok=True)

    path = date_dir / "transcript.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(transcript)
    log(f"逐字稿已歸檔：{path}")
    return path

def archive_image(image_data: bytes, filename: str, date_str: str = None) -> Path:
    """儲存圖片到日期資料夾"""
    ensure_dirs()
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")
    img_dir = get_date_dir(date_str) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    path = img_dir / filename
    with open(path, "wb") as f:
        f.write(image_data)
    log(f"圖片已歸檔：{path}")
    return path


# ============================================================
# 🤖 五部分總結（Codex CLI 主力）
# ============================================================

SUMMARY_PROMPT_TPL = """你是安麗事業「群雁團隊」培訓記錄整理師。

【群雁團隊文化】互助共飛｜感恩領導｜分享傳承｜積極正向｜堅持夢想｜榮耀歸團隊

【任務】閱讀以下培訓逐字稿，以群雁文化精神，整理為五個面向的學習總結。

【逐字稿】
{transcript}

【嚴格輸出規則】
1. 只輸出一個 JSON 物件，不加任何說明、標題、markdown
2. 每個欄位 50-100 字，用第一人稱書寫
3. 感恩：感謝老師、領導人或分享夥伴的具體貢獻
4. 悟到：最深刻的體會或啟發（連結群雁精神）
5. 學到：可立即傳承給夥伴的知識或技巧
6. 做到：今天就執行的一個具體承諾行動
7. 目標：本週可衡量的具體目標

{{"感恩":"...","悟到":"...","學到":"...","做到":"...","目標":"..."}}"""

def _run_cli_with_prompt(cli_cmd: str, prompt: str, timeout: int = 90) -> str:
    """共用：將 prompt 寫入 temp file，用 PowerShell UTF-8 pipe 給指定 CLI"""
    import tempfile
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as f:
            f.write(prompt)
            tmp_path = f.name
        ps_cmd = (
            "$OutputEncoding = [Console]::InputEncoding = "
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            f"Get-Content '{tmp_path}' -Encoding UTF8 -Raw | {cli_cmd}"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=timeout
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(stderr or stdout)
        return stdout
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

def _parse_json_output(raw: str) -> dict:
    """從 CLI 輸出中解析 JSON 物件"""
    cleaned = re.sub(r"```json|```", "", raw).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"無法解析 JSON：{cleaned[:200]}")
    return json.loads(match.group())

def summarize_with_codex(transcript: str) -> dict:
    """【主力】Codex CLI 整理五部分總結"""
    prompt = SUMMARY_PROMPT_TPL.format(transcript=transcript[:3000])
    log("使用 Codex CLI 整理五部分總結...")
    try:
        raw = _run_cli_with_prompt("codex -q", prompt, timeout=90)
        return _parse_json_output(raw)
    except Exception as e:
        log(f"Codex CLI 失敗：{e}")
        raise

def summarize_with_claude(transcript: str) -> dict:
    """【備援】Claude CLI 整理五部分總結"""
    prompt = SUMMARY_PROMPT_TPL.format(transcript=transcript[:3000])
    log("使用 Claude CLI 整理五部分總結（備援）...")
    try:
        raw = _run_cli_with_prompt("claude -p --output-format text", prompt, timeout=90)
        return _parse_json_output(raw)
    except Exception as e:
        log(f"Claude CLI 失敗：{e}")
        raise

def rule_based_summary(transcript: str) -> dict:
    """備援：規則式五部分摘要（零 API）"""
    lines = [l.strip() for l in transcript.splitlines() if l.strip()]
    total = len(lines)
    return {
        "感恩":  "感謝今日的培訓機會與夥伴們的分享。",
        "悟到":  "。".join(lines[:3]) if total >= 3 else transcript[:100],
        "學到":  "。".join(lines[3:6]) if total >= 6 else transcript[100:250],
        "做到":  "。".join(lines[6:8]) if total >= 8 else transcript[250:350],
        "目標":  lines[-1] if lines else "持續學習，落實行動。",
    }


# ============================================================
# 💾 儲存總結 & 建立 Key
# ============================================================

def save_summary(summary: dict, date_str: str, extra: dict = None) -> str:
    """儲存總結並回傳 Key"""
    key = f"MTG-{date_str}"
    date_dir = get_date_dir(date_str)
    date_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "key":        key,
        "date":       date_str,
        "created_at": datetime.now().isoformat(),
        "summary":    summary,
    }
    if extra:
        payload.update(extra)

    path = date_dir / "summary.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 同步產生 HTML 頁面
    html_path = date_dir / "summary.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(format_summary_html(key, summary, date_str))

    # 更新索引
    index = load_index()
    index[key] = date_str
    save_index(index)

    log(f"總結已儲存：{path}（Key: {key}）")
    return key


# ============================================================
# 📤 格式化總結訊息
# ============================================================

def format_summary_message(key: str, summary: dict, date_str: str, url: str = "") -> str:
    """精簡版 LINE 訊息（約 300 字）"""
    def trim(text: str, limit: int) -> str:
        text = (text or "").strip()
        return text[:limit] + "…" if len(text) > limit else text

    d = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
    return (
        f"📚 培訓記錄 {d}\n"
        f"🔑 {key}\n"
        f"{'─'*20}\n"
        f"🙏 {trim(summary.get('感恩',''), 40)}\n"
        f"💡 {trim(summary.get('悟到',''), 50)}\n"
        f"📖 {trim(summary.get('學到',''), 50)}\n"
        f"✅ {trim(summary.get('做到',''), 40)}\n"
        f"🎯 {trim(summary.get('目標',''), 40)}"
    )

def format_summary_html(key: str, summary: dict, date_str: str) -> str:
    """產生行動裝置友善的 HTML 總結頁面"""
    d = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
    def row(icon, title, content):
        return (
            f'<div class="card">'
            f'<div class="sec">{icon} {title}</div>'
            f'<div class="body">{content}</div>'
            f'</div>'
        )
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{key} 群雁培訓記錄</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:#f0f4ff;color:#333;padding:16px}}
  h1{{color:#1a73e8;font-size:1.2em;margin-bottom:4px}}
  .meta{{color:#666;font-size:.85em;margin-bottom:14px}}
  .key{{display:inline-block;background:#e8f0fe;color:#1a73e8;
        font-family:monospace;padding:4px 10px;border-radius:6px;font-size:.9em}}
  .card{{background:#fff;border-radius:12px;padding:16px;margin:10px 0;
         box-shadow:0 2px 8px rgba(0,0,0,.07)}}
  .sec{{font-weight:700;color:#444;margin-bottom:8px;font-size:1em}}
  .body{{line-height:1.7;color:#555;font-size:.95em}}
</style>
</head>
<body>
<h1>📚 群雁團隊培訓記錄</h1>
<p class="meta">📅 {d}</p>
<span class="key">🔑 {key}</span>
{row('🙏','感恩', summary.get('感恩',''))}
{row('💡','悟到', summary.get('悟到',''))}
{row('📖','學到', summary.get('學到',''))}
{row('✅','做到', summary.get('做到',''))}
{row('🎯','目標', summary.get('目標',''))}
</body>
</html>"""


# ============================================================
# 🔍 查詢 Key
# ============================================================

def get_summary_by_key(key: str) -> str | None:
    """輸入 Key 回傳格式化總結，找不到回傳 None"""
    key = key.strip().upper()
    index = load_index()
    if key not in index:
        return None
    date_str = index[key]
    path = get_date_dir(date_str) / "summary.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return format_summary_message(key, data["summary"], date_str)


# ============================================================
# 🚀 主流程：處理逐字稿
# ============================================================

def process_transcript(transcript: str, date_str: str = None, force: bool = False) -> tuple[str, str]:
    """
    處理逐字稿，回傳 (key, 格式化訊息)
    force=True：強制重新整理並覆蓋舊記錄
    force=False：若當天已整理過則直接回傳舊記錄
    """
    ensure_dirs()
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")

    key = f"MTG-{date_str}"

    # 已整理過且非強制 → 直接回傳
    if already_processed(date_str) and not force:
        log(f"{date_str} 已整理過，略過重複處理")
        msg = get_summary_by_key(key)
        return key, (msg or "已有整理記錄，輸入 Key 查詢")

    if force:
        log(f"{date_str} 強制重新整理，覆蓋舊記錄")

    # 歸檔逐字稿
    archive_transcript(transcript, date_str)

    # 整理五部分：Codex → Claude → 規則式
    summary = None
    for fn, name in [(summarize_with_codex, "Codex"), (summarize_with_claude, "Claude")]:
        try:
            summary = fn(transcript)
            log(f"{name} CLI 整理成功")
            break
        except Exception:
            log(f"{name} CLI 失敗，嘗試下一個...")
    if summary is None:
        log("所有 CLI 失敗，使用規則式摘要")
        summary = rule_based_summary(transcript)

    # 儲存
    key = save_summary(summary, date_str)
    msg = format_summary_message(key, summary, date_str)

    return key, msg


if __name__ == "__main__":
    # 測試用
    test_transcript = """
    今天非常感謝Linda分享她的成功故事，讓我們看到堅持的力量。
    我悟到做生意最重要的是心態，要用服務的心去接觸每一位朋友。
    今天學到了如何用三步驟介紹產品：先分享故事、再說產品、最後邀約體驗。
    我已經開始每天聯繫三位朋友分享健康理念，並且設立了個人LINE群組。
    目標是本月新增五位體驗客戶，下季晉升至Direct。
    """
    key, msg = process_transcript(test_transcript)
    print(f"\nKey: {key}")
    print(msg)
