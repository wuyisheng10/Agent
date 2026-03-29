import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, date
from hashlib import md5
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=r"C:\Users\user\claude AI_Agent\.env")

BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
CAL_DIR = BASE_DIR / "output" / "calendar"
IMG_DIR = CAL_DIR / "images"
DB_FILE = CAL_DIR / "calendar_events.json"
LOG_FILE = BASE_DIR / "logs" / "calendar_log.txt"

IMAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "is_calendar": {"type": "boolean"},
        "title": {"type": "string"},
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "title": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["date", "time", "title", "note"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["is_calendar", "title", "events"],
    "additionalProperties": False,
}


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [CALENDAR] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def ensure_dirs():
    IMG_DIR.mkdir(parents=True, exist_ok=True)


def load_events() -> list[dict]:
    ensure_dirs()
    if DB_FILE.exists():
        with open(DB_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_events(events: list[dict]):
    ensure_dirs()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def _resolve_codex_cli() -> list[str]:
    appdata = Path(os.getenv("APPDATA", r"C:\Users\user\AppData\Roaming"))
    node_exe = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    script = appdata / "npm" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
    return [node_exe, str(script)]


def _run_cli(args: list[str], timeout: int = 120,
             output_path: str | None = None,
             input_text: str | None = None) -> str:
    result = subprocess.run(
        args,
        input=input_text,
        capture_output=True,
        timeout=timeout,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        raise RuntimeError(stderr or stdout or f"CLI exited with {result.returncode}")
    if output_path and os.path.exists(output_path):
        with open(output_path, encoding="utf-8") as f:
            saved = f.read().strip()
        if saved:
            return saved
    return stdout


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        decoder = json.JSONDecoder()
        for idx, ch in enumerate(cleaned):
            if ch != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(cleaned[idx:])
            except Exception:
                continue
            if isinstance(parsed, dict):
                return parsed
        raise ValueError(f"無法解析 JSON：{cleaned[:300]}")


def _event_id(item: dict) -> str:
    base = f"{item['date']}|{item.get('time', '')}|{item['title']}"
    return "EVT-" + md5(base.encode("utf-8")).hexdigest()[:10].upper()


def _normalize_date(raw: str) -> str:
    raw = (raw or "").strip().replace("/", "-").replace(".", "-")
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw)
    if not m:
        raise ValueError("日期格式需為 YYYY-MM-DD")
    y, mo, d = map(int, m.groups())
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _normalize_time(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", raw)
    if not m:
        raise ValueError("時間格式需為 HH:MM")
    hh, mm = map(int, m.groups())
    return f"{hh:02d}:{mm:02d}"


def _event_sort_key(item: dict):
    return (
        item.get("date", "9999-12-31"),
        item.get("time") or "99:99",
        item.get("title", ""),
    )


def upcoming_events(today_str: str | None = None) -> list[dict]:
    today_str = today_str or date.today().isoformat()
    events = [e for e in load_events() if e.get("date", "") >= today_str]
    return sorted(events, key=_event_sort_key)


def events_between(date_from: str | None = None, date_to: str | None = None) -> list[dict]:
    events = load_events()
    if date_from:
        date_from = _normalize_date(date_from)
        events = [e for e in events if e.get("date", "") >= date_from]
    if date_to:
        date_to = _normalize_date(date_to)
        events = [e for e in events if e.get("date", "") <= date_to]
    return sorted(events, key=_event_sort_key)


def past_events(today_str: str | None = None) -> list[dict]:
    today_str = today_str or date.today().isoformat()
    events = [e for e in load_events() if e.get("date", "") < today_str]
    return sorted(events, key=_event_sort_key, reverse=True)


def format_events(events: list[dict], limit: int = 12, title: str = "今天之後的行事曆：") -> str:
    if not events:
        return f"{title}\n沒有符合條件的行事曆。"
    lines = [title]
    for item in events[:limit]:
        when = item["date"] + (f" {item['time']}" if item.get("time") else "")
        note = f"｜{item['note']}" if item.get("note") else ""
        lines.append(f"- {when}｜{item['title']}{note}")
    if len(events) > limit:
        lines.append(f"……其餘 {len(events) - limit} 筆可再查詢")
    return "\n".join(lines)


def _upsert_events(items: list[dict], source: str) -> list[dict]:
    events = load_events()
    by_id = {e["id"]: e for e in events}
    saved = []
    for item in items:
        normalized = {
            "date": _normalize_date(item.get("date", "")),
            "time": _normalize_time(item.get("time", "")),
            "title": (item.get("title", "") or "").strip(),
            "note": (item.get("note", "") or "").strip(),
        }
        if not normalized["title"]:
            continue
        normalized["id"] = _event_id(normalized)
        normalized["source"] = source
        normalized["updated_at"] = datetime.now().isoformat()
        if normalized["id"] not in by_id:
            normalized["created_at"] = normalized["updated_at"]
        else:
            normalized["created_at"] = by_id[normalized["id"]].get("created_at", normalized["updated_at"])
        by_id[normalized["id"]] = normalized
        saved.append(normalized)
    merged = sorted(by_id.values(), key=_event_sort_key)
    save_events(merged)
    return saved


def process_calendar_image(image_data: bytes, message_id: str) -> dict:
    ensure_dirs()
    image_path = IMG_DIR / f"calendar_{message_id}.jpg"
    with open(image_path, "wb") as f:
        f.write(image_data)

    schema_path = None
    output_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as f:
            json.dump(IMAGE_SCHEMA, f, ensure_ascii=False)
            schema_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
            output_path = f.name

        today_str = date.today().isoformat()
        prompt = (
            "請判斷這張圖片是不是行事曆、課表、活動表、月曆、時程表或會議排程圖。"
            "如果不是，回傳 is_calendar=false。"
            "如果是，請只整理今天之後的活動。"
            f"今天日期是 {today_str}。"
            "輸出 JSON：is_calendar, title, events。"
            "events 每筆都要有 date(YYYY-MM-DD), time(HH:MM 或空字串), title, note。"
        )
        raw = _run_cli(
            [
                *_resolve_codex_cli(),
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
                "-i",
                str(image_path),
                "-",
            ],
            timeout=120,
            input_text=prompt,
            output_path=output_path,
        )
        parsed = _parse_json(raw)
        if not parsed.get("is_calendar"):
            return {"is_calendar": False, "message": "這張圖片已存檔，但判定不是行事曆。"}

        saved = _upsert_events(parsed.get("events", []), source=f"image:{image_path.name}")
        upcoming = upcoming_events()
        return {
            "is_calendar": True,
            "saved_count": len(saved),
            "message": (
                f"已整理行事曆圖片：{parsed.get('title', '').strip() or '未命名行事曆'}\n"
                f"新增/更新 {len(saved)} 筆。\n"
                f"{format_events(upcoming)}\n"
                "可用：查詢行事曆 / 新增行事曆 / 修改行事曆 / 刪除行事曆"
            ).strip(),
        }
    finally:
        for path in (schema_path, output_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass


def query_calendar(command: str) -> str:
    msg = command.strip()
    if msg == "查詢過往行事曆":
        return format_events(
            past_events(),
            title="今天之前的行事曆：",
        )

    m = re.fullmatch(r"查詢行事曆\s+(\d{4}-\d{2}-\d{2})\s+到\s+(\d{4}-\d{2}-\d{2})", msg)
    if m:
        date_from, date_to = m.groups()
        return format_events(
            events_between(date_from, date_to),
            title=f"{date_from} 到 {date_to} 的行事曆：",
        )

    m = re.fullmatch(r"查詢行事曆(?:\s+(\d{4}-\d{2}-\d{2}))?", msg)
    if m:
        date_from = m.group(1)
        if date_from:
            return format_events(
                events_between(date_from, None),
                title=f"{date_from} 之後的行事曆：",
            )
        return format_events(upcoming_events(), title="今天之後的行事曆：")

    if msg == "查詢全部行事曆":
        return format_events(
            events_between(),
            title="全部行事曆：",
        )

    if msg == "行事曆":
        return format_events(upcoming_events(), title="今天之後的行事曆：")
    return ""


def add_calendar(command: str) -> str:
    m = re.fullmatch(r"新增行事曆\s+(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}:\d{2}))?\s+(.+?)(?:\s*\|\s*(.+))?", command.strip())
    if not m:
        return "格式：新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註"
    item = {
        "date": m.group(1),
        "time": m.group(2) or "",
        "title": m.group(3).strip(),
        "note": (m.group(4) or "").strip(),
    }
    saved = _upsert_events([item], source="manual:add")[0]
    return f"已新增：{saved['id']}｜{saved['date']} {saved.get('time','').strip()}｜{saved['title']}"


def update_calendar(command: str) -> str:
    m = re.fullmatch(r"修改行事曆\s+(EVT-[A-Z0-9]+)\s+(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}:\d{2}))?\s+(.+?)(?:\s*\|\s*(.+))?", command.strip())
    if not m:
        return "格式：修改行事曆 EVT-xxxx YYYY-MM-DD [HH:MM] 標題 | 備註"
    event_id = m.group(1)
    events = load_events()
    target = next((e for e in events if e["id"] == event_id), None)
    if not target:
        return f"找不到行事曆項目：{event_id}"
    target.update({
        "date": _normalize_date(m.group(2)),
        "time": _normalize_time(m.group(3) or ""),
        "title": m.group(4).strip(),
        "note": (m.group(5) or "").strip(),
        "updated_at": datetime.now().isoformat(),
        "source": "manual:update",
    })
    save_events(sorted(events, key=_event_sort_key))
    return f"已修改：{target['id']}｜{target['date']} {target.get('time','').strip()}｜{target['title']}"


def delete_calendar(command: str) -> str:
    m = re.fullmatch(r"刪除行事曆\s+(EVT-[A-Z0-9]+)", command.strip())
    if not m:
        return "格式：刪除行事曆 EVT-xxxx"
    event_id = m.group(1)
    events = load_events()
    remaining = [e for e in events if e["id"] != event_id]
    if len(remaining) == len(events):
        return f"找不到行事曆項目：{event_id}"
    save_events(sorted(remaining, key=_event_sort_key))
    return f"已刪除：{event_id}"


def handle_calendar_command(command: str) -> str:
    msg = command.strip()
    if msg.startswith("新增行事曆"):
        return add_calendar(msg)
    if msg.startswith("修改行事曆"):
        return update_calendar(msg)
    if msg.startswith("刪除行事曆"):
        return delete_calendar(msg)
    if msg == "行事曆" or msg.startswith("查詢行事曆"):
        return query_calendar(msg)
    return ""
