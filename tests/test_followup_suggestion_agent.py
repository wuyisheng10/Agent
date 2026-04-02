import importlib.util as ilu
import unittest
from pathlib import Path
from unittest.mock import patch


BASE = Path(r"C:\Users\user\claude AI_Agent")


def load_module(name: str, rel_path: str):
    spec = ilu.spec_from_file_location(name, str(BASE / rel_path))
    module = ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


agent_mod = load_module("followup_suggestion_agent_test", "agents/21_followup_suggestion_agent.py")


class FollowupSuggestionAgentTest(unittest.TestCase):
    def test_list_commands_return_names(self):
        with patch.object(agent_mod, "list_prospect_names", return_value=["Amy", "小美"]), \
             patch.object(agent_mod, "list_partner_names", return_value=["建德", "宜芸"]):
            self.assertIn("Amy", agent_mod.FollowupSuggestionAgent().handle_command("跟進建議 潛在家人"))
            self.assertIn("建德", agent_mod.FollowupSuggestionAgent().handle_command("跟進建議 夥伴"))

    def test_suggest_for_prospect_uses_codex(self):
        row = {
            "姓名": "Amy",
            "職業": "語言治療師",
            "地區": "中壢",
            "備註": "重視生活品質",
            "接觸狀態": "待接觸",
            "下次跟進日": "2026-04-05",
        }
        with patch.object(agent_mod, "_find_prospect", return_value=row), \
             patch.object(agent_mod, "run_codex_cli", return_value="SUGGEST:AMY"):
            result = agent_mod.suggest_for_prospect("Amy")
        self.assertEqual(result, "SUGGEST:AMY")

    def test_suggest_for_partner_falls_back(self):
        partner = {
            "name": "建德",
            "level": "1",
            "stage": "待跟進",
            "goal": "穩定帶線",
            "records": [{"time": "2026-04-02T10:00:00", "type": "followup", "content": "已邀約", "next_followup": "2026-04-05"}],
        }
        with patch.object(agent_mod, "_find_partner", return_value=partner), \
             patch.object(agent_mod, "run_codex_cli", side_effect=RuntimeError("cli down")):
            result = agent_mod.suggest_for_partner("建德")
        self.assertIn("跟進建議｜夥伴｜建德", result)
        self.assertIn("接下來7天", result)

    def test_different_people_get_different_strategies(self):
        prospect_health = {
            "姓名": "Amy",
            "職業": "語言治療師",
            "需求標籤": "健康需求型",
            "備註": "重視生活品質 有用淨水器",
            "接觸狀態": "待接觸",
            "淨水器型號": "eSpring Pro",
        }
        prospect_income = {
            "姓名": "Ben",
            "職業": "業務",
            "需求標籤": "收入需求型",
            "備註": "最近想找副業 增加收入",
            "接觸狀態": "已接觸",
        }
        with patch.object(agent_mod, "_find_prospect", side_effect=[prospect_health, prospect_income]), \
             patch.object(agent_mod, "run_codex_cli", side_effect=RuntimeError("cli down")):
            amy = agent_mod.suggest_for_prospect("Amy")
            ben = agent_mod.suggest_for_prospect("Ben")
        self.assertIn("健康體驗切入型", amy)
        self.assertIn("副業機會切入型", ben)
        self.assertNotEqual(amy, ben)


if __name__ == "__main__":
    unittest.main(verbosity=2)
