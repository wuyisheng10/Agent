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
# 🤖 五部分總結（Claude CLI）
# ============================================================

SUMMARY_PROMPT_TPL = """你是安麗事業「群雁團隊」的培訓記錄整理助理。

【群雁團隊文化核心】
群雁精神源自大雁南飛的智慧：
- 互助共飛：夥伴輪流領頭，分擔壓力，相互支援
- 感恩領導：感謝每一位帶領過自己的領導人與夥伴
- 分享傳承：將所學分享給下一位，讓團隊一起成長
- 積極正向：用鼓勵代替批評，用行動代替抱怨
- 堅持夢想：不論遇到什麼困難，都朝著夢想持續前進
- 榮耀歸團隊：個人的成功是團隊共同努力的結果

請將以下會議逐字稿，以群雁文化精神整理成五個部分，以純JSON格式回覆（不加markdown）：

逐字稿：
{transcript}

回覆格式：
{{
  "感恩": "以群雁感恩精神，感謝本次會議中的人事物（100字內）",
  "悟到": "從群雁互助角度，本次會議的領悟與洞見（150字內）",
  "學到": "可以傳承給夥伴的具體知識或技巧（150字內）",
  "做到": "承諾落實的具體行動，為團隊做出貢獻（100字內）",
  "目標": "個人與團隊共同前進的短中長期目標（100字內）"
}}"""

def summarize_with_claude(transcript: str) -> dict:
    """用 Claude CLI 產生五部分總結（temp file 避免 Windows stdin 中文編碼問題）"""
    import tempfile
    prompt = SUMMARY_PROMPT_TPL.format(transcript=transcript[:3000])
    log("使用 Claude CLI 整理五部分總結...")
    tmp_path = None
    try:
        # 寫入 UTF-8 temp 檔，繞過 Windows cmd stdin 編碼限制
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as f:
            f.write(prompt)
            tmp_path = f.name

        # PowerShell 以 UTF-8 讀檔後 pipe 給 claude，避免 cmd cp950 編碼問題
        ps_cmd = (
            "$OutputEncoding = [Console]::InputEncoding = "
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
            f"Get-Content '{tmp_path}' -Encoding UTF8 -Raw | "
            "claude -p --output-format text"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, timeout=90
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(stderr or stdout)
        cleaned = re.sub(r"```json|```", "", stdout).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError(f"無法解析 JSON，原始輸出：{cleaned[:200]}")
        return json.loads(match.group())
    except Exception as e:
        log(f"Claude CLI 失敗：{e}，使用規則式摘要")
        return rule_based_summary(transcript)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

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
    """精簡版 LINE 訊息（約 300 字），完整內容見 HTML 網頁"""
    def trim(text: str, limit: int) -> str:
        text = (text or "").strip()
        return text[:limit] + "…" if len(text) > limit else text

    d = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
    url_line = f"\n🌐 {url}/summary/{date_str}" if url else ""
    return (
        f"📚 培訓記錄 {d}\n"
        f"🔑 {key}{url_line}\n"
        f"{'─'*20}\n"
        f"🙏 {trim(summary.get('感恩',''), 40)}\n"
        f"💡 {trim(summary.get('悟到',''), 50)}\n"
        f"📖 {trim(summary.get('學到',''), 50)}\n"
        f"✅ {trim(summary.get('做到',''), 40)}\n"
        f"🎯 {trim(summary.get('目標',''), 40)}\n"
        f"{'─'*20}\n"
        f"點連結查看完整記錄 ↑"
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

    # 整理五部分
    summary = summarize_with_claude(transcript)

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
