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


training_system = load_module("training_system_agent", "agents/23_training_system_agent.py")


class TrainingSystemAgentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.training_dir = self.root / "training_system"
        self.patches = [
            patch.object(training_system, "TRAINING_DIR", self.training_dir),
            patch.object(training_system, "MODULES_FILE", self.training_dir / "modules.json"),
            patch.object(training_system, "SESSIONS_FILE", self.training_dir / "sessions.json"),
            patch.object(training_system, "REFLECTIONS_FILE", self.training_dir / "reflections.json"),
            patch.object(training_system, "PROGRESS_FILE", self.training_dir / "progress.json"),
        ]
        for p in self.patches:
            p.start()
        self.agent = training_system.TrainingSystemAgent()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_phase1_training_flow(self):
        msg1 = self.agent.handle_command(
            "新增培訓模組 四個勇於 | 領導人特質 | 建立領導人思維 | 勇於學習、勇於認錯、勇於改變、勇於承擔"
        )
        self.assertIn("已新增培訓模組", msg1)

        msg2 = self.agent.handle_command(
            "新增培訓課程 領導人特質｜四個勇於 | 四個勇於 | 2026-04-10 | 19:30 | 台南教室 | 鐘老師 | 夥伴"
        )
        self.assertIn("已新增培訓課程", msg2)

        msg3 = self.agent.handle_command(
            "新增培訓反思 王小美 | 領導人特質｜四個勇於 | 我願意先認錯 | 學到四個勇於是連動的 | 本週每天回報市場 | 本月建立節奏"
        )
        self.assertIn("已新增培訓反思", msg3)

        progress = self.agent.handle_command("查詢培訓進度 王小美")
        self.assertIn("王小美 的培訓進度", progress)
        self.assertIn("四個勇於", progress)
        self.assertIn("本週每天回報市場", progress)

        summary = self.agent.handle_command("查詢培訓總表")
        self.assertIn("培訓總表", summary)
        self.assertIn("王小美", summary)

    def test_list_options(self):
        self.agent.handle_command(
            "新增培訓模組 七天法則 | 新人守則 | 建立新人前七天節奏 | 打好預防針、帶進環境"
        )
        self.agent.handle_command(
            "新增培訓課程 新人七天法則 | 七天法則 | 2026-04-12 | 14:00 | 台中教室 | 王老師 | 夥伴"
        )
        modules = training_system.list_module_options()
        sessions = training_system.list_session_options()
        self.assertEqual(modules[0]["title"], "七天法則")
        self.assertEqual(sessions[0]["title"], "新人七天法則")
