import importlib.util as _ilu
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(r"C:\Users\user\claude AI_Agent")
load_dotenv(dotenv_path=BASE_DIR / ".env")

SENT_LOG = BASE_DIR / "output" / "sent_log.json"
LOG_FILE = BASE_DIR / "logs" / "webhook_log.txt"
CLASSIFIED_DIR = BASE_DIR / "output" / "classified"

LINE_TOKEN = os.getenv("LINE_CHANNEL_TOKEN", "")
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_REPLY = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH = "https://api.line.me/v2/bot/message/push"
NGROK_URL = os.getenv("NGROK_URL", "").rstrip("/")


def _load_module(module_name: str, filename: str):
    spec = _ilu.spec_from_file_location(module_name, str(BASE_DIR / "agents" / filename))
    module = _ilu.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_training():
    return _load_module("training_log", "07_training_log.py")


def _load_calendar():
    return _load_module("calendar_manager", "08_calendar_manager.py")


def _load_partner():
    return _load_module("partner_engagement", "09_partner_engagement.py")


def _load_market_dev():
    return _load_module("market_dev_agent", "11_market_dev_agent.py")


def _load_training_agent():
    return _load_module("training_agent", "12_training_agent.py")


def _load_followup():
    return _load_module("followup_agent", "13_followup_agent.py")


def _load_motivation():
    return _load_module("motivation_agent", "14_motivation_agent.py")


def _load_classifier():
    return _load_module("classifier_agent", "15_classifier_agent.py")


def _load_course_invite():
    return _load_module("course_invite_agent", "16_course_invite_agent.py")


def _load_daily_report():
    return _load_module("daily_report_agent", "17_daily_report_agent.py")


def _load_nutrition_dri():
    return _load_module("nutrition_dri_agent", "18_nutrition_dri_agent.py")


def _load_nutrition_assessment():
    return _load_module("nutrition_assessment_agent", "19_nutrition_assessment_agent.py")
