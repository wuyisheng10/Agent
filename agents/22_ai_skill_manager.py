import json
from pathlib import Path


BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
SKILL_FILE = BASE_DIR / "config" / "ai_skills.json"


DEFAULT_SKILLS = {
    "course_invite_strategy": {
        "label": "課程邀約策略",
        "description": "控制課程邀約、課程文宣與邀約文宣生成時的高階寫作原則。",
        "instruction": (
            "先保留真誠與低壓邀約原則，再依對象熟悉度調整語氣。"
            "內容應聚焦在環境價值、成長機會、夢想感與下一步行動。"
            "避免浮誇承諾、避免過度推銷、避免給人壓迫感。"
        ),
    },
    "nutrition_assessment_strategy": {
        "label": "營養評估策略",
        "description": "控制餐點照片分析與整體飲食評估報告的專業角度與說明方式。",
        "instruction": (
            "先以可觀察事實為主，再提出推論。"
            "強調營養均衡、DRI 對照、長期風險與可執行建議。"
            "不做醫療診斷，不把推估包裝成確定事實。"
        ),
    },
    "followup_suggestion_strategy": {
        "label": "跟進建議策略",
        "description": "控制潛在家人與夥伴跟進建議時的關係經營與分階段陪伴原則。",
        "instruction": (
            "先根據資料判斷目前最適合的關心切角，再提供 7 天與 30 天的行動建議。"
            "強調陪伴、好奇、夢想感、環境價值與節奏，不要過度進逼。"
            "建議要具體可執行，並包含一段可直接使用的訊息範例。"
        ),
    },
}


def _ensure_file():
    SKILL_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SKILL_FILE.exists():
        with open(SKILL_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SKILLS, f, ensure_ascii=False, indent=2)


def load_skills() -> dict:
    _ensure_file()
    with open(SKILL_FILE, encoding="utf-8") as f:
        data = json.load(f)
    merged = {}
    for key, default in DEFAULT_SKILLS.items():
        item = dict(default)
        item.update(data.get(key, {}))
        merged[key] = item
    for key, item in data.items():
        if key not in merged:
            merged[key] = item
    return merged


def save_skills(data: dict):
    _ensure_file()
    with open(SKILL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_skill_labels() -> list[dict]:
    data = load_skills()
    return [
        {"key": key, "label": item.get("label", key), "description": item.get("description", "")}
        for key, item in data.items()
    ]


def get_skill(key: str) -> dict | None:
    return load_skills().get(key)


def render_skill(key: str) -> str:
    item = get_skill(key)
    if not item:
        raise KeyError(key)
    return item["instruction"]


def update_skill(key: str, content: str) -> str:
    data = load_skills()
    if key not in data:
        return f"找不到這組 skill key：{key}"
    data[key]["instruction"] = content.strip()
    save_skills(data)
    return f"已更新 AI skill：{key}"


def format_skill_list() -> str:
    rows = list_skill_labels()
    lines = ["AI skill 清單："]
    for item in rows:
        lines.append(f"- {item['key']}｜{item['label']}")
    return "\n".join(lines)


def format_skill_detail(key: str) -> str:
    item = get_skill(key)
    if not item:
        return f"找不到這組 skill key：{key}"
    return (
        f"AI skill：{key}\n"
        f"名稱：{item.get('label', '')}\n"
        f"說明：{item.get('description', '')}\n\n"
        f"{item.get('instruction', '')}"
    )


def handle_command(command: str) -> str:
    msg = (command or "").strip()
    if msg == "查詢AI技能":
        return format_skill_list()
    if msg.startswith("查詢AI技能 "):
        return format_skill_detail(msg.replace("查詢AI技能", "", 1).strip())
    if msg.startswith("更新AI技能 "):
        raw = msg.replace("更新AI技能", "", 1).strip()
        parts = [p.strip() for p in raw.split("|", 1)]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            return "格式：更新AI技能 key | 內容"
        return update_skill(parts[0], parts[1])
    return ""
