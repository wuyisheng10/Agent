import importlib.util as ilu
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


BASE = Path(r"C:\Users\user\claude AI_Agent")


def load_module(name: str, rel_path: str):
    spec = ilu.spec_from_file_location(name, str(BASE / rel_path))
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


training = load_module("training_log", "agents/07_training_log.py")
calendar = load_module("calendar_manager", "agents/08_calendar_manager.py")
partner = load_module("partner_engagement", "agents/09_partner_engagement.py")
motivation = load_module("motivation_agent", "agents/14_motivation_agent.py")
classifier = load_module("classifier_agent", "agents/15_classifier_agent.py")
course = load_module("course_invite_agent", "agents/16_course_invite_agent.py")


class AllFeaturesSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.logs = self.root / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)

        self.training_dir = self.root / "training"
        self.training_index = self.training_dir / "training_index.json"

        self.calendar_dir = self.root / "calendar"
        self.calendar_img_dir = self.calendar_dir / "images"
        self.calendar_db = self.calendar_dir / "calendar_events.json"

        self.partner_dir = self.root / "partners"
        self.partner_file = self.partner_dir / "partners.json"

        self.pending_dir = self.root / "pending_archive"
        self.pending_file_dir = self.pending_dir / "files"
        self.pending_state_dir = self.pending_dir / "states"
        self.classified_dir = self.root / "classified"

        self.csv_dir = self.root / "csv_data"
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.meetings_file = self.csv_dir / "course_meetings.json"
        self.promos_file = self.csv_dir / "course_promos.json"
        self.invites_file = self.csv_dir / "course_invites.json"
        self.partners_csv = self.csv_dir / "partners.csv"
        self.motivation_log = self.csv_dir / "motivation_log.csv"

        self.patches = [
            patch.object(training, "TRAINING_DIR", self.training_dir),
            patch.object(training, "INDEX_FILE", self.training_index),
            patch.object(training, "LOG_FILE", self.logs / "training_log.txt"),
            patch.object(calendar, "CAL_DIR", self.calendar_dir),
            patch.object(calendar, "IMG_DIR", self.calendar_img_dir),
            patch.object(calendar, "DB_FILE", self.calendar_db),
            patch.object(calendar, "LOG_FILE", self.logs / "calendar_log.txt"),
            patch.object(partner, "PARTNER_DIR", self.partner_dir),
            patch.object(partner, "PARTNER_FILE", self.partner_file),
            patch.object(partner, "LOG_FILE", self.logs / "partner_log.txt"),
            patch.object(motivation, "CSV_DIR", self.csv_dir),
            patch.object(motivation, "PARTNERS_CSV", self.partners_csv),
            patch.object(motivation, "PARTNERS_JSON", self.partner_file),
            patch.object(motivation, "MOTIVATION_LOG", self.motivation_log),
            patch.object(motivation, "LOG_FILE", self.logs / "motivation_log.txt"),
            patch.object(classifier, "PENDING_DIR", self.pending_dir),
            patch.object(classifier, "PENDING_FILE_DIR", self.pending_file_dir),
            patch.object(classifier, "PENDING_STATE_DIR", self.pending_state_dir),
            patch.object(classifier, "CLASSIFIED_DIR", self.classified_dir),
            patch.object(classifier, "MODE_FILE", self.root / "classification_mode.json"),
            patch.object(course, "DATA_DIR", self.csv_dir),
            patch.object(course, "MEETINGS_FILE", self.meetings_file),
            patch.object(course, "PROMOS_FILE", self.promos_file),
            patch.object(course, "INVITES_FILE", self.invites_file),
            patch.object(course, "CAL_DB", self.calendar_db),
            patch.object(course, "PARTNERS_JSON", self.partner_file),
            patch.object(course, "LOG_FILE", self.logs / "course_log.txt"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_training_log_roundtrip(self):
        summary = {
            "感恩": "感謝今天有一場很扎實的培訓。",
            "悟到": "先把自己的狀態調對，分享才會有力量。",
            "學到": "課程邀約要先看對方目前需要什麼。",
            "做到": "今天已整理逐字稿並建立後續跟進清單。",
            "目標": "本週完成三位夥伴的會議邀約。",
        }
        key = training.save_summary(summary, "20260401")
        msg = training.get_summary_by_key(key)
        html = (training.get_date_dir("20260401") / "summary.html").read_text(encoding="utf-8")

        self.assertEqual(key, "MTG-20260401")
        self.assertIn("培訓記錄 2026/04/01", msg)
        self.assertIn("本週完成三位夥伴的會議邀約", html)

    def test_calendar_add_query_update_delete(self):
        add_msg = calendar.handle_calendar_command("新增行事曆 2026-04-05 19:30 團隊會議 | 台北教室")
        self.assertIn("已新增", add_msg)

        events = calendar.load_events()
        self.assertEqual(len(events), 1)
        event_id = events[0]["id"]

        query_msg = calendar.handle_calendar_command("查詢行事曆")
        self.assertIn("團隊會議", query_msg)

        update_msg = calendar.handle_calendar_command(
            f"修改行事曆 {event_id} 2026-04-06 20:00 核心會議 | 線上"
        )
        self.assertIn("已修改", update_msg)

        delete_msg = calendar.handle_calendar_command(f"刪除行事曆 {event_id}")
        self.assertIn(event_id, delete_msg)
        self.assertEqual(calendar.load_events(), [])

    def test_partner_management_flow(self):
        add_msg = partner.handle_partner_command(
            "新增夥伴 測試夥伴 | 建立穩定邀約節奏 | 2026-04-08 | 對課程有興趣 | A"
        )
        self.assertIn("已新增夥伴", add_msg)

        list_msg = partner.handle_partner_command("查詢夥伴")
        self.assertIn("測試夥伴", list_msg)
        self.assertIn("A", list_msg)

        update_msg = partner.handle_partner_command(
            "更新夥伴 測試夥伴 | 3 | 持續跟進 | 2026-04-09 | LINE:test123 | 備註更新 | 直銷商 | 1234567 | 合夥人甲 | 推薦人乙 | 2026-12-31 | 2026-04 | 新星獎 | 3% | 有 | 120 | 有 | 500 | 400 | 300 | 200 | B"
        )
        self.assertIn("已更新夥伴", update_msg)

        detail_msg = partner.handle_partner_command("查詢夥伴 測試夥伴")
        self.assertIn("分類：B", detail_msg)
        self.assertIn("1234567", detail_msg)

        follow_msg = partner.handle_partner_command("跟進夥伴 測試夥伴 | 已邀約課程 | 2026-04-10 | 等待對方確認")
        self.assertIn("已更新跟進", follow_msg)

    def test_motivation_flow(self):
        rows = [{
            "姓名": "激勵夥伴",
            "LINE_UID": "",
            "電話": "0912000000",
            "加入日期": "2026-03-20",
            "已完成培訓天": "5",
            "最後培訓推播日": "2026-03-28",
            "最後聯絡日": "2026-03-29",
            "本週動作數": "2",
            "風險等級": "",
            "里程碑": "",
            "備註": "需要鼓勵",
        }]
        with open(self.partners_csv, "w", encoding="utf-8-sig", newline="") as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=motivation.PARTNER_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

        agent = motivation.MotivationAgent()
        with patch.object(motivation, "generate_emotion_support", return_value="你做得很好，繼續前進。"):
            emotion_msg = agent.handle_realtime("激勵 激勵夥伴 最近有點累")
        self.assertIn("激勵夥伴", emotion_msg)

        with patch.object(motivation, "generate_milestone_celebration", return_value="恭喜你完成第一單。"):
            milestone_msg = agent.handle_realtime("里程碑 激勵夥伴 第一單")
        self.assertIn("第一單", milestone_msg)

        updated = motivation.read_partners()
        target = next(r for r in updated if r["姓名"] == "激勵夥伴")
        self.assertIn("第一單", target.get("里程碑", ""))

    def test_classifier_two_stage_archive(self):
        agent = classifier.ClassifierAgent()
        stage_msg = agent.stage_text("這是一段測試歸檔文字", "scope-1")
        self.assertIn("已接收", stage_msg)

        menu = agent.format_pending_menu("scope-1")
        self.assertIn("421故事歸檔", menu)
        option_index = next(
            idx for idx, opt in enumerate(agent._build_pending_options(), start=1)
            if opt["label"] == "421故事歸檔"
        )

        option_msg = agent.execute_pending_option("scope-1", option_index)
        self.assertIn("請輸入歸檔目錄名稱", option_msg)

        submit_msg = agent.submit_pending_folder_name("scope-1", "測試421故事")
        self.assertIn("已歸檔", submit_msg)

        note_files = list(self.classified_dir.rglob("notes.txt"))
        self.assertTrue(note_files)
        self.assertIn("測試歸檔文字", note_files[0].read_text(encoding="utf-8"))

    def test_course_invite_generated_invite_management(self):
        meeting = course.add_meeting("台南A級培訓", "2026-04-12", "19:30", "台南教室", "培訓說明")
        promo = course.add_promo("課程文宣", "這是一份課程文宣測試內容")
        course.save_invite(meeting["id"], "測試夥伴", "partner", "原始邀約文宣內容")

        self.assertTrue(promo["id"].startswith("PROMO-"))

        agent = course.CourseInviteAgent()
        query_msg = agent.handle_command("查詢已產生的今日之後會議邀約文宣")
        self.assertIn(meeting["id"], query_msg)
        self.assertIn("測試夥伴", query_msg)

        update_msg = agent.handle_command(
            f"修改已產生的今日之後會議邀約文宣 {meeting['id']} | 測試夥伴 | 更新後邀約文宣內容"
        )
        self.assertIn("已更新", update_msg)

        rows = course.list_upcoming_invites(today_only_after=True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["content"], "更新後邀約文宣內容")


if __name__ == "__main__":
    unittest.main()
