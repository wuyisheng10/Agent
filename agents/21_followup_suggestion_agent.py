from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

try:
    from common_runtime import BASE_DIR, run_codex_cli
except ModuleNotFoundError:
    from agents.common_runtime import BASE_DIR, run_codex_cli


MARKET_CSV = BASE_DIR / "output" / "csv_data" / "market_list.csv"
PARTNER_JSON = BASE_DIR / "output" / "partners" / "partners.json"
LOG_FILE = BASE_DIR / "logs" / "followup_suggestion_log.txt"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [FOLLOWUP_SUGGESTION] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _load_market_rows() -> list[dict]:
    if not MARKET_CSV.exists():
        return []
    with open(MARKET_CSV, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _load_partners() -> list[dict]:
    if not PARTNER_JSON.exists():
        return []
    with open(PARTNER_JSON, encoding="utf-8") as f:
        return json.load(f)


def _find_prospect(name: str) -> dict | None:
    key = (name or "").strip()
    for row in _load_market_rows():
        if str(row.get("姓名", "")).strip() == key:
            return row
    return None


def _find_partner(name: str) -> dict | None:
    key = (name or "").strip()
    for item in _load_partners():
        if str(item.get("name", "")).strip() == key or str(item.get("id", "")).strip() == key or str(item.get("amway_no", "")).strip() == key:
            return item
    return None


def list_prospect_names(limit: int = 20) -> list[str]:
    return [str(row.get("姓名", "")).strip() for row in _load_market_rows() if str(row.get("姓名", "")).strip()][:limit]


def list_partner_names(limit: int = 20) -> list[str]:
    return [str(item.get("name", "")).strip() for item in _load_partners() if str(item.get("name", "")).strip()][:limit]


def _format_prospect_profile(row: dict) -> str:
    ordered_keys = [
        "姓名",
        "電話",
        "職業",
        "接觸管道",
        "備註",
        "AI評分",
        "需求標籤",
        "接觸狀態",
        "最後更新",
        "下次跟進日",
        "地區",
        "地址",
        "使用產品",
        "淨水器型號",
        "濾心上次換",
        "濾心下次換",
        "體驗記錄",
        "話術_健康型",
        "話術_收入型",
        "話術_好奇型",
    ]
    lines = []
    for key in ordered_keys:
        value = str(row.get(key, "") or "").strip()
        if value:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) if lines else "無可用背景資料。"


def _format_partner_profile(item: dict) -> str:
    lines = []
    mapping = [
        ("姓名", item.get("name", "")),
        ("層級", item.get("level", "")),
        ("分類", item.get("category", "")),
        ("狀態", item.get("stage", "")),
        ("目標", item.get("goal", "")),
        ("聯絡資訊", item.get("contact_info", "")),
        ("推薦人", item.get("sponsor", "")),
        ("合夥人", item.get("partner", "")),
        ("類型", item.get("type", "")),
        ("編號", item.get("amway_no", "")),
        ("備註", item.get("note", "")),
        ("下次跟進", item.get("next_followup", "")),
    ]
    for key, value in mapping:
        value = str(value or "").strip()
        if value:
            lines.append(f"{key}: {value}")

    records = item.get("records", [])[-8:]
    if records:
        lines.append("跟進紀錄:")
        for record in records:
            stamp = str(record.get("time", "")).replace("T", " ")[:16]
            rtype = str(record.get("type", "")).strip()
            content = str(record.get("content", "")).strip()
            next_followup = str(record.get("next_followup", "")).strip()
            suffix = f" / 下次跟進:{next_followup}" if next_followup else ""
            lines.append(f"- {stamp} | {rtype} | {content}{suffix}")

    return "\n".join(lines) if lines else "無可用背景資料。"


def _contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def _prospect_features(row: dict) -> dict:
    note = " ".join(
        str(row.get(k, "") or "").strip()
        for k in ["備註", "需求標籤", "接觸狀態", "地區", "地址", "使用產品", "淨水器型號", "體驗記錄"]
    )
    job = str(row.get("職業", "") or "").strip()
    status = str(row.get("接觸狀態", "") or "").strip()
    tag = str(row.get("需求標籤", "") or "").strip()
    features = {
        "uses_product": bool(str(row.get("使用產品", "")).strip() or str(row.get("淨水器型號", "")).strip()),
        "health_interest": _contains_any(note + " " + tag, ["健康", "保養", "淨水", "體驗", "健康需求"]),
        "income_interest": _contains_any(note + " " + tag, ["收入", "副業", "賺錢", "機會"]),
        "dream_interest": _contains_any(note, ["夢想", "目標", "自由", "想要", "渴望"]),
        "busy_professional": _contains_any(job, ["治療師", "老師", "護理", "業務", "工程", "設計", "顧問"]),
        "new_contact": status in {"待接觸", "新增", "未接觸"},
        "has_experience": bool(str(row.get("體驗記錄", "")).strip()),
        "nearby": _contains_any(note, ["附近", "很近", "中壢", "台中", "台南", "屏東", "桃園"]),
    }
    return features


def _partner_features(item: dict) -> dict:
    note = " ".join(
        str(item.get(k, "") or "").strip()
        for k in ["note", "goal", "stage", "category", "contact_info"]
    )
    records = item.get("records", [])[-8:]
    record_text = " ".join(str(r.get("content", "") or "").strip() for r in records)
    stage = str(item.get("stage", "") or "").strip()
    category = str(item.get("category", "") or "").strip().upper()
    features = {
        "active_followup": stage in {"待跟進", "跟進中"},
        "needs_encouragement": stage in {"激勵", "低潮", "觀望"},
        "category_a": category == "A",
        "category_b": category == "B",
        "category_c": category == "C",
        "has_goal": bool(str(item.get("goal", "")).strip()),
        "recent_invite": _contains_any(record_text, ["邀約", "會議", "OPP", "培訓"]),
        "recent_stall": _contains_any(record_text + " " + note, ["忙", "沒空", "再看看", "考慮", "拒絕"]),
        "product_user": any(str(v).strip().upper() == "V" for v in (item.get("purchase_flags") or {}).values()) or bool(str(item.get("group_sales", "")).strip("0,.")),
    }
    return features


def _prospect_strategy(features: dict) -> tuple[str, list[str]]:
    reasons = []
    if features["health_interest"] or features["uses_product"]:
        strategy = "健康體驗切入型"
        reasons.append("對方對健康、淨水或產品體驗較有連結")
    elif features["income_interest"]:
        strategy = "副業機會切入型"
        reasons.append("對方可能對收入與選擇權有感")
    elif features["dream_interest"]:
        strategy = "夢想目標切入型"
        reasons.append("對方可能會被夢想、目標與人生選擇吸引")
    elif features["new_contact"]:
        strategy = "低壓暖身型"
        reasons.append("對方仍屬於初期接觸，不適合直接推機會")
    else:
        strategy = "環境好奇切入型"
        reasons.append("目前沒有強需求訊號，先讓他對環境與人產生好奇")
    if features["busy_professional"]:
        reasons.append("工作偏忙，跟進頻率要短而輕")
    if features["nearby"]:
        reasons.append("地緣接近，可安排輕鬆見面或體驗")
    return strategy, reasons


def _partner_strategy(features: dict) -> tuple[str, list[str]]:
    reasons = []
    if features["needs_encouragement"]:
        strategy = "先扶持狀態型"
        reasons.append("對方目前更需要被鼓勵與被理解")
    elif features["category_c"]:
        strategy = "陪伴建立信心型"
        reasons.append("對方還在了解階段，要先建立認同感")
    elif features["category_b"] or features["recent_stall"]:
        strategy = "低壓恢復節奏型"
        reasons.append("對方有基礎，但需要重新找回節奏")
    elif features["category_a"] and features["recent_invite"]:
        strategy = "帶入會議成長型"
        reasons.append("對方已有基礎且最近有互動，可以往活動與帶線前進")
    elif features["product_user"]:
        strategy = "產品成果放大型"
        reasons.append("對方已有產品基礎，可連回生活改變與分享")
    else:
        strategy = "關係維持觀察型"
        reasons.append("目前訊號不明確，先穩定維持關係")
    if features["has_goal"]:
        reasons.append("已有目標，可把關心與目標感重新連結")
    return strategy, reasons


def _strategy_block(strategy: str, reasons: list[str], person_type: str) -> str:
    lines = [
        f"建議主策略：{strategy}",
        "策略判斷原因：",
    ]
    lines.extend(f"- {r}" for r in reasons)
    lines.append("")
    if person_type == "潛在家人":
        if strategy == "低壓暖身型":
            lines.extend([
                "接下來7天如何關心：",
                "- 先關心近況、工作與生活節奏。",
                "- 不談制度，先分享你最近接觸到的正向人與好環境。",
                "- 找一個輕話題讓對方願意回你。",
                "接下來30天如何鋪陳：",
                "- 從聊天轉為一次輕鬆見面或產品體驗。",
                "- 若對方有回應，再慢慢引到夢想、環境與事業可能。",
            ])
        elif strategy == "健康體驗切入型":
            lines.extend([
                "接下來7天如何關心：",
                "- 用健康、生活品質、飲水或保養切入。",
                "- 先交換經驗，不急著教育。",
                "- 有機會時邀請低門檻體驗。",
                "接下來30天如何鋪陳：",
                "- 從體驗感受過渡到『為什麼有人願意持續經營這個環境』。",
                "- 讓對方先好奇人與文化，再談機會。",
            ])
        elif strategy == "副業機會切入型":
            lines.extend([
                "接下來7天如何關心：",
                "- 關心工作壓力與時間分配。",
                "- 輕描淡寫提到你看到一種不必立刻辭職、但能多一個選擇的方式。",
                "接下來30天如何鋪陳：",
                "- 找時機讓他接觸有目標感、又務實的人。",
                "- 把焦點放在選擇權，不是畫大餅。",
            ])
        elif strategy == "夢想目標切入型":
            lines.extend([
                "接下來7天如何關心：",
                "- 多問他想過怎樣的生活、最近在追什麼目標。",
                "- 分享你最近對夢想與環境的感受。",
                "接下來30天如何鋪陳：",
                "- 讓他接觸會談夢想也談落地行動的人。",
                "- 再自然帶到事業機會與支持系統。",
            ])
        else:
            lines.extend([
                "接下來7天如何關心：",
                "- 先從好奇、有趣、生活感話題切入。",
                "- 讓對方先對你最近接觸的人與環境產生好奇。",
                "接下來30天如何鋪陳：",
                "- 用一次短活動或見面，把抽象好奇變成具體感受。",
                "- 等他自己想問更多時再往下談。",
            ])
    else:
        if strategy == "先扶持狀態型":
            lines.extend([
                "接下來7天如何關心：",
                "- 先處理情緒與狀態，不急著談業績。",
                "- 每次互動都讓他感覺被看見、被理解。",
                "接下來30天如何鋪陳：",
                "- 幫他找回一個小贏面，例如一次參會、一次回報、一次簡單邀約。",
                "- 等狀態回來後再談更進一步目標。",
            ])
        elif strategy == "陪伴建立信心型":
            lines.extend([
                "接下來7天如何關心：",
                "- 先建立信心，不用丟太大目標。",
                "- 提供簡單、可完成的小動作。",
                "接下來30天如何鋪陳：",
                "- 用會議、回報、市場小成果堆出安全感。",
                "- 慢慢讓他感受到環境的支持。",
            ])
        elif strategy == "低壓恢復節奏型":
            lines.extend([
                "接下來7天如何關心：",
                "- 問近況、找卡點、不要責備。",
                "- 幫他訂一個可做到的回歸節奏。",
                "接下來30天如何鋪陳：",
                "- 每週協助校正一次，讓他重新感受到成長與進度。",
            ])
        elif strategy == "帶入會議成長型":
            lines.extend([
                "接下來7天如何關心：",
                "- 聚焦下一場最適合的會議或活動。",
                "- 協助他帶著明確問題去參加。",
                "接下來30天如何鋪陳：",
                "- 讓他把會議收穫轉成市場動作與帶線習慣。",
            ])
        elif strategy == "產品成果放大型":
            lines.extend([
                "接下來7天如何關心：",
                "- 從產品使用感受與生活改變切入。",
                "- 讓他先會講自己故事。",
                "接下來30天如何鋪陳：",
                "- 再慢慢把故事延伸成分享與邀約能力。",
            ])
        else:
            lines.extend([
                "接下來7天如何關心：",
                "- 維持穩定關心，不要消失。",
                "- 多觀察他最近真正卡住的是什麼。",
                "接下來30天如何鋪陳：",
                "- 找到最適合他的切入點後，再往活動或目標帶。",
            ])
    return "\n".join(lines)


def _fallback_suggestion(person_type: str, name: str, profile_text: str, strategy: str, reasons: list[str]) -> str:
    return (
        f"跟進建議｜{person_type}｜{name}\n\n"
        f"{_strategy_block(strategy, reasons, person_type)}\n\n"
        "對象觀察重點\n"
        "- 先順著他目前最在意的生活面向關心，不要急著切事業。\n"
        "- 先讓他感受到你是真的記得他的情況與需求。\n\n"
        "可以引起好奇的切入角度\n"
        "- 正向環境帶來的改變\n"
        "- 夢想被支持、被看見的感受\n"
        "- 更健康、更自由、更有選擇權的生活\n\n"
        "不要踩到的點\n"
        "- 不要高壓推銷。\n"
        "- 不要一次講太多制度或產品細節。\n"
        "- 不要忽略他現在的生活壓力與節奏。\n\n"
        "可直接使用的關心訊息範例\n"
        f"- {name}，最近想到你，因為我記得你現在的狀態和目標。我最近接觸一個很正向的環境，讓我重新思考生活、夢想和未來的可能。有空時想和你聊聊近況，也想聽聽你最近最在意的是什麼。\n\n"
        f"參考資料\n{profile_text[:900]}"
    )


def _render_prompt(person_type: str, name: str, profile_text: str, strategy: str, reasons: list[str]) -> str:
    reason_text = "\n".join(f"- {r}" for r in reasons)
    return f"""你是成熟的關係經營顧問，擅長依照個人背景與跟進紀錄，設計自然、不油膩、能逐步引起對方好奇的後續關心策略。

目標：
針對以下對象，提出接下來 7 天與 30 天的跟進建議，讓他慢慢對「正向的環境、安麗事業機會、夢想與目標的價值」產生好奇，但不要生硬推銷。

對象類型：{person_type}
姓名：{name}
已判定策略：{strategy}
策略判斷原因：
{reason_text}

背景資料：
{profile_text}

請用繁體中文輸出，格式固定為以下七段：
1. 建議主策略
2. 對象觀察重點
3. 接下來7天如何關心
4. 接下來30天如何鋪陳
5. 可以引起他好奇的切入角度
6. 不要踩到的點
7. 一段可直接使用的關心訊息範例

要求：
- 內容具體，不要空泛口號。
- 必須明確呼應已判定策略，不要寫成通用模板。
- 要引用提供的背景特徵，例如職業、地區、生活狀態、夢想、備註、跟進紀錄。
- 先建立關係，再引發好奇，再視時機帶到環境與機會。
- 不要高壓銷售，不要過度誇張。
"""


def suggest_for_prospect(name: str) -> str:
    row = _find_prospect(name)
    if not row:
        return f"找不到潛在家人：{name}"
    profile_text = _format_prospect_profile(row)
    features = _prospect_features(row)
    strategy, reasons = _prospect_strategy(features)
    prompt = _render_prompt("潛在家人", name, profile_text, strategy, reasons)
    try:
        return run_codex_cli(prompt, timeout=90)
    except Exception as exc:
        log(f"prospect suggestion fallback: {exc}")
        return _fallback_suggestion("潛在家人", name, profile_text, strategy, reasons)


def suggest_for_partner(name: str) -> str:
    item = _find_partner(name)
    if not item:
        return f"找不到夥伴：{name}"
    profile_text = _format_partner_profile(item)
    features = _partner_features(item)
    strategy, reasons = _partner_strategy(features)
    prompt = _render_prompt("夥伴", name, profile_text, strategy, reasons)
    try:
        return run_codex_cli(prompt, timeout=90)
    except Exception as exc:
        log(f"partner suggestion fallback: {exc}")
        return _fallback_suggestion("夥伴", name, profile_text, strategy, reasons)


def _format_name_list(title: str, names: list[str], example_prefix: str) -> str:
    if not names:
        return f"{title}\n目前沒有可選名單。"
    lines = [title, ""]
    for idx, name in enumerate(names, 1):
        lines.append(f"{idx}. {name}")
    lines.append("")
    lines.append(f"請直接輸入：{example_prefix} 姓名")
    return "\n".join(lines)


class FollowupSuggestionAgent:
    def handle_command(self, command: str) -> str:
        msg = (command or "").strip()
        if msg == "跟進建議 潛在家人":
            return _format_name_list("潛在家人清單", list_prospect_names(), "跟進建議 潛在家人")
        if msg == "跟進建議 夥伴":
            return _format_name_list("夥伴清單", list_partner_names(), "跟進建議 夥伴")
        if msg.startswith("跟進建議 潛在家人 "):
            name = msg.replace("跟進建議 潛在家人 ", "", 1).strip()
            if not name:
                return "格式：跟進建議 潛在家人 姓名"
            return suggest_for_prospect(name)
        if msg.startswith("跟進建議 夥伴 "):
            name = msg.replace("跟進建議 夥伴 ", "", 1).strip()
            if not name:
                return "格式：跟進建議 夥伴 姓名"
            return suggest_for_partner(name)
        return ""


if __name__ == "__main__":
    agent = FollowupSuggestionAgent()
    print(agent.handle_command("跟進建議 夥伴"))
