import csv
import importlib.util as ilu
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch


BASE = Path(r"C:\Users\user\claude AI_Agent")


def load_module(name: str, rel_path: str):
    spec = ilu.spec_from_file_location(name, str(BASE / rel_path))
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


daily_report = load_module("daily_report_agent", "agents/17_daily_report_agent.py")
line_webhook = load_module("line_webhook_daily_report", "agents/06_line_webhook.py")


class _ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self._target = target
        self.daemon = daemon

    def start(self):
        if self._target:
            self._target()


class DailyReportAgentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.csv_dir = self.root / "csv_data"
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.logs = self.root / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        self.calendar_dir = self.root / "calendar"
        self.calendar_dir.mkdir(parents=True, exist_ok=True)
        self.partners_dir = self.root / "partners"
        self.partners_dir.mkdir(parents=True, exist_ok=True)

        self.market_csv = self.csv_dir / "market_list.csv"
        self.partners_json = self.partners_dir / "partners.json"
        self.meetings_file = self.csv_dir / "course_meetings.json"
        self.invites_file = self.csv_dir / "course_invites.json"
        self.calendar_file = self.calendar_dir / "calendar_events.json"

        with open(self.market_csv, "w", encoding="utf-8-sig", newline="") as f:
            fieldnames = ["姓名", "電話", "下次行動建議", "最後聯絡日期", "AI評分"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                "姓名": "潛在家人測試",
                "電話": "0912000001",
                "下次行動建議": "安排會面",
                "最後聯絡日期": "2026-04-02",
                "AI評分": "5",
            })

        self.partners_json.write_text(json.dumps([
            {
                "id": "PTN-TEST1",
                "name": "跟進夥伴測試",
                "level": "3",
                "stage": "持續跟進",
                "next_followup": "2026-04-03",
                "category": "A",
            }
        ], ensure_ascii=False), encoding="utf-8")

        self.meetings_file.write_text(json.dumps([
            {
                "id": "COURSE-TEST1",
                "title": "台南A級培訓",
                "date": "2026-04-10",
                "time": "19:30",
                "location": "台南教室",
                "description": "測試會議",
            }
        ], ensure_ascii=False), encoding="utf-8")

        self.invites_file.write_text(json.dumps({
            "COURSE-TEST1::邀約對象": {
                "meeting_id": "COURSE-TEST1",
                "name": "邀約對象",
                "role": "partner",
                "content": "這是一封已產生的邀約文宣。",
                "created_at": "2026-04-01T08:00:00",
                "updated_at": "2026-04-01T08:00:00",
            }
        }, ensure_ascii=False), encoding="utf-8")

        self.calendar_file.write_text(json.dumps([
            {
                "id": "EVT-TEST1",
                "date": "2026-04-09",
                "time": "20:00",
                "title": "團隊會議",
                "note": "測試活動",
            }
        ], ensure_ascii=False), encoding="utf-8")

        self.patches = [
            patch.object(daily_report, "DATA_DIR", self.csv_dir),
            patch.object(daily_report, "MARKET_CSV", self.market_csv),
            patch.object(daily_report, "PARTNERS_JSON", self.partners_json),
            patch.object(daily_report, "MEETINGS_FILE", self.meetings_file),
            patch.object(daily_report, "INVITES_FILE", self.invites_file),
            patch.object(daily_report, "CALENDAR_FILE", self.calendar_file),
            patch.object(daily_report, "LOG_FILE", self.logs / "daily_report_log.txt"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_recipients_are_fixed_targets(self):
        self.assertEqual(
            daily_report.RECIPIENTS,
            ["wuyisheng10@gmail.com", "kidmanyeh@gmail.com"],
        )

    def test_build_report_contains_four_required_sections(self):
        subject, body = daily_report.build_report()
        self.assertIn("潛在家人清單", body)
        self.assertIn("跟進夥伴清單", body)
        self.assertIn("邀約文宣（今日後）", body)
        self.assertIn("行事曆（今日後）", body)
        self.assertIn("潛在家人測試", body)
        self.assertIn("跟進夥伴測試", body)
        self.assertIn("這是一封已產生的邀約文宣", body)
        self.assertIn("團隊會議", body)
        self.assertIn("每日", subject)

    @patch.object(daily_report, "send_email_to", create=True)
    def test_run_sends_to_both_recipients(self, mock_send):
        mock_send.return_value = True
        with patch.dict("sys.modules", {"email_notify": Mock(send_email_to=mock_send)}):
            result = daily_report.DailyReportAgent().run()
        self.assertIn("wuyisheng10@gmail.com", result)
        self.assertIn("kidmanyeh@gmail.com", result)
        args, _ = mock_send.call_args
        self.assertEqual(args[2], ["wuyisheng10@gmail.com", "kidmanyeh@gmail.com"])

    def test_line_trigger_daily_report(self):
        replies = []

        class _FakeDR:
            class DailyReportAgent:
                def run(self):
                    return "✅ 每日報告已寄送至 wuyisheng10@gmail.com, kidmanyeh@gmail.com"

        with patch.object(line_webhook, "_load_daily_report", return_value=_FakeDR):
            with patch.object(line_webhook, "reply_message", side_effect=lambda token, text: replies.append(("reply", text))):
                with patch.object(line_webhook, "push_message", side_effect=lambda target, text: replies.append(("push", text))):
                    with patch.object(line_webhook.threading, "Thread", _ImmediateThread):
                        handled = line_webhook.handle_training_command("寄送每日報告", "token", "U1", "")

        self.assertTrue(handled)
        self.assertTrue(any("正在產生每日報告並寄送" in text for kind, text in replies if kind == "reply"))
        self.assertTrue(any("每日報告已寄送至" in text for kind, text in replies if kind == "push"))

    def test_web_trigger_daily_report(self):
        class _FakeDR:
            class DailyReportAgent:
                def run(self):
                    return "✅ 每日報告已寄送至 wuyisheng10@gmail.com, kidmanyeh@gmail.com"

        with patch.object(line_webhook, "_load_daily_report", return_value=_FakeDR):
            result = line_webhook.process_web_command("寄送每日報告")
        self.assertIn("每日報告已寄送至", result)

    def test_api_trigger_daily_report(self):
        class _FakeDR:
            class DailyReportAgent:
                def run(self):
                    return "✅ 每日報告已寄送至 wuyisheng10@gmail.com, kidmanyeh@gmail.com"

        with patch.object(line_webhook, "_load_daily_report", return_value=_FakeDR):
            client = line_webhook.app.test_client()
            resp = client.post("/api/send-daily-report")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("每日報告已寄送至", resp.get_json()["result"])

    def test_setup_scheduler_contains_8am_daily_report_task(self):
        content = (BASE / "setup_scheduler.ps1").read_text(encoding="utf-8")
        self.assertIn("Amway_AI_DailyReport", content)
        self.assertIn('--mode daily_report', content)
        self.assertIn('Daily Report 08:00', content)


if __name__ == "__main__":
    unittest.main()
