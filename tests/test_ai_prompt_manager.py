import importlib.util as ilu
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


prompt_manager = load_module("ai_prompt_manager_test", "agents/20_ai_prompt_manager.py")
webhook = load_module("line_webhook_prompt_test", "agents/06_line_webhook.py")


class AIPromptManagerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.prompt_file = Path(self.tmp.name) / "ai_prompts.json"
        self.patch = patch.object(prompt_manager, "PROMPT_FILE", self.prompt_file)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_list_and_update_prompt(self):
        text = prompt_manager.handle_command("查詢AI提示詞")
        self.assertIn("course_promo_optimize", text)

        detail = prompt_manager.handle_command("查詢AI提示詞 course_promo_optimize")
        self.assertIn("優化課程文宣", detail)

        updated = prompt_manager.handle_command("更新AI提示詞 course_promo_optimize | 新版提示詞內容")
        self.assertIn("已更新", updated)

        detail2 = prompt_manager.handle_command("查詢AI提示詞 course_promo_optimize")
        self.assertIn("新版提示詞內容", detail2)

    def test_web_and_help_entry_present(self):
        self.assertIn("查詢AI提示詞", webhook.HELP_TEXT)
        self.assertIn("修改AI提示詞", webhook.EXEC_MENU_TEXT)

        html = webhook._render_dashboard_html_v2()
        self.assertIn("AI 提示詞", html)
        self.assertIn("修改AI提示詞", html)
        self.assertIn("/api/ai-prompt/", html)
        self.assertIn("目前提示詞預覽", html)


if __name__ == "__main__":
    unittest.main()
