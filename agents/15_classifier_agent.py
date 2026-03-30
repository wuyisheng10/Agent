"""
歸類 Agent
File: C:/Users/user/claude AI_Agent/agents/15_classifier_agent.py
Function: 歸類模式管理 — 支援「人員 + 模式」雙維度，所有上傳內容先暫存、再選項執行
State:   output/classification_mode.json
Archive:
  有指定人員 → output/classified/{人員}/{模式}/{YYYYMMDD}/{subdir}/
  無指定人員 → output/classified/{模式}/{YYYYMMDD}/{subdir}/

LINE 指令：
  小幫手 歸類模式                     → 查詢目前人員與模式
  小幫手 歸類模式 [模式]              → 設定模式（不指定人員）
  小幫手 歸類模式 [人員] [模式]       → 設定人員 + 模式
  小幫手 關閉歸類模式                 → 回到自動模式
  小幫手 查詢歸檔                     → 列出所有已歸檔人員
  小幫手 查詢歸檔 [人員]              → 列出該人員的所有歸檔內容
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR        = Path(r"C:\Users\user\claude AI_Agent")
MODE_FILE       = BASE_DIR / "output" / "classification_mode.json"
CLASSIFIED_DIR  = BASE_DIR / "output" / "classified"
PENDING_DIR     = BASE_DIR / "output" / "pending_archive"
PENDING_FILE_DIR = PENDING_DIR / "files"
PENDING_STATE_DIR = PENDING_DIR / "states"

AVAILABLE_MODES = [
    "會議記錄", "行事曆", "夥伴跟進", "市場開發", "培訓資料", "一般歸檔",
    "整理會議心得", "歸檔會議紀錄", "歸檔行動紀錄", "歸檔文件", "421故事歸檔", "課程文宣歸檔",
    # 安麗產品分類
    "營養保健歸檔", "美容保養歸檔", "居家清潔歸檔", "個人護理歸檔",
    "廚具生活歸檔", "空水設備歸檔", "體重管理歸檔", "香氛風格歸檔", "事業工具歸檔",
    # 故事分類
    "人物故事歸檔", "產品故事歸檔",
]
PENDING_ARCHIVE_MODES = ["整理會議心得", "歸檔會議紀錄", "歸檔行動紀錄", "歸檔文件"]
SPECIAL_PERSONS = ["建德", "宜芸"]

MODE_ICON = {
    "會議記錄": "📝", "行事曆": "🗓️", "夥伴跟進": "🤝",
    "市場開發": "🎯", "培訓資料": "📚", "一般歸檔": "📁", "auto": "🤖",
    "整理會議心得": "🧠", "歸檔會議紀錄": "📝", "歸檔行動紀錄": "✅", "歸檔文件": "📄",
    "421故事歸檔": "📚", "課程文宣歸檔": "📰",
    # 安麗產品
    "營養保健歸檔": "💊", "美容保養歸檔": "💄", "居家清潔歸檔": "🧹",
    "個人護理歸檔": "🪥", "廚具生活歸檔": "🍳", "空水設備歸檔": "💧",
    "體重管理歸檔": "⚖️", "香氛風格歸檔": "🌸", "事業工具歸檔": "🛠️",
    "人物故事歸檔": "👤", "產品故事歸檔": "📖",
}
MODE_DESC = {
    "會議記錄": "圖片→訓練歸檔 ／ 音檔→音訊資料夾 ／ 影片→影片資料夾 ／ PDF/PPTX→檔案資料夾 ／ 文字→備註",
    "行事曆":   "圖片→行事曆解析 ／ 文字→行事曆指令 ／ 檔案→行事曆資料夾",
    "夥伴跟進": "文字→夥伴指令或備註 ／ 圖片＆檔案→夥伴資料夾",
    "市場開發": "文字→潛在客戶備註 ／ 圖片＆檔案→市場資料夾",
    "培訓資料": "所有內容→培訓素材資料夾",
    "一般歸檔": "所有內容→今日日期資料夾",
    "整理會議心得": "先保存素材，後續可再搭配逐字稿整理心得",
    "歸檔會議紀錄": "歸入會議資料夾，保留圖檔、音檔、影片與文件",
    "歸檔行動紀錄": "歸入行動追蹤資料夾，集中保存執行與跟進素材",
    "歸檔文件": "歸入一般文件資料夾",
    "421故事歸檔": "集中歸檔 421 故事相關圖片、影片、文件與文字，並可自訂目錄名稱。",
    "課程文宣歸檔": "集中歸檔課程宣傳圖片、文案、影片與文件，並可自訂目錄名稱。",
    # 安麗產品
    "營養保健歸檔": "Nutrilite 系列－保健品圖片、文件、產品資訊歸檔",
    "美容保養歸檔": "Artistry 系列－保養品圖片、教學、文案歸檔",
    "居家清潔歸檔": "Amway Home 系列－清潔用品圖片、說明歸檔",
    "個人護理歸檔": "Glister 等個人護理品－圖片、產品資訊歸檔",
    "廚具生活歸檔": "Queen Cookware、eSpring 等廚具生活用品歸檔",
    "空水設備歸檔": "空氣清淨機、淨水器等設備圖片、說明書歸檔",
    "體重管理歸檔": "體重管理與運動營養產品資料歸檔",
    "香氛風格歸檔": "香氛與個人風格產品圖片、文案歸檔",
    "事業工具歸檔": "課程、培訓教材、系統工具等事業資源歸檔",
    "人物故事歸檔": "人物見證、成功故事、夥伴經歷等人物相關素材歸檔",
    "產品故事歸檔": "產品見證、使用心得、效果分享等產品相關故事歸檔",
}


# ============================================================
# 工具
# ============================================================

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [CLASSIFIER] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("cp950", errors="replace").decode("cp950"))
    log_file = BASE_DIR / "logs" / "classifier_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _fuzzy_mode(text: str) -> str | None:
    """模糊匹配模式名稱"""
    return next((m for m in AVAILABLE_MODES if text in m or m in text), None)


def _safe_name(name: str) -> str:
    cleaned = "".join(c for c in (name or "") if c.isalnum() or c in "._- ()[]")
    return cleaned.strip() or f"file_{datetime.now().strftime('%H%M%S')}"


def _safe_folder_name(name: str) -> str:
    forbidden = '<>:"/\\|?*'
    cleaned = "".join(c for c in (name or "") if c not in forbidden and ord(c) >= 32)
    return cleaned.strip().strip(".")[:80]


def _parse_archive_date(text: str) -> str | None:
    """
    解析歸檔日期字串，回傳 YYYYMMDD 或 None。
    支援：今日 / 今天 / 昨日 / 昨天 / YYYY-MM-DD / YYYYMMDD
    """
    import re as _re
    from datetime import timedelta
    text = text.strip()
    if text in ("今日", "今天"):
        return datetime.now().strftime("%Y%m%d")
    if text in ("昨日", "昨天"):
        return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    m = _re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return m.group(1) + m.group(2) + m.group(3)
    if _re.fullmatch(r"\d{8}", text):
        try:
            datetime.strptime(text, "%Y%m%d")
            return text
        except ValueError:
            pass
    return None


# ============================================================
# 主要 Agent 類別
# ============================================================

class ClassifierAgent:

    def __init__(self):
        PENDING_FILE_DIR.mkdir(parents=True, exist_ok=True)
        PENDING_STATE_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------
    # 模式讀寫
    # -------------------------------------------------------

    def get_mode(self) -> dict:
        """
        回傳 {mode, person, set_at}
        預設 mode='auto', person=''
        """
        if not MODE_FILE.exists():
            return {"mode": "auto", "person": "", "set_at": ""}
        try:
            with open(MODE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("mode") in AVAILABLE_MODES:
                data.setdefault("person", "")
                return data
        except Exception:
            pass
        return {"mode": "auto", "person": "", "set_at": ""}

    def set_mode(self, mode: str, person: str = "", date_str: str = "") -> str:
        MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(MODE_FILE, "w", encoding="utf-8") as f:
            json.dump({"mode": mode, "person": person, "set_at": now,
                       "archive_date": date_str}, f, ensure_ascii=False)

        icon = MODE_ICON.get(mode, "📌")
        desc = MODE_DESC.get(mode, "")
        target = f"「{person}」的「{mode}」" if person else f"「{mode}」"
        dest = self._today_dir(mode, person, date_str)
        date_label = date_str if date_str else datetime.now().strftime("%Y%m%d")
        return (
            f"{icon} 歸類模式已設定\n"
            f"{'👤 人員：' + person + chr(10) if person else ''}"
            f"📂 模式：{mode}\n"
            f"📅 歸檔日期：{date_label}\n"
            f"⏰ 時間：{now}\n"
            f"📁 路徑：.../{'/'.join(dest.parts[-3:])}\n\n"
            f"現在傳入任何內容都會歸入{target}：\n{desc}\n\n"
            f"輸入「小幫手 關閉歸類模式」可恢復自動模式。"
        )

    def clear_mode(self) -> str:
        if MODE_FILE.exists():
            MODE_FILE.unlink()
        return "🤖 已關閉歸類模式，回到預設流程。\n\n上傳內容會先進待歸檔目錄，文字仍需加觸發詞（小幫手）。"

    def get_status_text(self) -> str:
        info = self.get_mode()
        mode   = info["mode"]
        person = info.get("person", "")
        set_at = info.get("set_at", "")

        if mode == "auto":
            modes_list = "\n".join(f"  • {m}" for m in AVAILABLE_MODES)
            return (
                f"🤖 目前模式：預設流程\n\n"
                f"可設定的歸類模式：\n{modes_list}\n\n"
                f"指令：\n"
                f"  小幫手 歸類模式 [模式]\n"
                f"  小幫手 歸類模式 [人員] [模式]\n\n"
                f"例：小幫手 歸類模式 建德 會議記錄"
            )

        icon = MODE_ICON.get(mode, "📌")
        archive_date = info.get("archive_date", "")
        dest = self._today_dir(mode, person, archive_date)
        person_line = f"👤 人員：{person}\n" if person else ""
        date_label = archive_date if archive_date else datetime.now().strftime("%Y%m%d")
        return (
            f"{icon} 目前歸類模式\n\n"
            f"{person_line}"
            f"📂 模式：{mode}\n"
            f"📅 歸檔日期：{date_label}\n"
            f"⏰ 設定：{set_at}\n"
            f"📁 路徑：.../{'/'.join(dest.parts[-3:])}\n\n"
            f"輸入「小幫手 關閉歸類模式」可恢復自動模式。"
        )

    def handle_command(self, msg: str) -> str:
        """處理所有歸類模式相關指令"""
        msg = msg.strip()

        if msg == "關閉歸類模式":
            return self.clear_mode()

        if msg == "歸類模式":
            return self.get_status_text()

        if msg.startswith("歸類模式"):
            args = msg[4:].strip()
            if not args:
                return self.get_status_text()

            parts = args.split()

            # 抽取末尾日期（今日/昨日/YYYY-MM-DD/YYYYMMDD）
            date_str = ""
            if parts:
                parsed_date = _parse_archive_date(parts[-1])
                if parsed_date:
                    date_str = parsed_date
                    parts = parts[:-1]

            if not parts:
                return self.get_status_text()

            # 只有一個詞
            if len(parts) == 1:
                word = parts[0]
                matched_mode = _fuzzy_mode(word)
                if matched_mode:
                    current_person = self.get_mode().get("person", "")
                    return self.set_mode(matched_mode, current_person, date_str)
                # 不是模式名稱 → 視為查詢該人員狀態
                return self._query_person_brief(word)

            # 兩個以上的詞：第一個是人員，第二個（之後）是模式
            person_candidate = parts[0]
            mode_candidate   = " ".join(parts[1:])
            matched_mode = _fuzzy_mode(mode_candidate) or _fuzzy_mode(parts[1])
            if matched_mode:
                return self.set_mode(matched_mode, person_candidate, date_str)

            # 都不匹配
            modes_str = "、".join(AVAILABLE_MODES)
            return f"⚠️ 找不到模式「{mode_candidate}」\n可用模式：{modes_str}"

        return ""

    # -------------------------------------------------------
    # 查詢歸檔
    # -------------------------------------------------------

    def query_archive(self, person: str = "") -> str:
        """
        查詢歸檔內容：
          無 person → 列出所有人員資料夾
          有 person → 列出該人員所有模式與最近檔案
        """
        if not CLASSIFIED_DIR.exists():
            return "📁 尚無任何歸檔資料"

        if not person:
            return self._list_all_persons()
        return self._list_person_content(person)

    def _list_all_persons(self) -> str:
        """列出所有歸檔（人員 + 一般模式）"""
        lines = ["📁 歸檔總覽\n"]
        persons   = []
        modes_top = []

        for item in sorted(CLASSIFIED_DIR.iterdir()):
            if not item.is_dir():
                continue
            # 判斷是人員資料夾還是模式資料夾
            if item.name in AVAILABLE_MODES:
                # 頂層模式資料夾（無人員）
                count = sum(1 for _ in item.rglob("*") if _.is_file())
                modes_top.append(f"  📂 {item.name}（{count} 個檔案）")
            else:
                # 人員資料夾
                count = sum(1 for _ in item.rglob("*") if _.is_file())
                sub_modes = [d.name for d in item.iterdir() if d.is_dir() and d.name in AVAILABLE_MODES]
                sub_str = "、".join(sub_modes) if sub_modes else "（空）"
                persons.append(f"  👤 {item.name}：{sub_str}（{count} 個檔案）")

        if persons:
            lines.append("👥 人員歸檔：")
            lines.extend(persons)
        if modes_top:
            lines.append("\n📂 一般歸檔（無指定人員）：")
            lines.extend(modes_top)
        if not persons and not modes_top:
            lines.append("（尚無資料）")

        lines.append("\n指令：小幫手 查詢歸檔 [人員名稱]")
        return "\n".join(lines)

    def _list_person_content(self, person: str) -> str:
        """列出特定人員的所有歸檔內容"""
        # 模糊匹配資料夾名稱
        person_dir = None
        if CLASSIFIED_DIR.exists():
            for d in CLASSIFIED_DIR.iterdir():
                if d.is_dir() and (person in d.name or d.name in person):
                    person_dir = d
                    break

        if not person_dir:
            return f"⚠️ 找不到「{person}」的歸檔資料夾"

        lines = [f"👤 {person_dir.name} 的歸檔\n"]
        total_files = 0

        for mode_dir in sorted(person_dir.iterdir()):
            if not mode_dir.is_dir():
                continue
            mode_name = mode_dir.name
            icon = MODE_ICON.get(mode_name, "📁")

            # 列出日期子資料夾
            date_dirs = sorted(
                [d for d in mode_dir.iterdir() if d.is_dir()],
                reverse=True
            )[:5]  # 最近 5 天

            file_count = sum(1 for _ in mode_dir.rglob("*") if _.is_file())
            total_files += file_count
            lines.append(f"{icon} {mode_name}（共 {file_count} 個檔案）")

            for date_dir in date_dirs:
                date_label = date_dir.name  # YYYYMMDD
                try:
                    d = datetime.strptime(date_label, "%Y%m%d")
                    date_label = d.strftime("%m/%d")
                except Exception:
                    pass

                subdirs = {}
                for f in date_dir.rglob("*"):
                    if f.is_file():
                        subdir = f.parent.name if f.parent != date_dir else "notes"
                        subdirs[subdir] = subdirs.get(subdir, 0) + 1

                summary = " ／ ".join(f"{k}×{v}" for k, v in subdirs.items())
                lines.append(f"    {date_label}：{summary}")

        lines.append(f"\n合計：{total_files} 個檔案")
        return "\n".join(lines)

    def _query_person_brief(self, person: str) -> str:
        """簡短查詢一個人的近況（用於 歸類模式 [人名] 指令）"""
        return self._list_person_content(person)

    # -------------------------------------------------------
    # 待歸檔兩階段流程
    # -------------------------------------------------------

    def _pending_state_path(self, scope_id: str) -> Path:
        safe_scope = _safe_name(scope_id or "default")
        return PENDING_STATE_DIR / f"{safe_scope}.json"

    def get_pending(self, scope_id: str) -> dict | None:
        path = self._pending_state_path(scope_id)
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None
        if "items" not in data:
            pending_path = data.get("pending_path", "")
            if not pending_path:
                return None
            data["items"] = [{
                "filename": data.get("filename", Path(pending_path).name),
                "source_type": data.get("source_type", "file"),
                "content_type": data.get("content_type", ""),
                "source_name": data.get("source_name", ""),
                "pending_path": pending_path,
            }]
            data.setdefault("status", "collecting")
            data.setdefault("selected_option", None)
            data.setdefault("menu_token", "")
        valid_items = []
        for item in data.get("items", []):
            file_path = Path(item.get("pending_path", ""))
            if file_path.exists():
                valid_items.append(item)
        if not valid_items:
            try:
                path.unlink()
            except Exception:
                pass
            return None
        data["items"] = valid_items
        return data

    def _save_pending(self, scope_id: str, data: dict):
        data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self._pending_state_path(scope_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear_pending(self, scope_id: str, remove_file: bool = True) -> bool:
        pending = self.get_pending(scope_id)
        path = self._pending_state_path(scope_id)
        if remove_file and pending:
            for item in pending.get("items", []):
                try:
                    Path(item["pending_path"]).unlink(missing_ok=True)
                except Exception:
                    pass
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass
        return True

    def _list_person_options(self) -> list[str]:
        names: list[str] = []
        if CLASSIFIED_DIR.exists():
            for item in sorted(CLASSIFIED_DIR.iterdir()):
                if item.is_dir() and item.name not in AVAILABLE_MODES:
                    names.append(item.name)
        current_person = self.get_mode().get("person", "")
        if current_person and current_person not in names:
            names.append(current_person)
        return names

    def _build_pending_options(self) -> list[dict]:
        options: list[dict] = []
        for person in self._list_person_options():
            modes = PENDING_ARCHIVE_MODES if person in SPECIAL_PERSONS else ["歸檔文件"]
            for mode in modes:
                options.append({"label": f"{person} {mode}", "person": person, "mode": mode, "action": "archive"})
        for mode in PENDING_ARCHIVE_MODES:
            options.append({"label": mode, "person": "", "mode": mode, "action": "archive"})
        options.append({"label": "行事曆圖檔", "person": "", "mode": "行事曆", "action": "calendar_image"})
        options.append({"label": "行事曆文字新增", "person": "", "mode": "行事曆", "action": "calendar_text"})
        options.append({"label": "421故事歸檔", "person": "", "mode": "421故事歸檔", "action": "story_421"})
        options.append({"label": "課程文宣歸檔", "person": "", "mode": "課程文宣歸檔", "action": "archive"})
        return options

    def _pending_subdir(self, source_type: str) -> str:
        return {
            "image": "images",
            "audio": "audio",
            "video": "videos",
            "file": "files",
            "text": "notes",
        }.get(source_type, "files")

    def stage_file(self, data: bytes, filename: str, source_type: str, scope_id: str,
                   content_type: str = "", source_name: str = "") -> str:
        pending = self.get_pending(scope_id) or {
            "scope_id": scope_id,
            "items": [],
            "status": "collecting",
            "selected_option": None,
            "menu_token": "",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        safe_name = _safe_name(filename)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        pending_path = PENDING_FILE_DIR / f"{stamp}_{safe_name}"
        pending_path.write_bytes(data)

        pending["scope_id"] = scope_id
        pending.setdefault("items", [])
        pending["items"].append({
            "filename": safe_name,
            "source_type": source_type,
            "content_type": content_type,
            "source_name": source_name,
            "pending_path": str(pending_path),
        })
        pending["status"] = "collecting"
        pending["selected_option"] = None
        log(f"  待歸檔暫存：{pending_path}")
        self._save_pending(scope_id, pending)
        return self.get_stage_message(scope_id)

    def stage_text(self, text: str, scope_id: str) -> str:
        pending = self.get_pending(scope_id) or {
            "scope_id": scope_id,
            "items": [],
            "status": "collecting",
            "selected_option": None,
            "menu_token": "",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        pending_path = PENDING_FILE_DIR / f"{stamp}_text.txt"
        pending_path.write_text(text.strip() + "\n", encoding="utf-8")
        pending["items"].append({
            "filename": pending_path.name,
            "source_type": "text",
            "content_type": "text/plain",
            "source_name": "text",
            "pending_path": str(pending_path),
        })
        pending["status"] = "collecting"
        pending["selected_option"] = None
        self._save_pending(scope_id, pending)
        log(f"  待歸檔文字暫存：{pending_path}")
        return self.get_stage_message(scope_id)

    def get_stage_message(self, scope_id: str) -> str:
        pending = self.get_pending(scope_id)
        if not pending:
            return ""
        return f"已接收 {len(pending.get('items', []))} 個待歸檔項目"

    def mark_pending_menu(self, scope_id: str) -> str | None:
        pending = self.get_pending(scope_id)
        if not pending:
            return None
        token = datetime.now().strftime("%Y%m%d%H%M%S%f")
        pending["menu_token"] = token
        self._save_pending(scope_id, pending)
        return token

    def should_push_pending_menu(self, scope_id: str, token: str) -> bool:
        pending = self.get_pending(scope_id)
        return bool(
            pending
            and pending.get("status") == "collecting"
            and pending.get("menu_token") == token
            and pending.get("items")
        )

    def mark_menu_sent(self, scope_id: str):
        pending = self.get_pending(scope_id)
        if not pending:
            return
        pending["status"] = "awaiting_choice"
        self._save_pending(scope_id, pending)

    def format_pending_menu(self, scope_id: str) -> str:
        pending = self.get_pending(scope_id)
        if not pending:
            return "目前沒有待歸檔項目。"

        items = pending.get("items", [])
        lines = [
            "📥 已收到檔案，先放入待歸檔目錄。",
            f"項目數：{len(items)}",
            "",
            "已接收：",
        ]
        for item in items:
            lines.append(f"- {item.get('source_type', '-')}: {item.get('filename', '-')}")
        lines.extend([
            "",
            "請直接回覆數字執行：",
        ])
        for idx, option in enumerate(self._build_pending_options(), start=1):
            lines.append(f"{idx}. {option['label']}")
        lines.append("")
        lines.append("回覆選項數字後，系統會再詢問歸檔目錄名稱。")
        lines.append("回覆 NA 可取消並刪除所有待歸檔項目。")
        return "\n".join(lines)

    def execute_pending_option(self, scope_id: str, choice: int) -> str:
        pending = self.get_pending(scope_id)
        if not pending:
            return "目前沒有待歸檔項目。"

        options = self._build_pending_options()
        if choice < 1 or choice > len(options):
            return f"請輸入 1 到 {len(options)} 的數字。"

        option = options[choice - 1]
        person = option.get("person", "")
        label = option["label"]

        try:
            pending["status"] = "awaiting_folder_name"
            pending["selected_option"] = option
            self._save_pending(scope_id, pending)
            return (f"已選擇：{label}\n"
                    f"請輸入歸檔目錄名稱\n"
                    f"（可在末尾加日期，例：宜婷美容 昨日）\n"
                    f"輸入 NA 可取消並刪除待歸檔項目")
        except Exception as e:
            log(f"  待歸檔執行失敗：{e}")
            return f"⚠️ 執行失敗：{e}"

    def submit_pending_folder_name(self, scope_id: str, folder_name: str) -> str:
        pending = self.get_pending(scope_id)
        if not pending or pending.get("status") != "awaiting_folder_name":
            return ""
        # NA → 取消並刪除待歸檔項目
        if folder_name.strip().upper() == "NA":
            count = len(pending.get("items", []))
            self.clear_pending(scope_id, remove_file=True)
            return f"🗑️ 已取消歸檔，刪除 {count} 個待歸檔項目。"
        # 從輸入末尾解析日期（今日/昨日/YYYY-MM-DD/YYYYMMDD）
        tokens = folder_name.strip().split()
        input_date = ""
        if tokens:
            parsed = _parse_archive_date(tokens[-1])
            if parsed:
                input_date = parsed
                folder_name = " ".join(tokens[:-1]).strip()

        safe_folder = _safe_folder_name(folder_name)
        if not safe_folder:
            return "目錄名稱不可空白，請重新輸入"
        option = pending.get("selected_option") or {}
        action = option.get("action", "archive")
        mode = option.get("mode", "一般歸檔")
        person = option.get("person", "")
        label = option.get("label", mode)
        # 使用者輸入的日期優先，其次用模式預設日期，最後用今日
        date_str = input_date or self.get_mode().get("archive_date", "")
        try:
            if action == "calendar_image":
                image_items = [item for item in pending.get("items", []) if item.get("source_type") == "image"]
                if not image_items:
                    return "這個選項只適用於圖片，請改選其他歸檔項目。"
                image_item = image_items[-1]
                result = self._process_calendar_image(
                    Path(image_item["pending_path"]).read_bytes(),
                    image_item["filename"],
                )
                saved = self._archive_pending_items(
                    mode, person, pending.get("items", []),
                    custom_dir=safe_folder, date_str=date_str,
                )
                self.clear_pending(scope_id, remove_file=True)
                return f"已執行：{label}\n已歸檔到 {safe_folder} 目錄\n共 {len(saved)} 個項目\n{result}"

            if action == "calendar_text":
                saved = self._archive_pending_items(
                    mode, person, pending.get("items", []),
                    fixed_subdir="manual_add", custom_dir=safe_folder, date_str=date_str,
                )
                self.clear_pending(scope_id, remove_file=True)
                return (
                    f"已執行：{label}\n"
                    f"已歸檔到 {safe_folder} 目錄\n"
                    f"共 {len(saved)} 個項目\n"
                    "接著可輸入：小幫手 新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註"
                )

            for item in pending.get("items", []):
                if mode == "整理會議心得" and item.get("source_type") == "image":
                    self._archive_training_image(
                        Path(item["pending_path"]).read_bytes(),
                        item["filename"],
                    )
            saved = self._archive_pending_items(
                mode, person, pending.get("items", []),
                custom_dir=safe_folder, date_str=date_str,
            )
            self.clear_pending(scope_id, remove_file=True)
            date_label = date_str or datetime.now().strftime("%Y%m%d")
            return f"已執行：{label}\n已歸檔到 {safe_folder} 目錄\n📅 日期：{date_label}\n共 {len(saved)} 個項目"
        except Exception as e:
            log(f"  自訂目錄歸檔失敗：{e}")
            return f"歸檔失敗：{e}"

    def _archive_pending_items(self, mode: str, person: str, items: list[dict],
                               fixed_subdir: str = "", custom_dir: str = "",
                               date_str: str = "") -> list[str]:
        saved: list[str] = []
        for item in items:
            source_type = item.get("source_type", "file")
            if source_type == "text":
                text = Path(item["pending_path"]).read_text(encoding="utf-8").strip()
                if custom_dir:
                    self._archive_custom_text(mode, person, custom_dir, text, date_str)
                else:
                    self.archive_text(text, mode, person, date_str)
                saved.append(item["filename"])
                continue
            data = Path(item["pending_path"]).read_bytes()
            if custom_dir:
                saved_path = self._archive_to_custom_dir(
                    mode,
                    person,
                    custom_dir,
                    item["filename"],
                    data,
                    fixed_subdir or self._pending_subdir(source_type),
                    date_str,
                )
            else:
                saved_path = self.archive_file(
                    data,
                    item["filename"],
                    mode,
                    fixed_subdir or self._pending_subdir(source_type),
                    person,
                    date_str,
                )
            saved.append(saved_path.name)
        return saved

    def _custom_archive_dir(self, mode: str, person: str, folder_name: str,
                            date_str: str = "") -> Path:
        date = date_str or datetime.now().strftime("%Y%m%d")
        if person:
            dest = CLASSIFIED_DIR / person / mode / folder_name / date
        else:
            dest = CLASSIFIED_DIR / mode / folder_name / date
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def _archive_custom_text(self, mode: str, person: str, folder_name: str,
                             text: str, date_str: str = ""):
        notes_file = self._custom_archive_dir(mode, person, folder_name, date_str) / "notes.txt"
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(text.strip() + "\n\n")

    def _archive_to_custom_dir(self, mode: str, person: str, folder_name: str,
                               filename: str, data: bytes, subdir: str,
                               date_str: str = "") -> Path:
        dest_dir = self._custom_archive_dir(mode, person, folder_name, date_str)
        if subdir and subdir != "notes":
            dest_dir = dest_dir / subdir
            dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        dest.write_bytes(data)
        log(f"  自訂目錄歸檔：{dest}")
        return dest

    def _archive_training_image(self, data: bytes, filename: str):
        import importlib.util as _ilu

        spec = _ilu.spec_from_file_location(
            "training_log",
            str(BASE_DIR / "agents" / "07_training_log.py")
        )
        m = _ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        date_str = datetime.now().strftime("%Y%m%d")
        m.archive_image(data, filename, date_str)

    def _process_calendar_image(self, data: bytes, message_id: str) -> str:
        import importlib.util as _ilu

        spec = _ilu.spec_from_file_location(
            "calendar_manager",
            str(BASE_DIR / "agents" / "08_calendar_manager.py")
        )
        m = _ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        result = m.process_calendar_image(data, message_id)
        return result.get("message", "已完成行事曆整理。")

    # -------------------------------------------------------
    # 歸檔工具
    # -------------------------------------------------------

    def _today_dir(self, mode: str, person: str = "", date_str: str = "") -> Path:
        """
        有人員 → classified/{person}/{mode}/{YYYYMMDD}/
        無人員 → classified/{mode}/{YYYYMMDD}/
        date_str 可指定歸檔日期（YYYYMMDD），空白則用今日
        """
        date = date_str or datetime.now().strftime("%Y%m%d")
        if person:
            d = CLASSIFIED_DIR / person / mode / date
        else:
            d = CLASSIFIED_DIR / mode / date
        d.mkdir(parents=True, exist_ok=True)
        return d

    def archive_file(self, data: bytes, filename: str, mode: str,
                     subdir: str = "", person: str = "", date_str: str = "") -> Path:
        dest_dir = self._today_dir(mode, person, date_str)
        if subdir:
            dest_dir = dest_dir / subdir
            dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        dest.write_bytes(data)
        log(f"  歸檔：{dest}")
        return dest

    def archive_text(self, text: str, mode: str, person: str = "", date_str: str = "") -> str:
        dest_dir = self._today_dir(mode, person, date_str)
        notes_file = dest_dir / "notes.txt"
        ts = datetime.now().strftime("%H:%M:%S")
        with open(notes_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {text}\n\n")
        log(f"  文字已記入：{notes_file}")
        icon = MODE_ICON.get(mode, "📌")
        person_tag = f"「{person}」的" if person else ""
        short = text[:50] + ("..." if len(text) > 50 else "")
        return f"{icon} 已記入{person_tag}「{mode}」備註\n時間：{ts}\n內容：{short}"

    # -------------------------------------------------------
    # 路由：圖片
    # -------------------------------------------------------

    def route_image(self, img_bytes: bytes, msg_id: str,
                    mode: str, person: str,
                    reply_fn, push_fn, reply_token: str, push_target: str):
        import importlib.util as _ilu

        filename = f"image_{msg_id}.jpg"
        date_str = datetime.now().strftime("%Y%m%d")
        person_tag = f"「{person}」的" if person else ""

        if mode == "會議記錄":
            try:
                spec = _ilu.spec_from_file_location(
                    "training_log",
                    str(BASE_DIR / "agents" / "07_training_log.py")
                )
                m = _ilu.module_from_spec(spec)
                spec.loader.exec_module(m)
                m.archive_image(img_bytes, filename, date_str)
                # 同時備份到人員資料夾
                if person:
                    self.archive_file(img_bytes, filename, mode, "images", person)
                reply_fn(reply_token, f"📝 圖片已歸入{person_tag}「會議記錄」（{date_str}）")
            except Exception as e:
                self.archive_file(img_bytes, filename, mode, "images", person)
                reply_fn(reply_token, f"📝 圖片已儲存至{person_tag}「會議記錄」\n（訓練歸檔失敗：{e}）")
            return True

        if mode == "行事曆":
            try:
                spec = _ilu.spec_from_file_location(
                    "calendar_manager",
                    str(BASE_DIR / "agents" / "08_calendar_manager.py")
                )
                m = _ilu.module_from_spec(spec)
                spec.loader.exec_module(m)
                result = m.process_calendar_image(img_bytes, msg_id)
                if result.get("is_calendar"):
                    # 同時備份
                    self.archive_file(img_bytes, filename, mode, "images", person)
                    reply_fn(reply_token, result["message"])
                else:
                    self.archive_file(img_bytes, filename, mode, "images", person)
                    reply_fn(reply_token, f"🗓️ 圖片已存至{person_tag}「行事曆」（未偵測到行事曆格式）")
            except Exception as e:
                self.archive_file(img_bytes, filename, mode, "images", person)
                reply_fn(reply_token, f"🗓️ 圖片已儲存至{person_tag}「行事曆」\n（解析失敗：{e}）")
            return True

        # 其他模式
        saved = self.archive_file(img_bytes, filename, mode, "images", person)
        icon = MODE_ICON.get(mode, "📌")
        reply_fn(reply_token, f"{icon} 圖片已歸入{person_tag}「{mode}」\n檔名：{saved.name}")
        return True

    # -------------------------------------------------------
    # 路由：文字（無觸發詞）
    # -------------------------------------------------------

    def route_text(self, text: str, mode: str, person: str,
                   reply_fn, push_fn, reply_token: str, push_target: str) -> bool:
        import importlib.util as _ilu

        if mode == "行事曆":
            try:
                spec = _ilu.spec_from_file_location(
                    "calendar_manager",
                    str(BASE_DIR / "agents" / "08_calendar_manager.py")
                )
                m = _ilu.module_from_spec(spec)
                spec.loader.exec_module(m)
                cal_result = m.handle_calendar_command(text)
                if cal_result:
                    reply_fn(reply_token, cal_result)
                    return True
            except Exception:
                pass

        if mode == "夥伴跟進":
            try:
                spec = _ilu.spec_from_file_location(
                    "partner_engagement",
                    str(BASE_DIR / "agents" / "09_partner_engagement.py")
                )
                m = _ilu.module_from_spec(spec)
                spec.loader.exec_module(m)
                partner_result = m.handle_partner_command(text)
                if partner_result:
                    reply_fn(reply_token, partner_result)
                    return True
            except Exception:
                pass

        result = self.archive_text(text, mode, person)
        reply_fn(reply_token, result)
        return True


# ============================================================
# 工具函式（供 webhook 使用）
# ============================================================

def download_line_content(msg_id: str, line_token: str, timeout: int = 30) -> bytes | None:
    import requests
    url = f"https://api-data.line.me/v2/bot/message/{msg_id}/content"
    r = requests.get(url, headers={"Authorization": f"Bearer {line_token}"}, timeout=timeout)
    return r.content if r.status_code == 200 else None


if __name__ == "__main__":
    agent = ClassifierAgent()
    print(agent.get_status_text())
