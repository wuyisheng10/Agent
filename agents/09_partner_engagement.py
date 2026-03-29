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
    value = (value or "").strip()
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
        parts.append(f"獎金%：{item['percent']}")
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
