import json
import re
from datetime import date, datetime
from hashlib import md5
from pathlib import Path


BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
PARTNER_DIR = BASE_DIR / "output" / "partners"
PARTNER_FILE = PARTNER_DIR / "partners.json"
LOG_FILE = BASE_DIR / "logs" / "partner_log.txt"

PURCHASE_KEYS = ["this_month", "last_month", "prev2_month", "prev3_month"]
EMPTY_MARKERS = {"", "-", "無", "查詢", "null", "None"}


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [PARTNER] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def ensure_dirs():
    PARTNER_DIR.mkdir(parents=True, exist_ok=True)


def load_partners() -> list[dict]:
    ensure_dirs()
    if PARTNER_FILE.exists():
        with open(PARTNER_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_partners(items: list[dict]):
    ensure_dirs()
    with open(PARTNER_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _clean(value: str) -> str:
    value = (value or "").replace("\ufeff", "").strip()
    return "" if value in EMPTY_MARKERS else value


def _partner_id(name: str, amway_no: str = "") -> str:
    if amway_no:
        return f"PTN-{amway_no.strip()}"
    return "PTN-" + md5(name.strip().lower().encode("utf-8")).hexdigest()[:8].upper()


def _normalize_date(raw: str) -> str:
    raw = raw.strip().replace("/", "-")
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw)
    if not m:
        raise ValueError("日期格式需為 YYYY-MM-DD")
    y, mo, d = map(int, m.groups())
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _roc_to_iso(raw: str) -> str:
    raw = raw.strip()
    m = re.fullmatch(r"(\d{2,3})/(\d{1,2})/(\d{1,2})", raw)
    if not m:
        return raw
    y, mo, d = map(int, m.groups())
    return f"{y + 1911:04d}-{mo:02d}-{d:02d}"


def _sort_key(item: dict):
    return (
        item.get("next_followup") or "9999-12-31",
        str(item.get("level", "")),
        item.get("name", ""),
    )


def _find_partner(name_or_id: str, partners: list[dict]) -> dict | None:
    key = name_or_id.strip()
    for item in partners:
        if item.get("id") == key or item.get("name") == key or item.get("amway_no") == key:
            return item
    return None


def _append_record(item: dict, record_type: str, content: str, next_followup: str = ""):
    item.setdefault("records", [])
    item["records"].append(
        {
            "time": datetime.now().isoformat(),
            "type": record_type,
            "content": content.strip(),
            "next_followup": next_followup,
        }
    )
    item["updated_at"] = datetime.now().isoformat()
    if next_followup:
        item["next_followup"] = next_followup


def _format_partner(item: dict) -> str:
    parts = [f"- {item['name']}"]
    if item.get("level"):
        parts.append(f"層級{item['level']}")
    if item.get("category"):
        parts.append(f"分類：{item['category']}")
    if item.get("stage"):
        parts.append(f"狀態：{item['stage']}")
    if item.get("next_followup"):
        parts.append(f"下次跟進：{item['next_followup']}")
    if item.get("amway_no"):
        parts.append(f"編號：{item['amway_no']}")
    return "｜".join(parts)


def list_partners(title: str, items: list[dict]) -> str:
    if not items:
        return f"{title}\n目前沒有資料。"
    lines = [title]
    for item in items[:20]:
        lines.append(_format_partner(item))
    if len(items) > 20:
        lines.append(f"其餘 {len(items) - 20} 筆請用姓名查詢。")
    return "\n".join(lines)


def due_partners() -> list[dict]:
    today = date.today().isoformat()
    items = [p for p in load_partners() if p.get("next_followup") and p["next_followup"] <= today]
    return sorted(items, key=_sort_key)


def upcoming_partners() -> list[dict]:
    today = date.today().isoformat()
    items = [p for p in load_partners() if p.get("next_followup") and p["next_followup"] >= today]
    return sorted(items, key=_sort_key)


def _infer_stage(item: dict) -> str:
    purchase_flags = item.get("purchase_flags", {})
    if any(value == "V" for value in purchase_flags.values()):
        return "穩定購貨"
    sales = item.get("group_sales", "0").replace(",", "")
    if sales not in {"", "0"}:
        return "有組織活躍"
    if item.get("type") == "會員":
        return "會員觀察中"
    return "待跟進"


def _partner_note(item: dict) -> str:
    parts = []
    if item.get("category"):
        parts.append(f"分類:{item['category']}")
    if item.get("type"):
        parts.append(f"類型:{item['type']}")
    if item.get("authorized"):
        parts.append(f"個資授權:{item['authorized']}")
    if item.get("amway_no"):
        parts.append(f"編號:{item['amway_no']}")
    if item.get("sponsor"):
        parts.append(f"推薦人:{item['sponsor']}")
    if item.get("partner"):
        parts.append(f"合夥人:{item['partner']}")
    if item.get("expire_date"):
        parts.append(f"到期日:{item['expire_date']}")
    if item.get("year_month"):
        parts.append(f"年月:{item['year_month']}")
    if item.get("percent"):
        parts.append(f"獎金%:{item['percent']}")
    if item.get("first_bonus_percent"):
        parts.append(f"首次獎金%:{item['first_bonus_percent']}")
    if item.get("recent_title"):
        parts.append(f"一年內新上獎銜:{item['recent_title']}")
    if item.get("cash_voucher"):
        parts.append(f"現金抵用券:{item['cash_voucher']}")
    if item.get("shopping_points"):
        parts.append(f"購物積點:{item['shopping_points']}")
    if item.get("coupon"):
        parts.append(f"優惠券:{item['coupon']}")
    if item.get("contact_info"):
        parts.append(f"聯絡資訊:{item['contact_info']}")
    return "；".join(parts)


def _build_partner_item(item: dict) -> dict:
    now = datetime.now().isoformat()
    result = {
        "id": _partner_id(item["name"], item.get("amway_no", "")),
        "name": item["name"],
        "goal": item.get("goal", ""),
        "note": item.get("note", ""),
        "stage": item.get("stage", ""),
        "next_followup": item.get("next_followup", ""),
        "records": item.get("records", []),
        "created_at": item.get("created_at", now),
        "updated_at": now,
        "level": item.get("level", ""),
        "category": item.get("category", ""),
        "authorized": item.get("authorized", ""),
        "type": item.get("type", ""),
        "amway_no": item.get("amway_no", ""),
        "partner": item.get("partner", ""),
        "sponsor": item.get("sponsor", ""),
        "expire_date": item.get("expire_date", ""),
        "year_month": item.get("year_month", ""),
        "group_sales": item.get("group_sales", ""),
        "group_points": item.get("group_points", ""),
        "member_points": item.get("member_points", ""),
        "percent": item.get("percent", ""),
        "first_bonus_percent": item.get("first_bonus_percent", ""),
        "recent_title": item.get("recent_title", ""),
        "cash_voucher": item.get("cash_voucher", ""),
        "shopping_points": item.get("shopping_points", ""),
        "coupon": item.get("coupon", ""),
        "this_month_purchase": item.get("this_month_purchase", ""),
        "purchase_flags": item.get("purchase_flags", {k: "" for k in PURCHASE_KEYS}),
        "contact_info": item.get("contact_info", ""),
    }
    if not result["stage"]:
        result["stage"] = _infer_stage(result)
    if not result["note"]:
        result["note"] = _partner_note(result)
    return result


def import_partner_roster(raw_text: str) -> dict:
    lines = [_clean(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if line]

    records = []
    i = 0
    while i < len(lines):
        if not re.fullmatch(r"\d+", lines[i]):
            i += 1
            continue
        if i + 4 >= len(lines) or lines[i + 1] != "授權" or lines[i + 2] not in {"直銷商", "會員"}:
            i += 1
            continue

        level = lines[i]
        authorized = lines[i + 1]
        member_type = lines[i + 2]
        amway_no = lines[i + 3]
        name = lines[i + 4]
        if not re.fullmatch(r"\d{7}", amway_no):
            i += 1
            continue

        j = i + 5
        pre_date = []
        while j < len(lines) and not re.fullmatch(r"\d{2,3}/\d{1,2}/\d{1,2}", lines[j]):
            pre_date.append(lines[j])
            j += 1
        if j >= len(lines):
            break

        expire_date = _roc_to_iso(lines[j])
        j += 1
        metrics = lines[j:j + 4]
        if len(metrics) < 4:
            break
        group_sales, group_points, member_points, percent = metrics
        j += 4

        tail = []
        while j < len(lines):
            if (
                re.fullmatch(r"\d+", lines[j])
                and j + 2 < len(lines)
                and lines[j + 1] == "授權"
                and lines[j + 2] in {"直銷商", "會員"}
            ):
                break
            tail.append(lines[j])
            j += 1

        partner_name = pre_date[0] if len(pre_date) >= 2 else ""
        sponsor = pre_date[1] if len(pre_date) >= 2 else (pre_date[0] if len(pre_date) == 1 else "")

        cash_voucher = ""
        shopping_points = ""
        coupon = ""
        flags = []
        contact_info = ""

        if tail:
            cash_voucher = tail[0] if tail and tail[0] in {"有", "無"} else ""
            shopping_points = tail[1] if len(tail) >= 2 else ""
            coupon = tail[2] if len(tail) >= 3 and tail[2] in {"有", "無"} else ""
            flags = tail[3:7] if len(tail) > 3 else []
            extra = tail[7:] if len(tail) > 7 else []
            if extra:
                contact_info = " ".join([x for x in extra if x != "查詢"])

        purchase_flags = {key: "" for key in PURCHASE_KEYS}
        for key, value in zip(PURCHASE_KEYS, flags):
            purchase_flags[key] = value

        record = _build_partner_item(
            {
                "name": name,
                "level": level,
                "authorized": authorized,
                "type": member_type,
                "amway_no": amway_no,
                "partner": _clean(partner_name),
                "sponsor": _clean(sponsor),
                "expire_date": expire_date,
                "group_sales": group_sales,
                "group_points": group_points,
                "member_points": member_points,
                "percent": percent,
                "cash_voucher": cash_voucher,
                "shopping_points": shopping_points,
                "coupon": coupon,
                "this_month_purchase": purchase_flags["this_month"],
                "purchase_flags": purchase_flags,
                "contact_info": contact_info,
            }
        )
        records.append(record)
        i = j

    existing_items = load_partners()
    merged = {}
    for item in existing_items:
        merged[item["id"]] = item

    imported = 0
    for item in records:
        existing = merged.get(item["id"])
        if existing:
            item["records"] = existing.get("records", [])
            item["goal"] = existing.get("goal", "")
            item["next_followup"] = existing.get("next_followup", "")
            item["category"] = existing.get("category", "")
            item["created_at"] = existing.get("created_at", item["created_at"])
            if existing.get("stage") and existing.get("stage") not in {"待跟進", "會員觀察中", "有組織活躍", "穩定購貨"}:
                item["stage"] = existing["stage"]
            if existing.get("note"):
                item["note"] = existing["note"]
        merged[item["id"]] = item
        imported += 1

    items = sorted(merged.values(), key=_sort_key)
    save_partners(items)
    log(f"已匯入夥伴名單：{imported} 筆，總數 {len(items)} 筆")
    return {"imported": imported, "total": len(items)}


def add_partner(command: str) -> str:
    prefix = "新增夥伴"
    if not command.strip().startswith(prefix):
        return "格式：新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類"
    raw = command.strip()[len(prefix):].strip()
    if not raw:
        return "格式：新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類"
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) < 5:
        parts.extend([""] * (5 - len(parts)))
    name, goal, next_followup, note, category = parts[:5]
    if not name:
        return "格式：新增夥伴 姓名 | 目標 | 下次跟進日期 | 備註 | 分類"
    next_followup = _normalize_date(next_followup) if next_followup else ""
    category = category.upper()
    partners = load_partners()
    if _find_partner(name, partners):
        return f"夥伴已存在：{name}"
    item = _build_partner_item({
        "name": name,
        "goal": goal,
        "note": note,
        "next_followup": next_followup,
        "stage": "待跟進",
        "category": category,
    })
    partners.append(item)
    save_partners(sorted(partners, key=_sort_key))
    lines = [f"已新增夥伴：{name}"]
    if category:
        lines.append(f"分類：{category}")
    if next_followup:
        lines.append(f"下次跟進：{next_followup}")
    return "\n".join(lines)


def update_partner(command: str) -> str:
    prefix = "更新夥伴"
    if not command.strip().startswith(prefix):
        return "格式：更新夥伴 姓名 | 層級 | 近況 | 下次跟進日期 | 聯絡資訊 | 備註 | 類型 | 編號 | 合夥人 | 推薦人 | 到期日 | 年月 | 一年內新上獎銜 | 首次獎金% | 現金抵用券 | 購物積點 | 優惠券 | 本月購貨 | 上月購貨 | 前2月購貨 | 前3月購貨 | 分類"
    raw = command.strip()[len(prefix):].strip()
    if not raw:
        return "格式：更新夥伴 姓名 | 層級 | 近況 | 下次跟進日期 | 聯絡資訊 | 備註 | 類型 | 編號 | 合夥人 | 推薦人 | 到期日 | 年月 | 一年內新上獎銜 | 首次獎金% | 現金抵用券 | 購物積點 | 優惠券 | 本月購貨 | 上月購貨 | 前2月購貨 | 前3月購貨 | 分類"
    parts = [part.strip() for part in raw.split("|")]
    if len(parts) < 22:
        parts.extend([""] * (22 - len(parts)))
    (
        target,
        level,
        stage,
        next_followup,
        contact_info,
        note,
        partner_type,
        amway_no,
        partner_name,
        sponsor,
        expire_date,
        year_month,
        recent_title,
        first_bonus_percent,
        cash_voucher,
        shopping_points,
        coupon,
        this_month_purchase,
        last_month_purchase,
        prev2_month_purchase,
        prev3_month_purchase,
        category,
    ) = parts
    partners = load_partners()
    item = _find_partner(target, partners)
    if not item:
        return f"找不到夥伴：{target}"
    if level and level != "-":
        item["level"] = level
    if stage and stage != "-":
        item["stage"] = stage
    if next_followup and next_followup != "-":
        item["next_followup"] = _normalize_date(next_followup)
    if contact_info and contact_info != "-":
        item["contact_info"] = contact_info
    if note and note != "-":
        item["note"] = note
    if partner_type and partner_type != "-":
        item["type"] = partner_type
    if category and category != "-":
        item["category"] = category.upper()
    if amway_no and amway_no != "-":
        item["amway_no"] = amway_no
        item["id"] = _partner_id(item["name"], amway_no)
    if partner_name and partner_name != "-":
        item["partner"] = partner_name
    if sponsor and sponsor != "-":
        item["sponsor"] = sponsor
    if expire_date and expire_date != "-":
        item["expire_date"] = _normalize_date(expire_date)
    if year_month and year_month != "-":
        item["year_month"] = year_month
    if recent_title and recent_title != "-":
        item["recent_title"] = recent_title
    if first_bonus_percent and first_bonus_percent != "-":
        item["first_bonus_percent"] = first_bonus_percent
    if cash_voucher and cash_voucher != "-":
        item["cash_voucher"] = cash_voucher
    if shopping_points and shopping_points != "-":
        item["shopping_points"] = shopping_points
    if coupon and coupon != "-":
        item["coupon"] = coupon
    purchase_flags = item.get("purchase_flags", {k: "" for k in PURCHASE_KEYS})
    for key, value in [
        ("this_month", this_month_purchase),
        ("last_month", last_month_purchase),
        ("prev2_month", prev2_month_purchase),
        ("prev3_month", prev3_month_purchase),
    ]:
        if value and value != "-":
            purchase_flags[key] = value
    item["purchase_flags"] = purchase_flags
    if this_month_purchase and this_month_purchase != "-":
        item["this_month_purchase"] = this_month_purchase
    _append_record(
        item,
        "update",
        f"更新資料：層級={item.get('level','')}，狀態={item.get('stage','')}，類型={item.get('type','')}，分類={item.get('category','')}，編號={item.get('amway_no','')}，年月={item.get('year_month','')}，獎銜={item.get('recent_title','')}，現金抵用券={item.get('cash_voucher','')}",
        item.get("next_followup", ""),
    )
    save_partners(sorted(partners, key=_sort_key))
    return f"已更新夥伴：{item['name']}"


def invite_partner(command: str) -> str:
    m = re.fullmatch(r"邀約夥伴\s+(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})(?:\s*\|\s*(.+))?", command.strip())
    if not m:
        return "格式：邀約夥伴 姓名 | 活動名稱 | 下次跟進日期 | 備註"
    target, activity, next_followup, note = m.group(1).strip(), m.group(2).strip(), _normalize_date(m.group(3)), (m.group(4) or "").strip()
    partners = load_partners()
    item = _find_partner(target, partners)
    if not item:
        return f"找不到夥伴：{target}"
    item["stage"] = "已邀約活動"
    content = f"已邀約：{activity}" + (f"；{note}" if note else "")
    _append_record(item, "invite", content, next_followup=next_followup)
    save_partners(sorted(partners, key=_sort_key))
    return f"已記錄邀約：{item['name']}\n活動：{activity}\n下次跟進：{next_followup}"


def follow_partner(command: str) -> str:
    m = re.fullmatch(r"跟進夥伴\s+(.+?)\s*\|\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})(?:\s*\|\s*(.+))?", command.strip())
    if not m:
        return "格式：跟進夥伴 姓名 | 狀態 | 下次跟進日期 | 備註"
    target, stage, next_followup, note = m.group(1).strip(), m.group(2).strip(), _normalize_date(m.group(3)), (m.group(4) or "").strip()
    partners = load_partners()
    item = _find_partner(target, partners)
    if not item:
        return f"找不到夥伴：{target}"
    item["stage"] = stage
    _append_record(item, "followup", note or stage, next_followup=next_followup)
    save_partners(sorted(partners, key=_sort_key))
    return f"已更新跟進：{item['name']}\n狀態：{stage}\n下次跟進：{next_followup}"


def motivate_partner(command: str) -> str:
    m = re.fullmatch(r"激勵夥伴\s+(.+)", command.strip())
    if not m:
        return "格式：激勵夥伴 姓名"
    target = m.group(1).strip()
    partners = load_partners()
    item = _find_partner(target, partners)
    if not item:
        return f"找不到夥伴：{target}"
    goal = item.get("goal") or "先建立穩定分享與跟進節奏"
    next_followup = item.get("next_followup") or "請先安排下次跟進"
    msg = (
        f"{item['name']}，你現在的每一步都在累積未來的組織。\n"
        f"先把今天能做的邀約、關心、購貨節奏做好，團隊就會慢慢成形。\n"
        f"目前聚焦：{goal}\n"
        f"下一步：{next_followup}"
    )
    _append_record(item, "motivate", msg)
    save_partners(sorted(partners, key=_sort_key))
    return msg


def delete_partner(command: str) -> str:
    m = re.fullmatch(r"刪除夥伴\s+(.+)", command.strip())
    if not m:
        return "格式：刪除夥伴 姓名"
    target = m.group(1).strip()
    partners = load_partners()
    remaining = [p for p in partners if p.get("name") != target and p.get("id") != target and p.get("amway_no") != target]
    if len(remaining) == len(partners):
        return f"找不到夥伴：{target}"
    save_partners(sorted(remaining, key=_sort_key))
    return f"已刪除夥伴：{target}"


def query_partner(command: str) -> str:
    msg = command.strip()
    if msg == "查詢夥伴":
        return list_partners("夥伴清單", sorted(load_partners(), key=_sort_key))
    if msg == "查詢待跟進夥伴":
        return list_partners("待跟進夥伴", due_partners())
    m = re.fullmatch(r"查詢夥伴\s+(.+)", msg)
    if m:
        target = m.group(1).strip()
        partners = load_partners()
        item = _find_partner(target, partners)
        if not item:
            return f"找不到夥伴：{target}"
        lines = [
            f"{item['name']}｜層級{item.get('level', '') or '-'}｜狀態：{item.get('stage', '待跟進')}",
            f"編號：{item.get('amway_no', '-') or '-'}",
            f"類型：{item.get('type', '-') or '-'}",
            f"分類：{item.get('category', '-') or '-'}",
            f"推薦人：{item.get('sponsor', '-') or '-'}",
            f"合夥人：{item.get('partner', '-') or '-'}",
            f"到期日：{item.get('expire_date', '-') or '-'}",
            f"年月：{item.get('year_month', '-') or '-'}",
            f"小組售貨額：{item.get('group_sales', '-') or '-'}",
            f"小組積分額：{item.get('group_points', '-') or '-'}",
            f"會員積分額：{item.get('member_points', '-') or '-'}",
            f"獎金%：{item.get('percent', '-') or '-'}",
            f"一年內新上獎銜：{item.get('recent_title', '-') or '-'}",
            f"首次獎金%：{item.get('first_bonus_percent', '-') or '-'}",
            f"現金抵用券：{item.get('cash_voucher', '-') or '-'}",
            f"購物積點：{item.get('shopping_points', '-') or '-'}",
            f"優惠券：{item.get('coupon', '-') or '-'}",
            f"本月購貨：{item.get('purchase_flags', {}).get('this_month', '-') or '-'}",
            f"上月購貨：{item.get('purchase_flags', {}).get('last_month', '-') or '-'}",
            f"前2月購貨：{item.get('purchase_flags', {}).get('prev2_month', '-') or '-'}",
            f"前3月購貨：{item.get('purchase_flags', {}).get('prev3_month', '-') or '-'}",
            f"聯絡資訊：{item.get('contact_info', '-') or '-'}",
            f"下次跟進：{item.get('next_followup', '-') or '-'}",
        ]
        if item.get("goal"):
            lines.append(f"目標：{item['goal']}")
        if item.get("note"):
            lines.append(f"備註：{item['note']}")
        records = item.get("records", [])[-5:]
        if records:
            lines.append("最近紀錄：")
            for record in records:
                lines.append(f"- {record['type']}｜{record['content']}")
        return "\n".join(lines)
    return ""


def handle_partner_command(command: str) -> str:
    msg = command.strip()
    if msg.startswith("新增夥伴"):
        return add_partner(msg)
    if msg.startswith("更新夥伴"):
        return update_partner(msg)
    if msg.startswith("邀約夥伴"):
        return invite_partner(msg)
    if msg.startswith("跟進夥伴"):
        return follow_partner(msg)
    if msg.startswith("激勵夥伴"):
        return motivate_partner(msg)
    if msg.startswith("刪除夥伴"):
        return delete_partner(msg)
    if msg == "查詢夥伴" or msg == "查詢待跟進夥伴" or msg.startswith("查詢夥伴 "):
        return query_partner(msg)
    if msg.startswith("匯入夥伴名單"):
        raw = msg[len("匯入夥伴名單"):].strip()
        if not raw:
            return "格式：匯入夥伴名單\\n名單內容"
        result = import_partner_roster(raw)
        return f"已匯入夥伴名單：{result['imported']} 筆，目前共 {result['total']} 筆。"
    return ""
