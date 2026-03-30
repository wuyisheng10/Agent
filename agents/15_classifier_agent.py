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
import os
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
    "整理會議心得", "歸檔會議紀錄", "歸檔行動紀錄", "歸檔文件",
]
PENDING_ARCHIVE_MODES = ["整理會議心得", "歸檔會議紀錄", "歸檔行動紀錄", "歸檔文件"]
SPECIAL_PENDING_ACTIONS = ["行事曆圖檔", "行事曆文字新增"]

MODE_ICON = {
    "會議記錄": "📝", "行事曆": "🗓️", "夥伴跟進": "🤝",
    "市場開發": "🎯", "培訓資料": "📚", "一般歸檔": "📁", "auto": "🤖",
    "整理會議心得": "🧠", "歸檔會議紀錄": "📝", "歸檔行動紀錄": "✅", "歸檔文件": "📄",
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

    def set_mode(self, mode: str, person: str = "") -> str:
        MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(MODE_FILE, "w", encoding="utf-8") as f:
            json.dump({"mode": mode, "person": person, "set_at": now}, f, ensure_ascii=False)

        icon = MODE_ICON.get(mode, "📌")
        desc = MODE_DESC.get(mode, "")
        target = f"「{person}」的「{mode}」" if person else f"「{mode}」"
        dest = self._today_dir(mode, person)
        return (
            f"{icon} 歸類模式已設定\n"
            f"{'👤 人員：' + person + chr(10) if person else ''}"
            f"📂 模式：{mode}\n"
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
        dest = self._today_dir(mode, person)
        person_line = f"👤 人員：{person}\n" if person else ""
        return (
            f"{icon} 目前歸類模式\n\n"
            f"{person_line}"
            f"📂 模式：{mode}\n"
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

            # 只有一個詞
            if len(parts) == 1:
                word = parts[0]
                matched_mode = _fuzzy_mode(word)
                if matched_mode:
                    # 保留目前人員
                    current_person = self.get_mode().get("person", "")
                    return self.set_mode(matched_mode, current_person)
                # 不是模式名稱 → 視為查詢該人員狀態
                return self._query_person_brief(word)

            # 兩個以上的詞：第一個是人員，第二個是模式
            person_candidate = parts[0]
            mode_candidate   = " ".join(parts[1:])  # 支援「一般歸檔」等含空格的名稱
            matched_mode = _fuzzy_mode(mode_candidate) or _fuzzy_mode(parts[1])
            if matched_mode:
                return self.set_mode(matched_mode, person_candidate)

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
        file_path = Path(data.get("pending_path", ""))
        if not file_path.exists():
            try:
                path.unlink()
            except Exception:
                pass
            return None
        return data

    def clear_pending(self, scope_id: str, remove_file: bool = True) -> bool:
        pending = self.get_pending(scope_id)
        path = self._pending_state_path(scope_id)
        if remove_file and pending:
            try:
                Path(pending["pending_path"]).unlink(missing_ok=True)
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
            for mode in PENDING_ARCHIVE_MODES:
                options.append({"label": f"{person} {mode}", "person": person, "mode": mode, "action": "archive"})
        for mode in PENDING_ARCHIVE_MODES:
            options.append({"label": mode, "person": "", "mode": mode, "action": "archive"})
        options.append({"label": "行事曆圖檔", "person": "", "mode": "行事曆", "action": "calendar_image"})
        options.append({"label": "行事曆文字新增", "person": "", "mode": "行事曆", "action": "calendar_text"})
        return options

    def _pending_subdir(self, source_type: str) -> str:
        return {
            "image": "images",
            "audio": "audio",
            "video": "videos",
            "file": "files",
        }.get(source_type, "files")

    def stage_file(self, data: bytes, filename: str, source_type: str, scope_id: str,
                   content_type: str = "", source_name: str = "") -> str:
        self.clear_pending(scope_id, remove_file=True)
        safe_name = _safe_name(filename)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        pending_path = PENDING_FILE_DIR / f"{stamp}_{safe_name}"
        pending_path.write_bytes(data)

        payload = {
            "scope_id": scope_id,
            "filename": safe_name,
            "source_type": source_type,
            "content_type": content_type,
            "source_name": source_name,
            "pending_path": str(pending_path),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(self._pending_state_path(scope_id), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        log(f"  待歸檔暫存：{pending_path}")
        return self.format_pending_menu(scope_id)

    def format_pending_menu(self, scope_id: str) -> str:
        pending = self.get_pending(scope_id)
        if not pending:
            return "目前沒有待歸檔項目。"

        lines = [
            "📥 已收到檔案，先放入待歸檔目錄。",
            f"檔名：{pending.get('filename', '-')}",
            f"類型：{pending.get('source_type', '-')}",
            "",
            "請直接回覆數字執行：",
        ]
        for idx, option in enumerate(self._build_pending_options(), start=1):
            lines.append(f"{idx}. {option['label']}")
        lines.append("")
        lines.append("例如回覆 7，就會執行第 7 個選項。")
        return "\n".join(lines)

    def execute_pending_option(self, scope_id: str, choice: int) -> str:
        pending = self.get_pending(scope_id)
        if not pending:
            return "目前沒有待歸檔項目。"

        options = self._build_pending_options()
        if choice < 1 or choice > len(options):
            return f"請輸入 1 到 {len(options)} 的數字。"

        option = options[choice - 1]
        data = Path(pending["pending_path"]).read_bytes()
        filename = pending["filename"]
        source_type = pending.get("source_type", "file")
        person = option.get("person", "")
        label = option["label"]

        try:
            if option["action"] == "calendar_image":
                if source_type != "image":
                    return "這個選項只適用於圖片，請改選其他歸檔項目。"
                result = self._process_calendar_image(data, filename)
                self.clear_pending(scope_id, remove_file=True)
                return f"已執行：{label}\n{result}"

            if option["action"] == "calendar_text":
                saved = self.archive_file(data, filename, "行事曆", "manual_add", person)
                self.clear_pending(scope_id, remove_file=True)
                return (
                    f"已執行：{label}\n"
                    f"附件已存入：{saved.name}\n"
                    "接著可輸入：小幫手 新增行事曆 YYYY-MM-DD [HH:MM] 標題 | 備註"
                )

            mode = option["mode"]
            if mode == "整理會議心得" and source_type == "image":
                self._archive_training_image(data, filename)
            saved = self.archive_file(data, filename, mode, self._pending_subdir(source_type), person)
            self.clear_pending(scope_id, remove_file=True)
            person_tag = f"{person} " if person else ""
            return f"已執行：{person_tag}{mode}\n檔名：{saved.name}"
        except Exception as e:
            log(f"  待歸檔執行失敗：{e}")
            return f"⚠️ 執行失敗：{e}"

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

    def _today_dir(self, mode: str, person: str = "") -> Path:
        """
        有人員 → classified/{person}/{mode}/{YYYYMMDD}/
        無人員 → classified/{mode}/{YYYYMMDD}/
        """
        today = datetime.now().strftime("%Y%m%d")
        if person:
            d = CLASSIFIED_DIR / person / mode / today
        else:
            d = CLASSIFIED_DIR / mode / today
        d.mkdir(parents=True, exist_ok=True)
        return d

    def archive_file(self, data: bytes, filename: str, mode: str,
                     subdir: str = "", person: str = "") -> Path:
        dest_dir = self._today_dir(mode, person)
        if subdir:
            dest_dir = dest_dir / subdir
            dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        dest.write_bytes(data)
        log(f"  歸檔：{dest}")
        return dest

    def archive_text(self, text: str, mode: str, person: str = "") -> str:
        dest_dir = self._today_dir(mode, person)
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
