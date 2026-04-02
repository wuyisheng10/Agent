"""
課程會議邀約 Agent
File: agents/16_course_invite_agent.py
Function:
  1. 手動新增 / 查詢 / 刪除課程會議
  2. 從行事曆撈取接下來的課程相關活動
  3. 新增 / 查詢課程文宣
  4. 透過 Codex CLI 優化課程文宣
  5. 透過 Codex CLI 為「潛在家人」產生邀約文宣
  6. 透過 Codex CLI 為「跟進夥伴」產生邀約文宣

LINE 指令（前綴 小幫手）:
  新增課程會議 YYYY-MM-DD HH:MM 標題|地點|說明
  查詢課程會議
  刪除課程會議 COURSE-XXXX
  從行事曆加入課程 [關鍵字]          ← 把行事曆內符合的活動轉成課程會議
  新增課程文宣 標題|內文
  查詢課程文宣
  優化課程文宣 PROMO-XXXX
  邀約文宣 潛在家人 [姓名]           ← 不給姓名時產生通用邀約
  邀約文宣 跟進夥伴 [姓名]
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, date

import importlib.util as _ilu


def _load_prompt_manager():
    path = BASE_DIR / "agents" / "20_ai_prompt_manager.py"
    spec = _ilu.spec_from_file_location("ai_prompt_manager", str(path))
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
from hashlib import md5
from pathlib import Path

from dotenv import load_dotenv

try:
    from common_runtime import BASE_DIR
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR


def _resolve_codex_cli() -> list[str]:
    appdata = Path(os.getenv("APPDATA", r"C:\Users\user\AppData\Roaming"))
    node_exe = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    script = appdata / "npm" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
    return [node_exe, str(script)]


def _run_codex(prompt: str, timeout: int = 120) -> str:
    response_path = None
    try:
        logs_dir = BASE_DIR / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False, dir=str(logs_dir)
        ) as f:
            response_path = f.name

        result = subprocess.run(
            [
                *_resolve_codex_cli(),
                "exec",
                "--skip-git-repo-check",
                "--sandbox", "read-only",
                "--color", "never",
                "-C", str(BASE_DIR),
                "-o", response_path,
                "-",
            ],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"codex CLI 回傳非零 {result.returncode}")

        out = ""
        if response_path and os.path.exists(response_path):
            with open(response_path, encoding="utf-8", errors="replace") as f:
                out = f.read().strip()
        if not out:
            out = (result.stdout or "").strip()
        if out:
            return out
        raise RuntimeError("codex CLI 未回傳內容")
    finally:
        if response_path and os.path.exists(response_path):
            try:
                os.unlink(response_path)
            except Exception:
                pass

load_dotenv(dotenv_path=BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "output" / "csv_data"
MEETINGS_FILE = DATA_DIR / "course_meetings.json"
PROMOS_FILE = DATA_DIR / "course_promos.json"
INVITES_FILE = DATA_DIR / "course_invites.json"
LOG_FILE = BASE_DIR / "logs" / "course_invite_log.txt"

CAL_DB = BASE_DIR / "output" / "calendar" / "calendar_events.json"
PROSPECTS_CSV = DATA_DIR / "market_list.csv"
PARTNERS_JSON = BASE_DIR / "output" / "partners" / "partners.json"


# ============================================================
# Logging
# ============================================================

def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [COURSE] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp950", errors="replace").decode("cp950"))
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# Helpers
# ============================================================

def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Course Invites — Archive (course_invites.json)
# ============================================================

def _invite_key(meeting_id: str, name: str) -> str:
    return f"{meeting_id}__{name}"


def _load_invites() -> dict:
    _ensure_dir()
    if INVITES_FILE.exists():
        with open(INVITES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_invites(invites: dict):
    _ensure_dir()
    with open(INVITES_FILE, "w", encoding="utf-8") as f:
        json.dump(invites, f, ensure_ascii=False, indent=2)


def save_invite(meeting_id: str, name: str, role: str, content: str) -> None:
    invites = _load_invites()
    key = _invite_key(meeting_id, name)
    now = datetime.now().isoformat()
    if key in invites:
        invites[key]["content"] = content
        invites[key]["updated_at"] = now
    else:
        invites[key] = {
            "meeting_id": meeting_id,
            "name": name,
            "role": role,
            "content": content,
            "created_at": now,
            "updated_at": now,
        }
    _save_invites(invites)


def get_invite(meeting_id: str, name: str) -> dict | None:
    return _load_invites().get(_invite_key(meeting_id, name))


def update_invite(meeting_id: str, name: str, content: str) -> bool:
    invites = _load_invites()
    key = _invite_key(meeting_id, name)
    if key not in invites:
        return False
    invites[key]["content"] = content
    invites[key]["updated_at"] = datetime.now().isoformat()
    _save_invites(invites)
    return True


def list_upcoming_invites(today_only_after: bool = True) -> list[dict]:
    invites = _load_invites()
    meetings = {m["id"]: m for m in _load_meetings()}
    today = date.today().isoformat()
    rows = []
    for rec in invites.values():
        meeting = meetings.get(rec.get("meeting_id", ""))
        if not meeting:
            continue
        if today_only_after and meeting.get("date", "") < today:
            continue
        rows.append({
            **rec,
            "meeting": meeting,
        })
    rows.sort(key=lambda r: (r["meeting"].get("date", "9999-12-31"), r["meeting"].get("time") or "99:99", r.get("name", "")))
    return rows


def format_upcoming_invites() -> str:
    rows = list_upcoming_invites(today_only_after=True)
    if not rows:
        return "目前沒有今日之後已產生的會議邀約文宣。"
    lines = ["📨 今日之後已產生的會議邀約文宣："]
    for rec in rows:
        meeting = rec["meeting"]
        when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
        lines.append(
            f"- {meeting['id']}｜{rec.get('name','')}｜{meeting['title']}｜{when}"
        )
    lines.append("")
    lines.append("修改格式：")
    lines.append("修改已產生的今日之後會議邀約文宣 COURSE-XXXX | 姓名 | 新內容")
    return "\n".join(lines)


def _make_id(prefix: str, text: str) -> str:
    return prefix + md5(text.encode("utf-8")).hexdigest()[:8].upper()


def _normalize_date(raw: str) -> str:
    raw = (raw or "").strip().replace("/", "-")
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


# ============================================================
# Course Meetings — CRUD
# ============================================================

def _load_meetings() -> list[dict]:
    _ensure_dir()
    if MEETINGS_FILE.exists():
        with open(MEETINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_meetings(meetings: list[dict]):
    _ensure_dir()
    meetings_sorted = sorted(
        meetings,
        key=lambda e: (e.get("date", "9999-12-31"), e.get("time") or "99:99"),
    )
    with open(MEETINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(meetings_sorted, f, ensure_ascii=False, indent=2)


def add_meeting(title: str, date_str: str, time_str: str = "",
                location: str = "", description: str = "",
                speaker: str = "", speaker_bio: str = "",
                topics: str = "", topic_desc: str = "",
                source: str = "manual") -> dict:
    date_norm = _normalize_date(date_str)
    time_norm = _normalize_time(time_str)
    uid = _make_id("COURSE-", f"{date_norm}{time_norm}{title}")
    now = datetime.now().isoformat()
    meetings = _load_meetings()
    existing_ids = {m["id"] for m in meetings}
    item = {
        "id": uid,
        "title": title.strip(),
        "date": date_norm,
        "time": time_norm,
        "location": location.strip(),
        "description": description.strip(),
        "speaker": speaker.strip(),
        "speaker_bio": speaker_bio.strip(),
        "topics": topics.strip(),
        "topic_desc": topic_desc.strip(),
        "source": source,
        "created_at": now if uid not in existing_ids else next(
            (m["created_at"] for m in meetings if m["id"] == uid), now
        ),
        "updated_at": now,
    }
    by_id = {m["id"]: m for m in meetings}
    by_id[uid] = item
    _save_meetings(list(by_id.values()))
    return item


def list_meetings(upcoming_only: bool = True) -> list[dict]:
    meetings = _load_meetings()
    today = date.today().isoformat()
    if upcoming_only:
        meetings = [m for m in meetings if m.get("date", "") >= today]
    return meetings


def delete_meeting(meeting_id: str) -> str:
    meetings = _load_meetings()
    remaining = [m for m in meetings if m["id"] != meeting_id]
    if len(remaining) == len(meetings):
        return f"找不到課程會議：{meeting_id}"
    _save_meetings(remaining)
    return f"已刪除課程會議：{meeting_id}"


def update_meeting(meeting_id: str, fields: dict) -> str:
    """更新指定課程會議的欄位，fields 為 {欄位名: 新值} dict。"""
    meetings = _load_meetings()
    target = next((m for m in meetings if m["id"] == meeting_id), None)
    if target is None:
        return f"⚠️ 找不到課程會議：{meeting_id}"
    allowed = {"title", "date", "time", "location", "description",
               "speaker", "speaker_bio", "topics", "topic_desc"}
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k == "date":
            v = _normalize_date(v)
        elif k == "time":
            v = _normalize_time(v)
        target[k] = v.strip() if isinstance(v, str) else v
    target["updated_at"] = datetime.now().isoformat()
    _save_meetings(meetings)
    when = target["date"] + (f" {target['time']}" if target.get("time") else "")
    return (
        f"✅ 課程會議已更新\n"
        f"ID：{target['id']}\n"
        f"標題：{target['title']}\n"
        f"時間：{when}\n"
        f"地點：{target.get('location') or '（未填）'}\n"
        f"說明：{target.get('description') or '（未填）'}\n"
        f"演講貴賓：{target.get('speaker') or '（未填）'}\n"
        f"貴賓介紹：{target.get('speaker_bio') or '（未填）'}\n"
        f"課程主題：{target.get('topics') or '（未填）'}\n"
        f"主題介紹：{target.get('topic_desc') or '（未填）'}"
    )


def format_meetings(meetings: list[dict], title: str = "接下來的課程會議：") -> str:
    if not meetings:
        return f"{title}\n目前沒有課程會議資料。"
    lines = [title]
    for m in meetings:
        when = m["date"] + (f" {m['time']}" if m.get("time") else "")
        loc = f"｜📍{m['location']}" if m.get("location") else ""
        lines.append(f"🎓 {m['id']}｜{when}｜{m['title']}{loc}")
        if m.get("description"):
            lines.append(f"   說明：{m['description']}")
        if m.get("speaker"):
            lines.append(f"   🎤 演講貴賓：{m['speaker']}")
        if m.get("speaker_bio"):
            lines.append(f"      {m['speaker_bio']}")
        if m.get("topics"):
            lines.append(f"   📚 課程主題：{m['topics']}")
        if m.get("topic_desc"):
            lines.append(f"      {m['topic_desc']}")
    return "\n".join(lines)


# ============================================================
# Import from Calendar
# ============================================================

def import_from_calendar(keyword: str = "") -> str:
    if not CAL_DB.exists():
        return "⚠️ 找不到行事曆資料，請先上傳行事曆圖片或新增行事曆。"
    with open(CAL_DB, encoding="utf-8") as f:
        events = json.load(f)
    today = date.today().isoformat()
    upcoming = [e for e in events if e.get("date", "") >= today]
    if keyword:
        upcoming = [e for e in upcoming if keyword in e.get("title", "") or keyword in e.get("note", "")]
    if not upcoming:
        kw_hint = f"（關鍵字：{keyword}）" if keyword else ""
        return f"⚠️ 行事曆中沒有找到接下來的課程相關活動{kw_hint}。"
    added = []
    for e in upcoming:
        item = add_meeting(
            title=e["title"],
            date_str=e["date"],
            time_str=e.get("time", ""),
            description=e.get("note", ""),
            source="calendar",
        )
        added.append(item)
    lines = [f"✅ 已從行事曆匯入 {len(added)} 筆課程會議："]
    for item in added:
        when = item["date"] + (f" {item['time']}" if item.get("time") else "")
        lines.append(f"  {item['id']}｜{when}｜{item['title']}")
    return "\n".join(lines)


# ============================================================
# Course Promos — CRUD
# ============================================================

def _load_promos() -> list[dict]:
    _ensure_dir()
    if PROMOS_FILE.exists():
        with open(PROMOS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_promos(promos: list[dict]):
    _ensure_dir()
    with open(PROMOS_FILE, "w", encoding="utf-8") as f:
        json.dump(promos, f, ensure_ascii=False, indent=2)


def add_promo(title: str, content: str) -> dict:
    uid = _make_id("PROMO-", f"{title}{content[:30]}")
    now = datetime.now().isoformat()
    promos = _load_promos()
    by_id = {p["id"]: p for p in promos}
    item = {
        "id": uid,
        "title": title.strip(),
        "content": content.strip(),
        "optimized": "",
        "created_at": by_id[uid]["created_at"] if uid in by_id else now,
        "updated_at": now,
    }
    by_id[uid] = item
    _save_promos(list(by_id.values()))
    return item


def list_promos() -> list[dict]:
    return _load_promos()


def format_promos(promos: list[dict]) -> str:
    if not promos:
        return "目前沒有課程文宣資料。\n新增：小幫手 新增課程文宣 標題|內文"
    lines = ["📢 課程文宣清單："]
    for p in promos:
        lines.append(f"  {p['id']}｜{p['title']}")
    return "\n".join(lines)


def get_promo_detail(promo_id: str) -> dict | None:
    promos = _load_promos()
    return next((p for p in promos if p["id"] == promo_id), None)


# ============================================================
# Codex CLI: Optimize Promo
# ============================================================

def optimize_promo(promo_id: str) -> str:
    promo = get_promo_detail(promo_id)
    if not promo:
        return f"⚠️ 找不到文宣：{promo_id}"

    meetings = list_meetings()
    mtg_summary = format_meetings(meetings) if meetings else "（暫無排定的課程會議）"

    prompt = f"""你是一位擅長直銷事業推廣的文案高手。
請優化以下課程文宣，讓它更吸引人、更有行動力，保留核心訊息。
接下來的課程資訊：
{mtg_summary}

原始文宣標題：{promo['title']}
原始文宣內容：
{promo['content']}

優化要求：
- 開頭要有吸睛的一句話
- 條列課程重點（用 emoji）
- 結尾加入行動呼籲（報名、加入、詢問）
- 語氣輕鬆自然，不過度推銷
- 全文控制在 250 字以內
"""
    _log(f"優化文宣 {promo_id}...")
    optimized = _run_codex(prompt, timeout=90)

    promos = _load_promos()
    for p in promos:
        if p["id"] == promo_id:
            p["optimized"] = optimized
            p["updated_at"] = datetime.now().isoformat()
            break
    _save_promos(promos)

    return f"✅ 文宣已優化（{promo_id}）：\n\n{optimized}"


def apply_optimized_promo(promo_id: str) -> str:
    promos = _load_promos()
    for p in promos:
        if p["id"] == promo_id:
            optimized = (p.get("optimized") or "").strip()
            if not optimized:
                return f"⚠️ 文宣 {promo_id} 尚未有優化內容，請先執行：優化課程文宣 {promo_id}"
            p["content"] = optimized
            p["updated_at"] = datetime.now().isoformat()
            _save_promos(promos)
            return f"✅ 已將優化內容套用到課程文宣：{promo_id}"
    return f"⚠️ 找不到文宣：{promo_id}"


# ============================================================
# Codex CLI: Generate Invite — Prospect
# ============================================================

def _load_prospect_info(name: str) -> dict:
    import csv
    for fname in ("market_list.csv", "prospects.csv"):
        p = BASE_DIR / "output" / "csv_data" / fname
        if not p.exists():
            continue
        with open(p, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("姓名", "").strip() == name.strip():
                    return dict(row)
    return {}


def _load_partner_info(name: str) -> dict:
    if not PARTNERS_JSON.exists():
        return {}
    with open(PARTNERS_JSON, encoding="utf-8") as f:
        partners = json.load(f)
    for p in partners:
        if p.get("name", "").strip() == name.strip():
            return {
                "姓名": p.get("name", ""),
                "加入日期": p.get("created_at", "")[:10] if p.get("created_at") else "",
                "風險等級": p.get("stage", ""),
                "分類": p.get("category", ""),
                "里程碑": p.get("recent_title", "") or p.get("goal", ""),
                "備註": p.get("note", ""),
                "層級": str(p.get("level", "")),
            }
    return {}


def generate_prospect_invite(name: str = "") -> str:
    meetings = list_meetings()
    if not meetings:
        return "⚠️ 目前沒有排定的課程會議，請先新增課程會議。"
    mtg_summary = format_meetings(meetings)

    promos = _load_promos()
    _first_promo = promos[0] if promos else None
    promo_content = (_first_promo["optimized"] or _first_promo["content"]) if _first_promo else ""
    promo_section = ("課程文宣參考：\n" + promo_content) if promo_content else ""

    if name:
        info = _load_prospect_info(name)
        person_block = (
            f"姓名：{name}\n"
            f"職業：{info.get('職業', '')}\n"
            f"備註：{info.get('備註', '')}\n"
            f"需求標籤：{info.get('需求標籤', '')}"
        )
        target_desc = f"針對潛在家人「{name}」個人化邀約"
    else:
        person_block = "（通用邀約，不針對特定人）"
        target_desc = "通用潛在家人邀約"

    prompt = f"""你是一位溫暖有力的 Amway 邀約助理。
任務：產生{target_desc}文宣，邀請對方參加課程會議。

接下來的課程會議：
{mtg_summary}

{promo_section}

受邀者資訊：
{person_block}

邀約要求：
- 開頭自然打招呼
- 簡短介紹這堂課程的價值（對方會得到什麼）
- 說明時間、地點
- 一個清楚的行動呼籲（報名 / 回覆 / 聯絡）
- 語氣像朋友，不像業務
- 控制在 200 字以內
"""
    _log(f"產生潛在家人邀約：{name or '(通用)'}")
    return _run_codex(prompt, timeout=90)


# ============================================================
# Codex CLI: Generate Invite — Follow-up Partner
# ============================================================

def generate_partner_invite(name: str = "") -> str:
    meetings = list_meetings()
    if not meetings:
        return "⚠️ 目前沒有排定的課程會議，請先新增課程會議。"
    mtg_summary = format_meetings(meetings)

    if name:
        info = _load_partner_info(name)
        n_days = ""
        if info.get("加入日期"):
            try:
                join = datetime.strptime(info["加入日期"].strip(), "%Y-%m-%d").date()
                n_days = str((date.today() - join).days)
            except Exception:
                pass
        person_block = (
            f"姓名：{name}\n"
            f"加入天數：{n_days} 天\n"
            f"分類：{info.get('分類', '')}\n"
            f"風險等級：{info.get('風險等級', '')}\n"
            f"里程碑：{info.get('里程碑', '')}\n"
            f"備註：{info.get('備註', '')}"
        )
        target_desc = f"針對跟進夥伴「{name}」個人化邀約"
    else:
        person_block = "（通用邀約，不針對特定人）"
        target_desc = "通用跟進夥伴邀約"

    prompt = f"""你是一位鼓勵型的 Amway 培訓助理。
任務：產生{target_desc}文宣，邀請夥伴參加課程或會議。

接下來的課程會議：
{mtg_summary}

夥伴資訊：
{person_block}

邀約要求：
- 開頭溫暖問候，肯定夥伴的努力
- 說明這次課程對夥伴成長的幫助
- 說明時間、地點
- 一個清楚的行動呼籲（確認出席 / 報名 / 回覆）
- 語氣像資深夥伴，充滿鼓勵
- 控制在 200 字以內
"""
    _log(f"產生跟進夥伴邀約：{name or '(通用)'}")
    return _run_codex(prompt, timeout=90)


# ============================================================
# Codex CLI: Invite for specific person × specific meeting
# ============================================================

def generate_prospect_invite_for_meeting(name: str, meeting: dict) -> str:
    info = _load_prospect_info(name)
    person_block = (
        f"姓名：{name}\n"
        f"職業：{info.get('職業', '')}\n"
        f"興趣：{info.get('興趣', '')}\n"
        f"備註：{info.get('備註', '')}\n"
        f"需求標籤：{info.get('需求標籤', '')}\n"
        f"使用產品：{info.get('使用產品', '')}\n"
        f"體驗記錄：{info.get('體驗記錄', '')}"
    )
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    loc = meeting.get("location", "")
    desc = meeting.get("description", "")
    speaker = meeting.get("speaker", "")
    speaker_bio = meeting.get("speaker_bio", "")
    topics = meeting.get("topics", "")
    topic_desc = meeting.get("topic_desc", "")

    promos = _load_promos()
    _first_promo = promos[0] if promos else None
    promo_content = (_first_promo["optimized"] or _first_promo["content"]) if _first_promo else ""
    promo_section = ("課程文宣參考：\n" + promo_content) if promo_content else ""

    prompt = f"""你是一位溫暖有力的 Amway 邀約助理。
任務：針對潛在家人「{name}」產生個人化課程邀約文宣。

指定課程會議：
  標題：{meeting['title']}
  時間：{when}
  地點：{loc or '（未填）'}
  說明：{desc or '（未填）'}
  演講貴賓：{speaker or '（未填）'}
  貴賓介紹：{speaker_bio or '（未填）'}
  課程主題：{topics or '（未填）'}
  主題介紹：{topic_desc or '（未填）'}

{promo_section}

受邀者資訊：
{person_block}

邀約要求：
- 開頭自然打招呼，點名對方姓名
- 結合對方的職業、興趣、需求標籤說明這堂課對他/她的具體價值
- 若有演講貴賓，引用其介紹增加吸引力（如：知名鑽石XX將親自分享…）
- 若有課程主題介紹，提煉重點融入邀約
- 說明時間、地點
- 一個清楚的行動呼籲（報名 / 回覆 / 詢問）
- 語氣像朋友，不像業務
- 控制在 200 字以內
"""
    _log(f"產生潛在家人邀約：{name} × {meeting['title']}")
    result = _run_codex(prompt, timeout=90)
    save_invite(meeting["id"], name, "prospect", result)
    return result


def generate_partner_invite_for_meeting(name: str, meeting: dict) -> str:
    info = _load_partner_info(name)
    n_days = ""
    if info.get("加入日期"):
        try:
            join = datetime.strptime(info["加入日期"].strip(), "%Y-%m-%d").date()
            n_days = str((date.today() - join).days)
        except Exception:
            pass
    person_block = (
        f"姓名：{name}\n"
        f"加入天數：{n_days} 天\n"
        f"分類：{info.get('分類', '')}\n"
        f"風險等級：{info.get('風險等級', '')}\n"
        f"里程碑：{info.get('里程碑', '')}\n"
        f"備註：{info.get('備註', '')}"
    )
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    loc = meeting.get("location", "")
    desc = meeting.get("description", "")
    speaker = meeting.get("speaker", "")
    speaker_bio = meeting.get("speaker_bio", "")
    topics = meeting.get("topics", "")
    topic_desc = meeting.get("topic_desc", "")

    prompt = f"""你是一位鼓勵型的 Amway 培訓助理。
任務：針對跟進夥伴「{name}」產生個人化課程邀約文宣。

指定課程會議：
  標題：{meeting['title']}
  時間：{when}
  地點：{loc or '（未填）'}
  說明：{desc or '（未填）'}
  演講貴賓：{speaker or '（未填）'}
  貴賓介紹：{speaker_bio or '（未填）'}
  課程主題：{topics or '（未填）'}
  主題介紹：{topic_desc or '（未填）'}

夥伴資訊：
{person_block}

邀約要求：
- 開頭溫暖問候，點名夥伴姓名，肯定他/她的努力
- 結合夥伴的里程碑、備註說明這次課程對其成長的具體幫助
- 若有演講貴賓，引用其介紹增加說服力（如：這次有鑽石XX親自來分享…）
- 若有課程主題介紹，提煉重點說明對夥伴的直接幫助
- 說明時間、地點
- 一個清楚的行動呼籲（確認出席 / 報名 / 回覆）
- 語氣像資深夥伴，充滿鼓勵
- 控制在 200 字以內
"""
    _log(f"產生跟進夥伴邀約：{name} × {meeting['title']}")
    result = _run_codex(prompt, timeout=90)
    save_invite(meeting["id"], name, "partner", result)
    return result


# ============================================================
# Unified Command Handler
# ============================================================

class CourseInviteAgent:

    def handle_command(self, msg: str) -> str:
        msg = msg.strip()

        # 新增課程會議 YYYY-MM-DD HH:MM 標題|地點|說明
        if msg.startswith("新增課程會議"):
            return self._cmd_add_meeting(msg)

        # 查詢課程會議
        if msg in ("查詢課程會議", "課程會議", "課程"):
            meetings = list_meetings()
            return format_meetings(meetings)

        # 刪除課程會議 COURSE-XXXX
        if msg.startswith("刪除課程會議"):
            mid = msg.replace("刪除課程會議", "").strip()
            if not mid:
                return "⚠️ 格式：刪除課程會議 COURSE-XXXX"
            return delete_meeting(mid)

        # 修改課程會議 COURSE-XXXX 欄位:值|欄位:值...
        if msg.startswith("修改課程會議"):
            return self._cmd_update_meeting(msg)

        # 從行事曆加入課程 [關鍵字]
        if msg.startswith("從行事曆加入課程"):
            keyword = msg.replace("從行事曆加入課程", "").strip()
            return import_from_calendar(keyword)

        # 新增課程文宣 標題|內文
        if msg.startswith("新增課程文宣"):
            content = msg.replace("新增課程文宣", "").strip()
            parts = [p.strip() for p in content.split("|", 1)]
            if len(parts) < 2 or not parts[0] or not parts[1]:
                return "⚠️ 格式：新增課程文宣 標題|內文"
            item = add_promo(parts[0], parts[1])
            return f"✅ 已新增課程文宣：{item['id']}｜{item['title']}"

        # 查詢課程文宣
        if msg in ("查詢課程文宣", "課程文宣"):
            return format_promos(list_promos())

        if msg == "查詢已產生的今日之後會議邀約文宣":
            return format_upcoming_invites()

        if msg.startswith("修改已產生的今日之後會議邀約文宣"):
            raw = msg.replace("修改已產生的今日之後會議邀約文宣", "", 1).strip()
            parts = [p.strip() for p in raw.split("|", 2)]
            if len(parts) < 3 or not parts[0] or not parts[1] or not parts[2]:
                return "⚠️ 格式：修改已產生的今日之後會議邀約文宣 COURSE-XXXX | 姓名 | 新內容"
            meeting_id, name, content = parts
            if update_invite(meeting_id, name, content):
                return f"✅ 已更新邀約文宣：{meeting_id}｜{name}"
            return "⚠️ 找不到該筆邀約文宣，請先查詢或先產生。"

        # 優化課程文宣 PROMO-XXXX
        if msg.startswith("優化課程文宣"):
            pid = msg.replace("優化課程文宣", "").strip()
            if not pid:
                return "⚠️ 格式：優化課程文宣 PROMO-XXXX\n查詢現有文宣：查詢課程文宣"
            return optimize_promo(pid)

        if msg.startswith("套用優化課程文宣"):
            pid = msg.replace("套用優化課程文宣", "").strip()
            if not pid:
                return "⚠️ 格式：套用優化課程文宣 PROMO-XXXX"
            return apply_optimized_promo(pid)

        # 邀約文宣 潛在家人 [姓名]
        if msg.startswith("邀約文宣 潛在家人"):
            name = msg.replace("邀約文宣 潛在家人", "").strip()
            return generate_prospect_invite(name)

        # 邀約文宣 跟進夥伴 [姓名]
        if msg.startswith("邀約文宣 跟進夥伴"):
            name = msg.replace("邀約文宣 跟進夥伴", "").strip()
            return generate_partner_invite(name)

        return ""

    # ── private ──────────────────────────────────────────────

    def _cmd_update_meeting(self, msg: str) -> str:
        # 格式：修改課程會議 COURSE-XXXX 欄位:值|欄位:值...
        # 欄位名：標題 日期 時間 地點 說明 演講貴賓 貴賓介紹 課程主題 主題介紹
        FIELD_MAP = {
            "標題": "title", "日期": "date", "時間": "time",
            "地點": "location", "說明": "description",
            "演講貴賓": "speaker", "貴賓介紹": "speaker_bio",
            "課程主題": "topics", "主題介紹": "topic_desc",
        }
        content = msg.replace("修改課程會議", "").strip()
        m = re.match(r"(COURSE-\w+)\s+(.+)", content, re.DOTALL)
        if not m:
            return (
                "⚠️ 格式：\n修改課程會議 COURSE-XXXX 欄位:值|欄位:值\n\n"
                "可修改欄位：標題、日期、時間、地點、說明、演講貴賓、貴賓介紹、課程主題、主題介紹\n\n"
                "範例：\n修改課程會議 COURSE-XXXXXXXX 地點:台北車站旁會議室|演講貴賓:鑽石王大明"
            )
        meeting_id = m.group(1)
        pairs_str = m.group(2)
        fields = {}
        for pair in pairs_str.split("|"):
            if ":" not in pair:
                continue
            key, _, val = pair.partition(":")
            key = key.strip()
            if key in FIELD_MAP:
                fields[FIELD_MAP[key]] = val.strip()
        if not fields:
            keys = "、".join(FIELD_MAP.keys())
            return f"⚠️ 未偵測到有效欄位，可用欄位：{keys}"
        try:
            return update_meeting(meeting_id, fields)
        except ValueError as e:
            return f"⚠️ {e}"

    def _cmd_add_meeting(self, msg: str) -> str:
        # 格式：新增課程會議 YYYY-MM-DD [HH:MM] 標題|地點|說明|演講貴賓|貴賓介紹|課程主題|主題介紹
        content = msg.replace("新增課程會議", "").strip()
        m = re.match(
            r"(\d{4}-\d{2}-\d{2})(?:\s+(\d{1,2}:\d{2}))?\s+(.+)",
            content,
        )
        if not m:
            return (
                "⚠️ 格式：\n新增課程會議 YYYY-MM-DD [HH:MM] 標題|地點|說明|演講貴賓|貴賓介紹|課程主題|主題介紹\n\n"
                "範例：\n新增課程會議 2026-04-10 19:00 四月OPP說明會|台中大里店|歡迎帶朋友|鑽石李大明|20年資深鑽石，擅長事業說明|Amway事業機會|從零到鑽石的實戰分享"
            )
        date_str = m.group(1)
        time_str = m.group(2) or ""
        rest = m.group(3).strip()
        parts = [p.strip() for p in rest.split("|")]
        title       = parts[0]
        location    = parts[1] if len(parts) > 1 else ""
        description = parts[2] if len(parts) > 2 else ""
        speaker     = parts[3] if len(parts) > 3 else ""
        speaker_bio = parts[4] if len(parts) > 4 else ""
        topics      = parts[5] if len(parts) > 5 else ""
        topic_desc  = parts[6] if len(parts) > 6 else ""
        try:
            item = add_meeting(title, date_str, time_str, location, description,
                               speaker, speaker_bio, topics, topic_desc)
            when = item["date"] + (f" {item['time']}" if item.get("time") else "")
            return (
                f"✅ 已新增課程會議\n"
                f"ID：{item['id']}\n"
                f"標題：{item['title']}\n"
                f"時間：{when}\n"
                f"地點：{item['location'] or '（未填）'}\n"
                f"說明：{item['description'] or '（未填）'}\n"
                f"演講貴賓：{item['speaker'] or '（未填）'}\n"
                f"貴賓介紹：{item['speaker_bio'] or '（未填）'}\n"
                f"課程主題：{item['topics'] or '（未填）'}\n"
                f"主題介紹：{item['topic_desc'] or '（未填）'}"
            )
        except ValueError as e:
            return f"⚠️ {e}"


    def run(self):
        """Orchestrator 每日早班呼叫：記錄接下來的課程會議到 log。"""
        _log("=== 課程邀約 Agent 啟動 ===")
        meetings = list_meetings()
        if meetings:
            _log(f"接下來有 {len(meetings)} 個課程會議：")
            for m in meetings:
                when = m["date"] + (f" {m['time']}" if m.get("time") else "")
                _log(f"  {m['id']}｜{when}｜{m['title']}")
        else:
            _log("目前沒有接下來的課程會議。")
        _log("=== 課程邀約 Agent 完成 ===")


def _safe_text(value) -> str:
    return str(value or "").strip()


def _person_block_from_info(name: str, info: dict) -> str:
    lines = [f"姓名：{name}"]
    for key, value in (info or {}).items():
        text = _safe_text(value)
        if not text or key in ("name",):
            continue
        lines.append(f"{key}：{text}")
    return "\n".join(lines)


def optimize_promo(promo_id: str) -> str:
    promo = get_promo_detail(promo_id)
    if not promo:
        return f"找不到課程文宣：{promo_id}"
    meetings = list_meetings()
    mtg_summary = format_meetings(meetings) if meetings else "目前沒有今日之後的課程會議。"
    pm = _load_prompt_manager()
    prompt = pm.render_prompt(
        "course_promo_optimize",
        mtg_summary=mtg_summary,
        promo_title=promo["title"],
        promo_content=promo["content"],
    )
    _log(f"優化課程文宣 {promo_id}")
    optimized = _run_codex(prompt, timeout=90)
    promos = _load_promos()
    for p in promos:
        if p["id"] == promo_id:
            p["optimized"] = optimized
            p["updated_at"] = datetime.now().isoformat()
            break
    _save_promos(promos)
    return f"已優化課程文宣：{promo_id}\n\n{optimized}"


def generate_prospect_invite(name: str = "") -> str:
    meetings = list_meetings()
    if not meetings:
        return "目前沒有排定的課程會議，請先新增課程會議。"
    mtg_summary = format_meetings(meetings)
    promos = _load_promos()
    first_promo = promos[0] if promos else None
    promo_content = ((first_promo or {}).get("optimized") or (first_promo or {}).get("content") or "").strip()
    promo_section = ("課程文宣內容：\n" + promo_content) if promo_content else "目前沒有課程文宣內容。"
    if name:
        info = _load_prospect_info(name)
        target_desc = f"針對潛在家人 {name} 產生邀約文宣"
        person_block = _person_block_from_info(name, info)
    else:
        target_desc = "針對一般潛在家人產生邀約文宣"
        person_block = "未指定特定對象。"
    pm = _load_prompt_manager()
    prompt = pm.render_prompt(
        "course_invite_prospect_general",
        mtg_summary=mtg_summary,
        promo_section=promo_section,
        target_desc=target_desc,
        person_block=person_block,
    )
    _log(f"產生潛在家人邀約文宣 {name or '(通用)'}")
    return _run_codex(prompt, timeout=90)


def generate_partner_invite(name: str = "") -> str:
    meetings = list_meetings()
    if not meetings:
        return "目前沒有排定的課程會議，請先新增課程會議。"
    mtg_summary = format_meetings(meetings)
    if name:
        info = _load_partner_info(name)
        target_desc = f"針對跟進夥伴 {name} 產生邀約文宣"
        person_block = _person_block_from_info(name, info)
    else:
        target_desc = "針對一般跟進夥伴產生邀約文宣"
        person_block = "未指定特定對象。"
    pm = _load_prompt_manager()
    prompt = pm.render_prompt(
        "course_invite_partner_general",
        mtg_summary=mtg_summary,
        target_desc=target_desc,
        person_block=person_block,
    )
    _log(f"產生跟進夥伴邀約文宣 {name or '(通用)'}")
    return _run_codex(prompt, timeout=90)


def generate_prospect_invite_for_meeting(name: str, meeting: dict) -> str:
    info = _load_prospect_info(name)
    promos = _load_promos()
    first_promo = promos[0] if promos else None
    promo_content = ((first_promo or {}).get("optimized") or (first_promo or {}).get("content") or "").strip()
    promo_section = ("課程文宣內容：\n" + promo_content) if promo_content else "目前沒有課程文宣內容。"
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    pm = _load_prompt_manager()
    prompt = pm.render_prompt(
        "course_invite_prospect_meeting",
        name=name,
        meeting_title=_safe_text(meeting.get("title")),
        when=when,
        loc=_safe_text(meeting.get("location")) or "未提供",
        desc=_safe_text(meeting.get("description")) or "未提供",
        speaker=_safe_text(meeting.get("speaker")) or "未提供",
        speaker_bio=_safe_text(meeting.get("speaker_bio")) or "未提供",
        topics=_safe_text(meeting.get("topics")) or "未提供",
        topic_desc=_safe_text(meeting.get("topic_desc")) or "未提供",
        promo_section=promo_section,
        person_block=_person_block_from_info(name, info),
    )
    _log(f"產生潛在家人指定會議邀約 {name} / {meeting['title']}")
    result = _run_codex(prompt, timeout=90)
    save_invite(meeting["id"], name, "prospect", result)
    return result


def generate_partner_invite_for_meeting(name: str, meeting: dict) -> str:
    info = _load_partner_info(name)
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    pm = _load_prompt_manager()
    prompt = pm.render_prompt(
        "course_invite_partner_meeting",
        name=name,
        meeting_title=_safe_text(meeting.get("title")),
        when=when,
        loc=_safe_text(meeting.get("location")) or "未提供",
        desc=_safe_text(meeting.get("description")) or "未提供",
        speaker=_safe_text(meeting.get("speaker")) or "未提供",
        speaker_bio=_safe_text(meeting.get("speaker_bio")) or "未提供",
        topics=_safe_text(meeting.get("topics")) or "未提供",
        topic_desc=_safe_text(meeting.get("topic_desc")) or "未提供",
        person_block=_person_block_from_info(name, info),
    )
    _log(f"產生跟進夥伴指定會議邀約 {name} / {meeting['title']}")
    result = _run_codex(prompt, timeout=90)
    save_invite(meeting["id"], name, "partner", result)
    return result


if __name__ == "__main__":
    agent = CourseInviteAgent()
    # Quick smoke test
    print(agent.handle_command("查詢課程會議"))
