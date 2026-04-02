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
            patch.object(training_system, "SEVEN_DAY_FILE", self.training_dir / "seven_day.json"),
            patch.object(training_system, "ACTIONS_FILE", self.training_dir / "actions.json"),
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
            "新增培訓模組 四個勇於 | 領導人特質 | 培養面對錯誤與改變的能力 | 用真實案例說明勇於學習、認錯、改變、承擔"
        )
        self.assertIn("已新增培訓模組", msg1)

        msg2 = self.agent.handle_command(
            "新增培訓課程 領導人特質：四個勇於 | 四個勇於 | 2026-04-10 | 19:30 | 台南教室 | 鐘老師 | 夥伴"
        )
        self.assertIn("已新增培訓課程", msg2)

        msg3 = self.agent.handle_command(
            "新增培訓反思 王小美 | 領導人特質：四個勇於 | 原來承擔是成長的入口 | 學到帶人先帶自己 | 先完成一場會後關心 | 本週完成三次跟進"
        )
        self.assertIn("已新增培訓反思", msg3)

        progress = self.agent.handle_command("查詢培訓進度 王小美")
        self.assertIn("王小美 的培訓進度", progress)
        self.assertIn("領導人特質：四個勇於", progress)
        self.assertIn("本週完成三次跟進", progress)

        summary = self.agent.handle_command("查詢培訓總表")
        self.assertIn("培訓總表", summary)
        self.assertIn("模組數：1", summary)

    def test_phase2_seven_day_and_action_flow(self):
        self.agent.handle_command(
            "新增培訓模組 七天法則 | 新人守則 | 協助新人七天內穩定建立信心 | 聚焦環境、觀念、陪伴與行動"
        )
        self.agent.handle_command(
            "新增培訓課程 新人七天法則 | 七天法則 | 2026-04-12 | 14:00 | 台南教室 | 李老師 | 新人"
        )

        start_msg = self.agent.handle_command("啟動七天法則 建德 | 2026-04-12 | 先陪他進環境聽一場課")
        self.assertIn("已啟動七天法則", start_msg)

        report_msg = self.agent.handle_command(
            "七天法則回報 建德 | 第1天 | 聽一場 OPP 並整理問題 | 已完成 | 對制度開始有興趣"
        )
        self.assertIn("已回報七天法則", report_msg)

        seven_day = self.agent.handle_command("查詢七天法則 建德")
        self.assertIn("建德 的七天法則", seven_day)
        self.assertIn("第1天", seven_day)

        action_msg = self.agent.handle_command(
            "新增課後行動 建德 | 新人七天法則 | 兩天內再陪一次 OPP | 2026-04-18"
        )
        self.assertIn("已新增課後行動", action_msg)
        action_id = action_msg.split("\n")[1].replace("- ", "").strip()

        update_msg = self.agent.handle_command(
            f"回報課後行動 建德 | {action_id} | 進行中 | 已排好下一次 OPP 時間"
        )
        self.assertIn("已回報課後行動", update_msg)

        action_query = self.agent.handle_command("查詢課後行動 建德")
        self.assertIn(action_id, action_query)
        self.assertIn("進行中", action_query)

    def test_list_options(self):
        self.agent.handle_command(
            "新增培訓模組 七天法則 | 新人守則 | 協助新人七天內穩定建立信心 | 聚焦環境、觀念、陪伴與行動"
        )
        self.agent.handle_command(
            "新增培訓課程 新人七天法則 | 七天法則 | 2026-04-12 | 14:00 | 台南教室 | 李老師 | 新人"
        )
        modules = training_system.list_module_options()
        sessions = training_system.list_session_options()
        self.assertEqual(modules[0]["title"], "七天法則")
        self.assertEqual(sessions[0]["title"], "新人七天法則")


if __name__ == "__main__":
    unittest.main()
