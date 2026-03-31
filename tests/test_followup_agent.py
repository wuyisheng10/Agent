import importlib.util
import sys
import types
from pathlib import Path


def _load_followup_module():
    if "dotenv" not in sys.modules:
        m = types.ModuleType("dotenv")
        m.load_dotenv = lambda *args, **kwargs: None
        sys.modules["dotenv"] = m
    p = Path(__file__).resolve().parent.parent / "agents" / "13_followup_agent.py"
    spec = importlib.util.spec_from_file_location("followup_agent", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_classify_risk_handles_non_numeric_weekly_actions():
    m = _load_followup_module()
    partner = {"最後聯絡日": "2020-01-01", "本週動作數": "N/A"}
    risk = m.classify_risk(partner, red_days=3, yellow_days=5)
    assert risk == "red"
