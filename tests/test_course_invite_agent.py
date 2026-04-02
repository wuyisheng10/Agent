import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import importlib.util as ilu


BASE = Path(r"C:\Users\user\claude AI_Agent")
SPEC = ilu.spec_from_file_location("course_invite_agent", str(BASE / "agents" / "16_course_invite_agent.py"))
course = ilu.module_from_spec(SPEC)
SPEC.loader.exec_module(course)


class CourseInviteAgentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.csv_dir = self.tmp_path / "csv_data"
        self.csv_dir.mkdir(parents=True, exist_ok=True)

        self.meetings_file = self.csv_dir / "course_meetings.json"
        self.promos_file = self.csv_dir / "course_promos.json"
        self.calendar_file = self.tmp_path / "calendar" / "calendar_events.json"
        self.calendar_file.parent.mkdir(parents=True, exist_ok=True)

        self.patches = [
            patch.object(course, "DATA_DIR", self.csv_dir),
            patch.object(course, "MEETINGS_FILE", self.meetings_file),
            patch.object(course, "PROMOS_FILE", self.promos_file),
            patch.object(course, "CAL_DB", self.calendar_file),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_add_list_delete_meeting(self):
        item = course.add_meeting("四月OPP說明會", "2026-04-10", "19:00", "台中", "歡迎帶朋友")
        self.assertTrue(item["id"].startswith("COURSE-"))

        meetings = course.list_meetings(upcoming_only=False)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0]["title"], "四月OPP說明會")

        formatted = course.format_meetings(meetings)
        self.assertIn("四月OPP說明會", formatted)
        self.assertIn(item["id"], formatted)

        msg = course.delete_meeting(item["id"])
        self.assertIn(item["id"], msg)
        self.assertEqual(course.list_meetings(upcoming_only=False), [])

    def test_import_from_calendar(self):
        payload = [
            {"title": "OPP說明會", "date": "2026-04-12", "time": "19:30", "note": "歡迎新朋友"},
            {"title": "一般聚餐", "date": "2026-04-13", "time": "18:30", "note": "非課程"},
        ]
        self.calendar_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        result = course.import_from_calendar("OPP")
        self.assertIn("已從行事曆匯入 1 筆課程會議", result)
        meetings = course.list_meetings(upcoming_only=False)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0]["title"], "OPP說明會")

    def test_add_and_list_promos(self):
        item = course.add_promo("四月文宣", "一起來認識安麗事業")
        self.assertTrue(item["id"].startswith("PROMO-"))

        promos = course.list_promos()
        self.assertEqual(len(promos), 1)
        self.assertEqual(promos[0]["title"], "四月文宣")

        formatted = course.format_promos(promos)
        self.assertIn("四月文宣", formatted)
        self.assertIn(item["id"], formatted)

    def test_handle_command_paths(self):
        agent = course.CourseInviteAgent()

        add_result = agent.handle_command("新增課程會議 2026-04-10 19:00 四月OPP說明會|台中大里店|歡迎帶朋友")
        self.assertIn("已新增課程會議", add_result)

        list_result = agent.handle_command("查詢課程會議")
        self.assertIn("四月OPP說明會", list_result)

        promo_result = agent.handle_command("新增課程文宣 四月文宣|一起來認識安麗事業")
        self.assertIn("已新增課程文宣", promo_result)

        list_promo = agent.handle_command("查詢課程文宣")
        self.assertIn("四月文宣", list_promo)

    def test_generate_invite_without_meetings(self):
        with patch.object(course, "_run_codex", return_value="AI邀約文案"):
            result = course.generate_prospect_invite("Amy")
        self.assertIn("目前沒有排定的課程會議", result)

    def test_optimize_and_apply_promo(self):
        item = course.add_promo("四月文宣", "原始內容")
        with patch.object(course, "_run_codex", return_value="優化後內容"):
            result = course.optimize_promo(item["id"])
        self.assertIn("已優化", result)

        applied = course.apply_optimized_promo(item["id"])
        self.assertIn("已將優化內容套用", applied)

        updated = course.get_promo_detail(item["id"])
        self.assertEqual(updated["content"], "優化後內容")


if __name__ == "__main__":
    unittest.main()
