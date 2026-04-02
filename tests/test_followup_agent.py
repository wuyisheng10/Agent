import importlib.util
import json
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory


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
    partner = {"?敺蝯⊥": "2020-01-01", "?祇勗?雿": "N/A"}
    risk = m.classify_risk(partner, red_days=3, yellow_days=5)
    assert risk == "red"


def test_read_csv_falls_back_to_partners_json():
    m = _load_followup_module()
    with TemporaryDirectory() as td:
        root = Path(td)
        partners_json = root / "partners" / "partners.json"
        partners_json.parent.mkdir(parents=True, exist_ok=True)
        partners_json.write_text(
            json.dumps(
                [
                    {
                        "name": "建德",
                        "stage": "待跟進",
                        "goal": "穩定帶線",
                        "note": "測試備註",
                        "updated_at": "2026-04-02T09:00:00",
                        "created_at": "2026-03-01T09:00:00",
                        "records": [
                            {"time": "2026-04-01T10:00:00", "content": "已邀約"},
                            {"time": "2026-04-02T11:00:00", "content": "已回報"},
                        ],
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        old_csv = m.PARTNERS_CSV
        old_json = m.PARTNERS_JSON
        try:
            m.PARTNERS_CSV = root / "csv_data" / "partners.csv"
            m.PARTNERS_JSON = partners_json
            rows = m.read_csv()
        finally:
            m.PARTNERS_CSV = old_csv
            m.PARTNERS_JSON = old_json

        assert len(rows) == 1
        assert rows[0]["憪?"] == "建德"
