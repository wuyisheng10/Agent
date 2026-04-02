import json
from datetime import datetime
from pathlib import Path

try:
    from common_runtime import BASE_DIR
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR


TRAINING_DIR = BASE_DIR / "output" / "training_system"
MODULES_FILE = TRAINING_DIR / "modules.json"
SESSIONS_FILE = TRAINING_DIR / "sessions.json"
REFLECTIONS_FILE = TRAINING_DIR / "reflections.json"
PROGRESS_FILE = TRAINING_DIR / "progress.json"

MODULE_CATEGORIES = [
    "領導人特質",
    "新人守則",
    "帶線系統",
    "市場實戰",
    "畫畫培訓",
    "產品培訓",
    "事業培訓",
]


def _ensure_dirs():
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, key: str) -> list[dict]:
    _ensure_dirs()
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        rows = data.get(key, [])
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def _save_json(path: Path, key: str, rows: list[dict]):
    _ensure_dirs()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({key: rows}, f, ensure_ascii=False, indent=2)


def load_modules() -> list[dict]:
    return _load_json(MODULES_FILE, "modules")


def save_modules(rows: list[dict]):
    _save_json(MODULES_FILE, "modules", rows)


def load_sessions() -> list[dict]:
    return _load_json(SESSIONS_FILE, "sessions")


def save_sessions(rows: list[dict]):
    _save_json(SESSIONS_FILE, "sessions", rows)


def load_reflections() -> list[dict]:
    return _load_json(REFLECTIONS_FILE, "reflections")


def save_reflections(rows: list[dict]):
    _save_json(REFLECTIONS_FILE, "reflections", rows)


def load_progress() -> list[dict]:
    return _load_json(PROGRESS_FILE, "progress")


def save_progress(rows: list[dict]):
    _save_json(PROGRESS_FILE, "progress", rows)


def _slug(text: str) -> str:
    out = []
    for ch in (text or "").strip():
        if ch.isascii() and ch.isalnum():
            out.append(ch.upper())
        elif "\u4e00" <= ch <= "\u9fff":
            out.append(ch)
    s = "".join(out)
    return s[:24] or "MODULE"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _module_id(title: str) -> str:
    return f"TM-{_slug(title)}"


def _session_id(date_str: str, idx: int) -> str:
    return f"TS-{date_str.replace('-', '')}-{idx:03d}"


def _reflection_id(session_id: str, person_name: str) -> str:
    return f"TR-{session_id}-{_slug(person_name)[:12]}"


def list_module_options() -> list[dict]:
    return [{"id": row["id"], "title": row["title"], "category": row.get("category", "")} for row in load_modules() if row.get("title")]


def list_session_options() -> list[dict]:
    return [{"id": row["id"], "title": row["title"], "date": row.get("date", ""), "module_id": row.get("module_id", "")} for row in load_sessions() if row.get("title")]


def _find_module_by_title(title: str) -> dict | None:
    key = (title or "").strip()
    for row in load_modules():
        if row.get("title") == key or row.get("id") == key:
            return row
    return None


def _find_session_by_title(title: str) -> dict | None:
    key = (title or "").strip()
    for row in load_sessions():
        if row.get("title") == key or row.get("id") == key:
            return row
    return None


def _find_progress(name: str, rows: list[dict]) -> dict | None:
    for row in rows:
        if row.get("person_name") == name:
            return row
    return None


def create_module(title: str, category: str, goal: str, summary: str) -> str:
    title = title.strip()
    category = category.strip()
    goal = goal.strip()
    summary = summary.strip()
    if not title or not category:
        return "⚠️ 缺少模組名稱或模組類型。"
    modules = load_modules()
    if any(row.get("title") == title for row in modules):
        return f"⚠️ 培訓模組已存在：{title}"
    item = {
        "id": _module_id(title),
        "title": title,
        "category": category,
        "goal": goal,
        "summary": summary,
        "keywords": [],
        "attachments": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    modules.append(item)
    modules.sort(key=lambda x: (x.get("category", ""), x.get("title", "")))
    save_modules(modules)
    return f"✅ 已新增培訓模組\n- {title}｜{category}\n目標：{goal or '未填寫'}"


def list_modules(query: str = "") -> str:
    rows = load_modules()
    query = (query or "").strip()
    if query:
        rows = [row for row in rows if query in row.get("title", "") or query in row.get("category", "")]
    if not rows:
        return "⚠️ 目前沒有符合的培訓模組。"
    lines = ["📚 培訓模組清單"]
    for row in rows:
        lines.append(f"- {row.get('title','')}｜{row.get('category','')}")
        if row.get("goal"):
            lines.append(f"  目標：{row['goal']}")
    return "\n".join(lines)


def create_session(title: str, module_name: str, date_str: str, time_str: str, location: str, speaker: str, audience: str) -> str:
    title = title.strip()
    mod = _find_module_by_title(module_name)
    if not mod:
        return f"⚠️ 找不到培訓模組：{module_name}"
    sessions = load_sessions()
    idx = len([row for row in sessions if row.get("date") == date_str]) + 1
    item = {
        "id": _session_id(date_str, idx),
        "module_id": mod["id"],
        "title": title,
        "speaker": speaker.strip(),
        "date": date_str.strip(),
        "time": time_str.strip(),
        "location": location.strip(),
        "audience": audience.strip(),
        "description": "",
        "materials": [],
        "status": "scheduled",
        "participants": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    sessions.append(item)
    sessions.sort(key=lambda x: (x.get("date", ""), x.get("time", ""), x.get("title", "")))
    save_sessions(sessions)
    return f"✅ 已新增培訓課程\n- {title}\n- 模組：{mod['title']}\n- 時間：{date_str} {time_str}\n- 地點：{location}"


def list_sessions(query: str = "") -> str:
    rows = load_sessions()
    mods = {row["id"]: row for row in load_modules()}
    query = (query or "").strip()
    if query:
        rows = [
            row for row in rows
            if query in row.get("title", "")
            or query in row.get("date", "")
            or query in mods.get(row.get("module_id", ""), {}).get("title", "")
        ]
    if not rows:
        return "⚠️ 目前沒有符合的培訓課程。"
    lines = ["🗓️ 培訓課程清單"]
    for row in rows:
        mod_title = mods.get(row.get("module_id", ""), {}).get("title", "")
        lines.append(
            f"- {row.get('title','')}｜{mod_title}｜{row.get('date','')} {row.get('time','')}｜{row.get('location','')}"
        )
    return "\n".join(lines)


def add_reflection(person_name: str, session_title: str, insight: str, learned: str, action: str, goal: str) -> str:
    session = _find_session_by_title(session_title)
    if not session:
        return f"⚠️ 找不到培訓課程：{session_title}"
    reflections = load_reflections()
    ref = {
        "id": _reflection_id(session["id"], person_name),
        "session_id": session["id"],
        "module_id": session["module_id"],
        "person_name": person_name.strip(),
        "person_type": "partner",
        "insight": insight.strip(),
        "learned": learned.strip(),
        "action": action.strip(),
        "goal": goal.strip(),
        "coach_feedback": "",
        "created_at": _now(),
        "updated_at": _now(),
    }
    reflections = [row for row in reflections if row.get("id") != ref["id"]]
    reflections.append(ref)
    reflections.sort(key=lambda x: (x.get("person_name", ""), x.get("created_at", "")))
    save_reflections(reflections)
    _rebuild_progress_for_person(person_name.strip())
    return f"✅ 已新增培訓反思\n- {person_name.strip()}\n- 課程：{session.get('title','')}\n- 做到：{action.strip() or '未填寫'}"


def _rebuild_progress_for_person(person_name: str):
    reflections = [row for row in load_reflections() if row.get("person_name") == person_name]
    reflections.sort(key=lambda x: x.get("created_at", ""))
    progress = load_progress()
    item = _find_progress(person_name, progress)
    if item is None:
        item = {
            "person_name": person_name,
            "person_type": "partner",
            "completed_modules": [],
            "completed_sessions": [],
            "last_session_id": "",
            "last_reflection_id": "",
            "next_recommended_modules": [],
            "action_status": "active",
            "updated_at": _now(),
        }
        progress.append(item)
    item["completed_modules"] = sorted({row.get("module_id", "") for row in reflections if row.get("module_id")})
    item["completed_sessions"] = sorted({row.get("session_id", "") for row in reflections if row.get("session_id")})
    if reflections:
        last = reflections[-1]
        item["last_session_id"] = last.get("session_id", "")
        item["last_reflection_id"] = last.get("id", "")
        item["updated_at"] = _now()
    mods = load_modules()
    item["next_recommended_modules"] = [row["id"] for row in mods if row.get("id") not in item["completed_modules"]][:3]
    save_progress(sorted(progress, key=lambda x: x.get("person_name", "")))


def query_progress(person_name: str) -> str:
    mods = {row["id"]: row for row in load_modules()}
    sessions = {row["id"]: row for row in load_sessions()}
    reflections = [row for row in load_reflections() if row.get("person_name") == person_name.strip()]
    progress = _find_progress(person_name.strip(), load_progress())
    if not progress:
        return f"⚠️ 找不到 {person_name.strip()} 的培訓進度。"
    lines = [f"📈 {person_name.strip()} 的培訓進度"]
    completed = [mods[mid]["title"] for mid in progress.get("completed_modules", []) if mid in mods]
    lines.append("已完成模組：" + ("、".join(completed) if completed else "尚無"))
    last_session = sessions.get(progress.get("last_session_id", ""), {})
    if last_session:
        lines.append(f"最近課程：{last_session.get('title','')}｜{last_session.get('date','')} {last_session.get('time','')}")
    if reflections:
        last = sorted(reflections, key=lambda x: x.get("created_at", ""))[-1]
        lines.append(f"最近悟到：{last.get('insight','') or '未填寫'}")
        lines.append(f"最近做到：{last.get('action','') or '未填寫'}")
        lines.append(f"最近目標：{last.get('goal','') or '未填寫'}")
    next_mods = [mods[mid]["title"] for mid in progress.get("next_recommended_modules", []) if mid in mods]
    if next_mods:
        lines.append("下一步建議模組：" + "、".join(next_mods))
    return "\n".join(lines)


def query_team_summary() -> str:
    progress = load_progress()
    if not progress:
        return "⚠️ 目前沒有培訓進度資料。"
    lines = [f"📊 培訓總表（共 {len(progress)} 人）"]
    for item in progress[:20]:
        lines.append(
            f"- {item.get('person_name','')}｜完成模組 {len(item.get('completed_modules', []))}｜狀態：{item.get('action_status','active')}"
        )
    if len(progress) > 20:
        lines.append(f"其餘 {len(progress) - 20} 人請後續擴充分頁查詢。")
    return "\n".join(lines)


class TrainingSystemAgent:
    def handle_command(self, cmd: str) -> str | None:
        cmd = (cmd or "").strip()
        if cmd.startswith("新增培訓模組 "):
            parts = [p.strip() for p in cmd.replace("新增培訓模組", "", 1).split("|")]
            while len(parts) < 4:
                parts.append("")
            return create_module(parts[0], parts[1], parts[2], parts[3])
        if cmd == "查詢培訓模組":
            return list_modules()
        if cmd.startswith("查詢培訓模組 "):
            return list_modules(cmd.replace("查詢培訓模組", "", 1).strip())
        if cmd.startswith("新增培訓課程 "):
            parts = [p.strip() for p in cmd.replace("新增培訓課程", "", 1).split("|")]
            while len(parts) < 7:
                parts.append("")
            return create_session(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6])
        if cmd == "查詢培訓課程":
            return list_sessions()
        if cmd.startswith("查詢培訓課程 "):
            return list_sessions(cmd.replace("查詢培訓課程", "", 1).strip())
        if cmd.startswith("新增培訓反思 "):
            parts = [p.strip() for p in cmd.replace("新增培訓反思", "", 1).split("|")]
            while len(parts) < 6:
                parts.append("")
            return add_reflection(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5])
        if cmd.startswith("查詢培訓進度 "):
            return query_progress(cmd.replace("查詢培訓進度", "", 1).strip())
        if cmd == "查詢培訓總表":
            return query_team_summary()
        return None
