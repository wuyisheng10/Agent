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
import html
import shutil
import subprocess
import tempfile
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

SUMMARY_PROMPT_TPL = """你是安麗事業「群雁國際團隊」的會議記錄整理師。

【群雁團隊精神】
大雁南飛時輪流領頭、彼此鼓勵、一起飛得更遠。
群雁團隊以此為核心：
  ✦ 互助共飛   — 夥伴有難，主動支援，沒有人單打獨鬥
  ✦ 感恩領導   — 感謝每一位帶領、指引、陪伴過自己的人
  ✦ 分享傳承   — 把所學毫無保留地傳給下一位夥伴
  ✦ 積極正向   — 用鼓勵代替批評，用行動代替抱怨
  ✦ 堅持夢想   — 不論遇到什麼挫折，都不放棄對夢想的承諾
  ✦ 榮耀歸團隊 — 個人成就是團隊共同耕耘的果實

【安麗事業背景】
安麗以「自由創業、幫助他人成功」為核心，強調產品體驗、人際關係經營、
系統化複製、持續自我成長，以及透過共同奮鬥實現家庭與財務自由的夢想。

【本次會議逐字稿】
{transcript}

【整理任務】
請以「群雁團隊成員」的第一人稱視角，將逐字稿整理為以下五個面向。
每個面向須自然融入群雁文化精神，不要生硬套詞，要像真實的心得感想。

  感恩 — 具體感謝本次會議中給予啟發、支持或帶領的老師/領導人/夥伴，說明感謝的原因
  悟到 — 本次最深的內心觸動或領悟，連結到自己的安麗事業或人生方向
  學到 — 可以馬上複製給夥伴的具體方法、技巧或觀念（要有可操作性）
  做到 — 會議結束後「今天」就要執行的一個具體承諾行動（不是計劃，是承諾）
  目標 — 受此次會議激勵後，本週內要達成的具體可衡量目標

【輸出格式】
只輸出一個 JSON 物件，不加任何說明、標題或 markdown。
這份內容會直接做成網頁完整版，所以每欄都要完整、具體、可獨立閱讀。
請寫成「像可直接分享的整理稿」的風格，而不是一整段散文。
每一欄都盡量用以下格式：
1. 先用阿拉伯數字分點，例如 1. 2. 3.
2. 每一點先有一句短標或結論句
3. 若有延伸說明，再換行補充 1 到 3 句
4. 若有細項，可用 • 開頭條列
5. 各點之間保留空行，讓網頁閱讀起來清楚，風格接近：
   1.
   每天先給自己正向的設定很重要
   出門前先把狀態調對，先相信今天會有好事發生。

   2.
   狀態比技巧更重要
   一個人有沒有目標、有沒有希望，別人一感受就知道。
   • 有目標
   • 有希望
   • 有行動

每欄至少 4 點，沒有 300 字限制；以完整呈現脈絡、例子、行動與目標為優先：
{{"感恩":"（完整內容）","悟到":"（完整內容）","學到":"（完整內容）","做到":"（完整內容）","目標":"（完整內容）"}}"""

SUMMARY_KEYS = (
    "\u611f\u6069",
    "\u609f\u5230",
    "\u5b78\u5230",
    "\u505a\u5230",
    "\u76ee\u6a19",
)

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {key: {"type": "string"} for key in SUMMARY_KEYS},
    "required": list(SUMMARY_KEYS),
    "additionalProperties": False,
}

MAX_TRANSCRIPT_FOR_SUMMARY = 12000


def _strip_cli_noise(raw: str) -> str:
    ansi = re.compile(r"\x1b\[[0-9;]*[mGKHF]")
    return ansi.sub("", (raw or "")).strip()


def _normalize_summary_dict(data: dict) -> dict:
    if all(key in data for key in SUMMARY_KEYS):
        return {key: str(data[key]).strip() for key in SUMMARY_KEYS}

    for value in data.values():
        if isinstance(value, dict):
            try:
                return _normalize_summary_dict(value)
            except ValueError:
                continue
        if isinstance(value, str) and "{" in value and "}" in value:
            try:
                return _parse_json_output(value)
            except Exception:
                continue

    raise ValueError("JSON 缺少必要欄位")


def _parse_json_output(raw: str) -> dict:
    """從 CLI 輸出中解析 JSON 物件"""
    cleaned = re.sub(r"```json|```", "", _strip_cli_noise(raw))
    decoder = json.JSONDecoder()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return _normalize_summary_dict(parsed)
    except Exception:
        pass

    for idx, ch in enumerate(cleaned):
        if ch != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(cleaned[idx:])
        except Exception:
            continue
        if isinstance(parsed, dict):
            try:
                return _normalize_summary_dict(parsed)
            except ValueError:
                continue

    raise ValueError(f"無法解析 JSON：{cleaned[:300]}")


def _run_cli(args: list[str], input_text: str | None = None,
             timeout: int = 120, output_path: str | None = None) -> str:
    result = subprocess.run(
        args,
        input=input_text,
        capture_output=True,
        timeout=timeout,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout = _strip_cli_noise(result.stdout)
    stderr = _strip_cli_noise(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(stderr or stdout or f"CLI exited with {result.returncode}")

    if output_path and os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            saved = _strip_cli_noise(f.read())
        if saved:
            return saved
    return stdout


def _resolve_npm_node_cli(script_rel: str) -> list[str]:
    appdata = Path(os.getenv("APPDATA", r"C:\Users\user\AppData\Roaming"))
    node_exe = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    script_path = appdata / "npm" / "node_modules" / Path(script_rel)
    return [node_exe, str(script_path)]


def _summary_prompt(transcript: str) -> str:
    return SUMMARY_PROMPT_TPL.format(
        transcript=transcript[:MAX_TRANSCRIPT_FOR_SUMMARY]
    )

def summarize_with_codex(transcript: str) -> dict:
    """
    【主力】Codex CLI — prompt 直接作為命令列引數（避免 shell/pipe 編碼問題）
    Windows npm 全域套件入口為 codex.cmd；自動偵測可用指令。
    """
    prompt = _summary_prompt(transcript)
    log("使用 Codex CLI 整理五部分總結...")
    exe = _resolve_npm_node_cli(r"@openai\codex\bin\codex.js")
    schema_path = None
    output_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(SUMMARY_SCHEMA, f, ensure_ascii=False)
            schema_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as f:
            output_path = f.name

        stdout = _run_cli(
            [
                *exe,
                "exec",
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--color",
                "never",
                "--output-schema",
                schema_path,
                "--output-last-message",
                output_path,
                prompt,
            ],
            output_path=output_path,
        )
        return _parse_json_output(stdout)
    except Exception as e:
        log(f"Codex CLI 失敗：{e}")
        raise
    finally:
        for path in (schema_path, output_path):
            if path:
                try:
                    os.unlink(path)
                except Exception:
                    pass

def summarize_with_gemini(transcript: str) -> dict:
    """【二級備援】Gemini CLI — 支援 --prompt 直接引數模式"""
    prompt = _summary_prompt(transcript)
    log("使用 Gemini CLI 整理五部分總結（二級備援）...")
    exe = _resolve_npm_node_cli(r"@google\gemini-cli\dist\index.js")
    try:
        stdout = _run_cli(
            [
                *exe,
                "--prompt",
                prompt,
                "--output-format",
                "json",
                "--approval-mode",
                "yolo",
            ]
        )
        return _parse_json_output(stdout)
    except Exception as e:
        log(f"Gemini CLI 失敗：{e}")
        raise

def summarize_with_claude(transcript: str) -> dict:
    """
    Claude CLI 非互動模式，直接要求輸出符合 JSON Schema 的結果。
    """
    log("使用 Claude CLI 整理五部分總結...")
    exe = _resolve_npm_node_cli(r"@anthropic-ai\claude-code\cli.js")
    prompt = _summary_prompt(transcript)
    try:
        stdout = _run_cli(
            [
                *exe,
                "-p",
                "--output-format",
                "json",
                "--permission-mode",
                "dontAsk",
                "--json-schema",
                json.dumps(SUMMARY_SCHEMA, ensure_ascii=False),
                prompt,
            ]
        )
        return _parse_json_output(stdout)
    except Exception as e:
        log(f"Claude CLI 失敗：{e}")
        raise

def rule_based_summary(transcript: str) -> dict:
    """
    最終備援：從逐字稿直接截取內容，套入群雁文化框架。
    不呼叫任何 API / CLI，純文字處理。
    """
    lines = [l.strip() for l in transcript.splitlines() if len(l.strip()) > 5]
    n = len(lines)

    def pick(start_ratio: float, end_ratio: float, limit: int = 80) -> str:
        s = int(n * start_ratio)
        e = int(n * end_ratio)
        chunk = "，".join(lines[s:e]) if lines[s:e] else transcript[s*10:e*10]
        return chunk[:limit] + "…" if len(chunk) > limit else chunk

    opening  = pick(0.0,  0.15)   # 開場感恩語
    insight  = pick(0.15, 0.40)   # 中段啟發
    learning = pick(0.40, 0.65)   # 學習重點
    action   = pick(0.65, 0.85)   # 行動承諾
    closing  = pick(0.85, 1.0)    # 結語目標

    return {
        "感恩": (
            f"感謝今天的培訓夥伴及領導人的無私分享，"
            f"讓我有機會接收到寶貴的智慧。{opening}"
        )[:120],
        "悟到": (
            f"透過今天的會議，我深刻體會到群雁互助共飛的精神。"
            f"{insight}"
        )[:120],
        "學到": (
            f"今天學到可以立即傳承給夥伴的方法："
            f"{learning}"
        )[:120],
        "做到": (
            f"我承諾今天就執行：{action}"
            f"，不等明天，馬上行動。"
        )[:120],
        "目標": (
            f"受到今天的激勵，本週目標："
            f"{closing}"
            f"，堅持夢想、榮耀歸團隊。"
        )[:120],
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


def get_summary_url(date_str: str) -> str:
    base = os.getenv("NGROK_URL", "").strip().rstrip("/")
    if not base:
        return ""
    return f"{base}/summary/{date_str}"


def list_archived_images(date_str: str) -> list[str]:
    img_dir = get_date_dir(date_str) / "images"
    if not img_dir.exists():
        return []
    return sorted(
        [p.name for p in img_dir.iterdir() if p.is_file()],
        key=str.lower,
    )


# ============================================================
# 📤 格式化總結訊息
# ============================================================

def format_summary_message(key: str, summary: dict, date_str: str, url: str = "") -> str:
    """
    LINE 精簡版訊息。
    先產出完整五部分內容，再從完整內容壓成約 500 字的導讀。
    """
    def compress(text: str, limit: int = 24) -> str:
        text = (text or "").strip()
        for stop in ["。", "！", "？", "\n", ".", "!", "?"]:
            idx = text.find(stop)
            if 0 < idx < limit:
                return text[:idx + 1]
        return text[:limit] + "…" if len(text) > limit else text

    d = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
    msg = (
        f"📚 培訓記錄 {d}\n"
        f"🔑 {key}\n"
        f"{'─'*20}\n"
        f"🙏 感恩：{compress(summary.get('感恩',''))}\n"
        f"💡 悟到：{compress(summary.get('悟到',''))}\n"
        f"📖 學到：{compress(summary.get('學到',''))}\n"
        f"✅ 做到：{compress(summary.get('做到',''))}\n"
        f"🎯 目標：{compress(summary.get('目標',''))}\n"
        f"{'─'*20}\n"
        + (f"完整內容：{url}" if url else "點連結查看五部分完整內容 ↑")
    )
    return msg[:500] + "…" if len(msg) > 500 else msg


def _render_summary_html(content: str) -> str:
    lines = (content or "").splitlines()
    parts = []
    in_list = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append('<div class="gap"></div>')
            continue

        escaped = html.escape(stripped)
        if stripped.startswith("•"):
            if not in_list:
                parts.append('<ul class="bullet-list">')
                in_list = True
            parts.append(f"<li>{html.escape(stripped[1:].strip())}</li>")
            continue

        if in_list:
            parts.append("</ul>")
            in_list = False

        if re.match(r"^\d+\.$", stripped):
            parts.append(f'<div class="point-num">{escaped}</div>')
        elif re.match(r"^\d+\.\s*", stripped):
            parts.append(f'<div class="point-title">{escaped}</div>')
        else:
            parts.append(f'<p class="para">{escaped}</p>')

    if in_list:
        parts.append("</ul>")

    return "".join(parts)


def _render_image_gallery(date_str: str) -> str:
    images = list_archived_images(date_str)
    if not images:
        return ""

    cards = []
    for name in images:
        src = f"/summary/{date_str}/images/{name}"
        label = html.escape(name)
        cards.append(
            f'<a class="img-card" href="{src}" target="_blank" rel="noreferrer">'
            f'<img src="{src}" alt="{label}">'
            f'<div class="img-name">{label}</div>'
            f'</a>'
        )
    return (
        '<div class="card">'
        '<div class="sec">🖼️ 會議流程圖 / 圖片紀錄</div>'
        '<div class="gallery">'
        + "".join(cards) +
        '</div>'
        '</div>'
    )


def format_summary_html(key: str, summary: dict, date_str: str) -> str:
    """產生行動裝置友善的 HTML 總結頁面"""
    d = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
    def row(icon, title, content):
        return (
            f'<div class="card">'
            f'<div class="sec">{icon} {title}</div>'
            f'<div class="body">{_render_summary_html(content)}</div>'
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
  .body{{line-height:1.85;color:#555;font-size:.98em}}
  .point-num{{font-weight:800;color:#1a73e8;margin-top:10px}}
  .point-title{{font-weight:700;color:#222;margin:4px 0 6px}}
  .para{{margin:0 0 8px 0}}
  .gap{{height:8px}}
  .bullet-list{{margin:4px 0 10px 20px;padding:0}}
  .bullet-list li{{margin:4px 0}}
  .gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
  .img-card{{display:block;background:#f8fbff;border:1px solid #dbe7ff;border-radius:10px;
             overflow:hidden;text-decoration:none;color:#1f2d3d}}
  .img-card img{{display:block;width:100%;height:160px;object-fit:cover;background:#eef4ff}}
  .img-name{{padding:10px;font-size:.85em;word-break:break-all}}
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
{_render_image_gallery(date_str)}
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
    return format_summary_message(
        key,
        data["summary"],
        date_str,
        url=get_summary_url(date_str),
    )


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

    # 整理五部分：Claude → Codex → Gemini → 規則式
    summary = None
    for fn, name in [
        (summarize_with_claude, "Claude"),
        (summarize_with_codex,  "Codex"),
        (summarize_with_gemini, "Gemini"),
    ]:
        try:
            summary = fn(transcript)
            log(f"{name} CLI 整理成功")
            break
        except Exception as e:
            log(f"{name} CLI 失敗（{e}），嘗試下一個...")
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
