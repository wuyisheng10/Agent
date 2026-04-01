import importlib.util as ilu
import json
import re
import unittest
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


BASE = Path(r"C:\Users\user\claude AI_Agent")
OUTPUT_DIR = BASE / "output"


def load_module(name: str, rel_path: str):
    spec = ilu.spec_from_file_location(name, str(BASE / rel_path))
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


webhook = load_module("line_webhook_full_validation", "agents/06_line_webhook.py")


class _FakeCalendarModule:
    @staticmethod
    def handle_calendar_command(cmd):
        prefixes = (
            "查詢行事曆",
            "查詢過往行事曆",
            "查詢全部行事曆",
            "新增行事曆",
            "修改行事曆",
            "刪除行事曆",
        )
        if any(cmd.startswith(prefix) for prefix in prefixes):
            return f"CAL:{cmd}"
        return None


class _FakePartnerModule:
    @staticmethod
    def handle_partner_command(cmd):
        prefixes = (
            "查詢夥伴",
            "查詢待跟進夥伴",
            "新增夥伴",
            "更新夥伴",
            "跟進夥伴",
            "激勵夥伴",
            "刪除夥伴",
        )
        if any(cmd.startswith(prefix) for prefix in prefixes):
            return f"PARTNER:{cmd}"
        return None


class _FakeClassifierAgent:
    def __init__(self):
        self.pending = {}

    def get_mode(self):
        return {"mode": "auto", "set_at": ""}

    def get_pending(self, scope):
        return self.pending.get(scope)

    def submit_pending_folder_name(self, scope, text):
        return None

    def execute_pending_option(self, scope, choice):
        return f"PENDING:{scope}:{choice}"

    def format_pending_menu(self, scope):
        return f"PENDING_MENU:{scope}"

    def clear_pending(self, scope, remove_file=True):
        self.pending.pop(scope, None)

    def clear_mode(self):
        return "MODE:CLEARED"

    def set_mode(self, mode, person=""):
        return f"MODE:{mode}:{person}"

    def query_archive(self, person=None):
        return f"ARCHIVE:{person or 'ALL'}"

    def handle_command(self, cmd):
        if cmd == "歸類模式":
            return "MODE:STATUS"
        if cmd.startswith("歸類模式") or cmd == "關閉歸類模式":
            return f"MODE_CMD:{cmd}"
        return f"CLASSIFIER:{cmd}"


class _FakeClassifierModule:
    AVAILABLE_MODES = [
        "會議記錄",
        "行事曆",
        "夥伴跟進",
        "市場開發",
        "培訓資料",
        "一般歸檔",
        "整理會議心得",
        "歸檔會議紀錄",
        "歸檔行動紀錄",
        "歸檔文件",
        "421故事歸檔",
        "課程文宣歸檔",
        "營養保健歸檔",
        "美容保養歸檔",
        "居家清潔歸檔",
        "個人護理歸檔",
        "廚具生活歸檔",
        "空水設備歸檔",
        "體重管理歸檔",
        "香氛風格歸檔",
        "事業工具歸檔",
        "產品故事歸檔",
    ]

    def __init__(self):
        self._agent = _FakeClassifierAgent()

    def ClassifierAgent(self):
        return self._agent


class _FakeMarketDevAgent:
    @staticmethod
    def handle_add_prospect(cmd):
        return f"MARKET_ADD:{cmd}"

    @staticmethod
    def list_prospects(keyword=None):
        return [{"姓名": "王小美", "類型": "A"}]

    @staticmethod
    def update_prospect_fields(name, fields):
        return f"MARKET_UPDATE:{name}:{sorted(fields)}"

    @staticmethod
    def add_experience(name, product, note=""):
        return f"MARKET_EXPERIENCE:{name}:{product}:{note}"


class _FakeMarketDevModule:
    def MarketDevAgent(self):
        return _FakeMarketDevAgent()


class _FakeCourseInviteAgent:
    @staticmethod
    def handle_command(cmd):
        return f"COURSE:{cmd}"

    @staticmethod
    def list_meetings():
        return [{"id": "COURSE-1", "title": "台南OPP", "datetime": "2026-04-18 13:30"}]

    @staticmethod
    def generate_partner_invite_for_meeting(name, meeting):
        return f"PARTNER_INVITE:{name}:{meeting['id']}"

    @staticmethod
    def generate_prospect_invite_for_meeting(name, meeting):
        return f"PROSPECT_INVITE:{name}:{meeting['id']}"

    @staticmethod
    def update_invite(meeting_id, name, content):
        return True


class _FakeCourseInviteModule:
    def CourseInviteAgent(self):
        return _FakeCourseInviteAgent()


class _FakeDailyReportAgent:
    @staticmethod
    def run():
        return "DAILY:OK"


class _FakeDailyReportModule:
    def DailyReportAgent(self):
        return _FakeDailyReportAgent()


class _FakeDRIAgent:
    @staticmethod
    def handle_command(cmd):
        return f"DRI:{cmd}"


class _FakeDRIModule:
    def NutritionDRIAgent(self):
        return _FakeDRIAgent()


class _FakeNutritionAssessmentModule:
    @staticmethod
    def handle_command(cmd, sessions, scope_id, push_fn=None, reply_fn=None, reply_token=""):
        return f"ASSESS:{cmd}:{scope_id}"


class _FakeTrainingAgent:
    @staticmethod
    def handle_query(cmd):
        return f"TRAINING_AGENT:{cmd}"


class _FakeTrainingAgentModule:
    def TrainingAgent(self):
        return _FakeTrainingAgent()


class _FakeFollowupAgent:
    @staticmethod
    def generate_report_text():
        return "FOLLOWUP:OK"


class _FakeFollowupModule:
    def FollowupAgent(self):
        return _FakeFollowupAgent()


class _FakeMotivationAgent:
    @staticmethod
    def handle_realtime(cmd):
        return f"MOTIVATION:{cmd}"


class _FakeMotivationModule:
    def MotivationAgent(self):
        return _FakeMotivationAgent()


class _FakeTrainingLogModule:
    _root = None

    @staticmethod
    def get_summary_by_key(key):
        return f"SUMMARY:{key}"

    @staticmethod
    def process_transcript(transcript, date_str, force=False):
        return "20260401", f"TRAINING_LOG:{date_str}:{'FORCE' if force else 'NORMAL'}"

    @classmethod
    def get_date_dir(cls, date_str):
        path = cls._root / date_str
        path.mkdir(parents=True, exist_ok=True)
        transcript = path / "transcript.txt"
        if not transcript.exists():
            transcript.write_text("測試逐字稿", encoding="utf-8")
        return path

    @staticmethod
    def archive_transcript(transcript, date_str):
        return None


class _FakeRequest:
    def __init__(self, text):
        self.headers = {"X-Line-Signature": "sig"}
        self.json = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"userId": "U-test"},
                    "message": {"type": "text", "text": text},
                }
            ]
        }

    def get_data(self):
        return b"{}"


FORM_SAMPLES = {
    "新增潛在家人": "新增潛在家人 王小美|老師|朋友介紹|備註",
    "加入潛在家人資訊": "潛在家人資料 王小美",
    "查詢培訓進度": "培訓 建德",
    "激勵夥伴": "激勵 建德 最近需要鼓勵",
    "里程碑記錄": "里程碑 建德 首次達成目標",
    "新增夥伴": "新增夥伴 建德 | 月入三萬 | 2026-04-05 | 持續跟進 | A",
    "更新夥伴": "更新夥伴 建德 | 1 | 積極跟進 | 2026-04-05 | LINE:test | 備註 | 直銷商 | 7519213 | - | 陳薾云 | 2026-06-30 | 2026-03 | 翡翠 | 3% | 有 | 2821 | 有 | V | V | V | V | A",
    "查詢指定夥伴": "查詢夥伴 建德",
    "跟進夥伴": "跟進夥伴 建德 | 已邀約 | 2026-04-05 | 備註",
    "刪除夥伴": "刪除夥伴 建德",
    "手動新增行事曆": "新增行事曆 2026-04-05 19:30 團隊會議 | 台北教室",
    "修改行事曆": "修改行事曆 EVT-ABCD1234 2026-04-06 20:00 新標題 | 新備註",
    "刪除行事曆": "刪除行事曆 EVT-ABCD1234",
    "設定歸類模式": "歸類模式 市場開發",
    "查詢指定人員歸檔": "查詢歸檔 建德",
    "整理指定日期記錄": "整理 20260401",
    "查詢培訓記錄": "MTG-20260401",
    "👤 人物故事歸檔": "潛在家人資料 建德",
    "新增課程會議": "新增課程會議 2026-04-10 19:00 四月OPP說明會|台中大里店|歡迎帶朋友|鑽石李大明|資深鑽石|事業機會介紹|主題分享",
    "從行事曆加入課程": "從行事曆加入課程 OPP",
    "修改課程會議": "修改課程會議 COURSE-1234 標題:新版標題|地點:台北",
    "刪除課程會議": "刪除課程會議 COURSE-1234",
    "新增課程文宣": "新增課程文宣 四月OPP邀約|歡迎參加",
    "優化課程文宣（AI）": "優化課程文宣 PROMO-1234",
    "邀約文宣－潛在家人（AI）": "邀約文宣 潛在家人 Amy",
    "邀約文宣－跟進夥伴（AI）": "邀約文宣 跟進夥伴",
    "修改已產生的邀約文宣": "修改已產生的今日之後會議邀約文宣 COURSE-1234 | 建德 | 新內容",
    "查詢營養素標準": "查詢營養素標準 男 30 午餐",
    "營養素運作原理": "營養素運作原理 鈣",
    "開始飲食評估": "開始飲食評估 女 30 對象:王小美",
    "設定歸檔對象": "設定評估對象 王小美",
    "設定下一張餐別": "設定餐別 早餐",
    "執行飲食評估": "評估飲食 喝水量1500ml",
}


def _extract_web_items():
    text = (BASE / "agents/webhook_web_views.py").read_text(encoding="utf-8")
    return re.findall(r'\{label:"([^"]+)",tag:"([^"]+)"(?:,cmd:"([^"]+)")?', text)


class FullLineWebValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        _FakeTrainingLogModule._root = Path(self.tmp.name) / "training"
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(webhook, "_load_calendar", return_value=_FakeCalendarModule()))
        self.stack.enter_context(patch.object(webhook, "_load_partner", return_value=_FakePartnerModule()))
        self.stack.enter_context(patch.object(webhook, "_load_classifier", return_value=_FakeClassifierModule()))
        self.stack.enter_context(patch.object(webhook, "_load_market_dev", return_value=_FakeMarketDevModule()))
        self.stack.enter_context(patch.object(webhook, "_load_course_invite", return_value=_FakeCourseInviteModule()))
        self.stack.enter_context(patch.object(webhook, "_load_daily_report", return_value=_FakeDailyReportModule()))
        self.stack.enter_context(patch.object(webhook, "_load_nutrition_dri", return_value=_FakeDRIModule()))
        self.stack.enter_context(patch.object(webhook, "_load_nutrition_assessment", return_value=_FakeNutritionAssessmentModule()))
        self.stack.enter_context(patch.object(webhook, "_load_training_agent", return_value=_FakeTrainingAgentModule()))
        self.stack.enter_context(patch.object(webhook, "_load_followup", return_value=_FakeFollowupModule()))
        self.stack.enter_context(patch.object(webhook, "_load_motivation", return_value=_FakeMotivationModule()))
        self.stack.enter_context(patch.object(webhook, "_load_training", return_value=_FakeTrainingLogModule()))

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def _run_line_sequence(self, messages):
        replies = []
        pushes = []
        state = {
            "exec_menu_active": {},
            "awaiting_person_for_mode": {},
            "awaiting_exec_input": {},
            "awaiting_prospect_selection": {},
            "awaiting_prospect_file": {},
            "awaiting_invite_selection": {},
            "awaiting_partner_invite_category": {},
            "awaiting_partner_invite_person": {},
            "awaiting_partner_invite_meeting": {},
            "awaiting_invite_manage_select": {},
            "awaiting_invite_manage_action": {},
            "awaiting_invite_manage_edit": {},
        }

        def _reply(token, text):
            replies.append(text)

        def _push(target, text):
            pushes.append(text)

        class _ImmediateThread:
            def __init__(self, target=None, args=(), kwargs=None, daemon=None):
                self.target = target
                self.args = args
                self.kwargs = kwargs or {}

            def start(self):
                if self.target:
                    self.target(*self.args, **self.kwargs)

        with patch.object(webhook, "reply_message", _reply), \
             patch.object(webhook, "push_message", _push), \
             patch.object(webhook.threading, "Thread", _ImmediateThread):
            for message in messages:
                webhook._webhook_line_events.process_line_events(
                    request=_FakeRequest(message),
                    abort=lambda code: (_ for _ in ()).throw(RuntimeError(code)),
                    verify_signature=lambda body, sig: True,
                    log=lambda *_args, **_kwargs: None,
                    load_classifier=webhook._load_classifier,
                    handle_image_message=lambda *a, **k: None,
                    handle_audio_message=lambda *a, **k: None,
                    handle_video_message=lambda *a, **k: None,
                    handle_file_message=lambda *a, **k: None,
                    handle_training_command=webhook.handle_training_command,
                    reply_message=_reply,
                    execute_menu_text=webhook.EXEC_MENU_TEXT,
                    execute_menu_items=webhook.EXEC_MENU_ITEMS,
                    exec_menu_active=state["exec_menu_active"],
                    awaiting_person_for_mode=state["awaiting_person_for_mode"],
                    awaiting_exec_input=state["awaiting_exec_input"],
                    awaiting_prospect_selection=state["awaiting_prospect_selection"],
                    awaiting_prospect_file=state["awaiting_prospect_file"],
                    awaiting_invite_selection=state["awaiting_invite_selection"],
                    awaiting_partner_invite_category=state["awaiting_partner_invite_category"],
                    awaiting_partner_invite_person=state["awaiting_partner_invite_person"],
                    awaiting_partner_invite_meeting=state["awaiting_partner_invite_meeting"],
                    awaiting_invite_manage_select=state["awaiting_invite_manage_select"],
                    awaiting_invite_manage_action=state["awaiting_invite_manage_action"],
                    awaiting_invite_manage_edit=state["awaiting_invite_manage_edit"],
                    looks_like_explicit_command=webhook._looks_like_explicit_command,
                    normalize_partner_category_choice=webhook._normalize_partner_category_choice,
                    partners_by_category=webhook._partners_by_category,
                    format_partner_choice_menu=webhook._format_partner_choice_menu,
                    format_meeting_choice_menu=webhook._format_meeting_choice_menu,
                    format_invite_manage_actions=webhook._format_invite_manage_actions,
                    format_invite_edit_confirm=webhook._format_invite_edit_confirm,
                    load_course_invite=webhook._load_course_invite,
                    load_classifier_module=webhook._load_classifier,
                    load_market_dev=webhook._load_market_dev,
                    format_prospect_detail=webhook._format_prospect_detail,
                )
        return replies, pushes

    def test_line_exec_menu_all_items_respond(self):
        results = []
        replies, pushes = self._run_line_sequence(["5168"])
        self.assertTrue(replies and "執行選單" in replies[-1])

        for number, item in sorted(webhook.EXEC_MENU_ITEMS.items()):
            replies, pushes = self._run_line_sequence(["5168", str(number)])
            joined = "\n".join(replies + pushes)
            ok = False
            if item.get("prompt"):
                ok = item["prompt"] in joined
            elif item.get("cmd") == "指令集":
                ok = "完整說明" in joined or "營養評估" in joined
            elif item.get("cmd") == "寄送每日報告":
                ok = "DAILY:OK" in joined
            else:
                ok = bool(joined) and "⚠️ 無法辨識指令" not in joined
            results.append({
                "number": number,
                "label": item["label"],
                "ok": ok,
                "reply_count": len(replies),
                "push_count": len(pushes),
                "preview": joined[:200],
            })
            self.assertTrue(ok, f"LINE 選單 {number} {item['label']} 未正確回應: {joined}")

        (OUTPUT_DIR / "full_line_menu_validation.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def test_web_buttons_and_forms_all_respond(self):
        items = _extract_web_items()
        direct_results = []
        form_results = []

        direct_items = [(label, cmd) for label, tag, cmd in items if tag == "執行"]
        form_labels = [label for label, tag, _cmd in items if tag == "表單"]

        self.assertEqual(set(form_labels), set(FORM_SAMPLES), "表單驗證樣本未覆蓋所有網頁表單")

        for label, cmd in direct_items:
            result = webhook.process_web_command(cmd)
            ok = bool(result) and "無法辨識" not in result and "意圖：其他" not in result
            direct_results.append({"label": label, "cmd": cmd, "ok": ok, "preview": str(result)[:200]})
            self.assertTrue(ok, f"網頁直達按鈕 {label} 失敗: {result}")

        for label, cmd in FORM_SAMPLES.items():
            result = webhook.process_web_command(cmd)
            ok = bool(result) and "無法辨識" not in result and "意圖：其他" not in result
            form_results.append({"label": label, "cmd": cmd, "ok": ok, "preview": str(result)[:200]})
            self.assertTrue(ok, f"網頁表單 {label} 失敗: {result}")

        (OUTPUT_DIR / "full_web_direct_validation.json").write_text(
            json.dumps(direct_results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (OUTPUT_DIR / "full_web_form_validation.json").write_text(
            json.dumps(form_results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
