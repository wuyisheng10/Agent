import json
from pathlib import Path


def load_partner_rows(base_dir: Path) -> list[dict]:
    partners_json = base_dir / "output" / "partners" / "partners.json"
    if not partners_json.exists():
        return []
    try:
        with open(partners_json, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def partners_by_category(base_dir: Path, category: str) -> list[dict]:
    category = (category or "").strip().upper()
    rows = [
        p for p in load_partner_rows(base_dir)
        if (p.get("category", "") or "").upper() == category and p.get("name")
    ]
    rows.sort(key=lambda p: (p.get("level", ""), p.get("name", "")))
    return rows


def partner_category_menu() -> str:
    return (
        "📋 請先選擇夥伴分類屬性\n"
        "1. A 類：持續有使用產品、有積分額、且有聽過鐘老師演講\n"
        "2. B 類：偶爾使用產品，或有聽過鐘老師演講\n"
        "3. C 類：即將開始了解，或即將聽鐘老師演講\n\n"
        "請輸入 1、2、3 或 A、B、C，NA 取消"
    )


def normalize_partner_category_choice(raw: str) -> str:
    raw = (raw or "").strip().upper()
    return {"1": "A", "2": "B", "3": "C", "A": "A", "B": "B", "C": "C"}.get(raw, "")


def format_partner_choice_menu(category: str, people: list[dict]) -> str:
    lines = [f"📋 {category} 類夥伴清單（共 {len(people)} 位）", "輸入編號選人，NA 取消", ""]
    for i, person in enumerate(people[:30], 1):
        line = f"{i}. {person.get('name', '')}"
        if person.get("level"):
            line += f"｜層級{person.get('level', '')}"
        if person.get("stage"):
            line += f"｜{person.get('stage', '')}"
        lines.append(line)
    return "\n".join(lines)


def format_meeting_choice_menu(name: str, meetings: list[dict]) -> str:
    lines = [f"📋 {name} 的可邀約會議（共 {len(meetings)} 場）", "輸入編號產生邀約文宣，NA 取消", ""]
    for i, meeting in enumerate(meetings, 1):
        when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
        lines.append(f"{i}. {meeting['title']}（{when}）")
    return "\n".join(lines)


def format_invite_manage_list(rows: list[dict]) -> str:
    if not rows:
        return "目前沒有今日之後已產生的會議邀約文宣。"
    lines = ["📨 今日之後已產生的會議邀約文宣：", "輸入編號管理該筆文宣，NA 取消", ""]
    for i, rec in enumerate(rows, 1):
        meeting = rec["meeting"]
        when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
        lines.append(f"{i}. {meeting['id']}｜{rec.get('name', '')}｜{meeting['title']}｜{when}")
    return "\n".join(lines)


def format_invite_manage_actions(rec: dict) -> str:
    meeting = rec["meeting"]
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    return (
        "🛠️ 邀約文宣管理\n"
        f"{meeting['id']}｜{rec.get('name', '')}｜{meeting['title']}｜{when}\n\n"
        "1. 查看文宣\n"
        "2. 強制重新產生\n\n"
        "請輸入 1 或 2，NA 取消"
    )


def format_invite_view(rec: dict) -> str:
    meeting = rec["meeting"]
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    content = (rec.get("content", "") or "").strip() or "（目前沒有已產生內容）"
    return (
        "📄 邀約文宣內容\n"
        f"{meeting['id']}｜{rec.get('name', '')}｜{meeting['title']}｜{when}\n\n"
        f"{content}\n\n"
        "1. 修改這份文宣\n"
        "2. 返回\n\n"
        "請輸入 1 或 2，NA 取消"
    )


def format_invite_edit_confirm(rec: dict) -> str:
    meeting = rec["meeting"]
    when = meeting["date"] + (f" {meeting['time']}" if meeting.get("time") else "")
    content = (rec.get("content", "") or "").strip() or "（目前沒有已產生內容）"
    return (
        "📝 是否修改這份邀約文宣？\n"
        f"{meeting['id']}｜{rec.get('name', '')}｜{meeting['title']}｜{when}\n\n"
        f"目前內容：\n{content}\n\n"
        "1. 確定修改\n"
        "2. 取消\n\n"
        "請輸入 1 或 2，NA 取消"
    )


def looks_like_explicit_command(msg: str) -> bool:
    text = (msg or "").strip()
    if not text:
        return False
    prefixes = (
        "查詢", "新增", "更新", "修改", "刪除", "整理", "再次整理",
        "邀約文宣", "邀約夥伴", "跟進夥伴", "激勵夥伴", "里程碑", "培訓",
        "歸類模式", "關閉歸類模式", "潛在家人資料", "新增體驗", "換濾心",
        "執行選單", "指令集", "課程", "MTG-",
    )
    return any(text.startswith(prefix) for prefix in prefixes)
