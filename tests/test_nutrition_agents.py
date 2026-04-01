import importlib.util as ilu
import json
import unittest
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


BASE = Path(r"C:\Users\user\claude AI_Agent")


def load_module(name: str, rel_path: str):
    spec = ilu.spec_from_file_location(name, str(BASE / rel_path))
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dri = load_module("nutrition_dri_agent", "agents/18_nutrition_dri_agent.py")
assessment = load_module("nutrition_assessment_agent", "agents/19_nutrition_assessment_agent.py")
webhook = load_module("line_webhook_nutrition", "agents/06_line_webhook.py")


class _FakeResp:
    def __init__(self, text: str = "", content: bytes = b"", status_code: int = 200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeClassifierAgent:
    def __init__(self, root: Path):
        self.root = root

    def archive_file(self, data, filename, mode, category="files", person="", date_str=""):
        parts = [self.root]
        if person:
            parts.append(person)
        parts.append(mode)
        if date_str:
            parts.append(date_str)
        target_dir = Path(*parts)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / filename
        if isinstance(data, str):
            data = data.encode("utf-8")
        target.write_bytes(data)
        return target


class _FakeClassifierModule:
    def __init__(self, root: Path):
        self._root = root

    def ClassifierAgent(self):
        return _FakeClassifierAgent(self._root)


class _FakeEmailModule:
    def __init__(self):
        self.calls = []

    def send_email_to(self, subject, html, recipients):
        self.calls.append({"subject": subject, "html": html, "recipients": recipients})
        return True


class NutritionAgentsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.csv_dir = self.root / "csv_data"
        self.pdf_dir = self.root / "nutrition_pdfs"
        self.report_dir = self.root / "nutrition_reports"
        self.logs_dir = self.root / "logs"
        self.archive_dir = self.root / "classified"
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.patches = [
            patch.object(dri, "DRI_DATA_PATH", self.csv_dir / "nutrition_dri.json"),
            patch.object(dri, "PDF_DIR", self.pdf_dir),
            patch.object(assessment, "REPORT_DIR", self.report_dir),
            patch.object(assessment, "LOGS_DIR", self.logs_dir),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_dri_import_and_queries(self):
        html = """
        <html><body>
        <a href="/File/abc.pdf">全本.pdf</a>
        <a href='/File/def.pdf'>總表.pdf</a>
        </body></html>
        """
        calls = []

        def fake_get(url, headers=None, timeout=None, verify=True):
            calls.append(url)
            if url.endswith("pid=12285"):
                return _FakeResp(text=html)
            return _FakeResp(content=b"%PDF-1.4 fake pdf bytes")

        with patch.object(dri.requests, "get", side_effect=fake_get):
            agent = dri.NutritionDRIAgent()
            import_msg = agent.download_hpa_data()

        self.assertTrue((self.csv_dir / "nutrition_dri.json").exists())
        self.assertGreaterEqual(len(list(self.pdf_dir.glob("*.pdf"))), 2)
        self.assertIn("pdf", import_msg.lower())
        self.assertIn("12285", calls[0])

        agent = dri.NutritionDRIAgent()
        standard_msg = agent.handle_command("查詢營養素標準 女 30 午餐")
        mechanism_msg = agent.handle_command("營養素運作原理 鈣")

        self.assertIn("午餐", standard_msg)
        self.assertIn("30", standard_msg)
        self.assertIn("鈣", mechanism_msg)
        self.assertIn("警訊", mechanism_msg)

    def test_assessment_email_and_archive_by_person_name(self):
        fake_email = _FakeEmailModule()
        fake_classifier = _FakeClassifierModule(self.archive_dir)
        sessions = {}

        assessment_result = {
            "gender": "女",
            "age": 30,
            "dri_group": "19-30歲",
            "water_ml": 1500,
            "water_target": 2000,
            "meals": [{"label": "早餐", "analysis": "蛋白質偏低、蔬菜不足"}],
            "assessment_md": "\n".join([
                "## 總體評估",
                "- 蛋白質偏低",
                "- 維生素C可能不足",
                "## 長期維持這種飲食模式的身體警訊",
                "- 容易疲勞與恢復變慢",
            ]),
            "generated_at": "2026-04-01 08:00",
        }

        with patch.object(assessment, "_analyze_image_with_codex", return_value="早餐：吐司與咖啡，蛋白質不足"), \
             patch.object(assessment, "_assess_deficiencies", return_value=assessment_result), \
             patch.object(assessment, "_load_email", return_value=fake_email), \
             patch.object(assessment, "_load_classifier", return_value=fake_classifier):
            start_msg = assessment.handle_command("開始飲食評估 女 30 王小美", sessions, "scope-1")
            self.assertIn("王小美", start_msg)

            agent = assessment.NutritionAssessmentAgent()
            add_msg = agent.add_photo(sessions["scope-1"], b"fake-image", "早餐")
            self.assertIn("早餐", add_msg)

            result_msg = assessment.handle_command("評估飲食 喝水量1500ml", sessions, "scope-1")

        self.assertIn("飲食評估", result_msg)
        self.assertEqual(len(fake_email.calls), 1)
        self.assertEqual(fake_email.calls[0]["recipients"], ["wuyisheng10@gmail.com"])
        self.assertIn("王小美", "".join(str(p) for p in self.archive_dir.rglob("*")))
        archived_files = list(self.archive_dir.rglob("*nutrition_report*.html"))
        self.assertTrue(archived_files)

    def test_line_and_web_menu_wiring(self):
        self.assertIn("查詢營養素標準", webhook.HELP_TEXT)
        self.assertIn("開始飲食評估", webhook.HELP_TEXT)

        html = webhook._render_dashboard_html_v2()
        self.assertIn("營養評估", html)
        self.assertIn("查詢營養素標準", html)
        self.assertIn("開始飲食評估", html)

        class _FakeDRIAgent:
            def handle_command(self, cmd):
                return f"DRI_OK:{cmd}"

        class _FakeDRIModule:
            def NutritionDRIAgent(self):
                return _FakeDRIAgent()

        class _FakeAssessModule:
            @staticmethod
            def handle_command(cmd, sessions, scope_id, push_fn=None, reply_fn=None, reply_token=""):
                return f"ASSESS_OK:{cmd}:{scope_id}"

        with patch.object(webhook, "_load_nutrition_dri", return_value=_FakeDRIModule()), \
             patch.object(webhook, "_load_nutrition_assessment", return_value=_FakeAssessModule()):
            dri_result = webhook.process_web_command("查詢營養素標準 男 30")
            assess_result = webhook.process_web_command("開始飲食評估 男 30")

        self.assertEqual(dri_result, "DRI_OK:查詢營養素標準 男 30")
        self.assertEqual(assess_result, "ASSESS_OK:開始飲食評估 男 30:web")

    def test_web_upload_prefers_nutrition_session_over_archive(self):
        class _FakeNutritionAgent:
            def add_photo(self, session, data, meal_label=None):
                session["photos"].append({"bytes": data, "label": meal_label or "早餐"})
                return "NUTRITION_UPLOAD_OK"

        class _FakeNutritionModule:
            def NutritionAssessmentAgent(self):
                return _FakeNutritionAgent()

        webhook._nutrition_sessions["web"] = {
            "awaiting_photo": True,
            "next_meal_label": "早餐",
            "photos": [],
        }
        try:
            with patch.object(webhook, "_load_nutrition_assessment", return_value=_FakeNutritionModule()):
                client = webhook.app.test_client()
                resp = client.post(
                    "/api/upload",
                    data={"file": (io.BytesIO(b"fakeimg"), "meal.jpg")},
                    content_type="multipart/form-data",
                )
            data = resp.get_json()
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(data["result"], "NUTRITION_UPLOAD_OK")
            self.assertEqual(len(webhook._nutrition_sessions["web"]["photos"]), 1)
        finally:
            webhook._nutrition_sessions.pop("web", None)


if __name__ == "__main__":
    unittest.main()
