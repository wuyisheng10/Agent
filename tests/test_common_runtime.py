import tempfile
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch

from agents import common_runtime


class TestCommonRuntime(unittest.TestCase):
    def test_load_json_config_ok(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "settings.json"
            p.write_text('{"k": 1}', encoding="utf-8")
            self.assertEqual(common_runtime.load_json_config(p), {"k": 1})

    def test_load_json_config_missing(self):
        p = Path(tempfile.gettempdir()) / "not-exist-settings.json"
        self.assertEqual(common_runtime.load_json_config(p), {})

    @patch("agents.common_runtime.subprocess.run")
    def test_run_codex_cli_reads_response_file(self, mock_run):
        mock_run.return_value = Mock(returncode=0, stdout="")
        with tempfile.TemporaryDirectory() as td:
            with patch.object(common_runtime, "LOGS_DIR", Path(td)):
                with patch("agents.common_runtime.tempfile.NamedTemporaryFile") as ntf:
                    file_path = Path(td) / "resp.txt"
                    file_path.write_text("ok", encoding="utf-8")
                    entered = Mock()
                    entered.name = str(file_path)
                    ctx = Mock()
                    ctx.__enter__ = Mock(return_value=entered)
                    ctx.__exit__ = Mock(return_value=False)
                    ntf.return_value = ctx
                    result = common_runtime.run_codex_cli("hello", timeout=1)
                    self.assertEqual(result, "ok")

    @unittest.skipUnless(importlib.util.find_spec("requests"), "requests not installed")
    @patch("requests.post")
    def test_push_line_message(self, mock_post):
        mock_post.return_value = Mock(status_code=200)
        status = common_runtime.push_line_message("token", "user", "https://example.com", "hi")
        self.assertEqual(status, 200)

    def test_push_line_message_without_token(self):
        status = common_runtime.push_line_message("", "user", "https://example.com", "hi")
        self.assertIsNone(status)


if __name__ == "__main__":
    unittest.main()
