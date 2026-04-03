import importlib.util
import json
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory


def _load_followup_module():
    if "dotenv" not in sys.modules:
        module = types.ModuleType("dotenv")
        module.load_dotenv = lambda *args, **kwargs: None
        sys.modules["dotenv"] = module
    path = Path(__file__).resolve().parent.parent / "agents" / "13_followup_agent.py"
    spec = importlib.util.spec_from_file_location("followup_agent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_classify_risk_handles_non_numeric_weekly_actions():
    module = _load_followup_module()
    partner = {"最後聯絡日": "2020-01-01", "本週動作數": "N/A"}
    risk = module.classify_risk(partner, red_days=3, yellow_days=5)
    assert risk == "red"


def test_read_csv_falls_back_to_partners_json():
    module = _load_followup_module()
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
                        "goal": "建立穩定收入",
                        "note": "測試備註",
                        "updated_at": "2026-04-02T09:00:00",
                        "created_at": "2026-03-01T09:00:00",
                        "records": [
                            {"time": "2026-04-01T10:00:00", "content": "已跟進"},
                            {"time": "2026-04-02T11:00:00", "content": "再提醒"},
                        ],
                    }
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        old_csv = module.PARTNERS_CSV
        old_json = module.PARTNERS_JSON
        try:
            module.PARTNERS_CSV = root / "csv_data" / "partners.csv"
            module.PARTNERS_JSON = partners_json
            rows = module.read_csv()
        finally:
            module.PARTNERS_CSV = old_csv
            module.PARTNERS_JSON = old_json

        assert len(rows) == 1
        assert rows[0]["姓名"] == "建德"
        assert rows[0]["本週動作數"] == "2"
