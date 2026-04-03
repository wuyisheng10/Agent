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
SEVEN_DAY_FILE = TRAINING_DIR / "seven_day.json"
ACTIONS_FILE = TRAINING_DIR / "actions.json"

MODULE_CATEGORIES = [
    "領導人特質",
    "新人守則",
    "帶線系統",
    "市場實戰",
    "畫畫培訓",
    "產品培訓",
    "事業培訓",
]

ACTION_STATUSES = ["待執行", "進行中", "已完成", "延後", "需協助"]


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


def load_seven_day() -> list[dict]:
    return _load_json(SEVEN_DAY_FILE, "seven_day")


def save_seven_day(rows: list[dict]):
    _save_json(SEVEN_DAY_FILE, "seven_day", rows)


def load_actions() -> list[dict]:
    return _load_json(ACTIONS_FILE, "actions")


def save_actions(rows: list[dict]):
    _save_json(ACTIONS_FILE, "actions", rows)


def _slug(text: str) -> str:
    out = []
    for ch in (text or "").strip():
        if ch.isascii() and ch.isalnum():
            out.append(ch.upper())
        elif "\u4e00" <= ch <= "\u9fff":
            out.append(ch)
    return ("".join(out)[:24] or "ITEM").upper()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _module_id(title: str) -> str:
    return f"TM-{_slug(title)}"


def _session_id(date_str: str, idx: int) -> str:
    return f"TS-{date_str.replace('-', '')}-{idx:03d}"


def _reflection_id(session_id: str, person_name: str) -> str:
    return f"TR-{session_id}-{_slug(person_name)[:12]}"


def _seven_day_id(person_name: str, start_date: str) -> str:
    return f"SD-{start_date.replace('-', '')}-{_slug(person_name)[:12]}"


def _action_id(person_name: str, idx: int) -> str:
    return f"TA-{_slug(person_name)[:10]}-{idx:03d}"


def list_module_options() -> list[dict]:
    return [
        {"id": row["id"], "title": row["title"], "category": row.get("category", "")}
        for row in load_modules()
        if row.get("title")
    ]


def list_session_options() -> list[dict]:
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "date": row.get("date", ""),
            "module_id": row.get("module_id", ""),
        }
        for row in load_sessions()
        if row.get("title")
    ]


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
        return "請至少提供模組名稱與模組類型。"
    modules = load_modules()
    if any(row.get("title") == title for row in modules):
        return f"已存在同名培訓模組：{title}"
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
    return f"已新增培訓模組\n- {title}｜{category}\n- 目標：{goal or '未填寫'}"


def list_modules(query: str = "") -> str:
    rows = load_modules()
    query = (query or "").strip()
    if query:
        rows = [row for row in rows if query in row.get("title", "") or query in row.get("category", "")]
    if not rows:
        return "目前沒有符合條件的培訓模組。"
    lines = ["培訓模組清單"]
    for row in rows:
        lines.append(f"- {row.get('title', '')}｜{row.get('category', '')}")
        if row.get("goal"):
            lines.append(f"  目標：{row['goal']}")
    return "\n".join(lines)


def create_session(title: str, module_name: str, date_str: str, time_str: str, location: str, speaker: str, audience: str) -> str:
    title = title.strip()
    mod = _find_module_by_title(module_name)
    if not mod:
        return f"找不到培訓模組：{module_name}"
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
    return f"已新增培訓課程\n- {title}\n- 模組：{mod['title']}\n- 時間：{date_str} {time_str}\n- 地點：{location}"


def list_sessions(query: str = "") -> str:
    rows = load_sessions()
    mods = {row["id"]: row for row in load_modules()}
    query = (query or "").strip()
    if query:
        rows = [
            row
            for row in rows
            if query in row.get("title", "")
            or query in row.get("date", "")
            or query in mods.get(row.get("module_id", ""), {}).get("title", "")
        ]
    if not rows:
        return "目前沒有符合條件的培訓課程。"
    lines = ["培訓課程清單"]
    for row in rows:
        mod_title = mods.get(row.get("module_id", ""), {}).get("title", "")
        lines.append(
            f"- {row.get('date', '')} {row.get('time', '')}｜{row.get('title', '')}"
            f"｜模組：{mod_title or '未對應'}｜地點：{row.get('location', '')}"
        )
    return "\n".join(lines)


def add_reflection(person_name: str, session_name: str, insight: str, learned: str, action: str, goal: str) -> str:
    session = _find_session_by_title(session_name)
    if not session:
        return f"找不到培訓課程：{session_name}"

    reflections = load_reflections()
    progress = load_progress()
    reflection = {
        "id": _reflection_id(session["id"], person_name),
        "person_name": person_name.strip(),
        "session_id": session["id"],
        "session_title": session["title"],
        "insight": insight.strip(),
        "learned": learned.strip(),
        "action": action.strip(),
        "goal": goal.strip(),
        "created_at": _now(),
        "updated_at": _now(),
    }
    reflections = [r for r in reflections if r.get("id") != reflection["id"]]
    reflections.append(reflection)
    save_reflections(reflections)

    row = _find_progress(person_name, progress)
    if not row:
        row = {
            "person_name": person_name.strip(),
            "session_ids": [],
            "reflection_ids": [],
            "action_goals": [],
            "updated_at": _now(),
        }
        progress.append(row)
    if session["id"] not in row["session_ids"]:
        row["session_ids"].append(session["id"])
    if reflection["id"] not in row["reflection_ids"]:
        row["reflection_ids"].append(reflection["id"])
    if goal.strip():
        row["action_goals"].append(goal.strip())
    row["updated_at"] = _now()
    save_progress(progress)

    return f"已新增培訓反思\n- {person_name}\n- 課程：{session['title']}\n- 目標：{goal.strip() or '未填寫'}"


def get_progress(person_name: str) -> str:
    progress = load_progress()
    row = _find_progress(person_name.strip(), progress)
    if not row:
        return f"查無 {person_name} 的培訓進度。"

    reflections = {item["id"]: item for item in load_reflections()}
    sessions = {item["id"]: item for item in load_sessions()}

    lines = [f"{person_name} 的培訓進度"]
    lines.append(f"- 已完成課程：{len(row.get('session_ids', []))}")
    for session_id in row.get("session_ids", []):
        session = sessions.get(session_id)
        if session:
            lines.append(f"  - {session.get('date', '')}｜{session.get('title', '')}")

    if row.get("reflection_ids"):
        lines.append("- 最近反思：")
        for rid in row["reflection_ids"][-3:]:
            item = reflections.get(rid)
            if not item:
                continue
            lines.append(
                f"  - 課程：{item.get('session_title', '')}"
                f"｜悟到：{item.get('insight', '') or '未填寫'}"
                f"｜學到：{item.get('learned', '') or '未填寫'}"
            )
    if row.get("action_goals"):
        lines.append("- 近期目標：")
        for goal in row["action_goals"][-3:]:
            lines.append(f"  - {goal}")
    return "\n".join(lines)


def get_summary() -> str:
    progress = load_progress()
    modules = load_modules()
    sessions = load_sessions()
    reflections = load_reflections()
    return (
        "培訓總表\n"
        f"- 模組數：{len(modules)}\n"
        f"- 課程數：{len(sessions)}\n"
        f"- 反思數：{len(reflections)}\n"
        f"- 有進度學員：{len(progress)}"
    )


def start_seven_day(person_name: str, start_date: str, coach_note: str) -> str:
    rows = load_seven_day()
    item_id = _seven_day_id(person_name, start_date)
    rows = [row for row in rows if row.get("id") != item_id]
    rows.append(
        {
            "id": item_id,
            "person_name": person_name.strip(),
            "start_date": start_date.strip(),
            "coach_note": coach_note.strip(),
            "reports": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
    )
    save_seven_day(rows)
    return f"已啟動七天法則\n- 對象：{person_name}\n- 開始日：{start_date}"


def report_seven_day(person_name: str, day_label: str, task: str, done_text: str, note: str) -> str:
    rows = load_seven_day()
    row = None
    for item in reversed(rows):
        if item.get("person_name") == person_name.strip():
            row = item
            break
    if not row:
        return f"找不到 {person_name} 的七天法則紀錄。"

    report = {
        "day": day_label.strip(),
        "task": task.strip(),
        "done": done_text.strip(),
        "note": note.strip(),
        "reported_at": _now(),
    }
    row.setdefault("reports", []).append(report)
    row["updated_at"] = _now()
    save_seven_day(rows)
    return f"已回報七天法則\n- {person_name}\n- {day_label}\n- 狀態：{done_text}"


def query_seven_day(person_name: str) -> str:
    rows = load_seven_day()
    row = None
    for item in reversed(rows):
        if item.get("person_name") == person_name.strip():
            row = item
            break
    if not row:
        return f"找不到 {person_name} 的七天法則紀錄。"

    lines = [f"{person_name} 的七天法則"]
    lines.append(f"- 開始日：{row.get('start_date', '')}")
    lines.append(f"- 教練備註：{row.get('coach_note', '') or '未填寫'}")
    if row.get("reports"):
        lines.append("- 近期回報：")
        for report in row["reports"][-7:]:
            lines.append(
                f"  - {report.get('day', '')}｜{report.get('task', '')}"
                f"｜{report.get('done', '')}｜{report.get('note', '') or '無備註'}"
            )
    else:
        lines.append("- 尚未有回報")
    return "\n".join(lines)


def create_action(person_name: str, session_name: str, content: str, due_date: str) -> str:
    session = _find_session_by_title(session_name)
    if not session:
        return f"找不到培訓課程：{session_name}"
    rows = load_actions()
    idx = len([row for row in rows if row.get("person_name") == person_name.strip()]) + 1
    action_id = _action_id(person_name, idx)
    rows.append(
        {
            "id": action_id,
            "person_name": person_name.strip(),
            "session_id": session["id"],
            "session_title": session["title"],
            "content": content.strip(),
            "due_date": due_date.strip(),
            "status": "待執行",
            "note": "",
            "created_at": _now(),
            "updated_at": _now(),
        }
    )
    save_actions(rows)
    return f"已新增課後行動\n- {action_id}\n- {person_name}\n- 截止日：{due_date}"


def update_action(person_name: str, action_id: str, status: str, note: str) -> str:
    rows = load_actions()
    for row in rows:
        if row.get("person_name") == person_name.strip() and row.get("id") == action_id.strip():
            row["status"] = status.strip()
            row["note"] = note.strip()
            row["updated_at"] = _now()
            save_actions(rows)
            return f"已回報課後行動\n- {action_id}\n- 狀態：{status}"
    return f"找不到課後行動：{action_id}"


def query_actions(person_name: str) -> str:
    rows = [row for row in load_actions() if row.get("person_name") == person_name.strip()]
    if not rows:
        return f"找不到 {person_name} 的課後行動。"
    lines = [f"{person_name} 的課後行動"]
    for row in rows:
        lines.append(
            f"- {row.get('id', '')}｜{row.get('session_title', '')}"
            f"｜{row.get('content', '')}｜{row.get('status', '')}"
            f"｜截止：{row.get('due_date', '')}"
        )
    return "\n".join(lines)


class TrainingSystemAgent:
    def handle_command(self, cmd: str) -> str:
        cmd = (cmd or "").strip()

        if cmd.startswith("新增培訓模組 "):
            parts = [p.strip() for p in cmd.replace("新增培訓模組 ", "", 1).split("|")]
            while len(parts) < 4:
                parts.append("")
            return create_module(parts[0], parts[1], parts[2], parts[3])

        if cmd == "查詢培訓模組":
            return list_modules()
        if cmd.startswith("查詢培訓模組 "):
            return list_modules(cmd.replace("查詢培訓模組 ", "", 1))

        if cmd.startswith("新增培訓課程 "):
            parts = [p.strip() for p in cmd.replace("新增培訓課程 ", "", 1).split("|")]
            while len(parts) < 7:
                parts.append("")
            return create_session(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6])

        if cmd == "查詢培訓課程":
            return list_sessions()
        if cmd.startswith("查詢培訓課程 "):
            return list_sessions(cmd.replace("查詢培訓課程 ", "", 1))

        if cmd.startswith("新增培訓反思 "):
            parts = [p.strip() for p in cmd.replace("新增培訓反思 ", "", 1).split("|")]
            while len(parts) < 6:
                parts.append("")
            return add_reflection(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5])

        if cmd.startswith("查詢培訓進度 "):
            return get_progress(cmd.replace("查詢培訓進度 ", "", 1).strip())

        if cmd == "查詢培訓總表":
            return get_summary()

        if cmd.startswith("啟動七天法則 "):
            parts = [p.strip() for p in cmd.replace("啟動七天法則 ", "", 1).split("|")]
            while len(parts) < 3:
                parts.append("")
            return start_seven_day(parts[0], parts[1], parts[2])

        if cmd.startswith("七天法則回報 "):
            parts = [p.strip() for p in cmd.replace("七天法則回報 ", "", 1).split("|")]
            while len(parts) < 5:
                parts.append("")
            return report_seven_day(parts[0], parts[1], parts[2], parts[3], parts[4])

        if cmd.startswith("查詢七天法則 "):
            return query_seven_day(cmd.replace("查詢七天法則 ", "", 1).strip())

        if cmd.startswith("新增課後行動 "):
            parts = [p.strip() for p in cmd.replace("新增課後行動 ", "", 1).split("|")]
            while len(parts) < 4:
                parts.append("")
            return create_action(parts[0], parts[1], parts[2], parts[3])

        if cmd.startswith("回報課後行動 "):
            parts = [p.strip() for p in cmd.replace("回報課後行動 ", "", 1).split("|")]
            while len(parts) < 4:
                parts.append("")
            return update_action(parts[0], parts[1], parts[2], parts[3])

        if cmd.startswith("查詢課後行動 "):
            return query_actions(cmd.replace("查詢課後行動 ", "", 1).strip())

        return ""
